"""Trace objects returned by kernel routes."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from mathgraph.certificates import Certificate, TerminalForm, VerificationStatus
from mathgraph.verification import verify_certificate


@dataclass
class Trace:
    """A compact route trace for a kernel claim."""

    claim: str
    routes_tried: list[str]
    terminal_form: TerminalForm
    verification_status: VerificationStatus
    source: str | None = None
    target: str | None = None
    certificate: Certificate | None = None
    obstruction: Certificate | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    external_verifications: list[dict[str, Any]] = field(default_factory=list)
    created: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def verify(self) -> bool:
        """Validate the trace terminal form and certificate shape.

        External verification events are audit records only. They do not change
        the terminal form and do not make an obstruction into a proof.
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
            return False

        return False

    def add_external_verification(self, result: dict[str, Any]) -> None:
        self.external_verifications.append(result)

    def is_verified_proof(self) -> bool:
        return (
            self.terminal_form == TerminalForm.VERIFIED_PROOF
            and self.verification_status == VerificationStatus.VERIFIED
            and self.certificate is not None
            and self.verify()
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim": self.claim,
            "source": self.source,
            "target": self.target,
            "routes_tried": list(self.routes_tried),
            "terminal_form": self.terminal_form.value,
            "verification_status": self.verification_status.value,
            "certificate": self.certificate.to_dict() if self.certificate else None,
            "obstruction": self.obstruction.to_dict() if self.obstruction else None,
            "certificate_payload": self.certificate.payload if self.certificate else None,
            "obstruction_payload": self.obstruction.payload if self.obstruction else None,
            "external_verifications": list(self.external_verifications),
            "metadata": dict(self.metadata),
            "created": self.created,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Trace":
        certificate_data = data.get("certificate")
        obstruction_data = data.get("obstruction")
        return cls(
            claim=data["claim"],
            source=data.get("source"),
            target=data.get("target"),
            routes_tried=list(data.get("routes_tried", [])),
            terminal_form=TerminalForm(data["terminal_form"]),
            verification_status=VerificationStatus(data["verification_status"]),
            certificate=Certificate.from_dict(certificate_data) if certificate_data else None,
            obstruction=Certificate.from_dict(obstruction_data) if obstruction_data else None,
            metadata=dict(data.get("metadata", {})),
            external_verifications=list(data.get("external_verifications", [])),
            created=data.get("created") or datetime.now(timezone.utc).isoformat(),
        )
