"""Replay checks for MathGraph evidence manifests."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mathgraph.certificates import TerminalForm
from mathgraph.evidence_manifest import EvidenceManifest
from mathgraph.finite_magma_world import check_finite_countermodel
from mathgraph.hashing import sha256_hex
from mathgraph.invariants import check_unsafe_artifact_rejected


@dataclass(frozen=True)
class EvidenceReplayResult:
    ok: bool
    manifest_path: str = ""
    terminal_form: str = ""
    checked_artifacts: tuple[str, ...] = ()
    failures: tuple[str, ...] = ()
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "manifest_path": self.manifest_path,
            "terminal_form": self.terminal_form,
            "checked_artifacts": list(self.checked_artifacts),
            "failures": list(self.failures),
            "details": dict(self.details),
        }


def load_evidence_manifest(path: str | Path) -> EvidenceManifest:
    return EvidenceManifest.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def replay_evidence_manifest(path: str | Path, *, expected_terminal_form: TerminalForm | str | None = None) -> EvidenceReplayResult:
    manifest_path = Path(path)
    failures: list[str] = []
    checked: list[str] = []
    details: dict[str, Any] = {}
    try:
        manifest = load_evidence_manifest(manifest_path)
    except Exception as exc:
        return EvidenceReplayResult(False, str(manifest_path), failures=(f"manifest_invalid:{exc}",))

    if expected_terminal_form is not None and manifest.terminal_form != _terminal(expected_terminal_form):
        failures.append("terminal_form_mismatch")

    base_dir = manifest_path.parent
    for artifact_path, expected_hash in zip(manifest.artifact_paths, manifest.artifact_hashes):
        p = Path(artifact_path)
        if not p.is_absolute():
            p = base_dir / p
        if not p.exists():
            failures.append(f"artifact_missing:{artifact_path}")
            continue
        text = p.read_text(encoding="utf-8")
        checked.append(str(p))
        unsafe_report = check_unsafe_artifact_rejected({"artifact_text": text})
        if not unsafe_report.ok:
            failures.append("unsafe_artifact")
        actual_hash = _artifact_hash(text)
        if actual_hash != expected_hash:
            failures.append(f"artifact_hash_mismatch:{artifact_path}")

    if manifest.terminal_form == TerminalForm.FINITE_COUNTERMODEL:
        claim = dict(manifest.claim_data or {})
        required = ("source_equation", "target_equation", "table")
        if not all(key in claim for key in required):
            failures.append("finite_countermodel_claim_data_missing")
        else:
            result = check_finite_countermodel(claim["source_equation"], claim["target_equation"], claim["table"])
            details["finite_countermodel"] = result.to_dict()
            if not result.terminal_candidate_ok:
                failures.append("finite_countermodel_replay_failed")
            if dict(result.witness_env) != dict(manifest.witness or {}):
                failures.append("finite_countermodel_witness_mismatch")
    elif manifest.terminal_form == TerminalForm.VERIFIED_PROOF:
        if not manifest.theorem_name:
            failures.append("proof_theorem_missing")
    elif manifest.terminal_form == TerminalForm.NAMED_OBSTRUCTION:
        if not manifest.obstruction_id:
            failures.append("obstruction_id_missing")

    return EvidenceReplayResult(
        ok=not failures,
        manifest_path=str(manifest_path),
        terminal_form=manifest.terminal_form.value,
        checked_artifacts=tuple(checked),
        failures=tuple(failures),
        details=details,
    )


def _terminal(value: TerminalForm | str) -> TerminalForm:
    return value if isinstance(value, TerminalForm) else TerminalForm(str(value))


def _artifact_hash(text: str) -> str:
    try:
        return sha256_hex(json.loads(text))
    except Exception:
        return sha256_hex(text)
