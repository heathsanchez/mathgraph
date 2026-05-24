"""TRUE-side proof-template classification for ETP implication pairs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

from mathgraph.etp_terms import parse_equation, variable_first_canonicalize_equation
from mathgraph.polarized_quotient_ir import build_pair_features
from mathgraph.proof_congruence import ExplainTrace


@dataclass(frozen=True)
class TrueProofTemplate:
    eq1_id: int
    eq2_id: int
    equation1: str
    equation2: str
    template_family: str
    proof_status: str
    trust_level: str
    advisory_only: bool = True
    can_promote_truth: bool = False
    needs_lean: bool = True
    explanation_summary: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "eq1_id": self.eq1_id,
            "eq2_id": self.eq2_id,
            "equation1": self.equation1,
            "equation2": self.equation2,
            "template_family": self.template_family,
            "proof_status": self.proof_status,
            "trust_level": self.trust_level,
            "advisory_only": True,
            "can_promote_truth": False,
            "needs_lean": self.needs_lean,
            "explanation_summary": self.explanation_summary,
            "metadata": dict(self.metadata),
        }


def classify_true_pair(eq1: str, eq2: str, pair_features: dict[str, Any] | None = None, closure_trace: ExplainTrace | None = None) -> dict[str, Any]:
    pair_features = pair_features or build_pair_features(eq1, eq2)
    eq1_can = variable_first_canonicalize_equation(eq1)
    eq2_can = variable_first_canonicalize_equation(eq2)
    family = "unresolved_true_advisory"
    summary = "no bounded proof template found"
    trust = "CANDIDATE_PROOF_TEMPLATE"
    status = "proof_template_generated"
    if eq1_can == eq2_can:
        family = "reflexive_same_equation" if str(eq1).strip() == str(eq2).strip() else "alpha_equivalent"
        summary = "source and target are syntactically or alpha-equivalent"
    elif _direct_source(eq1, eq2):
        family = "lhs_rhs_direct_source"
        summary = "target is directly present as source equality orientation"
    elif bool(pair_features.get("source_implies_target_in_bounded_quotient")):
        family = "congruence_closure_bounded"
        summary = "bounded quotient closure collapses target sides"
    elif closure_trace and closure_trace.forced_equal:
        family = "congruence_closure_bounded"
        summary = "proof-producing bounded congruence trace forces target"
    elif pair_features.get("skeleton_equal"):
        family = "substitution_instance"
        summary = "source and target share canonical skeleton"
    elif int(pair_features.get("target_var_count", 0) or 0) < int(pair_features.get("source_var_count", 0) or 0):
        family = "variable_identification"
        summary = "target has fewer variables than source"
    elif float(pair_features.get("projection_boundary_score", 0.0) or 0.0) > 0:
        family = "projection_collapse"
        summary = "target resembles projection collapse"
    elif bool(pair_features.get("source_lhs_rhs_skeleton_equal")) and bool(pair_features.get("target_lhs_rhs_skeleton_equal")):
        family = "equivalence_candidate"
        summary = "both equations share lhs/rhs skeleton shape"
    elif int(pair_features.get("target_depth", 0) or 0) >= 2:
        family = "transitivity_candidate"
        summary = "target is deep enough to require chained congruence/proof"
    else:
        family = "needs_lean_proof"
        summary = "requires external proof route for terminal TRUE"
    if closure_trace and closure_trace.forced_equal:
        trust = "BOUNDED_CONGRUENCE_TRACE"
        status = "bounded_congruence_trace"
    return {
        "template_family": family,
        "proof_status": status,
        "trust_level": trust,
        "advisory_only": True,
        "can_promote_truth": False,
        "needs_lean": True,
        "explanation_summary": summary,
    }


def build_true_proof_template_inventory(true_pairs: Iterable[tuple[int, int]], equations: Sequence[str], features: dict[tuple[int, int], dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    feature_map = features or {}
    rows: list[dict[str, Any]] = []
    for i, j in true_pairs:
        eq1, eq2 = equations[int(i)], equations[int(j)]
        pf = feature_map.get((int(i), int(j))) or build_pair_features(eq1, eq2)
        classification = classify_true_pair(eq1, eq2, pf)
        rows.append(
            TrueProofTemplate(
                eq1_id=int(i),
                eq2_id=int(j),
                equation1=eq1,
                equation2=eq2,
                **classification,
            ).to_dict()
        )
    return rows


def _direct_source(eq1: str, eq2: str) -> bool:
    try:
        a = parse_equation(eq1)
        b = parse_equation(eq2)
    except Exception:
        return False
    return (a.lhs.to_string(), a.rhs.to_string()) in {
        (b.lhs.to_string(), b.rhs.to_string()),
        (b.rhs.to_string(), b.lhs.to_string()),
    }
