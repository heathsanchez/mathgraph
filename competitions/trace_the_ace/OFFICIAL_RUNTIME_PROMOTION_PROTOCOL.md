# Trace the Ace — Official Runtime Promotion Protocol

Primary objective: lowest expected unseen/private log loss. Public leaderboard movement is not a promotion criterion by itself.

## Scope

Apply this protocol to the winning V71–V77 candidate after frozen OOF evaluation. Do not alter model logic while translating it into runtime form. Any material model change creates a new candidate and must return to OOF evaluation.

## Gate 0 — Freeze the candidate

Record in a machine-readable manifest:

- source Git commit SHA;
- candidate/arm name;
- all hyperparameters;
- frozen fold-definition version/hash;
- overall and per-fold session-cold log loss;
- objective-cold, semantic-family-cold, rare-objective, worst-fold and calibration metrics;
- hashes of all fitted assets;
- expected prediction implementation/version.

No leaderboard-derived calibration or smoke-test tuning is permitted in this frozen candidate.

## Gate 1 — `submission_src` contract

Develop the submission in the official runtime repository's `submission_src/` directory. The packed archive must contain `main.py` at ZIP root.

Recommended source layout:

```text
submission_src/
├── main.py
├── assets/
│   ├── manifest.json
│   ├── objective_model.*
│   ├── objective_statistics.*
│   ├── vectorizer.*
│   ├── residual_model.*
│   └── calibration.*
└── trace_ace/
    ├── canonicalize.py
    ├── mastery.py
    ├── features.py
    └── predict.py
```

`main.py` must:

1. read `/code_execution/data/test_features.csv`;
2. read required transcript CSVs from `/code_execution/data/test_transcripts/`;
3. construct exactly the frozen representation;
4. load frozen fitted assets only;
5. generate one probability per response independently of unrelated test cases;
6. apply only frozen calibration;
7. use `/code_execution/data/submission_format.csv` as the output contract;
8. write `/code_execution/submission.csv` with exactly `response_id,probability`.

Forbidden during inference:

- fitting/updating model weights or fitted feature parameters from test data;
- pseudo-labeling;
- corpus-wide test statistics used as features;
- network calls;
- package installation;
- manual test annotations;
- cross-test-case information that changes a sample prediction.

## Gate 2 — Research/runtime parity

Create a frozen held-out fixture and run both the research implementation and `submission_src` implementation.

For deterministic components require:

```text
max_abs_probability_difference < 1e-8
```

If a GPU component makes bitwise equality impossible, predeclare a justified tolerance and require no meaningful log-loss change.

Also require the runtime implementation's held-out log loss to reproduce the frozen candidate within numerical tolerance. Failure means STOP: fix translation, do not submit.

## Gate 3 — Official container

Use the official `drivendataorg/tutoring-outcomes-runtime` repository and run, in order:

```bash
just pull
just pack-submission
just check-submission
just test-submission
```

All commands must exit successfully. Preserve `submission/log.txt` and the generated `submission/submission.csv` as validation evidence.

## Gate 4 — Competition-shaped held-out test

Create a local, non-Git-tracked data directory from held-out training sessions:

```text
data/
├── submission_format.csv
├── test_features.csv
└── test_transcripts/
    └── <session_id>.csv
```

Run:

```bash
DATA_DIR=/absolute/path/to/data just test-submission
```

Require prediction parity with the frozen held-out research implementation and expected held-out log loss.

Competition data must not be committed to the public repository.

## Gate 5 — Offline/cold-container audit

Run with the official default network isolation. Do not enable internet access.

Audit logs for:

- attempted downloads;
- Hugging Face Hub/network calls;
- package installation attempts;
- missing assets;
- hidden filesystem assumptions;
- warnings that alter model behavior.

Require successful cold-container inference with all required assets either packaged or officially preloaded.

## Gate 6 — Output integrity

Programmatically require:

```text
columns == ["response_id", "probability"]
row_count == submission_format row_count
response_ids exactly match submission_format
no duplicate response_ids
no NaN
no +/-inf
0 <= probability <= 1
```

Also inspect probability min/max and extreme-confidence counts. Unexpected tails are an investigation trigger because the competition metric is log loss.

## Gate 7 — Sample-independence metamorphic audit

Choose held-out response `x`. Predict it under:

- A: `x` alone;
- B: `x` plus unrelated held-out responses;
- C: same batch reordered;
- D: `x` plus a different unrelated batch.

Require:

```text
p_A(x) == p_B(x) == p_C(x) == p_D(x)
```

within the predeclared numerical tolerance.

This is a hard rule-compliance gate.

## Gate 8 — Runtime/resource budget

Record elapsed wall time, peak RAM, peak GPU VRAM if applicable, archive size and output size.

Hard competition constraints are six hours for full inference and 20 minutes for smoke. Internal promotion target:

```text
projected full-test runtime < 4 hours
```

Prefer substantially more headroom. Any candidate close to a hard resource limit is not promoted without a documented reason.

## Gate 9 — Platform smoke test

Only after Gates 0–8 pass, upload the exact packed archive as a smoke test.

Use smoke only for runtime validation:

- process starts;
- assets resolve;
- platform paths are correct;
- output is produced;
- runtime is comfortably under 20 minutes;
- logs comply with competition restrictions.

Do not tune model/calibration from smoke score.

## Gate 10 — Full-submission promotion

A candidate may consume one of the limited full submissions only if ALL conditions hold:

1. session-cold OOF log loss improves on the current frozen champion;
2. no unacceptable objective-cold regression;
3. no unacceptable semantic-family-cold regression;
4. rare-objective behavior is acceptable;
5. worst-fold risk is acceptable;
6. calibration is sound;
7. runtime implementation reproduces frozen predictions;
8. official offline container passes;
9. sample-independence audit passes;
10. platform smoke test passes;
11. projected full runtime has safe headroom;
12. expected private log loss is competitive with the winning target, not merely an incremental public-board improvement.

Current strategic target: do not spend a full submission on a candidate unless robust evidence makes private log loss around or below 0.595 plausible, unless a later evidence-based threshold supersedes this one.

## State machine

```text
OOF WIN
  -> FREEZE
  -> RUNTIME PARITY
  -> OFFICIAL CONTAINER
  -> HELD-OUT CONTAINER
  -> OFFLINE AUDIT
  -> OUTPUT INTEGRITY
  -> SAMPLE INDEPENDENCE
  -> RESOURCE GATE
  -> SMOKE
  -> FULL SUBMIT
```

Any failed gate returns the candidate to the appropriate earlier stage. Never bypass a failed gate because of a favorable public leaderboard score.
