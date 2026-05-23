"""Replayable evidence manifest for accepted MathGraph terminal entries."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from mathgraph.certificates import TerminalForm
from mathgraph.hashing import sha256_hex


@dataclass(frozen=True)
class EvidenceManifest:
    claim_id: str
    terminal_form: TerminalForm
    evidence_type: str
    verifier_boundary: str
    artifact_hashes: tuple[str, ...]
    replay_instructions: tuple[str, ...]
    command_contract_hash: str = ""
    witness: dict[str, Any] | None = None
    theorem_name: str = ""
    obstruction_id: str = ""
    provenance: tuple[str, ...] = ()
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self) -> None:
        object.__setattr__(self, "terminal_form", _terminal(self.terminal_form))
        object.__setattr__(self, "artifact_hashes", tuple(str(x) for x in self.artifact_hashes))
        object.__setattr__(self, "replay_instructions", tuple(str(x) for x in self.replay_instructions))
        object.__setattr__(self, "provenance", tuple(str(x) for x in self.provenance))
        validate_evidence_manifest(self)

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "terminal_form": self.terminal_form.value,
            "evidence_type": self.evidence_type,
            "verifier_boundary": self.verifier_boundary,
            "artifact_hashes": list(self.artifact_hashes),
            "command_contract_hash": self.command_contract_hash,
            "witness": dict(self.witness or {}),
            "theorem_name": self.theorem_name,
            "obstruction_id": self.obstruction_id,
            "provenance": list(self.provenance),
            "replay_instructions": list(self.replay_instructions),
            "created_at": self.created_at,
        }

    def stable_hash(self) -> str:
        data = self.to_dict()
        data.pop("created_at", None)
        return sha256_hex(data)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvidenceManifest":
        return cls(
            claim_id=str(data.get("claim_id", "")),
            terminal_form=_terminal(data.get("terminal_form", "")),
            evidence_type=str(data.get("evidence_type", "")),
            verifier_boundary=str(data.get("verifier_boundary", "")),
            artifact_hashes=tuple(data.get("artifact_hashes", ()) or ()),
            command_contract_hash=str(data.get("command_contract_hash", "")),
            witness=dict(data.get("witness", {}) or {}),
            theorem_name=str(data.get("theorem_name", "")),
            obstruction_id=str(data.get("obstruction_id", "")),
            provenance=tuple(data.get("provenance", ()) or ()),
            replay_instructions=tuple(data.get("replay_instructions", ()) or ()),
            created_at=str(data.get("created_at", datetime.now(timezone.utc).isoformat())),
        )


def validate_evidence_manifest(manifest: EvidenceManifest) -> None:
    missing = []
    if not manifest.claim_id:
        missing.append("claim_id")
    if not manifest.evidence_type:
        missing.append("evidence_type")
    if not manifest.verifier_boundary:
        missing.append("verifier_boundary")
    if not manifest.artifact_hashes:
        missing.append("artifact_hashes")
    if not manifest.provenance:
        missing.append("provenance")
    if not manifest.replay_instructions:
        missing.append("replay_instructions")
    if manifest.terminal_form == TerminalForm.FINITE_COUNTERMODEL and not manifest.witness:
        missing.append("witness")
    if manifest.terminal_form == TerminalForm.VERIFIED_PROOF and not manifest.theorem_name:
        missing.append("theorem_name")
    if manifest.terminal_form == TerminalForm.NAMED_OBSTRUCTION and not manifest.obstruction_id:
        missing.append("obstruction_id")
    if missing:
        raise ValueError(f"evidence manifest missing required fields: {', '.join(missing)}")


def _terminal(value: Any) -> TerminalForm:
    if isinstance(value, TerminalForm):
        return value
    return TerminalForm(str(value))
