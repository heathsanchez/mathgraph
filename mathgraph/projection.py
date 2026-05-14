"""Lightweight projection engine for lawbook compounding.

Projection applies already verified or chain-audited lawbook structure back to
residuals. Projection pressure is not truth: terminal projection results require
an existing verifier boundary or an explicitly chain-safe derived certificate.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from mathgraph.agent_biography import AgentExperience, AgentExperienceOutcome
from mathgraph.alchemy import AlchemicalPhase, AlchemicalStatus, AlchemicalTrace, make_alchemical_trace_id
from mathgraph.certificates import TerminalForm
from mathgraph.hashing import content_id


class ProjectionStatus(str, Enum):
    CANDIDATE = "CANDIDATE"
    APPLIED = "APPLIED"
    DERIVED_CERTIFICATE = "DERIVED_CERTIFICATE"
    KNOWN_SKIP = "KNOWN_SKIP"
    RESIDUAL_SPLIT = "RESIDUAL_SPLIT"
    OBSTRUCTION_PRESSURE = "OBSTRUCTION_PRESSURE"
    REJECTED = "REJECTED"
    ADVISORY_ONLY = "ADVISORY_ONLY"


class ProjectionRuleKind(str, Enum):
    EXACT_KNOWN = "EXACT_KNOWN"
    TRANSITIVITY = "TRANSITIVITY"
    SOURCE_WEAKENING_FALSE = "SOURCE_WEAKENING_FALSE"
    TARGET_STRENGTHENING_FALSE = "TARGET_STRENGTHENING_FALSE"
    EQUIVALENCE_COLLAPSE = "EQUIVALENCE_COLLAPSE"
    DUALITY = "DUALITY"
    CONSTRUCTOR_REPLAY = "CONSTRUCTOR_REPLAY"
    BASIN_EXPANSION = "BASIN_EXPANSION"
    ADVISORY_SIMILARITY = "ADVISORY_SIMILARITY"


@dataclass
class ProjectionCandidate:
    candidate_id: str
    source_claim_id: str | None
    target_claim_id: str | None
    source_idx: int | None = None
    target_idx: int | None = None
    source: str | None = None
    target: str | None = None
    rule_kind: ProjectionRuleKind = ProjectionRuleKind.ADVISORY_SIMILARITY
    originating_lawbook_entry_id: str | None = None
    originating_certificate_id: str | None = None
    confidence: float = 0.0
    advisory: bool = True
    reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "source_claim_id": self.source_claim_id,
            "target_claim_id": self.target_claim_id,
            "source_idx": self.source_idx,
            "target_idx": self.target_idx,
            "source": self.source,
            "target": self.target,
            "rule_kind": self.rule_kind.value,
            "originating_lawbook_entry_id": self.originating_lawbook_entry_id,
            "originating_certificate_id": self.originating_certificate_id,
            "confidence": self.confidence,
            "advisory": self.advisory,
            "reason": self.reason,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ProjectionCandidate":
        return cls(
            candidate_id=str(data["candidate_id"]),
            source_claim_id=_optional_str(data.get("source_claim_id")),
            target_claim_id=_optional_str(data.get("target_claim_id")),
            source_idx=_optional_int(data.get("source_idx")),
            target_idx=_optional_int(data.get("target_idx")),
            source=_optional_str(data.get("source")),
            target=_optional_str(data.get("target")),
            rule_kind=ProjectionRuleKind(str(data.get("rule_kind", ProjectionRuleKind.ADVISORY_SIMILARITY.value))),
            originating_lawbook_entry_id=_optional_str(data.get("originating_lawbook_entry_id")),
            originating_certificate_id=_optional_str(data.get("originating_certificate_id")),
            confidence=float(data.get("confidence", 0.0) or 0.0),
            advisory=bool(data.get("advisory", True)),
            reason=_optional_str(data.get("reason")),
            metadata=dict(data.get("metadata", {})),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "ProjectionCandidate":
        return cls.from_dict(json.loads(text))

    def to_jsonl_line(self) -> str:
        return self.to_json() + "\n"

    @classmethod
    def from_jsonl_line(cls, line: str) -> "ProjectionCandidate":
        return cls.from_json(line.strip())


@dataclass
class ProjectionResult:
    result_id: str
    candidate_id: str
    status: ProjectionStatus
    terminal_form: TerminalForm | None = None
    derived_certificate_id: str | None = None
    verifier_boundary_crossed: bool = False
    lawbook_entry_id: str | None = None
    residual_delta: int = 0
    compression_gain: float = 0.0
    projection_gain: float = 0.0
    rejection_reason: str | None = None
    advisory_notes: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_terminal(self) -> bool:
        if self.terminal_form is None:
            return False
        if self.status in {
            ProjectionStatus.ADVISORY_ONLY,
            ProjectionStatus.CANDIDATE,
            ProjectionStatus.OBSTRUCTION_PRESSURE,
            ProjectionStatus.RESIDUAL_SPLIT,
            ProjectionStatus.REJECTED,
        }:
            return False
        return self.verifier_boundary_crossed or (
            self.status == ProjectionStatus.DERIVED_CERTIFICATE and bool(self.derived_certificate_id)
        )

    def is_advisory(self) -> bool:
        return not self.is_terminal()

    def to_dict(self) -> dict[str, Any]:
        return {
            "result_id": self.result_id,
            "candidate_id": self.candidate_id,
            "status": self.status.value,
            "terminal_form": self.terminal_form.value if self.terminal_form else None,
            "derived_certificate_id": self.derived_certificate_id,
            "verifier_boundary_crossed": self.verifier_boundary_crossed,
            "lawbook_entry_id": self.lawbook_entry_id,
            "residual_delta": self.residual_delta,
            "compression_gain": self.compression_gain,
            "projection_gain": self.projection_gain,
            "rejection_reason": self.rejection_reason,
            "advisory_notes": list(self.advisory_notes),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ProjectionResult":
        return cls(
            result_id=str(data["result_id"]),
            candidate_id=str(data["candidate_id"]),
            status=ProjectionStatus(str(data["status"])),
            terminal_form=_optional_terminal_form(data.get("terminal_form")),
            derived_certificate_id=_optional_str(data.get("derived_certificate_id")),
            verifier_boundary_crossed=bool(data.get("verifier_boundary_crossed", False)),
            lawbook_entry_id=_optional_str(data.get("lawbook_entry_id")),
            residual_delta=int(data.get("residual_delta", 0) or 0),
            compression_gain=float(data.get("compression_gain", 0.0) or 0.0),
            projection_gain=float(data.get("projection_gain", 0.0) or 0.0),
            rejection_reason=_optional_str(data.get("rejection_reason")),
            advisory_notes=tuple(str(x) for x in data.get("advisory_notes", ())),
            metadata=dict(data.get("metadata", {})),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "ProjectionResult":
        return cls.from_dict(json.loads(text))

    def to_jsonl_line(self) -> str:
        return self.to_json() + "\n"

    @classmethod
    def from_jsonl_line(cls, line: str) -> "ProjectionResult":
        return cls.from_json(line.strip())


@dataclass
class ProjectionTrace:
    trace_id: str
    episode_id: str | None
    agent_id: str | None
    candidates: list[ProjectionCandidate] = field(default_factory=list)
    results: list[ProjectionResult] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    summary: dict[str, Any] = field(default_factory=dict)

    def terminal_count(self) -> int:
        return sum(1 for result in self.results if result.is_terminal())

    def advisory_count(self) -> int:
        return sum(1 for result in self.results if result.is_advisory())

    def residual_delta_total(self) -> int:
        return sum(result.residual_delta for result in self.results)

    def projection_gain_total(self) -> float:
        return sum(result.projection_gain for result in self.results)

    def compression_gain_total(self) -> float:
        return sum(result.compression_gain for result in self.results)

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "episode_id": self.episode_id,
            "agent_id": self.agent_id,
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "results": [result.to_dict() for result in self.results],
            "created_at": self.created_at,
            "summary": dict(self.summary),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ProjectionTrace":
        return cls(
            trace_id=str(data["trace_id"]),
            episode_id=_optional_str(data.get("episode_id")),
            agent_id=_optional_str(data.get("agent_id")),
            candidates=[ProjectionCandidate.from_dict(item) for item in data.get("candidates", [])],
            results=[ProjectionResult.from_dict(item) for item in data.get("results", [])],
            created_at=str(data.get("created_at") or datetime.now(timezone.utc).isoformat()),
            summary=dict(data.get("summary", {})),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "ProjectionTrace":
        return cls.from_dict(json.loads(text))

    def write_json(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.to_dict(), sort_keys=True, indent=2) + "\n", encoding="utf-8")

    @classmethod
    def read_json(cls, path: str | Path) -> "ProjectionTrace":
        return cls.from_json(Path(path).read_text(encoding="utf-8"))

    def write_jsonl(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.to_json() + "\n", encoding="utf-8")

    @classmethod
    def read_jsonl(cls, path: str | Path) -> list["ProjectionTrace"]:
        source = Path(path)
        if not source.exists():
            return []
        traces: list[ProjectionTrace] = []
        with source.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    traces.append(cls.from_json(line))
        return traces


def exact_known_projection(pair: Mapping[str, Any], known_entries: Sequence[Mapping[str, Any]]) -> ProjectionResult | None:
    source, target = _source_target(pair)
    source_idx, target_idx = _source_target_idx(pair)
    for entry in known_entries:
        if not _is_verified_or_chain_audited(entry):
            continue
        if _entry_matches(entry, source, target, source_idx, target_idx):
            candidate = _candidate_for_pair(
                pair,
                ProjectionRuleKind.EXACT_KNOWN,
                lawbook_entry=entry,
                advisory=False,
                confidence=1.0,
                reason="Pair is already present as a verified or chain-audited lawbook entry.",
            )
            return ProjectionResult(
                result_id=make_projection_result_id(candidate.candidate_id, ProjectionStatus.KNOWN_SKIP.value),
                candidate_id=candidate.candidate_id,
                status=ProjectionStatus.KNOWN_SKIP,
                terminal_form=_terminal(entry.get("terminal_form")),
                verifier_boundary_crossed=True,
                lawbook_entry_id=_entry_id(entry),
                residual_delta=-1,
                compression_gain=1.0,
                projection_gain=1.0,
                advisory_notes=("known skip from lawbook memory",),
                metadata={"candidate": candidate.to_dict(), "source": "exact_known_projection"},
            )
    return None


def transitivity_projection(a_implies_b: Mapping[str, Any], b_implies_c: Mapping[str, Any]) -> ProjectionCandidate:
    source = _text(a_implies_b.get("source"))
    bridge = _text(a_implies_b.get("target"))
    right_source = _text(b_implies_c.get("source"))
    target = _text(b_implies_c.get("target"))
    chain_safe = (
        bridge is not None
        and bridge == right_source
        and _terminal(a_implies_b.get("terminal_form")) == TerminalForm.VERIFIED_PROOF
        and _terminal(b_implies_c.get("terminal_form")) == TerminalForm.VERIFIED_PROOF
        and _is_verified_or_chain_audited(a_implies_b)
        and _is_verified_or_chain_audited(b_implies_c)
    )
    return _projection_candidate(
        source=source,
        target=target,
        rule_kind=ProjectionRuleKind.TRANSITIVITY,
        parents=[a_implies_b, b_implies_c],
        confidence=1.0 if chain_safe else 0.35,
        advisory=not chain_safe,
        reason="A=>B and B=>C suggest A=>C.",
        metadata={"chain_safe": chain_safe},
    )


def source_weakening_false_projection(a_not_c: Mapping[str, Any], a_implies_d: Mapping[str, Any]) -> ProjectionCandidate:
    source = _text(a_implies_d.get("target"))
    target = _text(a_not_c.get("target"))
    chain_safe = (
        _text(a_not_c.get("source")) == _text(a_implies_d.get("source"))
        and _terminal(a_not_c.get("terminal_form")) == TerminalForm.FINITE_COUNTERMODEL
        and _terminal(a_implies_d.get("terminal_form")) == TerminalForm.VERIFIED_PROOF
        and _is_verified_or_chain_audited(a_not_c)
        and _is_verified_or_chain_audited(a_implies_d)
    )
    return _projection_candidate(
        source=source,
        target=target,
        rule_kind=ProjectionRuleKind.SOURCE_WEAKENING_FALSE,
        parents=[a_not_c, a_implies_d],
        confidence=0.9 if chain_safe else 0.25,
        advisory=not chain_safe,
        reason="A not=> C and A=>D suggest D not=> C when the witness satisfies D through A.",
        metadata={"chain_safe": chain_safe, "requires_witness_preservation": True},
    )


def target_strengthening_false_projection(a_not_c: Mapping[str, Any], e_implies_c: Mapping[str, Any]) -> ProjectionCandidate:
    source = _text(a_not_c.get("source"))
    target = _text(e_implies_c.get("source"))
    chain_safe = (
        _text(a_not_c.get("target")) == _text(e_implies_c.get("target"))
        and _terminal(a_not_c.get("terminal_form")) == TerminalForm.FINITE_COUNTERMODEL
        and _terminal(e_implies_c.get("terminal_form")) == TerminalForm.VERIFIED_PROOF
        and _is_verified_or_chain_audited(a_not_c)
        and _is_verified_or_chain_audited(e_implies_c)
    )
    return _projection_candidate(
        source=source,
        target=target,
        rule_kind=ProjectionRuleKind.TARGET_STRENGTHENING_FALSE,
        parents=[a_not_c, e_implies_c],
        confidence=0.9 if chain_safe else 0.25,
        advisory=not chain_safe,
        reason="A not=> C and E=>C suggest A not=> E.",
        metadata={"chain_safe": chain_safe},
    )


def advisory_similarity_projection(
    pair: Mapping[str, Any],
    lawbook_entry: Mapping[str, Any] | None = None,
    reason: str | None = None,
) -> ProjectionCandidate:
    metadata = {"advisory_only": True}
    if lawbook_entry is not None:
        metadata["near_lawbook_entry_id"] = _entry_id(lawbook_entry)
    return _candidate_for_pair(
        pair,
        ProjectionRuleKind.ADVISORY_SIMILARITY,
        lawbook_entry=lawbook_entry,
        advisory=True,
        confidence=float(pair.get("confidence", 0.1) or 0.1),
        reason=reason or "Advisory similarity can schedule nearby residuals but cannot decide truth.",
        metadata=metadata,
    )


def run_projection_engine(
    *,
    lawbook_entries: Sequence[Mapping[str, Any]] = (),
    residual_pairs: Sequence[Mapping[str, Any]] = (),
    agent_id: str | None = None,
    episode_id: str | None = None,
    max_candidates: int | None = None,
) -> ProjectionTrace:
    entries = [dict(entry) for entry in lawbook_entries]
    residuals = [dict(pair) for pair in residual_pairs]
    candidates: list[ProjectionCandidate] = []
    results: list[ProjectionResult] = []

    for pair in residuals:
        known = exact_known_projection(pair, entries)
        if known is not None:
            candidate = ProjectionCandidate.from_dict(known.metadata["candidate"])
            candidates.append(candidate)
            results.append(known)
            if _limit_reached(candidates, max_candidates):
                break
            continue
        candidate = advisory_similarity_projection(pair, _nearest_entry(pair, entries))
        candidates.append(candidate)
        results.append(_advisory_result(candidate, ProjectionStatus.RESIDUAL_SPLIT))
        if _limit_reached(candidates, max_candidates):
            break

    if not _limit_reached(candidates, max_candidates):
        for candidate in _derived_candidates(entries):
            if _pair_in_entries(candidate, entries):
                continue
            candidates.append(candidate)
            results.append(_result_for_candidate(candidate))
            if _limit_reached(candidates, max_candidates):
                break

    trace = ProjectionTrace(
        trace_id=make_projection_trace_id(episode_id, agent_id, [candidate.to_dict() for candidate in candidates]),
        episode_id=episode_id,
        agent_id=agent_id,
        candidates=candidates,
        results=results,
    )
    trace.summary.update(_projection_summary(trace))
    return trace


def projection_trace_to_alchemical_trace(trace: ProjectionTrace, claim_id: str | None = None) -> AlchemicalTrace:
    alchemical = AlchemicalTrace(
        trace_id=make_alchemical_trace_id("projection", trace.trace_id),
        claim_id=claim_id,
        agent_id=trace.agent_id,
        episode_id=trace.episode_id,
    )
    alchemical.add_step(
        phase=AlchemicalPhase.RAW_MATTER,
        status=AlchemicalStatus.SUCCEEDED,
        output_artifact_ids=tuple(candidate.candidate_id for candidate in trace.candidates),
        advisory_notes=("projection inputs gathered from residuals and lawbook memory",),
    )
    alchemical.add_step(
        phase=AlchemicalPhase.MULTIPLICATION,
        status=AlchemicalStatus.SUCCEEDED,
        output_artifact_ids=tuple(result.result_id for result in trace.results),
        residual_delta=trace.residual_delta_total(),
        compression_gain=trace.compression_gain_total(),
        advisory_notes=("lawbook structure multiplied into residual pressure",),
    )
    promoted = [result for result in trace.results if result.is_terminal()]
    if promoted:
        first = promoted[0]
        alchemical.terminal_form = first.terminal_form
        alchemical.promoted_certificate_id = first.derived_certificate_id or first.lawbook_entry_id
        alchemical.add_step(
            phase=AlchemicalPhase.FIXATION,
            status=AlchemicalStatus.PROMOTED_BY_VERIFIER,
            verifier_boundary="PROJECTION_CHAIN_AUDITED" if first.derived_certificate_id else "LAWBOOK_EXACT_KNOWN",
            output_artifact_ids=tuple(result.result_id for result in promoted),
        )
    alchemical.add_step(
        phase=AlchemicalPhase.PROJECTION,
        status=AlchemicalStatus.SUCCEEDED if trace.results else AlchemicalStatus.ADVISORY_ONLY,
        residual_delta=trace.residual_delta_total(),
        compression_gain=trace.compression_gain_total(),
        advisory_notes=("projection remains advisory except for verifier-bound or chain-audited results",),
    )
    return alchemical


def projection_trace_to_agent_experiences(trace: ProjectionTrace) -> list[AgentExperience]:
    agent_id = trace.agent_id or "projection-engine"
    experiences: list[AgentExperience] = []
    for result in trace.results:
        outcome = _experience_outcome(result)
        experiences.append(
            AgentExperience(
                experience_id=content_id("projection_exp", result.to_dict(), n=24),
                agent_id=agent_id,
                episode_id=trace.episode_id,
                claim_id=result.metadata.get("candidate", {}).get("candidate_id", result.candidate_id),
                route="projection_engine",
                phase=AlchemicalPhase.PROJECTION.value,
                outcome=outcome,
                terminal_form=result.terminal_form if result.is_terminal() else None,
                certificate_id=(result.derived_certificate_id or result.lawbook_entry_id) if result.is_terminal() else None,
                cost_units=0.0,
                residual_delta=result.residual_delta,
                compression_gain=result.compression_gain,
                projection_gain=result.projection_gain,
                verifier_boundary_crossed=result.is_terminal(),
                scar_tags=("projection_rejected",) if result.status == ProjectionStatus.REJECTED else (),
                metadata={"projection_result": result.to_dict(), "advisory_boundary_preserved": True},
            )
        )
    return experiences


def make_projection_candidate_id(payload: Mapping[str, Any]) -> str:
    return content_id("projection_candidate", payload, n=24)


def make_projection_result_id(*parts: Any) -> str:
    return content_id("projection_result", parts, n=24)


def make_projection_trace_id(*parts: Any) -> str:
    return content_id("projection_trace", parts, n=24)


def _derived_candidates(entries: Sequence[Mapping[str, Any]]) -> list[ProjectionCandidate]:
    proofs = [entry for entry in entries if _terminal(entry.get("terminal_form")) == TerminalForm.VERIFIED_PROOF]
    false_entries = [entry for entry in entries if _terminal(entry.get("terminal_form")) == TerminalForm.FINITE_COUNTERMODEL]
    candidates: list[ProjectionCandidate] = []
    for left in proofs:
        for right in proofs:
            if _text(left.get("target")) == _text(right.get("source")):
                candidates.append(transitivity_projection(left, right))
    for false_entry in false_entries:
        for proof in proofs:
            if _text(false_entry.get("source")) == _text(proof.get("source")):
                candidates.append(source_weakening_false_projection(false_entry, proof))
            if _text(false_entry.get("target")) == _text(proof.get("target")):
                candidates.append(target_strengthening_false_projection(false_entry, proof))
    deduped: list[ProjectionCandidate] = []
    seen: set[tuple[str | None, str | None, str]] = set()
    for candidate in candidates:
        key = (candidate.source, candidate.target, candidate.rule_kind.value)
        if candidate.source == candidate.target or key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
    return deduped


def _result_for_candidate(candidate: ProjectionCandidate) -> ProjectionResult:
    if candidate.metadata.get("chain_safe") is True and candidate.rule_kind in {
        ProjectionRuleKind.TRANSITIVITY,
        ProjectionRuleKind.SOURCE_WEAKENING_FALSE,
        ProjectionRuleKind.TARGET_STRENGTHENING_FALSE,
    }:
        terminal = (
            TerminalForm.VERIFIED_PROOF
            if candidate.rule_kind == ProjectionRuleKind.TRANSITIVITY
            else TerminalForm.FINITE_COUNTERMODEL
        )
        derived_id = content_id("derived_projection", candidate.to_dict(), n=24)
        return ProjectionResult(
            result_id=make_projection_result_id(candidate.candidate_id, "derived"),
            candidate_id=candidate.candidate_id,
            status=ProjectionStatus.DERIVED_CERTIFICATE,
            terminal_form=terminal,
            derived_certificate_id=derived_id,
            residual_delta=-1,
            compression_gain=0.75,
            projection_gain=1.0,
            advisory_notes=("chain-safe derived certificate by verified lawbook composition",),
            metadata={"candidate": candidate.to_dict(), "chain_audited": True},
        )
    return _advisory_result(candidate, ProjectionStatus.ADVISORY_ONLY)


def _advisory_result(candidate: ProjectionCandidate, status: ProjectionStatus) -> ProjectionResult:
    return ProjectionResult(
        result_id=make_projection_result_id(candidate.candidate_id, status.value),
        candidate_id=candidate.candidate_id,
        status=status,
        residual_delta=-1 if status == ProjectionStatus.RESIDUAL_SPLIT else 0,
        compression_gain=0.1 if status == ProjectionStatus.RESIDUAL_SPLIT else 0.0,
        projection_gain=0.25 if status == ProjectionStatus.RESIDUAL_SPLIT else 0.0,
        advisory_notes=("projection pressure only", "not terminal truth"),
        metadata={"candidate": candidate.to_dict(), "advisory_only": True},
    )


def _projection_summary(trace: ProjectionTrace) -> dict[str, Any]:
    return {
        "candidates_total": len(trace.candidates),
        "terminal_results": trace.terminal_count(),
        "advisory_results": trace.advisory_count(),
        "known_skips": sum(1 for result in trace.results if result.status == ProjectionStatus.KNOWN_SKIP),
        "derived_certificates": sum(1 for result in trace.results if result.status == ProjectionStatus.DERIVED_CERTIFICATE),
        "residual_splits": sum(1 for result in trace.results if result.status == ProjectionStatus.RESIDUAL_SPLIT),
        "obstruction_pressure": sum(1 for result in trace.results if result.status == ProjectionStatus.OBSTRUCTION_PRESSURE),
        "rejected": sum(1 for result in trace.results if result.status == ProjectionStatus.REJECTED),
        "residual_delta_total": trace.residual_delta_total(),
        "compression_gain_total": trace.compression_gain_total(),
        "projection_gain_total": trace.projection_gain_total(),
    }


def _projection_candidate(
    *,
    source: str | None,
    target: str | None,
    rule_kind: ProjectionRuleKind,
    parents: Sequence[Mapping[str, Any]],
    confidence: float,
    advisory: bool,
    reason: str,
    metadata: Mapping[str, Any],
) -> ProjectionCandidate:
    payload = {
        "source": source,
        "target": target,
        "rule_kind": rule_kind.value,
        "parents": [_compact_entry(parent) for parent in parents],
        "metadata": dict(metadata),
    }
    return ProjectionCandidate(
        candidate_id=make_projection_candidate_id(payload),
        source_claim_id=_entry_claim_id(parents[0]) if parents else None,
        target_claim_id=_entry_claim_id(parents[-1]) if parents else None,
        source=source,
        target=target,
        rule_kind=rule_kind,
        originating_lawbook_entry_id=_entry_id(parents[0]) if parents else None,
        originating_certificate_id=_entry_certificate_id(parents[0]) if parents else None,
        confidence=confidence,
        advisory=advisory,
        reason=reason,
        metadata={**dict(metadata), "parents": [_compact_entry(parent) for parent in parents]},
    )


def _candidate_for_pair(
    pair: Mapping[str, Any],
    rule_kind: ProjectionRuleKind,
    *,
    lawbook_entry: Mapping[str, Any] | None = None,
    advisory: bool,
    confidence: float,
    reason: str,
    metadata: Mapping[str, Any] | None = None,
) -> ProjectionCandidate:
    source, target = _source_target(pair)
    source_idx, target_idx = _source_target_idx(pair)
    payload = {
        "pair": dict(pair),
        "rule_kind": rule_kind.value,
        "lawbook_entry_id": _entry_id(lawbook_entry or {}),
        "advisory": advisory,
    }
    return ProjectionCandidate(
        candidate_id=make_projection_candidate_id(payload),
        source_claim_id=_optional_str(pair.get("source_claim_id") or pair.get("claim_id")),
        target_claim_id=_optional_str(pair.get("target_claim_id")),
        source_idx=source_idx,
        target_idx=target_idx,
        source=source,
        target=target,
        rule_kind=rule_kind,
        originating_lawbook_entry_id=_entry_id(lawbook_entry or {}),
        originating_certificate_id=_entry_certificate_id(lawbook_entry or {}),
        confidence=confidence,
        advisory=advisory,
        reason=reason,
        metadata=dict(metadata or {}),
    )


def _experience_outcome(result: ProjectionResult) -> AgentExperienceOutcome:
    if result.status == ProjectionStatus.KNOWN_SKIP:
        return AgentExperienceOutcome.KNOWN_SKIPPED
    if result.status == ProjectionStatus.DERIVED_CERTIFICATE and result.terminal_form == TerminalForm.VERIFIED_PROOF:
        return AgentExperienceOutcome.VERIFIED_PROOF
    if result.status == ProjectionStatus.DERIVED_CERTIFICATE and result.terminal_form == TerminalForm.FINITE_COUNTERMODEL:
        return AgentExperienceOutcome.FINITE_COUNTERMODEL
    if result.status == ProjectionStatus.REJECTED:
        return AgentExperienceOutcome.INVALID_CANDIDATE
    if result.status == ProjectionStatus.RESIDUAL_SPLIT:
        return AgentExperienceOutcome.RESIDUAL
    return AgentExperienceOutcome.ADVISORY_ONLY


def _nearest_entry(pair: Mapping[str, Any], entries: Sequence[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    source, target = _source_target(pair)
    for entry in entries:
        if _text(entry.get("source")) == source or _text(entry.get("target")) == target:
            return entry
    return entries[0] if entries else None


def _pair_in_entries(candidate: ProjectionCandidate, entries: Sequence[Mapping[str, Any]]) -> bool:
    return any(_entry_matches(entry, candidate.source, candidate.target, candidate.source_idx, candidate.target_idx) for entry in entries)


def _entry_matches(
    entry: Mapping[str, Any],
    source: str | None,
    target: str | None,
    source_idx: int | None,
    target_idx: int | None,
) -> bool:
    entry_source, entry_target = _source_target(entry)
    entry_source_idx, entry_target_idx = _source_target_idx(entry)
    text_match = source is not None and target is not None and source == entry_source and target == entry_target
    idx_match = (
        source_idx is not None
        and target_idx is not None
        and source_idx == entry_source_idx
        and target_idx == entry_target_idx
    )
    return text_match or idx_match


def _is_verified_or_chain_audited(entry: Mapping[str, Any]) -> bool:
    status = _text(entry.get("verification_status"))
    trust = _text(entry.get("trust_level"))
    boundary = _text(entry.get("verifier_boundary"))
    if status in {"VERIFIED", "REFUTED", "OBSTRUCTED", "DERIVED_VERIFIED", "DERIVED_REFUTED"}:
        return True
    if trust in {"derived_from_verified_traces", "DERIVED_CHAIN_VERIFIED", "FINITE_VERIFIED", "LEAN_VERIFIED"}:
        return True
    return boundary in {"CHAIN_AUDITED", "IMPORTER_REVALIDATED", "FINITE_CHECKED", "LEAN_TYPECHECKED"}


def _source_target(record: Mapping[str, Any]) -> tuple[str | None, str | None]:
    return _text(record.get("source") or record.get("source_expr")), _text(record.get("target") or record.get("target_expr"))


def _source_target_idx(record: Mapping[str, Any]) -> tuple[int | None, int | None]:
    return _optional_int(record.get("source_idx")), _optional_int(record.get("target_idx"))


def _compact_entry(entry: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "entry_id": _entry_id(entry),
        "claim_id": _entry_claim_id(entry),
        "certificate_id": _entry_certificate_id(entry),
        "source": entry.get("source"),
        "target": entry.get("target"),
        "source_idx": entry.get("source_idx"),
        "target_idx": entry.get("target_idx"),
        "terminal_form": entry.get("terminal_form"),
        "verification_status": entry.get("verification_status"),
        "trust_level": entry.get("trust_level"),
    }


def _entry_id(entry: Mapping[str, Any]) -> str | None:
    return _optional_str(entry.get("lawbook_entry_id") or entry.get("entry_id") or entry.get("id") or entry.get("claim_id") or entry.get("claim"))


def _entry_claim_id(entry: Mapping[str, Any]) -> str | None:
    return _optional_str(entry.get("claim_id") or entry.get("claim_hash") or entry.get("claim"))


def _entry_certificate_id(entry: Mapping[str, Any]) -> str | None:
    return _optional_str(entry.get("certificate_id") or entry.get("derived_certificate_id"))


def _terminal(value: Any) -> TerminalForm | None:
    if value in (None, ""):
        return None
    if isinstance(value, TerminalForm):
        return value
    return TerminalForm(str(value))


def _optional_terminal_form(value: Any) -> TerminalForm | None:
    try:
        return _terminal(value)
    except ValueError:
        return None


def _text(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value)


def _optional_str(value: Any) -> str | None:
    return _text(value)


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _limit_reached(candidates: Sequence[ProjectionCandidate], max_candidates: int | None) -> bool:
    return max_candidates is not None and len(candidates) >= max_candidates
