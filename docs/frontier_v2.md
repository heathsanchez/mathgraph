# Frontier Builder v2

Flat failure lists are bad frontiers. They erase the membrane geometry that
Residual Atlas v1 just recovered: near misses, saturation, obstruction pressure,
route policy priority, and representation-shift pressure.

Frontier Builder v2 turns residual atlas cases into prioritized next-episode
task proposals.

```text
Residual Atlas → Frontier tasks → task queue rows → constructor attempt → verifier/importer
```

## Task Kinds

- `finite_countermodel_search`
- `obstruction_analysis`
- `representation_shift_probe`
- `near_miss_replay`
- `suppress_or_hold`

Only `finite_countermodel_search` rows are directly compatible with the current
finite countermodel executor. The other task kinds are advisory rows for future
adapters.

## Priority Formula

`expected_value` combines membrane pressure, H-tilt priority, representation
shift score, novelty, and replay priority.

`final_priority` subtracts a saturation penalty, then clamps into `[0, 1]`.

Tasks are sorted by final priority, membrane pressure, representation-shift
score, and stable residual id.

## Task Queue Compatibility

`frontier_v2_to_task_queue_rows()` emits JSONL rows with existing queue fields:
`task_id`, `task_kind`, `source`, `target`, indices, route, constructor family,
root label, priority, origin, warnings, and evidence.

## Episode Runner v2

Episode Runner v2 consumes the Frontier v2 task queue and executes only
`finite_countermodel_search` rows. Advisory rows such as obstruction analysis,
representation-shift probes, near-miss replay, and suppressed regions become
continuation traces rather than certificate attempts.

See [Episode Runner v2](episode_runner_v2.md) for the bounded next-cycle loop.

## Multi-Episode Harness

The [Multi-Episode Compounding Harness](multi_episode_compounding.md) uses each
generated Frontier v2 task queue as the next episode input and measures whether
the residual becomes better shaped over repeated bounded loops.

## Trust Boundary

Frontier tasks are proposals. Scheduling pressure is not truth. Only the
verifier/importer path can promote terminal certificates.
