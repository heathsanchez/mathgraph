#!/usr/bin/env python
"""Validate emitted FALSE Lean certificates against the official judge when possible."""

from __future__ import annotations

import argparse
import importlib.util
import json
import random
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--official-repo", default=str(ROOT / "official" / "equational-theories-lean-stage2"))
    parser.add_argument("--solver", default=str(ROOT / "dist" / "solver.py"))
    parser.add_argument("--equations-path")
    parser.add_argument("--matrix-path")
    parser.add_argument("--sample-size", type=int, default=50)
    parser.add_argument("--false-only", action="store_true")
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args(argv)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    pairs_payload = _load_false_pairs(args.equations_path, args.matrix_path, args.sample_size)
    if pairs_payload["status"] != "loaded":
        _write_outputs(out_dir, pairs_payload, [])
        print(json.dumps(pairs_payload, sort_keys=True))
        return 0

    judge = _load_official_judge(Path(args.official_repo))
    records = []
    counts = {
        "sampled_false_pairs": len(pairs_payload["pairs"]),
        "certificates_emitted": 0,
        "python_verified_false_certificates": 0,
        "official_accepted": 0,
        "unparsed": 0,
        "malformed": 0,
        "incomplete_proof": 0,
        "incorrect": 0,
        "official_not_run": 0,
        "unknown_or_not_emitted": 0,
    }
    for i, j, e1, e2 in pairs_payload["pairs"]:
        started = time.perf_counter()
        message, stderr = _run_solver_official(Path(args.solver), i, j, e1, e2)
        elapsed = time.perf_counter() - started
        if not message or message.get("call") != "judge":
            counts["unknown_or_not_emitted"] += 1
            records.append({"eq1_id": i, "eq2_id": j, "status": "not_emitted", "stderr": stderr, "elapsed_s": elapsed})
            continue
        code = message.get("code", "")
        counts["certificates_emitted"] += 1
        if message.get("verdict") == "false":
            counts["python_verified_false_certificates"] += 1
        status = "official_not_run"
        judge_result = {}
        if judge is not None:
            try:
                answer = json.dumps({"verdict": message.get("verdict"), "code": code})
                problem = {"id": "mg_%s_%s" % (i, j), "eq1_id": int(i), "eq2_id": int(j), "equation1": e1, "equation2": e2}
                judge_result = judge.verify_answer(problem, answer)
                status = judge_result.get("status", "unknown")
            except Exception as exc:
                status = "official_not_run"
                judge_result = {"error": str(exc)}
        count_key = "official_accepted" if status == "accepted" else status
        if count_key not in counts:
            count_key = "official_not_run"
        counts[count_key] = counts.get(count_key, 0) + 1
        records.append({
            "eq1_id": i,
            "eq2_id": j,
            "verdict": message.get("verdict"),
            "status": status,
            "code_hash": _hash_text(code),
            "code_bytes": len(code.encode("utf-8")),
            "elapsed_s": elapsed,
            "stderr": stderr,
            "judge_result": judge_result,
            "code": code,
        })

    accepted_bytes = [r["code_bytes"] for r in records if r.get("status") == "accepted"]
    summary = dict(counts)
    summary.update({
        "status": "completed",
        "official_repo": str(Path(args.official_repo)),
        "solver": str(Path(args.solver)),
        "official_judge_available": judge is not None,
        "bytes_per_accepted_certificate": (sum(accepted_bytes) / len(accepted_bytes)) if accepted_bytes else None,
        "top_failure_statuses": _failure_counts(records),
    })
    _write_outputs(out_dir, summary, records)
    print(json.dumps(summary, sort_keys=True))
    return 0


def _load_false_pairs(equations_path, matrix_path, sample_size):
    if not equations_path or not matrix_path or not Path(equations_path).exists() or not Path(matrix_path).exists():
        return {"status": "skipped", "reason": "equations or matrix file not found"}
    try:
        import numpy as np
    except Exception as exc:
        return {"status": "skipped", "reason": "numpy unavailable: %s" % exc}
    equations = [line.strip() for line in Path(equations_path).read_text(encoding="utf-8").splitlines() if line.strip()]
    matrix = np.load(matrix_path)
    pairs = [(i, j, equations[i], equations[j]) for i in range(len(equations)) for j in range(len(equations)) if not bool(matrix[i, j])]
    random.Random(0).shuffle(pairs)
    return {"status": "loaded", "pairs": pairs[:sample_size]}


def _load_official_judge(repo):
    verify_path = repo / "judge" / "verify.py"
    if not verify_path.exists():
        return None
    try:
        if str(repo) not in sys.path:
            sys.path.insert(0, str(repo))
        spec = importlib.util.spec_from_file_location("official_stage2_judge_verify", verify_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except Exception:
        return None


def _run_solver_official(solver, eq1_id, eq2_id, equation1, equation2):
    startup = {"type": "start", "problem": {"id": "mg_%s_%s" % (eq1_id, eq2_id), "eq1_id": int(eq1_id), "eq2_id": int(eq2_id), "equation1": equation1, "equation2": equation2}, "budget": {}}
    proc = subprocess.run(
        [sys.executable, str(solver)],
        input=json.dumps(startup) + "\n{}\n",
        text=True,
        capture_output=True,
        timeout=20,
    )
    first = proc.stdout.splitlines()[0] if proc.stdout.splitlines() else ""
    try:
        return json.loads(first), proc.stderr
    except Exception:
        return None, proc.stderr


def _hash_text(text):
    h = 2166136261
    for ch in text:
        h ^= ord(ch)
        h = (h * 16777619) & 0xFFFFFFFF
    return "%08x" % h


def _failure_counts(records):
    counts = {}
    for record in records:
        status = record.get("status")
        if status != "accepted":
            counts[status] = counts.get(status, 0) + 1
    return counts


def _write_outputs(out_dir, summary, records):
    (out_dir / "official_certificate_validation.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    with (out_dir / "official_certificate_validation.jsonl").open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    lines = ["# Official Certificate Validation", "", "```json", json.dumps(summary, indent=2, sort_keys=True), "```", "", "## Top failing snippets"]
    for record in records[:10]:
        if record.get("status") != "accepted":
            lines.append("- `%s -> %s`: %s `%s`" % (record.get("eq1_id"), record.get("eq2_id"), record.get("status"), record.get("code_hash", "")))
    (out_dir / "OFFICIAL_CERTIFICATE_VALIDATION.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
