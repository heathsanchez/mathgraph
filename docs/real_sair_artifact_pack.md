# Real SAIR Artifact Pack

The Real SAIR artifact pack is the reproducible evidence bundle for
multi-episode MathGraph compounding runs.  It does not change the thesis logic;
it packages the run so it can be inspected, archived, and compared over time.

## Required Inputs

Strict real mode expects:

- `/content/equations.txt`
- `/content/etp_matrix_full_best_bool.npy`

If those files are absent, the runner fails unless `--allow-fallback-smoke` is
passed.  Fallback packs are clearly marked and are not real SAIR evidence.

## Colab Command

```bash
python scripts/run_real_sair_artifact_pack.py \
  --equations-path /content/equations.txt \
  --matrix-path /content/etp_matrix_full_best_bool.npy \
  --output-dir /content/drive/MyDrive/SAIR_MathGraph/real_sair_multi_episode_pack \
  --num-episodes 3 \
  --episode-size 250 \
  --train-fraction 0.5 \
  --strict-admission \
  --create-archive
```

Fallback smoke:

```bash
python scripts/run_real_sair_artifact_pack.py \
  --output-dir /tmp/mathgraph_real_sair_artifact_pack_fallback_smoke \
  --num-episodes 3 \
  --episode-size 50 \
  --allow-fallback-smoke \
  --strict-admission \
  --create-archive
```

## Outputs

- `artifact_manifest.json`
- `real_sair_artifact_pack_summary.json`
- `real_sair_artifact_pack_report.md`
- `artifact_pack_result.json`
- `lawbook.sqlite`
- multi-episode CSV/JSON outputs
- per-episode benchmark and admission reports
- zip archive when enabled

## Interpretation

If `real_sair_used` is false, the pack is a fallback smoke artifact. It proves
packaging and boundary wiring only.

If `real_sair_used` is true but `compounding_signal_detected` is false, the run
did not yet prove compounding; inspect residuals, mode deltas, and durable reuse.

If both are true, the pack is initial evidence that durable verified memory
improved later verifier-directed episodes.

## Authority Boundary

Admission and promotion remain strict:

- fallback artifacts cannot enter durable memory
- failed finite searches do not imply TRUE
- advisory motifs and scheduler scores do not verify claims
- only verifier-backed terminal artifacts can become durable Lawbook memory

## Comparing Runs

Compare `artifact_manifest.json`, `multi_episode_cross_metrics.json`, and
`real_sair_artifact_pack_summary.json` across runs to track whether durable
reuse, residual shrinkage, and certificate yield per attempt improve over time.

