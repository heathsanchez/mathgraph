# TaskSAT semantic-boundary audit V1

**Status:** WARRANTED at the frozen upstream boundary below.

**Objective.** Test whether TaskSAT's Python SMT verifier and its executable Lean validator preserve the same semantics for bounded numeric assignments.

**Frozen upstream.** `nasa-jpl/tasksat@f9d6063b45967a3fea578c47f54806aadaafe1b0`.

**Decisive evidence.** GitHub Actions run [36606705115](https://github.com/heathsanchez/mathgraph/actions/runs/36606705115) passed the pinned dual-execution gate on commit `359d084c68e1815524c810c1bb1fe66ff3c05885`.

Observed outputs:

```text
TASKSAT_WELLFORMED=true
PYTHON_SMT_STATUS=UNSAT
PYTHON_ORDER=clamp_then_assignment
LEAN_SOURCE_ORDER=assignment_then_clamp
LEAN_ADMISSIBLE=true
LEAN_ASSIGNMENT_RESULT=within_[0,10]_after_clamp
```

Therefore the shared-semantics claim is **WARRANTED false for this accepted source fragment**: the Python verifier and executable Lean validator do not denote the same transition system here.

## Exact separator

For cumulative timelines, the two implementations order assignment and clamping differently.

Python SMT (`src/smt/tasknet_smt.py`) computes the delta evolution, clamps it to `bounds`, then lets an `ImpactAssign` override that clamped expression before asserting the next-zone value.

Lean (`src/lean/TaskNetExec/TaskNet/Semantics.lean`) forms the assigned/additive result first and then applies `clamp` in `applyChanges` before inserting the final value.

The minimal separating witness is:

```text
x : cumulative [0,10] bounds [0,10] = 0
required T at [1,2]: pre impact x = 50
```

This avoids the separate question of whether `range` is permitted to exceed `bounds`.

- **Python SMT:** UNSAT. Assignment forces a zone value of 50, while the hard range constraint requires `0 <= x <= 10`.
- **Lean validator:** admissible. The assignment is clamped to 10 before range checking.

## Verification boundary

The workflow `TaskSAT semantic boundary audit`:

1. checks out the exact upstream SHA;
2. parses and well-formedness-checks the witness with upstream TaskSAT;
3. executes the upstream Python SMT encoder and requires UNSAT;
4. source-guards the causal order at the frozen SHA;
5. builds the upstream `TaskNetExec` Lean package with its own pinned Lean toolchain;
6. executes `LeanWitness.lean` and requires `AdmissibleSparse = true`.

No PVS/CAD machinery is needed for V1 because the residual is cheaper: a one-dimensional linear separator already decides it. PVS CAD becomes relevant when a future semantic bridge produces genuinely quantified semialgebraic obligations.

## Epistemic state

- **WARRANTED:** the two pinned executable artifacts disagree on this accepted witness.
- **UNKNOWN:** which behavior is the intended authoritative TaskSAT semantics and therefore which implementation should change.
- **REUSABLE:** same-source / dual-semantics / minimized-counterexample / pinned-CI audit pattern.
- **SUPERSESSION rule:** if upstream later aligns the semantics, preserve this witness and mark the frozen result superseded rather than deleting it.

## Authority map

The divergence is not just Python versus Lean; the repository's semantic descriptions are themselves split.

Evidence favoring **clamp the final numeric value, including assignment**:
- `src/lean/TaskNet/TaskNet/Semantics.lean`: assignment overrides the old value, optional addition is applied, then bounds clamp the result.
- `src/lean/TaskNetExec/TaskNet/Semantics.lean`: the executable validator follows the same order.
- `src/smt/tasknet_ast.py`: describes bounds as the timeline's type and says computed values are clamped into it.
- `website/docs/reference/manual.md` and the tutorial: say any computed value is clamped to bounds / a cumulative value is always within bounds, while also allowing assignment.

Evidence favoring **assignment overrides an already-clamped additive value**:
- `src/smt/tasknet_smt.py`: the operational SMT encoding used by the verifier.
- `website/docs/theory/smt-encoding.md`: its detailed zone-transition formula places assignment after clamping.
- `src/lean/TaskNetPaper/TaskNet/semantics.lean`: an explicitly schematic paper skeleton also models assignment as overriding the clamped base value.

So the implementation disagreement is WARRANTED, and the repository contains a WARRANTED specification/description disagreement. Which branch is authoritative remains UNKNOWN until the TaskSAT/MEXEC intent is resolved.

## Lineage

Run [36606556197](https://github.com/heathsanchez/mathgraph/actions/runs/36606556197) already obtained the Python UNSAT result, but failed afterward on an over-specific source-text guard. That was a harness failure, not contrary mathematical evidence. Commit `359d084c68e1815524c810c1bb1fe66ff3c05885` corrected the guard without changing the witness or expected semantic outcomes; run 36606705115 then passed both executions.

## Why this matters

TaskSAT is a useful NASA/JPL semantic-audit target because it has both an operational SMT implementation and an independently executable Lean semantics. That makes semantic commuting failures observable:

```text
TaskSAT source
   |                    |
   v                    v
Python SMT model     Lean execution
   |                    |
   +---- must agree ----+
```

V1 proves one square does not commute at the frozen upstream commit.
