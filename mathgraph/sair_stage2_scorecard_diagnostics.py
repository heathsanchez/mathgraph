"""Scorecard diagnostics for the official SAIR Stage 2 evidence pack."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class SairStage2ComponentDiagnostic:
    component: str
    episode: int
    yield_count: float
    residual_count: float
    marginal_gain: float
    gain_over_baseline: float
    attempt_cost_per_certificate: float | None
    support: int
    classification: str
    advisory_only: bool
    can_promote_truth: bool


def load_evidence_pack(out_dir: str | Path) -> dict[str, Any]:
    root = Path(out_dir)
    return {
        "summary": _read_json(root / "sair_stage2_evidence_summary.json"),
        "episode_metrics": _read_csv(root / "episode_metrics.csv"),
        "heldout": _read_json(root / "heldout_compounding_report.json"),
        "trust": _read_json(root / "trust_boundary_audit.json"),
        "certificates": _read_csv(root / "certificate_manifest.csv"),
        "residuals": _read_csv(root / "residual_frontier.csv"),
        "obstructions": _read_csv(root / "named_obstructions.csv"),
    }


def diagnose_scorecard(out_dir: str | Path, *, min_support: int = 1) -> dict[str, Any]:
    artifacts = load_evidence_pack(out_dir)
    component_frame = build_component_diagnostics(artifacts, min_support=min_support)
    safety = trust_boundary_counts(artifacts)
    summary = {
        "out_dir": str(out_dir),
        "baseline_yield": _component_value(component_frame, "baseline", "yield_count"),
        "lawbook_yield": _component_value(component_frame, "lawbook", "yield_count"),
        "microbasin_yield": _component_value(component_frame, "microbasin", "yield_count"),
        "repair_yield": _component_value(component_frame, "repair", "yield_count"),
        "combined_yield": float(component_frame["yield_count"].max()) if not component_frame.empty else 0.0,
        "total_gain_over_baseline": float(_component_value(component_frame, "combined", "gain_over_baseline")),
        "helpful_components": _components_by_class(component_frame, "helpful"),
        "harmful_components": _components_by_class(component_frame, "harmful"),
        "neutral_components": _components_by_class(component_frame, "neutral"),
        "unstable_components": _components_by_class(component_frame, "unstable"),
        "overfit_components": _components_by_class(component_frame, "overfit"),
        "insufficient_support_components": _components_by_class(component_frame, "insufficient_support"),
        **safety,
    }
    return {"summary": summary, "components": component_frame, "artifacts": artifacts}


def write_scorecard_diagnostics(out_dir: str | Path, diagnostics: dict[str, Any]) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    component_path = root / "component_marginal_contributions.csv"
    scorecard_path = root / "breakthrough_scorecard.csv"
    summary_path = root / "scorecard_diagnostics_summary.json"
    diagnostics["components"].to_csv(component_path, index=False)
    pd.DataFrame([diagnostics["summary"]]).to_csv(scorecard_path, index=False)
    summary_path.write_text(json.dumps(diagnostics["summary"], indent=2, sort_keys=True, default=str), encoding="utf-8")
    return {
        "component_marginal_contributions.csv": str(component_path),
        "breakthrough_scorecard.csv": str(scorecard_path),
        "scorecard_diagnostics_summary.json": str(summary_path),
    }


def build_component_diagnostics(artifacts: dict[str, Any], *, min_support: int = 1) -> pd.DataFrame:
    summary = artifacts.get("summary", {})
    episodes = artifacts.get("episode_metrics", pd.DataFrame())
    trust = artifacts.get("trust", {})
    rows: list[dict[str, Any]] = []
    mapping = [
        ("baseline", 0),
        ("lawbook", 1),
        ("microbasin", 2),
        ("repair", 3),
    ]
    previous_yield = 0.0
    baseline_yield = 0.0
    for component, episode in mapping:
        row = _episode_row(episodes, episode)
        yield_count = float(row.get("certificates", 0) or 0)
        residual_count = float(row.get("residuals", 0) or 0)
        attempts = float(row.get("attempts", 0) or 0)
        if episode == 0:
            baseline_yield = yield_count
            marginal = 0.0
        else:
            marginal = yield_count - previous_yield
        support = int(max(0, yield_count))
        rows.append(
            SairStage2ComponentDiagnostic(
                component=component,
                episode=episode,
                yield_count=yield_count,
                residual_count=residual_count,
                marginal_gain=marginal,
                gain_over_baseline=yield_count - baseline_yield,
                attempt_cost_per_certificate=(attempts / yield_count) if yield_count > 0 and attempts > 0 else None,
                support=support,
                classification=_classify_component(component, marginal, support, min_support),
                advisory_only=component != "baseline",
                can_promote_truth=False,
            ).__dict__
        )
        previous_yield = yield_count
    combined = max(rows, key=lambda item: item["yield_count"]) if rows else {"yield_count": 0, "residual_count": 0}
    rows.append(
        {
            "component": "combined",
            "episode": 99,
            "yield_count": combined["yield_count"],
            "residual_count": combined["residual_count"],
            "marginal_gain": float(summary.get("total_gain_over_baseline", combined["yield_count"] - baseline_yield) or 0),
            "gain_over_baseline": combined["yield_count"] - baseline_yield,
            "attempt_cost_per_certificate": summary.get("attempt_cost_per_certificate_final"),
            "support": int(combined["yield_count"]),
            "classification": "helpful" if combined["yield_count"] - baseline_yield > 0 else "neutral",
            "advisory_only": True,
            "can_promote_truth": False,
        }
    )
    frame = pd.DataFrame(rows)
    safety = trust_boundary_counts(artifacts)
    for key, value in safety.items():
        frame[key] = value
    return frame


def trust_boundary_counts(artifacts: dict[str, Any]) -> dict[str, int | bool]:
    trust = artifacts.get("trust", {})
    failed = int(trust.get("failed_search_promoted_true_count", 0) or 0)
    advisory = int(trust.get("advisory_promoted_truth_count", 0) or 0)
    true_contam = int(trust.get("true_contamination_count", 0) or 0)
    unsafe = int(trust.get("unsafe_certificate_rejected_count", 0) or 0)
    return {
        "failed_search_promoted_true_count": failed,
        "advisory_promoted_truth_count": advisory,
        "true_contamination_count": true_contam,
        "unsafe_certificate_rejected_count": unsafe,
        "strict_admission_passed": bool(trust.get("strict_admission_passed", False) and failed == 0 and advisory == 0 and true_contam == 0 and unsafe == 0),
    }


def breakthrough_gate_passed(summary: dict[str, Any], *, min_total_gain: float = 0.0, min_lawbook_gain: float = 0.0, min_certificates: int = 1) -> bool:
    return bool(
        summary.get("real_sair_used", False)
        and summary.get("strict_admission_passed", False)
        and float(summary.get("total_gain_over_baseline", 0) or 0) > min_total_gain
        and float(summary.get("lawbook_gain_over_baseline", 0) or 0) >= min_lawbook_gain
        and int(summary.get("episode_3_certificates", summary.get("accepted_false_count", 0)) or 0) >= min_certificates
    )


def _classify_component(component: str, marginal_gain: float, support: int, min_support: int) -> str:
    if component == "baseline":
        return "required"
    if support < min_support:
        return "insufficient_support"
    if marginal_gain > 0:
        return "helpful"
    if marginal_gain < 0:
        return "harmful"
    return "neutral"


def _episode_row(episodes: pd.DataFrame, episode: int) -> dict[str, Any]:
    if episodes.empty or "episode" not in episodes:
        return {}
    match = episodes[pd.to_numeric(episodes["episode"], errors="coerce") == episode]
    if match.empty:
        return {}
    return match.iloc[0].to_dict()


def _components_by_class(frame: pd.DataFrame, label: str) -> list[str]:
    if frame.empty or "classification" not in frame:
        return []
    return [str(value) for value in frame.loc[frame["classification"] == label, "component"].tolist()]


def _component_value(frame: pd.DataFrame, component: str, column: str) -> float:
    if frame.empty or column not in frame:
        return 0.0
    match = frame[frame["component"] == component]
    if match.empty:
        return 0.0
    return float(match[column].iloc[0] or 0)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()
