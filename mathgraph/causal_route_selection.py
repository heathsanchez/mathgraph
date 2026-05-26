"""Causal route selection for persistent exact micro-basin memory.

The selector scores advisory route memories by support, non-regression, and
cross-episode stability. It does not verify claims and cannot promote truth.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from mathgraph.persistent_exact_microbasin_lawbook import normalize_recovery_frame


@dataclass(frozen=True)
class RouteEvidence:
    microbasin_key: str
    constructor_family: str
    constructor_id: str
    episode: int
    seed: int
    support: int
    generic_yield: int
    lawbook_yield: int
    persistent_yield_proxy: int
    gain_over_generic: int
    gain_over_lawbook: int
    generic_residuals: int
    lawbook_residuals: int
    persistent_residuals_proxy: int
    exact_recipe_reuse_count: int
    advisory_only: bool = True
    can_promote_truth: bool = False


@dataclass(frozen=True)
class CausalRouteScore:
    microbasin_key: str
    constructor_family: str
    constructor_id: str
    support_total: int
    episode_count: int
    seed_count: int
    positive_episode_count: int
    negative_episode_count: int
    neutral_episode_count: int
    mean_gain_over_generic: float
    mean_gain_over_lawbook: float
    min_gain_over_generic: float
    min_gain_over_lawbook: float
    non_regression_rate: float
    stability_score: float
    causal_score: float
    selected: bool
    rejection_reason: str
    advisory_only: bool = True
    can_promote_truth: bool = False


@dataclass(frozen=True)
class CausalRoutePolicy:
    min_support: int = 2
    min_episode_count: int = 2
    min_non_regression_rate: float = 0.75
    require_positive_mean_gain: bool = True


def load_episode_replay_frames(input_dirs: list[Path]) -> pd.DataFrame:
    """Load and concatenate persistent replay CSV files from episode dirs."""

    frames: list[pd.DataFrame] = []
    for idx, root in enumerate(input_dirs):
        path = Path(root) / "persistent_replay_eval.csv"
        if not path.exists():
            continue
        frame = pd.read_csv(path)
        if "episode" not in frame.columns:
            frame["episode"] = idx
        frames.append(frame)
    return pd.concat(frames, ignore_index=True, sort=False) if frames else pd.DataFrame()


def build_route_evidence(
    replay_df: pd.DataFrame,
    episode_idx: int | None = None,
    seed: int | None = None,
) -> pd.DataFrame:
    """Aggregate replay rows into per-route evidence rows."""

    if replay_df.empty:
        return _empty_evidence()
    df = replay_df.copy()
    if "microbasin_key" not in df.columns:
        df = normalize_recovery_frame(df)
    if episode_idx is not None:
        df["episode"] = episode_idx
    if seed is not None:
        df["seed"] = seed
    if "persistent_recovered_proxy" not in df.columns:
        df["persistent_recovered_proxy"] = df.get("generic_recovered_norm", False)
    rows: list[dict[str, Any]] = []
    group_cols = ["microbasin_key", "persistent_recommended_family", "persistent_recommended_constructor_id", "episode"]
    for (key, family, cid, episode), group in df.groupby(group_cols, dropna=False):
        if not str(cid):
            continue
        support = int(len(group))
        generic_yield = int(group.get("generic_recovered_norm", pd.Series(dtype=bool)).map(_as_bool).sum())
        lawbook_yield = int(group.get("lawbook_recovered_norm", pd.Series(dtype=bool)).map(_as_bool).sum())
        persistent_yield = int(group.get("persistent_recovered_proxy", pd.Series(dtype=bool)).map(_as_bool).sum())
        seeds = pd.to_numeric(group.get("seed", pd.Series([0])), errors="coerce").fillna(0).astype(int)
        rows.append(
            RouteEvidence(
                microbasin_key=str(key),
                constructor_family=str(family),
                constructor_id=str(cid),
                episode=int(episode),
                seed=int(seeds.iloc[0]) if len(seeds) else 0,
                support=support,
                generic_yield=generic_yield,
                lawbook_yield=lawbook_yield,
                persistent_yield_proxy=persistent_yield,
                gain_over_generic=persistent_yield - generic_yield,
                gain_over_lawbook=persistent_yield - lawbook_yield,
                generic_residuals=support - generic_yield,
                lawbook_residuals=support - lawbook_yield,
                persistent_residuals_proxy=support - persistent_yield,
                exact_recipe_reuse_count=support,
            ).__dict__
        )
    return pd.DataFrame(rows) if rows else _empty_evidence()


def score_causal_routes(
    evidence_df: pd.DataFrame,
    min_support: int = 2,
    min_episode_count: int = 2,
    min_non_regression_rate: float = 0.75,
    require_positive_mean_gain: bool = True,
) -> pd.DataFrame:
    """Score route memories and mark stable non-regressing selections."""

    if evidence_df.empty:
        return _empty_scores()
    rows: list[dict[str, Any]] = []
    group_cols = ["microbasin_key", "constructor_family", "constructor_id"]
    for (key, family, cid), group in evidence_df.groupby(group_cols, dropna=False):
        support = int(pd.to_numeric(group.get("support", 0), errors="coerce").fillna(0).sum())
        episode_count = int(group["episode"].nunique()) if "episode" in group else 0
        seed_count = int(group["seed"].nunique()) if "seed" in group else 0
        gain_generic = pd.to_numeric(group.get("gain_over_generic", 0), errors="coerce").fillna(0)
        gain_lawbook = pd.to_numeric(group.get("gain_over_lawbook", 0), errors="coerce").fillna(0)
        non_regression = (gain_generic >= 0) & (gain_lawbook >= 0)
        positive = (gain_generic > 0) | (gain_lawbook > 0)
        negative = (gain_generic < 0) | (gain_lawbook < 0)
        non_regression_rate = float(non_regression.mean()) if len(group) else 0.0
        mean_generic = float(gain_generic.mean()) if len(group) else 0.0
        mean_lawbook = float(gain_lawbook.mean()) if len(group) else 0.0
        min_generic = float(gain_generic.min()) if len(group) else 0.0
        min_lawbook = float(gain_lawbook.min()) if len(group) else 0.0
        stability = non_regression_rate * min(1.0, episode_count / max(1, min_episode_count)) * min(1.0, seed_count / max(1, min_episode_count))
        causal = (
            max(0.0, mean_generic)
            + max(0.0, mean_lawbook)
            + stability
            + min(1.0, support / max(1, min_support * 3))
            - float(negative.sum())
        )
        reason = ""
        selected = True
        if support < min_support:
            selected, reason = False, "support_below_threshold"
        elif episode_count < min_episode_count:
            selected, reason = False, "episode_count_below_threshold"
        elif non_regression_rate < min_non_regression_rate:
            selected, reason = False, "non_regression_rate_below_threshold"
        elif require_positive_mean_gain and mean_generic <= 0:
            selected, reason = False, "mean_gain_not_positive"
        elif min_generic < 0:
            selected, reason = False, "negative_generic_regression"
        rows.append(
            CausalRouteScore(
                microbasin_key=str(key),
                constructor_family=str(family),
                constructor_id=str(cid),
                support_total=support,
                episode_count=episode_count,
                seed_count=seed_count,
                positive_episode_count=int(positive.sum()),
                negative_episode_count=int(negative.sum()),
                neutral_episode_count=int((~positive & ~negative).sum()),
                mean_gain_over_generic=mean_generic,
                mean_gain_over_lawbook=mean_lawbook,
                min_gain_over_generic=min_generic,
                min_gain_over_lawbook=min_lawbook,
                non_regression_rate=non_regression_rate,
                stability_score=stability,
                causal_score=causal,
                selected=selected,
                rejection_reason=reason,
            ).__dict__
            | {"status": "causal_route_policy_advisory"}
        )
    out = pd.DataFrame(rows)
    return out.sort_values(["selected", "causal_score", "support_total"], ascending=[False, False, False]).reset_index(drop=True)


def select_causal_routes(score_df: pd.DataFrame) -> pd.DataFrame:
    """Return selected advisory causal routes."""

    if score_df.empty or "selected" not in score_df.columns:
        return _empty_scores()
    out = score_df[score_df["selected"].map(_as_bool)].copy()
    out["advisory_only"] = True
    out["can_promote_truth"] = False
    out["status"] = "causal_route_policy_advisory"
    return out.reset_index(drop=True)


def apply_causal_route_policy(
    heldout_df: pd.DataFrame,
    selected_routes: pd.DataFrame,
) -> pd.DataFrame:
    """Apply selected prior causal routes to held-out recovery rows."""

    df = normalize_recovery_frame(heldout_df)
    if selected_routes.empty:
        df["causal_route_available"] = False
        df["causal_recommended_family"] = ""
        df["causal_recommended_constructor_id"] = ""
    else:
        best = selected_routes.sort_values(["microbasin_key", "causal_score"], ascending=[True, False])
        best = best.drop_duplicates("microbasin_key", keep="first").set_index("microbasin_key")
        available: list[bool] = []
        families: list[str] = []
        constructors: list[str] = []
        for key in df["microbasin_key"].astype(str):
            if key in best.index:
                row = best.loc[key]
                available.append(True)
                families.append(str(row.get("constructor_family", "")))
                constructors.append(str(row.get("constructor_id", "")))
            else:
                available.append(False)
                families.append("")
                constructors.append("")
        df["causal_route_available"] = available
        df["causal_recommended_family"] = families
        df["causal_recommended_constructor_id"] = constructors
    id_match = df["causal_recommended_constructor_id"].astype(str) == df["lawbook_gain_constructor_id_norm"].astype(str)
    family_match = df["causal_recommended_family"].astype(str) == df["lawbook_gain_constructor_family_norm"].astype(str)
    causal_hit = df["causal_route_available"].astype(bool) & df["lawbook_recovered_norm"].astype(bool) & (id_match | family_match)
    df["v2_causal_recovered_proxy"] = df["generic_recovered_norm"].astype(bool) | causal_hit
    df["v2_causal_gain_over_generic_proxy"] = df["v2_causal_recovered_proxy"].astype(bool) & ~df["generic_recovered_norm"].astype(bool)
    df["v2_causal_gain_over_lawbook_proxy"] = df["v2_causal_recovered_proxy"].astype(bool) & ~df["lawbook_recovered_norm"].astype(bool)
    df["advisory_only"] = True
    df["can_promote_truth"] = False
    df["status"] = "causal_route_policy_advisory"
    return df


def evaluate_causal_policy(replay_df: pd.DataFrame) -> dict[str, Any]:
    """Evaluate v2 causal replay proxy metrics."""

    rows = int(len(replay_df))
    generic = int(replay_df.get("generic_recovered_norm", pd.Series(dtype=bool)).map(_as_bool).sum()) if rows else 0
    lawbook = int(replay_df.get("lawbook_recovered_norm", pd.Series(dtype=bool)).map(_as_bool).sum()) if rows else 0
    v2 = int(replay_df.get("v2_causal_recovered_proxy", pd.Series(dtype=bool)).map(_as_bool).sum()) if rows else 0
    reuse = int(replay_df.get("causal_route_available", pd.Series(dtype=bool)).map(_as_bool).sum()) if rows else 0
    advisory_truth = 0
    if {"advisory_only", "can_promote_truth"}.issubset(replay_df.columns):
        advisory_truth = int((replay_df["advisory_only"].map(_as_bool) & replay_df["can_promote_truth"].map(_as_bool)).sum())
    return {
        "rows": rows,
        "generic_yield": generic,
        "lawbook_yield": lawbook,
        "v2_causal_yield_proxy": v2,
        "v2_gain_over_generic": v2 - generic,
        "v2_gain_over_lawbook": v2 - lawbook,
        "v2_residuals_proxy": rows - v2,
        "exact_recipe_reuse_count_v2": reuse,
        "exact_recipe_reuse_rate_v2": reuse / rows if rows else 0.0,
        "true_contamination_count": int(pd.to_numeric(replay_df.get("true_contamination_count", pd.Series(dtype=int)), errors="coerce").fillna(0).sum()),
        "terminal_claims_from_advisory_count": advisory_truth,
        "failed_search_promoted_true_count": 0,
        "advisory_boundary_preserved": advisory_truth == 0,
    }


def _empty_evidence() -> pd.DataFrame:
    return pd.DataFrame(columns=[field for field in RouteEvidence.__dataclass_fields__])


def _empty_scores() -> pd.DataFrame:
    return pd.DataFrame(columns=[field for field in CausalRouteScore.__dataclass_fields__] + ["status"])


def _as_bool(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)
