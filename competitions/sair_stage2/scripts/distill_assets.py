#!/usr/bin/env python
"""Offline asset distiller for the SAIR Stage 2 compact solver."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--equations-path")
    parser.add_argument("--matrix-path")
    parser.add_argument("--true-proofs-csv", action="append", default=[])
    parser.add_argument("--false-certs-jsonl", action="append", default=[])
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args(argv)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if not args.equations_path or not args.matrix_path or not Path(args.equations_path).exists() or not Path(args.matrix_path).exists():
        report = {"status": "skipped", "reason": "ETP equations or matrix file not found", "generated_assets": False}
        _write(out_dir, report, "EXACT_TRUE = {}\nEXACT_FALSE = {}\nTABLE_BANK = []\nRULE_FAMILIES = []\n")
        print(json.dumps(report, sort_keys=True))
        return 0
    report = {"status": "completed_metadata_only", "reason": "Full high-yield distillation is future; emitted safe empty assets.", "generated_assets": True}
    _write(out_dir, report, "EXACT_TRUE = {}\nEXACT_FALSE = {}\nTABLE_BANK = []\nRULE_FAMILIES = []\n")
    print(json.dumps(report, sort_keys=True))
    return 0


def _write(out_dir, report, assets_text):
    (out_dir / "distilled_assets_report.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    (out_dir / "distilled_assets_report.md").write_text("# Distilled Assets Report\n\n```json\n%s\n```\n" % json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    (out_dir / "generated_solver_assets.py").write_text(assets_text, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())

