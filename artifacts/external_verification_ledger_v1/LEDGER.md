# MathGraph External Verification Ledger v1

## Current doctrine

The active bottleneck is no longer local generation. It is external acceptance.

MathGraph has produced multiple public proof/code-repair artifacts across independent repositories. The correct next behavior is to wait for external verifier feedback, not flood maintainers with more patches.

## Active public PRs

| Repo | PR | Status | External signal | Action |
|---|---:|---|---|---|
| strata-org/specimen | #46 | Draft, open | local `lake build` passes; GitHub CI action_required | wait for maintainer/CI approval |
| Beneficial-AI-Foundation/vericoding-benchmark | #12 | Open | mergeable, no comments yet | wait |
| mo271/FormalBook | #137 | Open | CI green 2/2 | wait for approval |
| mo271/FormalBook | #138 | Open | CI green 2/2 | wait for approval |
| digama0/lean4lean | #14 | Open | no checks visible | wait |
| digama0/lean4lean | #15 | Open | no checks visible | wait |
| teorth/equational_theories | #1461 | Open | CI green 1/1 | wait for approval |

## Parked bounty routes

| Route | Status | Reason |
|---|---|---|
| tenstorrent/tt-llk #1638 | parked | maintainer metric requested; no reply yet |
| tinygrad/tinygrad #3039 | certified negative | Tensor-level Hillis-Steele scan correct but slower |
| xevrion-v2/agent-playground #2207 | parked | no real implementation/test surface |
| Clanker OpenAgents issues | rejected | prompt/system exfiltration risk |

## Lawbook entries

### Strata/specimen #46

Residual: scorer laws implicit in executable `Scorable`.

Portal: introduce proof-carrying `LawfulScorable`.

Certificate: local Lean check and full `lake build` pass.

Boundary: PR is public but draft; CI requires maintainer action.

### tinygrad #3039

Residual: fast associative scan.

Portal tried: Tensor-level Hillis-Steele shifted-add scan.

Certificate: correctness against `Tensor.cumsum`.

Obstruction: slower than builtin by up to about 4x in local benchmark.

### Tenstorrent #1638

Residual: reduce RISC-V instruction count for Tensix/MOP path.

Portal found: matmul MOP/no-MOP performance surface.

Boundary: canonical scoring command/counter unknown; maintainer asked.

## Rule

Do not open another PR until one of these happens:

1. A maintainer asks for changes.
2. CI fails with actionable logs.
3. Tenstorrent replies with a scoring command.
4. A parked route gets a concrete verifier.
5. A new target has a real local judge and better expected value than maintaining the current queue.
