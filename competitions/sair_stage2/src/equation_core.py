"""Compact equation parsing and rewriting for the SAIR Stage 2 solver."""

from __future__ import annotations

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

