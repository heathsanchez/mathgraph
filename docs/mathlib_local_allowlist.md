# Real Local Mathlib Allowlist

The curated real-Mathlib demo builds on this membrane through `scripts/run_real_mathlib_demo.py`; local paths and generated manifests remain advisory until verifier evidence exists.

```bash
python scripts/run_mathlib_local_allowlist.py --ensure-examples
python scripts/run_mathlib_local_allowlist.py --use-synthetic-external
python scripts/run_mathlib_local_allowlist.py --use-synthetic-external --allow-execution --allow-missing-verifier
python scripts/run_mathlib_local_allowlist.py --manifest PATH --project-root PATH --allow-execution --allow-missing-verifier
```

This local-path-only pilot performs no downloads and no package-manager operations. Empty allowlists, environment checks, extracted declarations, imports, and dependency graphs remain advisory until explicit verifier evidence exists.

## Discovery Handoff

```bash
python scripts/run_mathlib_declaration_discovery.py --ensure-examples
python scripts/run_mathlib_declaration_discovery.py --use-synthetic-request --build-manifest
python scripts/run_mathlib_declaration_discovery.py --use-synthetic-request --build-manifest --run-allowlist-ingestion --allow-execution --allow-missing-verifier
```

## Demo Pack

```bash
python scripts/run_proof_library_demo.py --ensure-configs
python scripts/run_proof_library_demo.py --use-synthetic
python scripts/run_proof_library_demo.py --config examples/proof_library_demo/real_mathlib_demo_config.example.json --project-root /path/to/local/mathlib
```

For a revision-oriented local Mathlib workflow, see
`docs/real_mathlib_revision_demo.md`.

For real modules whose declarations depend on imported Mathlib context, use
`docs/mathlib_module_verification.md`; it is the preferred selected-declaration
availability check and does not claim source-proof replay.
