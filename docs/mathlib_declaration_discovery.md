# Mathlib Declaration Discovery

The curated real-Mathlib demo command composes this advisory discovery layer with explicit config and optional downstream verifier-bound ingestion; discovery remains advisory.

```bash
python scripts/run_mathlib_declaration_discovery.py --ensure-examples
python scripts/run_mathlib_declaration_discovery.py --use-synthetic-request --build-manifest
python scripts/run_mathlib_declaration_discovery.py --use-synthetic-request --build-manifest --run-allowlist-ingestion --allow-execution --allow-missing-verifier
```

Discovery only inspects explicitly selected local files. It emits advisory declarations, reference hints, and generated allowlist manifests; verifier evidence can appear only after the optional downstream allowlist-ingestion step.

For a polished repeatable walkthrough, use the proof-library demo pack:

```bash
python scripts/run_proof_library_demo.py --use-synthetic
python scripts/run_proof_library_demo.py --use-synthetic --run-allowlist-ingestion --allow-execution --allow-missing-verifier --accept-verified-entries-in-memory
```

For the public wrapper that packages this flow with release checks and
reproducible artifacts, use `python scripts/run_public_demo.py`.
