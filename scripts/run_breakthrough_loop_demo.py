#!/usr/bin/env python3
"""Run MathGraph Breakthrough Loop v1."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from mathgraph.breakthrough_demo import builtin_breakthrough_tasks, builtin_constructor_families
from mathgraph.breakthrough_loop import BreakthroughLoop, BreakthroughLoopConfig, render_breakthrough_report


def default_out_dir() -> Path:
    drive = Path("/content/drive/MyDrive/MathGraph_Lawbook/breakthrough_loop_demo")
    if drive.parent.exists():
        return drive
    return Path("/tmp/mathgraph_breakthrough_loop_demo")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the functioning MathGraph breakthrough loop demo.")
    parser.add_argument("--out-dir", default=str(default_out_dir()))
    parser.add_argument("--episodes", type=int, default=4)
    parser.add_argument("--attempts-per-task", type=int, default=1)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    db_path = out_dir / "reason_atlas.sqlite"
    out_dir.mkdir(parents=True, exist_ok=True)
    for suffix in ("", "-wal", "-shm"):
        path = Path(str(db_path) + suffix)
        if path.exists():
            path.unlink()
    loop = BreakthroughLoop(
        builtin_breakthrough_tasks(),
        builtin_constructor_families(),
        BreakthroughLoopConfig(
            episodes=args.episodes,
            attempts_per_task=args.attempts_per_task,
            out_dir=out_dir,
            reason_atlas_db=db_path,
        ),
    )
    summary = loop.run()
    print(render_breakthrough_report(summary))
    print(json.dumps({k: summary[k] for k in sorted(summary) if k != "episodes"}, indent=2, sort_keys=True))
    return 0 if summary.get("overall") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
