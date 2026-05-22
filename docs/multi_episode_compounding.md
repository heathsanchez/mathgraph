# Multi-Episode Lawbook Compounding Evaluation v0

Single-run benchmarks show whether a scheduler works on one slice.  They do not
prove compounding.  Compounding means that verified contact in one episode makes
later verifier-directed search cheaper or stronger.

This evaluation runs multiple controlled episodes and measures:

- durable Lawbook growth
- Lawbook attention hit/action-change rate
- durable artifact reuse
- residual shrinkage
- certificate yield per attempt
- H-Tilt plus Lawbook delta
- decode-filtered Lawbook delta

## Modes

Each episode reports:

- `baseline_static`
- `persistent_atlas`
- `htilt_best_v`
- `lawbook_attention`
- `lawbook_attention_plus_htilt`
- `decode_filtered_lawbook_plus_htilt`
- `durable_only_lawbook_plus_htilt`

The durable-only mode can only use artifacts admitted as durable/verified memory
by Production Lawbook Admission. Advisory motifs and fallback smoke artifacts
are excluded.

## Admission

Every episode sends benchmark artifacts through the admission workflow. Fallback
artifacts are blocked from durable memory. Failed finite search is residual
evidence only and never implies TRUE.

## Real vs Fallback

If `/content/equations.txt` and `/content/etp_matrix_full_best_bool.npy` exist,
the runner is ready for real SAIR mode. If they are absent and fallback is
allowed, the runner produces a clearly marked fallback smoke result:

- `real_sair_used: false`
- `fallback_mode: true`
- `fallback_smoke_compounding_signal` may be true or false

Fallback is useful for CI and wiring. It is not real compounding evidence.

## Run

```bash
python scripts/run_multi_episode_compounding.py \
  --equations-path /content/equations.txt \
  --matrix-path /content/etp_matrix_full_best_bool.npy \
  --lawbook-path /content/drive/MyDrive/SAIR_MathGraph/lawbook.sqlite \
  --output-dir /content/drive/MyDrive/SAIR_MathGraph/multi_episode_compounding_run \
  --num-episodes 3 \
  --episode-size 250 \
  --train-fraction 0.5 \
  --strict-admission
```

Local fallback smoke:

```bash
python scripts/run_multi_episode_compounding.py \
  --output-dir /tmp/mathgraph_multi_episode_compounding_smoke \
  --num-episodes 3 \
  --episode-size 50 \
  --allow-fallback \
  --strict-admission
```

