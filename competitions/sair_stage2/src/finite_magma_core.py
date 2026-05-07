"""Compact finite magma evaluator and countermodel certificates."""

from __future__ import annotations

from itertools import product

try:
    from .equation_core import vars_in_term
except ImportError:  # standalone build
    pass


def eval_term(term, table, assignment):
    if term[0] == "v":
        return int(assignment[term[1]])
    return int(table[eval_term(term[1], table, assignment)][eval_term(term[2], table, assignment)])


def all_assignments(var_names, n):
    names = sorted(var_names)
    for values in product(range(n), repeat=len(names)):
        yield dict(zip(names, values))


def satisfies_equation(eq, table):
    n = len(table)
    names = vars_in_term(eq[0]) | vars_in_term(eq[1])
    return all(eval_term(eq[0], table, a) == eval_term(eq[1], table, a) for a in all_assignments(names, n))


def find_violation(eq, table):
    n = len(table)
    names = vars_in_term(eq[0]) | vars_in_term(eq[1])
    for a in all_assignments(names, n):
        lhs = eval_term(eq[0], table, a)
        rhs = eval_term(eq[1], table, a)
        if lhs != rhs:
            return {"assignment": a, "lhs": lhs, "rhs": rhs}
    return None


def is_countermodel(eq1, eq2, table):
    return satisfies_equation(eq1, table) and find_violation(eq2, table) is not None


def countermodel_certificate(eq1, eq2, table):
    if not is_countermodel(eq1, eq2, table):
        return None
    violation = find_violation(eq2, table)
    return {
        "carrier_size": len(table),
        "table": [list(row) for row in table],
        "violating_assignment": dict(violation["assignment"]),
        "source_satisfied": True,
        "target_violated": True,
        "target_lhs": violation["lhs"],
        "target_rhs": violation["rhs"],
    }


def verify_countermodel_certificate(eq1, eq2, cert):
    try:
        table = tuple(tuple(int(x) for x in row) for row in cert["table"])
        n = int(cert["carrier_size"])
        if n != len(table) or any(len(row) != n for row in table):
            return False
        if any(x < 0 or x >= n for row in table for x in row):
            return False
        assignment = {str(k): int(v) for k, v in cert["violating_assignment"].items()}
        names = vars_in_term(eq1[0]) | vars_in_term(eq1[1]) | vars_in_term(eq2[0]) | vars_in_term(eq2[1])
        if any(name not in assignment for name in names):
            return False
        if not satisfies_equation(eq1, table):
            return False
        return eval_term(eq2[0], table, assignment) != eval_term(eq2[1], table, assignment)
    except Exception:
        return False

