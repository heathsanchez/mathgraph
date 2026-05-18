# Mathlib Declaration Discovery

```bash
python scripts/run_mathlib_declaration_discovery.py --ensure-examples
python scripts/run_mathlib_declaration_discovery.py --use-synthetic-request --build-manifest
python scripts/run_mathlib_declaration_discovery.py --use-synthetic-request --build-manifest --run-allowlist-ingestion --allow-execution --allow-missing-verifier
```

Discovery only inspects explicitly selected local files. It emits advisory declarations, reference hints, and generated allowlist manifests; verifier evidence can appear only after the optional downstream allowlist-ingestion step.
