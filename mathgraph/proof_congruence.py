"""Bounded proof-producing congruence traces for ETP TRUE candidates."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mathgraph.etp_terms import ETPEquation, parse_equation
from mathgraph.quotient_state import BoundedTermUniverse, CongruenceClosure, _split_binary


@dataclass(frozen=True)
class ProofStep:
    step_index: int
    lhs: str
    rhs: str
    reason: str
    premises: tuple[str, ...] = ()
    advisory_only: bool = True
    can_promote_truth: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_index": self.step_index,
            "lhs": self.lhs,
            "rhs": self.rhs,
            "reason": self.reason,
            "premises": list(self.premises),
            "advisory_only": True,
            "can_promote_truth": False,
        }


@dataclass(frozen=True)
class ExplainTrace:
    source_equation: str
    target_equation: str
    max_depth: int
    merged_pairs: tuple[tuple[str, str], ...]
    reasons: tuple[str, ...]
    proof_steps: tuple[ProofStep, ...]
    forced_equal: bool
    trust_level: str
    proof_status: str
    advisory_only: bool = True
    can_promote_truth: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_equation": self.source_equation,
            "target_equation": self.target_equation,
            "max_depth": self.max_depth,
            "merged_pairs": [list(pair) for pair in self.merged_pairs],
            "reasons": list(self.reasons),
            "proof_steps": [step.to_dict() for step in self.proof_steps],
            "forced_equal": self.forced_equal,
            "trust_level": self.trust_level,
            "proof_status": self.proof_status,
            "advisory_only": True,
            "can_promote_truth": False,
            "metadata": dict(self.metadata),
        }


class ProofCongruenceClosure:
    """Bounded congruence closure with an explainable advisory trace."""

    def __init__(self, variables: tuple[str, ...] = ("x", "y"), max_depth: int = 2) -> None:
        # Depth-3 universes with three or more variables explode quickly under
        # the simple v0 closure implementation. Cap them conservatively; this
        # remains a bounded candidate trace, not a completeness claim.
        self.requested_max_depth = int(max_depth)
        self.max_depth = min(int(max_depth), 2)
        self.universe = BoundedTermUniverse.build(variables, max_depth=self.max_depth)
        self.closure = CongruenceClosure(self.universe)
        self.source_equation: ETPEquation | None = None

    @classmethod
    def from_source_equation(cls, eq1: str, max_depth: int = 2) -> "ProofCongruenceClosure":
        eq = parse_equation(eq1)
        obj = cls(eq.variables(), max_depth=max_depth)
        obj.add_source_equation(eq1)
        return obj

    def add_source_equation(self, eq1: str) -> None:
        eq = parse_equation(eq1)
        self.source_equation = eq
        lhs = eq.lhs.to_string()
        rhs = eq.rhs.to_string()
        if self.closure.uf.union(lhs, rhs, "source_equation"):
            self.closure.explanations.append({"lhs": lhs, "rhs": rhs, "reason": "source_equation"})
        self.propagate_congruence()

    def propagate_congruence(self) -> None:
        terms = list(self.universe.terms)
        if len(terms) > 350:
            return
        for a in terms:
            parsed_a = _split_binary(a)
            if not parsed_a:
                continue
            al, ar = parsed_a
            for b in terms:
                parsed_b = _split_binary(b)
                if not parsed_b:
                    continue
                bl, br = parsed_b
                if self.closure.uf.find(al) == self.closure.uf.find(bl) and self.closure.uf.find(ar) == self.closure.uf.find(br):
                    if self.closure.uf.union(a, b, "bounded_congruence"):
                        self.closure.explanations.append({"lhs": a, "rhs": b, "reason": "bounded_congruence", "from": [al, ar, bl, br]})

    def target_forced(self, eq2: str) -> bool:
        target = parse_equation(eq2)
        return self.closure.are_equal(target.lhs, target.rhs)

    def explain_target(self, eq2: str) -> ExplainTrace:
        target = parse_equation(eq2)
        forced = self.target_forced(eq2)
        source_text = self.source_equation.normalized if self.source_equation else ""
        steps = []
        merged = []
        reasons = []
        for i, item in enumerate(self.closure.explanations):
            lhs = str(item.get("lhs", ""))
            rhs = str(item.get("rhs", ""))
            reason = str(item.get("reason", ""))
            premises = tuple(str(x) for x in item.get("from", ()) or ())
            merged.append((lhs, rhs))
            reasons.append(reason)
            steps.append(ProofStep(i, lhs, rhs, reason, premises))
        return ExplainTrace(
            source_equation=source_text,
            target_equation=target.normalized,
            max_depth=self.max_depth,
            merged_pairs=tuple(merged),
            reasons=tuple(reasons),
            proof_steps=tuple(steps),
            forced_equal=forced,
            trust_level="BOUNDED_CONGRUENCE_TRACE" if forced else "CANDIDATE_PROOF_TEMPLATE",
            proof_status="bounded_congruence_trace" if forced else "proof_template_generated",
            metadata={
                "target_lhs": target.lhs.to_string(),
                "target_rhs": target.rhs.to_string(),
                "finite_search_failure_is_not_true": True,
            },
        )


def explain_bounded_congruence(eq1: str, eq2: str, max_depth: int = 2) -> ExplainTrace:
    closure = ProofCongruenceClosure.from_source_equation(eq1, max_depth=max_depth)
    return closure.explain_target(eq2)
