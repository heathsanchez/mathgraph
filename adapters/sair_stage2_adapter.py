"""Import helpers for external SAIR Stage 2 / ETP result tables."""

from __future__ import annotations

import csv
import gzip
from collections import Counter
from pathlib import Path
from typing import Any

from mathgraph.artifacts import (
    build_artifact_record,
    extract_countermodel_from_json,
    normalize_external_path,
    read_json_artifact,
)
from mathgraph.certificates import (
    TerminalForm,
    VerificationStatus,
    finite_countermodel,
    named_obstruction,
    verified_proof,
)
from mathgraph.trace import Trace


TRUE_VALUES = {"1", "true", "yes", "y", "t", "verified", "success", "lean_verified"}
FALSE_VALUES = {"0", "false", "no", "n", "f", "failed", "failure", "error"}


def load_result_table(path: str | Path) -> list[dict[str, Any]]:
    file_path = Path(path)
    name = file_path.name.lower()

    if name.endswith(".csv") or name.endswith(".csv.gz"):
        opener = gzip.open if name.endswith(".gz") else open
        with opener(file_path, "rt", encoding="utf-8", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]

    if name.endswith(".parquet"):
        try:
            import pandas as pd
        except ImportError as exc:
            raise ImportError(
                "Loading SAIR Stage 2 parquet results requires pandas and a parquet engine "
                "such as pyarrow. Install optional dependencies or export a CSV."
            ) from exc
        try:
            return pd.read_parquet(file_path).to_dict(orient="records")
        except ImportError as exc:
            raise ImportError(
                "Loading parquet requires a pandas parquet engine such as pyarrow."
            ) from exc

    raise ValueError(f"unsupported results table extension: {file_path}")


def load_results_table(path: str | Path) -> list[dict[str, Any]]:
    return load_result_table(path)


def summarize_results(records: Any) -> dict[str, Any]:
    records = _records_from(records)
    traces = [record_to_trace(record) for record in records]
    terminal_counts = Counter(trace.terminal_form.value for trace in traces)
    verification_counts = _count_present(
        records,
        [
            "verification_status_v19_1",
            "verification_v19_1",
            "verification_status",
            "verification",
        ],
    )
    lean_counts = _count_present(records, ["lean_status_v19_1", "lean_status"])
    promotion_counts = _count_present(records, ["promotion_status_v19_1", "promotion_status"])
    route_counts = _count_present(
        records,
        ["compiled_route_v19_1", "route_name_v19_1", "compiled_route", "route_name"],
    )
    error_counts = _count_present(
        records,
        ["error_class_v19_1", "lean_error_class_v19_1", "error_class", "error", "lean_error_class"],
    )

    verified_true = sum(1 for record in records if _is_verified_true(record))
    verified_false = sum(1 for record in records if _is_verified_false(record))
    failed_total = sum(1 for record in records if _is_failure(record))

    return {
        "row_count": len(records),
        "terminal_form_counts": dict(terminal_counts),
        "verification_status_counts": dict(verification_counts),
        "lean_status_counts": dict(lean_counts),
        "promotion_status_counts": dict(promotion_counts),
        "compiled_route_counts": dict(route_counts),
        "verified_total": verified_true + verified_false,
        "verified_true": verified_true,
        "verified_false": verified_false,
        "failed_total": failed_total,
        "error_class_counts": dict(error_counts),
    }


def row_to_trace(
    record: dict[str, Any],
    *,
    load_artifacts: bool = False,
    artifact_base: str | Path | None = None,
) -> Trace:
    source = _first_present(record, ["source_equation", "source"])
    target = _first_present(record, ["target_equation", "target"])
    claim = _claim(record, source, target)
    routes_tried = [_route(record)] if _route(record) else []
    metadata = _metadata(record)
    artifacts = _artifact_records(record, load_artifacts=load_artifacts, artifact_base=artifact_base)
    if artifacts:
        metadata["artifacts"] = artifacts

    if _is_verified_false(record):
        countermodel = _first_present(
            record,
            [
                "countermodel_v19_1",
                "countermodel",
                "countermodel_json",
                "model",
                "finite_model",
                "witness",
            ],
        )
        countermodel_extraction = "not_attempted"
        if load_artifacts:
            extracted = _extract_countermodel_from_json_artifacts(artifacts)
            if extracted is not None:
                countermodel = extracted
                countermodel_extraction = "found"
            else:
                countermodel_extraction = "not_found"

        model = {
            "source": source,
            "target": target,
            "source_idx": _first_present(record, ["source_idx"]),
            "target_idx": _first_present(record, ["target_idx"]),
            "source_equation": _first_present(record, ["source_equation", "source"]),
            "target_equation": _first_present(record, ["target_equation", "target"]),
            "claim_hash": _first_present(record, ["claim_hash"]),
            "compiled_route": _route(record),
            "original_terminal_form": _first_present(record, ["terminal_form_v19_1", "terminal_form"]),
            "lean_status": _first_present(record, ["lean_status_v19_1", "lean_status"]),
            "promotion_status": _first_present(record, ["promotion_status_v19_1", "promotion_status"]),
            "countermodel_order": _first_present(record, ["countermodel_order", "model_order", "order"]),
            "countermodel_table_idx": _first_present(record, ["countermodel_table_idx", "table_idx"]),
            "countermodel_motif_hash": _first_present(record, ["countermodel_motif_hash", "motif_hash"]),
            "countermodel": countermodel,
            "countermodel_extraction": countermodel_extraction,
            "artifacts": artifacts,
            "record": metadata,
        }
        cert = finite_countermodel(claim, model)
        return Trace(
            claim=claim,
            source=_to_optional_str(source),
            target=_to_optional_str(target),
            routes_tried=routes_tried,
            terminal_form=TerminalForm.FINITE_COUNTERMODEL,
            verification_status=VerificationStatus.REFUTED,
            certificate=cert,
            metadata=metadata,
        )

    if _is_verified_true(record):
        proof_id = str(_first_present(record, ["proof_id", "certificate_id", "claim_hash"]) or "sair_stage2_verified_true")
        cert = verified_proof(claim, proof_id)
        cert_payload = dict(cert.payload)
        cert_payload.update(
            {
                "source_idx": _first_present(record, ["source_idx"]),
                "target_idx": _first_present(record, ["target_idx"]),
                "source_equation": _first_present(record, ["source_equation", "source"]),
                "target_equation": _first_present(record, ["target_equation", "target"]),
                "claim_hash": _first_present(record, ["claim_hash"]),
                "compiled_route": _route(record),
                "original_terminal_form": _first_present(record, ["terminal_form_v19_1", "terminal_form"]),
                "lean_status": _first_present(record, ["lean_status_v19_1", "lean_status"]),
                "promotion_status": _first_present(record, ["promotion_status_v19_1", "promotion_status"]),
                "proof_id": proof_id,
                "artifacts": artifacts,
                "record": metadata,
            }
        )
        cert = type(cert)(
            terminal_form=cert.terminal_form,
            claim=cert.claim,
            payload=cert_payload,
            verifier=cert.verifier,
            external_verification=cert.external_verification,
        )
        return Trace(
            claim=claim,
            source=_to_optional_str(source),
            target=_to_optional_str(target),
            routes_tried=routes_tried,
            terminal_form=TerminalForm.VERIFIED_PROOF,
            verification_status=VerificationStatus.VERIFIED,
            certificate=cert,
            metadata=metadata,
        )

    obstruction = named_obstruction(
        claim,
        "SAIR_STAGE2_RESULT_NOT_PROMOTABLE",
        "Imported record did not explicitly verify true or verify false.",
    )
    obstruction_payload = dict(obstruction.payload)
    obstruction_payload.update({"artifacts": artifacts, "record": metadata})
    obstruction = type(obstruction)(
        terminal_form=obstruction.terminal_form,
        claim=obstruction.claim,
        payload=obstruction_payload,
        verifier=obstruction.verifier,
        external_verification=obstruction.external_verification,
    )
    return Trace(
        claim=claim,
        source=_to_optional_str(source),
        target=_to_optional_str(target),
        routes_tried=routes_tried,
        terminal_form=TerminalForm.NAMED_OBSTRUCTION,
        verification_status=VerificationStatus.OBSTRUCTED,
        obstruction=obstruction,
        metadata=metadata,
    )


def record_to_trace(
    record: dict[str, Any],
    *,
    load_artifacts: bool = False,
    artifact_base: str | Path | None = None,
) -> Trace:
    return row_to_trace(record, load_artifacts=load_artifacts, artifact_base=artifact_base)


def import_traces(
    path: str | Path,
    limit: int | None = None,
    *,
    load_artifacts: bool = False,
    artifact_base: str | Path | None = None,
) -> list[Trace]:
    records = load_result_table(path)
    if limit is not None:
        records = records[:limit]
    return [
        record_to_trace(record, load_artifacts=load_artifacts, artifact_base=artifact_base)
        for record in records
    ]


def import_results(
    path: str | Path,
    limit: int | None = None,
    *,
    load_artifacts: bool = False,
    artifact_base: str | Path | None = None,
) -> dict[str, Any]:
    records = load_result_table(path)
    if limit is not None:
        records = records[:limit]
    traces = [
        row_to_trace(record, load_artifacts=load_artifacts, artifact_base=artifact_base)
        for record in records
    ]
    return {
        "traces": traces,
        "summary": summarize_results(records),
        "validation": validate_imported_traces(traces),
    }


def validate_imported_traces(traces: list[Trace]) -> dict[str, Any]:
    warnings: list[str] = []
    malformed_count = 0
    terminal_counts = Counter(trace.terminal_form.value for trace in traces)
    status_counts = Counter(trace.verification_status.value for trace in traces)

    for index, trace in enumerate(traces):
        if trace.terminal_form == TerminalForm.VERIFIED_PROOF and trace.certificate is None:
            malformed_count += 1
            warnings.append(f"trace {index} verified proof missing certificate")
        if trace.terminal_form == TerminalForm.FINITE_COUNTERMODEL and trace.certificate is None:
            malformed_count += 1
            warnings.append(f"trace {index} finite countermodel missing certificate")
        if trace.terminal_form == TerminalForm.NAMED_OBSTRUCTION and trace.is_verified_proof():
            malformed_count += 1
            warnings.append(f"trace {index} obstruction treated as proof")

    return {
        "total": len(traces),
        "by_terminal_form": dict(terminal_counts),
        "by_verification_status": dict(status_counts),
        "promotable_count": terminal_counts.get(TerminalForm.VERIFIED_PROOF.value, 0)
        + terminal_counts.get(TerminalForm.FINITE_COUNTERMODEL.value, 0),
        "obstruction_count": terminal_counts.get(TerminalForm.NAMED_OBSTRUCTION.value, 0),
        "malformed_count": malformed_count,
        "warnings": warnings,
    }


def _count_present(records: list[dict[str, Any]], fields: list[str]) -> Counter:
    counts: Counter = Counter()
    for record in records:
        value = _first_present(record, fields)
        if value not in (None, ""):
            counts[str(value)] += 1
    return counts


def _records_from(records: Any) -> list[dict[str, Any]]:
    if hasattr(records, "to_dict"):
        return records.to_dict(orient="records")
    return list(records)


def _first_present(record: dict[str, Any], fields: list[str]) -> Any:
    for field in fields:
        value = record.get(field)
        if value not in (None, ""):
            return value
    return None


def _bool_value(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    text = str(value).strip().lower()
    if text in TRUE_VALUES:
        return True
    if text in FALSE_VALUES:
        return False
    return None


def _is_verified_true(record: dict[str, Any]) -> bool:
    promotion = str(_first_present(record, ["promotion_status_v19_1", "promotion_status"]) or "").lower()
    if "lean_verified_true_promotable" in promotion or "lean_verified_true_promoted" in promotion:
        return True
    for field in [
        "verified_true_v19_1",
        "lean_verified_true_v19_1",
        "python_verified_true_v19_1",
        "verified_true",
        "lean_verified_true",
        "python_verified_true",
    ]:
        if _bool_value(record.get(field)) is True:
            return True
    if _bool_value(_first_present(record, ["lean_verified_v19_1", "lean_verified"])) is True and _truth_label(record) == "true":
        return True
    if _bool_value(_first_present(record, ["python_verified_v19_1", "python_verified"])) is True and _truth_label(record) == "true":
        return True
    return False


def _is_verified_false(record: dict[str, Any]) -> bool:
    promotion = str(_first_present(record, ["promotion_status_v19_1", "promotion_status"]) or "").lower()
    if "lean_verified_false_promotable" in promotion or "lean_verified_false_promoted" in promotion:
        return True
    for field in [
        "verified_false_v19_1",
        "lean_verified_false_v19_1",
        "python_verified_false_v19_1",
        "finite_countermodel_v19_1",
        "verified_false",
        "lean_verified_false",
        "python_verified_false",
        "finite_countermodel",
    ]:
        if _bool_value(record.get(field)) is True:
            return True
    if _bool_value(_first_present(record, ["lean_verified_v19_1", "lean_verified"])) is True and _truth_label(record) == "false":
        return True
    if _bool_value(_first_present(record, ["python_verified_v19_1", "python_verified"])) is True and _truth_label(record) == "false":
        return True
    return False


def _is_failure(record: dict[str, Any]) -> bool:
    for field in ["lean_status_v19_1", "verification_status_v19_1", "lean_status", "verification_status", "status"]:
        value = str(record.get(field, "")).strip().lower()
        if "fail" in value or "error" in value:
            return True
    return False


def _truth_label(record: dict[str, Any]) -> str | None:
    value = _first_present(
        record,
        [
            "truth_v19_1",
            "result_v19_1",
            "claim_truth_v19_1",
            "target_truth_v19_1",
            "truth",
            "result",
            "claim_truth",
            "target_truth",
        ],
    )
    if value is None:
        return None
    text = str(value).strip().lower()
    if text in {"true", "proved", "valid"}:
        return "true"
    if text in {"false", "countermodel", "invalid"}:
        return "false"
    return None


def _terminal_form(record: dict[str, Any]) -> TerminalForm | None:
    value = _first_present(record, ["terminal_form_v19_1", "terminal_form"])
    if value is None:
        return None
    try:
        return TerminalForm(str(value))
    except ValueError:
        return None


def _route(record: dict[str, Any]) -> str | None:
    value = _first_present(record, ["compiled_route_v19_1", "route_name_v19_1", "compiled_route", "route_name"])
    return str(value) if value is not None else None


def _claim(record: dict[str, Any], source: Any, target: Any) -> str:
    claim = _first_present(record, ["claim", "claim_hash"])
    if claim:
        return str(claim)
    if source is not None and target is not None:
        return f"{source} => {target}"
    return "sair_stage2_imported_record"


def _metadata(record: dict[str, Any]) -> dict[str, Any]:
    fields = [
        "source_idx",
        "target_idx",
        "claim_hash",
        "json_path",
        "json_sha256",
        "json_path_v19_1_input",
        "json_sha256_v19_1",
        "lean_path",
        "lean_sha256",
        "lean_path_v19_1_input",
        "lean_sha256_v19_1",
        "executed_lean_path_v19_1",
        "lean_path_prior",
        "json_path_prior",
        "countermodel_order",
        "countermodel_table_idx",
        "countermodel_motif_hash",
        "path",
        "file_path",
        "artifact_path",
        "trace_hash",
        "certificate_hash",
        "row_hash",
        "promotion_status_v19_1",
        "promotion_status",
        "compiled_route_v19_1",
        "compiled_route",
        "route_name_v19_1",
        "route_name",
        "lean_status_v19_1",
        "lean_status",
        "verification_status_v19_1",
        "verification_status",
        "error_class_v19_1",
        "lean_error_class",
        "error_class",
        "terminal_form_v19_1",
        "terminal_form",
        "lean_verified_v19_1",
        "lean_verified_true_v19_1",
        "lean_verified_false_v19_1",
        "lean_verified",
        "lean_verified_true",
        "lean_verified_false",
    ]
    return {field: record[field] for field in fields if field in record and record[field] not in (None, "")}


def _to_optional_str(value: Any) -> str | None:
    return str(value) if value is not None else None


def _artifact_records(
    record: dict[str, Any],
    *,
    load_artifacts: bool,
    artifact_base: str | Path | None,
) -> dict[str, list[dict[str, Any]]]:
    json_expected = _first_present(record, ["json_sha256_v19_1", "json_sha256"])
    lean_expected = _first_present(record, ["lean_sha256_v19_1", "lean_sha256"])
    artifacts: dict[str, list[dict[str, Any]]] = {"json": [], "lean": []}

    for path in _unique_paths(record, ["json_path_v19_1_input", "json_path", "json_path_prior"]):
        resolved = _resolve_artifact_path(path, artifact_base)
        artifacts["json"].append(
            _artifact_record(
                resolved,
                expected_sha256=_to_optional_str(json_expected),
                kind="json",
                inspect=load_artifacts,
                load_json=load_artifacts,
            )
        )

    for path in _unique_paths(
        record,
        ["executed_lean_path_v19_1", "lean_path_v19_1_input", "lean_path", "lean_path_prior"],
    ):
        resolved = _resolve_artifact_path(path, artifact_base)
        artifacts["lean"].append(
            _artifact_record(
                resolved,
                expected_sha256=_to_optional_str(lean_expected),
                kind="lean",
                inspect=load_artifacts,
                load_json=False,
            )
        )

    return {kind: records for kind, records in artifacts.items() if records}


def _artifact_record(
    path: str | None,
    *,
    expected_sha256: str | None,
    kind: str,
    inspect: bool,
    load_json: bool,
) -> dict[str, Any]:
    if path is None:
        return {
            "path": None,
            "kind": kind,
            "exists": False,
            "sha256": None,
            "expected_sha256": expected_sha256,
            "sha256_matches": None,
            "load_attempted": load_json,
            "load_ok": False if load_json else None,
            "error": "missing_path",
            "json_preview_keys": [],
        }
    if inspect:
        return build_artifact_record(
            path,
            expected_sha256=expected_sha256,
            kind=kind,
            load_json=load_json,
        )
    return {
        "path": path,
        "kind": kind,
        "exists": None,
        "sha256": None,
        "expected_sha256": expected_sha256,
        "sha256_matches": None,
        "load_attempted": False,
        "load_ok": None,
        "error": None,
        "json_preview_keys": [],
    }


def _unique_paths(record: dict[str, Any], fields: list[str]) -> list[str]:
    seen: set[str] = set()
    paths: list[str] = []
    for field in fields:
        path = normalize_external_path(record.get(field))
        if path is None or path in seen:
            continue
        seen.add(path)
        paths.append(path)
    return paths


def _resolve_artifact_path(path: str | None, artifact_base: str | Path | None) -> str | None:
    normalized = normalize_external_path(path)
    if normalized is None:
        return None
    target = Path(normalized)
    if target.is_absolute() or artifact_base is None:
        return str(target)
    return str(Path(artifact_base) / target)


def _extract_countermodel_from_json_artifacts(
    artifacts: dict[str, list[dict[str, Any]]],
) -> dict[str, Any] | list[Any] | None:
    for artifact in artifacts.get("json", []):
        if not artifact.get("exists"):
            continue
        try:
            data = read_json_artifact(artifact["path"])
        except (FileNotFoundError, ValueError, OSError):
            continue
        extracted = extract_countermodel_from_json(data)
        if extracted is not None:
            return extracted
    return None
