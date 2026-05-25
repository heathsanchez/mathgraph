"""Persistent exact micro-basin Lawbook replay.

This module turns exact held-out Lawbook gain attribution into durable advisory
route memory.  It never promotes truth: persistent micro-basin entries are route
learning evidence only, and replay metrics are proxy diagnostics over already
observed finite-core recovery columns.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import sqlite3
from typing import Any, Mapping

import pandas as pd


NUMERIC_KEY_FIELDS = (
    "quotient_pressure",
    "target_separation_pressure",
    "ir_constraint_loss",
    "fresh_variable_escape_count",
    "repeat_tail_pressure",
)


@dataclass(frozen=True)
class PersistentMicrobasinEntry:
    microbasin_key: str
    basin: str
    deep_ir_candidate: str
    constructor_family: str
    constructor_id: str
    support: int
    gain_hits: int
    generic_hits: int
    lawbook_hits: int
    gain_rate: float
    reuse_score: float
    residual_pressure: int
    first_seen_episode: int
    last_seen_episode: int
    source_seeds: list[int]
    advisory_only: bool = True
    can_promote_truth: bool = False
    status: str = "persistent_exact_microbasin_route_advisory"


def build_microbasin_key(row: Mapping[str, Any]) -> str:
    """Build a stable PQ-IR micro-basin key from whatever fields are present."""

    basin = _token(row.get("basin", "basin_na"))
    deep = _token(row.get("deep_ir_candidate", "deep_ir_na"))
    tokens = [basin, deep]
    for field in NUMERIC_KEY_FIELDS:
        tokens.append(_numeric_bin_token(field, row.get(field)))
    skeleton = row.get("skeleton_equal", row.get("source_lhs_rhs_skeleton_equal", False))
    tokens.append(f"skel{1 if _as_bool(skeleton) else 0}")
    return "__".join(tokens)


def add_microbasin_keys(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with ``microbasin_key`` present."""

    out = df.copy()
    if out.empty:
        out["microbasin_key"] = []
        return out
    out["microbasin_key"] = [build_microbasin_key(row) for row in out.to_dict("records")]
    return out


def detect_recovery_columns(df: pd.DataFrame) -> dict[str, str | None]:
    """Detect recovery and exact attribution columns across benchmark variants."""

    return {
        "generic_recovered": _first_col(df, ("generic_recovered", "baseline_recovered")),
        "lawbook_recovered": _first_col(
            df,
            (
                "heldout_lawbook_recovered",
                "lawbook_recovered",
                "heldout_lawbook_guided_recovered",
                "memory_recovered",
            ),
        ),
        "lawbook_gain_hit": _first_col(df, ("lawbook_gain_hit", "lawbook_new_recovery", "heldout_lawbook_new_recovery")),
        "lawbook_gain_constructor_id": _first_col(
            df,
            (
                "lawbook_gain_constructor_id",
                "heldout_lawbook_first_constructor_id",
                "lawbook_first_hit_constructor_id",
                "heldout_lawbook_first_hit_constructor_id",
            ),
        ),
        "lawbook_gain_constructor_family": _first_col(
            df,
            (
                "lawbook_gain_constructor_family",
                "heldout_lawbook_first_constructor_family",
                "lawbook_first_hit_constructor_family",
                "heldout_lawbook_first_hit_constructor_family",
            ),
        ),
    }


def normalize_recovery_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize held-out recovery artifacts into exact advisory gain fields."""

    out = add_microbasin_keys(df)
    cols = detect_recovery_columns(out)
    out["generic_recovered_norm"] = _bool_series(out, cols["generic_recovered"])
    out["lawbook_recovered_norm"] = _bool_series(out, cols["lawbook_recovered"])
    cid_col = cols["lawbook_gain_constructor_id"]
    fam_col = cols["lawbook_gain_constructor_family"]
    out["lawbook_gain_constructor_id_norm"] = _string_series(out, cid_col)
    out["lawbook_gain_constructor_family_norm"] = _string_series(out, fam_col)
    if cols["lawbook_gain_hit"] is not None:
        gain = _bool_series(out, cols["lawbook_gain_hit"])
    else:
        gain = out["lawbook_recovered_norm"] & ~out["generic_recovered_norm"]
    out["lawbook_gain_hit_norm"] = gain & out["lawbook_gain_constructor_id_norm"].astype(bool)
    out["advisory_only"] = True
    out["can_promote_truth"] = False
    return out


def build_persistent_lawbook(
    episode_frames: list[pd.DataFrame],
    min_support: int = 1,
    min_gain_hits: int = 1,
) -> pd.DataFrame:
    """Build advisory persistent entries from prior exact Lawbook gain hits."""

    normalized: list[pd.DataFrame] = []
    for episode, frame in enumerate(episode_frames):
        if frame.empty:
            continue
        current = normalize_recovery_frame(frame)
        if "episode" not in current.columns:
            current["episode"] = episode
        normalized.append(current)
    if not normalized:
        return _empty_lawbook()
    all_rows = pd.concat(normalized, ignore_index=True, sort=False)
    gains = all_rows[all_rows["lawbook_gain_hit_norm"].astype(bool)].copy()
    gains = gains[gains["lawbook_gain_constructor_id_norm"].astype(str) != ""]
    if gains.empty:
        return _empty_lawbook()
    support_by_key = all_rows.groupby("microbasin_key", dropna=False).size().to_dict()
    residual_by_key = (
        all_rows[~all_rows["lawbook_recovered_norm"].astype(bool)].groupby("microbasin_key", dropna=False).size().to_dict()
    )
    rows: list[dict[str, Any]] = []
    group_cols = ["microbasin_key", "lawbook_gain_constructor_family_norm", "lawbook_gain_constructor_id_norm"]
    for (key, family, cid), group in gains.groupby(group_cols, dropna=False):
        support = int(support_by_key.get(key, len(group)))
        gain_hits = int(len(group))
        if support < min_support or gain_hits < min_gain_hits:
            continue
        episodes = pd.to_numeric(group.get("episode", pd.Series([0])), errors="coerce").fillna(0).astype(int)
        seeds = sorted(
            int(seed)
            for seed in pd.to_numeric(group.get("seed", pd.Series(dtype=int)), errors="coerce").dropna().astype(int).unique()
        )
        lawbook_hits = int(group["lawbook_recovered_norm"].sum())
        generic_hits = int(group["generic_recovered_norm"].sum())
        residual_pressure = int(residual_by_key.get(key, 0))
        gain_rate = gain_hits / max(1, support)
        rows.append(
            PersistentMicrobasinEntry(
                microbasin_key=str(key),
                basin=str(_mode(group.get("basin"))),
                deep_ir_candidate=str(_mode(group.get("deep_ir_candidate"))),
                constructor_family=str(family),
                constructor_id=str(cid),
                support=support,
                gain_hits=gain_hits,
                generic_hits=generic_hits,
                lawbook_hits=lawbook_hits,
                gain_rate=gain_rate,
                reuse_score=round(gain_hits * gain_rate / max(1, residual_pressure + 1), 8),
                residual_pressure=residual_pressure,
                first_seen_episode=int(episodes.min()),
                last_seen_episode=int(episodes.max()),
                source_seeds=seeds,
            ).__dict__
        )
    if not rows:
        return _empty_lawbook()
    out = pd.DataFrame(rows)
    return out.sort_values(["reuse_score", "gain_hits", "support"], ascending=[False, False, False]).reset_index(drop=True)


def replay_persistent_lawbook(heldout_frame: pd.DataFrame, persistent_lawbook: pd.DataFrame) -> pd.DataFrame:
    """Replay prior advisory memory on a later held-out frame.

    The returned recovery columns are proxy diagnostics: they use observed exact
    recovery labels to estimate whether prior recipes would have selected a
    useful route.  They are not terminal verification.
    """

    df = normalize_recovery_frame(heldout_frame)
    if persistent_lawbook.empty:
        df["persistent_route_available"] = False
        df["persistent_recommended_family"] = ""
        df["persistent_recommended_constructor_id"] = ""
    else:
        lawbook = persistent_lawbook.copy()
        lawbook["_reuse"] = pd.to_numeric(lawbook.get("reuse_score", 0), errors="coerce").fillna(0)
        lawbook = lawbook.sort_values(["microbasin_key", "_reuse", "gain_hits"], ascending=[True, False, False])
        best = lawbook.drop_duplicates("microbasin_key", keep="first").set_index("microbasin_key")
        families: list[str] = []
        constructors: list[str] = []
        available: list[bool] = []
        for key in df["microbasin_key"].astype(str):
            if key in best.index:
                row = best.loc[key]
                families.append(str(row.get("constructor_family", "")))
                constructors.append(str(row.get("constructor_id", "")))
                available.append(True)
            else:
                families.append("")
                constructors.append("")
                available.append(False)
        df["persistent_route_available"] = available
        df["persistent_recommended_family"] = families
        df["persistent_recommended_constructor_id"] = constructors
    id_match = df["persistent_recommended_constructor_id"].astype(str) == df["lawbook_gain_constructor_id_norm"].astype(str)
    family_match = df["persistent_recommended_family"].astype(str) == df["lawbook_gain_constructor_family_norm"].astype(str)
    persistent_hit = df["persistent_route_available"].astype(bool) & df["lawbook_recovered_norm"].astype(bool) & (id_match | family_match)
    df["persistent_recovered_proxy"] = df["generic_recovered_norm"].astype(bool) | persistent_hit
    df["persistent_gain_over_generic_proxy"] = df["persistent_recovered_proxy"].astype(bool) & ~df["generic_recovered_norm"].astype(bool)
    df["persistent_gain_over_lawbook_proxy"] = df["persistent_recovered_proxy"].astype(bool) & ~df["lawbook_recovered_norm"].astype(bool)
    df["advisory_only"] = True
    df["can_promote_truth"] = False
    return df


def evaluate_persistent_replay(replay_df: pd.DataFrame) -> dict[str, Any]:
    """Compute JSON-safe proxy replay metrics and safety counts."""

    df = replay_df.copy()
    rows = int(len(df))
    generic_yield = int(df.get("generic_recovered_norm", pd.Series(dtype=bool)).map(_as_bool).sum()) if rows else 0
    lawbook_yield = int(df.get("lawbook_recovered_norm", pd.Series(dtype=bool)).map(_as_bool).sum()) if rows else 0
    persistent_yield = int(df.get("persistent_recovered_proxy", pd.Series(dtype=bool)).map(_as_bool).sum()) if rows else 0
    route_available = int(df.get("persistent_route_available", pd.Series(dtype=bool)).map(_as_bool).sum()) if rows else 0
    safety = _safety_counts(df)
    return {
        "rows": rows,
        "generic_yield": generic_yield,
        "lawbook_yield": lawbook_yield,
        "persistent_yield_proxy": persistent_yield,
        "generic_residuals": rows - generic_yield,
        "lawbook_residuals": rows - lawbook_yield,
        "persistent_residuals_proxy": rows - persistent_yield,
        "lawbook_gain_over_generic": lawbook_yield - generic_yield,
        "persistent_gain_over_generic_proxy": persistent_yield - generic_yield,
        "persistent_gain_over_lawbook_proxy": persistent_yield - lawbook_yield,
        "exact_recipe_reuse_count": route_available,
        "exact_recipe_reuse_rate": route_available / rows if rows else 0.0,
        "residual_compression_gain_proxy": (rows - generic_yield) - (rows - persistent_yield),
        **safety,
        "advisory_boundary_preserved": safety["true_contamination_count"] == 0
        and safety["terminal_claims_from_advisory_count"] == 0
        and safety["failed_search_promoted_true_count"] == 0,
    }


def write_persistent_lawbook_sqlite(path: str | Path, tables: dict[str, pd.DataFrame]) -> None:
    """Write persistent replay artifacts to SQLite without empty-frame crashes."""

    with sqlite3.connect(str(path)) as conn:
        for name, frame in tables.items():
            _sqlite_safe_frame(frame).to_sql(name, conn, if_exists="replace", index=False)


def _empty_lawbook() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "microbasin_key",
            "basin",
            "deep_ir_candidate",
            "constructor_family",
            "constructor_id",
            "support",
            "gain_hits",
            "generic_hits",
            "lawbook_hits",
            "gain_rate",
            "reuse_score",
            "residual_pressure",
            "first_seen_episode",
            "last_seen_episode",
            "source_seeds",
            "advisory_only",
            "can_promote_truth",
            "status",
        ]
    )


def _first_col(df: pd.DataFrame, names: tuple[str, ...]) -> str | None:
    for name in names:
        if name in df.columns:
            return name
    return None


def _bool_series(df: pd.DataFrame, column: str | None) -> pd.Series:
    if column is None:
        return pd.Series([False] * len(df), index=df.index, dtype=bool)
    return df[column].map(_as_bool).astype(bool)


def _string_series(df: pd.DataFrame, column: str | None) -> pd.Series:
    if column is None:
        return pd.Series([""] * len(df), index=df.index, dtype=object)
    return df[column].fillna("").astype(str)


def _as_bool(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _token(value: Any) -> str:
    text = str(value if value not in (None, "") else "na").strip().lower()
    return "".join(ch if ch.isalnum() else "_" for ch in text).strip("_") or "na"


def _numeric_bin_token(name: str, value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return f"{name}_na"
    if number <= 0:
        bucket = "q0"
    elif number <= 1:
        bucket = "q1"
    elif number <= 3:
        bucket = "q2"
    else:
        bucket = "q3"
    return f"{name}_{bucket}"


def _mode(series: Any) -> Any:
    if series is None:
        return ""
    try:
        mode = pd.Series(series).dropna().mode()
        return mode.iloc[0] if not mode.empty else ""
    except Exception:
        return ""


def _safety_counts(df: pd.DataFrame) -> dict[str, int]:
    true_contamination = int(pd.to_numeric(df.get("true_contamination_count", pd.Series(dtype=int)), errors="coerce").fillna(0).sum())
    advisory_truth = 0
    if {"advisory_only", "can_promote_truth"}.issubset(df.columns):
        advisory_truth = int((df["advisory_only"].map(_as_bool) & df["can_promote_truth"].map(_as_bool)).sum())
    failed_true = 0
    if {"status", "terminal_form"}.issubset(df.columns):
        failed_true = int(((df["status"].astype(str) == "RESIDUAL") & (df["terminal_form"].astype(str) == "VERIFIED_PROOF")).sum())
    return {
        "true_contamination_count": true_contamination,
        "terminal_claims_from_advisory_count": advisory_truth,
        "failed_search_promoted_true_count": failed_true,
    }


def _sqlite_safe_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty and len(frame.columns) == 0:
        return pd.DataFrame([{"empty": True}])
    safe = frame.copy()
    for col in safe.columns:
        safe[col] = safe[col].map(lambda value: json.dumps(value, sort_keys=True) if isinstance(value, (dict, list, tuple)) else value)
    return safe
