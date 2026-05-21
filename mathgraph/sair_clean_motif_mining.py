"""Mine advisory clean motifs from SAIR finite-countermodel traces."""

from __future__ import annotations

import itertools
import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from mathgraph.hashing import content_id


@dataclass(frozen=True)
class SAIRMotif:
    motif_id: str
    atoms: tuple[str, ...]
    support: int
    score: float
    advisory_only: bool = True


@dataclass(frozen=True)
class SAIRMotifMiningConfig:
    min_support: int = 2
    max_complexity: int = 4
    allow_single_batch: bool = True
    top_k: int = 200


@dataclass(frozen=True)
class SAIRMotifMiningReport:
    input_clean_rows: int
    motif_count: int
    deduplicated_motif_count: int
    top_score: float
    rejected_junk_count: int
    advisory_boundary_ok: bool

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


def mine_clean_constructor_motifs(clean_df: pd.DataFrame, config: SAIRMotifMiningConfig | None = None) -> pd.DataFrame:
    cfg = config or SAIRMotifMiningConfig()
    counter: Counter[tuple[str, ...]] = Counter()
    tasks: dict[tuple[str, ...], set[str]] = defaultdict(set)
    batches: dict[tuple[str, ...], set[str]] = defaultdict(set)
    for _idx, row in clean_df.iterrows():
        atoms = tuple(sorted(json.loads(row.get("atoms_json", "[]"))))
        for size in range(1, min(cfg.max_complexity, len(atoms)) + 1):
            for combo in itertools.combinations(atoms, size):
                counter[combo] += 1
                tasks[combo].add(str(row.get("task_id", "")))
                batches[combo].add(str(row.get("batch_id", "batch_0")))
    rows = []
    for atoms, support in counter.items():
        if support < cfg.min_support:
            continue
        if not cfg.allow_single_batch and len(batches[atoms]) < 2:
            continue
        rows.append(
            {
                "motif_id": content_id("sair-clean-motif", atoms),
                "atoms_json": json.dumps(list(atoms), sort_keys=True),
                "support": support,
                "task_support": len(tasks[atoms]),
                "batch_support": len(batches[atoms]),
                "complexity": len(atoms),
                "advisory_only": True,
            }
        )
    return pd.DataFrame(rows)


def score_clean_motifs(clean_df: pd.DataFrame, motifs_df: pd.DataFrame, config: SAIRMotifMiningConfig | None = None) -> pd.DataFrame:
    if motifs_df.empty:
        return motifs_df.copy()
    base = max(1, len(clean_df))
    rows = []
    for row in motifs_df.to_dict("records"):
        atoms = json.loads(row["atoms_json"])
        specificity = sum(_specificity(atom) for atom in atoms)
        support = int(row["support"])
        batch_bonus = 0.5 * max(0, int(row["batch_support"]) - 1)
        complexity_penalty = max(0, int(row["complexity"]) - 3) * 0.35
        lift = (support / base) / max(1 / base, 0.01)
        score = support + specificity + batch_bonus + 0.1 * lift - complexity_penalty
        row.update({"lift": lift, "score": score})
        rows.append(row)
    out = pd.DataFrame(rows).sort_values(["score", "support"], ascending=[False, False]).reset_index(drop=True)
    return out


def deduplicate_subsumed_motifs(motifs_df: pd.DataFrame, config: SAIRMotifMiningConfig | None = None) -> pd.DataFrame:
    if motifs_df.empty:
        return motifs_df.copy()
    kept = []
    seen: list[set[str]] = []
    for row in motifs_df.to_dict("records"):
        atoms = set(json.loads(row["atoms_json"]))
        score = float(row.get("score", 0.0))
        subsumed = any(atoms < other and score <= float(other_row.get("score", 0.0)) for other, other_row in seen)
        if not subsumed:
            kept.append(row)
            seen.append((atoms, row))
    return pd.DataFrame(kept).head((config or SAIRMotifMiningConfig()).top_k)


def motif_to_reason_atlas_entry(row: dict[str, Any]) -> dict[str, Any]:
    atoms = json.loads(row["atoms_json"]) if isinstance(row.get("atoms_json"), str) else list(row.get("atoms", []))
    return {
        "entry_id": row.get("motif_id") or content_id("sair-clean-motif-entry", atoms),
        "kind": "CONSTRUCTOR_HINT",
        "name": "clean_sair_motif:" + "|".join(atoms[:4]),
        "atoms": atoms,
        "pattern": " & ".join(atoms),
        "payload": dict(row),
        "evidence_kind": "ADVISORY_CLEAN_SAIR_MOTIF",
        "advisory_only": True,
        "verifier_promoted": False,
        "trust": "PROMOTED_ADVISORY",
        "support": int(row.get("support", 0) or 0),
        "promotion_score": float(row.get("score", 0.0) or 0.0),
        "priority_score": float(row.get("score", 0.0) or 0.0),
    }


def export_clean_motifs(clean_df: pd.DataFrame, motifs_df: pd.DataFrame, out_dir: str | Path) -> dict[str, str]:
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    ranked = output / "clean_constructor_motifs_ranked.csv"
    family = output / "clean_motif_family_summary.csv"
    entries = output / "clean_motif_reason_atlas_entries.jsonl"
    report = output / "clean_motif_mining_report.json"
    motifs_df.to_csv(ranked, index=False)
    motif_family_summary(motifs_df).to_csv(family, index=False)
    with entries.open("w", encoding="utf-8") as handle:
        for row in motifs_df.to_dict("records"):
            handle.write(json.dumps(motif_to_reason_atlas_entry(row), sort_keys=True) + "\n")
    mining_report = SAIRMotifMiningReport(
        input_clean_rows=len(clean_df),
        motif_count=len(motifs_df),
        deduplicated_motif_count=len(motifs_df),
        top_score=float(motifs_df["score"].max()) if not motifs_df.empty and "score" in motifs_df else 0.0,
        rejected_junk_count=0,
        advisory_boundary_ok=bool(motifs_df.empty or motifs_df["advisory_only"].all()),
    )
    report.write_text(json.dumps(mining_report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return {"ranked": str(ranked), "family_summary": str(family), "entries": str(entries), "report": str(report)}


def motif_family_summary(motifs_df: pd.DataFrame) -> pd.DataFrame:
    counts: Counter[str] = Counter()
    for atoms_json in motifs_df.get("atoms_json", []):
        for atom in json.loads(atoms_json):
            if atom.startswith(("constructor_family:", "basin:", "carrier:")):
                counts[atom] += 1
    return pd.DataFrame([{"family_atom": atom, "motif_count": count} for atom, count in counts.most_common()])


def _specificity(atom: str) -> float:
    if atom.startswith("constructor:"):
        return 2.0
    if atom.startswith("basin:"):
        return 1.0
    if atom.startswith("carrier:"):
        return 0.8
    if atom.startswith("constructor_family:"):
        return 0.6
    return 0.2
