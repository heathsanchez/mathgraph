# strata-org/specimen PR #46 Watch v7

## Verdict

`NO_CI_YET__WAIT_FOR_REVIEW`

## PR

https://github.com/strata-org/specimen/pull/46

## Current state

- state: `OPEN`
- draft: `True`
- review decision: `REVIEW_REQUIRED`
- local verify: `True`
- check count: `0`
- failed checks: `0`
- pending checks: `0`

## Next action

Do nothing yet. The PR is public and locally verified; wait for maintainer review or CI.

## Decision JSON

JSON:
{
  "verdict": "NO_CI_YET__WAIT_FOR_REVIEW",
  "pr_url": "https://github.com/strata-org/specimen/pull/46",
  "isDraft": true,
  "state": "OPEN",
  "reviewDecision": "REVIEW_REQUIRED",
  "local_verify_ok": true,
  "check_count": 0,
  "failed_checks": [],
  "pending_checks": [],
  "passed_checks": [],
  "needs_instances": false,
  "needs_worst": false,
  "needs_changes": false,
  "approved": false,
  "pr_view_ok": true
}

## PR summary

JSON:
{
  "number": 46,
  "title": "Add LawfulScorable scorer laws interface",
  "state": "OPEN",
  "isDraft": true,
  "url": "https://github.com/strata-org/specimen/pull/46",
  "author": "heathsanchez",
  "baseRefName": "main",
  "headRefName": "mathgraph-lawful-scorable-issue45",
  "headRefOid": "c69bc02191c1480aa2f6487554af86616344f0f5",
  "headRepositoryOwner": "heathsanchez",
  "mergeable": "MERGEABLE",
  "reviewDecision": "REVIEW_REQUIRED",
  "updatedAt": "2026-07-07T00:31:47Z",
  "createdAt": "2026-07-07T00:31:47Z",
  "files": [
    {
      "path": "Specimen/Scoring.lean",
      "additions": 34,
      "deletions": 0
    }
  ],
  "commits": [
    {
      "oid": "c69bc02191c1480aa2f6487554af86616344f0f5",
      "messageHeadline": "Add LawfulScorable scorer laws interface"
    }
  ],
  "statusCheckRollup": [],
  "reviews": [],
  "comment_count": 0,
  "pr_view_ok": true
}

## Comments



## Reviews



## Checks / runs

completed	action_required	Add LawfulScorable scorer laws interface	CI	mathgraph-lawful-scorable-issue45	pull_request	28832900255	0s	2026-07-07T00:31:50Z



## Local verify

branch:
mathgraph-lawful-scorable-issue45

head:
c69bc02191c1480aa2f6487554af86616344f0f5

status:

lake env lean Specimen/Scoring.lean
scoring_rc=0

lake build
Build completed successfully (47 jobs).
build_rc=0


## v8 patch plan

# v8 Patch Plan if Review Requests More Substance

Current PR #46 only adds the proof-carrying `LawfulScorable` interface.

If maintainers ask for concrete instances, do not blindly prove all current laws. First split the laws by what is actually true.

Likely safe next steps:

1. Add weaker executable helper lemmas, not global instances, for the current score shapes.
2. Replace the too-strong global `worst` wording with a bounded version if maintainers care about `worst := 1000`.
3. Consider removing `badness_mono`: `badness : S → Float` is visual/UI-facing and proving Float monotonicity may be noisy and not central to branch-and-bound correctness.

Candidate bounded law shape:

    class BoundedWorstScorable (S : Type) [Scorable S] : Prop where
      withinBound : S -> Prop
      worst_loses_to_bounded :
        forall a : S, withinBound a -> Scorable.isBetter (S := S) a (Scorable.worst (S := S))

Most likely maintainer-good v8:

- keep `LawfulScorable` as interface
- remove or postpone `badness_mono`
- add comment explaining finite sentinels
- ask whether to model `worst` with `WithTop` or bounded law


