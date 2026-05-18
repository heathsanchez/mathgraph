# Release Process

## v0.1 Release Candidate Gate

```bash
python -m pytest
python scripts/run_release_check.py --quick
python scripts/run_public_demo.py --out-dir demo_out
python scripts/run_public_demo.py --allow-execution --allow-missing-verifier --accept-verified-entries-in-memory --out-dir demo_live_out
python scripts/run_colab_testdrive.py --use-current-checkout --quick-smoke
```

## Required Acceptance

- full suite passes
- release check passes
- public demo report generated
- no unsafe, expected-missing, or import-failure entry is verified
- known-skip appears only after accepted replay
- docs updated
- version, changelog, and release notes updated
- curated real Mathlib demo examples and docs exist; real Mathlib is not required for the release gate

Release-check success is a release signal, not proof.
