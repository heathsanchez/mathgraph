# Mathlib Module-Aware Verification

MathGraph can generate temporary Lean files that import an explicitly selected
module and `#check` explicitly selected declaration names inside the local
project environment.

`#check` is useful for real Mathlib because declarations rely on module imports,
namespaces, notation, and the compiled local environment. It verifies imported
declaration availability; it does not mean MathGraph independently reconstructed
the source proof.

```bash
python scripts/run_mathlib_module_verification.py --ensure-examples
python scripts/run_mathlib_module_verification.py --use-synthetic-request --project-root examples/mathlib_micro_subset
python scripts/run_mathlib_module_verification.py --use-synthetic-request --project-root examples/mathlib_micro_subset --allow-execution --allow-missing-verifier --accept-verified-entries-in-memory
python scripts/run_real_mathlib_demo.py --project-root /path/to/mathlib4 --run-module-verification --execution-mode lake-env-lean --allow-execution --allow-missing-verifier
```

The local project must already exist and be usable. MathGraph does not clone,
download, update, or cache Mathlib for this workflow. Missing Lean or a missing
project skips cleanly when allowed.

Only allowlisted declarations with explicit verifier-bound evidence may cross
the truth boundary. Discovery, generated manifests, generated check files,
`#check` source text, graphs, reports, stdout, return code, and dry-runs remain
advisory.

Real Mathlib discovery can surface names that still need qualification repair in
the imported environment. Failed checks write `failed_check_diagnostics.json`
with generated check text, Lean output tails, unresolved names, and candidate
spellings. `--enable-name-candidate-fallback` performs an optional second
verifier pass; fallback creates evidence only for a resolved candidate that Lean
actually accepts.

For real Mathlib/Lake projects, use `lake env lean` from the project root:

```bash
python scripts/run_mathlib_module_verification.py --request /path/to/request.json --project-root /path/to/mathlib4 --execution-mode lake-env-lean --allow-execution --allow-missing-verifier
```

In `auto` mode MathGraph selects `lake env lean` when Lake and project markers
are available. Raw Lean mode is mainly for simple or synthetic projects. If
diagnostics mention object files under `/tmp/.../olean/Mathlib`, the check was
using the wrong import context; rerun with `--execution-mode lake-env-lean` from
the real project root. MathGraph will never run `lake update` or `lake exe cache
get`; if a cache is missing, run that manually outside MathGraph.
