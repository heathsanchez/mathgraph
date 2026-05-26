# Autonomous Compounding Engine

The autonomous compounding engine is a repo-native entry point for the serious
ETP finite-recovery path. It has two modes:

- `facade`: the stable compatibility path over the existing finite-core
  compounding runner.
- `native_v2`: the repo-native finite recovery, residual repair, and advisory
  Lawbook reuse loop.

It wraps `scripts/run_mathgraph_compounding_engine.py` rather than simulating
recovery in `facade` mode. The `native_v2` path uses the finite magma
satisfaction cache directly:

```text
constructor bank -> SAT cache -> generic route -> residual repair
-> PQ-IR obstruction naming -> advisory Lawbook reuse -> compact atlas route
```

## Boundary

- FALSE recovery is counted only when a constructor satisfies the source law and
  violates the target law.
- TRUE controls audit contamination.
- Failed finite search is residual evidence, never TRUE.
- PQ-IR, route policies, residual obstructions, and repair family memory are
  advisory until a verifier/checker boundary accepts a terminal form.

## Tiny demo

```bash
python scripts/run_autonomous_compounding_engine.py \
  --out-dir /tmp/mathgraph_autonomous_demo \
  --tiny-demo \
  --episodes 2 \
  --sample-pairs 80 \
  --repair-budget 20
```

Native v2 smoke:

```bash
python scripts/run_autonomous_compounding_engine.py \
  --out-dir /tmp/mathgraph_autonomous_v2_tiny \
  --tiny-demo \
  --finite-core-mode native_v2 \
  --episodes 3 \
  --sample-pairs 80 \
  --repair-budget 20 \
  --max-n 3 \
  --seed 20260524 \
  --write-report
```

## Real ETP / SAIR run

```bash
python scripts/run_autonomous_compounding_engine.py \
  --equations /content/equations.txt \
  --matrix /content/etp_matrix_full_best_bool.npy \
  --out-dir /content/drive/MyDrive/SAIR_MathGraph/Autonomous_Run \
  --episodes 4 \
  --sample-pairs 4000 \
  --repair-budget 40
```

Native v2 real ETP example:

```bash
python scripts/run_autonomous_compounding_engine.py \
  --equations /content/equations.txt \
  --matrix /content/etp_matrix_full_best_bool.npy \
  --out-dir /content/drive/MyDrive/SAIR_MathGraph/autonomous_v2_real \
  --finite-core-mode native_v2 \
  --episodes 4 \
  --sample-pairs 4000 \
  --repair-budget 40 \
  --max-n 4 \
  --constructor-limit 500 \
  --seed 20260524 \
  --write-report
```

The runner refuses real mode unless the equation and matrix files are supplied.

## Native v2 cross-seed benchmark

The benchmark harness runs native v2 once per seed, preserves each seed's
artifacts, stitches the seed-level CSV outputs, and reports cross-seed means for
generic routing, residual repair, advisory Lawbook reuse, and compact atlas
routing when those fields are emitted by the engine.

Colab-style real ETP run:

```bash
python scripts/run_autonomous_native_v2_benchmark.py \
  --equations /content/equations.txt \
  --matrix /content/etp_matrix_full_best_bool.npy \
  --out-dir /content/drive/MyDrive/SAIR_MathGraph/native_v2_benchmark \
  --seeds 20260524 20260525 20260526 \
  --episodes 4 \
  --sample-pairs 4000 \
  --repair-budget 40 \
  --max-n 4
```

Tiny fallback run:

```bash
python scripts/run_autonomous_native_v2_benchmark.py \
  --out-dir /tmp/mathgraph_native_v2_benchmark \
  --tiny-demo \
  --seeds 1729 1730 \
  --episodes 3 \
  --sample-pairs 80 \
  --repair-budget 10 \
  --max-n 3
```

Primary outputs:

- `benchmark_summary.json`
- `benchmark_report.md`
- `cross_seed_summary.csv`
- `cross_seed_episode_metrics.csv`
- `cross_seed_gate_results.csv`
- `cross_seed_terminal_audit.csv`
- `cross_seed_artifact_manifest.csv`

Safety gates require zero TRUE contamination, zero terminal claims from advisory
rows, and zero failed-search-to-TRUE promotion. Lawbook reuse is a routing
signal only unless the selected artifact is independently verifier-backed.

## Held-out Lawbook compounding benchmark

The held-out benchmark asks a stricter transfer question: can advisory
Lawbook/route structure learned on one FALSE-pair slice improve recovery on a
disjoint held-out FALSE slice?

Real ETP run:

```bash
python scripts/run_heldout_lawbook_compounding_benchmark.py \
  --equations /content/equations.txt \
  --matrix /content/etp_matrix_full_best_bool.npy \
  --out-dir /content/drive/MyDrive/SAIR_MathGraph/heldout_lawbook_compounding \
  --seeds 20260524,20260525,20260526 \
  --train-pairs 2500 \
  --heldout-pairs 2500 \
  --true-pairs 1000 \
  --episodes 3 \
  --repair-budget 40 \
  --max-n 4
```

Tiny fallback:

```bash
python scripts/run_heldout_lawbook_compounding_benchmark.py \
  --allow-fallback-demo \
  --out-dir /tmp/mathgraph_heldout_lawbook_demo \
  --seeds 1729,1730 \
  --train-pairs 30 \
  --heldout-pairs 30 \
  --true-pairs 10 \
  --episodes 2 \
  --repair-budget 8 \
  --max-n 3
```

The Lawbook-guided policy is selected from train-slice constructor evidence and
then evaluated on held-out pairs. The bounded repair reference is explicitly
marked as a reference policy because it may inspect held-out recovery structure.
No benchmark row can promote truth without checker/verifier evidence.

## Exact constructor attribution

Held-out recovery rows include first-hit constructor attribution for each route
policy. For a FALSE pair, the attributed constructor is the first constructor in
the policy route that satisfies the source equation and violates the target
equation according to the finite SAT cache.

This makes Lawbook gains actionable:

```text
held-out gain -> exact constructor attribution -> micro-basin recipe
-> persistent Lawbook candidate -> sharper held-out routing
```

Exact attribution is still route-learning evidence. It is not terminal truth by
itself; FALSE promotion still requires checker-backed finite countermodel
evidence, and TRUE promotion still requires proof-verifier evidence.

## Persistent exact micro-basin Lawbook

The persistent exact micro-basin benchmark builds advisory memory from exact
Lawbook gain hits in earlier held-out episodes, then replays that memory on
later held-out episodes without using current-episode evidence first.

```bash
python scripts/run_persistent_exact_microbasin_lawbook_benchmark.py \
  --out-dir /tmp/mathgraph_persistent_exact_demo \
  --fallback-demo \
  --seeds 1729,1730,1731
```

Real ETP:

```bash
python scripts/run_persistent_exact_microbasin_lawbook_benchmark.py \
  --equations /content/equations.txt \
  --matrix /content/etp_matrix_full_best_bool.npy \
  --out-dir /content/drive/MyDrive/SAIR_MathGraph/persistent_exact_microbasin_lawbook_v1 \
  --seeds 20260524,20260525,20260526,20260527,20260528 \
  --train-pairs 1200 \
  --heldout-pairs 1200 \
  --true-pairs 500 \
  --episodes 2 \
  --repair-budget 40 \
  --max-n 4
```

The classification is intentionally scoped: strong or weak compounding means
prior exact route memory improved proxy held-out recovery. It is not TRUE-side
proof and it does not admit terminal claims.

Persistent v2 adds causal route selection:

```bash
python scripts/run_persistent_exact_microbasin_lawbook_v2_benchmark.py \
  --out-dir /tmp/mathgraph_persistent_exact_v2_demo \
  --fallback-demo \
  --seeds 1729,1730,1731,1732
```

V2 compares generic, one-shot Lawbook, v1 persistent memory, and v2 causal
persistent memory. It is designed to reject one-shot exact memories that do not
show stable non-regression.
