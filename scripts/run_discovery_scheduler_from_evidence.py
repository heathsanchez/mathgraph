#!/usr/bin/env python3
"""Generate DiscoveryScheduler candidates from canonical evidence sources."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mathgraph.discovery_candidate_sources import (  # noqa: E402
    collect_discovery_candidates_from_sources,
    split_valid_candidates,
)
from mathgraph.discovery_scheduler import (  # noqa: E402
    allocate_attention,
    build_trust_boundary_audit,
    make_policy,
)


OUTPUT_FILES = (
    "evidence_candidate_inventory.csv",
    "valid_candidates.csv",
    "rejected_candidates.csv",
    "taste_policy_ledger.csv",
    "attention_allocation.csv",
    "discovery_from_evidence_summary.json",
    "discovery_from_evidence_report.md",
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-root", default="examples/evidence_packs")
    parser.add_argument("--lean-digest-dir")
    parser.add_argument("--lean-lawbook-dir")
    parser.add_argument("--lean-attention-dir")
    parser.add_argument("--mode", choices=("harvest", "frontier", "architectonic", "balanced"), default="balanced")
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--beta", type=float, default=1.0)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args(argv)

    result = run_from_evidence(
        evidence_root=Path(args.evidence_root),
        out_dir=Path(args.out_dir),
        lean_digest_dir=Path(args.lean_digest_dir) if args.lean_digest_dir else None,
        lean_lawbook_dir=Path(args.lean_lawbook_dir) if args.lean_lawbook_dir else None,
        lean_attention_dir=Path(args.lean_attention_dir) if args.lean_attention_dir else None,
        mode=args.mode,
        top_k=args.top_k,
        beta=args.beta,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def run_from_evidence(
    *,
    evidence_root: Path,
    out_dir: Path,
    lean_digest_dir: Path | None = None,
    lean_lawbook_dir: Path | None = None,
    lean_attention_dir: Path | None = None,
    mode: str = "balanced",
    top_k: int = 8,
    beta: float = 1.0,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    collected = collect_discovery_candidates_from_sources(
        evidence_root=evidence_root,
        lean_digest_dir=lean_digest_dir,
        lean_lawbook_dir=lean_lawbook_dir,
        lean_attention_dir=lean_attention_dir,
    )
    valid, invalid_from_candidates = split_valid_candidates(collected.candidates)
    rejected_rows = list(collected.rejected_rows) + invalid_from_candidates
    policy = make_policy(mode=mode, beta=beta)
    ranked, selected, allocation_invalid = allocate_attention(valid, policy, top_k=top_k)
    rejected_rows.extend(allocation_invalid)
    audit = build_trust_boundary_audit(valid, rejected_rows)
    source_counts = _source_counts(collected.candidates)
    outputs = {name: str(out_dir / name) for name in OUTPUT_FILES}
    summary = {
        "run_id": f"discovery_from_evidence_{mode}",
        "mode": mode,
        "beta": beta,
        "candidate_count": len(collected.candidates),
        "valid_count": len(valid),
        "rejected_count": len(rejected_rows),
        "chosen_count": len(selected),
        "source_counts": source_counts,
        "warnings": list(collected.warnings),
        "advisory_boundary_ok": audit["advisory_boundary_ok"],
        "can_promote_truth_count": audit["can_promote_truth_count"],
        "invalid_descension_count": audit["invalid_descension_count"],
        "top_candidate_id": ranked[0].candidate_id if ranked else "",
        "top_candidate_descension_target": ranked[0].descension_target if ranked else "",
        "total_attention_probability": sum(candidate.attention_probability for candidate in ranked),
        "outputs": outputs,
    }
    _write_csv(out_dir / "evidence_candidate_inventory.csv", [candidate.to_dict() for candidate in collected.candidates])
    _write_csv(out_dir / "valid_candidates.csv", [candidate.to_dict() for candidate in valid])
    _write_csv(out_dir / "rejected_candidates.csv", rejected_rows)
    _write_csv(out_dir / "taste_policy_ledger.csv", [_policy_row(policy)])
    _write_csv(out_dir / "attention_allocation.csv", [candidate.to_dict() for candidate in ranked])
    (out_dir / "discovery_from_evidence_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    (out_dir / "discovery_from_evidence_report.md").write_text(_report(summary, ranked, selected, rejected_rows), encoding="utf-8")
    return summary


def _source_counts(candidates: Sequence[Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for candidate in candidates:
        key = str(getattr(candidate, "source_kind", "") or getattr(candidate, "source", ""))
        counts[key] = counts.get(key, 0) + 1
    return counts


def _policy_row(policy: Any) -> dict[str, Any]:
    row = policy.to_dict()
    row["weights_json"] = json.dumps(row.pop("weights"), sort_keys=True)
    return row


def _report(summary: Mapping[str, Any], ranked: Sequence[Any], selected: Sequence[Any], rejected_rows: Sequence[Mapping[str, Any]]) -> str:
    lines = [
        "# DiscoveryScheduler v1: Evidence-Derived Candidates",
        "",
        "This run converts canonical evidence packs and optional Lean digest outputs into advisory, testable continuation candidates.",
        "It does not prove theorems, synthesize proofs, run H-tilt, or promote truth.",
        "",
        f"- mode: `{summary.get('mode')}`",
        f"- candidate_count: `{summary.get('candidate_count')}`",
        f"- valid_count: `{summary.get('valid_count')}`",
        f"- rejected_count: `{summary.get('rejected_count')}`",
        f"- chosen_count: `{summary.get('chosen_count')}`",
        f"- advisory_boundary_ok: `{summary.get('advisory_boundary_ok')}`",
        "",
        "## Source Counts",
    ]
    for source, count in sorted(dict(summary.get("source_counts", {})).items()):
        lines.append(f"- `{source}`: `{count}`")
    lines.extend(["", "## Top Candidates"])
    for candidate in ranked[:10]:
        lines.append(
            f"- `{candidate.candidate_id}` score `{candidate.taste_score:.3f}` "
            f"p `{candidate.attention_probability:.3f}` target `{candidate.descension_target}` "
            f"source `{candidate.source_ref or candidate.source}`"
        )
    if not ranked:
        lines.append("- none")
    lines.extend(["", "## Top Candidates By Mode Hint"])
    by_mode: dict[str, list[Any]] = {}
    for candidate in ranked:
        by_mode.setdefault(candidate.mode_hint or "unspecified", []).append(candidate)
    for mode, rows in sorted(by_mode.items()):
        top = rows[0]
        lines.append(f"- `{mode}`: `{top.candidate_id}` -> `{top.descension_target}`")
    lines.extend(["", "## Rejected / Audit Rows"])
    for row in rejected_rows[:20]:
        lines.append(f"- `{row.get('candidate_id') or row.get('source_ref')}`: `{row.get('violations')}`")
    if not rejected_rows:
        lines.append("- none")
    lines.extend(["", "## Trust Boundary", ""])
    lines.append("Every allocated candidate is advisory_only=true and can_promote_truth=false.")
    lines.append("CrossWorld candidates remain empirical invariant candidates, Collatz candidates remain not_a_proof, and textual Lean candidates cannot become VERIFIED_PROOF.")
    lines.append("Rejected candidates are retained for audit and receive no attention allocation.")
    lines.extend(["", "## Next Test Actions"])
    for candidate in selected:
        lines.append(f"- `{candidate.candidate_id}` would test `{candidate.descension_target}` via `{candidate.suggested_route}`")
    if not selected:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    keys: list[str] = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _csv_value(row.get(key)) for key in keys})


def _csv_value(value: Any) -> Any:
    if isinstance(value, (dict, list, tuple, set)):
        return json.dumps(value, sort_keys=True)
    return value


if __name__ == "__main__":
    raise SystemExit(main())
