"""Verifier/prover/model-finder backend metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class VerifierBackendKind(str, Enum):
    FINITE_TABLE_CHECKER = "FINITE_TABLE_CHECKER"
    LEAN = "LEAN"
    ISABELLE_SLEDGEHAMMER = "ISABELLE_SLEDGEHAMMER"
    ISABELLE_NITPICK = "ISABELLE_NITPICK"
    ISABELLE_NUNCHAKU = "ISABELLE_NUNCHAKU"
    SMT_SOLVER = "SMT_SOLVER"
    HOL_ATP = "HOL_ATP"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    IMPORT_ONLY = "IMPORT_ONLY"
    UNKNOWN = "UNKNOWN"


class BackendRole(str, Enum):
    PROOF_FINDER = "PROOF_FINDER"
    MODEL_FINDER = "MODEL_FINDER"
    CERTIFICATE_CHECKER = "CERTIFICATE_CHECKER"
    CHAIN_AUDITOR = "CHAIN_AUDITOR"
    EXPORTER = "EXPORTER"
    IMPORTER = "IMPORTER"
    ADVISORY_ANALYZER = "ADVISORY_ANALYZER"


def _enum(enum_type: Any, value: Any, default: Any) -> Any:
    if isinstance(value, enum_type):
        return value
    for member in enum_type:
        if str(value) == member.value:
            return member
    return default


@dataclass(frozen=True)
class VerifierBackendProfile:
    backend_id: str
    name: str
    backend_kind: VerifierBackendKind
    roles: list[BackendRole] = field(default_factory=list)
    host_logic: str | None = None
    object_logic: str | None = None
    supports_proofs: bool = False
    supports_models: bool = False
    produces_replayable_artifacts: bool = False
    native_to_domain_kernel: bool = False
    artifact_risk: str = "UNKNOWN"
    notes: str = ""
    payload: dict[str, Any] = field(default_factory=dict)

    def is_verifier_authoritative_for_native(self) -> bool:
        return self.native_to_domain_kernel and self.produces_replayable_artifacts

    def summary(self) -> dict[str, Any]:
        return {
            "backend_id": self.backend_id,
            "name": self.name,
            "backend_kind": self.backend_kind.value,
            "roles": [role.value for role in self.roles],
            "supports_proofs": self.supports_proofs,
            "supports_models": self.supports_models,
            "native_authoritative": self.is_verifier_authoritative_for_native(),
            "truth_boundary": "Backend metadata is not a terminal certificate.",
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "backend_id": self.backend_id,
            "name": self.name,
            "backend_kind": self.backend_kind.value,
            "roles": [role.value if hasattr(role, "value") else str(role) for role in self.roles],
            "host_logic": self.host_logic,
            "object_logic": self.object_logic,
            "supports_proofs": self.supports_proofs,
            "supports_models": self.supports_models,
            "produces_replayable_artifacts": self.produces_replayable_artifacts,
            "native_to_domain_kernel": self.native_to_domain_kernel,
            "artifact_risk": self.artifact_risk,
            "notes": self.notes,
            "payload": dict(self.payload),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VerifierBackendProfile":
        return cls(
            backend_id=str(data["backend_id"]),
            name=str(data["name"]),
            backend_kind=_enum(VerifierBackendKind, data.get("backend_kind"), VerifierBackendKind.UNKNOWN),
            roles=[_enum(BackendRole, item, BackendRole.ADVISORY_ANALYZER) for item in data.get("roles", [])],
            host_logic=data.get("host_logic"),
            object_logic=data.get("object_logic"),
            supports_proofs=bool(data.get("supports_proofs", False)),
            supports_models=bool(data.get("supports_models", False)),
            produces_replayable_artifacts=bool(data.get("produces_replayable_artifacts", False)),
            native_to_domain_kernel=bool(data.get("native_to_domain_kernel", False)),
            artifact_risk=str(data.get("artifact_risk", "UNKNOWN")),
            notes=str(data.get("notes", "")),
            payload=dict(data.get("payload", {})),
        )


def python_finite_table_checker_backend() -> VerifierBackendProfile:
    return VerifierBackendProfile(
        backend_id="backend_python_finite_table_checker",
        name="Python finite table checker",
        backend_kind=VerifierBackendKind.FINITE_TABLE_CHECKER,
        roles=[BackendRole.MODEL_FINDER, BackendRole.CERTIFICATE_CHECKER],
        host_logic="Python finite evaluator",
        object_logic="universal equational logic over finite magmas",
        supports_models=True,
        produces_replayable_artifacts=True,
        native_to_domain_kernel=True,
        artifact_risk="LOW",
        notes="Finite countermodel hits can become terminal only after replay/verification.",
    )


def lean_backend_placeholder() -> VerifierBackendProfile:
    return VerifierBackendProfile(
        backend_id="backend_lean_placeholder",
        name="Lean backend placeholder",
        backend_kind=VerifierBackendKind.LEAN,
        roles=[BackendRole.PROOF_FINDER, BackendRole.CERTIFICATE_CHECKER, BackendRole.EXPORTER],
        host_logic="Lean",
        supports_proofs=True,
        artifact_risk="UNKNOWN",
        notes="Metadata only; no Lean execution in this layer.",
    )


def isabelle_sledgehammer_backend_placeholder() -> VerifierBackendProfile:
    return VerifierBackendProfile(
        backend_id="backend_isabelle_sledgehammer_placeholder",
        name="Isabelle Sledgehammer placeholder",
        backend_kind=VerifierBackendKind.ISABELLE_SLEDGEHAMMER,
        roles=[BackendRole.PROOF_FINDER, BackendRole.ADVISORY_ANALYZER],
        host_logic="Isabelle/HOL",
        supports_proofs=True,
        artifact_risk="UNKNOWN",
        notes="Metadata only; no Isabelle execution.",
    )


def isabelle_nitpick_backend_placeholder() -> VerifierBackendProfile:
    return VerifierBackendProfile(
        backend_id="backend_isabelle_nitpick_placeholder",
        name="Isabelle Nitpick placeholder",
        backend_kind=VerifierBackendKind.ISABELLE_NITPICK,
        roles=[BackendRole.MODEL_FINDER, BackendRole.ADVISORY_ANALYZER],
        host_logic="Isabelle/HOL",
        supports_models=True,
        artifact_risk="UNKNOWN",
        notes="Metadata only; no model finder execution.",
    )


def isabelle_nunchaku_backend_placeholder() -> VerifierBackendProfile:
    return VerifierBackendProfile(
        backend_id="backend_isabelle_nunchaku_placeholder",
        name="Isabelle Nunchaku placeholder",
        backend_kind=VerifierBackendKind.ISABELLE_NUNCHAKU,
        roles=[BackendRole.MODEL_FINDER, BackendRole.ADVISORY_ANALYZER],
        host_logic="Isabelle/HOL",
        supports_models=True,
        artifact_risk="UNKNOWN",
        notes="Metadata only; no model finder execution.",
    )
