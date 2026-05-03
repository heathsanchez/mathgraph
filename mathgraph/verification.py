"""Verification contract checks for certificates."""

from __future__ import annotations

from typing import Any

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


def verify_external_artifact(kind: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Dispatch a small external artifact verification request.

    Adapter results are not MathGraph terminal forms by themselves.
    """

    if kind == "lean_file":
        from adapters.lean_adapter import verify_lean_file

        return verify_lean_file(payload.get("path"), timeout_sec=payload.get("timeout_sec", 30))

    if kind == "lean_code":
        from adapters.lean_adapter import verify_lean_code

        return verify_lean_code(payload.get("code", ""), timeout_sec=payload.get("timeout_sec", 30))

    return {
        "status": "unknown_verification_adapter",
        "kind": kind,
        "payload_keys": sorted(payload.keys()),
    }
