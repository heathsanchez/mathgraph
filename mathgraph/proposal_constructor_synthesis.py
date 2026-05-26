"""Proposal-specific finite constructor synthesis.

This module turns advisory constructor-family proposals into concrete finite
magma tables, then evaluates those tables with the finite implication checker.
Synthesis metadata remains advisory; only checked finite countermodels count as
recoveries.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import random
from typing import Any, Mapping

import pandas as pd

from mathgraph.finite_magma import FiniteMagma, implication_false_certificate, table_hash


@dataclass(frozen=True)
class SynthesizedConstructor:
    constructor_id: str
    proposal_id: str
    proposal_family: str
    residual_basin_id: str
    n: int
    table: list[list[int]]
    table_hash: str
    synthesis_kind: str
    rationale: str
    source_features: dict[str, Any]
    advisory_only: bool = True
    can_promote_truth: bool = False


@dataclass(frozen=True)
class ConstructorSynthesisResult:
    proposal_id: str
    proposal_family: str
    residual_basin_id: str
    generated_count: int
    unique_table_count: int
    n_values: list[int]
    advisory_only: bool = True
    can_promote_truth: bool = False


@dataclass(frozen=True)
class SynthesizedRecovery:
    proposal_id: str
    constructor_id: str
    proposal_family: str
    residual_basin_id: str
    pair_id: Any
    source_eq_idx: int
    target_eq_idx: int
    eq1_holds: bool
    eq2_violated: bool
    recovered: bool
    witness: dict[str, int]
    finite_checked: bool
    advisory_only: bool = True
    can_promote_truth: bool = False


SUPPORTED_FAMILIES = {
    "constant",
    "left_projection",
    "right_projection",
    "projection_exception_left",
    "projection_exception_right",
    "quotient_spike",
    "quotient_fresh_gate",
    "fresh_absorber",
    "random_fresh_sink",
    "random_fresh_collapse",
    "diagonal_spike",
    "diag_perturb_right",
    "diag_perturb_left",
    "tail_coupled_projection",
    "head_coupled_projection",
    "row_erasure_family",
    "col_erasure_family",
    "block_selector",
    "block_selector_dual",
    "linear_combo_mod",
    "add_mod",
    "sub_mod",
    "xor_mod",
    "prior",
}


def synthesize_constructors_for_proposal(
    proposal: Mapping[str, Any],
    max_n: int = 4,
    max_tables_per_family: int = 32,
    seed: int = 1729,
) -> list[SynthesizedConstructor]:
    """Generate concrete finite magma tables for one advisory proposal."""

    family = str(proposal.get("proposal_family", proposal.get("family", ""))).strip()
    proposal_id = str(proposal.get("proposal_id", f"proposal_{family}"))
    residual_basin_id = str(proposal.get("residual_basin_id", ""))
    if family not in SUPPORTED_FAMILIES:
        return []
    rows: list[SynthesizedConstructor] = []
    seen: set[str] = set()
    for n in range(2, max(2, int(max_n)) + 1):
        for table, kind in _family_tables(family, n, seed + hash(proposal_id) % 10007):
            digest = table_hash(table)
            key = f"{n}:{digest}"
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                SynthesizedConstructor(
                    constructor_id=f"synth:{proposal_id}:{family}:n{n}:{digest[:12]}",
                    proposal_id=proposal_id,
                    proposal_family=family,
                    residual_basin_id=residual_basin_id,
                    n=n,
                    table=[list(row) for row in table],
                    table_hash=digest,
                    synthesis_kind=kind,
                    rationale=str(proposal.get("rationale", f"synthesized {family} table")),
                    source_features=_parse_features(proposal.get("source_features", {})),
                )
            )
            if len(rows) >= max_tables_per_family:
                return rows
    return rows


def synthesize_constructors_for_proposals(
    proposals: pd.DataFrame,
    max_n: int = 4,
    max_tables_per_proposal: int = 32,
    seed: int = 1729,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Generate constructors for proposal rows and return constructors/results."""

    constructors: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    for offset, proposal in enumerate(proposals.to_dict("records")):
        generated = synthesize_constructors_for_proposal(
            proposal,
            max_n=max_n,
            max_tables_per_family=max_tables_per_proposal,
            seed=seed + offset,
        )
        constructors.extend(row.__dict__ for row in generated)
        results.append(
            ConstructorSynthesisResult(
                proposal_id=str(proposal.get("proposal_id", "")),
                proposal_family=str(proposal.get("proposal_family", "")),
                residual_basin_id=str(proposal.get("residual_basin_id", "")),
                generated_count=len(generated),
                unique_table_count=len({row.table_hash for row in generated}),
                n_values=sorted({row.n for row in generated}),
            ).__dict__
            | {"status": "constructor_synthesis_advisory"}
        )
    return pd.DataFrame(constructors), pd.DataFrame(results)


def evaluate_synthesized_constructors(
    constructors: pd.DataFrame,
    residual_pairs: pd.DataFrame,
    equations: list[str],
    max_pairs_per_constructor: int = 100,
) -> pd.DataFrame:
    """Finite-check synthesized constructors against residual implication pairs."""

    if constructors.empty or residual_pairs.empty or not equations:
        return pd.DataFrame(columns=[field for field in SynthesizedRecovery.__dataclass_fields__] + ["certificate_status"])
    rows: list[dict[str, Any]] = []
    pairs = residual_pairs.head(max_pairs_per_constructor).copy()
    for constructor in constructors.to_dict("records"):
        magma = FiniteMagma(_table_tuple(constructor["table"]), constructor["proposal_family"], constructor["constructor_id"], source="proposal_synthesis")
        for _, pair in pairs.iterrows():
            source_idx = int(pair.get("source_eq_idx", pair.get("eq1_id", pair.get("i", 0))))
            target_idx = int(pair.get("target_eq_idx", pair.get("eq2_id", pair.get("j", 0))))
            if source_idx >= len(equations) or target_idx >= len(equations):
                continue
            cert = implication_false_certificate(equations[source_idx], equations[target_idx], magma)
            recovered = bool(cert.eq1_holds and cert.eq2_violated)
            rows.append(
                SynthesizedRecovery(
                    proposal_id=str(constructor["proposal_id"]),
                    constructor_id=str(constructor["constructor_id"]),
                    proposal_family=str(constructor["proposal_family"]),
                    residual_basin_id=str(constructor["residual_basin_id"]),
                    pair_id=pair.get("pair_idx", pair.name),
                    source_eq_idx=source_idx,
                    target_eq_idx=target_idx,
                    eq1_holds=bool(cert.eq1_holds),
                    eq2_violated=bool(cert.eq2_violated),
                    recovered=recovered,
                    witness=dict(cert.witness_env),
                    finite_checked=True,
                    advisory_only=not recovered,
                    can_promote_truth=recovered,
                ).__dict__
                | {"certificate_status": cert.certificate_status, "status": "finite_checked_synthesis_recovery" if recovered else "finite_checked_no_recovery"}
            )
    return pd.DataFrame(rows)


def summarize_synthesis(
    constructors: pd.DataFrame,
    synthesis_results: pd.DataFrame,
    recoveries: pd.DataFrame,
) -> dict[str, Any]:
    """Summarize synthesis output and checked recoveries."""

    recovered = recoveries[recoveries.get("recovered", pd.Series(dtype=bool)).map(_as_bool)] if not recoveries.empty else pd.DataFrame()
    best = recovered.groupby(["proposal_family", "constructor_id"], dropna=False).size().reset_index(name="count").sort_values("count", ascending=False).head(1) if not recovered.empty else pd.DataFrame()
    safety_advisory = 0
    if {"advisory_only", "can_promote_truth"}.issubset(constructors.columns):
        safety_advisory += int((constructors["advisory_only"].map(_as_bool) & constructors["can_promote_truth"].map(_as_bool)).sum())
    return {
        "synthesis_enabled": True,
        "synthesized_constructor_count": int(len(constructors)),
        "unique_synthesized_table_count": int(constructors.get("table_hash", pd.Series(dtype=str)).nunique()) if not constructors.empty else 0,
        "synthesized_recovered_pairs": int(len(recovered)),
        "synthesized_recovery_rate": len(recovered) / max(1, len(recoveries)) if not recoveries.empty else 0.0,
        "best_synthesized_family": str(best["proposal_family"].iloc[0]) if not best.empty else "",
        "best_synthesized_constructor_id": str(best["constructor_id"].iloc[0]) if not best.empty else "",
        "finite_checked_recoveries": int(pd.to_numeric(recoveries.get("finite_checked", pd.Series(dtype=bool)), errors="coerce").fillna(0).sum()) if not recoveries.empty else 0,
        "true_contamination_count": 0,
        "terminal_claims_from_advisory_count": safety_advisory,
        "failed_search_promoted_true_count": 0,
    }


def _family_tables(family: str, n: int, seed: int) -> list[tuple[list[list[int]], str]]:
    fresh = n - 1
    tables: list[tuple[list[list[int]], str]] = []
    if family == "constant":
        tables.extend(([[c for _ in range(n)] for _ in range(n)], f"constant_{c}") for c in range(n))
    elif family == "left_projection":
        tables.append(([[i for _ in range(n)] for i in range(n)], "left_projection"))
    elif family == "right_projection":
        tables.append(([[j for j in range(n)] for _ in range(n)], "right_projection"))
    elif family == "add_mod":
        tables.append(([[(i + j) % n for j in range(n)] for i in range(n)], "add_mod"))
    elif family == "sub_mod":
        tables.append(([[(i - j) % n for j in range(n)] for i in range(n)], "sub_mod"))
    elif family == "xor_mod":
        tables.append(([[(i ^ j) % n for j in range(n)] for i in range(n)], "xor_mod"))
    elif family == "linear_combo_mod":
        for a, b, c in ((1, 1, 0), (1, 2, 0), (2, 1, 1)):
            tables.append(([[((a * i + b * j + c) % n) for j in range(n)] for i in range(n)], f"linear_{a}_{b}_{c}"))
    elif family in {"projection_exception_left", "quotient_spike"}:
        base = [[i for _ in range(n)] for i in range(n)]
        for c in range(n):
            table = [row[:] for row in base]
            table[fresh][fresh] = c
            tables.append((table, f"{family}_{c}"))
    elif family == "projection_exception_right":
        base = [[j for j in range(n)] for _ in range(n)]
        for c in range(n):
            table = [row[:] for row in base]
            table[fresh][fresh] = c
            tables.append((table, f"projection_exception_right_{c}"))
    elif family == "quotient_fresh_gate":
        tables.append(([[fresh if i == fresh or j == fresh else i for j in range(n)] for i in range(n)], "fresh_gate_left"))
        tables.append(([[fresh if i == fresh or j == fresh else j for j in range(n)] for i in range(n)], "fresh_gate_right"))
    elif family == "fresh_absorber":
        tables.append(([[fresh if i == fresh or j == fresh else 0 for j in range(n)] for i in range(n)], "fresh_absorber_zero"))
        tables.append(([[fresh if i == fresh or j == fresh else i for j in range(n)] for i in range(n)], "fresh_absorber_left"))
    elif family == "random_fresh_sink":
        rng = random.Random(seed)
        tables.append(([[fresh if i == fresh or j == fresh else rng.randrange(n) for j in range(n)] for i in range(n)], "random_fresh_sink"))
    elif family == "random_fresh_collapse":
        rng = random.Random(seed)
        tables.append(([[fresh if rng.random() < 0.65 or i == fresh or j == fresh else rng.randrange(n) for j in range(n)] for i in range(n)], "random_fresh_collapse"))
    elif family == "diagonal_spike":
        tables.append(([[fresh if i == j else 0 for j in range(n)] for i in range(n)], "diagonal_spike"))
    elif family == "diag_perturb_right":
        table = [[j for j in range(n)] for _ in range(n)]
        for i in range(n):
            table[i][i] = (i + 1) % n
        tables.append((table, "diag_perturb_right"))
    elif family == "diag_perturb_left":
        table = [[i for _ in range(n)] for i in range(n)]
        for i in range(n):
            table[i][i] = (i + 1) % n
        tables.append((table, "diag_perturb_left"))
    elif family == "tail_coupled_projection":
        tables.append(([[j if i <= j else i for j in range(n)] for i in range(n)], "tail_coupled_projection"))
    elif family == "head_coupled_projection":
        tables.append(([[i if i <= j else j for j in range(n)] for i in range(n)], "head_coupled_projection"))
    elif family == "row_erasure_family":
        for row in range(n):
            table = [[i for _ in range(n)] for i in range(n)]
            table[row] = [fresh for _ in range(n)]
            tables.append((table, f"row_erasure_{row}"))
    elif family == "col_erasure_family":
        for col in range(n):
            table = [[i for _ in range(n)] for i in range(n)]
            for i in range(n):
                table[i][col] = fresh
            tables.append((table, f"col_erasure_{col}"))
    elif family in {"block_selector", "block_selector_dual"}:
        split = max(1, n // 2)
        table = [[0 if (i < split) == (j < split) else fresh for j in range(n)] for i in range(n)]
        if family == "block_selector_dual":
            table = [[fresh - value if n > 1 else value for value in row] for row in table]
        tables.append((table, family))
    elif family == "prior":
        tables.extend(_family_tables("constant", n, seed)[:1])
        tables.extend(_family_tables("left_projection", n, seed))
        tables.extend(_family_tables("right_projection", n, seed))
    return tables


def _parse_features(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def _table_tuple(table: Any) -> tuple[tuple[int, ...], ...]:
    if isinstance(table, str):
        table = json.loads(table)
    return tuple(tuple(int(x) for x in row) for row in table)


def _as_bool(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)
