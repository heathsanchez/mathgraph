## Problem

Replay artifacts report judge outcomes through `tally`, `decisive_margin`, and per-task `rows`. Promotion, regression, and leaderboard tooling consume those fields, but nothing verifies they agree. A hand-edited artifact could inflate `decisive_margin` while per-task rows tell a different story.

## Proposal

Add `benchmark/tally_integrity.py` and `scripts/tally_integrity.py` that verify, for each scored replay slice:

- `tally` carries numeric challenger/baseline/tie counts that sum to `tasks`
- when `rows` are present, `len(rows) == tasks` and winner labels recount to the same tally
- `decisive_margin` equals `challenger - baseline` when present

Support single-repo, multi-repo `per_repo` entries, and `--generalization` partitions. Expose a `--strict` CLI exit code for CI gating.

## Acceptance

- Offline unit tests under `tests/test_tally_integrity.py`
- `ruff check .` and `VANGUARSTEW_OFFLINE=1 python -m pytest -q` pass