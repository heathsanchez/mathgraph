"""Proof digestion and lawbook assimilation candidates.

Proof digestion is a post-verification understanding layer. It may inherit an
already verified proof boundary, but it never creates truth and never verifies a
proof by itself.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from mathgraph.agent_biography import AgentExperience, AgentExperienceOutcome
from mathgraph.alchemy import AlchemicalPhase, AlchemicalStatus, AlchemicalTrace, make_alchemical_trace_id
from mathgraph.certificates import TerminalForm
from mathgraph.continuation_actions import (
    ContinuationActionOutput,
    ContinuationActionStatus,
    ContinuationOutputKind,
    make_continuation_output_id,
)
from mathgraph.hashing import content_id
from mathgraph.lean_adapter import LeanAdapterTrace, extract_lean_imports, extract_lean_theorem_names, lean_adapter_trace_to_proof_verification_trace
from mathgraph.proof_verification import (
    ProofArtifact,
    ProofVerificationTrace,
    make_proof_artifact_id,
)
from mathgraph.projection import ProjectionCandidate, ProjectionRuleKind, make_projection_candidate_id
from mathgraph.verification_episode import VerificationEpisodeTrace


class DigestionStatus(str, Enum):
    UNDIGESTED = "UNDIGESTED"
    DEPENDENCY_MAPPED = "DEPENDENCY_MAPPED"
    ROUTINE_STEPS_SEPARATED = "ROUTINE_STEPS_SEPARATED"
    KEY_IDEA_EXTRACTED = "KEY_IDEA_EXTRACTED"
    REUSABLE_SCHEMA_EXTRACTED = "REUSABLE_SCHEMA_EXTRACTED"
    EXPOSITION_READY = "EXPOSITION_READY"
    TEACHABLE = "TEACHABLE"
    ASSIMILATION_CANDIDATE = "ASSIMILATION_CANDIDATE"
    ASSIMILATED = "ASSIMILATED"
    RESIDUAL = "RESIDUAL"
    ADVISORY_ONLY = "ADVISORY_ONLY"


class DigestionArtifactKind(str, Enum):
    DEPENDENCY_MAP = "DEPENDENCY_MAP"
    STEP_CLASSIFICATION = "STEP_CLASSIFICATION"
    KEY_IDEA_CANDIDATE = "KEY_IDEA_CANDIDATE"
    REUSABLE_SCHEMA_CANDIDATE = "REUSABLE_SCHEMA_CANDIDATE"
    EXPOSITION_NOTE = "EXPOSITION_NOTE"
    FOLLOW_UP_QUESTION = "FOLLOW_UP_QUESTION"
    LAWBOOK_ASSIMILATION_CANDIDATE = "LAWBOOK_ASSIMILATION_CANDIDATE"
    PROJECTION_HINT = "PROJECTION_HINT"
    DIGESTION_METRIC = "DIGESTION_METRIC"
    UNKNOWN = "UNKNOWN"


@dataclass
class ProofDependencyMap:
    dependency_map_id: str
    proof_artifact_id: str | None = None
    certificate_id: str | None = None
    imports: tuple[str, ...] = ()
    theorem_names: tuple[str, ...] = ()
    parent_certificate_ids: tuple[str, ...] = ()
    referenced_artifact_ids: tuple[str, ...] = ()
    raw_dependency_names: tuple[str, ...] = ()
    verified_dependencies: tuple[str, ...] = ()
    unverified_dependencies: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    advisory: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "dependency_map_id": self.dependency_map_id,
            "proof_artifact_id": self.proof_artifact_id,
            "certificate_id": self.certificate_id,
            "imports": list(self.imports),
            "theorem_names": list(self.theorem_names),
            "parent_certificate_ids": list(self.parent_certificate_ids),
            "referenced_artifact_ids": list(self.referenced_artifact_ids),
            "raw_dependency_names": list(self.raw_dependency_names),
            "verified_dependencies": list(self.verified_dependencies),
            "unverified_dependencies": list(self.unverified_dependencies),
            "metadata": dict(self.metadata),
            "advisory": self.advisory,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ProofDependencyMap":
        return cls(
            dependency_map_id=str(data["dependency_map_id"]),
            proof_artifact_id=_optional_str(data.get("proof_artifact_id")),
            certificate_id=_optional_str(data.get("certificate_id")),
            imports=tuple(str(x) for x in data.get("imports", ())),
            theorem_names=tuple(str(x) for x in data.get("theorem_names", ())),
            parent_certificate_ids=tuple(str(x) for x in data.get("parent_certificate_ids", ())),
            referenced_artifact_ids=tuple(str(x) for x in data.get("referenced_artifact_ids", ())),
            raw_dependency_names=tuple(str(x) for x in data.get("raw_dependency_names", ())),
            verified_dependencies=tuple(str(x) for x in data.get("verified_dependencies", ())),
            unverified_dependencies=tuple(str(x) for x in data.get("unverified_dependencies", ())),
            metadata=dict(data.get("metadata", {})),
            advisory=bool(data.get("advisory", True)),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "ProofDependencyMap":
        return cls.from_dict(json.loads(text))


@dataclass
class ProofStepDigest:
    step_digest_id: str
    proof_artifact_id: str | None = None
    step_label: str | None = None
    content_excerpt: str = ""
    classification: str = "unknown"
    confidence: float = 0.0
    reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    advisory: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_digest_id": self.step_digest_id,
            "proof_artifact_id": self.proof_artifact_id,
            "step_label": self.step_label,
            "content_excerpt": self.content_excerpt,
            "classification": self.classification,
            "confidence": self.confidence,
            "reason": self.reason,
            "metadata": dict(self.metadata),
            "advisory": self.advisory,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ProofStepDigest":
        return cls(
            step_digest_id=str(data["step_digest_id"]),
            proof_artifact_id=_optional_str(data.get("proof_artifact_id")),
            step_label=_optional_str(data.get("step_label")),
            content_excerpt=str(data.get("content_excerpt", "")),
            classification=str(data.get("classification", "unknown")),
            confidence=float(data.get("confidence", 0.0) or 0.0),
            reason=_optional_str(data.get("reason")),
            metadata=dict(data.get("metadata", {})),
            advisory=bool(data.get("advisory", True)),
        )


@dataclass
class KeyIdeaCandidate:
    key_idea_id: str
    proof_artifact_id: str | None = None
    certificate_id: str | None = None
    statement: str = ""
    supporting_step_ids: tuple[str, ...] = ()
    novelty_hint: float = 0.0
    reuse_hint: float = 0.0
    compression_hint: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    advisory: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "key_idea_id": self.key_idea_id,
            "proof_artifact_id": self.proof_artifact_id,
            "certificate_id": self.certificate_id,
            "statement": self.statement,
            "supporting_step_ids": list(self.supporting_step_ids),
            "novelty_hint": self.novelty_hint,
            "reuse_hint": self.reuse_hint,
            "compression_hint": self.compression_hint,
            "metadata": dict(self.metadata),
            "advisory": self.advisory,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "KeyIdeaCandidate":
        return cls(
            key_idea_id=str(data["key_idea_id"]),
            proof_artifact_id=_optional_str(data.get("proof_artifact_id")),
            certificate_id=_optional_str(data.get("certificate_id")),
            statement=str(data.get("statement", "")),
            supporting_step_ids=tuple(str(x) for x in data.get("supporting_step_ids", ())),
            novelty_hint=float(data.get("novelty_hint", 0.0) or 0.0),
            reuse_hint=float(data.get("reuse_hint", 0.0) or 0.0),
            compression_hint=float(data.get("compression_hint", 0.0) or 0.0),
            metadata=dict(data.get("metadata", {})),
            advisory=bool(data.get("advisory", True)),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "KeyIdeaCandidate":
        return cls.from_dict(json.loads(text))


@dataclass
class ReusableSchemaCandidate:
    schema_id: str
    proof_artifact_id: str | None = None
    certificate_id: str | None = None
    name: str = ""
    pattern: str = ""
    conditions: tuple[str, ...] = ()
    possible_applications: tuple[str, ...] = ()
    projection_rules: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    advisory: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_id": self.schema_id,
            "proof_artifact_id": self.proof_artifact_id,
            "certificate_id": self.certificate_id,
            "name": self.name,
            "pattern": self.pattern,
            "conditions": list(self.conditions),
            "possible_applications": list(self.possible_applications),
            "projection_rules": list(self.projection_rules),
            "metadata": dict(self.metadata),
            "advisory": self.advisory,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ReusableSchemaCandidate":
        return cls(
            schema_id=str(data["schema_id"]),
            proof_artifact_id=_optional_str(data.get("proof_artifact_id")),
            certificate_id=_optional_str(data.get("certificate_id")),
            name=str(data.get("name", "")),
            pattern=str(data.get("pattern", "")),
            conditions=tuple(str(x) for x in data.get("conditions", ())),
            possible_applications=tuple(str(x) for x in data.get("possible_applications", ())),
            projection_rules=tuple(str(x) for x in data.get("projection_rules", ())),
            metadata=dict(data.get("metadata", {})),
            advisory=bool(data.get("advisory", True)),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "ReusableSchemaCandidate":
        return cls.from_dict(json.loads(text))


@dataclass
class ExpositionNote:
    note_id: str
    proof_artifact_id: str | None = None
    certificate_id: str | None = None
    title: str = ""
    summary: str = ""
    audience: str = "research"
    limitations: tuple[str, ...] = ()
    questions_to_answer: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    advisory: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "note_id": self.note_id,
            "proof_artifact_id": self.proof_artifact_id,
            "certificate_id": self.certificate_id,
            "title": self.title,
            "summary": self.summary,
            "audience": self.audience,
            "limitations": list(self.limitations),
            "questions_to_answer": list(self.questions_to_answer),
            "metadata": dict(self.metadata),
            "advisory": self.advisory,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ExpositionNote":
        return cls(
            note_id=str(data["note_id"]),
            proof_artifact_id=_optional_str(data.get("proof_artifact_id")),
            certificate_id=_optional_str(data.get("certificate_id")),
            title=str(data.get("title", "")),
            summary=str(data.get("summary", "")),
            audience=str(data.get("audience", "research")),
            limitations=tuple(str(x) for x in data.get("limitations", ())),
            questions_to_answer=tuple(str(x) for x in data.get("questions_to_answer", ())),
            metadata=dict(data.get("metadata", {})),
            advisory=bool(data.get("advisory", True)),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "ExpositionNote":
        return cls.from_dict(json.loads(text))


@dataclass
class ProofDigestionTrace:
    trace_id: str
    proof_artifact_ids: tuple[str, ...] = ()
    certificate_ids: tuple[str, ...] = ()
    status: DigestionStatus = DigestionStatus.UNDIGESTED
    dependency_maps: list[ProofDependencyMap] = field(default_factory=list)
    step_digests: list[ProofStepDigest] = field(default_factory=list)
    key_ideas: list[KeyIdeaCandidate] = field(default_factory=list)
    reusable_schemas: list[ReusableSchemaCandidate] = field(default_factory=list)
    exposition_notes: list[ExpositionNote] = field(default_factory=list)
    projection_candidates: list[ProjectionCandidate] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: _now())
    summary: dict[str, Any] = field(default_factory=dict)
    terminal_form: TerminalForm | None = None
    certificate_id: str | None = None
    verifier_boundary_crossed: bool = False
    advisory: bool = True

    def digestion_score(self) -> float:
        if self.summary.get("digestion_score") is not None:
            return float(self.summary["digestion_score"])
        return (
            len(self.dependency_maps) * 0.5
            + len(self.step_digests) * 0.05
            + len(self.key_ideas) * 1.0
            + len(self.reusable_schemas) * 1.0
            + len(self.exposition_notes) * 0.5
            + len(self.projection_candidates) * 0.25
        )

    def is_truth_terminal(self) -> bool:
        return self.terminal_form == TerminalForm.VERIFIED_PROOF and bool(self.certificate_id) and self.verifier_boundary_crossed

    def is_digested(self) -> bool:
        return self.status not in {DigestionStatus.UNDIGESTED, DigestionStatus.RESIDUAL, DigestionStatus.ADVISORY_ONLY}

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "proof_artifact_ids": list(self.proof_artifact_ids),
            "certificate_ids": list(self.certificate_ids),
            "status": self.status.value,
            "dependency_maps": [item.to_dict() for item in self.dependency_maps],
            "step_digests": [item.to_dict() for item in self.step_digests],
            "key_ideas": [item.to_dict() for item in self.key_ideas],
            "reusable_schemas": [item.to_dict() for item in self.reusable_schemas],
            "exposition_notes": [item.to_dict() for item in self.exposition_notes],
            "projection_candidates": [item.to_dict() for item in self.projection_candidates],
            "created_at": self.created_at,
            "summary": dict(self.summary),
            "terminal_form": self.terminal_form.value if self.terminal_form else None,
            "certificate_id": self.certificate_id,
            "verifier_boundary_crossed": self.verifier_boundary_crossed,
            "advisory": self.advisory,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ProofDigestionTrace":
        return cls(
            trace_id=str(data["trace_id"]),
            proof_artifact_ids=tuple(str(x) for x in data.get("proof_artifact_ids", ())),
            certificate_ids=tuple(str(x) for x in data.get("certificate_ids", ())),
            status=DigestionStatus(str(data.get("status", DigestionStatus.UNDIGESTED.value))),
            dependency_maps=[ProofDependencyMap.from_dict(item) for item in data.get("dependency_maps", [])],
            step_digests=[ProofStepDigest.from_dict(item) for item in data.get("step_digests", [])],
            key_ideas=[KeyIdeaCandidate.from_dict(item) for item in data.get("key_ideas", [])],
            reusable_schemas=[ReusableSchemaCandidate.from_dict(item) for item in data.get("reusable_schemas", [])],
            exposition_notes=[ExpositionNote.from_dict(item) for item in data.get("exposition_notes", [])],
            projection_candidates=[ProjectionCandidate.from_dict(item) for item in data.get("projection_candidates", [])],
            created_at=str(data.get("created_at") or _now()),
            summary=dict(data.get("summary", {})),
            terminal_form=_optional_terminal(data.get("terminal_form")),
            certificate_id=_optional_str(data.get("certificate_id")),
            verifier_boundary_crossed=bool(data.get("verifier_boundary_crossed", False)),
            advisory=bool(data.get("advisory", True)),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "ProofDigestionTrace":
        return cls.from_dict(json.loads(text))

    def write_json(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.to_dict(), sort_keys=True, indent=2) + "\n", encoding="utf-8")

    @classmethod
    def read_json(cls, path: str | Path) -> "ProofDigestionTrace":
        return cls.from_json(Path(path).read_text(encoding="utf-8"))

    def write_jsonl(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.to_json() + "\n", encoding="utf-8")

    @classmethod
    def read_jsonl(cls, path: str | Path) -> list["ProofDigestionTrace"]:
        source = Path(path)
        if not source.exists():
            return []
        return [cls.from_json(line) for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]


@dataclass
class LawbookAssimilationCandidate:
    assimilation_id: str
    digestion_trace_id: str
    certificate_id: str | None = None
    recommended_entry_kind: str = "proof_digest"
    key_idea_ids: tuple[str, ...] = ()
    schema_ids: tuple[str, ...] = ()
    dependency_map_ids: tuple[str, ...] = ()
    exposition_note_ids: tuple[str, ...] = ()
    projection_candidate_ids: tuple[str, ...] = ()
    score: float = 0.0
    ready: bool = False
    limitations: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    advisory: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "assimilation_id": self.assimilation_id,
            "digestion_trace_id": self.digestion_trace_id,
            "certificate_id": self.certificate_id,
            "recommended_entry_kind": self.recommended_entry_kind,
            "key_idea_ids": list(self.key_idea_ids),
            "schema_ids": list(self.schema_ids),
            "dependency_map_ids": list(self.dependency_map_ids),
            "exposition_note_ids": list(self.exposition_note_ids),
            "projection_candidate_ids": list(self.projection_candidate_ids),
            "score": self.score,
            "ready": self.ready,
            "limitations": list(self.limitations),
            "metadata": dict(self.metadata),
            "advisory": self.advisory,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "LawbookAssimilationCandidate":
        return cls(
            assimilation_id=str(data["assimilation_id"]),
            digestion_trace_id=str(data["digestion_trace_id"]),
            certificate_id=_optional_str(data.get("certificate_id")),
            recommended_entry_kind=str(data.get("recommended_entry_kind", "proof_digest")),
            key_idea_ids=tuple(str(x) for x in data.get("key_idea_ids", ())),
            schema_ids=tuple(str(x) for x in data.get("schema_ids", ())),
            dependency_map_ids=tuple(str(x) for x in data.get("dependency_map_ids", ())),
            exposition_note_ids=tuple(str(x) for x in data.get("exposition_note_ids", ())),
            projection_candidate_ids=tuple(str(x) for x in data.get("projection_candidate_ids", ())),
            score=float(data.get("score", 0.0) or 0.0),
            ready=bool(data.get("ready", False)),
            limitations=tuple(str(x) for x in data.get("limitations", ())),
            metadata=dict(data.get("metadata", {})),
            advisory=bool(data.get("advisory", True)),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "LawbookAssimilationCandidate":
        return cls.from_dict(json.loads(text))


def extract_dependencies_from_proof_artifact(artifact: ProofArtifact) -> ProofDependencyMap:
    imports = tuple(dict.fromkeys((*artifact.imports, *extract_lean_imports(artifact.content))))
    theorem_names = tuple(dict.fromkeys(tuple(x for x in [artifact.theorem_name] if x) + extract_lean_theorem_names(artifact.content)))
    metadata = dict(artifact.metadata)
    raw_deps = tuple(dict.fromkeys(tuple(artifact.dependencies) + tuple(str(x) for x in metadata.get("dependencies", ()) if x)))
    parent_ids = tuple(str(x) for x in metadata.get("parent_certificate_ids", ()) if x)
    referenced = tuple(str(x) for x in metadata.get("referenced_artifact_ids", ()) if x)
    verified_meta = set(str(x) for x in metadata.get("verified_dependencies", ()) if x)
    verified = tuple(dep for dep in raw_deps if dep in verified_meta)
    unverified = tuple(dep for dep in raw_deps if dep not in verified_meta)
    return ProofDependencyMap(
        dependency_map_id=make_dependency_map_id(artifact.artifact_id, imports, theorem_names, raw_deps, parent_ids),
        proof_artifact_id=artifact.artifact_id,
        certificate_id=_optional_str(metadata.get("certificate_id")),
        imports=imports,
        theorem_names=theorem_names,
        parent_certificate_ids=parent_ids,
        referenced_artifact_ids=referenced,
        raw_dependency_names=raw_deps,
        verified_dependencies=verified,
        unverified_dependencies=unverified,
        metadata={"advisory_only": True, "source": "proof_artifact"},
    )


def classify_proof_steps(artifact: ProofArtifact) -> list[ProofStepDigest]:
    steps: list[ProofStepDigest] = []
    for index, raw_line in enumerate(line for line in artifact.content.splitlines() if line.strip()):
        line = raw_line.strip()
        classification, confidence, reason = _classify_line(line)
        steps.append(
            ProofStepDigest(
                step_digest_id=make_step_digest_id(artifact.artifact_id, index, line, classification),
                proof_artifact_id=artifact.artifact_id,
                step_label=f"line:{index + 1}",
                content_excerpt=line[:240],
                classification=classification,
                confidence=confidence,
                reason=reason,
                metadata={"advisory_only": True, "line_number": index + 1},
            )
        )
    return steps


def extract_key_ideas(artifact: ProofArtifact, step_digests: Sequence[ProofStepDigest]) -> list[KeyIdeaCandidate]:
    ideas: list[KeyIdeaCandidate] = []
    metadata = dict(artifact.metadata)
    for key in ("key_idea", "reason", "proof_strategy"):
        if metadata.get(key):
            statement = str(metadata[key])
            ideas.append(_key_idea(artifact, statement, (), 0.6, 0.5, 0.5, {"source": f"metadata:{key}"}))
    comment_steps = [
        step for step in step_digests
        if step.classification in {"novel", "load_bearing"} and re.search(r"\b(key|main|idea|strategy)\b", step.content_excerpt, re.IGNORECASE)
    ]
    for step in comment_steps[:3]:
        ideas.append(_key_idea(artifact, step.content_excerpt, (step.step_digest_id,), 0.5, 0.4, 0.4, {"source": "step_comment"}))
    if artifact.theorem_name and any(step.classification == "load_bearing" for step in step_digests):
        supporting = tuple(step.step_digest_id for step in step_digests if step.classification == "load_bearing")[:3]
        ideas.append(_key_idea(artifact, f"Load-bearing structure around theorem {artifact.theorem_name}.", supporting, 0.2, 0.4, 0.3, {"source": "theorem_name"}))
    return _dedupe_ideas(ideas)


def extract_reusable_schemas(
    artifact: ProofArtifact,
    dependency_map: ProofDependencyMap,
    key_ideas: Sequence[KeyIdeaCandidate],
) -> list[ReusableSchemaCandidate]:
    schemas: list[ReusableSchemaCandidate] = []
    theorem = artifact.theorem_name or (dependency_map.theorem_names[0] if dependency_map.theorem_names else None)
    if theorem:
        pattern = artifact.target or artifact.source or theorem
        schemas.append(
            ReusableSchemaCandidate(
                schema_id=make_schema_id(artifact.artifact_id, theorem, pattern),
                proof_artifact_id=artifact.artifact_id,
                certificate_id=dependency_map.certificate_id,
                name=f"schema:{theorem}",
                pattern=pattern,
                conditions=tuple(x for x in [artifact.source, "heuristic digestion candidate; requires review"] if x),
                possible_applications=tuple(idea.statement for idea in key_ideas[:2]),
                projection_rules=("ADVISORY_SIMILARITY",),
                metadata={"advisory_only": True, "limitations": ["candidate schema, not proof"]},
            )
        )
    elif key_ideas:
        first = key_ideas[0]
        schemas.append(
            ReusableSchemaCandidate(
                schema_id=make_schema_id(artifact.artifact_id, "key_idea_schema", first.statement),
                proof_artifact_id=artifact.artifact_id,
                certificate_id=dependency_map.certificate_id,
                name="schema:key_idea",
                pattern=first.statement,
                conditions=("heuristic key-idea pattern; requires review",),
                projection_rules=("ADVISORY_SIMILARITY",),
                metadata={"advisory_only": True, "limitations": ["candidate schema, not proof"]},
            )
        )
    return schemas


def make_exposition_note(
    artifact: ProofArtifact,
    dependency_map: ProofDependencyMap | None,
    key_ideas: Sequence[KeyIdeaCandidate],
    schemas: Sequence[ReusableSchemaCandidate],
) -> ExpositionNote:
    theorem = artifact.theorem_name or (dependency_map.theorem_names[0] if dependency_map and dependency_map.theorem_names else artifact.artifact_id)
    summary = f"Digestion note for {theorem}: {len(key_ideas)} key idea candidate(s), {len(schemas)} reusable schema candidate(s)."
    if dependency_map:
        summary += f" Dependencies/imports recorded: {len(dependency_map.raw_dependency_names) + len(dependency_map.imports)}."
    return ExpositionNote(
        note_id=make_exposition_note_id(artifact.artifact_id, theorem, summary),
        proof_artifact_id=artifact.artifact_id,
        certificate_id=dependency_map.certificate_id if dependency_map else None,
        title=f"Digest of {theorem}",
        summary=summary,
        limitations=("Deterministic heuristic digestion; not proof verification.", "Requires human or lawbook-boundary review before assimilation."),
        questions_to_answer=("Which extracted schema is actually reusable?",) if schemas else ("Can this artifact yield a reusable schema?",),
        metadata={"advisory_only": True},
    )


def digest_proof_artifact(
    artifact: ProofArtifact,
    *,
    certificate_id: str | None = None,
    terminal_form: TerminalForm | None = None,
    verifier_boundary_crossed: bool = False,
) -> ProofDigestionTrace:
    inherited_terminal = terminal_form == TerminalForm.VERIFIED_PROOF and bool(certificate_id) and verifier_boundary_crossed
    dep = extract_dependencies_from_proof_artifact(artifact)
    if inherited_terminal:
        dep.certificate_id = certificate_id
    steps = classify_proof_steps(artifact)
    ideas = extract_key_ideas(artifact, steps)
    if inherited_terminal:
        ideas = [KeyIdeaCandidate.from_dict({**idea.to_dict(), "certificate_id": certificate_id}) for idea in ideas]
    schemas = extract_reusable_schemas(artifact, dep, ideas)
    if inherited_terminal:
        schemas = [ReusableSchemaCandidate.from_dict({**schema.to_dict(), "certificate_id": certificate_id}) for schema in schemas]
    note = make_exposition_note(artifact, dep, ideas, schemas)
    if inherited_terminal:
        note = ExpositionNote.from_dict({**note.to_dict(), "certificate_id": certificate_id})
    projections = [_projection_from_schema(artifact, schema, certificate_id if inherited_terminal else None) for schema in schemas]
    status = _digestion_status(dep, steps, ideas, schemas, note, inherited_terminal)
    trace = ProofDigestionTrace(
        trace_id=make_proof_digestion_trace_id(artifact.artifact_id, certificate_id, dep.to_dict(), [step.to_dict() for step in steps]),
        proof_artifact_ids=(artifact.artifact_id,),
        certificate_ids=(certificate_id,) if inherited_terminal and certificate_id else (),
        status=status,
        dependency_maps=[dep],
        step_digests=steps,
        key_ideas=ideas,
        reusable_schemas=schemas,
        exposition_notes=[note],
        projection_candidates=projections,
        terminal_form=TerminalForm.VERIFIED_PROOF if inherited_terminal else None,
        certificate_id=certificate_id if inherited_terminal else None,
        verifier_boundary_crossed=inherited_terminal,
        advisory=True,
    )
    trace.summary.update(_trace_summary(trace))
    return trace


def digest_proof_verification_trace(trace: ProofVerificationTrace) -> list[ProofDigestionTrace]:
    results_by_artifact = {result.artifact_id: result for result in trace.results}
    digests = []
    for artifact in trace.artifacts:
        result = results_by_artifact.get(artifact.artifact_id)
        digests.append(
            digest_proof_artifact(
                artifact,
                certificate_id=result.certificate_id if result and result.is_terminal() else None,
                terminal_form=result.terminal_form if result and result.is_terminal() else None,
                verifier_boundary_crossed=bool(result and result.is_terminal()),
            )
        )
    return digests


def digest_lean_adapter_trace(trace: LeanAdapterTrace) -> list[ProofDigestionTrace]:
    return digest_proof_verification_trace(lean_adapter_trace_to_proof_verification_trace(trace))


def digest_verification_episode_trace(trace: VerificationEpisodeTrace) -> list[ProofDigestionTrace]:
    if trace.proof_verification_trace is None:
        return []
    return digest_proof_verification_trace(trace.proof_verification_trace)


def make_lawbook_assimilation_candidate(digestion_trace: ProofDigestionTrace) -> LawbookAssimilationCandidate:
    useful = bool(digestion_trace.exposition_notes or digestion_trace.reusable_schemas or digestion_trace.key_ideas)
    ready = bool(digestion_trace.certificate_id and digestion_trace.is_truth_terminal() and useful)
    limitations = (
        "Assimilation candidate only; separate lawbook boundary must accept it.",
        "Digestion explains and compresses proof artifacts but does not verify them.",
    )
    if not ready:
        limitations += ("Not ready: missing verified certificate or useful digestion artifact.",)
    candidate = LawbookAssimilationCandidate(
        assimilation_id=make_assimilation_candidate_id(digestion_trace.trace_id, digestion_trace.certificate_id, digestion_trace.digestion_score()),
        digestion_trace_id=digestion_trace.trace_id,
        certificate_id=digestion_trace.certificate_id if ready else digestion_trace.certificate_id,
        key_idea_ids=tuple(idea.key_idea_id for idea in digestion_trace.key_ideas),
        schema_ids=tuple(schema.schema_id for schema in digestion_trace.reusable_schemas),
        dependency_map_ids=tuple(dep.dependency_map_id for dep in digestion_trace.dependency_maps),
        exposition_note_ids=tuple(note.note_id for note in digestion_trace.exposition_notes),
        projection_candidate_ids=tuple(candidate.candidate_id for candidate in digestion_trace.projection_candidates),
        score=digestion_trace.digestion_score(),
        ready=ready,
        limitations=limitations,
        metadata={"advisory_only": True, "lawbook_write_not_performed": True},
    )
    return candidate


def proof_digestion_trace_to_alchemical_trace(trace: ProofDigestionTrace) -> AlchemicalTrace:
    alchemy = AlchemicalTrace(trace_id=make_alchemical_trace_id("proof_digestion", trace.trace_id), claim_id=None, agent_id=None, episode_id=None)
    alchemy.add_step(phase=AlchemicalPhase.RAW_MATTER, status=AlchemicalStatus.SUCCEEDED)
    if trace.dependency_maps or trace.step_digests:
        alchemy.add_step(phase=AlchemicalPhase.DISTILLATION, status=AlchemicalStatus.ADVISORY_ONLY)
    if trace.key_ideas:
        alchemy.add_step(phase=AlchemicalPhase.SUBLIMATION, status=AlchemicalStatus.ADVISORY_ONLY)
    if trace.reusable_schemas:
        alchemy.add_step(phase=AlchemicalPhase.COAGULATION, status=AlchemicalStatus.ADVISORY_ONLY)
    if trace.exposition_notes:
        alchemy.add_step(phase=AlchemicalPhase.CERATION, status=AlchemicalStatus.ADVISORY_ONLY)
    alchemy.add_step(phase=AlchemicalPhase.CONJUNCTION, status=AlchemicalStatus.ADVISORY_ONLY)
    if trace.projection_candidates:
        alchemy.add_step(phase=AlchemicalPhase.PROJECTION, status=AlchemicalStatus.ADVISORY_ONLY)
    if trace.is_truth_terminal():
        alchemy.terminal_form = trace.terminal_form
        alchemy.promoted_certificate_id = trace.certificate_id
        alchemy.add_step(phase=AlchemicalPhase.FIXATION, status=AlchemicalStatus.PROMOTED_BY_VERIFIER, verifier_boundary="INHERITED_PROOF_VERIFICATION")
    return alchemy


def proof_digestion_trace_to_agent_experiences(trace: ProofDigestionTrace, agent_id: str | None = None) -> list[AgentExperience]:
    return [
        AgentExperience(
            experience_id=content_id("proof_digestion_exp", trace.to_dict(), n=24),
            agent_id=agent_id or "proof-digestion",
            episode_id=None,
            claim_id=trace.proof_artifact_ids[0] if trace.proof_artifact_ids else trace.trace_id,
            route="proof_digestion",
            phase=AlchemicalPhase.DISTILLATION.value,
            outcome=AgentExperienceOutcome.VERIFIED_PROOF if trace.is_truth_terminal() else AgentExperienceOutcome.ADVISORY_ONLY,
            terminal_form=trace.terminal_form if trace.is_truth_terminal() else None,
            certificate_id=trace.certificate_id if trace.is_truth_terminal() else None,
            compression_gain=trace.digestion_score(),
            projection_gain=float(len(trace.projection_candidates)),
            verifier_boundary_crossed=trace.is_truth_terminal(),
            metadata={"proof_digestion_trace": trace.to_dict(), "digestion_does_not_verify": True},
        )
    ]


def proof_digestion_trace_to_projection_candidates(trace: ProofDigestionTrace) -> list[ProjectionCandidate]:
    return list(trace.projection_candidates)


def proof_digestion_trace_to_continuation_outputs(trace: ProofDigestionTrace) -> list[ContinuationActionOutput]:
    outputs: list[ContinuationActionOutput] = []
    for idea in trace.key_ideas:
        outputs.append(_continuation_note(trace, ContinuationOutputKind.NOTE, f"Key idea candidate: {idea.statement}", {"key_idea": idea.to_dict()}))
    for schema in trace.reusable_schemas:
        outputs.append(_continuation_note(trace, ContinuationOutputKind.THEOREM_SCHEMA_CANDIDATE, schema.pattern, {"schema": schema.to_dict()}))
    for note in trace.exposition_notes:
        outputs.append(_continuation_note(trace, ContinuationOutputKind.NOTE, note.summary, {"exposition_note": note.to_dict()}))
    outputs.append(_continuation_note(trace, ContinuationOutputKind.TASK, "Follow-up: review proof digestion before lawbook assimilation.", {"task_kind": "proof_digest_review"}))
    return outputs


def make_dependency_map_id(*parts: Any) -> str:
    return content_id("proof_dependency_map", parts, n=24)


def make_step_digest_id(*parts: Any) -> str:
    return content_id("proof_step_digest", parts, n=24)


def make_key_idea_id(*parts: Any) -> str:
    return content_id("key_idea_candidate", parts, n=24)


def make_schema_id(*parts: Any) -> str:
    return content_id("reusable_schema_candidate", parts, n=24)


def make_exposition_note_id(*parts: Any) -> str:
    return content_id("exposition_note", parts, n=24)


def make_proof_digestion_trace_id(*parts: Any) -> str:
    return content_id("proof_digestion_trace", parts, n=24)


def make_assimilation_candidate_id(*parts: Any) -> str:
    return content_id("lawbook_assimilation_candidate", parts, n=24)


def proof_artifact_from_content(content: str, theorem_name: str | None = None) -> ProofArtifact:
    payload = {"content": content, "theorem_name": theorem_name}
    return ProofArtifact(
        artifact_id=make_proof_artifact_id(payload),
        claim_id=None,
        kind=_infer_artifact_kind(content),
        language="lean" if re.search(r"\b(theorem|lemma)\b", content) else None,
        content=content,
        theorem_name=theorem_name or (extract_lean_theorem_names(content)[0] if extract_lean_theorem_names(content) else None),
        imports=extract_lean_imports(content),
        advisory=True,
        metadata={"advisory_only": True, "content_input": True},
    )


def _trace_summary(trace: ProofDigestionTrace) -> dict[str, Any]:
    routine = sum(1 for step in trace.step_digests if step.classification == "routine")
    load_bearing = sum(1 for step in trace.step_digests if step.classification == "load_bearing")
    unknown = sum(1 for step in trace.step_digests if step.classification == "unknown")
    dependency_count = sum(len(dep.raw_dependency_names) + len(dep.imports) for dep in trace.dependency_maps)
    score = trace.digestion_score()
    return {
        "dependency_count": dependency_count,
        "verified_dependency_count": sum(len(dep.verified_dependencies) for dep in trace.dependency_maps),
        "unverified_dependency_count": sum(len(dep.unverified_dependencies) for dep in trace.dependency_maps),
        "step_count": len(trace.step_digests),
        "routine_step_count": routine,
        "load_bearing_step_count": load_bearing,
        "unknown_step_count": unknown,
        "key_idea_count": len(trace.key_ideas),
        "reusable_schema_count": len(trace.reusable_schemas),
        "exposition_note_count": len(trace.exposition_notes),
        "projection_candidate_count": len(trace.projection_candidates),
        "digestion_score": score,
        "advisory_only": not trace.is_truth_terminal(),
    }


def _classify_line(line: str) -> tuple[str, float, str]:
    lower = line.lower()
    if re.match(r"^(import|open|namespace|section)\b", lower):
        return "dependency", 0.7, "import/open/namespace line"
    if re.match(r"^(theorem|lemma)\b", lower):
        return "load_bearing", 0.8, "theorem or lemma declaration"
    if re.search(r"\b(exact|apply|have|suffices|calc)\b", lower):
        return "load_bearing", 0.6, "proof step may carry logical load"
    if re.search(r"\b(simp|ring|omega|norm_num|trivial)\b", lower):
        return "routine", 0.65, "routine tactic or closing step"
    if re.search(r"\b(key|main|idea|strategy)\b", lower):
        return "novel", 0.5, "comment or text mentions key idea"
    if lower.startswith("--") or lower.startswith("/-"):
        return "boilerplate", 0.35, "comment or documentation line"
    return "unknown", 0.2, "no deterministic classification signal"


def _key_idea(
    artifact: ProofArtifact,
    statement: str,
    supporting: Sequence[str],
    novelty: float,
    reuse: float,
    compression: float,
    metadata: Mapping[str, Any],
) -> KeyIdeaCandidate:
    return KeyIdeaCandidate(
        key_idea_id=make_key_idea_id(artifact.artifact_id, statement, list(supporting), metadata),
        proof_artifact_id=artifact.artifact_id,
        certificate_id=_optional_str(artifact.metadata.get("certificate_id")),
        statement=statement,
        supporting_step_ids=tuple(supporting),
        novelty_hint=novelty,
        reuse_hint=reuse,
        compression_hint=compression,
        metadata={**dict(metadata), "advisory_only": True},
    )


def _dedupe_ideas(ideas: Sequence[KeyIdeaCandidate]) -> list[KeyIdeaCandidate]:
    seen: set[str] = set()
    rows: list[KeyIdeaCandidate] = []
    for idea in ideas:
        key = idea.statement.strip()
        if key and key not in seen:
            seen.add(key)
            rows.append(idea)
    return rows


def _projection_from_schema(artifact: ProofArtifact, schema: ReusableSchemaCandidate, certificate_id: str | None) -> ProjectionCandidate:
    verified = bool(certificate_id)
    return ProjectionCandidate(
        candidate_id=make_projection_candidate_id({"schema": schema.to_dict(), "artifact": artifact.artifact_id, "certificate_id": certificate_id}),
        source_claim_id=artifact.claim_id,
        target_claim_id=None,
        source=artifact.source,
        target=artifact.target,
        rule_kind=ProjectionRuleKind.EXACT_KNOWN if verified else ProjectionRuleKind.ADVISORY_SIMILARITY,
        originating_certificate_id=certificate_id if verified else None,
        confidence=0.8 if verified else 0.2,
        advisory=True,
        reason="Proof digestion schema suggests reusable projection pressure.",
        metadata={"advisory_only": True, "digestion_schema_id": schema.schema_id, "projection_hint_not_truth": True},
    )


def _digestion_status(
    dep: ProofDependencyMap,
    steps: Sequence[ProofStepDigest],
    ideas: Sequence[KeyIdeaCandidate],
    schemas: Sequence[ReusableSchemaCandidate],
    note: ExpositionNote | None,
    inherited_terminal: bool,
) -> DigestionStatus:
    if inherited_terminal and (schemas or ideas or note):
        return DigestionStatus.ASSIMILATION_CANDIDATE
    if note:
        return DigestionStatus.EXPOSITION_READY
    if schemas:
        return DigestionStatus.REUSABLE_SCHEMA_EXTRACTED
    if ideas:
        return DigestionStatus.KEY_IDEA_EXTRACTED
    if steps:
        return DigestionStatus.ROUTINE_STEPS_SEPARATED
    if dep:
        return DigestionStatus.DEPENDENCY_MAPPED
    return DigestionStatus.UNDIGESTED


def _continuation_note(
    trace: ProofDigestionTrace,
    kind: ContinuationOutputKind,
    note: str,
    metadata: Mapping[str, Any],
) -> ContinuationActionOutput:
    return ContinuationActionOutput(
        output_id=make_continuation_output_id({"trace": trace.trace_id, "kind": kind.value, "note": note, "metadata": dict(metadata)}),
        action_id="proof_digestion",
        kind=kind,
        status=ContinuationActionStatus.PRODUCED_CANDIDATE if kind != ContinuationOutputKind.TASK else ContinuationActionStatus.PRODUCED_TASK,
        note=note,
        task_payload=dict(metadata) if kind == ContinuationOutputKind.TASK else {},
        metadata={**dict(metadata), "advisory_only": True, "digestion_output_not_truth": True},
    )


def _infer_artifact_kind(content: str):
    from mathgraph.proof_verification import ProofArtifactKind

    if re.search(r"\b(theorem|lemma)\b", content):
        return ProofArtifactKind.LEAN_SKELETON
    return ProofArtifactKind.PROOF_MOTIF


def _optional_str(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value)


def _optional_terminal(value: Any) -> TerminalForm | None:
    if value in (None, ""):
        return None
    return TerminalForm(str(value))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
