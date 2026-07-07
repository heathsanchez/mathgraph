# Recon Report

## Verdict

`PROMOTE_MONEY_RECON`

## Decision

JSON:
{
  "verdict": "PROMOTE_MONEY_RECON",
  "issue": {
    "url": "https://github.com/qurbaneliii/AI-Social-Media-Manager/issues/4",
    "title": "Frontend: GitHub Pages deployment fails due to static export constraints",
    "state": "OPEN",
    "labels": [],
    "comment_count": 0,
    "updatedAt": "2026-04-23T21:18:07Z"
  },
  "has_lean": false,
  "has_tests": true,
  "has_benchmark": true,
  "has_money": true,
  "has_surface": true,
  "risk": false
}

## Issue body excerpt

## Summary
GitHub Pages deployment for the frontend is failing intermittently due to Next.js static export incompatibilities with App Router API routes and dynamic route settings.

## Current behavior
- Build can fail with import resolution/type errors when API routes are moved incorrectly during Pages build.
- Static export fails when `app/api` is included.
- Dynamic route config can block export when not aligned with `output: export`.

## Expected behavior
Frontend should deploy reliably to GitHub Pages from `main` and publish the latest static build (`aria-frontend/out`) without manual intervention.

## Scope
- Stabilize Pages workflow for static export.
- Keep App Router API routes excluded from static export path safely.
- Ensure dynamic route configuration remains export-compatible.
- Add guardrails to avoid regressions in CI.

## Acceptance criteria
1. GitHub Pages workflow passes on push to `main`.
2. No `Cannot find module '@/app/api/ai/_lib'` errors in build logs.
3. Static export completes and uploads Pages artifact successfully.
4. Published site serves latest frontend version without 404 root error.


## Inventory excerpt

top files
.env.example
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
.git/ORIG_HEAD
.git/packed-refs
.github/workflows/deploy.yml
.github/workflows/frontend-ci.yml
.gitignore
.nojekyll
.vscode/launch.json
AI_ARCHITECTURE_AUDIT.md
AI_ARCHITECTURE.md
apps/audience-targeting/__init__.py
apps/audience-targeting/config.py
apps/audience-targeting/dependencies.py
apps/audience-targeting/Dockerfile
apps/audience-targeting/exceptions.py
apps/audience-targeting/main.py
apps/audience-targeting/requirements.txt
apps/audience-targeting/router.py
apps/caption-generation/__init__.py
apps/caption-generation/config.py
apps/caption-generation/dependencies.py
apps/caption-generation/Dockerfile
apps/caption-generation/exceptions.py
apps/caption-generation/main.py
apps/caption-generation/requirements.txt
apps/caption-generation/router.py
apps/content-analysis/__init__.py
apps/content-analysis/config.py
apps/content-analysis/dependencies.py
apps/content-analysis/Dockerfile
apps/content-analysis/exceptions.py
apps/content-analysis/main.py
apps/content-analysis/requirements.txt
apps/content-analysis/router.py
apps/hashtag-seo/__init__.py
apps/hashtag-seo/config.py
apps/hashtag-seo/dependencies.py
apps/hashtag-seo/Dockerfile
apps/hashtag-seo/exceptions.py
apps/hashtag-seo/main.py
apps/hashtag-seo/requirements.txt
apps/hashtag-seo/router.py
apps/scheduler/__init__.py
apps/scheduler/config.py
apps/scheduler/dependencies.py
apps/scheduler/Dockerfile
apps/scheduler/exceptions.py
apps/scheduler/main.py
apps/scheduler/requirements.txt
apps/scheduler/router.py
apps/time-optimization/__init__.py
apps/time-optimization/config.py
apps/time-optimization/dependencies.py
apps/time-optimization/Dockerfile
apps/time-optimization/exceptions.py
apps/time-optimization/main.py
apps/time-optimization/requirements.txt
apps/time-optimization/router.py
apps/visual-understanding/__init__.py
apps/visual-understanding/config.py
apps/visual-understanding/dependencies.py
apps/visual-understanding/Dockerfile
apps/visual-understanding/exceptions.py
apps/visual-understanding/main.py
apps/visual-understanding/requirements.txt
apps/visual-understanding/router.py
aria-frontend/.env.example
aria-frontend/.gitignore
aria-frontend/app/globals.css
aria-frontend/app/layout.tsx
aria-frontend/app/page.tsx
aria-frontend/app/providers.tsx
aria-frontend/config/constants.ts
aria-frontend/context/AuthContext.tsx
aria-frontend/Dockerfile
aria-frontend/hooks/useAuditLog.ts
aria-frontend/hooks/useCompanyPosts.ts
aria-frontend/hooks/useCountUp.ts
aria-frontend/hooks/useCreateSchedule.ts
aria-frontend/hooks/useDashboard.ts
aria-frontend/hooks/useDashboardFeed.ts
aria-frontend/hooks/useGenerate.ts
aria-frontend/hooks/useGeneratePost.ts
aria-frontend/hooks/useOnboardingStatus.ts
aria-frontend/hooks/usePostResult.ts
aria-frontend/hooks/usePresignUpload.ts
aria-frontend/hooks/useQualityCheck.ts
aria-frontend/hooks/useRequireAuth.ts
aria-frontend/hooks/useSaveDraftPost.ts
aria-frontend/lib/ai.ts
aria-frontend/lib/api.ts
aria-frontend/lib/auth-constants.ts
aria-frontend/lib/auth.ts
aria-frontend/lib/client-session.ts
aria-frontend/lib/isStatic.ts
aria-frontend/lib/mock-data.ts
aria-frontend/lib/mockData.ts
aria-frontend/lib/navigate.ts
aria-frontend/lib/openai.ts
aria-frontend/lib/prisma.ts
aria-frontend/lib/query-client.ts
aria-frontend/lib/role-routing.ts
aria-frontend/lib/store.ts
aria-frontend/lib/utils.ts
aria-frontend/lib/zod-schemas.ts
aria-frontend/middleware.ts
aria-frontend/next-env.d.ts
aria-frontend/next.config.js
aria-frontend/package-lock.json
aria-frontend/package.json
aria-frontend/postcss.config.mjs
aria-frontend/prisma/schema.prisma
aria-frontend/public/404.html
aria-frontend/scripts/seed.ts
aria-frontend/services/aiService.ts
aria-frontend/stores/useCompanyStore.ts
aria-frontend/stores/usePostStore.ts
aria-frontend/stores/useSchedulerStore.ts
aria-frontend/stores/useUIStore.ts
aria-frontend/tailwind.config.ts
aria-frontend/tsconfig.json
aria-frontend/types/index.ts
aria/.env.example
aria/.gitignore
aria/api/__init__.py
aria/api/analytics.py
aria/api/companies.py
aria/api/llm_proxy.py
aria/api/media.py
aria/api/oauth.py
aria/api/onboarding.py
aria/api/posts.py
aria/api/schedules.py
aria/app/cache.py
aria/app/main.py
aria/app/models.py
aria/app/providers.py
aria/app/router.py
aria/app/rules.py
aria/app/tasks.py
aria/app/vision.py
aria/db/__init__.py
aria/db/connection.py
aria/db/migrate.py
aria/docker-compose.yml
aria/Dockerfile
aria/flows/__init__.py
aria/flows/generation.py
aria/flows/onboarding.py
aria/flows/posting.py
aria/memory/__init__.py
aria/memory/feedback.py
aria/memory/learning.py
aria/memory/reembedder.py
aria/package.json
aria/pnpm-workspace.yaml
aria/prometheus.yml
aria/pyproject.toml
aria/README.md
aria/requirements.txt
aria/services/__init__.py
aria/services/brand_analysis.py
aria/services/context_assembly.py
aria/services/import_parser.py
aria/services/media.py
aria/services/oauth.py
aria/services/variant_scorer.py
aria/temporal/__init__.py
aria/temporal/worker.py
aria/turbo.json
deploy.ps1
docker-compose.yml
docs/full-system-architecture.md
git_deploy.py
git-deploy.bat
LICENSE
LOCAL_RUN_GUIDE.md
packages/decision-engine/__init__.py
packages/decision-engine/constants.py
packages/decision-engine/models.py
packages/decision-engine/requirements.txt
packages/prompt-templates/__init__.py
packages/prompt-templates/base.py
packages/prompt-templates/constants.py
packages/prompt-templates/repair.py
packages/prompt-templates/requirements.txt
packages/prompt-templates/validators.py
packages/types/__init__.py
packages/types/enums.py
packages/types/pyproject.toml
packages/types/requirements.txt
PHASE_2_IMPLEMENTATION_SUMMARY.md
PHASE_2_VERIFICATION_REPORT.md
PHASE_3_5_DATABASE_VERIFICATION.md
PHASE_3_IMPLEMENTATION_SUMMARY.md
PHASE_4_API_CONTRACTS.md
PHASE_4_IMPLEMENTATION_SUMMARY.md
PHASE_5_LIVE_DB_AND_APPROVAL_QUEUE_SUMMARY.md
PHASE_6_FRONTEND_APPROVAL_INTEGRATION_SUMMARY.md
PHASE_6_FRONTEND_INTEGRATION_AUDIT.md
PHASE_7_DETAIL_AND_REVIEW_UX_SUMMARY.md
PHASE_7_PRE_IMPLEMENTATION_AUDIT.md
PHASE_8_PRODUCT_AI_WORKSPACE_AUDIT.md
PHASE_8_PRODUCT_AI_WORKSPACE_SUMMARY.md
README.md
run-deploy.bat

build/test files
./aria-frontend/package.json
./aria/apps/api/package.json
./aria/apps/audience-targeting/pyproject.toml
./aria/apps/content-analysis/pyproject.toml
./aria/apps/dashboard/package.json
./aria/apps/hashtag-seo/pyproject.toml
./aria/apps/llm-orchestration/pyproject.toml
./aria/apps/scheduler/pyproject.toml
./aria/apps/time-optimization/pyproject.toml
./aria/apps/visual-understanding/pyproject.toml
./aria/package.json
./aria/packages/db/package.json
./aria/packages/decision-logic/pyproject.toml
./aria/packages/kafka-schemas/package.json
./aria/packages/platform-adapters/pyproject.toml
./aria/packages/prompt-templates/pyproject.toml
./aria/packages/python-contracts/pyproject.toml
./aria/packages/types/package.json
./aria/pyproject.toml
./aria/README.md
./packages/types/pyproject.toml
./README.md


## Grep excerpt

===== judge hits =====
./PHASE_2_VERIFICATION_REPORT.md:43:Prompts and workflows:
./PHASE_2_VERIFICATION_REPORT.md:49:- `aria/apps/llm-orchestration/app/ai/workflows/generate_content_package.py`
./PHASE_2_VERIFICATION_REPORT.md:50:- `aria/apps/llm-orchestration/app/ai/workflows/create_content_calendar.py`
./PHASE_2_VERIFICATION_REPORT.md:74:| `AIOrchestrator.generate_content_package` | Pass | Routes through content generator plus quality review workflow |
./PHASE_2_VERIFICATION_REPORT.md:98:- `aria/apps/llm-orchestration/app/ai/workflows/create_content_calendar.py` is still a placeholder wrapper. Runtime calendar generation is implemented through `AIOrchestrator.create_content_calendar` and `CalendarPlanningAgent`, and tests cover that path. A dedicated workflow wrapper can be added later if calendar orchestration becomes multi-step.
./PHASE_2_VERIFICATION_REPORT.md:118:& 'C:\Users\qurba\AppData\Local\Programs\Python\Python312\python.exe' -m pytest aria/apps/llm-orchestration/tests -q
./AI_ARCHITECTURE.md:17:- `workflows/`: end-to-end use-case composition. Phase 1 includes `GenerateContentPackageWorkflow`; Phase 2 keeps specialist orchestration thin and schema-first.
./AI_ARCHITECTURE.md:186:python -m pytest tests
./AI_ARCHITECTURE.md:221:5. Compose the agent inside `AIOrchestrator` or a workflow.
./AI_ARCHITECTURE.md:237:The primary frontend approval workflow is now available under `/dashboard/approval`, with focused content, calendar, community, and report queue routes.
./AI_ARCHITECTURE.md:254:Legacy direct-provider frontend helpers remain available for existing generator routes, but `app/api/ai/_lib.ts` and `lib/openai.ts` are marked deprecated for new approval workflow work. New approval UI code uses the centralized LLM orchestration service instead.
./AI_ARCHITECTURE.md:258:Phase 7 extends the approval workflow from queue-level review into safe detail review without exposing persistence internals.
./AI_ARCHITECTURE.md:293:- `ProductContext` defines ARIA as an AI Social Media Manager and Brand Manager with approval-based workflow mode.
./AI_ARCHITECTURE.md:294:- Supported capabilities include strategy, content generation, hashtag recommendation, visual concept generation, calendar planning, community management, reporting, competitor analysis, trend research, and approval workflow.
./PHASE_3_5_DATABASE_VERIFICATION.md:70:python -m pytest aria/apps/llm-orchestration/tests/test_phase_3_5_live_database.py -q
./PHASE_3_5_DATABASE_VERIFICATION.md:152:python -m pytest aria/apps/llm-orchestration/tests -q
./PHASE_3_5_DATABASE_VERIFICATION.md:166:python -m pytest aria/apps/llm-orchestration/tests/test_phase_3_5_live_database.py -q
./PHASE_3_5_DATABASE_VERIFICATION.md:197:python -m pytest aria/apps/llm-orchestration/tests/test_phase_3_5_live_database.py -q
./PHASE_4_IMPLEMENTATION_SUMMARY.md:137:python -m pytest aria/apps/llm-orchestration/tests -q
./PHASE_7_DETAIL_AND_REVIEW_UX_SUMMARY.md:5:Phase 7 hardened the approval-based AI Social Media Manager workflow with safe backend detail DTOs, typed detail routes, request-changes context, audit timeline support, a richer frontend detail review experience, and deployment-facing API/CORS/env checks.
./PHASE_7_DETAIL_AND_REVIEW_UX_SUMMARY.md:105:Still present outside approval workflow:
./PHASE_7_DETAIL_AND_REVIEW_UX_SUMMARY.md:111:These remain deprecated for new approval workflow work and should be migrated separately after compatibility tests exist.
./PHASE_7_DETAIL_AND_REVIEW_UX_SUMMARY.md:154:python -m pytest aria/apps/llm-orchestration/tests -q -rA
./PHASE_7_DETAIL_AND_REVIEW_UX_SUMMARY.md:206:3. Introduce an explicit revision/supersession model if draft editing or regeneration becomes part of the workflow.
./git_deploy.py:161:    deploy_workflow = Path(repo_path) / ".github" / "workflows" / "deploy.yml"
./git_deploy.py:162:    if deploy_workflow.exists():
./git_deploy.py:163:        print("✓ Deploy workflow found at: .github/workflows/deploy.yml")
./git_deploy.py:164:        with open(deploy_workflow) as f:
./git_deploy.py:165:            workflow_content = f.read()
./git_deploy.py:167:            if "main" in workflow_content:
./git_deploy.py:169:            if "aria-frontend" in workflow_content:
./git_deploy.py:171:            if "deploy-pages" in workflow_content:
./git_deploy.py:174:        print("✗ Deploy workflow NOT found")
./git_deploy.py:188:    print("  Workflow File:    .github/workflows/deploy.yml")
./aria-frontend/app/dashboard/scheduler/page.tsx:19:        <p className="text-sm text-[var(--text-secondary)]">Plan upcoming content in a calendar-focused workflow.</p>
./aria-frontend/app/api/ai/_lib.ts:1:// Deprecated for new approval workflows. New approval UI must use the
./aria-frontend/app/onboarding/company-profile/page.tsx:42:      brand_positioning_statement: "AI-powered social workflow automation for modern teams.",
./aria-frontend/app/onboarding/quality-check/page.tsx:117:          <p className="text-sm text-slate-600">Pass the quality threshold to unlock posting workflow.</p>
./aria-frontend/components/ai-workspace/AIWorkspacePanels.tsx:188:                Brand Brain has the required workflow context.
./aria-frontend/components/ai-workspace/AIWorkspacePanels.tsx:192:              <ErrorNotice message="AI workflows are using default/mock brand context until a real BrandProfile is saved." />
./aria-frontend/components/ai-workspace/AIWorkspacePanels.tsx:363:      <PageHeader title="Brand Brain" description="Configure brand-specific memory once. ARIA reuses it across every AI workflow." icon={Brain} />
./aria-frontend/components/ai-workspace/AIWorkspacePanels.tsx:427:        extra_context: { workflow: "phase_8_content_studio" }
./aria-frontend/components/ai-workspace/AIWorkspacePanels.tsx:484:  const [goal, setGoal] = useState("increase trust in approval-based AI workflows");
./aria-frontend/components/ai-workspace/AIWorkspacePanels.tsx:485:  const [competitors, setCompetitors] = useState("Manual spreadsheet workflow\nGeneric AI caption tool");
./aria-frontend/components/ai-workspace/AIWorkspacePanels.tsx:605:  const [goal, setGoal] = useState("differentiate ARIA's approval-based workflow");
./aria-frontend/components/ai-workspace/AIWorkspacePanels.tsx:606:  const [samples, setSamples] = useState("Generic AI caption tool | linkedin | Announces instant captions without review controls\nManual spreadsheet workflow | linkedin | Shows a calendar process but no AI assistance");
./aria-frontend/package-lock.json:671:      "integrity": "sha512-EriSTlt5OC9/7SXkRSCAhfSxxoSUgBm33OH+IkwbdpgoqsSsUg7y3uh+IICI/Qg4BBWr3U2i39RpmycbxMq4ew==",
./aria-frontend/package-lock.json:1000:      "integrity": "sha512-FMuvGijLDYG6lW+b/UvyilUWu5Ayu+3r2d1S8notiGCIyYU/76eig1UfMmkZ7vwgOrzKzlQbFSuQfgm7GYUPpA==",
./aria-frontend/package-lock.json:1370:      "integrity": "sha512-bRISgCIjP20/tbWSPWMEi54QVPRZExkuD9lJL+UIxUKtwVJA8wW1Trb1jMs1RFXo1CBTNZ/5hpC9QvmKWdopKw==",
./aria-frontend/package-lock.json:1491:      "integrity": "sha512-uRBo6THWei0chz+Y5j37qzx+BtoDRFIkDzZjlpCItBRXyMPIg079eIkOCl3aqr2tkxL4HFyJ4GHDes7W8HuAUg==",
./aria-frontend/package-lock.json:1867:      "integrity": "sha512-z4eqJvfiNnFMHIIvXP3CY57y2WJs5g2v3X0zm9mEJkrkNv4rDxu+sg9Jh8EkXyeqBkB7SOcboo9dMVqhyrACIg==",
./aria-frontend/package-lock.json:3948:      "integrity": "sha512-GsCCIZDE/p3i96vtEqx+7dBUGXrc7zeSK3wwPHIaRThS+9OhWIXRqzs4d6k1SVU8g91DrNRWxWUGhp5KXQb2VA==",
./aria-frontend/package-lock.json:4329:      "integrity": "sha512-fqtGgak3zX4DCB6PFpsH5+Kmt/8CIi4Bry4rb1ho6Av2QHTREM+47y282Uqiu3ZRF5IQioJQ5qWRV6jduA+iGw==",
./aria-frontend/package-lock.json:5654:      "integrity": "sha512-FGgH2h8zKNim9ljj7dankFPcICIK9Cp5bm+c2gQSYePhpaG5+esrLODihIorn+Pe6FGJzWhXQotPv73jTaldXA==",
./aria-frontend/package-lock.json:6210:      "integrity": "sha512-f3qQ9oQy9j2AhBe/H9VC91wLmKBCCU/gDOnKNAYG5hswO7BLKj09Hc5HYNz9cGI++xlpDCIgDaitVs03ATR84Q==",
./aria-frontend/package-lock.json:8979:      "integrity": "sha512-NlHwttCI/l5gCPR3D1nNXtWABUmBwvZpEQiD4IXSbIDq8BzLIK/7Ir5gTFSGZDUu37K5cMNp0hFtzO38sC7gWA==",
./aria-frontend/lib/openai.ts:3:// Deprecated for new approval workflows. Keep only for existing legacy routes
./aria-frontend/lib/api/ai-workspace.ts:4:  default_workflow_mode: string;
./aria-frontend/lib/api/ai-workspace.ts:315:  products_or_services: ["AI content workspace", "approval workflow"],
./aria-frontend/services/aiService.ts:273:        "Behind the scenes: our workflow for campaign quality",
./PHASE_3_IMPLEMENTATION_SUMMARY.md:112:- `aria/apps/llm-orchestration/app/ai/workflows/generate_content_package.py`
./PHASE_3_IMPLEMENTATION_SUMMARY.md:124:& 'C:\Users\qurba\AppData\Local\Programs\Python\Python312\python.exe' -m pytest aria/apps/llm-orchestration/tests -q
./PHASE_3_IMPLEMENTATION_SUMMARY.md:150:Phase 4 should focus on approved internal data ingestion for competitor, trend, reporting, and community workflows:
./PHASE_8_PRODUCT_AI_WORKSPACE_AUDIT.md:86:- `ContentGeneratorAgent` through the new backend workflow route
./PHASE_8_PRODUCT_AI_WORKSPACE_AUDIT.md:94:The frontend has mock brand profile cards and onboarding pages, but no active Brand Brain page that edits the backend `BrandProfile`, shows completeness, or warns when workflows are using mock/default brand context.
./git-deploy.bat:95:if exist .github\workflows (
./git-deploy.bat:96:    echo GitHub Actions workflows found:
./git-deploy.bat:97:    for /r .github\workflows %%F in (*.yml) do (
./docs/full-system-architecture.md:121:   3. Temporal workflow created with run_at_utc timers.
./docs/full-system-architecture.md:129:   1. If mode is human and not approved, workflow pauses and sends notification.
./docs/full-system-architecture.md:130:   2. If mode is auto or approved, workflow continues.
./docs/full-system-architecture.md:208:| Why | ACID consistency, rich indexing, mature RLS, strong JSONB support |
./PHASE_6_FRONTEND_INTEGRATION_AUDIT.md:126:- Existing frontend AI generation helpers remain present and should be deprecated for the approval workflow without breaking existing pages.
./README.md:7:AI Social Media Manager, also referred to as ARIA in the codebase, is a product-style AI application for content operations. It combines a Next.js frontend, Python/TypeScript service packages, LLM-assisted generation workflows, approval-oriented UX, scheduling logic, and deployment documentation.
./README.md:13:Social media workflows often spread strategy, copywriting, review, scheduling, and analytics across separate tools. This project explores a unified AI-assisted workspace where generated content remains constrained by brand rules, review states, platform context, and deterministic workflow logic.
./README.md:17:- Guided content-generation workflow for topic, platform, draft, review, refinement, and scheduling steps
./README.md:23:- Static GitHub Pages frontend deployment workflow for public demo access
./README.md:52:  api --> workflows["Temporal / scheduling workflows"]
./README.md:66:  .github/workflows/    GitHub Pages deployment
./README.md:129:| `TEMPORAL_ADDRESS` | Temporal service address for workflow-oriented components |
./README.md:167:- Keep only CI workflows that match the current app structure
./.gitignore:30:.pytest_cache/
./PHASE_2_IMPLEMENTATION_SUMMARY.md:91:python -m pytest aria\apps\llm-orchestration\tests -q
./aria/temporal/worker.py:2:# purpose: Temporal worker bootstrap registering onboarding and posting workflows with all required activities.
./aria/temporal/worker.py:3:# dependencies: os, asyncio, temporalio.client, temporalio.worker, temporal workflows
./aria/temporal/worker.py:13:from temporal.workflows.onboarding_workflow import (
./aria/temporal/worker.py:20:from temporal.workflows.posting_workflow import (
./aria/temporal/worker.py:38:        workflows=[PostingWorkflow, OnboardingWorkflow],
./aria/temporal/workflows/onboarding_workflow.py:1:# filename: temporal/workflows/onboarding_workflow.py
./aria/temporal/workflows/onboarding_workflow.py:2:# purpose: Temporal onboarding workflow coordinating tone/visual analysis, quality checks, and test post generation.
./aria/temporal/workflows/onboarding_workflow.py:3:# dependencies: datetime, temporalio.workflow, temporalio.activity, db.connection, flows.onboarding
./aria/temporal/workflows/onboarding_workflow.py:10:from temporalio import activity, workflow
./aria/temporal/workflows/onboarding_workflow.py:44:@workflow.defn
./aria/temporal/workflows/onboarding_workflow.py:46:    @workflow.run
./aria/temporal/workflows/onboarding_workflow.py:50:        a1 = workflow.start_activity(
./aria/temporal/workflows/onboarding_workflow.py:55:        a2 = workflow.start_activity(
./aria/temporal/workflows/onboarding_workflow.py:63:        qc = await workflow.execute_activity(
./aria/temporal/workflows/onboarding_workflow.py:76:        test_post = await workflow.execute_activity(
./aria/temporal/workflows/__init__.py:1:# filename: temporal/workflows/__init__.py
./aria/temporal/workflows/__init__.py:2:# purpose: Temporal workflows package exports.
./aria/temporal/workflows/__init__.py:3:# dependencies: posting_workflow, onboarding_workflow
./aria/temporal/workflows/__init__.py:5:from temporal.workflows.onboarding_workflow import OnboardingWorkflow
./aria/temporal/workflows/__init__.py:6:from temporal.workflows.posting_workflow import PostingWorkflow
./aria/temporal/workflows/posting_workflow.py:1:# filename: temporal/workflows/posting_workflow.py
./aria/temporal/workflows/posting_workflow.py:2:# purpose: Temporal posting workflow and activities for approval gating, publication, and failure handling.
./aria/temporal/workflows/posting_workflow.py:3:# dependencies: asyncio, uuid, datetime, temporalio.workflow, temporalio.activity, db.connection
./aria/temporal/workflows/posting_workflow.py:12:from temporalio import activity, workflow
./aria/temporal/workflows/posting_workflow.py:143:@workflow.defn
./aria/temporal/workflows/posting_workflow.py:145:    @workflow.run
./aria/temporal/workflows/posting_workflow.py:149:        schedule = await workflow.execute_activity(
./aria/temporal/workflows/posting_workflow.py:157:            await workflow.execute_activity(
./aria/temporal/workflows/posting_workflow.py:164:            publish_result = await workflow.execute_activity(
./aria/temporal/workflows/posting_workflow.py:175:            failure = await workflow.execute_activity(
./aria/temporal/__init__.py:2:# purpose: Temporal package marker and workflow exports.
./aria/temporal/__init__.py:3:# dependencies: temporal workflows
./aria/pyproject.toml:24:  "pytest==8.3.3",
./aria/pyproject.toml:25:  "pytest-asyncio==0.24.0"
./aria/pyproject.toml:28:[tool.pytest.ini_options]
./aria/README.md:32:5. Register the Temporal namespace used by workflows.
./aria/.gitignore:12:.pytest_cache/
./aria/packages/kafka-schemas/tests/contract.test.mjs:1:import { describe, it, expect } from "vitest";
./aria/packages/kafka-schemas/package.json:7:    "test": "vitest run"
./aria/packages/kafka-schemas/package.json:11:    "vitest": "^2.1.2"
./aria/packages/decision-logic/pyproject.toml:12:dev = ["pytest==8.3.3"]
./aria/db/migrations/001_schema.sql:18:  email CITEXT UNIQUE NOT NULL,
./aria/db/migrations/008_ai_approval_lifecycle.sql:63:  toxicity_risk DOUBLE PRECISION NOT NULL CHECK (toxicity_risk >= 0 AND toxicity_risk <= 1),
./aria/db/migrations/008_ai_approval_lifecycle.sql:64:  crisis_risk DOUBLE PRECISION NOT NULL CHECK (crisis_risk >= 0 AND crisis_risk <= 1),
./aria/db/migrations/008_ai_approval_lifecycle.sql:66:  confidence DOUBLE PRECISION NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
./aria/docker-compose.yml:2:# purpose: Local-first infrastructure stack for API, worker, data stores, streaming, workflow, and observability.
./aria/.env.example:67:# Temporal connection and queue settings for posting/onboarding workflows.
./aria/apps/scheduler/app/worker.py:28:from .workflows import PerformanceFeedbackWorkflow, PostGenerationWorkflow, PostPublishWorkflow
./aria/apps/scheduler/app/worker.py:36:        workflows=[PostGenerationWorkflow, PostPublishWorkflow, PerformanceFeedbackWorkflow],
./aria/apps/scheduler/app/workflows.py:4:from temporalio import workflow
./aria/apps/scheduler/app/workflows.py:7:with workflow.unsafe.imports_passed_through():
./aria/apps/scheduler/app/workflows.py:11:@workflow.defn
./aria/apps/scheduler/app/workflows.py:13:    @workflow.run
./aria/apps/scheduler/app/workflows.py:15:        validated = await workflow.execute_activity(
./aria/apps/scheduler/app/workflows.py:21:        parallel = await workflow.execute_activity(
./aria/apps/scheduler/app/workflows.py:29:            module_results = await workflow.execute_activity(
./aria/apps/scheduler/app/workflows.py:43:        scored = await workflow.execute_activity(
./aria/apps/scheduler/app/workflows.py:49:        delivered = await workflow.execute_activity(
./aria/apps/scheduler/app/workflows.py:58:@workflow.defn
./aria/apps/scheduler/app/workflows.py:60:    @workflow.run
./aria/apps/scheduler/app/workflows.py:62:        creds = await workflow.execute_activity(
./aria/apps/scheduler/app/workflows.py:68:        gate = await workflow.execute_activity(
./aria/apps/scheduler/app/workflows.py:85:            published = await workflow.execute_activity(
./aria/apps/scheduler/app/workflows.py:91:            confirmed = await workflow.execute_activity(
./aria/apps/scheduler/app/workflows.py:96:            scheduled = await workflow.execute_activity(
./aria/apps/scheduler/app/workflows.py:103:            dead = await workflow.execute_activity(
./aria/apps/scheduler/app/workflows.py:108:            notified = await workflow.execute_activity(
./aria/apps/scheduler/app/workflows.py:116:@workflow.defn
./aria/apps/scheduler/app/workflows.py:118:    @workflow.run
./aria/apps/scheduler/app/workflows.py:120:        await workflow.sleep(timedelta(hours=6))
./aria/apps/scheduler/app/workflows.py:122:        ingested = await workflow.execute_activity(
./aria/apps/scheduler/app/workflows.py:127:        scored = await workflow.ex

