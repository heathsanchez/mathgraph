#!/usr/bin/env python
"""Smoke test persistent advisory Reason Atlas memory."""

from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path(__file__)

from mathgraph.reason_atlas_feedback_loop import ReasonAtlasFeedbackLoop  # noqa: E402
from mathgraph.reason_atlas_store import ReasonAtlasFeedbackEvent, ReasonAtlasFeedbackOutcome, ReasonAtlasQuery  # noqa: E402
from mathgraph.root_operator_schema import ParameterSpec, RootOperatorSchema  # noqa: E402


OUT_DIR = Path("/tmp/mathgraph_reason_atlas_persistence_smoke")


def _schemas():
    return [
        RootOperatorSchema.create(
            [{"name": "move", "kind": "spatial", "params": {"axis": "$axis", "distance": 2}}, {"name": "recolor", "kind": "color", "params": {"color": "$color"}}],
            [ParameterSpec("axis", "axis", ("x", "y")), ParameterSpec("color", "color", (1, 7))],
            support=3,
            family_count=2,
            latent_root_count=1,
            hidden_program_count=3,
            promoted=True,
            promotion_score=1.2,
            source_trace_ids=("t1", "t2", "t3"),
        )
    ]


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    db_path = OUT_DIR / "reason_atlas_store.sqlite"
    if db_path.exists():
        db_path.unlink()
    loop = ReasonAtlasFeedbackLoop(db_path)
    entries = loop.ingest_root_operator_schemas(_schemas())
    entries.extend(
        loop.ingest_contact_promotions(
            [
                {"law_id": "law_contact_1", "law_kind": "PROMOTED_ROUTE_LAW", "shape": "nat_contact", "repair_strategy": "exact_existing", "support": 3, "promotion_score": 0.8},
                {"seed_id": "seed_contact_1", "kind": "STRICT_CONTACT_SEED", "decl_name": "Nat.seed", "shape": "nat_seed", "repair_strategy": "simp"},
            ]
        )
    )
    target = entries[0].entry_id
    loop.record_transfer_result(target, True, residual_before=10, residual_after=6)
    loop.record_transfer_result(target, False)
    loop.record_verifier_result(target, True)
    loop.record_verifier_result(target, False)
    loop.record_obstruction(target, "type_mismatch")
    loop.store.add_feedback(ReasonAtlasFeedbackEvent.create(target, ReasonAtlasFeedbackOutcome.DELETION_HURT))
    loop.rescore()
    query = loop.store.query(ReasonAtlasQuery(atom="move"))
    entries_jsonl = OUT_DIR / "reason_atlas_entries.jsonl"
    queue_jsonl = OUT_DIR / "next_queue_rows.jsonl"
    loop.store.export_reason_atlas_jsonl(entries_jsonl)
    queue = loop.store.export_next_queue_rows(queue_jsonl)
    stats = loop.store.stats()
    top = loop.store.query(ReasonAtlasQuery(limit=1)).entries[0]
    summary = {
        "overall": "PASS" if stats.entry_count >= 3 and stats.feedback_count >= 5 and queue and stats.advisory_boundary_ok else "FAIL",
        "db_path": str(db_path),
        "entry_count": stats.entry_count,
        "feedback_count": stats.feedback_count,
        "active_count": stats.active_count,
        "top_entry_id": top.entry_id,
        "top_priority_score": top.priority_score,
        "next_queue_count": len(queue),
        "query_count": query.total_count,
        "exported_reason_atlas_jsonl": str(entries_jsonl),
        "exported_next_queue_jsonl": str(queue_jsonl),
        "advisory_boundary_ok": stats.advisory_boundary_ok,
    }
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    loop.close()
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["overall"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
