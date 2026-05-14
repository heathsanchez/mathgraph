"""Verifier-bound Lean adapter hardening.

Lean files, skeletons, theorem names, and parseable Lean text are advisory until
Lean or a trusted importer crosses the proof verification boundary.
"""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from mathgraph.agent_biography import AgentExperience, AgentExperienceOutcome
from mathgraph.alchemy import AlchemicalPhase, AlchemicalStatus, AlchemicalTrace, make_alchemical_trace_id
from mathgraph.certificates import TerminalForm
from mathgraph.hashing import content_id
from mathgraph.proof_verification import (
    ProofArtifact,
    ProofArtifactKind,
    ProofVerificationResult,
    ProofVerificationStatus,
    ProofVerificationTrace,
    ProofVerifierKind,
    import_verified_proof,
    make_proof_artifact_id,
    make_proof_result_id,
    make_proof_trace_id,
    run_proof_verifier,
)


class LeanArtifactStatus(str, Enum):
    DRAFT = "DRAFT"
    SKELETON = "SKELETON"
    FILE_WRITTEN = "FILE_WRITTEN"
    LEAN_NOT_AVAILABLE = "LEAN_NOT_AVAILABLE"
    CHECK_NOT_RUN = "CHECK_NOT_RUN"
    CHECK_PASSED = "CHECK_PASSED"
    CHECK_FAILED = "CHECK_FAILED"
    IMPORTED_VERIFIED = "IMPORTED_VERIFIED"
    RESIDUAL = "RESIDUAL"
    ADVISORY_ONLY = "ADVISORY_ONLY"


@dataclass
class LeanEnvironment:
    lean_command: tuple[str, ...] = ("lean",)
    lake_command: tuple[str, ...] = ("lake",)
    project_root: str | None = None
    lean_available: bool | None = None
    lake_available: bool | None = None
    version: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    advisory: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "lean_command": list(self.lean_command),
            "lake_command": list(self.lake_command),
            "project_root": self.project_root,
            "lean_available": self.lean_available,
            "lake_available": self.lake_available,
            "version": self.version,
            "metadata": dict(self.metadata),
            "advisory": self.advisory,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "LeanEnvironment":
        return cls(
            lean_command=tuple(str(x) for x in data.get("lean_command", ("lean",))),
            lake_command=tuple(str(x) for x in data.get("lake_command", ("lake",))),
            project_root=_optional_str(data.get("project_root")),
            lean_available=_optional_bool(data.get("lean_available")),
            lake_available=_optional_bool(data.get("lake_available")),
            version=_optional_str(data.get("version")),
            metadata=dict(data.get("metadata", {})),
            advisory=bool(data.get("advisory", True)),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "LeanEnvironment":
        return cls.from_dict(json.loads(text))


@dataclass
class LeanFileArtifact:
    lean_file_id: str
    proof_artifact_id: str | None
    path: str | None
    content: str
    theorem_names: tuple[str, ...] = ()
    imports: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    status: LeanArtifactStatus = LeanArtifactStatus.DRAFT
    metadata: dict[str, Any] = field(default_factory=dict)
    advisory: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "lean_file_id": self.lean_file_id,
            "proof_artifact_id": self.proof_artifact_id,
            "path": self.path,
            "content": self.content,
            "theorem_names": list(self.theorem_names),
            "imports": list(self.imports),
            "dependencies": list(self.dependencies),
            "status": self.status.value,
            "metadata": dict(self.metadata),
            "advisory": self.advisory,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "LeanFileArtifact":
        return cls(
            lean_file_id=str(data["lean_file_id"]),
            proof_artifact_id=_optional_str(data.get("proof_artifact_id")),
            path=_optional_str(data.get("path")),
            content=str(data.get("content", "")),
            theorem_names=tuple(str(x) for x in data.get("theorem_names", ())),
            imports=tuple(str(x) for x in data.get("imports", ())),
            dependencies=tuple(str(x) for x in data.get("dependencies", ())),
            status=LeanArtifactStatus(str(data.get("status", LeanArtifactStatus.DRAFT.value))),
            metadata=dict(data.get("metadata", {})),
            advisory=bool(data.get("advisory", True)),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "LeanFileArtifact":
        return cls.from_dict(json.loads(text))

    def write_file(self, path: str | Path) -> "LeanFileArtifact":
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.content, encoding="utf-8")
        return LeanFileArtifact.from_dict(
            {
                **self.to_dict(),
                "path": str(target),
                "status": LeanArtifactStatus.FILE_WRITTEN.value,
            }
        )

    @classmethod
    def read_file(cls, path: str | Path) -> "LeanFileArtifact":
        source = Path(path)
        content = source.read_text(encoding="utf-8")
        return LeanFileArtifact(
            lean_file_id=make_lean_file_id(content=content, path=str(source)),
            proof_artifact_id=None,
            path=str(source),
            content=content,
            theorem_names=extract_lean_theorem_names(content),
            imports=extract_lean_imports(content),
            status=LeanArtifactStatus.FILE_WRITTEN,
            metadata={"advisory_only": True},
        )


@dataclass
class LeanCheckResult:
    result_id: str
    lean_file_id: str
    status: LeanArtifactStatus
    proof_verification_result: ProofVerificationResult | None = None
    command: tuple[str, ...] = ()
    return_code: int | None = None
    stdout_excerpt: str = ""
    stderr_excerpt: str = ""
    theorem_names: tuple[str, ...] = ()
    imports: tuple[str, ...] = ()
    checked_at: str | None = None
    verifier_boundary_crossed: bool = False
    certificate_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    advisory: bool = True

    def is_verified(self) -> bool:
        return (
            self.status in {LeanArtifactStatus.CHECK_PASSED, LeanArtifactStatus.IMPORTED_VERIFIED}
            and self.proof_verification_result is not None
            and self.proof_verification_result.is_terminal()
            and self.verifier_boundary_crossed
            and bool(self.certificate_id)
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "result_id": self.result_id,
            "lean_file_id": self.lean_file_id,
            "status": self.status.value,
            "proof_verification_result": self.proof_verification_result.to_dict() if self.proof_verification_result else None,
            "command": list(self.command),
            "return_code": self.return_code,
            "stdout_excerpt": self.stdout_excerpt,
            "stderr_excerpt": self.stderr_excerpt,
            "theorem_names": list(self.theorem_names),
            "imports": list(self.imports),
            "checked_at": self.checked_at,
            "verifier_boundary_crossed": self.verifier_boundary_crossed,
            "certificate_id": self.certificate_id,
            "metadata": dict(self.metadata),
            "advisory": self.advisory,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "LeanCheckResult":
        pvr = data.get("proof_verification_result")
        return cls(
            result_id=str(data["result_id"]),
            lean_file_id=str(data["lean_file_id"]),
            status=LeanArtifactStatus(str(data["status"])),
            proof_verification_result=ProofVerificationResult.from_dict(pvr) if pvr else None,
            command=tuple(str(x) for x in data.get("command", ())),
            return_code=_optional_int(data.get("return_code")),
            stdout_excerpt=str(data.get("stdout_excerpt", "")),
            stderr_excerpt=str(data.get("stderr_excerpt", "")),
            theorem_names=tuple(str(x) for x in data.get("theorem_names", ())),
            imports=tuple(str(x) for x in data.get("imports", ())),
            checked_at=_optional_str(data.get("checked_at")),
            verifier_boundary_crossed=bool(data.get("verifier_boundary_crossed", False)),
            certificate_id=_optional_str(data.get("certificate_id")),
            metadata=dict(data.get("metadata", {})),
            advisory=bool(data.get("advisory", True)),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "LeanCheckResult":
        return cls.from_dict(json.loads(text))


@dataclass
class LeanAdapterTrace:
    trace_id: str
    environment: LeanEnvironment
    files: list[LeanFileArtifact] = field(default_factory=list)
    results: list[LeanCheckResult] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    summary: dict[str, Any] = field(default_factory=dict)
    advisory: bool = True

    def verified_count(self) -> int:
        return sum(1 for result in self.results if result.is_verified())

    def failed_count(self) -> int:
        return sum(1 for result in self.results if result.status == LeanArtifactStatus.CHECK_FAILED)

    def not_available_count(self) -> int:
        return sum(1 for result in self.results if result.status == LeanArtifactStatus.LEAN_NOT_AVAILABLE)

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "environment": self.environment.to_dict(),
            "files": [file.to_dict() for file in self.files],
            "results": [result.to_dict() for result in self.results],
            "created_at": self.created_at,
            "summary": dict(self.summary),
            "advisory": self.advisory,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "LeanAdapterTrace":
        return cls(
            trace_id=str(data["trace_id"]),
            environment=LeanEnvironment.from_dict(data.get("environment", {})),
            files=[LeanFileArtifact.from_dict(item) for item in data.get("files", [])],
            results=[LeanCheckResult.from_dict(item) for item in data.get("results", [])],
            created_at=str(data.get("created_at") or _now()),
            summary=dict(data.get("summary", {})),
            advisory=bool(data.get("advisory", True)),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "LeanAdapterTrace":
        return cls.from_dict(json.loads(text))

    def write_json(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.to_dict(), sort_keys=True, indent=2) + "\n", encoding="utf-8")

    @classmethod
    def read_json(cls, path: str | Path) -> "LeanAdapterTrace":
        return cls.from_json(Path(path).read_text(encoding="utf-8"))

    def write_jsonl(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.to_json() + "\n", encoding="utf-8")

    @classmethod
    def read_jsonl(cls, path: str | Path) -> list["LeanAdapterTrace"]:
        source = Path(path)
        if not source.exists():
            return []
        traces: list[LeanAdapterTrace] = []
        with source.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    traces.append(cls.from_json(line))
        return traces


def detect_lean_environment(
    *,
    lean_command: Sequence[str] = ("lean",),
    lake_command: Sequence[str] = ("lake",),
    project_root: str | None = None,
    timeout_seconds: float = 5.0,
) -> LeanEnvironment:
    lean_cmd = tuple(str(x) for x in lean_command)
    lake_cmd = tuple(str(x) for x in lake_command)
    lean_available, lean_version, lean_error = _detect_command(lean_cmd, timeout_seconds)
    lake_available, lake_version, lake_error = _detect_command(lake_cmd, timeout_seconds)
    version = lean_version or lake_version
    metadata = {
        "lean_error": lean_error,
        "lake_error": lake_error,
        "shell": False,
        "advisory_only": True,
    }
    return LeanEnvironment(
        lean_command=lean_cmd,
        lake_command=lake_cmd,
        project_root=project_root,
        lean_available=lean_available,
        lake_available=lake_available,
        version=version,
        metadata=metadata,
    )


def extract_lean_imports(content: str) -> tuple[str, ...]:
    imports = []
    for line in content.splitlines():
        match = re.match(r"^\s*import\s+([A-Za-z0-9_.'/-]+)\s*$", line)
        if match:
            imports.append(match.group(1))
    return tuple(dict.fromkeys(imports))


def extract_lean_theorem_names(content: str) -> tuple[str, ...]:
    names = re.findall(r"^\s*(?:theorem|lemma)\s+([A-Za-z_][A-Za-z0-9_']*)\b", content, flags=re.MULTILINE)
    return tuple(dict.fromkeys(names))


def lean_file_from_proof_artifact(
    artifact: ProofArtifact,
    *,
    path: str | None = None,
) -> LeanFileArtifact:
    content = artifact.content
    status = LeanArtifactStatus.SKELETON if artifact.kind == ProofArtifactKind.LEAN_SKELETON else LeanArtifactStatus.DRAFT
    if path or artifact.file_path:
        status = LeanArtifactStatus.FILE_WRITTEN
    return LeanFileArtifact(
        lean_file_id=make_lean_file_id(content=content, path=path or artifact.file_path, proof_artifact_id=artifact.artifact_id),
        proof_artifact_id=artifact.artifact_id,
        path=path or artifact.file_path,
        content=content,
        theorem_names=extract_lean_theorem_names(content) or ((artifact.theorem_name,) if artifact.theorem_name else ()),
        imports=extract_lean_imports(content) or artifact.imports,
        dependencies=artifact.dependencies,
        status=status,
        metadata={"proof_artifact": artifact.to_dict(), "advisory_only": True},
    )


def proof_artifact_from_lean_file(lean_file: LeanFileArtifact) -> ProofArtifact:
    payload = {
        "lean_file_id": lean_file.lean_file_id,
        "path": lean_file.path,
        "content": lean_file.content,
        "theorem_names": list(lean_file.theorem_names),
    }
    return ProofArtifact(
        artifact_id=lean_file.proof_artifact_id or make_proof_artifact_id(payload),
        claim_id=_optional_str(lean_file.metadata.get("claim_id")),
        kind=ProofArtifactKind.LEAN_FILE,
        language="lean",
        content=lean_file.content,
        file_path=lean_file.path,
        theorem_name=lean_file.theorem_names[0] if lean_file.theorem_names else None,
        imports=lean_file.imports,
        dependencies=lean_file.dependencies,
        advisory=True,
        metadata={"lean_file": lean_file.to_dict(), "advisory_only": True},
    )


def check_lean_file(
    lean_file: LeanFileArtifact,
    *,
    environment: LeanEnvironment | None = None,
    timeout_seconds: float = 20.0,
    write_temp_if_needed: bool = True,
) -> LeanCheckResult:
    environment = environment or detect_lean_environment(timeout_seconds=min(timeout_seconds, 5.0))
    if environment.lean_available is not True:
        return _lean_check_result(
            lean_file,
            LeanArtifactStatus.LEAN_NOT_AVAILABLE,
            command=environment.lean_command,
            stderr="Lean executable was not available.",
            metadata={"environment": environment.to_dict(), "failure_reason": "lean_not_available"},
        )
    temp_path: Path | None = None
    path = Path(lean_file.path) if lean_file.path else None
    try:
        if path is None:
            if not write_temp_if_needed:
                return _lean_check_result(
                    lean_file,
                    LeanArtifactStatus.CHECK_NOT_RUN,
                    command=environment.lean_command,
                    stderr="Lean file has no path and temporary write disabled.",
                    metadata={"environment": environment.to_dict(), "failure_reason": "no_path"},
                )
            with tempfile.NamedTemporaryFile("w", suffix=".lean", encoding="utf-8", delete=False) as handle:
                handle.write(lean_file.content)
                temp_path = Path(handle.name)
            path = temp_path
        cmd = tuple(environment.lean_command) + (str(path),)
        artifact = proof_artifact_from_lean_file(LeanFileArtifact.from_dict({**lean_file.to_dict(), "path": str(path)}))
        proof_result = run_proof_verifier(
            artifact,
            verifier_kind=ProofVerifierKind.LEAN,
            command=cmd,
            timeout_seconds=timeout_seconds,
        )
        status = LeanArtifactStatus.CHECK_PASSED if proof_result.is_terminal() else LeanArtifactStatus.CHECK_FAILED
        return LeanCheckResult(
            result_id=make_lean_check_result_id(lean_file.lean_file_id, status.value, cmd, proof_result.to_dict()),
            lean_file_id=lean_file.lean_file_id,
            status=status,
            proof_verification_result=proof_result,
            command=cmd,
            return_code=proof_result.return_code,
            stdout_excerpt=proof_result.stdout_excerpt,
            stderr_excerpt=proof_result.stderr_excerpt,
            theorem_names=lean_file.theorem_names,
            imports=lean_file.imports,
            checked_at=proof_result.checked_at or _now(),
            verifier_boundary_crossed=proof_result.is_terminal(),
            certificate_id=proof_result.certificate_id if proof_result.is_terminal() else None,
            metadata={
                "environment": environment.to_dict(),
                "advisory_only": not proof_result.is_terminal(),
                "failure_reason": proof_result.failure_reason,
            },
            advisory=not proof_result.is_terminal(),
        )
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def import_checked_lean_artifact(
    lean_file: LeanFileArtifact,
    *,
    external_certificate_id: str | None = None,
    provenance: Mapping[str, Any] | None = None,
) -> LeanCheckResult:
    artifact = proof_artifact_from_lean_file(lean_file)
    proof_result = import_verified_proof(
        artifact=artifact,
        verifier_kind=ProofVerifierKind.TRUSTED_IMPORTER,
        external_certificate_id=external_certificate_id,
        provenance=provenance,
    )
    status = LeanArtifactStatus.IMPORTED_VERIFIED if proof_result.is_terminal() else LeanArtifactStatus.RESIDUAL
    return LeanCheckResult(
        result_id=make_lean_check_result_id(lean_file.lean_file_id, status.value, proof_result.to_dict()),
        lean_file_id=lean_file.lean_file_id,
        status=status,
        proof_verification_result=proof_result,
        theorem_names=lean_file.theorem_names,
        imports=lean_file.imports,
        checked_at=proof_result.checked_at or _now(),
        verifier_boundary_crossed=proof_result.is_terminal(),
        certificate_id=proof_result.certificate_id if proof_result.is_terminal() else None,
        metadata={"provenance": dict(provenance or {}), "external_certificate_id": external_certificate_id},
        advisory=not proof_result.is_terminal(),
    )


def run_lean_adapter_pipeline(
    *,
    proof_artifacts: Sequence[ProofArtifact] = (),
    lean_files: Sequence[LeanFileArtifact] = (),
    environment: LeanEnvironment | None = None,
    check: bool = False,
    import_verified: bool = False,
    timeout_seconds: float = 20.0,
) -> LeanAdapterTrace:
    files = list(lean_files)
    files.extend(lean_file_from_proof_artifact(artifact) for artifact in proof_artifacts if artifact.kind in {ProofArtifactKind.LEAN_SKELETON, ProofArtifactKind.LEAN_FILE})
    env = environment or detect_lean_environment(timeout_seconds=min(timeout_seconds, 5.0))
    results: list[LeanCheckResult] = []
    if check:
        results = [check_lean_file(file, environment=env, timeout_seconds=timeout_seconds) for file in files]
    elif import_verified:
        results = [
            import_checked_lean_artifact(
                file,
                external_certificate_id=_optional_str(file.metadata.get("external_certificate_id")),
                provenance=file.metadata.get("provenance") if isinstance(file.metadata.get("provenance"), Mapping) else None,
            )
            for file in files
        ]
    else:
        results = [
            _lean_check_result(
                file,
                LeanArtifactStatus.CHECK_NOT_RUN,
                metadata={"advisory_only": True, "reason": "check/import not requested"},
            )
            for file in files
        ]
    trace = LeanAdapterTrace(
        trace_id=make_lean_adapter_trace_id(env.to_dict(), [file.to_dict() for file in files], [result.to_dict() for result in results]),
        environment=env,
        files=files,
        results=results,
    )
    trace.summary.update(_trace_summary(trace, check_requested=check, import_requested=import_verified))
    return trace


def lean_adapter_trace_to_proof_verification_trace(trace: LeanAdapterTrace) -> ProofVerificationTrace:
    artifacts = [proof_artifact_from_lean_file(file) for file in trace.files]
    results = [result.proof_verification_result for result in trace.results if result.proof_verification_result is not None]
    proof_trace = ProofVerificationTrace(
        trace_id=make_proof_trace_id("lean_adapter", trace.trace_id),
        episode_id=None,
        agent_id=None,
        artifacts=artifacts,
        results=results,
    )
    proof_trace.summary.update(
        {
            "source": "lean_adapter",
            "lean_trace_id": trace.trace_id,
            "terminal_results": proof_trace.terminal_count(),
            "advisory_only": proof_trace.terminal_count() == 0,
        }
    )
    return proof_trace


def lean_adapter_trace_to_alchemical_trace(trace: LeanAdapterTrace) -> AlchemicalTrace:
    alchemical = AlchemicalTrace(
        trace_id=make_alchemical_trace_id("lean_adapter", trace.trace_id),
        claim_id=None,
        agent_id=None,
        episode_id=None,
    )
    alchemical.add_step(phase=AlchemicalPhase.RAW_MATTER, status=AlchemicalStatus.SUCCEEDED)
    if trace.files:
        alchemical.add_step(
            phase=AlchemicalPhase.DESCENSION,
            status=AlchemicalStatus.ADVISORY_ONLY,
            output_artifact_ids=tuple(file.lean_file_id for file in trace.files),
        )
    if trace.results:
        alchemical.add_step(
            phase=AlchemicalPhase.DISTILLATION,
            status=AlchemicalStatus.SUCCEEDED if trace.results else AlchemicalStatus.ADVISORY_ONLY,
            output_artifact_ids=tuple(result.result_id for result in trace.results),
        )
    verified = [result for result in trace.results if result.is_verified()]
    if verified:
        first = verified[0]
        alchemical.terminal_form = TerminalForm.VERIFIED_PROOF
        alchemical.promoted_certificate_id = first.certificate_id
        alchemical.add_step(
            phase=AlchemicalPhase.FIXATION,
            status=AlchemicalStatus.PROMOTED_BY_VERIFIER,
            verifier_boundary="LEAN_ADAPTER",
        )
        if any(file.theorem_names for file in trace.files):
            alchemical.add_step(phase=AlchemicalPhase.CERATION, status=AlchemicalStatus.SUCCEEDED)
    return alchemical


def lean_adapter_trace_to_agent_experiences(trace: LeanAdapterTrace, agent_id: str | None = None) -> list[AgentExperience]:
    actor = agent_id or "lean-adapter"
    experiences: list[AgentExperience] = []
    for result in trace.results:
        verified = result.is_verified()
        experiences.append(
            AgentExperience(
                experience_id=content_id("lean_adapter_exp", result.to_dict(), n=24),
                agent_id=actor,
                episode_id=None,
                claim_id=result.lean_file_id,
                route="lean_adapter",
                phase=AlchemicalPhase.DISTILLATION.value,
                outcome=AgentExperienceOutcome.VERIFIED_PROOF if verified else (
                    AgentExperienceOutcome.FAILED_SEARCH if result.status == LeanArtifactStatus.CHECK_FAILED else AgentExperienceOutcome.ADVISORY_ONLY
                ),
                terminal_form=TerminalForm.VERIFIED_PROOF if verified else None,
                certificate_id=result.certificate_id if verified else None,
                verifier_boundary_crossed=verified,
                scar_tags=("lean_check_failed",) if result.status == LeanArtifactStatus.CHECK_FAILED else (),
                metadata={"lean_check_result": result.to_dict(), "boundary_preserved": True},
            )
        )
    return experiences


def make_lean_file_id(**payload: Any) -> str:
    return content_id("lean_file", payload, n=24)


def make_lean_check_result_id(*parts: Any) -> str:
    return content_id("lean_check_result", parts, n=24)


def make_lean_adapter_trace_id(*parts: Any) -> str:
    return content_id("lean_adapter_trace", parts, n=24)


def _detect_command(command: tuple[str, ...], timeout_seconds: float) -> tuple[bool, str | None, str | None]:
    if not command:
        return False, None, "empty command"
    try:
        completed = subprocess.run(
            list(command) + ["--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, None, str(exc)
    text = (completed.stdout or completed.stderr or "").strip()
    return completed.returncode == 0, text or None, None if completed.returncode == 0 else text or f"exit {completed.returncode}"


def _lean_check_result(
    lean_file: LeanFileArtifact,
    status: LeanArtifactStatus,
    *,
    command: Sequence[str] = (),
    return_code: int | None = None,
    stdout: str = "",
    stderr: str = "",
    metadata: Mapping[str, Any] | None = None,
) -> LeanCheckResult:
    return LeanCheckResult(
        result_id=make_lean_check_result_id(lean_file.lean_file_id, status.value, tuple(command), return_code, stderr, dict(metadata or {})),
        lean_file_id=lean_file.lean_file_id,
        status=status,
        command=tuple(str(x) for x in command),
        return_code=return_code,
        stdout_excerpt=_excerpt(stdout),
        stderr_excerpt=_excerpt(stderr),
        theorem_names=lean_file.theorem_names,
        imports=lean_file.imports,
        checked_at=_now(),
        verifier_boundary_crossed=False,
        metadata=dict(metadata or {}),
        advisory=True,
    )


def _trace_summary(trace: LeanAdapterTrace, *, check_requested: bool, import_requested: bool) -> dict[str, Any]:
    theorem_names = sorted({name for file in trace.files for name in file.theorem_names})
    imports = sorted({name for file in trace.files for name in file.imports})
    return {
        "files_total": len(trace.files),
        "checks_total": len(trace.results),
        "verified": trace.verified_count(),
        "failed": trace.failed_count(),
        "lean_not_available": trace.not_available_count(),
        "theorem_names": theorem_names,
        "imports": imports,
        "check_requested": check_requested,
        "import_requested": import_requested,
        "advisory_only": trace.verified_count() == 0,
    }


def _excerpt(text: str, limit: int = 2000) -> str:
    if len(text) <= limit:
        return text
    half = limit // 2
    return text[:half] + "\n...\n" + text[-half:]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _optional_str(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value)


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


def _optional_bool(value: Any) -> bool | None:
    if value is None:
        return None
    return bool(value)
