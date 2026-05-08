#!/usr/bin/env python
"""Validate a standalone solver against optional ETP assets."""

from __future__ import annotations

import argparse
import importlib.util
import json
import random
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--solver", required=True)
    parser.add_argument("--equations-path")
    parser.add_argument("--matrix-path")
    parser.add_argument("--sample-size", type=int, default=100)
    parser.add_argument("--mode", choices=["sample", "all"], default="sample")
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args(argv)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if not args.equations_path or not args.matrix_path or not Path(args.equations_path).exists() or not Path(args.matrix_path).exists():
        payload = {"status": "skipped", "reason": "ETP equations or matrix file not found", "solver_size": Path(args.solver).stat().st_size if Path(args.solver).exists() else None}
        _write_outputs(out_dir, payload, [])
        print(json.dumps(payload, sort_keys=True))
        return 0
    try:
        import numpy as np  # offline validation may use numpy
    except Exception as exc:
        payload = {"status": "skipped", "reason": "numpy unavailable for matrix validation: %s" % exc}
        _write_outputs(out_dir, payload, [])
        print(json.dumps(payload, sort_keys=True))
        return 0
    equations = [line.strip() for line in Path(args.equations_path).read_text(encoding="utf-8").splitlines() if line.strip()]
    matrix = np.load(args.matrix_path)
    pairs = [(i, j) for i in range(len(equations)) for j in range(len(equations))]
    if args.mode == "sample":
        random.Random(0).shuffle(pairs)
        pairs = pairs[: args.sample_size]
    solver = _load_solver(Path(args.solver))
    errors = []
    metrics = {
        "total_tested": len(pairs),
        "answered": 0,
        "unknown": 0,
        "correct_true": 0,
        "wrong_true": 0,
        "correct_false": 0,
        "wrong_false": 0,
        "method_summary": {},
        "unsound_true_examples": [],
        "false_certificate_verification_pass_count": 0,
        "true_proof_replay_pass_count": 0,
    }
    runtimes = []
    for i, j in pairs:
        start = time.perf_counter()
        ans = solver.solve(equations[i], equations[j], i, j)
        runtimes.append(time.perf_counter() - start)
        expected = bool(matrix[i, j])
        if ans["verdict"] == "UNKNOWN":
            metrics["unknown"] += 1
            continue
        metrics["answered"] += 1
        method = ans.get("method", "unknown")
        metrics["method_summary"][method] = metrics["method_summary"].get(method, 0) + 1
        if ans["verdict"] == "TRUE":
            if expected:
                metrics["correct_true"] += 1
                if ans.get("terminal_form") == "VERIFIED_PROOF":
                    metrics["true_proof_replay_pass_count"] += 1
            else:
                metrics["wrong_true"] += 1
                if len(metrics["unsound_true_examples"]) < 20:
                    metrics["unsound_true_examples"].append({"i": i, "j": j, "equation1": equations[i], "equation2": equations[j], "answer": ans})
                errors.append({"i": i, "j": j, "expected": expected, "answer": ans})
        elif ans["verdict"] == "FALSE":
            cert_ok = solver.verify_countermodel_certificate(
                solver.parse_equation(equations[i]),
                solver.parse_equation(equations[j]),
                ans.get("certificate", {}),
            )
            if not expected and cert_ok:
                metrics["correct_false"] += 1
                metrics["false_certificate_verification_pass_count"] += 1
            else:
                metrics["wrong_false"] += 1
                errors.append({"i": i, "j": j, "expected": expected, "certificate_ok": cert_ok, "answer": ans})
    answered = metrics["answered"]
    metrics.update({
        "status": "completed",
        "coverage": answered / len(pairs) if pairs else 0.0,
        "answered_accuracy": (metrics["correct_true"] + metrics["correct_false"]) / answered if answered else 0.0,
        "avg_runtime": sum(runtimes) / len(runtimes) if runtimes else 0.0,
        "max_runtime": max(runtimes) if runtimes else 0.0,
        "solver_size": Path(args.solver).stat().st_size,
    })
    metrics["false_certificate_verification_pass"] = metrics["false_certificate_verification_pass_count"]
    metrics["true_certificate_replay_pass"] = metrics["true_proof_replay_pass_count"]
    _write_outputs(out_dir, metrics, errors)
    print(json.dumps(metrics, sort_keys=True))
    return 2 if metrics["wrong_true"] > 0 or metrics["wrong_false"] > 0 else 0


def _load_solver(path):
    spec = importlib.util.spec_from_file_location("sair_solver_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _write_outputs(out_dir, summary, errors):
    (out_dir / "validation_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    with (out_dir / "validation_errors.jsonl").open("w", encoding="utf-8") as handle:
        for err in errors:
            handle.write(json.dumps(err, sort_keys=True) + "\n")
    (out_dir / "validation_report.md").write_text("# Validation Report\n\n```json\n%s\n```\n" % json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
