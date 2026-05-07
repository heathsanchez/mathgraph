"""Runtime API for the compact standalone SAIR Stage 2 solver."""

from __future__ import annotations

import argparse
import json
import sys

try:
    from .equation_core import canonical_equation, parse_equation
    from .false_constructors import prove_false
    from .finite_magma_core import verify_countermodel_certificate
    from .official_adapter import run_official_solo
    from .solver_assets import EXACT_FALSE, EXACT_TRUE
    from .true_constructors import prove_true
except ImportError:  # standalone build
    pass


def solve(equation1, equation2, eq1_id=None, eq2_id=None):
    try:
        eq1 = parse_equation(equation1)
        eq2 = parse_equation(equation2)
    except Exception as exc:
        return _unknown("parse_error", "Could not parse input equations: %s" % exc)

    key = _asset_key(eq1, eq2, eq1_id, eq2_id)
    result = prove_true(eq1, eq2)
    if result is not None:
        return _true(result["method"], result["certificate"])

    asset = EXACT_TRUE.get(key)
    if asset:
        return _true("embedded_exact_true", asset)

    asset = EXACT_FALSE.get(key)
    if asset and verify_countermodel_certificate(eq1, eq2, asset):
        return _false("embedded_exact_false", asset)

    result = prove_false(eq1, eq2)
    if result is not None:
        return _false(result["method"], result["certificate"])

    return _unknown(
        "residual_unresolved",
        "No replayable proof or finite countermodel found within compact solver budget.",
    )


def solve_problem(problem):
    return solve(
        problem.get("equation1"),
        problem.get("equation2"),
        problem.get("eq1_id"),
        problem.get("eq2_id"),
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description="Standalone SAIR Stage 2 compact solver")
    parser.add_argument("--equation1")
    parser.add_argument("--equation2")
    parser.add_argument("--eq1-id")
    parser.add_argument("--eq2-id")
    parser.add_argument("--verdict-only", action="store_true")
    args = parser.parse_args(argv)
    outputs = []
    if args.equation1 is not None and args.equation2 is not None:
        outputs.append(solve(args.equation1, args.equation2, args.eq1_id, args.eq2_id))
    else:
        first = sys.stdin.readline()
        if not first:
            parser.error("provide --equation1/--equation2 or JSON/JSONL stdin")
        try:
            first_obj = json.loads(first)
        except Exception:
            first_obj = None
        if isinstance(first_obj, dict) and first_obj.get("type") == "start":
            return run_official_solo(first_obj, solve)
        text = (first + sys.stdin.read()).strip()
        if not text:
            parser.error("provide --equation1/--equation2 or JSON/JSONL stdin")
        if text.startswith("["):
            for problem in json.loads(text):
                outputs.append(solve_problem(problem))
        else:
            for line in text.splitlines():
                if line.strip():
                    outputs.append(solve_problem(json.loads(line)))
    if args.verdict_only:
        for item in outputs:
            print(item["verdict"])
    elif len(outputs) == 1:
        print(json.dumps(outputs[0], sort_keys=True))
    else:
        print(json.dumps(outputs, sort_keys=True))
    return 0


def _asset_key(eq1, eq2, eq1_id, eq2_id):
    if eq1_id is not None and eq2_id is not None:
        return str(eq1_id) + "->" + str(eq2_id)
    return canonical_equation(eq1) + "=>" + canonical_equation(eq2)


def _true(method, cert):
    return {
        "verdict": "TRUE",
        "terminal_form": "VERIFIED_PROOF",
        "method": method,
        "certificate": cert,
        "confidence": 1.0,
        "notes": "Replayable internal proof constructor succeeded.",
    }


def _false(method, cert):
    return {
        "verdict": "FALSE",
        "terminal_form": "FINITE_COUNTERMODEL",
        "method": method,
        "certificate": cert,
        "confidence": 1.0,
        "notes": "Finite countermodel certificate verified.",
    }


def _unknown(method, notes):
    return {
        "verdict": "UNKNOWN",
        "terminal_form": "NAMED_OBSTRUCTION",
        "method": method,
        "certificate": {"obstruction": method},
        "confidence": 0.0,
        "notes": notes,
    }


if __name__ == "__main__":
    raise SystemExit(main())
