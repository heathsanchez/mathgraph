#!/usr/bin/env python
"""Run advisory micro-basin causal distillation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd

from mathgraph.microbasin_distillation import DistillationConfig, run_microbasin_distillation


def _write_fallback_inputs(input_dir: Path) -> None:
    input_dir.mkdir(parents=True, exist_ok=True)
    pair_features = pd.DataFrame(
        [
            {"seed": 1729, "pair_idx": 0, "eq1_id": 0, "eq2_id": 1, "basin": "projection_pressure", "deep_ir_candidate": "high_gradient", "quotient_pressure": 2, "target_separation_pressure": 3, "ir_constraint_loss": 2, "fresh_variable_escape_count": 0, "repeat_tail_pressure": 1, "skeleton_equal": False},
            {"seed": 1729, "pair_idx": 1, "eq1_id": 0, "eq2_id": 2, "basin": "projection_pressure", "deep_ir_candidate": "high_gradient", "quotient_pressure": 2, "target_separation_pressure": 3, "ir_constraint_loss": 2, "fresh_variable_escape_count": 0, "repeat_tail_pressure": 1, "skeleton_equal": False},
            {"seed": 1729, "pair_idx": 2, "eq1_id": 0, "eq2_id": 3, "basin": "projection_pressure", "deep_ir_candidate": "high_gradient", "quotient_pressure": 2, "target_separation_pressure": 3, "ir_constraint_loss": 2, "fresh_variable_escape_count": 0, "repeat_tail_pressure": 1, "skeleton_equal": False},
            {"seed": 1729, "pair_idx": 3, "eq1_id": 3, "eq2_id": 4, "basin": "fresh_variable_escape", "deep_ir_candidate": "fresh_gate", "quotient_pressure": 0, "target_separation_pressure": 1, "ir_constraint_loss": 1, "fresh_variable_escape_count": 1, "repeat_tail_pressure": 0, "skeleton_equal": True},
            {"seed": 1729, "pair_idx": 4, "eq1_id": 5, "eq2_id": 6, "basin": "fresh_variable_escape", "deep_ir_candidate": "fresh_gate", "quotient_pressure": 0, "target_separation_pressure": 1, "ir_constraint_loss": 1, "fresh_variable_escape_count": 1, "repeat_tail_pressure": 0, "skeleton_equal": True},
        ]
    )
    recovery = pd.DataFrame(
        [
            {"seed": 1729, "pair_idx": 0, "eq1_id": 0, "eq2_id": 1, "generic_recovered": False, "lawbook_recovered": True},
            {"seed": 1729, "pair_idx": 1, "eq1_id": 0, "eq2_id": 2, "generic_recovered": False, "lawbook_recovered": True},
            {"seed": 1729, "pair_idx": 2, "eq1_id": 0, "eq2_id": 3, "generic_recovered": False, "lawbook_recovered": True},
            {"seed": 1729, "pair_idx": 3, "eq1_id": 3, "eq2_id": 4, "generic_recovered": False, "lawbook_recovered": False},
            {"seed": 1729, "pair_idx": 4, "eq1_id": 5, "eq2_id": 6, "generic_recovered": True, "lawbook_recovered": True},
        ]
    )
    manifest = pd.DataFrame(
        [
            {"seed": 1729, "rank": 0, "family": "projection_exception_left", "cid": "c_proj_left", "constructor_idx": 1, "advisory_only": True, "can_promote_truth": False},
            {"seed": 1729, "rank": 1, "family": "fresh_gate_right", "cid": "c_fresh", "constructor_idx": 2, "advisory_only": True, "can_promote_truth": False},
        ]
    )
    terminal = pd.DataFrame(
        [
            {"status": "RESIDUAL", "terminal_form": "NONE", "trust_level": "RESIDUAL_EVIDENCE", "accepted": False, "advisory_only": True, "can_promote_truth": False, "reason": "fallback residual"}
        ]
    )
    pair_features.to_csv(input_dir / "heldout_pair_features.csv", index=False)
    recovery.to_csv(input_dir / "heldout_recovery_eval.csv", index=False)
    manifest.to_csv(input_dir / "train_lawbook_manifest.csv", index=False)
    terminal.to_csv(input_dir / "terminal_form_audit.csv", index=False)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--min-microbasin-support", type=int, default=3)
    parser.add_argument("--min-microbasin-gain", type=int, default=1)
    parser.add_argument("--top-k-families", type=int, default=12)
    parser.add_argument("--top-k-constructors", type=int, default=12)
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--no-strict-safety", action="store_true")
    parser.add_argument("--fallback-demo", action="store_true")
    args = parser.parse_args(argv)

    out_dir = Path(args.out_dir)
    input_dir = Path(args.input_dir) if args.input_dir else out_dir / "_fallback_input"
    if args.fallback_demo:
        _write_fallback_inputs(input_dir)
    elif not args.input_dir:
        raise SystemExit("--input-dir is required unless --fallback-demo is used")
    result = run_microbasin_distillation(
        DistillationConfig(
            input_dir=input_dir,
            out_dir=out_dir,
            min_microbasin_support=args.min_microbasin_support,
            min_microbasin_gain=args.min_microbasin_gain,
            top_k_families=args.top_k_families,
            top_k_constructors=args.top_k_constructors,
            seed=args.seed,
            strict_safety=not args.no_strict_safety,
        )
    )
    print(json.dumps(result.summary, indent=2, sort_keys=True))
    return 0 if result.summary["safety"]["safety_passed"] or args.no_strict_safety else 2


if __name__ == "__main__":
    raise SystemExit(main())
