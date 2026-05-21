"""Persistent Reason Atlas admission for clean SAIR motifs."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from mathgraph.hashing import content_id
from mathgraph.reason_atlas_store import (
    ReasonAtlasEntry,
    ReasonAtlasEntryKind,
    ReasonAtlasFeedbackEvent,
    ReasonAtlasFeedbackOutcome,
    ReasonAtlasQuery,
    ReasonAtlasStore,
    ReasonAtlasStoreConfig,
    ReasonAtlasTrust,
)


@dataclass(frozen=True)
class SAIRReasonAtlasAdmissionConfig:
    db_path: str | Path
    min_support: int = 2
    min_score: float = 1.0


@dataclass(frozen=True)
class SAIRReasonAtlasAdmissionReport:
    attempted_motifs: int
    admitted_entries: int
    duplicate_entries: int
    superseded_entries: int
    rejected_low_quality: int
    rejected_boundary_violation: int
    loaded_reason_atlas_entries: int = 0
    advisory_boundary_ok: bool = True
    feedback_events: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


def clean_motif_to_reason_atlas_entry(row: dict[str, Any], *, scheduler_gain: float = 0.0) -> ReasonAtlasEntry:
    atoms = json.loads(row["atoms_json"]) if isinstance(row.get("atoms_json"), str) else list(row.get("atoms", []))
    motif_id = str(row.get("motif_id") or content_id("sair-clean-motif", atoms))
    constructors = [a.split(":", 1)[1] for a in atoms if a.startswith("constructor:")]
    basins = [a.split(":", 1)[1] for a in atoms if a.startswith("basin:")]
    carriers = [a.split(":", 1)[1] for a in atoms if a.startswith("carrier:")]
    return ReasonAtlasEntry(
        entry_id=motif_id,
        kind=ReasonAtlasEntryKind.CONSTRUCTOR_HINT,
        name="sair_clean_motif:" + "|".join(atoms[:4]),
        atoms=list(atoms),
        pattern=" & ".join(atoms),
        payload={
            **dict(row),
            "scheduler_gain": scheduler_gain,
            "constructor_family": _first_atom_value(atoms, "constructor_family:"),
            "basin_family": basins[0] if basins else "",
            "carrier_family": carriers[0] if carriers else "",
        },
        source_trace_ids=list(_safe_json(row.get("source_trace_ids_json"), [])),
        evidence_kind="ADVISORY_SAIR_CLEAN_MOTIF_FROM_PROMOTIONGATE_ACCEPTED_TRACES",
        advisory_only=True,
        verifier_promoted=False,
        trust=ReasonAtlasTrust.CANDIDATE,
        support=int(row.get("support", 0) or 0),
        family_count=1 if basins else 0,
        root_count=len(constructors),
        promotion_score=float(row.get("score", 0.0) or 0.0),
        priority_score=float(row.get("score", 0.0) or 0.0) + float(scheduler_gain),
        metadata={
            "provenance": "promotiongate_accepted_finite_countermodel_traces",
            "terminal_form": "ADVISORY_ONLY",
            "clean_atoms": list(atoms),
        },
    )


def clean_root_schema_to_reason_atlas_entry(row: dict[str, Any], *, source_entry_ids: list[str] | None = None) -> ReasonAtlasEntry:
    entry = clean_motif_to_reason_atlas_entry(row)
    return ReasonAtlasEntry.from_dict({**entry.to_dict(), "kind": ReasonAtlasEntryKind.ROOT_OPERATOR_SCHEMA.value, "source_entry_ids": source_entry_ids or []})


def admit_clean_motifs_to_reason_atlas(motifs_df: pd.DataFrame, config: SAIRReasonAtlasAdmissionConfig, *, scheduler_gain: float = 0.0) -> SAIRReasonAtlasAdmissionReport:
    store = ReasonAtlasStore(ReasonAtlasStoreConfig(config.db_path))
    store.initialize()
    admitted = duplicate = superseded = rejected_low = rejected_boundary = feedback = 0
    try:
        for row in motifs_df.to_dict("records"):
            if not bool(row.get("advisory_only", True)) or row.get("terminal_form") in {"TRUE", "FALSE", "VERIFIED_PROOF", "REFUTATION_CERTIFICATE"}:
                rejected_boundary += 1
                continue
            if int(row.get("support", 0) or 0) < config.min_support or float(row.get("score", 0.0) or 0.0) < config.min_score:
                rejected_low += 1
                continue
            entry = clean_motif_to_reason_atlas_entry(row, scheduler_gain=scheduler_gain)
            existing = store.get_entry(entry.entry_id)
            if existing:
                if entry.support > existing.support:
                    store.upsert_entry(entry)
                    store.add_feedback(ReasonAtlasFeedbackEvent.create(entry.entry_id, ReasonAtlasFeedbackOutcome.SUPERSEDED, metadata={"sair_admission_event": "superseded"}))
                    superseded += 1
                    feedback += 1
                else:
                    store.add_feedback(ReasonAtlasFeedbackEvent.create(entry.entry_id, ReasonAtlasFeedbackOutcome.DUPLICATE, metadata={"sair_admission_event": "duplicate"}))
                    duplicate += 1
                    feedback += 1
            else:
                store.upsert_entry(entry)
                store.add_feedback(ReasonAtlasFeedbackEvent.create(entry.entry_id, ReasonAtlasFeedbackOutcome.TRANSFER_SUCCESS, metadata={"sair_admission_event": "admitted"}))
                admitted += 1
                feedback += 1
            if scheduler_gain > 0:
                store.add_feedback(ReasonAtlasFeedbackEvent.create(entry.entry_id, ReasonAtlasFeedbackOutcome.RESIDUAL_COMPRESSED, residual_delta=scheduler_gain, metadata={"sair_admission_event": "scheduler_gain_observed"}))
                feedback += 1
        stats = store.stats()
        return SAIRReasonAtlasAdmissionReport(len(motifs_df), admitted, duplicate, superseded, rejected_low, rejected_boundary, stats.entry_count, stats.advisory_boundary_ok, feedback)
    finally:
        store.close()


def admit_clean_schemas_to_reason_atlas(schemas_df: pd.DataFrame, config: SAIRReasonAtlasAdmissionConfig) -> SAIRReasonAtlasAdmissionReport:
    rows = []
    for row in schemas_df.to_dict("records"):
        entry = clean_root_schema_to_reason_atlas_entry(row)
        rows.append({**row, "motif_id": entry.entry_id, "atoms_json": json.dumps(entry.atoms), "support": entry.support, "score": entry.priority_score, "advisory_only": True})
    return admit_clean_motifs_to_reason_atlas(pd.DataFrame(rows), config)


def load_sair_reason_atlas_priors(db_path: str | Path) -> pd.DataFrame:
    store = ReasonAtlasStore(ReasonAtlasStoreConfig(db_path))
    store.initialize()
    try:
        entries = store.query(ReasonAtlasQuery(kind=ReasonAtlasEntryKind.CONSTRUCTOR_HINT, limit=1_000_000)).entries
        rows = []
        for entry in entries:
            if not entry.advisory_only:
                continue
            rows.append(
                {
                    "motif_id": entry.entry_id,
                    "atoms_json": json.dumps(entry.atoms, sort_keys=True),
                    "support": entry.support,
                    "score": entry.priority_score,
                    "advisory_only": True,
                    "source": "persistent_reason_atlas",
                }
            )
        return pd.DataFrame(rows)
    finally:
        store.close()


def export_sair_reason_atlas_admission_report(report: SAIRReasonAtlasAdmissionReport, out_dir: str | Path, db_path: str | Path | None = None) -> dict[str, str]:
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    report_path = output / "reason_atlas_admission_report.json"
    report_path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    paths = {"reason_atlas_admission_report": str(report_path)}
    if db_path:
        entries = output / "admitted_reason_atlas_entries.jsonl"
        store = ReasonAtlasStore(ReasonAtlasStoreConfig(db_path))
        store.initialize()
        try:
            store.export_reason_atlas_jsonl(entries)
            paths["admitted_reason_atlas_entries"] = str(entries)
        finally:
            store.close()
    return paths


def _safe_json(value: Any, default: Any) -> Any:
    try:
        if value is None:
            return default
        return json.loads(value) if isinstance(value, str) else value
    except Exception:
        return default


def _first_atom_value(atoms: list[str], prefix: str) -> str:
    for atom in atoms:
        if atom.startswith(prefix):
            return atom.split(":", 1)[1]
    return ""
