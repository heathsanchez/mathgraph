"""Replayable proof-system project, artifact, and boundary contracts."""
from __future__ import annotations
import json,re
from collections import Counter
from dataclasses import dataclass,field
from datetime import datetime,timezone
from enum import Enum
from pathlib import Path
from typing import Any,Mapping,Sequence
from mathgraph.agent_biography import AgentExperience,AgentExperienceOutcome
from mathgraph.alchemy import AlchemicalPhase,AlchemicalStatus,AlchemicalTrace,make_alchemical_trace_id
from mathgraph.certificates import TerminalForm
from mathgraph.continuation_actions import ContinuationActionOutput,ContinuationActionStatus,ContinuationOutputKind,make_continuation_output_id
from mathgraph.continuation_curriculum import ContinuationCurriculum,CurriculumBuildStrategy,CurriculumStage,CurriculumStageKind,CurriculumStageStatus,CurriculumTraceStatus,make_curriculum_id,make_curriculum_stage_id
from mathgraph.discovery_value import DiscoveryValueObjectKind,DiscoveryValueScore,DiscoveryValueSignal,DiscoveryValueSignalKind
from mathgraph.hashing import content_id
from mathgraph.habit_rules import HabitObservation,HabitObservationKind,HabitOutcome
from mathgraph.lawbook import LawbookEntry,LawbookEntryKind,LawbookEntryStatus,make_lawbook_entry_id
from mathgraph.process_memory import ProcessContextItem,ProcessContextKind,ProcessContextRole,ProcessEpisodeRecord,ProcessEpisodeStatus,make_process_episode_id
from mathgraph.reason_compression import ReasonObservation,ReasonObservationKind,extract_atoms_from_mapping,make_reason_observation_id
from mathgraph.role_objects import RoleSignature,RoleSourceKind,RoleObjectKind,make_role_signature_id
from mathgraph.structural_analogy import AnalogySource,AnalogySourceKind,analogy_source_from_mapping
from mathgraph.structure_registry import StructureDescriptor,StructureObjectKind,TypedProjectionCandidate,TypedProjectionStatus,ProjectionCompatibility,structure_descriptor_from_mapping,make_typed_projection_candidate_id
from mathgraph.verifier_feedback import FlawSeverity,RepairLoopTrace,VerifierFeedback,VerifierFeedbackStatus,make_verifier_feedback_id
def _enum(n,v): return Enum(n,{x:x for x in v.split()},type=str)
ProofSystemKind=_enum("ProofSystemKind","LEAN ISABELLE COQ GENERIC_PROOF_ASSISTANT PROOF_TEXT_IMPORT UNKNOWN")
ProofArtifactKind=_enum("ProofArtifactKind","THEOREM_FILE MODULE_FILE IMPORT_FILE PROOF_SKETCH PROOF_TEXT COUNTERMODEL_FILE CERTIFICATE_FILE PROJECT_CONFIG BUILD_FILE UNKNOWN")
ProofArtifactStatus=_enum("ProofArtifactStatus","DISCOVERED REGISTERED MISSING PARSED NORMALIZED READY_FOR_CHECK CHECK_REQUESTED CHECK_PASSED CHECK_FAILED CHECK_SKIPPED PLACEHOLDER_DETECTED TRUSTED_IMPORTED BOUNDARY_EVIDENCE_READY UNKNOWN")
ImportEdgeKind=_enum("ImportEdgeKind","IMPORTS DEPENDS_ON REFERENCES GENERATED_FROM DIGESTED_FROM REPAIRS REPLACES UNKNOWN")
CheckCommandKind=_enum("CheckCommandKind","LEAN_CHECK LAKE_ENV_LEAN ISABELLE_BUILD COQ_CHECK GENERIC_CHECK IMPORT_ONLY NO_EXECUTION UNKNOWN")
CheckRequestStatus=_enum("CheckRequestStatus","CREATED READY BLOCKED_MISSING_TOOL BLOCKED_UNSAFE_COMMAND BLOCKED_MISSING_ARTIFACT BLOCKED_PLACEHOLDER RUN_ALLOWED RUN_NOT_ALLOWED UNKNOWN")
CheckResultStatus=_enum("CheckResultStatus","NOT_RUN PASSED FAILED TIMEOUT TOOL_MISSING UNSAFE_COMMAND PARSE_ERROR PLACEHOLDER_FOUND INCONCLUSIVE UNKNOWN")
ProofBoundaryKind=_enum("ProofBoundaryKind","VERIFIER_CHECK TRUSTED_IMPORT CHAIN_AUDIT FINITE_VALIDATION NONE UNKNOWN")
TrustedImportStatus=_enum("TrustedImportStatus","REQUESTED READY_FOR_REVIEW ACCEPTED_WITH_BOUNDARY REJECTED MISSING_PROVENANCE MISSING_ARTIFACT UNSUPPORTED UNKNOWN")
ProofSystemTaskKind=_enum("ProofSystemTaskKind","CREATE_THEOREM_FILE CHECK_THEOREM_FILE REPAIR_PROOF REMOVE_PLACEHOLDER FORMALIZE_TEXT DIGEST_PROOF BUILD_IMPORT_GRAPH TRUSTED_IMPORT_REVIEW CHAIN_AUDIT LAWBOOK_CANDIDATE_REVIEW HUMAN_REVIEW UNKNOWN")
ProofSystemIntegrationReportStatus=_enum("ProofSystemIntegrationReportStatus","EMPTY SPECS_REPORTED PROJECTS_REPORTED ARTIFACTS_REPORTED IMPORT_GRAPH_BUILT CHECK_REQUESTS_CREATED CHECK_RESULTS_RECORDED TRUSTED_IMPORTS_RECORDED BOUNDARY_EVIDENCE_RECORDED TASKS_EMITTED HAS_WARNINGS HAS_CRITICALS ADVISORY_ONLY")
@dataclass
class ProofSystemSpec:
 proof_system_id:str; kind:ProofSystemKind; name:str; file_extensions:tuple[str,...]=(); config_files:tuple[str,...]=(); default_check_command_kind:CheckCommandKind=CheckCommandKind.NO_EXECUTION; allowed_command_tokens:tuple[str,...]=(); placeholder_tokens:tuple[str,...]=(); success_patterns:tuple[str,...]=(); failure_patterns:tuple[str,...]=(); requires_external_tool:bool=True; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def recognizes_path(self,p): return any(str(p).endswith(x) for x in self.file_extensions)
 def detects_placeholder(self,t): return any(x.lower() in t.lower() for x in self.placeholder_tokens)
 def to_dict(self): return {**self.__dict__,"kind":self.kind.value,"file_extensions":list(self.file_extensions),"config_files":list(self.config_files),"default_check_command_kind":self.default_check_command_kind.value,"allowed_command_tokens":list(self.allowed_command_tokens),"placeholder_tokens":list(self.placeholder_tokens),"success_patterns":list(self.success_patterns),"failure_patterns":list(self.failure_patterns)}
 @classmethod
 def from_dict(c,d): return c(str(d["proof_system_id"]),ProofSystemKind(str(d.get("kind","UNKNOWN"))),str(d["name"]),tuple(d.get("file_extensions",())),tuple(d.get("config_files",())),CheckCommandKind(str(d.get("default_check_command_kind","NO_EXECUTION"))),tuple(d.get("allowed_command_tokens",())),tuple(d.get("placeholder_tokens",())),tuple(d.get("success_patterns",())),tuple(d.get("failure_patterns",())),bool(d.get("requires_external_tool",True)),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
@dataclass
class ProofProjectManifest:
 project_id:str; proof_system_id:str; kind:ProofSystemKind; root_path:str|None=None; project_name:str|None=None; config_paths:tuple[str,...]=(); artifact_ids:tuple[str,...]=(); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def to_dict(self): return {**self.__dict__,"kind":self.kind.value,"config_paths":list(self.config_paths),"artifact_ids":list(self.artifact_ids)}
 @classmethod
 def from_dict(c,d): return c(str(d["project_id"]),str(d["proof_system_id"]),ProofSystemKind(str(d.get("kind","UNKNOWN"))),_s(d.get("root_path")),_s(d.get("project_name")),tuple(d.get("config_paths",())),tuple(d.get("artifact_ids",())),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
@dataclass
class ProofArtifactManifest:
 artifact_id:str; proof_system_id:str; kind:ProofSystemKind; artifact_kind:ProofArtifactKind; path:str|None=None; content_hash:str|None=None; theorem_names:tuple[str,...]=(); imports:tuple[str,...]=(); placeholders:tuple[str,...]=(); status:ProofArtifactStatus=ProofArtifactStatus.DISCOVERED; source_object_id:str|None=None; source_kind:str|None=None; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def has_placeholder(self): return bool(self.placeholders)
 def to_dict(self): return {**self.__dict__,"kind":self.kind.value,"artifact_kind":self.artifact_kind.value,"theorem_names":list(self.theorem_names),"imports":list(self.imports),"placeholders":list(self.placeholders),"status":self.status.value}
 @classmethod
 def from_dict(c,d): return c(str(d["artifact_id"]),str(d["proof_system_id"]),ProofSystemKind(str(d.get("kind","UNKNOWN"))),ProofArtifactKind(str(d.get("artifact_kind","UNKNOWN"))),_s(d.get("path")),_s(d.get("content_hash")),tuple(d.get("theorem_names",())),tuple(d.get("imports",())),tuple(d.get("placeholders",())),ProofArtifactStatus(str(d.get("status","DISCOVERED"))),_s(d.get("source_object_id")),_s(d.get("source_kind")),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
@dataclass
class ProofImportGraph:
 graph_id:str; project_id:str|None=None; nodes:tuple[str,...]=(); edges:tuple[dict[str,Any],...]=(); cycles:tuple[tuple[str,...],...]=(); missing_imports:tuple[str,...]=(); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def to_dict(self): return {**self.__dict__,"nodes":list(self.nodes),"edges":[dict(x) for x in self.edges],"cycles":[list(x) for x in self.cycles],"missing_imports":list(self.missing_imports)}
 @classmethod
 def from_dict(c,d): return c(str(d["graph_id"]),_s(d.get("project_id")),tuple(d.get("nodes",())),tuple(dict(x) for x in d.get("edges",())),tuple(tuple(x) for x in d.get("cycles",())),tuple(d.get("missing_imports",())),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
@dataclass
class ProofCheckCommandContract:
 contract_id:str; proof_system_id:str; kind:ProofSystemKind; command_kind:CheckCommandKind; command_tokens:tuple[str,...]=(); allowed:bool=False; requires_external_tool:bool=True; timeout_seconds:int|None=None; working_directory:str|None=None; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def is_safe(self):
  if self.command_kind in {CheckCommandKind.NO_EXECUTION,CheckCommandKind.IMPORT_ONLY}: return self.allowed or not self.command_tokens
  bad=(";","&&","||","|",">","<","`","$(")
  return bool(self.allowed and self.command_tokens and all(isinstance(x,str) and not any(b in x for b in bad) for x in self.command_tokens))
 def to_dict(self): return {**self.__dict__,"kind":self.kind.value,"command_kind":self.command_kind.value,"command_tokens":list(self.command_tokens)}
 @classmethod
 def from_dict(c,d): return c(str(d["contract_id"]),str(d["proof_system_id"]),ProofSystemKind(str(d.get("kind","UNKNOWN"))),CheckCommandKind(str(d.get("command_kind","NO_EXECUTION"))),tuple(d.get("command_tokens",())),bool(d.get("allowed",False)),bool(d.get("requires_external_tool",True)),d.get("timeout_seconds"),_s(d.get("working_directory")),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
@dataclass
class ProofCheckRequest:
 request_id:str; artifact_id:str; contract_id:str; proof_system_id:str; kind:ProofSystemKind; status:CheckRequestStatus=CheckRequestStatus.CREATED; command_tokens:tuple[str,...]=(); run_allowed:bool=False; artifact_path:str|None=None; placeholder_blocked:bool=False; warnings:tuple[str,...]=(); criticals:tuple[str,...]=(); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def to_dict(self): return {**self.__dict__,"kind":self.kind.value,"status":self.status.value,"command_tokens":list(self.command_tokens),"warnings":list(self.warnings),"criticals":list(self.criticals)}
 @classmethod
 def from_dict(c,d): return c(str(d["request_id"]),str(d["artifact_id"]),str(d["contract_id"]),str(d["proof_system_id"]),ProofSystemKind(str(d.get("kind","UNKNOWN"))),CheckRequestStatus(str(d.get("status","CREATED"))),tuple(d.get("command_tokens",())),bool(d.get("run_allowed",False)),_s(d.get("artifact_path")),bool(d.get("placeholder_blocked",False)),tuple(d.get("warnings",())),tuple(d.get("criticals",())),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
@dataclass
class ProofCheckResult:
 result_id:str; request_id:str; artifact_id:str|None=None; proof_system_id:str|None=None; kind:ProofSystemKind=ProofSystemKind.UNKNOWN; status:CheckResultStatus=CheckResultStatus.NOT_RUN; stdout_excerpt:str|None=None; stderr_excerpt:str|None=None; exit_code:int|None=None; duration_seconds:float|None=None; theorem_names:tuple[str,...]=(); certificate_id:str|None=None; terminal_form:TerminalForm|None=None; verifier_boundary_crossed:bool=False; warnings:tuple[str,...]=(); criticals:tuple[str,...]=(); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def crosses_boundary(self): return bool(self.status==CheckResultStatus.PASSED and self.certificate_id and self.terminal_form and self.verifier_boundary_crossed)
 def to_dict(self): return {**self.__dict__,"kind":self.kind.value,"status":self.status.value,"theorem_names":list(self.theorem_names),"terminal_form":self.terminal_form.value if self.terminal_form else None,"warnings":list(self.warnings),"criticals":list(self.criticals)}
 @classmethod
 def from_dict(c,d): return c(str(d["result_id"]),str(d["request_id"]),_s(d.get("artifact_id")),_s(d.get("proof_system_id")),ProofSystemKind(str(d.get("kind","UNKNOWN"))),CheckResultStatus(str(d.get("status","NOT_RUN"))),_s(d.get("stdout_excerpt")),_s(d.get("stderr_excerpt")),d.get("exit_code"),d.get("duration_seconds"),tuple(d.get("theorem_names",())),_s(d.get("certificate_id")),_term(d.get("terminal_form")),bool(d.get("verifier_boundary_crossed",False)),tuple(d.get("warnings",())),tuple(d.get("criticals",())),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
@dataclass
class TrustedProofImportRecord:
 import_id:str; proof_system_id:str; kind:ProofSystemKind; source_uri:str|None=None; artifact_id:str|None=None; certificate_id:str|None=None; terminal_form:TerminalForm|None=None; status:TrustedImportStatus=TrustedImportStatus.REQUESTED; provenance:tuple[str,...]=(); reviewer:str|None=None; verifier_boundary_crossed:bool=False; warnings:tuple[str,...]=(); criticals:tuple[str,...]=(); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def crosses_boundary(self): return bool(self.status==TrustedImportStatus.ACCEPTED_WITH_BOUNDARY and self.certificate_id and self.terminal_form and self.verifier_boundary_crossed and self.provenance)
 def to_dict(self): return {**self.__dict__,"kind":self.kind.value,"terminal_form":self.terminal_form.value if self.terminal_form else None,"status":self.status.value,"provenance":list(self.provenance),"warnings":list(self.warnings),"criticals":list(self.criticals)}
 @classmethod
 def from_dict(c,d): return c(str(d["import_id"]),str(d["proof_system_id"]),ProofSystemKind(str(d.get("kind","UNKNOWN"))),_s(d.get("source_uri")),_s(d.get("artifact_id")),_s(d.get("certificate_id")),_term(d.get("terminal_form")),TrustedImportStatus(str(d.get("status","REQUESTED"))),tuple(d.get("provenance",())),_s(d.get("reviewer")),bool(d.get("verifier_boundary_crossed",False)),tuple(d.get("warnings",())),tuple(d.get("criticals",())),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
@dataclass
class ProofBoundaryEvidence:
 evidence_id:str; boundary_kind:ProofBoundaryKind; proof_system_id:str|None=None; kind:ProofSystemKind=ProofSystemKind.UNKNOWN; artifact_id:str|None=None; request_id:str|None=None; result_id:str|None=None; import_id:str|None=None; certificate_id:str|None=None; terminal_form:TerminalForm|None=None; verifier_boundary_crossed:bool=False; evidence_notes:tuple[str,...]=(); warnings:tuple[str,...]=(); criticals:tuple[str,...]=(); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=False
 def is_valid_boundary(self): return bool(self.certificate_id and self.terminal_form and self.verifier_boundary_crossed and self.boundary_kind in {ProofBoundaryKind.VERIFIER_CHECK,ProofBoundaryKind.TRUSTED_IMPORT,ProofBoundaryKind.CHAIN_AUDIT,ProofBoundaryKind.FINITE_VALIDATION})
 def to_dict(self): return {**self.__dict__,"boundary_kind":self.boundary_kind.value,"kind":self.kind.value,"terminal_form":self.terminal_form.value if self.terminal_form else None,"evidence_notes":list(self.evidence_notes),"warnings":list(self.warnings),"criticals":list(self.criticals)}
 @classmethod
 def from_dict(c,d): return c(str(d["evidence_id"]),ProofBoundaryKind(str(d.get("boundary_kind","UNKNOWN"))),_s(d.get("proof_system_id")),ProofSystemKind(str(d.get("kind","UNKNOWN"))),_s(d.get("artifact_id")),_s(d.get("request_id")),_s(d.get("result_id")),_s(d.get("import_id")),_s(d.get("certificate_id")),_term(d.get("terminal_form")),bool(d.get("verifier_boundary_crossed",False)),tuple(d.get("evidence_notes",())),tuple(d.get("warnings",())),tuple(d.get("criticals",())),dict(d.get("metadata",{})),bool(d.get("advisory",False)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
@dataclass
class ProofSystemTask:
 task_id:str; task_kind:ProofSystemTaskKind; proof_system_id:str|None=None; kind:ProofSystemKind=ProofSystemKind.UNKNOWN; artifact_id:str|None=None; project_id:str|None=None; title:str|None=None; description:str|None=None; priority:float=0.0; required_boundary:ProofBoundaryKind=ProofBoundaryKind.NONE; warnings:tuple[str,...]=(); criticals:tuple[str,...]=(); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def to_dict(self): return {**self.__dict__,"task_kind":self.task_kind.value,"kind":self.kind.value,"required_boundary":self.required_boundary.value,"warnings":list(self.warnings),"criticals":list(self.criticals)}
 @classmethod
 def from_dict(c,d): return c(str(d["task_id"]),ProofSystemTaskKind(str(d.get("task_kind","UNKNOWN"))),_s(d.get("proof_system_id")),ProofSystemKind(str(d.get("kind","UNKNOWN"))),_s(d.get("artifact_id")),_s(d.get("project_id")),_s(d.get("title")),_s(d.get("description")),float(d.get("priority",0)),ProofBoundaryKind(str(d.get("required_boundary","NONE"))),tuple(d.get("warnings",())),tuple(d.get("criticals",())),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
@dataclass
class ProofSystemIntegrationReport:
 report_id:str; specs:list[ProofSystemSpec]=field(default_factory=list); projects:list[ProofProjectManifest]=field(default_factory=list); artifacts:list[ProofArtifactManifest]=field(default_factory=list); import_graphs:list[ProofImportGraph]=field(default_factory=list); command_contracts:list[ProofCheckCommandContract]=field(default_factory=list); check_requests:list[ProofCheckRequest]=field(default_factory=list); check_results:list[ProofCheckResult]=field(default_factory=list); trusted_imports:list[TrustedProofImportRecord]=field(default_factory=list); boundary_evidence:list[ProofBoundaryEvidence]=field(default_factory=list); tasks:list[ProofSystemTask]=field(default_factory=list); status:ProofSystemIntegrationReportStatus=ProofSystemIntegrationReportStatus.EMPTY; created_at:str=field(default_factory=lambda:_now()); summary:dict[str,Any]=field(default_factory=dict); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def spec_count(self): return len(self.specs)
 def project_count(self): return len(self.projects)
 def artifact_count(self): return len(self.artifacts)
 def import_graph_count(self): return len(self.import_graphs)
 def command_contract_count(self): return len(self.command_contracts)
 def check_request_count(self): return len(self.check_requests)
 def check_result_count(self): return len(self.check_results)
 def trusted_import_count(self): return len(self.trusted_imports)
 def boundary_evidence_count(self): return len(self.boundary_evidence)
 def task_count(self): return len(self.tasks)
 def critical_count(self): return len([x for x in audit_proof_system_integration_report(self) if x["severity"]=="CRITICAL"])
 def summarize(self):
  self.summary={"spec_total":len(self.specs),"project_total":len(self.projects),"artifact_total":len(self.artifacts),"import_graph_total":len(self.import_graphs),"command_contract_total":len(self.command_contracts),"check_request_total":len(self.check_requests),"check_result_total":len(self.check_results),"trusted_import_total":len(self.trusted_imports),"boundary_evidence_total":len(self.boundary_evidence),"task_total":len(self.tasks),"proof_system_counts":dict(Counter(x.kind.value for x in self.artifacts)),"artifact_status_counts":dict(Counter(x.status.value for x in self.artifacts)),"request_status_counts":dict(Counter(x.status.value for x in self.check_requests)),"result_status_counts":dict(Counter(x.status.value for x in self.check_results)),"trusted_import_status_counts":dict(Counter(x.status.value for x in self.trusted_imports)),"boundary_kind_counts":dict(Counter(x.boundary_kind.value for x in self.boundary_evidence)),"placeholder_count":sum(x.has_placeholder() for x in self.artifacts),"boundary_crossed_count":sum(x.is_valid_boundary() for x in self.boundary_evidence),"critical_count":self.critical_count()}; return self.summary
 def to_dict(self): return {**self.__dict__,"specs":[x.to_dict() for x in self.specs],"projects":[x.to_dict() for x in self.projects],"artifacts":[x.to_dict() for x in self.artifacts],"import_graphs":[x.to_dict() for x in self.import_graphs],"command_contracts":[x.to_dict() for x in self.command_contracts],"check_requests":[x.to_dict() for x in self.check_requests],"check_results":[x.to_dict() for x in self.check_results],"trusted_imports":[x.to_dict() for x in self.trusted_imports],"boundary_evidence":[x.to_dict() for x in self.boundary_evidence],"tasks":[x.to_dict() for x in self.tasks],"status":self.status.value}
 @classmethod
 def from_dict(c,d): return c(str(d["report_id"]),[ProofSystemSpec.from_dict(x) for x in d.get("specs",())],[ProofProjectManifest.from_dict(x) for x in d.get("projects",())],[ProofArtifactManifest.from_dict(x) for x in d.get("artifacts",())],[ProofImportGraph.from_dict(x) for x in d.get("import_graphs",())],[ProofCheckCommandContract.from_dict(x) for x in d.get("command_contracts",())],[ProofCheckRequest.from_dict(x) for x in d.get("check_requests",())],[ProofCheckResult.from_dict(x) for x in d.get("check_results",())],[TrustedProofImportRecord.from_dict(x) for x in d.get("trusted_imports",())],[ProofBoundaryEvidence.from_dict(x) for x in d.get("boundary_evidence",())],[ProofSystemTask.from_dict(x) for x in d.get("tasks",())],ProofSystemIntegrationReportStatus(str(d.get("status","EMPTY"))),str(d.get("created_at",_now())),dict(d.get("summary",{})),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
 def write_json(self,p): _w(p,self.to_json())
 @classmethod
 def read_json(c,p): return c.from_json(Path(p).read_text())
 def write_jsonl(self,p): _w(p,self.to_json()+"\n")
 @classmethod
 def read_jsonl(c,p): return [c.from_json(x) for x in Path(p).read_text().splitlines() if x.strip()]
def make_proof_system_spec_id(*x): return content_id("proof-system-spec",x)
def make_proof_project_manifest_id(*x): return content_id("proof-project",x)
def make_proof_artifact_manifest_id(*x): return content_id("proof-artifact-manifest",x)
def make_proof_import_graph_id(*x): return content_id("proof-import-graph",x)
def make_proof_check_command_contract_id(*x): return content_id("proof-check-contract",x)
def make_proof_check_request_id(*x): return content_id("proof-check-request",x)
def make_proof_check_result_id(*x): return content_id("proof-check-result",x)
def make_trusted_proof_import_record_id(*x): return content_id("trusted-proof-import",x)
def make_proof_boundary_evidence_id(*x): return content_id("proof-boundary-evidence",x)
def make_proof_system_task_id(*x): return content_id("proof-system-task",x)
def make_proof_system_integration_report_id(*x): return content_id("proof-system-report",x)
def default_proof_system_specs():
 return [ProofSystemSpec(make_proof_system_spec_id(n),k,n,ext,cfg,cmd,allowed,ph,succ,fail,req) for n,k,ext,cfg,cmd,allowed,ph,succ,fail,req in [
 ("lean",ProofSystemKind.LEAN,(".lean",),("lakefile.lean","lean-toolchain","lake-manifest.json"),CheckCommandKind.LEAN_CHECK,("lean","lake"),("sorry","admit","by sorry"),("build completed successfully",),("error:","failed","unknown identifier","unsolved goals"),True),
 ("isabelle",ProofSystemKind.ISABELLE,(".thy",),("ROOT",),CheckCommandKind.ISABELLE_BUILD,("isabelle",),("sorry","oops"),("finished","ok"),("error","failed"),True),
 ("coq",ProofSystemKind.COQ,(".v",),("_CoqProject","Makefile"),CheckCommandKind.COQ_CHECK,("coqc",),("Admitted.","admit"),(),("Error:","Unable to unify"),True),
 ("generic_proof_assistant",ProofSystemKind.GENERIC_PROOF_ASSISTANT,(),(),CheckCommandKind.GENERIC_CHECK,(),("sorry","admit","todo"),(),(),True),
 ("proof_text_import",ProofSystemKind.PROOF_TEXT_IMPORT,(),(),CheckCommandKind.IMPORT_ONLY,(),("sketch","omitted","left to the reader"),(),(),False)]]
def detect_proof_system_kind(x):
 d=x if isinstance(x,Mapping) else {}; text=str(d.get("text") or d.get("path") or x or ""); low=text.lower()
 explicit=str(d.get("proof_system") or d.get("kind") or "").upper()
 if explicit in ProofSystemKind.__members__: return ProofSystemKind[explicit]
 if low.endswith(".v") or any(k in text for k in ("Theorem ","Lemma ","Require Import","Qed.")): return ProofSystemKind.COQ
 if low.endswith(".lean") or any(k in low for k in ("theorem ","lemma ","example ","namespace "," := "," by ")): return ProofSystemKind.LEAN
 if low.endswith(".thy") or any(k in low for k in ("theory ","imports ","begin")) and "theory" in low: return ProofSystemKind.ISABELLE
 if any(k in low for k in ("proof","suppose","therefore","hence","theorem")): return ProofSystemKind.PROOF_TEXT_IMPORT
 return ProofSystemKind.UNKNOWN
def proof_system_spec_for_kind(k,specs=None):
 ss=list(specs or default_proof_system_specs())
 return next((x for x in ss if x.kind==k),next(x for x in ss if x.kind==ProofSystemKind.GENERIC_PROOF_ASSISTANT))
def extract_lean_imports(t): return tuple(re.findall(r"^\s*import\s+([^\n]+)",t,re.M))
def extract_lean_theorem_names(t): return tuple(re.findall(r"\b(?:theorem|lemma|example)\s+([A-Za-z_][A-Za-z0-9_]*)",t))
def extract_isabelle_imports(t): return tuple(re.findall(r"^\s*imports\s+(.+)$",t,re.M))
def extract_isabelle_theorem_names(t): return tuple(re.findall(r"\b(?:theorem|lemma)\s+([A-Za-z_][A-Za-z0-9_]*)",t))
def extract_coq_imports(t): return tuple(re.findall(r"^\s*Require\s+Import\s+([^\.\n]+)",t,re.M))
def extract_coq_theorem_names(t): return tuple(re.findall(r"\b(?:Theorem|Lemma)\s+([A-Za-z_][A-Za-z0-9_]*)",t))
def extract_generic_proof_markers(t): return tuple(k for k in ("proof","theorem","lemma","suppose","therefore") if k in t.lower())
def proof_artifact_manifest_from_text(text,*,spec=None,path=None,source_object_id=None,source_kind=None):
 s=spec or proof_system_spec_for_kind(detect_proof_system_kind({"text":text,"path":path}))
 names,imps=(extract_lean_theorem_names(text),extract_lean_imports(text)) if s.kind==ProofSystemKind.LEAN else (extract_isabelle_theorem_names(text),extract_isabelle_imports(text)) if s.kind==ProofSystemKind.ISABELLE else (extract_coq_theorem_names(text),extract_coq_imports(text)) if s.kind==ProofSystemKind.COQ else (extract_generic_proof_markers(text),())
 ph=tuple(x for x in s.placeholder_tokens if x.lower() in text.lower()); kind=ProofArtifactKind.THEOREM_FILE if s.kind in {ProofSystemKind.LEAN,ProofSystemKind.ISABELLE,ProofSystemKind.COQ} else ProofArtifactKind.PROOF_TEXT
 return ProofArtifactManifest(make_proof_artifact_manifest_id(s.proof_system_id,path,text),s.proof_system_id,s.kind,kind,path,content_id("proof-artifact-content",text),names,imps,ph,ProofArtifactStatus.PLACEHOLDER_DETECTED if ph else ProofArtifactStatus.PARSED,source_object_id,source_kind,{"text":text})
def proof_artifact_manifest_from_path(path,*,spec=None,root_path=None,read_content=True,source_object_id=None,source_kind=None):
 p=Path(path); s=spec or proof_system_spec_for_kind(detect_proof_system_kind(str(p)))
 if not p.exists(): return ProofArtifactManifest(make_proof_artifact_manifest_id(s.proof_system_id,str(p),"missing"),s.proof_system_id,s.kind,ProofArtifactKind.THEOREM_FILE,str(p),status=ProofArtifactStatus.MISSING,source_object_id=source_object_id,source_kind=source_kind)
 return proof_artifact_manifest_from_text(p.read_text(encoding="utf-8") if read_content else "",spec=s,path=str(p),source_object_id=source_object_id,source_kind=source_kind)
def build_proof_project_manifest(root_path=None,artifacts=(),*,spec=None,project_name=None,scan_files=False,max_files=500):
 arts=list(artifacts); root=Path(root_path) if root_path else None; s=spec or proof_system_spec_for_kind(arts[0].kind if arts else ProofSystemKind.UNKNOWN)
 if scan_files and root and root.exists():
  for p in list(root.rglob("*"))[:max_files]:
   if p.is_file() and s.recognizes_path(p): arts.append(proof_artifact_manifest_from_path(p,spec=s))
 cfg=tuple(str(root/x) for x in s.config_files if root and (root/x).exists())
 return ProofProjectManifest(make_proof_project_manifest_id(str(root),[x.artifact_id for x in arts]),s.proof_system_id,s.kind,str(root) if root else None,project_name, cfg,tuple(x.artifact_id for x in arts))
def build_proof_import_graph(project=None,artifacts=()):
 arts=list(artifacts); byname={}
 for a in arts:
  if a.path: byname[Path(a.path).stem]=a.artifact_id
 edges=[]; missing=[]
 for a in arts:
  for imp in a.imports:
   key=imp.split(".")[-1].split()[0]; target=byname.get(key)
   edges.append({"source_artifact_id":a.artifact_id,"target_artifact_id":target,"target_import":None if target else imp,"edge_kind":ImportEdgeKind.IMPORTS.value})
   if not target: missing.append(imp)
 cycles=[]
 pairs={(e["source_artifact_id"],e.get("target_artifact_id")) for e in edges if e.get("target_artifact_id")}
 for a,b in pairs:
  if (b,a) in pairs: cycles.append(tuple(sorted((a,b))))
 return ProofImportGraph(make_proof_import_graph_id(project.project_id if project else None,edges),project.project_id if project else None,tuple(a.artifact_id for a in arts),tuple(edges),tuple(dict.fromkeys(cycles)),tuple(dict.fromkeys(missing)))
def default_check_command_contract_for_artifact(a,spec=None,*,allow_execution=False,timeout_seconds=30,working_directory=None):
 s=spec or proof_system_spec_for_kind(a.kind); toks=()
 if s.kind==ProofSystemKind.LEAN and a.path: toks=("lean",a.path)
 elif s.kind==ProofSystemKind.ISABELLE and working_directory: toks=("isabelle","build","-D",working_directory)
 elif s.kind==ProofSystemKind.COQ and a.path: toks=("coqc",a.path)
 return ProofCheckCommandContract(make_proof_check_command_contract_id(a.artifact_id,toks,allow_execution),s.proof_system_id,s.kind,s.default_check_command_kind,toks,allow_execution,s.requires_external_tool,timeout_seconds,working_directory)
def create_check_request(a,c):
 if a.has_placeholder(): st=CheckRequestStatus.BLOCKED_PLACEHOLDER
 elif not a.path or not Path(a.path).exists(): st=CheckRequestStatus.BLOCKED_MISSING_ARTIFACT
 elif not c.is_safe() and c.allowed: st=CheckRequestStatus.BLOCKED_UNSAFE_COMMAND
 elif not c.allowed: st=CheckRequestStatus.RUN_NOT_ALLOWED
 else: st=CheckRequestStatus.READY
 return ProofCheckRequest(make_proof_check_request_id(a.artifact_id,c.contract_id),a.artifact_id,c.contract_id,a.proof_system_id,a.kind,st,c.command_tokens,st in {CheckRequestStatus.READY,CheckRequestStatus.RUN_ALLOWED},a.path,a.has_placeholder(),metadata={"contract_safe":c.is_safe()})
def parse_check_result(req,*,stdout="",stderr="",exit_code=None,duration_seconds=None,certificate_id=None,terminal_form=None,verifier_boundary_crossed=False):
 text=(stdout+"\n"+stderr).lower(); blocked=req.status in {CheckRequestStatus.BLOCKED_MISSING_ARTIFACT,CheckRequestStatus.BLOCKED_PLACEHOLDER,CheckRequestStatus.BLOCKED_UNSAFE_COMMAND}
 if req.status==CheckRequestStatus.BLOCKED_PLACEHOLDER or "sorry" in text or "admit" in text: st=CheckResultStatus.PLACEHOLDER_FOUND
 elif blocked: st=CheckResultStatus.INCONCLUSIVE
 elif any(k in text for k in ("error","failed","unknown identifier","unsolved goals","unable to unify")): st=CheckResultStatus.FAILED
 elif exit_code==0: st=CheckResultStatus.PASSED
 else: st=CheckResultStatus.NOT_RUN
 return ProofCheckResult(make_proof_check_result_id(req.request_id,stdout,stderr,exit_code),req.request_id,req.artifact_id,req.proof_system_id,req.kind,st,stdout[:300] or None,stderr[:300] or None,exit_code,duration_seconds,certificate_id=_s(certificate_id),terminal_form=_term(terminal_form),verifier_boundary_crossed=verifier_boundary_crossed,metadata={"raw_success_text":"verified successfully" in text})
def proof_boundary_evidence_from_check_result(r):
 return ProofBoundaryEvidence(make_proof_boundary_evidence_id(r.result_id),ProofBoundaryKind.VERIFIER_CHECK,r.proof_system_id,r.kind,r.artifact_id,r.request_id,r.result_id,certificate_id=r.certificate_id,terminal_form=r.terminal_form,verifier_boundary_crossed=r.verifier_boundary_crossed,evidence_notes=("parsed passed check",)) if r.crosses_boundary() else None
def trusted_import_record_from_mapping(d):
 cert=_s(d.get("certificate_id")); tf=_term(d.get("terminal_form")); vb=bool(d.get("verifier_boundary_crossed",False)); prov=tuple(d.get("provenance",()))
 st=TrustedImportStatus.ACCEPTED_WITH_BOUNDARY if cert and tf and vb and prov else TrustedImportStatus.MISSING_PROVENANCE if cert and tf and vb and not prov else TrustedImportStatus.MISSING_ARTIFACT if not d.get("artifact_id") else TrustedImportStatus.REQUESTED
 return TrustedProofImportRecord(str(d.get("import_id") or make_trusted_proof_import_record_id(d)),str(d.get("proof_system_id","proof_text_import")),ProofSystemKind(str(d.get("kind","PROOF_TEXT_IMPORT"))),_s(d.get("source_uri")),_s(d.get("artifact_id")),cert,tf,st,prov,_s(d.get("reviewer")),vb,metadata=dict(d.get("metadata",{})))
def proof_boundary_evidence_from_trusted_import(r):
 return ProofBoundaryEvidence(make_proof_boundary_evidence_id(r.import_id),ProofBoundaryKind.TRUSTED_IMPORT,r.proof_system_id,r.kind,r.artifact_id,import_id=r.import_id,certificate_id=r.certificate_id,terminal_form=r.terminal_form,verifier_boundary_crossed=r.verifier_boundary_crossed,evidence_notes=("trusted import accepted with provenance",)) if r.crosses_boundary() else None
def proof_system_tasks_from_artifacts(arts,import_graph=None):
 out=[]
 for a in arts:
  if a.has_placeholder():
   out += [_task(a,ProofSystemTaskKind.REMOVE_PLACEHOLDER),_task(a,ProofSystemTaskKind.REPAIR_PROOF)]
  elif a.artifact_kind==ProofArtifactKind.PROOF_TEXT:
   out += [_task(a,ProofSystemTaskKind.FORMALIZE_TEXT),_task(a,ProofSystemTaskKind.DIGEST_PROOF)]
  elif a.status!=ProofArtifactStatus.MISSING: out.append(_task(a,ProofSystemTaskKind.CHECK_THEOREM_FILE,ProofBoundaryKind.VERIFIER_CHECK))
 if import_graph and import_graph.missing_imports: out.append(ProofSystemTask(make_proof_system_task_id(import_graph.graph_id,"imports"),ProofSystemTaskKind.BUILD_IMPORT_GRAPH,project_id=import_graph.project_id))
 return out
def proof_system_tasks_from_check_results(rs): return [ProofSystemTask(make_proof_system_task_id(r.result_id,"repair"),ProofSystemTaskKind.REPAIR_PROOF,r.proof_system_id,r.kind,r.artifact_id) for r in rs if r.status in {CheckResultStatus.FAILED,CheckResultStatus.PLACEHOLDER_FOUND}]
def proof_system_tasks_from_trusted_imports(rs): return [ProofSystemTask(make_proof_system_task_id(r.import_id,"review"),ProofSystemTaskKind.LAWBOOK_CANDIDATE_REVIEW if r.crosses_boundary() else ProofSystemTaskKind.TRUSTED_IMPORT_REVIEW,r.proof_system_id,r.kind,r.artifact_id) for r in rs]
def proof_system_inputs_from_object(o):
 if isinstance(o,Mapping): return [dict(o)]
 if isinstance(o,str): return [{"text":o,"source_kind":"text"}]
 if hasattr(o,"to_dict"):
  d=o.to_dict(); oid=next((d.get(k) for k in ("claim_id","handoff_id","task_id","parse_id","normalize_id","validation_id","entry_id","answer_id","candidate_id","descriptor_id","role_id","conjecture_id","reason_id","rule_id","episode_id","trace_id","stage_id","experience_id","report_id") if d.get(k)),None)
  if o.__class__.__name__.endswith("Report"):
   rows=[]
   for key in ("handoffs","tasks","parses","normalizations","validations","answers","typed_projection_candidates","role_objects","definition_candidates","conjecture_candidates","candidates","reason_nodes","rules","episodes","stages"):
    for x in getattr(o,key,[]) or []: rows += proof_system_inputs_from_object(x)
   return rows or [{"source_object_id":oid,"source_kind":o.__class__.__name__,"text":_j(d),"metadata":d}]
  return [{"source_object_id":oid,"source_kind":o.__class__.__name__,"text":d.get("raw_text") or d.get("raw") or d.get("statement") or d.get("text") or d.get("description") or _j(d),"path":d.get("path"),"proof_system":d.get("proof_system_id"),"kind":d.get("kind"),"artifact_kind":d.get("artifact_kind"),"theorem_names":d.get("theorem_names"),"imports":d.get("imports"),"certificate_id":d.get("certificate_id"),"terminal_form":d.get("terminal_form"),"verifier_boundary_crossed":d.get("verifier_boundary_crossed"),"provenance":d.get("provenance"),"metadata":d}]
 return []
def build_proof_system_integration_report(objects=(),specs=(),artifacts=(),projects=(),check_results=(),trusted_imports=(),*,include_default_specs=True,scan_project_files=False,allow_execution=False,create_check_requests=True,create_boundary_evidence=True):
 ss=list(specs)+(default_proof_system_specs() if include_default_specs else []); ss=list({x.proof_system_id:x for x in ss}.values()); arts=list(artifacts)
 for d in [x for o in objects for x in proof_system_inputs_from_object(o)]:
  if d.get("path"): arts.append(proof_artifact_manifest_from_path(d["path"],source_object_id=_s(d.get("source_object_id")),source_kind=_s(d.get("source_kind"))))
  elif d.get("text"): arts.append(proof_artifact_manifest_from_text(str(d["text"]),source_object_id=_s(d.get("source_object_id")),source_kind=_s(d.get("source_kind"))))
 projs=list(projects)
 if arts and not projs: projs.append(build_proof_project_manifest(artifacts=arts,spec=proof_system_spec_for_kind(arts[0].kind,ss)))
 graphs=[build_proof_import_graph(p,[a for a in arts if a.artifact_id in p.artifact_ids]) for p in projs]
 contracts=[default_check_command_contract_for_artifact(a,proof_system_spec_for_kind(a.kind,ss),allow_execution=allow_execution) for a in arts]
 reqs=[create_check_request(a,c) for a,c in zip(arts,contracts)] if create_check_requests else []
 results=list(check_results); imports=list(trusted_imports); evidence=[]
 if create_boundary_evidence:
  evidence += [e for e in (proof_boundary_evidence_from_check_result(x) for x in results) if e]
  evidence += [e for e in (proof_boundary_evidence_from_trusted_import(x) for x in imports) if e]
 tasks=[t for g in graphs for t in proof_system_tasks_from_artifacts([a for a in arts if a.artifact_id in g.nodes],g)]+proof_system_tasks_from_check_results(results)+proof_system_tasks_from_trusted_imports(imports)
 r=ProofSystemIntegrationReport(make_proof_system_integration_report_id([a.artifact_id for a in arts]),ss,projs,arts,graphs,contracts,reqs,results,imports,evidence,tasks); r.summarize(); r.status=ProofSystemIntegrationReportStatus.HAS_CRITICALS if r.critical_count() else ProofSystemIntegrationReportStatus.TASKS_EMITTED if tasks else ProofSystemIntegrationReportStatus.BOUNDARY_EVIDENCE_RECORDED if evidence else ProofSystemIntegrationReportStatus.CHECK_REQUESTS_CREATED if reqs else ProofSystemIntegrationReportStatus.ARTIFACTS_REPORTED if arts else ProofSystemIntegrationReportStatus.SPECS_REPORTED if ss else ProofSystemIntegrationReportStatus.EMPTY; return r
def proof_system_report_to_lawbook_candidates(r): return [LawbookEntry(make_lawbook_entry_id("proof-system",r.report_id,x.evidence_id if isinstance(x,ProofBoundaryEvidence) else x.artifact_id),LawbookEntryKind.VERIFIED_TRUTH_ENTRY if isinstance(x,ProofBoundaryEvidence) else LawbookEntryKind.ROUTE_RULE_ENTRY,LawbookEntryStatus.CANDIDATE,terminal_form=x.terminal_form if isinstance(x,ProofBoundaryEvidence) else None,certificate_id=x.certificate_id if isinstance(x,ProofBoundaryEvidence) else None,metadata={"proof_system_integration_not_truth":True,"proof_system_report_id":r.report_id,"proof_system_advisory_only":True,**({"boundary_evidence_id":x.evidence_id} if isinstance(x,ProofBoundaryEvidence) else {})},advisory=True) for x in list(r.boundary_evidence)+list(r.artifacts)]
def proof_system_report_to_continuation_outputs(r): return [ContinuationActionOutput(make_continuation_output_id({"proof-system":t.task_id}),"proof_system_integration",ContinuationOutputKind.TASK,ContinuationActionStatus.ADVISORY_ONLY,task_payload={"task":t.task_kind.value.lower(),"task_id":t.task_id},advisory=True) for t in r.tasks]
def proof_system_report_to_curriculum(r):
 stages=[CurriculumStage(make_curriculum_stage_id("proof-system",x),CurriculumStageKind.RESIDUAL_REVIEW,CurriculumStageStatus.ADVISORY_ONLY,title=x,metadata={"proof_system_advisory_only":True},advisory=True) for x in ("discover artifacts","build import graph","remove placeholders","check theorem file","parse check result","trusted import review","digest proof","lawbook candidate review")]
 return ContinuationCurriculum(make_curriculum_id("proof-system",r.report_id),strategy=CurriculumBuildStrategy.MIXED,stages=stages,status=CurriculumTraceStatus.ADVISORY_ONLY)
def proof_system_report_to_discovery_value_scores(r):
 out=[]
 for x in list(r.check_requests)+list(r.boundary_evidence):
  val=.9 if isinstance(x,ProofBoundaryEvidence) else .4 if x.status==CheckRequestStatus.READY else .1; sig=DiscoveryValueSignal(content_id("proof-system-signal",getattr(x,"evidence_id",getattr(x,"request_id",None))),DiscoveryValueSignalKind.REUSE_VALUE,val,source_object_kind=DiscoveryValueObjectKind.RAW_TASK); s=DiscoveryValueScore(content_id("proof-system-score",sig.signal_id),sig.signal_id,DiscoveryValueObjectKind.RAW_TASK,signals=[sig],metadata={"proof_system_advisory_only":True}); s.recompute(); out.append(s)
 return out
def proof_system_report_to_process_episodes(r): return [ProcessEpisodeRecord(make_process_episode_id("proof-system",a.artifact_id),ProcessEpisodeStatus.ADVISORY_ONLY,contexts=[ProcessContextItem(content_id("proof-system-context",a.artifact_id),ProcessContextKind.RAW_EVENT,ProcessContextRole.ADVISORY_ONLY,a.artifact_id)],advisory=True) for a in r.artifacts]
def proof_system_report_to_verifier_feedback(r): return [VerifierFeedback(make_verifier_feedback_id("proof-system",x.result_id),VerifierFeedbackStatus.ADVISORY_ONLY,FlawSeverity.MAJOR,source_object_id=x.result_id,summary="proof-system check failed",metadata={"proof_system_advisory_only":True}) for x in r.check_results if x.status==CheckResultStatus.FAILED]
def proof_system_report_to_repair_traces(r): return [RepairLoopTrace(content_id("proof-system-repair",x.artifact_id),source_object_id=x.artifact_id,metadata={"proof_system_advisory_only":True}) for x in r.artifacts if x.has_placeholder()]
def proof_system_report_to_proof_digestion_inputs(r): return [{"artifact_id":a.artifact_id,"text":a.metadata.get("text"),"proof_system_advisory_only":True} for a in r.artifacts if a.artifact_kind in {ProofArtifactKind.PROOF_TEXT,ProofArtifactKind.THEOREM_FILE}]
def proof_system_report_to_structure_descriptors(r): return [structure_descriptor_from_mapping({"proof_system":s.kind.value,"file_extensions":list(s.file_extensions)},object_id=s.proof_system_id,object_kind=StructureObjectKind.FORMAL_WORLD) for s in r.specs]
def proof_system_report_to_typed_projection_candidates(r): return [TypedProjectionCandidate(make_typed_projection_candidate_id("proof-system",a.artifact_id),a.artifact_id,status=TypedProjectionStatus.NEEDS_REVIEW,compatibility=ProjectionCompatibility.NEEDS_FORMALIZATION,required_review=True,metadata={"proof_system_advisory_only":True}) for a in r.artifacts]
def proof_system_report_to_role_signatures(r): return [RoleSignature(make_role_signature_id("proof-system",a.artifact_id),RoleSourceKind.RAW_EVENT,a.artifact_id,RoleObjectKind.PROOF_SCHEMA_ROLE,(a.kind.value.lower(),a.artifact_kind.value.lower()),metadata={"proof_system_advisory_only":True}) for a in r.artifacts]
def proof_system_report_to_analogy_sources(r): return [analogy_source_from_mapping(a.to_dict(),source_kind=AnalogySourceKind.RAW_EVENT,object_id=a.artifact_id) for a in r.artifacts]
def proof_system_report_to_habit_observations(r): return [HabitObservation(content_id("proof-system-habit",a.artifact_id),HabitObservationKind.RAW_EVENT,route="proof_system_integration",outcome=HabitOutcome.ADVISORY_ONLY,object_id=a.artifact_id,metadata={"proof_system_advisory_only":True}) for a in r.artifacts]
def proof_system_report_to_reason_observations(r): return [ReasonObservation(make_reason_observation_id("proof-system",a.artifact_id),ReasonObservationKind.RAW_EVENT,a.artifact_id,"proof_system_integration",*extract_atoms_from_mapping(a.to_dict()),metadata={"proof_system_advisory_only":True}) for a in r.artifacts]
def proof_system_report_to_structural_identity_objects(r): return [{"artifact_id":a.artifact_id,"kind":a.kind.value,"imports":list(a.imports),"proof_system_advisory_only":True} for a in r.artifacts]
def proof_system_report_to_alchemical_trace(r):
 t=AlchemicalTrace(make_alchemical_trace_id("proof-system",r.report_id))
 for p in (AlchemicalPhase.RAW_MATTER,AlchemicalPhase.CALCINATION,AlchemicalPhase.SOLUTION,AlchemicalPhase.DESCENSION,AlchemicalPhase.DISTILLATION,AlchemicalPhase.COAGULATION): t.add_step(phase=p,status=AlchemicalStatus.ADVISORY_ONLY)
 if any(e.is_valid_boundary() for e in r.boundary_evidence): t.add_step(phase=AlchemicalPhase.FIXATION,status=AlchemicalStatus.PROMOTED_BY_VERIFIER,metadata={"verifier_boundary_crossed":True})
 return t
def proof_system_report_to_agent_experiences(r,agent_id=None): return [AgentExperience(content_id("proof-system-exp",a.artifact_id),agent_id or "proof-system-integration",None,None,"proof_system_integration",None,AgentExperienceOutcome.ADVISORY_ONLY,metadata={"artifact_id":a.artifact_id}) for a in r.artifacts]
def proof_system_report_to_route_telemetry_events(r): return [{"event_id":content_id("proof-system-telemetry",t.task_id),"route_kind":"proof_system_integration","outcome":t.task_kind.value,"proof_system_advisory_only":True} for t in r.tasks]
def audit_proof_system_spec(x): return [_f("CRITICAL","PROOF_SYSTEM_SPEC_NON_ADVISORY","proof-system spec non-advisory",x.proof_system_id)] if not x.advisory else []
def audit_proof_project_manifest(x): return [_f("CRITICAL","PROOF_PROJECT_NON_ADVISORY","project manifest non-advisory",x.project_id)] if not x.advisory else []
def audit_proof_artifact_manifest(x):
 out=[]
 if not x.advisory: out.append(_f("CRITICAL","PROOF_ARTIFACT_NON_ADVISORY","artifact manifest non-advisory",x.artifact_id))
 if x.has_placeholder() and x.status==ProofArtifactStatus.CHECK_PASSED: out.append(_f("CRITICAL","PROOF_PLACEHOLDER_PASSED","placeholder artifact treated as passed",x.artifact_id))
 if x.has_placeholder(): out.append(_f("WARNING","PROOF_PLACEHOLDER_DETECTED","placeholder detected",x.artifact_id))
 return out
def audit_proof_import_graph(x): return ([] if x.advisory else [_f("CRITICAL","PROOF_IMPORT_GRAPH_NON_ADVISORY","import graph non-advisory",x.graph_id)])+([_f("WARNING","PROOF_IMPORT_MISSING","missing import",x.graph_id)] if x.missing_imports else [])
def audit_proof_check_command_contract(x):
 out=[] if x.advisory else [_f("CRITICAL","PROOF_CONTRACT_NON_ADVISORY","check contract non-advisory",x.contract_id)]
 if x.allowed and not x.is_safe(): out.append(_f("CRITICAL","PROOF_UNSAFE_COMMAND","unsafe command contract",x.contract_id))
 return out
def audit_proof_check_request(x):
 out=[] if x.advisory else [_f("CRITICAL","PROOF_REQUEST_NON_ADVISORY","check request non-advisory",x.request_id)]
 if x.status in {CheckRequestStatus.BLOCKED_MISSING_ARTIFACT,CheckRequestStatus.BLOCKED_PLACEHOLDER,CheckRequestStatus.BLOCKED_UNSAFE_COMMAND}: out.append(_f("WARNING","PROOF_REQUEST_BLOCKED","check request blocked",x.request_id))
 return out
def audit_proof_check_result(x):
 out=[] if x.advisory else [_f("CRITICAL","PROOF_RESULT_NON_ADVISORY","check result non-advisory",x.result_id)]
 if x.status==CheckResultStatus.PASSED and ("sorry" in (x.stdout_excerpt or "").lower() or "admit" in (x.stdout_excerpt or "").lower()): out.append(_f("CRITICAL","PROOF_PLACEHOLDER_RESULT_PASSED","placeholder passed as check",x.result_id))
 if x.status==CheckResultStatus.PASSED and x.metadata.get("raw_success_text") and not x.crosses_boundary(): out.append(_f("CRITICAL","PROOF_RAW_SUCCESS_AS_BOUNDARY","raw success text without boundary",x.result_id))
 if x.verifier_boundary_crossed and not x.crosses_boundary(): out.append(_f("CRITICAL","PROOF_BAD_RESULT_BOUNDARY","check result boundary incomplete",x.result_id))
 return out
def audit_trusted_proof_import_record(x):
 out=[] if x.advisory else [_f("CRITICAL","TRUSTED_IMPORT_NON_ADVISORY","trusted import record non-advisory",x.import_id)]
 if x.status==TrustedImportStatus.ACCEPTED_WITH_BOUNDARY and not x.crosses_boundary(): out.append(_f("CRITICAL","TRUSTED_IMPORT_BAD_BOUNDARY","trusted import accepted without complete boundary",x.import_id))
 return out
def audit_proof_boundary_evidence(x): return [] if x.is_valid_boundary() else [_f("CRITICAL","PROOF_BOUNDARY_INVALID","proof boundary evidence invalid",x.evidence_id)]
def audit_proof_system_task(x):
 out=[] if x.advisory else [_f("CRITICAL","PROOF_TASK_NON_ADVISORY","proof-system task non-advisory",x.task_id)]
 if x.metadata.get("terminal_form") or x.metadata.get("certificate_id"): out.append(_f("CRITICAL","PROOF_TASK_AS_TRUTH","task carries truth fields",x.task_id))
 return out
def audit_proof_system_integration_report(r):
 out=[y for xs in (r.specs,r.projects,r.artifacts,r.import_graphs,r.command_contracts,r.check_requests,r.check_results,r.trusted_imports,r.boundary_evidence,r.tasks) for x in xs for y in (audit_proof_system_spec(x) if isinstance(x,ProofSystemSpec) else audit_proof_project_manifest(x) if isinstance(x,ProofProjectManifest) else audit_proof_artifact_manifest(x) if isinstance(x,ProofArtifactManifest) else audit_proof_import_graph(x) if isinstance(x,ProofImportGraph) else audit_proof_check_command_contract(x) if isinstance(x,ProofCheckCommandContract) else audit_proof_check_request(x) if isinstance(x,ProofCheckRequest) else audit_proof_check_result(x) if isinstance(x,ProofCheckResult) else audit_trusted_proof_import_record(x) if isinstance(x,TrustedProofImportRecord) else audit_proof_boundary_evidence(x) if isinstance(x,ProofBoundaryEvidence) else audit_proof_system_task(x))]
 if not r.advisory: out.append(_f("CRITICAL","PROOF_REPORT_NON_ADVISORY","proof-system report non-advisory",r.report_id))
 return out
def _task(a,k,b=ProofBoundaryKind.NONE): return ProofSystemTask(make_proof_system_task_id(a.artifact_id,k.value),k,a.proof_system_id,a.kind,a.artifact_id,title=k.value.replace("_"," ").title(),required_boundary=b)
def _term(x):
 if isinstance(x,TerminalForm): return x
 try:return TerminalForm(str(x)) if x else None
 except ValueError:return None
def _s(x): return None if x is None else str(x)
def _now(): return datetime.now(timezone.utc).isoformat()
def _j(x): return json.dumps(x,sort_keys=True,separators=(",",":"),default=str)
def _w(p,t): path=Path(p); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(t,encoding="utf-8")
def _f(sev,code,msg,obj): return {"severity":sev,"code":code,"message":msg,"object_id":obj}
