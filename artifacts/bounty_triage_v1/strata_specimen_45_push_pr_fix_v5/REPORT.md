# strata-org/specimen #45 PR Push Fix v5

## Verdict

`DRAFT_PR_OPENED_OR_REUSED`

## PR

https://github.com/strata-org/specimen/pull/46

## Fork/branch

- fork: `heathsanchez/specimen`
- branch: `mathgraph-lawful-scorable-issue45`

## Local verifier

- `Specimen/Scoring.lean`: `True`
- `lake build`: `True`

## Meaning

The earlier v4 attempt produced a valid local Lean patch but failed because the fork remote did not exist. v5 force-created/polled the fork, pushed the branch, and created/reused the draft PR.

## PR body

```text
Draft progress for #45.

This PR adds a proof-carrying `LawfulScorable` interface next to the existing executable `Scorable` typeclass.

What is included:

- `combine` should not strictly improve the left score
- `isBetter` should be transitive
- `empty` should be a left and right identity for `combine`
- `worst` should not beat a real candidate
- `badness` should be monotone with `isBetter`

Local verification:

- `lake env lean Specimen/Scoring.lean` passes
- `lake build` passes

I kept this as a separate law class rather than modifying `Scorable`, so existing scoring strategies remain executable/lightweight and proof-carrying code can request the stronger interface explicitly.

Important design note: the issue text says `worst` must be worse than any real schedule. The current instances use finite sentinels such as `1000`, so a strong global law like “every score beats worst” may not hold for unbounded scores. This draft therefore uses the safer law “worst does not beat a candidate” while leaving open whether the final fix should use bounded laws or a true top sentinel.

Next step after feedback: add `LawfulScorable` instances or refine the `worst` law to match the intended branch-and-bound invariant.

Refs #45.

```

## Push output

```text
branch 'mathgraph-lawful-scorable-issue45' set up to track 'fork/mathgraph-lawful-scorable-issue45'.

remote: 
remote: Create a pull request for 'mathgraph-lawful-scorable-issue45' on GitHub by visiting:        
remote:      https://github.com/heathsanchez/specimen/pull/new/mathgraph-lawful-scorable-issue45        
remote: 
To https://github.com/heathsanchez/specimen.git
 * [new branch]      mathgraph-lawful-scorable-issue45 -> mathgraph-lawful-scorable-issue45

```

## Verify log

```text
lake env lean Specimen/Scoring.lean
scoring_rc=0

lake build
Build completed successfully (47 jobs).
build_rc=0

```

