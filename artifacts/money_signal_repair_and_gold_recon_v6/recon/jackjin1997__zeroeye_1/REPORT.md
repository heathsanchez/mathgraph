# Gold Recon Report

## Verdict

`PROMOTE_SMALL_PAID_RECON`

## Decision

```json
{
  "repo": "jackjin1997/zeroeye",
  "num": 1,
  "url": "https://github.com/jackjin1997/zeroeye/issues/1",
  "title": "[$30 BOUNTY] [Python] Expand backend API contract edge-case tests",
  "state": "OPEN",
  "updatedAt": "2026-06-30T23:25:23Z",
  "reason": "$30 Python pytest edge-case tests, small but judgeable",
  "amount_estimate": 30.0,
  "money": true,
  "local_judge": true,
  "benchmark_or_metric": true,
  "has_surface": true,
  "prompt_risk": false,
  "hardware_risk": false,
  "web3_risk": false,
  "verdict": "PROMOTE_SMALL_PAID_RECON"
}
```

## Issue body excerpt

**Bounty:** $30 (LT)

**Area:** `backend/api_contract.py` and `tests/backend_api/`

**Current state:** The backend API contract helpers have pytest coverage for the main happy path, but edge cases around malformed payloads, async wrappers, and error response shape still need focused tests.

**What is needed:** Extend the backend API contract test suite with deterministic negative cases and async wrapper coverage.

**Acceptance criteria:**
- Cover malformed or missing required fields returning a structured contract error.
- Cover async helper execution without requiring optional pytest plugins unless explicitly added.
- Cover response status/body assertions for at least two negative cases.
- Keep fixtures isolated so tests do not depend on network services.
- Update the test README or comments with the exact local command.

**Required validation:**
- Run `python3 -m pytest -q tests/backend_api` or the closest focused pytest command.
- Run `python3 build.py`.
- Include the generated `diagnostic/build-*.logd` artifact from `diagnostic/`; include the matching `diagnostic/build-*.json` if present.
- Use `.github/pull_request_template.md` for the submission.

## Cheap commands

```text
pwd=/Users/heath/Documents/mathgraph-lean-work/external/money_gold_recon_v6/jackjin1997__zeroeye_1

workflows:
.github/workflows/diagnostic-build-log.yml

```

## Inventory excerpt

```text
.git/config
.git/description
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
.git/objects/pack/pack-03bd8df14a8f46c67ee89870e8c667588574bb44.idx
.git/objects/pack/pack-03bd8df14a8f46c67ee89870e8c667588574bb44.pack
.git/objects/pack/pack-03bd8df14a8f46c67ee89870e8c667588574bb44.promisor
.git/objects/pack/pack-b36fbb37c0f7e9633a3765e96f7f8573580537b7.idx
.git/objects/pack/pack-b36fbb37c0f7e9633a3765e96f7f8573580537b7.pack
.git/objects/pack/pack-b36fbb37c0f7e9633a3765e96f7f8573580537b7.promisor
.git/packed-refs
.git/refs/heads/main
.git/shallow
.github/ISSUE_TEMPLATE/bug_report.yml
.github/ISSUE_TEMPLATE/config.yml
.github/ISSUE_TEMPLATE/feature_request.yml
.github/pull_request_template.md
.github/workflows/diagnostic-build-log.yml
.gitignore
ai_pipeline.sh
backend/Cargo.lock
backend/Cargo.toml
backend/src/ai/embeddings.rs
backend/src/ai/inference.rs
backend/src/ai/mod.rs
backend/src/config/mod.rs
backend/src/connector/bridge.rs
backend/src/connector/ffi.rs
backend/src/connector/legacy.rs
backend/src/connector/mod.rs
backend/src/connector/types.rs
backend/src/discovery/mod.rs
backend/src/legacy/deprecations.rs
backend/src/legacy/migrations.rs
backend/src/legacy/mod.rs
backend/src/legacy/v1_compat.rs
backend/src/lib.rs
backend/src/main.rs
backend/src/messaging/mod.rs
backend/src/protocol/codec.rs
backend/src/protocol/events.rs
backend/src/protocol/messages.rs
backend/src/protocol/mod.rs
backend/src/protocol/rpc.rs
backend/src/protocol/serialize.rs
backend/src/protocol/validate.rs
backend/src/registry/mod.rs
build.py
compliance/ComplianceAuditor.java
data/README.md
diagnostic/build-00000000.json
diagnostic/build-00000000.logd
docs/API_REFERENCE.md
docs/ARCHITECTURE.md
docs/CHANGELOG.md
docs/images/frame-handle.png
docs/openapi/deploy.tf
docs/openapi/Generate.hs
docs/openapi/Network/Wai.hs
docs/openapi/schema.sql
docs/openapi/Server.hs
docs/openapi/Types.hs
docs/openapi/v3.yaml
docs/openapi/Validate.hs
docs/OPERATIONS.md
docs/SECURITY.md
frailbox/connector/api.c
frailbox/connector/api.h
frailbox/connector/protocol.c
frailbox/connector/protocol.h
frailbox/connector/shim.c
frailbox/connector/shim.h
frailbox/engine_config.hpp
frailbox/engine.cpp
frailbox/engine.h
frailbox/engine/CMakeLists.txt
frailbox/engine/collision/collision.cpp
frailbox/engine/collision/collision.hpp
frailbox/engine/core/ecs.cpp
frailbox/engine/core/ecs.hpp
frailbox/engine/core/job_system.hpp
frailbox/engine/core/math.cpp
frailbox/engine/core/math.hpp
frailbox/engine/core/types.hpp
frailbox/engine/dynamics/constraint.cpp
frailbox/engine/dynamics/constraint.hpp
frailbox/engine/dynamics/rigidbody.cpp
frailbox/engine/dynamics/rigidbody.hpp
frailbox/engine/include/ai_controller.h
frailbox/engine/main.cpp
frailbox/engine/src/ai_controller.cpp
frailbox/include/arena.h
frailbox/include/logger.h
frailbox/include/sandbox.h
frailbox/main.c
frailbox/Makefile
frailbox/math_util.hpp
frailbox/nfc/scanner.lua
frailbox/render/camera.hpp
frailbox/render/pipeline.hpp
frailbox/src/arena.c
frailbox/src/logger.c
frailbox/src/sandbox.c
frailbox/tests/test_connector.c
frailbox/wat.cpp
frontend/index.html
frontend/package-lock.json
frontend/package.json
frontend/src/ai/chat.ts
frontend/src/ai/classifier.ts
frontend/src/ai/recommendations.ts
frontend/src/App.tsx
frontend/src/components/AssetSelector.tsx
frontend/src/components/Header.tsx
frontend/src/components/Layout.tsx
frontend/src/components/OrderBook.tsx
frontend/src/components/OrderHistory.tsx
frontend/src/components/PortfolioOverview.tsx
frontend/src/components/Sidebar.tsx
frontend/src/components/TradingChart.tsx
frontend/src/hooks/index.ts
frontend/src/hooks/useAiAssistant.ts
frontend/src/hooks/useMarketData.ts
frontend/src/hooks/useWebSocket.ts
frontend/src/main.tsx
frontend/src/pages/AdminPage.tsx
frontend/src/pages/Analytics.tsx
frontend/src/pages/Dashboard.tsx
frontend/src/pages/Settings.tsx
frontend/src/pages/TradePage.tsx
frontend/src/services/api.ts
frontend/src/services/auth.ts
frontend/src/services/telemetry.ts
frontend/src/store/index.ts
frontend/src/store/slices.ts
frontend/src/styles/legacy.css
frontend/src/types/index.ts
frontend/src/utils/dataService.ts
frontend/src/utils/dataTransforms.ts
frontend/src/utils/formatters.ts
frontend/src/utils/legacyCompat.ts
frontend/src/vite-env.d.ts
frontend/tsconfig.json
frontend/tsconfig.tsbuildinfo
frontend/vite.config.ts
market/ai/models.go
market/ai/predictor.go
market/ai/sentiment.go
market/analytics/collector.go
market/compliance/rules.go
market/gateway/api.go
market/gateway/middleware.go
market/go.mod
market/go.sum
market/main.go
market/matching/eng
```

## Grep excerpt

```text
===== money / judge / benchmark / test hits =====
./ai_pipeline.sh:102:    mkdir -p "$PROJECT_ROOT/metrics"
./ai_pipeline.sh:191:    log "INFO" "Running static analysis benchmark..."
./ai_pipeline.sh:224:    log "INFO" "Computing accuracy metrics..."
./ai_pipeline.sh:229:    cat << 'EVALREPORT' > "$PROJECT_ROOT/metrics/evaluation_${TIMESTAMP}.txt"
./ai_pipeline.sh:243:  - Sharpe Ratio (backtest): 1.24
./ai_pipeline.sh:260:    log "DONE" "Evaluation complete. Report saved to metrics/."
./ai_pipeline.sh:412:    log "INFO" "Metrics:    $PROJECT_ROOT/metrics/evaluation_${TIMESTAMP}.txt"
./tools/log_aggregator.py:22:which is fragile and breaks when log formats change. There's a test
./tools/log_aggregator.py:24:test suite has a 40% false pass rate because the test data was generated
./tools/log_aggregator.py:25:by the same parser code. The test data needs to be regenerated from
./tools/terraform_import.py:9:to use underscore-separated names for all resources managed through
./tools/terraform_import.py:87:    "aws_cloudwatch_metric_alarm",
./tools/openapi_pact.lua:6:--    -  The motto of Pact, a contract testing tool that Elena read about
./tools/openapi_pact.lua:10:--     this was the future of API testing. She wrote this Lua script to
./tools/openapi_pact.lua:18:-- This script generates Pact-style contract tests from an OpenAPI spec.
./tools/openapi_pact.lua:143:        symbol = "matching(term, 'BTC/USD')",
./tools/openapi_pact.lua:151:        symbol = "matching(term, 'BTC/USD')",
./tools/openapi_pact.lua:230:-- it to the product team. She has, however, written the contract test for it.
./tools/openapi_pact.lua:231:-- The contract test passes. There is no implementation. The contract test
./tools/openapi_pact.lua:232:-- is testing a dream. Elena is okay with this.
./tools/openapi_pact.lua:316:  -- Elena replaces spaces with underscores because file names with spaces
./tools/openapi_pact.lua:606:  print(GREEN .. "[Pact] Monad sat on the keyboard during testing." .. RESET)
./tools/deploy.py:6:including build, test, package, and deploy steps. It supports both
./tools/deploy.py:51:        "test_command": "cargo test --release",
./tools/deploy.py:62:        "test_command": "npm test",
./tools/deploy.py:73:        "test_command": "go test ./market/...",
./tools/deploy.py:84:        "test_command": "make -C frailbox test",
./tools/deploy.py:164:def test_service(service: str) -> bool:
./tools/deploy.py:170:    returncode, output = run_command(["sh", "-c", config["test_command"]], capture=True)
./tools/deploy.py:319:                   skip_build: bool = False, skip_test: bool = False,
./tools/deploy.py:325:    if not skip_test:
./tools/deploy.py:326:        if not test_service(service):
./tools/deploy.py:354:                          skip_build=True, skip_test=True, skip_health=False)
./tools/deploy.py:380:    parser.add_argument("--skip-test", action="store_true", help="Skip test step")
./tools/deploy.py:419:                  f"test={not args.skip_test}")
./tools/deploy.py:431:                                 args.skip_build, args.skip_test, args.skip_health)
./tools/benchmark.py:3:Performance benchmark tool for the Tent of Trials platform.
./tools/benchmark.py:7:WARNING: This benchmark tool is a LEGACY tool that was written for the
./tools/benchmark.py:10:this benchmark against the v2 API will produce unreliable results because
./tools/benchmark.py:13:The tool supports the following benchmark modes:
./tools/benchmark.py:18:  - spike: Sudden load spikes to test auto-scaling behavior
./tools/benchmark.py:22:or production benchmarks.
./tools/benchmark.py:24:TODO: The benchmark results are affected by the client-side rate limiter
./tools/benchmark.py:25:which is enabled by default. The rate limiter prevents the benchmark from
./tools/benchmark.py:27:of a load test. The rate limiter should be disabled during benchmarks but
./tools/benchmark.py:61:    benchmark_type: str
./tools/benchmark.py:184:def aggregate_results(results: List[LatencySample], benchmark_type: str,
./tools/benchmark.py:210:        benchmark_type=benchmark_type,
./tools/benchmark.py:238:def run_latency_benchmark(url: str, concurrency: int, request_count: int,
./tools/benchmark.py:240:    print(f"Running latency benchmark: {request_count} requests, {concurrency} concurrent")
./tools/benchmark.py:258:def run_throughput_benchmark(url: str, concurrency: int, duration: float,
./tools/benchmark.py:260:    print(f"Running throughput benchmark: {duration}s, {concurrency} concurrent, target {target_rps} RPS")
./tools/benchmark.py:281:def run_stress_benchmark(url: str, concurrency: int, max_rps: float,
./tools/benchmark.py:284:    print(f"Running stress benchmark: max {max_rps} RPS, step {step_rps}, {concurrency} concurrent")
./tools/benchmark.py:323:def run_soak_benchmark(url: str, concurrency: int, duration: float,
./tools/benchmark.py:325:    print(f"Running soak benchmark: {duration}s, {concurrency} concurrent, {target_rps} RPS")
./tools/benchmark.py:355:def run_spike_benchmark(url: str, concurrency: int, duration: float,
./tools/benchmark.py:359:    print(f"Running spike benchmark: {duration}s, spike at {spike_start}s for {spike_duration}s")
./tools/benchmark.py:385:    print(f"  Benchmark: {result.benchmark_type.upper()}")
./tools/benchmark.py:435:    str_p = subparsers.add_parser("stress", help="Stress test with ramp-up")
./tools/benchmark.py:442:    soak_p = subparsers.add_parser("soak", help="Soak test for memory leaks")
./tools/benchmark.py:447:    spike_p = subparsers.add_parser("spike", help="Spike test for auto-scaling")
./tools/benchmark.py:448:    spike_p.add_argument("--duration", type=float, default=120, help="Total test duration")
./tools/benchmark.py:463:        result = run_latency_benchmark(args.endpoint, args.concurrency, args.requests, args.timeout)
./tools/benchmark.py:465:        result = run_throughput_benchmark(args.endpoint, args.concurrency, args.duration, args.target_rps, args.timeout)
./tools/benchmark.py:467:        result = run_stress_benchmark(args.endpoint, args.concurrency, args.max_rps, args.step_rps, args.step_duration, args.error_threshold, args.timeout)
./tools/benchmark.py:469:        result = run_soak_benchmark(args.endpoint, args.concurrency, args.duration, args.target_rps, args.timeout)
./tools/benchmark.py:471:        result = run_spike_benchmark(args.endpoint, args.concurrency, args.duration, args.spike_start, args.spike_duration, args.normal_rps, args.spike_rps, args.timeout)
./tools/benchmark.py:478:                    "benchmark_type": result.benchmark_type,
./tools/db_migration.py:82:    {"version": "20210305000000", "description": "Create A/B test assignments", "type": "sql", "applied": False},
./tools/db_migration.py:102:    {"version": "20210505000000", "description": "Add user reputation score", "type": "sql", "applied": False},
./tools/openapi_diff.lua:178:    stability_score = calculate_stability(#diff.added, #diff.removed, #diff.changed),
./tools/openapi_diff.lua:188:-- Elena's stability score is a number between 0 and 100 that indicates
./tools/openapi_diff.lua:195:  local score = 100 - (added + removed + changed * 3) * 3
./tools/openapi_diff.lua:196:  return math.max(0, math.min(100, score))
./tools/openapi_diff.lua:202:-- Elena's vibe shift score describes how the "emotional character" of the
./tools/openapi_diff.lua:208:-- Elena has proposed adding this to the CI pipeline. The proposal is pending.
./tools/openapi_diff.lua:245:  print("  Stability score:     " .. diff.summary.stability_score .. "/100")
./tools/openapi_diff.lua:281:  if diff.summary.stability_score >= 90 then
./tools/openapi_diff.lua:284:  elseif diff.summary.stability_score >= 70 then
./tools/openapi_diff.lua:402:      stability_score = 100,
./tools/legacy_migration.py:35:to remove them because it would break the CI scripts that reference them.
./tools/legacy_migration.py:36:The CI scripts were also auto-generated and no one knows which ones exist.
./tools/legacy_migration.py:38:Ac
```
