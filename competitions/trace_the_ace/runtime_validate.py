#!/usr/bin/env python3
"""Rule/runtime validation helpers for a frozen Trace the Ace submission.

This script is intentionally model-agnostic. It validates the generated
submission contract, compares frozen research/runtime predictions, and checks
sample-independence fixtures produced by the runtime candidate.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd


def read_headers(path: Path) -> list[str]:
    return list(pd.read_csv(path, nrows=0).columns)


def validate_output(fmt_path: Path, pred_path: Path) -> dict:
    print("submission_format columns:", read_headers(fmt_path))
    print("submission columns:", read_headers(pred_path))
    fmt = pd.read_csv(fmt_path)
    pred = pd.read_csv(pred_path)
    required = ["response_id", "probability"]
    if list(pred.columns) != required:
        raise SystemExit(f"FAIL columns: expected {required}, got {list(pred.columns)}")
    if len(pred) != len(fmt):
        raise SystemExit(f"FAIL row count: {len(pred)} != {len(fmt)}")
    if pred.response_id.duplicated().any():
        raise SystemExit("FAIL duplicate response_id")
    if pred.response_id.astype(str).tolist() != fmt.response_id.astype(str).tolist():
        raise SystemExit("FAIL response IDs/order differ from submission_format")
    p = pred.probability.to_numpy(float)
    if not np.isfinite(p).all():
        raise SystemExit("FAIL non-finite probability")
    if ((p < 0) | (p > 1)).any():
        raise SystemExit("FAIL probability outside [0,1]")
    result = {
        "rows": int(len(p)),
        "min_probability": float(p.min()),
        "max_probability": float(p.max()),
        "lt_0p01": int((p < .01).sum()),
        "gt_0p99": int((p > .99).sum()),
        "quantiles": {str(q): float(np.quantile(p, q)) for q in [0,.001,.01,.05,.5,.95,.99,.999,1]},
    }
    print(json.dumps(result, indent=2))
    return result


def compare_predictions(a_path: Path, b_path: Path, tol: float) -> dict:
    print("reference columns:", read_headers(a_path))
    print("runtime columns:", read_headers(b_path))
    a = pd.read_csv(a_path)
    b = pd.read_csv(b_path)
    if "response_id" not in a or "probability" not in a or "response_id" not in b or "probability" not in b:
        raise SystemExit("FAIL comparison inputs need response_id,probability")
    m = a[["response_id","probability"]].merge(
        b[["response_id","probability"]], on="response_id", suffixes=("_a","_b"), validate="one_to_one"
    )
    if len(m) != len(a) or len(m) != len(b):
        raise SystemExit("FAIL comparison response ID sets differ")
    d = np.abs(m.probability_a.to_numpy(float) - m.probability_b.to_numpy(float))
    result = {"rows": int(len(m)), "max_abs_difference": float(d.max(initial=0)), "tolerance": tol}
    print(json.dumps(result, indent=2))
    if result["max_abs_difference"] > tol:
        raise SystemExit("FAIL prediction parity")
    return result


def independence(paths: list[Path], response_id: str, tol: float) -> dict:
    vals = []
    for path in paths:
        print(f"{path.name} columns:", read_headers(path))
        df = pd.read_csv(path)
        hit = df.loc[df.response_id.astype(str) == str(response_id), "probability"]
        if len(hit) != 1:
            raise SystemExit(f"FAIL {path}: expected one row for {response_id}, got {len(hit)}")
        vals.append(float(hit.iloc[0]))
    spread = max(vals) - min(vals)
    result = {"response_id": str(response_id), "probabilities": vals, "spread": spread, "tolerance": tol}
    print(json.dumps(result, indent=2))
    if spread > tol:
        raise SystemExit("FAIL sample independence")
    return result


def self_test() -> None:
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        fmt = pd.DataFrame({"response_id":["a","b"], "probability":[0.5,0.5]})
        p = pd.DataFrame({"response_id":["a","b"], "probability":[0.2,0.8]})
        fmt.to_csv(root/"fmt.csv", index=False); p.to_csv(root/"p.csv", index=False); p.to_csv(root/"q.csv", index=False)
        validate_output(root/"fmt.csv", root/"p.csv")
        compare_predictions(root/"p.csv", root/"q.csv", 1e-8)
        independence([root/"p.csv", root/"q.csv"], "a", 1e-8)
    print("SELF TEST PASS")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("self-test")
    p = sub.add_parser("output"); p.add_argument("--format", required=True); p.add_argument("--predictions", required=True)
    p = sub.add_parser("parity"); p.add_argument("--reference", required=True); p.add_argument("--runtime", required=True); p.add_argument("--tol", type=float, default=1e-8)
    p = sub.add_parser("independence"); p.add_argument("--response-id", required=True); p.add_argument("--predictions", nargs="+", required=True); p.add_argument("--tol", type=float, default=1e-8)
    args = ap.parse_args()
    if args.cmd == "self-test": self_test()
    elif args.cmd == "output": validate_output(Path(args.format), Path(args.predictions))
    elif args.cmd == "parity": compare_predictions(Path(args.reference), Path(args.runtime), args.tol)
    else: independence([Path(x) for x in args.predictions], args.response_id, args.tol)

if __name__ == "__main__":
    main()
