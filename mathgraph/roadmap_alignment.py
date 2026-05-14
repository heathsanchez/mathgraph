"""Roadmap doctrine checks for advisory and verifier-bound MathGraph records."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from mathgraph.agent_biography import AgentExperience, AgentExperienceOutcome
from mathgraph.alchemy import AlchemicalPhase, AlchemicalStatus, AlchemicalTrace
from mathgraph.certificates import TerminalForm
from mathgraph.proof_verification import (
    ProofArtifactKind,
    ProofVerificationStatus,
    ProofVerificationTrace,
    ProofVerifierKind,
)
from mathgraph.projection import ProjectionRuleKind, ProjectionStatus, ProjectionTrace
from mathgraph.root_constructors import RootConstructorStatus, RootConstructorTrace


@dataclass(frozen=True)
class RoadmapAlignmentFinding:
    severity: str
    code: str
    message: str
    recommendation: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "recommendation": self.recommendation,
        }


@dataclass
class RoadmapAlignmentReport:
    checked_at: str
    summary: dict[str, Any]
    findings: list[RoadmapAlignmentFinding] = field(default_factory=list)

    def critical_count(self) -> int:
        return sum(1 for finding in self.findings if finding.severity == "critical")

    def warning_count(self) -> int:
        return sum(1 for finding in self.findings if finding.severity == "warning")

    def info_count(self) -> int:
        return sum(1 for finding in self.findings if finding.severity == "info")

    def is_aligned(self) -> bool:
        return self.critical_count() == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "checked_at": self.checked_at,
            "summary": dict(self.summary),
            "findings": [finding.to_dict() for finding in self.findings],
            "critical_count": self.critical_count(),
            "warning_count": self.warning_count(),
            "info_count": self.info_count(),
            "is_aligned": self.is_aligned(),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, indent=2) + "\n"

    def write_json(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.to_json(), encoding="utf-8")

    def write_markdown(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "# Roadmap Alignment Report",
            "",
            f"- Checked at: `{self.checked_at}`",
            f"- Aligned: `{self.is_aligned()}`",
            f"- Critical: `{self.critical_count()}`",
            f"- Warnings: `{self.warning_count()}`",
            f"- Info: `{self.info_count()}`",
            "",
            "## Findings",
            "",
        ]
        if not self.findings:
            lines.append("No findings.")
        for finding in self.findings:
            lines.append(f"- **{finding.severity.upper()}** `{finding.code}`: {finding.message}")
            if finding.recommendation:
                lines.append(f"  Recommendation: {finding.recommendation}")
        target.write_text("\n".join(lines) + "\n", encoding="utf-8")


def check_roadmap_alignment(
    *,
    alchemical_traces: Sequence[AlchemicalTrace] = (),
    agent_experiences: Sequence[AgentExperience] = (),
    projection_traces: Sequence[ProjectionTrace] = (),
    root_constructor_traces: Sequence[RootConstructorTrace] = (),
    proof_verification_traces: Sequence[ProofVerificationTrace] = (),
    summary: Mapping[str, Any] | None = None,
) -> RoadmapAlignmentReport:
    """Check whether a run preserves MathGraph advisory/truth boundaries."""

    summary_data = dict(summary or {})
    findings: list[RoadmapAlignmentFinding] = []
    traces = list(alchemical_traces)
    experiences = list(agent_experiences)
    projections = list(projection_traces)
    root_constructors = list(root_constructor_traces)
    proof_traces = list(proof_verification_traces)

    _check_traces(traces, findings)
    _check_experiences(experiences, findings)
    _check_projection_traces(projections, findings)
    _check_root_constructor_traces(root_constructors, findings)
    _check_proof_verification_traces(proof_traces, findings)
    _check_summary(summary_data, findings)
    _check_cross_record_warnings(traces, experiences, projections, root_constructors, proof_traces, summary_data, findings)
    _add_positive_findings(traces, experiences, projections, root_constructors, proof_traces, summary_data, findings)

    report_summary = {
        **summary_data,
        "alchemical_trace_count": len(traces),
        "agent_experience_count": len(experiences),
        "projection_trace_count": len(projections),
        "root_constructor_trace_count": len(root_constructors),
        "proof_verification_trace_count": len(proof_traces),
        "promoted_trace_count": sum(1 for trace in traces if trace.is_promoted()),
        "verifier_boundary_experience_count": sum(1 for exp in experiences if exp.verifier_boundary_crossed),
        "projection_terminal_count": sum(trace.terminal_count() for trace in projections),
        "root_constructor_terminal_count": sum(trace.terminal_count() for trace in root_constructors),
        "proof_verification_terminal_count": sum(trace.terminal_count() for trace in proof_traces),
    }
    return RoadmapAlignmentReport(
        checked_at=datetime.now(timezone.utc).isoformat(),
        summary=report_summary,
        findings=findings,
    )


def _check_traces(traces: Sequence[AlchemicalTrace], findings: list[RoadmapAlignmentFinding]) -> None:
    for trace in traces:
        if trace.terminal_form and not trace.is_promoted():
            findings.append(
                RoadmapAlignmentFinding(
                    "critical",
                    "TRACE_TERMINAL_WITHOUT_PROMOTION",
                    f"Trace {trace.trace_id} carries terminal form {trace.terminal_form.value} without verifier promotion.",
                    "Attach a verifier-promoted certificate record or keep the trace advisory.",
                )
            )
        for step in trace.steps:
            text = " ".join(
                str(value)
                for value in [
                    step.failure_reason,
                    step.route,
                    " ".join(step.advisory_notes),
                    json.dumps(step.metadata, sort_keys=True),
                ]
                if value
            ).lower()
            if ("no countermodel" in text or "finite-search miss" in text or "finite search miss" in text) and (
                trace.terminal_form == TerminalForm.VERIFIED_PROOF
            ):
                findings.append(
                    RoadmapAlignmentFinding(
                        "critical",
                        "FINITE_SEARCH_MISS_AS_PROOF",
                        f"Trace {trace.trace_id} appears to represent finite-search failure as a proof.",
                        "Record bounded failure as residual or advisory pressure unless a proof verifier promotes it.",
                    )
                )
            if (
                step.status == AlchemicalStatus.ADVISORY_ONLY
                and step.metadata.get("terminal_form") in _terminal_values()
            ):
                findings.append(
                    RoadmapAlignmentFinding(
                        "critical",
                        "ADVISORY_STEP_CLAIMS_TERMINAL",
                        f"Advisory step in trace {trace.trace_id} claims terminal truth.",
                        "Move terminal claims behind the verifier/importer boundary.",
                    )
                )


def _check_experiences(
    experiences: Sequence[AgentExperience], findings: list[RoadmapAlignmentFinding]
) -> None:
    advisory_outcomes = {
        AgentExperienceOutcome.RESIDUAL,
        AgentExperienceOutcome.FAILED_SEARCH,
        AgentExperienceOutcome.INVALID_CANDIDATE,
        AgentExperienceOutcome.KNOWN_SKIPPED,
        AgentExperienceOutcome.ADVISORY_ONLY,
    }
    for exp in experiences:
        if exp.terminal_form and not exp.verifier_boundary_crossed and exp.outcome not in advisory_outcomes:
            findings.append(
                RoadmapAlignmentFinding(
                    "critical",
                    "EXPERIENCE_TERMINAL_WITHOUT_BOUNDARY",
                    f"Experience {exp.experience_id} carries {exp.terminal_form.value} without crossing the verifier boundary.",
                    "Keep agent memory advisory unless a verifier/importer boundary was crossed.",
                )
            )
        if exp.outcome in {AgentExperienceOutcome.VERIFIED_PROOF, AgentExperienceOutcome.FINITE_COUNTERMODEL}:
            if not exp.verifier_boundary_crossed or not exp.certificate_id:
                findings.append(
                    RoadmapAlignmentFinding(
                        "critical",
                        "ADVISORY_OUTCOME_FALSELY_TERMINAL",
                        f"Experience {exp.experience_id} reports {exp.outcome.value} without certificate-backed verification.",
                        "Use RESIDUAL, FAILED_SEARCH, or ADVISORY_ONLY for unpromoted agent outcomes.",
                    )
                )
        if exp.outcome == AgentExperienceOutcome.FAILED_SEARCH and exp.terminal_form == TerminalForm.VERIFIED_PROOF:
            findings.append(
                RoadmapAlignmentFinding(
                    "critical",
                    "FAILED_SEARCH_AS_PROOF",
                    f"Experience {exp.experience_id} turns failed search into VERIFIED_PROOF.",
                    "Failed bounded search can sharpen residuals but cannot prove a theorem.",
                )
            )


def _check_projection_traces(
    projection_traces: Sequence[ProjectionTrace], findings: list[RoadmapAlignmentFinding]
) -> None:
    never_terminal_statuses = {
        ProjectionStatus.ADVISORY_ONLY,
        ProjectionStatus.CANDIDATE,
        ProjectionStatus.OBSTRUCTION_PRESSURE,
        ProjectionStatus.RESIDUAL_SPLIT,
        ProjectionStatus.REJECTED,
    }
    for trace in projection_traces:
        for result in trace.results:
            if result.terminal_form and not result.is_terminal():
                findings.append(
                    RoadmapAlignmentFinding(
                        "critical",
                        "PROJECTION_TERMINAL_WITHOUT_BOUNDARY",
                        f"Projection result {result.result_id} carries terminal form without verifier boundary or derived certificate id.",
                        "Keep projection pressure advisory unless lawbook-backed, chain-audited, or revalidated.",
                    )
                )
            if result.status in never_terminal_statuses and result.terminal_form:
                code = (
                    "REJECTED_PROJECTION_CLAIMS_TERMINAL"
                    if result.status == ProjectionStatus.REJECTED
                    else "ADVISORY_PROJECTION_CLAIMS_TERMINAL"
                )
                findings.append(
                    RoadmapAlignmentFinding(
                        "critical",
                        code,
                        f"Projection result {result.result_id} has status {result.status.value} but claims terminal truth.",
                        "Remove terminal form from advisory/rejected projection results.",
                    )
                )
        if any(candidate.rule_kind == ProjectionRuleKind.ADVISORY_SIMILARITY for candidate in trace.candidates):
            metadata_text = json.dumps(trace.to_dict(), sort_keys=True).lower()
            if "advisory" not in metadata_text:
                findings.append(
                    RoadmapAlignmentFinding(
                        "warning",
                        "ADVISORY_SIMILARITY_WITHOUT_DISCLAIMER",
                        f"Projection trace {trace.trace_id} uses advisory similarity without advisory disclaimer metadata.",
                        "Mark advisory similarity output as scheduling pressure only.",
                    )
                )


def _check_root_constructor_traces(
    root_constructor_traces: Sequence[RootConstructorTrace], findings: list[RoadmapAlignmentFinding]
) -> None:
    for trace in root_constructor_traces:
        for signal in trace.root_signals:
            if _dict_claims_terminal(signal.to_dict()):
                findings.append(
                    RoadmapAlignmentFinding(
                        "critical",
                        "ROOT_SIGNAL_CLAIMS_TERMINAL",
                        f"Root signal {signal.root_id} claims terminal truth.",
                        "Keep root signals advisory; only verifier/importer records may carry terminal forms.",
                    )
                )
        for plan in trace.plans:
            if _dict_claims_terminal(plan.to_dict()):
                findings.append(
                    RoadmapAlignmentFinding(
                        "critical",
                        "CONSTRUCTOR_PLAN_CLAIMS_TERMINAL",
                        f"Constructor plan {plan.plan_id} claims terminal truth.",
                        "Plans are advisory and must not contain accepted terminal truth.",
                    )
                )
        for attempt in trace.attempts:
            if attempt.terminal_form == TerminalForm.FINITE_COUNTERMODEL and not attempt.is_terminal():
                findings.append(
                    RoadmapAlignmentFinding(
                        "critical",
                        "CONSTRUCTOR_FINITE_COUNTERMODEL_WITHOUT_IMPORTER",
                        f"Constructor attempt {attempt.attempt_id} claims FINITE_COUNTERMODEL without importer verification.",
                        "Promote only importer-revalidated finite countermodel certificates.",
                    )
                )
            if attempt.status == RootConstructorStatus.CANDIDATE_TABLE_FOUND and attempt.terminal_form:
                findings.append(
                    RoadmapAlignmentFinding(
                        "critical",
                        "CANDIDATE_TABLE_TREATED_AS_TERMINAL",
                        f"Constructor attempt {attempt.attempt_id} treats a candidate table as terminal.",
                        "Candidate tables must pass importer/revalidator before becoming certificates.",
                    )
                )
            if attempt.status == RootConstructorStatus.SEARCH_MISS and attempt.terminal_form == TerminalForm.VERIFIED_PROOF:
                findings.append(
                    RoadmapAlignmentFinding(
                        "critical",
                        "SEARCH_MISS_AS_VERIFIED_PROOF",
                        f"Constructor attempt {attempt.attempt_id} treats a search miss as VERIFIED_PROOF.",
                        "Finite-search misses are residuals, not TRUE proofs.",
                    )
                )
            if attempt.status == RootConstructorStatus.IMPORTER_REJECTED and attempt.terminal_form:
                findings.append(
                    RoadmapAlignmentFinding(
                        "critical",
                        "IMPORTER_REJECTED_CLAIMS_TERMINAL",
                        f"Constructor attempt {attempt.attempt_id} has importer rejection but claims terminal truth.",
                        "Rejected imports must remain advisory/residual.",
                    )
                )


def _check_proof_verification_traces(
    proof_traces: Sequence[ProofVerificationTrace], findings: list[RoadmapAlignmentFinding]
) -> None:
    for trace in proof_traces:
        for artifact in trace.artifacts:
            if _dict_claims_terminal(artifact.to_dict()):
                findings.append(
                    RoadmapAlignmentFinding(
                        "critical",
                        "PROOF_ARTIFACT_CLAIMS_TERMINAL",
                        f"Proof artifact {artifact.artifact_id} claims terminal truth.",
                        "Proof motifs, lemmas, sketches, and skeletons must remain advisory until verified.",
                    )
                )
        for result in trace.results:
            if result.terminal_form == TerminalForm.VERIFIED_PROOF and not result.is_terminal():
                findings.append(
                    RoadmapAlignmentFinding(
                        "critical",
                        "PROOF_VERIFIED_WITHOUT_BOUNDARY",
                        f"Proof result {result.result_id} claims VERIFIED_PROOF without a trusted boundary.",
                        "Require verifier/importer/chain-audit success plus certificate id.",
                    )
                )
            if result.status in {
                ProofVerificationStatus.SKELETON_GENERATED,
                ProofVerificationStatus.VERIFIER_FAILED,
                ProofVerificationStatus.VERIFIER_NOT_RUN,
            } and result.terminal_form:
                findings.append(
                    RoadmapAlignmentFinding(
                        "critical",
                        "UNVERIFIED_PROOF_STATUS_CLAIMS_TERMINAL",
                        f"Proof result {result.result_id} has status {result.status.value} but claims terminal truth.",
                        "Skeletons, failed verifier runs, and not-run results cannot become VERIFIED_PROOF.",
                    )
                )
            if (
                result.verifier_kind == ProofVerifierKind.MOCK_VERIFIER
                and result.is_terminal()
                and result.metadata.get("test_only") is not True
            ):
                findings.append(
                    RoadmapAlignmentFinding(
                        "critical",
                        "MOCK_VERIFIER_PRODUCTION_TRUTH",
                        f"Proof result {result.result_id} treats mock verifier output as production truth.",
                        "Mock verifier output must be test-only and cannot be production trust.",
                    )
                )
            if result.status == ProofVerificationStatus.IMPORTED_VERIFIED:
                provenance = result.metadata.get("provenance", {})
                if not result.certificate_id and not result.metadata.get("external_certificate_id"):
                    findings.append(
                        RoadmapAlignmentFinding(
                            "critical",
                            "IMPORTED_PROOF_WITHOUT_CERTIFICATE",
                            f"Imported proof result {result.result_id} lacks external certificate/provenance.",
                            "Trusted imports need an external certificate id or verified provenance.",
                        )
                    )
                if isinstance(provenance, Mapping) and not (provenance.get("verified") is True or result.metadata.get("external_certificate_id")):
                    findings.append(
                        RoadmapAlignmentFinding(
                            "critical",
                            "IMPORTED_PROOF_UNVERIFIED_PROVENANCE",
                            f"Imported proof result {result.result_id} lacks verified provenance.",
                            "Trusted imports must preserve verified provenance.",
                        )
                    )


def _check_summary(summary: Mapping[str, Any], findings: list[RoadmapAlignmentFinding]) -> None:
    text = json.dumps(summary, sort_keys=True).lower()
    if ("no_countermodel_found" in text or "finite_search_miss" in text) and "verified_proof" in text:
        findings.append(
            RoadmapAlignmentFinding(
                "critical",
                "SUMMARY_FINITE_MISS_AS_PROOF",
                "Summary appears to treat a finite-search miss as VERIFIED_PROOF.",
                "Require a verified proof route before claiming VERIFIED_PROOF.",
            )
        )
    advisory_truth_keys = ("route", "h_tilt", "htilt", "root", "motif")
    if any(key in text for key in advisory_truth_keys) and any(
        str(summary.get(key, "")).upper() in _terminal_values()
        for key in ("terminal_form", "truth", "accepted_claim", "claim_status")
    ):
        findings.append(
            RoadmapAlignmentFinding(
                "critical",
                "ADVISORY_PRESSURE_AS_TRUTH",
                "Summary appears to treat route/H-tilt/root/motif pressure as terminal truth.",
                "Keep advisory scores separate from accepted terminal forms.",
            )
        )
    if ("h_tilt" in text or "htilt" in text or "beta" in summary) and not _has_advisory_disclaimer(summary):
        findings.append(
            RoadmapAlignmentFinding(
                "warning",
                "HTILT_WITHOUT_ADVISORY_DISCLAIMER",
                "H-tilt score or beta appears without advisory disclaimer metadata.",
                "Add metadata declaring H-tilt output advisory-only.",
            )
        )


def _check_cross_record_warnings(
    traces: Sequence[AlchemicalTrace],
    experiences: Sequence[AgentExperience],
    projection_traces: Sequence[ProjectionTrace],
    root_constructor_traces: Sequence[RootConstructorTrace],
    proof_traces: Sequence[ProofVerificationTrace],
    summary: Mapping[str, Any],
    findings: list[RoadmapAlignmentFinding],
) -> None:
    if traces or experiences or projection_traces or root_constructor_traces or proof_traces or summary:
        if not _has_metric(summary, "residual_compression") and not any(
            trace.total_compression_gain() for trace in traces
        ) and not any(exp.compression_gain for exp in experiences) and not any(
            trace.compression_gain_total() for trace in projection_traces
        ) and not any(
            trace.compression_gain_total() for trace in root_constructor_traces
        ) and not any(
            trace.compression_gain_total() for trace in proof_traces
        ):
            findings.append(
                RoadmapAlignmentFinding(
                    "warning",
                    "NO_RESIDUAL_COMPRESSION_METRIC",
                    "No residual compression metric is present.",
                    "Record compression gain or explain why it is unavailable.",
                )
            )
        if not _has_metric(summary, "derived_amplification") and not any(
            exp.derived_amplification for exp in experiences
        ) and not any(
            trace.summary.get("derived_certificates", 0) for trace in projection_traces
        ) and not any(
            trace.summary.get("importer_verified", 0) for trace in root_constructor_traces
        ) and not any(
            trace.terminal_count() for trace in proof_traces
        ):
            findings.append(
                RoadmapAlignmentFinding(
                    "warning",
                    "NO_DERIVED_AMPLIFICATION_METRIC",
                    "No derived amplification metric is present.",
                    "Track whether fixed law compounds into additional claims.",
                )
            )
    trace_episodes = {trace.episode_id for trace in traces if trace.episode_id}
    experience_episodes = {exp.episode_id for exp in experiences if exp.episode_id}
    for episode_id in sorted(trace_episodes - experience_episodes):
        findings.append(
            RoadmapAlignmentFinding(
                "warning",
                "NO_AGENT_EXPERIENCE_FOR_EPISODE",
                f"Episode {episode_id} has alchemical traces but no agent experience.",
                "Record at least lightweight policy memory for the episode.",
            )
        )
    if traces and not any(trace.has_phase(AlchemicalPhase.PROJECTION) for trace in traces):
        findings.append(
            RoadmapAlignmentFinding(
                "warning",
                "NO_PROJECTION_PHASE",
                "No projection phase appears in alchemical traces.",
                "Record projection when fixed law is applied back to residuals.",
            )
        )
    failures = [exp for exp in experiences if exp.outcome in {AgentExperienceOutcome.FAILED_SEARCH, AgentExperienceOutcome.INVALID_CANDIDATE}]
    if failures and not any(
        exp.outcome in {AgentExperienceOutcome.RESIDUAL, AgentExperienceOutcome.NAMED_OBSTRUCTION}
        or exp.scar_tags
        or exp.obstruction_id
        for exp in experiences
    ):
        findings.append(
            RoadmapAlignmentFinding(
                "warning",
                "FAILURE_WITHOUT_RESIDUAL_OR_OBSTRUCTION",
                "A failure was recorded without residual, obstruction, or scar memory.",
                "Convert failed routes into residual structure or named obstruction pressure.",
            )
        )
    for exp in experiences:
        if exp.cost_units >= 100.0 and not (
            exp.residual_delta or exp.compression_gain or exp.projection_gain
        ):
            findings.append(
                RoadmapAlignmentFinding(
                    "warning",
                    "HIGH_COST_NO_GAIN",
                    f"Experience {exp.experience_id} has high cost without residual/compression/projection gain.",
                    "Use cost scars or adjust scheduling taste.",
                )
            )
    for trace in projection_traces:
        if trace.candidates and not trace.results:
            findings.append(
                RoadmapAlignmentFinding(
                    "warning",
                    "PROJECTION_CANDIDATES_WITHOUT_RESULTS",
                    f"Projection trace {trace.trace_id} has candidates but no results.",
                    "Record rejected or advisory results so projection replay is auditable.",
                )
            )
        if len(trace.candidates) >= 100 and not (
            trace.residual_delta_total() or trace.compression_gain_total() or trace.projection_gain_total()
        ):
            findings.append(
                RoadmapAlignmentFinding(
                    "warning",
                    "HIGH_PROJECTION_COUNT_NO_GAIN",
                    f"Projection trace {trace.trace_id} has many candidates but no residual/compression/projection gain.",
                    "Tune projection rules or record why the batch produced no measurable pressure.",
                )
            )
    for trace in root_constructor_traces:
        if len(trace.plans) >= 10 and not trace.attempts:
            findings.append(
                RoadmapAlignmentFinding(
                    "warning",
                    "MANY_CONSTRUCTOR_PLANS_NO_ATTEMPTS",
                    f"Root constructor trace {trace.trace_id} has many plans but zero attempts.",
                    "Run dry-run attempts or record why planning did not descend into attempts.",
                )
            )
        if trace.search_miss_count() >= 5 and not any(
            attempt.status in {RootConstructorStatus.RESIDUAL, RootConstructorStatus.OBSTRUCTION_NAMED}
            or attempt.obstruction_name
            for attempt in trace.attempts
        ):
            findings.append(
                RoadmapAlignmentFinding(
                    "warning",
                    "SEARCH_MISSES_WITHOUT_RESIDUAL_OR_OBSTRUCTION",
                    f"Root constructor trace {trace.trace_id} has many search misses without residual/obstruction naming.",
                    "Turn failed searches into sharper residuals or named obstruction pressure.",
                )
            )
        for attempt in trace.attempts:
            if attempt.cost_units >= 100.0 and not (
                attempt.residual_delta or attempt.compression_gain or attempt.projection_gain
            ):
                findings.append(
                    RoadmapAlignmentFinding(
                        "warning",
                        "HIGH_CONSTRUCTOR_COST_NO_GAIN",
                        f"Constructor attempt {attempt.attempt_id} has high cost without residual/compression/projection gain.",
                        "Record cost scars or tighten the constructor plan.",
                    )
                )
        if trace.summary.get("dry_run") and "advisory" not in json.dumps(trace.to_dict(), sort_keys=True).lower():
            findings.append(
                RoadmapAlignmentFinding(
                    "warning",
                    "DRY_RUN_WITHOUT_ADVISORY_DISCLAIMER",
                    f"Root constructor trace {trace.trace_id} is dry-run without advisory disclaimer metadata.",
                    "Mark dry-run constructor outputs advisory-only.",
                )
            )
        for signal in trace.root_signals:
            if signal.confidence >= 0.9 and signal.support <= 0 and not signal.metadata.get("provenance"):
                findings.append(
                    RoadmapAlignmentFinding(
                        "warning",
                        "HIGH_CONFIDENCE_ROOT_WITHOUT_SUPPORT",
                        f"Root signal {signal.root_id} has high confidence without support/provenance metadata.",
                        "Record support counts or provenance for high-confidence root pressure.",
                    )
                )
    for trace in proof_traces:
        skeleton_count = sum(
            1
            for artifact in trace.artifacts
            if artifact.kind in {ProofArtifactKind.LEAN_SKELETON, ProofArtifactKind.ISABELLE_SKELETON}
        )
        verifier_runs = sum(
            1
            for result in trace.results
            if result.status
            in {
                ProofVerificationStatus.VERIFIER_PASSED,
                ProofVerificationStatus.VERIFIER_FAILED,
                ProofVerificationStatus.IMPORTED_VERIFIED,
                ProofVerificationStatus.CHAIN_AUDITED,
            }
        )
        if skeleton_count >= 10 and verifier_runs == 0:
            findings.append(
                RoadmapAlignmentFinding(
                    "warning",
                    "MANY_SKELETONS_NO_VERIFIER_RUNS",
                    f"Proof trace {trace.trace_id} has many skeletons but no verifier runs.",
                    "Run a verifier/importer or keep the skeleton batch clearly advisory.",
                )
            )
        for artifact in trace.artifacts:
            if (artifact.source or artifact.target) and not artifact.metadata.get("encoding"):
                findings.append(
                    RoadmapAlignmentFinding(
                        "warning",
                        "PROOF_ARTIFACT_TEXT_WITHOUT_ENCODING",
                        f"Proof artifact {artifact.artifact_id} has source/target text but no encoding metadata.",
                        "Record formal encoding before treating source/target text as proof content.",
                    )
                )
        for result in trace.results:
            if result.verifier_kind not in {ProofVerifierKind.NONE, ProofVerifierKind.MOCK_VERIFIER}:
                if result.status == ProofVerificationStatus.VERIFIER_NOT_RUN and not result.command:
                    findings.append(
                        RoadmapAlignmentFinding(
                            "warning",
                            "PROOF_VERIFIER_COMMAND_MISSING",
                            f"Proof result {result.result_id} did not run because verifier command is missing.",
                            "Provide a verifier command or keep verifier_kind NONE.",
                        )
                    )
            if result.status == ProofVerificationStatus.CHAIN_AUDITED:
                parents = result.metadata.get("parent_certificate_ids", [])
                if result.metadata.get("chain_safe") is True and not parents:
                    findings.append(
                        RoadmapAlignmentFinding(
                            "warning",
                            "CHAIN_AUDIT_SAFE_WITHOUT_PARENTS",
                            f"Proof result {result.result_id} claims chain_safe without parent certificate ids.",
                            "Record parent certificate ids for chain-audited proof results.",
                        )
                    )
            if result.metadata.get("cost_units", 0.0) >= 100.0 and not (
                result.residual_delta or result.compression_gain or result.projection_gain
            ):
                findings.append(
                    RoadmapAlignmentFinding(
                        "warning",
                        "HIGH_PROOF_COST_NO_GAIN",
                        f"Proof result {result.result_id} has high cost without residual/compression/projection gain.",
                        "Record proof scars or tighten proof artifact generation.",
                    )
                )


def _add_positive_findings(
    traces: Sequence[AlchemicalTrace],
    experiences: Sequence[AgentExperience],
    projection_traces: Sequence[ProjectionTrace],
    root_constructor_traces: Sequence[RootConstructorTrace],
    proof_traces: Sequence[ProofVerificationTrace],
    summary: Mapping[str, Any],
    findings: list[RoadmapAlignmentFinding],
) -> None:
    if traces or experiences or projection_traces or root_constructor_traces or proof_traces:
        if not any(finding.severity == "critical" for finding in findings):
            findings.append(
                RoadmapAlignmentFinding(
                    "info",
                    "TERMINAL_CONTRACT_RESPECTED",
                    "No advisory record crossed into terminal truth without verifier promotion.",
                )
            )
    if any(trace.has_phase(AlchemicalPhase.PROJECTION) for trace in traces):
        findings.append(RoadmapAlignmentFinding("info", "PROJECTION_RECORDED", "Projection phase recorded."))
    if any(exp.taste_delta for exp in experiences) or summary.get("agent_taste_updated"):
        findings.append(RoadmapAlignmentFinding("info", "AGENT_TASTE_UPDATED", "Agent taste update recorded."))
    if any(exp.residual_delta for exp in experiences) or summary.get("residual_got_sharper"):
        findings.append(RoadmapAlignmentFinding("info", "RESIDUAL_GOT_SHARPER", "Residual got sharper."))
    if _has_metric(summary, "derived_amplification") or any(exp.derived_amplification for exp in experiences):
        findings.append(
            RoadmapAlignmentFinding("info", "DERIVED_AMPLIFICATION_OBSERVED", "Derived amplification observed.")
        )
    if any(exp.outcome == AgentExperienceOutcome.KNOWN_SKIPPED for exp in experiences):
        findings.append(
            RoadmapAlignmentFinding("info", "KNOWN_CLAIMS_SKIPPED", "Known claims skipped through lawbook memory.")
        )
    if any(
        result.status == ProjectionStatus.KNOWN_SKIP
        for trace in projection_traces
        for result in trace.results
    ):
        findings.append(RoadmapAlignmentFinding("info", "PROJECTION_KNOWN_SKIP_RECORDED", "Projection known skip recorded."))
    if any(
        result.status == ProjectionStatus.DERIVED_CERTIFICATE
        for trace in projection_traces
        for result in trace.results
    ):
        findings.append(
            RoadmapAlignmentFinding("info", "PROJECTION_DERIVED_CERTIFICATE_RECORDED", "Projection derived certificate recorded.")
        )
    if any(trace.residual_delta_total() for trace in projection_traces):
        findings.append(RoadmapAlignmentFinding("info", "PROJECTION_RESIDUAL_DELTA_IMPROVED", "Projection residual delta improved."))
    if any(trace.projection_gain_total() for trace in projection_traces):
        findings.append(RoadmapAlignmentFinding("info", "PROJECTION_GAIN_OBSERVED", "Projection gain observed."))
    if any(
        attempt.status == RootConstructorStatus.IMPORTER_VERIFIED
        for trace in root_constructor_traces
        for attempt in trace.attempts
    ):
        findings.append(
            RoadmapAlignmentFinding("info", "CONSTRUCTOR_IMPORTER_VERIFIED", "Importer-verified finite countermodel found.")
        )
    if any(
        attempt.status == RootConstructorStatus.CANDIDATE_TABLE_FOUND and not attempt.is_terminal()
        for trace in root_constructor_traces
        for attempt in trace.attempts
    ):
        findings.append(
            RoadmapAlignmentFinding(
                "info",
                "CANDIDATE_TABLE_BOUNDARY_PRESERVED",
                "Candidate table found while preserving verifier boundary.",
            )
        )
    if any(
        attempt.status in {RootConstructorStatus.SEARCH_MISS, RootConstructorStatus.RESIDUAL, RootConstructorStatus.OBSTRUCTION_NAMED}
        for trace in root_constructor_traces
        for attempt in trace.attempts
    ):
        findings.append(
            RoadmapAlignmentFinding("info", "CONSTRUCTOR_RESIDUAL_RECORDED", "Obstruction/residual recorded from constructor attempt.")
        )
    if any(trace.plans for trace in root_constructor_traces):
        findings.append(
            RoadmapAlignmentFinding("info", "ROOT_SIGNAL_COMPILED_TO_PLAN", "Root signal or residual pressure compiled into constructor plan.")
        )
    if any(trace.summary.get("bridge_exported") for trace in root_constructor_traces):
        findings.append(
            RoadmapAlignmentFinding(
                "info",
                "CONSTRUCTOR_BRIDGE_EXPORTED",
                "Constructor trace converted into alchemical trace or agent experience.",
            )
        )
    if any(
        result.status == ProofVerificationStatus.VERIFIER_PASSED
        for trace in proof_traces
        for result in trace.results
    ):
        findings.append(RoadmapAlignmentFinding("info", "PROOF_VERIFIER_PASSED", "Verifier-passed proof recorded."))
    if any(
        result.status == ProofVerificationStatus.IMPORTED_VERIFIED
        for trace in proof_traces
        for result in trace.results
    ):
        findings.append(RoadmapAlignmentFinding("info", "PROOF_IMPORTED_VERIFIED", "Imported verified proof recorded."))
    if any(
        result.status == ProofVerificationStatus.CHAIN_AUDITED
        for trace in proof_traces
        for result in trace.results
    ):
        findings.append(RoadmapAlignmentFinding("info", "PROOF_CHAIN_AUDITED", "Chain-audited proof recorded."))
    if any(
        artifact.kind in {ProofArtifactKind.LEAN_SKELETON, ProofArtifactKind.ISABELLE_SKELETON}
        for trace in proof_traces
        for artifact in trace.artifacts
    ):
        findings.append(RoadmapAlignmentFinding("info", "PROOF_SKELETON_BOUNDARY_PRESERVED", "Proof skeleton boundary preserved."))
    if any(
        result.status == ProofVerificationStatus.VERIFIER_FAILED
        for trace in proof_traces
        for result in trace.results
    ):
        findings.append(RoadmapAlignmentFinding("info", "PROOF_FAILURE_RECORDED", "Verifier failure recorded as residual/advisory."))


def _terminal_values() -> set[str]:
    return {terminal.value for terminal in TerminalForm}


def _has_metric(summary: Mapping[str, Any], name: str) -> bool:
    return any(name in str(key) and value not in (None, "") for key, value in summary.items())


def _has_advisory_disclaimer(summary: Mapping[str, Any]) -> bool:
    metadata = summary.get("metadata", summary)
    if not isinstance(metadata, Mapping):
        return False
    text = json.dumps(metadata, sort_keys=True).lower()
    return "advisory" in text and ("only" in text or "not truth" in text or "not terminal" in text)


def _dict_claims_terminal(data: Mapping[str, Any]) -> bool:
    if data.get("terminal_form") in _terminal_values():
        return True
    metadata = data.get("metadata")
    if isinstance(metadata, Mapping) and metadata.get("terminal_form") in _terminal_values():
        return True
    return False
