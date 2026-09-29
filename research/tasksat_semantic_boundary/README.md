# TaskSAT semantic-boundary audit V1

**Status:** CANDIDATE pending the pinned dual-execution CI gate.

**Objective.** Test whether TaskSAT's Python SMT verifier and its executable Lean validator preserve the same semantics for bounded numeric assignments.

**Frozen upstream.** `nasa-jpl/tasksat@f9d6063b45967a3fea578c47f54806aadaafe1b0`.

## Smallest residual

For cumulative timelines, the two implementations order assignment and clamping differently.

Python SMT (`src/smt/tasknet_smt.py`) computes the delta evolution, clamps it to `bounds`, then lets an `ImpactAssign` override that clamped expression before asserting the next-zone value.

Lean (`src/lean/TaskNetExec/TaskNet/Semantics.lean`) forms the assigned/additive result first and then applies `clamp` in `applyChanges` before inserting the final value.

The minimal separating witness is:

```text
x : cumulative [0,10] bounds [0,10] = 0
required T at [1,2]: pre impact x = 50
```

This avoids the separate question of whether `range` is permitted to exceed `bounds`.

### Predicted separator

- **Python SMT:** UNSAT. Assignment forces a zone value of 50, while the hard range constraint requires `0 <= x <= 10`.
- **Lean validator:** admissible. The assignment is clamped to 10 before range checking.

If both pinned executions confirm those outcomes, the shared-semantics claim is **WARRANTED false for this case**: the Python verifier and Lean validator do not denote the same transition system on an accepted TaskSAT syntax fragment.

## Evidence gate

The workflow `TaskSAT semantic boundary audit`:

1. checks out the exact upstream SHA;
2. parses and well-formedness-checks the witness with upstream TaskSAT;
3. executes the upstream Python SMT encoder and requires UNSAT;
4. source-guards the causal order at the frozen SHA;
5. builds the upstream `TaskNetExec` Lean package with its own pinned Lean toolchain;
6. executes `LeanWitness.lean` and requires `AdmissibleSparse = true`.

No PVS/CAD machinery is introduced here because this residual is cheaper: a one-dimensional linear separator already decides it. PVS CAD becomes relevant only when the semantic bridge produces genuinely quantified semialgebraic obligations.

## Promotion rule

Promote **CANDIDATE -> WARRANTED** only after the dual-execution GitHub Actions gate is green. A later upstream change that aligns the semantics should mark this witness **SUPERSEDED**, not erase it.

## Why this matters

TaskSAT is already a useful NASA/JPL bridge target because it has both an operational SMT implementation and an independently executable Lean semantics. That makes semantic commuting failures observable rather than philosophical:

```text
TaskSAT source
   |                    |
   v                    v
Python SMT model     Lean execution
   |                    |
   +---- must agree ----+
```

This V1 tests one exact square, preserves the upstream commit, and produces a replayable separator.
