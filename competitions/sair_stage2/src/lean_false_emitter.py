"""Build and emit official Lean judge calls for FALSE certificates."""

from __future__ import annotations

try:
    from .certificate_models import FiniteMagmaCertificate
    from .equation_core import parse_equation
    from .finite_magma_core import find_violation, satisfies_equation, verify_countermodel_certificate
    from .lean_templates import render_false_countermodel_lean
except ImportError:  # standalone build
    pass


def build_false_certificate(eq1_id, eq2_id, equation1, equation2, table, parser=None, evaluator=None):
    """Return a Python-verified finite magma certificate, or ``None``.

    Matrix truth and search misses are ignored here. The table must satisfy the
    source equation for all assignments and violate the target equation at a
    concrete witness assignment.
    """

    parser = parser or parse_equation
    try:
        eq1 = parser(equation1)
        eq2 = parser(equation2)
        table_t = tuple(tuple(int(x) for x in row) for row in table)
        if not satisfies_equation(eq1, table_t):
            return None
        violation = find_violation(eq2, table_t)
        if violation is None:
            return None
        raw = {
            "carrier_size": len(table_t),
            "table": [list(row) for row in table_t],
            "violating_assignment": dict(violation["assignment"]),
            "source_satisfied": True,
            "target_violated": True,
            "target_lhs": violation["lhs"],
            "target_rhs": violation["rhs"],
        }
        if not verify_countermodel_certificate(eq1, eq2, raw):
            return None
        return FiniteMagmaCertificate(
            eq1_id=eq1_id,
            eq2_id=eq2_id,
            equation1=equation1,
            equation2=equation2,
            n=len(table_t),
            table=[list(row) for row in table_t],
            witness=dict(violation["assignment"]),
            source_holds_verified_python=True,
            target_fails_verified_python=True,
            family=_table_family(table_t),
            method="finite_table_search",
        )
    except Exception:
        return None


def emit_false_judge_call(cert):
    if isinstance(cert, dict):
        cert = FiniteMagmaCertificate.from_dict(cert)
    return {
        "call": "judge",
        "verdict": "false",
        "code": render_false_countermodel_lean(cert),
    }


def _table_family(table):
    n = len(table)
    if all(table[i][j] == i for i in range(n) for j in range(n)):
        return "left_projection"
    if all(table[i][j] == j for i in range(n) for j in range(n)):
        return "right_projection"
    vals = {table[i][j] for i in range(n) for j in range(n)}
    if len(vals) == 1:
        return "constant"
    if all(table[i][j] == (i + j) % n for i in range(n) for j in range(n)):
        return "add_mod"
    if all(table[i][j] == (i - j) % n for i in range(n) for j in range(n)):
        return "sub_mod"
    if all(table[i][j] == min(i, j) for i in range(n) for j in range(n)):
        return "min"
    if all(table[i][j] == max(i, j) for i in range(n) for j in range(n)):
        return "max"
    return "custom"

