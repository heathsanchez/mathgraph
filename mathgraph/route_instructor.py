"""Route-level instruction cards extracted from a certificate lawbook."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mathgraph.certificates import TerminalForm, VerificationStatus


@dataclass(frozen=True)
class RouteInstruction:
    route: str
    count: int
    terminal_form_counts: dict[str, int]
    verification_status_counts: dict[str, int]
    source_count: int
    target_count: int
    sample_claims: list[str]
    sample_pairs: list[dict[str, Any]]
    route_kind: str
    positive_guidance: list[str]
    rejection_warnings: list[str]
    evidence_requirements: list[str]
    example_summaries: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "route": self.route,
            "count": self.count,
            "terminal_form_counts": dict(self.terminal_form_counts),
            "verification_status_counts": dict(self.verification_status_counts),
            "source_count": self.source_count,
            "target_count": self.target_count,
            "sample_claims": list(self.sample_claims),
            "sample_pairs": [dict(pair) for pair in self.sample_pairs],
            "route_kind": self.route_kind,
            "positive_guidance": list(self.positive_guidance),
            "rejection_warnings": list(self.rejection_warnings),
            "evidence_requirements": list(self.evidence_requirements),
            "example_summaries": [dict(example) for example in self.example_summaries],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RouteInstruction":
        return cls(
            route=str(data["route"]),
            count=int(data["count"]),
            terminal_form_counts=dict(data.get("terminal_form_counts", {})),
            verification_status_counts=dict(data.get("verification_status_counts", {})),
            source_count=int(data.get("source_count", 0)),
            target_count=int(data.get("target_count", 0)),
            sample_claims=list(data.get("sample_claims", [])),
            sample_pairs=list(data.get("sample_pairs", [])),
            route_kind=str(data.get("route_kind", "mixed_or_unknown")),
            positive_guidance=list(data.get("positive_guidance", [])),
            rejection_warnings=list(data.get("rejection_warnings", [])),
            evidence_requirements=list(data.get("evidence_requirements", [])),
            example_summaries=list(data.get("example_summaries", [])),
        )


def infer_route_kind(
    route: str,
    terminal_form_counts: dict[str, int],
    verification_status_counts: dict[str, int],
) -> str:
    if route == "finite_countermodel":
        return "countermodel_constructor"
    if route in {
        "variable_identification",
        "skeleton_preserving_relabel",
        "broad_split_to_skeleton_preserving_relabel",
        "direct_substitution_instance",
    }:
        return "proof_constructor"
    if (
        terminal_form_counts.get(TerminalForm.FINITE_COUNTERMODEL.value, 0) > 0
        and terminal_form_counts.get(TerminalForm.VERIFIED_PROOF.value, 0) == 0
        and verification_status_counts.get(VerificationStatus.REFUTED.value, 0) > 0
    ):
        return "countermodel_constructor"
    if (
        terminal_form_counts.get(TerminalForm.VERIFIED_PROOF.value, 0) > 0
        and terminal_form_counts.get(TerminalForm.FINITE_COUNTERMODEL.value, 0) == 0
        and verification_status_counts.get(VerificationStatus.VERIFIED.value, 0) > 0
    ):
        return "proof_constructor"
    return "mixed_or_unknown"


def build_route_instruction(lawbook: Any, route: str, sample_limit: int = 5) -> RouteInstruction:
    card = lawbook.route_card(route)
    traces = lawbook.find_by_route(route, limit=sample_limit)
    route_kind = infer_route_kind(
        route,
        card.get("terminal_form_counts", {}),
        card.get("verification_status_counts", {}),
    )
    guidance = _guidance(route, route_kind)
    return RouteInstruction(
        route=route,
        count=card["count"],
        terminal_form_counts=card["terminal_form_counts"],
        verification_status_counts=card["verification_status_counts"],
        source_count=card["source_count"],
        target_count=card["target_count"],
        sample_claims=card["sample_claims"][:sample_limit],
        sample_pairs=card["sample_pairs"][:sample_limit],
        route_kind=route_kind,
        positive_guidance=guidance["positive_guidance"],
        rejection_warnings=guidance["rejection_warnings"],
        evidence_requirements=guidance["evidence_requirements"],
        example_summaries=[_example_summary(trace) for trace in traces],
    )


def build_all_route_instructions(lawbook: Any, sample_limit: int = 5) -> dict[str, RouteInstruction]:
    return {
        route: build_route_instruction(lawbook, route, sample_limit=sample_limit)
        for route in lawbook.all_route_cards()
    }


def route_instruction_report(lawbook: Any, sample_limit: int = 5) -> dict[str, Any]:
    instructions = build_all_route_instructions(lawbook, sample_limit=sample_limit)
    return {
        "route_count": len(instructions),
        "total_traces": lawbook.summary()["trace_count"],
        "instructions": {
            route: instruction.to_dict() for route, instruction in instructions.items()
        },
    }


def save_route_instruction_report(path: str | Path, report: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _guidance(route: str, route_kind: str) -> dict[str, list[str]]:
    if route == "finite_countermodel":
        return {
            "positive_guidance": [
                "Search for a finite magma satisfying the source equation while violating the target equation.",
                "Treat the finite model as a refutation certificate, not as a heuristic score.",
                "Preserve source satisfaction and separate the target equality.",
            ],
            "evidence_requirements": [
                "finite table/model payload or external verified Lean artifact",
                "source equation",
                "target equation",
                "verification status REFUTED",
            ],
            "rejection_warnings": [
                "Finite search failure is not proof.",
                "A candidate table is not enough unless source satisfaction and target violation are verified.",
            ],
        }
    if route == "variable_identification":
        return _proof_guidance(
            [
                "Try identifying target variables as a substitution instance of the source law.",
                "Check whether the target is obtained by collapsing or equating variables from the source.",
                "Prefer exact substitution evidence over semantic guessing.",
            ]
        )
    if route == "skeleton_preserving_relabel":
        return _proof_guidance(
            [
                "Compare source and target tree skeletons under variable relabeling.",
                "Preserve operation structure while mapping variable roles.",
                "Use only verified relabel transformations.",
            ]
        )
    if route == "broad_split_to_skeleton_preserving_relabel":
        return _proof_guidance(
            [
                "Look for a broader decomposition followed by skeleton-preserving relabeling.",
                "Use this only when a direct relabel is insufficient but the verified trace supports the split.",
            ]
        )
    if route == "direct_substitution_instance":
        return _proof_guidance(
            [
                "Check whether the target is a direct syntactic substitution instance of the source.",
                "Prefer exact term substitution over loose analogy.",
            ]
        )
    return {
        "positive_guidance": [
            f"Treat route {route!r} as reference-only until its proof obligations are explicit.",
            "Use only terminal traces that already carry verified proof or refutation status.",
        ],
        "evidence_requirements": [
            "explicit source/target pair",
            "route name",
            "terminal form and verification status",
        ],
        "rejection_warnings": [
            "Do not infer truth from route name alone.",
            "Do not promote candidates without a verified terminal trace.",
        ],
    }


def _proof_guidance(positive_guidance: list[str]) -> dict[str, list[str]]:
    return {
        "positive_guidance": positive_guidance,
        "evidence_requirements": [
            "verified proof trace or Lean artifact",
            "explicit source/target pair",
            "route name",
            "verification status VERIFIED",
        ],
        "rejection_warnings": [
            "Do not infer truth from shape similarity alone.",
            "Do not promote to VERIFIED_PROOF without explicit verification.",
        ],
    }


def _example_summary(trace: Any) -> dict[str, Any]:
    return {
        "claim": trace.claim,
        "source_idx": _trace_value(trace, "source_idx"),
        "target_idx": _trace_value(trace, "target_idx"),
        "terminal_form": trace.terminal_form.value,
        "verification_status": trace.verification_status.value,
        "source_preview": _preview(trace.source or _trace_value(trace, "source_equation")),
        "target_preview": _preview(trace.target or _trace_value(trace, "target_equation")),
    }


def _trace_value(trace: Any, key: str) -> str | None:
    for payload in _payloads(trace):
        value = _nested_value(payload, key)
        if value is not None:
            return str(value)
    return None


def _payloads(trace: Any) -> list[dict[str, Any]]:
    payloads = [getattr(trace, "metadata", {})]
    certificate = getattr(trace, "certificate", None)
    if certificate is not None:
        payloads.append(certificate.payload)
    obstruction = getattr(trace, "obstruction", None)
    if obstruction is not None:
        payloads.append(obstruction.payload)
    return [payload for payload in payloads if isinstance(payload, dict)]


def _nested_value(payload: dict[str, Any], key: str) -> Any:
    if key in payload and payload[key] not in (None, ""):
        return payload[key]
    for nested_key in ("model", "record"):
        nested = payload.get(nested_key)
        if isinstance(nested, dict) and key in nested and nested[key] not in (None, ""):
            return nested[key]
    return None


def _preview(value: str | None, limit: int = 120) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if len(text) <= limit else text[: limit - 3] + "..."
