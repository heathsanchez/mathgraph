# Curated Real Mathlib Demo

This workflow is local-path-only for an already-working Mathlib or Lean/Mathlib checkout. It does not download Mathlib, run package-manager commands, or broad-scan a library.

```bash
python scripts/run_real_mathlib_demo.py --ensure-examples
python scripts/run_real_mathlib_demo.py
python scripts/run_real_mathlib_demo.py --config examples/real_mathlib_demo/curated_real_mathlib_demo_config.example.json --project-root /path/to/local/mathlib
python scripts/run_real_mathlib_demo.py --config examples/real_mathlib_demo/curated_real_mathlib_demo_config.example.json --project-root /path/to/local/mathlib --run-allowlist-ingestion --allow-execution --allow-missing-verifier
```

It diagnoses project markers, Lean, Lake when present, revision, toolchain, and selected module files; discovers declarations only from explicit module files; generates an advisory manifest; and optionally hands that manifest to the existing verifier-bound ingestion path.

Choose one or two stable modules, keep limits small, and use `selected_declaration_names` for exact curation. A missing project path is a clean skip, not a failure.

A local Mathlib checkout is candidate structured memory. Discovery, revisions, toolchains, generated manifests, dependency graphs, reports, stdout, and return codes are advisory. Only allowlisted declarations with explicit verifier boundary evidence become proof evidence.
