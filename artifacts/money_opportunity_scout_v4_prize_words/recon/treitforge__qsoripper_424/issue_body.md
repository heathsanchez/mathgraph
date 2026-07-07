## Summary

Ingest the [Kaggle Morse Learning Machine Challenge v2](https://www.kaggle.com/competitions/morse-learning-machine-challenge-v2) dataset as a **third external benchmark** alongside `training-set-a` (real OTA) and the adversarial synthetic suite (PR #417). Use it to (a) get a defensible external metric for our decoder, (b) cross-validate the `augment-arrl` (PR TBD) augmentation distributions, and (c) stress-test wider WPM range than our current suites cover.

## Dataset facts

- 200 WAV files, mono, 32-bit float, 8 kHz
- ~100 labeled (training, in `SampleSubmission.csv`); ~100 unlabeled (validation, scored via submission)
- Per-file randomization:
  - SNR: -14 to +20 dB
  - Pitch: 600 - 1200 Hz
  - Speed: 12 - 80 WPM
- Filename convention: `cw001.wav` ... `cw200.wav`
- Scoring metric: Levenshtein distance (== our CER, conveniently)

Reference baseline solution: https://github.com/talengu/kaggle_morse

## Why it matters

1. **External metric.** We have been grading our own homework on a 6-sample real OTA bench (training-set-a). The Kaggle leaderboard gives us a public, third-party number — useful for sanity checking and as a defensible "v1 done" signal.
2. **Augmentation distribution validation.** The competition's `(SNR ∈ [-14,+20], WPM ∈ [12,80], pitch ∈ [600,1200])` is exactly what `augment-arrl` is synthesizing. If our augmented corpus does not bracket the Kaggle distribution, our augmenter is mis-tuned. Cheap to check via histogram overlay.
3. **WPM stress test.** Our current bench tops out at 40 WPM. The Kaggle 50-80 WPM tail is something we never exercise. The two-pass WPM seed (PR #423) needs to be re-validated at high WPM since the bias-correction constants were tuned at 13-40 WPM.
4. **Independent overfitting check.** If we only optimize for training-set-a + adversarial-suite, we will silently overfit those distributions. Kaggle is held-out by construction.

## What this is NOT

- Not a training corpus. ~100 labeled files is too small for neural training. Our augmented ARRL corpus (~535 h, ~47k variants from `augment-arrl`) dwarfs it by 3+ orders of magnitude.
- Not "real world" — synthetic CW + AWGN, no Watterson channel, no QRM, no human fist variability. Beating Kaggle is necessary but not sufficient for OTA performance.
- Competition is closed (no prize), but the leaderboard still accepts submissions for scoring.

## Acceptance criteria

1. **Ingest pipeline**:
   - Script to download dataset (Kaggle CLI auth required) under `data/cw-samples/kaggle-morse-v2/` (gitignored).
   - Manifest at `experiments/cw-decoder/scripts/kaggle_morse_v2/manifest.jsonl` mapping file -> truth (where labeled).
   - Reuse the existing `bench.py` harness; emit per-file CER + aggregate stats.

2. **Baseline run**: Score current best (viterbi from PR #411 + wpm-seed-fix from PR #423) on the 100 labeled training samples. Report mean / median / p95 CER, broken down by SNR bucket and WPM bucket.

3. **Submission**: Generate a submission CSV from the 100 unlabeled validation samples and submit to the leaderboard. Capture the leaderboard score in the report.

4. **Distribution cross-validation** (depends on `augment-arrl` landing): overlay our augmented corpus distributions against Kaggle's per-file (SNR, WPM, pitch) statistics. Flag any mismatch.

5. **Regression check**: confirm the PR #423 wpm-seed-fix gate behaves correctly at high WPM (50-80). Specifically check:
   - Is the histogram bias correction (`frame_len + frame_step` ≈ 35 ms) still appropriate at 80 WPM dit length (~15 ms)?
   - Does the dit/dah concentration gate fire correctly when both clusters are sub-30 ms?

6. **Honest report** with:
   - Per-SNR-bucket CER table
   - Per-WPM-bucket CER table
   - Failure-mode analysis on the worst 10 files (paste decoded vs truth)
   - Comparison: our score vs published `talengu/kaggle_morse` baseline (CNN+LSTM, ~2018-era)
   - Recommendation: any concrete decoder changes needed to reduce the high-WPM or low-SNR error rate

## Sequencing

This depends on:
- PR #411 (viterbi) and PR #423 (wpm-seed-fix) merged so we have a stable best-of-bake-off baseline to evaluate
- `augment-arrl` (PR TBD) for the distribution cross-validation step

Can begin ingest + baseline run as soon as #411 and #423 land. Distribution check waits on `augment-arrl`.

## Risks

- **Kaggle ToS**: dataset license must be checked before redistributing or training models from it. Likely "competition use only" — that's fine for in-repo benchmarking, but flag for the LLM-repair experiment (#422) which would consume training pairs.
- **Kaggle CLI auth**: requires per-developer Kaggle API token. Document setup in the script.
- **Dataset is synthetic**: do not over-weight Kaggle results — they validate decoder robustness across SNR/WPM but tell us nothing about Watterson channel, QRM, or fist variation.

## Open design questions

1. Submit to the leaderboard? It's public and our score becomes visible. Probably yes — gives us a citation-grade external number.
2. Use the 100 labeled files as additional regression bench, or hold them out for distribution validation only?
3. The published `talengu/kaggle_morse` baseline uses CNN+LSTM. Worth mining for ideas / weights / architecture before our `augment-arrl` + neural work?