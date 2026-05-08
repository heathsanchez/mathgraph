"""Route Policy v2: advisory pressure cards from replay signals."""

from __future__ import annotations

import json
import math
import time
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from mathgraph.replay_engine import ReplayReport, RouteReplaySignal, replay_continuation_traces

POLICY_WARNINGS = [
    "Route policy is advisory scheduling pressure, not truth.",
    "H-tilt priority is not truth.",
    "Verifier/importer still decides terminal certificates.",
    "Failed finite search is not proof.",
    "Near-miss is not certificate.",
]


@dataclass(frozen=True)
class RoutePolicyV2Card:
    policy_id: str
    route_key: str
    root_label: str | None
    constructor_family: str | None
    route_type: str | None
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
    route_strength: float
    exploration_pressure: float
    obstruction_pressure: float
    exploitation_pressure: float
    htilt_priority: float
    recommendation: str
    trust_boundary: str
    warnings: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RoutePolicyV2Card":
        return cls(**dict(data))


@dataclass(frozen=True)
class RoutePolicyV2Report:
    run_id: str
    card_count: int
    summary: dict[str, Any]
    cards: list[RoutePolicyV2Card]
    outputs: dict[str, str]
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "card_count": self.card_count,
            "summary": dict(self.summary),
            "cards": [card.to_dict() for card in self.cards],
            "outputs": dict(self.outputs),
            "warnings": list(self.warnings),
            "advisory_only": True,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RoutePolicyV2Report":
        return cls(
            run_id=str(data.get("run_id") or ""),
            card_count=int(data.get("card_count", len(data.get("cards", []))) or 0),
            summary=dict(data.get("summary") or {}),
            cards=[RoutePolicyV2Card.from_dict(row) for row in data.get("cards", [])],
            outputs=dict(data.get("outputs") or {}),
            warnings=list(data.get("warnings") or []),
        )


def build_route_policy_v2_from_replay(
    replay_report: ReplayReport | dict[str, Any],
    *,
    beta: float = 1.0,
    exploration_weight: float = 0.4,
    obstruction_weight: float = 0.3,
) -> RoutePolicyV2Report:
    signals = _signals_from_replay(replay_report)
    run_id = f"route_policy_v2_{int(time.time() * 1000)}"
    cards = [
        _card_from_signal(
            signal,
            beta=beta,
            exploration_weight=exploration_weight,
            obstruction_weight=obstruction_weight,
        )
        for signal in signals
    ]
    cards = sorted(cards, key=lambda card: (-card.htilt_priority, card.route_key))
    summary = {
        "card_count": len(cards),
        "recommendation_counts": dict(sorted(Counter(card.recommendation for card in cards).items())),
        "top_route_key": cards[0].route_key if cards else None,
        "top_priority": cards[0].htilt_priority if cards else 0.0,
        "advisory_only": True,
    }
    return RoutePolicyV2Report(
        run_id=run_id,
        card_count=len(cards),
        summary=summary,
        cards=cards,
        outputs={},
        warnings=list(POLICY_WARNINGS),
    )


def build_route_policy_v2_from_trace_store(
    trace_store_path: str,
    *,
    out_dir: str | None = None,
    beta: float = 1.0,
) -> RoutePolicyV2Report:
    replay_dir = str(Path(out_dir) / "replay") if out_dir else None
    replay = replay_continuation_traces(trace_store_path, replay_dir)
    report = build_route_policy_v2_from_replay(replay, beta=beta)
    if out_dir:
        outputs = write_route_policy_v2(report, out_dir)
        report = RoutePolicyV2Report(
            run_id=report.run_id,
            card_count=report.card_count,
            summary=report.summary,
            cards=report.cards,
            outputs=outputs,
            warnings=report.warnings,
        )
    return report


def write_route_policy_v2(report: RoutePolicyV2Report | dict[str, Any], out_dir: str) -> dict[str, str]:
    policy = report if isinstance(report, RoutePolicyV2Report) else RoutePolicyV2Report.from_dict(report)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    outputs = {
        "route_policy_v2_report_json": str(out / "route_policy_v2_report.json"),
        "route_policy_v2_cards_jsonl": str(out / "route_policy_v2_cards.jsonl"),
        "route_policy_v2_report_md": str(out / "route_policy_v2_report.md"),
    }
    persisted = RoutePolicyV2Report(
        run_id=policy.run_id,
        card_count=policy.card_count,
        summary=policy.summary,
        cards=policy.cards,
        outputs=outputs,
        warnings=policy.warnings,
    )
    _write_json(persisted.to_dict(), out / "route_policy_v2_report.json")
    _write_jsonl([card.to_dict() for card in policy.cards], out / "route_policy_v2_cards.jsonl")
    _write_markdown(persisted, out / "route_policy_v2_report.md")
    return outputs


def _card_from_signal(
    signal: RouteReplaySignal,
    *,
    beta: float,
    exploration_weight: float,
    obstruction_weight: float,
) -> RoutePolicyV2Card:
    promoted_rate = signal.promoted / max(signal.attempts, 1)
    failure_rate = signal.failures / max(signal.attempts, 1)
    exploitation = signal.certificate_yield + 0.5 * promoted_rate
    exploration = signal.near_miss_rate * signal.mean_near_miss_score + max(
        signal.mean_residual_compression_delta, 0.0
    )
    if signal.recommendation == "convert_to_obstruction_pressure":
        obstruction = signal.residual_rate + failure_rate
    else:
        obstruction = 0.25 * signal.residual_rate
    route_strength = _normalize_strength(signal.route_strength_delta)
    raw = (
        route_strength
        + exploitation
        + exploration_weight * exploration
        + obstruction_weight * obstruction
        - 0.5 * signal.residual_rate
    )
    priority = _sigmoid(beta * raw)
    recommendation = _recommend_policy(signal, priority)
    route_type = _route_type_from_key(signal.route_key)
    return RoutePolicyV2Card(
        policy_id=f"policy_v2_{_safe_id(signal.route_key)}",
        route_key=signal.route_key,
        root_label=signal.root_label,
        constructor_family=signal.constructor_family,
        route_type=route_type,
        attempts=signal.attempts,
        verified=signal.verified,
        promoted=signal.promoted,
        failures=signal.failures,
        residuals=signal.residuals,
        near_misses=signal.near_misses,
        certificate_yield=signal.certificate_yield,
        near_miss_rate=signal.near_miss_rate,
        residual_rate=signal.residual_rate,
        mean_near_miss_score=signal.mean_near_miss_score,
        mean_residual_compression_delta=signal.mean_residual_compression_delta,
        route_strength=round(route_strength, 6),
        exploration_pressure=round(exploration, 6),
        obstruction_pressure=round(obstruction, 6),
        exploitation_pressure=round(exploitation, 6),
        htilt_priority=round(priority, 6),
        recommendation=recommendation,
        trust_boundary="advisory_scheduling_pressure_only",
        warnings=list(POLICY_WARNINGS),
        evidence={
            "advisory_only": True,
            "formula": "sigmoid(beta * (route_strength + exploitation + exploration_weight*exploration + obstruction_weight*obstruction - 0.5*residual_rate))",
            "beta": beta,
            "exploration_weight": exploration_weight,
            "obstruction_weight": obstruction_weight,
            "replay_recommendation": signal.recommendation,
            "failure_rate": round(failure_rate, 6),
            "promoted_rate": round(promoted_rate, 6),
            "route_strength_delta": signal.route_strength_delta,
        },
    )


def _recommend_policy(signal: RouteReplaySignal, priority: float) -> str:
    if signal.attempts < 3:
        return "insufficient_data"
    if signal.recommendation == "convert_to_obstruction_pressure":
        return "investigate_obstruction_route"
    if signal.certificate_yield > 0 and priority >= 0.55:
        return "exploit_verified_route"
    if signal.near_miss_rate >= 0.5 and signal.certificate_yield <= 0.5:
        return "explore_near_miss_route"
    if signal.attempts >= 3 and signal.certificate_yield == 0 and signal.near_miss_rate == 0 and signal.residual_rate >= 0.5:
        return "suppress_low_value_route"
    return "insufficient_data"


def _signals_from_replay(replay: ReplayReport | dict[str, Any]) -> list[RouteReplaySignal]:
    if isinstance(replay, ReplayReport):
        return list(replay.route_signals)
    return [RouteReplaySignal(**dict(row)) for row in replay.get("route_signals", [])]


def _normalize_strength(value: float) -> float:
    return _sigmoid(float(value))


def _sigmoid(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-value))


def _route_type_from_key(route_key: str) -> str | None:
    parts = str(route_key).split("|")
    return parts[2] if len(parts) >= 3 else None


def _safe_id(value: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in value)[:96]


def _write_json(payload: dict[str, Any], path: Path) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_jsonl(rows: list[dict[str, Any]], path: Path) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _write_markdown(report: RoutePolicyV2Report, path: Path) -> None:
    lines = [
        "# Route Policy v2 Report",
        "",
        "## Summary",
        "",
        "| metric | value |",
        "| --- | ---: |",
        f"| card_count | {report.card_count} |",
        f"| top_priority | {report.summary.get('top_priority', 0.0)} |",
        "",
        "## Top Routes",
        "",
        "| route_key | attempts | yield | near_miss_rate | htilt_priority | recommendation |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for card in sorted(report.cards, key=lambda item: (-item.htilt_priority, item.route_key))[:20]:
        lines.append(
            f"| `{card.route_key}` | {card.attempts} | {card.certificate_yield:.3f} | "
            f"{card.near_miss_rate:.3f} | {card.htilt_priority:.3f} | {card.recommendation} |"
        )
    lines.extend(
        [
            "",
            "## Trust Boundary",
            "",
            "- route policy is scheduling pressure",
            "- H-tilt priority is not truth",
            "- verifier/importer still decides terminal certificates",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
