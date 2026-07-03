# Replay Commands

All paths below assume the repository root is
`/Users/heath/Documents/New project`.

## Layer 1 and Layer 2 — main Lean 4.28 environment

```bash
cd experiments/continuation_claim_audit_lab/lean_project
lake env lean '/Users/heath/Documents/New project/examples/verifier_fixtures/lean/htilt_survivor_law.lean'
lake env lean '/Users/heath/Documents/New project/examples/verifier_fixtures/lean/htilt_discrete_doob_stationary.lean'
cd -
```

## Layer 3 — external exact-pin environment

```bash
cd experiments/pf_port_lab/vendor/HopfieldNet
lake build MCMC.PF.LinearAlgebra.Matrix.PerronFrobenius.Irreducible
lake build MCMC.PF.LinearAlgebra.Matrix.PerronFrobenius.Dominance
lake env lean '/Users/heath/Documents/New project/examples/verifier_fixtures/lean/htilt_pf_discrete_survivor_law.lean'
cd -
```

If disk headroom is low, use the bounded cache route described in
`experiments/pf_port_lab/pf_port_obstruction_trace.md`: cache the 30 direct
Mathlib roots of the 12-file PF closure rather than unpacking the full Mathlib
cache. That route downloaded 3,218 cached files in the recorded replay.

## Axiom audit

Temporarily place this command after the portal namespace and compile in the
external environment:

```lean
#print axioms HTiltPFDiscreteSurvivor.exists_positive_stationary_distribution_of_irreducible
```

Expected exact non-foundational result: no `sorryAx`. The recorded output is
`[propext, Classical.choice, Quot.sound]`.

## Placeholder scans for project files

```bash
rg -n '\b(sorry|admit|axiom|unsafe)\b' examples/verifier_fixtures/lean/htilt_survivor_law.lean || true
rg -n '\b(sorry|admit|axiom|unsafe)\b' examples/verifier_fixtures/lean/htilt_discrete_doob_stationary.lean || true
rg -n '\b(sorry|admit|axiom|unsafe)\b' examples/verifier_fixtures/lean/htilt_pf_discrete_survivor_law.lean || true
```

## External subtree scan

This scan may report one unrelated `sorry`; it is not in the promoted theorem's
dependency graph.

```bash
rg -n '\b(sorry|admit|axiom|unsafe)\b' experiments/pf_port_lab/vendor/HopfieldNet/MCMC/PF --glob '*.lean' || true
```

## Python regression

```bash
python -m pytest -q
```
