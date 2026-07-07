# qojulia #407 Smoke Runner Patch v10b

## Verdict

`READY_TO_PUSH_DRAFT_PR`

## Local verifier

- `julia --project=benchmark benchmark/run_smoke.jl`: rc `0`

## Patch

- Adds `benchmark/run_smoke.jl` as a lightweight benchmark-suite bitrot gate.
- Adds `.github/workflows/benchmark-smoke.yml` on normal `pull_request`, `push`, and `workflow_dispatch`.
- Documents the smoke command in `README.md`.

## Why v10b exists

The v10 external patch was valid and committed, but the MathGraph artifact report was corrupted by shell expansion inside an unquoted Python heredoc. v10b regenerates the report with a quoted-safe Python call and re-verifies the local smoke gate.

## PR rule

Open a draft PR only by rerunning with:

`OPEN_QOJULIA_PR=1 bash qojulia_407_smoke_runner_patch_v10b.sh`

