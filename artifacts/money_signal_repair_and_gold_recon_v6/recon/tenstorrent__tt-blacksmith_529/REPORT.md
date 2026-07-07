# Gold Recon Report

## Verdict

`PARK_HARDWARE_REQUIRED`

## Decision

```json
{
  "repo": "tenstorrent/tt-blacksmith",
  "num": 529,
  "url": "https://github.com/tenstorrent/tt-blacksmith/issues/529",
  "title": "[Bounty $2000] GraphSAGE training workload on Tenstorrent",
  "state": "OPEN",
  "updatedAt": "2026-06-15T08:39:07Z",
  "reason": "$2000 GraphSAGE workload; hardware gated, maybe ask milestone split",
  "amount_estimate": 2000.0,
  "money": true,
  "local_judge": true,
  "benchmark_or_metric": true,
  "has_surface": true,
  "prompt_risk": false,
  "hardware_risk": true,
  "web3_risk": false,
  "verdict": "PARK_HARDWARE_REQUIRED"
}
```

## Issue body excerpt

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

## Cheap commands

```text
pwd=/Users/heath/Documents/mathgraph-lean-work/external/money_gold_recon_v6/tenstorrent__tt-blacksmith_529

workflows:
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

```

## Inventory excerpt

```text
.cursor/skills/perf-benchmark-single-chip/reference.md
.cursor/skills/perf-benchmark-single-chip/SKILL.md
.flake8-config
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
.git/objects/pack/pack-05104cede8fa3c0217b97aba07a0fbc28837d60e.idx
.git/objects/pack/pack-05104cede8fa3c0217b97aba07a0fbc28837d60e.pack
.git/objects/pack/pack-05104cede8fa3c0217b97aba07a0fbc28837d60e.promisor
.git/objects/pack/pack-372ea34c9ee5d5ce1aae209ddfad8c644f35a9b4.idx
.git/objects/pack/pack-372ea34c9ee5d5ce1aae209ddfad8c644f35a9b4.pack
.git/objects/pack/pack-372ea34c9ee5d5ce1aae209ddfad8c644f35a9b4.promisor
.git/packed-refs
.git/refs/heads/main
.git/shallow
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
tests/configs/tt-llama_3_1_8b-sst2-d
```

## Grep excerpt

```text
===== money / judge / benchmark / test hits =====
./.cursor/skills/perf-benchmark-single-chip/reference.md:3:## tt-perf-report metrics
./.cursor/skills/perf-benchmark-single-chip/reference.md:65:| `ops_perf_results_<timestamp>.csv` | **Primary** -- per-op device metrics. Feed to `tt-perf-report`. |
./.cursor/skills/perf-benchmark-single-chip/SKILL.md:2:name: perf-benchmark-single-chip
./.cursor/skills/perf-benchmark-single-chip/SKILL.md:3:description: Run device performance benchmarks for tt-blacksmith single-chip training workloads. Use when the user asks to benchmark, profile, or measure performance of a training workload on Tenstorrent hardware, or mentions tracy, tt-perf-report, or device time analysis.
./.cursor/skills/perf-benchmark-single-chip/SKILL.md:6:# Single-chip perf benchmark
./.cursor/skills/perf-benchmark-single-chip/SKILL.md:27:Before running any workload, ensure no stale processes are holding the TT device. A previous process that was force-killed (kill -9) leaves the device in a bad state, causing "Timeout waiting for Ethernet core service" or "Waiting for lock 'CHIP_IN_USE_*_PCIe'" errors.
./.cursor/skills/perf-benchmark-single-chip/SKILL.md:107:- The sync must come **after backward**, not between forward and backward. Calls like `loss.item()` force an implicit sync -- move them after backward or remove them when benchmarking.
./.cursor/skills/perf-benchmark-single-chip/SKILL.md:133:Then in the training loop, place the early stopping check **immediately after `global_step` is incremented** -- before any logging, validation, metric commits, cache clearing, or checkpointing. If early stopping comes after these, a validation pass at the final step will run unnecessarily, wasting minutes and polluting the Tracy trace.
./.cursor/skills/perf-benchmark-single-chip/SKILL.md:137:    tracy.signpost("benchmark_complete")
./.cursor/skills/perf-benchmark-single-chip/SKILL.md:182:Find the latest report and copy for analysis:
./.cursor/skills/perf-benchmark-single-chip/SKILL.md:207:For metric details, see [reference.md](reference.md).
./.cursor/skills/perf-benchmark-single-chip/SKILL.md:249:- **"Timeout waiting for Ethernet core service" / "Waiting for lock 'CHIP_IN_USE_*_PCIe'"**: Kill all stale Python processes, then reset all devices: `tt-smi -r`. Wait a few seconds before starting a new process.
./LICENSE:168:      and charge a fee for, acceptance of support, warranty, indemnity,
./LICENSE:211:- googletest - https://github.com/google/googletest/blob/main/LICENSE
./.flake8-config:22:    .pytest_cache,
./tests/training_test_cases.py:4:import pytest
./tests/training_test_cases.py:8:    pytest.param(
./tests/training_test_cases.py:10:            "test_script": "blacksmith/experiments/torch/mnist/tensor_parallel/train.py",
./tests/training_test_cases.py:15:            pytest.mark.push,
./tests/training_test_cases.py:16:            pytest.mark.n300,
./tests/training_test_cases.py:17:            pytest.mark.torch,
./tests/training_test_cases.py:18:            pytest.mark.tensor_parallel,
./tests/training_test_cases.py:22:    pytest.param(
./tests/training_test_cases.py:24:            "test_script": "blacksmith/experiments/torch/mnist/data_parallel/train.py",
./tests/training_test_cases.py:29:            pytest.mark.push,
./tests/training_test_cases.py:30:            pytest.mark.n300,
./tests/training_test_cases.py:31:            pytest.mark.torch,
./tests/training_test_cases.py:32:            pytest.mark.data_parallel,
./tests/training_test_cases.py:36:    pytest.param(
./tests/training_test_cases.py:38:            "test_script": "blacksmith/experiments/torch/mnist/train.py",
./tests/training_test_cases.py:43:            pytest.mark.push,
./tests/training_test_cases.py:44:            pytest.mark.n150,
./tests/training_test_cases.py:45:            pytest.mark.n300,
./tests/training_test_cases.py:46:            pytest.mark.torch,
./tests/training_test_cases.py:47:            pytest.mark.single_chip,
./tests/training_test_cases.py:51:    # Bounty #453 (GATv2/PubMed). Disabled in CI until the experiment-specific
./tests/training_test_cases.py:52:    # torch_geometric dependency and a TT runner are wired into the regression pipeline;
./tests/training_test_cases.py:53:    # the golden config lives in tests/configs/BOUNTIES/. Re-enable by uncommenting.
./tests/training_test_cases.py:54:    # pytest.param(
./tests/training_test_cases.py:56:    #         "test_script": "blacksmith/experiments/torch/BOUNTIES/gatv2_pubmed/train.py",
./tests/training_test_cases.py:58:    #         "test_config": "tests/configs/BOUNTIES/tt-gatv2_pubmed-pubmed-n150.yaml",
./tests/training_test_cases.py:62:    #         pytest.mark.uplift,
./tests/training_test_cases.py:63:    #         pytest.mark.n150,
./tests/training_test_cases.py:64:    #         pytest.mark.n300,
./tests/training_test_cases.py:65:    #         pytest.mark.torch,
./tests/training_test_cases.py:66:    #         pytest.mark.single_chip,
./tests/training_test_cases.py:70:    pytest.param(
./tests/training_test_cases.py:72:            "test_script": "blacksmith/experiments/jax/mnist/multi_chip/data_parallel/train.py",
./tests/training_test_cases.py:78:            pytest.mark.uplift,
./tests/training_test_cases.py:79:            pytest.mark.n300,
./tests/training_test_cases.py:80:            pytest.mark.jax,
./tests/training_test_cases.py:81:            pytest.mark.data_parallel,
./tests/training_test_cases.py:85:    pytest.param(
./tests/training_test_cases.py:87:            "test_script": "blacksmith/experiments/jax/mnist/single_chip/train.py",
./tests/training_test_cases.py:93:            pytest.mark.uplift,
./tests/training_test_cases.py:94:            pytest.mark.n150,
./tests/training_test_cases.py:95:            pytest.mark.jax,
./tests/training_test_cases.py:96:            pytest.mark.single_chip,
./tests/training_test_cases.py:100:    pytest.param(
./tests/training_test_cases.py:102:            "test_script": "blacksmith/experiments/jax/mnist/single_chip/train_flax.py",
./tests/training_test_cases.py:108:            pytest.mark.uplift,
./tests/training_test_cases.py:109:            pytest.mark.n150,
./tests/training_test_cases.py:110:            pytest.mark.jax,
./tests/training_test_cases.py:111:            pytest.mark.single_chip,
./tests/training_test_cases.py:115:    pytest.param(
./tests/training_test_cases.py:117:            "test_script": "blacksmith/experiments/jax/mnist/multi_chip/tensor_parallel/train.py",
./tests/training_test_cases.py:123:            pytest.mark.skip(
./tests/training_test_cases.py:126:            pytest.mark.uplift,
./tests/training_test_cases.py:127:            pytest.mark.n300,
./tests/training_test_cases.py:128:            pytest.mark.jax,
./tests/training_test_cases.py:129:            pytest.mark.tensor_parallel,
./tests/training_test_cases.py:134:        pytest.param(
./tests/training_test_cases.py:136:                "test_script": "blacksmith/experiments/torch/llama/xla/train.py",
./tests/training_test_cases.py:138:                "test_config": "tests/configs/tt-llama_3_2_1b-sst2-n150.yaml",
./tests/training_test_cases.py:139:                "test_checkpoint_path": test_checkpoint_path,
./tests/training_test_cases.py:143:                pytest.mark.uplift,
./tests/training_test_cases.py:144:                pytest.mark.n150,
./tests/training_test_cases.py:145:                pytest.mark.torch,
./tests/training_test_cases.py:146:                pytest.mark.single_chip,
./tests/training_test_cases.py:147:                pytest.mark.split_0,
./tests/training_test_cases.py:151:        for i, test_checkpoint_path in enumerate(
./tests/training_test_cases.py:154:                "tests/checkpoints/tt-llama_3_2_1b-sst2-n150_checkpoint_step1340_epoch0_20260325_211954.pt",
./tests/training_test_cases.py:155:                "tests/checkpoints/tt-llama_3_2_1b-sst2-n150_checkpoint_step2680_epoch0_20260326_081459.pt",
./tests/training_test_cases.py:159:    pytest.param(
./tests/t
```
