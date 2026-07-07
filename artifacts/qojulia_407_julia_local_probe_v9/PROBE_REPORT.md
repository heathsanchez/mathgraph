# qojulia #407 Julia Local Probe v9

## Verdict

`PATCH_NEXT_BENCHMARK_PROJECT_LOAD_REPAIR`

## Result

- benchmark include/load: `include rc=127`
- one tiny benchmark: `tiny rc=999`
- claim posted: https://github.com/qojulia/QuantumOptics.jl/issues/407#issuecomment-4900216240

## Interpretation

The benchmark project or benchmark file does not load. v10 should first repair imports/dependencies/API drift before touching CI.

## v10 patch shape

1. Add `benchmark/run_smoke.jl` or equivalent narrow runner.
2. Make the runner select a tiny subset and fail if the suite cannot load/run.
3. Add a documented local command.
4. Add or adjust GitHub Actions so PRs run only the smoke gate; full benchmark remains manual/scheduled.
5. Do not implement QuTiP/QuantumToolbox comparative benchmark yet unless maintainer confirms that should be first.

## Files

- `probe_include.out` / `probe_include.err`
- `probe_tiny.out` / `probe_tiny.err`
- `workflow_and_docs_surface.txt`
- `decision.json`

