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

    def require_terminal(self) -> "Certificate":
        if not isinstance(self.terminal_form, TerminalForm):
            raise TypeError("certificate terminal_form must be a TerminalForm")
        if not self.claim:
            raise ValueError("certificate claim must be non-empty")
        return self


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
