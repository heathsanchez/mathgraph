## Summary

Adds a lightweight benchmark smoke gate for the existing `benchmark/` suite.

This is intentionally narrow for the first step of #407:

- instantiate the benchmark project
- load `benchmark/benchmarks.jl`
- run one tiny benchmark path
- fail CI if the benchmark suite no longer loads or cannot run a minimal benchmark

## Local verification

    julia --project=benchmark benchmark/run_smoke.jl

The smoke runner prints `BENCHMARK_SMOKE_OK` on success.

## Scope

This PR does not attempt the full comparative benchmark report against QuTiP / QuantumToolbox.jl yet. It is meant to establish the small PR-safe CI gate first, so the benchmark suite stops silently bitrotting.
