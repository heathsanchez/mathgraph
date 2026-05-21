#!/usr/bin/env python
"""Run a synthetic Reason Atlas contact-promotion smoke test."""

from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path(__file__)

from mathgraph.contact_promotion import ContactPromotionEngine  # noqa: E402
from mathgraph.reason_atlas_io import write_csv  # noqa: E402
from mathgraph.signature_atlas import SignatureAtlas, parse_check_output  # noqa: E402


OUT_DIR = Path("/tmp/mathgraph_contact_promotion_smoke")


def synthetic_probe_rows() -> list[dict[str, str]]:
    clean = []
    for idx, decl in enumerate(["Nat.foo_assoc", "Nat.bar_assoc", "Nat.baz_assoc"], start=1):
        clean.append(
            {
                "probe_id": f"clean_{idx}",
                "level": "L2_STRICT_CONTACT",
                "shape": "nat_binary_relation",
                "theorem_decl": decl,
                "expected_type": f"{decl} (a b : Nat) : a = b",
                "repair_strategy": "exact_existing",
                "strict_success": "true",
                "marker_start": "true",
                "marker_ok": "true",
                "marker_end": "true",
            }
        )
    return clean + [
        {
            "probe_id": "single_clean",
            "level": "L2_STRICT_CONTACT",
            "shape": "nat_singleton_shape",
            "theorem_decl": "Nat.single_seed",
            "expected_type": "Nat.single_seed (a : Nat) : a = a",
            "repair_strategy": "simp",
            "strict_success": "true",
            "marker_start": "true",
            "marker_ok": "true",
            "marker_end": "true",
        },
        {
            "probe_id": "visibility",
            "level": "L1_VISIBILITY_CONTACT",
            "shape": "nat_visibility_shape",
            "theorem_decl": "Nat.visible_only",
            "expected_type": "Nat.visible_only : True",
            "repair_strategy": "visibility_check",
            "strict_success": "true",
            "marker_start": "true",
            "marker_ok": "true",
            "marker_end": "true",
        },
        {
            "probe_id": "dirty_1",
            "level": "L2_STRICT_CONTACT",
            "shape": "nat_dirty_relation",
            "theorem_decl": "Nat.dirty_one",
            "repair_strategy": "repair_exact_existing",
            "strict_success": "false",
            "dirty_interval": "true",
            "failure_class": "type_mismatch",
            "failure_detail": "type mismatch",
        },
        {
            "probe_id": "dirty_2",
            "level": "L2_STRICT_CONTACT",
            "shape": "nat_parse_shape",
            "theorem_decl": "Nat.dirty_two",
            "repair_strategy": "simp",
            "strict_success": "false",
            "failure_class": "unknown_constant_or_identifier",
            "failure_detail": "unknown identifier",
        },
    ]


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = synthetic_probe_rows()
    engine = ContactPromotionEngine()
    engine.ingest_probe_rows(rows)
    engine.promote()
    atlas = SignatureAtlas()
    for row in rows:
        decl = row.get("theorem_decl", "")
        atlas.add(parse_check_output(row.get("expected_type", ""), decl, shape=row.get("shape", ""), source="synthetic_smoke"))
    write_csv(OUT_DIR / "contact_seeds.csv", engine.to_contact_seed_rows())
    write_csv(OUT_DIR / "contact_obstructions.csv", engine.to_obstruction_rows())
    write_csv(OUT_DIR / "promoted_route_laws.csv", engine.to_route_law_rows())
    write_csv(OUT_DIR / "next_queue.csv", engine.to_next_queue_rows())
    write_csv(OUT_DIR / "signature_atlas.csv", atlas.to_rows())
    summary = engine.summary()
    summary["signature_count"] = len(atlas.records)
    summary["out_dir"] = str(OUT_DIR)
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
