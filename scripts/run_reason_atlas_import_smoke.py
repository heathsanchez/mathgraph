#!/usr/bin/env python
"""Import probe rows into the signature/contact promotion atlas pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path(__file__)

from mathgraph.contact_promotion import ContactPromotionEngine  # noqa: E402
from mathgraph.reason_atlas_io import load_declarations_csv, load_probe_results_csv, write_csv  # noqa: E402
from mathgraph.signature_atlas import SignatureAtlas, parse_check_output  # noqa: E402


def _synthetic_rows() -> list[dict[str, str]]:
    return [
        {
            "probe_id": "s1",
            "level": "L2_STRICT_CONTACT",
            "shape": "nat_order",
            "theorem_decl": "Nat.alpha",
            "expected_type": "Nat.alpha (a : Nat) : a ≤ a",
            "repair_strategy": "exact_existing",
            "strict_success": "true",
            "marker_start": "true",
            "marker_ok": "true",
            "marker_end": "true",
        },
        {
            "probe_id": "s2",
            "level": "L2_STRICT_CONTACT",
            "shape": "nat_order",
            "theorem_decl": "Nat.beta",
            "expected_type": "Nat.beta (a : Nat) : a ≤ a",
            "repair_strategy": "exact_existing",
            "strict_success": "true",
            "marker_start": "true",
            "marker_ok": "true",
            "marker_end": "true",
        },
        {
            "probe_id": "s3",
            "level": "L2_STRICT_CONTACT",
            "shape": "nat_order",
            "theorem_decl": "Nat.gamma",
            "expected_type": "Nat.gamma (a : Nat) : a ≤ a",
            "repair_strategy": "exact_existing",
            "strict_success": "true",
            "marker_start": "true",
            "marker_ok": "true",
            "marker_end": "true",
        },
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe-results")
    parser.add_argument("--declarations")
    parser.add_argument("--out-dir", default="/tmp/mathgraph_reason_atlas_import_smoke")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    probe_rows = load_probe_results_csv(args.probe_results) if args.probe_results else _synthetic_rows()
    declaration_rows = load_declarations_csv(args.declarations) if args.declarations else []
    engine = ContactPromotionEngine()
    engine.ingest_probe_rows(probe_rows)
    engine.promote()
    atlas = SignatureAtlas()
    for row in declaration_rows or probe_rows:
        decl = str(row.get("decl_name") or row.get("theorem_decl") or row.get("target_decl") or "")
        raw = str(row.get("raw_check_output") or row.get("normalized_signature") or row.get("expected_type") or "")
        if decl or raw:
            atlas.add(parse_check_output(raw, decl, shape=str(row.get("shape", "")), source="reason_atlas_import_smoke"))
    write_csv(out_dir / "contact_seeds.csv", engine.to_contact_seed_rows())
    write_csv(out_dir / "contact_obstructions.csv", engine.to_obstruction_rows())
    write_csv(out_dir / "promoted_route_laws.csv", engine.to_route_law_rows())
    write_csv(out_dir / "next_queue.csv", engine.to_next_queue_rows())
    write_csv(out_dir / "signature_atlas.csv", atlas.to_rows())
    summary = engine.summary()
    summary.update({"signature_count": len(atlas.records), "probe_row_count": len(probe_rows), "out_dir": str(out_dir)})
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
