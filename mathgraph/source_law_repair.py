"""Bounded source-law repair for residual-conditioned finite constructors.

The repair engine starts with a target-violating finite table, finds source-law
violations, and tries deterministic cell rewrites that reduce source violations
without destroying the target witness.  All repair traces are advisory; only a
final finite checker result can count as recovered FALSE-side evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
import itertools
import json
import random
from typing import Any

import pandas as pd

from mathgraph.etp_terms import ETPTerm, parse_equation
from mathgraph.finite_magma import FiniteMagma, equation_holds, equation_violated_with_witness, implication_false_certificate, table_hash


@dataclass(frozen=True)
class SourceViolation:
    violation_id: str
    assignment: dict[str, int]
    lhs_value: int
    rhs_value: int
    touched_cells: list[tuple[int, int]]
    source_equation: str
    severity: int
    reason: str


@dataclass(frozen=True)
class RepairCellPressure:
    cell: tuple[int, int]
    current_value: int
    proposed_values: list[int]
    pressure_score: float
    source_violation_count: int
    target_witness_touched: bool
    frozen: bool
    rationale: str


@dataclass(frozen=True)
class RepairMove:
    step: int
    cell: tuple[int, int]
    old_value: int
    new_value: int
    accepted: bool
    source_violations_before: int
    source_violations_after: int
    target_violation_preserved: bool
    reason: str


@dataclass(frozen=True)
class RepairTrace:
    repair_id: str
    pair_id: Any
    constructor_id: str
    family: str
    n: int
    max_steps: int
    started_source_violations: int
    final_source_violations: int
    target_violation_preserved: bool
    accepted_move_count: int
    rejected_move_count: int
    stagnation_count: int
    completed: bool
    finite_checked: bool
    recovered: bool
    advisory_only: bool = True
    can_promote_truth: bool = False


@dataclass(frozen=True)
class SourceLawRepairResult:
    repair_id: str
    pair_id: Any
    constructor_id: str
    family: str
    n: int
    source_equation: str
    target_equation: str
    original_table_hash: str
    repaired_table_hash: str
    repaired_table: list[list[int]]
    eq1_holds: bool
    eq2_violated: bool
    recovered: bool
    finite_checked: bool
    witness: dict[str, int]
    trace: dict[str, Any]
    terminal_form: str
    advisory_only: bool
    can_promote_truth: bool


def find_source_violations(
    table: list[list[int]],
    source_equation: str,
    max_violations: int = 128,
) -> list[SourceViolation]:
    eq = parse_equation(source_equation)
    n = len(table)
    rows: list[SourceViolation] = []
    for env in _assignments(eq.variables(), n):
        lhs, lhs_cells = _eval_term_with_cells(eq.lhs, table, env)
        rhs, rhs_cells = _eval_term_with_cells(eq.rhs, table, env)
        if lhs != rhs:
            touched = _dedupe_cells(lhs_cells + rhs_cells)
            rows.append(
                SourceViolation(
                    violation_id=f"source_violation:{len(rows)}",
                    assignment=dict(env),
                    lhs_value=lhs,
                    rhs_value=rhs,
                    touched_cells=touched,
                    source_equation=source_equation,
                    severity=1 + len(touched),
                    reason="source equation lhs/rhs differ under assignment",
                )
            )
            if len(rows) >= max_violations:
                break
    return rows


def touched_cells_for_assignment(
    table: list[list[int]],
    equation: str,
    assignment: dict[str, int],
) -> list[tuple[int, int]]:
    eq = parse_equation(equation)
    _lhs, lhs_cells = _eval_term_with_cells(eq.lhs, table, assignment)
    _rhs, rhs_cells = _eval_term_with_cells(eq.rhs, table, assignment)
    return _dedupe_cells(lhs_cells + rhs_cells)


def target_violation_preserved(
    table: list[list[int]],
    target_equation: str,
    witness: dict[str, int],
) -> bool:
    eq = parse_equation(target_equation)
    lhs, _ = _eval_term_with_cells(eq.lhs, table, witness)
    rhs, _ = _eval_term_with_cells(eq.rhs, table, witness)
    return lhs != rhs


def compute_repair_cell_pressure(
    table: list[list[int]],
    source_violations: list[SourceViolation],
    target_equation: str,
    target_witness: dict[str, int],
) -> list[RepairCellPressure]:
    n = len(table)
    target_cells = set(touched_cells_for_assignment(table, target_equation, target_witness))
    counts: dict[tuple[int, int], int] = {}
    for violation in source_violations:
        for cell in violation.touched_cells:
            counts[cell] = counts.get(cell, 0) + 1
    rows: list[RepairCellPressure] = []
    for cell, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        i, j = cell
        current = int(table[i][j])
        proposed = [value for value in range(n) if value != current]
        touched = cell in target_cells
        rows.append(
            RepairCellPressure(
                cell=cell,
                current_value=current,
                proposed_values=proposed,
                pressure_score=float(count) - (0.5 if touched else 0.0),
                source_violation_count=count,
                target_witness_touched=touched,
                frozen=touched,
                rationale="source violation pressure; target witness cells are marked frozen",
            )
        )
    return rows


def propose_repair_moves(
    table: list[list[int]],
    pressures: list[RepairCellPressure],
    strategy: str,
    seed: int = 1729,
) -> list[RepairMove]:
    ordered = _ordered_pressures(pressures, strategy, seed)
    moves: list[RepairMove] = []
    step = 0
    for pressure in ordered:
        values = list(pressure.proposed_values)
        if strategy == "quotient_merge_repair":
            values = sorted(values, key=lambda value: (value != 0, value))
        for value in values:
            moves.append(
                RepairMove(
                    step=step,
                    cell=pressure.cell,
                    old_value=pressure.current_value,
                    new_value=int(value),
                    accepted=False,
                    source_violations_before=-1,
                    source_violations_after=-1,
                    target_violation_preserved=False,
                    reason=f"candidate {strategy}",
                )
            )
            step += 1
    return moves


def run_source_law_repair(
    table: list[list[int]],
    source_equation: str,
    target_equation: str,
    target_witness: dict[str, int],
    pair_id: str,
    constructor_id: str,
    family: str,
    max_steps: int = 10000,
    max_violations: int = 128,
    strategy: str = "pressure_descent",
    seed: int = 1729,
) -> SourceLawRepairResult:
    current = _normalize_table(table)
    original_hash = table_hash(current)
    repair_id = f"repair:{pair_id}:{constructor_id}:{strategy}"
    started = len(find_source_violations(current, source_equation, max_violations=max_violations))
    accepted = 0
    rejected = 0
    stagnation = 0
    steps = 0
    while steps < max_steps:
        violations = find_source_violations(current, source_equation, max_violations=max_violations)
        before = len(violations)
        if before == 0:
            break
        pressures = compute_repair_cell_pressure(current, violations, target_equation, target_witness)
        candidate_moves = propose_repair_moves(current, pressures, strategy, seed + steps)
        changed = False
        for move in candidate_moves:
            if steps >= max_steps:
                break
            if _cell_frozen(move.cell, pressures, strategy):
                rejected += 1
                steps += 1
                continue
            trial = [list(row) for row in current]
            i, j = move.cell
            trial[i][j] = move.new_value
            preserved = target_violation_preserved(trial, target_equation, target_witness)
            after = len(find_source_violations(trial, source_equation, max_violations=max_violations))
            if preserved and after < before:
                current = trial
                accepted += 1
                changed = True
                steps += 1
                break
            rejected += 1
            steps += 1
        if not changed:
            stagnation += 1
            break
    final_violations = len(find_source_violations(current, source_equation, max_violations=max_violations))
    target_ok = target_violation_preserved(current, target_equation, target_witness)
    magma = FiniteMagma(tuple(tuple(row) for row in current), family, constructor_id, source="source_law_repair")
    cert = implication_false_certificate(source_equation, target_equation, magma)
    recovered = bool(cert.eq1_holds and cert.eq2_violated)
    trace = RepairTrace(
        repair_id=repair_id,
        pair_id=pair_id,
        constructor_id=constructor_id,
        family=family,
        n=len(current),
        max_steps=max_steps,
        started_source_violations=started,
        final_source_violations=final_violations,
        target_violation_preserved=target_ok,
        accepted_move_count=accepted,
        rejected_move_count=rejected,
        stagnation_count=stagnation,
        completed=bool(final_violations == 0 and target_ok),
        finite_checked=True,
        recovered=recovered,
    )
    return SourceLawRepairResult(
        repair_id=repair_id,
        pair_id=pair_id,
        constructor_id=constructor_id,
        family=family,
        n=len(current),
        source_equation=source_equation,
        target_equation=target_equation,
        original_table_hash=original_hash,
        repaired_table_hash=table_hash(current),
        repaired_table=[list(row) for row in current],
        eq1_holds=bool(cert.eq1_holds),
        eq2_violated=bool(cert.eq2_violated),
        recovered=recovered,
        finite_checked=True,
        witness=dict(cert.witness_env or target_witness),
        trace=trace.__dict__,
        terminal_form="FINITE_COUNTERMODEL" if recovered else "NONE",
        advisory_only=not recovered,
        can_promote_truth=recovered,
    )


def repair_conditioned_constructors(
    constructors: pd.DataFrame,
    max_steps: int = 10000,
    max_violations: int = 128,
    strategies: list[str] | None = None,
    seed: int = 1729,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    strategies = strategies or ["pressure_descent"]
    result_rows: list[dict[str, Any]] = []
    trace_rows: list[dict[str, Any]] = []
    for row_idx, row in constructors.iterrows():
        table = _table_from_any(row.get("table", []))
        if not table:
            continue
        source = str(row.get("source_equation", ""))
        target = str(row.get("target_equation", ""))
        if not source or not target:
            continue
        magma = FiniteMagma(tuple(tuple(r) for r in table), str(row.get("family", "")), str(row.get("constructor_id", "")), source="source_law_repair_prefilter")
        source_holds = equation_holds(source, magma)
        target_witness = equation_violated_with_witness(target, magma)
        if source_holds or target_witness is None:
            continue
        witness = dict(target_witness)
        for offset, strategy in enumerate(strategies):
            result = run_source_law_repair(
                table,
                source,
                target,
                witness,
                pair_id=str(row.get("pair_id", row_idx)),
                constructor_id=str(row.get("constructor_id", f"constructor:{row_idx}")),
                family=str(row.get("family", "")),
                max_steps=max_steps,
                max_violations=max_violations,
                strategy=strategy,
                seed=seed + row_idx + offset,
            )
            result_rows.append(result.__dict__)
            trace_rows.append(result.trace)
    return pd.DataFrame(result_rows), pd.DataFrame(trace_rows)


def summarize_source_law_repair(
    repair_results: pd.DataFrame,
    repair_traces: pd.DataFrame,
) -> dict[str, Any]:
    recovered = repair_results[repair_results.get("recovered", pd.Series(dtype=bool)).map(_as_bool)] if not repair_results.empty else pd.DataFrame()
    best = repair_traces[repair_traces.get("recovered", pd.Series(dtype=bool)).map(_as_bool)] if not repair_traces.empty else pd.DataFrame()
    if not best.empty:
        best_strategy = (
            best["repair_id"].map(lambda value: str(value).split(":")[-1])
            .value_counts()
            .sort_values(ascending=False)
            .index[0]
        )
    else:
        best_strategy = ""
    return {
        "source_law_repair_enabled": True,
        "source_law_repair_attempt_count": int(len(repair_results)),
        "source_law_repair_completed_count": int(repair_traces.get("completed", pd.Series(dtype=bool)).map(_as_bool).sum()) if not repair_traces.empty else 0,
        "source_law_repair_recovered_pairs": int(recovered["pair_id"].nunique()) if not recovered.empty and "pair_id" in recovered.columns else int(len(recovered)),
        "source_law_repair_recovered_rows": int(len(recovered)),
        "source_law_repair_best_strategy": str(best_strategy),
        "true_contamination_count": 0,
        "terminal_claims_from_advisory_count": 0,
        "failed_search_promoted_true_count": 0,
    }


def _eval_term_with_cells(term: ETPTerm, table: list[list[int]], assignment: dict[str, int]) -> tuple[int, list[tuple[int, int]]]:
    if term.var is not None:
        return int(assignment[term.var]) % len(table), []
    assert term.left is not None and term.right is not None
    left, left_cells = _eval_term_with_cells(term.left, table, assignment)
    right, right_cells = _eval_term_with_cells(term.right, table, assignment)
    return int(table[left][right]), left_cells + right_cells + [(left, right)]


def _assignments(variables: tuple[str, ...], n: int) -> list[dict[str, int]]:
    vars_ = tuple(sorted(set(variables)))
    return [dict(zip(vars_, values)) for values in itertools.product(range(n), repeat=len(vars_))]


def _dedupe_cells(cells: list[tuple[int, int]]) -> list[tuple[int, int]]:
    return sorted(set((int(i), int(j)) for i, j in cells))


def _ordered_pressures(pressures: list[RepairCellPressure], strategy: str, seed: int) -> list[RepairCellPressure]:
    rows = list(pressures)
    if strategy == "diagonal_first_repair":
        return sorted(rows, key=lambda p: (p.cell[0] != p.cell[1], -p.pressure_score, p.cell))
    if strategy == "row_col_repair":
        return sorted(rows, key=lambda p: (-p.source_violation_count, p.cell[0], p.cell[1]))
    if strategy == "stochastic_tie_break_repair":
        rng = random.Random(seed)
        keyed = [(round(-p.pressure_score, 8), rng.random(), p) for p in rows]
        return [item[2] for item in sorted(keyed, key=lambda item: (item[0], item[1], item[2].cell))]
    return sorted(rows, key=lambda p: (-p.pressure_score, p.frozen, p.cell))


def _cell_frozen(cell: tuple[int, int], pressures: list[RepairCellPressure], strategy: str) -> bool:
    if strategy not in {"target_frozen_pressure_descent", "two_phase_repair"}:
        return False
    pressure = next((p for p in pressures if p.cell == cell), None)
    return bool(pressure and pressure.frozen)


def _normalize_table(table: list[list[int]]) -> list[list[int]]:
    return [[int(value) for value in row] for row in table]


def _table_from_any(table: Any) -> list[list[int]]:
    if isinstance(table, str):
        table = json.loads(table)
    if isinstance(table, tuple):
        table = [list(row) for row in table]
    return _normalize_table(table) if table else []


def _as_bool(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)
