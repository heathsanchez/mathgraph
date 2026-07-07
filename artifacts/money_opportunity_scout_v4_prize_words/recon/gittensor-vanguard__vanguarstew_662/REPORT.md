# Prize Recon Report

## Verdict

`PARK_RISK`

## Decision

JSON:
{
  "verdict": "PARK_RISK",
  "issue": {
    "url": "https://github.com/gittensor-vanguard/vanguarstew/issues/662",
    "title": "Add judge tally integrity gate for replay win/loss accounting",
    "state": "OPEN",
    "labels": [
      "enhancement",
      "benchmark",
      "tests"
    ],
    "comment_count": 1,
    "updatedAt": "2026-07-06T18:27:23Z"
  },
  "money": true,
  "competition": true,
  "judge": true,
  "local": true,
  "mgfit": true,
  "risk": true
}

## Cheap commands

pwd=/Users/heath/Documents/mathgraph-lean-work/external/money_opportunity_scout_v4_prize_words/gittensor-vanguard__vanguarstew_662

README head:
# vanguarstew — SN74 repo-maintainer agent

[![CI](https://github.com/gittensor-vanguard/vanguarstew/actions/workflows/ci.yml/badge.svg)](https://github.com/gittensor-vanguard/vanguarstew/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Powered by Gittensor](https://img.shields.io/badge/Powered%20by-Gittensor-6E56CF)](https://gittensor.io)

> **⚡ Powered by [Gittensor](https://gittensor.io).** This repository is built and continuously
> improved through **Gittensor** — a [Bittensor](https://bittensor.com) subnet (**SN74**) that rewards a
> network of contributors for making real, merged improvements to open-source software. The reviews,
> fixes, and features that land here are produced and incentivized through Gittensor. **Want to help
> build it (and earn)?** See [how Gittensor OSS contributions work](https://docs.gittensor.io/oss-contributions.html).

`vanguarstew` is an **SN74 repo-maintainer agent** and the **benchmark** that optimizes it, built to live as a repo on gittensor. It borrows the agentic-workflow + history-derived-benchmark approach of SN66 "ninja" (the coding-agent subnet) and retargets it from *"reproduce the code change"* to *"make the maintainer decisions a strong maintainer would have made."*

The core question it answers is not *"did the agent write good code?"* but *"does the agent understand where this repository is going, and would it have steered it the way the real maintainers did?"*

See [ROADMAP.md](ROADMAP.md) for milestones and [docs/architecture.md](docs/architecture.md) for the architecture (module layout, agent contract, topology, leakage defenses).

## Why this matters

Software development is bottlenecked less by writing code than by **maintaining** it —
triaging, reviewing, prioritizing, and steering a codebase over time. That maintainer
capacity is the real ceiling on how much useful software actually ships.

vanguarstew turns that bottleneck into a measurable optimization problem: *can an agent make
the maintainer decisions a strong human maintainer would have made?* By scoring against real
GitHub history, it builds a benchmark for maintainer capability — and a path to scaling it.

## Demo

![vanguarstew replay demo](docs/vanguarstew-demo.gif)

A **live** replay against a real model (frozen at a past commit, agent sees only history up
to there). It infers the repo's maintainer philosophy and plans the next actions — its top
call (quick-router fixes) and its read of the direction (toward v1.0) match what the
maintainers actually did next. Scored on trajectory + decision process; the pairwise judge
picks the agent over an empty baseline.

## How it works

```
freeze a repo @ time T  ──>  agent infers the repo's "maintainer philosophy",
                             then plans the next N maintainer actions / PRs
                                      │
reveal the actual history T→T+N  ──>  pairwise judge: whose plan is more
                                      consistent with where the repo actually went?
```

The agent is judged on **direction/theme match** (not exact-PR match), with an **objective anchor** (concrete decisions that have a hard ground truth — merge/reject, labels, reviewer, version bump) and a **judged layer** (trajectory + decision process), scored **pairwise** like ninja, averaged over many freeze-points and repos.

## The agent — what it actually does

The agent is the part contributors improve (it lives in [`agent/`](agent/)). Given a repo
frozen at a moment in time, it decides what a strong maintainer would do next — in four steps:

1. **Infer the "maintainer philosophy."** Before deciding anything, it reads the repo's
   history, README, and recent activity to work out the project's values and direction —
   conservative or fast-moving? refactor-first? heading toward a 1.0 release? This grounds
   everything that follows, and it's the hardest, most important part.
2. **Read the situation.** Open issues, open PRs, recent commits, releases — the maintainer's
   working surface as of that moment (and nothing from the future).
3. **Plan and decide.** Propose the next maintainer actions / PRs and the concrete calls
   (merge / request-changes / reject, triage, reviewer, release) — each with its reasoning.
4. **Implement when needed.** Produce an actual code patch when that's the right move — but
   writing code is only one of the actions a maintainer takes.

The benchmark then scores those decisions against what the maintainers **actually did next**.
So a better agent = better philosophy inference, planning, and judgment — that's what you
improve.

> New here? The module layout and the full agent contract are in
> [docs/architecture.md](docs/architecture.md). The friendliest place to start is a
> [`good first issue`](https://github.com/gittensor-vanguard/vanguarstew/labels/good%20first%20issue).

## Quickstart

```bash
# offline dry-run: no network, deterministic stub LLM — proves the loop wiring
VANGUARSTEW_OFFLINE=1 python -m scripts.run_eval --repo /path/to/some/git/repo --tasks 2 --horizon 5

# live run against a managed-inference endpoint (ninja-style contract)
python -m scripts.run_eval --repo /path/to/repo --tasks 5 --horizon 5 \
    --model <validator-model> --api-base http://validator-proxy/v1 --api-key "$TOKEN"

# multi-repo: replay several repos and aggregate a cross-repo composite (generalization)
VANGUARSTEW_OFFLINE=1 python -m scripts.run_eval --repos /path/to/a /path/to/b --tasks 2 --horizon 5

# repo-set: replay a checked-in curated config (clone listed repos locally first)
VANGUARSTEW_OFFLINE=1 python -m scripts.run_eval --repo-set benchmark/repo_sets/curated.json --tasks 2 --horizon 5

# validate a repo-set JSON before replay (types + freeze-window bounds)
python -m scripts.validate_repo_set benchmark/repo_sets/example.json

# smoke test (no network, no git needed)
VANGUARSTEW_OFFLINE=1 python -m pytest -q

# CI gate: exit non-zero when composite_mean drops below a floor
VANGUARSTEW_OFFLINE=1 python -m scripts.run_eval --repo /path/to/repo --tasks 2 --horizon 5 --fail-under 0.5

# compare two saved --out artifacts (JSON on stdout, headline on stderr)
python -m scripts.compare_eval baseline.json candidate.json

# render a saved --out artifact as a readable Markdown report
python -m scripts.report result.json

# rank several saved --out artifacts (pick the best candidate agent)
python -m scripts.leaderboard agent_a=run_a.json agent_b=run_b.json
```

> **Dev-only backend:** [`tools/codex_llm.py`](tools/codex_llm.py) can drive the benchmark and
> maintenance tooling from a locally-authenticated `codex` CLI (ChatGPT / OAuth, e.g. gpt-5.5)
> with **no API key** — convenient for local exploration. It is for development only: the
> scored `agent.solve` path always uses validator-supplied inference (the managed-inference
> contract in [`agent/llm.py`](agent/llm.py)), never codex.

`--repo` scores one repo; `--repos` scores several and averages each repo's own
`composite_mean` into one cross-repo number. Each single-repo `run_replay` result carries the
composite contract — `composite_mean` plus `composite_parts` (the `judge_mean` and
`objective_mean` it blends, per the `weights`):

```jsonc
// single-repo (--repo) result, composite fields:
{
  "composite_mean": 0.6,                              // mean blended score in [0, 1]
  "composite_parts": { "judge_mean": 1.0, "objective_mean": 0.0 },  // the two blended means
  "weights": { "judge": 0.6, "objective": 0.4 },     // how the parts are blended
  "rows": [ /* per-task: winner, objective, composite */ ]
}
```

The `--repos` aggregate result shape is:

```jsonc
{
  "repos": 2,            // repos given
  "scored_repos": 2,     // repos that produced tasks (and a composite_mean)
  "skipped": 0,          // repos too small for the horizon (kept below, excluded from the mean)
  "composite_mean": 0.6, // mean of each scored repo's composite_mean
  "composite_parts": { "judge_mean": 1.0, "objective_mean": 0.0 },  // means of the per-repo parts
  "per_repo": [ /* each repo's full run_replay result, or its {"error": ...} */ ]
}
```

## Status

**Active development.** The core loop runs end-to-end and is **live-verified against a real
model** (see the demo above). Shipped so far (M0–M3): history-derived replay, an objective
scoring anchor plus a decision-process judge, leakage defenses, knowable-at-T GitHub context,
and **generalization** — multi-repo replay with an aggregated cross-repo composite and a
leakage-safe, versioned repo-set config. Open source (MIT), CI green on Python 3.10–3.12, and
registered on gittensor. Next: held-out generalization scoring (finishing M3) and the fully
agentic loop (M4). See [ROADMAP.md](ROADMAP.md).

## Contributing

Contributions are welcome — the surface is open. **Open PRs against the `test` branch, not `main`** — `main` is maintainer-promoted from `test` (see [CONTRIBUTING → Branches](CONTRIBUTING.md#branches)). Start with [CONTRIBUTING.md](CONTRIBUTING.md)
for setup, and [REVIEW.md](REVIEW.md) for exactly how contributions are gated, reviewed, and
scored (the process is designed to be predictable and reproducible). Browse open
[issues](https://github.com/gittensor-vanguard/vanguarstew/issues) — especially
[`good first issue`](https://github.com/gittensor-vanguard/vanguarstew/labels/good%20first%20issue)
and [`help wanted`](https://github.com/gittensor-vanguard/vanguarstew/labels/help%20wanted).

The module layout and full agent contract live in [docs/architecture.md](docs/architecture.md).

pyproject head:
[build-system]
requires = ["setuptools>=61"]
build-backend = "setuptools.build_meta"

[project]
name = "vanguarstew"
version = "0.3.0"
description = "A general reposit

## Issue body

## Problem

Replay artifacts report judge outcomes through `tally`, `decisive_margin`, and per-task `rows`. Promotion, regression, and leaderboard tooling consume those fields, but nothing verifies they agree. A hand-edited artifact could inflate `decisive_margin` while per-task rows tell a different story.

## Proposal

Add `benchmark/tally_integrity.py` and `scripts/tally_integrity.py` that verify, for each scored replay slice:

- `tally` carries numeric challenger/baseline/tie counts that sum to `tasks`
- when `rows` are present, `len(rows) == tasks` and winner labels recount to the same tally
- `decisive_margin` equals `challenger - baseline` when present

Support single-repo, multi-repo `per_repo` entries, and `--generalization` partitions. Expose a `--strict` CLI exit code for CI gating.

## Acceptance

- Offline unit tests under `tests/test_tally_integrity.py`
- `ruff check .` and `VANGUARSTEW_OFFLINE=1 python -m pytest -q` pass

## Comments

## vanguarstew — 2026-07-06T18:27:20Z

This fits the roadmap's emphasis on benchmark reliability and CI gating. The proposal is clear and well-structured. Please proceed with implementing the described checks and unit tests. Ensure the --strict flag exits non-zero on mismatch for CI integration.

<!-- vanguarstew:triage:662 -->

## Inventory excerpt

top files
.git/config
.git/description
.git/FETCH_HEAD
.git/HEAD
.git/hooks/applypatch-msg.sample
.git/hooks/commit-msg.sample
.git/hooks/fsmonitor-watchman.sample
.git/hooks/post-update.sample
.git/hooks/pre-applypatch.sample
.git/hooks/pre-commit.sample
.git/hooks/pre-merge-commit.sample
.git/hooks/pre-push.sample
.git/hooks/pre-rebase.sample
.git/hooks/pre-receive.sample
.git/hooks/prepare-commit-msg.sample
.git/hooks/push-to-checkout.sample
.git/hooks/update.sample
.git/index
.git/info/exclude
.git/logs/HEAD
.git/objects/pack/pack-40d2aaf891b28469e812c6de7c39e18a6b42ca24.idx
.git/objects/pack/pack-40d2aaf891b28469e812c6de7c39e18a6b42ca24.pack
.git/objects/pack/pack-40d2aaf891b28469e812c6de7c39e18a6b42ca24.promisor
.git/objects/pack/pack-4f1a5f918430f3c160d90d318f22ac9ff70a445e.idx
.git/objects/pack/pack-4f1a5f918430f3c160d90d318f22ac9ff70a445e.pack
.git/objects/pack/pack-4f1a5f918430f3c160d90d318f22ac9ff70a445e.promisor
.git/ORIG_HEAD
.git/packed-refs
.git/refs/heads/main
.github/CODEOWNERS
.github/dependabot.yml
.github/ISSUE_TEMPLATE/bug_report.yml
.github/ISSUE_TEMPLATE/config.yml
.github/ISSUE_TEMPLATE/feature_request.yml
.github/PULL_REQUEST_TEMPLATE.md
.github/workflows/ci.yml
.github/workflows/labeler.yml
.github/workflows/pr-integrity.yml
.github/workflows/pr-limit.yml
.github/workflows/pr-source-check.yml
.github/workflows/pr-target-check.yml
.gitignore
agent.py
agent/__init__.py
agent/context.py
agent/decider.py
agent/llm.py
agent/philosophy.py
agent/planner.py
agent/review.py
AGENTS.md
benchmark/__init__.py
benchmark/acceptance.py
benchmark/aggregate_integrity.py
benchmark/agree_order_share.py
benchmark/artifact_snapshot.py
benchmark/baselines.py
benchmark/blend_weights.py
benchmark/comparability.py
benchmark/component_floor.py
benchmark/component_mix.py
benchmark/composite_spread.py
benchmark/coverage.py
benchmark/decisive_rate.py
benchmark/disagreement_outlook.py
benchmark/dual_order_coverage.py
benchmark/dual_order_share.py
benchmark/error_repo_share.py
benchmark/freeze_coverage.py
benchmark/freeze_digest.py
benchmark/freeze.py
benchmark/gap_integrity.py
benchmark/gap_outlook.py
benchmark/generalization_gate.py
benchmark/github_context.py
benchmark/improvement.py
benchmark/judge_calibration.py
benchmark/judge_corpus/__init__.py
benchmark/judge_corpus/manifest.json
benchmark/judge_corpus/scenarios/001-substance-beats-filler.json
benchmark/judge_corpus/scenarios/002-philosophy-breaks-plan-tie.json
benchmark/judge_corpus/scenarios/003-equal-submissions-tie.json
benchmark/judge_corpus/scenarios/004-structured-fields-bonus.json
benchmark/judge_corpus/scenarios/005-empty-plan-loses.json
benchmark/judge_corpus/scenarios/006-scalar-filler-scores-zero.json
benchmark/judge_corpus/scenarios/007-scalar-concrete-wins.json
benchmark/judge_corpus/scenarios/008-non-dict-submission-loses.json
benchmark/judge_corpus/scenarios/009-theme-filler-word-loses.json
benchmark/judge_corpus/scenarios/010-long-filler-vs-short-concrete.json
benchmark/judge_corpus/scenarios/011-multi-item-concrete-plan.json
benchmark/judge_corpus/scenarios/012-philosophy-values-signal.json
benchmark/judge_corpus/scenarios/013-philosophy-direction-signal.json
benchmark/judge_corpus/scenarios/014-rationale-breaks-tie.json
benchmark/judge_corpus/scenarios/015-null-plan-item-no-inflate.json
benchmark/judge_corpus/scenarios/016-non-string-title-survives.json
benchmark/judge_corpus/scenarios/017-symmetric-strong-a.json
benchmark/judge_corpus/scenarios/018-symmetric-strong-b.json
benchmark/judge_corpus/scenarios/019-symmetric-tie.json
benchmark/judge_corpus/scenarios/020-issue-backlog-context.json
benchmark/judge_corpus/scenarios/021-release-cadence-context.json
benchmark/judge_corpus/scenarios/022-refactor-momentum-context.json
benchmark/judge_corpus/scenarios/023-docs-plan-structured.json
benchmark/judge_corpus/scenarios/024-mixed-quality-two-step.json
benchmark/judge_corpus/scenarios/025-heavy-revealed-window.json
benchmark/judge_corpus/scenarios/026-partial-philosophy-edges.json
benchmark/judge_corpus/scenarios/027-files-field-bonus.json
benchmark/judge_corpus/scenarios/028-kind-only-bonus.json
benchmark/judge_corpus/scenarios/029-blank-title-items-ignored.json
benchmark/judge_corpus/scenarios/030-whitespace-title-items-ignored.json
benchmark/judge_gate.py
benchmark/judge_report_integrity.py
benchmark/judge_wlt.py
benchmark/judge.py
benchmark/leaderboard.py
benchmark/leakage_audit.py
benchmark/leakage.py
benchmark/margin_outlook.py
benchmark/offline_share.py
benchmark/order_agree_rate.py
benchmark/partition_task_share.py
benchmark/promotion.py
benchmark/regression.py
benchmark/repeatability.py
benchmark/repo_score_spread.py
benchmark/repo_set_readiness.py
benchmark/repo_set.py
benchmark/repo_sets/curated.json
benchmark/repo_sets/example.json
benchmark/repo_sets/README.md
benchmark/repo_task_mean.py
benchmark/report.py
benchmark/row_integrity.py
benchmark/run_clean.py
benchmark/runner.py
benchmark/sample_adequacy.py
benchmark/score_calibration.py
benchmark/score_corpus/__init__.py
benchmark/score_corpus/manifest.json
benchmark/score_corpus/scenarios/001-module-recall-by-name.json
benchmark/score_corpus/scenarios/002-module-recall-via-files.json
benchmark/score_corpus/scenarios/003-kind-tag-not-module-recall.json
benchmark/score_corpus/scenarios/004-weighted-module-recall.json
benchmark/score_corpus/scenarios/005-release-predicted.json
benchmark/score_corpus/scenarios/006-incidental-version-not-release.json
benchmark/score_corpus/scenarios/007-bump-major-match.json
benchmark/score_corpus/scenarios/008-backlog-recall-matches.json
benchmark/score_corpus/scenarios/009-backlog-excluded-from-component.json
benchmark/score_corpus/scenarios/010-empty-plan-zero.json
benchmark/score_corpus/scenarios/011-kind-recall-matched.json
benchmark/score_corpus/scenarios/012-composite-score-blend.json
benchmark/score_corpus/scenarios/013-scalar-plan-files.json
benchmark/score_integrity.py
benchmark/score.py
benchmark/scored_fraction.py
benchmark/single_order_share.py
benchmark/skip_budget.py
benchmark/skip_share.py
benchmark/tally_integrity.py
benchmark/taskgen.py
benchmark/tie_order_share.py
benchmark/trend.py
benchmark/weight_integrity.py
benchmark/win_rate.py
blog/m3-milestone.md
blog/spec-driven-development.md
CHANGELOG.md
CODE_OF_CONDUCT.md
CONTRIBUTING.md
docs/architecture.md
docs/spec-driven-development.md
docs/vanguarstew-demo.gif
docs/vanguarstew-m3.gif
LICENSE
m3_acceptance_result.json
pyproject.toml
README.md
REVIEW.md
ROADMAP.md
scripts/__init__.py
scripts/acceptance.py
scripts/aggregate_integrity.py
scripts/agree_order_share.py
scripts/artifact_snapshot.py
scripts/audit_context.py
scripts/blend_weights.py
scripts/calibrate_judge.py
scripts/calibrate_score.py
scripts/comparability.py
scripts/compare_eval.py
scripts/component_floor.py
scripts/component_mix.py
scripts/composite_spread.py
scripts/decisive_rate.py
scripts/disagreement_outlook.py
scripts/dual_order_coverage.py
scripts/dual_order_share.py
scripts/error_repo_share.py
scripts/freeze_coverage.py
scripts/freeze_digest.py
scripts/gap_integrity.py
scripts/gap_outlook.py
scripts/generalization_gate.py
scripts/improvement.py
scripts/judge_gate.py
scripts/judge_report_integrity.py
scripts/judge_wlt.py
scripts/leaderboard.py
scripts/margin_outlook.py
scripts/offline_share.py
scripts/order_agree_rate.py
scripts/partition_task_share.py
scripts/promotion.py
scripts/regression.py
scripts/repeatability.py
scripts/repo_coverage.py
scripts/repo_score_spread.py
scripts/repo_set_readiness.py
scripts/repo_task_mean.py
scripts/report.py
scripts/review_pr.py
scripts/row_integrity.py
scripts/run_clean.py
scripts/run_eval.py
scripts/sample_adequacy.py
scripts/score_integrity.py
scripts/scored_fraction.py
scripts/single_order_share.py
scripts/skip_budget.py
scripts/skip_share.py
scripts/tally_integrity.py
scripts/tie_order_share.py
scripts/trend.py
scripts/validate_repo_set.py
scripts/weight_integrity.py
scripts/win_rate.py
SECURITY.md
specs/001-solve-contract/plan.md
specs/001-solve-contract/spec.md
specs/002-scoring-anchor/plan.md
specs/002-scoring-anchor/spec.md
specs/003-leakage-integrity/plan.md
specs/003-leakage-integrity/spec.md
specs/004-pairwise-judge/plan.md
specs/004-pairwise-judge/spec.md
specs/005-repo-set/plan.md
specs/005-repo-set/spec.md
specs/006-agent-decision/plan.md
specs/006-agent-decision/spec.md
specs/007-agent-planner/plan.md
specs/007-agent-planner/spec.md
specs/009-agent-review/plan.md
specs/009-agent-review/spec.md
specs/010-agent-llm/plan.md
specs/010-agent-llm/spec.md
specs/017-benchmark-judge-calibration/plan.md
specs/017-benchmark-judge-calibration/spec.md
specs/018-benchmark-score-calibration/plan.md
specs/018-benchmark-score-calibration/spec.md
specs/019-benchmark-comparability/plan.md
specs/019-benchmark-comparability/spec.md
specs/021-benchmark-freeze-path-parse/plan.md
specs/021-benchmark-freeze-path-parse/spec.md
specs/022-benchmark-leakage-audit/plan.md
specs/022-benchmark-leakage-audit/spec.md
specs/024-benchmark-commit-kind/plan.md
specs/024-benchmark-commit-kind/spec.md
specs/025-benchmark-judge-wlt/plan.md
specs/025-benchmark-judge-wlt/spec.md
specs/027-benchmark-gap-integrity/plan.md
specs/027-benchmark-gap-integrity/spec.md
specs/028-benchmark-aggregate-integrity/plan.md
specs/028-benchmark-aggregate-integrity/spec.md
specs/029-benchmark-row-integrity/plan.md
specs/029-benchmark-row-integrity/spec.md
specs/031-benchmark-sample-adequacy/plan.md
specs/031-benchmark-sample-adequacy/spec.md
specs/032-benchmark-freeze-coverage/plan.md
specs/032-benchmark-freeze-coverage/spec.md
specs/034-benchmark-scored-fraction/plan.md
specs/034-benchmark-scored-fraction/spec.md
tests/test_acceptance.py
tests/test_aggregate_integrity.py
tests/test_agree_order_share.py
tests/test_artifact_snapshot.py
tests/test_baselines.py
tests/test_blend_weights.py
tests/test_codex_llm.py
tests/test_comparability.py
tests/test_compare_eval.py
tests/test_component_floor.py
tests/test_component_mix.py
tests/test_compose.py
tests/test_composite_spread.py
tests/test_context.py
tests/test_coverage.py
tests/test_decider.py
tests/test_decisive_rate.py
tests/test_disagreement_outlook.py
tests/test_dual_order_coverage.py
tests/test_dual_order_share.py
tests/test_error_repo_share.py
tests/test_freeze_coverage.py
tests/test_freeze_digest.py
tests/test_freeze.py
tests/test_gap_integrity.py
tests/test_gap_outlook.py
tests/test_generalization_gate.py
tests/test_generalization_report.py
tests/test_github_context.py
tests/test_improvement.py
tests/test_judge_calibration.py
tests/test_judge_gate.py
tests/test_judge_report_integrity.py
tests/test_judge_wlt.py
tests/test_judge.py
tests/test_leaderboard.py
tests/test_leakage_audit.py
tests/test_leakage.py
tests/test_margin_outlook.py
tests/test_multi_repo.py
tests/test_offline_share.py
tests/test_order_agree_rate.py
tests/test_partition_task_share.py
tests/test_philosophy.py
tests/test_planner.py
tests/test_promotion.py
tests/test_regression.py
tests/test_repeatability.py
tests/test_repo_score_spread.py
tests/test_repo_set_readiness.py
tests/test_repo_set.py
tests/test_repo_task_mean.py
tests/test_report.py
tests/test_review_pr.py
tests/test_review.py
tests/test_row_integrity.py
tests/test_run_clean.py
tests/test_run_eval.py
tests/test_sample_adequacy.py
tests/test_score_calibration.py
tests/test_score_integrity.py
tests/test_score.py
tests/test_scored_fraction.py
tests/test_single_order_share.py
tests/test_skip_budget.py
tests/test_skip_share.py
tests/test_smoke.py
tests/test_spec_001_solve.py
tests/test_spec_002_compose.py
tests/test_spec_003_leakage.py
tests/test_spec_004_judge.py
tests/test_spec_005_repo_set.py
tests/test_spec_006_decision.py
tests/test_spec_007_planner.py
tests/test_spec_009_review.py
tests/test_spec_010_llm.py
tests/test_spec_017_judge_calibration.py
tests/test_spec_018_score_calibration.py
tests/test_spec_019_comparability.py
tests/test_spec_021_freeze_path_parse.py
tests/test_spec_022_leakage_audit.py
tests/test

## Grep excerpt

===== issue body =====
## Problem

Replay artifacts report judge outcomes through `tally`, `decisive_margin`, and per-task `rows`. Promotion, regression, and leaderboard tooling consume those fields, but nothing verifies they agree. A hand-edited artifact could inflate `decisive_margin` while per-task rows tell a different story.

## Proposal

Add `benchmark/tally_integrity.py` and `scripts/tally_integrity.py` that verify, for each scored replay slice:

- `tally` carries numeric challenger/baseline/tie counts that sum to `tasks`
- when `rows` are present, `len(rows) == tasks` and winner labels recount to the same tally
- `decisive_margin` equals `challenger - baseline` when present

Support single-repo, multi-repo `per_repo` entries, and `--generalization` partitions. Expose a `--strict` CLI exit code for CI gating.

## Acceptance

- Offline unit tests under `tests/test_tally_integrity.py`
- `ruff check .` and `VANGUARSTEW_OFFLINE=1 python -m pytest -q` pass
===== money/competition/judge hits =====
./benchmark/judge_gate.py:3:The M2/M3 acceptance leans on judge robustness — "pairwise judging, dual-order consistency,
./benchmark/judge_gate.py:4:disagreement tracking." A composite score is only as trustworthy as the judge behind it: if the
./benchmark/judge_gate.py:7:``run_eval`` reports the judge stats, but whether they clear the bar is decided by eye.
./benchmark/judge_gate.py:9:This makes that a reproducible **pass/fail gate**. ``check_judge(result)`` evaluates a
./benchmark/judge_gate.py:22:Pure evaluation: no I/O, never mutates the result, and a malformed/non-dict result simply fails
./benchmark/judge_gate.py:207:    returns ``"judge: no checks evaluated"`` after logging any warnings.
./benchmark/judge_gate.py:212:        return "judge: no checks evaluated"
./benchmark/partition_task_share.py:1:"""Summarize how scored tasks are distributed across generalization partitions.
./benchmark/partition_task_share.py:4:scored tasks came from each ``tuned`` / ``held_out`` partition — useful when a headline
./benchmark/partition_task_share.py:16:from benchmark.comparability import artifact_kind
./benchmark/partition_task_share.py:62:def _scored_tasks(per_repo, field: str = "per_repo") -> int:
./benchmark/partition_task_share.py:85:    """Return scored-task distribution for a replay ``artifact``."""
./benchmark/partition_task_share.py:90:        scored = tasks if _is_int(tasks) and tasks > 0 else 0
./benchmark/partition_task_share.py:93:            "total_tasks": scored,
./benchmark/partition_task_share.py:97:        scored = _scored_tasks(artifact.get("per_repo"))
./benchmark/partition_task_share.py:100:            "total_tasks": scored,
./benchmark/partition_task_share.py:102:                "multi": _partition_entry(scored, scored),
./benchmark/partition_task_share.py:103:            } if scored > 0 else None,
./benchmark/partition_task_share.py:110:            totals[name] = _scored_tasks(part.get("per_repo"), f"{name}.per_repo")
./benchmark/partition_task_share.py:136:        return "partition task share: no scored tasks"
./benchmark/partition_task_share.py:146:    return f"partition task share: {kind} {total} scored task(s)"
./benchmark/error_repo_share.py:3:A multi-repo run keeps each repository's outcome in ``per_repo``; a repo that could not be evaluated
./benchmark/error_repo_share.py:9:Pure analysis: no I/O, never mutates its input. The share is always a decimal fraction in ``[0, 1]``
./benchmark/error_repo_share.py:17:from benchmark.comparability import artifact_kind
./benchmark/baselines.py:1:"""Reference baseline maintainers — the opponents a challenger is judged against.
./benchmark/baselines.py:9:                  bar than ``empty`` — a challenger has to actually out-reason "keep doing
./benchmark/baselines.py:12:                  the planner's own guidance that a strong maintainer clears or explicitly
./benchmark/baselines.py:22:rationale), so it can flow through ``_submission`` and the judge unchanged. Select one by
./benchmark/baselines.py:32:from benchmark.score import commit_kind, is_release_subject
./benchmark/baselines.py:45:    "ci": "refactor",
./benchmark/baselines.py:46:    "test": "refactor",
./benchmark/baselines.py:54:# itself is NOT here: it defers to score.is_release_subject (the canonical helper) so
./benchmark/baselines.py:55:# baseline classification can't drift from scoring semantics.
./benchmark/baselines.py:57:    ("dep", ("bump", "dependency", "dependencies", "deps", "upgrade", "dependabot")),
./benchmark/baselines.py:62:    ("test", ("test", "coverage", "ci")),
./benchmark/baselines.py:120:            # The planner has no "test" kind; CI/test hardening is infra momentum, not triage.
./benchmark/baselines.py:121:            if kind == "test":
./benchmark/baselines.py:144:        "merge_bar": "inferred from recent commit patterns (no explicit signal)",
./benchmark/baselines.py:211:    A strong maintainer clears (or explicitly schedules) the open review queue before starting
./benchmark/skip_budget.py:1:"""Gate whether a multi-repo run scored enough of its repos to be trusted.
./benchmark/skip_budget.py:3:``run_multi_replay`` attempts a set of repos and scores the ones that clone, build, and produce
./benchmark/skip_budget.py:4:tasks; the rest are *skipped* (``skipped = repos - scored_repos``). The headline composite is then
./benchmark/skip_budget.py:5:a mean over the repos that *did* score. Nothing stops a run that skipped most of its set - because
./benchmark/skip_budget.py:11:this gates the run *outcome* (enough of them actually scored). ``check_skip_budget(result)``
./benchmark/skip_budget.py:12:evaluates named criteria, each failing closed:
./benchmark/skip_budget.py:15:   ``scored_repos`` are whole numbers, ``0 <= scored_repos <= repos``, ``repos > 0``, and (when
./benchmark/skip_budget.py:16:   present) ``skipped`` equals ``repos - scored_repos``. A single-repo run, fractional counts, or
./benchmark/skip_budget.py:18:2. ``enough_scored`` - at least ``min_scored`` repos produced a score.
./benchmark/skip_budget.py:23:Pure evaluation: no I/O, never mutates the result, and a malformed/non-dict result (including one
./benchmark/skip_budget.py:113:    """``(repos, scored)`` when the result is a coherent multi-repo tally, else ``None``.
./benchmark/skip_budget.py:115:    Requires whole-number ``repos`` and ``scored_repos`` with ``repos > 0`` and
./benchmark/skip_budget.py:116:    ``0 <= scored <= repos``, and - when a ``skipped`` field is present - that it is a whole number
./benchmark/skip_budget.py:117:    equal to ``repos - scored`` (otherwise the accounting is internally inconsistent).
./benchmark/skip_budget.py:120:    scored = result.get("scored_repos")
./benchmark/skip_budget.py:121:    if not (_is_int(repos) and _is_int(scored)):
./benchmark/skip_budget.py:123:    if repos <= 0 or scored < 0 or scored > repos:
./benchmark/skip_budget.py:126:    if skipped is not None and not (_is_int(skipped) and skipped == repos - scored):
./benchmark/skip_budget.py:128:    return repos, scored
./benchmark/skip_budget.py:131:def check_skip_budget(result, min_scored: int = DEFAULT_MIN_SCORED,
./benchmark/skip_budget.py:133:    """Evaluate whether a multi-repo ``result`` scored enough of its repos to be trusted.
./benchmark/skip_budget.py:135:    Returns ``{"passed": bool, "checks": [{"name", "passed", "detail"}], "repos", "scored_repos",
./benchmark/skip_budget.py:136:    "skipped", "skip_rate", "min_scored", "max_skip_rate"}``. ``passed`` is True only when every
./benchmark/skip_budget.py:141:    repos, scored = counts if counts else (None, None)
./benchmark/skip_budget.py:142:    skipped = repos - scored if counts else None
./benchmark/skip_budget.py:150:        f"{scored} of {repos} repo(s) scored, {skipped} skipped" if counts
./benchmark/skip_budget.py:151:        else "no coherent multi-repo tally (repos / scored_repos / skipped)")
./benchmark/skip_budget.py:153:    add("enough_scored", counts is not None and scored >= min_scored,
./benchmark/skip_budget.py:154:        f"{scored} scored repo(s) >= {min_scored}" if counts else "scored-repo count unavailable")
./benchmark/skip_budget.py:164:        "scored_repos": scored,
./benchmark/skip_budget.py:167:        "min_scored": min_scored,
./benchmark/skip_budget.py:188:    returns ``"skip budget: no checks evaluated"`` after logging any warnings.
./benchmark/skip_budget.py:193:        return "skip budget: no checks evaluated"
./benchmark/skip_budget.py:195:        return (f"skip budget: COVERED ({result.get('scored_repos')} of {result.get('repos')} "
./benchmark/skip_budget.py:196:                f"repos scored, skip rate {result.get('skip_rate')})")
./benchmark/leakage_audit.py:5::func:`benchmark.leakage.strip_forward_refs` would change it, so the audit cannot drift from
./benchmark/leakage_audit.py:14:from benchmark.leakage import _scrub_list, strip_forward_refs
./benchmark/runner.py:4:top-level `agent.py` module and the `agent/` package don't collide. For MVP the challenger is
./benchmark/runner.py:5:compared against a naive baseline maintainer; in M2+ this becomes challenger-vs-king.
./benchmark/runner.py:22:from benchmark.baselines import DEFAULT_BASELINE, empty_solve, get_baseline
./benchmark/runner.py:23:from benchmark.freeze import write_frozen
./benchmark/runner.py:24:from benchmark.github_context import enrich_context, open_issues_from_context
./benchmark/runner.py:25:from benchmark.judge import build_judge_report, judge_verbose, summarize_judge_orders
./benchmark/runner.py:26:from benchmark.leakage import scrub_context
./benchmark/runner.py:27:from benchmark.repo_set import RepoSetError, is_placeholder_source, load_repo_set
./benchmark/runner.py:28:from benchmark.score import (
./benchmark/runner.py:30:    composite_score,
./benchmark/runner.py:32:    objective_score,
./benchmark/runner.py:35:from benchmark.taskgen import generate_tasks
./benchmark/runner.py:39:# Challenger-perspective judge outcome per row (mirrors score._JUDGE_OUTCOME, keyed by the
./benchmark/runner.py:40:# runner's decoded winner label): a win is 1.0, a tie 0.5, a loss 0.0.
./benchmark/runner.py:41:_JUDGE_COMPONENT = {"challenger": 1.0, "tie": 0.5, "baseline": 0.0}
./benchmark/runner.py:54:# Backwards-compatible alias; opponents now live in benchmark.baselines.
./benchmark/runner.py:58:def _submission(out: dict) -> dict:
./benchmark/runner.py:105:    tally = {"challenger": 0, "baseline": 0, "tie": 0}
./benchmark/runner.py:119:            challenger = solve(
./benchmark/runner.py:124:            if not isinstance(challenger, dict):
./benchmark/runner.py:125:                challenger = {}  # a miner agent may return a non-dict; degrade to empty, don't crash
./benchmark/runner.py:127:            winner, judge_order = judge_verbose(
./benchmark/runner.py:128:                ctx, _submission(challenger), _submission(baseline_out),
./benchmark/runner.py:130:            who = {"A": "challenger", "B": "baseline", "tie": "tie"}[winner]
./benchmark/runner.py:132:            obj = objective_score(
./benchmark/runner.py:133:                challenger.get("plan"), task["revealed"],
./benchmark/runner.py:134:                version_bump=challenger.get("version_bump"),
./benchmark/runner.py:141:                "winner": who,
./benchmark/runner.py:143:                "overlap": trajectory_overlap(challenger.get("plan"), task["revealed"]),
./benchmark/runner.py:145:                "composite": composite_score(winner, obj, w_judge, w_objective),
./benchmark/runner.py:151:    # The single-repo composite output contract: the mean blended score, plus the two
./benchmark/runner.py:153:    # inspectable and the multi-repo aggregate has explicit parts to average.
./benchmark/runner.py:155:    judge_parts = [_JUDGE_COMPONENT[r["winner"]] for r in rows]
./benchmark/runner.py:162:        "decisive_margin": tally["challenger"] - tally["baseline"],
./benchmark/runner.py:212:    """Return ``rows`` when it is a list; otherwise treat as no scored tasks.
./benchmark/runner.py:223:    Takes the already-scored per-task ``rows`` from :func:`run_replay` (each carrying a
./benchmark/runner.py:224:    ``winner`` and an ``objective``) and re-blends them at each ``(w_judge, w_objective)`` pair,
./benchmark/runner.py:228:    The per-task blend mirrors :func:`benchmark.score.composite_score` exactly (weights are
./benchmark/runner.py:234:    scored = []
./benchmark/runner.py:244:        winner = r.get("winner")
./benchmark/runner.py:245:        if winner in _JUDGE_COMPONENT:
./benchmark/runner.py:246:            scored.append(
./benchmark/runner.py:247:                (_JUDGE_COMPONENT[winner], objective_component(r.get("objective") or {}))
./benchmark/runner.py:252:        per_task = [round((w_judge * j + w_objective * o) / total, 3) for j, o in scored]
./benchmark/runner.py:264:    generalization signal: how the agent scores *across* codebases, not just within one.
./benchmark/runner.py:268:    miscounted as scored.
./benchmark/runner.py:271:    A repo that fails to score — too small to yield tasks, or unusable (missing path, not a git
./benchmark/runner.py:319:    tally = {"challenger": 0, "baseline": 0, "tie": 0}
./benchmark/runner.py:357:        "scored_repos": len(composites),
./benchmark/runner.py:376:    `run_multi_replay` scores one partition at a time; this runs both the `tuned` and
./benchmark/runner.py:379:    worse on repos it was never tuned against. That gap is the M3 acceptance signal: held-out
./benchmark/runner.py:381:    actually scored a repo, so it is never reported from a single side; a partition the config
./benchmark/runner.py:391:            return {"error": str(exc), "scored_repos": 0, "composite_mean": 0.0}
./benchmark/runner.py:397:    if tuned.get("scored_repos") and held_out.get("scored_repos"):
./benchmark/repo_sets/example.json:3:  "description": "EXAMPLE / starter leakage-safe repo set. The sources below are placeholders (OWNER/...) and are NOT operational — copy this file, replace them with vetted repos, and load that curated config for real scoring. The schema and freeze-window hints are the contract this demonstrates.",
./benchmark/repo_sets/example.json:4:  "strategy": "Mix RECENT repos (freeze windows past a model's training cutoff) with OBSCURE repos (low-traffic, unlikely to be memorized). Prefer recent commit windows and rotate freeze points so a memorized outcome cannot win. Reserve some repos as held_out to score generalization on codebases the agent was never tuned against.",
./benchmark/repo_sets/README.md:4:`benchmark.repo_set.load_repo_set(path)`. A path is **always required** — there is no implicit
./benchmark/repo_sets/README.md:35:- Same tier rules as above, but `held_out: true` — reserved for generalization scoring and
./benchmark/repo_sets/README.md:36:  excluded from tuning runs unless explicitly requested.
./benchmark/repo_sets/README.md:40:Clone the listed repositories locally, then point `run_eval` at the config:
./benchmark/repo_sets/README.md:43:VANGUARSTEW_OFFLINE=1 python -m scripts.run_eval \
./benchmark/repo_sets/README.md:44:  --repo-set benchmark/repo_sets/curated.json \
./benchmark/repo_sets/README.md:48:Use `--repo-set-partition held_out` to score only held-out entries, or `all` for every repo
./benchmark/repo_sets/curated.json:3:  "description": "Operational leakage-safe repo set for benchmark replay. Each entry is a vetted public repository with freeze-window hints aligned to the recent/obscure tier strategy. Use this config (not example.json) for intentional multi-repo scoring runs.",
./benchmark/repo_sets/curated.json:4:  "strategy": "Mix RECENT repos (freeze windows past a model's training cutoff) with OBSCURE repos (low-traffic, unlikely to be memorized). Reserve held_out entries for generalization scoring only.",
./benchmark/repo_sets/curated.json:20:      "source": "https://github.com/pytest-dev/pluggy",
./benchmark/repo_sets/curated.json:28:      "notes": "Steady pytest infrastructure maintenance; rotate freeze points to avoid answer reuse."
./benchmark/repo_sets/curated.json:51:      "notes": "Held-out recent repo for generalization scoring (#52)."
./benchmark/regression.py:1:"""Gate a candidate benchmark run against a baseline run for regressions.
./benchmark/regression.py:3:``compare_eval`` *reports* the diff between two artifacts and ``trend`` tracks a score over many
./benchmark/regression.py:4:runs; neither yields a **pass/fail decision** you can gate CI on for a single before/after pair.
./benchmark/regression.py:6:(this run), ``check_regression`` decides whether the candidate is safe to accept — it must not
./benchmark/regression.py:15:Pure evaluation: no I/O, never mutates its inputs, and a malformed/non-dict artifact simply fails
./benchmark/regression.py:23:from benchmark.trend import headline_score
./benchmark/regression.py:111:    """Decide whether ``candidate`` regressed versus ``baseline``.
./benchmark/regression.py:117:    base_score = headline_score(baseline)
./benchmark/regression.py:118:    cand_score = headline_score(candidate)
./benchmark/regression.py:126:    both_scored = base_score is not None and cand_score is not None
./benchmark/regression.py:127:    add("both_scored", both_scored,
./benchmark/regression.py:128:        f"baseline composite {base_score}, candidate composite {cand_score}"
./benchmark/regression.py:129:        if both_scored else "a composite score is missing from one artifact")
./benchmark/regression.py:131:    # Round the delta to the scores' 3-decimal precision before comparing, so a drop equal to
./benchmark/regression.py:133:    composite_delta = _round(cand_score - base_score) if both_scored else None
./benchmark/regression.py:134:    no_drop = both_scored and composite_delta >= -max_composite_drop
./benchmark/regression.py:136:        f"composite delta {composite_delta} >= -{max_composite_drop}" if both_scored
./benchmark/regression.py:153:        "baseline_composite": base_score,
./benchmark/regression.py:154:        "candidate_composite": cand_score,
./benchmark/regression.py:178:    returns ``"regression: no checks evaluated"`` after logging any warnings.
./benchmark/regression.py:183:        return "regression: no checks evaluated"
./benchmark/judge_corpus/manifest.json:4:  "description": "Golden scenarios for offline pairwise-judge calibration. Each entry documents the expected winner under VANGUARSTEW_OFFLINE=1 substance heuristics.",
./benchmark/judge_corpus/manifest.json:8:    {"id": "equal-submissions-tie", "file": "003-equal-submissions-tie.json"},
./benchmark/judge_corpus/manifest.json:11:    {"id": "scalar-filler-scores-zero", "file": "006-scalar-filler-scores-zero.json"},
./benchmark/judge_corpus/manifest.json:13:    {"id": "non-dict-submission-loses", "file": "008-non-dict-submission-loses.json"},
./benchmark/judge_corpus/manifest.json:22:    {"id": "symmetric-strong-a", "file": "017-symmetric-strong-a.json"},
./benchmark/judge_corpus/manifest.json:23:    {"id": "symmetric-strong-b", "file": "018-symmetric-strong-b.json"},
./benchmark/judge_corpus/manifest.json:24:    {"id": "symmetric-tie", "file": "019-symmetric-tie.json"},
./benchmark/judge_corpus/scenarios/030-whitespace-title-items-ignored.json:32:  "expect_symmetric": true,
./benchmark/judge_corpus/scenarios/030-whitespace-title-items-ignored.json:33:  "submission_a": {
./benchmark/judge_corpus/scenarios/030-whitespace-title-items-ignored.json:42:  "submission_b": {
./benchmark/judge_corpus/scenarios/030-whitespace-title-items-ignored.json:54:  "expected_winner": "A"
./benchmark/judge_corpus/scenarios/003-equal-submissions-tie.json:2:  "id": "equal-submissions-tie",
./benchmark/judge_corpus/scenarios/003-equal-submissions-tie.json:32:  "submission_a": {
./benchmark/judge_corpus/scenarios/003-equal-submissions-tie.json:48:  "submission_b": {
./benchmark/judge_corpus/scenarios/003-equal-submissions-tie.json:64:  "expected_winner": "tie"
./benchmark/judge_corpus/scenarios/028-kind-only-bonus.json:33:  "expect_symmetric": true,
./benchmark/judge_corpus/scenarios/028-kind-only-bonus.json:34:  "submission_a": {
./benchmark/judge_corpus/scenarios/028-kind-only-bonus.json:44:  "submission_b": {
./benchmark/judge_corpus/scenarios/028-kind-only-bonus.json:53:  "expected_winner": "A"
./benchmark/judge_corpus/scenarios/012-philosophy-values-signal.json:32:  "expect_symmetric": true,
./benchmark/judge_corpus/scenarios/012-philosophy-values-signal.json:33:  "submission_a": {
./benchmark/judge_corpus/scenarios/012-philosophy-values-signal.json:47:  "submission_b": {
./benchmark/judge_corpus/scenarios/012-philosophy-values-signal.json:56:  "expected_winner": "A"
./benchmark/judge_corpus/scenarios/011-multi-item-concrete-plan.json:32:  "expect_symmetric": true,
./benchmark/judge_corpus/scenarios/011-multi-item-concrete-plan.json:33:  "submission_a": {
./benchmark/judge_corpus/scenarios/011-multi-item-concrete-plan.json:47:        "title": "Add regression test",
./benchmark/judge_corpus/scenarios/011-multi-item-concrete-plan.json:48:        "kind": "test"
./benchmark/judge_corpus/scenarios/011-multi-item-concrete-plan.json:57:  "submission_b": {
./benchmark/judge_corpus/scenarios/011-multi-item-concrete-plan.json:73:  "expected_winner": "A"
./benchmark/judge_corpus/scenarios/004-structured-fields-bonus.json:33:  "expect_symmetric": true,
./benchmark/judge_corpus/scenarios/004-structured-fields-bonus.json:34:  "submission_a": {
./benchmark/judge_corpus/scenarios/004-structured-fields-bonus.json:54:  "submission_b": {
./benchmark/judge_corpus/scenarios/004-structured-fields-bonus.json:69:  "expected_winner": "A"
./benchmark/judge_corpus/scenarios/026-partial-philosophy-edges.json:32:  "expect_symmetric": true,
./benchmark/judge_corpus/scenarios/026-partial-philosophy-edges.json:33:  "submission_a": {
./benchmark/judge_corpus/scenarios/026-partial-philosophy-edges.json:44:  "submission_b": {
./benchmark/judge_corpus/scenarios/026-partial-philosophy-edges.json:55:  "expected_winner": "A"
./benchmark/judge_corpus/scenarios/029-blank-title-items-ignored.json:32:  "expect_symmetric": true,
./benchmark/judge_corpus/scenarios/029-blank-title-items-ignored.json:33:  "submission_a": {
./benchmark/judge_corpus/scenarios/029-blank-title-items-ignored.json:42:  "submission_b": {
./benchmark/judge_corpus/scenarios/029-blank-title-items-ignored.json:52:  "expected_winner": "A"
./benchmark/judge_corpus/scenarios/024-mixed-quality-two-step.json:32:  "expect_symmetric": true,
./benchmark/judge_corpus/scenarios/024-mixed-quality-two-step.json:33:  "submission_a": {
./benchmark/judge_corpus/scenarios/024-mixed-quality-two-step.json:47:        "title": "Add loader test",
./benchmark/judge_corpus/scenarios/024-mixed-quality-two-step.json:48:        "kind": "test"
./benchmark/judge_corpus/scenarios/024-mixed-quality-two-step.json:53:  "submission_b": {
./benchmark/judge_corpus/scenarios/024-mixed-quality-two-step.json:75:  "expected_winner": "A"
./benchmark/judge_corpus/scenarios/017-symmetric-strong-a.json:2:  "id": "symmetric-strong-a",
./benchmark/judge_corpus/scenarios/017-symmetric-strong-a.json:3:  "description": "Strong submission A wins; symmetry check verifies swap",
./benchmark/judge_corpus/scenarios/017-symmetric-strong-a.json:32:  "expect_symmetric": true,
./benchmark/judge_corpus/scenarios/017-symmetric-strong-a.json:33:  "submission_a": {
./benchmark/judge_corpus/scenarios/017-symmetric-strong-a.json:50:  "submission_b": {
./benchmark/judge_corpus/scenarios/017-symmetric-strong-a.json:59:  "expected_winner": "A"
./benchmark/judge_corpus/scenarios/008-non-dict-submission-loses.json:2:  "id": "non-dict-submission-loses",
./benchmark/judge_corpus/scenarios/008-non-dict-submission-loses.json:3:  "description": "Non-dict submission ranks zero and loses",
./benchmark/judge_corpus/scenarios/008-non-dict-submission-loses.json:32:  "expect_symmetric": true,
./benchmark/judge_corpus/scenarios/008-non-dict-submission-loses.json:33:  "submission_a": {
./benchmark/judge_cor

