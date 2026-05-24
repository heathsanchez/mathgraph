"""ETP/SAIR binary magma term parsing and features.

The parser is intentionally forgiving. Malformed inputs return parse-error
feature rows instead of crashing callers.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Any, Iterable


_OP_CHARS = {"◇", "⋄", "·", "∙", "∗", "＊", "×"}


@dataclass(frozen=True)
class ETPTerm:
    var: str | None = None
    left: "ETPTerm | None" = None
    right: "ETPTerm | None" = None

    @property
    def is_var(self) -> bool:
        return self.var is not None

    def variables(self) -> tuple[str, ...]:
        if self.var is not None:
            return (self.var,)
        assert self.left is not None and self.right is not None
        return tuple(sorted(set(self.left.variables()) | set(self.right.variables())))

    def variable_counts(self) -> Counter[str]:
        if self.var is not None:
            return Counter({self.var: 1})
        assert self.left is not None and self.right is not None
        return self.left.variable_counts() + self.right.variable_counts()

    def size(self) -> int:
        if self.var is not None:
            return 1
        assert self.left is not None and self.right is not None
        return 1 + self.left.size() + self.right.size()

    def depth(self) -> int:
        if self.var is not None:
            return 0
        assert self.left is not None and self.right is not None
        return 1 + max(self.left.depth(), self.right.depth())

    def positions(self, prefix: tuple[int, ...] = ()) -> tuple[tuple[int, ...], ...]:
        if self.var is not None:
            return (prefix,)
        assert self.left is not None and self.right is not None
        return (prefix,) + self.left.positions(prefix + (0,)) + self.right.positions(prefix + (1,))

    def skeleton(self) -> str:
        if self.var is not None:
            return "v"
        assert self.left is not None and self.right is not None
        return f"({self.left.skeleton()}*{self.right.skeleton()})"

    def canonical(self, mapping: dict[str, str] | None = None) -> str:
        mapping = {} if mapping is None else mapping
        if self.var is not None:
            if self.var not in mapping:
                mapping[self.var] = f"v{len(mapping)}"
            return mapping[self.var]
        assert self.left is not None and self.right is not None
        return f"({self.left.canonical(mapping)} * {self.right.canonical(mapping)})"

    def to_string(self) -> str:
        if self.var is not None:
            return self.var
        assert self.left is not None and self.right is not None
        return f"({self.left.to_string()} * {self.right.to_string()})"


@dataclass(frozen=True)
class ETPEquation:
    lhs: ETPTerm
    rhs: ETPTerm
    raw: str = ""
    normalized: str = ""

    def variables(self) -> tuple[str, ...]:
        return tuple(sorted(set(self.lhs.variables()) | set(self.rhs.variables())))

    def canonical(self) -> str:
        mapping: dict[str, str] = {}
        return f"{self.lhs.canonical(mapping)} = {self.rhs.canonical(mapping)}"


class _Parser:
    def __init__(self, text: str) -> None:
        self.tokens = re.findall(r"[A-Za-z][A-Za-z0-9_]*|\*|\(|\)", text)
        self.i = 0

    def parse(self) -> ETPTerm:
        term = self._term()
        if self.i != len(self.tokens):
            raise ValueError(f"unexpected token {self.tokens[self.i]}")
        return term

    def _term(self) -> ETPTerm:
        term = self._atom()
        while self._peek() == "*":
            self.i += 1
            term = ETPTerm(left=term, right=self._atom())
        return term

    def _atom(self) -> ETPTerm:
        tok = self._peek()
        if tok == "(":
            self.i += 1
            term = self._term()
            if self._peek() != ")":
                raise ValueError("expected ')'")
            self.i += 1
            return term
        if re.match(r"[A-Za-z]", tok or ""):
            self.i += 1
            return ETPTerm(var=tok)
        raise ValueError("expected term")

    def _peek(self) -> str:
        return self.tokens[self.i] if self.i < len(self.tokens) else ""


def normalize_operator_symbols(text: str) -> str:
    out = str(text or "")
    for op in _OP_CHARS:
        out = out.replace(op, "*")
    out = out.replace("=", " = ")
    out = re.sub(r"\s+", " ", out).strip()
    return out


def parse_term(text: str) -> ETPTerm:
    return _Parser(normalize_operator_symbols(text)).parse()


def parse_equation(text: str) -> ETPEquation:
    normalized = normalize_operator_symbols(text)
    if "=" not in normalized:
        raise ValueError("equation must contain '='")
    lhs, rhs = normalized.split("=", 1)
    return ETPEquation(parse_term(lhs.strip()), parse_term(rhs.strip()), raw=str(text), normalized=normalized)


def safe_parse_equation(text: str) -> tuple[ETPEquation | None, str]:
    try:
        return parse_equation(text), ""
    except Exception as exc:
        return None, str(exc)


def term_feature_row(term: ETPTerm, prefix: str = "term") -> dict[str, Any]:
    counts = term.variable_counts()
    return {
        f"{prefix}_size": term.size(),
        f"{prefix}_depth": term.depth(),
        f"{prefix}_vars": len(counts),
        f"{prefix}_repeat_count": sum(max(0, n - 1) for n in counts.values()),
        f"{prefix}_positions": len(term.positions()),
        f"{prefix}_skeleton": term.skeleton(),
        f"{prefix}_var_flow": variable_flow_signature(term),
    }


def equation_features(text: str) -> dict[str, Any]:
    eq, error = safe_parse_equation(text)
    if eq is None:
        return {"equation": text, "parse_ok": False, "parse_error": error}
    lhs = term_feature_row(eq.lhs, "lhs")
    rhs = term_feature_row(eq.rhs, "rhs")
    lhs_counts, rhs_counts = eq.lhs.variable_counts(), eq.rhs.variable_counts()
    return {
        "equation": text,
        "normalized": eq.normalized,
        "canonical": eq.canonical(),
        "parse_ok": True,
        "parse_error": "",
        **lhs,
        **rhs,
        "var_count": len(eq.variables()),
        "repeat_count": sum(max(0, n - 1) for n in (lhs_counts + rhs_counts).values()),
        "lhs_rhs_skeleton_equal": eq.lhs.skeleton() == eq.rhs.skeleton(),
        "lhs_new_var_count": len(set(eq.lhs.variables()) - set(eq.rhs.variables())),
        "rhs_new_var_count": len(set(eq.rhs.variables()) - set(eq.lhs.variables())),
    }


def variable_first_canonicalize_equation(text: str) -> str:
    eq, error = safe_parse_equation(text)
    return eq.canonical() if eq else normalize_operator_symbols(text)


def skeleton_signature(term_or_text: ETPTerm | str) -> str:
    term = parse_term(term_or_text) if isinstance(term_or_text, str) else term_or_text
    return term.skeleton()


def variable_flow_signature(term: ETPTerm) -> str:
    counts = term.variable_counts()
    return ",".join(f"{k}:{counts[k]}" for k in sorted(counts))


def term_position_paths(term_or_text: ETPTerm | str) -> tuple[tuple[int, ...], ...]:
    term = parse_term(term_or_text) if isinstance(term_or_text, str) else term_or_text
    return term.positions()
