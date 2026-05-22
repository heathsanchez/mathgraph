#!/usr/bin/env python3
"""Run the Real SAIR multi-episode artifact pack."""

from __future__ import annotations

import argparse
import json

from mathgraph.real_sair_artifact_pack import RealSairArtifactPackConfig, RealSairArtifactPackRunner


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--equations-path", default="/content/equations.txt")
    parser.add_argument("--matrix-path", default="/content/etp_matrix_full_best_bool.npy")
    parser.add_argument("--output-dir")
    parser.add_argument("--lawbook-path")
    parser.add_argument("--num-episodes", type=int, default=3)
    parser.add_argument("--episode-size", type=int, default=250)
    parser.add_argument("--train-fraction", type=float, default=0.5)
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--max-attempts-per-episode", type=int)
    parser.add_argument("--run-label")
    parser.add_argument("--strict-admission", dest="strict_admission", action="store_true", default=True)
    parser.add_argument("--non-strict-admission", dest="strict_admission", action="store_false")
    parser.add_argument("--create-archive", dest="create_archive", action="store_true", default=True)
    parser.add_argument("--no-archive", dest="create_archive", action="store_false")
    parser.add_argument("--allow-fallback-smoke", dest="allow_fallback", action="store_true", default=False)
    args = parser.parse_args()
    result = RealSairArtifactPackRunner(
        RealSairArtifactPackConfig(
            equations_path=args.equations_path,
            matrix_path=args.matrix_path,
            output_dir=args.output_dir,
            lawbook_path=args.lawbook_path,
            num_episodes=args.num_episodes,
            episode_size=args.episode_size,
            train_fraction=args.train_fraction,
            seed=args.seed,
            strict_admission=args.strict_admission,
            allow_fallback=args.allow_fallback,
            create_archive=args.create_archive,
            max_attempts_per_episode=args.max_attempts_per_episode,
            run_label=args.run_label,
        )
    ).run()
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

