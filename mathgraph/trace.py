"""Trace objects returned by kernel routes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mathgraph.certificates import Certificate, TerminalForm, VerificationStatus
from mathgraph.verification import verify_certificate


@dataclass(frozen=True)
class Trace:
    """A compact route trace for a kernel claim."""

    claim: str
    routes_tried: list[str]
    terminal_form: TerminalForm
    verification_status: VerificationStatus
    certificate: Certificate | None = None
    obstruction: Certificate | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def verify(self) -> bool:
        """Validate the trace terminal form and certificate shape.

        A valid obstruction trace returns ``True`` here because the trace is
        well-formed. Use ``is_verified_proof`` when asking whether the claim has
        been proved.
        """

        if self.terminal_form == TerminalForm.VERIFIED_PROOF:
            if self.verification_status != VerificationStatus.VERIFIED or self.certificate is None:
                return False
            return verify_certificate(self.certificate).terminal_form == self.terminal_form

        if self.terminal_form == TerminalForm.FINITE_COUNTERMODEL:
            if self.verification_status != VerificationStatus.REFUTED or self.certificate is None:
                return False
            return verify_certificate(self.certificate).terminal_form == self.terminal_form

        if self.terminal_form == TerminalForm.NAMED_OBSTRUCTION:
            if self.verification_status != VerificationStatus.OBSTRUCTED or self.obstruction is None:
                return False
            return verify_certificate(self.obstruction).terminal_form == self.terminal_form

        return False

    def is_verified_proof(self) -> bool:
        return (
            self.terminal_form == TerminalForm.VERIFIED_PROOF
            and self.verification_status == VerificationStatus.VERIFIED
            and self.certificate is not None
            and self.verify()
        )
