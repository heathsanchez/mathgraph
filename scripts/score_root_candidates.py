#!/usr/bin/env python
"""Score advisory root candidates without promoting terminal truth."""

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

from mathgraph.root_discovery import score_root_candidates


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="JSON or JSONL root candidates.")
    parser.add_argument("--signals", help="Optional JSON mapping root_node_id to signal dict.")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-jsonl", required=True)
    parser.add_argument("--out-md")
    args = parser.parse_args(argv)

    roots = _read_json_or_jsonl(args.input)
    signals = json.loads(Path(args.signals).read_text(encoding="utf-8")) if args.signals else None
    scores = score_root_candidates(roots, signals)
    rows = [score.to_dict() for score in scores]
    _write_json(args.out_json, {"scores": rows, "advisory_only": True})
    _write_jsonl(args.out_jsonl, rows)
    if args.out_md:
        _write_markdown(args.out_md, rows)
    return 0


def _read_json_or_jsonl(path: str) -> list[dict]:
    source = Path(path)
    text = source.read_text(encoding="utf-8")
    if source.suffix == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    data = json.loads(text)
    if isinstance(data, dict):
        for key in ("roots", "root_candidates", "scores"):
            if isinstance(data.get(key), list):
                return data[key]
    return data


def _write_json(path: str, payload) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_jsonl(path: str, rows: list[dict]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _write_markdown(path: str, rows: list[dict]) -> None:
    lines = [
        "# Root Candidate Scores",
        "",
        "Root scoring is advisory. Root nodes do not verify or refute claims.",
        "",
        "| root | recommendation | promotion | phase gate | shadow |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| `{row['root_node_id']}` | {row['recommendation']} | "
            f"{row['promotion_score']:.3f} | {row['phase_gate_score']:.3f} | {row['shadow_penalty']:.3f} |"
        )
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
