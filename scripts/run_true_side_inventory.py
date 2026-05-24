#!/usr/bin/env python
"""Build a bounded TRUE-side proof-template inventory for ETP."""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mathgraph.hashing import content_id
from mathgraph.lawbook import init_lawbook, upsert_run_summary, write_dataframe
from mathgraph.lean_artifacts import generate_true_congruence_lean_skeleton, write_lean_artifacts
from mathgraph.polarized_quotient_ir import build_pair_features
from mathgraph.promotion_gate import decide_promotion
from mathgraph.proof_congruence import explain_bounded_congruence
from mathgraph.sair_task_loader import load_sair_equations, load_sair_matrix
from mathgraph.true_proof_templates import classify_true_pair


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    equations, matrix, source_mode = _load_inputs(args)
    true_pairs, false_pairs = _sample_pairs(matrix, len(equations), args)
    run_id = f"true_inventory_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{args.seed}"
    template_rows: list[dict[str, Any]] = []
    trace_rows: list[dict[str, Any]] = []
    promotion_rows: list[dict[str, Any]] = []
    false_audit_rows: list[dict[str, Any]] = []

    for i, j in true_pairs:
        eq1, eq2 = equations[i], equations[j]
        features = build_pair_features(eq1, eq2, max_depth=min(args.max_depth, 2))
        trace = explain_bounded_congruence(eq1, eq2, max_depth=args.max_depth)
        trace_row = {"run_id": run_id, "trace_id": content_id("congruence-trace", trace.to_dict()), "eq1_id": i, "eq2_id": j, **trace.to_dict()}
        trace_rows.append(trace_row)
        classification = classify_true_pair(eq1, eq2, features, trace)
        template_row = {
            "run_id": run_id,
            "template_id": content_id("true-proof-template", {"i": i, "j": j, "classification": classification}),
            "eq1_id": i,
            "eq2_id": j,
            "equation1": eq1,
            "equation2": eq2,
            **classification,
        }
        template_rows.append(template_row)
        decision = decide_promotion(trace_row if trace.forced_equal else template_row)
        promotion_rows.append({"run_id": run_id, "decision_id": content_id("promotion-decision-row", {"i": i, "j": j}), "eq1_id": i, "eq2_id": j, **decision.to_dict()})

    for i, j in false_pairs:
        record = {"status": "finite_failed_small_n", "eq1_id": i, "eq2_id": j, "finite_search_miss": True}
        decision = decide_promotion(record)
        false_audit_rows.append({"run_id": run_id, "eq1_id": i, "eq2_id": j, **decision.to_dict()})

    artifacts = [generate_true_congruence_lean_skeleton(row) for row in trace_rows[: args.lean_artifact_limit]]
    lean_rows = write_lean_artifacts(out_dir / "lean_artifacts", artifacts)
    conn = init_lawbook(out_dir / "lawbook.sqlite")
    write_dataframe(conn, "true_proof_templates", template_rows)
    write_dataframe(conn, "congruence_explain_traces", trace_rows)
    write_dataframe(conn, "lean_artifacts", lean_rows)
    write_dataframe(conn, "promotion_decisions", promotion_rows + false_audit_rows)
    summary = _summary(args, out_dir, source_mode, equations, matrix, true_pairs, false_pairs, template_rows, trace_rows, promotion_rows, false_audit_rows, lean_rows)
    upsert_run_summary(conn, run_id, summary)
    conn.close()

    outputs = {
        "true_inventory_summary.json": summary,
        "true_inventory_report.md": _report(summary),
        "true_proof_template_inventory.csv": template_rows,
        "congruence_explain_traces.csv": trace_rows,
        "false_control_promotion_audit.csv": false_audit_rows,
        "promotion_gate_report.csv": promotion_rows + false_audit_rows,
        "lean_artifacts_manifest.csv": lean_rows,
    }
    for name, payload in outputs.items():
        if name.endswith(".json"):
            (out_dir / name).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        elif name.endswith(".md"):
            (out_dir / name).write_text(str(payload), encoding="utf-8")
        else:
            _write_csv(out_dir / name, payload)
    print(f"source_mode: {source_mode}")
    print(f"true_pairs_sampled: {len(true_pairs)}")
    print(f"false_controls_sampled: {len(false_pairs)}")
    print(f"templates_generated: {len(template_rows)}")
    print(f"bounded_forced_count: {summary['bounded_forced_count']}")
    print(f"false_controls_promoted_true: {summary['false_controls_promoted_true']}")
    print(f"output_dir: {out_dir}")
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--equations")
    parser.add_argument("--matrix")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--sample-true", type=int, default=5000)
    parser.add_argument("--sample-false-control", type=int, default=5000)
    parser.add_argument("--max-depth", type=int, default=3)
    parser.add_argument("--seed", type=int, default=20260524)
    parser.add_argument("--tiny-demo", action="store_true")
    parser.add_argument("--lean-artifact-limit", type=int, default=12)
    return parser


def _load_inputs(args: argparse.Namespace) -> tuple[list[str], Any, str]:
    if args.tiny_demo:
        return _tiny_equations(), _tiny_matrix(), "fallback_tiny_demo"
    if not args.equations or not args.matrix:
        raise SystemExit("--equations and --matrix are required unless --tiny-demo is used")
    equations = load_sair_equations(args.equations)
    matrix = load_sair_matrix(args.matrix)
    if not equations or matrix is None:
        raise SystemExit("ETP/SAIR inputs could not be loaded; use --tiny-demo for fallback")
    return equations, matrix, "real_etp"


def _sample_pairs(matrix: Any, n: int, args: argparse.Namespace) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    if args.tiny_demo:
        return [(0, 0), (1, 1), (1, 4), (3, 3), (5, 5)], [(0, 1), (0, 2), (3, 4), (6, 1)]
    rng = random.Random(args.seed)
    limit = min(n, int(matrix.shape[0]), int(matrix.shape[1]))
    true_pairs: list[tuple[int, int]] = []
    false_pairs: list[tuple[int, int]] = []
    attempts = 0
    while (len(true_pairs) < args.sample_true or len(false_pairs) < args.sample_false_control) and attempts < (args.sample_true + args.sample_false_control) * 200:
        attempts += 1
        i, j = rng.randrange(limit), rng.randrange(limit)
        if i == j:
            if len(true_pairs) < args.sample_true:
                true_pairs.append((i, j))
            continue
        if bool(matrix[i, j]) and len(true_pairs) < args.sample_true:
            true_pairs.append((i, j))
        elif not bool(matrix[i, j]) and len(false_pairs) < args.sample_false_control:
            false_pairs.append((i, j))
    return true_pairs, false_pairs


def _summary(args: argparse.Namespace, out_dir: Path, source_mode: str, equations: list[str], matrix: Any, true_pairs: list[tuple[int, int]], false_pairs: list[tuple[int, int]], templates: list[dict[str, Any]], traces: list[dict[str, Any]], promotions: list[dict[str, Any]], false_audit: list[dict[str, Any]], lean_rows: list[dict[str, Any]]) -> dict[str, Any]:
    false_promoted = sum(1 for row in false_audit if row.get("terminal_form") == "VERIFIED_PROOF" and row.get("accepted"))
    bounded = sum(1 for row in traces if row.get("forced_equal"))
    gates = {
        "data_loaded": len(equations) > 0,
        "true_pairs_sampled": len(true_pairs) > 0,
        "false_controls_sampled": len(false_pairs) > 0,
        "templates_generated": len(templates) > 0,
        "false_controls_not_promoted_true": false_promoted == 0,
        "failed_search_not_true": all(row.get("promotion_status") == "RESIDUAL" for row in false_audit),
        "promotion_gate_enforced": all(not row.get("can_promote_truth", False) for row in promotions if row.get("trust_level") in {"BOUNDED_CERT", "CANDIDATE_PROOF_TEMPLATE"}),
        "lawbook_written": (out_dir / "lawbook.sqlite").exists(),
        "lean_artifacts_written": len(lean_rows) > 0,
        "no_unverified_lean_claims": all(not row.get("verified", False) and not row.get("can_promote_truth", False) for row in lean_rows),
    }
    return {
        "source_mode": source_mode,
        "real_corpus_used": source_mode == "real_etp",
        "fallback_mode": source_mode != "real_etp",
        "output_dir": str(out_dir),
        "equations_loaded": len(equations),
        "matrix_shape": list(getattr(matrix, "shape", (len(equations), len(equations)))),
        "true_pairs_sampled": len(true_pairs),
        "false_controls_sampled": len(false_pairs),
        "templates_generated": len(templates),
        "bounded_forced_count": bounded,
        "lean_artifacts_written": len(lean_rows),
        "false_controls_promoted_true": false_promoted,
        "advisory_boundary_preserved": false_promoted == 0 and gates["promotion_gate_enforced"],
        "gates": [{"gate": key, "passed": bool(value)} for key, value in gates.items()],
    }


def _report(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# TRUE-Side Proof Inventory",
            "",
            f"- source_mode: {summary['source_mode']}",
            f"- equations_loaded: {summary['equations_loaded']}",
            f"- true_pairs_sampled: {summary['true_pairs_sampled']}",
            f"- false_controls_sampled: {summary['false_controls_sampled']}",
            f"- templates_generated: {summary['templates_generated']}",
            f"- bounded_forced_count: {summary['bounded_forced_count']}",
            f"- false_controls_promoted_true: {summary['false_controls_promoted_true']}",
            f"- advisory_boundary_preserved: {summary['advisory_boundary_preserved']}",
            "",
            "Bounded congruence traces and Lean skeletons are candidate proof-template artifacts. They are not LEAN_VERIFIED.",
            "",
        ]
    )


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = sorted({key for row in rows for key in row.keys()}) or ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _csv_value(row.get(key)) for key in fieldnames})


def _csv_value(value: Any) -> Any:
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, sort_keys=True)
    return value


def _tiny_equations() -> list[str]:
    return [
        "(x * y) = (y * x)",
        "(x * y) = x",
        "(x * y) = y",
        "x = x",
        "(x * x) = x",
        "((x * y) * z) = (x * (y * z))",
    ]


def _tiny_matrix() -> Any:
    import numpy as np

    n = 6
    matrix = np.zeros((n, n), dtype=bool)
    for i in range(n):
        matrix[i, i] = True
    matrix[1, 4] = True
    return matrix


if __name__ == "__main__":
    raise SystemExit(main())
