# MathGraph Proof-Repair / Verification Sprints

## Offer

MathGraph turns stuck formal/code claims into externally judged artifacts:

- verified Lean proofs
- removed `sorry` / `admit`
- repaired generated specs
- CI-green pull requests
- finite counterexamples
- benchmark-backed negative results
- named obstruction reports

The output is not advice. The output is proof, patch, counterexample, or obstruction, judged by your verifier.

## Best fit

Good:

- Lean 4 proof gaps
- failing proof obligations
- generated specs that almost compile
- small theorem repairs
- correctness invariants
- formal-methods repos with local CI
- benchmark tasks with clear acceptance criteria

Bad:

- vague “improve the agent” work
- no local verifier
- no reproducible failure
- prompt extraction / jailbreak tasks
- optimization work without a canonical metric

## Sprint format

You provide:

- repo
- issue
- failing file or theorem
- verifier command
- acceptance criterion

I return:

- patch or PR if repairable
- local verifier log
- short route trace
- obstruction report if not repairable

## Recent public traces

- `strata-org/specimen#46`: added `LawfulScorable` proof-carrying scorer-law interface; local `lake build` passes.
- `mo271/FormalBook#137`: Lean proof repair; CI green 2/2.
- `mo271/FormalBook#138`: Lean proof repair; CI green 2/2.
- `teorth/equational_theories#1461`: Law43 definability proof; CI green.
- `Beneficial-AI-Foundation/vericoding-benchmark#12`: generated-spec index-bound proof repairs.
- `tinygrad/tinygrad#3039`: certified negative result; correct Tensor-level scan was slower, so no bad PR was opened.
- `tenstorrent/tt-llk#1638`: metric requested before patching, to avoid blind optimization.

## Pricing

### Diagnostic sprint — USD $500

One repo, one issue, one verifier.

Output:

- setup/repro attempt
- obstruction map
- likely patch route
- go/no-go judgment

No guaranteed fix.

### Proof-repair sprint — USD $1,500

One small proof/code repair.

Output:

- patch or PR
- local verifier evidence
- short report

### Verification retainer — USD $3,000–$5,000/month

Ongoing queue of small proof/code repair tasks.

Output:

- weekly patches / PRs / obstruction reports
- Lawbook of verified fixes and failed routes

## One-line pitch

MathGraph turns stuck formal claims into verifier-judged artifacts: proof, counterexample, or named obstruction.
