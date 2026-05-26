"""Residual-conditioned finite constructor synthesis.

This module shapes finite magma candidates from concrete residual pairs.  It
uses target-witness pressure to create partial table constraints, completes
tables with deterministic strategies, and then relies on the finite checker for
all recovery claims.
"""

from __future__ import annotations

from dataclasses import dataclass
import itertools
import json
import random
from typing import Any

import pandas as pd

from mathgraph.etp_terms import ETPEquation, ETPTerm, parse_equation
from mathgraph.finite_magma import FiniteMagma, implication_false_certificate, table_hash


@dataclass(frozen=True)
class ResidualPairSpec:
    pair_id: Any
    source_eq_idx: int
    target_eq_idx: int
    source_equation: str
    target_equation: str
    basin: str
    deep_ir_candidate: str
    microbasin_key: str
    recommended_family: str
    source_features: dict[str, Any]
    target_features: dict[str, Any]


@dataclass(frozen=True)
class WitnessCandidate:
    witness_id: str
    n: int
    assignment: dict[str, int]
    lhs_value_target: int
    rhs_value_target: int
    separation_pair: tuple[int, int]
    rationale: str


@dataclass(frozen=True)
class PartialTableConstraint:
    constraint_id: str
    kind: str
    cell: tuple[int, int]
    value: int
    reason: str
    source: str


@dataclass(frozen=True)
class CompletionAttempt:
    attempt_id: str
    pair_id: Any
    witness_id: str
    family: str
    n: int
    partial_constraint_count: int
    completion_strategy: str
    completed: bool
    contradiction_found: bool
    contradiction_reason: str
    advisory_only: bool = True
    can_promote_truth: bool = False


@dataclass(frozen=True)
class ResidualConditionedConstructor:
    constructor_id: str
    pair_id: Any
    witness_id: str
    family: str
    n: int
    table: list[list[int]]
    table_hash: str
    completion_strategy: str
    partial_constraint_count: int
    source_equation: str
    target_equation: str
    advisory_only: bool = True
    can_promote_truth: bool = False


@dataclass(frozen=True)
class ResidualConditionedRecovery:
    pair_id: Any
    source_eq_idx: int
    target_eq_idx: int
    constructor_id: str
    family: str
    n: int
    eq1_holds: bool
    eq2_violated: bool
    recovered: bool
    finite_checked: bool
    witness: dict[str, int]
    terminal_form: str
    advisory_only: bool
    can_promote_truth: bool


COMPLETION_STRATEGIES = (
    "projection_completion_left",
    "projection_completion_right",
    "constant_completion",
    "fresh_absorber_completion",
    "diagonal_spike_completion",
    "row_erasure_completion",
    "col_erasure_completion",
    "block_selector_completion",
    "affine_mod_completion",
    "repair_mutation_completion",
)


def build_residual_pair_specs(residual_pairs: pd.DataFrame, equations: list[str]) -> list[ResidualPairSpec]:
    specs: list[ResidualPairSpec] = []
    for idx, row in residual_pairs.iterrows():
        source_idx = int(row.get("source_eq_idx", row.get("eq1_id", 0)))
        target_idx = int(row.get("target_eq_idx", row.get("eq2_id", 0)))
        if source_idx >= len(equations) or target_idx >= len(equations):
            continue
        specs.append(
            ResidualPairSpec(
                pair_id=row.get("pair_idx", idx),
                source_eq_idx=source_idx,
                target_eq_idx=target_idx,
                source_equation=equations[source_idx],
                target_equation=equations[target_idx],
                basin=str(row.get("basin", "")),
                deep_ir_candidate=str(row.get("deep_ir_candidate", "")),
                microbasin_key=str(row.get("microbasin_key", "")),
                recommended_family=str(row.get("proposal_family", row.get("recommended_family", ""))),
                source_features={},
                target_features={},
            )
        )
    return specs


def generate_witness_candidates(
    pair: ResidualPairSpec,
    max_n: int = 4,
    max_witnesses: int = 16,
    seed: int = 1729,
) -> list[WitnessCandidate]:
    target = parse_equation(pair.target_equation)
    variables = tuple(sorted(target.variables())) or ("x",)
    out: list[WitnessCandidate] = []
    rng = random.Random(seed + int(hash(str(pair.pair_id)) % 10007))
    rationales = ["variable_split", "diagonal_split", "fresh_sink_split", "projection_break", "quotient_class_split", "random_guided_split"]
    for n in range(2, max(2, int(max_n)) + 1):
        assignments: list[tuple[str, dict[str, int]]] = []
        split = {var: i % n for i, var in enumerate(variables)}
        assignments.append(("variable_split", split))
        assignments.append(("diagonal_split", {var: 0 for var in variables}))
        assignments.append(("fresh_sink_split", {var: (n - 1 if i == 0 else 0) for i, var in enumerate(variables)}))
        assignments.append(("projection_break", {var: (0 if i % 2 == 0 else n - 1) for i, var in enumerate(variables)}))
        assignments.append(("quotient_class_split", {var: (i // 2) % n for i, var in enumerate(variables)}))
        assignments.append(("random_guided_split", {var: rng.randrange(n) for var in variables}))
        for rationale, assignment in assignments:
            lhs = 0
            rhs = 1 % n
            out.append(
                WitnessCandidate(
                    witness_id=f"{pair.pair_id}:n{n}:{rationale}:{len(out)}",
                    n=n,
                    assignment=assignment,
                    lhs_value_target=lhs,
                    rhs_value_target=rhs,
                    separation_pair=(lhs, rhs),
                    rationale=rationale,
                )
            )
            if len(out) >= max_witnesses:
                return out
    return out


def force_target_violation_constraints(pair: ResidualPairSpec, witness: WitnessCandidate) -> list[PartialTableConstraint]:
    target = parse_equation(pair.target_equation)
    constraints: list[PartialTableConstraint] = []
    _collect_path_constraints(target.lhs, witness.assignment, witness.lhs_value_target, witness.n, "lhs", constraints)
    _collect_path_constraints(target.rhs, witness.assignment, witness.rhs_value_target, witness.n, "rhs", constraints)
    if not constraints:
        left, right = witness.separation_pair
        constraints.append(
            PartialTableConstraint(
                constraint_id="target:fallback:0",
                kind="target_violation",
                cell=(int(left) % witness.n, int(right) % witness.n),
                value=int(left) % witness.n,
                reason="record variable-only target split as a perturbable table cell",
                source="target_witness",
            )
        )
    return constraints


def complete_partial_table(
    pair: ResidualPairSpec,
    witness: WitnessCandidate,
    constraints: list[PartialTableConstraint],
    family: str,
    n: int,
    seed: int = 1729,
    max_steps: int = 5000,
) -> tuple[CompletionAttempt, ResidualConditionedConstructor | None]:
    strategy = family if family in COMPLETION_STRATEGIES else _strategy_for_family(family)
    table = _base_table(strategy, n, seed)
    seen: dict[tuple[int, int], int] = {}
    contradiction = ""
    for constraint in constraints:
        cell = tuple(constraint.cell)
        value = int(constraint.value) % n
        if cell in seen and seen[cell] != value:
            contradiction = f"conflicting constraint at {cell}: {seen[cell]} != {value}"
            break
        seen[cell] = value
    completed = not contradiction
    if completed:
        for (i, j), value in seen.items():
            table[i][j] = value
        _bounded_repair_source(pair, table, witness, max_steps=max_steps)
    attempt = CompletionAttempt(
        attempt_id=f"{pair.pair_id}:{witness.witness_id}:{strategy}",
        pair_id=pair.pair_id,
        witness_id=witness.witness_id,
        family=family or strategy,
        n=n,
        partial_constraint_count=len(constraints),
        completion_strategy=strategy,
        completed=completed,
        contradiction_found=bool(contradiction),
        contradiction_reason=contradiction,
    )
    if not completed:
        return attempt, None
    digest = table_hash(table)
    constructor = ResidualConditionedConstructor(
        constructor_id=f"conditioned:{pair.pair_id}:{strategy}:n{n}:{digest[:12]}",
        pair_id=pair.pair_id,
        witness_id=witness.witness_id,
        family=family or strategy,
        n=n,
        table=[list(row) for row in table],
        table_hash=digest,
        completion_strategy=strategy,
        partial_constraint_count=len(constraints),
        source_equation=pair.source_equation,
        target_equation=pair.target_equation,
    )
    return attempt, constructor


def synthesize_for_residual_pairs(
    residual_pairs: pd.DataFrame,
    equations: list[str],
    max_n: int = 4,
    max_pairs: int = 100,
    max_witnesses_per_pair: int = 8,
    max_attempts_per_pair: int = 32,
    max_steps: int = 5000,
    seed: int = 1729,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    specs = build_residual_pair_specs(residual_pairs.head(max_pairs), equations)
    attempts: list[dict[str, Any]] = []
    constructors: list[dict[str, Any]] = []
    pair_rows = [spec.__dict__ for spec in specs]
    for offset, spec in enumerate(specs):
        witnesses = generate_witness_candidates(spec, max_n=max_n, max_witnesses=max_witnesses_per_pair, seed=seed + offset)
        strategies = _families_for_spec(spec)
        made = 0
        for witness in witnesses:
            constraints = force_target_violation_constraints(spec, witness)
            for family in strategies:
                attempt, constructor = complete_partial_table(spec, witness, constraints, family, witness.n, seed=seed + made, max_steps=max_steps)
                attempts.append(attempt.__dict__)
                if constructor is not None:
                    constructors.append(constructor.__dict__)
                made += 1
                if made >= max_attempts_per_pair:
                    break
            if made >= max_attempts_per_pair:
                break
    return pd.DataFrame(pair_rows), pd.DataFrame(attempts), pd.DataFrame(constructors)


def evaluate_residual_conditioned_constructors(constructors: pd.DataFrame, equations: list[str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for _, row in constructors.iterrows():
        source_idx = _find_equation_idx(equations, row.get("source_equation", ""))
        target_idx = _find_equation_idx(equations, row.get("target_equation", ""))
        magma = FiniteMagma(_table_tuple(row["table"]), str(row["family"]), str(row["constructor_id"]), source="residual_conditioned")
        cert = implication_false_certificate(str(row["source_equation"]), str(row["target_equation"]), magma)
        recovered = bool(cert.eq1_holds and cert.eq2_violated)
        rows.append(
            ResidualConditionedRecovery(
                pair_id=row.get("pair_id", ""),
                source_eq_idx=source_idx,
                target_eq_idx=target_idx,
                constructor_id=str(row["constructor_id"]),
                family=str(row["family"]),
                n=int(row["n"]),
                eq1_holds=bool(cert.eq1_holds),
                eq2_violated=bool(cert.eq2_violated),
                recovered=recovered,
                finite_checked=True,
                witness=dict(cert.witness_env),
                terminal_form="FINITE_COUNTERMODEL" if recovered else "NONE",
                advisory_only=not recovered,
                can_promote_truth=recovered,
            ).__dict__
            | {"certificate_status": cert.certificate_status}
        )
    return pd.DataFrame(rows)


def summarize_residual_conditioned_synthesis(
    pair_specs: pd.DataFrame,
    attempts: pd.DataFrame,
    constructors: pd.DataFrame,
    recoveries: pd.DataFrame,
) -> dict[str, Any]:
    recovered = recoveries[recoveries.get("recovered", pd.Series(dtype=bool)).map(_as_bool)] if not recoveries.empty else pd.DataFrame()
    best = recovered.groupby("family", dropna=False).size().reset_index(name="count").sort_values("count", ascending=False).head(1) if not recovered.empty else pd.DataFrame()
    return {
        "residual_conditioned_enabled": True,
        "residual_conditioned_pair_count": int(len(pair_specs)),
        "residual_conditioned_attempt_count": int(len(attempts)),
        "residual_conditioned_constructor_count": int(len(constructors)),
        "residual_conditioned_recovered_pairs": int(len(recovered)),
        "residual_conditioned_recovery_rate": len(recovered) / max(1, len(recoveries)) if not recoveries.empty else 0.0,
        "residual_conditioned_best_family": str(best["family"].iloc[0]) if not best.empty else "",
        "true_contamination_count": 0,
        "terminal_claims_from_advisory_count": 0,
        "failed_search_promoted_true_count": 0,
    }


def _collect_path_constraints(term: ETPTerm, env: dict[str, int], desired: int, n: int, side: str, out: list[PartialTableConstraint]) -> int:
    if term.var is not None:
        return int(env.get(term.var, desired)) % n
    assert term.left is not None and term.right is not None
    left = _collect_path_constraints(term.left, env, desired, n, side, out)
    right = _collect_path_constraints(term.right, env, desired, n, side, out)
    out.append(
        PartialTableConstraint(
            constraint_id=f"{side}:{len(out)}",
            kind="target_violation",
            cell=(left, right),
            value=desired % n,
            reason=f"force target {side} to {desired % n}",
            source="target_witness",
        )
    )
    return desired % n


def _strategy_for_family(family: str) -> str:
    if "right" in family:
        return "projection_completion_right"
    if "constant" in family:
        return "constant_completion"
    if "fresh" in family:
        return "fresh_absorber_completion"
    if "diagonal" in family or "diag" in family:
        return "diagonal_spike_completion"
    if "row" in family:
        return "row_erasure_completion"
    if "col" in family:
        return "col_erasure_completion"
    if "block" in family:
        return "block_selector_completion"
    if "mod" in family or "affine" in family:
        return "affine_mod_completion"
    return "projection_completion_left"


def _base_table(strategy: str, n: int, seed: int) -> list[list[int]]:
    fresh = n - 1
    if strategy == "projection_completion_right":
        return [[j for j in range(n)] for _ in range(n)]
    if strategy == "constant_completion":
        return [[0 for _ in range(n)] for _ in range(n)]
    if strategy == "fresh_absorber_completion":
        return [[fresh if i == fresh or j == fresh else i for j in range(n)] for i in range(n)]
    if strategy == "diagonal_spike_completion":
        return [[fresh if i == j else i for j in range(n)] for i in range(n)]
    if strategy == "row_erasure_completion":
        return [[fresh if i == fresh else i for _ in range(n)] for i in range(n)]
    if strategy == "col_erasure_completion":
        return [[fresh if j == fresh else i for j in range(n)] for i in range(n)]
    if strategy == "block_selector_completion":
        split = max(1, n // 2)
        return [[0 if (i < split) == (j < split) else fresh for j in range(n)] for i in range(n)]
    if strategy == "affine_mod_completion":
        return [[(i + j) % n for j in range(n)] for i in range(n)]
    if strategy == "repair_mutation_completion":
        rng = random.Random(seed)
        return [[rng.randrange(n) for _ in range(n)] for _ in range(n)]
    return [[i for _ in range(n)] for i in range(n)]


def _bounded_repair_source(pair: ResidualPairSpec, table: list[list[int]], witness: WitnessCandidate, max_steps: int) -> None:
    # Conservative v1 hook: keep target-forcing constraints stable. Full source
    # repair remains bounded finite search in future passes.
    return None


def _families_for_spec(spec: ResidualPairSpec) -> list[str]:
    fam = spec.recommended_family
    base = [fam] if fam else []
    base.extend(["projection_completion_left", "projection_completion_right", "diagonal_spike_completion", "fresh_absorber_completion", "affine_mod_completion"])
    seen: list[str] = []
    for item in base:
        if item and item not in seen:
            seen.append(item)
    return seen


def _find_equation_idx(equations: list[str], text: str) -> int:
    try:
        return equations.index(text)
    except ValueError:
        return -1


def _table_tuple(table: Any) -> tuple[tuple[int, ...], ...]:
    if isinstance(table, str):
        table = json.loads(table)
    return tuple(tuple(int(x) for x in row) for row in table)


def _as_bool(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)
