"""Advisory replay over continuation traces."""

from __future__ import annotations

import json
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from mathgraph.continuation_traces import ContinuationTrace, ContinuationTraceStore

REPLAY_WARNINGS = [
    "Replay is advisory.",
    "Route strength is scheduling pressure, not truth.",
    "A failed trace is not proof.",
    "A near miss is not a certificate.",
    "Terminal truth still requires verified proof/refutation/importer revalidation.",
]


@dataclass(frozen=True)
class RouteReplaySignal:
    route_key: str
    root_label: str | None
    constructor_family: str | None
    attempts: int
    verified: int
    promoted: int
    failures: int
    residuals: int
    near_misses: int
    certificate_yield: float
    near_miss_rate: float
    residual_rate: float
    mean_near_miss_score: float
    mean_residual_compression_delta: float
    route_strength_delta: float
    recommendation: str
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReplayReport:
    run_id: str
    trace_count: int
    route_signals: list[RouteReplaySignal]
    root_summary: dict[str, Any]
    constructor_summary: dict[str, Any]
    obstruction_pressure: list[dict[str, Any]]
    warnings: list[str]
    outputs: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "trace_count": self.trace_count,
            "route_signals": [signal.to_dict() for signal in self.route_signals],
            "root_summary": dict(self.root_summary),
            "constructor_summary": dict(self.constructor_summary),
            "obstruction_pressure": list(self.obstruction_pressure),
            "warnings": list(self.warnings),
            "outputs": dict(self.outputs),
            "advisory_only": True,
        }


def replay_continuation_traces(trace_store_path: str, out_dir: str | None = None) -> ReplayReport:
    run_id = f"replay_{int(time.time() * 1000)}"
    traces = ContinuationTraceStore(trace_store_path).load_all()
    route_signals = _route_signals(traces)
    obstruction_pressure = _obstruction_pressure(traces)
    root_summary = dict(sorted(Counter(trace.root_label or "none" for trace in traces).items()))
    constructor_summary = dict(sorted(Counter(trace.constructor_family or "none" for trace in traces).items()))
    outputs: dict[str, str] = {}
    report = ReplayReport(
        run_id=run_id,
        trace_count=len(traces),
        route_signals=route_signals,
        root_summary=root_summary,
        constructor_summary=constructor_summary,
        obstruction_pressure=obstruction_pressure,
        warnings=list(REPLAY_WARNINGS),
        outputs=outputs,
    )
    if out_dir:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        outputs.update(
            {
                "replay_report_json": str(out / "replay_report.json"),
                "replay_report_md": str(out / "replay_report.md"),
                "route_signals_jsonl": str(out / "route_signals.jsonl"),
                "obstruction_pressure_jsonl": str(out / "obstruction_pressure.jsonl"),
            }
        )
        report = ReplayReport(
            run_id=report.run_id,
            trace_count=report.trace_count,
            route_signals=report.route_signals,
            root_summary=report.root_summary,
            constructor_summary=report.constructor_summary,
            obstruction_pressure=report.obstruction_pressure,
            warnings=report.warnings,
            outputs=outputs,
        )
        _write_json(report.to_dict(), out / "replay_report.json")
        _write_jsonl([signal.to_dict() for signal in route_signals], out / "route_signals.jsonl")
        _write_jsonl(obstruction_pressure, out / "obstruction_pressure.jsonl")
        _write_markdown(report, out / "replay_report.md")
    return report


def _route_signals(traces: list[ContinuationTrace]) -> list[RouteReplaySignal]:
    groups: dict[str, list[ContinuationTrace]] = defaultdict(list)
    for trace in traces:
        groups[_route_key(trace)].append(trace)
    signals: list[RouteReplaySignal] = []
    for key in sorted(groups):
        rows = groups[key]
        attempts = len(rows)
        verified = sum(1 for trace in rows if trace.verified)
        promoted = sum(1 for trace in rows if trace.promoted)
        failures = sum(1 for trace in rows if trace.status in {"constructor_failed", "parse_failed", "verification_failed", "error"})
        residuals = sum(1 for trace in rows if trace.status == "residual")
        near_misses = sum(1 for trace in rows if trace.status == "near_miss" or trace.near_miss_score >= 0.5)
        certificate_yield = verified / max(attempts, 1)
        near_miss_rate = near_misses / max(attempts, 1)
        residual_rate = residuals / max(attempts, 1)
        failure_rate = failures / max(attempts, 1)
        mean_near = sum(trace.near_miss_score for trace in rows) / max(attempts, 1)
        mean_compression = sum(trace.residual_compression_delta for trace in rows) / max(attempts, 1)
        strength = (
            2.0 * certificate_yield
            + 0.7 * near_miss_rate
            + 0.5 * mean_compression
            - 0.8 * residual_rate
            - 0.5 * failure_rate
        )
        recommendation = _recommend_route(
            attempts=attempts,
            verified=verified,
            promoted=promoted,
            failures=failures,
            residuals=residuals,
            near_misses=near_misses,
            mean_near=mean_near,
        )
        first = rows[0]
        signals.append(
            RouteReplaySignal(
                route_key=key,
                root_label=first.root_label,
                constructor_family=first.constructor_family,
                attempts=attempts,
                verified=verified,
                promoted=promoted,
                failures=failures,
                residuals=residuals,
                near_misses=near_misses,
                certificate_yield=round(certificate_yield, 6),
                near_miss_rate=round(near_miss_rate, 6),
                residual_rate=round(residual_rate, 6),
                mean_near_miss_score=round(mean_near, 6),
                mean_residual_compression_delta=round(mean_compression, 6),
                route_strength_delta=round(strength, 6),
                recommendation=recommendation,
                evidence={
                    "advisory_only": True,
                    "trace_ids": [trace.trace_id for trace in rows],
                    "warnings": list(REPLAY_WARNINGS),
                },
            )
        )
    return sorted(signals, key=lambda item: (-item.route_strength_delta, item.route_key))


def _obstruction_pressure(traces: list[ContinuationTrace]) -> list[dict[str, Any]]:
    groups: dict[tuple[str | None, str | None], list[ContinuationTrace]] = defaultdict(list)
    for trace in traces:
        if trace.status in {"constructor_failed", "residual", "verification_failed", "near_miss"}:
            groups[(trace.root_label, trace.constructor_family)].append(trace)
    rows: list[dict[str, Any]] = []
    for (root_label, constructor), group in sorted(groups.items(), key=lambda item: str(item[0])):
        if len(group) < 2:
            continue
        label = f"obstruction_pressure_{root_label or 'none'}_{constructor or 'none'}"
        rows.append(
            {
                "obstruction_label": label,
                "root_label": root_label,
                "constructor_family": constructor,
                "count": len(group),
                "mean_near_miss_score": round(sum(trace.near_miss_score for trace in group) / len(group), 6),
                "advisory_only": True,
                "evidence": {
                    "trace_ids": [trace.trace_id for trace in group],
                    "statuses": dict(sorted(Counter(trace.status for trace in group).items())),
                },
            }
        )
    return rows


def _recommend_route(
    *,
    attempts: int,
    verified: int,
    promoted: int,
    failures: int,
    residuals: int,
    near_misses: int,
    mean_near: float,
) -> str:
    if attempts < 2:
        return "insufficient_data"
    if verified > 0 or promoted > 0:
        return "strengthen_route"
    if failures + residuals >= 2 and near_misses > 0:
        return "convert_to_obstruction_pressure"
    if near_misses > 0 and mean_near >= 0.6:
        return "preserve_for_replay"
    if failures + residuals >= 2:
        return "weaken_route"
    return "insufficient_data"


def _route_key(trace: ContinuationTrace) -> str:
    return "|".join(
        [
            trace.root_label or "none",
            trace.constructor_family or "none",
            trace.route_type or "unknown_route",
        ]
    )


def _write_json(payload: dict[str, Any], path: Path) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_jsonl(rows: list[dict[str, Any]], path: Path) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _write_markdown(report: ReplayReport, path: Path) -> None:
    lines = [
        "# Continuation Replay Report",
        "",
        "## Summary",
        "",
        "| metric | value |",
        "| --- | ---: |",
        f"| trace_count | {report.trace_count} |",
        f"| route_signal_count | {len(report.route_signals)} |",
        f"| obstruction_pressure_count | {len(report.obstruction_pressure)} |",
        "",
        "## Route Signals",
        "",
        "| route_key | attempts | verified | near_misses | residuals | strength_delta | recommendation |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for signal in report.route_signals:
        lines.append(
            f"| `{signal.route_key}` | {signal.attempts} | {signal.verified} | {signal.near_misses} | "
            f"{signal.residuals} | {signal.route_strength_delta:.3f} | {signal.recommendation} |"
        )
    lines.extend(["", "## Obstruction Pressure", ""])
    if report.obstruction_pressure:
        for row in report.obstruction_pressure:
            lines.append(f"- `{row['obstruction_label']}`: {row['count']} traces")
    else:
        lines.append("No repeated structured failure pressure found.")
    lines.extend(
        [
            "",
            "## Trust Boundary",
            "",
            "- Replay is advisory.",
            "- Route strength is scheduling pressure.",
            "- Failed trace is not proof.",
            "- Near miss is not certificate.",
            "- Terminal truth still requires verified proof/refutation/importer revalidation.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
