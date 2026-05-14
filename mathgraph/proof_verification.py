"""TRUE-side proof artifact lifecycle and verifier-boundary scaffold."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from mathgraph.agent_biography import AgentExperience, AgentExperienceOutcome
from mathgraph.alchemy import AlchemicalPhase, AlchemicalStatus, AlchemicalTrace, make_alchemical_trace_id
from mathgraph.certificates import TerminalForm
from mathgraph.hashing import content_id
from mathgraph.lemma_candidates import canonical_lemma_name
from mathgraph.projection import ProjectionCandidate, ProjectionRuleKind, make_projection_candidate_id


class ProofArtifactKind(str, Enum):
    PROOF_MOTIF = "PROOF_MOTIF"
    LEMMA_CANDIDATE = "LEMMA_CANDIDATE"
    CUT_CANDIDATE = "CUT_CANDIDATE"
    LEAN_SKELETON = "LEAN_SKELETON"
    LEAN_FILE = "LEAN_FILE"
    ISABELLE_SKELETON = "ISABELLE_SKELETON"
    THEOREM_SCHEMA = "THEOREM_SCHEMA"
    IMPORTED_PROOF = "IMPORTED_PROOF"
    CHAIN_AUDIT = "CHAIN_AUDIT"
    UNKNOWN = "UNKNOWN"


class ProofVerificationStatus(str, Enum):
    DRAFT = "DRAFT"
    SKELETON_GENERATED = "SKELETON_GENERATED"
    VERIFIER_NOT_RUN = "VERIFIER_NOT_RUN"
    VERIFIER_PASSED = "VERIFIER_PASSED"
    VERIFIER_FAILED = "VERIFIER_FAILED"
    IMPORTED_VERIFIED = "IMPORTED_VERIFIED"
    CHAIN_AUDITED = "CHAIN_AUDITED"
    REJECTED = "REJECTED"
    RESIDUAL = "RESIDUAL"
    ADVISORY_ONLY = "ADVISORY_ONLY"


class ProofVerifierKind(str, Enum):
    NONE = "NONE"
    LEAN = "LEAN"
    ISABELLE = "ISABELLE"
    ROQC = "ROQC"
    COQ = "COQ"
    CHAIN_AUDITOR = "CHAIN_AUDITOR"
    TRUSTED_IMPORTER = "TRUSTED_IMPORTER"
    MOCK_VERIFIER = "MOCK_VERIFIER"


@dataclass
class ProofArtifact:
    artifact_id: str
    claim_id: str | None
    source: str | None = None
    target: str | None = None
    kind: ProofArtifactKind = ProofArtifactKind.UNKNOWN
    language: str | None = None
    content: str = ""
    file_path: str | None = None
    theorem_name: str | None = None
    imports: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    advisory: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "claim_id": self.claim_id,
            "source": self.source,
            "target": self.target,
            "kind": self.kind.value,
            "language": self.language,
            "content": self.content,
            "file_path": self.file_path,
            "theorem_name": self.theorem_name,
            "imports": list(self.imports),
            "dependencies": list(self.dependencies),
            "advisory": self.advisory,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ProofArtifact":
        return cls(
            artifact_id=str(data["artifact_id"]),
            claim_id=_optional_str(data.get("claim_id")),
            source=_optional_str(data.get("source")),
            target=_optional_str(data.get("target")),
            kind=ProofArtifactKind(str(data.get("kind", ProofArtifactKind.UNKNOWN.value))),
            language=_optional_str(data.get("language")),
            content=str(data.get("content", "")),
            file_path=_optional_str(data.get("file_path")),
            theorem_name=_optional_str(data.get("theorem_name")),
            imports=tuple(str(x) for x in data.get("imports", ())),
            dependencies=tuple(str(x) for x in data.get("dependencies", ())),
            advisory=bool(data.get("advisory", True)),
            metadata=dict(data.get("metadata", {})),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "ProofArtifact":
        return cls.from_dict(json.loads(text))

    def to_jsonl_line(self) -> str:
        return self.to_json() + "\n"

    @classmethod
    def from_jsonl_line(cls, line: str) -> "ProofArtifact":
        return cls.from_json(line.strip())


@dataclass
class ProofVerificationResult:
    result_id: str
    artifact_id: str
    status: ProofVerificationStatus
    verifier_kind: ProofVerifierKind = ProofVerifierKind.NONE
    terminal_form: TerminalForm | None = None
    certificate_id: str | None = None
    verifier_boundary_crossed: bool = False
    command: tuple[str, ...] = ()
    return_code: int | None = None
    stdout_excerpt: str = ""
    stderr_excerpt: str = ""
    checked_at: str | None = None
    failure_reason: str | None = None
    residual_delta: int = 0
    compression_gain: float = 0.0
    projection_gain: float = 0.0
    advisory_notes: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_terminal(self) -> bool:
        return (
            self.terminal_form == TerminalForm.VERIFIED_PROOF
            and bool(self.certificate_id)
            and self.verifier_boundary_crossed
            and self.status
            in {
                ProofVerificationStatus.VERIFIER_PASSED,
                ProofVerificationStatus.IMPORTED_VERIFIED,
                ProofVerificationStatus.CHAIN_AUDITED,
            }
        )

    def is_advisory(self) -> bool:
        return not self.is_terminal()

    def to_dict(self) -> dict[str, Any]:
        return {
            "result_id": self.result_id,
            "artifact_id": self.artifact_id,
            "status": self.status.value,
            "verifier_kind": self.verifier_kind.value,
            "terminal_form": self.terminal_form.value if self.terminal_form else None,
            "certificate_id": self.certificate_id,
            "verifier_boundary_crossed": self.verifier_boundary_crossed,
            "command": list(self.command),
            "return_code": self.return_code,
            "stdout_excerpt": self.stdout_excerpt,
            "stderr_excerpt": self.stderr_excerpt,
            "checked_at": self.checked_at,
            "failure_reason": self.failure_reason,
            "residual_delta": self.residual_delta,
            "compression_gain": self.compression_gain,
            "projection_gain": self.projection_gain,
            "advisory_notes": list(self.advisory_notes),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ProofVerificationResult":
        return cls(
            result_id=str(data["result_id"]),
            artifact_id=str(data["artifact_id"]),
            status=ProofVerificationStatus(str(data["status"])),
            verifier_kind=ProofVerifierKind(str(data.get("verifier_kind", ProofVerifierKind.NONE.value))),
            terminal_form=_optional_terminal_form(data.get("terminal_form")),
            certificate_id=_optional_str(data.get("certificate_id")),
            verifier_boundary_crossed=bool(data.get("verifier_boundary_crossed", False)),
            command=tuple(str(x) for x in data.get("command", ())),
            return_code=_optional_int(data.get("return_code")),
            stdout_excerpt=str(data.get("stdout_excerpt", "")),
            stderr_excerpt=str(data.get("stderr_excerpt", "")),
            checked_at=_optional_str(data.get("checked_at")),
            failure_reason=_optional_str(data.get("failure_reason")),
            residual_delta=int(data.get("residual_delta", 0) or 0),
            compression_gain=float(data.get("compression_gain", 0.0) or 0.0),
            projection_gain=float(data.get("projection_gain", 0.0) or 0.0),
            advisory_notes=tuple(str(x) for x in data.get("advisory_notes", ())),
            metadata=dict(data.get("metadata", {})),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "ProofVerificationResult":
        return cls.from_dict(json.loads(text))

    def to_jsonl_line(self) -> str:
        return self.to_json() + "\n"

    @classmethod
    def from_jsonl_line(cls, line: str) -> "ProofVerificationResult":
        return cls.from_json(line.strip())


@dataclass
class ProofVerificationTrace:
    trace_id: str
    episode_id: str | None
    agent_id: str | None
    artifacts: list[ProofArtifact] = field(default_factory=list)
    results: list[ProofVerificationResult] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    summary: dict[str, Any] = field(default_factory=dict)

    def terminal_count(self) -> int:
        return sum(1 for result in self.results if result.is_terminal())

    def advisory_count(self) -> int:
        return sum(1 for result in self.results if result.is_advisory())

    def failed_count(self) -> int:
        return sum(1 for result in self.results if result.status == ProofVerificationStatus.VERIFIER_FAILED)

    def residual_delta_total(self) -> int:
        return sum(result.residual_delta for result in self.results)

    def compression_gain_total(self) -> float:
        return sum(result.compression_gain for result in self.results)

    def projection_gain_total(self) -> float:
        return sum(result.projection_gain for result in self.results)

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "episode_id": self.episode_id,
            "agent_id": self.agent_id,
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
            "results": [result.to_dict() for result in self.results],
            "created_at": self.created_at,
            "summary": dict(self.summary),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ProofVerificationTrace":
        return cls(
            trace_id=str(data["trace_id"]),
            episode_id=_optional_str(data.get("episode_id")),
            agent_id=_optional_str(data.get("agent_id")),
            artifacts=[ProofArtifact.from_dict(item) for item in data.get("artifacts", [])],
            results=[ProofVerificationResult.from_dict(item) for item in data.get("results", [])],
            created_at=str(data.get("created_at") or datetime.now(timezone.utc).isoformat()),
            summary=dict(data.get("summary", {})),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "ProofVerificationTrace":
        return cls.from_dict(json.loads(text))

    def write_json(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.to_dict(), sort_keys=True, indent=2) + "\n", encoding="utf-8")

    @classmethod
    def read_json(cls, path: str | Path) -> "ProofVerificationTrace":
        return cls.from_json(Path(path).read_text(encoding="utf-8"))

    def write_jsonl(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.to_json() + "\n", encoding="utf-8")

    @classmethod
    def read_jsonl(cls, path: str | Path) -> list["ProofVerificationTrace"]:
        if not Path(path).exists():
            return []
        traces: list[ProofVerificationTrace] = []
        with Path(path).open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    traces.append(cls.from_json(line))
        return traces


def make_lean_skeleton(
    *,
    claim_id: str | None,
    source: str | None,
    target: str | None,
    theorem_name: str | None = None,
    imports: Sequence[str] = (),
    body: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> ProofArtifact:
    name = theorem_name or canonical_lemma_name("mathgraph", claim_id, "true_side")
    import_lines = "\n".join(f"import {item}" for item in imports)
    comment = f"/- Source: {source or 'unknown'}\nTarget: {target or 'unknown'}\nThis skeleton is advisory until checked by Lean. -/"
    proof_body = body or "by\n  trivial"
    content = "\n".join(part for part in [import_lines, "", comment, f"theorem {name} : True := {proof_body}", ""] if part != "")
    payload = {
        "claim_id": claim_id,
        "source": source,
        "target": target,
        "theorem_name": name,
        "imports": list(imports),
        "content": content,
        "metadata": dict(metadata or {}),
    }
    return ProofArtifact(
        artifact_id=make_proof_artifact_id(payload),
        claim_id=claim_id,
        source=source,
        target=target,
        kind=ProofArtifactKind.LEAN_SKELETON,
        language="lean",
        content=content,
        theorem_name=name,
        imports=tuple(imports),
        advisory=True,
        metadata={**dict(metadata or {}), "advisory_only": True, "source_target_not_encoded": bool(source or target)},
    )


def make_lemma_candidate(**kwargs: Any) -> ProofArtifact:
    return _simple_artifact(ProofArtifactKind.LEMMA_CANDIDATE, **kwargs)


def make_cut_candidate(**kwargs: Any) -> ProofArtifact:
    return _simple_artifact(ProofArtifactKind.CUT_CANDIDATE, **kwargs)


def make_theorem_schema(**kwargs: Any) -> ProofArtifact:
    return _simple_artifact(ProofArtifactKind.THEOREM_SCHEMA, **kwargs)


def run_proof_verifier(
    artifact: ProofArtifact,
    *,
    verifier_kind: ProofVerifierKind = ProofVerifierKind.NONE,
    command: Sequence[str] | None = None,
    timeout_seconds: float = 10.0,
    allow_mock_verifier: bool = False,
) -> ProofVerificationResult:
    verifier_kind = _verifier_kind(verifier_kind)
    if verifier_kind == ProofVerifierKind.NONE:
        return _not_run_result(artifact, verifier_kind, "verifier kind NONE")
    if verifier_kind == ProofVerifierKind.MOCK_VERIFIER:
        if allow_mock_verifier and artifact.metadata.get("test_only") is True:
            return _passed_result(artifact, verifier_kind, ("mock-verifier",), 0, "", "", {"test_only": True})
        return _rejected_result(artifact, verifier_kind, "mock verifier requires allow_mock_verifier and artifact metadata test_only=True")
    cmd = tuple(command or ())
    if verifier_kind == ProofVerifierKind.LEAN and not cmd:
        if artifact.file_path:
            cmd = ("lean", artifact.file_path)
        else:
            return _not_run_result(artifact, verifier_kind, "Lean command missing and artifact has no file_path")
    if not cmd:
        return _not_run_result(artifact, verifier_kind, "verifier command missing")
    try:
        completed = subprocess.run(
            list(cmd),
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except Exception as exc:
        return _failed_result(artifact, verifier_kind, cmd, None, "", str(exc), str(exc))
    if completed.returncode == 0:
        return _passed_result(
            artifact,
            verifier_kind,
            cmd,
            completed.returncode,
            completed.stdout,
            completed.stderr,
            {"test_only": False},
        )
    return _failed_result(
        artifact,
        verifier_kind,
        cmd,
        completed.returncode,
        completed.stdout,
        completed.stderr,
        "verifier command returned non-zero",
    )


def import_verified_proof(
    *,
    artifact: ProofArtifact,
    verifier_kind: ProofVerifierKind = ProofVerifierKind.TRUSTED_IMPORTER,
    external_certificate_id: str | None = None,
    provenance: Mapping[str, Any] | None = None,
) -> ProofVerificationResult:
    provenance_data = dict(provenance or {})
    verified = provenance_data.get("verified") is True or bool(external_certificate_id)
    if not verified:
        return _rejected_result(artifact, _verifier_kind(verifier_kind), "trusted import requires external certificate or verified provenance")
    certificate_id = external_certificate_id or content_id("imported_proof", {"artifact": artifact.to_dict(), "provenance": provenance_data}, n=24)
    return ProofVerificationResult(
        result_id=make_proof_result_id(artifact.artifact_id, "imported_verified", certificate_id),
        artifact_id=artifact.artifact_id,
        status=ProofVerificationStatus.IMPORTED_VERIFIED,
        verifier_kind=_verifier_kind(verifier_kind),
        terminal_form=TerminalForm.VERIFIED_PROOF,
        certificate_id=certificate_id,
        verifier_boundary_crossed=True,
        checked_at=_now(),
        compression_gain=1.0,
        projection_gain=1.0,
        advisory_notes=("trusted importer marked proof verified",),
        metadata={"provenance": provenance_data, "external_certificate_id": external_certificate_id},
    )


def chain_audit_proof(
    *,
    artifact: ProofArtifact,
    parent_certificate_ids: Sequence[str],
    audit_rule: str,
    audit_metadata: Mapping[str, Any] | None = None,
) -> ProofVerificationResult:
    metadata = dict(audit_metadata or {})
    if parent_certificate_ids and audit_rule and metadata.get("chain_safe") is True:
        certificate_id = content_id(
            "chain_audited_proof",
            {"artifact": artifact.to_dict(), "parents": list(parent_certificate_ids), "audit_rule": audit_rule, "metadata": metadata},
            n=24,
        )
        return ProofVerificationResult(
            result_id=make_proof_result_id(artifact.artifact_id, "chain_audited", certificate_id),
            artifact_id=artifact.artifact_id,
            status=ProofVerificationStatus.CHAIN_AUDITED,
            verifier_kind=ProofVerifierKind.CHAIN_AUDITOR,
            terminal_form=TerminalForm.VERIFIED_PROOF,
            certificate_id=certificate_id,
            verifier_boundary_crossed=True,
            checked_at=_now(),
            compression_gain=1.0,
            projection_gain=1.0,
            advisory_notes=("chain auditor accepted explicit chain_safe proof rule",),
            metadata={"parent_certificate_ids": list(parent_certificate_ids), "audit_rule": audit_rule, **metadata},
        )
    return ProofVerificationResult(
        result_id=make_proof_result_id(artifact.artifact_id, "chain_audit_residual", list(parent_certificate_ids), audit_rule),
        artifact_id=artifact.artifact_id,
        status=ProofVerificationStatus.RESIDUAL,
        verifier_kind=ProofVerifierKind.CHAIN_AUDITOR,
        failure_reason="chain audit requires parent certificate ids, audit rule, and chain_safe=True metadata",
        advisory_notes=("chain audit did not cross verifier boundary",),
        metadata={"parent_certificate_ids": list(parent_certificate_ids), "audit_rule": audit_rule, **metadata},
    )


def run_proof_verification_pipeline(
    *,
    artifacts: Sequence[ProofArtifact] = (),
    agent_id: str | None = None,
    episode_id: str | None = None,
    verifier_kind: ProofVerifierKind = ProofVerifierKind.NONE,
    command: Sequence[str] | None = None,
    timeout_seconds: float = 10.0,
    allow_mock_verifier: bool = False,
    max_artifacts: int | None = None,
) -> ProofVerificationTrace:
    selected = list(artifacts)[:max_artifacts] if max_artifacts is not None else list(artifacts)
    results = [
        run_proof_verifier(
            artifact,
            verifier_kind=verifier_kind,
            command=command,
            timeout_seconds=timeout_seconds,
            allow_mock_verifier=allow_mock_verifier,
        )
        for artifact in selected
    ]
    trace = ProofVerificationTrace(
        trace_id=make_proof_trace_id(episode_id, agent_id, [artifact.to_dict() for artifact in selected]),
        episode_id=episode_id,
        agent_id=agent_id,
        artifacts=selected,
        results=results,
    )
    trace.summary.update(_summary(trace))
    return trace


def proof_verification_trace_to_alchemical_trace(trace: ProofVerificationTrace) -> AlchemicalTrace:
    alchemical = AlchemicalTrace(
        trace_id=make_alchemical_trace_id("proof_verification", trace.trace_id),
        agent_id=trace.agent_id,
        episode_id=trace.episode_id,
    )
    alchemical.add_step(phase=AlchemicalPhase.RAW_MATTER, status=AlchemicalStatus.SUCCEEDED)
    if any(artifact.kind in {ProofArtifactKind.PROOF_MOTIF, ProofArtifactKind.LEMMA_CANDIDATE, ProofArtifactKind.CUT_CANDIDATE, ProofArtifactKind.THEOREM_SCHEMA} for artifact in trace.artifacts):
        alchemical.add_step(phase=AlchemicalPhase.SUBLIMATION, status=AlchemicalStatus.ADVISORY_ONLY)
    if any(artifact.kind in {ProofArtifactKind.LEAN_SKELETON, ProofArtifactKind.LEAN_FILE, ProofArtifactKind.ISABELLE_SKELETON} for artifact in trace.artifacts):
        alchemical.add_step(phase=AlchemicalPhase.DESCENSION, status=AlchemicalStatus.ADVISORY_ONLY)
    alchemical.add_step(
        phase=AlchemicalPhase.DISTILLATION,
        status=AlchemicalStatus.SUCCEEDED if trace.results else AlchemicalStatus.ADVISORY_ONLY,
        residual_delta=trace.residual_delta_total(),
        compression_gain=trace.compression_gain_total(),
    )
    terminals = [result for result in trace.results if result.is_terminal()]
    if terminals:
        first = terminals[0]
        alchemical.terminal_form = first.terminal_form
        alchemical.promoted_certificate_id = first.certificate_id
        alchemical.add_step(phase=AlchemicalPhase.FIXATION, status=AlchemicalStatus.PROMOTED_BY_VERIFIER, verifier_boundary=first.verifier_kind.value)
        alchemical.add_step(phase=AlchemicalPhase.CERATION, status=AlchemicalStatus.SUCCEEDED)
        alchemical.add_step(phase=AlchemicalPhase.PROJECTION, status=AlchemicalStatus.SUCCEEDED, compression_gain=trace.compression_gain_total())
    return alchemical


def proof_verification_trace_to_agent_experiences(trace: ProofVerificationTrace) -> list[AgentExperience]:
    agent_id = trace.agent_id or "proof-verification"
    artifacts = {artifact.artifact_id: artifact for artifact in trace.artifacts}
    experiences: list[AgentExperience] = []
    for result in trace.results:
        artifact = artifacts.get(result.artifact_id)
        experiences.append(
            AgentExperience(
                experience_id=content_id("proof_exp", result.to_dict(), n=24),
                agent_id=agent_id,
                episode_id=trace.episode_id,
                claim_id=artifact.claim_id if artifact else result.artifact_id,
                route=f"proof_verification:{result.verifier_kind.value.lower()}",
                phase=AlchemicalPhase.DISTILLATION.value,
                outcome=_experience_outcome(result),
                terminal_form=result.terminal_form if result.is_terminal() else None,
                certificate_id=result.certificate_id if result.is_terminal() else None,
                residual_delta=result.residual_delta,
                compression_gain=result.compression_gain,
                projection_gain=result.projection_gain,
                verifier_boundary_crossed=result.is_terminal(),
                scar_tags=("proof_verifier_failed",) if result.status == ProofVerificationStatus.VERIFIER_FAILED else (),
                metadata={"proof_verification_result": result.to_dict(), "boundary_preserved": True},
            )
        )
    return experiences


def proof_verification_trace_to_projection_candidates(trace: ProofVerificationTrace) -> list[ProjectionCandidate]:
    artifacts = {artifact.artifact_id: artifact for artifact in trace.artifacts}
    candidates: list[ProjectionCandidate] = []
    for result in trace.results:
        artifact = artifacts.get(result.artifact_id)
        if artifact is None:
            continue
        verified = result.is_terminal()
        payload = {"artifact_id": artifact.artifact_id, "result_id": result.result_id, "verified": verified}
        candidates.append(
            ProjectionCandidate(
                candidate_id=make_projection_candidate_id(payload),
                source_claim_id=artifact.claim_id,
                target_claim_id=None,
                source=artifact.source,
                target=artifact.target,
                rule_kind=ProjectionRuleKind.EXACT_KNOWN if verified else ProjectionRuleKind.ADVISORY_SIMILARITY,
                originating_certificate_id=result.certificate_id if verified else None,
                confidence=1.0 if verified else 0.1,
                advisory=not verified,
                reason="Verified proof can feed projection." if verified else "Unverified proof artifact is advisory projection pressure only.",
                metadata={"proof_result": result.to_dict(), "advisory_only": not verified},
            )
        )
    return candidates


def make_proof_artifact_id(payload: Mapping[str, Any]) -> str:
    return content_id("proof_artifact", payload, n=24)


def make_proof_result_id(*parts: Any) -> str:
    return content_id("proof_result", parts, n=24)


def make_proof_trace_id(*parts: Any) -> str:
    return content_id("proof_trace", parts, n=24)


def _simple_artifact(kind: ProofArtifactKind, **kwargs: Any) -> ProofArtifact:
    claim_id = _optional_str(kwargs.get("claim_id"))
    source = _optional_str(kwargs.get("source"))
    target = _optional_str(kwargs.get("target"))
    theorem_name = _optional_str(kwargs.get("theorem_name")) or canonical_lemma_name(kind.value.lower(), claim_id)
    content = str(kwargs.get("content") or kwargs.get("statement") or "")
    metadata = dict(kwargs.get("metadata") or {})
    payload = {"claim_id": claim_id, "source": source, "target": target, "kind": kind.value, "theorem_name": theorem_name, "content": content, "metadata": metadata}
    return ProofArtifact(
        artifact_id=make_proof_artifact_id(payload),
        claim_id=claim_id,
        source=source,
        target=target,
        kind=kind,
        language=_optional_str(kwargs.get("language")),
        content=content,
        theorem_name=theorem_name,
        advisory=True,
        metadata={**metadata, "advisory_only": True},
    )


def _not_run_result(artifact: ProofArtifact, verifier_kind: ProofVerifierKind, reason: str) -> ProofVerificationResult:
    return ProofVerificationResult(
        result_id=make_proof_result_id(artifact.artifact_id, verifier_kind.value, "not_run", reason),
        artifact_id=artifact.artifact_id,
        status=ProofVerificationStatus.VERIFIER_NOT_RUN,
        verifier_kind=verifier_kind,
        failure_reason=reason,
        advisory_notes=("verifier not run", "not terminal truth"),
        metadata={"artifact_kind": artifact.kind.value, "advisory_only": True},
    )


def _rejected_result(artifact: ProofArtifact, verifier_kind: ProofVerifierKind, reason: str) -> ProofVerificationResult:
    return ProofVerificationResult(
        result_id=make_proof_result_id(artifact.artifact_id, verifier_kind.value, "rejected", reason),
        artifact_id=artifact.artifact_id,
        status=ProofVerificationStatus.REJECTED,
        verifier_kind=verifier_kind,
        failure_reason=reason,
        advisory_notes=("proof artifact rejected", "not terminal truth"),
        metadata={"artifact_kind": artifact.kind.value, "advisory_only": True},
    )


def _passed_result(
    artifact: ProofArtifact,
    verifier_kind: ProofVerifierKind,
    command: Sequence[str],
    return_code: int | None,
    stdout: str,
    stderr: str,
    metadata: Mapping[str, Any],
) -> ProofVerificationResult:
    certificate_id = content_id("verified_proof", {"artifact": artifact.to_dict(), "verifier": verifier_kind.value, "command": list(command)}, n=24)
    return ProofVerificationResult(
        result_id=make_proof_result_id(artifact.artifact_id, verifier_kind.value, "passed", certificate_id),
        artifact_id=artifact.artifact_id,
        status=ProofVerificationStatus.VERIFIER_PASSED,
        verifier_kind=verifier_kind,
        terminal_form=TerminalForm.VERIFIED_PROOF,
        certificate_id=certificate_id,
        verifier_boundary_crossed=True,
        command=tuple(command),
        return_code=return_code,
        stdout_excerpt=_excerpt(stdout),
        stderr_excerpt=_excerpt(stderr),
        checked_at=_now(),
        compression_gain=1.0,
        projection_gain=1.0,
        advisory_notes=("verifier command passed",),
        metadata=dict(metadata),
    )


def _failed_result(
    artifact: ProofArtifact,
    verifier_kind: ProofVerifierKind,
    command: Sequence[str],
    return_code: int | None,
    stdout: str,
    stderr: str,
    reason: str,
) -> ProofVerificationResult:
    return ProofVerificationResult(
        result_id=make_proof_result_id(artifact.artifact_id, verifier_kind.value, "failed", return_code, reason),
        artifact_id=artifact.artifact_id,
        status=ProofVerificationStatus.VERIFIER_FAILED,
        verifier_kind=verifier_kind,
        command=tuple(command),
        return_code=return_code,
        stdout_excerpt=_excerpt(stdout),
        stderr_excerpt=_excerpt(stderr),
        checked_at=_now(),
        failure_reason=reason,
        residual_delta=1,
        advisory_notes=("verifier failed", "failure is residual/advisory, not truth"),
        metadata={"advisory_only": True},
    )


def _summary(trace: ProofVerificationTrace) -> dict[str, Any]:
    return {
        "artifacts_total": len(trace.artifacts),
        "terminal_results": trace.terminal_count(),
        "advisory_results": trace.advisory_count(),
        "verifier_passed": sum(1 for result in trace.results if result.status == ProofVerificationStatus.VERIFIER_PASSED),
        "verifier_failed": trace.failed_count(),
        "verifier_not_run": sum(1 for result in trace.results if result.status == ProofVerificationStatus.VERIFIER_NOT_RUN),
        "imported_verified": sum(1 for result in trace.results if result.status == ProofVerificationStatus.IMPORTED_VERIFIED),
        "chain_audited": sum(1 for result in trace.results if result.status == ProofVerificationStatus.CHAIN_AUDITED),
        "rejected": sum(1 for result in trace.results if result.status == ProofVerificationStatus.REJECTED),
        "residual_delta_total": trace.residual_delta_total(),
        "compression_gain_total": trace.compression_gain_total(),
        "projection_gain_total": trace.projection_gain_total(),
    }


def _experience_outcome(result: ProofVerificationResult) -> AgentExperienceOutcome:
    if result.is_terminal():
        return AgentExperienceOutcome.VERIFIED_PROOF
    if result.status == ProofVerificationStatus.VERIFIER_FAILED:
        return AgentExperienceOutcome.INVALID_CANDIDATE
    if result.status in {ProofVerificationStatus.VERIFIER_NOT_RUN, ProofVerificationStatus.RESIDUAL}:
        return AgentExperienceOutcome.RESIDUAL
    return AgentExperienceOutcome.ADVISORY_ONLY


def _verifier_kind(value: ProofVerifierKind | str) -> ProofVerifierKind:
    if isinstance(value, ProofVerifierKind):
        return value
    return ProofVerifierKind(str(value))


def _optional_terminal_form(value: Any) -> TerminalForm | None:
    if value in (None, ""):
        return None
    if isinstance(value, TerminalForm):
        return value
    return TerminalForm(str(value))


def _optional_str(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value)


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _excerpt(text: str, limit: int = 2000) -> str:
    if len(text) <= limit:
        return text
    half = limit // 2
    return text[:half] + "\n...\n" + text[-half:]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
