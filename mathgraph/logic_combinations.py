"""Advisory metadata for combining formal logics."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CombinationMethod(str, Enum):
    PRODUCT_COMBINATION = "PRODUCT_COMBINATION"
    FIBERED_COMBINATION = "FIBERED_COMBINATION"
    SHALLOW_HOL_COMBINATION = "SHALLOW_HOL_COMBINATION"
    SHARED_DOMAIN_COMBINATION = "SHARED_DOMAIN_COMBINATION"
    TRANSLATION_BRIDGE = "TRANSLATION_BRIDGE"
    ADVISORY_ALIGNMENT = "ADVISORY_ALIGNMENT"
    UNKNOWN = "UNKNOWN"


class ConflictPolicy(str, Enum):
    REJECT_ON_CONFLICT = "REJECT_ON_CONFLICT"
    KEEP_PARACONSISTENT = "KEEP_PARACONSISTENT"
    PREFER_NATIVE_KERNEL = "PREFER_NATIVE_KERNEL"
    PREFER_HIGHER_TRUST = "PREFER_HIGHER_TRUST"
    RECORD_OBSTRUCTION = "RECORD_OBSTRUCTION"
    UNKNOWN = "UNKNOWN"


def _enum(enum_type: Any, value: Any, default: Any) -> Any:
    if isinstance(value, enum_type):
        return value
    for member in enum_type:
        if str(value) == member.value:
            return member
    return default


@dataclass(frozen=True)
class LogicCombination:
    combination_id: str
    name: str
    component_kernel_ids: list[str]
    component_formal_world_ids: list[str] = field(default_factory=list)
    combination_method: CombinationMethod = CombinationMethod.UNKNOWN
    shared_semantic_domains: list[str] = field(default_factory=list)
    interaction_axioms: list[str] = field(default_factory=list)
    conflict_policy: ConflictPolicy = ConflictPolicy.RECORD_OBSTRUCTION
    faithfulness_status: str = "UNKNOWN"
    benchmark_status: str = "UNKNOWN"
    notes: str = ""
    payload: dict[str, Any] = field(default_factory=dict)

    def is_ready_for_truth_transfer(self) -> bool:
        return self.faithfulness_status in {"MECHANIZED", "PROVED_ON_PAPER"} and self.benchmark_status in {
            "BENCHMARKED",
            "PASSED",
        }

    def advisory_warning(self) -> str:
        return (
            f"Logic combination {self.combination_id} uses {self.combination_method.value}; "
            "truth transfer is unsafe until interaction semantics, conflict policy, "
            "faithfulness, and benchmarks are assessed."
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "combination_id": self.combination_id,
            "name": self.name,
            "component_kernel_ids": list(self.component_kernel_ids),
            "component_formal_world_ids": list(self.component_formal_world_ids),
            "combination_method": self.combination_method.value,
            "shared_semantic_domains": list(self.shared_semantic_domains),
            "interaction_axioms": list(self.interaction_axioms),
            "conflict_policy": self.conflict_policy.value,
            "faithfulness_status": self.faithfulness_status,
            "benchmark_status": self.benchmark_status,
            "notes": self.notes,
            "payload": dict(self.payload),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LogicCombination":
        return cls(
            combination_id=str(data["combination_id"]),
            name=str(data["name"]),
            component_kernel_ids=[str(item) for item in data.get("component_kernel_ids", [])],
            component_formal_world_ids=[str(item) for item in data.get("component_formal_world_ids", [])],
            combination_method=_enum(CombinationMethod, data.get("combination_method"), CombinationMethod.UNKNOWN),
            shared_semantic_domains=[str(item) for item in data.get("shared_semantic_domains", [])],
            interaction_axioms=[str(item) for item in data.get("interaction_axioms", [])],
            conflict_policy=_enum(ConflictPolicy, data.get("conflict_policy"), ConflictPolicy.RECORD_OBSTRUCTION),
            faithfulness_status=str(data.get("faithfulness_status", "UNKNOWN")),
            benchmark_status=str(data.get("benchmark_status", "UNKNOWN")),
            notes=str(data.get("notes", "")),
            payload=dict(data.get("payload", {})),
        )
