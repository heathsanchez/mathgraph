"""Verification contract checks for certificates."""

from __future__ import annotations

from mathgraph.certificates import Certificate, TerminalForm


def verify_certificate(certificate: Certificate) -> Certificate:
    certificate.require_terminal()
    payload = certificate.payload

    if certificate.terminal_form == TerminalForm.VERIFIED_PROOF and "proof_id" not in payload:
        raise ValueError("VERIFIED_PROOF certificates require payload['proof_id']")
    if certificate.terminal_form == TerminalForm.FINITE_COUNTERMODEL and "model" not in payload:
        raise ValueError("FINITE_COUNTERMODEL certificates require payload['model']")
    if certificate.terminal_form == TerminalForm.NAMED_OBSTRUCTION and "name" not in payload:
        raise ValueError("NAMED_OBSTRUCTION certificates require payload['name']")

    return certificate
