"""Advisory role-based object introduction for recurring MathGraph structure."""
from __future__ import annotations
import json,re
from collections import Counter,defaultdict
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
from mathgraph.lawbook import LawbookEntry,LawbookEntryKind,LawbookEntryStatus,LawbookStore,make_lawbook_entry_id
from mathgraph.process_memory import ProcessContextItem,ProcessContextKind,ProcessContextRole,ProcessEpisodeRecord,ProcessEpisodeStatus,make_process_episode_id
from mathgraph.reason_compression import ReasonObservation,ReasonObservationKind,extract_atoms_from_mapping,make_reason_observation_id
from mathgraph.structure_registry import StructureDescriptor,StructureMapping,StructureObjectKind,StructureRegistryReport,TypedProjectionCandidate,ProjectionCompatibility,TypedProjectionStatus,structure_descriptor_from_mapping,make_typed_projection_candidate_id
def _enum(n,v): return Enum(n,{x:x for x in v.split()},type=str)
RoleSourceKind=_enum("RoleSourceKind","STRUCTURE_DESCRIPTOR STRUCTURE_MAPPING TYPED_PROJECTION REASON HABIT PROCESS_MEMORY LAWBOOK_ENTRY LAWBOOK_QUERY PROJECTION STRUCTURAL_IDENTITY PROOF_DIGESTION VERIFIER_FEEDBACK REPAIR_LOOP CURRICULUM ALCHEMICAL_TRACE AGENT_EXPERIENCE ROUTE_TELEMETRY RAW_EVENT UNKNOWN")
RoleConditionKind=_enum("RoleConditionKind","STRUCTURE_FAMILY STRUCTURE_FEATURE SHARED_FEATURE LOAD_BEARING_ATOM HABIT_CONDITION PROCESS_CONTEXT ELIMINATION_PATTERN PROJECTION_COMPATIBILITY TERMINAL_FORM_PATTERN WITNESS_PATTERN ROUTE_PATTERN COST_PATTERN RISK_PATTERN TYPE_REQUIREMENT FORMALIZATION_REQUIREMENT ADAPTER_REQUIREMENT UNKNOWN")
RoleObjectKind=_enum("RoleObjectKind","ABSTRACT_STRUCTURE CONSTRUCTOR_ROLE OBSTRUCTION_ROLE PROOF_SCHEMA_ROLE PROJECTION_ROLE ROUTE_POLICY_ROLE WITNESS_ROLE COUNTERMODEL_ROLE DIGESTION_ROLE REPAIR_ROLE PROCESS_ROLE MIXED_ROLE UNKNOWN")
RoleCandidateStatus=_enum("RoleCandidateStatus","CANDIDATE SUPPORTED HAS_WITNESSES NEEDS_WITNESSES NEEDS_FORMALIZATION NEEDS_ADAPTER NEEDS_REVIEW ACCEPTED_ADVISORY REJECTED BLOCKED_CONFLICT HELD_IN_CHORA UNKNOWN")
RoleWitnessStatus=_enum("RoleWitnessStatus","CANDIDATE VERIFIED_EXISTING_CERTIFICATE FINITE_VALIDATION_REQUIRED PROOF_REQUIRED COUNTERMODEL_REQUIRED NEEDS_REVIEW REJECTED UNKNOWN")
RoleConjectureKind=_enum("RoleConjectureKind","PROOF_TASK COUNTERMODEL_TASK WITNESS_SEARCH_TASK FORMALIZATION_TASK ADAPTER_TASK PROJECTION_TASK DIGESTION_TASK REPAIR_TASK REVIEW_TASK UNKNOWN")
RoleReviewDecision=_enum("RoleReviewDecision","ACCEPT_ADVISORY REJECT NEEDS_MORE_SUPPORT NEEDS_WITNESSES NEEDS_FORMALIZATION NEEDS_ADAPTER NEEDS_LOWER_COMPLEXITY NEEDS_CONFLICT_RESOLUTION HOLD_IN_CHORA UNKNOWN")
RoleObjectReportStatus=_enum("RoleObjectReportStatus","EMPTY SIGNATURES_FOUND DEFINITIONS_FOUND WITNESSES_FOUND CONJECTURES_FOUND REVIEWED ACCEPTED_ROLES HAS_WARNINGS HAS_CRITICALS ADVISORY_ONLY")
@dataclass
class RoleSignature:
 signature_id:str; source_kind:RoleSourceKind; source_object_id:str|None=None; role_kind:RoleObjectKind=RoleObjectKind.UNKNOWN; condition_atoms:tuple[str,...]=(); condition_kinds:dict[str,str]=field(default_factory=dict); structure_families:tuple[str,...]=(); structure_features:tuple[str,...]=(); routes:tuple[str,...]=(); terminal_patterns:tuple[str,...]=(); support_object_ids:tuple[str,...]=(); support_count:int=0; risk_score:float=0.0; gain_score:float=0.0; complexity:int=0; confidence:float=0.0; warnings:tuple[str,...]=(); criticals:tuple[str,...]=(); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def to_dict(self): return {**self.__dict__,"source_kind":self.source_kind.value,"role_kind":self.role_kind.value,"condition_atoms":list(self.condition_atoms),"structure_families":list(self.structure_families),"structure_features":list(self.structure_features),"routes":list(self.routes),"terminal_patterns":list(self.terminal_patterns),"support_object_ids":list(self.support_object_ids),"warnings":list(self.warnings),"criticals":list(self.criticals)}
 @classmethod
 def from_dict(c,d): return c(str(d["signature_id"]),RoleSourceKind(str(d.get("source_kind","UNKNOWN"))),_s(d.get("source_object_id")),RoleObjectKind(str(d.get("role_kind","UNKNOWN"))),tuple(d.get("condition_atoms",())),dict(d.get("condition_kinds",{})),tuple(d.get("structure_families",())),tuple(d.get("structure_features",())),tuple(d.get("routes",())),tuple(d.get("terminal_patterns",())),tuple(d.get("support_object_ids",())),int(d.get("support_count",0)),float(d.get("risk_score",0)),float(d.get("gain_score",0)),int(d.get("complexity",0)),float(d.get("confidence",0)),tuple(d.get("warnings",())),tuple(d.get("criticals",())),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
@dataclass
class RoleDefinitionCandidate:
 candidate_id:str; role_kind:RoleObjectKind; proposed_name:str; description:str|None=None; defining_conditions:tuple[str,...]=(); optional_conditions:tuple[str,...]=(); excluded_conditions:tuple[str,...]=(); source_signature_ids:tuple[str,...]=(); support_count:int=0; witness_count:int=0; conjecture_count:int=0; complexity:int=0; confidence:float=0.0; risk_score:float=0.0; status:RoleCandidateStatus=RoleCandidateStatus.CANDIDATE; warnings:tuple[str,...]=(); criticals:tuple[str,...]=(); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def is_promotable(self,min_support=3,min_confidence=.4,max_complexity=10,max_risk=.5,require_witness=True): return self.advisory and not self.criticals and self.support_count>=min_support and self.confidence>=min_confidence and self.complexity<=max_complexity and self.risk_score<=max_risk and (not require_witness or self.witness_count>0)
 def to_dict(self): return {**self.__dict__,"role_kind":self.role_kind.value,"defining_conditions":list(self.defining_conditions),"optional_conditions":list(self.optional_conditions),"excluded_conditions":list(self.excluded_conditions),"source_signature_ids":list(self.source_signature_ids),"status":self.status.value,"warnings":list(self.warnings),"criticals":list(self.criticals)}
 @classmethod
 def from_dict(c,d): return c(str(d["candidate_id"]),RoleObjectKind(str(d.get("role_kind","UNKNOWN"))),str(d["proposed_name"]),_s(d.get("description")),tuple(d.get("defining_conditions",())),tuple(d.get("optional_conditions",())),tuple(d.get("excluded_conditions",())),tuple(d.get("source_signature_ids",())),int(d.get("support_count",0)),int(d.get("witness_count",0)),int(d.get("conjecture_count",0)),int(d.get("complexity",0)),float(d.get("confidence",0)),float(d.get("risk_score",0)),RoleCandidateStatus(str(d.get("status","CANDIDATE"))),tuple(d.get("warnings",())),tuple(d.get("criticals",())),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
@dataclass
class RoleWitnessCandidate:
 witness_id:str; role_candidate_id:str; source_object_id:str|None=None; source_kind:RoleSourceKind=RoleSourceKind.UNKNOWN; witness_status:RoleWitnessStatus=RoleWitnessStatus.CANDIDATE; witness_summary:str|None=None; certificate_id:str|None=None; terminal_form:TerminalForm|None=None; verifier_boundary_crossed:bool=False; conditions_satisfied:tuple[str,...]=(); conditions_missing:tuple[str,...]=(); confidence:float=0.0; warnings:tuple[str,...]=(); criticals:tuple[str,...]=(); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def has_verified_boundary(self): return bool(self.certificate_id and self.terminal_form and self.verifier_boundary_crossed)
 def to_dict(self): return {**self.__dict__,"source_kind":self.source_kind.value,"witness_status":self.witness_status.value,"terminal_form":self.terminal_form.value if self.terminal_form else None,"conditions_satisfied":list(self.conditions_satisfied),"conditions_missing":list(self.conditions_missing),"warnings":list(self.warnings),"criticals":list(self.criticals)}
 @classmethod
 def from_dict(c,d): return c(str(d["witness_id"]),str(d["role_candidate_id"]),_s(d.get("source_object_id")),RoleSourceKind(str(d.get("source_kind","UNKNOWN"))),RoleWitnessStatus(str(d.get("witness_status","CANDIDATE"))),_s(d.get("witness_summary")),_s(d.get("certificate_id")),TerminalForm(str(d["terminal_form"])) if d.get("terminal_form") else None,bool(d.get("verifier_boundary_crossed",False)),tuple(d.get("conditions_satisfied",())),tuple(d.get("conditions_missing",())),float(d.get("confidence",0)),tuple(d.get("warnings",())),tuple(d.get("criticals",())),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
@dataclass
class RoleConjectureCandidate:
 conjecture_id:str; role_candidate_id:str; kind:RoleConjectureKind; statement:str|None=None; source_object_id:str|None=None; target_object_id:str|None=None; route:str|None=None; priority:float=0.0; required_adapter:str|None=None; required_formalization:bool=False; required_review:bool=True; warnings:tuple[str,...]=(); criticals:tuple[str,...]=(); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def to_dict(self): return {**self.__dict__,"kind":self.kind.value,"warnings":list(self.warnings),"criticals":list(self.criticals)}
 @classmethod
 def from_dict(c,d): return c(str(d["conjecture_id"]),str(d["role_candidate_id"]),RoleConjectureKind(str(d.get("kind","UNKNOWN"))),_s(d.get("statement")),_s(d.get("source_object_id")),_s(d.get("target_object_id")),_s(d.get("route")),float(d.get("priority",0)),_s(d.get("required_adapter")),bool(d.get("required_formalization",False)),bool(d.get("required_review",True)),tuple(d.get("warnings",())),tuple(d.get("criticals",())),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
@dataclass
class RoleObject:
 role_id:str; role_kind:RoleObjectKind; name:str; description:str|None=None; defining_conditions:tuple[str,...]=(); optional_conditions:tuple[str,...]=(); excluded_conditions:tuple[str,...]=(); source_candidate_id:str|None=None; witness_ids:tuple[str,...]=(); conjecture_ids:tuple[str,...]=(); support_count:int=0; confidence:float=0.0; risk_score:float=0.0; accepted_at:str|None=None; accepted_by:str|None=None; status:RoleCandidateStatus=RoleCandidateStatus.ACCEPTED_ADVISORY; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def is_accepted(self): return self.status==RoleCandidateStatus.ACCEPTED_ADVISORY
 def matches(self,m): return bool(self.defining_conditions) and any(x in _j(dict(m)).lower() for x in self.defining_conditions)
 def to_dict(self): return {**self.__dict__,"role_kind":self.role_kind.value,"defining_conditions":list(self.defining_conditions),"optional_conditions":list(self.optional_conditions),"excluded_conditions":list(self.excluded_conditions),"witness_ids":list(self.witness_ids),"conjecture_ids":list(self.conjecture_ids),"status":self.status.value}
 @classmethod
 def from_dict(c,d): return c(str(d["role_id"]),RoleObjectKind(str(d.get("role_kind","UNKNOWN"))),str(d["name"]),_s(d.get("description")),tuple(d.get("defining_conditions",())),tuple(d.get("optional_conditions",())),tuple(d.get("excluded_conditions",())),_s(d.get("source_candidate_id")),tuple(d.get("witness_ids",())),tuple(d.get("conjecture_ids",())),int(d.get("support_count",0)),float(d.get("confidence",0)),float(d.get("risk_score",0)),_s(d.get("accepted_at")),_s(d.get("accepted_by")),RoleCandidateStatus(str(d.get("status","ACCEPTED_ADVISORY"))),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
@dataclass
class RoleReview:
 review_id:str; role_candidate_id:str; decision:RoleReviewDecision; reviewer:str|None=None; reason:str|None=None; required_evidence:tuple[str,...]=(); created_at:str=field(default_factory=lambda:_now()); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def to_dict(self): return {**self.__dict__,"decision":self.decision.value,"required_evidence":list(self.required_evidence)}
 @classmethod
 def from_dict(c,d): return c(str(d["review_id"]),str(d["role_candidate_id"]),RoleReviewDecision(str(d.get("decision","UNKNOWN"))),_s(d.get("reviewer")),_s(d.get("reason")),tuple(d.get("required_evidence",())),str(d.get("created_at") or _now()),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
@dataclass
class RoleObjectReport:
 report_id:str; signatures:list[RoleSignature]=field(default_factory=list); definition_candidates:list[RoleDefinitionCandidate]=field(default_factory=list); witness_candidates:list[RoleWitnessCandidate]=field(default_factory=list); conjecture_candidates:list[RoleConjectureCandidate]=field(default_factory=list); reviews:list[RoleReview]=field(default_factory=list); role_objects:list[RoleObject]=field(default_factory=list); status:RoleObjectReportStatus=RoleObjectReportStatus.EMPTY; created_at:str=field(default_factory=lambda:_now()); summary:dict[str,Any]=field(default_factory=dict); metadata:dict[str,Any]=field(default_factory=lambda:{"role_advisory_only":True}); advisory:bool=True
 def signature_count(self): return len(self.signatures)
 def candidate_count(self): return len(self.definition_candidates)
 def witness_count(self): return len(self.witness_candidates)
 def conjecture_count(self): return len(self.conjecture_candidates)
 def accepted_role_count(self): return sum(x.is_accepted() for x in self.role_objects)
 def critical_count(self): return sum(len(x.criticals) for x in self.signatures+self.definition_candidates+self.witness_candidates+self.conjecture_candidates)
 def summarize(self): self.summary={"signature_total":len(self.signatures),"definition_total":len(self.definition_candidates),"witness_total":len(self.witness_candidates),"conjecture_total":len(self.conjecture_candidates),"review_total":len(self.reviews),"role_total":len(self.role_objects),"accepted_role_count":self.accepted_role_count(),"critical_count":self.critical_count()}; return dict(self.summary)
 def to_dict(self): return {"report_id":self.report_id,"signatures":[x.to_dict() for x in self.signatures],"definition_candidates":[x.to_dict() for x in self.definition_candidates],"witness_candidates":[x.to_dict() for x in self.witness_candidates],"conjecture_candidates":[x.to_dict() for x in self.conjecture_candidates],"reviews":[x.to_dict() for x in self.reviews],"role_objects":[x.to_dict() for x in self.role_objects],"status":self.status.value,"created_at":self.created_at,"summary":dict(self.summary),"metadata":dict(self.metadata),"advisory":self.advisory}
 @classmethod
 def from_dict(c,d): return c(str(d["report_id"]),[RoleSignature.from_dict(x) for x in d.get("signatures",[])],[RoleDefinitionCandidate.from_dict(x) for x in d.get("definition_candidates",[])],[RoleWitnessCandidate.from_dict(x) for x in d.get("witness_candidates",[])],[RoleConjectureCandidate.from_dict(x) for x in d.get("conjecture_candidates",[])],[RoleReview.from_dict(x) for x in d.get("reviews",[])],[RoleObject.from_dict(x) for x in d.get("role_objects",[])],RoleObjectReportStatus(str(d.get("status","EMPTY"))),str(d.get("created_at") or _now()),dict(d.get("summary",{})),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
 def write_json(self,p): _w(p,self.to_json()+"\n")
 @classmethod
 def read_json(c,p): return c.from_json(Path(p).read_text())
 def write_jsonl(self,p): _w(p,self.to_json()+"\n")
 @classmethod
 def read_jsonl(c,p): return [c.from_json(x) for x in Path(p).read_text().splitlines() if x.strip()]
def make_role_signature_id(*x): return content_id("role-signature",x)
def make_role_definition_candidate_id(*x): return content_id("role-definition",x)
def make_role_witness_candidate_id(*x): return content_id("role-witness",x)
def make_role_conjecture_candidate_id(*x): return content_id("role-conjecture",x)
def make_role_object_id(*x): return content_id("role-object",x)
def make_role_review_id(*x): return content_id("role-review",x)
def make_role_object_report_id(*x): return content_id("role-report",x)
def normalize_role_atom(v):
 s=re.sub(r"[^a-z0-9_:/=\\-]+","_",str(v).strip().lower().replace(" ","_")).strip("_")
 return s[:80]+"_"+content_id("role-atom",s)[-8:] if len(s)>96 else s or "unknown"
def classify_role_condition(a,source_key=None):
 t=(str(source_key or "")+" "+a).lower()
 rules=[(("projection","compatibility"),"PROJECTION_COMPATIBILITY"),(("verified_proof","finite_countermodel","named_obstruction"),"TERMINAL_FORM_PATTERN"),(("witness","example","table"),"WITNESS_PATTERN"),(("load_bearing","reason"),"LOAD_BEARING_ATOM"),(("habit","condition"),"HABIT_CONDITION"),(("process","context"),"PROCESS_CONTEXT"),(("elimination","killed","failed"),"ELIMINATION_PATTERN"),(("route","scheduler"),"ROUTE_PATTERN"),(("formalization",),"FORMALIZATION_REQUIREMENT"),(("adapter",),"ADAPTER_REQUIREMENT"),(("cost",),"COST_PATTERN"),(("risk",),"RISK_PATTERN"),(("family","algebraic","order","topological","logical","computational"),"STRUCTURE_FAMILY"),(("feature","operation","relation","closure","quotient","transition"),"STRUCTURE_FEATURE"),(("shared",),"SHARED_FEATURE"),(("type",),"TYPE_REQUIREMENT")]
 for keys,k in rules:
  if any(x in t for x in keys): return RoleConditionKind(k)
 return RoleConditionKind.UNKNOWN
def extract_role_conditions_from_mapping(d,*,max_depth=4,max_items=200):
 out=[]; kinds={}
 def walk(x,key=None,depth=0):
  if depth>max_depth or len(out)>=max_items:return
  if isinstance(x,Mapping):
   for k,v in x.items():
    a=normalize_role_atom(k); out.append(a); kinds[a]=classify_role_condition(a,str(k)).value; walk(v,str(k),depth+1)
  elif isinstance(x,(list,tuple,set)):
   for v in list(x)[:max_items]: walk(v,key,depth+1)
  else:
   a=normalize_role_atom(getattr(x,"value",x)); out.append(a); kinds[a]=classify_role_condition(a,key).value
 walk(d); return tuple(dict.fromkeys(out)),kinds
def infer_role_kind(atoms,kinds,metadata=None):
 t=" ".join(atoms)
 hits=[]
 for keys,k in ((("constructor","generation"),"CONSTRUCTOR_ROLE"),(("obstruction","failure","killed","blocked"),"OBSTRUCTION_ROLE"),(("proof","theorem","lemma","digestion_schema"),"PROOF_SCHEMA_ROLE"),(("projection","compatibility","typed_projection"),"PROJECTION_ROLE"),(("habit","route_policy","scheduler"),"ROUTE_POLICY_ROLE"),(("witness","example","table"),"WITNESS_ROLE"),(("countermodel","finite_countermodel"),"COUNTERMODEL_ROLE"),(("digestion","exposition","key_idea"),"DIGESTION_ROLE"),(("repair","feedback","flaw"),"REPAIR_ROLE"),(("process","transition","elimination"),"PROCESS_ROLE")):
  if any(x in t for x in keys): hits.append(k)
 if len(set(hits))>1:return RoleObjectKind.MIXED_ROLE
 if hits:return RoleObjectKind(hits[0])
 return RoleObjectKind.ABSTRACT_STRUCTURE if any(v in kinds.values() for v in ("STRUCTURE_FAMILY","STRUCTURE_FEATURE")) else RoleObjectKind.UNKNOWN
def propose_role_name(kind,atoms):
 base=kind.value.lower()
 useful=[a for a in atoms if a not in {"unknown","status","metadata"}][:3]
 return "_".join([base]+useful) if useful else base
def role_signature_from_mapping(d,*,source_kind=RoleSourceKind.RAW_EVENT,source_object_id=None):
 atoms,kinds=extract_role_conditions_from_mapping(d); kind=infer_role_kind(atoms,kinds,d)
 return RoleSignature(make_role_signature_id(source_kind.value,source_object_id,atoms),source_kind,source_object_id,kind,atoms,kinds,tuple(a for a,k in kinds.items() if k=="STRUCTURE_FAMILY"),tuple(a for a,k in kinds.items() if k=="STRUCTURE_FEATURE"),tuple(a for a,k in kinds.items() if k=="ROUTE_PATTERN"),tuple(a for a,k in kinds.items() if k=="TERMINAL_FORM_PATTERN"),(source_object_id,) if source_object_id else (),1,float(d.get("risk_score",0) or 0),float(d.get("gain_score",d.get("gain_units",0)) or 0),len(atoms),min(1,.2+.05*len(atoms)),metadata=dict(d) if isinstance(d,Mapping) else {},advisory=True)
def _sig(o,k,oid=None): return role_signature_from_mapping(o.to_dict() if hasattr(o,"to_dict") else dict(o),source_kind=k,source_object_id=oid or getattr(o,"descriptor_id",getattr(o,"mapping_id",getattr(o,"candidate_id",getattr(o,"reason_id",getattr(o,"rule_id",getattr(o,"episode_id",getattr(o,"entry_id",None))))))))
def role_signature_from_structure_descriptor(x): return _sig(x,RoleSourceKind.STRUCTURE_DESCRIPTOR,x.descriptor_id)
def role_signature_from_structure_mapping(x): return _sig(x,RoleSourceKind.STRUCTURE_MAPPING,x.mapping_id)
def role_signature_from_typed_projection(x): return _sig(x,RoleSourceKind.TYPED_PROJECTION,x.candidate_id)
def role_signatures_from_structure_report(x): return [role_signature_from_structure_descriptor(d) for d in x.descriptors]+[role_signature_from_structure_mapping(m) for m in x.mappings]+[role_signature_from_typed_projection(c) for c in x.typed_projection_candidates]
def role_signature_from_reason_candidate(x): return _sig(x,RoleSourceKind.REASON,x.candidate_id)
def role_signature_from_reason_node(x): return _sig(x,RoleSourceKind.REASON,x.reason_id)
def role_signatures_from_reason_report(x): return [role_signature_from_reason_candidate(c) for c in x.candidates]+[role_signature_from_reason_node(n) for n in x.reason_nodes]
def role_signature_from_habit_rule(x): return _sig(x,RoleSourceKind.HABIT,x.rule_id)
def role_signatures_from_habit_report(x): return [role_signature_from_habit_rule(r) for r in x.rules]
def role_signature_from_process_episode(x): return _sig(x,RoleSourceKind.PROCESS_MEMORY,x.episode_id)
def role_signatures_from_process_report(x): return [role_signature_from_process_episode(e) for e in (x.store.episodes if x.store else [])]
def role_signature_from_lawbook_entry(x): return _sig(x,RoleSourceKind.LAWBOOK_ENTRY,x.entry_id)
def role_signatures_from_lawbook_store(x): return [role_signature_from_lawbook_entry(e) for e in x.entries]
def role_signatures_from_lawbook_query_report(x): return [_sig(a,RoleSourceKind.LAWBOOK_QUERY,a.answer_id) for a in x.answers]
def role_signature_from_projection_candidate(x): return _sig(x,RoleSourceKind.PROJECTION,x.candidate_id)
def role_signatures_from_projection_candidates(xs): return [role_signature_from_projection_candidate(x) for x in xs]
def role_signatures_from_structural_identity_report(x): return [_sig(c,RoleSourceKind.STRUCTURAL_IDENTITY,c.candidate_id) for c in x.merge_candidates]
def role_signature_from_proof_digestion_trace(x): return _sig(x,RoleSourceKind.PROOF_DIGESTION,x.trace_id)
def role_signature_from_verifier_feedback(x): return _sig(x,RoleSourceKind.VERIFIER_FEEDBACK,x.feedback_id)
def role_signature_from_repair_loop(x): return _sig(x,RoleSourceKind.REPAIR_LOOP,x.trace_id)
def role_signatures_from_curriculum(x): return [role_signature_from_curriculum_stage(s) for s in x.stages]
def role_signature_from_curriculum_stage(x): return _sig(x,RoleSourceKind.CURRICULUM,x.stage_id)
def role_signature_from_alchemical_trace(x): return _sig(x,RoleSourceKind.ALCHEMICAL_TRACE,x.trace_id)
def role_signature_from_agent_experience(x): return _sig(x,RoleSourceKind.AGENT_EXPERIENCE,x.experience_id)
def role_signature_from_route_telemetry_event(x): return role_signature_from_mapping(x,source_kind=RoleSourceKind.ROUTE_TELEMETRY,source_object_id=_s(x.get("event_id")))
def role_signatures_from_object(o):
 from mathgraph.habit_rules import HabitFormationReport,HabitRule
 from mathgraph.lawbook_query import LawbookQueryReport
 from mathgraph.projection import ProjectionCandidate
 from mathgraph.proof_digestion import ProofDigestionTrace
 from mathgraph.reason_compression import ReasonCandidate,ReasonCompressionReport,ReasonNode
 from mathgraph.structural_identity import StructuralIdentityReport
 from mathgraph.verifier_feedback import RepairLoopTrace,VerifierFeedback
 if isinstance(o,RoleSignature): return [o]
 if isinstance(o,StructureRegistryReport): return role_signatures_from_structure_report(o)
 if isinstance(o,StructureDescriptor): return [role_signature_from_structure_descriptor(o)]
 if isinstance(o,StructureMapping): return [role_signature_from_structure_mapping(o)]
 if isinstance(o,TypedProjectionCandidate): return [role_signature_from_typed_projection(o)]
 if isinstance(o,ReasonCompressionReport): return role_signatures_from_reason_report(o)
 if isinstance(o,ReasonCandidate): return [role_signature_from_reason_candidate(o)]
 if isinstance(o,ReasonNode): return [role_signature_from_reason_node(o)]
 if isinstance(o,HabitFormationReport): return role_signatures_from_habit_report(o)
 if isinstance(o,HabitRule): return [role_signature_from_habit_rule(o)]
 if hasattr(o,"store") and o.__class__.__name__=="ProcessMemoryReport": return role_signatures_from_process_report(o)
 if isinstance(o,ProcessEpisodeRecord): return [role_signature_from_process_episode(o)]
 if isinstance(o,LawbookEntry): return [role_signature_from_lawbook_entry(o)]
 if isinstance(o,LawbookStore): return role_signatures_from_lawbook_store(o)
 if isinstance(o,LawbookQueryReport): return role_signatures_from_lawbook_query_report(o)
 if isinstance(o,ProjectionCandidate): return [role_signature_from_projection_candidate(o)]
 if isinstance(o,StructuralIdentityReport): return role_signatures_from_structural_identity_report(o)
 if isinstance(o,ProofDigestionTrace): return [role_signature_from_proof_digestion_trace(o)]
 if isinstance(o,VerifierFeedback): return [role_signature_from_verifier_feedback(o)]
 if isinstance(o,RepairLoopTrace): return [role_signature_from_repair_loop(o)]
 if isinstance(o,ContinuationCurriculum): return role_signatures_from_curriculum(o)
 if isinstance(o,CurriculumStage): return [role_signature_from_curriculum_stage(o)]
 if isinstance(o,AlchemicalTrace): return [role_signature_from_alchemical_trace(o)]
 if isinstance(o,AgentExperience): return [role_signature_from_agent_experience(o)]
 if isinstance(o,Mapping): return [role_signature_from_route_telemetry_event(o)]
 return []
def build_role_definition_candidates(sigs,*,min_support=2,max_conditions=8,max_candidates=300):
 groups=defaultdict(list)
 for s in sigs: groups[s.role_kind].append(s)
 out=[]
 for kind,xs in groups.items():
  if kind==RoleObjectKind.UNKNOWN: continue
  cnt=Counter(a for s in xs for a in s.condition_atoms); defining=tuple(a for a,n in cnt.most_common(max_conditions) if n>=max(1,len(xs)//2)); optional=tuple(a for a,n in cnt.items() if n>=1 and a not in defining)[:max_conditions]; excluded=tuple(a for a in optional if any(k in a for k in ("conflict","blocked","high_risk")))
  support=len(xs); witnesses=sum(any(k in s.condition_kinds.values() for k in ("WITNESS_PATTERN","TERMINAL_FORM_PATTERN")) for s in xs); risk=sum(s.risk_score for s in xs)/support; conf=min(1,.2+.15*support+.1*witnesses-.2*risk); status=RoleCandidateStatus.SUPPORTED if support>=min_support else RoleCandidateStatus.CANDIDATE
  if not witnesses: status=RoleCandidateStatus.NEEDS_WITNESSES
  if any("adapter" in a for a in defining+optional): status=RoleCandidateStatus.NEEDS_ADAPTER
  if any("formalization" in a for a in defining+optional): status=RoleCandidateStatus.NEEDS_FORMALIZATION
  if excluded: status=RoleCandidateStatus.BLOCKED_CONFLICT
  c=RoleDefinitionCandidate(make_role_definition_candidate_id(kind.value,defining),kind,propose_role_name(kind,defining or optional),defining_conditions=defining,optional_conditions=optional,excluded_conditions=excluded,source_signature_ids=tuple(s.signature_id for s in xs),support_count=support,witness_count=witnesses,complexity=len(defining)+len(optional)+len(excluded),confidence=conf,risk_score=risk,status=status,warnings=tuple(x for x,ok in (("low support",support<3),("no witness",not witnesses),("high risk",risk>.5),("unclear role kind",kind==RoleObjectKind.UNKNOWN)) if ok),metadata={"role_advisory_only":True})
  out.append(c)
 return out[:max_candidates]
def build_role_witness_candidates(defs,sigs):
 out=[]
 for d in defs:
  for s in sigs:
   sat=tuple(a for a in d.defining_conditions if a in s.condition_atoms)
   if not sat: continue
   miss=tuple(a for a in d.defining_conditions if a not in s.condition_atoms); md=s.metadata; cert=_s(md.get("certificate_id")); tf=_term(md.get("terminal_form")); vb=bool(md.get("verifier_boundary_crossed",False)); status=RoleWitnessStatus.VERIFIED_EXISTING_CERTIFICATE if cert and tf and vb else RoleWitnessStatus.COUNTERMODEL_REQUIRED if d.role_kind==RoleObjectKind.COUNTERMODEL_ROLE else RoleWitnessStatus.PROOF_REQUIRED if d.role_kind==RoleObjectKind.PROOF_SCHEMA_ROLE else RoleWitnessStatus.CANDIDATE
   out.append(RoleWitnessCandidate(make_role_witness_candidate_id(d.candidate_id,s.signature_id),d.candidate_id,s.source_object_id,s.source_kind,status,certificate_id=cert,terminal_form=tf,verifier_boundary_crossed=vb,conditions_satisfied=sat,conditions_missing=miss,confidence=len(sat)/max(1,len(d.defining_conditions)),metadata={"role_advisory_only":True}))
 return out
def build_role_conjecture_candidates(defs,wits):
 out=[]
 for d in defs:
  mine=[w for w in wits if w.role_candidate_id==d.candidate_id]
  kinds=[]
  if not mine:kinds.append(RoleConjectureKind.WITNESS_SEARCH_TASK)
  if d.role_kind in {RoleObjectKind.PROOF_SCHEMA_ROLE,RoleObjectKind.ABSTRACT_STRUCTURE}: kinds.append(RoleConjectureKind.PROOF_TASK)
  if d.role_kind in {RoleObjectKind.OBSTRUCTION_ROLE,RoleObjectKind.COUNTERMODEL_ROLE}: kinds.append(RoleConjectureKind.COUNTERMODEL_TASK)
  if d.status==RoleCandidateStatus.NEEDS_FORMALIZATION:kinds.append(RoleConjectureKind.FORMALIZATION_TASK)
  if d.status==RoleCandidateStatus.NEEDS_ADAPTER:kinds.append(RoleConjectureKind.ADAPTER_TASK)
  if d.role_kind==RoleObjectKind.PROJECTION_ROLE:kinds.append(RoleConjectureKind.PROJECTION_TASK)
  for k in kinds or [RoleConjectureKind.REVIEW_TASK]:
   out.append(RoleConjectureCandidate(make_role_conjecture_candidate_id(d.candidate_id,k.value),d.candidate_id,k,f"Investigate role {d.proposed_name} under conditions: {', '.join(d.defining_conditions)}",priority=d.confidence,required_adapter="formal-world adapter" if k==RoleConjectureKind.ADAPTER_TASK else None,required_formalization=k==RoleConjectureKind.FORMALIZATION_TASK,metadata={"role_advisory_only":True}))
  d.conjecture_count=len([x for x in out if x.role_candidate_id==d.candidate_id])
 return out
def review_role_definition_candidate(c,witnesses=(),*,reviewer=None,min_support=3,min_confidence=.4,max_complexity=10,max_risk=.5,require_witness=True):
 mine=[w for w in witnesses if w.role_candidate_id==c.candidate_id]
 if not c.advisory or c.criticals: d=RoleReviewDecision.REJECT
 elif c.status==RoleCandidateStatus.BLOCKED_CONFLICT: d=RoleReviewDecision.NEEDS_CONFLICT_RESOLUTION
 elif c.support_count<min_support: d=RoleReviewDecision.NEEDS_MORE_SUPPORT
 elif require_witness and not mine: d=RoleReviewDecision.NEEDS_WITNESSES
 elif c.status==RoleCandidateStatus.NEEDS_FORMALIZATION: d=RoleReviewDecision.NEEDS_FORMALIZATION
 elif c.status==RoleCandidateStatus.NEEDS_ADAPTER: d=RoleReviewDecision.NEEDS_ADAPTER
 elif c.complexity>max_complexity: d=RoleReviewDecision.NEEDS_LOWER_COMPLEXITY
 elif c.confidence>=min_confidence and c.risk_score<=max_risk: d=RoleReviewDecision.ACCEPT_ADVISORY
 else: d=RoleReviewDecision.HOLD_IN_CHORA
 return RoleReview(make_role_review_id(c.candidate_id,d.value),c.candidate_id,d,reviewer,required_evidence=c.warnings)
def promote_role_definition_candidate(c,r,witnesses=(),conjectures=(),*,accepted_by=None):
 if r.decision==RoleReviewDecision.ACCEPT_ADVISORY and c.criticals: raise ValueError("critical role")
 ok=r.decision==RoleReviewDecision.ACCEPT_ADVISORY
 return RoleObject(make_role_object_id(c.candidate_id,r.review_id),c.role_kind,c.proposed_name,c.description,c.defining_conditions,c.optional_conditions,c.excluded_conditions,c.candidate_id,tuple(w.witness_id for w in witnesses if w.role_candidate_id==c.candidate_id),tuple(x.conjecture_id for x in conjectures if x.role_candidate_id==c.candidate_id),c.support_count,c.confidence,c.risk_score,_now() if ok else None,accepted_by,RoleCandidateStatus.ACCEPTED_ADVISORY if ok else RoleCandidateStatus.REJECTED if r.decision==RoleReviewDecision.REJECT else RoleCandidateStatus.NEEDS_REVIEW,{"role_object_not_truth":True},True)
def build_role_object_report(objects=(),signatures=(),*,auto_definitions=True,auto_witnesses=True,auto_conjectures=True,auto_review=True,auto_promote=False,reviewer=None,min_support=3,min_confidence=.4,max_complexity=10,max_risk=.5,require_witness=True):
 sigs=list(signatures)+[x for o in objects for x in role_signatures_from_object(o)]; defs=build_role_definition_candidates(sigs,min_support=min(2,min_support)) if auto_definitions else []; wits=build_role_witness_candidates(defs,sigs) if auto_witnesses else []
 for d in defs: d.witness_count=len([w for w in wits if w.role_candidate_id==d.candidate_id])
 conjs=build_role_conjecture_candidates(defs,wits) if auto_conjectures else []; revs=[review_role_definition_candidate(d,wits,reviewer=reviewer,min_support=min_support,min_confidence=min_confidence,max_complexity=max_complexity,max_risk=max_risk,require_witness=require_witness) for d in defs] if auto_review else []; roles=[promote_role_definition_candidate(d,r,wits,conjs,accepted_by=reviewer) for d in defs for r in revs if r.role_candidate_id==d.candidate_id and auto_promote and r.decision==RoleReviewDecision.ACCEPT_ADVISORY]
 rep=RoleObjectReport(make_role_object_report_id([s.signature_id for s in sigs]),sigs,defs,wits,conjs,revs,roles); rep.summarize(); rep.status=RoleObjectReportStatus.EMPTY if not sigs else RoleObjectReportStatus.HAS_CRITICALS if rep.critical_count() else RoleObjectReportStatus.ACCEPTED_ROLES if rep.accepted_role_count() else RoleObjectReportStatus.REVIEWED if revs else RoleObjectReportStatus.CONJECTURES_FOUND if conjs else RoleObjectReportStatus.WITNESSES_FOUND if wits else RoleObjectReportStatus.DEFINITIONS_FOUND if defs else RoleObjectReportStatus.SIGNATURES_FOUND; return rep
def apply_role_objects_to_routes(roles,scores):
 out=[]
 for row in scores:
  hits=[r for r in roles if r.is_accepted() and r.matches(row)]; base=float(row.get("score",row.get("raw_score",0)) or 0); delta=sum(max(0,r.confidence*(1-r.risk_score)) for r in hits)
  out.append({**dict(row),"role_object_ids":[r.role_id for r in hits],"role_delta":delta,"role_adjusted_score":base+delta,"role_advisory_only":True})
 return out
def rank_routes_with_role_objects(roles,scores): return sorted(apply_role_objects_to_routes(roles,scores),key=lambda x:x["role_adjusted_score"],reverse=True)
def role_report_to_lawbook_candidates(r): return [LawbookEntry(make_lawbook_entry_id("role",r.report_id,x.role_id if isinstance(x,RoleObject) else x.candidate_id),LawbookEntryKind.REUSABLE_SCHEMA_ENTRY,LawbookEntryStatus.CANDIDATE,conditions=x.defining_conditions,metadata={"role_object_not_truth":True,"role_object_report_id":r.report_id,"role_advisory_only":True,"role_id":getattr(x,"role_id",None),"role_candidate_id":getattr(x,"candidate_id",None),"role_conditions":list(x.defining_conditions)},advisory=True) for x in list(r.role_objects)+[d for d in r.definition_candidates if d.status==RoleCandidateStatus.SUPPORTED]]
def role_report_to_continuation_outputs(r): return [ContinuationActionOutput(make_continuation_output_id({"role":c.conjecture_id}),"role_objects",ContinuationOutputKind.TASK,ContinuationActionStatus.ADVISORY_ONLY,task_payload={"task":c.kind.value.lower(),"conjecture_id":c.conjecture_id},advisory=True) for c in r.conjecture_candidates]
def role_report_to_curriculum(r):
 stages=[CurriculumStage(make_curriculum_stage_id("role",c.conjecture_id),CurriculumStageKind.PROOF_TASK if c.kind==RoleConjectureKind.PROOF_TASK else CurriculumStageKind.RESIDUAL_REVIEW,CurriculumStageStatus.ADVISORY_ONLY,title="Role task",metadata={"conjecture_id":c.conjecture_id},advisory=True) for c in r.conjecture_candidates]
 return ContinuationCurriculum(make_curriculum_id("role",r.report_id),strategy=CurriculumBuildStrategy.MIXED,stages=stages,status=CurriculumTraceStatus.TASKS_EMITTED if stages else CurriculumTraceStatus.EMPTY,metadata={"advisory_only":True})
def role_report_to_discovery_value_scores(r):
 out=[]
 for d in r.definition_candidates:
  sig=DiscoveryValueSignal(content_id("role-signal",d.candidate_id),DiscoveryValueSignalKind.REUSE_VALUE,d.confidence,reason="role candidate",source_object_kind=DiscoveryValueObjectKind.RAW_TASK); s=DiscoveryValueScore(content_id("role-score",d.candidate_id),d.candidate_id,DiscoveryValueObjectKind.RAW_TASK,signals=[sig],metadata={"role_advisory_only":True}); s.recompute(); out.append(s)
 return out
def role_report_to_process_episodes(r): return [ProcessEpisodeRecord(make_process_episode_id("role",d.candidate_id),ProcessEpisodeStatus.ADVISORY_ONLY,contexts=[ProcessContextItem(content_id("role-context",d.candidate_id),ProcessContextKind.REASON,ProcessContextRole.CANDIDATE_ONLY,d.candidate_id)],advisory=True) for d in r.definition_candidates]
def role_report_to_structure_descriptors(r): return [structure_descriptor_from_mapping({"role_kind":x.role_kind.value,"conditions":list(x.defining_conditions)},object_id=getattr(x,"role_id",getattr(x,"candidate_id",None)),object_kind=StructureObjectKind.RAW_EVENT) for x in list(r.role_objects)+r.definition_candidates]
def role_report_to_typed_projection_candidates(r): return [TypedProjectionCandidate(make_typed_projection_candidate_id("role",c.conjecture_id),c.conjecture_id,status=TypedProjectionStatus.NEEDS_REVIEW,compatibility=ProjectionCompatibility.NEEDS_FORMALIZATION,required_review=True,reason=c.statement,metadata={"role_advisory_only":True}) for c in r.conjecture_candidates if c.kind==RoleConjectureKind.PROJECTION_TASK]
def role_report_to_habit_observations(r): return [HabitObservation(content_id("role-habit",x.role_id),HabitObservationKind.RAW_EVENT,route="role_reuse",outcome=HabitOutcome.ADVISORY_ONLY,object_id=x.role_id,metadata={"role_advisory_only":True}) for x in r.role_objects]
def role_report_to_reason_observations(r): return [ReasonObservation(make_reason_observation_id("role",x.role_id),ReasonObservationKind.RAW_EVENT,x.role_id,"role_objects",*extract_atoms_from_mapping(x.to_dict()),metadata={"role_advisory_only":True}) for x in r.role_objects]
def role_report_to_structural_identity_objects(r): return [{"role_id":x.role_id,"kind":x.role_kind.value,"conditions":list(x.defining_conditions),"role_advisory_only":True} for x in r.role_objects]
def role_report_to_alchemical_trace(r):
 t=AlchemicalTrace(make_alchemical_trace_id("role",r.report_id))
 for p in (AlchemicalPhase.RAW_MATTER,AlchemicalPhase.CALCINATION,AlchemicalPhase.SOLUTION,AlchemicalPhase.SUBLIMATION,AlchemicalPhase.DESCENSION,AlchemicalPhase.DISTILLATION,AlchemicalPhase.COAGULATION): t.add_step(phase=p,status=AlchemicalStatus.ADVISORY_ONLY)
 return t
def role_report_to_agent_experiences(r,agent_id=None): return [AgentExperience(content_id("role-exp",d.candidate_id),agent_id or "role-objects",None,None,"role_objects",None,AgentExperienceOutcome.ADVISORY_ONLY,metadata={"role_candidate_id":d.candidate_id}) for d in r.definition_candidates]
def role_report_to_route_telemetry_events(r): return [{"event_id":content_id("role-telemetry",d.candidate_id),"route_kind":"role_objects","outcome":d.status.value,"role_advisory_only":True} for d in r.definition_candidates]
def audit_role_signature(x): return [_f("CRITICAL","ROLE_SIGNATURE_NON_ADVISORY","role signature non-advisory",x.signature_id)] if not x.advisory else []
def audit_role_definition_candidate(x):
 fs=[]
 if not x.advisory: fs.append(_f("CRITICAL","ROLE_CANDIDATE_NON_ADVISORY","role candidate non-advisory",x.candidate_id))
 if x.support_count<3: fs.append(_f("WARNING","ROLE_LOW_SUPPORT","role candidate low support",x.candidate_id))
 if not x.witness_count: fs.append(_f("WARNING","ROLE_NO_WITNESSES","role candidate has no witnesses",x.candidate_id))
 return fs
def audit_role_witness_candidate(x):
 return [_f("CRITICAL","ROLE_WITNESS_FALSE_BOUNDARY","role witness claims verified boundary without full evidence",x.witness_id)] if x.witness_status==RoleWitnessStatus.VERIFIED_EXISTING_CERTIFICATE and not x.has_verified_boundary() else []
def audit_role_conjecture_candidate(x): return [_f("CRITICAL","ROLE_CONJECTURE_AS_TRUTH","role conjecture carries truth field",x.conjecture_id)] if x.metadata.get("terminal_form") or x.metadata.get("certificate_id") else []
def audit_role_object(x,max_risk=.5):
 fs=[]
 if not x.advisory: fs.append(_f("CRITICAL","ROLE_OBJECT_NON_ADVISORY","role object non-advisory",x.role_id))
 if x.is_accepted() and not x.defining_conditions: fs.append(_f("CRITICAL","ROLE_ACCEPTED_WITHOUT_CONDITIONS","accepted role lacks conditions",x.role_id))
 if x.is_accepted() and x.risk_score>max_risk: fs.append(_f("CRITICAL","ROLE_ACCEPTED_HIGH_RISK","accepted role high risk",x.role_id))
 return fs
def audit_role_object_report(r): return [y for xs in (r.signatures,r.definition_candidates,r.witness_candidates,r.conjecture_candidates,r.role_objects) for x in xs for y in (audit_role_signature(x) if isinstance(x,RoleSignature) else audit_role_definition_candidate(x) if isinstance(x,RoleDefinitionCandidate) else audit_role_witness_candidate(x) if isinstance(x,RoleWitnessCandidate) else audit_role_conjecture_candidate(x) if isinstance(x,RoleConjectureCandidate) else audit_role_object(x))]
def _term(x):
 try:return TerminalForm(str(x)) if x else None
 except ValueError:return None
def _s(x): return None if x is None else str(x)
def _now(): return datetime.now(timezone.utc).isoformat()
def _j(x): return json.dumps(x,sort_keys=True,separators=(",",":"))
def _w(p,t): path=Path(p); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(t,encoding="utf-8")
def _f(sev,code,msg,obj): return {"severity":sev,"code":code,"message":msg,"object_id":obj}
