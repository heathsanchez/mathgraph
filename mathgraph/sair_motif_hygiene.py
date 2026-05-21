"""Hygiene layer for SAIR finite-countermodel mechanism motifs."""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd


VALID_CONSTRUCTORS = {
    "right_projection_n2",
    "left_projection_n2",
    "right_projection_n3",
    "left_projection_n3",
    "constant_n2_0",
    "constant_n2_1",
    "constant_n3_0",
    "constant_n3_1",
    "xor_mod_2",
    "add_mod_2",
    "add_mod_3",
    "sub_mod_2",
    "sub_mod_3",
    "rectangular_band_n4",
    "comm_nonassoc_n3",
    "perturbation_n3",
    "min_n2",
    "max_n2",
    "min_n3",
    "max_n3",
}

VALID_BASINS = {
    "projection_pressure",
    "associative_or_deep_term_pressure",
    "idempotent_band_pressure",
    "collapse_or_constant_pressure",
    "commutativity_pressure",
    "mixed_sair_false_pair",
}

VALID_CARRIERS = {"n2", "n3", "n4", "n5"}


@dataclass(frozen=True)
class SAIRMechanismAtom:
    atom: str
    family: str
    source: str = ""
    advisory_only: bool = True


@dataclass(frozen=True)
class SAIRCleanTrace:
    trace_id: str
    task_id: str
    constructor_name: str
    basin: str
    atoms: tuple[str, ...]
    batch_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    advisory_only: bool = True


@dataclass(frozen=True)
class SAIRMotifHygieneConfig:
    require_promotiongate_acceptance: bool = True
    max_atom_length: int = 96
    allow_mixed_basin: bool = True


@dataclass(frozen=True)
class SAIRMotifHygieneReport:
    input_rows: int
    accepted_rows: int
    cleaned_rows: int
    rejected_rows: int
    total_atoms_before: int
    total_atoms_after: int
    rejected_atom_count: int
    rejected_atom_reason_counts: dict[str, int]
    accepted_atom_family_counts: dict[str, int]
    top_clean_constructors: list[tuple[str, int]]
    top_clean_constructor_families: list[tuple[str, int]]
    top_clean_basins: list[tuple[str, int]]
    advisory_boundary_ok: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "input_rows": self.input_rows,
            "accepted_rows": self.accepted_rows,
            "cleaned_rows": self.cleaned_rows,
            "rejected_rows": self.rejected_rows,
            "total_atoms_before": self.total_atoms_before,
            "total_atoms_after": self.total_atoms_after,
            "rejected_atom_count": self.rejected_atom_count,
            "rejected_atom_reason_counts": dict(self.rejected_atom_reason_counts),
            "accepted_atom_family_counts": dict(self.accepted_atom_family_counts),
            "top_clean_constructors": list(self.top_clean_constructors),
            "top_clean_constructor_families": list(self.top_clean_constructor_families),
            "top_clean_basins": list(self.top_clean_basins),
            "advisory_boundary_ok": self.advisory_boundary_ok,
        }


def normalize_constructor_name(value: Any) -> str | None:
    text = _clean_text(value)
    if text in VALID_CONSTRUCTORS:
        return text
    if text.startswith("constructor:"):
        return normalize_constructor_name(text.split(":", 1)[1])
    return None


def normalize_basin_name(value: Any) -> str | None:
    text = _clean_text(value)
    aliases = {
        "projection_refutable": "projection_pressure",
        "right_projection_refutable": "projection_pressure",
        "constant_refutable": "collapse_or_constant_pressure",
        "affine_refutable": "commutativity_pressure",
        "semilattice_refutable": "idempotent_band_pressure",
        "noncomm_assoc_refutable": "associative_or_deep_term_pressure",
        "hard_residual_or_unknown": "associative_or_deep_term_pressure",
    }
    if text in aliases:
        return aliases[text]
    if text in VALID_BASINS:
        return text
    if text.startswith("basin:"):
        return normalize_basin_name(text.split(":", 1)[1])
    return None


def normalize_carrier_name(value: Any) -> str | None:
    text = _clean_text(value)
    if text in VALID_CARRIERS:
        return text
    match = re.search(r"_n([2-5])(?:_|$)", text)
    if match:
        return f"n{match.group(1)}"
    if text.startswith("carrier:"):
        return normalize_carrier_name(text.split(":", 1)[1])
    return None


def normalize_equation_shape_atoms(eq1: Any, eq2: Any) -> list[str]:
    s1 = str(eq1 or "")
    s2 = str(eq2 or "")
    vars1 = set(re.findall(r"\b[x-z]\b", s1))
    vars2 = set(re.findall(r"\b[x-z]\b", s2))
    ops1 = s1.count("*")
    ops2 = s2.count("*")
    atoms = [
        f"eq1_vars_{len(vars1)}",
        f"eq2_vars_{len(vars2)}",
        f"eq1_ops_{min(ops1, 9)}",
        f"eq2_ops_{min(ops2, 9)}",
        f"delta_ops_{max(-9, min(9, ops2 - ops1))}",
    ]
    if _has_repeated_var(s1):
        atoms.append("source_repeats")
    if _has_repeated_var(s2):
        atoms.append("target_repeats")
    if ops2 > ops1:
        atoms.append("target_expands")
    if ops2 < ops1:
        atoms.append("target_compresses")
    if vars1 == vars2:
        atoms.append("same_var_set")
    if vars2 - vars1:
        atoms.append("newvar_pressure")
    return [f"eq_shape:{atom}" for atom in atoms]


def extract_clean_mechanism_atoms(row: Any) -> list[str]:
    data = _row_dict(row)
    cert = _json_field(data.get("certificate"))
    meta = _json_field(cert.get("metadata")) if isinstance(cert, dict) else {}
    task = _json_field(meta.get("task")) if isinstance(meta, dict) else {}
    task_meta = _json_field(task.get("metadata")) if isinstance(task, dict) else {}
    constructor = normalize_constructor_name(data.get("constructor_name") or meta.get("constructor_name"))
    basin = normalize_basin_name(data.get("family") or task.get("family"))
    atoms: list[str] = []
    if constructor:
        atoms.append(f"constructor:{constructor}")
        atoms.append(f"constructor_family:{_constructor_family(constructor)}")
        carrier = normalize_carrier_name(constructor)
        if carrier:
            atoms.append(f"carrier:{carrier}")
    if basin:
        atoms.append(f"basin:{basin}")
    eq1 = task.get("source_equation") or task_meta.get("equation1") or meta.get("source_equation")
    eq2 = task.get("target_equation") or task_meta.get("equation2") or meta.get("target_equation")
    atoms.extend(normalize_equation_shape_atoms(eq1, eq2))
    clean = []
    for atom in atoms:
        rejected, _reason = reject_leaky_or_junk_atom(atom, reason=True)
        if not rejected and atom not in clean:
            clean.append(atom)
    return clean


def reject_leaky_or_junk_atom(atom: Any, reason: bool = True) -> tuple[bool, str] | bool:
    text = str(atom or "").strip()
    low = text.lower()
    rejected = False
    why = ""
    if not text or low in {"nan", "none", "null", "unknown", "unknown_constructor", "unknown_basin", "unknown_route"}:
        rejected, why = True, "empty_or_unknown"
    elif len(text) > 96 or text.startswith("breakthrough-constructor-hint_"):
        rejected, why = True, "long_or_internal_id"
    elif any(ch in text for ch in "{}[]") or text.startswith(("{", "[")):
        rejected, why = True, "serialized_payload"
    elif re.fullmatch(r"[-+]?\d+(?:\.\d+)?", text):
        rejected, why = True, "number_only"
    elif any(token in low for token in ("success", "failed", "residual", "accepted", "rejected", "finite_countermodel_found", "lean_verified", "verified", "terminal", "status", "outcome", "source_file", "batch")):
        rejected, why = True, "status_or_answer_leakage"
    elif low in {"hint:constructor", "hint:table", "hint:min"}:
        rejected, why = True, "generic_hint"
    elif text.startswith("carrier:") and text.split(":", 1)[1] not in VALID_CARRIERS:
        rejected, why = True, "bad_carrier"
    elif text.startswith("constructor:") and text.split(":", 1)[1] not in VALID_CONSTRUCTORS:
        rejected, why = True, "bad_constructor"
    elif text.startswith("basin:") and text.split(":", 1)[1] not in VALID_BASINS:
        rejected, why = True, "bad_basin"
    elif "=" in text and not text.startswith("eq_shape:"):
        rejected, why = True, "raw_equation_text"
    return (rejected, why) if reason else rejected


def clean_breakthrough_trace_rows(df: pd.DataFrame, config: SAIRMotifHygieneConfig | None = None) -> tuple[pd.DataFrame, SAIRMotifHygieneReport]:
    cfg = config or SAIRMotifHygieneConfig()
    accepted = filter_to_accepted_finite_countermodel_rows(df, cfg)
    rows = []
    rejected_reasons: Counter[str] = Counter()
    total_before = 0
    for _idx, row in accepted.iterrows():
        raw_atoms = _raw_candidate_atoms(row)
        total_before += len(raw_atoms)
        for atom in raw_atoms:
            rejected, why = reject_leaky_or_junk_atom(atom, reason=True)
            if rejected:
                rejected_reasons[why] += 1
        atoms = extract_clean_mechanism_atoms(row)
        if not atoms:
            continue
        constructor = normalize_constructor_name(row.get("constructor_name")) or ""
        basin = normalize_basin_name(row.get("family")) or ""
        rows.append(
            {
                "trace_id": row.get("attempt_id", ""),
                "task_id": row.get("task_id", ""),
                "constructor_name": constructor,
                "constructor_family": _constructor_family(constructor) if constructor else "",
                "carrier": normalize_carrier_name(constructor) or "",
                "basin": basin,
                "atoms_json": json.dumps(atoms, sort_keys=True),
                "atom_count": len(atoms),
                "batch_id": row.get("batch_id", "batch_0"),
                "advisory_only": True,
            }
        )
    clean_df = pd.DataFrame(rows)
    atom_family_counts = Counter()
    constructor_counts = Counter()
    family_counts = Counter()
    basin_counts = Counter()
    for row in rows:
        atoms = json.loads(row["atoms_json"])
        for atom in atoms:
            atom_family_counts[atom.split(":", 1)[0]] += 1
        constructor_counts[row["constructor_name"]] += 1
        family_counts[row["constructor_family"]] += 1
        basin_counts[row["basin"]] += 1
    report = SAIRMotifHygieneReport(
        input_rows=len(df),
        accepted_rows=len(accepted),
        cleaned_rows=len(clean_df),
        rejected_rows=max(0, len(accepted) - len(clean_df)),
        total_atoms_before=total_before,
        total_atoms_after=sum(int(row["atom_count"]) for row in rows),
        rejected_atom_count=sum(rejected_reasons.values()),
        rejected_atom_reason_counts=dict(rejected_reasons),
        accepted_atom_family_counts=dict(atom_family_counts),
        top_clean_constructors=constructor_counts.most_common(20),
        top_clean_constructor_families=family_counts.most_common(20),
        top_clean_basins=basin_counts.most_common(20),
        advisory_boundary_ok=bool(clean_df.empty or clean_df["advisory_only"].all()),
    )
    return clean_df, report


def is_promotiongate_accepted_row(row: Any) -> bool:
    data = _row_dict(row)
    if str(data.get("promotion_accepted", "")).lower() not in {"true", "1", "yes"}:
        return False
    decision = _json_field(data.get("promotion_decision"))
    cert = _json_field(data.get("certificate"))
    return bool(
        decision.get("accepted") is True
        and decision.get("decision_kind") == "ACCEPT_FOR_LAWBOOK"
        and cert.get("certificate_kind") == "FINITE_COUNTERMODEL"
        and cert.get("boundary_valid") is True
    )


def filter_to_accepted_finite_countermodel_rows(df: pd.DataFrame, config: SAIRMotifHygieneConfig | None = None) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    mask = df.apply(is_promotiongate_accepted_row, axis=1)
    return df[mask].copy()


def write_hygiene_audit(clean_df: pd.DataFrame, report: SAIRMotifHygieneReport, out_dir: str | Path) -> dict[str, str]:
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    clean_path = output / "clean_trace_rows.csv"
    report_path = output / "hygiene_report.json"
    clean_df.to_csv(clean_path, index=False)
    report_path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return {"clean_trace_rows": str(clean_path), "hygiene_report": str(report_path)}


def _constructor_family(name: str) -> str:
    if "projection" in name:
        return "projection"
    if name.startswith("constant"):
        return "constant"
    if name.startswith(("add_mod", "sub_mod", "xor_mod")):
        return "affine_mod"
    if name.startswith(("min_", "max_")):
        return "semilattice"
    if name.startswith("rectangular"):
        return "rectangular_band"
    if "nonassoc" in name:
        return "nonassoc"
    if "perturbation" in name:
        return "perturbation"
    return "mixed"


def _raw_candidate_atoms(row: Any) -> list[str]:
    data = _row_dict(row)
    atoms = [data.get("constructor_name"), data.get("family"), data.get("entry_id"), data.get("diagnostic")]
    cert = _json_field(data.get("certificate"))
    meta = _json_field(cert.get("metadata")) if isinstance(cert, dict) else {}
    task = _json_field(meta.get("task")) if isinstance(meta, dict) else {}
    atoms.extend([meta.get("constructor_name"), task.get("source_equation"), task.get("target_equation")])
    return [str(atom) for atom in atoms if atom is not None]


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return str(value).strip()


def _json_field(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return {}
    try:
        parsed = json.loads(str(value))
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def _row_dict(row: Any) -> dict[str, Any]:
    return row.to_dict() if hasattr(row, "to_dict") else dict(row)


def _has_repeated_var(text: str) -> bool:
    vars_ = re.findall(r"\b[x-z]\b", text)
    return len(vars_) != len(set(vars_))
