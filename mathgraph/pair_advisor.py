"""Advisory route suggestions for source/target equation pairs."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from mathgraph.certificates import TerminalForm, VerificationStatus
from mathgraph.equations import parse_equation
from mathgraph.route_instructor import infer_route_kind


KNOWN_ROUTES = [
    "direct_substitution_instance",
    "variable_identification",
    "skeleton_preserving_relabel",
    "broad_split_to_skeleton_preserving_relabel",
    "finite_countermodel",
]


@dataclass(frozen=True)
class PairAdvice:
    source: str
    target: str
    status: str
    terminal_form: str
    verification_status: str
    known_claim: str | None
    exact_match: bool
    candidate_routes: list[dict[str, Any]]
    required_next_evidence: list[str]
    warnings: list[str]
    features: dict[str, Any]
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "status": self.status,
            "terminal_form": self.terminal_form,
            "verification_status": self.verification_status,
            "known_claim": self.known_claim,
            "exact_match": self.exact_match,
            "candidate_routes": [dict(route) for route in self.candidate_routes],
            "required_next_evidence": list(self.required_next_evidence),
            "warnings": list(self.warnings),
            "features": dict(self.features),
            "explanation": self.explanation,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PairAdvice":
        return cls(
            source=str(data.get("source", "")),
            target=str(data.get("target", "")),
            status=str(data.get("status", "advisory_only")),
            terminal_form=str(data.get("terminal_form", TerminalForm.NAMED_OBSTRUCTION.value)),
            verification_status=str(data.get("verification_status", "UNKNOWN")),
            known_claim=data.get("known_claim"),
            exact_match=bool(data.get("exact_match", False)),
            candidate_routes=list(data.get("candidate_routes", [])),
            required_next_evidence=list(data.get("required_next_evidence", [])),
            warnings=list(data.get("warnings", [])),
            features=dict(data.get("features", {})),
            explanation=str(data.get("explanation", "")),
        )


def advise_pair(lawbook: Any, source: str | None, target: str | None, max_routes: int = 5) -> PairAdvice:
    if not source or not target:
        return PairAdvice(
            source=str(source or ""),
            target=str(target or ""),
            status="malformed_input",
            terminal_form=TerminalForm.NAMED_OBSTRUCTION.value,
            verification_status="UNKNOWN",
            known_claim=None,
            exact_match=False,
            candidate_routes=[],
            required_next_evidence=[],
            warnings=["Both source and target must be provided.", *_default_warnings()],
            features={},
            explanation="Malformed pair input; no route advice was produced.",
        )

    exact = _find_exact_trace(lawbook, source, target)
    features = extract_pair_features(source, target)
    if exact is not None:
        routes = _trace_routes(exact)
        candidate_routes = [
            _candidate_from_instruction(lawbook, route, score=1.0, reason_codes=["exact_lawbook_trace"])
            for route in routes
        ]
        return PairAdvice(
            source=source,
            target=target,
            status="known_certificate",
            terminal_form=exact.terminal_form.value,
            verification_status=exact.verification_status.value,
            known_claim=exact.claim,
            exact_match=True,
            candidate_routes=candidate_routes[:max_routes],
            required_next_evidence=[],
            warnings=["This advice is based on an existing verified lawbook trace."],
            features=features,
            explanation="Exact source/target pair found in the certificate lawbook.",
        )

    candidates = _rank_candidate_routes(lawbook, features, max_routes=max_routes)
    return PairAdvice(
        source=source,
        target=target,
        status="advisory_only",
        terminal_form=TerminalForm.NAMED_OBSTRUCTION.value,
        verification_status="UNKNOWN",
        known_claim=None,
        exact_match=False,
        candidate_routes=candidates,
        required_next_evidence=_unique(
            item
            for candidate in candidates
            for item in candidate.get("evidence_requirements", [])
        ),
        warnings=_unique(
            [
                "This is advisory only, not a proof or refutation.",
                "Do not promote without a verified proof or finite countermodel.",
                "Finite search failure is not proof.",
                *[
                    warning
                    for candidate in candidates
                    for warning in candidate.get("warnings", [])
                ],
            ]
        ),
        features=features,
        explanation="No exact lawbook trace was found; route candidates are heuristic advice only.",
    )


def advise_many(lawbook: Any, pairs: Iterable[Any], max_routes: int = 5) -> list[PairAdvice]:
    results: list[PairAdvice] = []
    for pair in pairs:
        if isinstance(pair, dict):
            source = pair.get("source")
            target = pair.get("target")
        else:
            try:
                source, target = pair
            except (TypeError, ValueError):
                source, target = None, None
        results.append(advise_pair(lawbook, source, target, max_routes=max_routes))
    return results


def extract_pair_features(source: str, target: str) -> dict[str, Any]:
    source_vars = _variables(source)
    target_vars = _variables(target)
    source_op_count = _op_count(source)
    target_op_count = _op_count(target)
    return {
        "source_len": len(source),
        "target_len": len(target),
        "source_var_set": sorted(source_vars),
        "target_var_set": sorted(target_vars),
        "new_target_vars": sorted(target_vars - source_vars),
        "target_vars_subset_source_vars": target_vars.issubset(source_vars),
        "source_op_count": source_op_count,
        "target_op_count": target_op_count,
        "op_delta": target_op_count - source_op_count,
        "paren_delta": target.count("(") + target.count(")") - source.count("(") - source.count(")"),
        "same_text": _normalize(source) == _normalize(target),
        "same_skeleton_rough": _skeleton(source) == _skeleton(target),
        "source_var_count": len(source_vars),
        "target_var_count": len(target_vars),
        "target_has_repeated_vars": _has_repeated_vars(target),
        "source_has_repeated_vars": _has_repeated_vars(source),
    }


def save_pair_advice(path: str | Path, advice: PairAdvice) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(advice.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _rank_candidate_routes(lawbook: Any, features: dict[str, Any], max_routes: int) -> list[dict[str, Any]]:
    scored = []
    for route in KNOWN_ROUTES:
        score, reasons = _score_route(route, features)
        if score <= 0:
            continue
        scored.append(_candidate_from_instruction(lawbook, route, score=score, reason_codes=reasons))
    scored.sort(key=lambda item: (-item["score"], item["route"]))
    return scored[:max_routes]


def _score_route(route: str, features: dict[str, Any]) -> tuple[float, list[str]]:
    reasons: list[str] = []
    score = 0.0
    if route == "direct_substitution_instance":
        if features["same_text"]:
            score += 0.95
            reasons.append("same_text")
        if features["target_vars_subset_source_vars"] and features["op_delta"] <= 0:
            score += 0.45
            reasons.append("subset_vars_no_more_ops")
    elif route == "variable_identification":
        if features["target_vars_subset_source_vars"]:
            score += 0.35
            reasons.append("target_vars_subset_source_vars")
        if features["target_has_repeated_vars"]:
            score += 0.3
            reasons.append("target_has_repeated_vars")
        if features["source_var_count"] > features["target_var_count"]:
            score += 0.25
            reasons.append("fewer_target_variables")
    elif route == "skeleton_preserving_relabel":
        if features["same_skeleton_rough"] and features["op_delta"] == 0:
            score += 0.85
            reasons.append("same_skeleton_rough")
    elif route == "broad_split_to_skeleton_preserving_relabel":
        overlap = _var_overlap(features)
        if abs(features["op_delta"]) <= 1 and overlap > 0 and not features["same_skeleton_rough"]:
            score += 0.5 + min(overlap, 0.4)
            reasons.append("similar_ops_and_variable_overlap")
    elif route == "finite_countermodel":
        proof_signals = features["same_text"] or features["same_skeleton_rough"] or (
            features["target_vars_subset_source_vars"] and features["op_delta"] <= 0
        )
        if features["new_target_vars"]:
            score += 0.45
            reasons.append("target_introduces_new_variables")
        if features["op_delta"] >= 2:
            score += 0.35
            reasons.append("target_more_complex")
        if not features["target_vars_subset_source_vars"]:
            score += 0.25
            reasons.append("target_vars_not_subset_source_vars")
        if not proof_signals:
            score += 0.25
            reasons.append("proof_route_signals_weak")
    return round(min(score, 1.0), 3), reasons


def _candidate_from_instruction(
    lawbook: Any,
    route: str,
    *,
    score: float,
    reason_codes: list[str],
) -> dict[str, Any]:
    instruction = None
    try:
        instruction = lawbook.route_instruction(route)
    except Exception:
        instruction = None
    if instruction is None or getattr(instruction, "count", 0) == 0:
        route_kind = infer_route_kind(route, {}, {})
        return {
            "route": route,
            "score": score,
            "route_kind": route_kind,
            "evidence_requirements": ["explicit source/target pair", "verified terminal trace"],
            "warnings": _default_warnings(),
            "guidance": [f"Consider {route!r} only as advisory until verified."],
            "reason_codes": reason_codes,
        }
    return {
        "route": route,
        "score": score,
        "route_kind": instruction.route_kind,
        "evidence_requirements": list(instruction.evidence_requirements),
        "warnings": list(instruction.rejection_warnings),
        "guidance": list(instruction.positive_guidance),
        "reason_codes": reason_codes,
    }


def _find_exact_trace(lawbook: Any, source: str, target: str) -> Any:
    for trace in getattr(lawbook, "traces", []):
        trace_source = trace.source or _trace_value(trace, "source_equation")
        trace_target = trace.target or _trace_value(trace, "target_equation")
        if _equation_matches(trace_source, source) and _equation_matches(trace_target, target):
            return trace
    return None


def _trace_routes(trace: Any) -> list[str]:
    route = _trace_value(trace, "compiled_route")
    if route:
        return [route]
    return [str(route) for route in getattr(trace, "routes_tried", [])]


def _trace_value(trace: Any, key: str) -> str | None:
    payloads = [getattr(trace, "metadata", {})]
    certificate = getattr(trace, "certificate", None)
    if certificate is not None:
        payloads.append(certificate.payload)
    for payload in payloads:
        if not isinstance(payload, dict):
            continue
        if key in payload and payload[key] not in (None, ""):
            return str(payload[key])
        for nested_key in ("model", "record"):
            nested = payload.get(nested_key)
            if isinstance(nested, dict) and key in nested and nested[key] not in (None, ""):
                return str(nested[key])
    return None


def _variables(text: str) -> set[str]:
    return set(re.findall(r"\b[a-z][a-z0-9_]*\b", text))


def _op_count(text: str) -> int:
    return text.count("*") + text.count("◇") + text.count("⋆")


def _normalize(text: str) -> str:
    return re.sub(r"\s+", "", text)


def _equation_matches(left: str | None, right: str | None) -> bool:
    if _normalize(left or "") == _normalize(right or ""):
        return True
    if left is None or right is None:
        return False
    try:
        return str(parse_equation(left)) == str(parse_equation(right))
    except ValueError:
        return False


def _skeleton(text: str) -> str:
    return re.sub(r"\b[a-z][a-z0-9_]*\b", "v", _normalize(text))


def _has_repeated_vars(text: str) -> bool:
    vars_seen = re.findall(r"\b[a-z][a-z0-9_]*\b", text)
    return len(vars_seen) != len(set(vars_seen))


def _var_overlap(features: dict[str, Any]) -> float:
    source = set(features["source_var_set"])
    target = set(features["target_var_set"])
    if not source and not target:
        return 0.0
    return len(source & target) / len(source | target)


def _unique(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _default_warnings() -> list[str]:
    return [
        "This is advisory only, not a proof or refutation.",
        "Do not promote without a verified proof or finite countermodel.",
    ]
