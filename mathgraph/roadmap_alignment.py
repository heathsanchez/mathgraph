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
    summary: Mapping[str, Any] | None = None,
) -> RoadmapAlignmentReport:
    """Check whether a run preserves MathGraph advisory/truth boundaries."""

    summary_data = dict(summary or {})
    findings: list[RoadmapAlignmentFinding] = []
    traces = list(alchemical_traces)
    experiences = list(agent_experiences)

    _check_traces(traces, findings)
    _check_experiences(experiences, findings)
    _check_summary(summary_data, findings)
    _check_cross_record_warnings(traces, experiences, summary_data, findings)
    _add_positive_findings(traces, experiences, summary_data, findings)

    report_summary = {
        **summary_data,
        "alchemical_trace_count": len(traces),
        "agent_experience_count": len(experiences),
        "promoted_trace_count": sum(1 for trace in traces if trace.is_promoted()),
        "verifier_boundary_experience_count": sum(1 for exp in experiences if exp.verifier_boundary_crossed),
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
    summary: Mapping[str, Any],
    findings: list[RoadmapAlignmentFinding],
) -> None:
    if traces or experiences or summary:
        if not _has_metric(summary, "residual_compression") and not any(
            trace.total_compression_gain() for trace in traces
        ) and not any(exp.compression_gain for exp in experiences):
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


def _add_positive_findings(
    traces: Sequence[AlchemicalTrace],
    experiences: Sequence[AgentExperience],
    summary: Mapping[str, Any],
    findings: list[RoadmapAlignmentFinding],
) -> None:
    if traces or experiences:
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
