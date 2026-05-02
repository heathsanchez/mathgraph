#!/usr/bin/env python3
"""
SAIR Stage 2 / MathGraph v15.10 local runner.

This is a local, non-Colab version of the residual witness-partition constructor:
for each still-uncovered FALSE pair (EQ1, EQ2), ask Z3 for a finite magma table
that satisfies EQ1 universally and violates EQ2 at a scheduled witness assignment.
Every SAT table is replayed globally against the equation matrix.
"""

from __future__ import annotations

import argparse
import gc
import glob
import hashlib
import itertools
import json
import os
import random
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd
import z3


DEFAULT_EQUATIONS = "/Users/heath/Desktop/LOGOS Papers/Maths Derivations/equations.txt"
DEFAULT_MATRIX = "/Users/heath/Desktop/LOGOS Papers/Maths Derivations/etp_matrix_full_best_bool.npy"
DEFAULT_BASE_DIR = str(Path.cwd() / "SAIR_MathGraph")

RANDOM_SEED = 42
DEFAULT_CARRIERS = [3, 4, 5, 6]
HARD_CARRIERS = [4, 5, 6, 7]
BIAS_SCHEDULE = [
    "none",
    "diag_split",
    "noncomm",
    "left_bias",
    "right_bias",
    "row_distinct",
    "col_distinct",
    "anti_projection",
    "diagonal_power",
]


@dataclass(frozen=True)
class Term:
    kind: str
    name: Optional[str] = None
    left: Optional["Term"] = None
    right: Optional["Term"] = None

    def __str__(self) -> str:
        if self.kind == "var":
            return str(self.name)
        return f"({self.left} ◇ {self.right})"


@dataclass(frozen=True)
class Equation:
    raw: str
    lhs: Term
    rhs: Term
    idx: int = -1


class ParseError(Exception):
    pass


def ensure_dir(path: str | Path) -> str:
    Path(path).mkdir(parents=True, exist_ok=True)
    return str(path)


def banner(title: str, ch: str = "=") -> None:
    print("\n" + ch * 112)
    print(title)
    print(ch * 112)


def save_json(obj: Any, path: str | Path) -> None:
    ensure_dir(Path(path).parent)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False, default=str)
    print(f"Saved: {path}")


def save_csv(df: pd.DataFrame, path: str | Path) -> None:
    ensure_dir(Path(path).parent)
    df.to_csv(path, index=False)
    print(f"Saved: {path}")


def sha16_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()[:16]


def table_hash(table: List[List[int]]) -> str:
    return sha16_bytes(json.dumps(table, separators=(",", ":")).encode("utf-8"))


def safe_int(x: Any, default: int = 0) -> int:
    try:
        if pd.isna(x):
            return default
        return int(x)
    except Exception:
        try:
            return int(float(x))
        except Exception:
            return default


def safe_float(x: Any, default: float = 0.0) -> float:
    try:
        if pd.isna(x):
            return default
        return float(x)
    except Exception:
        return default


def normalize_str(x: Any, default: str = "") -> str:
    if x is None:
        return default
    try:
        if pd.isna(x):
            return default
    except Exception:
        pass
    return str(x)


def discover_files(patterns: List[str]) -> List[str]:
    out: List[str] = []
    for pat in patterns:
        out.extend(glob.glob(pat, recursive=True))
    seen: Set[str] = set()
    clean: List[str] = []
    for p in out:
        if p not in seen and os.path.exists(p):
            seen.add(p)
            clean.append(p)
    return clean


def read_csv_robust(path: str) -> Optional[pd.DataFrame]:
    try:
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            return None
        try:
            return pd.read_csv(path, low_memory=False)
        except pd.errors.EmptyDataError:
            return None
        except Exception:
            return pd.read_csv(path, engine="python", on_bad_lines="skip")
    except Exception:
        return None


def normalize_equation_text(s: str) -> str:
    s = str(s).strip()
    s = s.replace("⋄", "◇").replace("*", "◇").replace("·", "◇")
    s = s.replace("==", "=").replace("≃", "=").replace("≈", "=").replace("≡", "=")
    return re.sub(r"\s+", " ", s)


def tokenize_term(s: str) -> List[str]:
    s = normalize_equation_text(s)
    tokens: List[str] = []
    i = 0
    while i < len(s):
        c = s[i]
        if c.isspace():
            i += 1
        elif c in "()=":
            tokens.append(c)
            i += 1
        elif c == "◇":
            tokens.append(c)
            i += 1
        elif re.match(r"[A-Za-z0-9_']", c):
            j = i + 1
            while j < len(s) and re.match(r"[A-Za-z0-9_']", s[j]):
                j += 1
            tokens.append(s[i:j])
            i = j
        elif c in ",;":
            i += 1
        else:
            raise ParseError(f"Unexpected char {c!r} in {s!r}")
    return tokens


class TermParser:
    def __init__(self, tokens: List[str]):
        self.tokens = tokens
        self.i = 0

    def peek(self) -> Optional[str]:
        return None if self.i >= len(self.tokens) else self.tokens[self.i]

    def pop(self) -> str:
        if self.i >= len(self.tokens):
            raise ParseError("Unexpected end")
        t = self.tokens[self.i]
        self.i += 1
        return t

    def parse(self) -> Term:
        t = self.parse_atom()
        while self.peek() == "◇":
            self.pop()
            t = Term("op", left=t, right=self.parse_atom())
        return t

    def parse_atom(self) -> Term:
        tok = self.peek()
        if tok is None:
            raise ParseError("Expected atom")
        if tok == "(":
            self.pop()
            t = self.parse()
            if self.peek() != ")":
                raise ParseError(f"Expected ')', got {self.peek()}")
            self.pop()
            return t
        if tok in [")", "◇", "="]:
            raise ParseError(f"Expected atom, got {tok}")
        self.pop()
        return Term("var", name=tok)


def parse_term(s: str) -> Term:
    toks = tokenize_term(s)
    p = TermParser(toks)
    t = p.parse()
    if p.peek() is not None:
        raise ParseError(f"Trailing tokens {toks[p.i:]}")
    return t


def parse_equation(s: str, idx: int = -1) -> Equation:
    raw = normalize_equation_text(s)
    if "=" not in raw:
        raise ParseError(f"No equals in equation {raw!r}")
    lhs_s, rhs_s = raw.split("=", 1)
    return Equation(raw=raw, lhs=parse_term(lhs_s.strip()), rhs=parse_term(rhs_s.strip()), idx=idx)


def canonical_term(t: Term) -> str:
    if t.kind == "var":
        return str(t.name)
    return f"({canonical_term(t.left)}◇{canonical_term(t.right)})"


def vars_in_term(t: Term) -> List[str]:
    if t.kind == "var":
        return [str(t.name)]
    return vars_in_term(t.left) + vars_in_term(t.right)


def term_size(t: Term) -> int:
    return 1 if t.kind == "var" else 1 + term_size(t.left) + term_size(t.right)


def term_internal(t: Term) -> int:
    return 0 if t.kind == "var" else 1 + term_internal(t.left) + term_internal(t.right)


def term_depth(t: Term) -> int:
    return 0 if t.kind == "var" else 1 + max(term_depth(t.left), term_depth(t.right))


def term_skeleton(t: Term) -> str:
    return "v" if t.kind == "var" else f"({term_skeleton(t.left)}◇{term_skeleton(t.right)})"


def variable_counts(t: Term) -> Dict[str, int]:
    d: Dict[str, int] = {}
    for v in vars_in_term(t):
        d[v] = d.get(v, 0) + 1
    return d


def multiset_str(d: Dict[str, int]) -> str:
    return ";".join(f"{k}:{v}" for k, v in sorted(d.items()))


def canonical_variable_pattern(eq: Equation) -> str:
    all_vars = vars_in_term(eq.lhs) + vars_in_term(eq.rhs)
    counts: Dict[str, int] = {}
    for v in all_vars:
        counts[v] = counts.get(v, 0) + 1
    mults = sorted(counts.values(), reverse=True)
    return (
        f"{term_skeleton(eq.lhs)}={term_skeleton(eq.rhs)}"
        f"|mults={','.join(map(str, mults))}"
        f"|lhs_counts={sorted(variable_counts(eq.lhs).values(), reverse=True)}"
        f"|rhs_counts={sorted(variable_counts(eq.rhs).values(), reverse=True)}"
    )


def build_equation_features(eqs: List[Equation]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    t0 = time.time()
    for i, eq in enumerate(eqs):
        lv, rv = vars_in_term(eq.lhs), vars_in_term(eq.rhs)
        allv = lv + rv
        lc, rc = variable_counts(eq.lhs), variable_counts(eq.rhs)
        ac: Dict[str, int] = {}
        for v in allv:
            ac[v] = ac.get(v, 0) + 1
        lhs_skel, rhs_skel = term_skeleton(eq.lhs), term_skeleton(eq.rhs)
        rows.append({
            "eq_id": i,
            "equation": eq.raw,
            "lhs": canonical_term(eq.lhs),
            "rhs": canonical_term(eq.rhs),
            "source_shape_key": canonical_variable_pattern(eq),
            "lhs_size": term_size(eq.lhs),
            "rhs_size": term_size(eq.rhs),
            "total_size": term_size(eq.lhs) + term_size(eq.rhs),
            "lhs_internal": term_internal(eq.lhs),
            "rhs_internal": term_internal(eq.rhs),
            "total_internal": term_internal(eq.lhs) + term_internal(eq.rhs),
            "lhs_depth": term_depth(eq.lhs),
            "rhs_depth": term_depth(eq.rhs),
            "max_depth": max(term_depth(eq.lhs), term_depth(eq.rhs)),
            "lhs_var_count": len(lv),
            "rhs_var_count": len(rv),
            "total_var_count": len(allv),
            "lhs_distinct_vars": len(set(lv)),
            "rhs_distinct_vars": len(set(rv)),
            "distinct_vars": len(set(allv)),
            "rhs_new_var_count": len(set(rv) - set(lv)),
            "lhs_skeleton": lhs_skel,
            "rhs_skeleton": rhs_skel,
            "eq_skeleton": lhs_skel + "=" + rhs_skel,
            "same_skeleton": int(lhs_skel == rhs_skel),
            "max_var_mult": max(ac.values()) if ac else 0,
            "lhs_max_var_mult": max(lc.values()) if lc else 0,
            "rhs_max_var_mult": max(rc.values()) if rc else 0,
            "repeat_total": sum(max(0, v - 1) for v in ac.values()),
            "lhs_repeat_total": sum(max(0, v - 1) for v in lc.values()),
            "rhs_repeat_total": sum(max(0, v - 1) for v in rc.values()),
            "lhs_counts": multiset_str(lc),
            "rhs_counts": multiset_str(rc),
            "all_counts": multiset_str(ac),
            "is_lhs_var": int(eq.lhs.kind == "var"),
            "is_rhs_var": int(eq.rhs.kind == "var"),
        })
        if (i + 1) % 1000 == 0:
            print(f"  features {i+1:,}/{len(eqs):,} elapsed={time.time()-t0:.2f}s")
    return pd.DataFrame(rows)


def classify_target_family(f2: pd.Series, eq2: Equation) -> str:
    raw = eq2.raw.replace(" ", "")
    rhs_size, lhs_size = safe_int(f2.get("rhs_size")), safe_int(f2.get("lhs_size"))
    max_mult = safe_int(f2.get("max_var_mult"))
    repeat_total = safe_int(f2.get("repeat_total"))
    distinct_vars = safe_int(f2.get("distinct_vars"))
    if raw in ["x◇y=y◇x", "y◇x=x◇y"]:
        return "commutativity_or_swap"
    if max_mult >= 4 or repeat_total >= 3 or distinct_vars <= 1:
        return "diagonal_power_idempotent_pressure"
    if rhs_size < lhs_size:
        return "taildrop_target"
    if max_mult >= 3:
        return "repeated_variable_power_target"
    return "general_target"


def classify_source_macro(f1: pd.Series) -> str:
    max_mult = safe_int(f1.get("max_var_mult"))
    repeat_total = safe_int(f1.get("repeat_total"))
    distinct_vars = safe_int(f1.get("distinct_vars"))
    total_size = safe_int(f1.get("total_size"))
    if repeat_total >= 4 or max_mult >= 4:
        return "repeat_very_heavy_source"
    if repeat_total >= 2 or max_mult >= 3:
        return "repeat_heavy_source"
    if distinct_vars >= 4 and total_size >= 7:
        return "wide_source"
    if safe_int(f1.get("rhs_new_var_count")) > 0:
        return "new_variable_pressure_source"
    return "general_source"


def pair_feature_dict(f1: pd.Series, f2: pd.Series, eq1: Equation, eq2: Equation) -> Dict[str, Any]:
    s1, s2 = safe_int(f1.get("total_size")), safe_int(f2.get("total_size"))
    r1, r2 = safe_int(f1.get("rhs_size")), safe_int(f2.get("rhs_size"))
    dv1, dv2 = safe_int(f1.get("distinct_vars")), safe_int(f2.get("distinct_vars"))
    rep1, rep2 = safe_int(f1.get("repeat_total")), safe_int(f2.get("repeat_total"))
    m1, m2 = safe_int(f1.get("max_var_mult")), safe_int(f2.get("max_var_mult"))
    same_lhs_skel = str(f1.get("lhs_skeleton")) == str(f2.get("lhs_skeleton"))
    same_rhs_skel = str(f1.get("rhs_skeleton")) == str(f2.get("rhs_skeleton"))
    same_eq_skel = str(f1.get("eq_skeleton")) == str(f2.get("eq_skeleton"))
    delta_size, delta_rhs = s2 - s1, r2 - r1
    delta_dv, delta_rep, delta_max_mult = dv2 - dv1, rep2 - rep1, m2 - m1
    if same_eq_skel and delta_dv < 0:
        micro = "same_skeleton_var_collapse"
    elif same_eq_skel:
        micro = "role_permutation_same_skeleton"
    elif delta_size == 0 and delta_dv < 0:
        micro = "same_nodes_vardrop"
    elif delta_rhs < 0 and delta_dv < 0:
        micro = "taildrop_vardrop"
    elif delta_rhs < 0 and delta_rep < 0:
        micro = "taildrop_repeatdrop"
    elif delta_rhs < 0:
        micro = "taildrop_rhsdrop"
    elif delta_size == 0:
        micro = "near_shape_mutation"
    elif delta_dv > 0:
        micro = "newvar_pressure"
    elif delta_rhs > 0:
        micro = "rhs_expansion_residual"
    else:
        micro = "general_residual"
    source_macro = classify_source_macro(f1)
    target_family = classify_target_family(f2, eq2)
    exact = (
        f"shape_{'same' if same_eq_skel else 'changed'}"
        f"__var_{'plus' if delta_dv > 0 else 'minus' if delta_dv < 0 else 'same'}"
        f"__rhs_{'drop' if delta_rhs < 0 else 'expand' if delta_rhs > 0 else 'same'}"
        f"__repeat_{'gain' if delta_rep > 0 else 'drop' if delta_rep < 0 else 'same'}"
    )
    if micro in ["same_nodes_vardrop", "same_skeleton_var_collapse"]:
        cons = "var_collapse_obstruction"
    elif micro.startswith("taildrop"):
        cons = "taildrop_context_obstruction"
    elif micro == "role_permutation_same_skeleton":
        cons = "role_permutation_noncomm_obstruction"
    elif target_family == "diagonal_power_idempotent_pressure":
        cons = "diagonal_power_obstruction"
    else:
        cons = "small_magma_pair_obstruction"
    sharpness = 2.5 * max(0, -delta_dv) + 2.0 * max(0, -delta_rhs) + 1.5 * max(0, delta_rep) + max(0, delta_max_mult)
    return {
        "source_shape_key": str(f1.get("source_shape_key")),
        "target_shape_key": str(f2.get("source_shape_key")),
        "source_macro_basin": source_macro,
        "pair_micro_basin": micro,
        "target_family": target_family,
        "recommended_constructor": cons,
        "exact_motif": exact,
        "delta_total_size": delta_size,
        "delta_rhs_size": delta_rhs,
        "delta_distinct_vars": delta_dv,
        "delta_repeat_total": delta_rep,
        "delta_max_var_mult": delta_max_mult,
        "same_lhs_skeleton": int(same_lhs_skel),
        "same_rhs_skeleton": int(same_rhs_skel),
        "same_eq_skeleton": int(same_eq_skel),
        "geometry_sharpness": float(sharpness),
    }


def eval_term_concrete(t: Term, table: List[List[int]], env: Dict[str, int]) -> Optional[int]:
    if t.kind == "var":
        return env.get(str(t.name))
    a = eval_term_concrete(t.left, table, env)
    b = eval_term_concrete(t.right, table, env)
    if a is None or b is None:
        return None
    n = len(table)
    if a < 0 or b < 0 or a >= n or b >= n:
        return None
    return int(table[a][b])


def magma_satisfies_equation(eq: Equation, table: List[List[int]]) -> bool:
    vs = sorted(set(vars_in_term(eq.lhs) + vars_in_term(eq.rhs)))
    for vals in itertools.product(range(len(table)), repeat=len(vs)):
        env = dict(zip(vs, vals))
        if eval_term_concrete(eq.lhs, table, env) != eval_term_concrete(eq.rhs, table, env):
            return False
    return True


def magma_violation_witness(eq: Equation, table: List[List[int]]) -> Tuple[bool, Optional[Dict[str, int]], Optional[int], Optional[int]]:
    vs = sorted(set(vars_in_term(eq.lhs) + vars_in_term(eq.rhs)))
    for vals in itertools.product(range(len(table)), repeat=len(vs)):
        env = dict(zip(vs, vals))
        lv = eval_term_concrete(eq.lhs, table, env)
        rv = eval_term_concrete(eq.rhs, table, env)
        if lv is not None and rv is not None and int(lv) != int(rv):
            return True, env, int(lv), int(rv)
    return False, None, None, None


def validate_countermodel(eq1: Equation, eq2: Equation, table: List[List[int]]) -> Tuple[bool, Dict[str, Any]]:
    sat = magma_satisfies_equation(eq1, table)
    viol, env, lv, rv = magma_violation_witness(eq2, table)
    return bool(sat and viol), {"source_satisfied": sat, "target_violated": viol, "witness_env": env, "target_lhs_value": lv, "target_rhs_value": rv}


def table_truth_vectors(eqs: List[Equation], table: List[List[int]]) -> Tuple[np.ndarray, np.ndarray]:
    sat = np.zeros(len(eqs), dtype=bool)
    viol = np.zeros(len(eqs), dtype=bool)
    for i, eq in enumerate(eqs):
        vs = sorted(set(vars_in_term(eq.lhs) + vars_in_term(eq.rhs)))
        ok = True
        saw_viol = False
        for vals in itertools.product(range(len(table)), repeat=len(vs)):
            env = dict(zip(vs, vals))
            if eval_term_concrete(eq.lhs, table, env) != eval_term_concrete(eq.rhs, table, env):
                ok = False
                saw_viol = True
                break
        sat[i] = ok
        viol[i] = saw_viol
    return sat, viol


def z3_cell(cells: List[List[Any]], a: Any, b: Any, n: int) -> Any:
    expr = cells[n - 1][n - 1]
    for i in reversed(range(n)):
        for j in reversed(range(n)):
            expr = z3.If(z3.And(a == i, b == j), cells[i][j], expr)
    return expr


def eval_term_z3(t: Term, cells: List[List[Any]], env: Dict[str, Any], n: int) -> Any:
    if t.kind == "var":
        return env[str(t.name)]
    return z3_cell(cells, eval_term_z3(t.left, cells, env, n), eval_term_z3(t.right, cells, env, n), n)


def source_universal_constraints(eq: Equation, cells: List[List[Any]], n: int) -> Tuple[List[Any], int]:
    vs = sorted(set(vars_in_term(eq.lhs) + vars_in_term(eq.rhs)))
    clauses = []
    for vals in itertools.product(range(n), repeat=len(vs)):
        env = {v: z3.IntVal(vals[k]) for k, v in enumerate(vs)}
        clauses.append(eval_term_z3(eq.lhs, cells, env, n) == eval_term_z3(eq.rhs, cells, env, n))
    return clauses, n ** len(vs)


def all_set_partitions(items: List[str], max_partitions: int) -> List[Dict[str, int]]:
    if not items:
        return []
    parts: List[Dict[str, int]] = []

    def rec(k: int, assign: List[int], max_block: int) -> None:
        if len(parts) >= max_partitions:
            return
        if k == len(items):
            parts.append({items[i]: assign[i] for i in range(len(items))})
            return
        for b in range(max_block + 2):
            assign.append(b)
            rec(k + 1, assign, max(max_block, b))
            assign.pop()
            if len(parts) >= max_partitions:
                return

    rec(1, [0], 0)
    parts.sort(key=lambda p: (len(set(p.values())), -max(list(p.values()).count(b) for b in set(p.values())), tuple(p[v] for v in items)))
    return parts[:max_partitions]


def partition_to_witness_values(partition: Dict[str, int], n: int, offset: int = 0) -> Optional[Dict[str, int]]:
    blocks = sorted(set(partition.values()))
    if len(blocks) > n:
        return None
    block_to_value = {b: (k + offset) % n for k, b in enumerate(blocks)}
    return {v: block_to_value[b] for v, b in partition.items()}


def target_witness_constraints(eq: Equation, cells: List[List[Any]], n: int, witness_values: Dict[str, int]) -> List[Any]:
    vs = sorted(set(vars_in_term(eq.lhs) + vars_in_term(eq.rhs)))
    env = {v: z3.IntVal(int(witness_values.get(v, 0))) for v in vs}
    return [eval_term_z3(eq.lhs, cells, env, n) != eval_term_z3(eq.rhs, cells, env, n)]


def add_bias_constraints(s: Any, cells: List[List[Any]], n: int, bias: str) -> None:
    if bias == "diag_split":
        if n >= 3:
            s.add(cells[0][0] != cells[1][1], cells[1][1] != cells[2][2])
        elif n >= 2:
            s.add(cells[0][0] != cells[1][1])
    elif bias == "noncomm" and n >= 2:
        s.add(cells[0][1] != cells[1][0])
    elif bias == "left_bias" and n >= 3:
        s.add(cells[0][1] == 0, cells[1][2] == 1)
    elif bias == "right_bias" and n >= 3:
        s.add(cells[0][1] == 1, cells[1][2] == 2)
    elif bias == "row_distinct" and n >= 3:
        s.add(z3.Distinct(cells[0][0], cells[0][1], cells[0][2]))
    elif bias == "col_distinct" and n >= 3:
        s.add(z3.Distinct(cells[0][0], cells[1][0], cells[2][0]))
    elif bias == "anti_projection" and n >= 3:
        s.add(cells[0][1] != 0, cells[0][1] != 1, cells[1][2] != 1, cells[1][2] != 2)
    elif bias == "diagonal_power" and n >= 4:
        s.add(cells[0][0] != 0, cells[1][1] != 1, cells[2][2] != 2)


def solve_pair_witness_partition(eq1: Equation, eq2: Equation, n: int, witness_values: Dict[str, int], bias: str, timeout_ms: int) -> Dict[str, Any]:
    t0 = time.time()
    cells = [[z3.Int(f"m_{i}_{j}") for j in range(n)] for i in range(n)]
    s = z3.Solver()
    s.set(timeout=timeout_ms)
    for i in range(n):
        for j in range(n):
            s.add(cells[i][j] >= 0, cells[i][j] < n)
    s.add(cells[0][0] <= cells[n - 1][n - 1])
    if n >= 3:
        s.add(cells[0][0] <= cells[1][1], cells[0][0] <= cells[2][2])
    add_bias_constraints(s, cells, n, bias)
    src_clauses, src_assign = source_universal_constraints(eq1, cells, n)
    s.add(*src_clauses)
    s.add(*target_witness_constraints(eq2, cells, n, witness_values))
    status = s.check()
    elapsed = time.time() - t0
    if status == z3.sat:
        model = s.model()
        table = [[int(model.eval(cells[i][j], model_completion=True).as_long()) for j in range(n)] for i in range(n)]
        return {"status": "sat", "table": table, "elapsed_sec": elapsed, "clauses": len(s.assertions()), "src_assign": src_assign}
    return {"status": "unsat" if status == z3.unsat else "unknown", "table": None, "elapsed_sec": elapsed, "clauses": len(s.assertions()), "src_assign": src_assign}


def load_or_build_queue(covered_mask: np.ndarray, false_mask: np.ndarray, features_df: pd.DataFrame, eqs: List[Equation], out_dir: Path, queue_candidates: List[str]) -> pd.DataFrame:
    banner("LOADING / BUILDING RESIDUAL QUEUE")
    dfs: List[pd.DataFrame] = []
    for p in discover_files(queue_candidates):
        df = read_csv_robust(p)
        if df is None or df.empty or "eq1_id" not in df.columns or "eq2_id" not in df.columns:
            continue
        df = df.copy()
        df["eq1_id"] = df["eq1_id"].map(lambda x: safe_int(x, -1))
        df["eq2_id"] = df["eq2_id"].map(lambda x: safe_int(x, -1))
        df = df[(df.eq1_id >= 0) & (df.eq1_id < len(eqs)) & (df.eq2_id >= 0) & (df.eq2_id < len(eqs))]
        live = [bool(false_mask[int(r.eq1_id), int(r.eq2_id)] and not covered_mask[int(r.eq1_id), int(r.eq2_id)]) for r in df[["eq1_id", "eq2_id"]].itertuples(index=False)]
        df = df[np.array(live, dtype=bool)]
        if len(df):
            print(f"Loaded queue: {p} shape={df.shape}")
            dfs.append(df)
    if dfs:
        base = pd.concat(dfs, ignore_index=True, sort=False).drop_duplicates(["eq1_id", "eq2_id"]).reset_index(drop=True)
    else:
        ii, jj = np.where(false_mask & ~covered_mask)
        base = pd.DataFrame({"eq1_id": ii.astype(np.int32), "eq2_id": jj.astype(np.int32)})
    feat = features_df.set_index("eq_id")
    rows: List[Dict[str, Any]] = []
    for k, r in enumerate(base[["eq1_id", "eq2_id"]].itertuples(index=False)):
        i, j = int(r.eq1_id), int(r.eq2_id)
        d = pair_feature_dict(feat.loc[i], feat.loc[j], eqs[i], eqs[j])
        d.update({"eq1_id": i, "eq2_id": j, "eq1": eqs[i].raw, "eq2": eqs[j].raw})
        rows.append(d)
        if (k + 1) % 5000 == 0:
            print(f"  enriched {k+1:,}/{len(base):,}")
    base = pd.DataFrame(rows)
    src_counts = base.groupby("eq1_id")["eq2_id"].size().rename("source_residual_count")
    tgt_counts = base.groupby("eq2_id")["eq1_id"].size().rename("target_residual_count")
    shape_counts = base.groupby("source_shape_key")["eq2_id"].size().rename("source_shape_residual_count")
    base = base.merge(src_counts, on="eq1_id", how="left").merge(tgt_counts, on="eq2_id", how="left").merge(shape_counts, on="source_shape_key", how="left")
    basin_bonus: List[float] = []
    for _, r in base.iterrows():
        micro, fam, exact = normalize_str(r.get("pair_micro_basin")), normalize_str(r.get("target_family")), normalize_str(r.get("exact_motif"))
        b = 0.0
        if fam == "diagonal_power_idempotent_pressure":
            b += 70
        if micro == "same_nodes_vardrop":
            b += 90
        elif micro == "near_shape_mutation":
            b += 70
        elif micro == "taildrop_rhsdrop":
            b += 65
        elif micro == "role_permutation_same_skeleton":
            b += 40
        elif micro == "same_skeleton_var_collapse":
            b += 45
        elif micro.startswith("taildrop"):
            b += 45
        if "repeat_gain" in exact:
            b += 25
        if "rhs_drop" in exact:
            b += 20
        if "var_minus" in exact:
            b += 20
        basin_bonus.append(b)
    base["priority"] = base.target_residual_count.astype(float) * 8 + base.source_residual_count.astype(float) * 2 + base.source_shape_residual_count.astype(float) * 1.5 + base.geometry_sharpness.astype(float) * 12 + np.array(basin_bonus)
    base = base.sort_values(["priority", "target_residual_count", "source_residual_count"], ascending=False).reset_index(drop=True)
    save_csv(base, out_dir / "v15_10_active_residual_queue.csv")
    print(f"Active residual pairs : {len(base):,}")
    print(f"Unique sources        : {base.eq1_id.nunique():,}")
    print(f"Unique targets        : {base.eq2_id.nunique():,}")
    return base


def build_target_cluster_plan(queue: pd.DataFrame, eqs: List[Equation], out_dir: Path) -> pd.DataFrame:
    banner("BUILDING TARGET-CLUSTER PLAN")
    group_cols = ["target_family", "pair_micro_basin", "recommended_constructor", "exact_motif", "eq2_id"]
    plan = queue.groupby(group_cols, dropna=False).agg(
        pairs=("eq1_id", "size"),
        unique_sources=("eq1_id", "nunique"),
        unique_source_shapes=("source_shape_key", "nunique"),
        max_priority=("priority", "max"),
        avg_priority=("priority", "mean"),
        avg_geometry_sharpness=("geometry_sharpness", "mean"),
        source_residual_mass=("source_residual_count", "sum"),
        target_residual_count=("target_residual_count", "max"),
    ).reset_index()
    plan["eq2"] = plan.eq2_id.map(lambda i: eqs[int(i)].raw)
    plan["cluster_priority"] = (
        plan.pairs.astype(float) * 10
        + plan.unique_sources.astype(float) * 14
        + plan.unique_source_shapes.astype(float) * 18
        + plan.target_residual_count.astype(float) * 30
        + plan.avg_geometry_sharpness.astype(float) * 10
        + plan.max_priority.astype(float) * 0.2
    )
    plan = plan.sort_values(["cluster_priority", "pairs", "unique_sources"], ascending=False).reset_index(drop=True)
    save_csv(plan, out_dir / "v15_10_target_cluster_plan.csv")
    print(plan.head(40).to_string(index=False))
    return plan


def carrier_schedule_for_row(row: pd.Series, eq1: Equation, eq2: Equation) -> List[int]:
    micro, exact = normalize_str(row.get("pair_micro_basin")), normalize_str(row.get("exact_motif"))
    src_vars = len(set(vars_in_term(eq1.lhs) + vars_in_term(eq1.rhs)))
    tgt_vars = len(set(vars_in_term(eq2.lhs) + vars_in_term(eq2.rhs)))
    if src_vars >= 4:
        return [4, 5, 6]
    if tgt_vars >= 4 or micro in ["near_shape_mutation", "role_permutation_same_skeleton"] or "rhs_expand" in exact:
        return HARD_CARRIERS[:]
    return DEFAULT_CARRIERS[:]


def bias_schedule_for_row(row: pd.Series) -> List[str]:
    micro, fam = normalize_str(row.get("pair_micro_basin")), normalize_str(row.get("target_family"))
    if micro == "role_permutation_same_skeleton":
        return ["noncomm", "anti_projection", "none", "row_distinct", "col_distinct", "diag_split"]
    if micro == "near_shape_mutation":
        return ["anti_projection", "diag_split", "noncomm", "none", "row_distinct", "col_distinct"]
    if fam == "diagonal_power_idempotent_pressure":
        return ["diag_split", "diagonal_power", "anti_projection", "none", "noncomm", "row_distinct"]
    if micro.startswith("taildrop"):
        return ["none", "anti_projection", "left_bias", "right_bias", "diag_split", "noncomm"]
    return BIAS_SCHEDULE[:]


def timeout_for_row(row: pd.Series, n: int, base_ms: int, hard_ms: int) -> int:
    micro, fam = normalize_str(row.get("pair_micro_basin")), normalize_str(row.get("target_family"))
    t = base_ms + (3000 if n >= 6 else 0) + (6000 if n >= 7 else 0)
    if micro in ["near_shape_mutation", "role_permutation_same_skeleton"]:
        t += 3000
    if fam == "diagonal_power_idempotent_pressure":
        t += 1500
    if safe_int(row.get("source_residual_count")) > 100:
        t += 1500
    return min(t, hard_ms)


def witness_partitions_for_target(eq2: Equation, row: pd.Series, n: int, max_partitions: int, max_full_vars: int) -> List[Dict[str, int]]:
    tgt_vars = sorted(set(vars_in_term(eq2.lhs) + vars_in_term(eq2.rhs)))
    if not tgt_vars:
        return []
    micro, exact = normalize_str(row.get("pair_micro_basin")), normalize_str(row.get("exact_motif"))
    if len(tgt_vars) > max_full_vars:
        parts = [{v: 0 for v in tgt_vars}, {v: k for k, v in enumerate(tgt_vars)}]
        if len(tgt_vars) >= 2:
            p = {v: 1 for v in tgt_vars}
            p[tgt_vars[0]] = 0
            parts.append(p)
        parts.extend([{v: k % 2 for k, v in enumerate(tgt_vars)}, {v: k % 3 for k, v in enumerate(tgt_vars)}])
        return [p for p in parts if len(set(p.values())) <= n][:max_partitions]
    parts = all_set_partitions(tgt_vars, max_partitions)
    def score(p: Dict[str, int]) -> Tuple[int, int, Tuple[int, ...]]:
        blocks = [p[v] for v in tgt_vars]
        distinct = len(set(blocks))
        max_cnt = max(blocks.count(b) for b in set(blocks))
        if "var_minus" in exact or micro in ["same_nodes_vardrop", "same_skeleton_var_collapse"]:
            return (distinct, -max_cnt, tuple(blocks))
        if micro in ["near_shape_mutation", "role_permutation_same_skeleton"]:
            return (-distinct, max_cnt, tuple(blocks))
        return (abs(2 - distinct), -max_cnt, tuple(blocks))
    parts.sort(key=score)
    return [p for p in parts if len(set(p.values())) <= n][:max_partitions]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--equations", default=DEFAULT_EQUATIONS)
    p.add_argument("--matrix", default=DEFAULT_MATRIX)
    p.add_argument("--base-dir", default=DEFAULT_BASE_DIR)
    p.add_argument("--max-target-clusters", type=int, default=900)
    p.add_argument("--max-pairs-per-cluster", type=int, default=16)
    p.add_argument("--max-probes-per-pair", type=int, default=20)
    p.add_argument("--max-total-z3-calls", type=int, default=12000)
    p.add_argument("--max-tables-to-find", type=int, default=500)
    p.add_argument("--max-new-hits-target", type=int, default=1500)
    p.add_argument("--pair-timeout-ms-base", type=int, default=5500)
    p.add_argument("--pair-timeout-ms-hard", type=int, default=11000)
    p.add_argument("--cluster-budget-sec", type=float, default=110.0)
    p.add_argument("--global-budget-sec", type=float, default=5.5 * 3600)
    p.add_argument("--max-partitions-per-target", type=int, default=12)
    p.add_argument("--max-target-var-count-for-full-partitions", type=int, default=5)
    p.add_argument("--max-source-var-assignments", type=int, default=7 ** 4)
    p.add_argument("--checkpoint-every-z3-calls", type=int, default=100)
    p.add_argument("--checkpoint-every-tables", type=int, default=10)
    p.add_argument("--emit-lean-templates", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--max-lean-templates", type=int, default=8000)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)

    base_dir = Path(args.base_dir).expanduser()
    prev_15_9c = base_dir / "sair_stage2_mathgraph_v15_9c_winner_table_algebra_amplifier"
    prev_15_9b = base_dir / "sair_stage2_mathgraph_v15_9b_target_basin_first_finisher"
    out_dir = base_dir / "sair_stage2_mathgraph_v15_10_residual_witness_partition_constructor"
    table_dir = out_dir / "tables"
    lean_dir = out_dir / "lean_templates"
    ensure_dir(table_dir)
    ensure_dir(lean_dir)

    mask_candidates = [
        str(prev_15_9c / "v15_9c_covered_false_mask_final.npy"),
        str(prev_15_9c / "v15_9c_covered_false_mask_checkpoint.npy"),
        str(prev_15_9b / "v15_9b_covered_false_mask_final.npy"),
        str(prev_15_9b / "v15_9b_covered_false_mask_checkpoint.npy"),
        str(base_dir / "**/v*_covered_false_mask_final.npy"),
        str(base_dir / "**/v*_covered_false_mask_checkpoint.npy"),
        str(base_dir / "**/v*_covered_false_mask_interrupt_checkpoint.npy"),
        str(base_dir / "**/v*_false_coverage_mask_canonical.npy"),
    ]
    queue_candidates = [
        str(prev_15_9c / "v15_9c_remaining_queue_final_enriched.csv"),
        str(prev_15_9b / "v15_9b_remaining_queue_final_enriched.csv"),
        str(base_dir / "**/v*_remaining_queue_final_enriched.csv"),
        str(base_dir / "**/v*_active_residual_queue.csv"),
        str(base_dir / "**/v*_remaining_pairs_final.csv"),
    ]

    banner("LOADING CORE ASSETS")
    if not os.path.exists(args.equations):
        raise FileNotFoundError(args.equations)
    if not os.path.exists(args.matrix):
        raise FileNotFoundError(args.matrix)
    with open(args.equations, "r", encoding="utf-8", errors="replace") as f:
        raw_eq_lines = [line.strip() for line in f if line.strip()]
    eqs = [parse_equation(s, idx=i) for i, s in enumerate(raw_eq_lines)]
    m_bool = np.load(args.matrix).astype(bool)
    if m_bool.shape != (len(eqs), len(eqs)):
        raise ValueError(f"Matrix shape {m_bool.shape} does not match equations {len(eqs)}")
    false_mask = ~m_bool
    false_total = int(false_mask.sum())
    eq_sha16 = sha16_bytes("\n".join(raw_eq_lines).encode("utf-8"))
    print(f"Equations loaded : {len(eqs):,}")
    print(f"Matrix shape     : {m_bool.shape}")
    print(f"TRUE total       : {int(m_bool.sum()):,}")
    print(f"FALSE total      : {false_total:,}")
    print(f"Equations sha16  : {eq_sha16}")
    print(f"Z3 version       : {z3.get_version_string()}")
    print(f"Output dir       : {out_dir}")
    save_json({
        "equations_path": args.equations,
        "matrix_path": args.matrix,
        "equations_loaded": len(eqs),
        "matrix_shape": list(m_bool.shape),
        "true_total": int(m_bool.sum()),
        "false_total": false_total,
        "equations_sha16": eq_sha16,
        "z3_version": z3.get_version_string(),
        "output_dir": str(out_dir),
    }, out_dir / "v15_10_core_load_summary.json")

    banner("BUILDING EQUATION FEATURES")
    features_df = build_equation_features(eqs)
    save_csv(features_df, out_dir / "v15_10_equation_features.csv")
    features_by_id = features_df.set_index("eq_id")

    banner("LOADING BEST PRIOR COVERAGE MASK")
    best_mask = None
    best_path = None
    best_cov = -1
    mask_infos: List[Dict[str, Any]] = []
    for pth in sorted(discover_files(mask_candidates)):
        try:
            arr = np.load(pth)
            if arr.shape != m_bool.shape:
                continue
            arr = arr.astype(bool) & false_mask
            cov = int(arr.sum())
            mask_infos.append({"path": pth, "covered_false": cov, "coverage_rate": cov / false_total})
            print(f"Mask candidate: {pth}\n  covered={cov:,}/{false_total:,} rate={cov/false_total:.9f}")
            if cov > best_cov:
                best_cov, best_mask, best_path = cov, arr, pth
        except Exception as exc:
            print(f"Mask skipped: {pth}: {type(exc).__name__}: {exc}")
    if best_mask is None:
        best_mask = np.zeros_like(false_mask, dtype=bool)
        best_cov = 0
    covered_mask = best_mask.copy()
    starting_covered = int(covered_mask.sum())
    starting_remaining = int((false_mask & ~covered_mask).sum())
    print(f"Best mask path  : {best_path}")
    print(f"Starting covered: {starting_covered:,}/{false_total:,} = {starting_covered/false_total:.9f}")
    print(f"Starting remain : {starting_remaining:,}")
    save_json({"best_mask_path": best_path, "covered_false": starting_covered, "false_total": false_total, "remaining_false": starting_remaining, "mask_candidates": mask_infos}, out_dir / "v15_10_best_mask_loaded.json")

    queue = load_or_build_queue(covered_mask, false_mask, features_df, eqs, out_dir, queue_candidates)
    target_cluster_plan = build_target_cluster_plan(queue, eqs, out_dir)

    recoveries: List[Dict[str, Any]] = []
    attempts: List[Dict[str, Any]] = []
    tables_log: List[Dict[str, Any]] = []
    lean_manifest: List[Dict[str, Any]] = []
    source_shape_states: Dict[str, Dict[str, Any]] = {}
    table_hashes_seen: Set[str] = set()
    z3_calls = 0
    new_covered_total = 0
    tables_found = 0
    start_time = time.time()

    def current_remaining_count() -> int:
        return int((false_mask & ~covered_mask).sum())

    def get_shape_state(shape_key: str) -> Dict[str, Any]:
        if shape_key not in source_shape_states:
            source_shape_states[shape_key] = {"unsat_attempts": 0, "unknown_attempts": 0, "sat_attempts": 0, "hits": 0, "z3_calls": 0, "blacklisted": False}
        return source_shape_states[shape_key]

    def update_shape_state(shape_key: str, status: str, hit_count: int) -> None:
        st = get_shape_state(shape_key)
        st["z3_calls"] += 1
        if status == "sat":
            st["sat_attempts"] += 1
        elif status == "unsat":
            st["unsat_attempts"] += 1
        elif status == "unknown":
            st["unknown_attempts"] += 1
        st["hits"] += max(0, hit_count)
        if st["hits"] == 0 and (st["unsat_attempts"] >= 32 or st["unknown_attempts"] >= 18 or st["z3_calls"] >= 48):
            st["blacklisted"] = True

    def checkpoint(label: str) -> None:
        save_csv(pd.DataFrame(recoveries), out_dir / "v15_10_recoveries_checkpoint.csv")
        save_csv(pd.DataFrame(attempts), out_dir / "v15_10_attempts_checkpoint.csv")
        save_csv(pd.DataFrame(tables_log), out_dir / "v15_10_tables_checkpoint.csv")
        save_csv(pd.DataFrame(lean_manifest), out_dir / "v15_10_lean_manifest_checkpoint.csv")
        shape_df = pd.DataFrame([{"source_shape_key": k, **v} for k, v in source_shape_states.items()])
        save_csv(shape_df, out_dir / "v15_10_source_shape_states_checkpoint.csv")
        np.save(out_dir / "v15_10_covered_false_mask_checkpoint.npy", covered_mask)
        save_json({
            "label": label,
            "covered_false": int(covered_mask.sum()),
            "false_total": false_total,
            "coverage_rate": float(covered_mask.sum() / false_total),
            "remaining_false": current_remaining_count(),
            "new_covered_this_run": int(new_covered_total),
            "recoveries": len(recoveries),
            "z3_calls": z3_calls,
            "tables_found": tables_found,
            "elapsed_sec": time.time() - start_time,
        }, out_dir / "v15_10_status_checkpoint.json")
        print(f"Checkpoint {label}: covered={int(covered_mask.sum()):,}/{false_total:,} remaining={current_remaining_count():,} new={new_covered_total:,} z3={z3_calls:,} tables={tables_found:,}")

    def emit_lean_template(eq1_id: int, eq2_id: int, table: List[List[int]], witness: Optional[Dict[str, int]], h: str) -> str:
        path = lean_dir / f"countermodel_eq{eq1_id}_not_eq{eq2_id}_{h[:8]}.lean"
        payload = {"eq1_id": eq1_id, "eq2_id": eq2_id, "eq1": eqs[eq1_id].raw, "eq2": eqs[eq2_id].raw, "carrier_size": len(table), "table": table, "witness": witness, "table_hash": h}
        path.write_text(
            "-- SAIR Stage 2 finite magma countermodel template\n"
            "-- Generated by v15.10 residual witness-partition constructor.\n\n"
            f"-- EQ1 id: {eq1_id}\n-- EQ1   : {eqs[eq1_id].raw}\n"
            f"-- EQ2 id: {eq2_id}\n-- EQ2   : {eqs[eq2_id].raw}\n"
            f"-- Carrier size: {len(table)}\n-- Table hash: {h}\n-- Witness: {witness}\n"
            f"-- Cayley table:\n-- {json.dumps(table)}\n\n-- JSON payload:\n-- {json.dumps(payload, ensure_ascii=False)}\n",
            encoding="utf-8",
        )
        return str(path)

    def replay_sat_table(table: List[List[int]], eq1_id_hint: int, eq2_id_hint: int, generator: str, meta: Dict[str, Any]) -> int:
        nonlocal new_covered_total, tables_found
        h = table_hash(table)
        if h in table_hashes_seen:
            return 0
        table_hashes_seen.add(h)
        tables_found += 1
        sat_vec, viol_vec = table_truth_vectors(eqs, table)
        cert_mask = (sat_vec[:, None] & viol_vec[None, :]) & false_mask & ~covered_mask
        ii, jj = np.where(cert_mask)
        new_count = int(len(ii))
        if new_count:
            covered_mask[cert_mask] = True
            new_covered_total += new_count
        table_log = {
            "table_hash": h,
            "carrier_size": len(table),
            "generator": generator,
            "eq1_id_hint": eq1_id_hint,
            "eq2_id_hint": eq2_id_hint,
            "new_hits": new_count,
            "sat_equations": int(sat_vec.sum()),
            "violated_equations": int(viol_vec.sum()),
            "remaining_after": current_remaining_count(),
            **{f"meta_{k}": v for k, v in meta.items() if isinstance(v, (str, int, float, bool))},
        }
        tables_log.append(table_log)
        with open(table_dir / f"{h}.json", "w", encoding="utf-8") as f:
            json.dump({"table_hash": h, "table": table, "metadata": table_log}, f, indent=2)
        if new_count:
            for a, b in zip(ii.tolist(), jj.tolist()):
                ok, cm_meta = validate_countermodel(eqs[int(a)], eqs[int(b)], table)
                if not ok:
                    continue
                rec = {
                    "eq1_id": int(a),
                    "eq2_id": int(b),
                    "table_hash": h,
                    "carrier_size": len(table),
                    "generator": generator,
                    "eq1": eqs[int(a)].raw,
                    "eq2": eqs[int(b)].raw,
                    "witness_env": json.dumps(cm_meta.get("witness_env"), ensure_ascii=False),
                    "target_lhs_value": cm_meta.get("target_lhs_value"),
                    "target_rhs_value": cm_meta.get("target_rhs_value"),
                }
                if args.emit_lean_templates and len(lean_manifest) < args.max_lean_templates:
                    rec["lean_template"] = emit_lean_template(int(a), int(b), table, cm_meta.get("witness_env"), h)
                    lean_manifest.append({"eq1_id": int(a), "eq2_id": int(b), "table_hash": h, "lean_template": rec["lean_template"]})
                recoveries.append(rec)
            print(f"      GLOBAL HIT table={h} n={len(table)} new={new_count} total_new={new_covered_total} remaining={current_remaining_count():,}")
        return new_count

    banner("RUNNING v15.10 RESIDUAL WITNESS-PARTITION SEARCH")
    checkpoint("initial")

    cluster_counter = 0
    for cluster_row in target_cluster_plan.itertuples(index=False):
        if time.time() - start_time > args.global_budget_sec or z3_calls >= args.max_total_z3_calls or tables_found >= args.max_tables_to_find or new_covered_total >= args.max_new_hits_target or current_remaining_count() == 0:
            break
        cluster_counter += 1
        if cluster_counter > args.max_target_clusters:
            break
        eq2_id = int(getattr(cluster_row, "eq2_id"))
        tfam, micro, cons, motif = (normalize_str(getattr(cluster_row, c, "")) for c in ["target_family", "pair_micro_basin", "recommended_constructor", "exact_motif"])
        live_cluster = queue[(queue.eq2_id.astype(int) == eq2_id) & (queue.target_family.astype(str) == tfam) & (queue.pair_micro_basin.astype(str) == micro) & (queue.recommended_constructor.astype(str) == cons) & (queue.exact_motif.astype(str) == motif)].copy()
        live_cluster = live_cluster[[bool(false_mask[int(r.eq1_id), int(r.eq2_id)] and not covered_mask[int(r.eq1_id), int(r.eq2_id)]) for r in live_cluster[["eq1_id", "eq2_id"]].itertuples(index=False)]]
        if live_cluster.empty:
            continue
        live_cluster = live_cluster.sort_values(["priority", "source_residual_count"], ascending=False)
        cluster_start = time.time()
        print("\n" + "-" * 112)
        print(f"[target-cluster {cluster_counter}/{min(args.max_target_clusters, len(target_cluster_plan))}] eq2={eq2_id} pairs={len(live_cluster):,} unique_sources={live_cluster.eq1_id.nunique():,}")
        print(f"target_family={tfam} micro={micro} constructor={cons} motif={motif}")
        print(f"EQ2: {eqs[eq2_id].raw}")
        print("-" * 112)
        selected_rows: List[pd.Series] = []
        seen_shapes: Set[str] = set()
        for _, r in live_cluster.iterrows():
            shape_key = normalize_str(r.get("source_shape_key"))
            if shape_key not in seen_shapes:
                selected_rows.append(r)
                seen_shapes.add(shape_key)
            if len(selected_rows) >= args.max_pairs_per_cluster:
                break
        if len(selected_rows) < args.max_pairs_per_cluster:
            seen_pairs = {(int(x.eq1_id), int(x.eq2_id)) for x in selected_rows}
            for _, r in live_cluster.iterrows():
                key = (int(r.eq1_id), int(r.eq2_id))
                if key not in seen_pairs:
                    selected_rows.append(r)
                    seen_pairs.add(key)
                if len(selected_rows) >= args.max_pairs_per_cluster:
                    break
        for probe_idx, row in enumerate(selected_rows, start=1):
            if time.time() - cluster_start > args.cluster_budget_sec or time.time() - start_time > args.global_budget_sec or z3_calls >= args.max_total_z3_calls:
                break
            i, j = int(row["eq1_id"]), int(row["eq2_id"])
            if not (false_mask[i, j] and not covered_mask[i, j]):
                continue
            eq1, eq2 = eqs[i], eqs[j]
            source_shape_key = normalize_str(row.get("source_shape_key", features_by_id.loc[i].get("source_shape_key", "")))
            if get_shape_state(source_shape_key).get("blacklisted"):
                continue
            src_vars = sorted(set(vars_in_term(eq1.lhs) + vars_in_term(eq1.rhs)))
            tgt_vars = sorted(set(vars_in_term(eq2.lhs) + vars_in_term(eq2.rhs)))
            print(f"  probe {probe_idx}/{len(selected_rows)} EQ{i}->{j} src_vars={len(src_vars)} tgt_vars={len(tgt_vars)} shape_state={json.dumps(get_shape_state(source_shape_key))}")
            print(f"    EQ1: {eq1.raw}")
            attempts_for_pair = 0
            pair_hit = False
            for n in carrier_schedule_for_row(row, eq1, eq2):
                if pair_hit or n ** len(src_vars) > args.max_source_var_assignments:
                    continue
                partitions = witness_partitions_for_target(eq2, row, n, args.max_partitions_per_target, args.max_target_var_count_for_full_partitions)
                for part_idx, part in enumerate(partitions, start=1):
                    if pair_hit:
                        break
                    for offset in range(min(n, 3)):
                        witness_values = partition_to_witness_values(part, n, offset)
                        if witness_values is None:
                            continue
                        for bias in bias_schedule_for_row(row):
                            if time.time() - cluster_start > args.cluster_budget_sec or time.time() - start_time > args.global_budget_sec or z3_calls >= args.max_total_z3_calls or attempts_for_pair >= args.max_probes_per_pair:
                                break
                            attempts_for_pair += 1
                            z3_calls += 1
                            res = solve_pair_witness_partition(eq1, eq2, n, witness_values, bias, timeout_for_row(row, n, args.pair_timeout_ms_base, args.pair_timeout_ms_hard))
                            status, table, elapsed = normalize_str(res.get("status")), res.get("table"), safe_float(res.get("elapsed_sec"))
                            hit_count = 0
                            attempt_rec = {"eq1_id": i, "eq2_id": j, "status": status, "carrier": n, "bias": bias, "partition_idx": part_idx, "partition": json.dumps(part, ensure_ascii=False), "witness_values": json.dumps(witness_values, ensure_ascii=False), "elapsed_sec": elapsed, "clauses": safe_int(res.get("clauses")), "src_assign": safe_int(res.get("src_assign")), "source_shape_key": source_shape_key, "target_family": tfam, "pair_micro_basin": micro, "recommended_constructor": cons, "exact_motif": motif}
                            if status == "sat" and table is not None:
                                ok, _ = validate_countermodel(eq1, eq2, table)
                                attempt_rec["validated_pair"] = bool(ok)
                                if ok:
                                    h = table_hash(table)
                                    attempt_rec["table_hash"] = h
                                    hit_count = replay_sat_table(table, i, j, "v15_10_witness_partition", {"bias": bias, "carrier": n, "partition_idx": part_idx, "target_family": tfam, "pair_micro_basin": micro, "constructor": cons})
                                    pair_hit = hit_count > 0 or ok
                                    print(f"      SAT {'+ RECOVERED' if hit_count else 'pair-valid global-new=0'} table={h} n={n} bias={bias} hits={hit_count}")
                                else:
                                    print(f"      SAT but failed concrete validation n={n} bias={bias} elapsed={elapsed:.2f}s")
                            else:
                                if attempts_for_pair <= 5 or status != "unsat":
                                    print(f"      n={n} bias={bias} status={status} part={part_idx} elapsed={elapsed:.2f}s src_assign={safe_int(res.get('src_assign'))}")
                            attempts.append(attempt_rec)
                            update_shape_state(source_shape_key, status, hit_count)
                            if z3_calls % args.checkpoint_every_z3_calls == 0:
                                checkpoint(f"z3_calls_{z3_calls}")
                            if tables_found > 0 and tables_found % args.checkpoint_every_tables == 0:
                                checkpoint(f"tables_{tables_found}")
                            if hit_count > 0:
                                break
                        if pair_hit or attempts_for_pair >= args.max_probes_per_pair:
                            break
                    if pair_hit or attempts_for_pair >= args.max_probes_per_pair:
                        break
        checkpoint(f"after_target_cluster_{cluster_counter}")
        if cluster_counter % 20 == 0:
            gc.collect()

    banner("FINALIZING v15.10")
    ii, jj = np.where(false_mask & ~covered_mask)
    final_remaining_df = pd.DataFrame({"eq1_id": ii.astype(np.int32), "eq2_id": jj.astype(np.int32)})
    save_csv(final_remaining_df, out_dir / "v15_10_remaining_pairs_final.csv")
    rows = []
    for r in final_remaining_df.itertuples(index=False):
        i, j = int(r.eq1_id), int(r.eq2_id)
        d = pair_feature_dict(features_by_id.loc[i], features_by_id.loc[j], eqs[i], eqs[j])
        d.update({"eq1_id": i, "eq2_id": j, "eq1": eqs[i].raw, "eq2": eqs[j].raw})
        rows.append(d)
    final_remaining_enriched = pd.DataFrame(rows)
    save_csv(final_remaining_enriched, out_dir / "v15_10_remaining_queue_final_enriched.csv")
    if not final_remaining_enriched.empty:
        final_basin_summary = final_remaining_enriched.groupby(["target_family", "pair_micro_basin", "recommended_constructor", "exact_motif"], dropna=False).agg(
            residual_pairs=("eq2_id", "size"),
            unique_sources=("eq1_id", "nunique"),
            unique_source_shapes=("source_shape_key", "nunique"),
            unique_targets=("eq2_id", "nunique"),
            avg_geometry_sharpness=("geometry_sharpness", "mean"),
            avg_delta_rhs=("delta_rhs_size", "mean"),
            avg_delta_distinct=("delta_distinct_vars", "mean"),
            avg_delta_repeat=("delta_repeat_total", "mean"),
        ).reset_index().sort_values("residual_pairs", ascending=False)
    else:
        final_basin_summary = pd.DataFrame()
    save_csv(final_basin_summary, out_dir / "v15_10_remaining_basin_summary_final.csv")
    save_csv(pd.DataFrame([{"source_shape_key": k, **v} for k, v in source_shape_states.items()]), out_dir / "v15_10_source_shape_states_final.csv")
    np.save(out_dir / "v15_10_covered_false_mask_final.npy", covered_mask)
    final_summary = {
        "starting_covered_false": starting_covered,
        "starting_coverage_rate": float(starting_covered / false_total),
        "starting_remaining_false": starting_remaining,
        "final_covered_false": int(covered_mask.sum()),
        "final_coverage_rate": float(covered_mask.sum() / false_total),
        "final_remaining_false": current_remaining_count(),
        "new_covered_this_run": int(new_covered_total),
        "false_total": false_total,
        "recoveries": len(recoveries),
        "z3_calls": z3_calls,
        "tables_found": tables_found,
        "elapsed_sec": float(time.time() - start_time),
        "out_dir": str(out_dir),
        "best_prior_mask": best_path,
        "method": "residual_witness_partition_constructor",
    }
    save_json(final_summary, out_dir / "v15_10_final_summary.json")
    checkpoint("final")
    print("\n" + "=" * 112)
    print("v15.10 FINAL SUMMARY")
    print("=" * 112)
    print(f"Starting covered FALSE : {starting_covered:,}/{false_total:,} = {starting_covered/false_total:.9f}")
    print(f"Final covered FALSE    : {int(covered_mask.sum()):,}/{false_total:,} = {covered_mask.sum()/false_total:.9f}")
    print(f"New covered this run   : {new_covered_total:,}")
    print(f"Final remaining FALSE  : {current_remaining_count():,}")
    print(f"Recoveries             : {len(recoveries):,}")
    print(f"Z3 calls               : {z3_calls:,}")
    print(f"Tables found           : {tables_found:,}")
    print(f"Elapsed sec            : {time.time() - start_time:.1f}")
    print(f"Output dir             : {out_dir}")


if __name__ == "__main__":
    main()
