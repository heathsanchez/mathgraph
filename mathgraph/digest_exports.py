"""Export helpers for persistent Mathlib digest Lawbooks."""

from __future__ import annotations

import json
from pathlib import Path

from mathgraph.constructor_atlas import export_constructor_atlas
from mathgraph.digest_scheduler import export_next_pack_config
from mathgraph.lawbook_accumulator import connect_lawbook, render_lawbook_summary_markdown, summarize_lawbook
from mathgraph.reason_atlas import export_reason_atlas


def export_lawbook_summary(lawbook: str | Path, out_dir: str | Path, *, html: bool = False) -> dict[str, str]:
    conn = connect_lawbook(lawbook)
    summary = summarize_lawbook(conn)
    conn.close()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": out / "lawbook_summary.json",
        "markdown": out / "lawbook_summary.md",
    }
    paths["json"].write_text(json.dumps(summary, indent=2, sort_keys=True, default=str), encoding="utf-8")
    paths["markdown"].write_text(render_lawbook_summary_markdown(summary), encoding="utf-8")
    if html:
        h = out / "lawbook_summary.html"
        h.write_text("<html><body><pre>" + paths["markdown"].read_text(encoding="utf-8") + "</pre></body></html>", encoding="utf-8")
        paths["html"] = h
    return {k: str(v) for k, v in paths.items()}


def export_all_digest_artifacts(lawbook: str | Path, out_dir: str | Path) -> dict[str, str]:
    paths = {}
    paths.update({f"constructor_{k}": v for k, v in export_constructor_atlas(lawbook, out_dir).items()})
    paths.update({f"reason_{k}": v for k, v in export_reason_atlas(lawbook, out_dir).items()})
    paths.update({f"summary_{k}": v for k, v in export_lawbook_summary(lawbook, out_dir).items()})
    paths.update({f"scheduler_{k}": v for k, v in export_next_pack_config(lawbook, out_dir).items()})
    return paths
