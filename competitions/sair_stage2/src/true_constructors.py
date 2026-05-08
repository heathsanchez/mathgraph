"""Replayable TRUE constructors for the compact SAIR solver."""

from __future__ import annotations

try:
    from .equation_core import (
        alpha_canonical_equation,
        apply_subst,
        bounded_rewrite_derives,
        canonical_equation,
        canonical_term,
        match_pattern,
        parse_equation,
        replace_subterm_once,
        term_depth,
        term_size,
        vars_in_term,
    )
except ImportError:  # standalone build
    pass


def prove_alpha_or_swap(eq1, eq2):
    variants = [
        ("alpha", eq1),
        ("side_swap_alpha", (eq1[1], eq1[0])),
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
    ):
        result = fn(eq1, eq2)
        if result is not None:
            return result
    return None


def _proof(method, cert):
    return {"terminal_form": "ADVISORY_TRUE_CANDIDATE", "method": method, "certificate": cert}


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
