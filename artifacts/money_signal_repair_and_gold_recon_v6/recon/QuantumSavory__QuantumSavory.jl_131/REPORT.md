# Gold Recon Report

## Verdict

`PARK_WEB3_SECURITY_RISK`

## Decision

```json
{
  "repo": "QuantumSavory/QuantumSavory.jl",
  "num": 131,
  "url": "https://github.com/QuantumSavory/QuantumSavory.jl/issues/131",
  "title": "More thorough benchmarks [$200]",
  "state": "OPEN",
  "updatedAt": "2026-06-29T02:55:38Z",
  "reason": "$200 benchmark route, likely real judged route",
  "amount_estimate": 200.0,
  "money": true,
  "local_judge": true,
  "benchmark_or_metric": true,
  "has_surface": true,
  "prompt_risk": false,
  "hardware_risk": false,
  "web3_risk": true,
  "verdict": "PARK_WEB3_SECURITY_RISK"
}
```

## Issue body excerpt

<details>
<summary><strong>Bug bounty logistic details</strong> (click to expand)</summary>

To claim exclusive time to work on this bounty either post a comment here or message [skrastanov@umass.edu](mailto:skrastanov@umass.edu) with:

- your name
- github username
- **(optional)** a brief list of previous pertinent projects you have engaged in

If you want to, you can work on this project without making a claim, however claims are encouraged to give you and other contributors peace of mind. Whoever has made a claim takes precedence when solutions are considered.

You can always propose your own funded project, if you would like to contribute something of value that is not yet covered by an official bounty.
</details>

# Project: "More thorough benchmarks" [$200]

We have a small benchmark suite already implemented, which is executed as part of our CI runs. It is defined in the `benchmark` folder and reported for each pull request. **We would like to expand this benchmark suite** to include many more facets of this library. E.g. basic register operations using a variety of backends; queries and tags and locks on registers and channels; time to import; time to run examples. The new benchmarks should be legible, easy to follow, and organized by topic. Most of them should be microbenchmarks testing only one concept, but a few holistic benchmarks would make sense as well.

**Required skills**: Generic Julia skills.

**Reviewer**: Stefan Krastanov

**Duration**: 1 month

#### Payout procedure:

The Funding for these bounties comes from the National Science Foundation and from the NSF Center for Quantum Networks. The payouts are managed by the NumFOCUS foundation and processed in bulk once every two months. If you live in a country in which NumFOCUS can make payments, you can participate in this bounty program.

[Click here for more details about the bug bounty program.](https://github.com/QuantumSavory/.github/blob/main/BUG_BOUNTIES.md)

## Cheap commands

```text
pwd=/Users/heath/Documents/mathgraph-lean-work/external/money_gold_recon_v6/QuantumSavory__QuantumSavory.jl_131

Julia Project.toml found.

julia not installed locally; cannot run Pkg.test without setup.

workflows:
.github/workflows/benchmark.yml
.github/workflows/changelog-enforcer.yml
.github/workflows/ci.yml
.github/workflows/downgrade.yml
.github/workflows/spelling.yml
.github/workflows/TagBot.yml

```

## Inventory excerpt

```text
.agents/channels/classical-and-quantum-channels-dev.md
.agents/channels/classical-and-quantum-channels-user.md
.agents/evals/anythingllm-eval-results.csv
.agents/evals/anythingllm-eval-results.md
.agents/evals/anythingllm-eval-results.png
.agents/evals/codex-grade-schema.json
.agents/evals/dataset/abstraction-boundaries-A.md
.agents/evals/dataset/abstraction-boundaries-Q.md
.agents/evals/dataset/abstraction-boundaries.yaml
.agents/evals/dataset/async-timing-A.md
.agents/evals/dataset/async-timing-Q.md
.agents/evals/dataset/async-timing.yaml
.agents/evals/dataset/backend-extension-A.md
.agents/evals/dataset/backend-extension-Q.md
.agents/evals/dataset/backend-extension.yaml
.agents/evals/dataset/channel-modeling-A.md
.agents/evals/dataset/channel-modeling-Q.md
.agents/evals/dataset/channel-modeling.yaml
.agents/evals/dataset/choose-backend-bosonic-A.md
.agents/evals/dataset/choose-backend-bosonic-Q.md
.agents/evals/dataset/choose-backend-bosonic.yaml
.agents/evals/dataset/choose-backend-stabilizer-A.md
.agents/evals/dataset/choose-backend-stabilizer-Q.md
.agents/evals/dataset/choose-backend-stabilizer.yaml
.agents/evals/dataset/classical-coordination-A.md
.agents/evals/dataset/classical-coordination-Q.md
.agents/evals/dataset/classical-coordination.yaml
.agents/evals/dataset/classical-vs-quantum-transport-A.md
.agents/evals/dataset/classical-vs-quantum-transport-Q.md
.agents/evals/dataset/classical-vs-quantum-transport.yaml
.agents/evals/dataset/debugging-inspection-A.md
.agents/evals/dataset/debugging-inspection-Q.md
.agents/evals/dataset/debugging-inspection.yaml
.agents/evals/dataset/delayed-quantum-channel-A.md
.agents/evals/dataset/delayed-quantum-channel-Q.md
.agents/evals/dataset/delayed-quantum-channel.yaml
.agents/evals/dataset/factorization-time-noise-A.md
.agents/evals/dataset/factorization-time-noise-Q.md
.agents/evals/dataset/factorization-time-noise.yaml
.agents/evals/dataset/first-steps-A.md
.agents/evals/dataset/first-steps-Q.md
.agents/evals/dataset/first-steps.yaml
.agents/evals/dataset/live-visualization-A.md
.agents/evals/dataset/live-visualization-Q.md
.agents/evals/dataset/live-visualization.yaml
.agents/evals/dataset/modeling-limitations-A.md
.agents/evals/dataset/modeling-limitations-Q.md
.agents/evals/dataset/modeling-limitations.yaml
.agents/evals/dataset/noninstant-gates-A.md
.agents/evals/dataset/noninstant-gates-Q.md
.agents/evals/dataset/noninstant-gates.yaml
.agents/evals/dataset/performance-bottlenecks-A.md
.agents/evals/dataset/performance-bottlenecks-Q.md
.agents/evals/dataset/performance-bottlenecks.yaml
.agents/evals/dataset/qchannel-routing-A.md
.agents/evals/dataset/qchannel-routing-Q.md
.agents/evals/dataset/qchannel-routing.yaml
.agents/evals/dataset/register-vs-regnet-A.md
.agents/evals/dataset/register-vs-regnet-Q.md
.agents/evals/dataset/register-vs-regnet.yaml
.agents/evals/dataset/repeater-stack-plan-A.md
.agents/evals/dataset/repeater-stack-plan-Q.md
.agents/evals/dataset/repeater-stack-plan.yaml
.agents/evals/dataset/representable-hardware-A.md
.agents/evals/dataset/representable-hardware-Q.md
.agents/evals/dataset/representable-hardware.yaml
.agents/evals/dataset/scope-overview-A.md
.agents/evals/dataset/scope-overview-Q.md
.agents/evals/dataset/scope-overview.yaml
.agents/evals/dataset/state-explorer-A.md
.agents/evals/dataset/state-explorer-Q.md
.agents/evals/dataset/state-explorer.yaml
.agents/evals/dataset/stateszoo-extension-A.md
.agents/evals/dataset/stateszoo-extension-Q.md
.agents/evals/dataset/stateszoo-extension.yaml
.agents/evals/dataset/supported-protocols-A.md
.agents/evals/dataset/supported-protocols-Q.md
.agents/evals/dataset/supported-protocols.yaml
.agents/evals/dataset/symbolic-frontend-A.md
.agents/evals/dataset/symbolic-frontend-Q.md
.agents/evals/dataset/symbolic-frontend.yaml
.agents/evals/dataset/wait-for-tags-A.md
.agents/evals/dataset/wait-for-tags-Q.md
.agents/evals/dataset/wait-for-tags.yaml
.agents/evals/dataset/weighted-states-A.md
.agents/evals/dataset/weighted-states-Q.md
.agents/evals/dataset/weighted-states.yaml
.agents/evals/dataset/zoo-selection-A.md
.agents/evals/dataset/zoo-selection-Q.md
.agents/evals/dataset/zoo-selection.yaml
.agents/evals/evaluate_anythingllm.jl
.agents/evals/Project.toml
.agents/evals/README.md
.agents/metadata/tags-queries-dev.md
.agents/metadata/tags-queries-user.md
.agents/registers/register-interface-user.md
.agents/registers/register-internals-and-backend-hooks.md
.agents/zoos/circuit-zoo-dev.md
.agents/zoos/circuit-zoo-user.md
.agents/zoos/protocol-zoo-dev.md
.agents/zoos/protocol-zoo-user.md
.agents/zoos/states-zoo-dev.md
.agents/zoos/states-zoo-user.md
.buildkite/pipeline.yml
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
.git
```

## Grep excerpt

```text
===== money / judge / benchmark / test hits =====
./benchmark/benchmark_tagquery.jl:3:function tagquery_interfacetest()
./benchmark/benchmark_tagquery.jl:33:SUITE["tagquery"]["misc"]["from_tests"] = @benchmarkable tagquery_interfacetest()
./benchmark/benchmark_tagquery.jl:45:SUITE["tagquery"]["register"]["query"] = @benchmarkable @benchmark query(reg, EntanglementCounterpart, 6, ❓; filo=true)
./benchmark/benchmark_tagquery.jl:46:SUITE["tagquery"]["register"]["queryall"] = @benchmarkable @benchmark queryall(reg, EntanglementCounterpart, 6, ❓; filo=true)
./benchmark/benchmark_tagquery.jl:59:SUITE["tagquery"]["messagebuffer"]["query"] = @benchmarkable query(mb, EntanglementCounterpart, 6, ❓)
./benchmark/benchmark_tagquery.jl:60:SUITE["tagquery"]["messagebuffer"]["querydelete"] = @benchmarkable querydelete!(_mb, EntanglementCounterpart, 6, ❓) setup=(_mb = deepcopy(mb))  evals=1
./benchmark/benchmark_tagquery.jl:78:SUITE["tagquery"]["register"]["query_exact_filo"] = @benchmarkable query(reg_mixed, EntanglementCounterpart, 1, 12)
./benchmark/benchmark_tagquery.jl:79:SUITE["tagquery"]["register"]["query_exact_fifo"] = @benchmarkable query(reg_mixed, EntanglementCounterpart, 1, 12; filo=false)
./benchmark/benchmark_tagquery.jl:80:SUITE["tagquery"]["register"]["query_predicate"] = @benchmarkable query(reg_mixed, EntanglementCounterpart, ==(2), >(120))
./benchmark/benchmark_tagquery.jl:81:SUITE["tagquery"]["register"]["query_tag_dispatch"] = @benchmarkable query(reg_mixed, Tag(EntanglementCounterpart, 1, 12))
./benchmark/benchmark_tagquery.jl:82:SUITE["tagquery"]["register"]["query_miss"] = @benchmarkable query(reg_mixed, EntanglementCounterpart, 99, ❓)
./benchmark/benchmark_tagquery.jl:83:SUITE["tagquery"]["register"]["query_assigned"] = @benchmarkable query(reg_mixed, EntanglementCounterpart, 1, ❓; assigned=true, locked=false)
./benchmark/benchmark_tagquery.jl:84:SUITE["tagquery"]["register"]["query_unassigned"] = @benchmarkable query(reg_mixed, EntanglementCounterpart, 1, ❓; assigned=false, locked=false)
./benchmark/benchmark_tagquery.jl:85:SUITE["tagquery"]["register"]["query_locked"] = @benchmarkable query(reg_mixed, EntanglementCounterpart, 1, ❓; locked=true)
./benchmark/benchmark_tagquery.jl:86:SUITE["tagquery"]["register"]["queryall_filo"] = @benchmarkable queryall(reg_mixed, EntanglementCounterpart, 1, ❓; filo=true)
./benchmark/benchmark_tagquery.jl:87:SUITE["tagquery"]["register"]["queryall_fifo"] = @benchmarkable queryall(reg_mixed, EntanglementCounterpart, 1, ❓; filo=false)
./benchmark/benchmark_tagquery.jl:88:SUITE["tagquery"]["register"]["queryall_tag_dispatch"] = @benchmarkable queryall(reg_mixed, Tag(EntanglementCounterpart, 2, 22))
./benchmark/benchmark_tagquery.jl:91:# benchmark RegRef dispatch separately because it skips cross-slot checks.
./benchmark/benchmark_tagquery.jl:100:SUITE["tagquery"]["register_ref"]["query_filo"] = @benchmarkable query(reg_ref[1], EntanglementCounterpart, 4, 9)
./benchmark/benchmark_tagquery.jl:101:SUITE["tagquery"]["register_ref"]["query_fifo"] = @benchmarkable query(reg_ref[1], EntanglementCounterpart, 4, 9; filo=false)
./benchmark/benchmark_tagquery.jl:102:SUITE["tagquery"]["register_ref"]["queryall_filo"] = @benchmarkable queryall(reg_ref[1], EntanglementCounterpart, 4, 9)
./benchmark/benchmark_tagquery.jl:103:SUITE["tagquery"]["register_ref"]["queryall_fifo"] = @benchmarkable queryall(reg_ref[1], EntanglementCounterpart, 4, 9; filo=false)
./benchmark/benchmark_tagquery.jl:104:SUITE["tagquery"]["register_ref"]["query_tag_dispatch"] = @benchmarkable query(reg_ref[1], Tag(EntanglementCounterpart, 4, 9))
./benchmark/benchmark_tagquery.jl:107:# These benchmarks use deepcopy in setup so each evaluation runs on a fresh state.
./benchmark/benchmark_tagquery.jl:109:SUITE["tagquery"]["register_mutating"]["querydelete_regref_filo"] = @benchmarkable querydelete!(_slot, EntanglementCounterpart, 4, 9) setup=(_reg = deepcopy(reg_ref); _slot = _reg[1]) evals=1
./benchmark/benchmark_tagquery.jl:110:SUITE["tagquery"]["register_mutating"]["querydelete_regref_fifo"] = @benchmarkable querydelete!(_slot, EntanglementCounterpart, 4, 9; filo=false) setup=(_reg = deepcopy(reg_ref); _slot = _reg[1]) evals=1
./benchmark/benchmark_tagquery.jl:111:SUITE["tagquery"]["register_mutating"]["querydelete_register"] = @benchmarkable querydelete!(_reg, EntanglementCounterpart, 4, 9) setup=(_reg = deepcopy(reg_ref)) evals=1
./benchmark/benchmark_tagquery.jl:112:SUITE["tagquery"]["register_mutating"]["untag_by_id"] = @benchmarkable untag!(_reg, _id) setup=(_reg = deepcopy(reg_ref); _id = query(_reg[1], EntanglementCounterpart, 4, 9).id) evals=1
./benchmark/benchmark_tagquery.jl:120:SUITE["tagquery"]["register_high_arity"]["query_exact"] = @benchmarkable query(reg_long, :longtag, 1, 2, 3, 4, 5, 6)
./benchmark/benchmark_tagquery.jl:121:SUITE["tagquery"]["register_high_arity"]["query_predicate"] = @benchmarkable query(reg_long, :longtag, ==(1), ==(2), ==(3), ==(4), ==(5), >(5))
./benchmark/benchmark_tagquery.jl:122:SUITE["tagquery"]["register_high_arity"]["queryall"] = @benchmarkable queryall(reg_long, :longtag, 1, 2, 3, 4, 5, ❓)
./benchmark/benchmark_tagquery.jl:125:# We benchmark fast-hit and deep-scan cases, plus mutating deletes.
./benchmark/benchmark_tagquery.jl:140:SUITE["tagquery"]["messagebuffer"]["query_tag_dispatch"] = @benchmarkable query(mb_back, Tag(:flow, 1, 2, 3, 4, 5, 6))
./benchmark/benchmark_tagquery.jl:141:SUITE["tagquery"]["messagebuffer"]["query_high_arity"] = @benchmarkable query(mb_back, :flow, 1, 2, 3, 4, 5, 6)
./benchmark/benchmark_tagquery.jl:142:SUITE["tagquery"]["messagebuffer"]["query_high_arity_predicate"] = @benchmarkable query(mb_back, :flow, ==(1), ==(2), >(2), >(3), >(4), >(5))
./benchmark/benchmark_tagquery.jl:143:SUITE["tagquery"]["messagebuffer"]["query_miss"] = @benchmarkable query(mb_back, :flow, 10, 20, 30, 40, 50, 60)
./benchmark/benchmark_tagquery.jl:144:SUITE["tagquery"]["messagebuffer"]["querydelete_front"] = @benchmarkable querydelete!(_mb, :flow, 1, 2, 3, 4, 5, 6) setup=(_mb = deepcopy(mb_front)) evals=1
./benchmark/benchmark_tagquery.jl:145:SUITE["tagquery"]["messagebuffer"]["querydelete_back"] = @benchmarkable querydelete!(_mb, :flow, 1, 2, 3, 4, 5, 6) setup=(_mb = deepcopy(mb_back)) evals=1
./benchmark/benchmark_tagquery.jl:146:SUITE["tagquery"]["messagebuffer"]["querydelete_miss"] = @benchmarkable querydelete!(_mb, :flow, 10, 20, 30, 40, 50, 60) setup=(_mb = deepcopy(mb_back)) evals=1
./benchmark/benchmark_tagquery.jl:212:SUITE["tagquery"]["index_selectivity"]["register_head_query_rare"] = @benchmarkable query(reg_head_selective, :distilled, 1)
./benchmark/benchmark_tagquery.jl:213:SUITE["tagquery"]["index_selectivity"]["register_head_queryall_rare"] = @benchmarkable queryall(reg_queryall_selective, :distilled, ❓)
./benchmark/benchmark_tagquery.jl:214:SUITE["tagquery"]["index_selectivity"]["register_slot_query_rare"] = @benchmarkable query(reg_slot_selective[1], :entangled, 1)
./benchmark/benchmark_tagquery.jl:215:SUITE["tagquery"]["index_selectivity"]["register_slot_queryall_rare"] = @benchmarkable queryall(reg_slot_selective[1], :entangled, ❓)
./benchmark/benchmark_tagquery.jl:216:SUITE["tagquery"]["index_selectivity"]["messagebuffer_query_rare_back"] = @benchmarkable query(mb_head_selective, :distilled, 1)
./benchmark/benchmark_tagquery.jl:217:SUITE["tagquery"]["index_selectivity"]["messagebuffer_query_rare_miss"] = @benchmarkable query(mb_head_selective_miss, :distilled, 999)
./benchmark/benchmark_tagquery.jl:218:SUITE["tagquery"]["index_selectivity"]["messagebuffer_query_missing_head"] = @benchmarkable query(mb_missing_head_selective, :error_corrected, ❓)
./benchmark/benchmark_tagquery.jl:219:SUITE["tagquery"]["index_selectivity"]["messagebuffer_querydelete_rare_back"] = @benchmarkable querydelete!(_mb, :distilled, 1) setup=(_mb = deepcopy(mb_head_selective)) evals=1
./benchmark/benchmark_semaphore.jl:59:SUITE["change_notifier"]["api"]["lock_direct"] = @benchmarkable lock(notifier) setup=(sim =
```
