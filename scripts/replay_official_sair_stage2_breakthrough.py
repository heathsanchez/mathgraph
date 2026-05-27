#!/usr/bin/env python
"""Replay the official SAIR Stage 2 breakthrough evidence pack."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Sequence


DEFAULT_EQUATIONS = "/content/equations.txt"
DEFAULT_MATRIX = "/content/etp_matrix_full_best_bool.npy"
DEFAULT_OUT_DIR = "/content/drive/MyDrive/SAIR_MathGraph/official_sair_stage2_breakthrough_replay"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def build_replay_command(
    *,
    equations: str = DEFAULT_EQUATIONS,
    matrix: str = DEFAULT_MATRIX,
    out_dir: str = DEFAULT_OUT_DIR,
    quick: bool = False,
    fail_if_no_compounding: bool = True,
) -> list[str]:
    if quick:
        seeds = "20260524,20260525"
        train_false = "1000"
        heldout_false = "1000"
        sample_true = "500"
        episodes = "3"
        repair_budget = "30"
        rounds = "3"
    else:
        seeds = "20260524,20260525,20260526,20260527,20260528"
        train_false = "2500"
        heldout_false = "2500"
        sample_true = "1000"
        episodes = "4"
        repair_budget = "40"
        rounds = "5"
    command = [
        sys.executable,
        str(repo_root() / "scripts" / "run_sair_stage2_breakthrough_search.py"),
        "--equations",
        equations,
        "--matrix",
        matrix,
        "--out-dir",
        out_dir,
        "--seeds",
        seeds,
        "--episodes",
        episodes,
        "--max-n",
        "4",
        "--repair-budget",
        repair_budget,
        "--train-false",
        train_false,
        "--heldout-false",
        heldout_false,
        "--sample-true",
        sample_true,
        "--policy-search-rounds",
        rounds,
        "--strict-admission",
    ]
    if fail_if_no_compounding:
        command.append("--fail-if-no-compounding")
    return command


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--equations", default=DEFAULT_EQUATIONS)
    parser.add_argument("--matrix", default=DEFAULT_MATRIX)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--quick", action="store_true")
    mode.add_argument("--full", action="store_true")
    parser.add_argument("--no-fail-if-no-compounding", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    command = build_replay_command(
        equations=args.equations,
        matrix=args.matrix,
        out_dir=args.out_dir,
        quick=args.quick,
        fail_if_no_compounding=not args.no_fail_if_no_compounding,
    )
    print("Running official SAIR Stage 2 breakthrough replay:")
    print(" ".join(_quote(part) for part in command))
    result = subprocess.run(command, cwd=repo_root())
    _print_compact_summary(Path(args.out_dir) / "breakthrough_search_summary.json")
    return int(result.returncode)


def _print_compact_summary(path: Path) -> None:
    if not path.exists():
        print(f"No summary found at {path}")
        return
    summary = json.loads(path.read_text(encoding="utf-8"))
    keys = [
        "final_classification",
        "real_sair_used",
        "finite_checked_countermodels",
        "accepted_false_certificates",
        "total_gain_over_baseline",
        "lawbook_gain_over_baseline",
        "failed_search_promoted_true_count",
        "advisory_promoted_truth_count",
        "true_contamination_count",
        "selected_components",
        "rejected_components",
    ]
    compact = {key: summary.get(key) for key in keys}
    print(json.dumps(compact, indent=2, sort_keys=True))


def _quote(value: str) -> str:
    if not value or any(ch.isspace() for ch in value):
        return repr(value)
    return value


if __name__ == "__main__":
    raise SystemExit(main())
