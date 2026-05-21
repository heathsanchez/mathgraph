"""Advisory continuous-to-symbolic grounding records."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Any, Callable, Sequence


class GroundingStatus(str, Enum):
    UNGROUNDED = "UNGROUNDED"
    EMPIRICALLY_GROUNDED = "EMPIRICALLY_GROUNDED"
    PARTIALLY_GROUNDED = "PARTIALLY_GROUNDED"
    GROUNDING_FAILED = "GROUNDING_FAILED"
    ADVISORY_ONLY = "ADVISORY_ONLY"


def _parse_status(value: Any) -> GroundingStatus:
    if isinstance(value, GroundingStatus):
        return value
    text = str(value or "").strip().upper().replace("-", "_")
    for item in GroundingStatus:
        if text == item.value:
            return item
    return GroundingStatus.UNGROUNDED


@dataclass(frozen=True)
class SensorSignature:
    sensor_id: str
    modality: str
    dimensionality: int
    sampling_rate: float
    value_range: tuple[float, float] = (-1.0, 1.0)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "sensor_id": self.sensor_id,
            "modality": self.modality,
            "dimensionality": self.dimensionality,
            "sampling_rate": self.sampling_rate,
            "value_range": list(self.value_range),
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SensorSignature":
        value_range = data.get("value_range", (-1.0, 1.0))
        return cls(
            sensor_id=str(data.get("sensor_id", "")),
            modality=str(data.get("modality", "")),
            dimensionality=int(data.get("dimensionality", 0) or 0),
            sampling_rate=float(data.get("sampling_rate", 0.0) or 0.0),
            value_range=(float(value_range[0]), float(value_range[1])),
            notes=str(data.get("notes", "")),
        )


@dataclass(frozen=True)
class GroundingFunctionSpec:
    function_id: str
    description: str
    threshold: float | None = None
    uses_htilt: bool = False
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "function_id": self.function_id,
            "description": self.description,
            "threshold": self.threshold,
            "uses_htilt": self.uses_htilt,
            "payload": dict(self.payload),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GroundingFunctionSpec":
        threshold = data.get("threshold")
        return cls(
            function_id=str(data.get("function_id", "")),
            description=str(data.get("description", "")),
            threshold=float(threshold) if threshold is not None else None,
            uses_htilt=bool(data.get("uses_htilt", False)),
            payload=dict(data.get("payload", {})),
        )


@dataclass(frozen=True)
class GroundingRecord:
    grounding_id: str
    symbol: str
    sensor: SensorSignature
    grounding_function: GroundingFunctionSpec
    status: GroundingStatus = GroundingStatus.UNGROUNDED
    evidence_samples: int = 0
    confidence: float = 0.0
    notes: str = ""
    advisory: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "status", _parse_status(self.status))
        object.__setattr__(self, "advisory", True)

    def attempt_grounding(
        self,
        signal: Sequence[float],
        htilt_fn: Callable[[Sequence[float]], float] | None = None,
    ) -> "GroundingRecord":
        if not signal:
            return replace(
                self,
                status=GroundingStatus.GROUNDING_FAILED,
                evidence_samples=0,
                confidence=0.0,
                notes="No signal samples were supplied.",
                advisory=True,
            )
        if htilt_fn is not None:
            score = float(htilt_fn(signal))
        else:
            lo, hi = self.sensor.value_range
            span = hi - lo if hi != lo else 1.0
            mean = sum(float(x) for x in signal) / len(signal)
            score = (mean - lo) / span
        score = min(max(score, 0.0), 1.0)
        threshold = self.grounding_function.threshold
        threshold = 0.5 if threshold is None else float(threshold)
        status = GroundingStatus.EMPIRICALLY_GROUNDED if score >= threshold else GroundingStatus.PARTIALLY_GROUNDED
        return replace(
            self,
            status=status,
            evidence_samples=len(signal),
            confidence=score,
            notes="Grounding score is advisory and cannot promote truth.",
            advisory=True,
        )

    def to_denotation_payload(self) -> dict[str, Any]:
        return {
            "grounding_id": self.grounding_id,
            "symbol": self.symbol,
            "status": self.status.value,
            "confidence": self.confidence,
            "evidence_samples": self.evidence_samples,
            "advisory": True,
            "can_cross_verifier_boundary": False,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "grounding_id": self.grounding_id,
            "symbol": self.symbol,
            "sensor": self.sensor.to_dict(),
            "grounding_function": self.grounding_function.to_dict(),
            "status": self.status.value,
            "evidence_samples": self.evidence_samples,
            "confidence": self.confidence,
            "notes": self.notes,
            "advisory": True,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GroundingRecord":
        return cls(
            grounding_id=str(data.get("grounding_id", "")),
            symbol=str(data.get("symbol", "")),
            sensor=SensorSignature.from_dict(data.get("sensor", {})),
            grounding_function=GroundingFunctionSpec.from_dict(data.get("grounding_function", {})),
            status=_parse_status(data.get("status")),
            evidence_samples=int(data.get("evidence_samples", 0) or 0),
            confidence=float(data.get("confidence", 0.0) or 0.0),
            notes=str(data.get("notes", "")),
            advisory=True,
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, text: str) -> "GroundingRecord":
        return cls.from_dict(json.loads(text))
