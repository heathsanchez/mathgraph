#!/usr/bin/env python3
"""Run Multi-Episode Lawbook Compounding Evaluation v0."""

from __future__ import annotations

import argparse
import json

from mathgraph.multi_episode_compounding import MultiEpisodeCompoundingRunner, MultiEpisodeConfig


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--equations-path", default="/content/equations.txt")
    parser.add_argument("--matrix-path", default="/content/etp_matrix_full_best_bool.npy")
    parser.add_argument("--lawbook-path")
    parser.add_argument("--output-dir", default="/tmp/mathgraph_multi_episode_compounding")
    parser.add_argument("--num-episodes", type=int, default=3)
    parser.add_argument("--episode-size", type=int, default=250)
    parser.add_argument("--train-fraction", type=float, default=0.5)
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--max-attempts-per-episode", type=int)
    parser.add_argument("--strict-admission", dest="strict_admission", action="store_true", default=True)
    parser.add_argument("--non-strict-admission", dest="strict_admission", action="store_false")
    fallback = parser.add_mutually_exclusive_group()
    fallback.add_argument("--allow-fallback", dest="allow_fallback", action="store_true", default=True)
    fallback.add_argument("--no-fallback", dest="allow_fallback", action="store_false")
    args = parser.parse_args()
    result = MultiEpisodeCompoundingRunner(
        MultiEpisodeConfig(
            equations_path=args.equations_path,
            matrix_path=args.matrix_path,
            lawbook_path=args.lawbook_path,
            output_dir=args.output_dir,
            num_episodes=args.num_episodes,
            episode_size=args.episode_size,
            train_fraction=args.train_fraction,
            seed=args.seed,
            strict_admission=args.strict_admission,
            allow_fallback=args.allow_fallback,
            max_attempts_per_episode=args.max_attempts_per_episode,
        )
    ).run()
    print(
        json.dumps(
            {
                "real_sair_used": result.real_sair_used,
                "fallback_mode": result.fallback_mode,
                "num_episodes": result.num_episodes,
                "advisory_boundary_preserved": result.advisory_boundary_preserved,
                "compounding_signal_detected": result.compounding_signal_detected,
                "fallback_smoke_compounding_signal": result.fallback_smoke_compounding_signal,
                "outputs": result.outputs,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

