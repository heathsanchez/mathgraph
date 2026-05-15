"""Formal-workbench metadata for registered MathGraph worlds."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class WorkbenchLayer(str, Enum):
    L0_META_LOGIC_SUBSTRATE = "L0_META_LOGIC_SUBSTRATE"
    L1_LOGIC_AND_EMBEDDINGS = "L1_LOGIC_AND_EMBEDDINGS"
    L2_DOMAIN_THEORIES = "L2_DOMAIN_THEORIES"
    L3_APPLICATION_SCENARIOS = "L3_APPLICATION_SCENARIOS"


class WorkbenchLifecycleStatus(str, Enum):
    DECLARED = "DECLARED"
    SEMANTICS_SELECTED = "SEMANTICS_SELECTED"
    EMBEDDING_IMPLEMENTED = "EMBEDDING_IMPLEMENTED"
    MODEL_FINDER_TESTED = "MODEL_FINDER_TESTED"
    PROVER_TESTED = "PROVER_TESTED"
    FAITHFULNESS_ASSESSED = "FAITHFULNESS_ASSESSED"
    BENCHMARKED = "BENCHMARKED"
    DOMAIN_READY = "DOMAIN_READY"
    APPLICATION_READY = "APPLICATION_READY"
    DEPRECATED = "DEPRECATED"


def _enum(enum_type: Any, value: Any, default: Any) -> Any:
    if isinstance(value, enum_type):
        return value
    for member in enum_type:
        if str(value) == member.value:
            return member
    return default


@dataclass(frozen=True)
class LogicWorkbench:
    workbench_id: str
    name: str
    description: str = ""
    layer: WorkbenchLayer = WorkbenchLayer.L0_META_LOGIC_SUBSTRATE
    domain_kernel_ids: list[str] = field(default_factory=list)
    formal_world_ids: list[str] = field(default_factory=list)
    logic_combination_ids: list[str] = field(default_factory=list)
    benchmark_suite_ids: list[str] = field(default_factory=list)
    lifecycle_status: WorkbenchLifecycleStatus = WorkbenchLifecycleStatus.DECLARED
    notes: str = ""
    payload: dict[str, Any] = field(default_factory=dict)

    def is_application_ready(self) -> bool:
        return self.lifecycle_status is WorkbenchLifecycleStatus.APPLICATION_READY

    def summary(self) -> dict[str, Any]:
        return {
            "workbench_id": self.workbench_id,
            "name": self.name,
            "layer": self.layer.value,
            "lifecycle_status": self.lifecycle_status.value,
            "domain_kernel_count": len(self.domain_kernel_ids),
            "formal_world_count": len(self.formal_world_ids),
            "benchmark_suite_count": len(self.benchmark_suite_ids),
            "application_ready": self.is_application_ready(),
            "truth_boundary": "Workbench metadata organizes evidence; it is not verification.",
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "workbench_id": self.workbench_id,
            "name": self.name,
            "description": self.description,
            "layer": self.layer.value,
            "domain_kernel_ids": list(self.domain_kernel_ids),
            "formal_world_ids": list(self.formal_world_ids),
            "logic_combination_ids": list(self.logic_combination_ids),
            "benchmark_suite_ids": list(self.benchmark_suite_ids),
            "lifecycle_status": self.lifecycle_status.value,
            "notes": self.notes,
            "payload": dict(self.payload),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LogicWorkbench":
        return cls(
            workbench_id=str(data["workbench_id"]),
            name=str(data["name"]),
            description=str(data.get("description", "")),
            layer=_enum(WorkbenchLayer, data.get("layer"), WorkbenchLayer.L0_META_LOGIC_SUBSTRATE),
            domain_kernel_ids=[str(item) for item in data.get("domain_kernel_ids", [])],
            formal_world_ids=[str(item) for item in data.get("formal_world_ids", [])],
            logic_combination_ids=[str(item) for item in data.get("logic_combination_ids", [])],
            benchmark_suite_ids=[str(item) for item in data.get("benchmark_suite_ids", [])],
            lifecycle_status=_enum(
                WorkbenchLifecycleStatus,
                data.get("lifecycle_status"),
                WorkbenchLifecycleStatus.DECLARED,
            ),
            notes=str(data.get("notes", "")),
            payload=dict(data.get("payload", {})),
        )


def reference_logic_workbench() -> LogicWorkbench:
    return LogicWorkbench(
        workbench_id="workbench_logikey_style",
        name="Reference logic workbench",
        description=(
            "Methodology metadata for layered object logics, shallow semantic "
            "embeddings in HOL, prover/model-finder experimentation, and "
            "faithfulness assessment."
        ),
        layer=WorkbenchLayer.L1_LOGIC_AND_EMBEDDINGS,
        formal_world_ids=["formal_world_aot_precedent"],
        benchmark_suite_ids=["benchmark_logikey_methodology"],
        lifecycle_status=WorkbenchLifecycleStatus.DECLARED,
        notes=(
            "This is not an imported external theory. It records the workbench "
            "discipline: L1/L2/L3 separation, logic combinations, interpretation "
            "choice points, backend experimentation, and bridge faithfulness."
        ),
        payload={"advisory_only": True, "imported_external_theories": False},
    )


def logikey_style_workbench() -> LogicWorkbench:
    """Legacy internal alias; use ``reference_logic_workbench`` publicly."""

    return reference_logic_workbench()


def mathgraph_default_workbench() -> LogicWorkbench:
    return LogicWorkbench(
        workbench_id="workbench_mathgraph_default",
        name="MathGraph default verification workbench",
        description=(
            "Generative verification kernel workbench for ETP nursery, "
            "DomainKernel/FormalWorld metadata, LawbookStore, and "
            "Root/Reason/Obstruction atlases."
        ),
        layer=WorkbenchLayer.L3_APPLICATION_SCENARIOS,
        domain_kernel_ids=["etp_magma"],
        formal_world_ids=["formal_world_etp_magma"],
        benchmark_suite_ids=["benchmark_etp_matrix_metadata"],
        lifecycle_status=WorkbenchLifecycleStatus.BENCHMARKED,
        notes="Verifiers decide; scheduler, roots, reasons, and benchmarks remain advisory.",
        payload={"truth_boundary": "benchmarks_are_not_proof"},
    )
