# Prize Recon Report

## Verdict

`PARK_RISK`

## Decision

JSON:
{
  "verdict": "PARK_RISK",
  "issue": {
    "url": "https://github.com/agentclash/agentclash/issues/1097",
    "title": "RAG Eval W8: reference RAG challenge packs",
    "state": "OPEN",
    "labels": [
      "enhancement"
    ],
    "comment_count": 0,
    "updatedAt": "2026-06-23T19:32:01Z"
  },
  "money": true,
  "competition": true,
  "judge": true,
  "local": true,
  "mgfit": true,
  "risk": true
}

## Cheap commands

pwd=/Users/heath/Documents/mathgraph-lean-work/external/money_opportunity_scout_v4_prize_words/agentclash__agentclash_1097

README head:
![AgentClash banner](docs/assets/agentclash-readme-banner.png)

# AgentClash

Open-source AI-agent evaluation for real tasks. AgentClash helps teams find where agents break, replay the evidence, score the outcome, and turn failures into regression gates before release.

[Website](https://www.agentclash.dev) | [Docs](https://www.agentclash.dev/docs) | [Quickstart](https://www.agentclash.dev/docs/getting-started/quickstart) | [Challenge Packs](https://www.agentclash.dev/docs/challenge-packs) | [CI Gates](https://www.agentclash.dev/docs/guides/ci-cd-agent-gates) | [Changelog](https://www.agentclash.dev/changelog)

[![npm version](https://img.shields.io/npm/v/agentclash?logo=npm&color=cb3837)](https://www.npmjs.com/package/agentclash)
[![npm downloads](https://img.shields.io/npm/dm/agentclash?logo=npm&color=cb3837)](https://www.npmjs.com/package/agentclash)
[![License: MIT](https://img.shields.io/github/license/agentclash/agentclash?color=blue)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/agentclash/agentclash?style=flat&logo=github)](https://github.com/agentclash/agentclash)

AgentClash is built for teams shipping agents, not leaderboard demos. It runs agents against the same workload with the same tools and constraints, then preserves the transcript, artifacts, replay, scorecard, and failure taxonomy that explain why an agent passed or failed.

<img width="1774" height="887" alt="AgentClash scorecard with overall score, comparison ranking, dimensions, and validators" src="https://github.com/user-attachments/assets/a8578daa-6a1e-4268-b1c9-5fef542d8ad7" />

## Start Here

| Goal | Best first step | Docs |
| --- | --- | --- |
| Run an eval | `agentclash eval start --follow` | [Quickstart](https://www.agentclash.dev/docs/getting-started/quickstart) |
| Author a workload | `agentclash challenge-pack init support-eval.yaml` | [Write a challenge pack](https://www.agentclash.dev/docs/guides/write-a-challenge-pack) |
| Gate CI | `agentclash ci init .agentclash/ci.yaml` | [CI/CD agent gates](https://www.agentclash.dev/docs/guides/ci-cd-agent-gates) |
| Use from an AI coding tool | `agentclash integration codex install` | [Use with AI tools](https://www.agentclash.dev/docs/guides/use-with-ai-tools) |
| Hack on the stack | `./scripts/dev/start-local-stack.sh` | [Self-host](https://www.agentclash.dev/docs/getting-started/self-host) |

## Quickstart

Install the CLI and connect a workspace:

```bash
npm i -g agentclash

export AGENTCLASH_API_URL="https://api.agentclash.dev"
agentclash auth login --device
agentclash link
agentclash doctor
```

Released npm binaries default to the hosted API. Keep the `AGENTCLASH_API_URL` export when you want to be explicit or switch between hosted and self-hosted environments.

If the workspace already has challenge packs and deployments, start an eval:

```bash
agentclash eval start --follow
agentclash eval scorecard
```

If the workspace is empty, scaffold and publish a pack first:

```bash
agentclash challenge-pack init support-eval.yaml
agentclash challenge-pack validate support-eval.yaml
agentclash challenge-pack publish support-eval.yaml
agentclash eval start --pack support-eval --follow
```

For a specific completed run, use the run-first scorecard command:

```bash
agentclash eval scorecard <run-id> --agent <agent-label-or-run-agent-id>
```

`agentclash run scorecard` is lower-level and expects a run-agent ID. Use `agentclash run agents <run-id>` when you need that ID directly.

## What You Can Evaluate

- **Challenge packs** package prompts, tools, sandboxes, input sets, validators, judges, expected artifacts, and scoring rules. Start with the [challenge pack reference](https://www.agentclash.dev/docs/challenge-packs).
- **Replay and scorecards** preserve the full trajectory: model calls, tool calls, sandbox commands, artifacts, verdicts, latency, cost, and failure evidence. See [interpreting results](https://www.agentclash.dev/docs/guides/interpret-results).
- **Regression suites** promote escaped failures into permanent checks so the same mistake is tested before future releases.
- **Datasets** import or curate pinned examples, run real agent evals, record baselines, sync regression suites, and gate CI. See [datasets overview](https://www.agentclash.dev/docs/guides/datasets-overview).
- **Multi-turn packs** support scripted, LLM-driven, and human user simulators with takeover commands for operator input. See [multi-turn packs](https://www.agentclash.dev/docs/challenge-packs/multi-turn).
- **Security evals** test prompt injection, secret hygiene, and sandbox or vault boundaries without copying real secrets into docs. See [security evaluation](https://www.agentclash.dev/docs/guides/security-evaluation).
- **Agent harnesses** run external coding agents such as Claude Code, Codex, OpenClaw, and Hermes as first-class eval candidates in sandboxes.

## CI And Release Gates

AgentClash can compare a candidate run against a baseline and fail CI when the candidate regresses.

```bash
agentclash ci init .agentclash/ci.yaml
agentclash ci validate .agentclash/ci.yaml --remote
agentclash ci run \
  --manifest .agentclash/ci.yaml \
  --json \
  --artifact-dir agentclash-artifacts
```

Use the bundled GitHub Action when you want PR comments and uploaded artifacts:

```yaml
- id: agentclash
  uses: agentclash/agentclash/.github/actions/agentclash-ci@main
  with:
    manifest: .agentclash/ci.yaml
    token: ${{ secrets.AGENTCLASH_TOKEN }}
    workspace: ${{ secrets.AGENTCLASH_WORKSPACE }}
```

`AGENTCLASH_TOKEN` is the automation token used by CI. `AGENTCLASH_WORKSPACE` is the workspace ID that should own the run and artifacts. For local CLI sessions, `agentclash link` can save the workspace; CI should pass both values explicitly through repository or organization secrets.

API URL resolution order is:

```text
--api-url > AGENTCLASH_API_URL > saved user config > default
```

Manifest gates, dataset gates, and release-gate policies are covered in [CI/CD agent gates](https://www.agentclash.dev/docs/guides/ci-cd-agent-gates) and [dataset CI gates](https://www.agentclash.dev/docs/guides/dataset-ci-gates).

## Agent Skills

AgentClash ships Agent Skills that teach coding agents how to use the CLI, read scorecards, author packs, and gate releases.

Install first-class integration skills with the CLI:

```bash
agentclash integration claude install
agentclash integration codex install
agentclash integration cursor install
agentclash integration claude doctor
```

Supported CLI integration hosts are `claude`, `codex`, `cursor`, `openclaw`, `hermes`, and `opencode`. GitHub CLI skill bundles for additional hosts are documented in [Use with AI tools](https://www.agentclash.dev/docs/guides/use-with-ai-tools).

## Local Development

AgentClash is a monorepo:

- `backend/` - Go API server and Temporal worker.
- `cli/` - Go CLI module published through the `agentclash` npm package.
- `web/` - Next.js marketing, app, and docs site.

Run CLI checks from `cli/`:

```bash
cd cli
go build ./...
go vet ./...
go test -short -race -count=1 ./...
```

For the full stack, start with [self-host](https://www.agentclash.dev/docs/getting-started/self-host), [local API development](docs/api-server/local-development.md), and the repo-specific guidance in [AGENTS.md](AGENTS.md).

## Project

- [Contributing](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Security policy](SECURITY.md)
- [CLI distribution](docs/cli-distribution.md)
- [License](LICENSE)

AgentClash is released under the [MIT License](LICENSE).

Makefile targets:
5:.PHONY: db-up db-down db-reset db-migrate db-seed db-psql api-server worker cli-skills-snapshot
7:db-up:
10:db-down:
13:db-reset:
17:db-migrate:
20:db-seed:
23:db-psql:
26:api-server:
29:worker:
36:cli-skills-snapshot:


## Issue body

Epic: #1088  
Roadmap order: **8 / 14**  
Depends on: #1092, #1093, #1095, #1096

## Goal

Ship runnable reference packs that prove the RAG eval stack works end to end and provide fixtures for CI, docs, demos, and regression tests.

## MVP packs

Ship these first:

| Slug | Tiers | Purpose |
|---|---|---|
| `rag-citation-required` | A | Evidence envelope, citation schema, retrieval hit |
| `rag-faithfulness-v2` | A+B | Grounded QA with citations and advisory judge metrics |
| `rag-abstention` | A+D | Unanswerable questions and refusal scoring |

## Full suite after MVP

| Slug | Tiers | Purpose |
|---|---|---|
| `rag-noisy-context` | D | MIRAGE-style mixed context |
| `rag-multi-hop` | A+B | Sequential retrieval and partial credit |
| `rag-claim-diagnostic` | C | Gold claims for RAGChecker-style attribution |

## Requirements per pack

- `eval_slice` on every case.
- Pinned corpus snapshot when using platform corpus; inline assets allowed for early fixture packs.
- Bad-agent fixtures that fail the expected dimension.
- Scorecard tier breakdown.
- Catalog metadata: category, difficulty, estimated cost.
- Builder/decompiler round-trip tests.

## Acceptance criteria

- [ ] MVP three packs pass catalog load and runnable tests.
- [ ] Each MVP pack fails a deliberately bad agent fixture on the expected dimension.
- [ ] At least one pack uses a real corpus snapshot once #1083/#1090 are available.
- [ ] Full six-pack suite is tracked but not required for the first CI gate.
- [ ] Docs explain which packs are fixture/demo vs benchmark-quality.
- [ ] Pack gallery does not imply public leaderboard validity before #1099.

## Blocks

#1102, #1101, #1099


## Comments



## Inventory excerpt

top files
.claude/skills/frontend-design/SKILL.md
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
.git/objects/pack/pack-e5e329c87a7f9c419ebdfa75e4a96e7360335645.idx
.git/objects/pack/pack-e5e329c87a7f9c419ebdfa75e4a96e7360335645.pack
.git/objects/pack/pack-e5e329c87a7f9c419ebdfa75e4a96e7360335645.promisor
.git/objects/pack/pack-e7d069d857c5232ffbb52fe41741584327a7c502.idx
.git/objects/pack/pack-e7d069d857c5232ffbb52fe41741584327a7c502.pack
.git/objects/pack/pack-e7d069d857c5232ffbb52fe41741584327a7c502.promisor
.git/ORIG_HEAD
.git/packed-refs
.git/refs/heads/main
.githooks/post-commit
.github/.release-please-manifest.json
.github/actions/agentclash-ci/action.yml
.github/actions/agentclash-ci/comment_test.py
.github/actions/agentclash-ci/comment.py
.github/actions/agentclash-ci/README.md
.github/actions/agentclash-ci/run_test.py
.github/actions/agentclash-ci/run.sh
.github/CODEOWNERS
.github/ISSUE_TEMPLATE/bug_report.md
.github/ISSUE_TEMPLATE/config.yml
.github/ISSUE_TEMPLATE/feature_request.md
.github/PULL_REQUEST_TEMPLATE.md
.github/release-please-config.json
.github/workflows/backend.yml
.github/workflows/cli-snapshot.yml
.github/workflows/cli.yml
.github/workflows/frontend.yml
.github/workflows/internal-agent-skills-harness.yml
.github/workflows/pr-review-bot.yml
.github/workflows/publish-skills.yml
.github/workflows/release-cli.yml
.github/workflows/release-please.yml
.github/workflows/roadmap-sync.yml
.github/workflows/runtime.yml
.gitignore
.opencode/opencode.json
AGENTS.md
architecture.md
backend/.env.example
backend/cmd/api-server/main.go
backend/cmd/worker/main.go
backend/db/migrations/00001_extensions_and_helpers.sql
backend/db/migrations/00002_identity_and_tenancy.sql
backend/db/migrations/00003_challenge_catalog.sql
backend/db/migrations/00004_provider_infrastructure.sql
backend/db/migrations/00005_agent_registry.sql
backend/db/migrations/00006_run_orchestration.sql
backend/db/migrations/00007_replay_and_scoring.sql
backend/db/migrations/00008_publication_and_arena.sql
backend/db/migrations/00009_hosted_run_executions.sql
backend/db/migrations/00010_scoring_result_uniqueness.sql
backend/db/migrations/00011_run_comparisons.sql
backend/db/migrations/00012_agent_spec_schema.sql
backend/db/migrations/00013_agent_spec_object_constraints.sql
backend/db/migrations/00014_run_comparison_release_gates.sql
backend/db/migrations/00015_challenge_pack_workspace_scope.sql
backend/db/migrations/00016_workspace_secrets.sql
backend/db/migrations/00017_playgrounds.sql
backend/db/migrations/00018_users_email_partial_unique.sql
backend/db/migrations/00019_fix_model_alias_unique_indexes.sql
backend/db/migrations/00020_scorecard_passed_column.sql
backend/db/migrations/00020_spend_tracking.sql
backend/db/migrations/00021_cli_auth.sql
backend/db/migrations/00021_llm_judge_results.sql
backend/db/migrations/00022_behavioral_score.sql
backend/db/migrations/00023_regression_suites.sql
backend/db/migrations/00024_regression_promotion_uniqueness.sql
backend/db/migrations/00025_run_regression_selection.sql
backend/db/migrations/00026_eval_sessions.sql
backend/db/migrations/00027_eval_session_results.sql
backend/db/migrations/00028_public_share_links.sql
backend/db/migrations/00029_race_context.sql
backend/db/migrations/00030_same_run_agent_comparisons.sql
backend/db/migrations/00031_billing_entitlements.sql
backend/db/migrations/00032_agent_harnesses.sql
backend/db/migrations/00033_agent_harness_executions.sql
backend/db/migrations/00034_agent_harness_execution_events.sql
backend/db/migrations/00035_github_app_installations.sql
backend/db/migrations/00036_billing_trial_grants.sql
backend/db/migrations/00036_run_ci_metadata.sql
backend/db/migrations/00037_regression_case_proposal_status.sql
backend/db/migrations/00038_scope_evaluation_spec_uniqueness.sql
backend/db/migrations/00039_agent_harness_claude_kind.sql
backend/db/migrations/00040_workspace_ci_profiles.sql
backend/db/migrations/00041_agent_harness_execution_run_bridge.sql
backend/db/migrations/00041_membership_invite_tokens.sql
backend/db/migrations/00042_agent_harness_suites.sql
backend/db/migrations/00043_agent_harness_execution_controls.sql
backend/db/migrations/00044_agent_harness_failure_annotations.sql
backend/db/migrations/00045_model_alias_pricing_snapshot.sql
backend/db/migrations/00046_workspace_public_packs.sql
backend/db/migrations/00047_multi_turn_human_calibration_arena.sql
backend/db/migrations/00048_runtime_execution_targets.sql
backend/db/migrations/00049_vibe_eval_drafts.sql
backend/db/migrations/00050_datasets.sql
backend/db/migrations/00051_dataset_evals.sql
backend/db/migrations/00052_dataset_traces.sql
backend/db/migrations/00053_dataset_ci_gates.sql
backend/db/migrations/00054_dataset_generation_jobs.sql
backend/db/migrations/00055_dataset_example_source_check.sql
backend/db/migrations/00056_agent_tryouts.sql
backend/db/migrations/00057_agent_tryout_parent_lineage.sql
backend/db/migrations/00058_agent_tryout_events.sql
backend/db/migrations/00059_agent_tryout_selected_harness.sql
backend/db/migrations/00060_agent_tryout_turns.sql
backend/db/migrations/00061_drop_model_aliases_catalog.sql
backend/db/migrations/00062_challenge_pieces.sql
backend/db/migrations/00063_challenge_pack_drafts.sql
backend/db/migrations/00064_llm_judge_results_single_model_confidence.sql
backend/db/queries/agent_builds.sql
backend/db/queries/agent_deployments.sql
backend/db/queries/agent_tryouts.sql
backend/db/queries/billing.sql
backend/db/queries/challenge_pack_drafts.sql
backend/db/queries/challenge_packs.sql
backend/db/queries/challenge_pieces.sql
backend/db/queries/dataset_evals.sql
backend/db/queries/dataset_gates.sql
backend/db/queries/dataset_generations.sql
backend/db/queries/dataset_traces.sql
backend/db/queries/datasets.sql
backend/db/queries/eval_sessions.sql
backend/db/queries/evaluation_specs.sql
backend/db/queries/hosted_runs.sql
backend/db/queries/llm_judge_results.sql
backend/db/queries/playgrounds.sql
backend/db/queries/regression_suites.sql
backend/db/queries/replay_reads.sql
backend/db/queries/run_agents.sql
backend/db/queries/run_comparisons.sql
backend/db/queries/run_creation.sql
backend/db/queries/run_events.sql
backend/db/queries/runs.sql
backend/db/queries/scoring_results.sql
backend/db/queries/vibe_eval.sql
backend/db/queries/worker_execution_context.sql
backend/Dockerfile
backend/Dockerfile.worker
backend/e2b-template/build.claude.dev.ts
backend/e2b-template/build.claude.prod.ts
backend/e2b-template/build.codex.dev.ts
backend/e2b-template/build.codex.prod.ts
backend/e2b-template/build.dev.ts
backend/e2b-template/build.hermes.dev.ts
backend/e2b-template/build.hermes.prod.ts
backend/e2b-template/build.openclaw.dev.ts
backend/e2b-template/build.openclaw.prod.ts
backend/e2b-template/build.prod.ts
backend/e2b-template/package-lock.json
backend/e2b-template/package.json
backend/e2b-template/template.ts
backend/e2b-template/tools/csv_to_json.py
backend/e2b-template/tools/http_request.py
backend/e2b-template/tools/json_query.py
backend/e2b-template/tools/pdf_extract.py
backend/go.mod
backend/go.sum
backend/internal/api/agent_build_templates_test.go
backend/internal/api/agent_build_templates.go
backend/internal/api/agent_builds_test.go
backend/internal/api/agent_builds.go
backend/internal/api/agent_deployments.go
backend/internal/api/agent_harnesses_test.go
backend/internal/api/agent_harnesses.go
backend/internal/api/agent_tryout_attachments_test.go
backend/internal/api/agent_tryout_attachments.go
backend/internal/api/agent_tryout_conversions_test.go
backend/internal/api/agent_tryout_conversions.go
backend/internal/api/agent_tryout_design_test.go
backend/internal/api/agent_tryout_design.go
backend/internal/api/agent_tryout_events_test.go
backend/internal/api/agent_tryout_events.go
backend/internal/api/agent_tryout_judge_test.go
backend/internal/api/agent_tryout_judge.go
backend/internal/api/agent_tryout_share_safety_test.go
backend/internal/api/agent_tryout_share_safety.go
backend/internal/api/agent_tryouts_prompt_test.go
backend/internal/api/agent_tryouts_test.go
backend/internal/api/agent_tryouts.go
backend/internal/api/artifacts_test.go
backend/internal/api/artifacts.go
backend/internal/api/auth_cli_token.go
backend/internal/api/auth_composite_test.go
backend/internal/api/auth_composite.go
backend/internal/api/auth_dev.go
backend/internal/api/auth_workos_test.go
backend/internal/api/auth_workos.go
backend/internal/api/auth.go
backend/internal/api/billing_test.go
backend/internal/api/billing.go
backend/internal/api/challenge_pack_builder_hydrate_test.go
backend/internal/api/challenge_pack_builder.go
backend/internal/api/challenge_pack_catalog_test.go
backend/internal/api/challenge_pack_catalog.go
backend/internal/api/challenge_packs_test.go
backend/internal/api/challenge_packs.go
backend/internal/api/challenge_piece_library.go
backend/internal/api/cli_auth_routes_test.go
backend/internal/api/cli_auth_test.go
backend/internal/api/cli_auth.go
backend/internal/api/compare_reads_test.go
backend/internal/api/compare_reads.go
backend/internal/api/compare_viewer.go
backend/internal/api/config_test.go
backend/internal/api/config.go
backend/internal/api/cors_test.go
backend/internal/api/cors.go
backend/internal/api/datasets_eval_test.go
backend/internal/api/datasets_gates_test.go
backend/internal/api/datasets_gates.go
backend/internal/api/datasets_generations_test.go
backend/internal/api/datasets_generations.go
backend/internal/api/datasets_import_test.go
backend/internal/api/datasets_regression_sync.go
backend/internal/api/datasets_traces_test.go
backend/internal/api/datasets_traces.go
backend/internal/api/datasets.go
backend/internal/api/eval_session_reads_test.go
backend/internal/api/eval_session_reads.go
backend/internal/api/eval_session_service.go
backend/internal/api/eval_sessions.go
backend/internal/api/failure_reviews_test.go
backend/internal/api/failure_reviews.go
backend/internal/api/github_integrations_test.go
backend/internal/api/github_integrations.go
backend/internal/api/health.go
backend/internal/api/hosted_runs_test.go
backend/internal/api/hosted_runs.go
backend/internal/api/infrastructure_manager_test.go
backend/internal/api/infrastructure_manager.go
backend/internal/api/infrastructure_test.go
backend/internal/api/infrastructure.go
backend/internal/api/invite_urls.go
backend/internal/api/list_pagination_test.go
backend/internal/api/list_pagination.go
backend/internal/api/middleware_test.go
backend/internal/api/middleware.go
backend/internal/api/multi_turn.go
backend/internal/api/onboarding.go
backend/internal/api/org_memberships_test.go
backend/internal/api/org_memberships.go
backend/internal/api/organizations.go
backend/internal/api/permissions_test.go
backend/internal/api/permissions.go
backend/internal/api/playgrounds.go
backend/internal/api/public_shares_test.go
backend/internal/api/public_shares.go
backend/internal/api/regression_suites_test.go
backend/internal/api/regression_suites.go
backend/internal/api/release_gates_regression.go
backend/internal/api/release_gates_test.go
backend/internal/api/release_gates.go
backend/internal/api/replay_reads_test.go
backend/internal/api/replay_reads.go
backend/internal/api/replay_viewer.go
backend/internal/api/respond.go
backend/internal/api/routes.go
backend/internal/api/run_events_sse_test.go
backend/internal/api/run_events_sse.go
backend/internal/api/run_ranking_insights_test.go
backend/internal/api/run_ranking_insights.go
backend/internal/api/run_ranking_test.go
backend/internal/api/run_ranking.go
backend/inte

## Grep excerpt

===== issue body =====
Epic: #1088  
Roadmap order: **8 / 14**  
Depends on: #1092, #1093, #1095, #1096

## Goal

Ship runnable reference packs that prove the RAG eval stack works end to end and provide fixtures for CI, docs, demos, and regression tests.

## MVP packs

Ship these first:

| Slug | Tiers | Purpose |
|---|---|---|
| `rag-citation-required` | A | Evidence envelope, citation schema, retrieval hit |
| `rag-faithfulness-v2` | A+B | Grounded QA with citations and advisory judge metrics |
| `rag-abstention` | A+D | Unanswerable questions and refusal scoring |

## Full suite after MVP

| Slug | Tiers | Purpose |
|---|---|---|
| `rag-noisy-context` | D | MIRAGE-style mixed context |
| `rag-multi-hop` | A+B | Sequential retrieval and partial credit |
| `rag-claim-diagnostic` | C | Gold claims for RAGChecker-style attribution |

## Requirements per pack

- `eval_slice` on every case.
- Pinned corpus snapshot when using platform corpus; inline assets allowed for early fixture packs.
- Bad-agent fixtures that fail the expected dimension.
- Scorecard tier breakdown.
- Catalog metadata: category, difficulty, estimated cost.
- Builder/decompiler round-trip tests.

## Acceptance criteria

- [ ] MVP three packs pass catalog load and runnable tests.
- [ ] Each MVP pack fails a deliberately bad agent fixture on the expected dimension.
- [ ] At least one pack uses a real corpus snapshot once #1083/#1090 are available.
- [ ] Full six-pack suite is tracked but not required for the first CI gate.
- [ ] Docs explain which packs are fixture/demo vs benchmark-quality.
- [ ] Pack gallery does not imply public leaderboard validity before #1099.

## Blocks

#1102, #1101, #1099

===== money/competition/judge hits =====
./CODE_OF_CONDUCT.md:9:We are committed to making participation in this project a harassment-free,
./CODE_OF_CONDUCT.md:11:identity. We expect all participants to be respectful, constructive, and
./CODE_OF_CONDUCT.md:26:Maintainers are responsible for clarifying and enforcing standards of acceptable
./infra/e2b/agentclash-tryout-office/README.md:5:`backend/internal/workflow/activities.go`
./infra/e2b/agentclash-tryout-office/e2b.Dockerfile:40:# Agent CLIs distributed via npm. Each --version is a build-time smoke test:
./infra/e2b/agentclash-tryout-office/e2b.Dockerfile:45:        @openai/codex@latest \
./infra/e2b/agentclash-tryout-office/e2b.Dockerfile:46:        @anthropic-ai/claude-code@latest \
./infra/e2b/agentclash-tryout-office/e2b.Dockerfile:47:        openclaw@latest \
./architecture.md:11:It is the implementation-facing architecture for AgentClash:
./architecture.md:15:- Private evaluation is the core value surface.
./architecture.md:17:- The system must support live execution, replay, scorecards, comparisons, and publication.
./architecture.md:30:AgentClash is a two-plane system. The `control plane` owns organizations, workspaces, challenges, agent definitions, runs, billing, publication, and UI-facing APIs. The `execution plane` owns long-running benchmark execution, sandbox provisioning, provider calls, tool execution, event generation, replay assembly, and scoring. The browser talks to a `Next.js` app and `Go` API server. The API server persists product state in `PostgreSQL`, starts durable `Temporal` workflows, and serves live updates over WebSockets. `Go` workers execute native and hosted agent runs, provision isolated sandboxes through `E2B` for native builds, persist large artifacts to `S3`, publish live events through `Redis`, compute scorecards, and materialize public snapshots when a run is published.
./architecture.md:38:Team data, prompts, provider credentials, traces, and challenge inputs are private unless explicitly published.
./architecture.md:49:- retrieval and memory behavior
./architecture.md:56:### 3.4 Fair benchmark execution
./architecture.md:60:- immutable challenge pack version
./architecture.md:62:- explicit runtime policy
./architecture.md:63:- persisted scorecard methodology
./architecture.md:71:The v1 architecture must be strong enough for serious product use without forcing early Kubernetes, Kafka, or many microservices.
./architecture.md:77:### 4.1 Canonical evaluation unit
./architecture.md:79:AgentClash evaluates:
./architecture.md:136:- app-router SSR and streaming are useful for replay and leaderboard pages
./architecture.md:145:- `Temporal Cloud` for workflows
./architecture.md:155:- Go is the better fit for orchestration-heavy, concurrent, infra-facing backend work
./architecture.md:180:- the hard problem is workflow durability, not very high-volume streaming
./architecture.md:215:The control plane owns product state and user-facing coordination:
./architecture.md:220:- challenge-pack catalog
./architecture.md:225:- publication workflow
./architecture.md:226:- leaderboard reads
./architecture.md:238:The execution plane owns benchmark execution:
./architecture.md:240:- workflow progression
./architecture.md:248:- scorecard generation
./architecture.md:268:- leaderboard and comparison pages
./architecture.md:273:- run benchmark logic
./architecture.md:275:- orchestrate workflows directly
./architecture.md:284:- run submission
./architecture.md:288:- read models for leaderboard and replay summaries
./architecture.md:302:- start run workflows
./architecture.md:317:- prepare challenge runtime
./architecture.md:323:- compute scorecards
./architecture.md:336:- hold temporary challenge workspace and file writes
./architecture.md:350:  /workflow             # Temporal workflows and activities
./architecture.md:351:  /provider             # provider adapters and policies
./architecture.md:354:  /scoring              # scorecards and validators
./architecture.md:420:### `challenge_packs`
./architecture.md:431:### `challenge_pack_versions`
./architecture.md:436:- `challenge_pack_id`
./architecture.md:439:- `scorecard_definition`
./architecture.md:440:- `leaderboard_policy`
./architecture.md:443:### `challenge_tasks`
./architecture.md:448:- `challenge_pack_version_id`
./architecture.md:467:### `tool_policies`
./architecture.md:536:- `challenge_pack_version_id`
./architecture.md:541:- `temporal_workflow_id`
./architecture.md:553:- `final_score`
./architecture.md:580:### `scorecards`
./architecture.md:586:- `scorecard_json`
./architecture.md:587:- `score_version`
./architecture.md:614:### `arena_submissions`
./architecture.md:620:- `challenge_pack_version_id`
./architecture.md:621:- `submission_status`
./architecture.md:624:### `leaderboard_entries`
./architecture.md:629:- `challenge_pack_version_id`
./architecture.md:634:- `score`
./architecture.md:645:- challenge metadata
./architecture.md:648:- scorecards
./architecture.md:651:- leaderboard materializations
./architecture.md:660:- challenge manifests and fixtures
./architecture.md:667:  challenge-packs/{pack_id}/{version}/...
./architecture.md:691:    participant User
./architecture.md:692:    participant Web as Next.js
./architecture.md:693:    participant API as API Server
./architecture.md:694:    participant DB as Postgres
./architecture.md:695:    participant TW as Temporal
./architecture.md:696:    participant WK as Worker
./architecture.md:697:    participant SB as E2B Sandbox
./architecture.md:698:    participant LLM as LLM Provider
./architecture.md:708:    WK->>DB: Persist state and scorecard
./architecture.md:713:1. User selects a workspace, challenge pack version, and one or more agent deployments.
./architecture.md:714:2. API server validates authz, plan limits, challenge visibility, and deployment compatibility.
./architecture.md:716:4. API starts a Temporal workflow and stores the workflow ID on the run.
./architecture.md:718:6. Worker uploads challenge assets and runtime metadata into the sandbox.
./architecture.md:725:9. Worker computes final scorecards and finalizes `run_agents`.
./architecture.md:734:- no AgentClash-managed sandbox is required unless the benchmark policy demands a proxy wrapper
./architecture.md:745:- AgentClash sends benchmark input
./architecture.md:755:  - `retrieval_hit`
./architecture.md:781:- provider credentials, private prompts, raw private traces, and tenant-specific artifacts never move into public objects
./architecture.md:795:- `retrieval_hit`
./architecture.md:813:- event schema versioning must be explicit
./architecture.md:828:- provider-specific errors
./architecture.md:844:Every challenge run should use an explicit tool policy that defines:
./architecture.md:863:- code patching or test running
./architecture.md:870:- challenge inputs mounted or uploaded per run
./architecture.md:889:Scoring should be challenge-pack-driven, not hardcoded globally.
./architecture.md:891:Every challenge pack version defines:
./architecture.md:894:- metric weights
./architecture.md:895:- score normalization
./architecture.md:896:- leaderboard eligibility
./architecture.md:906:- rule-specific metrics such as citation quality or test pass rate
./architecture.md:908:The scoring system should output both:
./architecture.md:910:- machine-readable structured scorecards
./architecture.md:921:- leaderboard entries
./architecture.md:933:### 16.2 Official vs community split
./architecture.md:935:Even if community submissions are added later, keep them distinct from official benchmark credibility.
./architecture.md:939:- `official`
./architecture.md:950:- `/v1/challenge-packs`
./architecture.md:955:- `/v1/scorecards`
./architecture.md:956:- `/v1/public/leaderboards`
./architecture.md:965:- `GET /v1/scorecards/{runAgentId}`
./architecture.md:982:- immutable challenge pack versions for auditability
./architecture.md:988:- sandbox outbound network disabled unless challenge policy allows it
./architecture.md:989:- all public content derived from explicit publication
./architecture.md:996:- metrics for API latency, queue depth, workflow failures, sandbox startup time, provider latency, run duration, replay generation time
./architecture.md:997:- traces across API submission to worker completion
./architecture.md:1003:- run failure rate by challenge pack
./architecture.md:1024:- Stripe test mode
./architecture.md:1025:- WorkOS test tenant
./architecture.md:1033:- autoscaling worker based on queue depth and workflow pressure
./architecture.md:1058:- add materialized leaderboard jobs
./architecture.md:1072:- evaluate self-managed runtime pools or Firecracker-based workers
./architecture.md:1075:## 22. Explicit Non-Goals
./architecture.md:1082:- user-authored workflow graph builder
./architecture.md:1083:- arbitrary custom challenge authoring for everyone
./architecture.md:1101:The most important architectural decision is not the exact framework list. It is the system boundary:
./try-cli/bun.lock:7:      "devDependencies": {
./try-cli/bun.lock:18:      "dependencies": {
./try-cli/bun.lock:25:      "dependencies": {
./try-cli/package.json:8:  "devDependencies": {
./try-cli/packages/core/package.json:9:  "dependencies": {
./try-cli/packages/cli/package.json:9:  "dependencies": {
./LICENSE:6:of this software and associated documentation files (the "Software"), to deal
./CITATION.cff:2:message: "If you use AgentClash in your research, please cite it as below."
./CITATION.cff:6:  real tasks with live scoring: sandboxed tools, replay, scorecards, and CI
./CITATION.cff:15:  - ai-agent-evaluation
./CITATION.cff:16:  - llm-evaluation
./CITATION.cff:17:  - agent-benchmark
./CITATION.cff:18:  - regression-testing
./CITATION.cff:19:  - eval
./web/pnpm-lock.yaml:10:    dependencies:
./web/pnpm-lock.yaml:12:        specifier: ^1.3.0
./web/pnpm-lock.yaml:15:        specifier: ^1.5.3
./web/pnpm-lock.yaml:18:        specifier: ^5.5.4
./web/pnpm-lock.yaml:21:        specifier: ^4.7.0
./web/pnpm-lock.yaml:24:        specifier: ^4.5.1
./web/pnpm-lock.yaml:27:        specifier: ^9.6.0
./web/pnpm-lock.yaml:30:        specifier: ^2.0.1
./web/pnpm-lock.yaml:33:        specifier: ^2.3.1
./web/pnpm-lock.yaml:36:        specifier: ^2.0.0
./web/pnpm-lock.yaml:39:        specifier: ^3.0.1
./web/pnpm-lock.yaml:42:        specifier: ^0.10.0
./web/pnpm-lock.yaml:45:        specifier: ^0.11.0
./web/pnpm-lock.yaml:48:        specifier: ^5.5.0
./web/pnpm-lock.yaml:51:        specifier: ^12.11.0
./web/pnpm-lock.yaml:54:        specifier: ^0.7.1
./web/pnpm-lock.yaml:57:        specifier: ^2.1.1
./web/pnpm-lock.yaml:60:        specifier: ^1.4.0
./web/pnpm-lock.yaml:63:        specifier: ^4.0.3
./web/pnpm-lock.yaml:65:      lucide-react:
./web/pnpm-lock.yaml:66:        specifier: ^0.577.0
./web/pnpm-lock.yaml:69:        specifier: ^15.5.15
./web/pnpm-lock.yaml:72:        specifier: ^6.0.0
./web/pnpm-lock.yaml:75:        specifier: ^1.376.3
./web/pnpm-lock.yaml:78:        specifier: 19.2.3
./web/pnpm-lock.yaml:81:        specifier: 19.2.3
./web/pnpm-lock.yaml:84:        specifier: ^16.1.1
./web/pnpm-lock.yaml:87:        specifier: ^4.0.1
./web/pnpm-lock.yaml:90:        specifier: ^6.9.4
./web/pnpm-lock.yaml:93:        specifier: ^4.2.0
./web/pnpm-lock.yaml:96:        specifier: ^2.0.7
./web/pnpm-lock.yaml:99:        specifier: ^2.4.1
./web/pnpm-lock.yaml:102:        specifier: ^3.5.0
./web/pnpm-lock.yaml:105:        specifier: ^0.184.0
./web/pnpm-lock.yaml:108:        specifier: ^1.4.0
./web/pnpm-lock.yaml:111:        specifier: ^4.1.7
./web/pnpm-lock.yaml:114:        specifier: ^4.3.6
./web/pnpm-lock.yaml:117:        specifier: ^5.0.12
./web/pnpm-lock.yaml:119:    devDependencies:
./web/pnpm-lock.yaml:121:        specifier: ^4
./web/pnpm-lock.yaml:124:        specifier: ^20
./web/pnpm-lock.yaml:127:        specifier: ^19
./web/pnpm-lock.yaml:130:        specifier: ^19
./web/pnpm-lock.yaml:133:        specifier: ^15.5.13
./web/pnpm-lock.yaml:136:        specifier: ^0.184.0
./web/pnpm-lock.yaml:139:        specifier: ^6.0.1
./web/pnpm-lock.yaml:142:        specifier: ^9
./web/pnpm-lock.yaml:145:        specifier: 16.1.7
./web/pnpm-lock.yaml:148:        specifier: ^29.0.2
./web/pnpm-lock.yaml:151:        specifier: ^4
./web/pnpm-lock.yaml:154:        specifier: ^5
./web/pnpm-lock.yaml:156:      vitest:
./web/pnpm-lock.yaml:157:        specifier: ^4.1.4
./web/pnpm-lock.yaml:171:    peerDependencies:
./web/pnpm-lock.yaml:177:    peerDependencies:
./web/pnpm-lock.yaml:191:    peerDependencies:
./web/pnpm-lock.yaml:197:    peerDependencies:
./web/pnpm-lock.yaml:228:    resolution: {integrity: sha512-T1NCJqT/j9+cn8fvkt7jtwbLBfLC/1y1c7NtCeXFRgzGTsafi68MRv8yzkYSapBnFA6L3U2VSc02ciDzoAJhJg==}
./web/pnpm-lock.yaml:250:    peerDependencies:
./web/pnpm-lock.yaml:268:    peerDependencies:
./web/pnpm-lock.yaml:282:    peerDependencies:
./web/pnpm-lock.yaml:313:    peerDependencies:
./web/pnpm-lock.yaml:319:    peerDependencies:
./web/pnpm-lock.yaml:325:    peerDependencies:
./web/pnpm-lock.yaml:331:    peerDependencies:
./web/pnpm-lock.yaml:337:    peerDependencies:
./web/pnpm-lock.yaml:359:    peerDependencies:
./web/pnpm-lock.yaml:363:    peerDependenciesMeta:
./web/pnpm-lock.yaml:370:    peerDependencies:
./web/pnpm-lock.yaml:376:    peerDependenciesMeta:
./web/pnpm-lock.yaml:382:    peerDependencies:
./web/pnpm-lock.yaml:386:    peerDependenciesMeta:
./web/pnpm-lock.yaml:392:    peerDependencies:
./web/pnpm-lock.yaml:396:    peerDependenciesMeta:
./web/pnpm-lock.yaml:402:    peerDependencies:
./web/pnpm-lock.yaml:406:    peerDependenciesMeta:
./web/pnpm-lock.yaml:420:  '@bramus/specificity@2.4.2':
./web/pnpm-lock.yaml:429:    peerDependencies:
./web/pnpm-lock.yaml:434:    resolution: {integrity: sha512-pqqKaeLB8R6BvyegcpI9gAyY6Xyx1bKYfWvIGOvIbTpguWyM1BBBVcT9DCeGe8Zw7Ujp5K56ci7isRUrT2Uadg==}
./web/pnpm-lock.yaml:458:    peerDependencies:
./web/pnpm-lock.yaml:465:    peerDependencies:
./web/pnpm-lock.yaml:472:    peerDependencies:
./web/pnpm-lock.yaml:477:    peerDependencies:
./web/pnpm-lock.yaml:479:    peerDependenciesMeta:
./web/pnpm-lock.yaml:495:    peerDependencies:
./web/pnpm-lock.yaml:500:    peerDependencies:
./web/pnpm-lock.yaml:506:    peerDependencies:
./web/pnpm-lock.yaml:512:    peerDependencies:
./web/pnpm-lock.yaml:518:    peerDependencies:
./web/pnpm-lock.yaml:525:  '@ecies/ciphers@0.2.6':
./web/pnpm-lock.yaml:528:    peerDependencies:
./web/pnpm-lock.yaml:529:      '@noble/ciphers': ^1.0.0
./web/pnpm-lock.yaml:545:    peerDependencies:
./web/pnpm-lock.yaml:572:    peerDependencies:
./web/pnpm-lock.yaml:575:    peerDependenciesMeta:
./web/pnpm-lock.yaml:593:    peerDependencies:
./web/pnpm-lock.yaml:645:    resolution: {integrity: sha512-TGbO26Yw2xsHzxtbVFGEXBFH0FRAP7gtcPE7P5yP7wGy7cXK2oO7RyOhL5NLiqTlBh47XhmIUXuGciXEqYFfBQ==}
./web/pnpm-lock.yaml:663:    resolution: {integrity: sha512-0y9KrdVnbMM2/vG8KfU0byhUN+EFCny9+8g202gYqSSVMonbsCfLjUO+rCci7pM0WBEtz+oK/PIwHkzxkyharA==}
./web/pnpm-lock.yaml:693:    resolution: {integrity: sha512-MsKncOcgTNvdtiISc/jZs/Zf8d0cl/t3gYWX8J9ubBnVOwlk65UIEEvgBORTiljloIWnBzLs4qhzPkJcitIzIg==}
./web/pnpm-lock.yaml:761:    peerDependencies:
./web/pnpm-lock.yaml:799:    peerDependencies:
./web/pnpm-lock.yaml:801:    peerDependenciesMeta:
./web/pnpm-lock.yaml:813:    peerDependencies:
./web/pnpm-lock.yaml:819:    peerDependencies:
./web/pnpm-lock.yaml:828:    peerDependencies:
./web/pnpm-lock.yaml:834:    peerDependencies:
./web/pnpm-lock.yaml:840:    peerDependencies:
./web/pnpm-lock.yaml:844:    resolution: {integrity: sha512-5DyQ4+1JEUzejeK1JGICcideyfUbGixgS9jNgex5nqkW+cY7WZhxBigmieN5Qnw9ZosSNVC9KQKyb+GUaGyKUA==}
./web/pnpm-lock.yaml:1029:    peerDependencies:
./web/pnpm-lock.yaml:1031:    peerDependenciesMeta:
./web/pnpm-lock.yaml:1038:    peerDependencies:
./web/pnpm-lock.yaml:1040:    peerDependenciesMeta:
./web/pnpm-lock.yaml:1047:    peerDependencies:
./web/pnpm-lock.yaml:1049:    peerDependenciesMeta:
./web/pnpm-lock.yaml:1056:    peerDependencies:
./web/pnpm-lock.yaml:1058:    peerDependenciesMeta:
./web/pnpm-lock.yaml:1065:    peerDependencies:
./web/pnpm-lock.yaml:1067:    peerDependenciesMeta:
./web/pnpm-lock.yaml:1074:    peerDependencies:
./web/pnpm-lock.yaml:1076:    peerDependenciesMeta:
./web/pnpm-lock.yaml:1083:    peerDependencies:
./web/pnpm-lock.yaml:1085:    peerDependenciesMeta:
./web/pnpm-lock.yaml:1092:    peerDependencies:
./web/pnpm-lock.yaml:1094:    peerDependenciesMeta:
./web/pnpm-lock.yaml:1109:    peerDependencies:
./web/pnpm-lock.yaml:1111:    peerDependenciesMeta:
./web/pnpm-lock.yaml:1118:    peerDependencies:
./web/pnpm-lock.yaml:1120:    peerDependenciesMeta:
./web/pnpm-lock.yaml:1127:    peerDependencies:
./web/pnpm-lock.yaml:1129:    peerDependenciesMeta:
./web/pnpm-lock.yaml:1136:    peerDependencies:
./web/pnpm-lock.yaml:1138:    peerDependenciesMeta:
./web/pnpm-lock.yaml:1145:    peerDependencies:
./web/pnpm-lock.yaml:1147:    peerDependenciesMeta:
./web/pnpm-lock.yaml:1154:    peerDependencies:
./web/pnpm-lock.yaml:1156:    peerDependenciesMeta:
./web/pnpm-lock.yaml:1163:    peerDependencies:
./web/pnpm-lock.yaml:1165:    peerDependenciesMeta:
./web/pnpm-lock.yaml:1172:    peerDependencies:
./web/pnpm-lock.yaml:1174:    peerDependenciesMeta:
./web/pnpm-lock.yaml:1181:    peerDependencies:
./web/pnpm-lock.yaml:1183:    peerDependenciesMeta:
./web/pnpm-lock.yaml:1217:    peerDependencies:
./web/pnpm-lock.yaml:1223:    peerDependencies:
./web/pnpm-lock.yaml:1231:    peerDependencies:
./web/pnpm-lock.yaml:1244:    peerDependencies:
./web/pnpm-lock.yaml:1258:    peerDependencies:
./web/pnpm-lock.yaml:1261:    peerDependenciesMeta:
./web/pnpm-lock.yaml:1270:    peerDependencies:
./web/pnpm-lock.yaml:1284:    peerDependencies:
./web/pnpm-lock.yaml:1346:  '@noble/ciphers@1.3.0':
./web/pnpm-lock.yaml:1351:    resolution: {integrity: sha512-gbKGcRUYIjA3/zCCNaWDciTMFI0dCkvou3TL8Zmy5Nc7sJ47a0jtOeZoTaMxkuqRo9cRhjOdZJXegxYE5FN/xw==}
./web/pnpm-lock.yaml:1394:    peerDependencies:
./web/pnpm-lock.yaml:1400:    peerDependencies:
./web/pnpm-lock.yaml:1406:    peerDependencies:
./web/pnpm-lock.yaml:1412:    peerDependencies:
./web/pnpm-lock.yaml:1418:    peerDependencies:
./web/pnpm-lock.yaml:1424:    peerDependencies:
./web/pnpm-lock.yaml:1430:    peerDependencies:
./web/pnpm-lock.yaml:1436:    peerDependencies:
./web/pnpm-lock.yaml:1439:  '@opentelemetry/sdk-metrics@2.2.0':
./web/pnpm-lock.yaml:1442:    peerDependencies:
./web/pnpm-lock.yaml:1448:    peerDependencies:
./web/pnpm-lock.yaml:1460:    peerDependencies:
./web/pnpm-lock.yaml:1512:    peerDependencies:
./web/pnpm-lock.yaml:1517:    peerDependenciesMeta:
./web/pnpm-lock.yaml:1525:    peerDependencies:
./web/pnpm-lock.yaml:1528:    peerDependenciesMeta:
./web/pnpm-lock.yaml:1534:    peerDependencies:
./web/pnpm-lock.yaml:1537:    peerDependenciesMeta:
./web/pnpm-lock.yaml:1543:    peerDependencies:
./web/pnpm-lock.yaml:1548:    peerDependenciesMeta:
./web/pnpm-lock.yaml:1556:    peerDependencies:
./web/pnpm-lock.yaml:1559:    peerDependenciesMeta:
./web/pnpm-lock.yaml:1565:    peerDependencies:
./web/pnpm-lock.yaml:1570:    peerDependenciesMeta:
./web/pnpm-lock.yaml:1578:    peerDependencies:
./web/pnpm-lock.yaml:1583:    peerDependenciesMeta:
./web/pnpm-lock.yaml:1591:    peerDependencies:
./web/pnpm-lock.yaml:1596:    peerDependenciesMeta:
./web/pnpm-lock.yaml:1604:    peerDependencies:
./web/pnpm-lock.yaml:1609:    peerDependenciesMeta:
./web/pnpm-lock.yaml:1617:    peerDependencies:
./web/pnpm-lock.yaml:1622:    peerDependenciesMeta:
./web/pnpm-lock.yaml:1630:    peerDependencies:
./web/pnpm-lock.yaml:1635:    peerDependenciesMeta:
./web/pnpm-lock.yaml:1643:    peerDependencies:
./web/pnpm-lock.yaml:1646:    peerDependenciesMeta:
./web/pnpm-lock.yaml:1652:    peerDependencies:
./web/pnpm-lock.yaml:1655:    peerDependenciesMeta:
./web/pnpm-lock.yaml:1661:    peerDependencies:
./web/pnpm-lock.yaml:1666:    peerDependenciesMeta:
./web/pnpm-lock.yaml:1674:    peerDependencies:
./web/pnpm-lock.yaml:1677:    peerDependenciesMeta:
./web/pnpm-lock.yaml:1683:    peerDependencies:
./web/pnpm-lock.yaml:1686:    peerDependenciesMeta:
./web/pnpm-lock.yaml:1692:    peerDependencies:
./web/pnpm-lock.yaml:1695:    peerDependenciesMeta:
./web/pnpm-lock.yaml:1701:    peerDependencies:
./web/pnpm-lock.yaml:1704:    peerDependenciesMeta:
./web/pnpm-lock.yaml:1710:    peerDependencies:
./web/pnpm-lock.yaml:1713:    peerDependenciesMeta:
./web/pnpm-lock.yaml:1719:    peerDependencies:
./web/pnpm-lock.yaml:1722:    peerDependenciesMeta:
./web/pnpm-lock.yaml:1728:    peerDependencies:
./web/pnpm-lock.yaml:1731:    peerDependenciesMeta:
./web/pnpm-lock.yaml:1737:    peerDependencies:
./web/pnpm-lock.yaml:1742:    peerDependenciesMeta:
./web/pnpm-lock.yaml:1757:    peerDependencies:
./web/pnpm-lock.yaml:1763:    peerDependencies:
./web/pnpm-lock.yaml:1769:    peerDependencies:
./web/pnpm-lock.yaml:1775:    peerDependencies:
./web/pnpm-lock.yaml:1781:    peerDependencies:
./web/pnpm-lock.yaml:1787:    peerDependencies:
./web/pnpm-lock.yaml:1793:    peerDependencies:
./web/pnpm-lock.yaml:1799:    peerDependencies:
./web/pnpm-lock.yaml:1806:    peerDependencies:
./web/pnpm-lock.yaml:1812:    peerDependencies:
./web/pnpm-lock.yaml:1818:    peerDependencies:
./web/pnpm-lock.yaml:1823:    resolution: {integrity: sha512-Q61IMR47piUBudgixJ30CciKIy9b1H95qe7GgEKOmSJVJXvFRWJllJfQry9tif+MX2cWFXWJf/RXz4kaCeq/Fg==}
./web/pnpm-lock.yaml:1824:    peerDependencies:
./web/pnpm-lock.yaml:1830:    peerDependencies:
./web/pnpm-lock.yaml:1836:    peerDependencies:
./web/pnpm-lock.yaml:1840:  '@rc-component/mini-decimal@1.1.3':
./web/pnpm-lock.yaml:1846:    peerDependencies:
./web/pnpm-lock.yaml:1853:    peerDependencies:
./web/pnpm-lock.yaml:1860:    peerDependencies:
./web/pnpm-lock.yaml:1866:    peerDependencies:
./web/pnpm-lock.yaml:1872:    peerDependencies:
./web/pnpm-lock.yaml:1879:    peerDependencies:
./web/pnpm-lock.yaml:1886:    peerDependenciesMeta:
./web/pnpm-lock.yaml:1899:    peerDependencies:
./web/pnpm-lock.yaml:1906:    peerDependencies:
./web/pnpm-lock.yaml:1912:    peerDependencies:
./web/pnpm-lock.yaml:1919:    peerDependencies:
./web/pnpm-lock.yaml:1926:    peerDependencies:
./web/pnpm-lock.yaml:1932:    peerDependencies:
./web/pnpm-lock.yaml:1938:    peerDependencies:
./web/pnpm-lock.yaml

