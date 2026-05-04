#!/usr/bin/env python
"""Learn route/constructor diagnostics from assimilation episode directories."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mathgraph.episode_learning import EpisodeLearningConfig, learn_from_assimilation_episodes  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--episode-dir", action="append", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--progress", action="store_true")
    parser.add_argument("--heartbeat-sec", type=float, default=10.0)
    parser.add_argument("--progress-jsonl", default=None)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    result = learn_from_assimilation_episodes(
        EpisodeLearningConfig(
            episode_dirs=args.episode_dir,
            out_dir=args.out_dir,
            progress=args.progress,
            heartbeat_sec=args.heartbeat_sec,
            progress_jsonl=args.progress_jsonl,
            quiet=args.quiet,
        )
    )
    if not args.quiet:
        print(json.dumps(result.summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
