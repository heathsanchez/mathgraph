"""Polarized Quotient-Continuation IR feature extraction."""

from __future__ import annotations

from typing import Any

from mathgraph.constructor_families import default_priority_for_basin
from mathgraph.etp_terms import equation_features, safe_parse_equation
from mathgraph.quotient_state import closure_from_equation


def build_equation_features(equation_text: str) -> dict[str, Any]:
    return equation_features(equation_text)


def build_pair_features(eq1_text: str, eq2_text: str, max_depth: int = 2) -> dict[str, Any]:
    src = equation_features(eq1_text)
    tgt = equation_features(eq2_text)
    if not src.get("parse_ok") or not tgt.get("parse_ok"):
        return {
            "eq1": eq1_text,
            "eq2": eq2_text,
            "parse_ok": False,
            "parse_error": src.get("parse_error") or tgt.get("parse_error"),
            "advisory_only": True,
            "can_promote_truth": False,
        }
    source_size = int(src["lhs_size"]) + int(src["rhs_size"])
    target_size = int(tgt["lhs_size"]) + int(tgt["rhs_size"])
    source_depth = max(int(src["lhs_depth"]), int(src["rhs_depth"]))
    target_depth = max(int(tgt["lhs_depth"]), int(tgt["rhs_depth"]))
    source_repeat = int(src["repeat_count"])
    target_repeat = int(tgt["repeat_count"])
    closure_equal = False
    try:
        target_eq, _ = safe_parse_equation(eq2_text)
        closure = closure_from_equation(eq1_text, max_depth=max_depth)
        closure_equal = bool(target_eq and closure.are_equal(target_eq.lhs, target_eq.rhs))
    except Exception:
        closure_equal = False
    rhs_new = len(set(_vars(tgt, "rhs")) - set(_vars(src, "lhs")) - set(_vars(src, "rhs")))
    lhs_new = len(set(_vars(tgt, "lhs")) - set(_vars(src, "lhs")) - set(_vars(src, "rhs")))
    node_delta = target_size - source_size
    repeat_delta = target_repeat - source_repeat
    quotient_pressure = max(0.0, source_repeat + (1.0 if src["lhs_skeleton"] == src["rhs_skeleton"] else 0.0))
    target_separation = max(0.0, target_size + target_repeat - (2.0 if closure_equal else 0.0))
    fresh_escape = rhs_new + lhs_new
    projection_score = _projection_score(eq2_text)
    repeat_tail = max(0.0, repeat_delta + target_depth * 0.25)
    compression = max(0.0, source_size - target_size)
    expansion = max(0.0, target_size - source_size)
    ir_loss = target_separation + fresh_escape + expansion - quotient_pressure
    gradient = ir_loss + projection_score + repeat_tail
    goi_cycle = 1.0 if src["lhs_skeleton"] == src["rhs_skeleton"] and tgt["lhs_skeleton"] == tgt["rhs_skeleton"] else 0.0
    row: dict[str, Any] = {
        "eq1": eq1_text,
        "eq2": eq2_text,
        "parse_ok": True,
        "source_size": source_size,
        "target_size": target_size,
        "source_depth": source_depth,
        "target_depth": target_depth,
        "source_var_count": int(src["var_count"]),
        "target_var_count": int(tgt["var_count"]),
        "source_repeat_count": source_repeat,
        "target_repeat_count": target_repeat,
        "rhs_new_var_count": rhs_new,
        "lhs_new_var_count": lhs_new,
        "node_delta_pair": node_delta,
        "repeat_delta_pair": repeat_delta,
        "skeleton_equal": src["canonical"] == tgt["canonical"],
        "source_lhs_rhs_skeleton_equal": bool(src["lhs_rhs_skeleton_equal"]),
        "target_lhs_rhs_skeleton_equal": bool(tgt["lhs_rhs_skeleton_equal"]),
        "quotient_pressure": round(quotient_pressure, 6),
        "target_separation_pressure": round(target_separation, 6),
        "fresh_variable_escape_count": fresh_escape,
        "projection_boundary_score": round(projection_score, 6),
        "repeat_tail_pressure": round(repeat_tail, 6),
        "compression_pressure": round(compression, 6),
        "expansion_pressure": round(expansion, 6),
        "ir_constraint_loss": round(ir_loss, 6),
        "ir_continuation_gradient": round(gradient, 6),
        "goi_limit_cycle_proxy": goi_cycle,
        "source_implies_target_in_bounded_quotient": closure_equal,
        "advisory_only": True,
        "can_promote_truth": False,
    }
    row["basin"] = classify_basin(row)
    row["deep_ir_candidate"] = classify_deep_ir(row)
    row["recommended_families"] = recommend_constructor_families(row)
    return row


def classify_basin(pair_features: dict[str, Any]) -> str:
    if int(pair_features.get("fresh_variable_escape_count", 0)) > 0:
        return "fresh_variable_escape"
    if float(pair_features.get("projection_boundary_score", 0.0)) > 0:
        return "projection_pressure"
    if float(pair_features.get("compression_pressure", 0.0)) > 1:
        return "collapse_or_constant_pressure"
    if bool(pair_features.get("target_lhs_rhs_skeleton_equal")):
        return "idempotent_band_pressure"
    if int(pair_features.get("target_depth", 0)) >= 2:
        return "associative_or_deep_term_pressure"
    return "mixed_sair_false_pair"


def classify_deep_ir(pair_features: dict[str, Any]) -> str:
    if float(pair_features.get("ir_continuation_gradient", 0.0)) >= 5:
        return "high_gradient"
    if int(pair_features.get("fresh_variable_escape_count", 0)) > 0:
        return "fresh_escape"
    if float(pair_features.get("repeat_tail_pressure", 0.0)) >= 2:
        return "repeat_tail"
    if bool(pair_features.get("source_implies_target_in_bounded_quotient")):
        return "bounded_quotient_collapse"
    return "shallow"


def recommend_constructor_families(pair_features: dict[str, Any]) -> list[str]:
    families = default_priority_for_basin(str(pair_features.get("basin", "")))
    if int(pair_features.get("fresh_variable_escape_count", 0)) > 0:
        families = ["quotient_fresh_gate", "fresh_absorber"] + [f for f in families if f not in {"quotient_fresh_gate", "fresh_absorber"}]
    return families[:8]


def _projection_score(eq: str) -> float:
    text = str(eq)
    score = 0.0
    if "= x" in text or "x =" in text:
        score += 1.0
    if "= y" in text or "y =" in text:
        score += 1.0
    return score


def _vars(features: dict[str, Any], side: str) -> list[str]:
    flow = str(features.get(f"{side}_var_flow", ""))
    return [part.split(":", 1)[0] for part in flow.split(",") if part]
