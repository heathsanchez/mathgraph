"""Official Stage 2 adapter hooks for the compact solver."""

from __future__ import annotations

import json
import sys

try:
    from .lean_false_emitter import build_false_certificate, emit_false_judge_call
except ImportError:  # standalone build
    pass


def official_contract_mode(contract=None):
    """Return a compact runtime mode inferred from an inspected contract."""

    contract = contract or {}
    location = _value(contract.get("expected_solver_location"))
    return {
        "expected_solver_location": location or "solver.py",
        "supports_solve_function": True,
        "supports_cli": True,
        "notes": "Adapter preserves solve()/solve_problem()/CLI unless the official contract requires narrowing.",
    }


def read_official_stdin(stdin=None):
    """Parse official-compatible stdin.

    Current adapter keeps JSON/JSONL compatibility and leaves official-specific
    narrowing to contract evidence.
    """

    text = (stdin or sys.stdin).read().strip()
    if not text:
        return []
    if text.startswith("["):
        return json.loads(text)
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def run_official_solo(startup, solve_fn, stdin=None, stdout=None):
    """Run the official Solo stdin/stdout judge protocol.

    The compact solver only submits certificates it can render as Lean source.
    At present that means finite countermodel certificates. Internal TRUE
    constructors remain useful for local API mode, but they are not submitted as
    Lean proofs until a real Lean renderer is added.
    """

    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout
    problem = startup.get("problem", {})
    result = solve_fn(
        problem.get("equation1", ""),
        problem.get("equation2", ""),
        problem.get("eq1_id"),
        problem.get("eq2_id"),
    )
    if result.get("terminal_form") == "FINITE_COUNTERMODEL":
        cert = build_false_certificate(
            problem.get("eq1_id"),
            problem.get("eq2_id"),
            problem.get("equation1", ""),
            problem.get("equation2", ""),
            result.get("certificate", {}).get("table", []),
        )
        if cert is None:
            return 0
        print(json.dumps(emit_false_judge_call(cert)), file=stdout, flush=True)
        try:
            stdin.readline()
        except Exception:
            pass
    return 0


def make_false_lean_code(cert):
    return emit_false_judge_call(cert)["code"]


def _value(field):
    if isinstance(field, dict):
        return field.get("value")
    return field
