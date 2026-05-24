# Polarized Quotient-Continuation IR

For SAIR/ETP, a task has the form `EQ1 => EQ2`. The source equation creates
quotient pressure on the bounded term universe: some terms are forced together,
some continuations remain possible, and a target equation asks whether a
separation is still possible.

Polarized Quotient-Continuation IR records this as advisory routing data:

- source quotient pressure
- target separation pressure
- fresh-variable escape pressure
- projection boundary behavior
- repeat/tail continuation behavior
- viable and killed constructor families
- named obstruction pressure

PQ-IR is not a truth oracle. It cannot prove `TRUE`, `FALSE`,
`VERIFIED_PROOF`, or `FINITE_COUNTERMODEL`. It can only guide constructor and
verification routes. Finite-search failure never implies TRUE.

## Obstruction Names

Residual groups are named with:

```text
{basin}__{deep_ir_candidate}__{stage}_unresolved
```

These records are `named_obstruction_advisory` until separately validated by an
accepted obstruction boundary.

## Demo

```bash
python scripts/run_polarized_quotient_ir_demo.py \
  --out-dir /tmp/mathgraph_pqir_demo \
  --sample-pairs 100
```

With real SAIR files:

```bash
python scripts/run_polarized_quotient_ir_demo.py \
  --equations /content/equations.txt \
  --matrix /content/etp_matrix_full_best_bool.npy \
  --out-dir /content/mathgraph_pqir_demo \
  --sample-pairs 1000 \
  --seed 1729
```

The demo writes pair features, advisory obstruction records, and a short
summary. Later compounding engines can use these features to prioritize finite
checker attempts and residual queues.
