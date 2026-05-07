"""Diagnostics and reporting for MathGraph metabolic cycle episodes."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class MetabolicDiagnostics:
    initial_claim_count: int
    known_before_count: int
    primitive_countermodels_added: int
    primitive_proofs_added: int
    derived_certificates_added: int
    proof_motifs_added: int
    lemma_candidates_added: int
    obstructions_added: int
    unresolved_before: int
    unresolved_after: int
    residual_compression_gain: float
    derived_amplification_factor: float
    route_yield_by_route: dict[str, Any]
    advisory_artifact_count: int
    authoritative_artifact_count: int
    contradiction_count: int
    better_shaped_unknown: bool
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def compute_residual_compression_gain(before: int, after: int) -> float:
    """Return the fraction of unresolved work compressed or resolved."""

    if before <= 0:
        return 0.0
    return max(0.0, min(1.0, (before - after) / before))


def compute_derived_amplification_factor(primitive_added: int, derived_added: int) -> float:
    """Return derived artifacts per primitive terminal artifact added."""

    if primitive_added <= 0:
        return float(derived_added) if derived_added > 0 else 0.0
    return derived_added / primitive_added


def evaluate_better_shaped_unknown(metrics: dict[str, Any]) -> tuple[bool, str]:
    """Decide whether the episode left a sharper residual frontier."""

    if int(metrics.get("unresolved_after", 0)) < int(metrics.get("unresolved_before", 0)):
        return True, "The unresolved set shrank after verified terminal work."
    if int(metrics.get("derived_certificates_added", 0)) > 0:
        return True, "Derived certificates compounded primitive terminal artifacts."
    if int(metrics.get("obstructions_added", 0)) > 0 and bool(
        metrics.get("residuals_grouped_by_signature", False)
    ):
        return True, "Residual tasks were grouped into named obstruction pressure."
    if bool(metrics.get("next_frontier_sharper", False)):
        return True, "The next frontier is smaller or more route-specific."
    route_yield = metrics.get("route_yield_by_route", {})
    if isinstance(route_yield, dict) and any(
        (value or {}).get("tasks", 0) > 0 and "yield_rate" in (value or {})
        for value in route_yield.values()
        if isinstance(value, dict)
    ):
        return True, "Route-yield statistics became more informative."
    return False, "The run produced no new terminal, obstruction, route, or frontier structure."


def write_metabolic_report(result: Any, path: str | Path) -> None:
    """Write a human-readable metabolic cycle report."""

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    data = result.to_dict() if hasattr(result, "to_dict") else dict(result)
    summary = data.get("summary", {})
    diagnostics = data.get("diagnostics", {})
    artifacts = data.get("artifacts", {})
    warnings = data.get("warnings", [])

    lines = [
        "# MathGraph Metabolic Cycle Report",
        "",
        "This report describes one local MathGraph metabolic episode. It is a testbed run, not a proof of broad ETP coverage.",
        "",
        "## Terminal Boundary",
        "",
        "MathGraph only treats verified proof traces, finite countermodels, and named obstructions as terminal forms. Route scores, proof motifs, lemma candidates, and Lean sketches remain advisory unless backed by explicit verifier artifacts.",
        "",
        "## Authoritative Additions",
        "",
        f"- Primitive countermodels added: {summary.get('primitive_countermodels_added', 0)}",
        f"- Primitive proofs added: {summary.get('primitive_proofs_added', 0)}",
        f"- Derived certificates added: {summary.get('derived_certificates_added', 0)}",
        f"- Contradictions detected: {summary.get('contradiction_count', diagnostics.get('contradiction_count', 0))}",
        "",
        "## Advisory Additions",
        "",
        f"- Proof motifs added: {summary.get('proof_motifs_added', 0)}",
        f"- Lemma candidates added: {summary.get('lemma_candidates_added', 0)}",
        f"- Obstructions/residual records added: {summary.get('obstructions_added', 0)}",
        f"- Advisory artifact count: {summary.get('advisory_artifact_count', 0)}",
        "",
        "## Residual Shape",
        "",
        f"- Unresolved before: {summary.get('unresolved_before', 0)}",
        f"- Unresolved after: {summary.get('unresolved_after', 0)}",
        f"- Residual compression gain: {summary.get('residual_compression_gain', 0.0):.3f}",
        f"- Derived amplification factor: {summary.get('derived_amplification_factor', 0.0):.3f}",
        f"- Better-shaped unknown: {summary.get('better_shaped_unknown', False)}",
        f"- Explanation: {summary.get('better_shaped_unknown_explanation', diagnostics.get('explanation', ''))}",
        "",
        "## Route Learning",
        "",
        "Route-yield statistics are search pressure only. They do not alter terminal forms.",
        "",
        "```json",
        json.dumps(summary.get("route_yield_by_route", {}), indent=2, sort_keys=True),
        "```",
        "",
        "## Artifacts",
        "",
    ]
    for name, artifact_path in sorted(artifacts.items()):
        lines.append(f"- `{name}`: `{artifact_path}`")
    if warnings:
        lines.extend(["", "## Warnings", ""])
        for warning in warnings:
            lines.append(f"- {warning}")
    lines.extend(
        [
            "",
            "## Truth-Safety Note",
            "",
            "No unsupported truth claims were made: no-countermodel-found rows are residual evidence, proof motifs are not proofs, lemma candidates are not theorems, and generated sketches are not Lean verification.",
            "",
        ]
    )
    output.write_text("\n".join(lines), encoding="utf-8")

