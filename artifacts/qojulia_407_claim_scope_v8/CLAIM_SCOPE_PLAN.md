# qojulia #407 Claim + Scope v8

## Verdict

`CLAIM_BEFORE_PATCH`

## Why

- Bounty is explicit and unclaimed in the issue packet.
- Existing benchmark infra already exists, so this is a repair/modernization bounty.
- No local Julia runtime is installed, so a patch without scope confirmation is risky.
- Issue logistics explicitly encourage a claim comment.

## Proposed route

1. Claim/scope the bounty.
2. v9: install or locate Julia only if scope is confirmed.
3. v10: patch a small benchmark smoke command + CI job.
4. v11: comparative QuTiP/QuantumToolbox + Makefile/page command.

## Claim comment

Hi, I’d like to claim this bounty if it is still available.

Name: Heath Sanchez
GitHub: @heathsanchez

Proposed scope/sequence:

1. First PR: repair the existing `benchmark/` suite enough that it has a reproducible local command and a lightweight GitHub Actions smoke gate suitable for pull requests.
2. Preserve/reuse the current `benchmark/benchmarks.jl` and `benchmark/Project.toml` where possible rather than replacing them.
3. Second step, if the first PR direction is accepted: repair/extend comparative benchmark support for QuTiP and QuantumToolbox.jl, then add a Makefile/documented command for regenerating the public comparative benchmark page.

Before I patch, I want to confirm the intended CI shape: should PR CI run a small benchmark smoke subset only, with full benchmarks reserved for manual/scheduled runs? That seems safest to avoid expensive/noisy PR jobs while still preventing benchmark-suite bitrot.

I’ll keep the first patch narrow and reviewable: benchmark project repair, smoke runner, CI wiring, and documentation for the local command.

