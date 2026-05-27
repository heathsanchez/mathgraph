# Seeking Lean / Formal-Methods Collaborators: MathGraph Verification Memory Layer

MathGraph is a generative verification kernel for trustworthy mathematical
discovery and verified AI reasoning. It routes generated claims toward explicit
verifier, finite-checker, trusted-importer, or chain-audit boundaries, while
keeping advisory memory separate from terminal truth.

## Current Evidence Milestone

MathGraph has produced an official SAIR Stage 2 evidence pack: a real-data
FALSE-side run with 36 finite-checked countermodels, +8.0 held-out gain over
baseline, harmful-route rejection, and zero trust-boundary violations.

This is a bounded FALSE-side result. TRUE-side Lean proof verification remains
an open engineering and research frontier.

## What Is Needed Next

- TRUE-side Lean proof verification
- finite countermodel certificate format review
- Lean Project Digest
- EvidenceManifest review
- replay/audit hardening
- API review

## What Collaborators Can Run

```bash
python scripts/replay_official_sair_stage2_breakthrough.py \
  --equations /content/equations.txt \
  --matrix /content/etp_matrix_full_best_bool.npy \
  --out-dir /content/drive/MyDrive/SAIR_MathGraph/official_sair_stage2_breakthrough_replay \
  --full
```

## Caveat

The current milestone is a bounded FALSE-side finite-countermodel and
verified-memory-compounding result. TRUE-side Lean proof generation is not
claimed and remains the next frontier.
