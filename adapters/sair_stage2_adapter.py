"""Import helpers for external SAIR Stage 2 / ETP result tables."""

from __future__ import annotations

import csv
import gzip
from collections import Counter
from pathlib import Path
from typing import Any

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


def row_to_trace(record: dict[str, Any]) -> Trace:
    source = _first_present(record, ["source_equation", "source"])
    target = _first_present(record, ["target_equation", "target"])
    claim = _claim(record, source, target)
    routes_tried = [_route(record)] if _route(record) else []
    metadata = _metadata(record)

    if _is_verified_false(record):
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
            "countermodel": _first_present(
                record,
                [
                    "countermodel_v19_1",
                    "countermodel",
                    "countermodel_json",
                    "model",
                    "finite_model",
                    "witness",
                ],
            ),
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


def record_to_trace(record: dict[str, Any]) -> Trace:
    return row_to_trace(record)


def import_traces(path: str | Path, limit: int | None = None) -> list[Trace]:
    records = load_result_table(path)
    if limit is not None:
        records = records[:limit]
    return [record_to_trace(record) for record in records]


def import_results(path: str | Path, limit: int | None = None) -> dict[str, Any]:
    records = load_result_table(path)
    if limit is not None:
        records = records[:limit]
    traces = [row_to_trace(record) for record in records]
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
    ]
    return {field: record[field] for field in fields if field in record and record[field] not in (None, "")}


def _to_optional_str(value: Any) -> str | None:
    return str(value) if value is not None else None
