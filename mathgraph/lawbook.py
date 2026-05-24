"""Lawbook memory surfaces for MathGraph.

``CertificateLawbook`` is the older compact query layer over imported traces.
The accepted-entry dataclasses below it model the explicit public-memory
boundary: certificates, digestion, assimilation candidates, projection
candidates, and value scores may recommend memory, but only Lawbook acceptance
creates accepted public memory.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from mathgraph.certificates import TerminalForm, VerificationStatus
from mathgraph.hashing import content_id
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

    @property
    def by_claim(self) -> dict[str, list[Trace]]:
        return dict(self._claim_index)

    @property
    def by_pair(self) -> dict[tuple[str, str], list[Trace]]:
        return dict(self._pair_index)

    @property
    def by_source(self) -> dict[str, list[Trace]]:
        return dict(self._source_index)

    @property
    def by_target(self) -> dict[str, list[Trace]]:
        return dict(self._target_index)

    @property
    def by_route(self) -> dict[str, list[Trace]]:
        return dict(self._route_index)

    def get_by_claim(self, claim_hash: str) -> Trace | None:
        return _first(self._claim_index.get(claim_hash, []))

    def get_by_pair(self, source_idx: str | int, target_idx: str | int) -> Trace | None:
        return _first(self._pair_index.get((str(source_idx), str(target_idx)), []))

    def find_by_source(self, source_idx: str | int, limit: int | None = None) -> list[Trace]:
        return _limited(self._source_index.get(str(source_idx), []), limit)

    def find_by_target(self, target_idx: str | int, limit: int | None = None) -> list[Trace]:
        return _limited(self._target_index.get(str(target_idx), []), limit)

    def find_by_route(self, route: str, limit: int | None = None) -> list[Trace]:
        return _limited(self._route_index.get(route, []), limit)

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

    def explain_trace(self, trace_or_claim: Trace | str) -> dict[str, Any]:
        trace = trace_or_claim if isinstance(trace_or_claim, Trace) else self.get_by_claim(trace_or_claim)
        if trace is None:
            return _not_in_lawbook(str(trace_or_claim))
        artifacts = _artifact_records(trace)
        hash_values = [
            record.get("sha256_matches")
            for record in artifacts
            if record.get("hash_applicable") is True
        ]
        route = _primary_route(trace)
        payload = trace.certificate.payload if trace.certificate is not None else {}
        return {
            "claim": trace.claim,
            "source_idx": _trace_value(trace, "source_idx"),
            "target_idx": _trace_value(trace, "target_idx"),
            "source": trace.source,
            "target": trace.target,
            "terminal_form": trace.terminal_form.value,
            "verification_status": trace.verification_status.value,
            "route": route,
            "routes_tried": list(trace.routes_tried),
            "proof_countermodel_obstruction_kind": _terminal_kind(trace),
            "lean_status": _trace_value(trace, "lean_status"),
            "promotion_status": _trace_value(trace, "promotion_status"),
            "has_certificate": trace.certificate is not None,
            "has_countermodel": extract_countermodel(trace) is not None,
            "has_proof_payload": extract_proof_payload(trace) is not None,
            "artifact_counts": _artifact_counts(artifacts),
            "artifact_roles": sorted({str(record.get("role")) for record in artifacts}),
            "hash_status": _hash_status(hash_values),
            "certificate_payload_keys": sorted(payload.keys()) if isinstance(payload, dict) else [],
        }

    def explain_claim(self, claim: str) -> dict[str, Any]:
        return self.explain_trace(claim)

    def explain_pair(self, source_idx: str | int, target_idx: str | int) -> dict[str, Any]:
        trace = self.get_by_pair(source_idx, target_idx)
        if trace is None:
            return _not_in_lawbook(
                f"{source_idx}->{target_idx}",
                source_idx=str(source_idx),
                target_idx=str(target_idx),
            )
        return self.explain_trace(trace)

    def route_card(self, route: str) -> dict[str, Any]:
        traces = self._route_index.get(route, [])
        return {
            "route": route,
            "count": len(traces),
            "source_count": len(
                {_trace_value(trace, "source_idx") for trace in traces if _trace_value(trace, "source_idx") is not None}
            ),
            "target_count": len(
                {_trace_value(trace, "target_idx") for trace in traces if _trace_value(trace, "target_idx") is not None}
            ),
            "terminal_form_counts": self._counts(trace.terminal_form.value for trace in traces),
            "verification_status_counts": self._counts(
                trace.verification_status.value for trace in traces
            ),
            "sample_claims": [trace.claim for trace in traces[:5]],
            "sample_pairs": [
                {
                    "source_idx": _trace_value(trace, "source_idx"),
                    "target_idx": _trace_value(trace, "target_idx"),
                }
                for trace in traces[:5]
            ],
        }

    def all_route_cards(self) -> dict[str, dict[str, Any]]:
        return {route: self.route_card(route) for route in sorted(self._route_index)}

    def route_instruction(self, route: str, sample_limit: int = 5) -> Any:
        from mathgraph.route_instructor import build_route_instruction

        return build_route_instruction(self, route, sample_limit=sample_limit)

    def all_route_instructions(self, sample_limit: int = 5) -> dict[str, Any]:
        from mathgraph.route_instructor import build_all_route_instructions

        return build_all_route_instructions(self, sample_limit=sample_limit)

    def advise_pair(self, source: str, target: str, max_routes: int = 5) -> Any:
        from mathgraph.pair_advisor import advise_pair

        return advise_pair(self, source, target, max_routes=max_routes)

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


def _primary_route(trace: Trace) -> str | None:
    routes = _routes(trace)
    return routes[0] if routes else None


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


def _first(traces: list[Trace]) -> Trace | None:
    return traces[0] if traces else None


def _limited(traces: list[Trace], limit: int | None) -> list[Trace]:
    return list(traces if limit is None else traces[:limit])


def _terminal_kind(trace: Trace) -> str:
    if trace.terminal_form == TerminalForm.FINITE_COUNTERMODEL:
        return "countermodel"
    if trace.terminal_form == TerminalForm.VERIFIED_PROOF:
        return "proof"
    return "obstruction"


def _artifact_counts(records: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "total": len(records),
        "json": sum(1 for record in records if record.get("kind") == "json"),
        "lean": sum(1 for record in records if record.get("kind") == "lean"),
    }


def _not_in_lawbook(
    claim: str,
    *,
    source_idx: str | None = None,
    target_idx: str | None = None,
) -> dict[str, Any]:
    return {
        "claim": claim,
        "source_idx": source_idx,
        "target_idx": target_idx,
        "source": None,
        "target": None,
        "terminal_form": TerminalForm.NAMED_OBSTRUCTION.value,
        "verification_status": VerificationStatus.OBSTRUCTED.value,
        "route": None,
        "proof_countermodel_obstruction_kind": "not_in_lawbook",
        "detail": "No matching verified terminal trace was found in this lawbook.",
        "has_certificate": False,
        "has_countermodel": False,
        "has_proof_payload": False,
        "artifact_counts": {"total": 0, "json": 0, "lean": 0},
        "artifact_roles": [],
        "hash_status": None,
        "certificate_payload_keys": [],
    }


class LawbookEntryKind(str, Enum):
    VERIFIED_PROOF_ENTRY = "VERIFIED_PROOF_ENTRY"
    FINITE_COUNTERMODEL_ENTRY = "FINITE_COUNTERMODEL_ENTRY"
    NAMED_OBSTRUCTION_ENTRY = "NAMED_OBSTRUCTION_ENTRY"
    DERIVED_CERTIFICATE_ENTRY = "DERIVED_CERTIFICATE_ENTRY"
    DIGESTED_PROOF_ENTRY = "DIGESTED_PROOF_ENTRY"
    CONSTRUCTOR_FAMILY_ENTRY = "CONSTRUCTOR_FAMILY_ENTRY"
    PROJECTION_RULE_ENTRY = "PROJECTION_RULE_ENTRY"
    ROUTE_RULE_ENTRY = "ROUTE_RULE_ENTRY"
    BASIN_DETECTOR_ENTRY = "BASIN_DETECTOR_ENTRY"
    REUSABLE_SCHEMA_ENTRY = "REUSABLE_SCHEMA_ENTRY"
    UNKNOWN = "UNKNOWN"


class LawbookEntryStatus(str, Enum):
    CANDIDATE = "CANDIDATE"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"
    RETIRED = "RETIRED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    INVALID = "INVALID"
    UNKNOWN = "UNKNOWN"


class LawbookAcceptanceBoundary(str, Enum):
    VERIFIED_PROOF = "VERIFIED_PROOF"
    FINITE_COUNTERMODEL = "FINITE_COUNTERMODEL"
    NAMED_OBSTRUCTION = "NAMED_OBSTRUCTION"
    TRUSTED_IMPORT = "TRUSTED_IMPORT"
    CHAIN_AUDIT = "CHAIN_AUDIT"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    DIGESTION_REVIEW = "DIGESTION_REVIEW"
    PROJECTION_REVIEW = "PROJECTION_REVIEW"
    NONE = "NONE"
    UNKNOWN = "UNKNOWN"


class LawbookReviewDecision(str, Enum):
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"
    NEEDS_MORE_EVIDENCE = "NEEDS_MORE_EVIDENCE"
    NEEDS_DIGESTION = "NEEDS_DIGESTION"
    NEEDS_VERIFIER = "NEEDS_VERIFIER"
    NEEDS_PROJECTION_REVIEW = "NEEDS_PROJECTION_REVIEW"
    HOLD_IN_CHORA = "HOLD_IN_CHORA"
    UNKNOWN = "UNKNOWN"


class LawbookStoreStatus(str, Enum):
    EMPTY = "EMPTY"
    LOADED = "LOADED"
    UPDATED = "UPDATED"
    AUDITED = "AUDITED"
    HAS_CRITICALS = "HAS_CRITICALS"
    ADVISORY_ONLY = "ADVISORY_ONLY"


@dataclass
class LawbookEntry:
    entry_id: str
    kind: LawbookEntryKind
    status: LawbookEntryStatus = LawbookEntryStatus.CANDIDATE
    claim_id: str | None = None
    source: str | None = None
    target: str | None = None
    raw: str | None = None
    terminal_form: TerminalForm | None = None
    certificate_id: str | None = None
    verifier_boundary_crossed: bool = False
    acceptance_boundary: LawbookAcceptanceBoundary = LawbookAcceptanceBoundary.NONE
    accepted_at: str | None = None
    accepted_by: str | None = None
    artifact_ids: tuple[str, ...] = ()
    digestion_trace_ids: tuple[str, ...] = ()
    assimilation_candidate_ids: tuple[str, ...] = ()
    projection_rule_ids: tuple[str, ...] = ()
    constructor_family_ids: tuple[str, ...] = ()
    route_rule_ids: tuple[str, ...] = ()
    basin: str | None = None
    conditions: tuple[str, ...] = ()
    failure_boundaries: tuple[str, ...] = ()
    reason_links: tuple[str, ...] = ()
    root_links: tuple[str, ...] = ()
    provenance: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    advisory: bool = False

    def is_candidate(self) -> bool:
        return self.status == LawbookEntryStatus.CANDIDATE

    def is_accepted(self) -> bool:
        return self.status == LawbookEntryStatus.ACCEPTED

    def is_truth_entry(self) -> bool:
        return self.kind in {
            LawbookEntryKind.VERIFIED_PROOF_ENTRY,
            LawbookEntryKind.FINITE_COUNTERMODEL_ENTRY,
            LawbookEntryKind.DERIVED_CERTIFICATE_ENTRY,
        }

    def is_projection_entry(self) -> bool:
        return self.kind == LawbookEntryKind.PROJECTION_RULE_ENTRY

    def has_valid_truth_boundary(self) -> bool:
        return (
            self.terminal_form is not None
            and bool(self.certificate_id)
            and self.verifier_boundary_crossed
            and self.acceptance_boundary
            in {
                LawbookAcceptanceBoundary.VERIFIED_PROOF,
                LawbookAcceptanceBoundary.FINITE_COUNTERMODEL,
                LawbookAcceptanceBoundary.TRUSTED_IMPORT,
                LawbookAcceptanceBoundary.CHAIN_AUDIT,
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "kind": self.kind.value,
            "status": self.status.value,
            "claim_id": self.claim_id,
            "source": self.source,
            "target": self.target,
            "raw": self.raw,
            "terminal_form": self.terminal_form.value if self.terminal_form else None,
            "certificate_id": self.certificate_id,
            "verifier_boundary_crossed": self.verifier_boundary_crossed,
            "acceptance_boundary": self.acceptance_boundary.value,
            "accepted_at": self.accepted_at,
            "accepted_by": self.accepted_by,
            "artifact_ids": list(self.artifact_ids),
            "digestion_trace_ids": list(self.digestion_trace_ids),
            "assimilation_candidate_ids": list(self.assimilation_candidate_ids),
            "projection_rule_ids": list(self.projection_rule_ids),
            "constructor_family_ids": list(self.constructor_family_ids),
            "route_rule_ids": list(self.route_rule_ids),
            "basin": self.basin,
            "conditions": list(self.conditions),
            "failure_boundaries": list(self.failure_boundaries),
            "reason_links": list(self.reason_links),
            "root_links": list(self.root_links),
            "provenance": dict(self.provenance),
            "metadata": dict(self.metadata),
            "advisory": self.advisory,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "LawbookEntry":
        terminal = data.get("terminal_form")
        return cls(
            entry_id=str(data["entry_id"]),
            kind=LawbookEntryKind(str(data.get("kind", LawbookEntryKind.UNKNOWN.value))),
            status=LawbookEntryStatus(str(data.get("status", LawbookEntryStatus.CANDIDATE.value))),
            claim_id=_optional_str(data.get("claim_id")),
            source=_optional_str(data.get("source")),
            target=_optional_str(data.get("target")),
            raw=_optional_str(data.get("raw")),
            terminal_form=TerminalForm(str(terminal)) if terminal else None,
            certificate_id=_optional_str(data.get("certificate_id")),
            verifier_boundary_crossed=bool(data.get("verifier_boundary_crossed", False)),
            acceptance_boundary=LawbookAcceptanceBoundary(str(data.get("acceptance_boundary", LawbookAcceptanceBoundary.NONE.value))),
            accepted_at=_optional_str(data.get("accepted_at")),
            accepted_by=_optional_str(data.get("accepted_by")),
            artifact_ids=tuple(str(x) for x in data.get("artifact_ids", ())),
            digestion_trace_ids=tuple(str(x) for x in data.get("digestion_trace_ids", ())),
            assimilation_candidate_ids=tuple(str(x) for x in data.get("assimilation_candidate_ids", ())),
            projection_rule_ids=tuple(str(x) for x in data.get("projection_rule_ids", ())),
            constructor_family_ids=tuple(str(x) for x in data.get("constructor_family_ids", ())),
            route_rule_ids=tuple(str(x) for x in data.get("route_rule_ids", ())),
            basin=_optional_str(data.get("basin")),
            conditions=tuple(str(x) for x in data.get("conditions", ())),
            failure_boundaries=tuple(str(x) for x in data.get("failure_boundaries", ())),
            reason_links=tuple(str(x) for x in data.get("reason_links", ())),
            root_links=tuple(str(x) for x in data.get("root_links", ())),
            provenance=dict(data.get("provenance", {})),
            metadata=dict(data.get("metadata", {})),
            advisory=bool(data.get("advisory", False)),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "LawbookEntry":
        return cls.from_dict(json.loads(text))


@dataclass
class LawbookReview:
    review_id: str
    candidate_entry_id: str
    decision: LawbookReviewDecision
    reviewer: str | None = None
    reason: str | None = None
    required_evidence: tuple[str, ...] = ()
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)
    advisory: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "review_id": self.review_id,
            "candidate_entry_id": self.candidate_entry_id,
            "decision": self.decision.value,
            "reviewer": self.reviewer,
            "reason": self.reason,
            "required_evidence": list(self.required_evidence),
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
            "advisory": self.advisory,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "LawbookReview":
        return cls(
            review_id=str(data["review_id"]),
            candidate_entry_id=str(data["candidate_entry_id"]),
            decision=LawbookReviewDecision(str(data.get("decision", LawbookReviewDecision.UNKNOWN.value))),
            reviewer=_optional_str(data.get("reviewer")),
            reason=_optional_str(data.get("reason")),
            required_evidence=tuple(str(x) for x in data.get("required_evidence", ())),
            created_at=str(data.get("created_at") or datetime.now(timezone.utc).isoformat()),
            metadata=dict(data.get("metadata", {})),
            advisory=bool(data.get("advisory", True)),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "LawbookReview":
        return cls.from_dict(json.loads(text))


@dataclass
class LawbookStore:
    store_id: str
    entries: list[LawbookEntry] = field(default_factory=list)
    reviews: list[LawbookReview] = field(default_factory=list)
    status: LawbookStoreStatus = LawbookStoreStatus.EMPTY
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    summary: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def entry_count(self) -> int:
        return len(self.entries)

    def accepted_entries(self) -> list[LawbookEntry]:
        return [entry for entry in self.entries if entry.is_accepted()]

    def candidate_entries(self) -> list[LawbookEntry]:
        return [entry for entry in self.entries if entry.is_candidate()]

    def truth_entries(self) -> list[LawbookEntry]:
        return [entry for entry in self.entries if entry.is_truth_entry()]

    def projection_entries(self) -> list[LawbookEntry]:
        return [entry for entry in self.entries if entry.is_projection_entry()]

    def find_by_claim_id(self, claim_id: str) -> list[LawbookEntry]:
        return [entry for entry in self.entries if entry.claim_id == claim_id]

    def find_by_certificate_id(self, certificate_id: str) -> list[LawbookEntry]:
        return [entry for entry in self.entries if entry.certificate_id == certificate_id]

    def add_entry(self, entry: LawbookEntry) -> None:
        self.entries.append(entry)
        self.status = LawbookStoreStatus.UPDATED

    def add_review(self, review: LawbookReview) -> None:
        self.reviews.append(review)
        self.status = LawbookStoreStatus.UPDATED

    def summarize(self) -> dict[str, Any]:
        self.summary = {
            "entry_total": len(self.entries),
            "candidate_count": sum(entry.status == LawbookEntryStatus.CANDIDATE for entry in self.entries),
            "accepted_count": sum(entry.status == LawbookEntryStatus.ACCEPTED for entry in self.entries),
            "rejected_count": sum(entry.status == LawbookEntryStatus.REJECTED for entry in self.entries),
            "needs_review_count": sum(entry.status == LawbookEntryStatus.NEEDS_REVIEW for entry in self.entries),
            "verified_proof_entries": sum(entry.kind == LawbookEntryKind.VERIFIED_PROOF_ENTRY for entry in self.entries),
            "finite_countermodel_entries": sum(entry.kind == LawbookEntryKind.FINITE_COUNTERMODEL_ENTRY for entry in self.entries),
            "named_obstruction_entries": sum(entry.kind == LawbookEntryKind.NAMED_OBSTRUCTION_ENTRY for entry in self.entries),
            "digested_proof_entries": sum(entry.kind == LawbookEntryKind.DIGESTED_PROOF_ENTRY for entry in self.entries),
            "projection_rule_entries": sum(entry.kind == LawbookEntryKind.PROJECTION_RULE_ENTRY for entry in self.entries),
            "invalid_count": sum(entry.status == LawbookEntryStatus.INVALID for entry in self.entries),
            "advisory_count": sum(entry.advisory for entry in self.entries),
        }
        return dict(self.summary)

    def audit(self) -> list[dict[str, Any]]:
        findings = audit_lawbook_store(self)
        critical_count = sum(item["severity"] == "CRITICAL" for item in findings)
        self.summary = {**self.summarize(), "critical_count": critical_count, "finding_count": len(findings)}
        self.status = LawbookStoreStatus.HAS_CRITICALS if critical_count else LawbookStoreStatus.AUDITED
        return findings

    def to_dict(self) -> dict[str, Any]:
        return {
            "store_id": self.store_id,
            "entries": [entry.to_dict() for entry in self.entries],
            "reviews": [review.to_dict() for review in self.reviews],
            "status": self.status.value,
            "created_at": self.created_at,
            "summary": dict(self.summary),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "LawbookStore":
        return cls(
            store_id=str(data["store_id"]),
            entries=[LawbookEntry.from_dict(item) for item in data.get("entries", [])],
            reviews=[LawbookReview.from_dict(item) for item in data.get("reviews", [])],
            status=LawbookStoreStatus(str(data.get("status", LawbookStoreStatus.EMPTY.value))),
            created_at=str(data.get("created_at") or datetime.now(timezone.utc).isoformat()),
            summary=dict(data.get("summary", {})),
            metadata=dict(data.get("metadata", {})),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "LawbookStore":
        return cls.from_dict(json.loads(text))

    def write_json(self, path: str | Path) -> None:
        _write_json(path, self.to_dict())

    @classmethod
    def read_json(cls, path: str | Path) -> "LawbookStore":
        return cls.from_json(Path(path).read_text(encoding="utf-8"))

    def write_jsonl(self, path: str | Path) -> None:
        _write_jsonl(path, [entry.to_dict() for entry in self.entries])

    @classmethod
    def read_jsonl(cls, path: str | Path) -> "LawbookStore":
        return cls(store_id=make_lawbook_store_id(path), entries=[LawbookEntry.from_dict(item) for item in _read_jsonl(path)])


def make_lawbook_entry_id(*parts: Any) -> str:
    return content_id("lawbook-entry", parts)


def make_lawbook_review_id(*parts: Any) -> str:
    return content_id("lawbook-review", parts)


def make_lawbook_store_id(*parts: Any) -> str:
    return content_id("lawbook-store", parts)


def lawbook_entry_from_certificate_like(
    *,
    claim_id: str | None = None,
    source: str | None = None,
    target: str | None = None,
    raw: str | None = None,
    terminal_form: TerminalForm | str | None = None,
    certificate_id: str | None = None,
    verifier_boundary_crossed: bool = False,
    artifact_ids: Sequence[str] = (),
    provenance: Mapping[str, Any] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> LawbookEntry:
    terminal = terminal_form if isinstance(terminal_form, TerminalForm) else TerminalForm(str(terminal_form)) if terminal_form else None
    kind = {
        TerminalForm.VERIFIED_PROOF: LawbookEntryKind.VERIFIED_PROOF_ENTRY,
        TerminalForm.FINITE_COUNTERMODEL: LawbookEntryKind.FINITE_COUNTERMODEL_ENTRY,
        TerminalForm.NAMED_OBSTRUCTION: LawbookEntryKind.NAMED_OBSTRUCTION_ENTRY,
    }.get(terminal, LawbookEntryKind.UNKNOWN)
    boundary = {
        TerminalForm.VERIFIED_PROOF: LawbookAcceptanceBoundary.VERIFIED_PROOF,
        TerminalForm.FINITE_COUNTERMODEL: LawbookAcceptanceBoundary.FINITE_COUNTERMODEL,
        TerminalForm.NAMED_OBSTRUCTION: LawbookAcceptanceBoundary.NAMED_OBSTRUCTION,
    }.get(terminal, LawbookAcceptanceBoundary.NONE)
    return LawbookEntry(
        entry_id=make_lawbook_entry_id(claim_id, source, target, raw, terminal.value if terminal else None, certificate_id),
        kind=kind,
        claim_id=claim_id,
        source=source,
        target=target,
        raw=raw,
        terminal_form=terminal,
        certificate_id=certificate_id,
        verifier_boundary_crossed=verifier_boundary_crossed,
        acceptance_boundary=boundary,
        artifact_ids=tuple(str(x) for x in artifact_ids),
        provenance=dict(provenance or {}),
        metadata=dict(metadata or {}),
    )


def lawbook_entry_from_proof_digestion(trace: Any, *, existing_certificate_id: str | None = None) -> LawbookEntry:
    certificate_id = existing_certificate_id or trace.certificate_id
    metadata = {
        "digestion_not_verification": True,
        "digestion_trace_id": trace.trace_id,
        "key_idea_count": len(trace.key_ideas),
        "schema_count": len(trace.reusable_schemas),
        "projection_candidate_count": len(trace.projection_candidates),
    }
    return LawbookEntry(
        entry_id=make_lawbook_entry_id("digestion", trace.trace_id, certificate_id),
        kind=LawbookEntryKind.DIGESTED_PROOF_ENTRY,
        terminal_form=trace.terminal_form if trace.verifier_boundary_crossed else None,
        certificate_id=certificate_id,
        verifier_boundary_crossed=bool(trace.verifier_boundary_crossed and certificate_id),
        acceptance_boundary=LawbookAcceptanceBoundary.DIGESTION_REVIEW,
        digestion_trace_ids=(trace.trace_id,),
        metadata=metadata,
        advisory=True,
    )


def lawbook_entry_from_assimilation_candidate(candidate: Any) -> LawbookEntry:
    return LawbookEntry(
        entry_id=make_lawbook_entry_id("assimilation", candidate.assimilation_id),
        kind=LawbookEntryKind.DIGESTED_PROOF_ENTRY,
        certificate_id=candidate.certificate_id,
        assimilation_candidate_ids=(candidate.assimilation_id,),
        digestion_trace_ids=(candidate.digestion_trace_id,),
        metadata={"assimilation_candidate_not_lawbook_entry": True, "ready": candidate.ready},
        advisory=True,
    )


def lawbook_entry_from_projection_candidate(candidate: Any) -> LawbookEntry:
    return LawbookEntry(
        entry_id=make_lawbook_entry_id("projection", candidate.candidate_id),
        kind=LawbookEntryKind.PROJECTION_RULE_ENTRY,
        claim_id=candidate.target_claim_id,
        source=candidate.source,
        target=candidate.target,
        certificate_id=None,
        projection_rule_ids=(candidate.candidate_id,),
        conditions=tuple(str(x) for x in candidate.metadata.get("conditions", ())),
        provenance={"projection_candidate_id": candidate.candidate_id},
        metadata={"projection_candidate_not_certificate": True, **dict(candidate.metadata)},
        advisory=True,
    )


def lawbook_entry_from_discovery_value_score(score: Any) -> LawbookEntry:
    status = LawbookEntryStatus.NEEDS_REVIEW if getattr(score, "decision", None) else LawbookEntryStatus.CANDIDATE
    return LawbookEntry(
        entry_id=make_lawbook_entry_id("discovery-value", score.score_id),
        kind=LawbookEntryKind.UNKNOWN,
        status=status,
        metadata={
            "value_score_not_truth": True,
            "discovery_value_score_id": score.score_id,
            "decision": score.decision.value,
            "normalized_score": score.normalized_score,
        },
        advisory=True,
    )


def review_lawbook_candidate(entry: LawbookEntry, *, reviewer: str | None = None, allow_human_review: bool = True) -> LawbookReview:
    decision = LawbookReviewDecision.NEEDS_MORE_EVIDENCE
    required: tuple[str, ...] = ()
    reason = "Candidate requires more evidence."
    if entry.kind == LawbookEntryKind.VERIFIED_PROOF_ENTRY:
        decision = LawbookReviewDecision.ACCEPT if entry.has_valid_truth_boundary() else LawbookReviewDecision.NEEDS_VERIFIER
        reason = "Verified proof boundary present." if decision == LawbookReviewDecision.ACCEPT else "Verified proof entry lacks valid verifier boundary."
    elif entry.kind == LawbookEntryKind.FINITE_COUNTERMODEL_ENTRY:
        valid = entry.terminal_form == TerminalForm.FINITE_COUNTERMODEL and bool(entry.certificate_id) and entry.verifier_boundary_crossed
        decision = LawbookReviewDecision.ACCEPT if valid else LawbookReviewDecision.NEEDS_VERIFIER
        reason = "Finite validator boundary present." if valid else "Finite countermodel entry lacks validated boundary."
    elif entry.kind == LawbookEntryKind.DERIVED_CERTIFICATE_ENTRY:
        valid = entry.acceptance_boundary == LawbookAcceptanceBoundary.CHAIN_AUDIT and bool(entry.certificate_id)
        decision = LawbookReviewDecision.ACCEPT if valid else LawbookReviewDecision.NEEDS_VERIFIER
        reason = "Chain audit present." if valid else "Derived certificate lacks chain audit."
    elif entry.kind == LawbookEntryKind.NAMED_OBSTRUCTION_ENTRY:
        evidence = bool(entry.provenance or entry.metadata.get("obstruction") or entry.failure_boundaries)
        valid = entry.acceptance_boundary in {LawbookAcceptanceBoundary.NAMED_OBSTRUCTION, LawbookAcceptanceBoundary.HUMAN_REVIEW} and evidence
        decision = LawbookReviewDecision.ACCEPT if valid else LawbookReviewDecision.NEEDS_MORE_EVIDENCE
        reason = "Named obstruction evidence present." if valid else "Named obstruction needs reviewed obstruction evidence."
    elif entry.kind == LawbookEntryKind.DIGESTED_PROOF_ENTRY:
        valid = bool(entry.certificate_id) and bool(entry.metadata.get("digestion_not_verification"))
        decision = LawbookReviewDecision.ACCEPT if valid else (LawbookReviewDecision.NEEDS_VERIFIER if not entry.certificate_id else LawbookReviewDecision.NEEDS_DIGESTION)
        reason = "Digestion linked to existing certificate." if valid else "Digestion needs certificate linkage and review metadata."
    elif entry.kind == LawbookEntryKind.PROJECTION_RULE_ENTRY:
        valid = bool(entry.metadata.get("projection_candidate_not_certificate")) and bool(entry.conditions or entry.provenance)
        decision = LawbookReviewDecision.ACCEPT if valid else LawbookReviewDecision.NEEDS_PROJECTION_REVIEW
        reason = "Projection review prerequisites present." if valid else "Projection rule needs conditions or provenance."
    elif entry.kind == LawbookEntryKind.REUSABLE_SCHEMA_ENTRY:
        valid = bool(entry.digestion_trace_ids or entry.certificate_id)
        decision = LawbookReviewDecision.ACCEPT if valid else LawbookReviewDecision.NEEDS_MORE_EVIDENCE
        reason = "Schema linked to digestion/certificate." if valid else "Reusable schema needs digestion or certificate link."
    return LawbookReview(
        review_id=make_lawbook_review_id(entry.entry_id, decision.value, reviewer),
        candidate_entry_id=entry.entry_id,
        decision=decision,
        reviewer=reviewer,
        reason=reason,
        required_evidence=required,
    )


def accept_lawbook_entry(entry: LawbookEntry, review: LawbookReview, *, accepted_by: str | None = None) -> LawbookEntry:
    if review.decision != LawbookReviewDecision.ACCEPT:
        status = LawbookEntryStatus.REJECTED if review.decision == LawbookReviewDecision.REJECT else LawbookEntryStatus.NEEDS_REVIEW
        return replace(entry, status=status)
    if entry.is_truth_entry() and not entry.has_valid_truth_boundary():
        raise ValueError("cannot accept truth entry without valid truth boundary")
    boundary = entry.acceptance_boundary
    if boundary in {LawbookAcceptanceBoundary.NONE, LawbookAcceptanceBoundary.UNKNOWN}:
        boundary = {
            LawbookEntryKind.VERIFIED_PROOF_ENTRY: LawbookAcceptanceBoundary.VERIFIED_PROOF,
            LawbookEntryKind.FINITE_COUNTERMODEL_ENTRY: LawbookAcceptanceBoundary.FINITE_COUNTERMODEL,
            LawbookEntryKind.DERIVED_CERTIFICATE_ENTRY: LawbookAcceptanceBoundary.CHAIN_AUDIT,
            LawbookEntryKind.DIGESTED_PROOF_ENTRY: LawbookAcceptanceBoundary.DIGESTION_REVIEW,
            LawbookEntryKind.PROJECTION_RULE_ENTRY: LawbookAcceptanceBoundary.PROJECTION_REVIEW,
        }.get(entry.kind, LawbookAcceptanceBoundary.HUMAN_REVIEW)
    return replace(
        entry,
        status=LawbookEntryStatus.ACCEPTED,
        accepted_at=datetime.now(timezone.utc).isoformat(),
        accepted_by=accepted_by,
        acceptance_boundary=boundary,
    )


def build_lawbook_store(
    *,
    entries: Sequence[LawbookEntry] = (),
    reviews: Sequence[LawbookReview] = (),
    auto_review: bool = False,
    auto_accept: bool = False,
    reviewer: str | None = None,
) -> LawbookStore:
    store = LawbookStore(store_id=make_lawbook_store_id(*(entry.entry_id for entry in entries)), entries=list(entries), reviews=list(reviews), status=LawbookStoreStatus.LOADED if entries else LawbookStoreStatus.EMPTY)
    if auto_review:
        known = {review.candidate_entry_id for review in store.reviews}
        for entry in store.entries:
            if entry.is_candidate() and entry.entry_id not in known:
                store.add_review(review_lawbook_candidate(entry, reviewer=reviewer))
    if auto_accept:
        review_by_entry = {review.candidate_entry_id: review for review in store.reviews}
        store.entries = [accept_lawbook_entry(entry, review_by_entry[entry.entry_id], accepted_by=reviewer) if review_by_entry.get(entry.entry_id, None) and review_by_entry[entry.entry_id].decision == LawbookReviewDecision.ACCEPT else entry for entry in store.entries]
    store.audit()
    return store


def audit_lawbook_entry(entry: LawbookEntry) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []

    def add(severity: str, code: str, message: str) -> None:
        findings.append({"severity": severity, "code": code, "message": message, "entry_id": entry.entry_id})

    text = json.dumps(entry.to_dict(), sort_keys=True).lower()
    if entry.is_accepted() and entry.is_truth_entry() and not entry.has_valid_truth_boundary():
        add("CRITICAL", "ACCEPTED_TRUTH_WITHOUT_BOUNDARY", "Accepted truth entry lacks valid truth boundary.")
    if entry.is_accepted() and entry.kind == LawbookEntryKind.VERIFIED_PROOF_ENTRY and entry.terminal_form != TerminalForm.VERIFIED_PROOF:
        add("CRITICAL", "ACCEPTED_PROOF_WRONG_TERMINAL", "Accepted verified proof entry lacks VERIFIED_PROOF terminal form.")
    if entry.is_accepted() and entry.kind == LawbookEntryKind.FINITE_COUNTERMODEL_ENTRY and entry.terminal_form != TerminalForm.FINITE_COUNTERMODEL:
        add("CRITICAL", "ACCEPTED_COUNTERMODEL_WRONG_TERMINAL", "Accepted countermodel entry lacks FINITE_COUNTERMODEL terminal form.")
    if entry.is_accepted() and entry.certificate_id and not entry.verifier_boundary_crossed and entry.is_truth_entry():
        add("CRITICAL", "CERTIFICATE_WITHOUT_BOUNDARY", "Accepted truth entry has certificate id without verifier boundary.")
    if entry.kind == LawbookEntryKind.DIGESTED_PROOF_ENTRY and entry.metadata.get("digestion_creates_proof"):
        add("CRITICAL", "DIGESTION_AS_PROOF", "Digested proof entry claims digestion creates proof.")
    if entry.kind == LawbookEntryKind.PROJECTION_RULE_ENTRY and (entry.metadata.get("projection_is_certificate") or entry.terminal_form):
        add("CRITICAL", "PROJECTION_AS_CERTIFICATE", "Projection rule entry claims certificate status.")
    if entry.metadata.get("value_score_as_truth"):
        add("CRITICAL", "VALUE_AS_LAWBOOK_TRUTH", "Discovery value score accepted as truth.")
    if entry.metadata.get("assimilation_candidate_as_truth"):
        add("CRITICAL", "ASSIMILATION_AS_TRUTH", "Assimilation candidate accepted as truth without review.")
    if entry.metadata.get("natural_language_verifier_boundary"):
        add("CRITICAL", "NATURAL_LANGUAGE_AS_BOUNDARY", "Natural-language note accepted as verifier boundary.")
    if entry.is_accepted() and entry.acceptance_boundary in {LawbookAcceptanceBoundary.NONE, LawbookAcceptanceBoundary.UNKNOWN}:
        add("CRITICAL", "ACCEPTED_WITHOUT_ACCEPTANCE_BOUNDARY", "Accepted entry lacks acceptance boundary.")
    if entry.is_candidate() and not entry.provenance:
        add("WARNING", "CANDIDATE_WITHOUT_PROVENANCE", "Candidate has no provenance.")
    if entry.is_candidate() and not entry.conditions:
        add("WARNING", "CANDIDATE_WITHOUT_CONDITIONS", "Candidate has no conditions.")
    if entry.kind == LawbookEntryKind.PROJECTION_RULE_ENTRY and not (entry.projection_rule_ids or entry.metadata.get("projection_candidate_not_certificate")):
        add("WARNING", "PROJECTION_RULE_WITHOUT_METADATA", "Projection rule has no projection ids or metadata.")
    if entry.kind == LawbookEntryKind.DIGESTED_PROOF_ENTRY and not entry.digestion_trace_ids:
        add("WARNING", "DIGESTED_PROOF_WITHOUT_TRACE", "Digested proof has no digestion trace ids.")
    if entry.kind == LawbookEntryKind.NAMED_OBSTRUCTION_ENTRY and not (entry.failure_boundaries or entry.metadata.get("obstruction")):
        add("WARNING", "OBSTRUCTION_WITHOUT_FAILURE_BOUNDARY", "Named obstruction lacks failure boundary metadata.")
    if entry.is_accepted() and entry.advisory:
        add("WARNING", "ACCEPTED_ENTRY_STILL_ADVISORY", "Accepted entry is still marked advisory.")
    if entry.kind == LawbookEntryKind.UNKNOWN or entry.status == LawbookEntryStatus.UNKNOWN:
        add("WARNING", "UNKNOWN_LAWBOOK_ENTRY", "Lawbook entry has unknown kind or status.")
    if entry.is_accepted() and entry.kind == LawbookEntryKind.VERIFIED_PROOF_ENTRY and entry.has_valid_truth_boundary():
        add("INFO", "ACCEPTED_PROOF_VALID_BOUNDARY", "Accepted proof entry has valid boundary.")
    if entry.is_accepted() and entry.kind == LawbookEntryKind.FINITE_COUNTERMODEL_ENTRY and entry.has_valid_truth_boundary():
        add("INFO", "ACCEPTED_COUNTERMODEL_VALID_BOUNDARY", "Accepted countermodel entry has valid boundary.")
    if entry.kind == LawbookEntryKind.DIGESTED_PROOF_ENTRY and entry.certificate_id:
        add("INFO", "DIGESTION_LINKED_TO_CERTIFICATE", "Digestion entry is linked to an existing certificate.")
    if entry.kind == LawbookEntryKind.PROJECTION_RULE_ENTRY and entry.metadata.get("projection_candidate_not_certificate"):
        add("INFO", "PROJECTION_MARKED_NOT_CERTIFICATE", "Projection rule is marked not-certificate.")
    if entry.is_candidate():
        add("INFO", "CANDIDATE_REMAINS_CANDIDATE", "Candidate remains non-terminal.")
    return findings


def audit_lawbook_store(store: LawbookStore) -> list[dict[str, Any]]:
    return [finding for entry in store.entries for finding in audit_lawbook_entry(entry)]


def lawbook_store_to_projection_candidates(store: LawbookStore) -> list[Any]:
    from mathgraph.projection import ProjectionCandidate, ProjectionRuleKind

    outputs = []
    for entry in store.accepted_entries():
        if entry.kind == LawbookEntryKind.PROJECTION_RULE_ENTRY:
            outputs.append(
                ProjectionCandidate(
                    candidate_id=content_id("lawbook-projection", entry.entry_id),
                    source_claim_id=entry.claim_id,
                    target_claim_id=entry.claim_id,
                    source=entry.source,
                    target=entry.target,
                    rule_kind=ProjectionRuleKind.ADVISORY_SIMILARITY,
                    originating_lawbook_entry_id=entry.entry_id,
                    confidence=1.0,
                    advisory=True,
                    metadata={"accepted_projection_rule": True, "not_truth": True},
                )
            )
        elif entry.is_truth_entry() and entry.has_valid_truth_boundary():
            outputs.append(
                ProjectionCandidate(
                    candidate_id=content_id("lawbook-known-skip", entry.entry_id),
                    source_claim_id=entry.claim_id,
                    target_claim_id=entry.claim_id,
                    source=entry.source,
                    target=entry.target,
                    rule_kind=ProjectionRuleKind.EXACT_KNOWN,
                    originating_lawbook_entry_id=entry.entry_id,
                    originating_certificate_id=entry.certificate_id,
                    confidence=1.0,
                    advisory=True,
                    metadata={"known_skip_candidate": True, "not_truth": True},
                )
            )
    return outputs


def lawbook_store_to_continuation_outputs(store: LawbookStore) -> list[Any]:
    from mathgraph.continuation_actions import ContinuationActionOutput, ContinuationActionStatus, ContinuationOutputKind

    outputs = []
    for entry in store.entries:
        kind = ContinuationOutputKind.TASK
        payload = {"entry_id": entry.entry_id, "task": "review_lawbook_entry" if not entry.is_accepted() else "project_lawbook_entry"}
        outputs.append(
            ContinuationActionOutput(
                output_id=content_id("lawbook-output", entry.entry_id),
                action_id="lawbook",
                kind=kind,
                status=ContinuationActionStatus.PRODUCED_TASK,
                task_payload=payload,
                metadata={"advisory_only": True},
                advisory=True,
            )
        )
    return outputs


def lawbook_store_to_alchemical_trace(store: LawbookStore) -> Any:
    from mathgraph.alchemy import AlchemicalPhase, AlchemicalStatus, AlchemicalStep, AlchemicalTrace

    trace = AlchemicalTrace(trace_id=content_id("lawbook-alchemy", store.store_id))
    if store.entries:
        trace.add_step(AlchemicalStep(phase=AlchemicalPhase.RAW_MATTER, status=AlchemicalStatus.ADVISORY_ONLY))
    if store.reviews:
        trace.add_step(AlchemicalStep(phase=AlchemicalPhase.DISTILLATION, status=AlchemicalStatus.ADVISORY_ONLY))
    if store.accepted_entries():
        trace.add_step(AlchemicalStep(phase=AlchemicalPhase.COAGULATION, status=AlchemicalStatus.ADVISORY_ONLY))
    if any(entry.is_projection_entry() for entry in store.accepted_entries()):
        trace.add_step(AlchemicalStep(phase=AlchemicalPhase.PROJECTION, status=AlchemicalStatus.ADVISORY_ONLY))
    if any(entry.is_truth_entry() and entry.has_valid_truth_boundary() for entry in store.accepted_entries()):
        trace.add_step(AlchemicalStep(phase=AlchemicalPhase.FIXATION, status=AlchemicalStatus.PROMOTED_BY_VERIFIER, verifier_boundary="inherited"))
    return trace


def lawbook_store_to_agent_experiences(store: LawbookStore, agent_id: str | None = None) -> list[Any]:
    from mathgraph.agent_biography import AgentExperience, AgentExperienceOutcome

    experiences = []
    for entry in store.entries:
        outcome = AgentExperienceOutcome.ADVISORY_ONLY
        if entry.is_accepted() and entry.has_valid_truth_boundary():
            if entry.terminal_form == TerminalForm.VERIFIED_PROOF:
                outcome = AgentExperienceOutcome.VERIFIED_PROOF
            elif entry.terminal_form == TerminalForm.FINITE_COUNTERMODEL:
                outcome = AgentExperienceOutcome.FINITE_COUNTERMODEL
        elif entry.kind == LawbookEntryKind.NAMED_OBSTRUCTION_ENTRY and entry.is_accepted():
            outcome = AgentExperienceOutcome.RESIDUAL
        experiences.append(
            AgentExperience(
                experience_id=content_id("lawbook-experience", entry.entry_id),
                agent_id=agent_id or "lawbook",
                episode_id=None,
                claim_id=entry.claim_id,
                route="lawbook",
                phase="COAGULATION",
                outcome=outcome,
                terminal_form=entry.terminal_form if outcome in {AgentExperienceOutcome.VERIFIED_PROOF, AgentExperienceOutcome.FINITE_COUNTERMODEL} else None,
                certificate_id=entry.certificate_id if outcome in {AgentExperienceOutcome.VERIFIED_PROOF, AgentExperienceOutcome.FINITE_COUNTERMODEL} else None,
                verifier_boundary_crossed=entry.has_valid_truth_boundary(),
                metadata={"lawbook_entry_id": entry.entry_id, "public_memory_boundary": True},
            )
        )
    return experiences


def lawbook_store_to_route_telemetry_events(store: LawbookStore) -> list[dict[str, Any]]:
    return [
        {
            "event_id": content_id("lawbook-telemetry", entry.entry_id),
            "route_kind": "lawbook",
            "outcome": entry.status.value,
            "lawbook_entry_id": entry.entry_id,
            "advisory": not entry.is_accepted(),
        }
        for entry in store.entries
    ]


def _write_jsonl(path: str | Path, rows: Sequence[Mapping[str, Any]]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("".join(json.dumps(dict(row), sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    source = Path(path)
    if not source.exists():
        return []
    return [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]


def _optional_str(value: Any) -> str | None:
    return None if value is None else str(value)


# ---------------------------------------------------------------------------
# SQLite Lawbook helpers for repo-native compounding runs.
#
# This is intentionally a compatibility layer rather than a replacement for the
# accepted-entry LawbookStore above. New compounding scripts can write concise
# episode artifacts here while older public imports keep working.


LAWBOOK_SQLITE_TABLES: dict[str, str] = {
    "runs": "run_id TEXT PRIMARY KEY, payload_json TEXT, created_at TEXT",
    "episodes": "episode_id TEXT PRIMARY KEY, run_id TEXT, episode INTEGER, payload_json TEXT, created_at TEXT",
    "constructors": "row_id TEXT PRIMARY KEY, run_id TEXT, constructor_id TEXT, family TEXT, payload_json TEXT, created_at TEXT",
    "policy_eval": "row_id TEXT PRIMARY KEY, run_id TEXT, episode INTEGER, policy TEXT, payload_json TEXT, created_at TEXT",
    "finite_countermodels": "row_id TEXT PRIMARY KEY, run_id TEXT, episode INTEGER, claim_id TEXT, payload_json TEXT, created_at TEXT",
    "obstruction_atlas": "row_id TEXT PRIMARY KEY, run_id TEXT, episode INTEGER, obstruction_name TEXT, payload_json TEXT, created_at TEXT",
    "residual_queue": "row_id TEXT PRIMARY KEY, run_id TEXT, episode INTEGER, payload_json TEXT, created_at TEXT",
    "repair_family_lawbook": "row_id TEXT PRIMARY KEY, run_id TEXT, family TEXT, payload_json TEXT, created_at TEXT",
    "promotion_events": "row_id TEXT PRIMARY KEY, run_id TEXT, event_type TEXT, payload_json TEXT, created_at TEXT",
    "true_proof_templates": "row_id TEXT PRIMARY KEY, run_id TEXT, template_id TEXT, payload_json TEXT, created_at TEXT",
}


def init_lawbook(path: str | Path) -> Any:
    """Create/open a lightweight SQLite Lawbook for compounding artifacts."""

    import sqlite3

    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    for table, schema in LAWBOOK_SQLITE_TABLES.items():
        conn.execute(f"CREATE TABLE IF NOT EXISTS {table} ({schema})")
    conn.commit()
    return conn


def write_dataframe(*args: Any, **kwargs: Any) -> int:
    """Write dataframe-like rows to SQLite without crashing on empties.

    Supported call forms:
      write_dataframe(conn, table_name, rows)
      write_dataframe(table_name, rows, conn=conn)
      write_dataframe(table_name, rows, path="lawbook.sqlite")
    """

    conn = kwargs.pop("conn", None)
    path = kwargs.pop("path", None)
    if len(args) == 3:
        conn, table_name, rows = args
    elif len(args) == 2:
        table_name, rows = args
    else:
        raise TypeError("write_dataframe expects (conn, table, rows) or (table, rows, conn=...)")
    close = False
    if conn is None:
        if path is None:
            raise ValueError("conn or path is required")
        conn = init_lawbook(path)
        close = True
    try:
        count = _sqlite_write_rows(conn, str(table_name), _rows_from_dataframe(rows))
        conn.commit()
        return count
    finally:
        if close:
            conn.close()


def upsert_run_summary(conn: Any, run_id: str, summary: Mapping[str, Any]) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO runs(run_id, payload_json, created_at) VALUES (?, ?, ?)",
        (str(run_id), json.dumps(dict(summary), sort_keys=True), _utc_now()),
    )
    conn.commit()


def upsert_episode_summary(conn: Any, run_id: str, episode: int, summary: Mapping[str, Any]) -> None:
    episode_id = f"{run_id}:episode:{int(episode)}"
    conn.execute(
        "INSERT OR REPLACE INTO episodes(episode_id, run_id, episode, payload_json, created_at) VALUES (?, ?, ?, ?, ?)",
        (episode_id, str(run_id), int(episode), json.dumps(dict(summary), sort_keys=True), _utc_now()),
    )
    conn.commit()


def _sqlite_write_rows(conn: Any, table_name: str, rows: list[dict[str, Any]]) -> int:
    if not rows:
        conn.execute(f"CREATE TABLE IF NOT EXISTS {table_name} (_empty INTEGER)")
        return 0
    if table_name in LAWBOOK_SQLITE_TABLES:
        return _sqlite_write_canonical_rows(conn, table_name, rows)
    columns = sorted({str(key) for row in rows for key in row.keys()}) or ["payload_json"]
    column_sql = ", ".join(f"{_sql_ident(col)} TEXT" for col in columns)
    conn.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({column_sql})")
    placeholders = ", ".join("?" for _ in columns)
    col_sql = ", ".join(_sql_ident(col) for col in columns)
    values = [[_sqlite_value(row.get(col)) for col in columns] for row in rows]
    conn.executemany(f"INSERT INTO {table_name} ({col_sql}) VALUES ({placeholders})", values)
    return len(rows)


def _sqlite_write_canonical_rows(conn: Any, table_name: str, rows: list[dict[str, Any]]) -> int:
    now = _utc_now()
    if table_name == "runs":
        for i, row in enumerate(rows):
            run_id = str(row.get("run_id") or row.get("id") or content_id("lawbook-run-row", {"i": i, "row": row}))
            conn.execute(
                "INSERT OR REPLACE INTO runs(run_id, payload_json, created_at) VALUES (?, ?, ?)",
                (run_id, json.dumps(row, sort_keys=True), now),
            )
        return len(rows)
    if table_name == "episodes":
        for i, row in enumerate(rows):
            run_id = str(row.get("run_id", ""))
            episode = _int_value(row.get("episode", i))
            episode_id = str(row.get("episode_id") or f"{run_id}:episode:{episode}")
            conn.execute(
                "INSERT OR REPLACE INTO episodes(episode_id, run_id, episode, payload_json, created_at) VALUES (?, ?, ?, ?, ?)",
                (episode_id, run_id, episode, json.dumps(row, sort_keys=True), now),
            )
        return len(rows)
    mapping = {
        "constructors": ("constructor_id", "family"),
        "policy_eval": ("policy",),
        "finite_countermodels": ("claim_id",),
        "obstruction_atlas": ("obstruction_name",),
        "repair_family_lawbook": ("family",),
        "promotion_events": ("event_type",),
        "true_proof_templates": ("template_id",),
    }
    for i, row in enumerate(rows):
        row_id = str(row.get("row_id") or content_id(f"lawbook-{table_name}", {"i": i, "row": row}))
        run_id = str(row.get("run_id", ""))
        episode = _int_value(row.get("episode", 0))
        payload = json.dumps(row, sort_keys=True)
        if table_name == "residual_queue":
            conn.execute(
                "INSERT OR REPLACE INTO residual_queue(row_id, run_id, episode, payload_json, created_at) VALUES (?, ?, ?, ?, ?)",
                (row_id, run_id, episode, payload, now),
            )
        elif table_name in mapping:
            fields = mapping[table_name]
            values = [str(row.get(field, "")) for field in fields]
            if table_name == "constructors":
                conn.execute(
                    "INSERT OR REPLACE INTO constructors(row_id, run_id, constructor_id, family, payload_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (row_id, run_id, values[0], values[1], payload, now),
                )
            elif table_name == "policy_eval":
                conn.execute(
                    "INSERT OR REPLACE INTO policy_eval(row_id, run_id, episode, policy, payload_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (row_id, run_id, episode, values[0], payload, now),
                )
            elif table_name == "finite_countermodels":
                conn.execute(
                    "INSERT OR REPLACE INTO finite_countermodels(row_id, run_id, episode, claim_id, payload_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (row_id, run_id, episode, values[0], payload, now),
                )
            elif table_name == "obstruction_atlas":
                conn.execute(
                    "INSERT OR REPLACE INTO obstruction_atlas(row_id, run_id, episode, obstruction_name, payload_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (row_id, run_id, episode, values[0], payload, now),
                )
            elif table_name == "repair_family_lawbook":
                conn.execute(
                    "INSERT OR REPLACE INTO repair_family_lawbook(row_id, run_id, family, payload_json, created_at) VALUES (?, ?, ?, ?, ?)",
                    (row_id, run_id, values[0], payload, now),
                )
            elif table_name == "promotion_events":
                conn.execute(
                    "INSERT OR REPLACE INTO promotion_events(row_id, run_id, event_type, payload_json, created_at) VALUES (?, ?, ?, ?, ?)",
                    (row_id, run_id, values[0], payload, now),
                )
            elif table_name == "true_proof_templates":
                conn.execute(
                    "INSERT OR REPLACE INTO true_proof_templates(row_id, run_id, template_id, payload_json, created_at) VALUES (?, ?, ?, ?, ?)",
                    (row_id, run_id, values[0], payload, now),
                )
    return len(rows)


def _int_value(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def _rows_from_dataframe(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if hasattr(value, "to_dict"):
        try:
            records = value.to_dict("records")
            if isinstance(records, list):
                return [dict(row) for row in records]
        except TypeError:
            pass
    return [dict(row) for row in value]


def _sqlite_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list, tuple, bool)):
        return json.dumps(value, sort_keys=True)
    return str(value)


def _sql_ident(value: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in str(value))
    return f'"{safe or "col"}"'


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
