#!/usr/bin/env python3
"""
SAIR Stage 2 / MathGraph v16.0 Colab runner.

Residual obstruction factory.

MATHGRAPH v16 PRINCIPLE
Do not generate tables first.
First derive the quotient geometry forced by the source law.
Then locate the smallest target equality not forced by that quotient.
Then search only for finite magmas that preserve the source quotient while separating that equality.
Every failure becomes a closure constraint.
Every success becomes a certificate family.
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
import subprocess
import sys
import time
import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd


def ensure_z3():
    try:
        import z3
        print(f"Z3 OK: {z3.__file__}")
        return z3, True
    except ModuleNotFoundError:
        print("Z3 missing. Installing z3-solver...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "z3-solver"])
        importlib.invalidate_caches()
        import z3
        print(f"Z3 OK after install: {z3.__file__}")
        return z3, True
    except Exception as e:
        print(f"Z3 unavailable: {type(e).__name__}: {e}")
        return None, False


z3, Z3_AVAILABLE = ensure_z3()

try:
    from google.colab import drive
    drive.mount("/content/drive")
except Exception as e:
    print(f"Drive mount skipped/unavailable: {type(e).__name__}: {e}")


DEFAULT_EQUATIONS = "/content/equations.txt"
DEFAULT_MATRIX = "/content/etp_matrix_full_best_bool.npy"
DEFAULT_BASE_DIR = "/content/drive/MyDrive/SAIR_MathGraph"

RANDOM_SEED = 42
DEFAULT_CARRIERS = [3, 4, 5, 6]
HARD_CARRIERS = [4, 5, 6, 7]
DIAGONAL_CARRIERS = [3, 4, 5, 6]
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
    "power_split_r",
    "power_split_l",
    "assoc_diag_split",
    "role_escape",
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
    elif bias == "power_split_r" and n >= 3:
        p2 = cells[0][0]
        p3r = z3_cell(cells, z3.IntVal(0), p2, n)
        p4r = z3_cell(cells, z3.IntVal(0), p3r, n)
        s.add(z3.Or(p2 != p3r, p3r != p4r))
    elif bias == "power_split_l" and n >= 3:
        p2 = cells[0][0]
        p3l = z3_cell(cells, p2, z3.IntVal(0), n)
        p4l = z3_cell(cells, p3l, z3.IntVal(0), n)
        s.add(z3.Or(p2 != p3l, p3l != p4l))
    elif bias == "assoc_diag_split" and n >= 3:
        p2 = cells[0][0]
        p3r = z3_cell(cells, z3.IntVal(0), p2, n)
        p3l = z3_cell(cells, p2, z3.IntVal(0), n)
        s.add(p3r != p3l)
    elif bias == "role_escape" and n >= 3:
        s.add(z3.Or(cells[0][1] != cells[1][0], cells[0][0] != cells[0][1], cells[1][1] != cells[1][0]))


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


def eval_term_z3_uf(t: Term, op: Any, env: Dict[str, Any], n: int) -> Tuple[Any, List[Any]]:
    if t.kind == "var":
        return env[str(t.name)], []
    a, ca = eval_term_z3_uf(t.left, op, env, n)
    b, cb = eval_term_z3_uf(t.right, op, env, n)
    v = op(a, b)
    return v, ca + cb + [v >= 0, v < n]


def add_uf_bias_constraints(s: Any, op: Any, n: int, bias: str) -> None:
    cell = lambda i, j: op(z3.IntVal(i), z3.IntVal(j))
    if bias == "diag_split":
        if n >= 3:
            s.add(cell(0, 0) != cell(1, 1), cell(1, 1) != cell(2, 2))
        elif n >= 2:
            s.add(cell(0, 0) != cell(1, 1))
    elif bias == "noncomm" and n >= 2:
        s.add(cell(0, 1) != cell(1, 0))
    elif bias == "left_bias" and n >= 3:
        s.add(cell(0, 1) == 0, cell(1, 2) == 1)
    elif bias == "right_bias" and n >= 3:
        s.add(cell(0, 1) == 1, cell(1, 2) == 2)
    elif bias == "row_distinct" and n >= 3:
        s.add(z3.Distinct(cell(0, 0), cell(0, 1), cell(0, 2)))
    elif bias == "col_distinct" and n >= 3:
        s.add(z3.Distinct(cell(0, 0), cell(1, 0), cell(2, 0)))
    elif bias == "anti_projection" and n >= 3:
        s.add(cell(0, 1) != 0, cell(0, 1) != 1, cell(1, 2) != 1, cell(1, 2) != 2)
    elif bias == "diagonal_power" and n >= 4:
        s.add(cell(0, 0) != 0, cell(1, 1) != 1, cell(2, 2) != 2)
    elif bias == "power_split_r" and n >= 3:
        p2 = cell(0, 0)
        p3r = op(z3.IntVal(0), p2)
        p4r = op(z3.IntVal(0), p3r)
        s.add(p3r >= 0, p3r < n, p4r >= 0, p4r < n, z3.Or(p2 != p3r, p3r != p4r))
    elif bias == "power_split_l" and n >= 3:
        p2 = cell(0, 0)
        p3l = op(p2, z3.IntVal(0))
        p4l = op(p3l, z3.IntVal(0))
        s.add(p3l >= 0, p3l < n, p4l >= 0, p4l < n, z3.Or(p2 != p3l, p3l != p4l))
    elif bias == "assoc_diag_split" and n >= 3:
        p2 = cell(0, 0)
        p3r = op(z3.IntVal(0), p2)
        p3l = op(p2, z3.IntVal(0))
        s.add(p3r >= 0, p3r < n, p3l >= 0, p3l < n, p3r != p3l)
    elif bias == "role_escape" and n >= 3:
        s.add(z3.Or(cell(0, 1) != cell(1, 0), cell(0, 0) != cell(0, 1), cell(1, 1) != cell(1, 0)))


def solve_pair_witness_partition_uf(eq1: Equation, eq2: Equation, n: int, witness_values: Dict[str, int], bias: str, timeout_ms: int) -> Dict[str, Any]:
    t0 = time.time()
    op = z3.Function("op", z3.IntSort(), z3.IntSort(), z3.IntSort())
    s = z3.Solver()
    s.set(timeout=timeout_ms)

    for i in range(n):
        for j in range(n):
            v = op(z3.IntVal(i), z3.IntVal(j))
            s.add(v >= 0, v < n)

    s.add(op(0, 0) <= op(n - 1, n - 1))
    if n >= 3:
        s.add(op(0, 0) <= op(1, 1), op(0, 0) <= op(2, 2))

    add_uf_bias_constraints(s, op, n, bias)

    src_vars = sorted(set(vars_in_term(eq1.lhs) + vars_in_term(eq1.rhs)))
    src_assign = n ** len(src_vars)
    for vals in itertools.product(range(n), repeat=len(src_vars)):
        env = {v: z3.IntVal(vals[k]) for k, v in enumerate(src_vars)}
        lv, lc = eval_term_z3_uf(eq1.lhs, op, env, n)
        rv, rc = eval_term_z3_uf(eq1.rhs, op, env, n)
        if lc:
            s.add(*lc)
        if rc:
            s.add(*rc)
        s.add(lv == rv)

    tgt_vars = sorted(set(vars_in_term(eq2.lhs) + vars_in_term(eq2.rhs)))
    env = {v: z3.IntVal(int(witness_values.get(v, 0))) for v in tgt_vars}
    lv, lc = eval_term_z3_uf(eq2.lhs, op, env, n)
    rv, rc = eval_term_z3_uf(eq2.rhs, op, env, n)
    if lc:
        s.add(*lc)
    if rc:
        s.add(*rc)
    s.add(lv != rv)

    status = s.check()
    elapsed = time.time() - t0
    if status == z3.sat:
        model = s.model()
        table = []
        for i in range(n):
            row = []
            for j in range(n):
                row.append(int(model.eval(op(z3.IntVal(i), z3.IntVal(j)), model_completion=True).as_long()))
            table.append(row)
        return {"status": "sat", "table": table, "elapsed_sec": elapsed, "clauses": len(s.assertions()), "src_assign": src_assign}
    return {"status": "unsat" if status == z3.unsat else "unknown", "table": None, "elapsed_sec": elapsed, "clauses": len(s.assertions()), "src_assign": src_assign}


# ==================================================================================================
# BOUNDED SOURCE-CLOSURE / OBSTRUCTION GEOMETRY
# ==================================================================================================

TRACE_ROLES = ["x"]
ESCAPE_ROLES = ["x", "y"]
WIDE_ROLES = ["x", "y", "z"]


def subst_term(t: Term, subst: Dict[str, str]) -> Term:
    if t.kind == "var":
        return Term("var", name=subst.get(str(t.name), str(t.name)))
    return Term("op", left=subst_term(t.left, subst), right=subst_term(t.right, subst))


def generate_terms_for_roles(roles: List[str], max_depth: int) -> List[Term]:
    by_depth: List[List[Term]] = [[Term("var", name=r) for r in roles]]
    seen = {canonical_term(t): t for t in by_depth[0]}
    for d in range(1, max_depth + 1):
        level: List[Term] = []
        for dl in range(d):
            dr = d - 1 - dl
            for a in by_depth[dl]:
                for b in by_depth[dr]:
                    t = Term("op", left=a, right=b)
                    key = canonical_term(t)
                    if key not in seen:
                        seen[key] = t
                        level.append(t)
        by_depth.append(level)
    return list(seen.values())


class UnionFind:
    def __init__(self, items: List[str]):
        self.parent = {x: x for x in items}

    def find(self, x: str) -> str:
        if x not in self.parent:
            self.parent[x] = x
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: str, b: str) -> bool:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if rb < ra:
            ra, rb = rb, ra
        self.parent[rb] = ra
        return True


def role_substitutions(source_vars: List[str], roles: List[str], cap: int = 96) -> List[Dict[str, str]]:
    if not source_vars:
        return []
    out = []
    for vals in itertools.product(roles, repeat=len(source_vars)):
        out.append(dict(zip(source_vars, vals)))
        if len(out) >= cap:
            break
    # Ensure the pure diagonal substitution is first.
    diag = {v: roles[0] for v in source_vars}
    key = tuple(diag[v] for v in source_vars)
    dedup = {key: diag}
    for s in out:
        dedup[tuple(s[v] for v in source_vars)] = s
    return list(dedup.values())


def bounded_source_closure(eq: Equation, roles: List[str], max_depth: int = 5) -> Dict[str, Any]:
    terms = generate_terms_for_roles(roles, max_depth)
    term_by_key = {canonical_term(t): t for t in terms}
    uf = UnionFind(list(term_by_key.keys()))

    source_vars = sorted(set(vars_in_term(eq.lhs) + vars_in_term(eq.rhs)))
    substitutions = role_substitutions(source_vars, roles)
    direct_equalities = 0

    for subst in substitutions:
        lhs = canonical_term(subst_term(eq.lhs, subst))
        rhs = canonical_term(subst_term(eq.rhs, subst))
        if lhs in term_by_key and rhs in term_by_key:
            direct_equalities += int(uf.union(lhs, rhs))

    # Bounded congruence closure over the generated universe.
    op_index: Dict[Tuple[str, str], str] = {}
    for t in terms:
        if t.kind == "op":
            op_index[(canonical_term(t.left), canonical_term(t.right))] = canonical_term(t)

    changed = True
    rounds = 0
    congruence_unions = 0
    while changed and rounds < 12:
        changed = False
        rounds += 1
        buckets: Dict[Tuple[str, str], str] = {}
        for (a, b), parent in op_index.items():
            sig = (uf.find(a), uf.find(b))
            if sig in buckets:
                if uf.union(parent, buckets[sig]):
                    changed = True
                    congruence_unions += 1
            else:
                buckets[sig] = parent

    classes: Dict[str, List[str]] = {}
    for k in term_by_key:
        classes.setdefault(uf.find(k), []).append(k)

    diag_terms = [k for k in term_by_key if set(re.findall(r"[A-Za-z][A-Za-z0-9_']*", k)) <= {"x"}]
    diag_classes = {k: uf.find(k) for k in diag_terms}
    return {
        "roles": roles,
        "max_depth": max_depth,
        "terms": term_by_key,
        "uf": uf,
        "classes": classes,
        "class_count": len(classes),
        "largest_class": max((len(v) for v in classes.values()), default=0),
        "direct_equalities": direct_equalities,
        "congruence_unions": congruence_unions,
        "diag_terms": diag_terms,
        "diag_classes": diag_classes,
        "closure_rank": len(classes) / max(1, len(term_by_key)),
        "signature_hash": sha16_bytes(json.dumps(sorted((k, uf.find(k)) for k in term_by_key), separators=(",", ":")).encode("utf-8")),
    }


def target_partition_specs(eq2: Equation, max_specs: int = 12) -> List[Tuple[str, Dict[str, str]]]:
    vs = sorted(set(vars_in_term(eq2.lhs) + vars_in_term(eq2.rhs)))
    if not vs:
        return []
    specs: List[Tuple[str, Dict[str, str]]] = []
    specs.append(("all_same", {v: "x" for v in vs}))
    if len(vs) >= 2:
        specs.append(("first_split", {v: ("x" if k == 0 else "y") for k, v in enumerate(vs)}))
        specs.append(("last_split", {v: ("y" if k == len(vs) - 1 else "x") for k, v in enumerate(vs)}))
        specs.append(("alternating_xy", {v: ("x" if k % 2 == 0 else "y") for k, v in enumerate(vs)}))
    if len(vs) >= 3:
        specs.append(("xyz_roles", {v: WIDE_ROLES[k % 3] for k, v in enumerate(vs)}))
    seen = set()
    clean = []
    for name, spec in specs:
        key = tuple(spec[v] for v in vs)
        if key not in seen:
            seen.add(key)
            clean.append((name, spec))
    return clean[:max_specs]


def classify_pair_by_source_closure(eq1: Equation, eq2: Equation, diag_closure: Dict[str, Any], escape_closure: Dict[str, Any]) -> Dict[str, Any]:
    best_forced = False
    best_same_role = False
    best_lhs = ""
    best_rhs = ""
    best_name = ""
    min_class_size = 10**9
    for name, spec in target_partition_specs(eq2):
        roles_used = sorted(set(spec.values()))
        closure = diag_closure if roles_used == ["x"] else escape_closure
        lhs = canonical_term(subst_term(eq2.lhs, spec))
        rhs = canonical_term(subst_term(eq2.rhs, spec))
        uf = closure["uf"]
        terms = closure["terms"]
        if lhs in terms and rhs in terms:
            same = uf.find(lhs) == uf.find(rhs)
            cls_size = len(closure["classes"].get(uf.find(lhs), [])) + len(closure["classes"].get(uf.find(rhs), []))
            if cls_size < min_class_size:
                min_class_size = cls_size
                best_same_role = same
                best_lhs, best_rhs, best_name = lhs, rhs, name
            if same:
                best_forced = True
    if best_forced:
        conflict = "closure_forced_theorem_shadow"
    elif best_same_role:
        conflict = "closure_same_role_near"
    elif "x" in best_lhs and "x" in best_rhs:
        conflict = "closure_near_escape_candidate"
    else:
        conflict = "closure_unclassified_escape"
    return {
        "eq2_in_source_diag_closure": bool(best_forced and best_name == "all_same"),
        "eq2_forced_by_bounded_source_closure": bool(best_forced),
        "eq2_near_source_diag_closure": bool(best_same_role),
        "diag_distance": int(0 if best_forced else 1 if best_same_role else 2),
        "target_partition_name": best_name,
        "target_lhs_subst": best_lhs,
        "target_rhs_subst": best_rhs,
        "source_closure_rank": float(diag_closure["closure_rank"]),
        "source_diag_class_count": int(diag_closure["class_count"]),
        "source_diag_largest_class": int(diag_closure["largest_class"]),
        "source_diag_signature_hash": diag_closure["signature_hash"],
        "closure_conflict_type": conflict,
    }


def add_diagonal_closure_atlas(queue: pd.DataFrame, eqs: List[Equation], out_dir: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    banner("BUILDING v16 SOURCE-CLOSURE ATLAS")
    source_ids = sorted(queue.eq1_id.astype(int).unique().tolist())
    source_rows: List[Dict[str, Any]] = []
    source_cache: Dict[int, Tuple[Dict[str, Any], Dict[str, Any]]] = {}
    t0 = time.time()
    for k, sid in enumerate(source_ids, start=1):
        eq = eqs[sid]
        diag = bounded_source_closure(eq, TRACE_ROLES, max_depth=5)
        escape = bounded_source_closure(eq, ESCAPE_ROLES, max_depth=4)
        source_cache[sid] = (diag, escape)
        source_rows.append({
            "eq1_id": sid,
            "eq1": eq.raw,
            "diag_class_count": diag["class_count"],
            "diag_largest_class": diag["largest_class"],
            "diag_direct_equalities": diag["direct_equalities"],
            "diag_congruence_unions": diag["congruence_unions"],
            "diag_closure_rank": diag["closure_rank"],
            "diag_signature_hash": diag["signature_hash"],
            "escape_class_count": escape["class_count"],
            "escape_largest_class": escape["largest_class"],
            "escape_closure_rank": escape["closure_rank"],
            "escape_signature_hash": escape["signature_hash"],
        })
        if k % 50 == 0:
            print(f"  closure {k:,}/{len(source_ids):,} elapsed={time.time()-t0:.1f}s")
    source_df = pd.DataFrame(source_rows)
    save_csv(source_df, out_dir / "v16_0_source_diag_closure.csv")

    pair_rows: List[Dict[str, Any]] = []
    for k, r in enumerate(queue[["eq1_id", "eq2_id"]].itertuples(index=False), start=1):
        i, j = int(r.eq1_id), int(r.eq2_id)
        diag, escape = source_cache[i]
        d = classify_pair_by_source_closure(eqs[i], eqs[j], diag, escape)
        d.update({"eq1_id": i, "eq2_id": j})
        pair_rows.append(d)
        if k % 5000 == 0:
            print(f"  pair closure classify {k:,}/{len(queue):,}")
    pair_df = pd.DataFrame(pair_rows)
    save_csv(pair_df, out_dir / "v16_0_pair_diag_closure_classification.csv")

    queue2 = queue.merge(pair_df, on=["eq1_id", "eq2_id"], how="left")
    # Survivor tilt: prefer diagonal-power residuals that are close but not already closure-forced.
    family_bonus = (queue2["target_family"].astype(str) == "diagonal_power_idempotent_pressure").astype(float) * 600.0
    near_bonus = queue2["closure_conflict_type"].astype(str).map({
        "closure_near_escape_candidate": 550.0,
        "closure_same_role_near": 300.0,
        "closure_unclassified_escape": 160.0,
        "closure_forced_theorem_shadow": -450.0,
    }).fillna(0.0)
    motif_bonus = queue2["pair_micro_basin"].astype(str).map({
        "same_nodes_vardrop": 260.0,
        "taildrop_rhsdrop": 230.0,
        "taildrop_vardrop": 220.0,
        "same_skeleton_var_collapse": 210.0,
        "role_permutation_same_skeleton": 190.0,
        "near_shape_mutation": 130.0,
    }).fillna(0.0)
    queue2["v16_priority"] = queue2["priority"].astype(float) + family_bonus + near_bonus + motif_bonus + queue2["geometry_sharpness"].astype(float) * 18.0
    queue2 = queue2.sort_values(["v16_priority", "priority"], ascending=False).reset_index(drop=True)
    save_csv(queue2, out_dir / "v16_0_active_residual_queue_closure_enriched.csv")
    return queue2, source_df


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
    save_csv(base, out_dir / "v16_0_active_residual_queue.csv")
    print(f"Active residual pairs : {len(base):,}")
    print(f"Unique sources        : {base.eq1_id.nunique():,}")
    print(f"Unique targets        : {base.eq2_id.nunique():,}")
    return base


def build_target_cluster_plan(queue: pd.DataFrame, eqs: List[Equation], out_dir: Path) -> pd.DataFrame:
    banner("BUILDING TARGET-CLUSTER PLAN")
    if "closure_conflict_type" not in queue.columns:
        queue = queue.copy()
        queue["closure_conflict_type"] = "not_classified"
    if "v16_priority" not in queue.columns:
        queue = queue.copy()
        queue["v16_priority"] = queue["priority"]
    group_cols = ["target_family", "pair_micro_basin", "recommended_constructor", "exact_motif", "closure_conflict_type", "eq2_id"]
    plan = queue.groupby(group_cols, dropna=False).agg(
        pairs=("eq1_id", "size"),
        unique_sources=("eq1_id", "nunique"),
        unique_source_shapes=("source_shape_key", "nunique"),
        max_priority=("priority", "max"),
        max_v16_priority=("v16_priority", "max"),
        avg_v16_priority=("v16_priority", "mean"),
        avg_priority=("priority", "mean"),
        avg_geometry_sharpness=("geometry_sharpness", "mean"),
        source_residual_mass=("source_residual_count", "sum"),
        target_residual_count=("target_residual_count", "max"),
        avg_diag_distance=("diag_distance", "mean") if "diag_distance" in queue.columns else ("priority", "mean"),
    ).reset_index()
    plan["eq2"] = plan.eq2_id.map(lambda i: eqs[int(i)].raw)
    closure_bonus = plan["closure_conflict_type"].astype(str).map({
        "closure_near_escape_candidate": 2000.0,
        "closure_same_role_near": 900.0,
        "closure_unclassified_escape": 350.0,
        "closure_forced_theorem_shadow": -1500.0,
    }).fillna(0.0)
    family_bonus = (plan["target_family"].astype(str) == "diagonal_power_idempotent_pressure").astype(float) * 1600.0
    plan["cluster_priority"] = (
        plan.pairs.astype(float) * 10
        + plan.unique_sources.astype(float) * 14
        + plan.unique_source_shapes.astype(float) * 18
        + plan.target_residual_count.astype(float) * 30
        + plan.avg_geometry_sharpness.astype(float) * 10
        + plan.max_v16_priority.astype(float) * 0.35
        + closure_bonus
        + family_bonus
    )
    plan = plan.sort_values(["cluster_priority", "pairs", "unique_sources"], ascending=False).reset_index(drop=True)
    save_csv(plan, out_dir / "v16_0_target_cluster_plan.csv")
    print(plan.head(40).to_string(index=False))
    return plan


def carrier_schedule_for_row(row: pd.Series, eq1: Equation, eq2: Equation) -> List[int]:
    micro, exact = normalize_str(row.get("pair_micro_basin")), normalize_str(row.get("exact_motif"))
    fam = normalize_str(row.get("target_family"))
    conflict = normalize_str(row.get("closure_conflict_type"))
    src_vars = len(set(vars_in_term(eq1.lhs) + vars_in_term(eq1.rhs)))
    tgt_vars = len(set(vars_in_term(eq2.lhs) + vars_in_term(eq2.rhs)))
    if fam == "general_target" and conflict == "closure_unclassified_escape":
        return [7, 8, 9]
    if fam == "diagonal_power_idempotent_pressure" and conflict in ["closure_near_escape_candidate", "closure_same_role_near"]:
        return DIAGONAL_CARRIERS[:]
    if src_vars >= 4:
        return [4, 5, 6]
    if tgt_vars >= 4 or micro in ["near_shape_mutation", "role_permutation_same_skeleton"] or "rhs_expand" in exact:
        return HARD_CARRIERS[:]
    return DEFAULT_CARRIERS[:]


def apply_carrier_bounds(carriers: List[int], min_carrier: int, max_carrier: int) -> List[int]:
    out = [n for n in carriers if min_carrier <= n <= max_carrier]
    return sorted(dict.fromkeys(out))


def bias_schedule_for_row(row: pd.Series) -> List[str]:
    micro, fam = normalize_str(row.get("pair_micro_basin")), normalize_str(row.get("target_family"))
    if micro == "role_permutation_same_skeleton":
        return ["none", "role_escape", "noncomm", "anti_projection", "row_distinct", "col_distinct", "diag_split"]
    if micro == "near_shape_mutation":
        return ["none", "assoc_diag_split", "power_split_r", "power_split_l", "anti_projection", "diag_split", "noncomm", "row_distinct", "col_distinct"]
    if fam == "diagonal_power_idempotent_pressure":
        return ["none", "power_split_r", "power_split_l", "assoc_diag_split", "diag_split", "diagonal_power", "role_escape", "anti_projection", "noncomm", "row_distinct"]
    if micro.startswith("taildrop"):
        return ["none", "role_escape", "anti_projection", "left_bias", "right_bias", "diag_split", "noncomm"]
    return BIAS_SCHEDULE[:]


def bias_schedule_for_round(row: pd.Series, round_idx: int) -> List[str]:
    base = bias_schedule_for_row(row)
    if round_idx == 0:
        # Breadth pass: first ask the pure countermodel question, plus one constructor
        # hint. Extra biases are often overconstraints on these residuals.
        keep = ["none"]
        for b in ["role_escape", "power_split_r", "assoc_diag_split", "noncomm"]:
            if b in base:
                keep.append(b)
                break
        return keep
    return base


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
    conflict = normalize_str(row.get("closure_conflict_type"))
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
        if conflict in ["closure_unclassified_escape", "closure_near_escape_candidate"] and len(tgt_vars) >= 2:
            # Escape constructors need role separation first. The all-same partition just replays
            # the diagonal quotient and burns the pair budget on theorem-shadow behavior.
            return (-distinct, max_cnt, tuple(blocks))
        if "var_minus" in exact or micro in ["same_nodes_vardrop", "same_skeleton_var_collapse"]:
            return (-distinct, max_cnt, tuple(blocks))
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
    p.add_argument("--max-target-clusters", type=int, default=750)
    p.add_argument("--max-pairs-per-cluster", type=int, default=18)
    p.add_argument("--max-probes-per-pair", type=int, default=28)
    p.add_argument("--max-total-z3-calls", type=int, default=16000)
    p.add_argument("--max-tables-to-find", type=int, default=500)
    p.add_argument("--max-new-hits-target", type=int, default=1500)
    p.add_argument("--pair-timeout-ms-base", type=int, default=6500)
    p.add_argument("--pair-timeout-ms-hard", type=int, default=14500)
    p.add_argument("--cluster-budget-sec", type=float, default=150.0)
    p.add_argument("--global-budget-sec", type=float, default=7.0 * 3600)
    p.add_argument("--max-partitions-per-target", type=int, default=16)
    p.add_argument("--max-target-var-count-for-full-partitions", type=int, default=5)
    p.add_argument("--max-source-var-assignments", type=int, default=9 ** 4)
    p.add_argument("--min-carrier", type=int, default=3)
    p.add_argument("--max-carrier", type=int, default=9)
    p.add_argument("--checkpoint-every-z3-calls", type=int, default=100)
    p.add_argument("--checkpoint-every-tables", type=int, default=10)
    p.add_argument("--emit-lean-templates", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--max-lean-templates", type=int, default=8000)
    p.add_argument("--focus-closure-types", default="", help="Comma-separated closure_conflict_type values to keep before planning.")
    p.add_argument("--focus-target-families", default="", help="Comma-separated target_family values to keep before planning.")
    args, _ = p.parse_known_args()
    return args


def main() -> None:
    if not Z3_AVAILABLE:
        raise RuntimeError("Z3 is required for v16.0.")
    args = parse_args()
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)

    base_dir = Path(args.base_dir).expanduser()
    prev_15_10 = base_dir / "sair_stage2_mathgraph_v15_10_residual_witness_partition_constructor"
    prev_15_9c = base_dir / "sair_stage2_mathgraph_v15_9c_winner_table_algebra_amplifier"
    prev_15_9b = base_dir / "sair_stage2_mathgraph_v15_9b_target_basin_first_finisher"
    out_dir = base_dir / "sair_stage2_mathgraph_v16_0_obstruction_factory"
    table_dir = out_dir / "tables"
    lean_dir = out_dir / "lean_templates"
    ensure_dir(table_dir)
    ensure_dir(lean_dir)

    mask_candidates = [
        str(prev_15_10 / "v15_10_covered_false_mask_final.npy"),
        str(prev_15_10 / "v15_10_covered_false_mask_checkpoint.npy"),
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
        str(prev_15_10 / "v15_10_remaining_queue_final_enriched.csv"),
        str(prev_15_10 / "v15_10_active_residual_queue.csv"),
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
    }, out_dir / "v16_0_core_load_summary.json")

    banner("BUILDING EQUATION FEATURES")
    features_df = build_equation_features(eqs)
    save_csv(features_df, out_dir / "v16_0_equation_features.csv")
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
    save_json({"best_mask_path": best_path, "covered_false": starting_covered, "false_total": false_total, "remaining_false": starting_remaining, "mask_candidates": mask_infos}, out_dir / "v16_0_best_mask_loaded.json")

    queue = load_or_build_queue(covered_mask, false_mask, features_df, eqs, out_dir, queue_candidates)
    queue, source_closure_df = add_diagonal_closure_atlas(queue, eqs, out_dir)
    if args.focus_closure_types.strip():
        focus_types = {x.strip() for x in args.focus_closure_types.split(",") if x.strip()}
        before = len(queue)
        queue = queue[queue["closure_conflict_type"].astype(str).isin(focus_types)].copy()
        print(f"Focused queue by closure_conflict_type={sorted(focus_types)}: {len(queue):,}/{before:,} pairs")
        save_csv(queue, out_dir / "v16_0_active_residual_queue_focus.csv")
    if args.focus_target_families.strip():
        focus_families = {x.strip() for x in args.focus_target_families.split(",") if x.strip()}
        before = len(queue)
        queue = queue[queue["target_family"].astype(str).isin(focus_families)].copy()
        print(f"Focused queue by target_family={sorted(focus_families)}: {len(queue):,}/{before:,} pairs")
        save_csv(queue, out_dir / "v16_0_active_residual_queue_focus.csv")
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
        save_csv(pd.DataFrame(recoveries), out_dir / "v16_0_recoveries_checkpoint.csv")
        save_csv(pd.DataFrame(attempts), out_dir / "v16_0_attempts_checkpoint.csv")
        save_csv(pd.DataFrame(tables_log), out_dir / "v16_0_tables_checkpoint.csv")
        save_csv(pd.DataFrame(lean_manifest), out_dir / "v16_0_lean_manifest_checkpoint.csv")
        shape_df = pd.DataFrame([{"source_shape_key": k, **v} for k, v in source_shape_states.items()])
        save_csv(shape_df, out_dir / "v16_0_source_shape_states_checkpoint.csv")
        np.save(out_dir / "v16_0_covered_false_mask_checkpoint.npy", covered_mask)
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
        }, out_dir / "v16_0_status_checkpoint.json")
        print(f"Checkpoint {label}: covered={int(covered_mask.sum()):,}/{false_total:,} remaining={current_remaining_count():,} new={new_covered_total:,} z3={z3_calls:,} tables={tables_found:,}")

    def emit_lean_template(eq1_id: int, eq2_id: int, table: List[List[int]], witness: Optional[Dict[str, int]], h: str) -> str:
        path = lean_dir / f"countermodel_eq{eq1_id}_not_eq{eq2_id}_{h[:8]}.lean"
        payload = {"eq1_id": eq1_id, "eq2_id": eq2_id, "eq1": eqs[eq1_id].raw, "eq2": eqs[eq2_id].raw, "carrier_size": len(table), "table": table, "witness": witness, "table_hash": h}
        path.write_text(
            "-- SAIR Stage 2 finite magma countermodel template\n"
            "-- Generated by v16.0 obstruction factory.\n\n"
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

    banner("RUNNING v16.0 OBSTRUCTION-FACTORY SEARCH")
    checkpoint("initial")

    cluster_counter = 0
    for cluster_row in target_cluster_plan.itertuples(index=False):
        if time.time() - start_time > args.global_budget_sec or z3_calls >= args.max_total_z3_calls or tables_found >= args.max_tables_to_find or new_covered_total >= args.max_new_hits_target or current_remaining_count() == 0:
            break
        cluster_counter += 1
        if cluster_counter > args.max_target_clusters:
            break
        eq2_id = int(getattr(cluster_row, "eq2_id"))
        tfam, micro, cons, motif, closure_type = (normalize_str(getattr(cluster_row, c, "")) for c in ["target_family", "pair_micro_basin", "recommended_constructor", "exact_motif", "closure_conflict_type"])
        live_cluster = queue[
            (queue.eq2_id.astype(int) == eq2_id)
            & (queue.target_family.astype(str) == tfam)
            & (queue.pair_micro_basin.astype(str) == micro)
            & (queue.recommended_constructor.astype(str) == cons)
            & (queue.exact_motif.astype(str) == motif)
            & (queue.closure_conflict_type.astype(str) == closure_type)
        ].copy()
        live_cluster = live_cluster[[bool(false_mask[int(r.eq1_id), int(r.eq2_id)] and not covered_mask[int(r.eq1_id), int(r.eq2_id)]) for r in live_cluster[["eq1_id", "eq2_id"]].itertuples(index=False)]]
        if live_cluster.empty:
            continue
        sort_cols = ["v16_priority", "priority", "source_residual_count"] if "v16_priority" in live_cluster.columns else ["priority", "source_residual_count"]
        live_cluster = live_cluster.sort_values(sort_cols, ascending=False)
        cluster_start = time.time()
        print("\n" + "-" * 112)
        print(f"[target-cluster {cluster_counter}/{min(args.max_target_clusters, len(target_cluster_plan))}] eq2={eq2_id} pairs={len(live_cluster):,} unique_sources={live_cluster.eq1_id.nunique():,}")
        print(f"target_family={tfam} micro={micro} constructor={cons} motif={motif}")
        print(f"closure_conflict_type={closure_type}")
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
            src_vars = sorted(set(vars_in_term(eq1.lhs) + vars_in_term(eq1.rhs)))
            tgt_vars = sorted(set(vars_in_term(eq2.lhs) + vars_in_term(eq2.rhs)))
            conflict = normalize_str(row.get("closure_conflict_type"))
            if conflict == "closure_forced_theorem_shadow" and safe_int(row.get("diag_distance"), 2) == 0:
                # This is evidence for a theorem-shadow or large-model basin. Do not spend generic Z3 here.
                get_shape_state(source_shape_key)["theorem_shadow_skips"] = get_shape_state(source_shape_key).get("theorem_shadow_skips", 0) + 1
                continue
            print(f"  probe {probe_idx}/{len(selected_rows)} EQ{i}->{j} src_vars={len(src_vars)} tgt_vars={len(tgt_vars)} conflict={conflict} shape_state={json.dumps(get_shape_state(source_shape_key))}")
            print(f"    EQ1: {eq1.raw}")
            attempts_for_pair = 0
            pair_hit = False
            carriers = apply_carrier_bounds(carrier_schedule_for_row(row, eq1, eq2), args.min_carrier, args.max_carrier)
            carriers = [n for n in carriers if n ** len(src_vars) <= args.max_source_var_assignments]
            partitions_by_n = {
                n: witness_partitions_for_target(eq2, row, n, args.max_partitions_per_target, args.max_target_var_count_for_full_partitions)
                for n in carriers
            }
            max_partition_count = max((len(v) for v in partitions_by_n.values()), default=0)
            # Interleave carriers before spending the whole pair budget on one n.
            # This matters for the large-carrier escape corridor where n=8 often
            # times out/unsats but n=9 can produce a basin table.
            for round_idx in range(2):
                if pair_hit or attempts_for_pair >= args.max_probes_per_pair:
                    break
                for part_pos in range(max_partition_count):
                    if pair_hit or attempts_for_pair >= args.max_probes_per_pair:
                        break
                    for n in carriers:
                        partitions = partitions_by_n.get(n, [])
                        if part_pos >= len(partitions):
                            continue
                        part_idx = part_pos + 1
                        part = partitions[part_pos]
                        max_offsets = 1 if round_idx == 0 else min(n, 3)
                        for offset in range(max_offsets):
                            witness_values = partition_to_witness_values(part, n, offset)
                            if witness_values is None:
                                continue
                            for bias in bias_schedule_for_round(row, round_idx):
                                if (
                                    time.time() - cluster_start > args.cluster_budget_sec
                                    or time.time() - start_time > args.global_budget_sec
                                    or z3_calls >= args.max_total_z3_calls
                                    or attempts_for_pair >= args.max_probes_per_pair
                                ):
                                    break
                                attempts_for_pair += 1
                                z3_calls += 1
                                res = solve_pair_witness_partition_uf(eq1, eq2, n, witness_values, bias, timeout_for_row(row, n, args.pair_timeout_ms_base, args.pair_timeout_ms_hard))
                                status, table, elapsed = normalize_str(res.get("status")), res.get("table"), safe_float(res.get("elapsed_sec"))
                                hit_count = 0
                                attempt_rec = {
                                    "eq1_id": i,
                                    "eq2_id": j,
                                    "status": status,
                                    "carrier": n,
                                    "bias": bias,
                                    "round_idx": round_idx,
                                    "partition_idx": part_idx,
                                    "partition": json.dumps(part, ensure_ascii=False),
                                    "witness_values": json.dumps(witness_values, ensure_ascii=False),
                                    "elapsed_sec": elapsed,
                                    "clauses": safe_int(res.get("clauses")),
                                    "src_assign": safe_int(res.get("src_assign")),
                                    "source_shape_key": source_shape_key,
                                    "target_family": tfam,
                                    "pair_micro_basin": micro,
                                    "recommended_constructor": cons,
                                    "exact_motif": motif,
                                    "closure_conflict_type": conflict,
                                    "diag_distance": safe_int(row.get("diag_distance"), -1),
                                    "source_diag_signature_hash": normalize_str(row.get("source_diag_signature_hash")),
                                    "target_partition_name": normalize_str(row.get("target_partition_name")),
                                }
                                if status == "sat" and table is not None:
                                    ok, _ = validate_countermodel(eq1, eq2, table)
                                    attempt_rec["validated_pair"] = bool(ok)
                                    if ok:
                                        h = table_hash(table)
                                        attempt_rec["table_hash"] = h
                                        hit_count = replay_sat_table(table, i, j, "v16_0_obstruction_factory", {"bias": bias, "carrier": n, "partition_idx": part_idx, "target_family": tfam, "pair_micro_basin": micro, "constructor": cons, "closure_conflict_type": conflict, "diag_distance": safe_int(row.get("diag_distance"), -1)})
                                        pair_hit = hit_count > 0 or ok
                                        print(f"      SAT {'+ RECOVERED' if hit_count else 'pair-valid global-new=0'} table={h} n={n} bias={bias} hits={hit_count}")
                                    else:
                                        print(f"      SAT but failed concrete validation n={n} bias={bias} elapsed={elapsed:.2f}s")
                                else:
                                    if attempts_for_pair <= 5 or status != "unsat":
                                        print(f"      n={n} bias={bias} status={status} part={part_idx} round={round_idx} elapsed={elapsed:.2f}s src_assign={safe_int(res.get('src_assign'))}")
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

    banner("FINALIZING v16.0")
    ii, jj = np.where(false_mask & ~covered_mask)
    final_remaining_df = pd.DataFrame({"eq1_id": ii.astype(np.int32), "eq2_id": jj.astype(np.int32)})
    save_csv(final_remaining_df, out_dir / "v16_0_remaining_pairs_final.csv")
    rows = []
    for r in final_remaining_df.itertuples(index=False):
        i, j = int(r.eq1_id), int(r.eq2_id)
        d = pair_feature_dict(features_by_id.loc[i], features_by_id.loc[j], eqs[i], eqs[j])
        d.update({"eq1_id": i, "eq2_id": j, "eq1": eqs[i].raw, "eq2": eqs[j].raw})
        rows.append(d)
    final_remaining_enriched = pd.DataFrame(rows)
    closure_cols = [
        "eq1_id",
        "eq2_id",
        "eq2_in_source_diag_closure",
        "eq2_forced_by_bounded_source_closure",
        "eq2_near_source_diag_closure",
        "diag_distance",
        "target_partition_name",
        "target_lhs_subst",
        "target_rhs_subst",
        "source_closure_rank",
        "source_diag_class_count",
        "source_diag_largest_class",
        "source_diag_signature_hash",
        "closure_conflict_type",
        "v16_priority",
    ]
    closure_cols = [c for c in closure_cols if c in queue.columns]
    if not final_remaining_enriched.empty and len(closure_cols) > 2:
        final_remaining_enriched = final_remaining_enriched.merge(
            queue[closure_cols].drop_duplicates(["eq1_id", "eq2_id"]),
            on=["eq1_id", "eq2_id"],
            how="left",
        )
    save_csv(final_remaining_enriched, out_dir / "v16_0_remaining_queue_final_enriched.csv")
    if not final_remaining_enriched.empty:
        final_group_cols = ["target_family", "pair_micro_basin", "recommended_constructor", "exact_motif"]
        if "closure_conflict_type" in final_remaining_enriched.columns:
            final_group_cols.append("closure_conflict_type")
        final_basin_summary = final_remaining_enriched.groupby(final_group_cols, dropna=False).agg(
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
    save_csv(final_basin_summary, out_dir / "v16_0_remaining_basin_summary_final.csv")
    save_csv(pd.DataFrame([{"source_shape_key": k, **v} for k, v in source_shape_states.items()]), out_dir / "v16_0_source_shape_states_final.csv")
    np.save(out_dir / "v16_0_covered_false_mask_final.npy", covered_mask)
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
        "method": "obstruction_factory_with_bounded_source_closure",
    }
    save_json(final_summary, out_dir / "v16_0_final_summary.json")
    checkpoint("final")
    print("\n" + "=" * 112)
    print("v16.0 FINAL SUMMARY")
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
