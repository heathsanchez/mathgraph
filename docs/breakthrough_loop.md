# MathGraph Breakthrough Loop v1

This is the first runnable MathGraph metabolism demo:

```text
unresolved finite magma implications
-> advisory constructor queue
-> deterministic finite checker
-> ExternalCertificate
-> PromotionGate
-> Lawbook candidate when boundary evidence is valid
-> Reason Atlas feedback
-> rescored next episode
```

## What Is Real

The formal world is finite magma equational implication. A task has:

```text
source equation implies target equation
```

A refutation certificate is a finite magma table plus witness environment such
that the source equation holds globally and the target equation fails at the
witness. The checker enumerates all finite environments for the source and
target. This is deterministic and exact for the supplied finite table.

Successful checks become `ExternalCertificate` objects with
`boundary_kind = FINITE_CHECKED` and `certificate_kind = FINITE_COUNTERMODEL`.
They are passed through `PromotionGate`. Only accepted gate decisions emit
Lawbook candidate rows.

## What Is Toy

The built-in corpus is small and synthetic. Constructor families are handpicked
finite tables such as projections, constant magmas, modular addition, and a
commutative non-associative table. The point is not benchmark scale; the point
is to prove the loop closes with real semantics.

## Variation, Evaluation, Selective Retention

- **Variation**: Reason Atlas constructor hints and queue priorities choose
  which finite table to try for each residual family.
- **Evaluation**: `mathgraph.finite_magma_world` checks the implication
  refutation exactly.
- **Selective retention**: `PromotionGate` admits only valid finite boundary
  certificates. Failures become Reason Atlas feedback and obstructions.
- **Compounding**: later episodes use updated feedback scores, try better
  constructor families, reduce residuals, and lower residual entropy.

## Boundary

Advisory artifacts do not promote truth. Failed finite searches are residual
feedback only. A table becomes a terminal refutation candidate only when the
checker proves:

1. the source equation holds globally on the table;
2. the target equation fails at a concrete witness;
3. the resulting `ExternalCertificate` has valid finite boundary evidence;
4. `PromotionGate` accepts it.

## Run

```bash
python scripts/run_breakthrough_loop_demo.py
```

Outputs are written to `/tmp/mathgraph_breakthrough_loop_demo/` by default:

- `breakthrough_summary.json`
- `episode_metrics.csv`
- `attempts.csv`
- `accepted_certificates.jsonl`
- `rejected_attempts.jsonl`
- `residual_tasks.csv`
- `reason_atlas_feedback.jsonl`
- `lawbook_candidates.jsonl`
- `queue_before_after.csv`
- `report.md`

## Toward SAIR

Finite magma implication is the right first bridge to SAIR Stage 2. The demo
uses toy tasks, but the checker shape matches the real false-factory contract:
source equation holds globally, target equation fails at a witness. Future work
can replace the built-in corpus with real SAIR pairs and plug in richer
countermodel constructors.

## Next Steps

- replace demo corpus with real SAIR equation pairs
- plug the full false factory into `BreakthroughLoop`
- add a Lean proof-side executor for proof terminal forms
- persist accepted Lawbook candidates into the production Lawbook store
- run H-Tilt over persistent Reason Atlas families
- induce root operators over finite countermodel traces
- add larger multi-episode compounding benchmarks
