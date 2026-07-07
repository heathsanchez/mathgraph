# qojulia #407 Patch Benchmark Workflow v14

## Verdict

`PATCHED_EXISTING_BENCHMARK_WORKFLOW`

## Why

The visible failing check was the existing full AirspeedVelocity benchmark job. It failed at `schroedinger / qo types / 20//1` with `MethodError: no method matching iterate(::QuantumOpticsBase.Ket...)`.

## Change

- Existing `Benchmarks / benchmark` now runs the smoke gate on PR/push.
- Full AirspeedVelocity benchmark remains available manually through `workflow_dispatch` with `full=true`.
- Removed duplicate separate `benchmark-smoke.yml` workflow.

## Local verifier

- smoke rc: `0`

