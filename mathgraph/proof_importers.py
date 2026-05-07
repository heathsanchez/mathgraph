"""Tolerant import helpers for TRUE-side proof metadata."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from mathgraph.lean_artifacts import LeanArtifact, LeanArtifactKind, LeanVerificationStatus, make_lean_artifact_id
from mathgraph.proof_atlas import build_proof_atlas_from_true_rows


TRUE_PROOF_FILENAMES = (
    "true_proofs.csv",
    "verified_true_certificates.csv",
    "lean_proofs.csv",
    "proof_motifs.csv",
    "lemma_candidates.csv",
    "lean_artifacts.csv",
    "true_implication_certificates.csv",
)


def discover_true_proof_artifacts(base_dir: str | Path) -> list[dict[str, Any]]:
    directory = Path(base_dir)
    if directory.is_file():
        return [{"path": str(directory), "kind": _kind_for_name(directory.name)}]
    if not directory.exists():
        return []
    found: list[dict[str, Any]] = []
    for path in sorted(directory.iterdir()):
        if path.name in TRUE_PROOF_FILENAMES or any(name.replace(".csv", "") in path.name for name in TRUE_PROOF_FILENAMES):
            if path.suffix.lower() in {".csv", ".jsonl", ".json"}:
                found.append({"path": str(path), "kind": _kind_for_name(path.name)})
    return found


def load_true_proof_rows(path: str | Path, limit: int | None = None) -> list[dict[str, Any]]:
    source = Path(path)
    rows: list[dict[str, Any]] = []
    if source.suffix.lower() == ".jsonl":
        with source.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    rows.append(normalize_true_proof_row(json.loads(line)))
                    if limit is not None and len(rows) >= limit:
                        break
    elif source.suffix.lower() == ".json":
        payload = json.loads(source.read_text(encoding="utf-8"))
        raw_rows = payload if isinstance(payload, list) else payload.get("rows", [])
        for row in raw_rows[:limit]:
            rows.append(normalize_true_proof_row(row))
    else:
        with source.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                rows.append(normalize_true_proof_row(row))
                if limit is not None and len(rows) >= limit:
                    break
    return rows


def normalize_true_proof_row(row: dict[str, Any]) -> dict[str, Any]:
    data = dict(row)
    source_idx = _pick(data, "source_idx", "eq1_idx", "source_id", "premise_idx")
    target_idx = _pick(data, "target_idx", "eq2_idx", "target_id", "conclusion_idx")
    proof_route = _pick(data, "proof_route", "route_name", "route", "compiled_route")
    theorem_name = _pick(data, "theorem_name", "lean_theorem", "proof_id")
    claim_id = _pick(data, "claim_id", "claim_hash") or (
        f"{source_idx}->{target_idx}" if source_idx not in (None, "") and target_idx not in (None, "") else None
    )
    normalized = {
        **data,
        "source_idx": _int_or_original(source_idx),
        "target_idx": _int_or_original(target_idx),
        "source": _pick(data, "source", "source_equation", "eq1"),
        "target": _pick(data, "target", "target_equation", "eq2"),
        "claim_id": claim_id,
        "proof_route": proof_route,
        "route_name": proof_route,
        "proof_motif": _pick(data, "proof_motif", "motif_kind"),
        "source_basin": _pick(data, "source_basin", "source_shape"),
        "target_basin": _pick(data, "target_basin", "target_shape"),
        "trust_level": _pick(data, "trust_level") or "ADVISORY_ROUTE",
        "provenance_type": _pick(data, "provenance_type") or "IMPORTED",
        "verification_status": _pick(data, "verification_status", "lean_status") or "UNKNOWN",
        "theorem_name": theorem_name,
        "lean_file": _pick(data, "lean_file", "source_file"),
        "proof_text": _pick(data, "proof_text", "lean_proof"),
    }
    return normalized


def import_true_proof_artifacts_to_store(store: Any, path_or_dir: str | Path, limit: int | None = None) -> dict[str, Any]:
    artifacts = discover_true_proof_artifacts(path_or_dir)
    if not artifacts and Path(path_or_dir).is_file():
        artifacts = [{"path": str(path_or_dir), "kind": _kind_for_name(Path(path_or_dir).name)}]
    all_rows: list[dict[str, Any]] = []
    imported = {"files": artifacts, "row_count": 0, "proof_motifs": 0, "lemma_candidates": 0, "lean_artifacts": 0}
    for artifact in artifacts:
        rows = load_true_proof_rows(artifact["path"], limit=limit)
        all_rows.extend(rows)
        for row in rows:
            lean_artifact = _lean_artifact_from_row(row)
            if lean_artifact and hasattr(store, "add_lean_artifact"):
                store.add_lean_artifact(lean_artifact)
                imported["lean_artifacts"] += 1
        if hasattr(store, "record_artifact_import"):
            store.record_artifact_import(artifact["path"], f"true_proof_{artifact['kind']}", len(rows))
    if all_rows:
        atlas = build_proof_atlas_from_true_rows(all_rows, domain_kernel_id="etp_magma")
        if hasattr(store, "add_proof_motif"):
            for motif in atlas.proof_motifs:
                store.add_proof_motif(motif)
            imported["proof_motifs"] = len(atlas.proof_motifs)
        if hasattr(store, "add_lemma_candidate"):
            for candidate in atlas.lemma_candidates:
                store.add_lemma_candidate(candidate)
            imported["lemma_candidates"] = len(atlas.lemma_candidates)
        if hasattr(store, "add_proof_atlas"):
            store.add_proof_atlas(atlas)
    imported["row_count"] = len(all_rows)
    return imported


def _lean_artifact_from_row(row: dict[str, Any]) -> LeanArtifact | None:
    name = row.get("theorem_name")
    if not name and not row.get("proof_text") and not row.get("lean_file"):
        return None
    verification = row.get("verification_status") or "IMPORTED_UNCHECKED"
    trust = row.get("trust_level") or ("LEAN_VERIFIED" if verification == "LEAN_VERIFIED" else "ADVISORY_ROUTE")
    artifact_id = make_lean_artifact_id(str(name or row.get("claim_id") or "lean_artifact"), LeanArtifactKind.THEOREM_STATEMENT.value)
    return LeanArtifact(
        lean_artifact_id=artifact_id,
        artifact_kind=LeanArtifactKind.COMPLETE_PROOF if row.get("proof_text") else LeanArtifactKind.THEOREM_STATEMENT,
        name=str(name or artifact_id),
        domain_kernel_id="etp_magma",
        theorem_name=name,
        statement=row.get("target") or row.get("claim_id"),
        proof_text=row.get("proof_text"),
        verification_status=verification if verification in LeanVerificationStatus.__members__ else "IMPORTED_UNCHECKED",
        trust_level=trust,
        provenance_type=row.get("provenance_type") or "IMPORTED",
        source_file=row.get("lean_file"),
        payload={"source_idx": row.get("source_idx"), "target_idx": row.get("target_idx")},
    )


def _kind_for_name(name: str) -> str:
    lower = name.lower()
    if "lemma" in lower:
        return "lemma_candidates"
    if "motif" in lower:
        return "proof_motifs"
    if "lean" in lower:
        return "lean_artifacts"
    return "true_proofs"


def _pick(data: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = data.get(key)
        if value not in (None, ""):
            return value
    return None


def _int_or_original(value: Any) -> Any:
    try:
        return int(value)
    except (TypeError, ValueError):
        return value
