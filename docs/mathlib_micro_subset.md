# Mathlib Micro-Subset Pilot

```bash
python scripts/run_mathlib_micro_subset.py --ensure-synthetic-subset
python scripts/run_mathlib_micro_subset.py --allow-execution --allow-missing-verifier
python scripts/run_mathlib_micro_subset.py --manifest PATH --project-root PATH --allow-execution --allow-missing-verifier
```

The built-in subset is synthetic and local. External mode reads only an
already-existing local path; it does not download Mathlib, run package-manager
operations, or treat environment readiness as proof.
