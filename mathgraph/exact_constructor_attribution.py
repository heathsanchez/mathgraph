"""Exact first-hit constructor attribution for finite-core route policies."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


POLICY_ALIASES = {
    "generic": "generic",
    "heldout_lawbook_guided": "heldout_lawbook",
    "compact_atlas_guided": "compact_atlas",
    "heldout_repair_oracle_like_bounded": "heldout_repair_oracle_like_bounded",
}


def first_recovering_constructor_for_pair(pair_hits: np.ndarray, route_indices: list[int]) -> int | None:
    """Return the first route constructor that recovers one pair."""

    for idx in route_indices:
        if 0 <= int(idx) < pair_hits.shape[0] and bool(pair_hits[int(idx)]):
            return int(idx)
    return None


def attribute_policy_recoveries(
    policy_name: str,
    route_indices: list[int],
    pair_recovery_matrix: np.ndarray,
    constructor_manifest: pd.DataFrame,
) -> list[dict[str, Any]]:
    """Return exact first-hit attribution rows for one policy."""

    prefix = POLICY_ALIASES.get(policy_name, policy_name)
    rows: list[dict[str, Any]] = []
    for pair_idx in range(int(pair_recovery_matrix.shape[0])):
        first = first_recovering_constructor_for_pair(pair_recovery_matrix[pair_idx], route_indices)
        meta = _constructor_meta(first, constructor_manifest)
        rows.append(
            {
                "pair_idx": pair_idx,
                f"{prefix}_recovered": first is not None,
                f"{prefix}_first_constructor_idx": first,
                f"{prefix}_first_constructor_id": meta.get("cid"),
                f"{prefix}_first_constructor_family": meta.get("family"),
                f"{prefix}_first_constructor_name": meta.get("name"),
                f"{prefix}_first_constructor_n": meta.get("n"),
            }
        )
    return rows


def build_exact_constructor_attribution_frame(
    pairs: list[tuple[int, int]],
    pair_recovery_matrix: np.ndarray,
    constructor_manifest: pd.DataFrame,
    policy_routes: dict[str, list[int]],
    seed: int | None = None,
) -> pd.DataFrame:
    """Build one row per pair with exact first-hit columns for all policies."""

    base_rows = [
        {
            "seed": seed,
            "pair_idx": pair_idx,
            "eq1_id": int(eq1_id),
            "eq2_id": int(eq2_id),
            "source_eq_idx": int(eq1_id),
            "target_eq_idx": int(eq2_id),
            "i": int(eq1_id),
            "j": int(eq2_id),
        }
        for pair_idx, (eq1_id, eq2_id) in enumerate(pairs)
    ]
    frame = pd.DataFrame(base_rows)
    for policy, route in policy_routes.items():
        policy_frame = pd.DataFrame(attribute_policy_recoveries(policy, route, pair_recovery_matrix, constructor_manifest))
        frame = frame.merge(policy_frame, on="pair_idx", how="left")
    if "heldout_lawbook_recovered" in frame.columns:
        frame["lawbook_recovered"] = frame["heldout_lawbook_recovered"].fillna(False).astype(bool)
    if "generic_recovered" in frame.columns:
        frame["generic_recovered"] = frame["generic_recovered"].fillna(False).astype(bool)
    frame["lawbook_gain_hit"] = frame.get("lawbook_recovered", False) & ~frame.get("generic_recovered", False)
    for suffix in ("idx", "id", "family", "name", "n"):
        src = f"heldout_lawbook_first_constructor_{suffix}"
        dst = f"lawbook_gain_constructor_{suffix}"
        frame[dst] = frame[src].where(frame["lawbook_gain_hit"], None) if src in frame.columns else None
    if "compact_atlas_recovered" in frame.columns:
        frame["compact_gain_hit"] = frame["compact_atlas_recovered"].fillna(False).astype(bool) & ~frame["generic_recovered"]
        frame["compact_gain_constructor_id"] = frame.get("compact_atlas_first_constructor_id").where(frame["compact_gain_hit"], None)
        frame["compact_gain_constructor_family"] = frame.get("compact_atlas_first_constructor_family").where(frame["compact_gain_hit"], None)
    if "heldout_repair_oracle_like_bounded_recovered" in frame.columns:
        frame["bounded_repair_gain_hit"] = frame["heldout_repair_oracle_like_bounded_recovered"].fillna(False).astype(bool) & ~frame["generic_recovered"]
        frame["bounded_repair_gain_constructor_id"] = frame.get("heldout_repair_oracle_like_bounded_first_constructor_id").where(frame["bounded_repair_gain_hit"], None)
        frame["bounded_repair_gain_constructor_family"] = frame.get("heldout_repair_oracle_like_bounded_first_constructor_family").where(frame["bounded_repair_gain_hit"], None)
    frame["exact_attribution_available"] = True
    frame["attribution_mode"] = "exact_constructor"
    frame["advisory_only"] = True
    frame["can_promote_truth"] = False
    return frame


def top_lawbook_gain_constructor_families(attribution_frame: pd.DataFrame, limit: int = 10) -> list[dict[str, Any]]:
    if attribution_frame.empty or "lawbook_gain_constructor_family" not in attribution_frame.columns:
        return []
    hits = attribution_frame[attribution_frame.get("lawbook_gain_hit", False).astype(bool)]
    counts = hits["lawbook_gain_constructor_family"].dropna().astype(str)
    counts = counts[counts != ""].value_counts().head(limit)
    return [{"family": family, "count": int(count)} for family, count in counts.items()]


def top_lawbook_gain_constructors(attribution_frame: pd.DataFrame, limit: int = 10) -> list[dict[str, Any]]:
    if attribution_frame.empty or "lawbook_gain_constructor_id" not in attribution_frame.columns:
        return []
    hits = attribution_frame[attribution_frame.get("lawbook_gain_hit", False).astype(bool)]
    counts = hits["lawbook_gain_constructor_id"].dropna().astype(str)
    counts = counts[counts != ""].value_counts().head(limit)
    return [{"constructor_id": cid, "count": int(count)} for cid, count in counts.items()]


def _constructor_meta(idx: int | None, manifest: pd.DataFrame) -> dict[str, Any]:
    if idx is None or idx < 0 or idx >= len(manifest):
        return {"cid": None, "family": None, "name": None, "n": None}
    row = manifest.iloc[int(idx)]
    return {
        "cid": row.get("cid"),
        "family": row.get("family"),
        "name": row.get("name"),
        "n": row.get("n"),
    }
