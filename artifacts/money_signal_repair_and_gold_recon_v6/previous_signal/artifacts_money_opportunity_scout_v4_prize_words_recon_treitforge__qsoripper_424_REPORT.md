# Prize Recon Report

## Verdict

`PARK_RISK`

## Decision

JSON:
{
  "verdict": "PARK_RISK",
  "issue": {
    "url": "https://github.com/treitforge/qsoripper/issues/424",
    "title": "experiment: ingest Kaggle Morse Learning Machine Challenge v2 as external benchmark",
    "state": "OPEN",
    "labels": [],
    "comment_count": 0,
    "updatedAt": "2026-05-09T03:03:14Z"
  },
  "money": true,
  "competition": true,
  "judge": true,
  "local": true,
  "mgfit": true,
  "risk": true
}

## Cheap commands

pwd=/Users/heath/Documents/mathgraph-lean-work/external/money_opportunity_scout_v4_prize_words/treitforge__qsoripper_424

README head:
# QsoRipper

High-performance ham radio logging platform built around shared gRPC/protobuf contracts, interchangeable engine hosts, and keyboard-first clients.

## Architecture

QsoRipper is a **gRPC/protobuf-first** project. The stable core is the contract in `proto/`, not any single process implementation. An engine host implements those services. A client consumes them. Because both sides meet at the same protobuf/gRPC seam, engines and clients can be mixed and matched across languages without changing the contract.

```
┌─────────────────────────────────────────────┐
│ Clients                                     │
│ Rust TUI | .NET CLI/GUI/DebugHost | Web | ... │
└──────────────────┬──────────────────────────┘
                   │ gRPC + protobuf
┌──────────────────▼──────────────────────────┐
│ Shared contracts in proto/                  │
│ EngineService, SetupService, LookupService, │
│ LogbookService, StationProfileService, ...  │
└──────────────────┬──────────────────────────┘
         ┌─────────┴─────────┐
         ▼                   ▼
┌─────────────────┐  ┌────────────────────┐
│ Rust engine     │  │ .NET engine        │
│ rust-tonic      │  │ dotnet-aspnet      │
└─────────────────┘  └────────────────────┘
```

The repository currently ships two engine hosts behind the same contracts:

- **Rust engine (`rust-tonic`)** for the main engine/runtime implementation
- **.NET engine (`dotnet-aspnet`)** as a second real host proving the contract is not Rust-only

It also ships multiple clients on top of that seam: the Rust TUI plus the .NET CLI, GUI, and DebugHost. Nothing in the contract privileges a specific engine language or client stack.

### Engine and client decoupling

Any engine implementation only needs to satisfy the shared service contracts. Any client implementation only needs a gRPC client. Examples of swappable pieces:

- A **Rust** or **.NET** engine host today, with room for future Go, Java, or other implementations.
- A **terminal UI** built with ratatui, crossterm, or any TUI library in any language.
- A **native desktop GUI** using Avalonia, WPF, Win32, GTK, Qt, or similar.
- A **web UI**, **mobile app**, or **CLI tool**.
- Multiple clients can run simultaneously against the same engine instance.

No engine host or client is privileged. The protobuf/gRPC contract is the only shared interface.

### Protocol Buffers

Proto files under `proto/` are the **single source of truth** for all shared types (`QsoRecord`, `CallsignRecord`, `LookupResult`, bands, modes, etc.). Code can be generated for any consuming language -- zero hand-duplicated types:

- **Rust** (engine): `prost` + `tonic-build` generate structs and gRPC server stubs
- **Any client language**: standard protobuf/gRPC tooling generates client stubs (e.g., `Grpc.Tools` for C#, `protoc-gen-go` for Go, `grpc-web` for browsers)
- **Schema quality**: `buf lint` and `buf breaking` enforce conventions and backward compatibility
- **Contract shape**: protobuf 1-1-1 is the default — one top-level entity per file, service files that contain only the `service`, and unique `XxxRequest` / `XxxResponse` envelopes for every RPC

### gRPC Services

| Service | Purpose |
|---|---|
| **EngineService** | Engine identity, version, and capability discovery |
| **SetupService** | First-run and shared engine settings, persisted config status, bootstrap storage/station defaults |
| **StationProfileService** | Persisted station profile CRUD, active profile selection, bounded session overrides |
| **LookupService** | Callsign lookups -- unary, streaming, cached, plus optional batch/DXCC surfaces |
| **LogbookService** | QSO CRUD, QRZ logbook sync, ADIF import/export |
| **DeveloperControlService** | Developer-only runtime config inspection and mutation |
| **SpaceWeatherService** | Current NOAA SWPC snapshot reads and explicit refresh for engine clients |

The built-in engine hosts advertise fine-grained lookup capabilities (`lookup-callsign`, `lookup-stream`, `lookup-cache`) so discovery matches the actually implemented surface. `BatchLookup` and DXCC lookup by code are implemented in both Rust and .NET hosts; DXCC lookup by prefix still returns `UNIMPLEMENTED`.

**Building a client or a new engine host?** See the [Engine API Documentation](docs/api/README.md) for the shared contract reference, stub generation guidance, transport notes, and implementation-status details.

### ADIF

ADIF (Amateur Data Interchange Format) is used **only at the edges** -- QRZ API calls and file I/O. Internal communication always uses protobuf. Engine-specific ADIF adapters convert to/from proto types at the boundary, with an `extra_fields` map for lossless round-tripping.

## Getting Started

### Prerequisites

**Rust toolchain** -- install via [rustup](https://rustup.rs/):

```
# Windows
winget install Rustlang.Rustup

# Linux (Debian/Ubuntu)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

**.NET SDK 10** -- required for the .NET workspace under `src/dotnet/`, including the developer debug workbench and engine validation CLI:

```
# Windows
winget install Microsoft.DotNet.SDK.10

# Linux (Debian/Ubuntu)
sudo apt install dotnet-sdk-10.0
```

The repository pins SDK `10.0.201` in `global.json`.

**Node.js + npm** -- required for the repo-local Playwright tooling and for bootstrapping the local Terminalizer runtime used by terminal capture:

```
# Windows
winget install OpenJS.NodeJS.LTS

# Linux (Debian/Ubuntu)
sudo apt install nodejs npm
```

Node 22 LTS is the safest default for local UI automation work. A newer globally installed Node is fine as long as `npm` is available; `capture-tui.ps1` bootstraps its own repo-local Node 22 runtime for Terminalizer.

**PowerShell 7** -- required for the repo automation scripts under `scripts/`, including Avalonia and terminal capture:

```powershell
# Windows
winget install Microsoft.PowerShell
```

**Protocol Buffers compiler** -- needed to generate gRPC code from proto files:

```
# Windows
winget install Google.Protobuf

# Linux (Debian/Ubuntu)
sudo apt install protobuf-compiler

# Linux (Fedora)
sudo dnf install protobuf-compiler
```

**C compiler** -- required for the native FFI libraries under `src/c/`. On Windows, install the "Desktop development with C++" workload in Visual Studio or the [Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/). On Linux, `gcc` or `clang` is typically already available; install with `sudo apt install build-essential` if needed. The `cc` crate finds the compiler automatically on both platforms.

**buf** (optional) -- for linting and breaking change detection on proto files:

```
# Windows
winget install Bufbuild.Buf

# Linux
# See https://buf.build/docs/installation
```

**cppcheck** (optional, recommended for Win32 work) -- enables extra static analysis for `src\c\qsoripper-win32` when you run `.\build.ps1` or configure the CMake project:

```
# Windows
winget install Cppcheck.Cppcheck

# Linux (Debian/Ubuntu)
sudo apt install cppcheck

# Linux (Fedora)
sudo dnf install cppcheck
```

If `cppcheck` is not installed, `.\build.ps1` still builds the Win32 app and skips only that extra analysis step.

### Build and Test

**Repository build script:**

```powershell
.\build.ps1
.\build.ps1 -Configuration Debug
.\build.ps1 check
.\test.ps1
.\build-and-test.ps1
```

By default, `.\build.ps1` builds the Rust workspace in **Release**, publishes the Native AOT CLI to `artifacts\publish\qsoripper-cli\Release\`, and publishes the desktop GUI to `artifacts\publish\qsoripper-gui\Release\`. Use `-Configuration Debug` to switch the Rust build and both .NET publish outputs to `Debug`.

Use `.\test.ps1` to run the Rust, .NET, Win32 CTest, and Pester suites without the heavier formatting, coverage, and vulnerability gates from `.\build.ps1 check`. Use `.\build-and-test.ps1` when you want to build first and then run the full test script. Local Win32 CMake tests use Visual Studio Build Tools 2026 (`Visual Studio 18 2026`).

For engine-neutral local validation, use the split checks plus the shared conformance harness:

```powershell
.\build.ps1 check-dotnet
.\build.ps1 check-rust
.\tests\Run-EngineConformance.ps1
```

The conformance harness runs the common CLI slice against both built-in engine hosts so cross-language engine behavior stays aligned at the gRPC/protobuf seam.

**Rust engine:**

```
cd src/rust
cargo build
cargo test
```

This compiles the C libraries via FFI, generates Rust types from the proto files, and builds the engine. All tests (unit + integration) run with `cargo test`.

### UI inspection and automation setup

The repo now includes three developer-facing UX inspection lanes:

- **Web** screenshots and diffs with Playwright
- **Avalonia desktop** deterministic capture plus Windows UI automation
- **Terminal** workflow capture to GIF/transcript via a repo-local Terminalizer runtime (**Windows-only** today)
- **Terminal/TUI live automation** through a repo-local PTY harness with JSON action scripts and screen snapshots

One-time setup after cloning:

```powershell
npm install
npx playwright install chromium
```

- `npm install` restores the root TypeScript and Playwright tooling used by `scripts\capture-web.ts` and `scripts\capture-web-diff.ts`.
- The same repo-local Node toolchain now also drives `scripts\drive-tui.ts`, browser-rendered terminal snapshots, and the sample terminal fixture used for TUI automation smoke coverage.
- `npx playwright install chromium` installs the browser binary used for web captures.
- `scripts\capture-tui.ps1` is currently **Windows-only**. It does **not** require a global Terminalizer install; on first run it bootstraps a repo-local Node 22 + Terminalizer runtime under `tools\terminalizer-bootstrap\` and `tools\terminalizer-runtime\`.
- `scripts\drive-avalonia.ps1` is **Windows-only** and needs a

## Issue body

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

1. Submit to the leaderboard? It's public and our score becomes visible. Probably yes — gives us a citation-grade external number.
2. Use the 100 labeled files as additional regression bench, or hold them out for distribution validation only?
3. The published `talengu/kaggle_morse` baseline uses CNN+LSTM. Worth mining for ideas / weights / architecture before our `augment-arrl` + neural work?

## Comments



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
.git/objects/pack/pack-8c98c3e30b9137cd8b5ac319d1db0c22a7183f30.idx
.git/objects/pack/pack-8c98c3e30b9137cd8b5ac319d1db0c22a7183f30.pack
.git/objects/pack/pack-8c98c3e30b9137cd8b5ac319d1db0c22a7183f30.promisor
.git/objects/pack/pack-b9efa23bf0336452f236404d17268cddd32cf75f.idx
.git/objects/pack/pack-b9efa23bf0336452f236404d17268cddd32cf75f.pack
.git/objects/pack/pack-b9efa23bf0336452f236404d17268cddd32cf75f.promisor
.git/ORIG_HEAD
.git/packed-refs
.git/refs/heads/main
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
experiments/cathub-frequency-probe/App.xaml
experiments/cathub-frequency-probe/App.xaml.cs
experiments/cathub-frequency-probe/CatHubFrequencyProbe.csproj
experiments/cathub-frequency-probe/CatHubRigClient.cs
experiments/cathub-frequency-probe/DiagnosticLog.cs
experiments/cathub-frequency-probe/EngineFrequencySnapshot.cs
experiments/cathub-frequency-probe/EngineRigClient.cs
experiments/cathub-frequency-probe/FrequencySnapshot.cs
experiments/cathub-frequency-probe/MainWindow.xaml
experiments/cathub-frequency-probe/MainWindow.xaml.cs
experiments/cathub-frequency-probe/README.md
experiments/cw-decoder/.cargo/config.toml
experiments/cw-decoder/.gitignore
experiments/cw-decoder/adversarial_report_viterbi.json
experiments/cw-decoder/adversarial_report.json
experiments/cw-decoder/Cargo.toml
experiments/cw-decoder/docs/cw-decoder-architecture.html
experiments/cw-decoder/examples/diagnose_qsb.rs
experiments/cw-decoder/EXPERIMENT_REPORT.md
experiments/cw-decoder/gui-screenshot-blur.png
experiments/cw-decoder/gui-screenshot-final.png
experiments/cw-decoder/gui-screenshot-snr.png
experiments/cw-decoder/gui-screenshot-v2.png
experiments/cw-decoder/gui-screenshot.png
experiments/cw-decoder/gui/App.axaml
experiments/cw-decoder/gui/App.axaml.cs
experiments/cw-decoder/gui/app.manifest
experiments/cw-decoder/gui/CwDecoderGui.csproj
experiments/cw-decoder/gui/Program.cs
experiments/cw-decoder/README.md
experiments/cw-decoder/screenshots/sensitivity-panel.png
experiments/cw-decoder/scripts/.gitignore
experiments/cw-decoder/scripts/adversarial_manifest.jsonl
experiments/cw-decoder/scripts/arrl_augmented_sample_manifest.jsonl
experiments/cw-decoder/scripts/augment_cer_vs_snr.png
experiments/cw-decoder/scripts/augment_distribution_check.png
experiments/cw-decoder/scripts/augment_eval.jsonl
experiments/cw-decoder/scripts/augment_report.md
experiments/cw-decoder/scripts/bench_adversarial.py
experiments/cw-decoder/scripts/bench_training_set_a.py
experiments/cw-decoder/scripts/bench-30wpm.ps1
experiments/cw-decoder/scripts/gen-30wpm-variants.ps1
experiments/cw-decoder/scripts/generate_adversarial_suites.py
experiments/cw-decoder/scripts/stress-eval.ps1
experiments/cw-decoder/scripts/stress-gen.ps1
experiments/cw-decoder/src/append_decode.rs
experiments/cw-decoder/src/audio.rs
experiments/cw-decoder/src/bench_latency.rs
experiments/cw-decoder/src/corpus_validator.rs
experiments/cw-decoder/src/decoder.rs
experiments/cw-decoder/src/ditdah_streaming.rs
experiments/cw-decoder/src/envelope_decoder.rs
experiments/cw-decoder/src/harvest.rs
experiments/cw-decoder/src/json.rs
experiments/cw-decoder/src/lib.rs
experiments/cw-decoder/src/log_capture.rs
experiments/cw-decoder/src/main.rs
experiments/cw-decoder/src/preprocess.rs
experiments/cw-decoder/src/preview.rs
experiments/cw-decoder/src/region_stream.rs
experiments/cw-decoder/src/region_streamer.rs
experiments/cw-decoder/src/region_trace.rs
experiments/cw-decoder/src/streaming_v2.rs
experiments/cw-decoder/src/streaming.rs
experiments/cw-decoder/src/synthetic_qso.rs
experiments/cw-decoder/src/tui.rs
experiments/nuget.config
global.json
launcher.ps1
LICENSE
lotw-upload.adi
package-lock.json
package.json
proto/domain/band.proto
proto/domain/callsign_ambiguity.proto
proto/domain/callsign_record.proto
proto/domain/conflict_policy.proto
proto/domain/contest_calendar_entry.proto
proto/domain/contest_calendar_status.proto
proto/domain/contest_details_status.proto
proto/domain/debug_http_exchange.proto
proto/domain/debug_http_header.proto
proto/domain/dxcc_entity.proto
proto/domain/geo_point.proto
proto/domain/geo_reference.proto
proto/domain/geo_source.proto
proto/domain/great_circle_path.proto
proto/domain/lookup_result.proto
proto/domain/lookup_state.proto
proto/domain/mode.proto
proto/domain/modifier_kind.proto
proto/domain/qsl_preference.proto
proto/domain/qsl_status.proto
proto/domain/qso_completion.proto
proto/domain/qso_history_entry.proto
proto/domain/qso_record.proto
proto/domain/rig_connection_status.proto
proto/domain/rig_snapshot.proto
proto/domain/rst_report.proto
proto/domain/space_weather_snapshot.proto
proto/domain/space_weather_status.proto
proto/domain/station_profile.proto
proto/domain/station_snapshot.proto
proto/domain/sync_config.proto
proto/domain/sync_status.proto
proto/services/active_station_context.proto
proto/services/adif_chunk.proto
proto/services/apply_runtime_config_request.proto
proto/services/apply_runtime_config_response.proto
proto/services/batch_lookup_request.proto
proto/services/batch_lookup_response.proto
proto/services/cat_hub_event_settings.proto
proto/services/cat_hub_hamlib_net_endpoint.proto
proto/services/cat_hub_permission.proto
proto/services/cat_hub_poll_settings.proto
proto/services/cat_hub_ptt_settings.proto
proto/services/cat_hub_radio_settings.proto
proto/services/cat_hub_serial_face.proto
proto/services/cat_hub_settings.proto
proto/services/clear_session_station_profile_override_request.proto
proto/services/clear_session_station_profile_override_response.proto
proto/services/compute_great_circle_request.proto
proto/services/compute_great_circle_response.proto
proto/services/contest_calendar_service.proto
proto/services/delete_qso_request.proto
proto/services/delete_qso_response.proto
proto/services/delete_station_profile_request.proto
proto/services/delete_station_profile_response.proto
proto/services/deleted_records_filter.proto
proto/services/developer_control_service.proto
proto/services/engine_info.proto
proto/services/engine_service.proto
proto/services/export_adif_request.proto
proto/services/export_adif_response.proto
proto/services/get_active_contests_request.proto
proto/services/get_active_contests_response.proto
proto/services/get_active_station_context_request.proto
proto/services/get_active_station_context_response.proto
proto/services/get_cached_callsign_request.proto
proto/services/get_cached_callsign_response.proto
proto/services/get_current_space_weather_request.proto
proto/services/get_current_space_weather_response.proto
proto/services/get_dxcc_entity_request.proto
proto/services/get_dxcc_entity_response.proto
proto/services/get_engine_info_request.proto
proto/services/get_engine_info_response.proto
proto/services/get_qso_request.proto
proto/services/get_qso_response.proto
proto/services/get_rig_snapshot_request.proto
proto/services/get_rig_snapshot_response.proto
proto/services/get_rig_status_request.proto
proto/services/get_rig_status_response.proto
proto/services/get_runtime_config_request.proto
proto/services/get_runtime_config_response.proto
proto/services/get_setup_status_request.proto
proto/services/get_setup_status_response.proto
proto/services/get_setup_wizard_state_request.proto
proto/services/get_setup_wizard_state_response.proto
proto/services/get_station_profile_request.proto
proto/services/get_station_profile_response.proto
proto/services/get_stress_run_status_request.proto
proto/services/get_stress_run_status_response.proto
proto/services/get_sync_status_request.proto
proto/services

## Grep excerpt

===== issue body =====
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

1. Submit to the leaderboard? It's public and our score becomes visible. Probably yes — gives us a citation-grade external number.
2. Use the 100 labeled files as additional regression bench, or hold them out for distribution validation only?
3. The published `talengu/kaggle_morse` baseline uses CNN+LSTM. Worth mining for ideas / weights / architecture before our `augment-arrl` + neural work?
===== money/competition/judge hits =====
./tools/ditdah-direct/Cargo.toml:6:[dependencies]
./tools/ditdah-direct/Cargo.toml:15:name = "pin-wpm-test"
./tools/ditdah-direct/Cargo.toml:16:path = "pin_wpm_test.rs"
./tools/ditdah-direct/Cargo-up.toml:6:[dependencies]
./tools/ditdah-prefix-probe/Cargo.toml:6:[dependencies]
./tools/wpm-measure/Cargo.toml:6:[dependencies]
./tools/wpm-measure/main.rs:76:    let mut out = Vec::with_capacity(samples.len() / hop_samples);
./tools/wpm-measure/main.rs:365:        ("symmetric 50/50  HIGH=0.50 LOW=0.50", 0.50, 0.50),
./tools/wpm-measure/main.rs:369:        ("symmetric 50     HIGH=0.50 LOW=0.50", 0.50, 0.50),
./tools/wpm-measure/main.rs:370:        ("symmetric 60     HIGH=0.60 LOW=0.60", 0.60, 0.60),
./tools/wpm-measure/main.rs:446:        // median of shortest 1/3 = (dot + intra-gap) ≈ 2*dot
./tools/wpm-measure/main.rs:450:        println!("  shortest-third median rising-edge interval = {:.2}ms",
./tools/corpus-sweep/pin_sweep.py:2:Sweep cw-decoder corpus at multiple pinned WPMs via the ditdah pin-wpm-test
./tools/corpus-sweep/pin_sweep.py:18:PIN_BIN = REPO / "tools" / "ditdah-direct" / "target" / "release" / "pin-wpm-test.exe"
./tools/corpus-sweep/pin_sweep.py:76:    pin-wpm-test prints `=== auto WPM ===` then text, then for each pin_wpm in
./tools/corpus-sweep/pin_sweep.py:147:        print(f"pin-wpm-test not built: {PIN_BIN}", file=sys.stderr)
./tools/corpus-sweep/sweep.py:50:    word-spacing errors."""
./tools/rolling-whole-buffer/Cargo.toml:6:[dependencies]
./tools/ditdah-direct-up/Cargo.toml:6:[dependencies]
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
./LICENSE:6:of this software and associated documentation files (the "Software"), to deal
./proto/domain/geo_point.proto:7:// A geographic point on Earth in WGS84 decimal degrees.
./proto/domain/contest_calendar_status.proto:7:enum ContestCalendarStatus {
./proto/domain/qso_history_entry.proto:16:// sufficient for both:
./proto/domain/qso_history_entry.proto:18://   - Future contest-mode dupe checks: (band, mode, contest_id) covers every
./proto/domain/qso_history_entry.proto:19://     common contest dupe rule, and contest_id distinguishes current-contest
./proto/domain/qso_history_entry.proto:20://     contacts from past contacts. Contest mode is not implemented yet; this
./proto/domain/qso_history_entry.proto:39:  // Precise transmit frequency in Hz, when known.
./proto/domain/qso_history_entry.proto:45:  // Contest identifier for the contact, when logged in a contest. Empty for
./proto/domain/qso_history_entry.proto:46:  // non-contest QSOs. Used by future contest-mode dupe logic to differentiate
./proto/domain/qso_history_entry.proto:47:  // current-contest dupes from past-contest history.
./proto/domain/qso_history_entry.proto:48:  optional string contest_id = 8;
./proto/domain/station_profile.proto:20:  optional double latitude = 12;  // Logging station latitude in decimal degrees
./proto/domain/station_profile.proto:21:  optional double longitude = 13;  // Logging station longitude in decimal degrees
./proto/domain/contest_calendar_entry.proto:8:import "domain/contest_details_status.proto";
./proto/domain/contest_calendar_entry.proto:12:message ContestCalendarEntry {
./proto/domain/contest_calendar_entry.proto:13:  string contest_id = 1;
./proto/domain/contest_calendar_entry.proto:23:  ContestDetailsStatus details_status = 11;
./proto/domain/conflict_policy.proto:10:  // Default / unset value. Engines should require an explicit policy before
./proto/domain/station_snapshot.proto:20:  optional double latitude = 12;  // Logging station latitude in decimal degrees
./proto/domain/station_snapshot.proto:21:  optional double longitude = 13;  // Logging station longitude in decimal degrees
./proto/domain/qso_completion.proto:12:  QSO_COMPLETION_NO = 2;  // N — QSO not complete (operator decision).
./proto/domain/qso_record.proto:29:  optional uint64 frequency_khz = 15 [deprecated = true];  // Deprecated: use frequency_hz for sub-kHz precision
./proto/domain/qso_record.proto:30:  optional uint64 frequency_hz = 116;  // Precise frequency in Hz (e.g., 28075730 for 28.075730 MHz)
./proto/domain/qso_record.proto:65:  // --- Contest fields ---
./proto/domain/qso_record.proto:66:  optional string contest_id = 50;
./proto/domain/qso_record.proto:89:  // persists until explicitly purged, allowing restore via RestoreQso.
./proto/domain/qso_record.proto:103:  // Decimal degrees, signed (negative for S/W).
./proto/domain/qso_record.proto:109:  // precision on top of `worked_grid`.
./proto/domain/qso_record.proto:113:  // Deprecated: use frequency_rx_hz for sub-kHz precision.
./proto/domain/qso_record.proto:145:  // This is an intentionally lossy "latest snapshot" cache. A future
./proto/domain/contest_details_status.proto:7:enum ContestDetailsStatus {
./proto/domain/great_circle_path.proto:19:// for antipodal points where the great circle is not unique.
./proto/services/purge_deleted_qsos_request.proto:37:  // accidental client-side dispatches.
./proto/services/compute_great_circle_response.proto:7:import "domain/great_circle_path.proto";
./proto/services/compute_great_circle_response.proto:9:// Response carrying the resolved great-circle path between the request's
./proto/services/test_qrz_logbook_credentials_response.proto:10:  // Human-readable error message when the test failed.
./proto/services/lookup_service.proto:18:// The app-facing callsign lookup interface.
./proto/services/lookup_service.proto:47:  // Batch lookup for prefetch/contest scenarios. Returns one LookupResult per callsign,
./proto/services/lookup_service.proto:48:  // in request order. Useful for warming the cache before a contest session begins.
./proto/services/list_qsos_request.proto:19:  optional string contest_id = 6;
./proto/services/list_qsos_request.proto:23:  // Controls inclusion of soft-deleted rows. Unspecified = ACTIVE_ONLY.
./proto/services/great_circle_service.proto:7:import "services/compute_great_circle_request.proto";
./proto/services/great_circle_service.proto:8:import "services/compute_great_circle_response.proto";
./proto/services/great_circle_service.proto:10:// Pure-geometry service for great-circle / azimuthal-projection support
./proto/services/great_circle_service.proto:15:  // Origin and target may be supplied as decimal-degree coordinates or
./proto/services/refresh_contest_calendar_response.proto:7:import "domain/contest_calendar_entry.proto";
./proto/services/refresh_contest_calendar_response.proto:8:import "domain/contest_calendar_status.proto";
./proto/services/refresh_contest_calendar_response.proto:11:message RefreshContestCalendarResponse {
./proto/services/refresh_contest_calendar_response.proto:12:  repeated qsoripper.domain.ContestCalendarEntry contests = 1;
./proto/services/refresh_contest_calendar_response.proto:13:  qsoripper.domain.ContestCalendarStatus status = 2;
./proto/services/get_sync_status_response.proto:16:  bool is_syncing = 6;
./proto/services/compute_great_circle_request.proto:9:// Request to compute a great-circle geodesic between two points.
./proto/services/rig_control_service.proto:11:import "services/test_rig_connection_request.proto";
./proto/services/rig_control_service.proto:12:import "services/test_rig_connection_response.proto";
./proto/services/stress_run_configuration.proto:11:  uint32 metrics_interval_ms = 4;
./proto/services/contest_calendar_service.proto:7:import "services/get_active_contests_request.proto";
./proto/services/contest_calendar_service.proto:8:import "services/get_active_contests_response.proto";
./proto/services/contest_calendar_service.proto:9:import "services/refresh_contest_calendar_request.proto";
./proto/services/contest_calendar_service.proto:10:import "services/refresh_contest_calendar_response.proto";
./proto/services/contest_calendar_service.proto:12:service ContestCalendarService {
./proto/services/contest_calendar_service.proto:13:  rpc GetActiveContests(GetActiveContestsRequest) returns (GetActiveContestsResponse);
./proto/services/contest_calendar_service.proto:14:  rpc RefreshContestCalendar(RefreshContestCalendarRequest) returns (RefreshContestCalendarResponse);
./proto/services/test_rig_connection_request.proto:7:// Allows testing rig connectivity with optional overrides before persisting config.
./proto/services/setup_service.proto:13:import "services/test_qrz_credentials_request.proto";
./proto/services/setup_service.proto:14:import "services/test_qrz_credentials_response.proto";
./proto/services/setup_service.proto:15:import "services/test_qrz_logbook_credentials_request.proto";
./proto/services/setup_service.proto:16:import "services/test_qrz_logbook_credentials_response.proto";
./proto/services/stress_control_service.proto:29:  // Stream the latest stress snapshot whenever it changes.
./proto/services/station_profile_service.proto:45:  // Apply an explicit process-session station override without mutating persisted profiles.
./proto/services/get_active_contests_response.proto:7:import "domain/contest_calendar_entry.proto";
./proto/services/get_active_contests_response.proto:8:import "domain/contest_calendar_status.proto";
./proto/services/get_active_contests_response.proto:11:message GetActiveContestsResponse {
./proto/services/get_active_contests_response.proto:12:  repeated qsoripper.domain.ContestCalendarEntry contests = 1;
./proto/services/get_active_contests_response.proto:13:  qsoripper.domain.ContestCalendarStatus status = 2;
./proto/services/logbook_service.proto:63:  // can reverse the decision via RestoreQso before the next sync runs.
./proto/services/export_adif_request.proto:12:  optional string contest_id = 3;
./proto/services/get_active_contests_request.proto:11:message GetActiveContestsRequest {
./proto/services/refresh_contest_calendar_request.proto:7:message RefreshContestCalendarRequest {}
./proto/services/stress_run_snapshot.proto:9:import "services/stress_process_metrics.proto";
./proto/services/setup_status.proto:46:  // User-facing title for the persistence step.
./proto/services/setup_status.proto:48:  // User-facing description for the persistence step.
./proto/services/setup_status.proto:54:  // True when the engine explicitly uses the engine-neutral persistence contract.
./proto/services/setup_status.proto:56:  bool persistence_contract_explicit = 25;
./config/cathub.toml:5:# so there is no VFO A/B oscillation, no frequency drift, and no PTT contention.
./config/cathub.toml:72:# can never oscillate the TS-590's A/B VFO selection.
./experiments/cathub-frequency-probe/MainWindow.xaml:20:                <Setter Property="CharacterSpacing" Value="120" />
./experiments/cathub-frequency-probe/MainWindow.xaml:44:                               CharacterSpacing="120" />
./experiments/cathub-frequency-probe/MainWindow.xaml:78:                               CharacterSpacing="160" />
./experiments/cathub-frequency-probe/MainWindow.xaml:81:                        <StackPanel Orientation="Horizontal" Spacing="18">
./experiments/cathub-frequency-probe/MainWindow.xaml:88:                                       CharacterSpacing="50" />
./experiments/cathub-frequency-probe/MainWindow.xaml:99:                    <Grid Grid.Row="2" ColumnSpacing="18">
./experiments/cathub-frequency-probe/MainWindow.xaml:147:                <Grid RowSpacing="8">
./experiments/cathub-frequency-probe/DiagnosticLog.cs:14:            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
./experiments/cathub-frequency-probe/README.md:3:Single-purpose WinUI 3 diagnostic app for CAT latency testing.
./experiments/cathub-frequency-probe/CatHubFrequencyProbe.csproj:17:    <ImplicitUsings>enable</ImplicitUsings>
./experiments/cw-decoder/Cargo.toml:12:name = "eval"
./experiments/cw-decoder/Cargo.toml:13:path = "src/bin/eval.rs"
./experiments/cw-decoder/Cargo.toml:19:[dependencies]
./experiments/cw-decoder/EXPERIMENT_REPORT.md:9:targeting a specific decoder failure mode. We evaluate the current
./experiments/cw-decoder/EXPERIMENT_REPORT.md:24:| `experiments/cw-decoder/scripts/bench_adversarial.py` | Bench harness (CER/WER + element-level + suite-specific metrics) |
./experiments/cw-decoder/EXPERIMENT_REPORT.md:40:| `fast-contest` | 20 | 35 / 40 / 45 WPM short contest exchanges | Standard timing, 0.025 white noise floor |
./experiments/cw-decoder/EXPERIMENT_REPORT.md:48:| Suite | mean CER | mean WER | el-recall | el-precision | suite-specific |
./experiments/cw-decoder/EXPERIMENT_REPORT.md:57:| `fast-contest`        | 0.000 | 0.000 | 1.000 | 1.000 | — |
./experiments/cw-decoder/EXPERIMENT_REPORT.md:62:precision = matches / |hypothesis elements|.
./experiments/cw-decoder/EXPERIMENT_REPORT.md:80:## Specific findings the brief asked for
./experiments/cw-decoder/EXPERIMENT_REPORT.md:97:3. **`noise-only` (hallucination check)** — the decoder is clean: **100% of
./experiments/cw-decoder/EXPERIMENT_REPORT.md:103:   element recall drops to **0.362** (precision 0.650). The long word /
./experiments/cw-decoder/EXPERIMENT_REPORT.md:109:   precision drops (0.73) because the interferer adds extra elements that
./experiments/cw-decoder/EXPERIMENT_REPORT.md:112:6. **`fast-contest`** — perfect (CER 0).
./experiments/cw-decoder/EXPERIMENT_REPORT.md:122:| `fast-contest` | `mean_cer == 0.0` |
./experiments/cw-decoder/EXPERIMENT_REPORT.md:135:| `qrm-same-pitch` el-precision | 0.729 | Decoder needs to pick a track when two collide |
./experiments/cw-decoder/EXPERIMENT_REPORT.md:158:The 6-sample bench at the worktree root remains as a smoke test; this
./experiments/cw-decoder/docs/cw-decoder-architecture.html:39:    letter-spacing: 0.05em;
./experiments/cw-decoder/docs/cw-decoder-architecture.html:43:  .masthead .meta { font-size: 0.85em; color: var(--muted); letter-spacing: 0.04em; }
./experiments/cw-decoder/docs/cw-decoder-architecture.html:78:    letter-spacing: 0.06em;
./experiments/cw-decoder/docs/cw-decoder-architecture.html:103:    letter-spacing: 0.04em;
./experiments/cw-decoder/docs/cw-decoder-architecture.html:168:    letter-spacing: 0.04em;
./experiments/cw-decoder/docs/cw-decoder-architecture.html:184:    letter-spacing: 0.06em;
./experiments/cw-decoder/docs/cw-decoder-architecture.html:201:  .small-caps { font-variant: small-caps; letter-spacing: 0.04em; }
./experiments/cw-decoder/docs/cw-decoder-architecture.html:231:      state, mis-classify dits and dahs at the new speed, or hallucinate
./experiments/cw-decoder/docs/cw-decoder-architecture.html:256:    contest exchanges, callsign capture, and post-QSO reconstruction.
./experiments/cw-decoder/docs/cw-decoder-architecture.html:262:    The reference test case for this work is
./experiments/cw-decoder/docs/cw-decoder-architecture.html:295:    visualizer and at producing a stable transcript on long, single-speed
./experiments/cw-decoder/docs/cw-decoder-architecture.html:325:      the transcript &mdash; later cycles cannot undo it without producing
./experiments/cw-decoder/docs/cw-decoder-architecture.html:360:      <rect x="20" y="115" width="720" height="10" fill="#ddd" opacity="0.6"/>
./experiments/cw-decoder/docs/cw-decoder-architecture.html:363:      <rect x="60"  y="60" width="80"  height="60" fill="#102a54" opacity="0.85"/>
./experiments/cw-decoder/docs/cw-decoder-architecture.html:367:      <rect x="200" y="40" width="120" height="80" fill="#102a54" opacity="0.85"/>
./experiments/cw-decoder/docs/cw-decoder-architecture.html:371:      <rect x="380" y="70" width="140" height="50" fill="#102a54" opacity="0.85"/>
./experiments/cw-decoder/docs/cw-decoder-architecture.html:375:      <rect x="570" y="70" width="140" height="50" fill="#102a54" opacity="0.85"/>
./experiments/cw-decoder/docs/cw-decoder-architecture.html:417:    With <code>threshold_factor = 0.30</code>, the decision boundary
./experiments/cw-decoder/docs/cw-decoder-architecture.html:423:    static spikes. Each surviving run is padded symmetrically by
./experiments/cw-decoder/docs/cw-dec

