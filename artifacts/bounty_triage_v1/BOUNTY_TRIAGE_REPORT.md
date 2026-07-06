# MathGraph Bounty Triage v1

Generated: 2026-07-06 23:28:58 UTC

## Executive ranking

### WORK_FIRST · score 110 · rank 2 · [Bounty $1000] Reduce RISCV instructions used to pass on tensix instructions using AI/Optimizer.

- Repo: `tenstorrent/tt-llk`
- Issue: https://github.com/tenstorrent/tt-llk/issues/1638
- Seed reason: Best optimization/search bounty fit: $1000 external objective
- Detected money/budget: `1000`
- Clone path: `/Users/heath/Documents/mathgraph-lean-work/external/bounty_triage_v1/tenstorrent__tt-llk`
- Labels: `P2, bounty, bounty_difficulty/medium, LLK`

Reasons:
- explicit bounty/paid/reward language
- detected payout/budget ≈ 1000
- acceptance/test/benchmark language
- repo has detectable local judge signals
- MathGraph-shaped technical terms

Risks:
- No major automatic red flags detected

Detected local judge signals:
- CI workflows available
- pytest/tests present

Suggested first commands:
- `python -m pytest`

Issue snippet:

```text
The number of tensix instructions to do a particular task can be easily optimized with human thinking, as the main task would have an algorithm and the proper instructions and sequence can often be easily chosen. But to pass on the tensix insturctions to the tensix engine, we often use MOPs and Replay buffers to pass them so that the number of RISCV instructions are rerduced. That part has too many ways of accomplishing and is not too easy to find out what is the most optimal way all the time. 

This is where we can use AI to reduce the number of RISV instructions used, by varying the possibilities of writing the MOP and arrangement of the replay buffer. Overall the task is 

Objective : Minimize the number of RISCV instructions to issue instructions to tensix engine 
Constraints : Sequence of tensix instructions passed remains the same
                       Only specified amount of replay buffer is used (for example if Math thread uses whole of the buffer, it may clash with SFPU algorithms when they are run from a separate thread on WH/BH for the buffer being shared. 
                        Take into account two ways of writing mops and their constraints. 

An AI agent may be asked to do it for all the ops we have and then we filter out the good suggestions and apply them.
```

### WORK_FIRST · score 98 · rank 5 · BGL PR bounty hunt ($10000 overall budget)

- Repo: `BitgesellOfficial/bitgesell`
- Issue: https://github.com/BitgesellOfficial/bitgesell/issues/39
- Seed reason: Broad PR bounty, maybe small test-fix opportunities, crowded
- Detected money/budget: `10000`
- Clone path: `/Users/heath/Documents/mathgraph-lean-work/external/bounty_triage_v1/BitgesellOfficial__bitgesell`
- Labels: ``

Reasons:
- explicit bounty/paid/reward language
- detected payout/budget ≈ 10000
- acceptance/test/benchmark language
- repo has detectable local judge signals
- MathGraph-shaped technical terms

Risks:
- crowded issue

Detected local judge signals:
- CI workflows available

Suggested first commands:
- Manual inspection needed

Issue snippet:

```text
To get more people involved and provide motivation, we are announcing Bitgesell Pull Request bounty hunt!

The rules are simple:

- You can create any reasonable pull request that may contain any modifications, including, but not limited to:
  - Refactoring and simplification;
  - Test fixes (1 test group/file fixed by single PR counts!);
  - Cleanup of features that are no longer used (e.g. non-segwit transactions);
  - Documentation and comments (but if no code changes then some reasonable amount of changes should be done to count);
  - Bug fixes;
- Every PR would be paid $500 in USDT upon approval, larger PRs could receive bigger payouts (PRs of lesser significance like comments editing or one-line changes could receive lesser payout).
- Interested people are welcome to become maintainers of the project;
```

### WORK_FIRST · score 82 · rank 3 · Bounty: Fast parallel scan (Mamba, etc). 

- Repo: `tinygrad/tinygrad`
- Issue: https://github.com/tinygrad/tinygrad/issues/3039
- Seed reason: Strong OSS credibility: $500 algorithm/performance bounty
- Detected money/budget: `500`
- Clone path: `/Users/heath/Documents/mathgraph-lean-work/external/bounty_triage_v1/tinygrad__tinygrad`
- Labels: `bounty`

Reasons:
- explicit bounty/paid/reward language
- detected payout/budget ≈ 500
- acceptance/test/benchmark language
- repo has detectable local judge signals

Risks:
- No major automatic red flags detected

Detected local judge signals:
- CI workflows available

Suggested first commands:
- Manual inspection needed

Issue snippet:

```text
It would be great to have a general parallel prefix sum (associative scan) operation in tinygrad, something like [associative_scan](https://jax.readthedocs.io/en/latest/_autosummary/jax.lax.associative_scan.html) in JAX or [scan_associative](https://www.tensorflow.org/probability/api_docs/python/tfp/math/scan_associative) in TensorFlow Probability. This operation is key for the parallelization of some algorithms in CRFs, [filtering/smoothing in state space models](https://github.com/EEA-sensors/sequential-parallelization-examples/blob/main/python/temporal-parallelization-bayes-smoothers/parallel_kalman_jax.ipynb), mamba etc.

Additional Reference

https://arxiv.org/abs/2311.06281
---

Current Bounty: $500
To lock the bounty submit a draft PR with a decent amount of progress made
Make sure to reference this issue in the PR for future tracking

Notice: If the PR goes stale the bounty will be unlocked
```

### WORK_FIRST · score 82 · rank 4 · [Bounty] Validate user creation payloads

- Repo: `xevrion-v2/agent-playground`
- Issue: https://github.com/xevrion-v2/agent-playground/issues/2207
- Seed reason: Easiest cash/test-driven API validation: $250
- Detected money/budget: `250`
- Clone path: `/Users/heath/Documents/mathgraph-lean-work/external/bounty_triage_v1/xevrion-v2__agent-playground`
- Labels: `good first issue, bounty, AI agent friendly`

Reasons:
- explicit bounty/paid/reward language
- detected payout/budget ≈ 250
- acceptance/test/benchmark language
- repo has detectable local judge signals

Risks:
- No major automatic red flags detected

Detected local judge signals:
- CI workflows available
- package.json script: lint
- package.json script: test

Suggested first commands:
- `npm run test`
- `npm run lint`

Issue snippet:

```text
POST /users currently trusts arbitrary request bodies. A client can send a custom id and extra fields, and the API returns them in the created user response. User creation should generate ids server-side, require a valid email, normalize optional names, and reject invalid JSON shapes.

Acceptance criteria:
- Reject non-object JSON bodies. In
- Require a valid email.
- Normalize email/name values.
- Ignore client-controlled id and unrelated fields.
- Add regression tests for these cases.

/bounty $250

References #33
```

### WORK_FIRST · score 81 · rank 1 · LawfulScorable: formally verify scorer invariants

- Repo: `strata-org/specimen`
- Issue: https://github.com/strata-org/specimen/issues/45
- Seed reason: Most MathGraph-native if real: formal verifier/invariants
- Clone path: `/Users/heath/Documents/mathgraph-lean-work/external/bounty_triage_v1/strata-org__specimen`
- Labels: ``

Reasons:
- explicit bounty/paid/reward language
- acceptance/test/benchmark language
- repo has detectable local judge signals
- MathGraph-shaped technical terms
- low comment competition

Risks:
- security/audit lane; higher reputation/legal risk

Detected local judge signals:
- CI workflows available
- Lean/Lake checker

Suggested first commands:
- `lake build`
- `lake env lean <target>.lean`

Issue snippet:

```text
## Plan

Define a `LawfulScorable` typeclass that bundles `Scorable` with its invariants as Lean lemmas, so custom scorers must prove correctness at compile time.

### Invariants to encode

1. **Monotonicity of `combine`**: `¬ isBetter (combine a b) a` — extending a partial schedule can never improve its score. Critical for branch-and-bound soundness.
2. **Transitivity of `isBetter`**: needed for bound propagation.
3. **`worst` is a valid initial bound**: no real score should be pruned by it.
4. **`empty` is identity for `combine`**.
5. **`badness` is monotone with `isBetter`**: `isBetter a b → badness a ≤ badness b` — the [0,1] mapping must preserve the score ordering so weight functions don't reward worse schedules.

### Steps

1. Define `class LawfulScorable (σ : Type) [Scorable σ]` with the above as Prop-valued fields.
2. Prove instances for `GradedUniformDensityScore`, `BoundedGradedScore`, `SourceQualityScore` (should be straightforward given `combine = max/sum`).
3. Add `[LawfulScorable σ]` constraint to `searchBestScheduleM` so ill-formed scorers are rejected at compile time.

```

## Recommended next move

Work only the first target with all four properties:

1. explicit real payout
2. local judge/test/benchmark
3. small enough first patch attempt
4. no prompt/secret/security weirdness

Do not chase highest nominal payout if the issue is proposal-shaped, security-shaped, or reputation-risky.

## Red-flag exclusions

ClankerNation/OpenAgents bounties were excluded despite high payout because their issue text asks for the full platform initialization/system prompt. Do not submit that.
