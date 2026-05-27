"""Conservative policy selection for SAIR Stage 2 evidence packs."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class SairStage2PolicyRule:
    component: str
    selected: bool
    reason: str
    marginal_gain: float
    support: int
    advisory_only: bool
    can_promote_truth: bool


def learn_canonical_policy(
    component_diagnostics: pd.DataFrame,
    *,
    min_support: int = 1,
    min_marginal_gain: float = 0.0,
    allow_experimental: bool = False,
) -> dict[str, Any]:
    selected: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for _, row in component_diagnostics.iterrows():
        component = str(row.get("component", ""))
        if component == "combined" or not component:
            continue
        marginal = float(row.get("marginal_gain", 0) or 0)
        support = int(row.get("support", 0) or 0)
        if component == "baseline":
            rule = _rule(component, True, "baseline finite constructor search is always retained", marginal, support)
            selected.append(rule)
            continue
        if marginal < 0:
            rejected.append(_rule(component, False, "negative held-out marginal contribution", marginal, support))
            continue
        if support < min_support and not allow_experimental:
            rejected.append(_rule(component, False, "insufficient held-out support", marginal, support))
            continue
        if marginal >= min_marginal_gain:
            selected.append(_rule(component, True, "non-negative held-out evidence with sufficient support", marginal, support))
        else:
            rejected.append(_rule(component, False, "below minimum marginal gain", marginal, support))
    return {
        "policy_name": "sair_stage2_conservative_canonical_policy",
        "selected_components": selected,
        "rejected_components": rejected,
        "experimental_allowed": allow_experimental,
        "advisory_only": True,
        "can_promote_truth": False,
        "trust_boundary": "policy routes do not promote truth; terminal forms still require finite checker or proof verifier evidence",
    }


def apply_policy_to_scorecard(scorecard: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    selected = {row["component"] for row in policy.get("selected_components", [])}
    baseline = float(scorecard.get("episode_0_certificates", 0) or 0)
    candidate_yields = [baseline]
    if "lawbook" in selected:
        candidate_yields.append(float(scorecard.get("episode_1_certificates", baseline) or 0))
    if "microbasin" in selected:
        candidate_yields.append(float(scorecard.get("episode_2_certificates", baseline) or 0))
    if "repair" in selected:
        candidate_yields.append(float(scorecard.get("episode_3_certificates", baseline) or 0))
    adjusted_yield = max(candidate_yields) if candidate_yields else baseline
    adjusted = dict(scorecard)
    adjusted["policy_selected_components"] = sorted(selected)
    adjusted["policy_rejected_components"] = [row["component"] for row in policy.get("rejected_components", [])]
    adjusted["policy_adjusted_certificate_yield"] = adjusted_yield
    adjusted["policy_adjusted_total_gain_over_baseline"] = adjusted_yield - baseline
    adjusted["total_gain_over_baseline"] = adjusted_yield - baseline
    if adjusted.get("real_sair_used") and adjusted.get("strict_admission_passed") and adjusted["total_gain_over_baseline"] > 0:
        adjusted["final_classification"] = "verified_memory_compounding_breakthrough"
    elif adjusted.get("real_sair_used") and int(adjusted.get("episode_3_certificates", 0) or 0) > 0:
        adjusted["final_classification"] = "durable_certificate_breakthrough_no_positive_compounding"
    elif not adjusted.get("real_sair_used"):
        adjusted["final_classification"] = "safe_infrastructure_only"
    return adjusted


def write_policy_artifacts(policy: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    selected = pd.DataFrame(policy.get("selected_components", []))
    rejected = pd.DataFrame(policy.get("rejected_components", []))
    paths = {
        "canonical_policy.json": root / "canonical_policy.json",
        "canonical_policy.csv": root / "canonical_policy.csv",
        "selected_components.csv": root / "selected_components.csv",
        "rejected_components.csv": root / "rejected_components.csv",
        "policy_rationale.md": root / "policy_rationale.md",
    }
    paths["canonical_policy.json"].write_text(json.dumps(policy, indent=2, sort_keys=True, default=str), encoding="utf-8")
    pd.concat([selected, rejected], ignore_index=True).to_csv(paths["canonical_policy.csv"], index=False)
    _write_csv(paths["selected_components.csv"], selected)
    _write_csv(paths["rejected_components.csv"], rejected)
    lines = [
        "# SAIR Stage 2 Canonical Policy",
        "",
        "This policy is advisory route selection only. It cannot promote truth.",
        "",
        "## Selected Components",
        *[f"- `{row.get('component')}`: {row.get('reason')}" for row in policy.get("selected_components", [])],
        "",
        "## Rejected Components",
        *[f"- `{row.get('component')}`: {row.get('reason')}" for row in policy.get("rejected_components", [])],
        "",
    ]
    paths["policy_rationale.md"].write_text("\n".join(lines), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def load_policy(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _rule(component: str, selected: bool, reason: str, marginal_gain: float, support: int) -> dict[str, Any]:
    return SairStage2PolicyRule(
        component=component,
        selected=selected,
        reason=reason,
        marginal_gain=float(marginal_gain),
        support=int(support),
        advisory_only=True,
        can_promote_truth=False,
    ).__dict__


def _write_csv(path: Path, frame: pd.DataFrame) -> None:
    if frame.empty:
        frame = pd.DataFrame([{"empty_table_name": path.stem, "row_count": 0, "note": "not applicable"}])
    frame.to_csv(path, index=False)
