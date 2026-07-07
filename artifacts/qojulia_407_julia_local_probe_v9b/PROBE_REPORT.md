# qojulia #407 Julia Local Probe v9b

## Verdict

`PATCH_NEXT_SMOKE_RUNNER_AND_CI`

## Result

- benchmark project status: `pkg status rc=0`
- benchmark include/load: `include rc=0`
- one tiny benchmark: `tiny rc=0`

## Corrected interpretation

The existing benchmark suite loads and a tiny benchmark runs. v10 should add a narrow smoke runner, docs, and safe CI wiring.

## v10 patch route

1. Work on a branch in the external QuantumOptics checkout.
2. Patch only the narrow smoke path first.
3. Verify locally with Julia 1.10.
4. Open PR only if local smoke passes.

## Files

- `pkg_status.out` / `pkg_status.err`
- `probe_include.out` / `probe_include.err`
- `probe_tiny.out` / `probe_tiny.err`
- `workflow_and_docs_surface.txt`
- `decision.json`

