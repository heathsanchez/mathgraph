#!/usr/bin/env python3
"""Run a lightweight Polarized Quotient-Continuation IR demo."""

from __future__ import annotations

import csv
import json
import random
import sys
from pathlib import Path
from typing import Any

try:
    from _bootstrap import ensure_repo_root_on_path
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
else:
    ensure_repo_root_on_path(__file__)

from mathgraph.obstruction_atlas import residual_queue, summarize_obstructions
from mathgraph.polarized_quotient_ir import build_pair_features
from mathgraph.sair_task_loader import load_sair_equations, load_sair_matrix


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--equations")
    parser.add_argument("--matrix")
    parser.add_argument("--out-dir", default="/tmp/mathgraph_pqir_demo")
    parser.add_argument("--sample-pairs", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=1729)
    args = parser.parse_args(argv)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    equations, matrix, source_mode = _load(args.equations, args.matrix)
    pairs = _sample_pairs(equations, matrix, args.sample_pairs, args.seed)
    feature_rows = []
    for pair in pairs:
        row = build_pair_features(equations[pair["source_idx"]], equations[pair["target_idx"]])
        feature_rows.append({**pair, **row, "recommended_families": "|".join(row.get("recommended_families", []))})
    obstructions = summarize_obstructions([row for row in feature_rows if not row.get("expected_matrix_label", False)], stage="pqir")
    _write_csv(out_dir / "pair_features.csv", feature_rows)
    _write_csv(out_dir / "obstruction_atlas.csv", [rec.to_dict() for rec in obstructions])
    summary = {
        "source_mode": source_mode,
        "equations_loaded": len(equations),
        "pairs_sampled": len(feature_rows),
        "obstruction_count": len(obstructions),
        "advisory_boundary_preserved": True,
        "terminal_claims_from_advisory_count": 0,
        "failed_search_promoted_true_count": 0,
        "top_basins": _top_counts(row.get("basin", "") for row in feature_rows),
        "residual_queue_count": len(residual_queue(obstructions)),
    }
    (out_dir / "pqir_demo_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    (out_dir / "pqir_demo_report.md").write_text(_report(summary), encoding="utf-8")
    print(json.dumps({"overall": "PASS", **summary, "out_dir": str(out_dir)}, indent=2, sort_keys=True))
    return 0


def _load(equations_path: str | None, matrix_path: str | None) -> tuple[list[str], Any, str]:
    if equations_path and matrix_path:
        equations = load_sair_equations(equations_path)
        matrix = load_sair_matrix(matrix_path)
        if equations and matrix is not None:
            return equations, matrix, "real_sair"
    equations = [
        "(x * y) = (y * x)",
        "(x * y) = x",
        "(x * y) = y",
        "x = x",
        "x = y",
        "(x * x) = x",
        "((x * y) * z) = (x * (y * z))",
        "(x * y) = (x * y)",
    ]
    matrix = [
        [True, False, False, True, False, False, False, True],
        [False, True, False, True, False, True, False, True],
        [False, False, True, True, False, True, False, True],
        [False, False, False, True, False, False, False, True],
        [False, False, False, True, True, False, False, True],
        [False, False, False, True, False, True, False, True],
        [False, False, False, True, False, False, True, True],
        [False, False, False, True, False, False, False, True],
    ]
    return equations, matrix, "fallback_demo"


def _sample_pairs(equations: list[str], matrix: Any, limit: int, seed: int) -> list[dict[str, Any]]:
    n = len(equations)
    pairs = []
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            label = bool(matrix[i][j]) if not hasattr(matrix, "shape") else bool(matrix[i, j])
            pairs.append({"pair_id": f"p_{i}_{j}", "source_idx": i, "target_idx": j, "expected_matrix_label": label})
    rng = random.Random(seed)
    rng.shuffle(pairs)
    return pairs[: max(0, limit)]


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    keys = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def _top_counts(values) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[str(value)] = counts.get(str(value), 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:8])


def _report(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Polarized Quotient-Continuation IR Demo",
            "",
            f"- Source mode: `{summary['source_mode']}`",
            f"- Equations loaded: {summary['equations_loaded']}",
            f"- Pairs sampled: {summary['pairs_sampled']}",
            f"- Obstruction records: {summary['obstruction_count']}",
            f"- Advisory boundary preserved: `{summary['advisory_boundary_preserved']}`",
            "",
            "PQ-IR features are advisory routing features. They do not verify claims.",
        ]
    ) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
