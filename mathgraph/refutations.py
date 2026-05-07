"""Public refutation-certificate abstraction.

The current algebraic nursery represents concrete refutations as finite magma
countermodels.  ``TerminalForm.FINITE_COUNTERMODEL`` remains the compatibility
terminal form, while this module names the broader concept.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mathgraph.certificates import TerminalForm


@dataclass(frozen=True)
class RefutationCertificate:
    certificate_id: str
    refutation_kind: str = "finite_magma_countermodel"
    terminal_form: str = TerminalForm.FINITE_COUNTERMODEL.value
    source: str | None = None
    target: str | None = None
    countermodel: dict[str, Any] | None = None
    witness: dict[str, Any] | None = None
    evidence: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "certificate_id": self.certificate_id,
            "refutation_kind": self.refutation_kind,
            "terminal_form": self.terminal_form,
            "source": self.source,
            "target": self.target,
            "countermodel": self.countermodel,
            "witness": self.witness,
            "evidence": dict(self.evidence),
            "warnings": list(self.warnings),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RefutationCertificate":
        return cls(
            certificate_id=str(data.get("certificate_id", "")),
            refutation_kind=str(data.get("refutation_kind", "finite_magma_countermodel")),
            terminal_form=str(data.get("terminal_form", TerminalForm.FINITE_COUNTERMODEL.value)),
            source=data.get("source"),
            target=data.get("target"),
            countermodel=data.get("countermodel"),
            witness=data.get("witness"),
            evidence=dict(data.get("evidence", {})),
            warnings=[str(item) for item in data.get("warnings", [])],
        )


def finite_countermodel_to_refutation(payload: dict[str, Any]) -> RefutationCertificate:
    return RefutationCertificate(
        certificate_id=str(payload.get("certificate_id") or payload.get("proof_id") or ""),
        source=payload.get("source") or payload.get("source_equation"),
        target=payload.get("target") or payload.get("target_equation"),
        countermodel=payload.get("countermodel") or payload.get("model"),
        witness=payload.get("witness"),
        evidence=dict(payload),
    )
