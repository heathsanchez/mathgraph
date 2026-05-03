"""Certificate objects and terminal forms for accepted MathGraph claims."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TerminalForm(str, Enum):
    """The only terminal forms accepted by the kernel."""

    VERIFIED_PROOF = "VERIFIED_PROOF"
    FINITE_COUNTERMODEL = "FINITE_COUNTERMODEL"
    NAMED_OBSTRUCTION = "NAMED_OBSTRUCTION"


class VerificationStatus(str, Enum):
    """High-level verification status for a terminal trace."""

    VERIFIED = "VERIFIED"
    REFUTED = "REFUTED"
    OBSTRUCTED = "OBSTRUCTED"


@dataclass(frozen=True)
class Certificate:
    """A compact certificate that records how a claim terminates."""

    terminal_form: TerminalForm
    claim: str
    payload: dict[str, Any] = field(default_factory=dict)
    verifier: str = "mathgraph.kernel"
    external_verification: dict[str, Any] | None = None

    def require_terminal(self) -> "Certificate":
        if not isinstance(self.terminal_form, TerminalForm):
            raise TypeError("certificate terminal_form must be a TerminalForm")
        if not self.claim:
            raise ValueError("certificate claim must be non-empty")
        return self

    def has_external_verification(self) -> bool:
        return self.external_verification is not None

    def external_status(self) -> str | None:
        if self.external_verification is None:
            return None
        status = self.external_verification.get("status")
        return str(status) if status is not None else None

    def to_dict(self) -> dict[str, Any]:
        return {
            "terminal_form": self.terminal_form.value,
            "verification_status": _status_for_terminal_form(self.terminal_form).value,
            "claim": self.claim,
            "payload": self.payload,
            "verifier": self.verifier,
            "external_verification": self.external_verification,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Certificate":
        return cls(
            terminal_form=TerminalForm(data["terminal_form"]),
            claim=data["claim"],
            payload=dict(data.get("payload", {})),
            verifier=data.get("verifier", "mathgraph.kernel"),
            external_verification=data.get("external_verification"),
        )


def verified_proof(claim: str, proof_id: str) -> Certificate:
    return Certificate(
        terminal_form=TerminalForm.VERIFIED_PROOF,
        claim=claim,
        payload={"proof_id": proof_id},
    )


def finite_countermodel(claim: str, model: dict[str, Any]) -> Certificate:
    return Certificate(
        terminal_form=TerminalForm.FINITE_COUNTERMODEL,
        claim=claim,
        payload={"model": model},
        verifier="adapters.finite_magma_adapter",
    )


def named_obstruction(claim: str, obstruction_name: str, detail: str = "") -> Certificate:
    return Certificate(
        terminal_form=TerminalForm.NAMED_OBSTRUCTION,
        claim=claim,
        payload={"name": obstruction_name, "detail": detail},
    )


def _status_for_terminal_form(terminal_form: TerminalForm) -> VerificationStatus:
    if terminal_form == TerminalForm.VERIFIED_PROOF:
        return VerificationStatus.VERIFIED
    if terminal_form == TerminalForm.FINITE_COUNTERMODEL:
        return VerificationStatus.REFUTED
    return VerificationStatus.OBSTRUCTED
