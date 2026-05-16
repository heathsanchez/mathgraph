"""Advisory structure-family registry and typed projection checks."""
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
from mathgraph.process_memory import ProcessEpisodeRecord,ProcessEpisodeStatus,ProcessContextItem,ProcessContextKind,ProcessContextRole,make_process_episode_id
from mathgraph.projection import ProjectionCandidate,ProjectionRuleKind,make_projection_candidate_id
from mathgraph.reason_compression import ReasonObservation,ReasonObservationKind,extract_atoms_from_mapping,make_reason_observation_id
def _enum(n,v): return Enum(n,{x:x for x in v.split()},type=str)
StructureFamily=_enum("StructureFamily","ALGEBRAIC ORDER TOPOLOGICAL COMBINATORIAL LOGICAL COMPUTATIONAL GEOMETRIC ANALYTIC PROBABILISTIC DYNAMICAL GRAPHICAL CATEGORICAL MIXED UNKNOWN")
StructureObjectKind=_enum("StructureObjectKind","DOMAIN_CLAIM FORMAL_WORLD LAWBOOK_ENTRY LAWBOOK_STORE LAWBOOK_QUERY PROJECTION_CANDIDATE STRUCTURAL_IDENTITY STRUCTURAL_GRAPH STRUCTURAL_SIGNATURE HABIT REASON PROCESS_MEMORY PROOF_DIGESTION VERIFIER_FEEDBACK REPAIR_LOOP CURRICULUM ALCHEMICAL_TRACE AGENT_EXPERIENCE ROUTE_TELEMETRY RAW_EVENT UNKNOWN")
StructureFeatureKind=_enum("StructureFeatureKind","OPERATION RELATION ORDER_RELATION EQUIVALENCE CLOSURE QUOTIENT IDENTITY COMPOSITION MAP HOMOMORPHISM INVARIANT DIAGRAM PATH NEIGHBORHOOD LIMIT METRIC MEASURE PROBABILITY TRANSITION STATE RULE TYPE TERM FORMULA PROOF COUNTERMODEL OBSTRUCTION ROUTE UNKNOWN")
ProjectionCompatibility=_enum("ProjectionCompatibility","EXACT_SAME_STRUCTURE SAME_FAMILY CROSS_FAMILY_COMPATIBLE MIXED_STRUCTURE_COMPATIBLE NEEDS_ADAPTER NEEDS_FORMALIZATION TOO_WEAK TYPE_MISMATCH CONFLICT UNKNOWN")
TypedProjectionStatus=_enum("TypedProjectionStatus","CANDIDATE SCHEDULED BLOCKED_TYPE_MISMATCH BLOCKED_CONFLICT NEEDS_ADAPTER NEEDS_FORMALIZATION NEEDS_REVIEW ACCEPTED_ADVISORY REJECTED UNKNOWN")
StructureRegistryReportStatus=_enum("StructureRegistryReportStatus","EMPTY DESCRIBED MAPPINGS_FOUND PROJECTIONS_FOUND BLOCKED_PROJECTIONS REVIEWED HAS_WARNINGS HAS_CRITICALS ADVISORY_ONLY")
@dataclass
class StructureType:
 type_id:str; family:StructureFamily; name:str; description:str|None=None; parent_type_ids:tuple[str,...]=(); feature_kinds:tuple[str,...]=(); axioms_or_conditions:tuple[str,...]=(); compatible_family_hints:tuple[str,...]=(); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def to_dict(self): return {**self.__dict__,"family":self.family.value,"parent_type_ids":list(self.parent_type_ids),"feature_kinds":list(self.feature_kinds),"axioms_or_conditions":list(self.axioms_or_conditions),"compatible_family_hints":list(self.compatible_family_hints)}
 @classmethod
 def from_dict(c,d): return c(str(d["type_id"]),StructureFamily(str(d["family"])),str(d["name"]),_s(d.get("description")),tuple(d.get("parent_type_ids",())),tuple(d.get("feature_kinds",())),tuple(d.get("axioms_or_conditions",())),tuple(d.get("compatible_family_hints",())),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
@dataclass
class StructureDescriptor:
 descriptor_id:str; object_id:str|None=None; object_kind:StructureObjectKind=StructureObjectKind.UNKNOWN; families:tuple[str,...]=(); primary_family:StructureFamily=StructureFamily.UNKNOWN; feature_atoms:tuple[str,...]=(); feature_kinds:dict[str,str]=field(default_factory=dict); structure_type_ids:tuple[str,...]=(); confidence:float=0.0; evidence:dict[str,Any]=field(default_factory=dict); warnings:tuple[str,...]=(); criticals:tuple[str,...]=(); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def has_family(self,f): return (f.value if isinstance(f,StructureFamily) else str(f)) in self.families
 def to_dict(self): return {**self.__dict__,"object_kind":self.object_kind.value,"families":list(self.families),"primary_family":self.primary_family.value,"feature_atoms":list(self.feature_atoms),"structure_type_ids":list(self.structure_type_ids),"warnings":list(self.warnings),"criticals":list(self.criticals)}
 @classmethod
 def from_dict(c,d): return c(str(d["descriptor_id"]),_s(d.get("object_id")),StructureObjectKind(str(d.get("object_kind","UNKNOWN"))),tuple(d.get("families",())),StructureFamily(str(d.get("primary_family","UNKNOWN"))),tuple(d.get("feature_atoms",())),dict(d.get("feature_kinds",{})),tuple(d.get("structure_type_ids",())),float(d.get("confidence",0)),dict(d.get("evidence",{})),tuple(d.get("warnings",())),tuple(d.get("criticals",())),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
@dataclass
class StructureRegistryEntry:
 entry_id:str; descriptor:StructureDescriptor; status:str="CANDIDATE"; reviewed:bool=False; reviewer:str|None=None; review_reason:str|None=None; created_at:str=field(default_factory=lambda:_now()); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def is_reviewed(self): return self.reviewed
 def to_dict(self): return {**self.__dict__,"descriptor":self.descriptor.to_dict()}
 @classmethod
 def from_dict(c,d): return c(str(d["entry_id"]),StructureDescriptor.from_dict(d["descriptor"]),str(d.get("status","CANDIDATE")),bool(d.get("reviewed",False)),_s(d.get("reviewer")),_s(d.get("review_reason")),str(d.get("created_at") or _now()),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
@dataclass
class StructureMapping:
 mapping_id:str; source_descriptor_id:str; target_descriptor_id:str; source_object_id:str|None=None; target_object_id:str|None=None; source_family:StructureFamily=StructureFamily.UNKNOWN; target_family:StructureFamily=StructureFamily.UNKNOWN; compatibility:ProjectionCompatibility=ProjectionCompatibility.UNKNOWN; shared_features:tuple[str,...]=(); missing_features:tuple[str,...]=(); conflict_features:tuple[str,...]=(); compatibility_score:float=0.0; reason:str|None=None; warnings:tuple[str,...]=(); criticals:tuple[str,...]=(); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def is_schedulable(self): return self.compatibility in {ProjectionCompatibility.EXACT_SAME_STRUCTURE,ProjectionCompatibility.SAME_FAMILY,ProjectionCompatibility.CROSS_FAMILY_COMPATIBLE,ProjectionCompatibility.MIXED_STRUCTURE_COMPATIBLE,ProjectionCompatibility.NEEDS_ADAPTER,ProjectionCompatibility.NEEDS_FORMALIZATION}
 def to_dict(self): return {**self.__dict__,"source_family":self.source_family.value,"target_family":self.target_family.value,"compatibility":self.compatibility.value,"shared_features":list(self.shared_features),"missing_features":list(self.missing_features),"conflict_features":list(self.conflict_features),"warnings":list(self.warnings),"criticals":list(self.criticals)}
 @classmethod
 def from_dict(c,d): return c(str(d["mapping_id"]),str(d["source_descriptor_id"]),str(d["target_descriptor_id"]),_s(d.get("source_object_id")),_s(d.get("target_object_id")),StructureFamily(str(d.get("source_family","UNKNOWN"))),StructureFamily(str(d.get("target_family","UNKNOWN"))),ProjectionCompatibility(str(d.get("compatibility","UNKNOWN"))),tuple(d.get("shared_features",())),tuple(d.get("missing_features",())),tuple(d.get("conflict_features",())),float(d.get("compatibility_score",0)),_s(d.get("reason")),tuple(d.get("warnings",())),tuple(d.get("criticals",())),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
@dataclass
class TypedProjectionCandidate:
 candidate_id:str; mapping_id:str; source_object_id:str|None=None; target_object_id:str|None=None; source_family:StructureFamily=StructureFamily.UNKNOWN; target_family:StructureFamily=StructureFamily.UNKNOWN; compatibility:ProjectionCompatibility=ProjectionCompatibility.UNKNOWN; status:TypedProjectionStatus=TypedProjectionStatus.CANDIDATE; route:str|None=None; projection_kind:str|None=None; priority:float=0.0; compatibility_score:float=0.0; required_adapter:str|None=None; required_review:bool=True; reason:str|None=None; warnings:tuple[str,...]=(); criticals:tuple[str,...]=(); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def is_blocked(self): return self.status in {TypedProjectionStatus.BLOCKED_TYPE_MISMATCH,TypedProjectionStatus.BLOCKED_CONFLICT}
 def is_schedulable(self): return not self.is_blocked() and self.status not in {TypedProjectionStatus.REJECTED,TypedProjectionStatus.UNKNOWN}
 def to_dict(self): return {**self.__dict__,"source_family":self.source_family.value,"target_family":self.target_family.value,"compatibility":self.compatibility.value,"status":self.status.value,"warnings":list(self.warnings),"criticals":list(self.criticals)}
 @classmethod
 def from_dict(c,d): return c(str(d["candidate_id"]),str(d["mapping_id"]),_s(d.get("source_object_id")),_s(d.get("target_object_id")),StructureFamily(str(d.get("source_family","UNKNOWN"))),StructureFamily(str(d.get("target_family","UNKNOWN"))),ProjectionCompatibility(str(d.get("compatibility","UNKNOWN"))),TypedProjectionStatus(str(d.get("status","CANDIDATE"))),_s(d.get("route")),_s(d.get("projection_kind")),float(d.get("priority",0)),float(d.get("compatibility_score",0)),_s(d.get("required_adapter")),bool(d.get("required_review",True)),_s(d.get("reason")),tuple(d.get("warnings",())),tuple(d.get("criticals",())),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
@dataclass
class StructureRegistryStore:
 store_id:str; structure_types:list[StructureType]=field(default_factory=list); entries:list[StructureRegistryEntry]=field(default_factory=list); mappings:list[StructureMapping]=field(default_factory=list); typed_projection_candidates:list[TypedProjectionCandidate]=field(default_factory=list); created_at:str=field(default_factory=lambda:_now()); summary:dict[str,Any]=field(default_factory=dict); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def type_count(self): return len(self.structure_types)
 def entry_count(self): return len(self.entries)
 def descriptor_count(self): return len(self.entries)
 def mapping_count(self): return len(self.mappings)
 def projection_candidate_count(self): return len(self.typed_projection_candidates)
 def add_type(self,x): self.structure_types.append(x)
 def add_entry(self,x): self.entries.append(x)
 def add_mapping(self,x): self.mappings.append(x)
 def add_projection_candidate(self,x): self.typed_projection_candidates.append(x)
 def find_descriptors_by_family(self,f): return [e.descriptor for e in self.entries if e.descriptor.has_family(f)]
 def summarize(self):
  self.summary={"type_total":len(self.structure_types),"entry_total":len(self.entries),"descriptor_total":len(self.entries),"mapping_total":len(self.mappings),"projection_candidate_total":len(self.typed_projection_candidates),"family_counts":dict(Counter(e.descriptor.primary_family.value for e in self.entries)),"compatibility_counts":dict(Counter(m.compatibility.value for m in self.mappings)),"blocked_projection_count":sum(c.is_blocked() for c in self.typed_projection_candidates),"needs_adapter_count":sum(c.status==TypedProjectionStatus.NEEDS_ADAPTER for c in self.typed_projection_candidates),"needs_formalization_count":sum(c.status==TypedProjectionStatus.NEEDS_FORMALIZATION for c in self.typed_projection_candidates),"schedulable_projection_count":sum(c.is_schedulable() for c in self.typed_projection_candidates),"critical_count":sum(len(e.descriptor.criticals) for e in self.entries)+sum(len(m.criticals) for m in self.mappings)+sum(len(c.criticals) for c in self.typed_projection_candidates)}; return dict(self.summary)
 def to_dict(self): return {"store_id":self.store_id,"structure_types":[x.to_dict() for x in self.structure_types],"entries":[x.to_dict() for x in self.entries],"mappings":[x.to_dict() for x in self.mappings],"typed_projection_candidates":[x.to_dict() for x in self.typed_projection_candidates],"created_at":self.created_at,"summary":dict(self.summary),"metadata":dict(self.metadata),"advisory":self.advisory}
 @classmethod
 def from_dict(c,d): return c(str(d["store_id"]),[StructureType.from_dict(x) for x in d.get("structure_types",[])],[StructureRegistryEntry.from_dict(x) for x in d.get("entries",[])],[StructureMapping.from_dict(x) for x in d.get("mappings",[])],[TypedProjectionCandidate.from_dict(x) for x in d.get("typed_projection_candidates",[])],str(d.get("created_at") or _now()),dict(d.get("summary",{})),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
 def write_json(self,p): _w(p,self.to_json()+"\n")
 @classmethod
 def read_json(c,p): return c.from_json(Path(p).read_text())
 def write_jsonl(self,p): _w(p,self.to_json()+"\n")
 @classmethod
 def read_jsonl(c,p): return [c.from_json(x) for x in Path(p).read_text().splitlines() if x.strip()]
@dataclass
class StructureRegistryReport:
 report_id:str; descriptors:list[StructureDescriptor]=field(default_factory=list); mappings:list[StructureMapping]=field(default_factory=list); typed_projection_candidates:list[TypedProjectionCandidate]=field(default_factory=list); store:StructureRegistryStore|None=None; status:StructureRegistryReportStatus=StructureRegistryReportStatus.EMPTY; created_at:str=field(default_factory=lambda:_now()); summary:dict[str,Any]=field(default_factory=dict); metadata:dict[str,Any]=field(default_factory=lambda:{"typed_projection_advisory_only":True}); advisory:bool=True
 def descriptor_count(self): return len(self.descriptors)
 def mapping_count(self): return len(self.mappings)
 def projection_candidate_count(self): return len(self.typed_projection_candidates)
 def critical_count(self): return sum(len(x.criticals) for x in self.descriptors)+sum(len(x.criticals) for x in self.mappings)+sum(len(x.criticals) for x in self.typed_projection_candidates)
 def summarize(self): self.summary={"descriptor_total":len(self.descriptors),"mapping_total":len(self.mappings),"projection_candidate_total":len(self.typed_projection_candidates),"critical_count":self.critical_count(),**(self.store.summary if self.store else {})}; return dict(self.summary)
 def to_dict(self): return {"report_id":self.report_id,"descriptors":[x.to_dict() for x in self.descriptors],"mappings":[x.to_dict() for x in self.mappings],"typed_projection_candidates":[x.to_dict() for x in self.typed_projection_candidates],"store":self.store.to_dict() if self.store else None,"status":self.status.value,"created_at":self.created_at,"summary":dict(self.summary),"metadata":dict(self.metadata),"advisory":self.advisory}
 @classmethod
 def from_dict(c,d): return c(str(d["report_id"]),[StructureDescriptor.from_dict(x) for x in d.get("descriptors",[])],[StructureMapping.from_dict(x) for x in d.get("mappings",[])],[TypedProjectionCandidate.from_dict(x) for x in d.get("typed_projection_candidates",[])],StructureRegistryStore.from_dict(d["store"]) if d.get("store") else None,StructureRegistryReportStatus(str(d.get("status","EMPTY"))),str(d.get("created_at") or _now()),dict(d.get("summary",{})),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
 def write_json(self,p): _w(p,self.to_json()+"\n")
 @classmethod
 def read_json(c,p): return c.from_json(Path(p).read_text())
 def write_jsonl(self,p): _w(p,self.to_json()+"\n")
 @classmethod
 def read_jsonl(c,p): return [c.from_json(x) for x in Path(p).read_text().splitlines() if x.strip()]
def make_structure_type_id(*x): return content_id("structure-type",x)
def make_structure_descriptor_id(*x): return content_id("structure-descriptor",x)
def make_structure_registry_entry_id(*x): return content_id("structure-entry",x)
def make_structure_mapping_id(*x): return content_id("structure-mapping",x)
def make_typed_projection_candidate_id(*x): return content_id("typed-projection",x)
def make_structure_registry_store_id(*x): return content_id("structure-store",x)
def make_structure_registry_report_id(*x): return content_id("structure-report",x)
def default_structure_types():
 rows=[("magma_like","ALGEBRAIC",("OPERATION","TERM","FORMULA")),("equational_theory_like","MIXED",("FORMULA","PROOF","COUNTERMODEL")),("order_like","ORDER",("ORDER_RELATION","RELATION")),("graph_like","GRAPHICAL",("DIAGRAM","PATH")),("transition_system_like","DYNAMICAL",("STATE","TRANSITION","RULE")),("proof_system_like","LOGICAL",("PROOF","RULE","FORMULA")),("projection_system_like","COMPUTATIONAL",("MAP","ROUTE","RULE")),("process_trace_like","COMPUTATIONAL",("TRANSITION","STATE","ROUTE")),("metric_like","ANALYTIC",("METRIC","LIMIT")),("probability_like","PROBABILISTIC",("PROBABILITY","MEASURE")),("topology_like","TOPOLOGICAL",("NEIGHBORHOOD","LIMIT","CLOSURE")),("category_like","CATEGORICAL",("MAP","COMPOSITION","DIAGRAM")),("mixed_formal_world_like","MIXED",("TYPE","RELATION","OPERATION","RULE"))]
 return [StructureType(make_structure_type_id(n),StructureFamily(f),n,feature_kinds=k) for n,f,k in rows]
def normalize_structure_atom(v):
 s=re.sub(r"[^a-z0-9_:/=\\-]+","_",str(v).strip().lower().replace(" ","_")).strip("_")
 return s[:80]+"_"+content_id("atom",s)[-8:] if len(s)>96 else s or "unknown"
def classify_structure_feature(a,source_key=None):
 t=(str(source_key or "")+" "+a).lower()
 rules=[(("op","operation","magma","binary"),"OPERATION"),(("order","leq","partial_order"),"ORDER_RELATION"),(("quotient",),"QUOTIENT"),(("equal","equivalence"),"EQUIVALENCE"),(("closure","closed"),"CLOSURE"),(("compose","composition"),"COMPOSITION"),(("hom",),"HOMOMORPHISM"),(("map","morphism"),"MAP"),(("invariant","preserved"),"INVARIANT"),(("graph","node","edge"),"DIAGRAM"),(("path",),"PATH"),(("neighborhood",),"NEIGHBORHOOD"),(("metric","distance"),"METRIC"),(("limit",),"LIMIT"),(("measure",),"MEASURE"),(("probability",),"PROBABILITY"),(("transition",),"TRANSITION"),(("state",),"STATE"),(("proof","theorem","lemma"),"PROOF"),(("countermodel","table","witness"),"COUNTERMODEL"),(("obstruction","failure"),"OBSTRUCTION"),(("route","scheduler"),"ROUTE"),(("type","formal_world"),"TYPE"),(("term",),"TERM"),(("formula","equation","claim"),"FORMULA"),(("relation","predicate"),"RELATION")]
 for keys,k in rules:
  if any(x in t for x in keys): return StructureFeatureKind(k)
 return StructureFeatureKind.UNKNOWN
def extract_structure_features_from_mapping(d,*,max_depth=4,max_items=200):
 out=[]; kinds={}
 def walk(x,key=None,depth=0):
  if depth>max_depth or len(out)>=max_items:return
  if isinstance(x,Mapping):
   for k,v in x.items():
    atom=normalize_structure_atom(k); out.append(atom); kinds[atom]=classify_structure_feature(atom,str(k)).value; walk(v,str(k),depth+1)
  elif isinstance(x,(list,tuple,set)):
   for v in list(x)[:max_items]: walk(v,key,depth+1)
  else:
   atom=normalize_structure_atom(getattr(x,"value",x)); out.append(atom); kinds[atom]=classify_structure_feature(atom,key).value
 walk(d); return tuple(dict.fromkeys(out)),kinds
def infer_structure_families(atoms,kinds,metadata=None):
 vals=set(kinds.values()); fam=[]
 if {"OPERATION"}<=vals and vals&{"TERM","FORMULA"}: fam.append("ALGEBRAIC")
 if vals&{"FORMULA","PROOF","COUNTERMODEL","OBSTRUCTION"}: fam.append("LOGICAL")
 if "ORDER_RELATION" in vals: fam.append("ORDER")
 if vals&{"PATH","DIAGRAM"}: fam.append("GRAPHICAL")
 if vals&{"STATE","TRANSITION"}: fam.append("DYNAMICAL" if "STATE" in vals else "COMPUTATIONAL")
 if vals&{"METRIC","LIMIT"}: fam.append("ANALYTIC")
 if vals&{"PROBABILITY","MEASURE"}: fam.append("PROBABILISTIC")
 if vals&{"CLOSURE","NEIGHBORHOOD"}: fam.append("TOPOLOGICAL")
 if vals&{"COMPOSITION","HOMOMORPHISM"} and "DIAGRAM" in vals: fam.append("CATEGORICAL")
 fam=tuple(dict.fromkeys(fam)); primary=StructureFamily.MIXED if len(fam)>1 and not (len(fam)==2 and "ALGEBRAIC" in fam and "LOGICAL" in fam) else StructureFamily(fam[0]) if fam else StructureFamily.UNKNOWN
 return fam,primary,min(1.0,.15*len(vals)+.2*len(fam))
def structure_descriptor_from_mapping(d,*,object_id=None,object_kind=StructureObjectKind.RAW_EVENT):
 atoms,kinds=extract_structure_features_from_mapping(d); fam,primary,conf=infer_structure_families(atoms,kinds,d)
 return StructureDescriptor(make_structure_descriptor_id(object_id or d,object_kind.value),object_id,object_kind,fam,primary,atoms,kinds,confidence=conf,evidence={"atom_count":len(atoms)},warnings=("unknown family",) if primary==StructureFamily.UNKNOWN else (),metadata={"typed_projection_advisory_only":True})
def _desc(o,kind,oid=None): return structure_descriptor_from_mapping(o.to_dict() if hasattr(o,"to_dict") else dict(o),object_id=oid or getattr(o,"entry_id",getattr(o,"candidate_id",getattr(o,"report_id",getattr(o,"episode_id",None)))),object_kind=kind)
def structure_descriptor_from_domain_claim(x): return _desc(x,StructureObjectKind.DOMAIN_CLAIM,getattr(x,"claim_id",None))
def structure_descriptor_from_lawbook_entry(x): return _desc(x,StructureObjectKind.LAWBOOK_ENTRY,x.entry_id)
def structure_descriptors_from_lawbook_store(x): return [structure_descriptor_from_lawbook_entry(e) for e in x.entries]
def structure_descriptors_from_lawbook_query_report(x): return [_desc(a,StructureObjectKind.LAWBOOK_QUERY,a.answer_id) for a in x.answers]
def structure_descriptor_from_projection_candidate(x): return _desc(x,StructureObjectKind.PROJECTION_CANDIDATE,x.candidate_id)
def structure_descriptors_from_structural_identity_report(x): return [_desc(c,StructureObjectKind.STRUCTURAL_IDENTITY,c.candidate_id) for c in x.merge_candidates]
def structure_descriptor_from_structural_graph(x): return _desc(x,StructureObjectKind.STRUCTURAL_GRAPH,x.graph_id)
def structure_descriptor_from_structural_signature(x): return _desc(x,StructureObjectKind.STRUCTURAL_SIGNATURE,x.signature_id)
def structure_descriptors_from_habit_report(x): return [_desc(r,StructureObjectKind.HABIT,r.rule_id) for r in x.rules]
def structure_descriptor_from_habit_rule(x): return _desc(x,StructureObjectKind.HABIT,x.rule_id)
def structure_descriptors_from_reason_report(x): return [_desc(n,StructureObjectKind.REASON,n.reason_id) for n in x.reason_nodes]
def structure_descriptor_from_reason_node(x): return _desc(x,StructureObjectKind.REASON,x.reason_id)
def structure_descriptors_from_process_memory_report(x): return [structure_descriptor_from_process_episode(e) for e in (x.store.episodes if x.store else [])]
def structure_descriptor_from_process_episode(x): return _desc(x,StructureObjectKind.PROCESS_MEMORY,x.episode_id)
def structure_descriptor_from_proof_digestion_trace(x): return _desc(x,StructureObjectKind.PROOF_DIGESTION,x.trace_id)
def structure_descriptor_from_verifier_feedback(x): return _desc(x,StructureObjectKind.VERIFIER_FEEDBACK,x.feedback_id)
def structure_descriptor_from_repair_loop(x): return _desc(x,StructureObjectKind.REPAIR_LOOP,x.trace_id)
def structure_descriptors_from_curriculum(x): return [structure_descriptor_from_curriculum_stage(s) for s in x.stages]
def structure_descriptor_from_curriculum_stage(x): return _desc(x,StructureObjectKind.CURRICULUM,x.stage_id)
def structure_descriptor_from_alchemical_trace(x): return _desc(x,StructureObjectKind.ALCHEMICAL_TRACE,x.trace_id)
def structure_descriptor_from_agent_experience(x): return _desc(x,StructureObjectKind.AGENT_EXPERIENCE,x.experience_id)
def structure_descriptor_from_route_telemetry_event(x): return structure_descriptor_from_mapping(x,object_id=_s(x.get("event_id")),object_kind=StructureObjectKind.ROUTE_TELEMETRY)
def structure_descriptors_from_object(o):
 from mathgraph.domain_claims import DomainClaim
 from mathgraph.habit_rules import HabitFormationReport,HabitRule
 from mathgraph.lawbook_query import LawbookQueryReport
 from mathgraph.proof_digestion import ProofDigestionTrace
 from mathgraph.reason_compression import ReasonCompressionReport,ReasonNode
 from mathgraph.structural_identity import StructuralGraph,StructuralIdentityReport,StructuralSignature
 from mathgraph.verifier_feedback import RepairLoopTrace,VerifierFeedback
 if isinstance(o,StructureDescriptor): return [o]
 if isinstance(o,DomainClaim): return [structure_descriptor_from_domain_claim(o)]
 if isinstance(o,LawbookEntry): return [structure_descriptor_from_lawbook_entry(o)]
 if isinstance(o,LawbookStore): return structure_descriptors_from_lawbook_store(o)
 if isinstance(o,LawbookQueryReport): return structure_descriptors_from_lawbook_query_report(o)
 if isinstance(o,ProjectionCandidate): return [structure_descriptor_from_projection_candidate(o)]
 if isinstance(o,StructuralIdentityReport): return structure_descriptors_from_structural_identity_report(o)
 if isinstance(o,StructuralGraph): return [structure_descriptor_from_structural_graph(o)]
 if isinstance(o,StructuralSignature): return [structure_descriptor_from_structural_signature(o)]
 if isinstance(o,HabitFormationReport): return structure_descriptors_from_habit_report(o)
 if isinstance(o,HabitRule): return [structure_descriptor_from_habit_rule(o)]
 if isinstance(o,ReasonCompressionReport): return structure_descriptors_from_reason_report(o)
 if isinstance(o,ReasonNode): return [structure_descriptor_from_reason_node(o)]
 if isinstance(o,ProcessEpisodeRecord): return [structure_descriptor_from_process_episode(o)]
 if hasattr(o,"store") and o.__class__.__name__=="ProcessMemoryReport": return structure_descriptors_from_process_memory_report(o)
 if isinstance(o,ProofDigestionTrace): return [structure_descriptor_from_proof_digestion_trace(o)]
 if isinstance(o,VerifierFeedback): return [structure_descriptor_from_verifier_feedback(o)]
 if isinstance(o,RepairLoopTrace): return [structure_descriptor_from_repair_loop(o)]
 if isinstance(o,ContinuationCurriculum): return structure_descriptors_from_curriculum(o)
 if isinstance(o,CurriculumStage): return [structure_descriptor_from_curriculum_stage(o)]
 if isinstance(o,AlchemicalTrace): return [structure_descriptor_from_alchemical_trace(o)]
 if isinstance(o,AgentExperience): return [structure_descriptor_from_agent_experience(o)]
 if isinstance(o,Mapping): return [structure_descriptor_from_route_telemetry_event(o)]
 return []
_cross={frozenset(("ALGEBRAIC","LOGICAL")),frozenset(("ALGEBRAIC","CATEGORICAL")),frozenset(("ORDER","TOPOLOGICAL")),frozenset(("GRAPHICAL","COMBINATORIAL")),frozenset(("DYNAMICAL","COMPUTATIONAL")),frozenset(("PROBABILISTIC","ANALYTIC")),frozenset(("LOGICAL","COMPUTATIONAL"))}
def compute_structure_mapping(s,t):
 shared=tuple(sorted(set(s.feature_atoms)&set(t.feature_atoms))); missing=tuple(sorted(set(t.feature_atoms)-set(s.feature_atoms))); union=max(1,len(set(s.feature_atoms)|set(t.feature_atoms))); score=len(shared)/union
 conflicts=()
 text=" ".join(s.feature_atoms+t.feature_atoms)
 if "verified_proof" in text and "invalid" in text: conflicts=("proof_invalid_conflict",)
 if conflicts: comp=ProjectionCompatibility.CONFLICT
 elif len(s.feature_atoms)<2: comp=ProjectionCompatibility.TOO_WEAK
 elif s.primary_family==t.primary_family and s.primary_family!=StructureFamily.UNKNOWN and score>=.5: comp=ProjectionCompatibility.EXACT_SAME_STRUCTURE
 elif s.primary_family==t.primary_family and s.primary_family!=StructureFamily.UNKNOWN: comp=ProjectionCompatibility.SAME_FAMILY
 elif StructureFamily.MIXED in {s.primary_family,t.primary_family} and shared: comp=ProjectionCompatibility.MIXED_STRUCTURE_COMPATIBLE
 elif frozenset((s.primary_family.value,t.primary_family.value)) in _cross and shared: comp=ProjectionCompatibility.CROSS_FAMILY_COMPATIBLE
 elif frozenset((s.primary_family.value,t.primary_family.value)) in _cross: comp=ProjectionCompatibility.NEEDS_ADAPTER
 elif s.primary_family==StructureFamily.UNKNOWN or t.primary_family==StructureFamily.LOGICAL and s.object_kind==StructureObjectKind.RAW_EVENT: comp=ProjectionCompatibility.NEEDS_FORMALIZATION
 else: comp=ProjectionCompatibility.TYPE_MISMATCH
 return StructureMapping(make_structure_mapping_id(s.descriptor_id,t.descriptor_id),s.descriptor_id,t.descriptor_id,s.object_id,t.object_id,s.primary_family,t.primary_family,comp,shared,missing,conflicts,score,reason=comp.value,warnings=("no shared features",) if not shared else (),metadata={"typed_projection_advisory_only":True})
def build_structure_mappings(ds,*,min_score=.2,max_pairs=2000):
 out=[]
 for i,s in enumerate(ds):
  for t in ds[i+1:]:
   if len(out)>=max_pairs:return out
   m=compute_structure_mapping(s,t)
   if m.compatibility_score>=min_score or m.compatibility in {ProjectionCompatibility.NEEDS_ADAPTER,ProjectionCompatibility.NEEDS_FORMALIZATION,ProjectionCompatibility.TYPE_MISMATCH,ProjectionCompatibility.CONFLICT}: out.append(m)
 return out
def typed_projection_candidate_from_mapping(m):
 status=TypedProjectionStatus.CANDIDATE; route="typed_projection_same_family"; priority=m.compatibility_score; adapter=None
 if m.compatibility in {ProjectionCompatibility.CROSS_FAMILY_COMPATIBLE,ProjectionCompatibility.MIXED_STRUCTURE_COMPATIBLE}: status=TypedProjectionStatus.NEEDS_REVIEW; route="typed_projection_cross_family"; priority=.75*m.compatibility_score
 elif m.compatibility==ProjectionCompatibility.NEEDS_ADAPTER: status=TypedProjectionStatus.NEEDS_ADAPTER; route=None; priority=.5*m.compatibility_score; adapter="formal-world adapter"
 elif m.compatibility==ProjectionCompatibility.NEEDS_FORMALIZATION: status=TypedProjectionStatus.NEEDS_FORMALIZATION; route=None; priority=.4*m.compatibility_score
 elif m.compatibility==ProjectionCompatibility.TYPE_MISMATCH: status=TypedProjectionStatus.BLOCKED_TYPE_MISMATCH; route=None; priority=0
 elif m.compatibility==ProjectionCompatibility.CONFLICT: status=TypedProjectionStatus.BLOCKED_CONFLICT; route=None; priority=0
 elif m.compatibility==ProjectionCompatibility.TOO_WEAK: status=TypedProjectionStatus.NEEDS_REVIEW; route=None; priority=0
 return TypedProjectionCandidate(make_typed_projection_candidate_id(m.mapping_id),m.mapping_id,m.source_object_id,m.target_object_id,m.source_family,m.target_family,m.compatibility,status,route,None,priority,m.compatibility_score,adapter,True,m.reason,metadata={"typed_projection_advisory_only":True},advisory=True)
def build_typed_projection_candidates(ms,*,min_score=.2): return [typed_projection_candidate_from_mapping(m) for m in ms if m.compatibility_score>=min_score or m.compatibility in {ProjectionCompatibility.NEEDS_ADAPTER,ProjectionCompatibility.NEEDS_FORMALIZATION,ProjectionCompatibility.TYPE_MISMATCH,ProjectionCompatibility.CONFLICT}]
def build_structure_registry_store(objects=(),descriptors=(),mappings=(),typed_projection_candidates=(),include_default_types=True,build_mappings=True,build_projection_candidates=True,min_mapping_score=.2):
 ds=list(descriptors)+[d for o in objects for d in structure_descriptors_from_object(o)]; ded={d.descriptor_id:d for d in ds}; entries=[StructureRegistryEntry(make_structure_registry_entry_id(d.descriptor_id),d) for d in ded.values()]; ms=list(mappings) or (build_structure_mappings(list(ded.values()),min_score=min_mapping_score) if build_mappings else []); cs=list(typed_projection_candidates) or (build_typed_projection_candidates(ms,min_score=min_mapping_score) if build_projection_candidates else []); s=StructureRegistryStore(make_structure_registry_store_id(sorted(ded)),default_structure_types() if include_default_types else [],entries,ms,cs); s.summarize(); return s
def build_structure_registry_report(objects=(),descriptors=(),*,build_mappings=True,build_projection_candidates=True,min_mapping_score=.2):
 s=build_structure_registry_store(objects,descriptors,build_mappings=build_mappings,build_projection_candidates=build_projection_candidates,min_mapping_score=min_mapping_score); r=StructureRegistryReport(make_structure_registry_report_id(s.store_id),[e.descriptor for e in s.entries],s.mappings,s.typed_projection_candidates,s); r.summarize(); r.status=StructureRegistryReportStatus.EMPTY if not r.descriptors else StructureRegistryReportStatus.HAS_CRITICALS if r.critical_count() else StructureRegistryReportStatus.BLOCKED_PROJECTIONS if any(c.is_blocked() for c in r.typed_projection_candidates) else StructureRegistryReportStatus.PROJECTIONS_FOUND if r.typed_projection_candidates else StructureRegistryReportStatus.MAPPINGS_FOUND if r.mappings else StructureRegistryReportStatus.DESCRIBED; return r
def structure_report_to_lawbook_candidates(r): return [LawbookEntry(make_lawbook_entry_id("structure",r.report_id,c.candidate_id),LawbookEntryKind.ROUTE_RULE_ENTRY,LawbookEntryStatus.CANDIDATE,metadata={"structure_registry_not_truth":True,"structure_registry_report_id":r.report_id,"typed_projection_advisory_only":True},advisory=True) for c in r.typed_projection_candidates]
def structure_report_to_projection_candidates(r): return [ProjectionCandidate(make_projection_candidate_id({"source_claim_id":c.source_object_id,"target_claim_id":c.target_object_id,"route":c.route or "typed"}),c.source_object_id,c.target_object_id,rule_kind=ProjectionRuleKind.ADVISORY_SIMILARITY,confidence=c.priority,reason=c.reason,metadata={"typed_projection_advisory_only":True}) for c in r.typed_projection_candidates if c.is_schedulable() and not c.is_blocked() and c.route]
def structure_report_to_continuation_outputs(r): return [ContinuationActionOutput(make_continuation_output_id({"typed":c.candidate_id}),"structure_registry",ContinuationOutputKind.TASK,ContinuationActionStatus.ADVISORY_ONLY,task_payload={"task":"project structure" if c.is_schedulable() and not c.is_blocked() else "review typed projection","candidate_id":c.candidate_id},advisory=True) for c in r.typed_projection_candidates]
def structure_report_to_curriculum(r):
 stages=[CurriculumStage(make_curriculum_stage_id("structure",c.candidate_id),CurriculumStageKind.PROJECTION_TASK if c.is_schedulable() and not c.is_blocked() else CurriculumStageKind.RESIDUAL_REVIEW,CurriculumStageStatus.ADVISORY_ONLY,title="Typed projection",metadata={"typed_projection_id":c.candidate_id},advisory=True) for c in r.typed_projection_candidates]
 return ContinuationCurriculum(make_curriculum_id("structure",r.report_id),strategy=CurriculumBuildStrategy.MIXED,stages=stages,status=CurriculumTraceStatus.TASKS_EMITTED if stages else CurriculumTraceStatus.EMPTY,metadata={"advisory_only":True})
def structure_report_to_discovery_value_scores(r):
 out=[]
 for c in r.typed_projection_candidates:
  sig=DiscoveryValueSignal(content_id("structure-signal",c.candidate_id),DiscoveryValueSignalKind.REUSE_VALUE,c.priority if not c.is_blocked() else 0,reason=c.status.value,source_object_kind=DiscoveryValueObjectKind.RAW_TASK); s=DiscoveryValueScore(content_id("structure-score",c.candidate_id),c.candidate_id,DiscoveryValueObjectKind.RAW_TASK,signals=[sig],metadata={"typed_projection_advisory_only":True}); s.recompute(); out.append(s)
 return out
def structure_report_to_process_episodes(r): return [ProcessEpisodeRecord(make_process_episode_id("structure",c.candidate_id),ProcessEpisodeStatus.ADVISORY_ONLY,contexts=[ProcessContextItem(content_id("structure-context",c.candidate_id),ProcessContextKind.PROJECTION,ProcessContextRole.CANDIDATE_ONLY,c.candidate_id)],advisory=True) for c in r.typed_projection_candidates]
def structure_report_to_habit_observations(r): return [HabitObservation(content_id("structure-habit",c.candidate_id),HabitObservationKind.STRUCTURAL_IDENTITY,route=c.route or c.status.value,outcome=HabitOutcome.STRUCTURAL_REVIEW if not c.is_blocked() else HabitOutcome.KILLED_ROUTE,object_id=c.candidate_id,metadata={"typed_projection_advisory_only":True}) for c in r.typed_projection_candidates]
def structure_report_to_reason_observations(r): return [ReasonObservation(make_reason_observation_id("structure",d.descriptor_id),ReasonObservationKind.STRUCTURAL_IDENTITY,d.descriptor_id,"structure_registry",*extract_atoms_from_mapping(d.to_dict()),metadata={"typed_projection_advisory_only":True}) for d in r.descriptors]
def structure_report_to_structural_identity_objects(r): return [{"descriptor_id":d.descriptor_id,"family":d.primary_family.value,"features":list(d.feature_atoms),"typed_projection_advisory_only":True} for d in r.descriptors]
def structure_report_to_alchemical_trace(r):
 t=AlchemicalTrace(make_alchemical_trace_id("structure",r.report_id))
 for p in (AlchemicalPhase.RAW_MATTER,AlchemicalPhase.CALCINATION,AlchemicalPhase.SOLUTION,AlchemicalPhase.SUBLIMATION,AlchemicalPhase.DESCENSION,AlchemicalPhase.DISTILLATION): t.add_step(phase=p,status=AlchemicalStatus.ADVISORY_ONLY)
 return t
def structure_report_to_agent_experiences(r,agent_id=None): return [AgentExperience(content_id("structure-exp",c.candidate_id),agent_id or "structure-registry",None,None,"structure_registry",None,AgentExperienceOutcome.ADVISORY_ONLY,metadata={"typed_projection_id":c.candidate_id}) for c in r.typed_projection_candidates]
def structure_report_to_route_telemetry_events(r): return [{"event_id":content_id("structure-telemetry",c.candidate_id),"route_kind":"typed_projection","outcome":c.status.value,"typed_projection_advisory_only":True} for c in r.typed_projection_candidates]
def audit_structure_descriptor(d):
 fs=[]
 if not d.advisory: fs.append(_f("CRITICAL","STRUCTURE_DESCRIPTOR_NON_ADVISORY","descriptor non-advisory",d.descriptor_id))
 if d.primary_family==StructureFamily.UNKNOWN and d.confidence<.5: fs.append(_f("WARNING","STRUCTURE_UNKNOWN_FAMILY","descriptor has unknown family",d.descriptor_id))
 return fs
def audit_structure_mapping(m):
 fs=[]
 if not m.advisory: fs.append(_f("CRITICAL","STRUCTURE_MAPPING_NON_ADVISORY","mapping non-advisory",m.mapping_id))
 if m.compatibility_score<.2: fs.append(_f("WARNING","STRUCTURE_LOW_COMPATIBILITY","mapping low compatibility",m.mapping_id))
 if not m.shared_features: fs.append(_f("WARNING","STRUCTURE_NO_SHARED_FEATURES","mapping has no shared features",m.mapping_id))
 return fs
def audit_typed_projection_candidate(c):
 fs=[]
 if not c.advisory: fs.append(_f("CRITICAL","TYPED_PROJECTION_NON_ADVISORY","typed projection non-advisory",c.candidate_id))
 if c.metadata.get("terminal_form") or c.metadata.get("certificate_id"): fs.append(_f("CRITICAL","TYPED_PROJECTION_AS_TRUTH","typed projection carries truth field",c.candidate_id))
 if c.is_blocked() and c.route: fs.append(_f("CRITICAL","TYPED_PROJECTION_BLOCKED_SCHEDULED","blocked projection has direct route",c.candidate_id))
 if c.status in {TypedProjectionStatus.NEEDS_ADAPTER,TypedProjectionStatus.NEEDS_FORMALIZATION} and not c.required_review: fs.append(_f("WARNING","TYPED_PROJECTION_REVIEW_REQUIRED","adapter/formalization lacks review",c.candidate_id))
 return fs
def audit_structure_registry_report(r): return [x for d in r.descriptors for x in audit_structure_descriptor(d)]+[x for m in r.mappings for x in audit_structure_mapping(m)]+[x for c in r.typed_projection_candidates for x in audit_typed_projection_candidate(c)]
def _s(x): return None if x is None else str(x)
def _now(): return datetime.now(timezone.utc).isoformat()
def _j(x): return json.dumps(x,sort_keys=True,separators=(",",":"))
def _w(p,t): path=Path(p); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(t,encoding="utf-8")
def _f(sev,code,msg,obj): return {"severity":sev,"code":code,"message":msg,"object_id":obj}
