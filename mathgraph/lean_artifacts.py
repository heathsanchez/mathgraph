"""Lean skeleton generation for MathGraph proof/countermodel artifacts."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Iterable

from mathgraph.hashing import content_id, sha256_hex


class LeanArtifactKind(str, Enum):
    THEOREM_STATEMENT = "THEOREM_STATEMENT"
    COMPLETE_PROOF = "COMPLETE_PROOF"
    PROOF_SKETCH = "PROOF_SKETCH"
    IMPORT_DECLARATION = "IMPORT_DECLARATION"
    INSTANCE_PROOF = "INSTANCE_PROOF"
    FAMILY_PROOF = "FAMILY_PROOF"
    PROOF_SKELETON = "PROOF_SKELETON"
    COUNTERMODEL_SKELETON = "COUNTERMODEL_SKELETON"
    UNKNOWN = "UNKNOWN"


class LeanVerificationStatus(str, Enum):
    NOT_ATTEMPTED = "NOT_ATTEMPTED"
    LEAN_VERIFIED = "LEAN_VERIFIED"
    LEAN_FAILED = "LEAN_FAILED"
    IMPORTED_VERIFIED = "IMPORTED_VERIFIED"
    IMPORTED_UNCHECKED = "IMPORTED_UNCHECKED"
    GENERATED_UNCHECKED = "GENERATED_UNCHECKED"
    GENERATED = "GENERATED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class LeanArtifact:
    lean_artifact_id: str = ""
    artifact_kind: str | LeanArtifactKind = ""
    name: str = ""
    domain_kernel_id: str = ""
    formal_world_id: str | None = None
    theorem_name: str | None = None
    statement: str | None = None
    proof_text: str | None = None
    verification_status: str | LeanVerificationStatus = LeanVerificationStatus.GENERATED_UNCHECKED
    trust_level: str = "ADVISORY_ROUTE"
    provenance_type: str = "GENERATED"
    source_file: str | None = None
    imports: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)
    line_start: int | None = None
    line_end: int | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    filename: str = ""
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    verified: bool = False
    advisory_only: bool = True
    can_promote_truth: bool = False

    def __post_init__(self) -> None:
        if isinstance(self.artifact_kind, LeanArtifactKind):
            object.__setattr__(self, "artifact_kind", self.artifact_kind.value)
        if isinstance(self.verification_status, LeanVerificationStatus):
            object.__setattr__(self, "verification_status", self.verification_status.value)
        artifact_id = self.lean_artifact_id or make_lean_artifact_id(self.name or self.filename or "lean_artifact", str(self.artifact_kind or "PROOF_SKELETON"))
        object.__setattr__(self, "lean_artifact_id", artifact_id)
        if not self.filename:
            object.__setattr__(self, "filename", f"{_lean_name('artifact', self.name or artifact_id)}.lean")
        if not self.content:
            object.__setattr__(self, "content", render_lean_skeleton(self))
        object.__setattr__(self, "verified", bool(self.verified or self.verification_status in {LeanVerificationStatus.LEAN_VERIFIED.value, LeanVerificationStatus.IMPORTED_VERIFIED.value}))

    @property
    def artifact_id(self) -> str:
        return self.lean_artifact_id

    @property
    def content_hash(self) -> str:
        return sha256_hex(self.content)

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "lean_artifact_id": self.lean_artifact_id,
            "filename": self.filename,
            "artifact_kind": self.artifact_kind,
            "content_hash": self.content_hash,
            "verified": self.verified,
            "advisory_only": True,
            "can_promote_truth": False,
            "name": self.name,
            "theorem_name": self.theorem_name,
            "statement": self.statement,
            "proof_text": self.proof_text,
            "source_file": self.source_file,
            "imports": list(self.imports),
            "depends_on": list(self.depends_on),
            "line_start": self.line_start,
            "line_end": self.line_end,
            "verification_status": self.verification_status,
            "trust_level": self.trust_level,
            "provenance_type": self.provenance_type,
            "metadata": dict(self.metadata),
            "payload": dict(self.payload),
        }

    def is_verified(self) -> bool:
        return bool(self.verified or self.verification_status in {LeanVerificationStatus.LEAN_VERIFIED.value, LeanVerificationStatus.IMPORTED_VERIFIED.value})

    def is_authoritative(self) -> bool:
        return self.is_verified() and self.trust_level in {"LEAN_VERIFIED", "DERIVED_CHAIN_VERIFIED"}

    def summary(self) -> dict[str, Any]:
        return {
            "lean_artifact_id": self.lean_artifact_id,
            "artifact_kind": self.artifact_kind,
            "name": self.name,
            "verification_status": self.verification_status,
            "trust_level": self.trust_level,
            "truth_boundary": True,
            "advisory_only": not self.is_authoritative(),
        }


def make_lean_artifact_id(name: str, artifact_kind: str = "", statement: str | None = None) -> str:
    return content_id("lean-artifact", {"name": name, "artifact_kind": artifact_kind, "statement": statement or ""})


def generate_false_countermodel_lean_skeleton(certificate: Any) -> LeanArtifact:
    data = certificate.to_dict() if hasattr(certificate, "to_dict") else dict(certificate)
    name = _lean_name("finite_countermodel", data.get("cid", "cert"))
    content = "\n".join(
        [
            "-- Generated candidate artifact",
            "-- Not promoted unless verified by Lean",
            f"-- finite countermodel certificate id: {data.get('cid', '')}",
            f"-- source holds globally: {data.get('eq1_holds', False)}",
            f"-- target violated: {data.get('eq2_violated', False)}",
            f"-- witness: {data.get('witness_env', {})}",
            f"theorem {name} : True := by",
            "  trivial",
            "",
        ]
    )
    return LeanArtifact(
        lean_artifact_id=content_id("lean-artifact", content),
        artifact_kind=LeanArtifactKind.COUNTERMODEL_SKELETON,
        name=name,
        filename=f"{name}.lean",
        content=content,
        metadata={"certificate": data},
    )


def generate_true_congruence_lean_skeleton(trace: Any) -> LeanArtifact:
    data = trace.to_dict() if hasattr(trace, "to_dict") else dict(trace)
    name = _lean_name("bounded_congruence", data.get("target_equation", "trace"))
    content = "\n".join(
        [
            "-- Generated candidate artifact",
            "-- Not promoted unless verified by Lean",
            f"-- source equation: {data.get('source_equation', '')}",
            f"-- target equation: {data.get('target_equation', '')}",
            f"-- bounded max depth: {data.get('max_depth', '')}",
            f"-- forced in bounded closure: {data.get('forced_equal', False)}",
            f"theorem {name} : True := by",
            "  trivial",
            "",
        ]
    )
    return LeanArtifact(
        lean_artifact_id=content_id("lean-artifact", content),
        artifact_kind=LeanArtifactKind.PROOF_SKELETON,
        name=name,
        filename=f"{name}.lean",
        content=content,
        metadata={"trace": data},
    )


def write_lean_artifacts(out_dir: str | Path, artifacts: Iterable[LeanArtifact]) -> list[dict[str, Any]]:
    target = Path(out_dir)
    target.mkdir(parents=True, exist_ok=True)
    rows = []
    for artifact in artifacts:
        path = target / artifact.filename
        path.write_text(artifact.content, encoding="utf-8")
        row = artifact.to_dict()
        row["path"] = str(path)
        rows.append(row)
    return rows


def _lean_name(prefix: str, value: Any) -> str:
    slug = "".join(ch.lower() if ch.isalnum() else "_" for ch in str(value))[:48].strip("_") or "artifact"
    return f"mathgraph_{prefix}_{slug}"


def render_lean_skeleton(candidate: Any) -> str:
    name = str(getattr(candidate, "lean_name", "") or getattr(candidate, "name", "") or getattr(candidate, "candidate_name", "") or "mathgraph_candidate")
    statement = str(getattr(candidate, "lean_statement", "") or getattr(candidate, "statement", "") or "True")
    proof_text = getattr(candidate, "proof_text", None)
    if isinstance(candidate, LeanArtifact) and candidate.proof_text:
        proof_text = candidate.proof_text
    body = proof_text or "by\n  trivial"
    return "\n".join(
        [
            "-- Generated candidate artifact; not authoritative unless verified by Lean.",
            "-- MathGraph keeps this advisory until a verifier boundary accepts it.",
            f"theorem {name} : {statement} := {body}",
            "",
        ]
    )
