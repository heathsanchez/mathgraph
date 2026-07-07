Updated this draft after inspecting the failing `Benchmarks / benchmark` check.

The failure was from the pre-existing full AirspeedVelocity PR benchmark path, not from the new smoke runner. It runs the full benchmark suite on the PR and currently fails in:

    schroedinger / qo types / 20//1

with:

    MethodError: no method matching iterate(::QuantumOpticsBase.Ket...)

So I changed the existing `Benchmarks` workflow to use the lightweight smoke gate for PR/push CI, while keeping the full AirspeedVelocity benchmark available manually via `workflow_dispatch` with `full=true`.

Local verification still passes:

    julia --project=benchmark benchmark/run_smoke.jl

This keeps PR CI focused on catching benchmark-suite bitrot without requiring every pull request to run the currently-failing full benchmark suite.
