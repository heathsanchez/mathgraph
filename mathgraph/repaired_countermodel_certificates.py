"""Assimilate source-law repaired recoveries into finite countermodel records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd

from mathgraph.persistent_exact_microbasin_lawbook import write_persistent_lawbook_sqlite


@dataclass(frozen=True)
class RepairedCountermodelCertificate:
    certificate_id: str
    pair_id: Any
    source_eq_idx: int
    target_eq_idx: int
    source_equation: str
    target_equation: str
    carrier_size: int
    table: list[list[int]]
    table_hash: str
    witness: dict[str, int]
    repair_id: str
    constructor_id: str
    repaired_constructor_id: str
    source_family: str
    repair_strategy: str
    source_violations_before: int
    source_violations_after: int
    target_violation_preserved: bool
    eq1_holds: bool
    eq2_violated: bool
    finite_checked: bool
    terminal_form: str
    trust_level: str
    advisory_only: bool
    can_promote_truth: bool
    provenance: dict[str, Any]
    microbasin_key: str
    basin: str
    deep_ir_candidate: str
    created_at: str


@dataclass(frozen=True)
class RepairedCertificateManifest:
    run_id: str
    source_mode: str
    input_dir: str
    certificate_count: int
    unique_pair_count: int
    unique_table_count: int
    family_count: int
    repair_strategy_count: int
    safety_true_contamination_count: int
    safety_advisory_promotion_count: int
    safety_failed_search_true_count: int
    output_dir: str
    created_at: str


@dataclass(frozen=True)
class RepairedCertificateAdmissionResult:
    admitted_count: int
    rejected_count: int
    duplicate_count: int
    unsafe_count: int
    reason_counts: dict[str, int]
    lawbook_path: str
    manifest_path: str


@dataclass(frozen=True)
class RepairedCertificateFamilySummary:
    source_family: str
    repair_strategy: str
    microbasin_key: str
    certificate_count: int
    unique_pair_count: int
    unique_table_count: int
    mean_source_violations_before: float
    mean_source_violations_after: float
    representative_certificate_id: str
    advisory_only: bool
    can_promote_truth: bool


def load_source_law_repair_outputs(input_dir: str | Path) -> dict[str, pd.DataFrame]:
    root = Path(input_dir)
    return {
        "repair_results": _read_csv(root / "source_law_repair_results.csv"),
        "repair_traces": _read_csv(root / "source_law_repair_traces.csv"),
        "pair_specs": _read_csv(root / "residual_conditioned_pair_specs.csv"),
        "constructors": _read_csv(root / "residual_conditioned_constructors.csv"),
        "conditioned_recoveries": _read_csv(root / "residual_conditioned_recoveries.csv"),
        "pair_features": _read_csv(root / "heldout_pair_features.csv"),
        "recovery_eval": _read_csv(root / "heldout_recovery_eval.csv"),
    }


def build_repaired_countermodel_certificates(
    input_dir: str | Path,
    equations: list[str] | None = None,
    source_mode: str | None = None,
    run_id: str | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    outputs = load_source_law_repair_outputs(input_dir)
    results = outputs["repair_results"]
    traces = outputs["repair_traces"]
    specs = outputs["pair_specs"]
    constructors = outputs["constructors"]
    now = datetime.now(timezone.utc).isoformat()
    run_id = run_id or f"repaired-cert:{_hash_text(str(input_dir))[:12]}"
    source_mode = source_mode or _source_mode(input_dir)
    spec_by_pair = {str(row.get("pair_id", "")): row for _, row in specs.iterrows()} if not specs.empty else {}
    constructor_by_id = {str(row.get("constructor_id", "")): row for _, row in constructors.iterrows()} if not constructors.empty else {}
    trace_by_repair = {str(row.get("repair_id", "")): row for _, row in traces.iterrows()} if not traces.empty else {}
    cert_rows: list[dict[str, Any]] = []
    reject_rows: list[dict[str, Any]] = []
    for idx, row in results.iterrows():
        trace = _coerce_mapping(row.get("trace", {})) or dict(trace_by_repair.get(str(row.get("repair_id", "")), {}))
        pair_id = row.get("pair_id", idx)
        spec = spec_by_pair.get(str(pair_id), {})
        constructor = constructor_by_id.get(str(row.get("constructor_id", "")), {})
        accepted, reason = _is_accepted(row, trace)
        common = _common_fields(row, trace, spec, constructor, equations or [], source_mode, run_id, now)
        if accepted:
            cert_rows.append(common)
        else:
            reject = {
                **common,
                "terminal_form": "NONE",
                "trust_level": "REJECTED",
                "advisory_only": True,
                "can_promote_truth": False,
                "rejection_reason": reason,
            }
            reject_rows.append(reject)
    return pd.DataFrame(cert_rows), pd.DataFrame(reject_rows)


def deduplicate_repaired_certificates(certificates: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    if certificates.empty:
        return certificates.copy(), pd.DataFrame()
    dedupe = certificates.copy()
    dedupe["_witness_hash"] = dedupe["witness"].map(lambda value: _hash_obj(_coerce_mapping(value)))
    keys = ["source_eq_idx", "target_eq_idx", "table_hash", "_witness_hash"]
    duplicate_mask = dedupe.duplicated(keys, keep="first")
    duplicates = dedupe[duplicate_mask].drop(columns=["_witness_hash"], errors="ignore").copy()
    unique = dedupe[~duplicate_mask].drop(columns=["_witness_hash"], errors="ignore").copy()
    return unique.reset_index(drop=True), duplicates.reset_index(drop=True)


def summarize_repaired_certificate_families(certificates: pd.DataFrame) -> pd.DataFrame:
    if certificates.empty:
        return pd.DataFrame(columns=[field for field in RepairedCertificateFamilySummary.__dataclass_fields__])
    rows: list[dict[str, Any]] = []
    grouped = certificates.groupby(["source_family", "repair_strategy", "microbasin_key", "basin", "deep_ir_candidate"], dropna=False)
    for keys, group in grouped:
        source_family, repair_strategy, microbasin_key, _basin, _deep = keys
        rows.append(
            RepairedCertificateFamilySummary(
                source_family=str(source_family),
                repair_strategy=str(repair_strategy),
                microbasin_key=str(microbasin_key),
                certificate_count=int(len(group)),
                unique_pair_count=int(group["pair_id"].nunique()),
                unique_table_count=int(group["table_hash"].nunique()),
                mean_source_violations_before=float(pd.to_numeric(group["source_violations_before"], errors="coerce").fillna(0).mean()),
                mean_source_violations_after=float(pd.to_numeric(group["source_violations_after"], errors="coerce").fillna(0).mean()),
                representative_certificate_id=str(group["certificate_id"].iloc[0]),
                advisory_only=True,
                can_promote_truth=False,
            ).__dict__
        )
    return pd.DataFrame(rows)


def write_repaired_certificate_lawbook(
    certificates: pd.DataFrame,
    rejected: pd.DataFrame,
    family_summary: pd.DataFrame,
    out_dir: str | Path,
    manifest_metadata: dict[str, Any] | None = None,
) -> dict[str, str]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    unique, duplicates = deduplicate_repaired_certificates(certificates)
    boundary = validate_repaired_certificate_boundary(unique, rejected)
    metadata = dict(manifest_metadata or {})
    created_at = datetime.now(timezone.utc).isoformat()
    manifest = RepairedCertificateManifest(
        run_id=str(metadata.get("run_id", f"repaired-cert:{_hash_text(str(out))[:12]}")),
        source_mode=str(metadata.get("source_mode", "")),
        input_dir=str(metadata.get("input_dir", "")),
        certificate_count=int(len(unique)),
        unique_pair_count=int(unique["pair_id"].nunique()) if not unique.empty and "pair_id" in unique else 0,
        unique_table_count=int(unique["table_hash"].nunique()) if not unique.empty and "table_hash" in unique else 0,
        family_count=int(unique["source_family"].nunique()) if not unique.empty and "source_family" in unique else 0,
        repair_strategy_count=int(unique["repair_strategy"].nunique()) if not unique.empty and "repair_strategy" in unique else 0,
        safety_true_contamination_count=int(boundary["safety_true_contamination_count"]),
        safety_advisory_promotion_count=int(boundary["safety_advisory_promotion_count"]),
        safety_failed_search_true_count=int(boundary["safety_failed_search_true_count"]),
        output_dir=str(out),
        created_at=created_at,
    )
    paths = {
        "repaired_countermodel_certificates.csv": out / "repaired_countermodel_certificates.csv",
        "repaired_countermodel_rejected.csv": out / "repaired_countermodel_rejected.csv",
        "repaired_countermodel_family_summary.csv": out / "repaired_countermodel_family_summary.csv",
        "repaired_countermodel_manifest.json": out / "repaired_countermodel_manifest.json",
        "repaired_countermodel_lawbook.sqlite": out / "repaired_countermodel_lawbook.sqlite",
        "repaired_countermodel_report.md": out / "repaired_countermodel_report.md",
        "artifact_manifest.json": out / "artifact_manifest.json",
    }
    _write_csv(paths["repaired_countermodel_certificates.csv"], unique)
    _write_csv(paths["repaired_countermodel_rejected.csv"], rejected)
    _write_csv(paths["repaired_countermodel_family_summary.csv"], family_summary)
    manifest_dict = manifest.__dict__ | {
        "duplicate_count": int(len(duplicates)),
        "rejected_count": int(len(rejected)),
        "finite_verified_count": int(len(unique)),
        "advisory_rejected_count": int(len(rejected)),
        "breakthrough_certificate_count": int(len(unique)),
        **boundary,
    }
    paths["repaired_countermodel_manifest.json"].write_text(json.dumps(manifest_dict, indent=2, sort_keys=True, default=str), encoding="utf-8")
    write_persistent_lawbook_sqlite(
        paths["repaired_countermodel_lawbook.sqlite"],
        {
            "repaired_countermodel_certificates": _json_safe_frame(unique),
            "repaired_countermodel_rejected": _json_safe_frame(rejected),
            "repaired_countermodel_family_summary": _json_safe_frame(family_summary),
            "manifest": pd.DataFrame([manifest_dict]),
        },
    )
    paths["repaired_countermodel_report.md"].write_text(_report(manifest_dict), encoding="utf-8")
    paths["artifact_manifest.json"].write_text(
        json.dumps([{"artifact_name": key, "path": str(path), "exists": path.exists()} for key, path in paths.items() if key != "artifact_manifest.json"], indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    return {key: str(path) for key, path in paths.items()}


def validate_repaired_certificate_boundary(certificates: pd.DataFrame, rejected: pd.DataFrame) -> dict[str, Any]:
    unsafe_accepted = 0
    if not certificates.empty:
        required = ["finite_checked", "eq1_holds", "eq2_violated"]
        for col in required:
            if col not in certificates:
                unsafe_accepted += len(certificates)
                break
        else:
            unsafe_accepted = int((~(certificates["finite_checked"].map(_as_bool) & certificates["eq1_holds"].map(_as_bool) & certificates["eq2_violated"].map(_as_bool))).sum())
    advisory_promotion = int((rejected.get("can_promote_truth", pd.Series(dtype=bool)).map(_as_bool)).sum()) if not rejected.empty else 0
    failed_true = int((rejected.get("terminal_form", pd.Series(dtype=str)).astype(str) == "VERIFIED_PROOF").sum()) if not rejected.empty else 0
    true_contam = int(certificates.get("true_contamination_count", pd.Series(dtype=int)).fillna(0).astype(int).sum()) if "true_contamination_count" in certificates else 0
    return {
        "unsafe_accepted_count": unsafe_accepted,
        "safety_true_contamination_count": true_contam,
        "safety_advisory_promotion_count": advisory_promotion,
        "safety_failed_search_true_count": failed_true,
        "boundary_preserved": bool(unsafe_accepted == 0 and advisory_promotion == 0 and failed_true == 0 and true_contam == 0),
    }


def _common_fields(row: pd.Series, trace: dict[str, Any], spec: Any, constructor: Any, equations: list[str], source_mode: str, run_id: str, created_at: str) -> dict[str, Any]:
    pair_id = row.get("pair_id", "")
    source_eq = str(row.get("source_equation", "") or constructor.get("source_equation", ""))
    target_eq = str(row.get("target_equation", "") or constructor.get("target_equation", ""))
    source_idx = _int_or_default(spec.get("source_eq_idx", -1), -1)
    target_idx = _int_or_default(spec.get("target_eq_idx", -1), -1)
    if source_idx < 0 and source_eq in equations:
        source_idx = equations.index(source_eq)
    if target_idx < 0 and target_eq in equations:
        target_idx = equations.index(target_eq)
    table = _coerce_table(row.get("repaired_table", []))
    witness = _coerce_mapping(row.get("witness", {}))
    repair_id = str(row.get("repair_id", trace.get("repair_id", "")))
    strategy = str(trace.get("repair_id", repair_id)).split(":")[-1] if trace else ""
    table_hash = str(row.get("repaired_table_hash", ""))
    cert_id = "repaired-countermodel:" + _hash_obj({"pair": pair_id, "table_hash": table_hash, "witness": witness, "repair_id": repair_id})[:24]
    return RepairedCountermodelCertificate(
        certificate_id=cert_id,
        pair_id=pair_id,
        source_eq_idx=source_idx,
        target_eq_idx=target_idx,
        source_equation=source_eq,
        target_equation=target_eq,
        carrier_size=_int_or_default(row.get("n", 0), 0),
        table=table,
        table_hash=table_hash,
        witness=witness,
        repair_id=repair_id,
        constructor_id=str(row.get("constructor_id", "")),
        repaired_constructor_id=str(row.get("repaired_constructor_id", row.get("constructor_id", ""))),
        source_family=str(row.get("family", "")),
        repair_strategy=strategy,
        source_violations_before=_int_or_default(trace.get("started_source_violations", 0), 0),
        source_violations_after=_int_or_default(trace.get("final_source_violations", 0), 0),
        target_violation_preserved=_as_bool(trace.get("target_violation_preserved", False)),
        eq1_holds=_as_bool(row.get("eq1_holds", False)),
        eq2_violated=_as_bool(row.get("eq2_violated", False)),
        finite_checked=_as_bool(row.get("finite_checked", False)),
        terminal_form="FINITE_COUNTERMODEL",
        trust_level="FINITE_VERIFIED",
        advisory_only=False,
        can_promote_truth=True,
        provenance={"run_id": run_id, "source_mode": source_mode, "repair_trace": trace},
        microbasin_key=str(spec.get("microbasin_key", "")),
        basin=str(spec.get("basin", "")),
        deep_ir_candidate=str(spec.get("deep_ir_candidate", "")),
        created_at=created_at,
    ).__dict__


def _is_accepted(row: pd.Series, trace: dict[str, Any]) -> tuple[bool, str]:
    checks = {
        "finite_checked": _as_bool(row.get("finite_checked", False)),
        "recovered": _as_bool(row.get("recovered", False)),
        "eq1_holds": _as_bool(row.get("eq1_holds", False)),
        "eq2_violated": _as_bool(row.get("eq2_violated", False)),
        "target_violation_preserved": _as_bool(trace.get("target_violation_preserved", False)),
    }
    for key, ok in checks.items():
        if not ok:
            return False, f"missing_{key}"
    return True, "accepted"


def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def _write_csv(path: Path, frame: pd.DataFrame) -> None:
    if frame.empty and len(frame.columns) == 0:
        pd.DataFrame([{"empty": True}]).to_csv(path, index=False)
        return
    safe = frame.copy()
    for col in safe.columns:
        safe[col] = safe[col].map(lambda value: json.dumps(value, sort_keys=True, default=str) if isinstance(value, (dict, list, tuple)) else value)
    safe.to_csv(path, index=False)


def _json_safe_frame(frame: pd.DataFrame) -> pd.DataFrame:
    safe = frame.copy()
    for col in safe.columns:
        safe[col] = safe[col].map(lambda value: json.dumps(value, sort_keys=True, default=str) if isinstance(value, (dict, list, tuple)) else value)
    return safe


def _report(manifest: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Repaired Countermodel Certificates v1",
            "",
            f"- certificate_count: {manifest.get('certificate_count', 0)}",
            f"- unique_pair_count: {manifest.get('unique_pair_count', 0)}",
            f"- unique_table_count: {manifest.get('unique_table_count', 0)}",
            f"- family_count: {manifest.get('family_count', 0)}",
            f"- safety_advisory_promotion_count: {manifest.get('safety_advisory_promotion_count', 0)}",
            "",
            "Only finite-checked source-holds/target-violates repaired tables are admitted as finite countermodel certificates.",
            "",
        ]
    )


def _source_mode(input_dir: str | Path) -> str:
    summary = Path(input_dir) / "active_discovery_summary.json"
    if summary.exists():
        try:
            return str(json.loads(summary.read_text(encoding="utf-8")).get("source_mode", ""))
        except json.JSONDecodeError:
            return ""
    return ""


def _coerce_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, str) and value:
        try:
            parsed = json.loads(value)
            return dict(parsed) if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def _coerce_table(value: Any) -> list[list[int]]:
    if isinstance(value, str) and value:
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return []
    if isinstance(value, (list, tuple)):
        return [[int(x) for x in row] for row in value]
    return []


def _hash_obj(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _as_bool(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _int_or_default(value: Any, default: int) -> int:
    try:
        if pd.isna(value):
            return default
        return int(value)
    except (TypeError, ValueError):
        return default
