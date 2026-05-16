"""Advisory structural analogy and exposition over MathGraph artifacts."""
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
from mathgraph.continuation_actions import ContinuationActionOutput,ContinuationActionStatus,ContinuationOutputKind,make_continuation_output_id
from mathgraph.continuation_curriculum import ContinuationCurriculum,CurriculumBuildStrategy,CurriculumStage,CurriculumStageKind,CurriculumStageStatus,CurriculumTraceStatus,make_curriculum_id,make_curriculum_stage_id
from mathgraph.discovery_value import DiscoveryValueObjectKind,DiscoveryValueScore,DiscoveryValueSignal,DiscoveryValueSignalKind
from mathgraph.hashing import content_id
from mathgraph.habit_rules import HabitObservation,HabitObservationKind,HabitOutcome
from mathgraph.lawbook import LawbookEntry,LawbookEntryKind,LawbookEntryStatus,LawbookStore,make_lawbook_entry_id
from mathgraph.process_memory import ProcessContextItem,ProcessContextKind,ProcessContextRole,ProcessEpisodeRecord,ProcessEpisodeStatus,make_process_episode_id
from mathgraph.reason_compression import ReasonObservation,ReasonObservationKind,extract_atoms_from_mapping,make_reason_observation_id
from mathgraph.role_objects import RoleSignature,RoleSourceKind,RoleObjectKind,make_role_signature_id
from mathgraph.structure_registry import StructureDescriptor,StructureObjectKind,TypedProjectionCandidate,TypedProjectionStatus,ProjectionCompatibility,structure_descriptor_from_mapping,make_typed_projection_candidate_id
def _enum(n,v): return Enum(n,{x:x for x in v.split()},type=str)
AnalogySourceKind=_enum("AnalogySourceKind","ROLE_OBJECT ROLE_DEFINITION ROLE_SIGNATURE STRUCTURE_DESCRIPTOR STRUCTURE_MAPPING TYPED_PROJECTION REASON HABIT PROCESS_MEMORY LAWBOOK_ENTRY LAWBOOK_QUERY PROJECTION STRUCTURAL_IDENTITY PROOF_DIGESTION VERIFIER_FEEDBACK REPAIR_LOOP CURRICULUM ALCHEMICAL_TRACE AGENT_EXPERIENCE ROUTE_TELEMETRY RAW_EVENT UNKNOWN")
AnalogyFeatureKind=_enum("AnalogyFeatureKind","STRUCTURE_FAMILY STRUCTURE_FEATURE ROLE_CONDITION REASON_ATOM HABIT_CONDITION PROCESS_PATTERN ROUTE_PATTERN PROJECTION_COMPATIBILITY TERMINAL_PATTERN WITNESS_PATTERN OBSTRUCTION_PATTERN PROOF_PATTERN COST_PATTERN RISK_PATTERN TEXT_PATTERN UNKNOWN")
AnalogyRelationKind=_enum("AnalogyRelationKind","SAME_ROLE SAME_STRUCTURE_FAMILY SHARED_FEATURES SHARED_REASON SHARED_HABIT SHARED_PROCESS SOURCE_TARGET_PARALLEL PROOF_TO_PROOF COUNTERMODEL_TO_COUNTERMODEL OBSTRUCTION_TO_OBSTRUCTION PROJECTION_TO_PROJECTION CROSS_FAMILY_ANALOGY WEAK_ANALOGY CONFLICTING_ANALOGY UNKNOWN")
AnalogyBreakKind=_enum("AnalogyBreakKind","TYPE_MISMATCH FAMILY_MISMATCH MISSING_FEATURE CONFLICTING_FEATURE UNSUPPORTED_PROJECTION VERIFIER_BOUNDARY_MISMATCH TERMINAL_FORM_MISMATCH WITNESS_MISSING ADAPTER_REQUIRED FORMALIZATION_REQUIRED HIGH_RISK LOW_SUPPORT OVERGENERALIZED UNKNOWN")
AnalogyCandidateStatus=_enum("AnalogyCandidateStatus","CANDIDATE STRONG_ADVISORY WEAK_ADVISORY NEEDS_REVIEW NEEDS_ADAPTER NEEDS_FORMALIZATION BLOCKED_BY_BREAK BLOCKED_CONFLICT HELD_IN_CHORA ACCEPTED_EXPOSITION REJECTED UNKNOWN")
ExpositionNoteKind=_enum("ExpositionNoteKind","SUMMARY KEY_IDEA ANALOGY_MAP ANALOGY_LIMIT PROOF_DIGESTION COUNTERMODEL_DIGESTION OBSTRUCTION_DIGESTION PROJECTION_GUIDE HUMAN_REVIEW_GUIDE TEACHING_NOTE WARNING UNKNOWN")
AnalogyReviewDecision=_enum("AnalogyReviewDecision","ACCEPT_EXPOSITION REJECT NEEDS_MORE_SUPPORT NEEDS_BREAK_ANALYSIS NEEDS_FORMALIZATION NEEDS_ADAPTER NEEDS_HUMAN_REVIEW HOLD_IN_CHORA UNKNOWN")
StructuralAnalogyReportStatus=_enum("StructuralAnalogyReportStatus","EMPTY SOURCES_FOUND FEATURE_MAPS_FOUND ANALOGIES_FOUND BREAKS_FOUND EXPOSITION_FOUND REVIEWED ACCEPTED_EXPOSITION HAS_WARNINGS HAS_CRITICALS ADVISORY_ONLY")
@dataclass
class AnalogySource:
 source_id:str; source_kind:AnalogySourceKind; object_id:str|None=None; label:str|None=None; feature_atoms:tuple[str,...]=(); feature_kinds:dict[str,str]=field(default_factory=dict); structure_families:tuple[str,...]=(); role_kinds:tuple[str,...]=(); routes:tuple[str,...]=(); terminal_patterns:tuple[str,...]=(); support_object_ids:tuple[str,...]=(); risk_score:float=0.0; gain_score:float=0.0; confidence:float=0.0; warnings:tuple[str,...]=(); criticals:tuple[str,...]=(); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def to_dict(self): return {**self.__dict__,"source_kind":self.source_kind.value,"feature_atoms":list(self.feature_atoms),"structure_families":list(self.structure_families),"role_kinds":list(self.role_kinds),"routes":list(self.routes),"terminal_patterns":list(self.terminal_patterns),"support_object_ids":list(self.support_object_ids),"warnings":list(self.warnings),"criticals":list(self.criticals)}
 @classmethod
 def from_dict(c,d): return c(str(d["source_id"]),AnalogySourceKind(str(d.get("source_kind","UNKNOWN"))),_s(d.get("object_id")),_s(d.get("label")),tuple(d.get("feature_atoms",())),dict(d.get("feature_kinds",{})),tuple(d.get("structure_families",())),tuple(d.get("role_kinds",())),tuple(d.get("routes",())),tuple(d.get("terminal_patterns",())),tuple(d.get("support_object_ids",())),float(d.get("risk_score",0)),float(d.get("gain_score",0)),float(d.get("confidence",0)),tuple(d.get("warnings",())),tuple(d.get("criticals",())),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
@dataclass
class AnalogyFeatureMap:
 map_id:str; source_id:str; target_id:str; relation_kind:AnalogyRelationKind=AnalogyRelationKind.UNKNOWN; mapped_features:dict[str,str]=field(default_factory=dict); shared_features:tuple[str,...]=(); source_only_features:tuple[str,...]=(); target_only_features:tuple[str,...]=(); shared_families:tuple[str,...]=(); shared_roles:tuple[str,...]=(); score:float=0.0; risk_score:float=0.0; warnings:tuple[str,...]=(); criticals:tuple[str,...]=(); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def to_dict(self): return {**self.__dict__,"relation_kind":self.relation_kind.value,"shared_features":list(self.shared_features),"source_only_features":list(self.source_only_features),"target_only_features":list(self.target_only_features),"shared_families":list(self.shared_families),"shared_roles":list(self.shared_roles),"warnings":list(self.warnings),"criticals":list(self.criticals)}
 @classmethod
 def from_dict(c,d): return c(str(d["map_id"]),str(d["source_id"]),str(d["target_id"]),AnalogyRelationKind(str(d.get("relation_kind","UNKNOWN"))),dict(d.get("mapped_features",{})),tuple(d.get("shared_features",())),tuple(d.get("source_only_features",())),tuple(d.get("target_only_features",())),tuple(d.get("shared_families",())),tuple(d.get("shared_roles",())),float(d.get("score",0)),float(d.get("risk_score",0)),tuple(d.get("warnings",())),tuple(d.get("criticals",())),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
@dataclass
class AnalogyBreak:
 break_id:str; map_id:str|None=None; candidate_id:str|None=None; break_kind:AnalogyBreakKind=AnalogyBreakKind.UNKNOWN; feature:str|None=None; description:str|None=None; severity:float=0.0; blocks_projection:bool=False; requires_review:bool=True; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def to_dict(self): return {**self.__dict__,"break_kind":self.break_kind.value}
 @classmethod
 def from_dict(c,d): return c(str(d["break_id"]),_s(d.get("map_id")),_s(d.get("candidate_id")),AnalogyBreakKind(str(d.get("break_kind","UNKNOWN"))),_s(d.get("feature")),_s(d.get("description")),float(d.get("severity",0)),bool(d.get("blocks_projection",False)),bool(d.get("requires_review",True)),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
@dataclass
class StructuralAnalogyCandidate:
 candidate_id:str; source_id:str; target_id:str; map_id:str; relation_kind:AnalogyRelationKind=AnalogyRelationKind.UNKNOWN; status:AnalogyCandidateStatus=AnalogyCandidateStatus.CANDIDATE; analogy_score:float=0.0; risk_score:float=0.0; break_ids:tuple[str,...]=(); projected_task_kinds:tuple[str,...]=(); explanation:str|None=None; requires_review:bool=True; required_adapter:str|None=None; required_formalization:bool=False; warnings:tuple[str,...]=(); criticals:tuple[str,...]=(); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def is_blocked(self): return self.status in {AnalogyCandidateStatus.BLOCKED_BY_BREAK,AnalogyCandidateStatus.BLOCKED_CONFLICT,AnalogyCandidateStatus.REJECTED}
 def is_schedulable(self): return self.status in {AnalogyCandidateStatus.STRONG_ADVISORY,AnalogyCandidateStatus.WEAK_ADVISORY,AnalogyCandidateStatus.NEEDS_REVIEW,AnalogyCandidateStatus.NEEDS_ADAPTER,AnalogyCandidateStatus.NEEDS_FORMALIZATION}
 def to_dict(self): return {**self.__dict__,"relation_kind":self.relation_kind.value,"status":self.status.value,"break_ids":list(self.break_ids),"projected_task_kinds":list(self.projected_task_kinds),"warnings":list(self.warnings),"criticals":list(self.criticals)}
 @classmethod
 def from_dict(c,d): return c(str(d["candidate_id"]),str(d["source_id"]),str(d["target_id"]),str(d["map_id"]),AnalogyRelationKind(str(d.get("relation_kind","UNKNOWN"))),AnalogyCandidateStatus(str(d.get("status","CANDIDATE"))),float(d.get("analogy_score",0)),float(d.get("risk_score",0)),tuple(d.get("break_ids",())),tuple(d.get("projected_task_kinds",())),_s(d.get("explanation")),bool(d.get("requires_review",True)),_s(d.get("required_adapter")),bool(d.get("required_formalization",False)),tuple(d.get("warnings",())),tuple(d.get("criticals",())),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
@dataclass
class ExpositionNote:
 note_id:str; kind:ExpositionNoteKind; candidate_id:str|None=None; source_id:str|None=None; target_id:str|None=None; title:str|None=None; text:str=""; key_points:tuple[str,...]=(); limitations:tuple[str,...]=(); suggested_tasks:tuple[str,...]=(); warnings:tuple[str,...]=(); criticals:tuple[str,...]=(); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def to_dict(self): return {**self.__dict__,"kind":self.kind.value,"key_points":list(self.key_points),"limitations":list(self.limitations),"suggested_tasks":list(self.suggested_tasks),"warnings":list(self.warnings),"criticals":list(self.criticals)}
 @classmethod
 def from_dict(c,d): return c(str(d["note_id"]),ExpositionNoteKind(str(d.get("kind","UNKNOWN"))),_s(d.get("candidate_id")),_s(d.get("source_id")),_s(d.get("target_id")),_s(d.get("title")),str(d.get("text","")),tuple(d.get("key_points",())),tuple(d.get("limitations",())),tuple(d.get("suggested_tasks",())),tuple(d.get("warnings",())),tuple(d.get("criticals",())),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
@dataclass
class AnalogyReview:
 review_id:str; candidate_id:str; decision:AnalogyReviewDecision; reviewer:str|None=None; reason:str|None=None; required_evidence:tuple[str,...]=(); created_at:str=field(default_factory=lambda:_now()); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def to_dict(self): return {**self.__dict__,"decision":self.decision.value,"required_evidence":list(self.required_evidence)}
 @classmethod
 def from_dict(c,d): return c(str(d["review_id"]),str(d["candidate_id"]),AnalogyReviewDecision(str(d.get("decision","UNKNOWN"))),_s(d.get("reviewer")),_s(d.get("reason")),tuple(d.get("required_evidence",())),str(d.get("created_at") or _now()),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
@dataclass
class StructuralAnalogyReport:
 report_id:str; sources:list[AnalogySource]=field(default_factory=list); feature_maps:list[AnalogyFeatureMap]=field(default_factory=list); breaks:list[AnalogyBreak]=field(default_factory=list); candidates:list[StructuralAnalogyCandidate]=field(default_factory=list); exposition_notes:list[ExpositionNote]=field(default_factory=list); reviews:list[AnalogyReview]=field(default_factory=list); status:StructuralAnalogyReportStatus=StructuralAnalogyReportStatus.EMPTY; created_at:str=field(default_factory=lambda:_now()); summary:dict[str,Any]=field(default_factory=dict); metadata:dict[str,Any]=field(default_factory=lambda:{"analogy_advisory_only":True}); advisory:bool=True
 def source_count(self): return len(self.sources)
 def feature_map_count(self): return len(self.feature_maps)
 def break_count(self): return len(self.breaks)
 def candidate_count(self): return len(self.candidates)
 def exposition_count(self): return len(self.exposition_notes)
 def critical_count(self): return sum(len(x.criticals) for x in self.sources+self.feature_maps+self.candidates+self.exposition_notes)
 def summarize(self):
  self.summary={"source_total":len(self.sources),"feature_map_total":len(self.feature_maps),"break_total":len(self.breaks),"candidate_total":len(self.candidates),"exposition_total":len(self.exposition_notes),"review_total":len(self.reviews),"strong_analogy_count":sum(c.status==AnalogyCandidateStatus.STRONG_ADVISORY for c in self.candidates),"weak_analogy_count":sum(c.status==AnalogyCandidateStatus.WEAK_ADVISORY for c in self.candidates),"blocked_count":sum(c.is_blocked() for c in self.candidates),"needs_adapter_count":sum(c.status==AnalogyCandidateStatus.NEEDS_ADAPTER for c in self.candidates),"needs_formalization_count":sum(c.status==AnalogyCandidateStatus.NEEDS_FORMALIZATION for c in self.candidates),"accepted_exposition_count":sum(r.decision==AnalogyReviewDecision.ACCEPT_EXPOSITION for r in self.reviews),"family_counts":dict(Counter(f for s in self.sources for f in s.structure_families)),"relation_counts":dict(Counter(c.relation_kind.value for c in self.candidates)),"break_kind_counts":dict(Counter(b.break_kind.value for b in self.breaks)),"critical_count":self.critical_count()}; return dict(self.summary)
 def to_dict(self): return {"report_id":self.report_id,"sources":[x.to_dict() for x in self.sources],"feature_maps":[x.to_dict() for x in self.feature_maps],"breaks":[x.to_dict() for x in self.breaks],"candidates":[x.to_dict() for x in self.candidates],"exposition_notes":[x.to_dict() for x in self.exposition_notes],"reviews":[x.to_dict() for x in self.reviews],"status":self.status.value,"created_at":self.created_at,"summary":dict(self.summary),"metadata":dict(self.metadata),"advisory":self.advisory}
 @classmethod
 def from_dict(c,d): return c(str(d["report_id"]),[AnalogySource.from_dict(x) for x in d.get("sources",[])],[AnalogyFeatureMap.from_dict(x) for x in d.get("feature_maps",[])],[AnalogyBreak.from_dict(x) for x in d.get("breaks",[])],[StructuralAnalogyCandidate.from_dict(x) for x in d.get("candidates",[])],[ExpositionNote.from_dict(x) for x in d.get("exposition_notes",[])],[AnalogyReview.from_dict(x) for x in d.get("reviews",[])],StructuralAnalogyReportStatus(str(d.get("status","EMPTY"))),str(d.get("created_at") or _now()),dict(d.get("summary",{})),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
 def write_json(self,p): _w(p,self.to_json()+"\n")
 @classmethod
 def read_json(c,p): return c.from_json(Path(p).read_text())
 def write_jsonl(self,p): _w(p,self.to_json()+"\n")
 @classmethod
 def read_jsonl(c,p): return [c.from_json(x) for x in Path(p).read_text().splitlines() if x.strip()]
def make_analogy_source_id(*x): return content_id("analogy-source",x)
def make_analogy_feature_map_id(*x): return content_id("analogy-map",x)
def make_analogy_break_id(*x): return content_id("analogy-break",x)
def make_structural_analogy_candidate_id(*x): return content_id("analogy-candidate",x)
def make_exposition_note_id(*x): return content_id("exposition-note",x)
def make_analogy_review_id(*x): return content_id("analogy-review",x)
def make_structural_analogy_report_id(*x): return content_id("analogy-report",x)
def normalize_analogy_atom(v):
 s=re.sub(r"[^a-z0-9_:/=\-]+","_",str(v).strip().lower().replace(" ","_")).strip("_")
 return s[:80]+"_"+content_id("analogy-atom",s)[-8:] if len(s)>96 else s or "unknown"
def classify_analogy_feature(a,source_key=None):
 t=(str(source_key or "")+" "+a).lower()
 rules=[(("role","constructor","obstruction","proof_schema","projection_role"),"ROLE_CONDITION"),(("reason","load_bearing","minimal"),"REASON_ATOM"),(("process","context","elimination","transition"),"PROCESS_PATTERN"),(("projection","compatibility"),"PROJECTION_COMPATIBILITY"),(("verified_proof","finite_countermodel","named_obstruction"),"TERMINAL_PATTERN"),(("witness","example","table"),"WITNESS_PATTERN"),(("obstruction","blocked","failed"),"OBSTRUCTION_PATTERN"),(("proof","theorem","lemma"),"PROOF_PATTERN"),(("habit","condition"),"HABIT_CONDITION"),(("route","scheduler"),"ROUTE_PATTERN"),(("family","algebraic","order","topological","logical","computational"),"STRUCTURE_FAMILY"),(("feature","operation","relation","closure","quotient","transition"),"STRUCTURE_FEATURE"),(("cost",),"COST_PATTERN"),(("risk",),"RISK_PATTERN"),(("text","note","explanation"),"TEXT_PATTERN")]
 for keys,k in rules:
  if any(x in t for x in keys): return AnalogyFeatureKind(k)
 return AnalogyFeatureKind.UNKNOWN
def extract_analogy_features_from_mapping(d,*,max_depth=4,max_items=220):
 out=[]; kinds={}
 def walk(x,key=None,depth=0):
  if depth>max_depth or len(out)>=max_items:return
  if isinstance(x,Mapping):
   for k,v in x.items():
    a=normalize_analogy_atom(k); out.append(a); kinds[a]=classify_analogy_feature(a,str(k)).value; walk(v,str(k),depth+1)
  elif isinstance(x,(list,tuple,set)):
   for v in list(x)[:max_items]: walk(v,key,depth+1)
  else:
   a=normalize_analogy_atom(getattr(x,"value",x)); out.append(a); kinds[a]=classify_analogy_feature(a,key).value
 walk(d); return tuple(dict.fromkeys(out)),kinds
def analogy_source_from_mapping(d,*,source_kind=AnalogySourceKind.RAW_EVENT,object_id=None,label=None):
 atoms,kinds=extract_analogy_features_from_mapping(d)
 fam=tuple(a for a,k in kinds.items() if k=="STRUCTURE_FAMILY" and a not in {"family","structure_families"})
 roles=tuple(a for a,k in kinds.items() if k=="ROLE_CONDITION" and a not in {"role","role_kinds"})
 routes=tuple(a for a,k in kinds.items() if k=="ROUTE_PATTERN")
 terms=tuple(a for a,k in kinds.items() if k=="TERMINAL_PATTERN")
 return AnalogySource(make_analogy_source_id(source_kind.value,object_id,atoms),source_kind,object_id,label,atoms,kinds,fam,roles,routes,terms,(object_id,) if object_id else (),float(d.get("risk_score",0) or 0),float(d.get("gain_score",d.get("gain_units",0)) or 0),min(1,.2+.04*len(atoms)),metadata=dict(d),advisory=True)
def _src(o,k,oid=None):
 return analogy_source_from_mapping(o.to_dict() if hasattr(o,"to_dict") else dict(o),source_kind=k,object_id=oid or getattr(o,"role_id",getattr(o,"candidate_id",getattr(o,"signature_id",getattr(o,"descriptor_id",getattr(o,"mapping_id",getattr(o,"reason_id",getattr(o,"rule_id",getattr(o,"episode_id",getattr(o,"entry_id",None))))))))))
def analogy_source_from_role_object(x): return _src(x,AnalogySourceKind.ROLE_OBJECT,x.role_id)
def analogy_source_from_role_definition(x): return _src(x,AnalogySourceKind.ROLE_DEFINITION,x.candidate_id)
def analogy_source_from_role_signature(x): return _src(x,AnalogySourceKind.ROLE_SIGNATURE,x.signature_id)
def analogy_sources_from_role_report(x): return [analogy_source_from_role_object(o) for o in x.role_objects]+[analogy_source_from_role_definition(d) for d in x.definition_candidates]+[analogy_source_from_role_signature(s) for s in x.signatures]
def analogy_source_from_structure_descriptor(x): return _src(x,AnalogySourceKind.STRUCTURE_DESCRIPTOR,x.descriptor_id)
def analogy_source_from_structure_mapping(x): return _src(x,AnalogySourceKind.STRUCTURE_MAPPING,x.mapping_id)
def analogy_source_from_typed_projection(x): return _src(x,AnalogySourceKind.TYPED_PROJECTION,x.candidate_id)
def analogy_sources_from_structure_report(x): return [analogy_source_from_structure_descriptor(d) for d in x.descriptors]+[analogy_source_from_structure_mapping(m) for m in x.mappings]+[analogy_source_from_typed_projection(c) for c in x.typed_projection_candidates]
def analogy_source_from_reason_candidate(x): return _src(x,AnalogySourceKind.REASON,x.candidate_id)
def analogy_source_from_reason_node(x): return _src(x,AnalogySourceKind.REASON,x.reason_id)
def analogy_sources_from_reason_report(x): return [analogy_source_from_reason_candidate(c) for c in x.candidates]+[analogy_source_from_reason_node(n) for n in x.reason_nodes]
def analogy_source_from_habit_rule(x): return _src(x,AnalogySourceKind.HABIT,x.rule_id)
def analogy_sources_from_habit_report(x): return [analogy_source_from_habit_rule(r) for r in x.rules]
def analogy_source_from_process_episode(x): return _src(x,AnalogySourceKind.PROCESS_MEMORY,x.episode_id)
def analogy_sources_from_process_report(x): return [analogy_source_from_process_episode(e) for e in (x.store.episodes if x.store else [])]
def analogy_source_from_lawbook_entry(x): return _src(x,AnalogySourceKind.LAWBOOK_ENTRY,x.entry_id)
def analogy_sources_from_lawbook_store(x): return [analogy_source_from_lawbook_entry(e) for e in x.entries]
def analogy_sources_from_lawbook_query_report(x): return [_src(a,AnalogySourceKind.LAWBOOK_QUERY,a.answer_id) for a in x.answers]
def analogy_source_from_projection_candidate(x): return _src(x,AnalogySourceKind.PROJECTION,x.candidate_id)
def analogy_sources_from_projection_candidates(xs): return [analogy_source_from_projection_candidate(x) for x in xs]
def analogy_sources_from_structural_identity_report(x): return [_src(c,AnalogySourceKind.STRUCTURAL_IDENTITY,c.candidate_id) for c in x.merge_candidates]
def analogy_source_from_structural_graph(x): return _src(x,AnalogySourceKind.STRUCTURAL_IDENTITY,x.graph_id)
def analogy_source_from_structural_signature(x): return _src(x,AnalogySourceKind.STRUCTURAL_IDENTITY,x.signature_id)
def analogy_source_from_proof_digestion_trace(x): return _src(x,AnalogySourceKind.PROOF_DIGESTION,x.trace_id)
def analogy_source_from_verifier_feedback(x): return _src(x,AnalogySourceKind.VERIFIER_FEEDBACK,x.feedback_id)
def analogy_source_from_repair_loop(x): return _src(x,AnalogySourceKind.REPAIR_LOOP,x.trace_id)
def analogy_sources_from_curriculum(x): return [analogy_source_from_curriculum_stage(s) for s in x.stages]
def analogy_source_from_curriculum_stage(x): return _src(x,AnalogySourceKind.CURRICULUM,x.stage_id)
def analogy_source_from_alchemical_trace(x): return _src(x,AnalogySourceKind.ALCHEMICAL_TRACE,x.trace_id)
def analogy_source_from_agent_experience(x): return _src(x,AnalogySourceKind.AGENT_EXPERIENCE,x.experience_id)
def analogy_source_from_route_telemetry_event(x): return analogy_source_from_mapping(x,source_kind=AnalogySourceKind.ROUTE_TELEMETRY,object_id=_s(x.get("event_id")))
def analogy_sources_from_object(o):
 from mathgraph.habit_rules import HabitFormationReport,HabitRule
 from mathgraph.lawbook_query import LawbookQueryReport
 from mathgraph.projection import ProjectionCandidate
 from mathgraph.proof_digestion import ProofDigestionTrace
 from mathgraph.reason_compression import ReasonCandidate,ReasonCompressionReport,ReasonNode
 from mathgraph.role_objects import RoleDefinitionCandidate,RoleObject,RoleObjectReport,RoleSignature
 from mathgraph.structural_identity import StructuralGraph,StructuralIdentityReport,StructuralSignature
 from mathgraph.structure_registry import StructureMapping,StructureRegistryReport
 from mathgraph.verifier_feedback import RepairLoopTrace,VerifierFeedback
 if isinstance(o,AnalogySource): return [o]
 if isinstance(o,RoleObjectReport): return analogy_sources_from_role_report(o)
 if isinstance(o,RoleObject): return [analogy_source_from_role_object(o)]
 if isinstance(o,RoleDefinitionCandidate): return [analogy_source_from_role_definition(o)]
 if isinstance(o,RoleSignature): return [analogy_source_from_role_signature(o)]
 if isinstance(o,StructureRegistryReport): return analogy_sources_from_structure_report(o)
 if isinstance(o,StructureDescriptor): return [analogy_source_from_structure_descriptor(o)]
 if isinstance(o,StructureMapping): return [analogy_source_from_structure_mapping(o)]
 if isinstance(o,TypedProjectionCandidate): return [analogy_source_from_typed_projection(o)]
 if isinstance(o,ReasonCompressionReport): return analogy_sources_from_reason_report(o)
 if isinstance(o,ReasonCandidate): return [analogy_source_from_reason_candidate(o)]
 if isinstance(o,ReasonNode): return [analogy_source_from_reason_node(o)]
 if isinstance(o,HabitFormationReport): return analogy_sources_from_habit_report(o)
 if isinstance(o,HabitRule): return [analogy_source_from_habit_rule(o)]
 if hasattr(o,"store") and o.__class__.__name__=="ProcessMemoryReport": return analogy_sources_from_process_report(o)
 if isinstance(o,ProcessEpisodeRecord): return [analogy_source_from_process_episode(o)]
 if isinstance(o,LawbookEntry): return [analogy_source_from_lawbook_entry(o)]
 if isinstance(o,LawbookStore): return analogy_sources_from_lawbook_store(o)
 if isinstance(o,LawbookQueryReport): return analogy_sources_from_lawbook_query_report(o)
 if isinstance(o,ProjectionCandidate): return [analogy_source_from_projection_candidate(o)]
 if isinstance(o,StructuralIdentityReport): return analogy_sources_from_structural_identity_report(o)
 if isinstance(o,StructuralGraph): return [analogy_source_from_structural_graph(o)]
 if isinstance(o,StructuralSignature): return [analogy_source_from_structural_signature(o)]
 if isinstance(o,ProofDigestionTrace): return [analogy_source_from_proof_digestion_trace(o)]
 if isinstance(o,VerifierFeedback): return [analogy_source_from_verifier_feedback(o)]
 if isinstance(o,RepairLoopTrace): return [analogy_source_from_repair_loop(o)]
 if isinstance(o,ContinuationCurriculum): return analogy_sources_from_curriculum(o)
 if isinstance(o,CurriculumStage): return [analogy_source_from_curriculum_stage(o)]
 if isinstance(o,AlchemicalTrace): return [analogy_source_from_alchemical_trace(o)]
 if isinstance(o,AgentExperience): return [analogy_source_from_agent_experience(o)]
 if isinstance(o,Mapping): return [analogy_source_from_route_telemetry_event(o)]
 return []
def infer_analogy_relation_kind(a,b,shared):
 if set(a.role_kinds)&set(b.role_kinds): return AnalogyRelationKind.SAME_ROLE
 if set(a.structure_families)&set(b.structure_families): return AnalogyRelationKind.SAME_STRUCTURE_FAMILY
 kinds={a.feature_kinds.get(x) for x in shared}|{b.feature_kinds.get(x) for x in shared}
 text=" ".join(shared)
 if "REASON_ATOM" in kinds:return AnalogyRelationKind.SHARED_REASON
 if "HABIT_CONDITION" in kinds:return AnalogyRelationKind.SHARED_HABIT
 if "PROCESS_PATTERN" in kinds:return AnalogyRelationKind.SHARED_PROCESS
 if "projection" in text:return AnalogyRelationKind.PROJECTION_TO_PROJECTION
 if any(x in text for x in ("source","target")):return AnalogyRelationKind.SOURCE_TARGET_PARALLEL
 if "proof" in text:return AnalogyRelationKind.PROOF_TO_PROOF
 if "countermodel" in text:return AnalogyRelationKind.COUNTERMODEL_TO_COUNTERMODEL
 if "obstruction" in text:return AnalogyRelationKind.OBSTRUCTION_TO_OBSTRUCTION
 if a.structure_families and b.structure_families and shared:return AnalogyRelationKind.CROSS_FAMILY_ANALOGY
 return AnalogyRelationKind.SHARED_FEATURES if shared else AnalogyRelationKind.WEAK_ANALOGY
def compute_analogy_feature_map(a,b):
 shared=tuple(sorted(set(a.feature_atoms)&set(b.feature_atoms))); ao=tuple(sorted(set(a.feature_atoms)-set(b.feature_atoms))); bo=tuple(sorted(set(b.feature_atoms)-set(a.feature_atoms))); fam=tuple(sorted(set(a.structure_families)&set(b.structure_families))); roles=tuple(sorted(set(a.role_kinds)&set(b.role_kinds)))
 union=max(1,len(set(a.feature_atoms)|set(b.feature_atoms))); score=min(1,len(shared)/union+.15*bool(fam)+.15*bool(roles)+.05*bool(set(a.routes)&set(b.routes))); risk=min(1,(a.risk_score+b.risk_score)/2+.2*bool(a.criticals or b.criticals)+.2*bool(bool(a.terminal_patterns)^bool(b.terminal_patterns)))
 return AnalogyFeatureMap(make_analogy_feature_map_id(a.source_id,b.source_id),a.source_id,b.source_id,infer_analogy_relation_kind(a,b,shared),{x:x for x in shared},shared,ao,bo,fam,roles,score,risk,advisory=True)
def build_analogy_feature_maps(xs,*,min_score=.15,max_pairs=2500):
 out=[]
 for i,a in enumerate(xs):
  for b in xs[i+1:]:
   if len(out)>=max_pairs:return out
   m=compute_analogy_feature_map(a,b)
   if m.score>=min_score: out.append(m)
 return out
def identify_analogy_breaks(m,a,b):
 out=[]
 def add(k,sev,feature=None,blocks=False): out.append(AnalogyBreak(make_analogy_break_id(m.map_id,k.value,feature),m.map_id,None,k,feature,k.value.lower().replace("_"," "),sev,blocks,True))
 if not m.shared_families and len(m.shared_features)<3:add(AnalogyBreakKind.TYPE_MISMATCH,.8,blocks=True)
 if a.structure_families and b.structure_families and not m.shared_families:add(AnalogyBreakKind.FAMILY_MISMATCH,.4)
 important=[x for x in m.target_only_features if any(y in x for y in ("proof","witness","compatibility","adapter","formalization"))]
 if important:add(AnalogyBreakKind.MISSING_FEATURE,.35,important[0])
 text=" ".join(m.shared_features+m.source_only_features+m.target_only_features)
 if any(x in text for x in ("conflict","blocked","failed")):add(AnalogyBreakKind.CONFLICTING_FEATURE,.85,blocks=True)
 if "projection" in text and "compatibility" not in text and "adapter" not in text:add(AnalogyBreakKind.UNSUPPORTED_PROJECTION,.75,blocks=True)
 if bool(a.terminal_patterns)^bool(b.terminal_patterns):add(AnalogyBreakKind.VERIFIER_BOUNDARY_MISMATCH,.8,blocks=True)
 if "verified_proof" in text and "finite_countermodel" in text:add(AnalogyBreakKind.TERMINAL_FORM_MISMATCH,.9,blocks=True)
 if any("witness" in x for x in a.feature_atoms+b.feature_atoms) and not any("witness" in x for x in m.shared_features):add(AnalogyBreakKind.WITNESS_MISSING,.3)
 if "adapter" in text:add(AnalogyBreakKind.ADAPTER_REQUIRED,.35)
 if "formalization" in text:add(AnalogyBreakKind.FORMALIZATION_REQUIRED,.35)
 if m.risk_score>.6:add(AnalogyBreakKind.HIGH_RISK,m.risk_score)
 if len(m.shared_features)<2:add(AnalogyBreakKind.LOW_SUPPORT,.25)
 if m.relation_kind in {AnalogyRelationKind.SAME_ROLE,AnalogyRelationKind.SAME_STRUCTURE_FAMILY} and len(m.shared_features)<2:add(AnalogyBreakKind.OVERGENERALIZED,.45)
 return out
def structural_analogy_candidate_from_map(m,breaks=()):
 kinds={b.break_kind for b in breaks}; blocking=any(b.blocks_projection for b in breaks)
 if kinds&{AnalogyBreakKind.CONFLICTING_FEATURE,AnalogyBreakKind.TERMINAL_FORM_MISMATCH,AnalogyBreakKind.VERIFIER_BOUNDARY_MISMATCH}: st=AnalogyCandidateStatus.BLOCKED_CONFLICT
 elif blocking: st=AnalogyCandidateStatus.BLOCKED_BY_BREAK
 elif AnalogyBreakKind.ADAPTER_REQUIRED in kinds: st=AnalogyCandidateStatus.NEEDS_ADAPTER
 elif AnalogyBreakKind.FORMALIZATION_REQUIRED in kinds: st=AnalogyCandidateStatus.NEEDS_FORMALIZATION
 elif m.score>=.55 and m.risk_score<=.35: st=AnalogyCandidateStatus.STRONG_ADVISORY
 elif m.score>=.25: st=AnalogyCandidateStatus.WEAK_ADVISORY
 elif m.score>=.15 and breaks: st=AnalogyCandidateStatus.NEEDS_REVIEW
 else: st=AnalogyCandidateStatus.HELD_IN_CHORA if m.score>=.1 else AnalogyCandidateStatus.REJECTED
 tasks=["REVIEW_TASK"] if st!=AnalogyCandidateStatus.STRONG_ADVISORY else []
 if m.relation_kind in {AnalogyRelationKind.PROJECTION_TO_PROJECTION,AnalogyRelationKind.SOURCE_TARGET_PARALLEL} and not blocking: tasks.append("PROJECTION_TASK")
 if m.relation_kind in {AnalogyRelationKind.PROOF_TO_PROOF,AnalogyRelationKind.COUNTERMODEL_TO_COUNTERMODEL,AnalogyRelationKind.OBSTRUCTION_TO_OBSTRUCTION}: tasks.append("DIGESTION_TASK")
 if AnalogyBreakKind.FORMALIZATION_REQUIRED in kinds: tasks.append("FORMALIZATION_TASK")
 if AnalogyBreakKind.ADAPTER_REQUIRED in kinds: tasks.append("ADAPTER_TASK")
 limits=", ".join(sorted(k.value.lower() for k in kinds)) or "no recorded breaks"
 exp=f"This analogy relates {m.source_id} to {m.target_id} through shared features {', '.join(m.shared_features[:4]) or 'none'}; limits: {limits}."
 return StructuralAnalogyCandidate(make_structural_analogy_candidate_id(m.map_id),m.source_id,m.target_id,m.map_id,m.relation_kind,st,m.score,m.risk_score,tuple(b.break_id for b in breaks),tuple(tasks),exp,st!=AnalogyCandidateStatus.STRONG_ADVISORY,"formal-world adapter" if AnalogyBreakKind.ADAPTER_REQUIRED in kinds else None,AnalogyBreakKind.FORMALIZATION_REQUIRED in kinds,metadata={"analogy_advisory_only":True},advisory=True)
def build_structural_analogy_candidates(sources,maps=None,*,min_score=.15,max_pairs=2500):
 maps=list(maps) if maps is not None else build_analogy_feature_maps(sources,min_score=min_score,max_pairs=max_pairs); by={s.source_id:s for s in sources}; breaks=[]; cands=[]
 for m in maps:
  bs=identify_analogy_breaks(m,by[m.source_id],by[m.target_id]); breaks+=bs; cands.append(structural_analogy_candidate_from_map(m,bs))
 return maps,breaks,cands
def exposition_notes_from_candidate(c,m,breaks=()):
 md={"exposition_not_verification":True,"analogy_advisory_only":True}; lim=tuple(b.description or b.break_kind.value for b in breaks); base=(c.candidate_id,c.source_id,c.target_id)
 notes=[ExpositionNote(make_exposition_note_id(*base,"summary"),ExpositionNoteKind.SUMMARY,*base,"Analogy summary",f"{c.explanation} This is advisory exposition, not verification.",(c.relation_kind.value,c.status.value),lim,tuple(c.projected_task_kinds),metadata=md),ExpositionNote(make_exposition_note_id(*base,"map"),ExpositionNoteKind.ANALOGY_MAP,*base,"Feature map",", ".join(f"{k}->{v}" for k,v in m.mapped_features.items()),tuple(m.shared_features),lim,metadata=md),ExpositionNote(make_exposition_note_id(*base,"guide"),ExpositionNoteKind.PROJECTION_GUIDE,*base,"Projection guide","Schedule only reviewable advisory tasks.",tuple(c.projected_task_kinds),lim,tuple(c.projected_task_kinds),metadata=md),ExpositionNote(make_exposition_note_id(*base,"review"),ExpositionNoteKind.HUMAN_REVIEW_GUIDE,*base,"Human review guide","Inspect shared features, breaks, and missing formalization before reuse.",tuple(m.shared_features),lim,tuple(c.projected_task_kinds),metadata=md)]
 if breaks: notes.append(ExpositionNote(make_exposition_note_id(*base,"limit"),ExpositionNoteKind.ANALOGY_LIMIT,*base,"Analogy limits","The analogy has explicit recorded limits and is not proof.",limitations=lim,metadata=md))
 if c.relation_kind in {AnalogyRelationKind.PROOF_TO_PROOF,AnalogyRelationKind.COUNTERMODEL_TO_COUNTERMODEL,AnalogyRelationKind.OBSTRUCTION_TO_OBSTRUCTION}: notes.append(ExpositionNote(make_exposition_note_id(*base,"digest"),ExpositionNoteKind.PROOF_DIGESTION,*base,"Digestion note","Use this relation for digestion only.",limitations=lim,metadata=md))
 return notes
def review_structural_analogy_candidate(c,breaks=(),*,reviewer=None,min_score=.35,max_risk=.5):
 kinds={b.break_kind for b in breaks}
 if not c.advisory or c.criticals or c.status in {AnalogyCandidateStatus.BLOCKED_CONFLICT,AnalogyCandidateStatus.REJECTED}: d=AnalogyReviewDecision.REJECT
 elif any(b.blocks_projection for b in breaks): d=AnalogyReviewDecision.REJECT
 elif AnalogyBreakKind.ADAPTER_REQUIRED in kinds: d=AnalogyReviewDecision.NEEDS_ADAPTER
 elif AnalogyBreakKind.FORMALIZATION_REQUIRED in kinds: d=AnalogyReviewDecision.NEEDS_FORMALIZATION
 elif c.analogy_score<min_score: d=AnalogyReviewDecision.NEEDS_MORE_SUPPORT
 elif breaks: d=AnalogyReviewDecision.NEEDS_BREAK_ANALYSIS
 elif c.risk_score>max_risk: d=AnalogyReviewDecision.HOLD_IN_CHORA
 elif c.relation_kind==AnalogyRelationKind.UNKNOWN: d=AnalogyReviewDecision.NEEDS_HUMAN_REVIEW
 else: d=AnalogyReviewDecision.ACCEPT_EXPOSITION
 return AnalogyReview(make_analogy_review_id(c.candidate_id,d.value),c.candidate_id,d,reviewer)
def build_structural_analogy_report(objects=(),sources=(),*,build_maps=True,build_candidates=True,build_exposition=True,auto_review=True,reviewer=None,min_map_score=.15,max_pairs=2500):
 src={s.source_id:s for s in list(sources)+[x for o in objects for x in analogy_sources_from_object(o)]}; maps=build_analogy_feature_maps(list(src.values()),min_score=min_map_score,max_pairs=max_pairs) if build_maps else []; br=[]; cand=[]
 if build_candidates: maps,br,cand=build_structural_analogy_candidates(list(src.values()),maps,min_score=min_map_score,max_pairs=max_pairs)
 by={b.map_id:[] for b in br}
 for b in br: by.setdefault(b.map_id,[]).append(b)
 notes=[n for c in cand for n in (exposition_notes_from_candidate(c,next(m for m in maps if m.map_id==c.map_id),by.get(c.map_id,())) if build_exposition else [])]
 reviews=[review_structural_analogy_candidate(c,by.get(c.map_id,()),reviewer=reviewer) for c in cand] if auto_review else []
 r=StructuralAnalogyReport(make_structural_analogy_report_id(tuple(src),tuple(c.candidate_id for c in cand)),list(src.values()),maps,br,cand,notes,reviews)
 r.summarize()
 if r.critical_count(): r.status=StructuralAnalogyReportStatus.HAS_CRITICALS
 elif any(x.decision==AnalogyReviewDecision.ACCEPT_EXPOSITION for x in reviews): r.status=StructuralAnalogyReportStatus.ACCEPTED_EXPOSITION
 elif reviews:r.status=StructuralAnalogyReportStatus.REVIEWED
 elif notes:r.status=StructuralAnalogyReportStatus.EXPOSITION_FOUND
 elif br:r.status=StructuralAnalogyReportStatus.BREAKS_FOUND
 elif cand:r.status=StructuralAnalogyReportStatus.ANALOGIES_FOUND
 elif maps:r.status=StructuralAnalogyReportStatus.FEATURE_MAPS_FOUND
 elif src:r.status=StructuralAnalogyReportStatus.SOURCES_FOUND
 return r
def analogy_report_to_lawbook_candidates(r): return [LawbookEntry(make_lawbook_entry_id("analogy",r.report_id,n.note_id),LawbookEntryKind.REUSABLE_SCHEMA_ENTRY,LawbookEntryStatus.CANDIDATE,metadata={"structural_analogy_not_truth":True,"analogy_report_id":r.report_id,"analogy_advisory_only":True,"exposition_not_verification":True},advisory=True) for n in r.exposition_notes if any(v.decision==AnalogyReviewDecision.ACCEPT_EXPOSITION and v.candidate_id==n.candidate_id for v in r.reviews)]
def analogy_report_to_continuation_outputs(r): return [ContinuationActionOutput(make_continuation_output_id({"analogy":c.candidate_id}),"structural_analogy",ContinuationOutputKind.TASK,ContinuationActionStatus.ADVISORY_ONLY,task_payload={"task":(c.projected_task_kinds or ("REVIEW_TASK",))[0].lower(),"candidate_id":c.candidate_id},advisory=True) for c in r.candidates]
def analogy_report_to_curriculum(r):
 stages=[CurriculumStage(make_curriculum_stage_id("analogy",x),CurriculumStageKind.RESIDUAL_REVIEW,CurriculumStageStatus.ADVISORY_ONLY,title=x,metadata={"analogy_advisory_only":True},advisory=True) for x in ("compare sources","map features","analyze breaks","review exposition")]
 return ContinuationCurriculum(make_curriculum_id("analogy",r.report_id),strategy=CurriculumBuildStrategy.MIXED,stages=stages,status=CurriculumTraceStatus.ADVISORY_ONLY,metadata={"analogy_advisory_only":True},advisory=True)
def analogy_report_to_discovery_value_scores(r):
 out=[]
 for c in r.candidates:
  sig=DiscoveryValueSignal(content_id("analogy-signal",c.candidate_id),DiscoveryValueSignalKind.REUSE_VALUE,c.analogy_score-c.risk_score,reason="analogy candidate",source_object_kind=DiscoveryValueObjectKind.RAW_TASK); s=DiscoveryValueScore(content_id("analogy-value",c.candidate_id),c.candidate_id,DiscoveryValueObjectKind.RAW_TASK,signals=[sig],metadata={"analogy_advisory_only":True}); s.recompute(); out.append(s)
 return out
def analogy_report_to_process_episodes(r): return [ProcessEpisodeRecord(make_process_episode_id("analogy",c.candidate_id),ProcessEpisodeStatus.ADVISORY_ONLY,contexts=[ProcessContextItem(content_id("analogy-context",c.candidate_id),ProcessContextKind.REASON,ProcessContextRole.ADVISORY_ONLY,c.candidate_id)],advisory=True) for c in r.candidates]
def analogy_report_to_role_signatures(r): return [RoleSignature(make_role_signature_id("analogy",c.candidate_id),RoleSourceKind.RAW_EVENT,c.candidate_id,RoleObjectKind.PROJECTION_ROLE if c.relation_kind==AnalogyRelationKind.PROJECTION_TO_PROJECTION else RoleObjectKind.MIXED_ROLE,tuple(c.projected_task_kinds),metadata={"analogy_advisory_only":True},advisory=True) for c in r.candidates if c.status in {AnalogyCandidateStatus.STRONG_ADVISORY,AnalogyCandidateStatus.BLOCKED_BY_BREAK,AnalogyCandidateStatus.BLOCKED_CONFLICT}]
def analogy_report_to_structure_descriptors(r): return [structure_descriptor_from_mapping({"relation":c.relation_kind.value,"status":c.status.value,"tasks":list(c.projected_task_kinds)},object_id=c.candidate_id,object_kind=StructureObjectKind.RAW_EVENT) for c in r.candidates]
def analogy_report_to_typed_projection_candidates(r):
 out=[]
 for c in r.candidates:
  if c.relation_kind not in {AnalogyRelationKind.PROJECTION_TO_PROJECTION,AnalogyRelationKind.SOURCE_TARGET_PARALLEL}: continue
  blocked=c.is_blocked(); st=TypedProjectionStatus.BLOCKED_CONFLICT if c.status==AnalogyCandidateStatus.BLOCKED_CONFLICT else TypedProjectionStatus.BLOCKED_TYPE_MISMATCH if blocked else TypedProjectionStatus.NEEDS_REVIEW
  out.append(TypedProjectionCandidate(make_typed_projection_candidate_id("analogy",c.candidate_id),c.candidate_id,compatibility=ProjectionCompatibility.CONFLICT if blocked else ProjectionCompatibility.NEEDS_FORMALIZATION,status=st,required_review=True,reason=c.explanation,metadata={"analogy_advisory_only":True},advisory=True))
 return out
def analogy_report_to_habit_observations(r): return [HabitObservation(content_id("analogy-habit",c.candidate_id),HabitObservationKind.RAW_EVENT,route="structural_analogy",outcome=HabitOutcome.ADVISORY_ONLY if not c.is_blocked() else HabitOutcome.KILLED_ROUTE,object_id=c.candidate_id,metadata={"analogy_advisory_only":True}) for c in r.candidates]
def analogy_report_to_reason_observations(r): return [ReasonObservation(make_reason_observation_id("analogy",m.map_id),ReasonObservationKind.RAW_EVENT,m.map_id,"structural_analogy",*extract_atoms_from_mapping(m.to_dict()),metadata={"analogy_advisory_only":True}) for m in r.feature_maps]
def analogy_report_to_structural_identity_objects(r): return [{"analogy_candidate_id":c.candidate_id,"relation":c.relation_kind.value,"status":c.status.value,"analogy_advisory_only":True} for c in r.candidates]
def analogy_report_to_alchemical_trace(r):
 t=AlchemicalTrace(make_alchemical_trace_id("analogy",r.report_id))
 for p in (AlchemicalPhase.RAW_MATTER,AlchemicalPhase.CALCINATION,AlchemicalPhase.SOLUTION,AlchemicalPhase.SUBLIMATION,AlchemicalPhase.DESCENSION,AlchemicalPhase.DISTILLATION,AlchemicalPhase.COAGULATION): t.add_step(phase=p,status=AlchemicalStatus.ADVISORY_ONLY,metadata={"analogy_advisory_only":True})
 return t
def analogy_report_to_agent_experiences(r,agent_id=None): return [AgentExperience(content_id("analogy-exp",c.candidate_id),agent_id or "structural-analogy",None,None,"structural_analogy",None,AgentExperienceOutcome.ADVISORY_ONLY,metadata={"analogy_candidate_id":c.candidate_id}) for c in r.candidates]
def analogy_report_to_route_telemetry_events(r): return [{"event_id":content_id("analogy-telemetry",c.candidate_id),"route_kind":"structural_analogy","outcome":c.status.value,"analogy_advisory_only":True} for c in r.candidates]
def apply_analogy_candidates_to_routes(cands,scores):
 out=[]
 for s in scores:
  text=_j(dict(s)).lower(); hits=[c for c in cands if any(x and x.lower() in text for x in (c.source_id,c.target_id,c.relation_kind.value))]
  delta=sum(.2 if c.status==AnalogyCandidateStatus.STRONG_ADVISORY else -.2 if c.is_blocked() else .05 for c in hits); d=dict(s); d.update({"analogy_candidate_ids":[c.candidate_id for c in hits],"analogy_delta":delta,"analogy_adjusted_score":float(s.get("score",0))+delta,"analogy_advisory_only":True}); out.append(d)
 return out
def rank_routes_with_analogies(c,s): return sorted(apply_analogy_candidates_to_routes(c,s),key=lambda x:x["analogy_adjusted_score"],reverse=True)
def audit_analogy_source(x): return [_f("CRITICAL","ANALOGY_SOURCE_NON_ADVISORY","analogy source non-advisory",x.source_id)] if not x.advisory else []
def audit_analogy_feature_map(x):
 out=[]
 if not x.advisory: out.append(_f("CRITICAL","ANALOGY_MAP_NON_ADVISORY","analogy map non-advisory",x.map_id))
 if not x.shared_features: out.append(_f("WARNING","ANALOGY_MAP_NO_SHARED_FEATURES","feature map has no shared features",x.map_id))
 return out
def audit_analogy_break(x): return [_f("CRITICAL","ANALOGY_BREAK_NON_ADVISORY","analogy break non-advisory",x.break_id)] if not x.advisory else []
def audit_structural_analogy_candidate(x):
 out=[]
 if not x.advisory: out.append(_f("CRITICAL","ANALOGY_CANDIDATE_NON_ADVISORY","analogy candidate non-advisory",x.candidate_id))
 if x.metadata.get("terminal_form") or x.metadata.get("certificate_id"): out.append(_f("CRITICAL","ANALOGY_CANDIDATE_AS_TRUTH","analogy candidate carries truth field",x.candidate_id))
 if x.is_blocked() and x.is_schedulable(): out.append(_f("CRITICAL","ANALOGY_BLOCKED_SCHEDULABLE","blocked analogy marked schedulable",x.candidate_id))
 if x.analogy_score<.15: out.append(_f("WARNING","ANALOGY_LOW_SCORE","analogy candidate low score",x.candidate_id))
 return out
def audit_exposition_note(x):
 text=(x.text+" "+_j(x.metadata)).lower(); out=[]
 if not x.advisory: out.append(_f("CRITICAL","EXPOSITION_NON_ADVISORY","exposition note non-advisory",x.note_id))
 if any(k in text for k in ("verified proof","verified theorem","creates certificate")): out.append(_f("CRITICAL","EXPOSITION_AS_VERIFICATION","exposition note claims verification",x.note_id))
 return out
def audit_structural_analogy_report(r): return [y for xs in (r.sources,r.feature_maps,r.breaks,r.candidates,r.exposition_notes) for x in xs for y in (audit_analogy_source(x) if isinstance(x,AnalogySource) else audit_analogy_feature_map(x) if isinstance(x,AnalogyFeatureMap) else audit_analogy_break(x) if isinstance(x,AnalogyBreak) else audit_structural_analogy_candidate(x) if isinstance(x,StructuralAnalogyCandidate) else audit_exposition_note(x))]
def _s(x): return None if x is None else str(x)
def _now(): return datetime.now(timezone.utc).isoformat()
def _j(x): return json.dumps(x,sort_keys=True,default=str)
def _w(p,t): p=Path(p); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(t)
def _f(sev,code,msg,obj): return {"severity":sev,"code":code,"message":msg,"object_id":obj}
