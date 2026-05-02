"""Small invariant helpers for kernel objects."""

from __future__ import annotations

from mathgraph.certificates import Certificate
from mathgraph.verification import verify_certificate


def has_terminal_form(certificate: Certificate) -> bool:
    try:
        verify_certificate(certificate)
    except (TypeError, ValueError):
        return False
    return True
