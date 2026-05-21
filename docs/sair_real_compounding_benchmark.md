# Real SAIR Compounding Benchmark v0

This benchmark is the first direct test of the MathGraph compounding thesis on
SAIR-style finite-countermodel recovery:

```text
episode memory
-> LawbookStore
-> sparse Lawbook attention
-> reason coagulation
-> decode-to-verify filtering
-> H-Tilt/V scheduling
-> held-out finite-countermodel recovery
```

## Data

Real mode expects:

- `/content/equations.txt`
- `/content/etp_matrix_full_best_bool.npy`

The implication matrix is used to sample known FALSE pairs.  A recovered FALSE
pair is counted only when the finite magma checker finds a concrete table that
satisfies the source equation globally and violates the target equation at a
witness, and the resulting certificate passes the existing PromotionGate path.

If the files are missing and fallback is enabled, the benchmark runs the
deterministic fallback corpus and marks:

- `real_sair_used: false`
- `fallback_mode: true`

Fallback smoke output is useful for CI, but it is not a real SAIR benchmark.

## Modes

The benchmark always reports the six canonical modes:

- `baseline_static`: static constructor order, no Lawbook attention, no H-Tilt.
- `persistent_atlas`: existing persistent/static Reason Atlas scheduling.
- `htilt_best_v`: best V/H-Tilt policy selected by the V-operator evaluator.
- `lawbook_attention`: Lawbook attention context without an H-Tilt boost.
- `lawbook_attention_plus_htilt`: Lawbook attention with best V/H-Tilt policy.
- `decode_filtered_lawbook_plus_htilt`: decode-tested Lawbook reasons with best
  V/H-Tilt policy.

In v0, Lawbook-attention modes reuse verifier-backed scheduler results and add
the Lawbook retrieval/decode layer around them.  Attention and decode are
advisory context.  They do not certify claims.

## Authority Boundary

The benchmark does not infer TRUE from finite-search failure.

Motifs, reasons, H-Tilt scores, scheduler priorities, and Lawbook attention are
advisory.  They can affect ordering and context.  They cannot emit terminal
truth.

Only PromotionGate-accepted finite-countermodel certificates count as recovered
FALSE artifacts.

## Metrics

Per mode:

- recovered false count
- yield rate
- certificates per attempt
- residual count and residual reduction
- cost proxy and cost per certificate
- Lawbook hit rate and action-change rate
- decode success rate
- H-Tilt operator and whether it added signal
- oracle fraction captured when available
- advisory boundary preservation

Aggregate:

- mean yield
- yield deltas versus baseline and persistent atlas
- best mode
- compounding signal detected
- real/fallback mode flags

## Run

```bash
python scripts/run_sair_real_compounding_benchmark.py \
  --equations-path /content/equations.txt \
  --matrix-path /content/etp_matrix_full_best_bool.npy \
  --out-dir /content/drive/MyDrive/SAIR_MathGraph/real_compounding_benchmark_v0 \
  --train-size 250 \
  --heldout-size 250 \
  --seeds 0,1,2 \
  --fallback-if-missing
```

Local fallback smoke:

```bash
python scripts/run_sair_real_compounding_benchmark.py \
  --out-dir /tmp/mathgraph_real_compounding_fallback_smoke \
  --fallback-if-missing \
  --train-size 50 \
  --heldout-size 50 \
  --seeds 0,1
```

