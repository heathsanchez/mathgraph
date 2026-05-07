#!/usr/bin/env python
"""Standalone SAIR Stage 2 compact solver.

Generated from competitions/sair_stage2. Uses only Python stdlib.
"""
from __future__ import annotations
import argparse
import json
import sys
from itertools import product

SOLVER_BUILD = '2026-05-07T21:02:58.114050+00:00'


# section: equation_core.py
OPS = {"*", "◇", "⋄", "·"}

def normalize_equation_text(s):
    s = str(s).strip()
    for op in ("◇", "⋄", "·"):
        s = s.replace(op, "*")
    return " ".join(s.replace("(", " ( ").replace(")", " ) ").replace("*", " * ").replace("=", " = ").split())

def tokenize(s):
    return normalize_equation_text(s).split()

def parse_term(s):
    toks = tokenize(s) if isinstance(s, str) else list(s)
    term, pos = _parse_term_bp(toks, 0)
    if pos != len(toks):
        raise ValueError("unexpected token: " + toks[pos])
    return term

def parse_equation(s):
    toks = tokenize(s)
    if toks.count("=") != 1:
        raise ValueError("equation must contain exactly one '='")
    i = toks.index("=")
    if i == 0 or i == len(toks) - 1:
        raise ValueError("equation sides must be nonempty")
    return (parse_term(toks[:i]), parse_term(toks[i + 1 :]))

def canonical_term(term):
    if term[0] == "v":
        return term[1]
    return "(" + canonical_term(term[1]) + "*" + canonical_term(term[2]) + ")"

def canonical_equation(eq):
    return canonical_term(eq[0]) + "=" + canonical_term(eq[1])

def alpha_canonical_term(term):
    names = {}

    def rec(t):
        if t[0] == "v":
            if t[1] not in names:
                names[t[1]] = "v" + str(len(names))
            return ("v", names[t[1]])
        return ("*", rec(t[1]), rec(t[2]))

    return rec(term)

def alpha_canonical_equation(eq):
    names = {}

    def rec(t):
        if t[0] == "v":
            if t[1] not in names:
                names[t[1]] = "v" + str(len(names))
            return ("v", names[t[1]])
        return ("*", rec(t[1]), rec(t[2]))

    return (rec(eq[0]), rec(eq[1]))

def dual_term(term):
    if term[0] == "v":
        return term
    return ("*", dual_term(term[2]), dual_term(term[1]))

def dual_equation(eq):
    return (dual_term(eq[0]), dual_term(eq[1]))

def vars_in_term(term):
    if term[0] == "v":
        return {term[1]}
    return vars_in_term(term[1]) | vars_in_term(term[2])

def term_size(term):
    if term[0] == "v":
        return 1
    return 1 + term_size(term[1]) + term_size(term[2])

def term_depth(term):
    if term[0] == "v":
        return 0
    return 1 + max(term_depth(term[1]), term_depth(term[2]))

def term_skeleton(term):
    if term[0] == "v":
        return ("v", "_")
    return ("*", term_skeleton(term[1]), term_skeleton(term[2]))

def term_subterms(term):
    out = [term]
    if term[0] == "*":
        out.extend(term_subterms(term[1]))
        out.extend(term_subterms(term[2]))
    return out

def variable_counts(term):
    counts = {}
    for name in vars_in_term(term):
        counts[name] = _count_var(term, name)
    return counts

def match_pattern(pattern, target, subst=None):
    subst = dict(subst or {})
    if pattern[0] == "v":
        bound = subst.get(pattern[1])
        if bound is None:
            subst[pattern[1]] = target
            return subst
        return subst if bound == target else None
    if target[0] != "*":
        return None
    left = match_pattern(pattern[1], target[1], subst)
    if left is None:
        return None
    return match_pattern(pattern[2], target[2], left)

def apply_subst(term, subst):
    if term[0] == "v":
        return subst.get(term[1], term)
    return ("*", apply_subst(term[1], subst), apply_subst(term[2], subst))

def replace_subterm_once(term, pattern, replacement):
    subst = match_pattern(pattern, term)
    if subst is not None:
        return apply_subst(replacement, subst)
    if term[0] != "*":
        return None
    left = replace_subterm_once(term[1], pattern, replacement)
    if left is not None:
        return ("*", left, term[2])
    right = replace_subterm_once(term[2], pattern, replacement)
    if right is not None:
        return ("*", term[1], right)
    return None

def bounded_rewrite_derives(source_eq, target_eq, max_steps=4, max_terms=900):
    rules = [(source_eq[0], source_eq[1]), (source_eq[1], source_eq[0])]
    start, goal = target_eq
    if start == goal:
        return [canonical_term(start)]
    queue = [(start, [start])]
    seen = {start}
    while queue and len(seen) <= max_terms:
        term, path = queue.pop(0)
        if len(path) - 1 >= max_steps:
            continue
        for a, b in rules:
            for nxt in _all_single_rewrites(term, a, b):
                if nxt in seen:
                    continue
                npath = path + [nxt]
                if nxt == goal:
                    return [canonical_term(x) for x in npath]
                seen.add(nxt)
                queue.append((nxt, npath))
    return None

def _parse_term_bp(toks, pos):
    if pos >= len(toks):
        raise ValueError("unexpected end of term")
    tok = toks[pos]
    if tok == "(":
        left, pos = _parse_term_bp(toks, pos + 1)
        if pos >= len(toks) or toks[pos] != ")":
            raise ValueError("missing ')'")
        pos += 1
    elif tok in {")", "*", "="}:
        raise ValueError("unexpected token: " + tok)
    else:
        left, pos = ("v", tok), pos + 1
    while pos < len(toks) and toks[pos] == "*":
        right, pos = _parse_term_bp(toks, pos + 1)
        left = ("*", left, right)
    return left, pos

def _count_var(term, name):
    if term[0] == "v":
        return 1 if term[1] == name else 0
    return _count_var(term[1], name) + _count_var(term[2], name)

def _all_single_rewrites(term, pattern, replacement):
    out = []
    subst = match_pattern(pattern, term)
    if subst is not None:
        out.append(apply_subst(replacement, subst))
    if term[0] == "*":
        for left in _all_single_rewrites(term[1], pattern, replacement):
            out.append(("*", left, term[2]))
        for right in _all_single_rewrites(term[2], pattern, replacement):
            out.append(("*", term[1], right))
    return out



# section: finite_magma_core.py
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



# section: true_constructors.py
def prove_alpha_or_swap(eq1, eq2):
    variants = [
        ("alpha", eq1),
        ("side_swap_alpha", (eq1[1], eq1[0])),
        ("dual_alpha", dual_equation(eq1)),
        ("dual_side_swap_alpha", (dual_equation(eq1)[1], dual_equation(eq1)[0])),
    ]
    target = alpha_canonical_equation(eq2)
    for method, eq in variants:
        if alpha_canonical_equation(eq) == target:
            return _proof(method, {"source": canonical_equation(eq1), "target": canonical_equation(eq2)})
    return None

def prove_direct_substitution(eq1, eq2):
    subst = match_pattern(eq1[0], eq2[0], {})
    if subst is not None:
        subst = match_pattern(eq1[1], eq2[1], subst)
    if subst is not None:
        return _proof(
            "direct_substitution",
            {"substitution": {k: canonical_term(v) for k, v in sorted(subst.items())}},
        )
    return None

def prove_bounded_rewrite(eq1, eq2):
    path = bounded_rewrite_derives(eq1, eq2, max_steps=4, max_terms=900)
    if path:
        return _proof("bounded_rewrite", {"rewrite_path": path, "max_steps": 4})
    return None

def prove_normal_form(eq1, eq2):
    a, b = _orient(eq1[0], eq1[1])
    left_path = _normalize_path(eq2[0], a, b)
    right_path = _normalize_path(eq2[1], a, b)
    if left_path[-1] == right_path[-1]:
        return _proof(
            "normal_form",
            {
                "oriented_rule": [canonical_term(a), canonical_term(b)],
                "lhs_path": [canonical_term(x) for x in left_path],
                "rhs_path": [canonical_term(x) for x in right_path],
            },
        )
    return None

def prove_contextual_fixed_point(eq1, eq2):
    candidates = []
    if eq1[0][0] == "v" and eq1[0][1] in vars_in_term(eq1[1]):
        candidates.append((eq1[0], eq1[1]))
    if eq1[1][0] == "v" and eq1[1][1] in vars_in_term(eq1[0]):
        candidates.append((eq1[1], eq1[0]))
    for var, ctx in candidates:
        closure = _closure(var, ctx, var[1], 5)
        if eq2[0] in closure and eq2[1] in closure:
            return _proof(
                "contextual_fixed_point",
                {"closure": [canonical_term(x) for x in closure], "variable": var[1]},
            )
    return None

def prove_true(eq1, eq2):
    for fn in (
        prove_alpha_or_swap,
        prove_direct_substitution,
        prove_bounded_rewrite,
        prove_normal_form,
        prove_contextual_fixed_point,
    ):
        result = fn(eq1, eq2)
        if result is not None:
            return result
    return None

def _proof(method, cert):
    return {"terminal_form": "VERIFIED_PROOF", "method": method, "certificate": cert}

def _orient(a, b):
    ka = (term_size(a), term_depth(a), canonical_term(a))
    kb = (term_size(b), term_depth(b), canonical_term(b))
    return (a, b) if ka > kb else (b, a)

def _normalize_path(term, pattern, replacement, max_steps=8):
    path = [term]
    cur = term
    for _ in range(max_steps):
        nxt = replace_subterm_once(cur, pattern, replacement)
        if nxt is None or nxt == cur:
            break
        path.append(nxt)
        cur = nxt
    return path

def _closure(var, ctx, name, max_depth):
    out = [var]
    cur = var
    for _ in range(max_depth):
        cur = _subst_var(ctx, name, cur)
        if cur in out:
            break
        out.append(cur)
    return out

def _subst_var(term, name, value):
    if term[0] == "v":
        return value if term[1] == name else term
    return ("*", _subst_var(term[1], name, value), _subst_var(term[2], name, value))



# section: false_constructors.py
def generated_tables(max_n=4):
    seen = set()

    def add(name, table):
        key = tuple(tuple(row) for row in table)
        if key not in seen:
            seen.add(key)
            yield name, key

    for n in range(1, max_n + 1):
        yield from add("left_projection_%d" % n, [[i for j in range(n)] for i in range(n)])
        yield from add("right_projection_%d" % n, [[j for j in range(n)] for i in range(n)])
        for c in range(n):
            yield from add("constant_%d_%d" % (n, c), [[c for j in range(n)] for i in range(n)])
        yield from add("add_mod_%d" % n, [[(i + j) % n for j in range(n)] for i in range(n)])
        yield from add("sub_mod_%d" % n, [[(i - j) % n for j in range(n)] for i in range(n)])
        yield from add("min_%d" % n, [[min(i, j) for j in range(n)] for i in range(n)])
        yield from add("max_%d" % n, [[max(i, j) for j in range(n)] for i in range(n)])
        yield from add("left_zero_%d" % n, [[0 if i == 0 else j for j in range(n)] for i in range(n)])
        yield from add("right_zero_%d" % n, [[0 if j == 0 else i for j in range(n)] for i in range(n)])
        yield from add("first_nonzero_%d" % n, [[i if i != 0 else j for j in range(n)] for i in range(n)])
        yield from add("second_nonzero_%d" % n, [[j if j != 0 else i for j in range(n)] for i in range(n)])
        if n <= 4:
            for A in range(n):
                for B in range(n):
                    for C in range(n):
                        if A == 0 and B == 0:
                            continue
                        yield from add(
                            "affine_%d_%d_%d_%d" % (n, A, B, C),
                            [[(A * i + B * j + C) % n for j in range(n)] for i in range(n)],
                        )

def prove_false_by_table_search(eq1, eq2, max_n=4):
    for name, table in generated_tables(max_n=max_n):
        cert = countermodel_certificate(eq1, eq2, table)
        if cert and verify_countermodel_certificate(eq1, eq2, cert):
            cert["table_name"] = name
            return {"terminal_form": "FINITE_COUNTERMODEL", "method": "finite_table_search", "certificate": cert}
    return None

def prove_false(eq1, eq2):
    return prove_false_by_table_search(eq1, eq2, max_n=4)



# section: solver_assets.py
EXACT_TRUE = {}
EXACT_FALSE = {}
TABLE_BANK = []
RULE_FAMILIES = []



# section: solver_runtime.py
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
        text = sys.stdin.read().strip()
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

