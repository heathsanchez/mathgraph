# Real Local Mathlib Revision Demo

Use the template only with an already-working local checkout:

```bash
python scripts/run_proof_library_demo.py --config examples/proof_library_demo/real_mathlib_demo_config.example.json --project-root /path/to/mathlib
```

The revision workflow records local git/toolchain metadata, never downloads dependencies, and skips cleanly when the project is absent.

For the curated user-facing command, see `docs/curated_real_mathlib_demo.md` and `python scripts/run_real_mathlib_demo.py --ensure-examples`.
