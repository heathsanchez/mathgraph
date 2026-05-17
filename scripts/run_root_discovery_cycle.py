#!/usr/bin/env python
"""Run the advisory root discovery consolidation pipeline."""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from _bootstrap import ensure_repo_root_on_path
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
else:
    ensure_repo_root_on_path(__file__)

import argparse
import json
from pathlib import Path

from mathgraph.persistent_filtration import build_filtration_evidence, summarize_persistence
from mathgraph.root_compiler import compile_constructor_plans
from mathgraph.root_promotion import promote_roots, promotion_summary
from mathgraph.root_shadow_collapse import collapse_root_shadows


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--telemetry-jsonl", required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--roots-json")
    group.add_argument("--roots-jsonl")
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args(argv)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = _read_jsonl(args.telemetry_jsonl)
    roots = _read_json_or_jsonl(args.roots_json, args.roots_jsonl)
    filtration = build_filtration_evidence(rows, roots)
    persistence = summarize_persistence(roots, filtration)
    shadow = collapse_root_shadows(roots)
    promotions = promote_roots(roots, persistence, shadow)
    plans = compile_constructor_plans(roots, promotions, rows=rows)
    summary = {
        "telemetry_rows": len(rows),
        "root_candidates": len(roots),
        "filtration_evidence": len(filtration),
        "persistence_summaries": len(persistence),
        "canonical_roots": len(shadow.canonical_roots),
        "shadow_links": len(shadow.shadow_links),
        "promotion_summary": promotion_summary(promotions),
        "constructor_plans": len(plans),
        "advisory_only": True,
        "verifier_boundary_unchanged": True,
    }
    _write_jsonl(out_dir / "filtration_evidence.jsonl", [item.to_dict() for item in filtration])
    _write_json(out_dir / "persistence_summary.json", {"persistence_summaries": [item.to_dict() for item in persistence]})
    _write_json(out_dir / "shadow_collapse.json", shadow.to_dict())
    _write_json(out_dir / "root_promotions.json", {"promotion_records": [item.to_dict() for item in promotions]})
    _write_json(out_dir / "constructor_plans.json", {"constructor_plans": [item.to_dict() for item in plans]})
    _write_json(out_dir / "root_discovery_cycle_summary.json", summary)
    _write_report(out_dir / "root_discovery_cycle_report.md", summary)
    print(json.dumps(summary, sort_keys=True))
    return 0


def _read_jsonl(path: str) -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def _read_json_or_jsonl(json_path: str | None, jsonl_path: str | None) -> list[dict]:
    if jsonl_path:
        return _read_jsonl(jsonl_path)
    data = json.loads(Path(str(json_path)).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        for key in ("roots", "root_candidates", "canonical_roots"):
            if isinstance(data.get(key), list):
                return data[key]
    return data


def _write_json(path: Path, payload) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _write_report(path: Path, summary: dict) -> None:
    lines = [
        "# Root Discovery Cycle Report",
        "",
        "This report is advisory only. It does not promote terminal truth.",
        "",
        f"- telemetry rows: {summary['telemetry_rows']}",
        f"- root candidates: {summary['root_candidates']}",
        f"- canonical roots after shadow collapse: {summary['canonical_roots']}",
        f"- shadow links: {summary['shadow_links']}",
        f"- constructor plans: {summary['constructor_plans']}",
        "",
        "Verifier/importer boundaries remain authoritative.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
