"""Ephemeral ledger helpers.

Persistent ledgers and run directories are intentionally excluded from git.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from mathgraph.certificates import Certificate


@dataclass
class Ledger:
    entries: list[Certificate] = field(default_factory=list)

    def append(self, certificate: Certificate) -> Certificate:
        self.entries.append(certificate)
        return certificate
