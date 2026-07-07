# Strict Recon Report

## Verdict

`PARK_RISK`

## Decision

JSON:
{
  "verdict": "PARK_RISK",
  "issue": {
    "url": "https://github.com/tenstorrent/tt-blacksmith/issues/529",
    "title": "[Bounty $2000] GraphSAGE training workload on Tenstorrent",
    "state": "OPEN",
    "labels": [
      "bounty_difficulty/hard",
      "task"
    ],
    "comment_count": 4,
    "updatedAt": "2026-06-15T08:39:07Z"
  },
  "has_explicit_acceptance": true,
  "has_local_command": true,
  "has_ci": true,
  "has_concrete_error": true,
  "has_money": true,
  "risk": true
}

## Cheap commands

pwd=/Users/heath/Documents/mathgraph-lean-work/external/money_opportunity_scout_v3_strict/tenstorrent__tt-blacksmith_529



## Issue body

## Summary
Propose adding a GraphSAGE training workload to tt-blacksmith

## Proposed Scope
- Primary focus: training
- Secondary stretch goal: inference if time permits
- Hardware target: Wormhole N300
- Initial datasets:
  - Reddit (main target)
  - PubMed (smaller fallback / bring-up option)

## Initial Plan
1. Build a CPU baseline
2. Profile the workload and identify the most important stages
3. Port the model into a tt-blacksmith experiment structure using TT-supported ops where possible
4. Run on Tenstorrent hardware
5. Compare correctness and performance against CPU
6. Document limitations, blocked ops, and optimisation opportunities

## Deliverables
- Working CPU baseline
- Working TT implementation for the training workload (or core training stages)
- CPU vs TT parity checks
- Benchmarking / profiling results
- Reproducible setup and documentation

## Success Criteria
- TT execution on hardware, with only targeted CPU fallbacks if necessary
- Clear correctness checks against CPU
- Measurable benchmarking results
- Documentation of unsupported or difficult stages and possible next steps

## Open Questions
- Preferred dataset for initial bring-up: Reddit vs PubMed?
- Preferred framework path inside tt-blacksmith / Forge?
- What level of TT execution is acceptable for the first milestone?
- Should milestones be split similarly to other training workload issues?

## Inventory excerpt

top files
.cursor/skills/perf-benchmark-single-chip/reference.md
.cursor/skills/perf-benchmark-single-chip/SKILL.md
.flake8-config
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
.git/objects/pack/pack-3cf0b11d55fb186504fa9d9f8d5cfb3a2b267b7e.idx
.git/objects/pack/pack-3cf0b11d55fb186504fa9d9f8d5cfb3a2b267b7e.pack
.git/objects/pack/pack-3cf0b11d55fb186504fa9d9f8d5cfb3a2b267b7e.promisor
.git/objects/pack/pack-6ad72c236846dadec023b02224ab8e2db40b9c0e.idx
.git/objects/pack/pack-6ad72c236846dadec023b02224ab8e2db40b9c0e.pack
.git/objects/pack/pack-6ad72c236846dadec023b02224ab8e2db40b9c0e.promisor
.git/ORIG_HEAD
.git/packed-refs
.git/refs/heads/main
.gitattributes
.github/check-spdx.yml
.github/CODEOWNERS
.github/ISSUE_TEMPLATE/bug_report.yml
.github/ISSUE_TEMPLATE/documentation_request.yml
.github/ISSUE_TEMPLATE/feature_request.yml
.github/ISSUE_TEMPLATE/how_to.yml
.github/pull_request_template.md
.github/PULL_REQUEST_TEMPLATE/adding_an_experiment.md
.github/PULL_REQUEST_TEMPLATE/bugfix.md
.github/PULL_REQUEST_TEMPLATE/generic.md
.github/workflows/call-build-docs.yml
.github/workflows/call-generate-matrix.yml
.github/workflows/call-pre-commit.yml
.github/workflows/call-test.yml
.github/workflows/codeql.yml
.github/workflows/docs-deploy.yml
.github/workflows/issue-update-date.yml
.github/workflows/manual-test.yml
.github/workflows/pr-main.yml
.github/workflows/push-main.yml
.github/workflows/schedule-uplift.yml
.github/workflows/test-matrix-presets/basic-test.json
.github/workflows/test-matrix-presets/regressed-test.json
.github/workflows/test-matrix-presets/uplift-test.json
.github/workflows/workflow-run-collect-data.yml
.gitignore
.pre-commit-config.yaml
blacksmith/__init__.py
blacksmith/datasets/__init__.py
blacksmith/datasets/jax/dataset_utils.py
blacksmith/datasets/torch/dataset_utils.py
blacksmith/datasets/torch/torch_dataset.py
blacksmith/experiments/__init__.py
blacksmith/experiments/easydel/setup_gpu_requirements.sh
blacksmith/experiments/lightning/__init__.py
blacksmith/experiments/torch/__init__.py
blacksmith/models/__init__.py
blacksmith/tools/__init__.py
blacksmith/tools/checkpoints_manager.py
blacksmith/tools/cli.py
blacksmith/tools/device_manager.py
blacksmith/tools/dpo_utils.py
blacksmith/tools/forge_tooling.py
blacksmith/tools/hf_callbacks.py
blacksmith/tools/jax/__init__.py
blacksmith/tools/jax/checkpoint_manager.py
blacksmith/tools/jax/device_manager.py
blacksmith/tools/jax/helpers.py
blacksmith/tools/logging_manager.py
blacksmith/tools/logging/configs.py
blacksmith/tools/logging/logger_config.yaml
blacksmith/tools/reproducibility_manager.py
blacksmith/tools/storage_backends.py
blacksmith/tools/templates/configs.py
blacksmith/tools/templates/test_model_template.py
blacksmith/tools/templates/test_model_template.yaml
blacksmith/tools/test_config.py
blacksmith/tools/torch_helpers.py
blacksmith/tools/torch_lightning.py
blacksmith/tools/trainer/__init__.py
blacksmith/tools/trainer/callback.py
blacksmith/tools/trainer/callbacks_handler.py
blacksmith/tools/trainer/trainer.py
blacksmith/tools/trainer/utils.py
blacksmith/tools/workaround_utils.py
CLAUDE.md
CODE_OF_CONDUCT.md
CONTRIBUTING.md
docs/conf.py
docs/index.rst
docs/Makefile
docs/requirements.txt
docs/shared/_static/docs-toc.js
docs/shared/_static/home.css
docs/shared/_static/logotype.png
docs/shared/_static/tt_theme.css
docs/shared/_templates/feedback_widget.html
docs/shared/_templates/layout.html
docs/shared/_templates/redirect_template.html
docs/shared/_templates/versions.html
docs/shared/images/favicon.png
docs/shared/images/nerf_demo.gif
docs/shared/images/tt_logo.svg
docs/shared/images/tt-blacksmith-logo.png
docs/src/coding-guidelines.md
docs/src/experiments.md
docs/src/getting-started.md
docs/src/introduction.md
env/activate
env/download_debug_wheel.sh
env/ffe_requirements.txt
env/gpu_requirements.txt
env/requirements.txt
env/xla_requirements.txt
LICENSE
LICENSE_understanding.txt
README.md
scripts/index_remote_search.py
setup.py
tests/checkpoints/tt-gemma11-math_preference_sft-p150_checkpoint_step360_epoch2_20260622_192415.pt
tests/checkpoints/tt-llama_3_2_1b-sst2-n150_checkpoint_step1340_epoch0_20260325_211954.pt
tests/checkpoints/tt-llama_3_2_1b-sst2-n150_checkpoint_step2680_epoch0_20260326_081459.pt
tests/configs/BOUNTIES/tt-gatv2_pubmed-pubmed-n150.yaml
tests/configs/tt-albert_base_v2-banking77-n150.yaml
tests/configs/tt-gemma11-math_preference_dpo-p150.yaml
tests/configs/tt-llama_3_1_70b-sst2-n300-galaxy.yaml
tests/configs/tt-llama_3_1_8b_instruct-metamathqa-n300-llmbox.yaml
tests/configs/tt-llama_3_1_8b-sst2-data_tensor_parallel-n300-llmbox.yaml
tests/configs/tt-llama_3_1_8b-sst2-galaxy-batch-model.yaml
tests/configs/tt-llama_3_1_8b-sst2-qb2-blackhole.yaml
tests/configs/tt-llama_3_1_8b-sst2-tensor_parallel-n300-llmbox.yaml
tests/configs/tt-llama_3_2_1b-sst2-n150.yaml
tests/conftest.py
tests/golden_files/tt-albert_base_v2-banking77-n150_train.csv
tests/golden_files/tt-albert_base_v2-banking77-n150_val.csv
tests/golden_files/tt-gatv2_pubmed-pubmed-n150_train.csv
tests/golden_files/tt-gatv2_pubmed-pubmed-n150_val.csv
tests/golden_files/tt-gemma11-math_preference_dpo-p150_train.csv
tests/golden_files/tt-gemma11-math_preference_dpo-p150_val.csv
tests/golden_files/tt-gemma11-squadv2-n150_train.csv
tests/golden_files/tt-gemma11-squadv2-n150_val.csv
tests/golden_files/tt-llama_3_1_70b-sst2-n300-galaxy_train.csv
tests/golden_files/tt-llama_3_1_70b-sst2-n300-galaxy_val.csv
tests/golden_files/tt-llama_3_1_8b_instruct-metamathqa-n300-llmbox_train.csv
tests/golden_files/tt-llama_3_1_8b_instruct-metamathqa-n300-llmbox_val.csv
tests/golden_files/tt-llama_3_1_8b-sst2-data_tensor_parallel-n300-llmbox_train.csv
tests/golden_files/tt-llama_3_1_8b-sst2-data_tensor_parallel-n300-llmbox_val.csv
tests/golden_files/tt-llama_3_1_8b-sst2-p150_train.csv
tests/golden_files/tt-llama_3_1_8b-sst2-p150_val.csv
tests/golden_files/tt-llama_3_1_8b-sst2-qb2-blackhole_train.csv
tests/golden_files/tt-llama_3_1_8b-sst2-qb2-blackhole_val.csv
tests/golden_files/tt-llama_3_1_8b-sst2-tensor_parallel-n300-llmbox_train.csv
tests/golden_files/tt-llama_3_1_8b-sst2-tensor_parallel-n300-llmbox_val.csv
tests/golden_files/tt-llama_3_2_1b-sst2-n150-0_train.csv
tests/golden_files/tt-llama_3_2_1b-sst2-n150-0_val.csv
tests/golden_files/tt-llama_3_2_1b-sst2-n150-1_train.csv
tests/golden_files/tt-llama_3_2_1b-sst2-n150-1_val.csv
tests/golden_files/tt-llama_3_2_1b-sst2-n150-2_train.csv
tests/golden_files/tt-llama_3_2_1b-sst2-n150-2_val.csv
tests/golden_files/tt-llama_3_2_1b-sst2-n300-galaxy_train.csv
tests/golden_files/tt-llama_3_2_1b-sst2-n300-galaxy_val.csv
tests/golden_files/tt-llama_3_2_1b-sst2-n300-llmbox_train.csv
tests/golden_files/tt-llama_3_2_1b-sst2-n300-llmbox_val.csv
tests/golden_files/tt-mlp-mnist-n150_train.csv
tests/golden_files/tt-mlp-mnist-n150_val.csv
tests/golden_files/tt-mlp-mnist-n300-dp_train.csv
tests/golden_files/tt-mlp-mnist-n300-dp_val.csv
tests/golden_files/tt-mlp-mnist-n300-tp_train.csv
tests/golden_files/tt-mlp-mnist-n300-tp_val.csv
tests/golden_files/tt-phi1-sst2-n150_train.csv
tests/golden_files/tt-phi1-sst2-n150_val.csv
tests/golden_files/tt-qwen_1_5b-text2sql-n150_train.csv
tests/golden_files/tt-qwen_1_5b-text2sql-n150_val.csv
tests/pytest.ini
tests/test_all.py
tests/trainer/test_callbacks_handler.py
tests/training_test_cases.py

build/test files
./blacksmith/experiments/easydel/qwen/lora/README.md
./blacksmith/experiments/jax/BOUNTIES/nanogpt/README.md
./blacksmith/experiments/jax/distil_bert/README.md
./blacksmith/experiments/jax/llama/dora/README.md
./blacksmith/experiments/jax/llama/lora/README.md
./blacksmith/experiments/jax/mnist/README.md
./blacksmith/experiments/jax/nerf/README.md
./blacksmith/experiments/lightning/mnist/README.md
./blacksmith/experiments/lightning/nerf/README.md
./blacksmith/experiments/lightning/nerf/requirements.txt
./blacksmith/experiments/torch/albert/README.md
./blacksmith/experiments/torch/BOUNTIES/falcon3_1b/README.md
./blacksmith/experiments/torch/BOUNTIES/gatv2_pubmed/README.md
./blacksmith/experiments/torch/BOUNTIES/gatv2_pubmed/requirements.txt
./blacksmith/experiments/torch/BOUNTIES/ppo_breakout/README.md
./blacksmith/experiments/torch/BOUNTIES/ppo_breakout/requirements.txt
./blacksmith/experiments/torch/gemma/README.md
./blacksmith/experiments/torch/gemma11/dpo/README.md
./blacksmith/experiments/torch/gemma11/lora/README.md
./blacksmith/experiments/torch/gpt_oss/README.md
./blacksmith/experiments/torch/llama/ffe/README.md
./blacksmith/experiments/torch/mnist_cnn/README.md
./blacksmith/experiments/torch/mnist/README.md
./blacksmith/experiments/torch/phi/README.md
./blacksmith/experiments/torch/qwen/README.md
./blacksmith/experiments/torch/vit/README.md
./blacksmith/experiments/torch/wan2_2/README.md
./docs/Makefile
./docs/requirements.txt
./env/requirements.txt
./README.md

workflows
.github/workflows/call-build-docs.yml
.github/workflows/call-generate-matrix.yml
.github/workflows/call-pre-commit.yml
.github/workflows/call-test.yml
.github/workflows/codeql.yml
.github/workflows/docs-deploy.yml
.github/workflows/issue-update-date.yml
.github/workflows/manual-test.yml
.github/workflows/pr-main.yml
.github/workflows/push-main.yml
.github/workflows/schedule-uplift.yml
.github/workflows/test-matrix-presets/basic-test.json
.github/workflows/test-matrix-presets/regressed-test.json
.github/workflows/test-matrix-presets/uplift-test.json
.github/workflows/workflow-run-collect-data.yml


## Grep excerpt

===== issue terms =====
## Summary
Propose adding a GraphSAGE training workload to tt-blacksmith

## Proposed Scope
- Primary focus: training
- Secondary stretch goal: inference if time permits
- Hardware target: Wormhole N300
- Initial datasets:
  - Reddit (main target)
  - PubMed (smaller fallback / bring-up option)

## Initial Plan
1. Build a CPU baseline
2. Profile the workload and identify the most important stages
3. Port the model into a tt-blacksmith experiment structure using TT-supported ops where possible
4. Run on Tenstorrent hardware
5. Compare correctness and performance against CPU
6. Document limitations, blocked ops, and optimisation opportunities

## Deliverables
- Working CPU baseline
- Working TT implementation for the training workload (or core training stages)
- CPU vs TT parity checks
- Benchmarking / profiling results
- Reproducible setup and documentation

## Success Criteria
- TT execution on hardware, with only targeted CPU fallbacks if necessary
- Clear correctness checks against CPU
- Measurable benchmarking results
- Documentation of unsupported or difficult stages and possible next steps

## Open Questions
- Preferred dataset for initial bring-up: Reddit vs PubMed?
- Preferred framework path inside tt-blacksmith / Forge?
- What level of TT execution is acceptable for the first milestone?
- Should milestones be split similarly to other training workload issues?
===== judge hits =====
./.cursor/skills/perf-benchmark-single-chip/reference.md:78:## Tracy signpost workflow
./.cursor/skills/perf-benchmark-single-chip/SKILL.md:2:name: perf-benchmark-single-chip
./.cursor/skills/perf-benchmark-single-chip/SKILL.md:3:description: Run device performance benchmarks for tt-blacksmith single-chip training workloads. Use when the user asks to benchmark, profile, or measure performance of a training workload on Tenstorrent hardware, or mentions tracy, tt-perf-report, or device time analysis.
./.cursor/skills/perf-benchmark-single-chip/SKILL.md:6:# Single-chip perf benchmark
./.cursor/skills/perf-benchmark-single-chip/SKILL.md:27:Before running any workload, ensure no stale processes are holding the TT device. A previous process that was force-killed (kill -9) leaves the device in a bad state, causing "Timeout waiting for Ethernet core service" or "Waiting for lock 'CHIP_IN_USE_*_PCIe'" errors.
./.cursor/skills/perf-benchmark-single-chip/SKILL.md:107:- The sync must come **after backward**, not between forward and backward. Calls like `loss.item()` force an implicit sync -- move them after backward or remove them when benchmarking.
./.cursor/skills/perf-benchmark-single-chip/SKILL.md:137:    tracy.signpost("benchmark_complete")
./.cursor/skills/perf-benchmark-single-chip/SKILL.md:249:- **"Timeout waiting for Ethernet core service" / "Waiting for lock 'CHIP_IN_USE_*_PCIe'"**: Kill all stale Python processes, then reset all devices: `tt-smi -r`. Wait a few seconds before starting a new process.
./LICENSE:168:      and charge a fee for, acceptance of support, warranty, indemnity,
./.flake8-config:22:    .pytest_cache,
./tests/training_test_cases.py:4:import pytest
./tests/training_test_cases.py:8:    pytest.param(
./tests/training_test_cases.py:15:            pytest.mark.push,
./tests/training_test_cases.py:16:            pytest.mark.n300,
./tests/training_test_cases.py:17:            pytest.mark.torch,
./tests/training_test_cases.py:18:            pytest.mark.tensor_parallel,
./tests/training_test_cases.py:22:    pytest.param(
./tests/training_test_cases.py:29:            pytest.mark.push,
./tests/training_test_cases.py:30:            pytest.mark.n300,
./tests/training_test_cases.py:31:            pytest.mark.torch,
./tests/training_test_cases.py:32:            pytest.mark.data_parallel,
./tests/training_test_cases.py:36:    pytest.param(
./tests/training_test_cases.py:43:            pytest.mark.push,
./tests/training_test_cases.py:44:            pytest.mark.n150,
./tests/training_test_cases.py:45:            pytest.mark.n300,
./tests/training_test_cases.py:46:            pytest.mark.torch,
./tests/training_test_cases.py:47:            pytest.mark.single_chip,
./tests/training_test_cases.py:51:    # Bounty #453 (GATv2/PubMed). Disabled in CI until the experiment-specific
./tests/training_test_cases.py:52:    # torch_geometric dependency and a TT runner are wired into the regression pipeline;
./tests/training_test_cases.py:54:    # pytest.param(
./tests/training_test_cases.py:62:    #         pytest.mark.uplift,
./tests/training_test_cases.py:63:    #         pytest.mark.n150,
./tests/training_test_cases.py:64:    #         pytest.mark.n300,
./tests/training_test_cases.py:65:    #         pytest.mark.torch,
./tests/training_test_cases.py:66:    #         pytest.mark.single_chip,
./tests/training_test_cases.py:70:    pytest.param(
./tests/training_test_cases.py:78:            pytest.mark.uplift,
./tests/training_test_cases.py:79:            pytest.mark.n300,
./tests/training_test_cases.py:80:            pytest.mark.jax,
./tests/training_test_cases.py:81:            pytest.mark.data_parallel,
./tests/training_test_cases.py:85:    pytest.param(
./tests/training_test_cases.py:93:            pytest.mark.uplift,
./tests/training_test_cases.py:94:            pytest.mark.n150,
./tests/training_test_cases.py:95:            pytest.mark.jax,
./tests/training_test_cases.py:96:            pytest.mark.single_chip,
./tests/training_test_cases.py:100:    pytest.param(
./tests/training_test_cases.py:108:            pytest.mark.uplift,
./tests/training_test_cases.py:109:            pytest.mark.n150,
./tests/training_test_cases.py:110:            pytest.mark.jax,
./tests/training_test_cases.py:111:            pytest.mark.single_chip,
./tests/training_test_cases.py:115:    pytest.param(
./tests/training_test_cases.py:123:            pytest.mark.skip(
./tests/training_test_cases.py:126:            pytest.mark.uplift,
./tests/training_test_cases.py:127:            pytest.mark.n300,
./tests/training_test_cases.py:128:            pytest.mark.jax,
./tests/training_test_cases.py:129:            pytest.mark.tensor_parallel,
./tests/training_test_cases.py:134:        pytest.param(
./tests/training_test_cases.py:143:                pytest.mark.uplift,
./tests/training_test_cases.py:144:                pytest.mark.n150,
./tests/training_test_cases.py:145:                pytest.mark.torch,
./tests/training_test_cases.py:146:                pytest.mark.single_chip,
./tests/training_test_cases.py:147:                pytest.mark.split_0,
./tests/training_test_cases.py:159:    pytest.param(
./tests/training_test_cases.py:166:            pytest.mark.uplift,
./tests/training_test_cases.py:167:            pytest.mark.n300_llmbox,
./tests/training_test_cases.py:168:            pytest.mark.torch,
./tests/training_test_cases.py:169:            pytest.mark.data_parallel,
./tests/training_test_cases.py:170:            pytest.mark.tensor_parallel,
./tests/training_test_cases.py:174:    pytest.param(
./tests/training_test_cases.py:182:            pytest.mark.uplift,
./tests/training_test_cases.py:183:            pytest.mark.n300_llmbox,
./tests/training_test_cases.py:184:            pytest.mark.torch,
./tests/training_test_cases.py:185:            pytest.mark.data_parallel,
./tests/training_test_cases.py:186:            pytest.mark.tensor_parallel,
./tests/training_test_cases.py:190:    pytest.param(
./tests/training_test_cases.py:198:            pytest.mark.uplift,
./tests/training_test_cases.py:199:            pytest.mark.n300_llmbox,
./tests/training_test_cases.py:200:            pytest.mark.torch,
./tests/training_test_cases.py:201:            pytest.mark.data_parallel,
./tests/training_test_cases.py:202:            pytest.mark.tensor_parallel,
./tests/training_test_cases.py:206:    pytest.param(
./tests/training_test_cases.py:215:            pytest.mark.uplift,
./tests/training_test_cases.py:216:            pytest.mark.qb2_blackhole,
./tests/training_test_cases.py:217:            pytest.mark.torch,
./tests/training_test_cases.py:218:            pytest.mark.tensor_parallel,
./tests/training_test_cases.py:222:    pytest.param(
./tests/training_test_cases.py:230:            pytest.mark.uplift,
./tests/training_test_cases.py:231:            pytest.mark.n300_llmbox,
./tests/training_test_cases.py:232:            pytest.mark.torch,
./tests/training_test_cases.py:233:            pytest.mark.tensor_parallel,
./tests/training_test_cases.py:237:    pytest.param(
./tests/training_test_cases.py:244:            pytest.mark.uplift,
./tests/training_test_cases.py:245:            pytest.mark.p150,
./tests/training_test_cases.py:246:            pytest.mark.torch,
./tests/training_test_cases.py:247:            pytest.mark.single_chip,
./tests/training_test_cases.py:251:    pytest.param(
./tests/training_test_cases.py:258:            pytest.mark.skip(reason="OOM on Galaxy llama 8B"),
./tests/training_test_cases.py:259:            pytest.mark.uplift,
./tests/training_test_cases.py:260:            pytest.mark.galaxy,
./tests/training_test_cases.py:261:            pytest.mark.torch,
./tests/training_test_cases.py:262:            pytest.mark.data_parallel,
./tests/training_test_cases.py:263:            pytest.mark.tensor_parallel,
./tests/training_test_cases.py:267:    pytest.param(
./tests/training_test_cases.py:275:            pytest.mark.skip(reason="OOM on Galaxy llama 8B"),
./tests/training_test_cases.py:276:            pytest.mark.uplift,
./tests/training_test_cases.py:277:            pytest.mark.galaxy,
./tests/training_test_cases.py:278:            pytest.mark.torch,
./tests/training_test_cases.py:279:            pytest.mark.data_parallel,
./tests/training_test_cases.py:280:            pytest.mark.tensor_parallel,
./tests/training_test_cases.py:284:    pytest.param(
./tests/training_test_cases.py:292:            pytest.mark.uplift,
./tests/training_test_cases.py:293:            pytest.mark.galaxy,
./tests/training_test_cases.py:294:            pytest.mark.torch,
./tests/training_test_cases.py:295:            pytest.mark.tensor_parallel,
./tests/training_test_cases.py:299:    pytest.param(
./tests/training_test_cases.py:306:            pytest.mark.uplift,
./tests/training_test_cases.py:307:            pytest.mark.galaxy,
./tests/training_test_cases.py:308:            pytest.mark.torch,
./tests/training_test_cases.py:309:            pytest.mark.data_parallel,
./tests/training_test_cases.py:310:            pytest.mark.tensor_parallel,
./tests/training_test_cases.py:314:    pytest.param(
./tests/training_test_cases.py:321:            pytest.mark.uplift,
./tests/training_test_cases.py:322:            pytest.mark.n150,
./tests/training_test_cases.py:323:            pytest.mark.torch,
./tests/training_test_cases.py:324:            pytest.mark.single_chip,
./tests/training_test_cases.py:325:            pytest.mark.split_0,
./tests/training_test_cases.py:329:    pytest.param(
./tests/training_test_cases.py:336:            pytest.mark.xfail(reason="PCC issues, currently investigating.", strict=False),
./tests/training_test_cases.py:337:            pytest.mark.uplift,
./tests/training_test_cases.py:338:            pytest.mark.n150,
./tests/training_test_cases.py:339:            pytest.mark.torch,
./tests/training_test_cases.py:340:            pytest.mark.single_chip,
./tests/training_test_cases.py:341:            pytest.mark.split_1,
./tests/training_test_cases.py:345:    pytest.param(
./tests/training_test_cases.py:354:            pytest.mark.uplift,
./tests/training_test_cases.py:355:            pytest.mark.p150,
./tests/training_test_cases.py:356:            pytest.mark.torch,
./tests/training_test_cases.py:357:            pytest.mark.single_chip,
./tests/training_test_cases.py:361:    pytest.param(
./tests/training_test_cases.py:370:            pytest.mark.uplift,
./tests/training_test_cases.py:371:            pytest.mark.n150,
./tests/training_test_cases.py:372:            pytest.mark.torch,
./tests/training_test_cases.py:373:            pytest.mark.single_chip,
./tests/training_test_cases.py:374:            pytest.mark.split_1,
./tests/training_test_cases.py:378:    pytest.param(
./tests/training_test_cases.py:385:            pytest.mark.uplift,
./tests/training_test_cases.py:386:            pytest.mark.n150,
./tests/training_test_cases.py:387:            pytest.mark.torch,
./tests/training_test_cases.py:388:            pytest.mark.single_chip,
./tests/training_test_cases.py:392:    pytest.param(
./tests/training_test_cases.py:400:            pytest.mark.skip(reason="Jax tests are not supported yet."),
./tests/training_test_cases.py:401:            pytest.mark.uplift,
./tests/training_test_cases.py:402:            pytest.mark.n150,
./tests/training_test_cases.py:403:            pytest.mark.jax,
./tests/training_test_cases.py:404:            pytest.mark.single_chip,
./tests/training_test_cases.py:408:    pytest.param(
./tests/training_test_cases.py:416:            pytest.mark.skip(reason="Jax tests are not supported yet."),
./tests/training_test_cases.py:417:            pytest.mark.uplift,
./tests/training_test_cases.py:418:            pytest.mark.n150,
./tests/training_test_cases.py:419:            pytest.mark.jax,
./tests/training_test_cases.py:420:            pytest.mark.single_chip,
./tests/training_test_cases.py:424:    pytest.param(
./tests/training_test_cases.py:432:            pytest.mark.skip(reason="Jax tests are not supported yet."),
./tests/training_test_cases.py:433:            pytest.mark.uplift,
./tests/training_test_cases.py:434:            pytest.mark.n150,
./tests/training_test_cases.py:435:            pytest.mark.jax,
./tests/training_test_cases.py:436:            pytest.mark.single_chip,
./tests/conftest.py:4:def pytest_addoption(parser):
./tests/pytest.ini:1:[pytest]
./tests/test_all.py:9:import pytest
./tests/test_all.py:28:@pytest.fixture
./tests/test_all.py:92:            pytest.fail(f"Training script exited with code {result.returncode}")
./tests/test_all.py:95:        pytest.fail(f"Training script timed out after {setup_dict['timeout']} seconds")
./tests/test_all.py:115:        pytest.fail(f"Checkpoint not found: {checkpoint_path}")
./tests/test_all.py:121:@pytest.mark.parametrize("setup_dict", TRAINING_TEST_CASES)
./tests/test_all.py:124:    request: pytest.FixtureRequest,
./tests/test_all.py:140:        request: pytest request object.
./tests/configs/BOUNTIES/tt-gatv2_pubmed-pubmed-n150.yaml:1:# CI test overlay for GATv2/PubMed on a single Wormhole chip.
./tests/configs/tt-gemma11-math_preference_dpo-p150.yaml:1:# CI overrides for the Gemma 1.1 2B DPO experiment
./tests/trainer/test_callbacks_handler.py:8:# TODO(mmilosevicTT): Add tests to CI once we have trainings through trainer class. See https://github.com/tenstorrent/tt-blacksmith/issues/629.
./docs/shared/_templates/layout.html:41:          <a href="{{ _home }}aibs/blackhole/index.html">Blackhole™ PCIe Cards</a>
./docs/shared/_templates/layout.html:45:          <a href="{{ _home }}aibs/wormhole/index.html">Wormhole™ PCIe Cards</a>
./docs/src/introduction.md:3:The **TT-Blacksmith** project contains optimized training recipes for a variety of machine learning models on [Tenstorrent](https://tenstorrent.com/) hardware, powered by the [TT-Forge](https://github.com/tenstorrent/tt-forge) compiler stack. Showcasing the compiler's flexibility, it enables the use of popular [AI frameworks](https://github.com/tenstorrent/tt-forge?tab=readme-ov-file#current-ai-framework-front-end-projects) like PyTorch and JAX for training workflows.
./docs/src/introduction.md:6:- **Demonstrations:** Practical examples and workflows showcasing how to train various ML models on Tenstorrent hardware.
./docs/src/coding-guidelines.md:244:loss = criterion(output, target)
./README.md:20:The **TT-Blacksmith** project contains optimized training recipes for a variety of machine learning models on [Tenstorrent](https://tenstorrent.com/) hardware, powered by the [TT-Forge](https://github.com/tenstorrent/tt-forge) compiler stack. Showcasing the compiler's flexibility, it enables the use of popular [AI frameworks](https://github.com/tenstorrent/tt-forge?tab=readme-ov-file#current-ai-framework-front-end-projects) like PyTorch and JAX for training workflows.
./README.md:38:- **Demonstrations:** Practical examples and workflows showcasing how to train various ML models on Tenstorrent hardware.
./env/requirements.txt:11:pytest
./env/activate:23:# pytest alias for venv interpreter
./env/activate:24:alias pytest='python -m pytest'
./blacksmith/tools/reproducibility_manager.py:42:            torch.backends.cudnn.benchmark = False
./blacksmith/tools/cli.py:33:    # When running under pytest, apply defaults to limit training duration and
./blacksmith/tools/cli.py:64:        "--test-config", type=Path, required=False, help="[Testing utils] Configuration that is used for CI testing"
./blacksmith/tools/test_config.py:13:    This config is used during pytest runs to speed up tests by limiting
./blacksmith/experiments/torch/albert/README.md:18:mteb/banking77 is a fine-grained intent classification dataset consisting of online banking customer service queries annotated with their corresponding intents. The dataset contains 13,083 queries labeled across 77 distinct intent categories (such as 'activate_my_card', 'apple_pay', 'bank_transfer', etc.), making it significantly more challenging than previous intent detection benchmarks that typically contain fewer than 10 classes.
./blacksmith/experiments/torch/gpt_oss/README.md:88:GLUE, the General Language Understanding Evaluation benchmark (https://gluebenchmark.com/) is a
./blacksmith/experiments/torch/gemma/README.md:20:GLUE, the General Language Understanding Evaluation benchmark (https://gluebenchmark.com/) is a collection of resources for training, evaluating, and analyzing natural language understanding systems.
./blacksmith/experiments/torch/qwen/README.md:144:GLUE, the General Language Understanding Evaluation benchmark (https://gluebenchmark.com/) is a collection of resources for training, evaluating, and analyzing natural language understanding systems.
./blacksmith/experiments/torch/BOUNTIES/gatv2_pubmed/README.md:57:A golden-loss regression case (`tt-gatv2_pubmed-pubmed-n150`, config under
./blacksmith/experiments/torch/BOUNTIES/gatv2_pubmed/README.md:59:commented out until the experiment dependency and a TT runner are wired into CI.
./blacksmith/experiments/torch/gemma11/dpo/configs.py:121:    # Testing utils (used to limit training duration during CI runs).
./blacksmith/experiments/torch/gemma11/lora/README.md:48:GLUE, the General Language Understanding Evaluation benchmark (https://gluebenchmark.com/) is a collection of resources for training, evaluating, and analyzing natural language understanding systems.
./blacksmith/experiments/torch/gemma11/lora/README.md:67:The Stanford Question Answering Dataset V2.0 (SQuAD V2.0) is a challenging benchmark for extractive Question Answering (QA) models.
./blacksmith/experiments/torch/phi/README.md:22:GLUE, the General Language Understanding Evaluation benchmark (https://gluebenchmark.com/) is a collection of resources for training, evaluating, and analyzing natural language understanding systems.
./blacksmith/experiments/torch/phi/README.md:41:The Stanford Question Answering Dataset V2.0 (SQuAD V2.0) is a challenging benchmark for extractive Question Answering (QA) models.
./blacksmith/experiments/torch/llama/xla/adapters/README.md:20:GLUE, the General Language Understanding Evaluation benchmark (https://gluebenchmark.com/) is a collection of resources for training, evaluating, and analyzing natural language understanding systems.
./blacksmith/experiments/torch/llama/xla/lora/README.md:192:GLUE, the General Language Understanding Evaluation benchmark (https://gluebenchmark.com/) is a collection of resources for training, evaluating, and analyzing natural language understanding systems.
./blacksmith/experiments/torch/llama/ffe/READM

