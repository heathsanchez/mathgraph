"""Orchestration loop for persistent advisory Reason Atlas feedback."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from mathgraph.reason_atlas_adapters import entry_from_contact_promotion, entry_from_root_operator_schema
from mathgraph.reason_atlas_store import (
    ReasonAtlasEntry,
    ReasonAtlasFeedbackEvent,
    ReasonAtlasFeedbackOutcome,
    ReasonAtlasQuery,
    ReasonAtlasStore,
    ReasonAtlasStoreConfig,
)
from mathgraph.schema_feedback import residual_compression_delta


@dataclass(frozen=True)
class ReasonAtlasFeedbackLoopConfig:
    db_path: str | Path


class ReasonAtlasFeedbackLoop:
    def __init__(self, config: ReasonAtlasFeedbackLoopConfig | str | Path) -> None:
        cfg = config if isinstance(config, ReasonAtlasFeedbackLoopConfig) else ReasonAtlasFeedbackLoopConfig(config)
        self.store = ReasonAtlasStore(ReasonAtlasStoreConfig(cfg.db_path))
        self.store.initialize()

    def ingest_entries(self, entries: Sequence[ReasonAtlasEntry | dict[str, Any]]) -> list[ReasonAtlasEntry]:
        out = []
        for entry in entries:
            out.append(self.store.upsert_entry(entry if isinstance(entry, ReasonAtlasEntry) else ReasonAtlasEntry.from_dict(entry)))
        return out

    def ingest_root_operator_schemas(self, schemas: Sequence[Any]) -> list[ReasonAtlasEntry]:
        return [self.store.upsert_entry(entry_from_root_operator_schema(schema)) for schema in schemas]

    def ingest_contact_promotions(self, promotions: Sequence[Any]) -> list[ReasonAtlasEntry]:
        return [self.store.upsert_entry(entry_from_contact_promotion(item)) for item in promotions]

    def record_transfer_result(self, entry_id: str, success: bool, residual_before: int | None = None, residual_after: int | None = None, metadata: dict[str, Any] | None = None) -> ReasonAtlasFeedbackEvent:
        outcome = ReasonAtlasFeedbackOutcome.TRANSFER_SUCCESS if success else ReasonAtlasFeedbackOutcome.TRANSFER_FAILURE
        event = self.store.add_feedback(ReasonAtlasFeedbackEvent.create(entry_id, outcome, metadata=dict(metadata or {})))
        if residual_before is not None and residual_after is not None:
            delta = residual_compression_delta(residual_before, residual_after)
            if delta > 0:
                self.store.add_feedback(ReasonAtlasFeedbackEvent.create(entry_id, ReasonAtlasFeedbackOutcome.RESIDUAL_COMPRESSED, residual_delta=delta, metadata=dict(metadata or {})))
        return event

    def record_verifier_result(self, entry_id: str, success: bool, metadata: dict[str, Any] | None = None) -> ReasonAtlasFeedbackEvent:
        outcome = ReasonAtlasFeedbackOutcome.VERIFIER_SUCCESS if success else ReasonAtlasFeedbackOutcome.VERIFIER_FAILURE
        return self.store.add_feedback(ReasonAtlasFeedbackEvent.create(entry_id, outcome, metadata=dict(metadata or {})))

    def record_obstruction(self, entry_id: str, obstruction_name: str, metadata: dict[str, Any] | None = None) -> ReasonAtlasFeedbackEvent:
        return self.store.add_feedback(ReasonAtlasFeedbackEvent.create(entry_id, ReasonAtlasFeedbackOutcome.OBSTRUCTION_FOUND, metadata={"obstruction_name": obstruction_name, **dict(metadata or {})}))

    def rescore(self) -> None:
        self.store.recompute_all_scores()

    def next_advisory_tasks(self, limit: int = 100) -> list[dict[str, Any]]:
        tmp = Path("/tmp/mathgraph_reason_atlas_next_queue_tmp.jsonl")
        return self.store.export_next_queue_rows(tmp, limit=limit)

    def export_all(self, out_dir: str | Path) -> dict[str, str]:
        output = Path(out_dir)
        output.mkdir(parents=True, exist_ok=True)
        entries = output / "reason_atlas_entries.jsonl"
        queue = output / "next_queue_rows.jsonl"
        summary = output / "summary.json"
        self.store.export_reason_atlas_jsonl(entries)
        rows = self.store.export_next_queue_rows(queue)
        stats = self.store.stats().to_dict()
        stats["next_queue_count"] = len(rows)
        summary.write_text(json.dumps(stats, indent=2, sort_keys=True), encoding="utf-8")
        return {"entries": str(entries), "next_queue": str(queue), "summary": str(summary)}

    def close(self) -> None:
        self.store.close()
