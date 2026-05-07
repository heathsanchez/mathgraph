#!/usr/bin/env python
"""Sample false pairs and summarize compact finite magma certificate coverage."""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from competitions.sair_stage2.src.equation_core import parse_equation  # noqa: E402
from competitions.sair_stage2.src.false_constructors import prove_false  # noqa: E402
from competitions.sair_stage2.src.lean_false_emitter import build_false_certificate  # noqa: E402


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--equations-path", required=True)
    parser.add_argument("--matrix-path", required=True)
    parser.add_argument("--sample-size", type=int, default=100)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args(argv)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    equations_path = Path(args.equations_path)
    matrix_path = Path(args.matrix_path)
    if not equations_path.exists() or not matrix_path.exists():
        summary = {"status": "skipped", "reason": "equations or matrix file not found"}
        _write(out_dir, summary, [])
        print(json.dumps(summary, sort_keys=True))
        return 0
    try:
        import numpy as np
    except Exception as exc:
        summary = {"status": "skipped", "reason": "numpy unavailable: %s" % exc}
        _write(out_dir, summary, [])
        print(json.dumps(summary, sort_keys=True))
        return 0

    equations = [line.strip() for line in equations_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    matrix = np.load(matrix_path)
    false_pairs = [(i, j) for i in range(len(equations)) for j in range(len(equations)) if not bool(matrix[i, j])]
    random.Random(0).shuffle(false_pairs)
    false_pairs = false_pairs[: args.sample_size]
    records = []
    families = {}
    for i, j in false_pairs:
        try:
            result = prove_false(parse_equation(equations[i]), parse_equation(equations[j]))
        except Exception:
            result = None
        if not result:
            records.append({"eq1_id": i, "eq2_id": j, "status": "not_found"})
            continue
        cert = build_false_certificate(i, j, equations[i], equations[j], result["certificate"]["table"])
        if cert is None:
            records.append({"eq1_id": i, "eq2_id": j, "status": "python_rejected"})
            continue
        data = cert.to_dict()
        data["status"] = "python_verified"
        records.append(data)
        families[data["family"]] = families.get(data["family"], 0) + 1
    summary = {
        "status": "completed",
        "sampled_false_pairs": len(false_pairs),
        "certificates_found": sum(1 for r in records if r.get("status") == "python_verified"),
        "family_counts": families,
    }
    _write(out_dir, summary, records)
    print(json.dumps(summary, sort_keys=True))
    return 0


def _write(out_dir, summary, records):
    (out_dir / "false_certificate_sample_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    with (out_dir / "false_certificate_candidates.jsonl").open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    lines = ["# False Certificate Sample", "", "```json", json.dumps(summary, indent=2, sort_keys=True), "```"]
    (out_dir / "FALSE_CERTIFICATE_SAMPLE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
