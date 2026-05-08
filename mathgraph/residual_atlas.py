"""Residual Atlas v1: advisory membrane mapping for unresolved claims."""

from __future__ import annotations

import json
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

from mathgraph.continuation_traces import ContinuationTrace, ContinuationTraceStore
from mathgraph.hashing import content_id
from mathgraph.route_policy_v2 import RoutePolicyV2Report

RESIDUAL_STATUSES = {
    "constructor_failed",
    "parse_failed",
    "verification_failed",
    "residual",
    "near_miss",
    "obstruction_recorded",
    "skipped",
}

VERIFIED_STATUSES = {"verified_false", "verified_true", "known_certificate_found"}

ATLAS_WARNINGS = [
    "Residual atlas is advisory, not truth.",
    "Residual classification never verifies or refutes a claim.",
    "Failed search is not proof.",
    "Near miss is not certificate.",
    "Terminal truth still requires verified proof/refutation/importer revalidation.",
]


@dataclass(frozen=True)
class ResidualCase:
    residual_id: str
    source: str
    target: str
    source_idx: int | None
    target_idx: int | None
    claim_id: str | None
    status: str
    root_label: str | None
    obstruction_label: str | None
    constructor_family: str | None
    route_key: str | None
    attempts: int
    failures: int
    residuals: int
    near_misses: int
    verified: int
    promoted: int
    best_near_miss_score: float
    mean_near_miss_score: float
    residual_compression_delta: float
    htilt_priority: float
    membrane_pressure: float
    saturation_score: float
    representation_shift_score: float
    next_action: str
    warnings: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ResidualCase":
        return cls(**dict(data))


@dataclass(frozen=True)
class ResidualCluster:
    cluster_id: str
    label: str
    root_label: str | None
    obstruction_label: str | None
    constructor_family: str | None
    case_count: int
    attempted_count: int
    near_miss_count: int
    failure_count: int
    verified_count: int
    mean_membrane_pressure: float
    mean_saturation_score: float
    mean_representation_shift_score: float
    top_cases: list[str]
    recommendation: str
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ResidualCluster":
        return cls(**dict(data))


@dataclass(frozen=True)
class ResidualAtlasReport:
    run_id: str
    case_count: int
    cluster_count: int
    summary: dict[str, Any]
    cases: list[ResidualCase]
    clusters: list[ResidualCluster]
    outputs: dict[str, str]
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "case_count": self.case_count,
            "cluster_count": self.cluster_count,
            "summary": dict(self.summary),
            "cases": [case.to_dict() for case in self.cases],
            "clusters": [cluster.to_dict() for cluster in self.clusters],
            "outputs": dict(self.outputs),
            "warnings": list(self.warnings),
            "advisory_only": True,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ResidualAtlasReport":
        return cls(
            run_id=str(data.get("run_id") or ""),
            case_count=int(data.get("case_count", len(data.get("cases", []))) or 0),
            cluster_count=int(data.get("cluster_count", len(data.get("clusters", []))) or 0),
            summary=dict(data.get("summary") or {}),
            cases=[ResidualCase.from_dict(row) for row in data.get("cases", [])],
            clusters=[ResidualCluster.from_dict(row) for row in data.get("clusters", [])],
            outputs=dict(data.get("outputs") or {}),
            warnings=list(data.get("warnings") or []),
        )


def build_residual_atlas_from_traces(
    trace_store_path: str,
    *,
    route_policy: RoutePolicyV2Report | dict[str, Any] | None = None,
    out_dir: str | None = None,
    run_id: str | None = None,
) -> ResidualAtlasReport:
    traces = [trace.to_dict() for trace in ContinuationTraceStore(trace_store_path).load_all()]
    return build_residual_atlas_from_rows(traces, route_policy=route_policy, out_dir=out_dir, run_id=run_id)


def build_residual_atlas_from_rows(
    rows: Iterable[dict[str, Any]],
    *,
    route_policy: RoutePolicyV2Report | dict[str, Any] | None = None,
    out_dir: str | None = None,
    run_id: str | None = None,
) -> ResidualAtlasReport:
    run_id = run_id or f"residual_atlas_{int(time.time() * 1000)}"
    traces = [_trace_dict(row) for row in rows]
    policy_by_route = _policy_by_route(route_policy)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    verified_context: Counter[str] = Counter()
    for row in traces:
        claim_id = _claim_id(row)
        if row.get("status") in VERIFIED_STATUSES:
            verified_context[claim_id] += 1
            continue
        if _is_unresolved(row):
            grouped[claim_id].append(row)

    cases = [_case_from_group(claim_id, group, policy_by_route, verified_context[claim_id]) for claim_id, group in grouped.items()]
    cases = sorted(cases, key=lambda item: (-item.membrane_pressure, item.residual_id))
    clusters = _clusters(cases)
    summary = {
        "case_count": len(cases),
        "cluster_count": len(clusters),
        "recommendation_counts": dict(sorted(Counter(case.next_action for case in cases).items())),
        "cluster_recommendation_counts": dict(sorted(Counter(cluster.recommendation for cluster in clusters).items())),
        "top_cluster": clusters[0].label if clusters else None,
        "advisory_only": True,
    }
    outputs: dict[str, str] = {}
    report = ResidualAtlasReport(
        run_id=run_id,
        case_count=len(cases),
        cluster_count=len(clusters),
        summary=summary,
        cases=cases,
        clusters=clusters,
        outputs=outputs,
        warnings=list(ATLAS_WARNINGS),
    )
    if out_dir:
        outputs = write_residual_atlas(report, out_dir)
        report = ResidualAtlasReport(
            run_id=report.run_id,
            case_count=report.case_count,
            cluster_count=report.cluster_count,
            summary=report.summary,
            cases=report.cases,
            clusters=report.clusters,
            outputs=outputs,
            warnings=report.warnings,
        )
    return report


def write_residual_atlas(report: ResidualAtlasReport | dict[str, Any], out_dir: str) -> dict[str, str]:
    atlas = report if isinstance(report, ResidualAtlasReport) else ResidualAtlasReport.from_dict(report)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    outputs = {
        "residual_atlas_report_json": str(out / "residual_atlas_report.json"),
        "residual_cases_jsonl": str(out / "residual_cases.jsonl"),
        "residual_clusters_jsonl": str(out / "residual_clusters.jsonl"),
        "residual_atlas_report_md": str(out / "residual_atlas_report.md"),
    }
    persisted = ResidualAtlasReport(
        run_id=atlas.run_id,
        case_count=atlas.case_count,
        cluster_count=atlas.cluster_count,
        summary=atlas.summary,
        cases=atlas.cases,
        clusters=atlas.clusters,
        outputs=outputs,
        warnings=atlas.warnings,
    )
    _write_json(persisted.to_dict(), out / "residual_atlas_report.json")
    _write_jsonl([case.to_dict() for case in atlas.cases], out / "residual_cases.jsonl")
    _write_jsonl([cluster.to_dict() for cluster in atlas.clusters], out / "residual_clusters.jsonl")
    _write_markdown(persisted, out / "residual_atlas_report.md")
    return outputs


def _case_from_group(
    claim_id: str,
    group: list[dict[str, Any]],
    policy_by_route: dict[str, dict[str, Any]],
    verified_context_count: int,
) -> ResidualCase:
    first = group[0]
    attempts = len(group)
    failures = sum(1 for row in group if row.get("status") in {"constructor_failed", "parse_failed", "verification_failed", "error"})
    residuals = sum(1 for row in group if row.get("status") in {"residual", "skipped"})
    near_misses = sum(1 for row in group if row.get("status") == "near_miss" or float(row.get("near_miss_score") or 0.0) > 0)
    verified = sum(1 for row in group if row.get("verified"))
    promoted = sum(1 for row in group if row.get("promoted"))
    scores = [float(row.get("near_miss_score") or 0.0) for row in group]
    best_near = max(scores, default=0.0)
    mean_near = sum(scores) / max(len(scores), 1)
    compression = max(float(row.get("residual_compression_delta") or 0.0) for row in group)
    route_key = _route_key(first)
    policy = policy_by_route.get(route_key, {})
    priority = float(policy.get("htilt_priority") or 0.0)
    attempt_pressure = min(1.0, attempts / 5.0)
    failure_pressure = min(1.0, (failures + residuals) / max(attempts, 1))
    near_miss_pressure = min(1.0, mean_near)
    membrane = 0.25 * attempt_pressure + 0.25 * failure_pressure + 0.25 * near_miss_pressure + 0.25 * priority
    saturation = 0.50 * attempt_pressure + 0.35 * failure_pressure + 0.15 * (1.0 - near_miss_pressure)
    obstruction_repeat = 1.0 if _stable_label(group, "obstruction_label") and failures + residuals >= 2 else 0.0
    representation = 0.50 * membrane + 0.35 * saturation + 0.15 * obstruction_repeat
    next_action = _next_action(
        attempts=attempts,
        failures=failures,
        residuals=residuals,
        mean_near=mean_near,
        priority=priority,
        saturation=saturation,
        representation_shift=representation,
        stable_label=obstruction_repeat > 0,
    )
    return ResidualCase(
        residual_id=content_id("residual", {"claim_id": claim_id, "route_key": route_key}, n=20),
        source=str(first.get("source") or ""),
        target=str(first.get("target") or ""),
        source_idx=_optional_int(first.get("source_idx")),
        target_idx=_optional_int(first.get("target_idx")),
        claim_id=claim_id,
        status=_dominant_status(group),
        root_label=_stable_value(group, "root_label"),
        obstruction_label=_stable_value(group, "obstruction_label"),
        constructor_family=_stable_value(group, "constructor_family"),
        route_key=route_key,
        attempts=attempts,
        failures=failures,
        residuals=residuals,
        near_misses=near_misses,
        verified=verified,
        promoted=promoted,
        best_near_miss_score=round(best_near, 6),
        mean_near_miss_score=round(mean_near, 6),
        residual_compression_delta=round(compression, 6),
        htilt_priority=round(priority, 6),
        membrane_pressure=round(membrane, 6),
        saturation_score=round(saturation, 6),
        representation_shift_score=round(representation, 6),
        next_action=next_action,
        warnings=list(ATLAS_WARNINGS),
        evidence={
            "advisory_only": True,
            "trace_ids": [row.get("trace_id") for row in group if row.get("trace_id")],
            "verified_context_count": verified_context_count,
            "policy_recommendation": policy.get("recommendation"),
            "attempt_pressure": round(attempt_pressure, 6),
            "failure_pressure": round(failure_pressure, 6),
            "near_miss_pressure": round(near_miss_pressure, 6),
        },
    )


def _clusters(cases: list[ResidualCase]) -> list[ResidualCluster]:
    groups: dict[tuple[str | None, str | None, str | None], list[ResidualCase]] = defaultdict(list)
    for case in cases:
        key = (case.root_label, case.obstruction_label, case.constructor_family)
        if key == (None, None, None):
            key = (case.root_label, case.obstruction_label, case.constructor_family or "unclassified_residual")
        groups[key].append(case)
    clusters: list[ResidualCluster] = []
    for key, rows in sorted(groups.items(), key=lambda item: str(item[0])):
        root, obstruction, constructor = key
        mean_membrane = _mean([row.membrane_pressure for row in rows])
        mean_saturation = _mean([row.saturation_score for row in rows])
        mean_shift = _mean([row.representation_shift_score for row in rows])
        near_miss_count = sum(row.near_misses for row in rows)
        failure_count = sum(row.failures for row in rows)
        verified_count = sum(row.verified for row in rows)
        recommendation = _cluster_recommendation(
            mean_membrane=mean_membrane,
            mean_saturation=mean_saturation,
            mean_shift=mean_shift,
            near_miss_count=near_miss_count,
            failure_count=failure_count,
            verified_count=verified_count,
            case_count=len(rows),
        )
        label = "|".join(str(part) for part in (root or "none", obstruction or "none", constructor or "none"))
        clusters.append(
            ResidualCluster(
                cluster_id=content_id("residual_cluster", label, n=20),
                label=label,
                root_label=root,
                obstruction_label=obstruction,
                constructor_family=constructor,
                case_count=len(rows),
                attempted_count=sum(row.attempts for row in rows),
                near_miss_count=near_miss_count,
                failure_count=failure_count,
                verified_count=verified_count,
                mean_membrane_pressure=round(mean_membrane, 6),
                mean_saturation_score=round(mean_saturation, 6),
                mean_representation_shift_score=round(mean_shift, 6),
                top_cases=[row.residual_id for row in sorted(rows, key=lambda item: -item.membrane_pressure)[:5]],
                recommendation=recommendation,
                evidence={"advisory_only": True, "case_ids": [row.residual_id for row in rows]},
            )
        )
    return sorted(clusters, key=lambda item: (-item.mean_membrane_pressure, item.cluster_id))


def _next_action(
    *,
    attempts: int,
    failures: int,
    residuals: int,
    mean_near: float,
    priority: float,
    saturation: float,
    representation_shift: float,
    stable_label: bool,
) -> str:
    if priority >= 0.65 and mean_near >= 0.5:
        return "schedule_next_attempt"
    if failures + residuals >= 2 and stable_label:
        return "name_obstruction"
    if representation_shift >= 0.65:
        return "seek_representation_shift"
    if saturation >= 0.65 and priority < 0.45:
        return "suppress_saturated_region"
    if attempts <= 1:
        return "hold"
    return "hold"


def _cluster_recommendation(
    *,
    mean_membrane: float,
    mean_saturation: float,
    mean_shift: float,
    near_miss_count: int,
    failure_count: int,
    verified_count: int,
    case_count: int,
) -> str:
    if mean_membrane >= 0.55 and near_miss_count > 0:
        return "schedule_next_attempt"
    if failure_count >= 2 and verified_count == 0 and case_count >= 2:
        return "name_obstruction"
    if mean_shift >= 0.65:
        return "seek_representation_shift"
    if mean_saturation >= 0.65 and near_miss_count == 0:
        return "suppress_saturated_region"
    return "insufficient_evidence"


def _policy_by_route(policy: RoutePolicyV2Report | dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if policy is None:
        return {}
    cards = policy.cards if isinstance(policy, RoutePolicyV2Report) else policy.get("cards", [])
    output = {}
    for card in cards:
        data = card.to_dict() if hasattr(card, "to_dict") else dict(card)
        output[str(data.get("route_key"))] = data
    return output


def _trace_dict(row: dict[str, Any]) -> dict[str, Any]:
    if isinstance(row, ContinuationTrace):
        return row.to_dict()
    data = dict(row)
    if "status" not in data:
        data["status"] = "residual"
    data.setdefault("claim_id", _claim_id(data))
    return data


def _is_unresolved(row: dict[str, Any]) -> bool:
    if row.get("status") in RESIDUAL_STATUSES:
        return True
    return row.get("status") == "skipped" and not row.get("verified")


def _claim_id(row: dict[str, Any]) -> str:
    return str(
        row.get("claim_id")
        or content_id(
            "claim",
            {
                "source": row.get("source"),
                "target": row.get("target"),
                "source_idx": row.get("source_idx"),
                "target_idx": row.get("target_idx"),
            },
            n=20,
        )
    )


def _route_key(row: dict[str, Any]) -> str:
    return str(
        row.get("route_key")
        or "|".join(
            [
                str(row.get("root_label") or "none"),
                str(row.get("constructor_family") or "none"),
                str(row.get("route_type") or "unknown_route"),
            ]
        )
    )


def _dominant_status(rows: list[dict[str, Any]]) -> str:
    return Counter(str(row.get("status") or "residual") for row in rows).most_common(1)[0][0]


def _stable_value(rows: list[dict[str, Any]], key: str) -> str | None:
    values = [row.get(key) for row in rows if row.get(key) not in (None, "")]
    if not values:
        return None
    value, _ = Counter(values).most_common(1)[0]
    return str(value)


def _stable_label(rows: list[dict[str, Any]], key: str) -> bool:
    values = [row.get(key) for row in rows if row.get(key) not in (None, "")]
    return bool(values and len(set(values)) == 1)


def _mean(values: list[float]) -> float:
    return sum(values) / max(len(values), 1)


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _write_json(payload: dict[str, Any], path: Path) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_jsonl(rows: list[dict[str, Any]], path: Path) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _write_markdown(report: ResidualAtlasReport, path: Path) -> None:
    lines = [
        "# Residual Atlas Report",
        "",
        "## Summary",
        "",
        "| metric | value |",
        "| --- | ---: |",
        f"| case_count | {report.case_count} |",
        f"| cluster_count | {report.cluster_count} |",
        "",
        "## Top Clusters",
        "",
        "| label | cases | membrane_pressure | saturation | representation_shift | recommendation |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for cluster in report.clusters[:20]:
        lines.append(
            f"| `{cluster.label}` | {cluster.case_count} | {cluster.mean_membrane_pressure:.3f} | "
            f"{cluster.mean_saturation_score:.3f} | {cluster.mean_representation_shift_score:.3f} | "
            f"{cluster.recommendation} |"
        )
    lines.extend(["", "## Top Cases", ""])
    lines.extend(
        [
            "| residual_id | root | obstruction | constructor | pressure | next_action |",
            "| --- | --- | --- | --- | ---: | --- |",
        ]
    )
    for case in report.cases[:20]:
        lines.append(
            f"| `{case.residual_id}` | {case.root_label or ''} | {case.obstruction_label or ''} | "
            f"{case.constructor_family or ''} | {case.membrane_pressure:.3f} | {case.next_action} |"
        )
    lines.extend(
        [
            "",
            "## Trust Boundary",
            "",
            "- residual classification is advisory",
            "- failed search is not proof",
            "- near miss is not certificate",
            "- terminal truth still requires verified proof/refutation/importer revalidation",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
