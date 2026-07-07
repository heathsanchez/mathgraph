# Gold Recon Report

## Verdict

`PROMOTE_EXTERNAL_BENCHMARK_RECON`

## Decision

```json
{
  "repo": "treitforge/qsoripper",
  "num": 424,
  "url": "https://github.com/treitforge/qsoripper/issues/424",
  "title": "experiment: ingest Kaggle Morse Learning Machine Challenge v2 as external benchmark",
  "state": "OPEN",
  "updatedAt": "2026-05-09T03:03:14Z",
  "reason": "Kaggle external benchmark route; no cash but high MathGraph fit",
  "amount_estimate": 0.0,
  "money": false,
  "local_judge": true,
  "benchmark_or_metric": true,
  "has_surface": true,
  "prompt_risk": false,
  "hardware_risk": false,
  "web3_risk": false,
  "verdict": "PROMOTE_EXTERNAL_BENCHMARK_RECON"
}
```

## Issue body excerpt

## Summary

Ingest the [Kaggle Morse Learning Machine Challenge v2](https://www.kaggle.com/competitions/morse-learning-machine-challenge-v2) dataset as a **third external benchmark** alongside `training-set-a` (real OTA) and the adversarial synthetic suite (PR #417). Use it to (a) get a defensible external metric for our decoder, (b) cross-validate the `augment-arrl` (PR TBD) augmentation distributions, and (c) stress-test wider WPM range than our current suites cover.

## Dataset facts

- 200 WAV files, mono, 32-bit float, 8 kHz
- ~100 labeled (training, in `SampleSubmission.csv`); ~100 unlabeled (validation, scored via submission)
- Per-file randomization:
  - SNR: -14 to +20 dB
  - Pitch: 600 - 1200 Hz
  - Speed: 12 - 80 WPM
- Filename convention: `cw001.wav` ... `cw200.wav`
- Scoring metric: Levenshtein distance (== our CER, conveniently)

Reference baseline solution: https://github.com/talengu/kaggle_morse

## Why it matters

1. **External metric.** We have been grading our own homework on a 6-sample real OTA bench (training-set-a). The Kaggle leaderboard gives us a public, third-party number — useful for sanity checking and as a defensible "v1 done" signal.
2. **Augmentation distribution validation.** The competition's `(SNR ∈ [-14,+20], WPM ∈ [12,80], pitch ∈ [600,1200])` is exactly what `augment-arrl` is synthesizing. If our augmented corpus does not bracket the Kaggle distribution, our augmenter is mis-tuned. Cheap to check via histogram overlay.
3. **WPM stress test.** Our current bench tops out at 40 WPM. The Kaggle 50-80 WPM tail is something we never exercise. The two-pass WPM seed (PR #423) needs to be re-validated at high WPM since the bias-correction constants were tuned at 13-40 WPM.
4. **Independent overfitting check.** If we only optimize for training-set-a + adversarial-suite, we will silently overfit those distributions. Kaggle is held-out by construction.

## What this is NOT

- Not a training corpus. ~100 labeled files is too small for neural training. Our augmented ARRL corpus (~535 h, ~47k variants from `augment-arrl`) dwarfs it by 3+ orders of magnitude.
- Not "real world" — synthetic CW + AWGN, no Watterson channel, no QRM, no human fist variability. Beating Kaggle is necessary but not sufficient for OTA performance.
- Competition is closed (no prize), but the leaderboard still accepts submissions for scoring.

## Acceptance criteria

1. **Ingest pipeline**:
   - Script to download dataset (Kaggle CLI auth required) under `data/cw-samples/kaggle-morse-v2/` (gitignored).
   - Manifest at `experiments/cw-decoder/scripts/kaggle_morse_v2/manifest.jsonl` mapping file -> truth (where labeled).
   - Reuse the existing `bench.py` harness; emit per-file CER + aggregate stats.

2. **Baseline run**: Score current best (viterbi from PR #411 + wpm-seed-fix from PR #423) on the 100 labeled training samples. Report mean / median / p95 CER, broken down by SNR bucket and WPM bucket.

3. **Submission**: Generate a submission CSV from the 100 unlabeled validation samples and submit to the leaderboard. Capture the leaderboard score in the report.

4. **Distribution cross-validation** (depends on `augment-arrl` landing): overlay our augmented corpus distributions against Kaggle's per-file (SNR, WPM, pitch) statistics. Flag any mismatch.

5. **Regression check**: confirm the PR #423 wpm-seed-fix gate behaves correctly at high WPM (50-80). Specifically check:
   - Is the histogram bias correction (`frame_len + frame_step` ≈ 35 ms) still appropriate at 80 WPM dit length (~15 ms)?
   - Does the dit/dah concentration gate fire correctly when both clusters are sub-30 ms?

6. **Honest report** with:
   - Per-SNR-bucket CER table
   - Per-WPM-bucket CER table
   - Failure-mode analysis on the worst 10 files (paste decoded vs truth)
   - Comparison: our score vs published `talengu/kaggle_morse` baseline (CNN+LSTM, ~2018-era)
   - Recommendation: any concrete decoder changes needed to reduce the high-WPM or low-SNR error rate

## Sequencing

This depends on:
- PR #411 (viterbi) and PR #423 (wpm-seed-fix) merged so we have a stable best-of-bake-off baseline to evaluate
- `augment-arrl` (PR TBD) for the distribution cross-validation step

Can begin ingest + baseline run as soon as #411 and #423 land. Distribution check waits on `augment-arrl`.

## Risks

- **Kaggle ToS**: dataset license must be checked before redistributing or training models from it. Likely "competition use only" — that's fine for in-repo benchmarking, but flag for the LLM-repair experiment (#422) which would consume training pairs.
- **Kaggle CLI auth**: requires per-developer Kaggle API token. Document setup in the script.
- **Dataset is synthetic**: do not over-weight Kaggle results — they validate decoder robustness across SNR/WPM but tell us nothing about Watterson channel, QRM, or fist variation.

## Open design questions

1. Submit to the leaderboard? It's public and our score becomes visible. Probably yes — gives us a citation-grade ext

## Cheap commands

```text
pwd=/Users/heath/Documents/mathgraph-lean-work/external/money_gold_recon_v6/treitforge__qsoripper_424

package scripts:
{
  "ux:capture:web": "tsx scripts/capture-web.ts",
  "ux:diff:web": "tsx scripts/capture-web-diff.ts",
  "ux:drive:tui": "tsx scripts/drive-tui.ts"
}


workflows:
.github/workflows/copilot-setup-steps.yml
.github/workflows/dotnet-quality.yml
.github/workflows/engine-conformance.yml
.github/workflows/full-stack-quality.yml
.github/workflows/powershell-quality.yml
.github/workflows/rust-quality.yml
.github/workflows/win32-quality.yml

```

## Inventory excerpt

```text
.env.example
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
.git/objects/pack/pack-2d95a5778a4749fe86649be79519aedbb60034ee.idx
.git/objects/pack/pack-2d95a5778a4749fe86649be79519aedbb60034ee.pack
.git/objects/pack/pack-2d95a5778a4749fe86649be79519aedbb60034ee.promisor
.git/objects/pack/pack-e860f4f6365b5eef26d0cbb8bc1240f112647b07.idx
.git/objects/pack/pack-e860f4f6365b5eef26d0cbb8bc1240f112647b07.pack
.git/objects/pack/pack-e860f4f6365b5eef26d0cbb8bc1240f112647b07.promisor
.git/packed-refs
.git/refs/heads/main
.git/shallow
.gitattributes
.github/agents/code-reviewer.agent.md
.github/agents/implementer.agent.md
.github/agents/investigator.agent.md
.github/agents/planner.agent.md
.github/agents/security-auditor.agent.md
.github/agents/ui-reviewer.agent.md
.github/copilot-instructions.md
.github/hooks/copilot-policy.json
.github/hooks/scripts/post-build-check.ps1
.github/hooks/scripts/pre-tool-policy.ps1
.github/instructions/architecture.instructions.md
.github/instructions/copilot-customization.instructions.md
.github/instructions/integrations.instructions.md
.github/instructions/performance.instructions.md
.github/instructions/proto-contract.instructions.md
.github/instructions/rust.instructions.md
.github/instructions/security.instructions.md
.github/instructions/ui-ux.instructions.md
.github/prompts/debug-investigation.prompt.md
.github/prompts/feature-implementation.prompt.md
.github/prompts/qrz-integration.prompt.md
.github/prompts/rust-engine-change.prompt.md
.github/skills/adif-parsing/SKILL.md
.github/skills/analyzing-dotnet-performance/SKILL.md
.github/skills/avalonia-ui/SKILL.md
.github/skills/code-testing/SKILL.md
.github/skills/csharp-scripts/SKILL.md
.github/skills/directory-build-organization/SKILL.md
.github/skills/dotnet-aot-compat/SKILL.md
.github/skills/including-generated-files/SKILL.md
.github/skills/keyboard-first-ui/SKILL.md
.github/skills/logging-workflow/SKILL.md
.github/skills/qrz-lookup/SKILL.md
.github/skills/run-tests/SKILL.md
.github/skills/rust-api-and-idioms/SKILL.md
.github/skills/rust-clippy-and-lints/SKILL.md
.github/skills/rust-engine-workflow/SKILL.md
.github/skills/test-anti-patterns/SKILL.md
.github/skills/tonic-proto-contracts/SKILL.md
.github/skills/ux-inspection/SKILL.md
.github/workflows/copilot-setup-steps.yml
.github/workflows/dotnet-quality.yml
.github/workflows/engine-conformance.yml
.github/workflows/full-stack-quality.yml
.github/workflows/powershell-quality.yml
.github/workflows/rust-quality.yml
.github/workflows/win32-quality.yml
.gitignore
.mcp.json
bench.py
buf.yaml
build-and-test.ps1
build.ps1
cli.ps1
config/cathub.toml
coverage/05db5231-3b54-48b1-93c8-43a5e3d30608/coverage.cobertura.xml
coverage/0c3139b0-3aee-4392-9b57-87572697c172/coverage.cobertura.xml
coverage/0df21c42-b92a-488d-bf26-0441cc4dca5d/coverage.cobertura.xml
coverage/0e65a2a8-c240-4851-9066-39ded6468d9d/coverage.cobertura.xml
coverage/53c837f6-e198-4fe6-8a70-33d15c8c122c/coverage.cobertura.xml
coverage/62c4b8bf-826e-4691-8860-8d56ef977c1e/coverage.cobertura.xml
coverage/7704fe29-c62b-4ee8-bba9-777776d7e611/coverage.cobertura.xml
coverage/94b88f4c-2140-43bb-8b75-8e11e3bc9ea5/coverage.cobertura.xml
coverage/9c755ae1-6838-48da-ac67-207229b6e38b/coverage.cobertura.xml
coverage/9fba5c99-e29b-45e1-ae6d-dd6c923a943f/coverage.cobertura.xml
coverage/dc9684e5-3965-4162-8f38-41fda0895fca/coverage.cobertura.xml
coverage/e51dea7b-220e-4b94-bc92-d7761463fe4a/coverage.cobertura.xml
coverage/eeb5423f-e82f-410f-9ef9-cd6547d2fb2d/coverage.cobertura.xml
coverage/report/Summary.txt
data/contest-calendar/contest-details.json
docs/api/client-integration.md
docs/api/logbook-service.md
docs/api/lookup-service.md
docs/api/README.md
docs/api/setup-service.md
docs/api/station-profile-service.md
docs/api/workflows.md
docs/architecture/data-model.md
docs/architecture/engine-specification.md
docs/design/cathub-multi-client-cat-hub.md
docs/development/ui-inspection.md
docs/experiments/cw-decoder-bakeoff-2026-05.md
docs/experiments/kaggle-morse-v2-baseline-2026-05.md
docs/integrations/adif-specification.md
docs/integrations/cathub-setup.md
docs/integrations/qrz-logbook-api.md
docs/integrations/qrz-xml-lookup-api.md
docs/keyboard-shortcuts.md
experiment_report_seed_off.json
experiment_report_seed_on.json
experiment_report.json
EXPERIMENT_REPORT.md
experiments/cathub-frequency-probe-native/CMakeLists.txt
experiments/cathub-frequency-probe-native/main.cpp
experiments/cathub-frequency-probe-native/README.md
experiments/cathub-frequency-probe/app.manifest
experiments/cathub-frequency-probe/
```

## Grep excerpt

```text
===== money / judge / benchmark / test hits =====
./tools/ditdah-direct/Cargo.toml:15:name = "pin-wpm-test"
./tools/ditdah-direct/Cargo.toml:16:path = "pin_wpm_test.rs"
./tools/wpm-measure/main.rs:365:        ("symmetric 50/50  HIGH=0.50 LOW=0.50", 0.50, 0.50),
./tools/wpm-measure/main.rs:369:        ("symmetric 50     HIGH=0.50 LOW=0.50", 0.50, 0.50),
./tools/wpm-measure/main.rs:370:        ("symmetric 60     HIGH=0.60 LOW=0.60", 0.60, 0.60),
./tools/wpm-measure/main.rs:446:        // median of shortest 1/3 = (dot + intra-gap) ≈ 2*dot
./tools/wpm-measure/main.rs:450:        println!("  shortest-third median rising-edge interval = {:.2}ms",
./tools/corpus-sweep/pin_sweep.py:2:Sweep cw-decoder corpus at multiple pinned WPMs via the ditdah pin-wpm-test
./tools/corpus-sweep/pin_sweep.py:18:PIN_BIN = REPO / "tools" / "ditdah-direct" / "target" / "release" / "pin-wpm-test.exe"
./tools/corpus-sweep/pin_sweep.py:76:    pin-wpm-test prints `=== auto WPM ===` then text, then for each pin_wpm in
./tools/corpus-sweep/pin_sweep.py:147:        print(f"pin-wpm-test not built: {PIN_BIN}", file=sys.stderr)
./test.ps1:4:    Cross-platform test script for QsoRipper.
./test.ps1:7:    Runs the repository's automated test suites without the heavier build,
./test.ps1:11:    The test command to run. Default: all.
./test.ps1:14:    Build configuration for .NET and Win32 test runs. Default: Debug.
./test.ps1:17:    CMake generator for local Win32 tests. Default: Visual Studio 18 2026.
./test.ps1:20:    ./test.ps1
./test.ps1:21:    ./test.ps1 dotnet
./test.ps1:22:    ./test.ps1 win32 -Configuration Release
./test.ps1:41:$Win32BuildDir = Join-Path $PSScriptRoot 'build' 'win32-tests'
./test.ps1:42:$PesterTestsDir = Join-Path $PSScriptRoot 'tests'
./test.ps1:43:$EngineConformanceScript = Join-Path $PSScriptRoot 'tests' 'Run-EngineConformance.ps1'
./test.ps1:173:        if ($line -match 'test result:\s+\w+\.\s+(?<passed>\d+) passed;\s+(?<failed>\d+) failed;\s+(?<ignored>\d+) ignored;') {
./test.ps1:196:function Get-CtestCounts([string[]]$Lines) {
./test.ps1:198:        if ($line -match '(?<failed>\d+) tests failed out of (?<total>\d+)') {
./test.ps1:282:    Invoke-TestStepWithCounts 'Rust tests' cargo @('test', '--manifest-path', $RustManifest) 'Rust' ${function:Get-RustTestCounts}
./test.ps1:286:    Invoke-TestStepWithCounts ".NET tests ($Configuration)" dotnet @('test', $DotnetSolution, '-c', $Configuration) '.NET' ${function:Get-DotnetTestCounts}
./test.ps1:291:        Write-Step 'Win32 tests'
./test.ps1:292:        Write-Host 'Win32 tests require Windows; skipping on this platform.' -ForegroundColor Yellow
./test.ps1:298:        Write-Step 'Win32 tests'
./test.ps1:304:        Write-Step 'Win32 tests'
./test.ps1:309:    Measure-TestStep "Configuring Win32 tests ($Win32Generator)" {
./test.ps1:313:    Invoke-TestStep "Building Win32 tests ($Configuration)" cmake @(
./test.ps1:319:    Invoke-TestStepWithCounts "Running Win32 CTest ($Configuration)" ctest @(
./test.ps1:320:        '--test-dir', $Win32BuildDir,
./test.ps1:323:    ) 'Win32' ${function:Get-CtestCounts}
./test.ps1:329:        Write-Step 'Pester tests'
./test.ps1:330:        Write-Host 'Pester not installed; skipping PowerShell tests. Install-Module Pester -Scope CurrentUser' -ForegroundColor Yellow
./test.ps1:335:    Measure-TestStep 'Pester tests' {
./test.ps1:398:Usage: ./test.ps1 [command] [-Configuration Release|Debug] [-Win32Generator <generator>]
./test.ps1:401:  all       Run Rust, .NET, Win32, Pester, and engine conformance tests (default)
./test.ps1:402:  rust      Run Rust workspace tests
./test.ps1:403:  dotnet    Run .NET solution tests
./test.ps1:404:  win32     Configure, build, and run Win32 CTest tests
./test.ps1:405:  pester    Run PowerShell/Pester tests under tests/
./test.ps1:410:  ./test.ps1
./test.ps1:411:  ./test.ps1 dotnet -Configuration Release
./test.ps1:412:  ./test.ps1 win32
./proto/domain/qsl_status.proto:9:  QSL_STATUS_UNSPECIFIED = 0;
./proto/domain/rig_connection_status.proto:9:  RIG_CONNECTION_STATUS_UNSPECIFIED = 0;
./proto/domain/contest_calendar_status.proto:7:enum ContestCalendarStatus {
./proto/domain/contest_calendar_status.proto:8:  CONTEST_CALENDAR_STATUS_UNSPECIFIED = 0;
./proto/domain/space_weather_status.proto:8:  SPACE_WEATHER_STATUS_UNSPECIFIED = 0;
./proto/domain/qso_history_entry.proto:18://   - Future contest-mode dupe checks: (band, mode, contest_id) covers every
./proto/domain/qso_history_entry.proto:19://     common contest dupe rule, and contest_id distinguishes current-contest
./proto/domain/qso_history_entry.proto:20://     contacts from past contacts. Contest mode is not implemented yet; this
./proto/domain/qso_history_entry.proto:45:  // Contest identifier for the contact, when logged in a contest. Empty for
./proto/domain/qso_history_entry.proto:46:  // non-contest QSOs. Used by future contest-mode dupe logic to differentiate
./proto/domain/qso_history_entry.proto:47:  // current-contest dupes from past-contest history.
./proto/domain/qso_history_entry.proto:48:  optional string contest_id = 8;
./proto/domain/contest_calendar_entry.proto:8:import "domain/contest_details_status.proto";
./proto/domain/contest_calendar_entry.proto:12:message ContestCalendarEntry {
./proto/domain/contest_calendar_entry.proto:13:  string contest_id = 1;
./proto/domain/contest_calendar_entry.proto:23:  ContestDetailsStatus details_status = 11;
./proto/domain/conflict_policy.proto:12:  CONFLICT_POLICY_UNSPECIFIED = 0;
./proto/domain/callsign_ambiguity.proto:9:  CALLSIGN_AMBIGUITY_UNSPECIFIED = 0;
./proto/domain/band.proto:9:  BAND_UNSPECIFIED = 0;
./proto/domain/geo_source.proto:10:  GEO_SOURCE_UNSPECIFIED = 0;
./proto/domain/qso_completion.proto:10:  QSO_COMPLETION_UNSPECIFIED = 0;  // No value present in source ADIF.
./proto/domain/qso_record.proto:65:  // --- Contest fields ---
./proto/domain/qso_record.proto:66:  optional string contest_id = 50;
./proto/domain/qso_record.proto:117:  // Receiver band when running split. Defaults to BAND_UNSPECIFIED if absent.
./proto/domain/qso_record.proto:145:  // This is an intentionally lossy "latest snapshot" cache. A future
./proto/domain/modifier_kind.proto:9:  MODIFIER_KIND_UNSPECIFIED = 0;
./proto/domain/contest_details_status.proto:7:enum ContestDetailsStatus {
./proto/domain/contest_details_status.proto:8:  CONTEST_DETAILS_STATUS_UNSPECIFIED = 0;
./proto/domain/mode.proto:10:  MODE_UNSPECIFIED = 0;
./proto/domain/lookup_state.proto:12:  LOOKUP_STATE_UNSPECIFIED = 0;  // Default/zero value — should not appear in normal responses
./proto/services/stress_vector_state.proto:8:  STRESS_VECTOR_STATE_UNSPECIFIED = 0;
./proto/services/test_qrz_logbook_credentials_response.proto:10:  // Human-readable error message when the test failed.
./proto/services/lookup_service.proto:47:  // Batch lookup for prefetch/contest scenarios. Returns one LookupResult per callsign,
./proto/services/lookup_service.proto:48:  // in request order. Useful for warming the cache before a contest session begins.
./proto/services/list_qsos_request.proto:19:  optional string contest_id = 6;
./proto/services/runtime_config_value_kind.proto:8:  RUNTIME_CONFIG_VALUE_KIND_UNSPECIFIED = 0;
./proto/services/stress_run_state.proto:8:  STRESS_RUN_STATE_UNSPECIFIED = 0;
./proto/services/refresh_contest_calendar_response.proto:7:import "domain/contest_calendar_entry.proto";
./proto/services/refresh_contest_calendar_response.proto:8:import "domain/contest_calendar_status.proto";
./proto/services/refresh_contest_calendar_response.proto:11:message RefreshContestCalendarResponse {
./proto/services/refresh_contest_calendar_response.proto:12:  repeated qsoripper.domain.ContestCalendarEntry contests = 1;
./proto/services/refresh_contest_calendar_response.proto:13:  qsoripper.domain.ContestCalendarStatus status = 2;
./proto/services/deleted_records_filter.proto:8:// Default (UNSPECIFIED) is treated as ACTIVE_ONLY so existing callers keep
./proto/services/deleted_records_filter.proto:11: 
```
