"""Certificate lawbook: compact memory over imported MathGraph traces."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from mathgraph.certificates import TerminalForm, VerificationStatus
from mathgraph.ledger import JsonlLedger
from mathgraph.trace import Trace


class CertificateLawbook:
    """In-memory query/explain layer for terminal certificate traces."""

    def __init__(self, traces: Iterable[Trace | dict[str, Any]] = ()) -> None:
        self.traces = [_coerce_trace(trace) for trace in traces]
        self._claim_index: dict[str, list[Trace]] = defaultdict(list)
        self._pair_index: dict[tuple[str, str], list[Trace]] = defaultdict(list)
        self._source_index: dict[str, list[Trace]] = defaultdict(list)
        self._target_index: dict[str, list[Trace]] = defaultdict(list)
        self._terminal_index: dict[str, list[Trace]] = defaultdict(list)
        self._status_index: dict[str, list[Trace]] = defaultdict(list)
        self._route_index: dict[str, list[Trace]] = defaultdict(list)
        self._build_indexes()

    @classmethod
    def from_traces(cls, traces: Iterable[Trace | dict[str, Any]]) -> "CertificateLawbook":
        return cls(traces)

    @classmethod
    def from_json(cls, path: str | Path) -> "CertificateLawbook":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if isinstance(data, dict):
            traces = data.get("traces", data.get("items", []))
        else:
            traces = data
        if not isinstance(traces, list):
            raise ValueError("lawbook JSON must contain a list of traces")
        return cls(traces)

    @classmethod
    def from_jsonl(cls, path: str | Path) -> "CertificateLawbook":
        return cls(JsonlLedger(path).iter_traces())

    def summary(self) -> dict[str, Any]:
        terminal_counts = self._counts(trace.terminal_form.value for trace in self.traces)
        status_counts = self._counts(trace.verification_status.value for trace in self.traces)
        malformed_count = sum(1 for trace in self.traces if _malformed(trace))
        claim_counts = Counter(trace.claim for trace in self.traces)
        duplicate_claim_count = sum(1 for count in claim_counts.values() if count > 1)
        return {
            "trace_count": len(self.traces),
            "terminal_form_counts": terminal_counts,
            "verification_status_counts": status_counts,
            "route_counts": self._route_counts(),
            "source_count": len(self._source_index),
            "target_count": len(self._target_index),
            "pair_count": len(self._pair_index),
            "promotable_count": terminal_counts.get(TerminalForm.VERIFIED_PROOF.value, 0)
            + terminal_counts.get(TerminalForm.FINITE_COUNTERMODEL.value, 0),
            "obstruction_count": terminal_counts.get(TerminalForm.NAMED_OBSTRUCTION.value, 0),
            "countermodel_count": terminal_counts.get(TerminalForm.FINITE_COUNTERMODEL.value, 0),
            "verified_proof_count": terminal_counts.get(TerminalForm.VERIFIED_PROOF.value, 0),
            "malformed_count": malformed_count,
            "duplicate_claim_count": duplicate_claim_count,
        }

    def route_summary(self) -> dict[str, dict[str, Any]]:
        summary: dict[str, dict[str, Any]] = {}
        for route, traces in sorted(self._route_index.items()):
            summary[route] = {
                "count": len(traces),
                "terminal_form_counts": self._counts(trace.terminal_form.value for trace in traces),
                "verification_status_counts": self._counts(
                    trace.verification_status.value for trace in traces
                ),
                "source_count": len({_trace_value(trace, "source_idx") for trace in traces if _trace_value(trace, "source_idx") is not None}),
                "target_count": len({_trace_value(trace, "target_idx") for trace in traces if _trace_value(trace, "target_idx") is not None}),
                "sample_claims": [trace.claim for trace in traces[:5]],
            }
        return summary

    def source_summary(self, source_idx: str | int) -> dict[str, Any]:
        traces = self._source_index.get(str(source_idx), [])
        return self._endpoint_summary("source_idx", source_idx, traces)

    def target_summary(self, target_idx: str | int) -> dict[str, Any]:
        traces = self._target_index.get(str(target_idx), [])
        return self._endpoint_summary("target_idx", target_idx, traces)

    def get_by_claim(self, claim: str) -> list[Trace]:
        return list(self._claim_index.get(claim, []))

    def get_by_pair(self, source_idx: str | int, target_idx: str | int) -> list[Trace]:
        return list(self._pair_index.get((str(source_idx), str(target_idx)), []))

    def query(
        self,
        *,
        terminal_form: TerminalForm | str | None = None,
        verification_status: VerificationStatus | str | None = None,
        route: str | None = None,
        source_idx: str | int | None = None,
        target_idx: str | int | None = None,
        limit: int | None = None,
    ) -> list[Trace]:
        terminal = _enum_value(terminal_form)
        status = _enum_value(verification_status)
        results: list[Trace] = []
        for trace in self.traces:
            if terminal is not None and trace.terminal_form.value != terminal:
                continue
            if status is not None and trace.verification_status.value != status:
                continue
            if route is not None and route not in _routes(trace):
                continue
            if source_idx is not None and _trace_value(trace, "source_idx") != str(source_idx):
                continue
            if target_idx is not None and _trace_value(trace, "target_idx") != str(target_idx):
                continue
            results.append(trace)
            if limit is not None and len(results) >= limit:
                break
        return results

    def countermodels(self, limit: int | None = None) -> list[Trace]:
        return self.query(terminal_form=TerminalForm.FINITE_COUNTERMODEL, limit=limit)

    def verified_proofs(self, limit: int | None = None) -> list[Trace]:
        return self.query(terminal_form=TerminalForm.VERIFIED_PROOF, limit=limit)

    def obstructions(self, limit: int | None = None) -> list[Trace]:
        return self.query(terminal_form=TerminalForm.NAMED_OBSTRUCTION, limit=limit)

    def extract_countermodel(self, trace: Trace) -> Any:
        return extract_countermodel(trace)

    def extract_proof_payload(self, trace: Trace) -> Any:
        return extract_proof_payload(trace)

    def explain_trace(self, trace: Trace) -> dict[str, Any]:
        artifacts = _artifact_records(trace)
        hash_values = [
            record.get("sha256_matches")
            for record in artifacts
            if record.get("hash_applicable") is True
        ]
        return {
            "claim": trace.claim,
            "source_idx": _trace_value(trace, "source_idx"),
            "target_idx": _trace_value(trace, "target_idx"),
            "source": trace.source,
            "target": trace.target,
            "terminal_form": trace.terminal_form.value,
            "verification_status": trace.verification_status.value,
            "routes_tried": list(trace.routes_tried),
            "compiled_route": _trace_value(trace, "compiled_route"),
            "lean_status": _trace_value(trace, "lean_status"),
            "promotion_status": _trace_value(trace, "promotion_status"),
            "has_certificate": trace.certificate is not None,
            "has_countermodel": extract_countermodel(trace) is not None,
            "has_proof_payload": extract_proof_payload(trace) is not None,
            "artifact_roles": sorted({str(record.get("role")) for record in artifacts}),
            "hash_status": _hash_status(hash_values),
        }

    def explain_claim(self, claim: str) -> list[dict[str, Any]]:
        return [self.explain_trace(trace) for trace in self.get_by_claim(claim)]

    def explain_pair(self, source_idx: str | int, target_idx: str | int) -> list[dict[str, Any]]:
        return [self.explain_trace(trace) for trace in self.get_by_pair(source_idx, target_idx)]

    def to_summary_dict(self) -> dict[str, Any]:
        return {"summary": self.summary(), "route_summary": self.route_summary()}

    def save_summary(self, path: str | Path) -> None:
        _write_json(path, self.to_summary_dict())

    def save_route_summary(self, path: str | Path) -> None:
        _write_json(path, self.route_summary())

    def _build_indexes(self) -> None:
        for trace in self.traces:
            self._claim_index[trace.claim].append(trace)
            claim_hash = _trace_value(trace, "claim_hash")
            if claim_hash:
                self._claim_index[claim_hash].append(trace)
            source_idx = _trace_value(trace, "source_idx")
            target_idx = _trace_value(trace, "target_idx")
            if source_idx:
                self._source_index[source_idx].append(trace)
            if target_idx:
                self._target_index[target_idx].append(trace)
            if source_idx and target_idx:
                self._pair_index[(source_idx, target_idx)].append(trace)
            self._terminal_index[trace.terminal_form.value].append(trace)
            self._status_index[trace.verification_status.value].append(trace)
            for route in _routes(trace):
                self._route_index[route].append(trace)

    def _route_counts(self) -> dict[str, int]:
        return {route: len(traces) for route, traces in sorted(self._route_index.items())}

    def _endpoint_summary(self, key: str, value: str | int, traces: list[Trace]) -> dict[str, Any]:
        equation_key = "source_equation" if key == "source_idx" else "target_equation"
        peer_key = "target_idx" if key == "source_idx" else "source_idx"
        return {
            key: str(value),
            equation_key: _first_trace_value(traces, equation_key),
            "trace_count": len(traces),
            "terminal_form_counts": self._counts(trace.terminal_form.value for trace in traces),
            "route_counts": self._counts(route for trace in traces for route in _routes(trace)),
            "target_indices" if key == "source_idx" else "source_indices": sorted(
                {
                    peer
                    for trace in traces
                    for peer in [_trace_value(trace, peer_key)]
                    if peer is not None
                }
            ),
            "sample_claims": [trace.claim for trace in traces[:5]],
        }

    @staticmethod
    def _counts(values: Iterable[str]) -> dict[str, int]:
        return dict(Counter(values))


def extract_countermodel(trace: Trace) -> Any:
    payload = trace.certificate.payload if trace.certificate is not None else {}
    model = payload.get("model") if isinstance(payload, dict) else None
    if isinstance(model, dict):
        for key in ("countermodel", "table"):
            if model.get(key) is not None:
                return model[key]
    for key in ("countermodel", "table"):
        if isinstance(payload, dict) and payload.get(key) is not None:
            return payload[key]
    return None


def extract_proof_payload(trace: Trace) -> Any:
    payload = trace.certificate.payload if trace.certificate is not None else None
    if not isinstance(payload, dict):
        return None
    for key in ("proof", "lean"):
        if payload.get(key) is not None:
            return payload[key]
    return payload if trace.terminal_form == TerminalForm.VERIFIED_PROOF else None


def _coerce_trace(trace: Trace | dict[str, Any]) -> Trace:
    if isinstance(trace, Trace):
        return trace
    if isinstance(trace, dict) and isinstance(trace.get("trace"), dict):
        return Trace.from_dict(trace["trace"])
    if isinstance(trace, dict):
        return Trace.from_dict(trace)
    raise TypeError("lawbook traces must be Trace objects or dictionaries")


def _enum_value(value: TerminalForm | VerificationStatus | str | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, (TerminalForm, VerificationStatus)):
        return value.value
    return str(value)


def _routes(trace: Trace) -> list[str]:
    route = _trace_value(trace, "compiled_route")
    if route:
        return [route]
    return [str(route) for route in trace.routes_tried]


def _trace_value(trace: Trace, key: str) -> str | None:
    for payload in _payloads(trace):
        value = _nested_value(payload, key)
        if value is not None:
            return str(value)
    return None


def _nested_value(payload: dict[str, Any], key: str) -> Any:
    if key in payload and payload[key] not in (None, ""):
        return payload[key]
    for nested_key in ("model", "record"):
        nested = payload.get(nested_key)
        if isinstance(nested, dict) and key in nested and nested[key] not in (None, ""):
            return nested[key]
    return None


def _payloads(trace: Trace) -> list[dict[str, Any]]:
    payloads = [trace.metadata]
    if trace.certificate is not None:
        payloads.append(trace.certificate.payload)
    if trace.obstruction is not None:
        payloads.append(trace.obstruction.payload)
    return [payload for payload in payloads if isinstance(payload, dict)]


def _artifact_records(trace: Trace) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str | None]] = set()
    for payload in _payloads(trace):
        artifacts = payload.get("artifacts")
        if not isinstance(artifacts, dict):
            continue
        for value in artifacts.values():
            items = value if isinstance(value, list) else [value]
            for item in items:
                if not isinstance(item, dict):
                    continue
                key = (
                    str(item.get("kind")),
                    str(item.get("role")),
                    str(item.get("source_column")),
                    item.get("path"),
                )
                if key not in seen:
                    seen.add(key)
                    records.append(item)
    return records


def _hash_status(values: list[Any]) -> str | None:
    if not values:
        return None
    if any(value is False for value in values):
        return "mismatch"
    if all(value is True for value in values):
        return "matched"
    return "unknown"


def _first_trace_value(traces: list[Trace], key: str) -> str | None:
    for trace in traces:
        value = _trace_value(trace, key)
        if value is not None:
            return value
    return None


def _malformed(trace: Trace) -> bool:
    if trace.terminal_form in {TerminalForm.VERIFIED_PROOF, TerminalForm.FINITE_COUNTERMODEL}:
        return trace.certificate is None
    if trace.terminal_form == TerminalForm.NAMED_OBSTRUCTION:
        return trace.verification_status == VerificationStatus.VERIFIED
    return True


def _write_json(path: str | Path, payload: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
