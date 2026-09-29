#!/usr/bin/env python3
"""
Pinned TaskSAT semantic-boundary audit.

Witness:
  cumulative x has range=bounds=[0,10], initial 0;
  required task T assigns x := 50 at pre.

At upstream commit f9d6063b45967a3fea578c47f54806aadaafe1b0:
- the Python SMT encoding clamps accumulated/delta evolution first, then lets
  value assignment override the clamped expression;
- the executable Lean semantics applies assignment/addition first, then clamps
  the resulting value.

Therefore the Python SMT verifier makes the witness UNSAT (x=50 violates the
range constraint), while the Lean validator accepts the pinned schedule after
clamping the assignment to 10.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


UPSTREAM_SHA = "f9d6063b45967a3fea578c47f54806aadaafe1b0"


def require_in_order(text: str, needles: list[str], label: str) -> None:
    pos = -1
    for needle in needles:
        nxt = text.find(needle, pos + 1)
        if nxt < 0:
            raise AssertionError(f"{label}: missing expected source fragment: {needle!r}")
        if nxt <= pos:
            raise AssertionError(f"{label}: source-order check failed at: {needle!r}")
        pos = nxt


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasksat-root", required=True)
    ap.add_argument("--spec", required=True)
    args = ap.parse_args()

    root = Path(args.tasksat_root).resolve()
    spec = Path(args.spec).resolve()
    smt_dir = root / "src" / "smt"
    sys.path.insert(0, str(smt_dir))

    # Import the pinned upstream implementation, not a local reimplementation.
    from tasknet_parser import parse_tasknet_file
    from tasknet_transforms import apply_transforms
    from tasknet_wellformedness import check_wellformedness
    from tasknet_smt import TaskNetSMT

    tn = parse_tasknet_file(str(spec))
    tn, _ = apply_transforms(tn)

    if not check_wellformedness(tn):
        raise AssertionError("Pinned TaskSAT rejects the witness as ill-formed; audit precondition failed")

    enc = TaskNetSMT(tn, use_optimization=False, track=False)
    model, _ = enc.solve(analyze_core=False)

    if model is not None:
        try:
            evolution = enc.extract_timeline_evolution(model)
        except Exception:
            evolution = "<unavailable>"
        raise AssertionError(
            "Expected pinned Python SMT encoding to be UNSAT, but it returned a model. "
            f"Evolution: {evolution}"
        )

    # Guard the causal explanation against upstream-source drift at the frozen SHA.
    py_src = (smt_dir / "tasknet_smt.py").read_text(encoding="utf-8")
    require_in_order(
        py_src,
        [
            "raw = cur + delta",
            "clamped = If(raw < low_bnd, low_bnd,",
            "expr = clamped",
            "if isinstance(imp.how, ImpactAssign):",
            "expr = If(zi == s, val, expr)",
            "vars_z[i + 1] == expr",
        ],
        "Python cumulative transition",
    )

    lean_src = (
        root / "src" / "lean" / "TaskNetExec" / "TaskNet" / "Semantics.lean"
    ).read_text(encoding="utf-8")
    require_in_order(
        lean_src,
        [
            "match asgn? with",
            "| some v => v",
            "let resultV :=",
            "let finalV :=",
            "match bnds.get? tl with",
            "| some r => Value.realVal (clamp r low high)",
            "acc.insert tl finalV",
        ],
        "Lean applyChanges",
    )

    print(f"UPSTREAM_SHA={UPSTREAM_SHA}")
    print("TASKSAT_WELLFORMED=true")
    print("PYTHON_SMT_STATUS=UNSAT")
    print("PYTHON_ORDER=clamp_then_assignment")
    print("LEAN_SOURCE_ORDER=assignment_then_clamp")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
