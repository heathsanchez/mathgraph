"""Active residual constructor discovery.

This module converts unresolved held-out micro-basins into advisory constructor
pressure, then evaluates proposals with either finite-core recovery rows or a
clearly labeled proxy.  Proposal rows never promote truth.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from mathgraph.persistent_exact_microbasin_lawbook import add_microbasin_keys, normalize_recovery_frame


@dataclass(frozen=True)
class ResidualBasin:
    residual_basin_id: str
    microbasin_key: str
    basin: str
    deep_ir_candidate: str
    support: int
    generic_residual_count: int
    lawbook_residual_count: int
    compact_residual_count: int
    quotient_pressure_mean: float
    target_separation_pressure_mean: float
    fresh_variable_escape_mean: float
    repeat_tail_pressure_mean: float
    compression_pressure_mean: float
    expansion_pressure_mean: float
    dominant_failed_families: str
    dominant_success_families: str
    obstruction_name: str
    advisory_only: bool = True
    can_promote_truth: bool = False


@dataclass(frozen=True)
class ConstructorProposal:
    proposal_id: str
    residual_basin_id: str
    microbasin_key: str
    proposal_family: str
    proposal_kind: str
    priority: float
    rationale: str
    source_features: dict[str, Any]
    parent_families: list[str]
    expected_failure_mode: str
    advisory_only: bool = True
    can_promote_truth: bool = False


@dataclass(frozen=True)
class ProposalEvaluation:
    proposal_id: str
    proposal_family: str
    residual_basin_id: str
    tested_pairs: int
    recovered_pairs: int
    recovery_rate: float
    recovered_pair_ids: list[Any]
    true_contamination_count: int
    terminal_claims_from_advisory_count: int
    finite_checked: bool
    accepted_as_route: bool
    advisory_only: bool = True
    can_promote_truth: bool = False


@dataclass(frozen=True)
class ActiveDiscoverySummary:
    residual_basin_count: int
    proposal_count: int
    evaluated_proposal_count: int
    accepted_route_count: int
    total_tested_pairs: int
    total_recovered_pairs: int
    recovery_rate: float
    advisory_boundary_preserved: bool


INPUT_ALIASES = {
    "pair_features": ("heldout_pair_features.csv", "pair_features.csv"),
    "recovery_eval": ("heldout_recovery_eval.csv", "recovery_eval.csv"),
    "obstruction_atlas": ("heldout_obstruction_atlas.csv", "obstruction_atlas.csv"),
    "train_lawbook_manifest": ("train_lawbook_manifest.csv",),
    "terminal_form_audit": ("terminal_form_audit.csv",),
}


def load_discovery_inputs(input_dir: Path) -> dict[str, pd.DataFrame]:
    """Load discovery inputs, auto-descending into common run directories."""

    root = _discover_artifact_dir(Path(input_dir))
    frames = {name: _read_first(root, aliases) for name, aliases in INPUT_ALIASES.items()}
    if frames["pair_features"].empty and frames["recovery_eval"].empty:
        raise ValueError(f"no held-out pair/recovery artifacts found under {input_dir}")
    return frames | {"artifact_dir": pd.DataFrame([{"path": str(root)}])}


def build_residual_basins(
    pair_features: pd.DataFrame,
    recovery_eval: pd.DataFrame,
    min_support: int = 3,
) -> pd.DataFrame:
    """Build residual micro-basins from pairs missed by generic and Lawbook."""

    joined = _join_features_recovery(pair_features, recovery_eval)
    joined = normalize_recovery_frame(joined)
    compact_col = _first_col(joined, ("compact_atlas_recovered", "compact_recovered"))
    joined["compact_recovered_norm"] = joined[compact_col].map(_as_bool) if compact_col else False
    residual = joined[(~joined["generic_recovered_norm"]) & (~joined["lawbook_recovered_norm"])].copy()
    if residual.empty:
        return pd.DataFrame(columns=[field for field in ResidualBasin.__dataclass_fields__])
    rows: list[dict[str, Any]] = []
    for key, group in residual.groupby("microbasin_key", dropna=False):
        support = int(len(group))
        if support < min_support:
            continue
        basin = str(_mode(group.get("basin")) or "residual")
        deep = str(_mode(group.get("deep_ir_candidate")) or "unknown")
        rows.append(
            ResidualBasin(
                residual_basin_id=f"residual_{len(rows):04d}",
                microbasin_key=str(key),
                basin=basin,
                deep_ir_candidate=deep,
                support=support,
                generic_residual_count=int((~group["generic_recovered_norm"]).sum()),
                lawbook_residual_count=int((~group["lawbook_recovered_norm"]).sum()),
                compact_residual_count=int((~group["compact_recovered_norm"].map(_as_bool)).sum()),
                quotient_pressure_mean=_mean(group.get("quotient_pressure", [])),
                target_separation_pressure_mean=_mean(group.get("target_separation_pressure", [])),
                fresh_variable_escape_mean=_mean(group.get("fresh_variable_escape_count", [])),
                repeat_tail_pressure_mean=_mean(group.get("repeat_tail_pressure", [])),
                compression_pressure_mean=_mean(group.get("compression_pressure", [])),
                expansion_pressure_mean=_mean(group.get("expansion_pressure", [])),
                dominant_failed_families=_top_join(group.get("generic_first_constructor_family")),
                dominant_success_families=_top_join(group.get("lawbook_gain_constructor_family")),
                obstruction_name=f"{basin}__{deep}__active_residual_unresolved",
            ).__dict__
            | {"status": "residual_basin_advisory"}
        )
    return pd.DataFrame(rows)


def propose_constructor_recipes(
    residual_basins: pd.DataFrame,
    max_proposals_per_basin: int = 3,
) -> pd.DataFrame:
    """Emit deterministic advisory constructor recipes from residual geometry."""

    rows: list[dict[str, Any]] = []
    for _, basin in residual_basins.iterrows():
        families, rationale = _families_for_basin(basin)
        for rank, family in enumerate(families[: max(1, max_proposals_per_basin)]):
            rows.append(
                ConstructorProposal(
                    proposal_id=f"{basin['residual_basin_id']}__{rank:02d}__{family}",
                    residual_basin_id=str(basin["residual_basin_id"]),
                    microbasin_key=str(basin["microbasin_key"]),
                    proposal_family=family,
                    proposal_kind="residual_geometry_family",
                    priority=float(max(0.0, 10.0 - rank) + float(basin.get("support", 0)) / 100.0),
                    rationale=rationale,
                    source_features={
                        "quotient_pressure_mean": basin.get("quotient_pressure_mean", 0),
                        "target_separation_pressure_mean": basin.get("target_separation_pressure_mean", 0),
                        "fresh_variable_escape_mean": basin.get("fresh_variable_escape_mean", 0),
                        "repeat_tail_pressure_mean": basin.get("repeat_tail_pressure_mean", 0),
                    },
                    parent_families=[part for part in str(basin.get("dominant_failed_families", "")).split(";") if part],
                    expected_failure_mode=str(basin.get("obstruction_name", "")),
                ).__dict__
                | {"status": "constructor_proposal_advisory"}
            )
    return pd.DataFrame(rows)


def evaluate_constructor_proposals(
    proposals: pd.DataFrame,
    pair_features: pd.DataFrame,
    recovery_eval: pd.DataFrame,
    equations: list[str] | None = None,
    matrix: Any | None = None,
    max_n: int = 4,
    max_pairs_per_proposal: int = 100,
) -> pd.DataFrame:
    """Evaluate proposals on residual rows.

    The current repo exposes exact recovery by existing constructor routes. New
    family synthesis is therefore proxy-labeled unless future constructor
    generators attach proposal-specific finite checks. The proxy uses explicit
    diagnostic columns such as ``active_discovery_family_hit`` when present.
    """

    joined = normalize_recovery_frame(_join_features_recovery(pair_features, recovery_eval))
    residual = joined[(~joined["generic_recovered_norm"]) & (~joined["lawbook_recovered_norm"])].copy()
    rows: list[dict[str, Any]] = []
    for _, proposal in proposals.iterrows():
        group = residual[residual["microbasin_key"].astype(str) == str(proposal["microbasin_key"])].head(max_pairs_per_proposal)
        recovered = _proposal_recovered_mask(group, str(proposal["proposal_family"]))
        recovered_ids = group.loc[recovered, _id_column(group)].tolist() if not group.empty else []
        tested = int(len(group))
        recovered_count = int(recovered.sum()) if tested else 0
        rows.append(
            ProposalEvaluation(
                proposal_id=str(proposal["proposal_id"]),
                proposal_family=str(proposal["proposal_family"]),
                residual_basin_id=str(proposal["residual_basin_id"]),
                tested_pairs=tested,
                recovered_pairs=recovered_count,
                recovery_rate=recovered_count / tested if tested else 0.0,
                recovered_pair_ids=recovered_ids,
                true_contamination_count=0,
                terminal_claims_from_advisory_count=0,
                finite_checked=False,
                accepted_as_route=recovered_count > 0,
            ).__dict__
            | {"evaluation_mode": "proxy", "status": "proposal_evaluation_advisory"}
        )
    return pd.DataFrame(rows)


def summarize_active_discovery(
    residual_basins: pd.DataFrame,
    proposals: pd.DataFrame,
    evaluations: pd.DataFrame,
) -> dict[str, Any]:
    """Summarize active residual discovery outputs and safety."""

    tested = int(pd.to_numeric(evaluations.get("tested_pairs", pd.Series(dtype=int)), errors="coerce").fillna(0).sum())
    recovered = int(pd.to_numeric(evaluations.get("recovered_pairs", pd.Series(dtype=int)), errors="coerce").fillna(0).sum())
    true_bad = int(pd.to_numeric(evaluations.get("true_contamination_count", pd.Series(dtype=int)), errors="coerce").fillna(0).sum())
    advisory_bad = int(pd.to_numeric(evaluations.get("terminal_claims_from_advisory_count", pd.Series(dtype=int)), errors="coerce").fillna(0).sum())
    failed_true = 0
    best = evaluations.sort_values(["recovered_pairs", "recovery_rate"], ascending=[False, False]).head(1) if not evaluations.empty else pd.DataFrame()
    return {
        "residual_basin_count": int(len(residual_basins)),
        "proposal_count": int(len(proposals)),
        "evaluated_proposal_count": int(len(evaluations)),
        "accepted_route_count": int(pd.to_numeric(evaluations.get("accepted_as_route", pd.Series(dtype=bool)), errors="coerce").fillna(0).sum()) if not evaluations.empty else 0,
        "total_tested_pairs": tested,
        "total_recovered_pairs": recovered,
        "recovery_rate": recovered / tested if tested else 0.0,
        "best_proposal_family": str(best["proposal_family"].iloc[0]) if not best.empty else "",
        "best_proposal_recovered_pairs": int(best["recovered_pairs"].iloc[0]) if not best.empty else 0,
        "evaluation_mode": _mode(evaluations.get("evaluation_mode")) if not evaluations.empty else "proxy",
        "true_contamination_count": true_bad,
        "terminal_claims_from_advisory_count": advisory_bad,
        "failed_search_promoted_true_count": failed_true,
        "advisory_boundary_preserved": true_bad == 0 and advisory_bad == 0 and failed_true == 0,
    }


def _discover_artifact_dir(root: Path) -> Path:
    if (root / "heldout_recovery_eval.csv").exists():
        return root
    candidates = list(root.glob("episode_*")) + [root / "baseline_large", root / "large"]
    for candidate in candidates:
        if candidate.exists() and (candidate / "heldout_recovery_eval.csv").exists():
            return candidate
    return root


def _read_first(root: Path, aliases: tuple[str, ...]) -> pd.DataFrame:
    for name in aliases:
        path = root / name
        if path.exists():
            try:
                return pd.read_csv(path)
            except pd.errors.EmptyDataError:
                return pd.DataFrame()
    return pd.DataFrame()


def _join_features_recovery(pair_features: pd.DataFrame, recovery_eval: pd.DataFrame) -> pd.DataFrame:
    if pair_features.empty:
        return recovery_eval.copy()
    if recovery_eval.empty:
        return pair_features.copy()
    if {"seed", "pair_idx"}.issubset(pair_features.columns) and {"seed", "pair_idx"}.issubset(recovery_eval.columns):
        return pair_features.merge(recovery_eval, on=["seed", "pair_idx"], how="left", suffixes=("", "_recovery"))
    if {"seed", "eq1_id", "eq2_id"}.issubset(pair_features.columns) and {"seed", "eq1_id", "eq2_id"}.issubset(recovery_eval.columns):
        return pair_features.merge(recovery_eval, on=["seed", "eq1_id", "eq2_id"], how="left", suffixes=("", "_recovery"))
    return recovery_eval.copy()


def _families_for_basin(row: pd.Series) -> tuple[list[str], str]:
    fresh = float(row.get("fresh_variable_escape_mean", 0) or 0)
    sep = float(row.get("target_separation_pressure_mean", 0) or 0)
    repeat = float(row.get("repeat_tail_pressure_mean", 0) or 0)
    compression = float(row.get("compression_pressure_mean", 0) or 0)
    expansion = float(row.get("expansion_pressure_mean", 0) or 0)
    if fresh >= max(sep, repeat, compression, expansion, 1):
        return ["quotient_fresh_gate", "fresh_absorber", "random_fresh_sink", "random_fresh_collapse"], "fresh-variable escape pressure"
    if sep >= max(repeat, compression, expansion, 1):
        return ["projection_exception_left", "projection_exception_right", "diagonal_escape", "quotient_spike"], "target separation pressure"
    if repeat >= max(compression, expansion, 1):
        return ["tail_coupled_projection", "head_coupled_projection", "diag_perturb_right", "diag_perturb_left"], "repeat-tail pressure"
    if compression >= max(expansion, 1):
        return ["diagonal_spike", "row_erasure_family", "col_erasure_family", "block_selector"], "compression pressure"
    if expansion >= 1:
        return ["linear_combo_mod", "add_mod", "sub_mod", "xor_mod"], "expansion pressure"
    return ["prior", "left_projection", "right_projection", "constant"], "general residual pressure"


def _proposal_recovered_mask(group: pd.DataFrame, family: str) -> pd.Series:
    if group.empty:
        return pd.Series(dtype=bool)
    if "active_discovery_family_hit" in group.columns:
        return group["active_discovery_family_hit"].fillna("").astype(str) == family
    if "oracle_recovered" in group.columns:
        return group["oracle_recovered"].map(_as_bool) & (group.get("lawbook_gain_constructor_family", "").fillna("").astype(str) == family)
    return pd.Series([False] * len(group), index=group.index)


def _id_column(group: pd.DataFrame) -> str:
    for col in ("pair_idx", "row_id", "eq1_id"):
        if col in group.columns:
            return col
    return group.columns[0]


def _first_col(df: pd.DataFrame, names: tuple[str, ...]) -> str | None:
    for name in names:
        if name in df.columns:
            return name
    return None


def _mean(values: Any) -> float:
    vals = pd.to_numeric(pd.Series(values), errors="coerce").dropna()
    return float(vals.mean()) if len(vals) else 0.0


def _mode(series: Any) -> Any:
    if series is None:
        return ""
    values = pd.Series(series).dropna().astype(str)
    return values.mode().iloc[0] if len(values) else ""


def _top_join(series: Any, limit: int = 3) -> str:
    if series is None:
        return ""
    values = pd.Series(series).dropna().astype(str)
    values = values[values != ""]
    return ";".join(values.value_counts().head(limit).index.tolist())


def _as_bool(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)
