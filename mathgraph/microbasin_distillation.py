"""Micro-basin causal distillation for advisory Lawbook route evidence.

The functions in this module summarize held-out recovery artifacts into
micro-basin route recipes. They do not verify claims and cannot promote truth.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class MicrobasinKeyConfig:
    q_bins: int = 4
    min_support: int = 3
    min_gain: int = 1
    include_basin: bool = True
    include_deep_ir: bool = True
    include_quantile_bins: bool = True
    include_skeleton_flag: bool = True


@dataclass(frozen=True)
class DistillationConfig:
    input_dir: str | Path
    out_dir: str | Path
    min_microbasin_support: int = 3
    min_microbasin_gain: int = 1
    top_k_families: int = 12
    top_k_constructors: int = 12
    seed: int = 1729
    strict_safety: bool = True


@dataclass(frozen=True)
class MicrobasinDistillationResult:
    summary: dict[str, Any]
    artifacts: dict[str, str]


INPUT_ALIASES = {
    "pair_features": ("heldout_pair_features.csv", "pair_features.csv"),
    "recovery_eval": ("heldout_recovery_eval.csv", "recovery_eval.csv"),
    "joined": ("joined_recovery_features_v2.csv", "joined_recovery_features.csv"),
    "train_lawbook_manifest": ("train_lawbook_manifest.csv", "actual_microbasin_lawbook_v2.csv"),
    "obstruction_atlas": ("heldout_obstruction_atlas.csv", "obstruction_atlas.csv"),
    "policy_eval": ("per_seed_policy_eval.csv", "persistent_replay_eval_v2.csv"),
    "terminal_form_audit": ("terminal_form_audit.csv",),
    "existing_microbasin_lawbook": ("actual_microbasin_lawbook_v2.csv",),
    "persistent_replay_eval": ("persistent_replay_eval_v2.csv",),
    "residual_microbasins": ("residual_microbasins_after_persistent_v2.csv",),
}

NUMERIC_KEY_FIELDS = (
    "quotient_pressure",
    "target_separation_pressure",
    "ir_constraint_loss",
    "fresh_variable_escape_count",
    "repeat_tail_pressure",
)


def load_distillation_inputs(input_dir: str | Path) -> dict[str, pd.DataFrame]:
    """Load standard held-out or Colab v2 distillation artifacts."""

    root = Path(input_dir)
    if not root.exists():
        raise ValueError(f"input_dir does not exist: {root}")
    frames: dict[str, pd.DataFrame] = {}
    for key, aliases in INPUT_ALIASES.items():
        frames[key] = _read_first(root, aliases)
    if frames["joined"].empty:
        if frames["pair_features"].empty or frames["recovery_eval"].empty:
            raise ValueError("distillation requires joined_recovery_features or both heldout_pair_features and heldout_recovery_eval")
        frames["joined"] = join_pair_recovery_features(frames["pair_features"], frames["recovery_eval"])
    else:
        frames["joined"] = join_pair_recovery_features(frames["joined"], pd.DataFrame())
    return frames


def join_pair_recovery_features(pair_features: pd.DataFrame, recovery_eval: pd.DataFrame) -> pd.DataFrame:
    """Join PQ-IR pair features to recovery columns using stable keys."""

    pair_df = pair_features.copy()
    recovery_cols = {"generic_recovered", "lawbook_recovered", "lawbook_new_recovery", "compact_recovered", "oracle_recovered"}
    if recovery_cols & set(pair_df.columns):
        return _normalize_recovery_columns(pair_df)
    rec_df = recovery_eval.copy()
    if rec_df.empty:
        raise ValueError("recovery_eval is required when pair features do not contain recovery columns")
    if {"seed", "pair_idx"}.issubset(pair_df.columns) and {"seed", "pair_idx"}.issubset(rec_df.columns):
        joined = pair_df.merge(rec_df, on=["seed", "pair_idx"], how="left", suffixes=("", "_recovery"))
    elif {"seed", "eq1_id", "eq2_id"}.issubset(pair_df.columns) and {"seed", "eq1_id", "eq2_id"}.issubset(rec_df.columns):
        joined = pair_df.merge(rec_df, on=["seed", "eq1_id", "eq2_id"], how="left", suffixes=("", "_recovery"))
    else:
        raise ValueError("cannot join pair/recovery features; need seed+pair_idx or seed+eq1_id+eq2_id")
    return _normalize_recovery_columns(joined)


def add_microbasin_keys(df: pd.DataFrame, config: MicrobasinKeyConfig) -> pd.DataFrame:
    """Add deterministic microbasin keys from PQ-IR fields."""

    out = df.copy()
    for field in NUMERIC_KEY_FIELDS:
        if config.include_quantile_bins:
            out[f"{field}_bin"] = _quantile_tokens(out[field], field, config.q_bins) if field in out.columns else [f"{field}_na"] * len(out)
        else:
            out[f"{field}_bin"] = [f"{field}_na"] * len(out)
    keys = []
    for _, row in out.iterrows():
        tokens: list[str] = []
        if config.include_basin:
            tokens.append(_token(row.get("basin", "basin_na")))
        if config.include_deep_ir:
            tokens.append(_token(row.get("deep_ir_candidate", "deep_ir_na")))
        if config.include_quantile_bins:
            tokens.extend(str(row.get(f"{field}_bin", f"{field}_na")) for field in NUMERIC_KEY_FIELDS)
        if config.include_skeleton_flag:
            tokens.append(f"skel{1 if _as_bool(row.get('skeleton_equal')) else 0}")
        keys.append("__".join(tokens))
    out["microbasin_key"] = keys
    return out


def summarize_microbasins(joined_df: pd.DataFrame, config: MicrobasinKeyConfig | None = None) -> pd.DataFrame:
    """Summarize generic and Lawbook recovery by microbasin."""

    config = config or MicrobasinKeyConfig()
    df = joined_df if "microbasin_key" in joined_df.columns else add_microbasin_keys(joined_df, config)
    rows: list[dict[str, Any]] = []
    for key, group in df.groupby("microbasin_key", dropna=False):
        support = int(len(group))
        generic = int(group["generic_recovered"].sum())
        lawbook = int(group["lawbook_recovered"].sum())
        gain = lawbook - generic
        residual_generic = support - generic
        residual_lawbook = support - lawbook
        row = {
            "microbasin_key": key,
            "support": support,
            "generic_yield": generic,
            "lawbook_yield": lawbook,
            "lawbook_gain": gain,
            "generic_rate": generic / support if support else 0.0,
            "lawbook_rate": lawbook / support if support else 0.0,
            "residual_after_generic": residual_generic,
            "residual_after_lawbook": residual_lawbook,
            "residual_only_gain": int(group["lawbook_new_recovery"].sum()),
            "basin": _mode(group.get("basin")),
            "deep_ir_candidate": _mode(group.get("deep_ir_candidate")),
            "advisory_only": True,
            "can_promote_truth": False,
            "status": "microbasin_route_advisory",
            "terminal_form": "NONE",
        }
        gain_hits = group[group["lawbook_new_recovery"].astype(bool)]
        exact_hits = gain_hits[gain_hits.get("lawbook_gain_constructor_id", pd.Series(index=gain_hits.index, dtype=object)).notna()] if not gain_hits.empty else pd.DataFrame()
        row["exact_gain_hits"] = int(len(exact_hits))
        row["exact_gain_constructor_family_count"] = int(exact_hits.get("lawbook_gain_constructor_family", pd.Series(dtype=object)).dropna().nunique()) if not exact_hits.empty else 0
        row["top_exact_gain_constructor_family"] = _top_values(exact_hits.get("lawbook_gain_constructor_family"), 1)[0] if not exact_hits.empty and _top_values(exact_hits.get("lawbook_gain_constructor_family"), 1) else ""
        row["top_exact_gain_constructor_id"] = _top_values(exact_hits.get("lawbook_gain_constructor_id"), 1)[0] if not exact_hits.empty and _top_values(exact_hits.get("lawbook_gain_constructor_id"), 1) else ""
        row["attribution_mode"] = "exact_constructor" if row["exact_gain_hits"] else "route_prior_proxy"
        for field in NUMERIC_KEY_FIELDS:
            if f"{field}_bin" in group.columns:
                row[f"{field}_bin"] = _mode(group[f"{field}_bin"])
        rows.append(row)
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values(["lawbook_gain", "residual_only_gain", "support", "lawbook_rate"], ascending=[False, False, False, False]).reset_index(drop=True)


def attribute_lawbook_gains(joined_df: pd.DataFrame, train_lawbook_manifest: pd.DataFrame) -> pd.DataFrame:
    """Attribute marginal Lawbook recoveries to exact constructors or route priors."""

    if joined_df.empty:
        return pd.DataFrame()
    exact = {"lawbook_gain_hit", "lawbook_gain_constructor_id", "lawbook_gain_constructor_family"}.issubset(joined_df.columns)
    manifest = train_lawbook_manifest.copy()
    if manifest.empty:
        manifest = pd.DataFrame([{"family": "", "cid": "", "constructor_idx": ""}])
    rank_source = manifest["rank"] if "rank" in manifest.columns else pd.Series(range(len(manifest)), index=manifest.index)
    manifest["_rank"] = pd.to_numeric(rank_source, errors="coerce")
    manifest["_rank"] = manifest["_rank"].fillna(pd.Series(range(len(manifest)), index=manifest.index))
    manifest = manifest.sort_values("_rank")
    rows: list[dict[str, Any]] = []
    gains = joined_df[joined_df["lawbook_new_recovery"].astype(bool)]
    for _, pair in gains.iterrows():
        if exact and _as_bool(pair.get("lawbook_gain_hit")) and pd.notna(pair.get("lawbook_gain_constructor_id")):
            candidates = [
                {
                    "family": pair.get("lawbook_gain_constructor_family"),
                    "cid": pair.get("lawbook_gain_constructor_id"),
                    "constructor_idx": pair.get("lawbook_gain_constructor_idx"),
                }
            ]
            mode = "exact"
            confidence = 1.0
        else:
            candidates = manifest.head(3).to_dict("records")
            mode = "route_prior_proxy"
            confidence = 0.35
        for candidate in candidates:
            rows.append(
                {
                    "seed": pair.get("seed", candidate.get("seed", "")),
                    "microbasin_key": pair.get("microbasin_key", ""),
                    "eq1_id": pair.get("eq1_id", ""),
                    "eq2_id": pair.get("eq2_id", ""),
                    "pair_idx": pair.get("pair_idx", ""),
                    "family": candidate.get("family", pair.get("family", "")),
                    "constructor_id": candidate.get("cid", candidate.get("constructor_id", candidate.get("constructor_idx", ""))),
                    "attribution_mode": mode,
                    "attribution_confidence": confidence,
                    "lawbook_new_recovery": True,
                    "generic_recovered": bool(pair.get("generic_recovered", False)),
                    "lawbook_recovered": bool(pair.get("lawbook_recovered", False)),
                    "advisory_only": True,
                    "can_promote_truth": False,
                }
            )
    return pd.DataFrame(rows)


def distill_minimal_recipes(microbasin_summary: pd.DataFrame, attribution_df: pd.DataFrame, config: DistillationConfig) -> pd.DataFrame:
    """Distill positive-gain microbasins into minimal advisory constructor recipes."""

    rows: list[dict[str, Any]] = []
    if microbasin_summary.empty:
        return pd.DataFrame()
    positive = microbasin_summary[
        (pd.to_numeric(microbasin_summary["support"], errors="coerce").fillna(0) >= config.min_microbasin_support)
        & (pd.to_numeric(microbasin_summary["lawbook_gain"], errors="coerce").fillna(0) >= config.min_microbasin_gain)
    ]
    for _, basin in positive.iterrows():
        key = basin["microbasin_key"]
        attrs = attribution_df[attribution_df.get("microbasin_key", pd.Series(dtype=str)).astype(str) == str(key)] if not attribution_df.empty else pd.DataFrame()
        families = _top_values(attrs.get("family"), config.top_k_families)
        constructors = _top_values(attrs.get("constructor_id"), config.top_k_constructors)
        modes = set(attrs.get("attribution_mode", [])) if not attrs.empty else set()
        strength = "exact" if "exact" in modes else "proxy"
        if strength == "exact" and not attrs.empty:
            grouped = attrs.groupby(["family", "constructor_id"], dropna=False).size().reset_index(name="exact_gain_hits")
            grouped = grouped.sort_values(["exact_gain_hits", "family", "constructor_id"], ascending=[False, True, True]).head(config.top_k_constructors)
            for _, grow in grouped.iterrows():
                rows.append(_recipe_row(key, basin, [str(grow["family"])], [str(grow["constructor_id"])], strength, int(grow["exact_gain_hits"])))
        else:
            rows.append(_recipe_row(key, basin, families, constructors, strength, int(basin.get("lawbook_gain", 0))))
    return pd.DataFrame(rows)


def _recipe_row(key: str, basin: pd.Series, families: list[str], constructors: list[str], strength: str, exact_hits: int) -> dict[str, Any]:
    return {
        "microbasin_key": key,
        "basin": basin.get("basin", ""),
        "deep_ir_candidate": basin.get("deep_ir_candidate", ""),
        "constructor_family": families[0] if families else "",
        "constructor_id": constructors[0] if constructors else "",
        "exact_gain_hits": exact_hits if strength == "exact" else 0,
        "support": int(basin.get("support", 0)),
        "lawbook_gain": int(basin.get("lawbook_gain", 0)),
        "gain_rate": float(basin.get("lawbook_gain", 0)) / max(1, int(basin.get("support", 0))),
        "residual_after_lawbook": int(basin.get("residual_after_lawbook", 0)),
        "recipe_families": families,
        "recipe_constructors": constructors,
        "recipe_size": len(families) + len(constructors),
        "recipe_strength": strength,
        "attribution_mode": "exact_constructor" if strength == "exact" else "route_prior_proxy",
        "explanation": f"{strength} advisory recipe for marginal recoveries in {key}",
        "advisory_only": True,
        "can_promote_truth": False,
        "status": "microbasin_constructor_recipe_advisory",
        "terminal_form": "NONE",
    }


def summarize_residual_obstruction_targets(joined_df: pd.DataFrame, microbasin_summary: pd.DataFrame) -> pd.DataFrame:
    """Name unresolved post-Lawbook residual microbasin targets."""

    if joined_df.empty:
        return pd.DataFrame()
    residual = joined_df[(~joined_df["generic_recovered"].astype(bool)) & (~joined_df["lawbook_recovered"].astype(bool))]
    rows: list[dict[str, Any]] = []
    total = max(1, len(residual))
    summary = microbasin_summary.set_index("microbasin_key") if not microbasin_summary.empty and "microbasin_key" in microbasin_summary.columns else pd.DataFrame()
    for key, group in residual.groupby("microbasin_key", dropna=False):
        first = group.iloc[0]
        basin = str(first.get("basin", "residual"))
        deep = str(first.get("deep_ir_candidate", "unknown"))
        rows.append(
            {
                "obstruction_target_id": f"{key}__post_lawbook",
                "microbasin_key": key,
                "basin": basin,
                "deep_ir_candidate": deep,
                "residual_pairs": int(len(group)),
                "generic_hits": int(group["generic_recovered"].sum()),
                "lawbook_hits": int(group["lawbook_recovered"].sum()),
                "residual_entropy_contribution": _entropy_part(len(group), total),
                "suggested_next_constructor_pressure": _constructor_pressure(first),
                "post_exact_lawbook_residual_count": int(len(group)),
                "top_failed_microbasin": key,
                "suggested_next_constructor_family": _constructor_pressure(first),
                "obstruction_name": f"{basin}__{deep}__post_lawbook_distillation_unresolved",
                "stage": "post_lawbook_distillation",
                "status": "named_obstruction_advisory",
                "advisory_only": True,
                "can_promote_truth": False,
                "terminal_form": "NONE",
                "summary_support": int(summary.loc[key]["support"]) if not summary.empty and key in summary.index else int(len(group)),
            }
        )
    return pd.DataFrame(rows).sort_values(["residual_pairs", "microbasin_key"], ascending=[False, True]).reset_index(drop=True) if rows else pd.DataFrame()


def run_microbasin_distillation(config: DistillationConfig) -> MicrobasinDistillationResult:
    """Run the full advisory microbasin distillation pipeline."""

    out_dir = Path(config.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    inputs = load_distillation_inputs(config.input_dir)
    key_config = MicrobasinKeyConfig(min_support=config.min_microbasin_support, min_gain=config.min_microbasin_gain)
    joined = add_microbasin_keys(inputs["joined"], key_config)
    microbasins = summarize_microbasins(joined, key_config)
    attribution = attribute_lawbook_gains(joined, inputs["train_lawbook_manifest"])
    recipes = distill_minimal_recipes(microbasins, attribution, config)
    residual_targets = summarize_residual_obstruction_targets(joined, microbasins)
    safety = _safety_summary(inputs["terminal_form_audit"], [joined, microbasins, attribution, recipes, residual_targets])
    artifacts = {
        "joined_recovery_features.csv": out_dir / "joined_recovery_features.csv",
        "microbasin_summary.csv": out_dir / "microbasin_summary.csv",
        "microbasin_gain_attribution.csv": out_dir / "microbasin_gain_attribution.csv",
        "minimal_constructor_recipes.csv": out_dir / "minimal_constructor_recipes.csv",
        "microbasin_constructor_recipes.csv": out_dir / "microbasin_constructor_recipes.csv",
        "residual_obstruction_targets.csv": out_dir / "residual_obstruction_targets.csv",
        "microbasin_distillation_summary.json": out_dir / "microbasin_distillation_summary.json",
        "microbasin_distillation_report.md": out_dir / "microbasin_distillation_report.md",
        "artifact_manifest.json": out_dir / "artifact_manifest.json",
        "microbasin_distillation.sqlite": out_dir / "microbasin_distillation.sqlite",
    }
    frames = {
        "joined_recovery_features": joined,
        "microbasin_summary": microbasins,
        "microbasin_gain_attribution": attribution,
        "minimal_constructor_recipes": recipes,
        "residual_obstruction_targets": residual_targets,
    }
    for table, frame in frames.items():
        frame.to_csv(artifacts[f"{table}.csv"], index=False)
    recipes.to_csv(artifacts["microbasin_constructor_recipes.csv"], index=False)
    exact_available = {"lawbook_gain_hit", "lawbook_gain_constructor_id", "lawbook_gain_constructor_family"}.issubset(joined.columns)
    summary = {
        "input_dir": str(config.input_dir),
        "out_dir": str(out_dir),
        "rows": int(len(joined)),
        "microbasin_count": int(len(microbasins)),
        "positive_gain_microbasins": int((pd.to_numeric(microbasins.get("lawbook_gain", pd.Series(dtype=int)), errors="coerce").fillna(0) > 0).sum()) if not microbasins.empty else 0,
        "total_generic_yield": int(joined["generic_recovered"].sum()) if "generic_recovered" in joined else 0,
        "total_lawbook_yield": int(joined["lawbook_recovered"].sum()) if "lawbook_recovered" in joined else 0,
        "total_lawbook_gain": int(joined["lawbook_recovered"].sum() - joined["generic_recovered"].sum()) if {"lawbook_recovered", "generic_recovered"}.issubset(joined.columns) else 0,
        "residual_after_lawbook": int((~joined["lawbook_recovered"].astype(bool)).sum()) if "lawbook_recovered" in joined else 0,
        "recipe_count": int(len(recipes)),
        "residual_obstruction_target_count": int(len(residual_targets)),
        "attribution_modes": sorted(str(mode) for mode in attribution.get("attribution_mode", pd.Series(dtype=str)).dropna().unique()) if not attribution.empty else [],
        "exact_attribution_available": exact_available,
        "total_exact_lawbook_gain_hits": int(joined.get("lawbook_gain_hit", pd.Series(dtype=bool)).map(_as_bool).sum()) if "lawbook_gain_hit" in joined.columns else 0,
        "exact_recipe_count": int((recipes.get("attribution_mode", pd.Series(dtype=str)) == "exact_constructor").sum()) if not recipes.empty else 0,
        "top_exact_gain_constructor_families": _count_column(joined[joined.get("lawbook_gain_hit", pd.Series(dtype=bool)).map(_as_bool)] if "lawbook_gain_hit" in joined.columns else pd.DataFrame(), "lawbook_gain_constructor_family"),
        "safety": safety,
        "advisory_only": True,
        "can_promote_truth": False,
        "benchmark_meaning": "This distills advisory routing evidence into constructor recipes and residual targets; it does not promote truth.",
    }
    artifacts["microbasin_distillation_summary.json"].write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    artifacts["microbasin_distillation_report.md"].write_text(_report(summary), encoding="utf-8")
    _write_sqlite(artifacts["microbasin_distillation.sqlite"], frames | {"summary": pd.DataFrame([summary])})
    manifest = [{"artifact_name": name, "path": str(path), "exists": path.exists()} for name, path in artifacts.items()]
    artifacts["artifact_manifest.json"].write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    if config.strict_safety and not safety["safety_passed"]:
        raise RuntimeError("microbasin distillation safety audit failed")
    return MicrobasinDistillationResult(summary=summary, artifacts={name: str(path) for name, path in artifacts.items()})


def _read_first(root: Path, names: tuple[str, ...]) -> pd.DataFrame:
    for name in names:
        path = root / name
        if path.exists():
            return pd.read_csv(path)
    return pd.DataFrame()


def _normalize_recovery_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for column in ("generic_recovered", "lawbook_recovered", "compact_recovered", "oracle_recovered"):
        if column not in out.columns:
            out[column] = False if column != "oracle_recovered" else out.get("lawbook_recovered", False)
        out[column] = out[column].map(_as_bool).astype(bool)
    if "lawbook_new_recovery" not in out.columns:
        out["lawbook_new_recovery"] = out["lawbook_recovered"] & ~out["generic_recovered"]
    else:
        out["lawbook_new_recovery"] = out["lawbook_new_recovery"].map(_as_bool).astype(bool)
    return out


def _quantile_tokens(series: Any, name: str, bins: int) -> list[str]:
    if series is None:
        return [f"{name}_na"]
    values = pd.to_numeric(series, errors="coerce")
    if values.notna().sum() == 0 or values.nunique(dropna=True) <= 1:
        return [f"{name}_q0" if pd.notna(value) else f"{name}_na" for value in values]
    try:
        codes = pd.qcut(values, q=max(1, bins), labels=False, duplicates="drop")
    except ValueError:
        codes = pd.Series([0 if pd.notna(value) else None for value in values])
    return [f"{name}_q{int(code)}" if pd.notna(code) else f"{name}_na" for code in codes]


def _token(value: Any) -> str:
    text = str(value if value not in (None, "") else "na").strip().lower()
    return "".join(ch if ch.isalnum() else "_" for ch in text).strip("_") or "na"


def _as_bool(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _mode(series: Any) -> Any:
    if series is None:
        return ""
    try:
        mode = series.mode(dropna=True)
        return mode.iloc[0] if not mode.empty else ""
    except Exception:
        return ""


def _top_values(series: Any, limit: int) -> list[str]:
    if series is None:
        return []
    values = pd.Series(series).dropna().astype(str)
    values = values[values != ""]
    return values.value_counts().head(max(0, limit)).index.tolist()


def _count_column(frame: pd.DataFrame, column: str, limit: int = 10) -> list[dict[str, Any]]:
    if frame.empty or column not in frame.columns:
        return []
    counts = frame[column].dropna().astype(str)
    counts = counts[counts != ""].value_counts().head(limit)
    return [{"value": value, "count": int(count)} for value, count in counts.items()]


def _entropy_part(count: int, total: int) -> float:
    p = count / total if total else 0.0
    return float(-p * math.log2(p)) if p > 0 else 0.0


def _constructor_pressure(row: pd.Series) -> str:
    basin = str(row.get("basin", ""))
    deep = str(row.get("deep_ir_candidate", ""))
    fresh = float(row.get("fresh_variable_escape_count", 0) or 0)
    repeat = float(row.get("repeat_tail_pressure", 0) or 0)
    loss = float(row.get("ir_constraint_loss", 0) or 0)
    if fresh > 0 or "fresh" in basin:
        return "fresh_gate_or_absorber_constructor"
    if repeat > 0 or loss >= 5:
        return "tail_coupled_or_depth_sensitive_constructor"
    if "projection" in basin or "projection" in deep:
        return "non_diagonal_escape_constructor"
    return "residual_specific_constructor_search"


def _safety_summary(terminal_audit: pd.DataFrame, advisory_frames: list[pd.DataFrame]) -> dict[str, Any]:
    true_contamination = 0
    advisory_truth = 0
    failed_true = 0
    if not terminal_audit.empty:
        if "true_contamination_count" in terminal_audit:
            true_contamination = int(pd.to_numeric(terminal_audit["true_contamination_count"], errors="coerce").fillna(0).sum())
        advisory_truth = int(((terminal_audit.get("advisory_only", False).map(_as_bool) if "advisory_only" in terminal_audit else False) & (terminal_audit.get("can_promote_truth", False).map(_as_bool) if "can_promote_truth" in terminal_audit else False)).sum()) if {"advisory_only", "can_promote_truth"}.issubset(terminal_audit.columns) else 0
        failed_true = int(((terminal_audit.get("status", "").astype(str) == "RESIDUAL") & (terminal_audit.get("terminal_form", "").astype(str) == "VERIFIED_PROOF")).sum()) if {"status", "terminal_form"}.issubset(terminal_audit.columns) else 0
    advisory_rows_can_promote = 0
    for frame in advisory_frames:
        if {"advisory_only", "can_promote_truth"}.issubset(frame.columns):
            advisory_rows_can_promote += int((frame["advisory_only"].map(_as_bool) & frame["can_promote_truth"].map(_as_bool)).sum())
    return {
        "true_contamination_count": true_contamination,
        "terminal_claims_from_advisory_count": advisory_truth,
        "failed_search_promoted_true_count": failed_true,
        "advisory_rows_can_promote_truth_count": advisory_rows_can_promote,
        "safety_passed": true_contamination == 0 and advisory_truth == 0 and failed_true == 0 and advisory_rows_can_promote == 0,
    }


def _write_sqlite(path: Path, frames: dict[str, pd.DataFrame]) -> None:
    with sqlite3.connect(str(path)) as conn:
        for table, frame in frames.items():
            safe = _sqlite_safe_frame(frame)
            safe.to_sql(table, conn, if_exists="replace", index=False)


def _sqlite_safe_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty and len(frame.columns) == 0:
        return pd.DataFrame([{"empty": True}])
    safe = frame.copy()
    for col in safe.columns:
        safe[col] = safe[col].map(lambda value: json.dumps(value, sort_keys=True) if isinstance(value, (dict, list, tuple)) else value)
    return safe


def _report(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Micro-basin Causal Distillation",
            "",
            "## Summary",
            f"- rows: {summary['rows']}",
            f"- microbasin_count: {summary['microbasin_count']}",
            f"- positive_gain_microbasins: {summary['positive_gain_microbasins']}",
            f"- total_lawbook_gain: {summary['total_lawbook_gain']}",
            f"- recipe_count: {summary['recipe_count']}",
            f"- residual_obstruction_target_count: {summary['residual_obstruction_target_count']}",
            "",
            "## Boundary",
            "All outputs are advisory routing evidence. They do not promote truth.",
            "",
            "## Safety",
            f"- safety_passed: {summary['safety']['safety_passed']}",
            f"- true_contamination_count: {summary['safety']['true_contamination_count']}",
            f"- terminal_claims_from_advisory_count: {summary['safety']['terminal_claims_from_advisory_count']}",
            f"- failed_search_promoted_true_count: {summary['safety']['failed_search_promoted_true_count']}",
            "",
        ]
    )
