Hi, I’d like to claim this bounty if it is still available.

Name: Heath Sanchez
GitHub: @heathsanchez

Proposed scope/sequence:

1. First PR: repair the existing `benchmark/` suite enough that it has a reproducible local command and a lightweight GitHub Actions smoke gate suitable for pull requests.
2. Preserve/reuse the current `benchmark/benchmarks.jl` and `benchmark/Project.toml` where possible rather than replacing them.
3. Second step, if the first PR direction is accepted: repair/extend comparative benchmark support for QuTiP and QuantumToolbox.jl, then add a Makefile/documented command for regenerating the public comparative benchmark page.

Before I patch, I want to confirm the intended CI shape: should PR CI run a small benchmark smoke subset only, with full benchmarks reserved for manual/scheduled runs? That seems safest to avoid expensive/noisy PR jobs while still preventing benchmark-suite bitrot.

I’ll keep the first patch narrow and reviewable: benchmark project repair, smoke runner, CI wiring, and documentation for the local command.
