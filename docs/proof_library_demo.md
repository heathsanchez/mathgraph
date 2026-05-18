# Proof-Library Demo Pack

Run the repo-local synthetic demo:

```bash
python scripts/run_proof_library_demo.py --ensure-configs
python scripts/run_proof_library_demo.py --use-synthetic
python scripts/run_proof_library_demo.py --use-synthetic --run-allowlist-ingestion
python scripts/run_proof_library_demo.py --use-synthetic --run-allowlist-ingestion --allow-execution --allow-missing-verifier --accept-verified-entries-in-memory
```

Start from the optional real local template only after pointing it at an already-working local checkout:

```bash
python scripts/run_proof_library_demo.py --config examples/proof_library_demo/real_mathlib_demo_config.example.json --project-root /path/to/local/mathlib
```

The demo is read-only with respect to persistent Lawbook state. Discovery, generated manifests, dependency graphs, and reports are advisory; only explicit verifier/importer/finite-validator/chain-audit evidence promotes truth.

For the public-facing wrapper around this flow, use `scripts/run_public_demo.py`;
for release smoke checks, use `scripts/run_release_check.py`.
