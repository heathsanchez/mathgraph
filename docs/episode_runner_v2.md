# Episode Runner v2

Episode Runner v2 is the bounded next-cycle runner for Frontier v2 task queues.
It executes only the certificate-capable subset of a frontier, records every
route as continuation trace memory, and regenerates the advisory learning
artifacts for the next episode.

```text
Frontier task queue
→ finite execution subset
→ importer revalidation
→ continuation traces
→ replay
→ route policy
→ residual atlas
→ next frontier
```

## Executable Subset

Only `finite_countermodel_search` tasks are executable in this runner.

These task kinds are preserved as advisory traces and are not executed as
certificate attempts:

- `obstruction_analysis`
- `representation_shift_probe`
- `near_miss_replay`
- `suppress_or_hold`

This keeps the current verifier/importer boundary intact. A frontier task is a
work proposal, not truth.

## Outputs

The runner writes:

- `episode_v2_report.json`
- `episode_v2_report.md`
- `input_frontier_tasks.jsonl`
- `executable_tasks.jsonl`
- `advisory_tasks.jsonl`
- `finite_countermodel_results.jsonl`
- `countermodel_import_summary.json`
- `continuation_traces.jsonl`
- `audit_report.json` when audit is enabled
- `replay/`
- `route_policy_v2/`
- `residual_atlas/`
- `next_frontier_v2/`

The trace, replay, policy, atlas, and frontier outputs are advisory learning
artifacts. They guide the next episode but do not verify or refute claims.

## CLI

```bash
python scripts/run_episode_v2.py \
  --frontier-task-queue /tmp/root_lab/frontier_v2/frontier_v2_task_queue.jsonl \
  --store /tmp/episode_v2/lawbook.sqlite \
  --out-dir /tmp/episode_v2 \
  --episode-id episode_v2_smoke \
  --max-tasks 100 \
  --max-countermodel-order 3
```

Disable regeneration stages with `--no-replay`, `--no-route-policy`,
`--no-residual-atlas`, or `--no-next-frontier`.

## Trust Boundary

- only `finite_countermodel_search` is executable
- advisory task kinds are not certificates
- finite search failure is not proof
- importer/revalidation decides finite refutation promotion
- replay, route policy, residual atlas, and frontier outputs are advisory

