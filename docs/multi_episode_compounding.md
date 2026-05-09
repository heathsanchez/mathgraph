# Multi-Episode Compounding Harness

Episode Runner v2 closes one bounded loop. The Multi-Episode Compounding
Harness asks whether repeated loops compound.

The goal is not only to count more certificates. The diagnostic question is
whether the unknown becomes smaller, sharper, more clustered, more nameable,
more constructible, and more compressible.

```text
initial frontier
→ episode runner v2
→ next frontier
→ episode runner v2
→ compounding diagnostics
```

## Better-Shaped Unknown Metrics

- `smaller`: positive when the next frontier or residual count decreases.
- `sharper`: positive when frontier priority or recommendation concentration
  increases.
- `clustered`: positive when residual cases compress into fewer organized
  clusters.
- `nameable`: positive when obstruction naming pressure appears in organized
  clusters.
- `constructible`: positive when finite countermodel task share or verified
  finite-refutation yield improves.
- `compressible`: positive when importer-revalidated certificates coincide with
  a smaller next frontier or stronger compression signals.

`better_shaped_unknown_score` averages the available normalized components.
Missing metrics produce warnings and conservative defaults.

## Outputs

The harness writes:

- `multi_episode_report.json`
- `multi_episode_report.md`
- `episode_summaries.jsonl`
- one `episode_i/` directory per Episode Runner v2 run

Each episode directory contains its own reproducible input frontier, executable
task queue, advisory task queue, finite results, importer summary, continuation
traces, replay, route policy, residual atlas, and next frontier.

## CLI

```bash
python scripts/run_multi_episode_harness.py \
  --initial-frontier-task-queue /tmp/root_lab/frontier_v2/frontier_v2_task_queue.jsonl \
  --store /tmp/multi_episode/lawbook.sqlite \
  --out-dir /tmp/multi_episode \
  --episodes 3 \
  --max-tasks-per-episode 50 \
  --max-countermodel-order 3
```

## Trust Boundary

- multi-episode metrics are diagnostics
- compounding score does not verify or refute claims
- failed finite search is not proof
- only importer-revalidated certificates cross the terminal boundary
- advisory task kinds remain advisory

