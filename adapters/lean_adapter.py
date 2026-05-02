"""Placeholder Lean adapter.

Lean build outputs are intentionally not committed to this repository.
"""

from mathgraph.certificates import Certificate, named_obstruction


def unavailable(claim: str) -> Certificate:
    return named_obstruction(claim, "LEAN_ADAPTER_NOT_CONFIGURED")
