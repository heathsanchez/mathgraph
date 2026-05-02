"""Placeholder external theorem prover adapter."""

from mathgraph.certificates import Certificate, named_obstruction


def unavailable(claim: str) -> Certificate:
    return named_obstruction(claim, "ETP_ADAPTER_NOT_CONFIGURED")
