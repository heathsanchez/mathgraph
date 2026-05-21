"""Advisory causal claim records and conservative identifiability hooks."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CausalClaimKind(str, Enum):
    OBSERVATIONAL = "OBSERVATIONAL"
    INTERVENTIONAL = "INTERVENTIONAL"
    COUNTERFACTUAL = "COUNTERFACTUAL"
    CAUSAL_MECHANISM = "CAUSAL_MECHANISM"
    TRANSPORT_CLAIM = "TRANSPORT_CLAIM"


class CausalResolutionKind(str, Enum):
    CAUSAL_PROOF = "CAUSAL_PROOF"
    CAUSAL_REFUTATION = "CAUSAL_REFUTATION"
    MECHANISM_IDENTIFIED = "MECHANISM_IDENTIFIED"
    TRANSPORT_VERIFIED = "TRANSPORT_VERIFIED"
    NAMED_CAUSAL_OBSTRUCTION = "NAMED_CAUSAL_OBSTRUCTION"
    ADVISORY_ONLY = "ADVISORY_ONLY"


def _parse_enum(enum_cls: type[Enum], value: Any, default: Enum) -> Enum:
    if isinstance(value, enum_cls):
        return value
    text = str(value or "").strip().upper().replace("-", "_")
    for item in enum_cls:
        if text == item.name or text == str(item.value).upper():
            return item
    return default


@dataclass(frozen=True)
class CausalVariable:
    name: str
    domain: str = "real"
    is_observable: bool = True
    is_latent: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "domain": self.domain,
            "is_observable": self.is_observable,
            "is_latent": self.is_latent,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CausalVariable":
        return cls(
            name=str(data.get("name", "")),
            domain=str(data.get("domain", "real")),
            is_observable=bool(data.get("is_observable", True)),
            is_latent=bool(data.get("is_latent", False)),
        )


@dataclass(frozen=True)
class CausalEdge:
    parent: str
    child: str
    mechanism: str = ""
    is_confounded: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "parent": self.parent,
            "child": self.child,
            "mechanism": self.mechanism,
            "is_confounded": self.is_confounded,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CausalEdge":
        return cls(
            parent=str(data.get("parent", "")),
            child=str(data.get("child", "")),
            mechanism=str(data.get("mechanism", "")),
            is_confounded=bool(data.get("is_confounded", False)),
        )


@dataclass(frozen=True)
class Intervention:
    variable: str
    value: Any

    def to_dict(self) -> dict[str, Any]:
        return {"variable": self.variable, "value": self.value}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Intervention":
        return cls(variable=str(data.get("variable", "")), value=data.get("value"))


@dataclass(frozen=True)
class CausalClaim:
    claim_id: str
    kind: CausalClaimKind
    variables: list[CausalVariable]
    edges: list[CausalEdge]
    query: str
    interventions: list[Intervention] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)
    advisory: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", _parse_enum(CausalClaimKind, self.kind, CausalClaimKind.OBSERVATIONAL))
        object.__setattr__(self, "advisory", True)

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "kind": self.kind.value,
            "variables": [v.to_dict() for v in self.variables],
            "edges": [e.to_dict() for e in self.edges],
            "query": self.query,
            "interventions": [i.to_dict() for i in self.interventions],
            "assumptions": list(self.assumptions),
            "evidence": dict(self.evidence),
            "advisory": True,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CausalClaim":
        return cls(
            claim_id=str(data.get("claim_id", "")),
            kind=_parse_enum(CausalClaimKind, data.get("kind"), CausalClaimKind.OBSERVATIONAL),  # type: ignore[arg-type]
            variables=[CausalVariable.from_dict(item) for item in data.get("variables", [])],
            edges=[CausalEdge.from_dict(item) for item in data.get("edges", [])],
            query=str(data.get("query", "")),
            interventions=[Intervention.from_dict(item) for item in data.get("interventions", [])],
            assumptions=[str(item) for item in data.get("assumptions", [])],
            evidence=dict(data.get("evidence", {})),
            advisory=True,
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, text: str) -> "CausalClaim":
        return cls.from_dict(json.loads(text))

    def variable_names(self) -> list[str]:
        return [variable.name for variable in self.variables]

    def has_latent_variables(self) -> bool:
        return any(variable.is_latent or not variable.is_observable for variable in self.variables)

    def has_confounded_edges(self) -> bool:
        return any(edge.is_confounded for edge in self.edges)

    def simple_identifiability_check(self) -> tuple[bool, str]:
        if self.has_latent_variables():
            return False, "Latent variables block this simple identifiability check."
        if self.has_confounded_edges():
            return False, "Confounded edges block this simple identifiability check."
        if self.kind == CausalClaimKind.OBSERVATIONAL and not self.interventions:
            return True, "Observational claim is identifiable by this limited structural check."
        if self.kind == CausalClaimKind.INTERVENTIONAL:
            return True, "Interventional claim is probably identifiable under the supplied no-confounding structure."
        return False, "This claim kind needs a real causal calculus module; only advisory hooks exist."

    def to_named_obstruction(self, reason: str) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "terminal_form": "NAMED_OBSTRUCTION",
            "obstruction_name": "CAUSAL_IDENTIFIABILITY_BLOCKED",
            "reason": reason,
            "advisory": True,
            "can_cross_verifier_boundary": False,
        }
