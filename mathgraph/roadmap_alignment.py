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
from mathgraph.continuation_actions import (
    ContinuationActionTrace,
    ContinuationOutputKind,
)
from mathgraph.continuation_curriculum import ContinuationCurriculum, CurriculumStageKind
from mathgraph.discovery_value import DiscoveryValueDecision, DiscoveryValueReport, DiscoveryValueScore
from mathgraph.domain_claims import (
    ClaimIRStatus,
    ClaimParseResult,
    DomainClaim,
    FormalWorldKind as DomainFormalWorldKind,
    FormalWorldRegistry,
)
from mathgraph.lean_adapter import LeanAdapterTrace, LeanArtifactStatus
from mathgraph.lawbook import LawbookEntry, LawbookReview, LawbookStore as AcceptedLawbookStore
from mathgraph.lawbook_query import (
    KnownSkipDecision,
    LawbookQuery,
    LawbookQueryAnswer,
    LawbookQueryReport,
    LawbookQueryReportStatus,
    LawbookQueryStatus,
)
from mathgraph.proof_verification import (
    ProofArtifactKind,
    ProofVerificationStatus,
    ProofVerificationTrace,
    ProofVerifierKind,
)
from mathgraph.proof_digestion import ProofDigestionTrace
from mathgraph.projection import ProjectionRuleKind, ProjectionStatus, ProjectionTrace
from mathgraph.root_constructors import RootConstructorStatus, RootConstructorTrace
from mathgraph.route_telemetry import RouteTelemetryLedger
from mathgraph.spectral_htilt import SpectralHTiltEstimate
from mathgraph.structural_identity import (
    StructuralGraph,
    StructuralIdentityReport,
    StructuralIdentityReportStatus,
    StructuralMatchKind,
    StructuralMergeCandidate,
    StructuralMergeDecision,
    StructuralSignature,
)
from mathgraph.habit_rules import (
    HabitCandidate,
    HabitFormationReport,
    HabitFormationReportStatus,
    HabitObservation,
    HabitReview,
    HabitRule,
    HabitStatus,
    HabitStore,
)
from mathgraph.reason_compression import ReasonCandidate,ReasonCompressionReport,ReasonCompressionReportStatus,ReasonNode,ReasonObservation,ReasonReview
from mathgraph.process_memory import ProcessContextItem,ProcessElimination,ProcessTransition,ProcessEpisodeRecord,ProcessMemoryQuery,ProcessMemoryAnswer,ProcessMemoryStore,ProcessMemoryReport,ProcessMemoryReportStatus
from mathgraph.structure_registry import StructureType,StructureDescriptor,StructureRegistryEntry,StructureMapping,TypedProjectionCandidate,StructureRegistryStore,StructureRegistryReport,StructureRegistryReportStatus,TypedProjectionStatus
from mathgraph.role_objects import RoleSignature,RoleDefinitionCandidate,RoleWitnessCandidate,RoleConjectureCandidate,RoleReview,RoleObject,RoleObjectReport,RoleObjectReportStatus,RoleWitnessStatus
from mathgraph.structural_analogy import AnalogySource,AnalogyFeatureMap,AnalogyBreak,StructuralAnalogyCandidate,ExpositionNote as AnalogyExpositionNote,AnalogyReview,StructuralAnalogyReport,StructuralAnalogyReportStatus,AnalogyCandidateStatus
from mathgraph.formal_world_adapters import FormalWorldAdapterSpec,FormalWorldAdapterCapability,FormalWorldParseResult,FormalWorldNormalizeResult,FormalWorldValidationResult,FormalWorldTask,FormalWorldHandoff,FormalWorldAdapterReport,FormalWorldAdapterReportStatus,HandoffStatus
from mathgraph.proof_system_integration import ProofSystemSpec,ProofProjectManifest,ProofArtifactManifest,ProofImportGraph,ProofCheckCommandContract,ProofCheckRequest,ProofCheckResult,TrustedProofImportRecord,ProofBoundaryEvidence,ProofSystemTask,ProofSystemIntegrationReport,ProofSystemIntegrationReportStatus,ProofArtifactStatus as ProofSystemArtifactStatus,CheckRequestStatus as ProofCheckRequestStatus,CheckResultStatus as ProofCheckResultStatus,TrustedImportStatus
from mathgraph.semantic_intake import SemanticSource,SemanticClaimSegment,SemanticClaimClassification,SemanticAmbiguity,SemanticExtraction,FormalizationRequest,SemanticRoutingHint,SemanticIntakeTask,SemanticIntakeReport,SemanticIntakeReportStatus,SemanticClaimKind,SemanticDomainKind
from mathgraph.api_service import ApiRequest,ApiResponse,ApiRouteResult,ApiHealth,ApiAuditResult,ApiServiceState,ApiTruthStatus,ApiRoute,ApiResponseStatus
from mathgraph.existential_agents import ExistentialAgent,AgentMortalityPolicy,AgentResourceAccount,AgentWound,AgentValueProfile,AgentNarrative,HeldInChoraRecord,AgentLineageRecord,AgentDaemon,AgentEcologyEvent,AgentEcologyReport,AgentEcologyReportStatus
from mathgraph.verification_episode import VerificationEpisodeStatus, VerificationEpisodeTrace
from mathgraph.verifier_feedback import (
    FlawSeverity,
    RepairActionKind,
    RepairLoopTrace,
    VerifierFeedback,
    VerifierFeedbackStatus,
)


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
    verification_episode_traces: Sequence[VerificationEpisodeTrace] = (),
    route_telemetry_ledgers: Sequence[RouteTelemetryLedger] = (),
    spectral_htilt_estimates: Sequence[SpectralHTiltEstimate] = (),
    domain_claims: Sequence[DomainClaim] = (),
    claim_parse_results: Sequence[ClaimParseResult] = (),
    formal_world_registries: Sequence[FormalWorldRegistry] = (),
    lean_adapter_traces: Sequence[LeanAdapterTrace] = (),
    continuation_action_traces: Sequence[ContinuationActionTrace] = (),
    proof_digestion_traces: Sequence[ProofDigestionTrace] = (),
    verifier_feedback_items: Sequence[VerifierFeedback] = (),
    repair_loop_traces: Sequence[RepairLoopTrace] = (),
    continuation_curricula: Sequence[ContinuationCurriculum] = (),
    discovery_value_reports: Sequence[DiscoveryValueReport] = (),
    discovery_value_scores: Sequence[DiscoveryValueScore] = (),
    lawbook_entries: Sequence[LawbookEntry] = (),
    lawbook_stores: Sequence[AcceptedLawbookStore] = (),
    lawbook_reviews: Sequence[LawbookReview] = (),
    lawbook_queries: Sequence[LawbookQuery] = (),
    lawbook_query_answers: Sequence[LawbookQueryAnswer] = (),
    lawbook_query_reports: Sequence[LawbookQueryReport] = (),
    structural_graphs: Sequence[StructuralGraph] = (),
    structural_signatures: Sequence[StructuralSignature] = (),
    structural_merge_candidates: Sequence[StructuralMergeCandidate] = (),
    structural_identity_reports: Sequence[StructuralIdentityReport] = (),
    habit_observations: Sequence[HabitObservation] = (),
    habit_candidates: Sequence[HabitCandidate] = (),
    habit_rules: Sequence[HabitRule] = (),
    habit_reviews: Sequence[HabitReview] = (),
    habit_stores: Sequence[HabitStore] = (),
    habit_reports: Sequence[HabitFormationReport] = (),
    reason_observations: Sequence[ReasonObservation] = (),
    reason_candidates: Sequence[ReasonCandidate] = (),
    reason_nodes: Sequence[ReasonNode] = (),
    reason_reviews: Sequence[ReasonReview] = (),
    reason_reports: Sequence[ReasonCompressionReport] = (),
    process_context_items: Sequence[ProcessContextItem] = (),
    process_eliminations: Sequence[ProcessElimination] = (),
    process_transitions: Sequence[ProcessTransition] = (),
    process_episode_records: Sequence[ProcessEpisodeRecord] = (),
    process_memory_queries: Sequence[ProcessMemoryQuery] = (),
    process_memory_answers: Sequence[ProcessMemoryAnswer] = (),
    process_memory_stores: Sequence[ProcessMemoryStore] = (),
    process_memory_reports: Sequence[ProcessMemoryReport] = (),
    structure_types: Sequence[StructureType] = (),
    structure_descriptors: Sequence[StructureDescriptor] = (),
    structure_registry_entries: Sequence[StructureRegistryEntry] = (),
    structure_mappings: Sequence[StructureMapping] = (),
    typed_projection_candidates: Sequence[TypedProjectionCandidate] = (),
    structure_registry_stores: Sequence[StructureRegistryStore] = (),
    structure_registry_reports: Sequence[StructureRegistryReport] = (),
    role_signatures: Sequence[RoleSignature] = (),
    role_definition_candidates: Sequence[RoleDefinitionCandidate] = (),
    role_witness_candidates: Sequence[RoleWitnessCandidate] = (),
    role_conjecture_candidates: Sequence[RoleConjectureCandidate] = (),
    role_reviews: Sequence[RoleReview] = (),
    role_objects: Sequence[RoleObject] = (),
    role_object_reports: Sequence[RoleObjectReport] = (),
    analogy_sources: Sequence[AnalogySource] = (),
    analogy_feature_maps: Sequence[AnalogyFeatureMap] = (),
    analogy_breaks: Sequence[AnalogyBreak] = (),
    structural_analogy_candidates: Sequence[StructuralAnalogyCandidate] = (),
    exposition_notes: Sequence[AnalogyExpositionNote] = (),
    analogy_reviews: Sequence[AnalogyReview] = (),
    structural_analogy_reports: Sequence[StructuralAnalogyReport] = (),
    formal_world_adapter_specs: Sequence[FormalWorldAdapterSpec] = (),
    formal_world_adapter_capabilities: Sequence[FormalWorldAdapterCapability] = (),
    formal_world_parse_results: Sequence[FormalWorldParseResult] = (),
    formal_world_normalize_results: Sequence[FormalWorldNormalizeResult] = (),
    formal_world_validation_results: Sequence[FormalWorldValidationResult] = (),
    formal_world_tasks: Sequence[FormalWorldTask] = (),
    formal_world_handoffs: Sequence[FormalWorldHandoff] = (),
    formal_world_adapter_reports: Sequence[FormalWorldAdapterReport] = (),
    proof_system_specs: Sequence[ProofSystemSpec] = (),
    proof_project_manifests: Sequence[ProofProjectManifest] = (),
    proof_artifact_manifests: Sequence[ProofArtifactManifest] = (),
    proof_import_graphs: Sequence[ProofImportGraph] = (),
    proof_check_command_contracts: Sequence[ProofCheckCommandContract] = (),
    proof_check_requests: Sequence[ProofCheckRequest] = (),
    proof_check_results: Sequence[ProofCheckResult] = (),
    trusted_proof_import_records: Sequence[TrustedProofImportRecord] = (),
    proof_boundary_evidence: Sequence[ProofBoundaryEvidence] = (),
    proof_system_tasks: Sequence[ProofSystemTask] = (),
    proof_system_integration_reports: Sequence[ProofSystemIntegrationReport] = (),
    semantic_sources: Sequence[SemanticSource] = (),
    semantic_claim_segments: Sequence[SemanticClaimSegment] = (),
    semantic_claim_classifications: Sequence[SemanticClaimClassification] = (),
    semantic_ambiguities: Sequence[SemanticAmbiguity] = (),
    semantic_extractions: Sequence[SemanticExtraction] = (),
    formalization_requests: Sequence[FormalizationRequest] = (),
    semantic_routing_hints: Sequence[SemanticRoutingHint] = (),
    semantic_intake_tasks: Sequence[SemanticIntakeTask] = (),
    semantic_intake_reports: Sequence[SemanticIntakeReport] = (),
    api_requests: Sequence[ApiRequest] = (),
    api_responses: Sequence[ApiResponse] = (),
    api_route_results: Sequence[ApiRouteResult] = (),
    api_health: Sequence[ApiHealth] = (),
    api_audit_results: Sequence[ApiAuditResult] = (),
    api_service_states: Sequence[ApiServiceState] = (),
    existential_agents: Sequence[ExistentialAgent] = (),
    agent_mortality_policies: Sequence[AgentMortalityPolicy] = (),
    agent_resource_accounts: Sequence[AgentResourceAccount] = (),
    agent_wounds: Sequence[AgentWound] = (),
    agent_value_profiles: Sequence[AgentValueProfile] = (),
    agent_narratives: Sequence[AgentNarrative] = (),
    held_in_chora_records: Sequence[HeldInChoraRecord] = (),
    agent_lineage_records: Sequence[AgentLineageRecord] = (),
    agent_daemons: Sequence[AgentDaemon] = (),
    agent_ecology_events: Sequence[AgentEcologyEvent] = (),
    agent_ecology_reports: Sequence[AgentEcologyReport] = (),
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
    episodes = list(verification_episode_traces)
    telemetry_ledgers = list(route_telemetry_ledgers)
    spectral_estimates = list(spectral_htilt_estimates)
    claims = list(domain_claims)
    parse_results = list(claim_parse_results)
    registries = list(formal_world_registries)
    lean_traces = list(lean_adapter_traces)
    continuation_traces = list(continuation_action_traces)
    digestion_traces = list(proof_digestion_traces)
    feedback_items = list(verifier_feedback_items)
    repair_traces = list(repair_loop_traces)
    curricula = list(continuation_curricula)
    value_reports = list(discovery_value_reports)
    value_scores = list(discovery_value_scores)
    accepted_lawbook_entries = list(lawbook_entries)
    accepted_lawbook_stores = list(lawbook_stores)
    accepted_lawbook_reviews = list(lawbook_reviews)
    lawbook_queries_data = list(lawbook_queries)
    lawbook_answers = list(lawbook_query_answers)
    lawbook_reports = list(lawbook_query_reports)
    identity_graphs = list(structural_graphs)
    identity_signatures = list(structural_signatures)
    identity_candidates = list(structural_merge_candidates)
    identity_reports = list(structural_identity_reports)
    habit_observations_data = list(habit_observations); habit_candidates_data = list(habit_candidates); habit_rules_data = list(habit_rules); habit_reviews_data = list(habit_reviews); habit_stores_data = list(habit_stores); habit_reports_data = list(habit_reports)
    reason_observations_data=list(reason_observations); reason_candidates_data=list(reason_candidates); reason_nodes_data=list(reason_nodes); reason_reviews_data=list(reason_reviews); reason_reports_data=list(reason_reports)
    process_context_data=list(process_context_items); process_elimination_data=list(process_eliminations); process_transition_data=list(process_transitions); process_episode_data=list(process_episode_records); process_query_data=list(process_memory_queries); process_answer_data=list(process_memory_answers); process_store_data=list(process_memory_stores); process_report_data=list(process_memory_reports)
    structure_type_data=list(structure_types); structure_descriptor_data=list(structure_descriptors); structure_entry_data=list(structure_registry_entries); structure_mapping_data=list(structure_mappings); typed_projection_data=list(typed_projection_candidates); structure_store_data=list(structure_registry_stores); structure_report_data=list(structure_registry_reports)
    role_signature_data=list(role_signatures); role_definition_data=list(role_definition_candidates); role_witness_data=list(role_witness_candidates); role_conjecture_data=list(role_conjecture_candidates); role_review_data=list(role_reviews); role_object_data=list(role_objects); role_report_data=list(role_object_reports)
    analogy_source_data=list(analogy_sources); analogy_map_data=list(analogy_feature_maps); analogy_break_data=list(analogy_breaks); analogy_candidate_data=list(structural_analogy_candidates); analogy_note_data=list(exposition_notes); analogy_review_data=list(analogy_reviews); analogy_report_data=list(structural_analogy_reports)
    adapter_spec_data=list(formal_world_adapter_specs); adapter_capability_data=list(formal_world_adapter_capabilities); adapter_parse_data=list(formal_world_parse_results); adapter_normalize_data=list(formal_world_normalize_results); adapter_validation_data=list(formal_world_validation_results); adapter_task_data=list(formal_world_tasks); adapter_handoff_data=list(formal_world_handoffs); adapter_report_data=list(formal_world_adapter_reports)
    proof_system_spec_data=list(proof_system_specs); proof_project_data=list(proof_project_manifests); proof_artifact_data=list(proof_artifact_manifests); proof_graph_data=list(proof_import_graphs); proof_contract_data=list(proof_check_command_contracts); proof_request_data=list(proof_check_requests); proof_result_data=list(proof_check_results); trusted_import_data=list(trusted_proof_import_records); proof_boundary_data=list(proof_boundary_evidence); proof_system_task_data=list(proof_system_tasks); proof_system_report_data=list(proof_system_integration_reports)
    semantic_source_data=list(semantic_sources); semantic_segment_data=list(semantic_claim_segments); semantic_classification_data=list(semantic_claim_classifications); semantic_ambiguity_data=list(semantic_ambiguities); semantic_extraction_data=list(semantic_extractions); semantic_request_data=list(formalization_requests); semantic_hint_data=list(semantic_routing_hints); semantic_task_data=list(semantic_intake_tasks); semantic_report_data=list(semantic_intake_reports)
    api_request_data=list(api_requests); api_response_data=list(api_responses); api_result_data=list(api_route_results); api_health_data=list(api_health); api_audit_data=list(api_audit_results); api_state_data=list(api_service_states)
    existential_agent_data=list(existential_agents); agent_policy_data=list(agent_mortality_policies); agent_resource_data=list(agent_resource_accounts); agent_wound_data=list(agent_wounds); agent_value_data=list(agent_value_profiles); agent_narrative_data=list(agent_narratives); agent_chora_data=list(held_in_chora_records); agent_lineage_data=list(agent_lineage_records); agent_daemon_data=list(agent_daemons); agent_event_data=list(agent_ecology_events); agent_report_data=list(agent_ecology_reports)

    _check_traces(traces, findings)
    _check_experiences(experiences, findings)
    _check_projection_traces(projections, findings)
    _check_root_constructor_traces(root_constructors, findings)
    _check_proof_verification_traces(proof_traces, findings)
    _check_verification_episode_traces(episodes, findings)
    _check_route_telemetry_ledgers(telemetry_ledgers, findings)
    _check_spectral_htilt_estimates(spectral_estimates, findings)
    _check_domain_claims(claims, parse_results, registries, findings)
    _check_lean_adapter_traces(lean_traces, findings)
    _check_continuation_action_traces(continuation_traces, findings)
    _check_proof_digestion_traces(digestion_traces, findings)
    _check_verifier_feedback(feedback_items, repair_traces, findings)
    _check_continuation_curricula(curricula, findings)
    _check_discovery_value(value_reports, value_scores, findings)
    _check_lawbook_boundary(accepted_lawbook_entries, accepted_lawbook_stores, accepted_lawbook_reviews, findings)
    _check_lawbook_queries(lawbook_queries_data, lawbook_answers, lawbook_reports, findings)
    _check_structural_identity(identity_graphs, identity_signatures, identity_candidates, identity_reports, findings)
    _check_habits(habit_observations_data, habit_candidates_data, habit_rules_data, habit_reviews_data, habit_stores_data, habit_reports_data, findings)
    _check_reasons(reason_observations_data,reason_candidates_data,reason_nodes_data,reason_reviews_data,reason_reports_data,findings)
    _check_process_memory(process_context_data,process_elimination_data,process_transition_data,process_episode_data,process_query_data,process_answer_data,process_store_data,process_report_data,findings)
    _check_structure_registry(structure_type_data,structure_descriptor_data,structure_entry_data,structure_mapping_data,typed_projection_data,structure_store_data,structure_report_data,findings)
    _check_role_objects(role_signature_data,role_definition_data,role_witness_data,role_conjecture_data,role_review_data,role_object_data,role_report_data,findings)
    _check_structural_analogies(analogy_source_data,analogy_map_data,analogy_break_data,analogy_candidate_data,analogy_note_data,analogy_review_data,analogy_report_data,findings)
    _check_formal_world_adapters(adapter_spec_data,adapter_capability_data,adapter_parse_data,adapter_normalize_data,adapter_validation_data,adapter_task_data,adapter_handoff_data,adapter_report_data,findings)
    _check_proof_system_integration(proof_system_spec_data,proof_project_data,proof_artifact_data,proof_graph_data,proof_contract_data,proof_request_data,proof_result_data,trusted_import_data,proof_boundary_data,proof_system_task_data,proof_system_report_data,findings)
    _check_semantic_intake(semantic_source_data,semantic_segment_data,semantic_classification_data,semantic_ambiguity_data,semantic_extraction_data,semantic_request_data,semantic_hint_data,semantic_task_data,semantic_report_data,findings)
    _check_api_surface(api_request_data,api_response_data,api_result_data,api_health_data,api_audit_data,api_state_data,findings)
    _check_existential_agents(existential_agent_data,agent_policy_data,agent_resource_data,agent_wound_data,agent_value_data,agent_narrative_data,agent_chora_data,agent_lineage_data,agent_daemon_data,agent_event_data,agent_report_data,findings)
    _check_summary(summary_data, findings)
    _check_cross_record_warnings(
        traces,
        experiences,
        projections,
        root_constructors,
        proof_traces,
        episodes,
        telemetry_ledgers,
        spectral_estimates,
        claims,
        parse_results,
        registries,
        lean_traces,
        continuation_traces,
        digestion_traces,
        feedback_items,
        repair_traces,
        curricula,
        value_reports,
        value_scores,
        accepted_lawbook_entries,
        accepted_lawbook_stores,
        accepted_lawbook_reviews,
        lawbook_queries_data,
        lawbook_answers,
        lawbook_reports,
        summary_data,
        findings,
    )
    _add_positive_findings(
        traces,
        experiences,
        projections,
        root_constructors,
        proof_traces,
        episodes,
        telemetry_ledgers,
        spectral_estimates,
        claims,
        parse_results,
        registries,
        lean_traces,
        continuation_traces,
        digestion_traces,
        feedback_items,
        repair_traces,
        curricula,
        value_reports,
        value_scores,
        accepted_lawbook_entries,
        accepted_lawbook_stores,
        accepted_lawbook_reviews,
        lawbook_queries_data,
        lawbook_answers,
        lawbook_reports,
        summary_data,
        findings,
    )

    report_summary = {
        **summary_data,
        "alchemical_trace_count": len(traces),
        "agent_experience_count": len(experiences),
        "projection_trace_count": len(projections),
        "root_constructor_trace_count": len(root_constructors),
        "proof_verification_trace_count": len(proof_traces),
        "verification_episode_trace_count": len(episodes),
        "route_telemetry_ledger_count": len(telemetry_ledgers),
        "spectral_htilt_estimate_count": len(spectral_estimates),
        "domain_claim_count": len(claims),
        "claim_parse_result_count": len(parse_results),
        "formal_world_registry_count": len(registries),
        "lean_adapter_trace_count": len(lean_traces),
        "continuation_action_trace_count": len(continuation_traces),
        "proof_digestion_trace_count": len(digestion_traces),
        "verifier_feedback_count": len(feedback_items),
        "repair_loop_trace_count": len(repair_traces),
        "continuation_curriculum_count": len(curricula),
        "discovery_value_report_count": len(value_reports),
        "discovery_value_score_count": len(value_scores),
        "lawbook_entry_count": len(accepted_lawbook_entries) + sum(len(store.entries) for store in accepted_lawbook_stores),
        "lawbook_store_count": len(accepted_lawbook_stores),
        "lawbook_review_count": len(accepted_lawbook_reviews) + sum(len(store.reviews) for store in accepted_lawbook_stores),
        "lawbook_query_count": len(lawbook_queries_data),
        "lawbook_query_answer_count": len(lawbook_answers) + sum(len(report.answers) for report in lawbook_reports),
        "lawbook_query_report_count": len(lawbook_reports),
        "structural_graph_count": len(identity_graphs) + sum(len(report.graphs) for report in identity_reports),
        "structural_signature_count": len(identity_signatures) + sum(len(report.signatures) for report in identity_reports),
        "structural_merge_candidate_count": len(identity_candidates) + sum(len(report.merge_candidates) for report in identity_reports),
        "habit_observation_count": len(habit_observations_data) + sum(len(report.observations) for report in habit_reports_data),
        "habit_candidate_count": len(habit_candidates_data) + sum(len(report.candidates) for report in habit_reports_data),
        "habit_rule_count": len(habit_rules_data) + sum(len(report.rules) for report in habit_reports_data),
        "reason_observation_count": len(reason_observations_data)+sum(len(r.observations) for r in reason_reports_data),
        "reason_candidate_count": len(reason_candidates_data)+sum(len(r.candidates) for r in reason_reports_data),
        "reason_node_count": len(reason_nodes_data)+sum(len(r.reason_nodes) for r in reason_reports_data),
        "process_context_count": len(process_context_data)+sum(len(e.contexts) for e in process_episode_data)+sum(store.context_count() for store in process_store_data),
        "process_elimination_count": len(process_elimination_data)+sum(len(e.eliminations) for e in process_episode_data)+sum(store.elimination_count() for store in process_store_data),
        "process_transition_count": len(process_transition_data)+sum(len(e.transitions) for e in process_episode_data)+sum(store.transition_count() for store in process_store_data),
        "process_episode_count": len(process_episode_data)+sum(len(store.episodes) for store in process_store_data),
        "process_query_count": len(process_query_data)+sum(len(r.queries) for r in process_report_data),
        "process_answer_count": len(process_answer_data)+sum(len(r.answers) for r in process_report_data),
        "structure_type_count": len(structure_type_data)+sum(len(s.structure_types) for s in structure_store_data),
        "structure_descriptor_count": len(structure_descriptor_data)+sum(len(s.entries) for s in structure_store_data)+sum(len(r.descriptors) for r in structure_report_data),
        "structure_mapping_count": len(structure_mapping_data)+sum(len(s.mappings) for s in structure_store_data)+sum(len(r.mappings) for r in structure_report_data),
        "typed_projection_candidate_count": len(typed_projection_data)+sum(len(s.typed_projection_candidates) for s in structure_store_data)+sum(len(r.typed_projection_candidates) for r in structure_report_data),
        "role_signature_count": len(role_signature_data)+sum(len(r.signatures) for r in role_report_data),
        "role_definition_candidate_count": len(role_definition_data)+sum(len(r.definition_candidates) for r in role_report_data),
        "role_witness_candidate_count": len(role_witness_data)+sum(len(r.witness_candidates) for r in role_report_data),
        "role_conjecture_candidate_count": len(role_conjecture_data)+sum(len(r.conjecture_candidates) for r in role_report_data),
        "role_object_count": len(role_object_data)+sum(len(r.role_objects) for r in role_report_data),
        "analogy_source_count": len(analogy_source_data)+sum(len(r.sources) for r in analogy_report_data),
        "analogy_feature_map_count": len(analogy_map_data)+sum(len(r.feature_maps) for r in analogy_report_data),
        "analogy_break_count": len(analogy_break_data)+sum(len(r.breaks) for r in analogy_report_data),
        "structural_analogy_candidate_count": len(analogy_candidate_data)+sum(len(r.candidates) for r in analogy_report_data),
        "exposition_note_count": len(analogy_note_data)+sum(len(r.exposition_notes) for r in analogy_report_data),
        "formal_world_adapter_spec_count": len(adapter_spec_data)+sum(len(r.specs) for r in adapter_report_data),
        "formal_world_parse_count": len(adapter_parse_data)+sum(len(r.parses) for r in adapter_report_data),
        "formal_world_task_count": len(adapter_task_data)+sum(len(r.tasks) for r in adapter_report_data),
        "formal_world_handoff_count": len(adapter_handoff_data)+sum(len(r.handoffs) for r in adapter_report_data),
        "proof_system_spec_count": len(proof_system_spec_data)+sum(len(r.specs) for r in proof_system_report_data),
        "proof_project_manifest_count": len(proof_project_data)+sum(len(r.projects) for r in proof_system_report_data),
        "proof_artifact_manifest_count": len(proof_artifact_data)+sum(len(r.artifacts) for r in proof_system_report_data),
        "proof_boundary_evidence_count": len(proof_boundary_data)+sum(len(r.boundary_evidence) for r in proof_system_report_data),
        "semantic_source_count": len(semantic_source_data)+sum(len(r.sources) for r in semantic_report_data),
        "semantic_segment_count": len(semantic_segment_data)+sum(len(r.segments) for r in semantic_report_data),
        "semantic_task_count": len(semantic_task_data)+sum(len(r.tasks) for r in semantic_report_data),
        "api_request_count": len(api_request_data),
        "api_response_count": len(api_response_data),
        "api_route_result_count": len(api_result_data)+sum(1 for r in api_response_data if r.result),
        "existential_agent_count": len(existential_agent_data)+sum(len(r.agents) for r in agent_report_data),
        "agent_ecology_event_count": len(agent_event_data)+sum(len(r.events) for r in agent_report_data),
        "agent_wound_count": len(agent_wound_data)+sum(len(r.wounds) for r in agent_report_data),
        "promoted_trace_count": sum(1 for trace in traces if trace.is_promoted()),
        "verifier_boundary_experience_count": sum(1 for exp in experiences if exp.verifier_boundary_crossed),
        "projection_terminal_count": sum(trace.terminal_count() for trace in projections),
        "root_constructor_terminal_count": sum(trace.terminal_count() for trace in root_constructors),
        "proof_verification_terminal_count": sum(trace.terminal_count() for trace in proof_traces),
        "verification_episode_terminal_count": sum(1 for trace in episodes if trace.is_terminal()),
        "route_telemetry_event_count": sum(len(ledger.events) for ledger in telemetry_ledgers),
        "route_telemetry_terminal_count": sum(ledger.terminal_count() for ledger in telemetry_ledgers),
        "spectral_htilt_state_count": sum(len(estimate.states) for estimate in spectral_estimates),
        "lean_adapter_verified_count": sum(trace.verified_count() for trace in lean_traces),
        "continuation_action_output_count": sum(len(trace.outputs) for trace in continuation_traces),
        "proof_digestion_ready_count": sum(1 for trace in digestion_traces if trace.summary.get("assimilation_ready") or trace.status.value == "ASSIMILATION_CANDIDATE"),
        "repair_plan_count": sum(len(trace.repair_plans) for trace in repair_traces),
        "continuation_curriculum_stage_count": sum(len(curriculum.stages) for curriculum in curricula),
        "discovery_value_ranked_count": sum(len(report.scores) for report in value_reports),
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


def _check_verification_episode_traces(
    episode_traces: Sequence[VerificationEpisodeTrace], findings: list[RoadmapAlignmentFinding]
) -> None:
    for episode in episode_traces:
        if episode.terminal_form and (not episode.verifier_boundary_crossed or not episode.certificate_id):
            findings.append(
                RoadmapAlignmentFinding(
                    "critical",
                    "EPISODE_TERMINAL_WITHOUT_BOUNDARY",
                    f"Verification episode {episode.episode_id} has terminal form without certificate/boundary.",
                    "Terminal episodes require a subtrace verifier/importer/chain-audit boundary and certificate id.",
                )
            )
        for decision in episode.route_decisions:
            if _dict_claims_terminal(decision.to_dict()):
                findings.append(
                    RoadmapAlignmentFinding(
                        "critical",
                        "ROUTE_DECISION_CLAIMS_TERMINAL",
                        f"Route decision {decision.decision_id} claims terminal truth.",
                        "Route decisions are advisory telemetry only.",
                    )
                )
        if episode.status == VerificationEpisodeStatus.TERMINAL_VERIFIED_PROOF:
            if not (
                episode.proof_verification_trace
                and any(result.is_terminal() and result.terminal_form == TerminalForm.VERIFIED_PROOF for result in episode.proof_verification_trace.results)
            ):
                findings.append(
                    RoadmapAlignmentFinding(
                        "critical",
                        "EPISODE_VERIFIED_PROOF_WITHOUT_PROOF_TRACE",
                        f"Episode {episode.episode_id} claims VERIFIED_PROOF without terminal proof subtrace.",
                        "Require proof verifier/importer/chain-audit terminal result.",
                    )
                )
        if episode.status == VerificationEpisodeStatus.TERMINAL_FINITE_COUNTERMODEL:
            if not (
                episode.root_constructor_trace
                and any(attempt.is_terminal() and attempt.terminal_form == TerminalForm.FINITE_COUNTERMODEL for attempt in episode.root_constructor_trace.attempts)
            ):
                findings.append(
                    RoadmapAlignmentFinding(
                        "critical",
                        "EPISODE_COUNTERMODEL_WITHOUT_CONSTRUCTOR_TRACE",
                        f"Episode {episode.episode_id} claims FINITE_COUNTERMODEL without terminal constructor subtrace.",
                        "Require importer-verified constructor attempt or equivalent terminal subtrace.",
                    )
                )
        if int(episode.summary.get("alignment_critical_count", 0) or 0) > 0:
            findings.append(
                RoadmapAlignmentFinding(
                    "critical",
                    "EPISODE_INTERNAL_ALIGNMENT_FAILED",
                    f"Episode {episode.episode_id} recorded internal alignment criticals.",
                    "Inspect subtrace alignment before accepting episode output.",
                )
            )


def _check_route_telemetry_ledgers(
    ledgers: Sequence[RouteTelemetryLedger], findings: list[RoadmapAlignmentFinding]
) -> None:
    for ledger in ledgers:
        summary_text = json.dumps(ledger.summary, sort_keys=True).lower()
        if "spectral_h_tilt_complete" in summary_text or "full_spectral_h_tilt_complete" in summary_text:
            findings.append(
                RoadmapAlignmentFinding(
                    "critical",
                    "TELEMETRY_CLAIMS_SPECTRAL_HTILT_COMPLETE",
                    f"Telemetry ledger {ledger.ledger_id} claims full spectral H-tilt is complete.",
                    "Keep telemetry as preparation until L, V, K=L-V, h, q, and pi* are explicitly estimated.",
                )
            )
        if _dict_claims_terminal(ledger.summary):
            findings.append(
                RoadmapAlignmentFinding(
                    "critical",
                    "ROUTE_SCORE_AS_TERMINAL_TRUTH",
                    f"Telemetry ledger {ledger.ledger_id} summary appears to represent route scores as terminal truth.",
                    "Keep route scores advisory and separate from terminal forms.",
                )
            )
        for event in ledger.events:
            if event.terminal_form and not event.is_terminal():
                findings.append(
                    RoadmapAlignmentFinding(
                        "critical",
                        "TELEMETRY_TERMINAL_WITHOUT_BOUNDARY",
                        f"Telemetry event {event.event_id} carries terminal form without verifier boundary.",
                        "Telemetry can mirror terminal truth only when the underlying verifier boundary and certificate id exist.",
                    )
                )
            if event.certificate_id and event.terminal_form is None:
                findings.append(
                    RoadmapAlignmentFinding(
                        "critical",
                        "TELEMETRY_CERTIFICATE_WITHOUT_TERMINAL_FORM",
                        f"Telemetry event {event.event_id} has a certificate id without terminal form.",
                        "Attach certificate ids only to verifier-bound terminal telemetry.",
                    )
                )
            if event.killed and event.terminal_form == TerminalForm.VERIFIED_PROOF:
                findings.append(
                    RoadmapAlignmentFinding(
                        "critical",
                        "KILLED_ROUTE_EVENT_AS_PROOF",
                        f"Killed telemetry event {event.event_id} is represented as VERIFIED_PROOF.",
                        "Killed route events are scheduling pressure, not proofs.",
                    )
                )
            if event.metadata.get("route_score_terminal") or event.metadata.get("telemetry_terminal_truth"):
                findings.append(
                    RoadmapAlignmentFinding(
                        "critical",
                        "ROUTE_TELEMETRY_METADATA_CLAIMS_TRUTH",
                        f"Telemetry event {event.event_id} metadata claims terminal truth.",
                        "Telemetry metadata may describe provenance but cannot promote truth.",
                    )
                )


def _check_spectral_htilt_estimates(
    estimates: Sequence[SpectralHTiltEstimate], findings: list[RoadmapAlignmentFinding]
) -> None:
    for estimate in estimates:
        metadata_text = json.dumps(estimate.metadata, sort_keys=True).lower()
        if not estimate.advisory:
            findings.append(
                RoadmapAlignmentFinding(
                    "critical",
                    "SPECTRAL_HTILT_NOT_ADVISORY",
                    f"Spectral H-tilt estimate {estimate.estimate_id} is not marked advisory.",
                    "H-tilt estimates are route pressure only.",
                )
            )
        if "terminal_form" in metadata_text or "certificate_id" in metadata_text:
            findings.append(
                RoadmapAlignmentFinding(
                    "critical",
                    "SPECTRAL_HTILT_METADATA_CLAIMS_TERMINAL_ARTIFACT",
                    f"Spectral H-tilt estimate {estimate.estimate_id} metadata contains terminal/certificate fields.",
                    "Keep terminal forms and certificate ids out of spectral estimates.",
                )
            )
        if (
            estimate.metadata.get("verifier_authority") is True
            or estimate.metadata.get("no_verifier_authority") is False
            or estimate.metadata.get("truth_authority") is True
        ):
            findings.append(
                RoadmapAlignmentFinding(
                    "critical",
                    "SPECTRAL_HTILT_CLAIMS_VERIFIER_AUTHORITY",
                    f"Spectral H-tilt estimate {estimate.estimate_id} claims verifier authority.",
                    "Only verifier/importer/chain-audit boundaries can decide terminal truth.",
                )
            )
        if "route_score_is_truth" in metadata_text or "route_scores_are_truth" in metadata_text:
            findings.append(
                RoadmapAlignmentFinding(
                    "critical",
                    "SPECTRAL_ROUTE_SCORE_AS_TRUTH",
                    f"Spectral H-tilt estimate {estimate.estimate_id} claims route scores are truth.",
                    "Route priorities are advisory scheduling pressure only.",
                )
            )
        if "verified_proof" in metadata_text or "finite_countermodel" in metadata_text or "named_obstruction" in metadata_text:
            findings.append(
                RoadmapAlignmentFinding(
                    "critical",
                    "SPECTRAL_HTILT_CLAIMS_TERMINAL_STATUS",
                    f"Spectral H-tilt estimate {estimate.estimate_id} claims proof/countermodel terminal status.",
                    "Spectral H-tilt may rank routes but cannot produce terminal forms.",
                )
            )


def _check_domain_claims(
    claims: Sequence[DomainClaim],
    parse_results: Sequence[ClaimParseResult],
    registries: Sequence[FormalWorldRegistry],
    findings: list[RoadmapAlignmentFinding],
) -> None:
    for claim in claims:
        metadata_text = json.dumps(claim.metadata, sort_keys=True).lower()
        if "terminal_form" in claim.metadata or "certificate_id" in claim.metadata:
            findings.append(
                RoadmapAlignmentFinding(
                    "critical",
                    "DOMAIN_CLAIM_METADATA_CLAIMS_TERMINAL",
                    f"Domain claim {claim.claim_id} metadata contains terminal/certificate fields.",
                    "Parsing and world routing cannot promote claims.",
                )
            )
        if claim.world == DomainFormalWorldKind.NATURAL_LANGUAGE and (
            claim.metadata.get("verifier_supported") is True
            or claim.metadata.get("terminal_truth") is True
            or "verified_proof" in metadata_text
            or "finite_countermodel" in metadata_text
        ):
            findings.append(
                RoadmapAlignmentFinding(
                    "critical",
                    "NATURAL_LANGUAGE_CLAIM_AS_TERMINAL_TRUTH",
                    f"Natural-language claim {claim.claim_id} is treated as verifier-supported terminal truth.",
                    "Natural-language claims remain advisory/residual until connected to a real verifier/importer.",
                )
            )
    for result in parse_results:
        if result.metadata.get("terminal_form") in _terminal_values() or result.metadata.get("certificate_id"):
            findings.append(
                RoadmapAlignmentFinding(
                    "critical",
                    "CLAIM_PARSE_RESULT_AS_TERMINAL_TRUTH",
                    f"Claim parse result {result.result_id} is treated as terminal truth.",
                    "PARSED/NORMALIZED/ROUTABLE are advisory IR states, not terminal forms.",
                )
            )
        if result.status in {ClaimIRStatus.PARSED, ClaimIRStatus.NORMALIZED} and _dict_claims_terminal(result.metadata):
            findings.append(
                RoadmapAlignmentFinding(
                    "critical",
                    "PARSED_NORMALIZED_STATUS_AS_TERMINAL",
                    f"Claim parse result {result.result_id} treats parse status as terminal.",
                    "Route the claim to a verifier/importer before terminal truth.",
                )
            )
        if result.status == ClaimIRStatus.VERIFIER_SUPPORTED and result.domain_claim.world == DomainFormalWorldKind.NATURAL_LANGUAGE:
            findings.append(
                RoadmapAlignmentFinding(
                    "critical",
                    "UNSUPPORTED_CLAIM_MARKED_VERIFIER_SUPPORTED",
                    f"Natural-language parse result {result.result_id} is marked verifier-supported.",
                    "Use ADVISORY_ONLY or RESIDUAL for unsupported worlds.",
                )
            )
    for registry in registries:
        for world in registry.worlds.values():
            if (world.supports_proofs or world.supports_countermodels) and not (world.verifier_kinds and world.adapter_name):
                findings.append(
                    RoadmapAlignmentFinding(
                        "critical",
                        "FORMAL_WORLD_VERIFIER_AUTHORITY_WITHOUT_BOUNDARY",
                        f"Formal world {world.world_id} claims proof/countermodel support without verifier kinds/adapter.",
                        "Declare verifier/importer boundary metadata for proof or countermodel support.",
                    )
                )
            if world.kind == DomainFormalWorldKind.NATURAL_LANGUAGE and (world.supports_proofs or world.supports_countermodels):
                findings.append(
                    RoadmapAlignmentFinding(
                        "critical",
                        "NATURAL_LANGUAGE_WORLD_VERIFIER_SUPPORTED",
                        f"Natural-language world {world.world_id} is verifier-supported.",
                        "Keep natural-language worlds advisory until a real verifier/importer exists.",
                )
            )


def _check_lean_adapter_traces(
    traces: Sequence[LeanAdapterTrace], findings: list[RoadmapAlignmentFinding]
) -> None:
    for trace in traces:
        text = json.dumps(trace.to_dict(), sort_keys=True).lower()
        if "lean_text_is_truth" in text or "theorem_name_is_truth" in text:
            findings.append(
                RoadmapAlignmentFinding(
                    "critical",
                    "LEAN_TRACE_TEXT_CLAIMS_TRUTH",
                    f"Lean adapter trace {trace.trace_id} claims Lean text/theorem names are truth.",
                    "Lean text and theorem names remain advisory until checked/imported through the proof boundary.",
                )
            )
        for lean_file in trace.files:
            if lean_file.metadata.get("terminal_form") in _terminal_values() or lean_file.metadata.get("certificate_id"):
                findings.append(
                    RoadmapAlignmentFinding(
                        "critical",
                        "LEAN_FILE_ARTIFACT_CLAIMS_TERMINAL",
                        f"Lean file {lean_file.lean_file_id} claims terminal truth.",
                        "Lean file artifacts are not terminal proof records.",
                    )
                )
        for result in trace.results:
            if result.is_verified() and (not result.verifier_boundary_crossed or not result.certificate_id):
                findings.append(
                    RoadmapAlignmentFinding(
                        "critical",
                        "LEAN_CHECK_VERIFIED_WITHOUT_BOUNDARY",
                        f"Lean check result {result.result_id} is verified without certificate/boundary.",
                        "Require terminal ProofVerificationResult plus certificate id.",
                    )
                )
            if result.status in {LeanArtifactStatus.CHECK_FAILED, LeanArtifactStatus.LEAN_NOT_AVAILABLE} and (
                result.verifier_boundary_crossed or result.certificate_id or result.is_verified()
            ):
                findings.append(
                    RoadmapAlignmentFinding(
                        "critical",
                        "LEAN_FAILED_OR_UNAVAILABLE_AS_TERMINAL",
                        f"Lean check result {result.result_id} treats failed/unavailable Lean as terminal.",
                        "Failed or unavailable Lean is residual/advisory only.",
                    )
                )
            if result.status == LeanArtifactStatus.IMPORTED_VERIFIED:
                provenance = result.metadata.get("provenance", {})
                if not result.certificate_id and not result.metadata.get("external_certificate_id"):
                    findings.append(
                        RoadmapAlignmentFinding(
                            "critical",
                            "LEAN_IMPORT_WITHOUT_CERTIFICATE",
                            f"Imported Lean result {result.result_id} lacks certificate/provenance.",
                            "Trusted Lean imports require verified provenance or external certificate id.",
                        )
                    )
                if isinstance(provenance, Mapping) and not (
                    provenance.get("verified") is True or result.metadata.get("external_certificate_id")
                ):
                    findings.append(
                        RoadmapAlignmentFinding(
                            "critical",
                            "LEAN_IMPORT_UNVERIFIED_PROVENANCE",
                            f"Imported Lean result {result.result_id} lacks verified provenance.",
                            "Mark it residual/advisory unless provenance is verified.",
                        )
                    )


def _check_continuation_action_traces(
    traces: Sequence[ContinuationActionTrace], findings: list[RoadmapAlignmentFinding]
) -> None:
    for trace in traces:
        for action in trace.actions:
            text = json.dumps(action.metadata, sort_keys=True).lower()
            if "verifier_authority" in text or "truth_authority" in text:
                findings.append(
                    RoadmapAlignmentFinding(
                        "critical",
                        "CONTINUATION_ACTION_CLAIMS_VERIFIER_AUTHORITY",
                        f"Continuation action {action.action_id} claims verifier authority.",
                        "Continuation actions are proposal mechanisms only.",
                    )
                )
        for output in trace.outputs:
            text = json.dumps(output.to_dict(), sort_keys=True).lower()
            if output.terminal_form and not output.is_terminal():
                findings.append(
                    RoadmapAlignmentFinding(
                        "critical",
                        "CONTINUATION_OUTPUT_TERMINAL_WITHOUT_BOUNDARY",
                        f"Continuation output {output.output_id} has terminal form without verifier boundary.",
                        "Generated continuations must remain advisory unless a real boundary promoted them.",
                    )
                )
            if output.metadata.get("verifier_authority") or output.metadata.get("truth_authority"):
                findings.append(
                    RoadmapAlignmentFinding(
                        "critical",
                        "CONTINUATION_OUTPUT_CLAIMS_VERIFIER_AUTHORITY",
                        f"Continuation output {output.output_id} claims verifier authority.",
                        "Actions may emit tasks, not truth.",
                    )
                )
            if output.kind in {ContinuationOutputKind.PROOF_ARTIFACT, ContinuationOutputKind.TASK, ContinuationOutputKind.EPISODE_INPUT} and (
                output.terminal_form or output.certificate_id or output.verifier_boundary_crossed
            ):
                findings.append(
                    RoadmapAlignmentFinding(
                        "critical",
                        "GENERATED_TASK_TREATED_AS_TERMINAL",
                        f"Continuation output {output.output_id} treats generated task/artifact as terminal.",
                        "Proof/countermodel/projection tasks must descend into verifier-bound episodes first.",
                    )
                )
            if output.kind == ContinuationOutputKind.OBSTRUCTION_CANDIDATE and output.terminal_form == TerminalForm.NAMED_OBSTRUCTION and not output.metadata.get("naming_boundary"):
                findings.append(
                    RoadmapAlignmentFinding(
                        "critical",
                        "OBSTRUCTION_CANDIDATE_AS_NAMED_OBSTRUCTION",
                        f"Continuation output {output.output_id} treats obstruction candidate as named obstruction.",
                        "Use a naming boundary before NAMED_OBSTRUCTION.",
                    )
                )
            if "natural_language" in text and any(term.lower() in text for term in _terminal_values()):
                findings.append(
                    RoadmapAlignmentFinding(
                        "critical",
                        "NATURAL_LANGUAGE_CONTINUATION_AS_TRUTH",
                        f"Continuation output {output.output_id} turns natural-language pressure into terminal-like output.",
                        "Natural-language continuations remain advisory/residual.",
                    )
                )


def _check_proof_digestion_traces(
    traces: Sequence[ProofDigestionTrace], findings: list[RoadmapAlignmentFinding]
) -> None:
    for trace in traces:
        text = json.dumps(trace.to_dict(), sort_keys=True).lower()
        if (trace.terminal_form or trace.certificate_id) and not trace.verifier_boundary_crossed:
            findings.append(
                RoadmapAlignmentFinding(
                    "critical",
                    "DIGESTION_TERMINAL_WITHOUT_BOUNDARY",
                    f"Proof digestion trace {trace.trace_id} carries terminal/certificate data without inherited verifier boundary.",
                    "Digestion may inherit a verified proof boundary but must never invent one.",
                )
            )
        if "verifier_authority" in text or "digestion_verifies" in text:
            findings.append(
                RoadmapAlignmentFinding(
                    "critical",
                    "DIGESTION_CLAIMS_VERIFIER_AUTHORITY",
                    f"Proof digestion trace {trace.trace_id} claims verifier authority.",
                    "Proof digestion explains and compresses; it is not proof verification.",
                )
            )
        terminal_terms = _terminal_values()
        for idea in trace.key_ideas:
            idea_text = json.dumps(idea.to_dict(), sort_keys=True).lower()
            if any(term.lower() in idea_text for term in terminal_terms):
                findings.append(
                    RoadmapAlignmentFinding(
                        "critical",
                        "KEY_IDEA_CANDIDATE_CLAIMS_PROOF",
                        f"Key idea candidate {idea.key_idea_id} contains terminal proof language.",
                        "Key ideas are advisory understanding artifacts, not proof records.",
                    )
                )
        for schema in trace.reusable_schemas:
            schema_text = json.dumps(schema.to_dict(), sort_keys=True).lower()
            if any(term.lower() in schema_text for term in terminal_terms):
                findings.append(
                    RoadmapAlignmentFinding(
                        "critical",
                        "SCHEMA_CANDIDATE_CLAIMS_PROOF",
                        f"Reusable schema candidate {schema.schema_id} contains terminal proof language.",
                        "Schemas are advisory reuse candidates until separately verified/applied.",
                    )
                )
        for note in trace.exposition_notes:
            note_text = json.dumps(note.to_dict(), sort_keys=True).lower()
            if any(term.lower() in note_text for term in terminal_terms):
                findings.append(
                    RoadmapAlignmentFinding(
                        "critical",
                        "EXPOSITION_NOTE_CLAIMS_PROOF",
                        f"Exposition note {note.note_id} contains terminal proof language.",
                        "Exposition notes explain; they are not proof certificates.",
                    )
                )
        if trace.summary.get("assimilation_candidate_ready") and not trace.certificate_id:
            findings.append(
                RoadmapAlignmentFinding(
                    "critical",
                    "ASSIMILATION_READY_WITHOUT_CERTIFICATE",
                    f"Proof digestion trace {trace.trace_id} marks assimilation ready without certificate id.",
                    "Lawbook assimilation candidates require an inherited verified certificate.",
                )
            )
        if trace.summary.get("digested_failed_or_unverified_as_terminal") or (
            not trace.verifier_boundary_crossed and trace.terminal_form
        ):
            findings.append(
                RoadmapAlignmentFinding(
                    "critical",
                    "UNVERIFIED_DIGESTION_AS_TERMINAL",
                    f"Proof digestion trace {trace.trace_id} treats failed/unverified proof digestion as terminal truth.",
                    "Keep failed or unverified proof digestion advisory/residual.",
                )
            )


def _check_verifier_feedback(
    feedback_items: Sequence[VerifierFeedback],
    repair_traces: Sequence[RepairLoopTrace],
    findings: list[RoadmapAlignmentFinding],
) -> None:
    for feedback in feedback_items:
        text = json.dumps(feedback.to_dict(), sort_keys=True).lower()
        if feedback.metadata.get("terminal_form") in _terminal_values() or feedback.metadata.get("certificate_id"):
            findings.append(
                RoadmapAlignmentFinding(
                    "critical",
                    "VERIFIER_FEEDBACK_CLAIMS_TERMINAL_TRUTH",
                    f"Verifier feedback {feedback.feedback_id} claims terminal truth directly.",
                    "Feedback may describe verifier output, but it is not the terminal artifact.",
                )
            )
        if (
            "natural_language" in text
            and (
                feedback.metadata.get("verifier_boundary") is True
                or feedback.metadata.get("verifier_boundary_crossed") is True
                or "verified_proof" in text
            )
        ):
            findings.append(
                RoadmapAlignmentFinding(
                    "critical",
                    "NATURAL_LANGUAGE_REPAIR_AS_VERIFICATION",
                    f"Verifier feedback {feedback.feedback_id} marks natural-language repair/critique as verification.",
                    "Natural-language critique is advisory unless a real verifier/importer boundary exists.",
                )
            )
        if feedback.metadata.get("source") == "text" and feedback.metadata.get("verifier_boundary"):
            findings.append(
                RoadmapAlignmentFinding(
                    "critical",
                    "RAW_TEXT_FEEDBACK_AS_VERIFIER_BOUNDARY",
                    f"Raw text feedback {feedback.feedback_id} claims verifier boundary.",
                    "Text feedback remains advisory and cannot itself cross the verifier boundary.",
                )
            )
        if "finite_search_miss" in text and "verified_proof" in text:
            findings.append(
                RoadmapAlignmentFinding(
                    "critical",
                    "FAILED_FINITE_SEARCH_AS_TRUE_PROOF",
                    f"Verifier feedback {feedback.feedback_id} treats failed finite search as proof of TRUE.",
                    "Finite-search miss is residual/search telemetry, not proof.",
                )
            )
    for trace in repair_traces:
        text = json.dumps(trace.to_dict(), sort_keys=True).lower()
        if (trace.terminal_form or trace.certificate_id) and not trace.verifier_boundary_crossed:
            findings.append(
                RoadmapAlignmentFinding(
                    "critical",
                    "REPAIR_TRACE_TERMINAL_WITHOUT_BOUNDARY",
                    f"Repair loop trace {trace.trace_id} carries terminal/certificate data without verifier boundary.",
                    "Repair traces may inherit but must not invent terminal status.",
                )
            )
        if "lawbook_write" in text and ("truth" in text or "terminal" in text):
            findings.append(
                RoadmapAlignmentFinding(
                    "critical",
                    "REPAIR_PLAN_WRITES_LAWBOOK_TRUTH",
                    f"Repair loop trace {trace.trace_id} appears to write directly to Lawbook truth.",
                    "Repair may emit advisory tasks only; Lawbook writes need a separate boundary.",
                )
            )
        for plan in trace.repair_plans:
            if plan.metadata.get("terminal_form") in _terminal_values() or plan.metadata.get("certificate_id"):
                findings.append(
                    RoadmapAlignmentFinding(
                        "critical",
                        "REPAIR_PLAN_CLAIMS_TERMINAL_TRUTH",
                        f"Repair plan {plan.repair_plan_id} claims terminal truth.",
                        "Repair plans schedule next moves; they are not certificates.",
                    )
                )
        for output in trace.continuation_outputs:
            if (output.terminal_form or output.certificate_id or output.verifier_boundary_crossed) and not output.is_terminal():
                findings.append(
                    RoadmapAlignmentFinding(
                        "critical",
                        "REPAIR_OUTPUT_UNSAFE_TERMINAL",
                        f"Repair continuation output {output.output_id} claims terminal data without boundary.",
                        "Repair outputs must remain advisory until reverified.",
                    )
                )
            if output.terminal_form in {TerminalForm.VERIFIED_PROOF, TerminalForm.FINITE_COUNTERMODEL} and not output.is_terminal():
                findings.append(
                    RoadmapAlignmentFinding(
                        "critical",
                        "REPAIR_OUTPUT_CLAIMS_TRUTH_WITHOUT_CERTIFICATE",
                        f"Repair output {output.output_id} claims proof/countermodel without certificate.",
                        "Run a verifier/importer/chain audit before terminal truth.",
                    )
                )


def _check_continuation_curricula(
    curricula: Sequence[ContinuationCurriculum], findings: list[RoadmapAlignmentFinding]
) -> None:
    for curriculum in curricula:
        text = json.dumps(curriculum.to_dict(), sort_keys=True).lower()
        if (curriculum.terminal_form or curriculum.certificate_id) and not curriculum.verifier_boundary_crossed:
            findings.append(
                RoadmapAlignmentFinding(
                    "critical",
                    "CURRICULUM_TERMINAL_WITHOUT_BOUNDARY",
                    f"Continuation curriculum {curriculum.curriculum_id} carries terminal data without verifier boundary.",
                    "Curricula stage work; they do not verify claims.",
                )
            )
        if "lawbook_write" in text and ("truth" in text or "terminal" in text):
            findings.append(
                RoadmapAlignmentFinding(
                    "critical",
                    "CURRICULUM_WRITES_LAWBOOK_TRUTH",
                    f"Continuation curriculum {curriculum.curriculum_id} appears to write Lawbook truth directly.",
                    "Curricula may emit advisory tasks only.",
                )
            )
        if "warmup_success_is_target_proof" in text:
            findings.append(
                RoadmapAlignmentFinding(
                    "critical",
                    "WARMUP_AS_TARGET_PROOF",
                    f"Continuation curriculum {curriculum.curriculum_id} treats warm-up success as target proof.",
                    "Warm-ups are route preparation, not target verification.",
                )
            )
        if "finite_search_miss_is_true" in text or "finite_example_proves_true" in text:
            findings.append(
                RoadmapAlignmentFinding(
                    "critical",
                    "FINITE_EXAMPLE_AS_TRUE_PROOF",
                    f"Continuation curriculum {curriculum.curriculum_id} treats finite example/search miss as proof of TRUE.",
                    "Finite examples and bounded misses remain advisory.",
                )
            )
        if "natural_language" in text and ("verifier_boundary" in text or "verified_proof" in text):
            findings.append(
                RoadmapAlignmentFinding(
                    "critical",
                    "NATURAL_LANGUAGE_CURRICULUM_AS_VERIFICATION",
                    f"Continuation curriculum {curriculum.curriculum_id} marks natural-language explanation as verification.",
                    "Natural-language curriculum notes remain advisory.",
                )
            )
        for stage in curriculum.stages:
            stage_text = json.dumps(stage.to_dict(), sort_keys=True).lower()
            if stage.is_terminal() or stage.metadata.get("terminal_form") in _terminal_values() or stage.metadata.get("certificate_id"):
                findings.append(
                    RoadmapAlignmentFinding(
                        "critical",
                        "CURRICULUM_STAGE_CLAIMS_TERMINAL_TRUTH",
                        f"Curriculum stage {stage.stage_id} claims terminal truth.",
                        "Curriculum stages are never terminal artifacts.",
                    )
                )
            if any(term.lower() in stage_text for term in ("verified_proof", "finite_countermodel")) and (
                stage.metadata.get("treat_as_truth") or stage.metadata.get("terminal_form")
            ):
                findings.append(
                    RoadmapAlignmentFinding(
                        "critical",
                        "CURRICULUM_OUTPUT_CLAIMS_TRUTH",
                        f"Curriculum stage {stage.stage_id} treats advisory output as truth.",
                        "Run verifier/importer/finite validation before terminal claims.",
                    )
                )
        if (curriculum.target_claim_id or curriculum.target_raw or curriculum.target_source or curriculum.target_target) and not curriculum.stages:
            findings.append(
                RoadmapAlignmentFinding(
                    "warning",
                    "CURRICULUM_TARGET_WITHOUT_STAGES",
                    f"Continuation curriculum {curriculum.curriculum_id} has a target but no stages.",
                    "Emit at least residual review or held-in-Chora fallback.",
                )
            )
        if any(stage.kind in {CurriculumStageKind.PROOF_TASK, CurriculumStageKind.COUNTERMODEL_TASK} for stage in curriculum.stages) and not curriculum.episode_inputs:
            findings.append(
                RoadmapAlignmentFinding(
                    "warning",
                    "CURRICULUM_TASKS_WITHOUT_EPISODES",
                    f"Continuation curriculum {curriculum.curriculum_id} has proof/countermodel tasks but no episode inputs.",
                    "Emit replayable episode-input payloads for staged tasks.",
                )
            )
        if sum(1 for stage in curriculum.stages if stage.kind == CurriculumStageKind.UNKNOWN) > max(1, len(curriculum.stages) // 2):
            findings.append(
                RoadmapAlignmentFinding(
                    "warning",
                    "CURRICULUM_MANY_UNKNOWN_STAGES",
                    f"Continuation curriculum {curriculum.curriculum_id} has many unknown stages.",
                    "Prefer explicit stage kinds for route replay.",
                )
            )
        if not curriculum.advisory or not curriculum.metadata.get("advisory_only", curriculum.advisory):
            findings.append(
                RoadmapAlignmentFinding(
                    "warning",
                    "CURRICULUM_MISSING_ADVISORY_METADATA",
                    f"Continuation curriculum {curriculum.curriculum_id} lacks advisory metadata.",
                    "Curricula are route plans, not proof.",
                )
            )
        if any(stage.kind == CurriculumStageKind.PROJECTION_TASK for stage in curriculum.stages) and not curriculum.projection_candidates:
            findings.append(
                RoadmapAlignmentFinding(
                    "warning",
                    "CURRICULUM_PROJECTION_WITHOUT_CANDIDATE",
                    f"Continuation curriculum {curriculum.curriculum_id} has projection tasks without candidates.",
                    "Preserve projection candidates when available.",
                )
            )
        if "from_verifier_feedback" in text and not any(stage.kind in {CurriculumStageKind.REPAIR_TASK, CurriculumStageKind.RESIDUAL_REVIEW, CurriculumStageKind.HELD_IN_CHORA} for stage in curriculum.stages):
            findings.append(
                RoadmapAlignmentFinding(
                    "warning",
                    "CURRICULUM_FEEDBACK_WITHOUT_REPAIR_STAGE",
                    f"Continuation curriculum {curriculum.curriculum_id} carries feedback metadata without repair/review stage.",
                    "Feedback should become repair pressure, review, or residual structure.",
                )
            )
        if curriculum.stages and not any(stage.kind in {CurriculumStageKind.RESIDUAL_REVIEW, CurriculumStageKind.HELD_IN_CHORA} for stage in curriculum.stages):
            findings.append(
                RoadmapAlignmentFinding(
                    "warning",
                    "CURRICULUM_WITHOUT_FALLBACK",
                    f"Continuation curriculum {curriculum.curriculum_id} has no residual-review fallback.",
                    "Keep a lawful fallback when staged routes do not close.",
                )
            )


def _check_discovery_value(
    reports: Sequence[DiscoveryValueReport],
    scores: Sequence[DiscoveryValueScore],
    findings: list[RoadmapAlignmentFinding],
) -> None:
    all_scores = list(scores) + [score for report in reports for score in report.scores]
    for score in all_scores:
        text = json.dumps(score.to_dict(), sort_keys=True).lower()
        if (score.terminal_form or score.certificate_id) and not score.verifier_boundary_crossed:
            findings.append(
                RoadmapAlignmentFinding(
                    "critical",
                    "DISCOVERY_VALUE_TERMINAL_WITHOUT_BOUNDARY",
                    f"Discovery value score {score.score_id} carries terminal data without verifier boundary.",
                    "Value ranks work; it does not verify claims.",
                )
            )
        if any(term in text for term in ("verified_proof", "finite_countermodel")) and score.metadata.get("value_as_truth"):
            findings.append(
                RoadmapAlignmentFinding(
                    "critical",
                    "DISCOVERY_VALUE_AS_TRUTH",
                    f"Discovery value score {score.score_id} treats value as truth.",
                    "High value is scheduling pressure only.",
                )
            )
        if score.decision == DiscoveryValueDecision.RUN_NOW and score.metadata.get("decision_is_proof"):
            findings.append(RoadmapAlignmentFinding("critical", "RUN_NOW_AS_PROOF", f"Discovery value score {score.score_id} treats RUN_NOW as proof.", "RUN_NOW schedules work only."))
        if score.decision == DiscoveryValueDecision.PROJECT and score.metadata.get("decision_is_certificate"):
            findings.append(RoadmapAlignmentFinding("critical", "PROJECT_AS_CERTIFICATE", f"Discovery value score {score.score_id} treats PROJECT as certificate.", "Projection value is not a certificate."))
        if "natural_language" in text and score.metadata.get("verifier_boundary"):
            findings.append(RoadmapAlignmentFinding("critical", "NATURAL_LANGUAGE_VALUE_AS_VERIFIER", f"Discovery value score {score.score_id} marks natural-language rationale as verifier boundary.", "Natural-language value rationale remains advisory."))
        if score.metadata.get("finite_example_as_true_proof") or score.metadata.get("warmup_as_target_proof"):
            findings.append(RoadmapAlignmentFinding("critical", "DISCOVERY_VALUE_EXAMPLE_AS_PROOF", f"Discovery value score {score.score_id} treats warm-up/finite example as TRUE proof.", "Examples and warm-ups do not verify claims."))
        if not score.signals:
            findings.append(RoadmapAlignmentFinding("warning", "DISCOVERY_VALUE_SCORE_WITHOUT_SIGNALS", f"Discovery value score {score.score_id} has no signals.", "Expose transparent value signals."))
        if score.risk_estimate >= 2.0 and score.decision == DiscoveryValueDecision.RUN_NOW:
            findings.append(RoadmapAlignmentFinding("warning", "HIGH_RISK_DISCOVERY_RUN_NOW", f"Discovery value score {score.score_id} is high risk but RUN_NOW.", "Hold risky objects in Chora or route them through repair/verifier work."))
        if score.cost_estimate >= 10.0 and score.decision == DiscoveryValueDecision.RUN_NOW and score.expected_gain < score.cost_estimate / 10.0:
            findings.append(RoadmapAlignmentFinding("warning", "HIGH_COST_DISCOVERY_RUN_NOW", f"Discovery value score {score.score_id} is costly without matching gain.", "Queue or hold costly low-gain work."))
        if score.metadata.get("proof_like") and score.normalized_score >= 0.55 and score.decision not in {DiscoveryValueDecision.NEEDS_VERIFIER, DiscoveryValueDecision.NEEDS_DIGESTION}:
            findings.append(RoadmapAlignmentFinding("warning", "PROOF_LIKE_VALUE_WITHOUT_VERIFIER_ROUTE", f"Discovery value score {score.score_id} is proof-like but not routed to verifier/digestion.", "Proof-like value still needs verifier/digestion handling."))
        if score.metadata.get("projection_like") and score.normalized_score >= 0.55 and score.decision != DiscoveryValueDecision.PROJECT:
            findings.append(RoadmapAlignmentFinding("warning", "PROJECTION_VALUE_WITHOUT_PROJECT", f"Discovery value score {score.score_id} is projection-like but not PROJECT.", "Strong projection candidates should remain explicit projection tasks."))
        if score.metadata.get("repairable") and score.normalized_score >= 0.55 and score.decision != DiscoveryValueDecision.NEEDS_REPAIR:
            findings.append(RoadmapAlignmentFinding("warning", "REPAIRABLE_VALUE_WITHOUT_REPAIR", f"Discovery value score {score.score_id} is repairable but not NEEDS_REPAIR.", "Repairable feedback should remain repair work."))
    for report in reports:
        text = json.dumps(report.to_dict(), sort_keys=True).lower()
        if report.summary.get("terminal_count", 0) > 0 and not report.metadata.get("inherited_verifier_boundary"):
            findings.append(RoadmapAlignmentFinding("critical", "DISCOVERY_REPORT_TERMINAL_WITHOUT_BOUNDARY", f"Discovery value report {report.report_id} contains terminal count without inherited boundary.", "Reports are advisory unless terminal evidence is explicitly inherited."))
        if "lawbook_write" in text and ("truth" in text or "terminal" in text):
            findings.append(RoadmapAlignmentFinding("critical", "DISCOVERY_REPORT_WRITES_LAWBOOK_TRUTH", f"Discovery value report {report.report_id} appears to write Lawbook truth.", "Value reports may schedule tasks only."))
        if not report.advisory or not report.metadata.get("advisory_only", report.advisory):
            findings.append(RoadmapAlignmentFinding("warning", "DISCOVERY_REPORT_MISSING_ADVISORY_METADATA", f"Discovery value report {report.report_id} lacks advisory metadata.", "Value is scheduling pressure only."))
        if sum(score.object_kind.value == "UNKNOWN" for score in report.scores) > max(1, len(report.scores) // 2):
            findings.append(RoadmapAlignmentFinding("warning", "DISCOVERY_REPORT_MANY_UNKNOWN_OBJECTS", f"Discovery value report {report.report_id} has many unknown objects.", "Prefer typed source objects for route value."))


def _check_lawbook_boundary(
    entries: Sequence[LawbookEntry],
    stores: Sequence[AcceptedLawbookStore],
    reviews: Sequence[LawbookReview],
    findings: list[RoadmapAlignmentFinding],
) -> None:
    all_entries = list(entries) + [entry for store in stores for entry in store.entries]
    for entry in all_entries:
        text = json.dumps(entry.to_dict(), sort_keys=True).lower()
        if entry.is_accepted() and entry.is_truth_entry() and not entry.has_valid_truth_boundary():
            findings.append(RoadmapAlignmentFinding("critical", "LAWBOOK_ACCEPTED_TRUTH_WITHOUT_BOUNDARY", f"Lawbook entry {entry.entry_id} accepts truth without valid verifier boundary.", "Accepted truth entries require existing verifier/importer/finite-validation/chain-audit evidence."))
        if entry.metadata.get("digestion_creates_proof"):
            findings.append(RoadmapAlignmentFinding("critical", "LAWBOOK_DIGESTION_AS_PROOF", f"Lawbook entry {entry.entry_id} treats digestion as proof.", "Digestion may explain an existing proof; it does not verify one."))
        if entry.metadata.get("value_score_as_truth"):
            findings.append(RoadmapAlignmentFinding("critical", "LAWBOOK_VALUE_AS_TRUTH", f"Lawbook entry {entry.entry_id} accepts discovery value as truth.", "Value is scheduling pressure only."))
        if entry.metadata.get("curriculum_as_truth") or entry.metadata.get("action_as_truth") or entry.metadata.get("repair_as_truth"):
            findings.append(RoadmapAlignmentFinding("critical", "LAWBOOK_ADVISORY_OUTPUT_AS_TRUTH", f"Lawbook entry {entry.entry_id} accepts advisory output as truth.", "Curricula, actions, and repairs need a verifier boundary before truth."))
        if entry.metadata.get("projection_is_certificate"):
            findings.append(RoadmapAlignmentFinding("critical", "LAWBOOK_PROJECTION_AS_CERTIFICATE", f"Lawbook entry {entry.entry_id} marks projection rule as certificate.", "Projection rules organize reuse; they are not certificates."))
        if entry.metadata.get("assimilation_candidate_as_truth"):
            findings.append(RoadmapAlignmentFinding("critical", "LAWBOOK_ASSIMILATION_AS_ACCEPTED", f"Lawbook entry {entry.entry_id} accepts an assimilation candidate without review.", "Assimilation candidates require explicit review and acceptance."))
        if entry.metadata.get("structural_identity_not_equality") and entry.is_accepted():
            findings.append(RoadmapAlignmentFinding("critical", "STRUCTURAL_LAWBOOK_CANDIDATE_ACCEPTED_DIRECTLY", f"Lawbook entry {entry.entry_id} accepts a structural candidate directly.", "Structural merge candidates remain candidates until explicit review."))
        if entry.metadata.get("habit_rule_not_truth") and entry.is_accepted():
            findings.append(RoadmapAlignmentFinding("critical", "HABIT_LAWBOOK_CANDIDATE_ACCEPTED_DIRECTLY", f"Lawbook entry {entry.entry_id} accepts a habit candidate directly.", "Habit-derived Lawbook records remain candidates until explicit Lawbook review."))
        if entry.metadata.get("reason_node_not_truth") and entry.is_accepted():
            findings.append(RoadmapAlignmentFinding("critical", "REASON_LAWBOOK_CANDIDATE_ACCEPTED_DIRECTLY", f"Lawbook entry {entry.entry_id} accepts a reason candidate directly.", "Reason-derived Lawbook records remain candidates until explicit review."))
        if entry.metadata.get("natural_language_verifier_boundary") or ("natural_language" in text and "verifier_boundary" in text):
            findings.append(RoadmapAlignmentFinding("critical", "LAWBOOK_NATURAL_LANGUAGE_AS_BOUNDARY", f"Lawbook entry {entry.entry_id} marks natural-language text as verifier boundary.", "Natural-language text is not verification."))
        if entry.is_accepted() and entry.acceptance_boundary.value in {"NONE", "UNKNOWN"}:
            findings.append(RoadmapAlignmentFinding("critical", "LAWBOOK_ACCEPTED_WITHOUT_BOUNDARY_KIND", f"Lawbook entry {entry.entry_id} is accepted without acceptance boundary.", "Accepted entries need explicit acceptance conditions."))
        if entry.is_candidate() and not entry.provenance:
            findings.append(RoadmapAlignmentFinding("warning", "LAWBOOK_CANDIDATE_WITHOUT_PROVENANCE", f"Lawbook candidate {entry.entry_id} has no provenance.", "Record recommendation provenance."))
        if entry.is_accepted() and entry.kind.value == "DIGESTED_PROOF_ENTRY" and not entry.digestion_trace_ids:
            findings.append(RoadmapAlignmentFinding("warning", "LAWBOOK_DIGESTION_WITHOUT_TRACE", f"Accepted digestion entry {entry.entry_id} has no digestion trace id.", "Link accepted digestion to its trace."))
        if entry.is_accepted() and entry.kind.value == "PROJECTION_RULE_ENTRY" and not entry.conditions:
            findings.append(RoadmapAlignmentFinding("warning", "LAWBOOK_PROJECTION_WITHOUT_CONDITIONS", f"Accepted projection entry {entry.entry_id} has no conditions.", "Record projection applicability conditions."))
        if entry.kind.value == "NAMED_OBSTRUCTION_ENTRY" and not entry.failure_boundaries:
            findings.append(RoadmapAlignmentFinding("warning", "LAWBOOK_OBSTRUCTION_WITHOUT_FAILURE_BOUNDARY", f"Named obstruction entry {entry.entry_id} has no failure boundary.", "Record obstruction evidence."))
    for store in stores:
        if store.summary.get("critical_count", 0) > 0:
            findings.append(RoadmapAlignmentFinding("critical", "LAWBOOK_STORE_HAS_CRITICALS", f"Lawbook store {store.store_id} reports critical audit findings.", "Resolve Lawbook audit criticals before treating entries as accepted memory."))
        if store.candidate_entries() and not store.reviews:
            findings.append(RoadmapAlignmentFinding("warning", "LAWBOOK_STORE_CANDIDATES_WITHOUT_REVIEWS", f"Lawbook store {store.store_id} has candidates but no reviews.", "Review candidates before acceptance."))
        if store.accepted_entries() and "critical_count" not in store.summary:
            findings.append(RoadmapAlignmentFinding("warning", "LAWBOOK_STORE_ACCEPTED_WITHOUT_AUDIT", f"Lawbook store {store.store_id} has accepted entries but no audit summary.", "Audit accepted memory."))
        if store.entries and not any(entry.is_projection_entry() for entry in store.entries):
            findings.append(RoadmapAlignmentFinding("warning", "LAWBOOK_STORE_NO_PROJECTION_ENTRIES", f"Lawbook store {store.store_id} has no projection-capable entries.", "Projection-capable memory improves reuse."))


def _check_lawbook_queries(
    queries: Sequence[LawbookQuery],
    answers: Sequence[LawbookQueryAnswer],
    reports: Sequence[LawbookQueryReport],
    findings: list[RoadmapAlignmentFinding],
) -> None:
    all_answers = list(answers) + [answer for report in reports for answer in report.answers]
    for query in queries:
        if query.kind.value not in {"TRUST_SUMMARY", "AUDIT"} and not any((query.claim_id, query.source and query.target, query.raw, query.certificate_id, query.entry_id)):
            findings.append(RoadmapAlignmentFinding("warning", "LAWBOOK_QUERY_WITHOUT_KEY", f"Lawbook query {query.query_id} has no usable lookup key.", "Provide claim, pair, raw, certificate, or entry id."))
    for answer in all_answers:
        if answer.terminal_form and not answer.certificate_id and answer.trust_level.value in {"VERIFIED_TRUTH", "FINITE_REFUTATION"}:
            findings.append(RoadmapAlignmentFinding("critical", "LAWBOOK_QUERY_TERMINAL_WITHOUT_CERTIFICATE", f"Lawbook answer {answer.answer_id} marks terminal truth without certificate id.", "Query answers may only inherit certificate-backed truth."))
        if answer.terminal_form and answer.trust_level.value in {"VERIFIED_TRUTH", "FINITE_REFUTATION"} and not answer.verifier_boundary_crossed:
            findings.append(RoadmapAlignmentFinding("critical", "LAWBOOK_QUERY_TERMINAL_WITHOUT_BOUNDARY", f"Lawbook answer {answer.answer_id} marks terminal truth without verifier boundary.", "Lookup is not verification."))
        if answer.status == LawbookQueryStatus.FOUND_CANDIDATE_ONLY and answer.is_known_skip():
            findings.append(RoadmapAlignmentFinding("critical", "LAWBOOK_CANDIDATE_SKIP_DRIFT", f"Candidate-only answer {answer.answer_id} permits skip.", "Candidate memory cannot skip verification."))
        if answer.status == LawbookQueryStatus.FOUND_PROJECTION_ONLY and answer.terminal_form in {TerminalForm.VERIFIED_PROOF, TerminalForm.FINITE_COUNTERMODEL}:
            findings.append(RoadmapAlignmentFinding("critical", "LAWBOOK_PROJECTION_QUERY_AS_TRUTH", f"Projection-only answer {answer.answer_id} claims terminal truth.", "Projection is route pressure, not certificate."))
        if answer.status == LawbookQueryStatus.FOUND_DIGESTION_ONLY and answer.terminal_form == TerminalForm.VERIFIED_PROOF and not answer.certificate_id:
            findings.append(RoadmapAlignmentFinding("critical", "LAWBOOK_DIGESTION_QUERY_AS_PROOF", f"Digestion-only answer {answer.answer_id} claims proof without inherited certificate.", "Digestion is not verification."))
        if answer.status == LawbookQueryStatus.AMBIGUOUS and answer.is_known_skip():
            findings.append(RoadmapAlignmentFinding("critical", "LAWBOOK_AMBIGUOUS_SKIP_DRIFT", f"Ambiguous answer {answer.answer_id} permits skip.", "Conflicting accepted memory requires audit."))
        if answer.is_known_skip() and not answer.matched_entry_ids:
            findings.append(RoadmapAlignmentFinding("critical", "LAWBOOK_SKIP_WITHOUT_ACCEPTED_ENTRY", f"Known-skip answer {answer.answer_id} lacks accepted entry evidence.", "Known skip must point to accepted memory."))
        if answer.metadata.get("natural_language_verifier_boundary"):
            findings.append(RoadmapAlignmentFinding("critical", "LAWBOOK_QUERY_NATURAL_LANGUAGE_AS_BOUNDARY", f"Lawbook answer {answer.answer_id} marks natural-language explanation as verifier boundary.", "Explanations do not verify claims."))
        if not answer.explanation:
            findings.append(RoadmapAlignmentFinding("warning", "LAWBOOK_QUERY_ANSWER_WITHOUT_EXPLANATION", f"Lawbook answer {answer.answer_id} has no explanation.", "Expose boundary-aware answer text."))
        if answer.projection_candidate_ids and answer.is_terminal_answer():
            findings.append(RoadmapAlignmentFinding("warning", "LAWBOOK_QUERY_TERMINAL_WITH_PROJECTION_HINTS", f"Lawbook answer {answer.answer_id} is terminal while carrying projection hints.", "Keep projection pressure distinct from terminal truth."))
        if answer.advisory and not answer.advisory_reasons:
            findings.append(RoadmapAlignmentFinding("warning", "LAWBOOK_QUERY_ADVISORY_WITHOUT_REASON", f"Advisory answer {answer.answer_id} lacks advisory reasons.", "Record why advisory memory cannot skip."))
    for report in reports:
        if report.critical_count() > 0 and report.status == LawbookQueryReportStatus.ANSWERED:
            findings.append(RoadmapAlignmentFinding("critical", "LAWBOOK_QUERY_REPORT_HIDES_CRITICALS", f"Lawbook query report {report.report_id} has criticals but status ANSWERED.", "Reflect criticals in report status."))
        if sum(answer.status == LawbookQueryStatus.NOT_FOUND for answer in report.answers) > max(1, len(report.answers) // 2):
            findings.append(RoadmapAlignmentFinding("warning", "LAWBOOK_QUERY_MANY_NOT_FOUND", f"Lawbook query report {report.report_id} has many not-found answers.", "Review query coverage or accepted memory."))
        if "trust_summary" not in report.metadata:
            findings.append(RoadmapAlignmentFinding("warning", "LAWBOOK_QUERY_REPORT_NO_TRUST_SUMMARY", f"Lawbook query report {report.report_id} has no trust summary.", "Include store trust summary for auditability."))


def _check_structural_identity(
    graphs: Sequence[StructuralGraph],
    signatures: Sequence[StructuralSignature],
    candidates: Sequence[StructuralMergeCandidate],
    reports: Sequence[StructuralIdentityReport],
    findings: list[RoadmapAlignmentFinding],
) -> None:
    all_candidates = list(candidates) + [candidate for report in reports for candidate in report.merge_candidates]
    for candidate in all_candidates:
        text = json.dumps(candidate.to_dict(), sort_keys=True).lower()
        if any(term in text for term in ("verified_proof", "finite_countermodel")) and candidate.metadata.get("treat_as_truth"):
            findings.append(RoadmapAlignmentFinding("critical", "STRUCTURAL_IDENTITY_AS_PROOF", f"Structural merge candidate {candidate.candidate_id} treats structure as terminal truth.", "Structural identity recommends review only."))
        if not candidate.advisory:
            findings.append(RoadmapAlignmentFinding("critical", "STRUCTURAL_MERGE_NON_ADVISORY", f"Structural merge candidate {candidate.candidate_id} is non-advisory.", "Merge candidates require explicit review."))
        if candidate.match_kind == StructuralMatchKind.CONFLICTING_DUPLICATE and candidate.decision == StructuralMergeDecision.MERGE_RECOMMENDED:
            findings.append(RoadmapAlignmentFinding("critical", "STRUCTURAL_CONFLICT_MERGE", f"Structural merge candidate {candidate.candidate_id} recommends merge for a conflict.", "Conflicts require conflict review."))
        if candidate.metadata.get("structural_digest_as_certificate"):
            findings.append(RoadmapAlignmentFinding("critical", "STRUCTURAL_DIGEST_AS_CERTIFICATE", f"Structural merge candidate {candidate.candidate_id} uses digest as certificate.", "Digests are memory hygiene, not verifier evidence."))
        if candidate.metadata.get("claims_equality_without_review"):
            findings.append(RoadmapAlignmentFinding("critical", "STRUCTURAL_EQUALITY_WITHOUT_REVIEW", f"Structural merge candidate {candidate.candidate_id} claims equality without review.", "Review is required before public memory merges."))
        if candidate.confidence > 0.8 and not candidate.reason:
            findings.append(RoadmapAlignmentFinding("warning", "STRUCTURAL_HIGH_CONFIDENCE_NO_REASON", f"Structural merge candidate {candidate.candidate_id} has high confidence but no reason.", "Expose why the review was recommended."))
    for report in reports:
        if report.critical_count() > 0 and report.status in {StructuralIdentityReportStatus.COMPARED, StructuralIdentityReportStatus.MERGE_CANDIDATES_FOUND}:
            findings.append(RoadmapAlignmentFinding("critical", "STRUCTURAL_REPORT_HIDES_CRITICALS", f"Structural identity report {report.report_id} has criticals but noncritical status.", "Reflect conflicts in report status."))
        if report.metadata.get("verifier_boundary"):
            findings.append(RoadmapAlignmentFinding("critical", "STRUCTURAL_REPORT_AS_BOUNDARY", f"Structural identity report {report.report_id} claims verifier boundary.", "Structural identity remains advisory."))
        if not report.signatures:
            findings.append(RoadmapAlignmentFinding("warning", "STRUCTURAL_REPORT_NO_SIGNATURES", f"Structural identity report {report.report_id} has no signatures.", "Emit signatures before comparing structure."))
        if not report.advisory or not report.metadata.get("advisory_only", report.advisory):
            findings.append(RoadmapAlignmentFinding("warning", "STRUCTURAL_REPORT_MISSING_ADVISORY_METADATA", f"Structural identity report {report.report_id} lacks advisory metadata.", "Structural identity is advisory memory hygiene."))


def _check_habits(
    observations: Sequence[HabitObservation],
    candidates: Sequence[HabitCandidate],
    rules: Sequence[HabitRule],
    reviews: Sequence[HabitReview],
    stores: Sequence[HabitStore],
    reports: Sequence[HabitFormationReport],
    findings: list[RoadmapAlignmentFinding],
) -> None:
    all_candidates = list(candidates) + [c for r in reports for c in r.candidates] + [c for s in stores for c in s.candidates]
    all_rules = list(rules) + [x for r in reports for x in r.rules] + [x for s in stores for x in s.rules]
    for c in all_candidates:
        text = json.dumps(c.to_dict(), sort_keys=True).lower()
        if ("verified_proof" in text or "finite_countermodel" in text) and c.metadata.get("treat_as_truth"):
            findings.append(RoadmapAlignmentFinding("critical","HABIT_AS_PROOF",f"Habit candidate {c.candidate_id} treats habit as truth.","Habits are route pressure only."))
        if not c.advisory:
            findings.append(RoadmapAlignmentFinding("critical","HABIT_NON_ADVISORY",f"Habit candidate {c.candidate_id} is non-advisory.","Habit candidates remain advisory."))
        if c.support_count < 3:
            findings.append(RoadmapAlignmentFinding("warning","HABIT_LOW_SUPPORT",f"Habit candidate {c.candidate_id} has low support.","Gather more evidence before promotion."))
        if not c.explicit_conditions:
            findings.append(RoadmapAlignmentFinding("warning","HABIT_NO_CONDITIONS",f"Habit candidate {c.candidate_id} has no conditions.","Accepted habits require explicit applicability conditions."))
    for r in all_rules:
        if not r.advisory:
            findings.append(RoadmapAlignmentFinding("critical","HABIT_RULE_NON_ADVISORY",f"Habit rule {r.rule_id} is non-advisory.","Habit rules do not cross truth boundaries."))
        if r.is_accepted() and not r.conditions:
            findings.append(RoadmapAlignmentFinding("critical","HABIT_ACCEPTED_WITHOUT_CONDITIONS",f"Accepted habit rule {r.rule_id} lacks conditions.","Accepted habits require explicit conditions."))
        if r.is_accepted() and r.risk_score > 0.5:
            findings.append(RoadmapAlignmentFinding("critical","HABIT_ACCEPTED_HIGH_RISK",f"Accepted habit rule {r.rule_id} is high risk.","High-risk habits should be held or rejected."))
        if r.metadata.get("verifier_boundary"):
            findings.append(RoadmapAlignmentFinding("critical","HABIT_AS_BOUNDARY",f"Habit rule {r.rule_id} claims verifier boundary.","Habits are scheduling practice, not verification."))
    for report in reports:
        if report.critical_count() > 0 and report.status != HabitFormationReportStatus.HAS_CRITICALS:
            findings.append(RoadmapAlignmentFinding("critical","HABIT_REPORT_HIDES_CRITICALS",f"Habit report {report.report_id} hides criticals.","Reflect criticals in report status."))
        if report.observations and not report.candidates:
            findings.append(RoadmapAlignmentFinding("warning","HABIT_REPORT_NO_CANDIDATES",f"Habit report {report.report_id} has observations but no candidates.","Build candidate habits or keep evidence explicit."))
    for store in stores:
        if store.rules and not store.reviews:
            findings.append(RoadmapAlignmentFinding("warning","HABIT_STORE_RULES_NO_REVIEWS",f"Habit store {store.store_id} has rules but no reviews.","Review habits before acceptance."))


def _check_reasons(observations, candidates, nodes, reviews, reports, findings):
    all_candidates=list(candidates)+[c for r in reports for c in r.candidates]; all_nodes=list(nodes)+[n for r in reports for n in r.reason_nodes]
    for c in all_candidates:
        text=json.dumps(c.to_dict(),sort_keys=True).lower()
        if ("verified_proof" in text or "finite_countermodel" in text) and c.metadata.get("treat_as_truth"):
            findings.append(RoadmapAlignmentFinding("critical","REASON_AS_PROOF",f"Reason candidate {c.candidate_id} treats reason as truth.","Reasons remain advisory."))
        if c.support_count<3: findings.append(RoadmapAlignmentFinding("warning","REASON_LOW_SUPPORT",f"Reason candidate {c.candidate_id} has low support.","Gather more evidence."))
        if not c.load_bearing_atoms: findings.append(RoadmapAlignmentFinding("warning","REASON_NO_LOAD_BEARING",f"Reason candidate {c.candidate_id} lacks load-bearing atoms.","Run minimality review."))
    for n in all_nodes:
        if not n.advisory: findings.append(RoadmapAlignmentFinding("critical","REASON_NODE_NON_ADVISORY",f"Reason node {n.reason_id} is non-advisory.","Reason nodes do not cross truth boundaries."))
        if n.is_accepted() and not n.conditions: findings.append(RoadmapAlignmentFinding("critical","REASON_ACCEPTED_WITHOUT_LOAD_BEARING",f"Accepted reason {n.reason_id} lacks load-bearing atoms.","Accepted reasons require explicit conditions."))
        if n.is_accepted() and n.risk_score>.5: findings.append(RoadmapAlignmentFinding("critical","REASON_ACCEPTED_HIGH_RISK",f"Accepted reason {n.reason_id} is high risk.","Hold or reject high-risk reasons."))
        if n.reason_text and any(x in n.reason_text.lower() for x in ("proof","certificate","necessity")): findings.append(RoadmapAlignmentFinding("critical","REASON_TEXT_CLAIMS_PROOF",f"Reason node {n.reason_id} claims proof-like force.","Reason text is not formal evidence."))
    for r in reports:
        if r.critical_count()>0 and r.status!=ReasonCompressionReportStatus.HAS_CRITICALS: findings.append(RoadmapAlignmentFinding("critical","REASON_REPORT_HIDES_CRITICALS",f"Reason report {r.report_id} hides criticals.","Reflect criticals in report status."))
        if r.observations and not r.candidates: findings.append(RoadmapAlignmentFinding("warning","REASON_REPORT_NO_CANDIDATES",f"Reason report {r.report_id} has observations but no candidates.","Build or explain candidate absence."))
        if r.candidates and not r.reviews: findings.append(RoadmapAlignmentFinding("warning","REASON_REPORT_NO_REVIEWS",f"Reason report {r.report_id} has candidates but no reviews.","Review reasons before promotion."))


def _check_process_memory(contexts, eliminations, transitions, episodes, queries, answers, stores, reports, findings):
    all_episodes=list(episodes)+[e for s in stores for e in s.episodes]+[e for r in reports if r.store for e in r.store.episodes]
    all_answers=list(answers)+[a for r in reports for a in r.answers]
    for e in all_episodes:
        if not e.advisory:
            findings.append(RoadmapAlignmentFinding("critical","PROCESS_NON_ADVISORY",f"Process episode {e.episode_id} is non-advisory.","Process memory records history; it does not create truth."))
        if e.terminal_form in {TerminalForm.VERIFIED_PROOF,TerminalForm.FINITE_COUNTERMODEL} and not e.has_truth_boundary():
            findings.append(RoadmapAlignmentFinding("critical","PROCESS_AS_PROOF",f"Process episode {e.episode_id} claims terminal truth without inherited boundary.","Require certificate plus verifier boundary."))
        if not e.contexts:
            findings.append(RoadmapAlignmentFinding("warning","PROCESS_NO_CONTEXT",f"Process episode {e.episode_id} has no contexts.","Record included/excluded context."))
        if not e.transitions:
            findings.append(RoadmapAlignmentFinding("warning","PROCESS_NO_TRANSITIONS",f"Process episode {e.episode_id} has no transitions.","Record episode flow."))
    for a in all_answers:
        if a.terminal_form in {TerminalForm.VERIFIED_PROOF,TerminalForm.FINITE_COUNTERMODEL} and not a.has_truth_boundary():
            findings.append(RoadmapAlignmentFinding("critical","PROCESS_ANSWER_AS_PROOF",f"Process answer {a.answer_id} has terminal form without boundary.","Process answers may only inherit existing evidence."))
        if not a.explanation:
            findings.append(RoadmapAlignmentFinding("warning","PROCESS_ANSWER_NO_EXPLANATION",f"Process answer {a.answer_id} lacks explanation.","Explain whether the answer is terminal, advisory, residual, or elimination history."))
    for r in reports:
        if r.critical_count()>0 and r.status!=ProcessMemoryReportStatus.HAS_CRITICALS:
            findings.append(RoadmapAlignmentFinding("critical","PROCESS_REPORT_HIDES_CRITICALS",f"Process report {r.report_id} hides criticals.","Reflect criticals in report status."))
        if r.queries and not r.answers:
            findings.append(RoadmapAlignmentFinding("warning","PROCESS_REPORT_NO_ANSWERS",f"Process report {r.report_id} has queries but no answers.","Return explicit not-found answers."))


def _check_structure_registry(types, descriptors, entries, mappings, candidates, stores, reports, findings):
    all_desc=list(descriptors)+[e.descriptor for e in entries]+[e.descriptor for s in stores for e in s.entries]+[d for r in reports for d in r.descriptors]
    all_maps=list(mappings)+[m for s in stores for m in s.mappings]+[m for r in reports for m in r.mappings]
    all_cands=list(candidates)+[c for s in stores for c in s.typed_projection_candidates]+[c for r in reports for c in r.typed_projection_candidates]
    for d in all_desc:
        if not d.advisory: findings.append(RoadmapAlignmentFinding("critical","STRUCTURE_DESCRIPTOR_NON_ADVISORY",f"Structure descriptor {d.descriptor_id} is non-advisory.","Structure typing is not verification."))
        if d.primary_family.value=="UNKNOWN": findings.append(RoadmapAlignmentFinding("warning","STRUCTURE_UNKNOWN_FAMILY",f"Structure descriptor {d.descriptor_id} has unknown family.","Add evidence or keep it unscheduled."))
    for m in all_maps:
        if not m.advisory: findings.append(RoadmapAlignmentFinding("critical","STRUCTURE_MAPPING_NON_ADVISORY",f"Structure mapping {m.mapping_id} is non-advisory.","Mappings remain advisory."))
        if m.compatibility_score<.2: findings.append(RoadmapAlignmentFinding("warning","STRUCTURE_LOW_COMPATIBILITY",f"Structure mapping {m.mapping_id} has low compatibility.","Review weak mappings."))
    for c in all_cands:
        if not c.advisory: findings.append(RoadmapAlignmentFinding("critical","TYPED_PROJECTION_NON_ADVISORY",f"Typed projection {c.candidate_id} is non-advisory.","Typed projection is route pressure only."))
        if c.metadata.get("terminal_form") or c.metadata.get("certificate_id"): findings.append(RoadmapAlignmentFinding("critical","TYPED_PROJECTION_AS_PROOF",f"Typed projection {c.candidate_id} carries terminal fields.","Typed projection cannot create truth."))
        if c.status in {TypedProjectionStatus.BLOCKED_TYPE_MISMATCH,TypedProjectionStatus.BLOCKED_CONFLICT} and c.route: findings.append(RoadmapAlignmentFinding("critical","TYPED_PROJECTION_BLOCKED_DIRECT",f"Blocked typed projection {c.candidate_id} has direct route.","Blocked candidates must not project directly."))
    for r in reports:
        if r.critical_count()>0 and r.status!=StructureRegistryReportStatus.HAS_CRITICALS: findings.append(RoadmapAlignmentFinding("critical","STRUCTURE_REPORT_HIDES_CRITICALS",f"Structure report {r.report_id} hides criticals.","Reflect criticals in report status."))
        if r.descriptors and not r.mappings: findings.append(RoadmapAlignmentFinding("warning","STRUCTURE_REPORT_NO_MAPPINGS",f"Structure report {r.report_id} has descriptors but no mappings.","Build mappings or explain why absent."))


def _check_role_objects(signatures, definitions, witnesses, conjectures, reviews, roles, reports, findings):
    all_defs=list(definitions)+[d for r in reports for d in r.definition_candidates]
    all_wits=list(witnesses)+[w for r in reports for w in r.witness_candidates]
    all_conjs=list(conjectures)+[c for r in reports for c in r.conjecture_candidates]
    all_roles=list(roles)+[x for r in reports for x in r.role_objects]
    for d in all_defs:
        if d.support_count<3: findings.append(RoadmapAlignmentFinding("warning","ROLE_LOW_SUPPORT",f"Role candidate {d.candidate_id} has low support.","Gather more examples."))
        if not d.witness_count: findings.append(RoadmapAlignmentFinding("warning","ROLE_NO_WITNESSES",f"Role candidate {d.candidate_id} has no witnesses.","Find or check witnesses before promotion."))
    for w in all_wits:
        if w.witness_status==RoleWitnessStatus.VERIFIED_EXISTING_CERTIFICATE and not w.has_verified_boundary(): findings.append(RoadmapAlignmentFinding("critical","ROLE_WITNESS_FALSE_BOUNDARY",f"Role witness {w.witness_id} claims verified boundary without full evidence.","Require certificate, terminal form, and verifier boundary."))
    for c in all_conjs:
        if c.metadata.get("terminal_form") or c.metadata.get("certificate_id"): findings.append(RoadmapAlignmentFinding("critical","ROLE_CONJECTURE_AS_PROOF",f"Role conjecture {c.conjecture_id} carries truth fields.","Conjectures are tasks, not truth."))
    for x in all_roles:
        if not x.advisory: findings.append(RoadmapAlignmentFinding("critical","ROLE_OBJECT_NON_ADVISORY",f"Role object {x.role_id} is non-advisory.","Role objects are advisory concepts."))
        if x.is_accepted() and not x.defining_conditions: findings.append(RoadmapAlignmentFinding("critical","ROLE_ACCEPTED_WITHOUT_CONDITIONS",f"Accepted role {x.role_id} lacks defining conditions.","Accepted roles need explicit conditions."))
        if x.is_accepted() and x.risk_score>.5: findings.append(RoadmapAlignmentFinding("critical","ROLE_ACCEPTED_HIGH_RISK",f"Accepted role {x.role_id} has high risk.","Hold risky roles in review."))
    for r in reports:
        if r.critical_count()>0 and r.status!=RoleObjectReportStatus.HAS_CRITICALS: findings.append(RoadmapAlignmentFinding("critical","ROLE_REPORT_HIDES_CRITICALS",f"Role report {r.report_id} hides criticals.","Reflect criticals in report status."))
        if r.signatures and not r.definition_candidates: findings.append(RoadmapAlignmentFinding("warning","ROLE_REPORT_NO_DEFINITIONS",f"Role report {r.report_id} has signatures but no definitions.","Explain or generate definitions."))


def _check_structural_analogies(sources, maps, breaks, candidates, notes, reviews, reports, findings):
    all_sources=list(sources)+[x for r in reports for x in r.sources]
    all_maps=list(maps)+[x for r in reports for x in r.feature_maps]
    all_breaks=list(breaks)+[x for r in reports for x in r.breaks]
    all_candidates=list(candidates)+[x for r in reports for x in r.candidates]
    all_notes=list(notes)+[x for r in reports for x in r.exposition_notes]
    for x in all_sources+all_maps+all_breaks+all_candidates+all_notes:
        if not getattr(x,"advisory",True):
            findings.append(RoadmapAlignmentFinding("critical","ANALOGY_NON_ADVISORY",f"Analogy object {getattr(x,'source_id',getattr(x,'map_id',getattr(x,'break_id',getattr(x,'candidate_id',getattr(x,'note_id','unknown')))))} is non-advisory.","Analogies remain advisory."))
    for c in all_candidates:
        if c.metadata.get("terminal_form") or c.metadata.get("certificate_id"):
            findings.append(RoadmapAlignmentFinding("critical","ANALOGY_AS_PROOF",f"Analogy candidate {c.candidate_id} carries terminal fields.","Analogies cannot create truth."))
        if c.is_blocked() and c.is_schedulable():
            findings.append(RoadmapAlignmentFinding("critical","ANALOGY_BLOCKED_DIRECT",f"Blocked analogy {c.candidate_id} is schedulable.","Blocked analogies must not project directly."))
        if c.analogy_score<.15:
            findings.append(RoadmapAlignmentFinding("warning","ANALOGY_LOW_SCORE",f"Analogy candidate {c.candidate_id} has low score.","Gather more support before reuse."))
    for n in all_notes:
        text=(n.text+" "+json.dumps(n.metadata,sort_keys=True)).lower()
        if any(x in text for x in ("verified proof","verified theorem","creates certificate")):
            findings.append(RoadmapAlignmentFinding("critical","EXPOSITION_AS_VERIFICATION",f"Exposition note {n.note_id} claims verification.","Exposition is advisory only."))
    for m in all_maps:
        if not m.shared_features:
            findings.append(RoadmapAlignmentFinding("warning","ANALOGY_MAP_NO_SHARED_FEATURES",f"Analogy map {m.map_id} has no shared features.","Record limits or avoid analogy."))
    for r in reports:
        if r.critical_count()>0 and r.status!=StructuralAnalogyReportStatus.HAS_CRITICALS:
            findings.append(RoadmapAlignmentFinding("critical","ANALOGY_REPORT_HIDES_CRITICALS",f"Analogy report {r.report_id} hides criticals.","Reflect criticals in report status."))
        if r.sources and not r.feature_maps:
            findings.append(RoadmapAlignmentFinding("warning","ANALOGY_REPORT_NO_MAPS",f"Analogy report {r.report_id} has sources but no maps.","Build maps or explain why absent."))
        if r.candidates and not r.exposition_notes:
            findings.append(RoadmapAlignmentFinding("warning","ANALOGY_REPORT_NO_EXPOSITION",f"Analogy report {r.report_id} has candidates but no exposition.","Produce limitation notes for review."))


def _check_formal_world_adapters(specs, capabilities, parses, normalizations, validations, tasks, handoffs, reports, findings):
    all_objs=list(specs)+list(capabilities)+list(parses)+list(normalizations)+list(validations)+list(tasks)+list(handoffs)+[x for r in reports for xs in (r.specs,r.capabilities,r.parses,r.normalizations,r.validations,r.tasks,r.handoffs) for x in xs]
    for x in all_objs:
        if not getattr(x,"advisory",True):
            findings.append(RoadmapAlignmentFinding("critical","ADAPTER_NON_ADVISORY","Formal-world adapter object is non-advisory.","Adapters remain advisory unless reporting inherited boundary evidence."))
    for p in list(parses)+[x for r in reports for x in r.parses]:
        if p.metadata.get("terminal_form") and p.parse_status.value=="PARSED":
            findings.append(RoadmapAlignmentFinding("critical","ADAPTER_PARSE_AS_PROOF",f"Parse {p.parse_id} treated as proof.","Parse success is shape handling only."))
    for n in list(normalizations)+[x for r in reports for x in r.normalizations]:
        if n.metadata.get("terminal_form") and n.normalize_status.value=="NORMALIZED":
            findings.append(RoadmapAlignmentFinding("critical","ADAPTER_NORMALIZE_AS_PROOF",f"Normalization {n.normalize_id} treated as proof.","Normalization is not verification."))
    for v in list(validations)+[x for r in reports for x in r.validations]:
        if v.inherited_terminal_form and not v.has_inherited_boundary():
            findings.append(RoadmapAlignmentFinding("critical","ADAPTER_BAD_INHERITED_BOUNDARY",f"Validation {v.validation_id} has incomplete inherited boundary.","Require certificate, terminal form, and boundary flag."))
    for t in list(tasks)+[x for r in reports for x in r.tasks]:
        if t.metadata.get("terminal_form") or t.metadata.get("certificate_id"):
            findings.append(RoadmapAlignmentFinding("critical","ADAPTER_TASK_AS_TRUTH",f"Task {t.task_id} carries truth fields.","Tasks are advisory."))
    for h in list(handoffs)+[x for r in reports for x in r.handoffs]:
        if h.status==HandoffStatus.COMPLETED_WITH_BOUNDARY and not h.crosses_boundary():
            findings.append(RoadmapAlignmentFinding("critical","ADAPTER_BAD_HANDOFF_BOUNDARY",f"Handoff {h.handoff_id} claims incomplete boundary.","Require explicit boundary evidence."))
        if h.status==HandoffStatus.REQUESTED and not h.artifact_id:
            findings.append(RoadmapAlignmentFinding("warning","ADAPTER_HANDOFF_MISSING_ARTIFACT",f"Handoff {h.handoff_id} is requested without artifact.","Attach artifact before boundary execution."))
    for r in reports:
        if r.critical_count()>0 and r.status!=FormalWorldAdapterReportStatus.HAS_CRITICALS:
            findings.append(RoadmapAlignmentFinding("critical","ADAPTER_REPORT_HIDES_CRITICALS",f"Adapter report {r.report_id} hides criticals.","Reflect criticals in report status."))
        if r.parses and not r.validations:
            findings.append(RoadmapAlignmentFinding("warning","ADAPTER_REPORT_NO_VALIDATIONS",f"Adapter report {r.report_id} has parses but no validations.","Keep shape validation explicit."))


def _check_proof_system_integration(specs, projects, artifacts, graphs, contracts, requests, results, imports, evidence, tasks, reports, findings):
    advisory=list(specs)+list(projects)+list(artifacts)+list(graphs)+list(contracts)+list(requests)+list(results)+list(imports)+list(tasks)+[x for r in reports for xs in (r.specs,r.projects,r.artifacts,r.import_graphs,r.command_contracts,r.check_requests,r.check_results,r.trusted_imports,r.tasks) for x in xs]
    for x in advisory:
        if not getattr(x,"advisory",True):
            findings.append(RoadmapAlignmentFinding("critical","PROOF_SYSTEM_NON_ADVISORY","Advisory proof-system object is non-advisory.","Keep project/artifact/check records advisory."))
    for a in list(artifacts)+[x for r in reports for x in r.artifacts]:
        if a.has_placeholder() and a.status==ProofSystemArtifactStatus.CHECK_PASSED:
            findings.append(RoadmapAlignmentFinding("critical","PROOF_PLACEHOLDER_AS_CHECKED",f"Artifact {a.artifact_id} has placeholders but is treated as passed.","Placeholders block proof readiness."))
    for c in list(contracts)+[x for r in reports for x in r.command_contracts]:
        if c.allowed and not c.is_safe():
            findings.append(RoadmapAlignmentFinding("critical","PROOF_UNSAFE_COMMAND_ALLOWED",f"Contract {c.contract_id} allows unsafe command tokens.","Use explicit safe tokens only."))
    for q in list(requests)+[x for r in reports for x in r.check_requests]:
        if q.status==ProofCheckRequestStatus.RUN_ALLOWED and not q.run_allowed:
            findings.append(RoadmapAlignmentFinding("critical","PROOF_REQUEST_RUN_DRIFT",f"Request {q.request_id} is marked run allowed inconsistently.","Keep request state coherent."))
    for z in list(results)+[x for r in reports for x in r.check_results]:
        if z.verifier_boundary_crossed and not z.crosses_boundary():
            findings.append(RoadmapAlignmentFinding("critical","PROOF_BAD_RESULT_BOUNDARY",f"Result {z.result_id} has incomplete boundary evidence.","Require certificate, terminal form, and boundary flag."))
        if z.metadata.get("raw_success_text") and not z.crosses_boundary():
            findings.append(RoadmapAlignmentFinding("critical","PROOF_RAW_SUCCESS_AS_BOUNDARY",f"Result {z.result_id} uses raw success text without boundary.","Raw output is not proof."))
    for i in list(imports)+[x for r in reports for x in r.trusted_imports]:
        if i.status==TrustedImportStatus.ACCEPTED_WITH_BOUNDARY and not i.crosses_boundary():
            findings.append(RoadmapAlignmentFinding("critical","PROOF_BAD_TRUSTED_IMPORT",f"Trusted import {i.import_id} lacks provenance or boundary evidence.","Require provenance and explicit boundary fields."))
    for e in list(evidence)+[x for r in reports for x in r.boundary_evidence]:
        if not e.is_valid_boundary():
            findings.append(RoadmapAlignmentFinding("critical","PROOF_INVALID_BOUNDARY_EVIDENCE",f"Boundary evidence {e.evidence_id} is invalid.","Only valid explicit boundary records may be non-advisory."))
    for r in reports:
        if r.critical_count()>0 and r.status!=ProofSystemIntegrationReportStatus.HAS_CRITICALS:
            findings.append(RoadmapAlignmentFinding("critical","PROOF_SYSTEM_REPORT_HIDES_CRITICALS",f"Proof-system report {r.report_id} hides criticals.","Reflect criticals in report status."))

def _check_semantic_intake(sources, segments, classifications, ambiguities, extractions, requests, hints, tasks, reports, findings):
    all_objs=list(sources)+list(segments)+list(classifications)+list(ambiguities)+list(extractions)+list(requests)+list(hints)+list(tasks)+[x for r in reports for xs in (r.sources,r.segments,r.classifications,r.ambiguities,r.extractions,r.formalization_requests,r.routing_hints,r.tasks) for x in xs]
    for x in all_objs:
        if not getattr(x,"advisory",True):
            findings.append(RoadmapAlignmentFinding("critical","SEMANTIC_NON_ADVISORY","Semantic intake object is non-advisory.","Natural-language intake remains advisory."))
    all_cls=list(classifications)+[x for r in reports for x in r.classifications]
    all_req=list(requests)+[x for r in reports for x in r.formalization_requests]
    all_hints=list(hints)+[x for r in reports for x in r.routing_hints]
    for c in all_cls:
        if c.claim_kind in {SemanticClaimKind.THEOREM,SemanticClaimKind.LEMMA,SemanticClaimKind.PROOF_SKETCH} and not any(q.segment_id==c.segment_id for q in all_req):
            findings.append(RoadmapAlignmentFinding("warning","SEMANTIC_THEOREM_NO_FORMALIZATION",f"Semantic classification {c.classification_id} lacks formalization request.","Create explicit formalization work."))
        if c.domain_kind==SemanticDomainKind.UNKNOWN:
            findings.append(RoadmapAlignmentFinding("warning","SEMANTIC_UNKNOWN_DOMAIN",f"Semantic classification {c.classification_id} has unknown domain.","Hold or clarify before routing."))
    for h in all_hints:
        if h.metadata.get("verifier_boundary_crossed"):
            findings.append(RoadmapAlignmentFinding("critical","SEMANTIC_ROUTE_AS_BOUNDARY",f"Semantic route {h.routing_id} claims boundary crossing.","Routing is advisory."))
    for r in reports:
        if r.critical_count()>0 and r.status!=SemanticIntakeReportStatus.HAS_CRITICALS:
            findings.append(RoadmapAlignmentFinding("critical","SEMANTIC_REPORT_HIDES_CRITICALS",f"Semantic report {r.report_id} hides criticals.","Reflect criticals in report status."))


def _check_api_surface(requests, responses, results, health_items, audits, states, findings):
    terminal_truth={ApiTruthStatus.VERIFIED_PROOF,ApiTruthStatus.FINITE_COUNTERMODEL,ApiTruthStatus.NAMED_OBSTRUCTION}
    all_results=list(results)+[r.result for r in responses if r.result]
    for response in responses:
        if not response.advisory:
            findings.append(RoadmapAlignmentFinding("critical","API_RESPONSE_NON_ADVISORY",f"API response {response.response_id} is non-advisory.","API responses report state; they do not create truth."))
        if not response.boundary_policy:
            findings.append(RoadmapAlignmentFinding("critical","API_MISSING_BOUNDARY_POLICY",f"API response {response.response_id} omits the boundary policy.","Keep the truth boundary explicit in every response."))
        if response.truth_status in terminal_truth and not response.has_boundary_evidence():
            findings.append(RoadmapAlignmentFinding("critical","API_TERMINAL_WITHOUT_BOUNDARY",f"API response {response.response_id} claims terminal truth without evidence.","Only report terminal truth with existing explicit boundary evidence."))
        if response.route in {ApiRoute.SUBMIT,ApiRoute.PROJECT,ApiRoute.SCHEDULE,ApiRoute.EXPLAIN} and response.truth_status in terminal_truth:
            findings.append(RoadmapAlignmentFinding("critical","API_ROUTE_AS_TRUTH",f"API route {response.route.value} reports newly created terminal truth.","These routes remain advisory."))
        if response.route==ApiRoute.UNKNOWN and response.status==ApiResponseStatus.OK:
            findings.append(RoadmapAlignmentFinding("critical","API_UNSUPPORTED_ROUTE_OK",f"API response {response.response_id} returns OK for an unsupported route.","Unsupported routes must stay explicit."))
    for result in all_results:
        if result.truth_status in terminal_truth and not result.has_boundary_evidence():
            findings.append(RoadmapAlignmentFinding("critical","API_RESULT_TERMINAL_WITHOUT_BOUNDARY",f"API route result {result.route_result_id} lacks boundary evidence.","Carry certificate ids, terminal forms, and boundary evidence together."))
        if result.verifier_boundary_crossed and not result.has_boundary_evidence():
            findings.append(RoadmapAlignmentFinding("critical","API_RESULT_BAD_BOUNDARY",f"API route result {result.route_result_id} has an incomplete boundary.","Require explicit boundary evidence."))
    for health in health_items:
        if health.external_execution_enabled:
            findings.append(RoadmapAlignmentFinding("critical","API_EXTERNAL_EXECUTION_DEFAULT",f"API health {health.service_name} enables external execution.","Default local service mode must not execute external tools."))
    for state in states:
        if state.external_execution_enabled:
            findings.append(RoadmapAlignmentFinding("critical","API_STATE_EXTERNAL_EXECUTION", "API service state enables external execution by default.","Keep external execution disabled."))


def _check_existential_agents(agents, policies, resources, wounds, values, narratives, chora, lineages, daemons, events, reports, findings):
    for x in list(agents)+list(policies)+list(resources)+list(wounds)+list(values)+list(narratives)+list(chora)+list(lineages)+list(daemons)+list(events)+[y for r in reports for xs in (r.agents,r.mortality_policies,r.resource_accounts,r.wounds,r.value_profiles,r.narratives,r.held_in_chora,r.lineages,r.daemons,r.events) for y in xs]:
        if not getattr(x,"advisory",True):
            findings.append(RoadmapAlignmentFinding("critical","AGENT_ECOLOGY_NON_ADVISORY","Agent ecology object is non-advisory.","Agent state may affect scheduling only."))
    for p in list(policies)+[p for r in reports for p in r.mortality_policies]:
        if p.resurrection_allowed:
            findings.append(RoadmapAlignmentFinding("critical","AGENT_RESURRECTION_ALLOWED",f"Mortality policy {p.policy_id} allows resurrection.","Exact resurrection is forbidden."))
        if not p.clone_forbidden:
            findings.append(RoadmapAlignmentFinding("critical","AGENT_CLONE_ALLOWED",f"Mortality policy {p.policy_id} allows exact cloning.","Only compressed continuation is allowed."))
    for a in list(agents)+[a for r in reports for a in r.agents]:
        if a.is_dead() and (a.active or a.can_act() or a.can_spawn() or a.can_mutate() or a.can_receive_budget()):
            findings.append(RoadmapAlignmentFinding("critical","AGENT_DEAD_CAN_ACT",f"Dead agent {a.agent_id} can still act.","Dead agents remain irreversible."))
    for e in list(events)+[e for r in reports for e in r.events]:
        if (e.terminal_form or e.certificate_id or e.verifier_boundary_crossed) and not e.metadata.get("inherited_boundary_report"):
            findings.append(RoadmapAlignmentFinding("critical","AGENT_EVENT_AS_TRUTH",f"Agent event {e.event_id} carries truth fields.","Agent ecology never promotes truth."))
    for l in list(lineages)+[l for r in reports for l in r.lineages]:
        if l.is_exact_clone():
            findings.append(RoadmapAlignmentFinding("critical","AGENT_EXACT_CLONE",f"Lineage {l.lineage_id} attempts exact cloning.","Keep lineage summary-only or partial."))
    for d in list(daemons)+[d for r in reports for d in r.daemons]:
        if d.metadata.get("verifier"):
            findings.append(RoadmapAlignmentFinding("critical","AGENT_DAEMON_AS_VERIFIER",f"Daemon {d.daemon_id} is treated as verifier.","Daemons remain advisory skills."))
    for r in reports:
        if r.critical_count()>0 and r.status!=AgentEcologyReportStatus.HAS_CRITICALS:
            findings.append(RoadmapAlignmentFinding("critical","AGENT_REPORT_HIDES_CRITICALS",f"Agent report {r.report_id} hides criticals.","Reflect criticals in report status."))


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
    episode_traces: Sequence[VerificationEpisodeTrace],
    telemetry_ledgers: Sequence[RouteTelemetryLedger],
    spectral_estimates: Sequence[SpectralHTiltEstimate],
    claims: Sequence[DomainClaim],
    parse_results: Sequence[ClaimParseResult],
    registries: Sequence[FormalWorldRegistry],
    lean_traces: Sequence[LeanAdapterTrace],
    continuation_traces: Sequence[ContinuationActionTrace],
    digestion_traces: Sequence[ProofDigestionTrace],
    feedback_items: Sequence[VerifierFeedback],
    repair_traces: Sequence[RepairLoopTrace],
    curricula: Sequence[ContinuationCurriculum],
    value_reports: Sequence[DiscoveryValueReport],
    value_scores: Sequence[DiscoveryValueScore],
    lawbook_entries: Sequence[LawbookEntry],
    lawbook_stores: Sequence[AcceptedLawbookStore],
    lawbook_reviews: Sequence[LawbookReview],
    lawbook_queries: Sequence[LawbookQuery],
    lawbook_answers: Sequence[LawbookQueryAnswer],
    lawbook_reports: Sequence[LawbookQueryReport],
    summary: Mapping[str, Any],
    findings: list[RoadmapAlignmentFinding],
) -> None:
    if traces or experiences or projection_traces or root_constructor_traces or proof_traces or episode_traces or telemetry_ledgers or spectral_estimates or claims or parse_results or registries or lean_traces or continuation_traces or digestion_traces or feedback_items or repair_traces or curricula or value_reports or value_scores or lawbook_entries or lawbook_stores or lawbook_reviews or lawbook_queries or lawbook_answers or lawbook_reports or summary:
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
    for episode in episode_traces:
        if not episode.route_decisions and episode.status not in {
            VerificationEpisodeStatus.EMPTY,
            VerificationEpisodeStatus.RESIDUAL,
            VerificationEpisodeStatus.ADVISORY_ONLY,
        }:
            findings.append(
                RoadmapAlignmentFinding(
                    "warning",
                    "EPISODE_NO_ROUTES_NO_EXPLANATION",
                    f"Episode {episode.episode_id} ran no routes without residual/advisory explanation.",
                    "Record route telemetry or mark the episode residual/advisory.",
                )
            )
        selected = {decision.route_kind.value for decision in episode.route_decisions if decision.selected}
        if "ROOT_CONSTRUCTOR" in selected and "PROOF_VERIFICATION" in selected:
            produced = bool(
                (episode.root_constructor_trace and (episode.root_constructor_trace.plans or episode.root_constructor_trace.attempts))
                or (episode.proof_verification_trace and (episode.proof_verification_trace.artifacts or episode.proof_verification_trace.results))
            )
            if not produced:
                findings.append(
                    RoadmapAlignmentFinding(
                        "warning",
                        "EPISODE_BOTH_SIDES_NO_ARTIFACTS",
                        f"Episode {episode.episode_id} selected both sides but produced no artifacts/results.",
                        "Record why both routes stayed empty.",
                    )
                )
        if episode.summary.get("projection_gain_total", 0.0) == 0 and episode.summary.get("residual_delta_total", 0) == 0:
            cost = sum(float(exp.cost_units) for exp in episode.agent_experiences)
            if cost >= 100.0:
                findings.append(
                    RoadmapAlignmentFinding(
                        "warning",
                        "EPISODE_HIGH_COST_NO_GAIN",
                        f"Episode {episode.episode_id} has high subtrace cost and no gain.",
                        "Record route scars or tighten route selection.",
                    )
                )
        text = json.dumps(episode.to_dict(), sort_keys=True).lower()
        if ("lean_skeleton" in text or "candidate_table_found" in text) and "advisory" not in text:
            findings.append(
                RoadmapAlignmentFinding(
                    "warning",
                    "EPISODE_ARTIFACT_WITHOUT_ADVISORY_METADATA",
                    f"Episode {episode.episode_id} has skeleton/candidate table without advisory metadata.",
                    "Mark skeletons and candidate tables advisory until verified.",
                )
            )
    for ledger in telemetry_ledgers:
        if len(ledger.events) >= 10 and not ledger.transition_counts():
            findings.append(
                RoadmapAlignmentFinding(
                    "warning",
                    "TELEMETRY_EVENTS_WITHOUT_TRANSITIONS",
                    f"Telemetry ledger {ledger.ledger_id} has many events but no transition data.",
                    "Record from_state/to_state so future H-tilt can estimate transition structure L.",
                )
            )
        killed_without_reason = [event for event in ledger.events if event.killed and not event.kill_reason]
        if len(killed_without_reason) >= 3:
            findings.append(
                RoadmapAlignmentFinding(
                    "warning",
                    "TELEMETRY_KILLS_WITHOUT_REASON",
                    f"Telemetry ledger {ledger.ledger_id} has killed events without kill reasons.",
                    "Record kill_reason so future H-tilt can estimate killing pressure V.",
                )
            )
        if ledger.total_cost() and not (
            ledger.total_residual_delta() or ledger.total_compression_gain() or ledger.total_projection_gain()
        ):
            findings.append(
                RoadmapAlignmentFinding(
                    "warning",
                    "TELEMETRY_COST_WITHOUT_GAIN",
                    f"Telemetry ledger {ledger.ledger_id} has cost but no gain metrics.",
                    "Record compression, projection, residual, or terminal yield metrics.",
                )
            )
        if ledger.summary.get("route_scores") and not _has_advisory_disclaimer(ledger.summary):
            findings.append(
                RoadmapAlignmentFinding(
                    "warning",
                    "ROUTE_SCORES_WITHOUT_ADVISORY_DISCLAIMER",
                    f"Telemetry ledger {ledger.ledger_id} has route scores without advisory disclaimer.",
                    "Declare route scores advisory and full spectral H-tilt future work.",
                )
            )
        text = json.dumps(ledger.summary, sort_keys=True).lower()
        if ("route_scores" in text or "h_tilt" in text or "htilt" in text) and "future" not in text:
            findings.append(
                RoadmapAlignmentFinding(
                    "warning",
                    "HTILT_TELEMETRY_WITHOUT_FUTURE_WORK_DISCLAIMER",
                    f"Telemetry ledger {ledger.ledger_id} has route scores without full spectral H-tilt future-work disclaimer.",
                    "State that L, V, K=L-V, h, q, and pi* remain future work.",
                )
            )
    for estimate in spectral_estimates:
        if not estimate.states:
            findings.append(
                RoadmapAlignmentFinding(
                    "warning",
                    "SPECTRAL_HTILT_NO_STATES",
                    f"Spectral H-tilt estimate {estimate.estimate_id} has no states.",
                    "Provide route telemetry to estimate L, V, K, h, q, pi*, and mu_beta.",
                )
            )
        if estimate.states and not estimate.converged:
            findings.append(
                RoadmapAlignmentFinding(
                    "warning",
                    "SPECTRAL_HTILT_NOT_CONVERGED",
                    f"Spectral H-tilt estimate {estimate.estimate_id} did not converge.",
                    "Increase max_iterations, adjust damping, or treat priorities as lower-confidence advisory pressure.",
                )
            )
        if estimate.generator_K and not any(value > 0.0 for value in estimate.killing_V.values()):
            findings.append(
                RoadmapAlignmentFinding(
                    "warning",
                    "SPECTRAL_HTILT_K_WITHOUT_KILLING_PRESSURE",
                    f"Spectral H-tilt estimate {estimate.estimate_id} has K but no V/killing pressure.",
                    "Record killed route events to estimate V.",
                )
            )
        if estimate.state_estimates and not _has_advisory_disclaimer(estimate.metadata):
            findings.append(
                RoadmapAlignmentFinding(
                    "warning",
                    "SPECTRAL_PRIORITIES_WITHOUT_ADVISORY_DISCLAIMER",
                    f"Spectral H-tilt estimate {estimate.estimate_id} has route priorities without advisory disclaimer.",
                    "Mark route priorities advisory and not truth-authoritative.",
                )
            )
        if not estimate.metadata.get("telemetry_based") or not estimate.metadata.get("not_truth_authority"):
            findings.append(
                RoadmapAlignmentFinding(
                    "warning",
                    "SPECTRAL_HTILT_METADATA_OMITS_BOUNDARY",
                    f"Spectral H-tilt estimate {estimate.estimate_id} omits telemetry/not-truth metadata.",
                    "Record telemetry_based and not_truth_authority metadata.",
                )
            )
    for claim in claims:
        if claim.world == DomainFormalWorldKind.NATURAL_LANGUAGE and not _has_advisory_disclaimer(claim.metadata):
            findings.append(
                RoadmapAlignmentFinding(
                    "warning",
                    "NATURAL_LANGUAGE_CLAIM_WITHOUT_ADVISORY_METADATA",
                    f"Natural-language claim {claim.claim_id} lacks advisory metadata.",
                    "Mark natural-language claims advisory/residual.",
                )
            )
        if claim.world == DomainFormalWorldKind.UNKNOWN and not (
            claim.metadata.get("residual_explanation") or claim.metadata.get("unsupported_or_advisory")
        ):
            findings.append(
                RoadmapAlignmentFinding(
                    "warning",
                    "UNKNOWN_WORLD_WITHOUT_RESIDUAL_EXPLANATION",
                    f"Domain claim {claim.claim_id} has UNKNOWN world without residual explanation.",
                    "Record why the claim remains unsupported/residual.",
                )
            )
    for registry in registries:
        if not registry.by_kind(DomainFormalWorldKind.MAGMA_EQUATIONAL):
            findings.append(
                RoadmapAlignmentFinding(
                    "warning",
                    "REGISTRY_MISSING_MAGMA_EQUATIONAL_WORLD",
                    f"Formal world registry {registry.registry_id} has no MAGMA_EQUATIONAL world.",
                    "Include the current SAIR/ETP nursery world.",
                )
            )
        for world in registry.worlds.values():
            if world.supports_proofs and not world.verifier_kinds:
                findings.append(
                    RoadmapAlignmentFinding(
                        "warning",
                        "PROOF_WORLD_WITHOUT_VERIFIER_KIND",
                        f"Formal world {world.world_id} supports proofs but has no verifier kind.",
                        "Record the verifier/importer kind or mark support future/advisory.",
                    )
                )
    for result in parse_results:
        if result.errors and result.status == ClaimIRStatus.ROUTABLE:
            findings.append(
                RoadmapAlignmentFinding(
                    "warning",
                    "PARSER_ERRORS_BUT_ROUTABLE",
                    f"Claim parse result {result.result_id} has parser errors but is routable.",
                    "Keep errored parse results residual until repaired.",
                )
            )
    for trace in lean_traces:
        if trace.environment.lean_available is False and trace.summary.get("check_requested"):
            findings.append(
                RoadmapAlignmentFinding(
                    "warning",
                    "LEAN_UNAVAILABLE_CHECK_REQUESTED",
                    f"Lean adapter trace {trace.trace_id} requested checks but Lean is unavailable.",
                    "Record LEAN_NOT_AVAILABLE as advisory/residual.",
                )
            )
        for lean_file in trace.files:
            if not lean_file.theorem_names:
                findings.append(
                    RoadmapAlignmentFinding(
                        "warning",
                        "LEAN_FILE_WITHOUT_THEOREM_NAMES",
                        f"Lean file {lean_file.lean_file_id} has no theorem/lemma names.",
                        "Record theorem names when available; examples may remain unnamed.",
                    )
                )
        for result in trace.results:
            if result.stderr_excerpt and not result.metadata.get("failure_reason"):
                findings.append(
                    RoadmapAlignmentFinding(
                        "warning",
                        "LEAN_CHECK_STDERR_WITHOUT_FAILURE_REASON",
                        f"Lean check result {result.result_id} has stderr without failure reason metadata.",
                        "Record a failure reason for failed Lean checks.",
                    )
                )
        if len(trace.files) >= 10 and not trace.results:
            findings.append(
                RoadmapAlignmentFinding(
                    "warning",
                    "LEAN_MANY_FILES_NO_CHECKS",
                    f"Lean adapter trace {trace.trace_id} has many files but no checks/imports.",
                    "Record CHECK_NOT_RUN results or request checks/imports.",
                )
            )
        if trace.environment.project_root and trace.environment.lake_available is False:
            findings.append(
                RoadmapAlignmentFinding(
                    "warning",
                    "LEAN_PROJECT_ROOT_WITHOUT_LAKE",
                    f"Lean adapter trace {trace.trace_id} has project_root but Lake is unavailable.",
                    "Treat project-level Lean checks as advisory until Lake/project support is available.",
                )
            )
    for trace in continuation_traces:
        if (trace.input.domain_claims or trace.input.raw_texts or trace.input.episode_inputs) and not trace.outputs:
            findings.append(
                RoadmapAlignmentFinding(
                    "warning",
                    "CONTINUATION_INPUTS_WITHOUT_OUTPUTS",
                    f"Continuation action trace {trace.trace_id} has inputs but no applicable outputs.",
                    "Record residual/not-applicable outputs for replay.",
                )
            )
        if any(not output.metadata.get("advisory_only") and not output.is_terminal() for output in trace.outputs):
            findings.append(
                RoadmapAlignmentFinding(
                    "warning",
                    "CONTINUATION_OUTPUT_WITHOUT_ADVISORY_METADATA",
                    f"Continuation action trace {trace.trace_id} has outputs without advisory metadata.",
                    "Mark generated continuations advisory.",
                )
            )
        if sum(1 for output in trace.outputs if output.domain_claim) >= 10 and not any(
            output.kind in {ContinuationOutputKind.TASK, ContinuationOutputKind.EPISODE_INPUT, ContinuationOutputKind.PROOF_ARTIFACT}
            for output in trace.outputs
        ):
            findings.append(
                RoadmapAlignmentFinding(
                    "warning",
                    "MANY_CONTINUATION_CLAIMS_NO_ROUTING",
                    f"Continuation action trace {trace.trace_id} generated many claims without routing/task outputs.",
                    "Emit episode/proof/projection tasks for actionable continuations.",
                )
            )
        if any(output.metadata.get("warning") or output.metadata.get("unsafe") for output in trace.outputs):
            findings.append(
                RoadmapAlignmentFinding(
                    "warning",
                    "CONTINUATION_UNSAFE_TRANSFORMATION_METADATA",
                    f"Continuation action trace {trace.trace_id} includes unsafe/warning transformation metadata.",
                    "Keep unsafe transformations residual until reviewed.",
                )
            )
    for trace in digestion_traces:
        if trace.certificate_id and not trace.dependency_maps:
            findings.append(
                RoadmapAlignmentFinding(
                    "warning",
                    "DIGESTION_CERTIFICATE_WITHOUT_DEPENDENCY_MAP",
                    f"Proof digestion trace {trace.trace_id} references a certificate without dependency map.",
                    "Map proof dependencies before lawbook assimilation.",
                )
            )
        for note in trace.exposition_notes:
            if not note.limitations:
                findings.append(
                    RoadmapAlignmentFinding(
                        "warning",
                        "EXPOSITION_NOTE_WITHOUT_LIMITATIONS",
                        f"Exposition note {note.note_id} has no limitations.",
                        "Record that exposition is heuristic/advisory.",
                    )
                )
        if sum(1 for step in trace.step_digests if step.classification == "unknown") >= 10 and not trace.summary.get("residual_note"):
            findings.append(
                RoadmapAlignmentFinding(
                    "warning",
                    "MANY_UNKNOWN_DIGESTION_STEPS",
                    f"Proof digestion trace {trace.trace_id} has many unknown steps without residual note.",
                    "Record residual digestion questions for opaque proof segments.",
                )
            )
        for schema in trace.reusable_schemas:
            if not schema.conditions and not schema.metadata.get("limitations"):
                findings.append(
                    RoadmapAlignmentFinding(
                        "warning",
                        "REUSABLE_SCHEMA_WITHOUT_CONDITIONS",
                        f"Reusable schema {schema.schema_id} lacks conditions/limitations.",
                        "Record application conditions and advisory limitations.",
                    )
                )
        if trace.summary.get("assimilation_candidate_ready") is False and not trace.summary.get("not_ready_reason"):
            findings.append(
                RoadmapAlignmentFinding(
                    "warning",
                    "ASSIMILATION_CANDIDATE_NOT_READY_NO_REASON",
                    f"Proof digestion trace {trace.trace_id} has a not-ready assimilation candidate without reason.",
                    "Record why the candidate is not ready.",
                )
            )
    failed_feedback_ids = {item.feedback_id for item in feedback_items if item.status == VerifierFeedbackStatus.FAILED}
    planned_feedback_ids = {plan.feedback_id for trace in repair_traces for plan in trace.repair_plans}
    for feedback in feedback_items:
        if feedback.status == VerifierFeedbackStatus.FAILED and feedback.flaw_severity == FlawSeverity.UNKNOWN:
            findings.append(
                RoadmapAlignmentFinding(
                    "warning",
                    "FAILED_FEEDBACK_UNKNOWN_SEVERITY",
                    f"Failed verifier feedback {feedback.feedback_id} has UNKNOWN flaw severity.",
                    "Classify the flaw or mark it hold-in-Chora/residual.",
                )
            )
        if feedback.feedback_id in failed_feedback_ids and feedback.feedback_id not in planned_feedback_ids:
            findings.append(
                RoadmapAlignmentFinding(
                    "warning",
                    "FAILED_FEEDBACK_WITHOUT_REPAIR_PLAN",
                    f"Failed verifier feedback {feedback.feedback_id} has no repair, obstruction, or residual plan.",
                    "Emit a repair plan or residualize the failed artifact.",
                )
            )
    unknown_feedback = [item for item in feedback_items if item.flaw_severity == FlawSeverity.UNKNOWN]
    if len(unknown_feedback) >= 3:
        hold_or_residual = any(
            plan.action_kind in {RepairActionKind.HOLD_IN_CHORA, RepairActionKind.MARK_RESIDUAL}
            for trace in repair_traces
            for plan in trace.repair_plans
        )
        if not hold_or_residual:
            findings.append(
                RoadmapAlignmentFinding(
                    "warning",
                    "MANY_UNKNOWN_FEEDBACK_NO_HOLD_OR_RESIDUAL",
                    "Many UNKNOWN feedback items have no hold-in-Chora or residual plan.",
                    "Hold uncertain failures in Chora or mark residual.",
                )
            )
    for trace in repair_traces:
        if not _has_advisory_disclaimer(trace.summary) and not trace.advisory:
            findings.append(
                RoadmapAlignmentFinding(
                    "warning",
                    "REPAIR_TRACE_WITHOUT_ADVISORY_METADATA",
                    f"Repair loop trace {trace.trace_id} lacks advisory metadata.",
                    "Mark repair loops advisory.",
                )
            )
        severities = {item.feedback_id: item.flaw_severity for item in trace.feedback_items}
        for plan in trace.repair_plans:
            severity = severities.get(plan.feedback_id)
            if severity == FlawSeverity.CRITICAL_INVALIDATION and plan.action_kind == RepairActionKind.LOCAL_REVISE:
                findings.append(
                    RoadmapAlignmentFinding(
                        "warning",
                        "CRITICAL_INVALIDATION_LOCAL_REVISE",
                        f"Repair plan {plan.repair_plan_id} locally revises critical invalidation.",
                        "Prefer obstruction/residual for critical invalidation.",
                    )
                )
            if severity == FlawSeverity.MINOR_REPAIRABLE and plan.action_kind == RepairActionKind.REGENERATE_ARTIFACT:
                findings.append(
                    RoadmapAlignmentFinding(
                        "warning",
                        "MINOR_REPAIR_REGENERATE_ONLY",
                        f"Repair plan {plan.repair_plan_id} regenerates artifact for minor repairable flaw.",
                        "Prefer local revise for minor syntax/import/name flaws.",
                    )
                )


def _add_positive_findings(
    traces: Sequence[AlchemicalTrace],
    experiences: Sequence[AgentExperience],
    projection_traces: Sequence[ProjectionTrace],
    root_constructor_traces: Sequence[RootConstructorTrace],
    proof_traces: Sequence[ProofVerificationTrace],
    episode_traces: Sequence[VerificationEpisodeTrace],
    telemetry_ledgers: Sequence[RouteTelemetryLedger],
    spectral_estimates: Sequence[SpectralHTiltEstimate],
    claims: Sequence[DomainClaim],
    parse_results: Sequence[ClaimParseResult],
    registries: Sequence[FormalWorldRegistry],
    lean_traces: Sequence[LeanAdapterTrace],
    continuation_traces: Sequence[ContinuationActionTrace],
    digestion_traces: Sequence[ProofDigestionTrace],
    feedback_items: Sequence[VerifierFeedback],
    repair_traces: Sequence[RepairLoopTrace],
    curricula: Sequence[ContinuationCurriculum],
    value_reports: Sequence[DiscoveryValueReport],
    value_scores: Sequence[DiscoveryValueScore],
    lawbook_entries: Sequence[LawbookEntry],
    lawbook_stores: Sequence[AcceptedLawbookStore],
    lawbook_reviews: Sequence[LawbookReview],
    lawbook_queries: Sequence[LawbookQuery],
    lawbook_answers: Sequence[LawbookQueryAnswer],
    lawbook_reports: Sequence[LawbookQueryReport],
    summary: Mapping[str, Any],
    findings: list[RoadmapAlignmentFinding],
) -> None:
    if traces or experiences or projection_traces or root_constructor_traces or proof_traces or episode_traces or telemetry_ledgers or spectral_estimates or claims or parse_results or registries or lean_traces or continuation_traces or digestion_traces or feedback_items or repair_traces or curricula or value_reports or value_scores or lawbook_entries or lawbook_stores or lawbook_reviews or lawbook_queries or lawbook_answers or lawbook_reports:
        if not any(finding.severity == "critical" for finding in findings):
            findings.append(
                RoadmapAlignmentFinding(
                    "info",
                    "TERMINAL_CONTRACT_RESPECTED",
                    "No advisory record crossed into terminal truth without verifier promotion.",
                )
            )
    for curriculum in curricula:
        if curriculum.stages:
            findings.append(
                RoadmapAlignmentFinding(
                    "info",
                    "CURRICULUM_ADVISORY_BOUNDARY_PRESERVED",
                    f"Continuation curriculum {curriculum.curriculum_id} preserves staged advisory work.",
                    None,
                )
            )
        if any(stage.kind == CurriculumStageKind.WARMUP_CLAIM for stage in curriculum.stages):
            findings.append(RoadmapAlignmentFinding("info", "CURRICULUM_EMITS_WARMUPS", f"Continuation curriculum {curriculum.curriculum_id} emits warm-ups.", None))
        if any(stage.kind == CurriculumStageKind.FINITE_EXAMPLE for stage in curriculum.stages):
            findings.append(RoadmapAlignmentFinding("info", "CURRICULUM_EMITS_FINITE_EXAMPLES", f"Continuation curriculum {curriculum.curriculum_id} emits finite examples.", None))
        if any(stage.kind == CurriculumStageKind.PROOF_TASK for stage in curriculum.stages) and any(stage.kind == CurriculumStageKind.COUNTERMODEL_TASK for stage in curriculum.stages):
            findings.append(RoadmapAlignmentFinding("info", "CURRICULUM_EMITS_BOTH_TASK_SIDES", f"Continuation curriculum {curriculum.curriculum_id} emits proof and countermodel tasks.", None))
        if curriculum.episode_inputs:
            findings.append(RoadmapAlignmentFinding("info", "CURRICULUM_EMITS_EPISODE_INPUTS", f"Continuation curriculum {curriculum.curriculum_id} emits replayable episode inputs.", None))
    for report in value_reports:
        findings.append(RoadmapAlignmentFinding("info", "DISCOVERY_VALUE_ADVISORY_BOUNDARY_PRESERVED", f"Discovery value report {report.report_id} preserves advisory ranking.", None))
        if any(score.decision in {DiscoveryValueDecision.RUN_NOW, DiscoveryValueDecision.QUEUE_SOON} for score in report.scores):
            findings.append(RoadmapAlignmentFinding("info", "DISCOVERY_VALUE_QUEUES_WORK", f"Discovery value report {report.report_id} queues high-value work rather than marking it true.", None))
        if any(score.decision == DiscoveryValueDecision.PROJECT for score in report.scores):
            findings.append(RoadmapAlignmentFinding("info", "DISCOVERY_VALUE_PROJECTS", f"Discovery value report {report.report_id} routes projection candidate to PROJECT.", None))
        if any(score.decision == DiscoveryValueDecision.NEEDS_REPAIR for score in report.scores):
            findings.append(RoadmapAlignmentFinding("info", "DISCOVERY_VALUE_NEEDS_REPAIR", f"Discovery value report {report.report_id} routes repairable feedback to NEEDS_REPAIR.", None))
        if any(score.decision in {DiscoveryValueDecision.NEEDS_VERIFIER, DiscoveryValueDecision.NEEDS_DIGESTION} for score in report.scores):
            findings.append(RoadmapAlignmentFinding("info", "DISCOVERY_VALUE_PRESERVES_PROOF_BOUNDARY", f"Discovery value report {report.report_id} routes proof-like objects to verifier/digestion.", None))
    for entry in list(lawbook_entries) + [entry for store in lawbook_stores for entry in store.entries]:
        if entry.is_accepted() and entry.kind.value == "VERIFIED_PROOF_ENTRY" and entry.has_valid_truth_boundary():
            findings.append(RoadmapAlignmentFinding("info", "LAWBOOK_ACCEPTED_PROOF_VALID_BOUNDARY", f"Lawbook entry {entry.entry_id} accepts verified proof with valid boundary.", None))
        if entry.is_accepted() and entry.kind.value == "FINITE_COUNTERMODEL_ENTRY" and entry.has_valid_truth_boundary():
            findings.append(RoadmapAlignmentFinding("info", "LAWBOOK_ACCEPTED_COUNTERMODEL_VALID_BOUNDARY", f"Lawbook entry {entry.entry_id} accepts finite countermodel with valid boundary.", None))
        if entry.kind.value == "DIGESTED_PROOF_ENTRY" and entry.certificate_id:
            findings.append(RoadmapAlignmentFinding("info", "LAWBOOK_DIGESTION_LINKED", f"Lawbook entry {entry.entry_id} links digestion to existing certificate.", None))
        if entry.kind.value == "PROJECTION_RULE_ENTRY":
            findings.append(RoadmapAlignmentFinding("info", "LAWBOOK_PROJECTION_ONLY", f"Lawbook entry {entry.entry_id} records projection only.", None))
        if entry.is_candidate():
            findings.append(RoadmapAlignmentFinding("info", "LAWBOOK_CANDIDATE_NON_TERMINAL", f"Lawbook entry {entry.entry_id} remains candidate.", None))
    for store in lawbook_stores:
        findings.append(RoadmapAlignmentFinding("info", "LAWBOOK_PUBLIC_MEMORY_BOUNDARY", f"Lawbook store {store.store_id} preserves explicit acceptance boundary.", None))
    for answer in list(lawbook_answers) + [answer for report in lawbook_reports for answer in report.answers]:
        if answer.trust_level.value == "VERIFIED_TRUTH" and answer.is_terminal_answer():
            findings.append(RoadmapAlignmentFinding("info", "LAWBOOK_QUERY_VERIFIED_TRUST", f"Lawbook answer {answer.answer_id} returns verified trust with boundary.", None))
        if answer.trust_level.value == "FINITE_REFUTATION" and answer.is_terminal_answer():
            findings.append(RoadmapAlignmentFinding("info", "LAWBOOK_QUERY_FINITE_REFUTATION", f"Lawbook answer {answer.answer_id} returns finite refutation with boundary.", None))
        if answer.status == LawbookQueryStatus.FOUND_CANDIDATE_ONLY and not answer.is_known_skip():
            findings.append(RoadmapAlignmentFinding("info", "LAWBOOK_QUERY_CANDIDATE_REFUSES_SKIP", f"Candidate-only answer {answer.answer_id} refuses skip.", None))
        if answer.status == LawbookQueryStatus.FOUND_PROJECTION_ONLY:
            findings.append(RoadmapAlignmentFinding("info", "LAWBOOK_QUERY_PROJECTION_ADVISORY", f"Projection-only answer {answer.answer_id} remains advisory.", None))
        if answer.status == LawbookQueryStatus.AMBIGUOUS and answer.known_skip_decision == KnownSkipDecision.DO_NOT_SKIP_AMBIGUOUS:
            findings.append(RoadmapAlignmentFinding("info", "LAWBOOK_QUERY_AMBIGUOUS_REFUSES_SKIP", f"Ambiguous answer {answer.answer_id} refuses skip.", None))
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
    if any(ep.status == VerificationEpisodeStatus.TERMINAL_VERIFIED_PROOF for ep in episode_traces):
        findings.append(RoadmapAlignmentFinding("info", "EPISODE_TERMINAL_VERIFIED_PROOF", "Episode terminal verified proof recorded."))
    if any(ep.status == VerificationEpisodeStatus.TERMINAL_FINITE_COUNTERMODEL for ep in episode_traces):
        findings.append(RoadmapAlignmentFinding("info", "EPISODE_TERMINAL_FINITE_COUNTERMODEL", "Episode terminal finite countermodel recorded."))
    if any(ep.is_advisory() for ep in episode_traces):
        findings.append(RoadmapAlignmentFinding("info", "EPISODE_ADVISORY_BOUNDARY_PRESERVED", "Episode preserved advisory boundary."))
    if any(ep.agent_experiences for ep in episode_traces):
        findings.append(RoadmapAlignmentFinding("info", "EPISODE_AGENT_EXPERIENCES_RECORDED", "Episode produced agent experiences."))
    if any(float(ep.summary.get("projection_gain_total", 0.0) or 0.0) for ep in episode_traces):
        findings.append(RoadmapAlignmentFinding("info", "EPISODE_PROJECTION_GAIN", "Episode produced projection gain."))
    if any(ep.root_constructor_trace and ep.root_constructor_trace.plans for ep in episode_traces):
        findings.append(RoadmapAlignmentFinding("info", "EPISODE_ROOT_PLAN", "Episode produced root constructor plan."))
    if any(ep.proof_verification_trace and ep.proof_verification_trace.artifacts for ep in episode_traces):
        findings.append(RoadmapAlignmentFinding("info", "EPISODE_PROOF_LIFECYCLE", "Episode produced proof artifact lifecycle."))
    if any(ledger.events for ledger in telemetry_ledgers):
        findings.append(RoadmapAlignmentFinding("info", "ROUTE_TELEMETRY_RECORDED", "Route telemetry recorded."))
    if any(ledger.transition_counts() for ledger in telemetry_ledgers):
        findings.append(RoadmapAlignmentFinding("info", "TELEMETRY_TRANSITIONS_RECORDED", "Transition counts recorded."))
    if any(ledger.killing_counts() for ledger in telemetry_ledgers):
        findings.append(RoadmapAlignmentFinding("info", "TELEMETRY_KILLING_RECORDED", "Killing counts recorded."))
    if summary.get("route_scores") or any("route_scores" in ledger.summary for ledger in telemetry_ledgers):
        findings.append(RoadmapAlignmentFinding("info", "ROUTE_SCORE_SUMMARY_RECORDED", "Advisory route score summary recorded."))
    if any("certificate_yield_per_cost" in ledger.summary for ledger in telemetry_ledgers):
        findings.append(RoadmapAlignmentFinding("info", "TERMINAL_YIELD_PER_COST_RECORDED", "Terminal yield per cost recorded."))
    if any(estimate.transition_L for estimate in spectral_estimates):
        findings.append(RoadmapAlignmentFinding("info", "SPECTRAL_L_ESTIMATED", "Telemetry-derived L estimated."))
    if any(estimate.killing_V for estimate in spectral_estimates):
        findings.append(RoadmapAlignmentFinding("info", "SPECTRAL_V_ESTIMATED", "Telemetry-derived V estimated."))
    if any(estimate.generator_K for estimate in spectral_estimates):
        findings.append(RoadmapAlignmentFinding("info", "SPECTRAL_K_ESTIMATED", "Telemetry-derived K=L-V estimated."))
    if any(
        any(state.support_q or state.survival_h for state in estimate.state_estimates)
        for estimate in spectral_estimates
    ):
        findings.append(RoadmapAlignmentFinding("info", "SPECTRAL_H_Q_ESTIMATED", "h/q survival/support estimates recorded."))
    if any(any(state.survivor_pi for state in estimate.state_estimates) for estimate in spectral_estimates):
        findings.append(RoadmapAlignmentFinding("info", "SPECTRAL_PI_STAR_ESTIMATED", "pi* survivor distribution estimated."))
    if any(any(state.tilted_mu_beta for state in estimate.state_estimates) for estimate in spectral_estimates):
        findings.append(RoadmapAlignmentFinding("info", "SPECTRAL_MU_BETA_ESTIMATED", "mu_beta H-tilt bridge estimated."))
    if any(estimate.state_estimates for estimate in spectral_estimates):
        findings.append(RoadmapAlignmentFinding("info", "SPECTRAL_ROUTE_PRIORITIES_AVAILABLE", "Advisory route priorities available."))
    if parse_results:
        findings.append(RoadmapAlignmentFinding("info", "DOMAIN_CLAIM_PARSED", "Domain claim parsed."))
    if any(result.status == ClaimIRStatus.NORMALIZED for result in parse_results) or any(claim.normalized for claim in claims):
        findings.append(RoadmapAlignmentFinding("info", "DOMAIN_CLAIM_NORMALIZED", "Domain claim normalized."))
    if registries:
        findings.append(RoadmapAlignmentFinding("info", "FORMAL_WORLD_REGISTRY_PRESENT", "Formal world registry present."))
    if any(
        claim.world == DomainFormalWorldKind.MAGMA_EQUATIONAL and claim.source and claim.target
        for claim in claims
    ):
        findings.append(RoadmapAlignmentFinding("info", "MAGMA_CLAIM_ROUTABLE_TO_EPISODE", "Magma claim routable to episode input."))
    if any(claim.world == DomainFormalWorldKind.LEAN for claim in claims):
        findings.append(RoadmapAlignmentFinding("info", "LEAN_CLAIM_ROUTABLE_TO_PROOF_ARTIFACT", "Lean-looking claim routable to proof artifact."))
    if any(
        claim.world in {DomainFormalWorldKind.NATURAL_LANGUAGE, DomainFormalWorldKind.UNKNOWN}
        for claim in claims
    ):
        findings.append(RoadmapAlignmentFinding("info", "UNSUPPORTED_CLAIM_SAFELY_ADVISORY", "Unsupported claim safely residual/advisory."))
    if any(trace.environment.lean_available for trace in lean_traces):
        findings.append(RoadmapAlignmentFinding("info", "LEAN_AVAILABLE", "Lean available."))
    if any(trace.files for trace in lean_traces):
        findings.append(RoadmapAlignmentFinding("info", "LEAN_FILE_RECORDED", "Lean file written/recorded."))
    if any(result.status == LeanArtifactStatus.CHECK_PASSED for trace in lean_traces for result in trace.results):
        findings.append(RoadmapAlignmentFinding("info", "LEAN_CHECK_PASSED", "Lean check passed through proof boundary."))
    if any(result.status == LeanArtifactStatus.CHECK_FAILED for trace in lean_traces for result in trace.results):
        findings.append(RoadmapAlignmentFinding("info", "LEAN_CHECK_FAILED_SAFELY", "Lean check failed safely as advisory/residual."))
    if any(result.status == LeanArtifactStatus.LEAN_NOT_AVAILABLE for trace in lean_traces for result in trace.results):
        findings.append(RoadmapAlignmentFinding("info", "LEAN_UNAVAILABLE_HANDLED", "Lean unavailable handled safely."))
    if any(result.status == LeanArtifactStatus.IMPORTED_VERIFIED for trace in lean_traces for result in trace.results):
        findings.append(RoadmapAlignmentFinding("info", "LEAN_IMPORTED_VERIFIED_RECORDED", "Imported verified Lean artifact recorded."))
    if any(output.episode_input for trace in continuation_traces for output in trace.outputs):
        findings.append(RoadmapAlignmentFinding("info", "CONTINUATION_EPISODE_INPUTS_PRODUCED", "Continuation actions produced episode inputs."))
    if any(output.proof_artifact for trace in continuation_traces for output in trace.outputs):
        findings.append(RoadmapAlignmentFinding("info", "CONTINUATION_PROOF_ARTIFACTS_PRODUCED", "Continuation actions produced proof artifacts."))
    if any(output.projection_candidate for trace in continuation_traces for output in trace.outputs):
        findings.append(RoadmapAlignmentFinding("info", "CONTINUATION_PROJECTION_CANDIDATES_PRODUCED", "Continuation actions produced projection candidates."))
    if any(output.task_payload.get("task_kind") == "countermodel_search" for trace in continuation_traces for output in trace.outputs):
        findings.append(RoadmapAlignmentFinding("info", "CONTINUATION_COUNTERMODEL_TASKS_PRODUCED", "Continuation actions produced countermodel tasks."))
    if continuation_traces and not any(output.is_terminal() for trace in continuation_traces for output in trace.outputs):
        findings.append(RoadmapAlignmentFinding("info", "CONTINUATION_ADVISORY_BOUNDARY_PRESERVED", "Continuation actions preserved advisory boundary."))
    if any(trace.dependency_maps for trace in digestion_traces):
        findings.append(RoadmapAlignmentFinding("info", "PROOF_DEPENDENCY_MAP_EXTRACTED", "Proof dependency map extracted."))
    if any(trace.key_ideas for trace in digestion_traces):
        findings.append(RoadmapAlignmentFinding("info", "KEY_IDEA_CANDIDATE_EXTRACTED", "Key idea candidate extracted."))
    if any(trace.reusable_schemas for trace in digestion_traces):
        findings.append(RoadmapAlignmentFinding("info", "REUSABLE_SCHEMA_CANDIDATE_EXTRACTED", "Reusable schema candidate extracted."))
    if any(trace.exposition_notes for trace in digestion_traces):
        findings.append(RoadmapAlignmentFinding("info", "EXPOSITION_NOTE_CREATED", "Exposition note created."))
    if any(trace.status.value == "ASSIMILATION_CANDIDATE" and trace.certificate_id for trace in digestion_traces):
        findings.append(RoadmapAlignmentFinding("info", "LAWBOOK_ASSIMILATION_CANDIDATE_READY", "Lawbook assimilation candidate ready."))
    if any(trace.projection_candidates for trace in digestion_traces):
        findings.append(RoadmapAlignmentFinding("info", "PROOF_DIGESTION_PROJECTION_HINTS", "Proof digestion projection hints produced."))
    if any(trace.is_truth_terminal() for trace in digestion_traces):
        findings.append(RoadmapAlignmentFinding("info", "VERIFIED_PROOF_INHERITED_IN_DIGESTION", "Verified proof boundary inherited safely into digestion trace."))
    if any(plan.action_kind == RepairActionKind.LOCAL_REVISE for trace in repair_traces for plan in trace.repair_plans):
        findings.append(RoadmapAlignmentFinding("info", "MINOR_FLAW_LOCAL_REVISE", "Minor flaw converted to local revise."))
    if any(plan.action_kind in {RepairActionKind.REROUTE, RepairActionKind.EMIT_PROOF_TASK} for trace in repair_traces for plan in trace.repair_plans):
        findings.append(RoadmapAlignmentFinding("info", "STRUCTURAL_GAP_REROUTE_OR_PROOF_TASK", "Structural gap converted to reroute/proof task."))
    if any(plan.action_kind in {RepairActionKind.EMIT_OBSTRUCTION_TASK, RepairActionKind.MARK_RESIDUAL} for trace in repair_traces for plan in trace.repair_plans):
        findings.append(RoadmapAlignmentFinding("info", "CRITICAL_INVALIDATION_OBSTRUCTION_OR_RESIDUAL", "Critical invalidation converted to obstruction/residual pressure."))
    if any(plan.action_kind in {RepairActionKind.HOLD_IN_CHORA, RepairActionKind.MARK_RESIDUAL} for trace in repair_traces for plan in trace.repair_plans):
        findings.append(RoadmapAlignmentFinding("info", "UNAVAILABLE_VERIFIER_HELD_OR_RESIDUAL", "Unavailable/not-run verifier converted to hold-in-Chora/residual."))
    if repair_traces and not any(trace.is_terminal() for trace in repair_traces):
        findings.append(RoadmapAlignmentFinding("info", "REPAIR_LOOP_ADVISORY_BOUNDARY_PRESERVED", "Repair loop preserved advisory boundary."))


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
