"""Deterministic advisory intake for informal mathematical and scientific text."""
from __future__ import annotations
import json,re
from collections import Counter
from dataclasses import MISSING,dataclass,field
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
from mathgraph.lawbook import LawbookEntry,LawbookEntryKind,LawbookEntryStatus,make_lawbook_entry_id
from mathgraph.process_memory import ProcessContextItem,ProcessContextKind,ProcessContextRole,ProcessEpisodeRecord,ProcessEpisodeStatus,make_process_episode_id
from mathgraph.reason_compression import ReasonObservation,ReasonObservationKind,extract_atoms_from_mapping,make_reason_observation_id
from mathgraph.role_objects import RoleSignature,RoleSourceKind,RoleObjectKind,make_role_signature_id
from mathgraph.structural_analogy import AnalogySource,AnalogySourceKind,analogy_source_from_mapping
from mathgraph.structure_registry import StructureObjectKind,TypedProjectionCandidate,TypedProjectionStatus,ProjectionCompatibility,structure_descriptor_from_mapping,make_typed_projection_candidate_id
from mathgraph.verifier_feedback import FlawSeverity,RepairLoopTrace,VerifierFeedback,VerifierFeedbackStatus,make_verifier_feedback_id
def _enum(n,v): return Enum(n,{x:x for x in v.split()},type=str)
SemanticSourceKind=_enum("SemanticSourceKind","RAW_TEXT USER_NOTE CLAIM_TEXT PROOF_TEXT THEOREM_TEXT CONJECTURE_TEXT DEFINITION_TEXT EXAMPLE_TEXT COUNTEREXAMPLE_TEXT QUESTION_TEXT PAPER_EXCERPT DIGESTION_NOTE FEEDBACK_TEXT REPAIR_NOTE LAWBOOK_NOTE ROLE_DESCRIPTION ANALOGY_DESCRIPTION PROCESS_NOTE UNKNOWN")
SemanticClaimKind=_enum("SemanticClaimKind","THEOREM LEMMA PROPOSITION COROLLARY CONJECTURE DEFINITION AXIOM ASSUMPTION HYPOTHESIS CLAIM PROOF_SKETCH EXAMPLE COUNTEREXAMPLE QUESTION TASK_REQUEST META_COMMENT EXPLANATION UNKNOWN")
SemanticDomainKind=_enum("SemanticDomainKind","ALGEBRA EQUATIONAL_LOGIC MAGMA_THEORY ORDER_THEORY TOPOLOGY CATEGORY_THEORY GRAPH_THEORY NUMBER_THEORY ANALYSIS PROBABILITY COMPUTATION LOGIC TYPE_THEORY PROOF_ASSISTANT SCIENTIFIC GENERAL_MATHEMATICS UNKNOWN")
SemanticRiskLevel=_enum("SemanticRiskLevel","LOW MEDIUM HIGH CRITICAL UNKNOWN")
SemanticAmbiguityKind=_enum("SemanticAmbiguityKind","MISSING_DEFINITION AMBIGUOUS_SYMBOL AMBIGUOUS_SCOPE AMBIGUOUS_QUANTIFIER AMBIGUOUS_DOMAIN AMBIGUOUS_EQUALITY INFORMAL_PROOF_GAP UNSTATED_ASSUMPTION OVERLOADED_TERM NATURAL_LANGUAGE_ONLY CITATION_REQUIRED FORMALIZATION_REQUIRED VERIFIER_REQUIRED COUNTERMODEL_REQUIRED EXAMPLE_NOT_GENERAL UNKNOWN")
SemanticExtractionKind=_enum("SemanticExtractionKind","SYMBOL VARIABLE OPERATOR OBJECT RELATION HYPOTHESIS CONCLUSION QUANTIFIER DEFINITION EQUATION IMPLICATION EXAMPLE COUNTEREXAMPLE PROOF_MARKER CITATION_MARKER UNKNOWN")
FormalizationRequestKind=_enum("FormalizationRequestKind","FORMALIZE_THEOREM FORMALIZE_DEFINITION FORMALIZE_PROOF_SKETCH FORMALIZE_EXAMPLE FORMALIZE_COUNTEREXAMPLE FORMALIZE_EQUATIONAL_IMPLICATION FORMALIZE_FINITE_STRUCTURE FORMALIZE_PROOF_ASSISTANT_FILE REQUEST_DOMAIN_ADAPTER REQUEST_CLARIFICATION REQUEST_REVIEW UNKNOWN")
SemanticRouteTarget=_enum("SemanticRouteTarget","FORMAL_WORLD_ADAPTER PROOF_SYSTEM_INTEGRATION CONTINUATION_ACTIONS CONTINUATION_CURRICULUM PROOF_DIGESTION VERIFIER_FEEDBACK REPAIR_LOOP DISCOVERY_VALUE LAWBOOK_QUERY LAWBOOK_CANDIDATE_REVIEW STRUCTURE_REGISTRY TYPED_PROJECTION ROLE_OBJECTS STRUCTURAL_ANALOGY PROCESS_MEMORY HUMAN_REVIEW HOLD_IN_CHORA UNKNOWN")
SemanticIntakeTaskKind=_enum("SemanticIntakeTaskKind","CLARIFY_DEFINITION CLARIFY_SYMBOL CLARIFY_QUANTIFIER FORMALIZE_CLAIM FORMALIZE_PROOF FORMALIZE_DEFINITION SEARCH_COUNTERMODEL REQUEST_PROOF REQUEST_FINITE_VALIDATION REQUEST_VERIFIER_CHECK REQUEST_TRUSTED_IMPORT_REVIEW DIGEST_PROOF_TEXT BUILD_CURRICULUM ROUTE_TO_ADAPTER ROUTE_TO_PROOF_SYSTEM ROUTE_TO_REPAIR ROUTE_TO_REVIEW HOLD_IN_CHORA UNKNOWN")
SemanticIntakeReportStatus=_enum("SemanticIntakeReportStatus","EMPTY SOURCES_RECORDED SEGMENTS_CREATED CLASSIFIED AMBIGUITIES_RECORDED EXTRACTIONS_CREATED FORMALIZATION_REQUESTS_CREATED ROUTING_HINTS_CREATED TASKS_EMITTED HAS_WARNINGS HAS_CRITICALS ADVISORY_ONLY")
def _serial(cls, enums=()):
 def td(self):
  d=dict(self.__dict__)
  for k in enums:
   if isinstance(d.get(k),Enum): d[k]=d[k].value
  for k,v in list(d.items()):
   if isinstance(v,tuple): d[k]=list(v)
  return d
 @classmethod
 def fd(c,d):
  vals=[]
  for f in c.__dataclass_fields__.values():
   if f.name in d: v=d[f.name]
   elif f.default is not MISSING: v=f.default
   elif f.default_factory is not MISSING: v=f.default_factory()
   else: raise KeyError(f.name)
   if f.name in enums and v is not None:
    typ=f.type if isinstance(f.type,type) else globals().get(str(f.type).split("|")[0]); v=typ(str(v))
   if getattr(f.type,"__origin__",None) is tuple and v is not None: v=tuple(v)
   vals.append(v)
  return c(*vals)
 cls.to_dict=td; cls.from_dict=fd; cls.to_json=lambda self:_j(self.to_dict()); cls.from_json=classmethod(lambda c,t:c.from_dict(json.loads(t))); return cls
@_serial
@dataclass
class SemanticSource:
 source_id:str; source_kind:SemanticSourceKind; text:str; source_object_id:str|None=None; source_object_kind:str|None=None; title:str|None=None; language:str="en"; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
@_serial
@dataclass
class SemanticClaimSegment:
 segment_id:str; source_id:str; text:str; index:int=0; start_char:int|None=None; end_char:int|None=None; heading:str|None=None; sentence_count:int=0; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
@_serial
@dataclass
class SemanticClaimClassification:
 classification_id:str; segment_id:str; source_id:str; claim_kind:SemanticClaimKind=SemanticClaimKind.UNKNOWN; domain_kind:SemanticDomainKind=SemanticDomainKind.UNKNOWN; risk_level:SemanticRiskLevel=SemanticRiskLevel.UNKNOWN; confidence:float=0.0; labels:tuple[str,...]=(); rationale:tuple[str,...]=(); warnings:tuple[str,...]=(); criticals:tuple[str,...]=(); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
@_serial
@dataclass
class SemanticAmbiguity:
 ambiguity_id:str; segment_id:str; source_id:str; ambiguity_kind:SemanticAmbiguityKind; text_span:str|None=None; description:str|None=None; severity:SemanticRiskLevel=SemanticRiskLevel.UNKNOWN; suggested_resolution:str|None=None; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
@_serial
@dataclass
class SemanticExtraction:
 extraction_id:str; segment_id:str; source_id:str; extraction_kind:SemanticExtractionKind; value:str; normalized_value:str|None=None; role:str|None=None; confidence:float=0.0; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
@_serial
@dataclass
class FormalizationRequest:
 request_id:str; segment_id:str; source_id:str; request_kind:FormalizationRequestKind; target_world:str|None=None; target_proof_system:str|None=None; informal_text:str|None=None; candidate_formal_text:str|None=None; required_clarifications:tuple[str,...]=(); required_boundaries:tuple[str,...]=(); priority:float=0.0; warnings:tuple[str,...]=(); criticals:tuple[str,...]=(); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
@_serial
@dataclass
class SemanticRoutingHint:
 routing_id:str; segment_id:str; source_id:str; target:SemanticRouteTarget; route:str|None=None; reason:str|None=None; priority:float=0.0; requires_boundary:bool=False; boundary_kind:str|None=None; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
@_serial
@dataclass
class SemanticIntakeTask:
 task_id:str; segment_id:str|None=None; source_id:str|None=None; task_kind:SemanticIntakeTaskKind=SemanticIntakeTaskKind.UNKNOWN; title:str|None=None; description:str|None=None; priority:float=0.0; required_route:SemanticRouteTarget=SemanticRouteTarget.UNKNOWN; required_boundary:str|None=None; warnings:tuple[str,...]=(); criticals:tuple[str,...]=(); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
@dataclass
class SemanticIntakeReport:
 report_id:str; sources:list[SemanticSource]=field(default_factory=list); segments:list[SemanticClaimSegment]=field(default_factory=list); classifications:list[SemanticClaimClassification]=field(default_factory=list); ambiguities:list[SemanticAmbiguity]=field(default_factory=list); extractions:list[SemanticExtraction]=field(default_factory=list); formalization_requests:list[FormalizationRequest]=field(default_factory=list); routing_hints:list[SemanticRoutingHint]=field(default_factory=list); tasks:list[SemanticIntakeTask]=field(default_factory=list); status:SemanticIntakeReportStatus=SemanticIntakeReportStatus.EMPTY; created_at:str=field(default_factory=lambda:_now()); summary:dict[str,Any]=field(default_factory=dict); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def source_count(self): return len(self.sources)
 def segment_count(self): return len(self.segments)
 def classification_count(self): return len(self.classifications)
 def ambiguity_count(self): return len(self.ambiguities)
 def extraction_count(self): return len(self.extractions)
 def formalization_request_count(self): return len(self.formalization_requests)
 def routing_hint_count(self): return len(self.routing_hints)
 def task_count(self): return len(self.tasks)
 def critical_count(self): return len([x for x in audit_semantic_intake_report(self) if x["severity"]=="CRITICAL"])
 def summarize(self):
  self.summary={"source_total":len(self.sources),"segment_total":len(self.segments),"classification_total":len(self.classifications),"ambiguity_total":len(self.ambiguities),"extraction_total":len(self.extractions),"formalization_request_total":len(self.formalization_requests),"routing_hint_total":len(self.routing_hints),"task_total":len(self.tasks),"claim_kind_counts":dict(Counter(x.claim_kind.value for x in self.classifications)),"domain_kind_counts":dict(Counter(x.domain_kind.value for x in self.classifications)),"risk_level_counts":dict(Counter(x.risk_level.value for x in self.classifications)),"ambiguity_kind_counts":dict(Counter(x.ambiguity_kind.value for x in self.ambiguities)),"extraction_kind_counts":dict(Counter(x.extraction_kind.value for x in self.extractions)),"request_kind_counts":dict(Counter(x.request_kind.value for x in self.formalization_requests)),"route_target_counts":dict(Counter(x.target.value for x in self.routing_hints)),"task_kind_counts":dict(Counter(x.task_kind.value for x in self.tasks)),"critical_count":self.critical_count()}; return self.summary
 def to_dict(self): return {**self.__dict__,"sources":[x.to_dict() for x in self.sources],"segments":[x.to_dict() for x in self.segments],"classifications":[x.to_dict() for x in self.classifications],"ambiguities":[x.to_dict() for x in self.ambiguities],"extractions":[x.to_dict() for x in self.extractions],"formalization_requests":[x.to_dict() for x in self.formalization_requests],"routing_hints":[x.to_dict() for x in self.routing_hints],"tasks":[x.to_dict() for x in self.tasks],"status":self.status.value}
 @classmethod
 def from_dict(c,d): return c(str(d["report_id"]),[SemanticSource.from_dict(x) for x in d.get("sources",())],[SemanticClaimSegment.from_dict(x) for x in d.get("segments",())],[SemanticClaimClassification.from_dict(x) for x in d.get("classifications",())],[SemanticAmbiguity.from_dict(x) for x in d.get("ambiguities",())],[SemanticExtraction.from_dict(x) for x in d.get("extractions",())],[FormalizationRequest.from_dict(x) for x in d.get("formalization_requests",())],[SemanticRoutingHint.from_dict(x) for x in d.get("routing_hints",())],[SemanticIntakeTask.from_dict(x) for x in d.get("tasks",())],SemanticIntakeReportStatus(str(d.get("status","EMPTY"))),str(d.get("created_at",_now())),dict(d.get("summary",{})),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
 def write_json(self,p): _w(p,self.to_json())
 @classmethod
 def read_json(c,p): return c.from_json(Path(p).read_text())
 def write_jsonl(self,p): _w(p,self.to_json()+"\n")
 @classmethod
 def read_jsonl(c,p): return [c.from_json(x) for x in Path(p).read_text().splitlines() if x.strip()]
for _c,_e in [(SemanticSource,("source_kind",)),(SemanticClaimClassification,("claim_kind","domain_kind","risk_level")),(SemanticAmbiguity,("ambiguity_kind","severity")),(SemanticExtraction,("extraction_kind",)),(FormalizationRequest,("request_kind",)),(SemanticRoutingHint,("target",)),(SemanticIntakeTask,("task_kind","required_route"))]: _serial(_c,_e)
def make_semantic_source_id(*x): return content_id("semantic-source",x)
def make_semantic_claim_segment_id(*x): return content_id("semantic-segment",x)
def make_semantic_claim_classification_id(*x): return content_id("semantic-classification",x)
def make_semantic_ambiguity_id(*x): return content_id("semantic-ambiguity",x)
def make_semantic_extraction_id(*x): return content_id("semantic-extraction",x)
def make_formalization_request_id(*x): return content_id("formalization-request",x)
def make_semantic_routing_hint_id(*x): return content_id("semantic-routing",x)
def make_semantic_intake_task_id(*x): return content_id("semantic-task",x)
def make_semantic_intake_report_id(*x): return content_id("semantic-report",x)
def semantic_sources_from_object(o):
 if isinstance(o,SemanticSource): return [o]
 if isinstance(o,str): return [SemanticSource(make_semantic_source_id("text",o),SemanticSourceKind.RAW_TEXT,o)]
 if isinstance(o,Mapping):
  keys=("text","statement","theorem","lemma","conjecture","claim","source","target","source_text","target_text","informal_text","proof_text","description","notes","rationale","title","route","error_message","feedback","stdout_excerpt","stderr_excerpt")
  parts=[f"{k}: {o[k]}" for k in keys if o.get(k)]
  return [SemanticSource(make_semantic_source_id("mapping",parts),SemanticSourceKind.RAW_TEXT,"\n".join(parts),_s(o.get("source_object_id")),_s(o.get("source_kind")),metadata=dict(o))] if parts else []
 if hasattr(o,"to_dict"):
  d=o.to_dict(); oid=next((d.get(k) for k in ("claim_id","task_id","handoff_id","parse_id","normalize_id","validation_id","artifact_id","result_id","trace_id","entry_id","answer_id","candidate_id","descriptor_id","role_id","reason_id","rule_id","episode_id","stage_id","experience_id","report_id") if d.get(k)),None)
  if o.__class__.__name__.endswith("Report"):
   rows=[]
   for key in ("tasks","handoffs","parses","normalizations","validations","artifacts","check_results","answers","typed_projection_candidates","role_objects","definition_candidates","conjecture_candidates","candidates","reason_nodes","rules","episodes","stages"):
    for x in getattr(o,key,[]) or []: rows+=semantic_sources_from_object(x)
   return rows or semantic_sources_from_object({"text":_j(d),"source_object_id":oid,"source_kind":o.__class__.__name__})
  return semantic_sources_from_object({**d,"source_object_id":oid,"source_kind":o.__class__.__name__})
 return []
def segment_semantic_source(s):
 if not s.text.strip(): return []
 chunks=[x for x in re.split(r"\n\s*\n|(?=^\s*(?:Theorem|Lemma|Definition|Conjecture)\b)",s.text,flags=re.M) if x.strip()]
 out=[]; pos=0
 for i,ch in enumerate(chunks):
  start=s.text.find(ch,pos); pos=start+len(ch); sent=max(1,len(re.findall(r"[.!?]",ch))); out.append(SemanticClaimSegment(make_semantic_claim_segment_id(s.source_id,i,ch),s.source_id,ch.strip(),i,start,pos,ch.split(":",1)[0] if re.match(r"\s*(Theorem|Lemma|Definition|Conjecture)\b",ch,re.I) else None,sent))
 return out
def segment_semantic_sources(ss): return [x for s in ss for x in segment_semantic_source(s)]
def classify_semantic_segment(seg,source=None):
 t=seg.text.lower(); ck=SemanticClaimKind.UNKNOWN; why=[]
 for k,kind in [("theorem",SemanticClaimKind.THEOREM),("lemma",SemanticClaimKind.LEMMA),("corollary",SemanticClaimKind.COROLLARY),("proposition",SemanticClaimKind.PROPOSITION),("conjecture",SemanticClaimKind.CONJECTURE),("definition",SemanticClaimKind.DEFINITION),("define",SemanticClaimKind.DEFINITION),("axiom",SemanticClaimKind.AXIOM),("counterexample",SemanticClaimKind.COUNTEREXAMPLE),("example",SemanticClaimKind.EXAMPLE),("proof",SemanticClaimKind.PROOF_SKETCH)]:
  if k in t: ck=kind; why.append(k); break
 if ck==SemanticClaimKind.UNKNOWN and ("?" in t or "is it true" in t or "does every" in t): ck=SemanticClaimKind.QUESTION
 if ck==SemanticClaimKind.UNKNOWN and re.match(r"\s*(prove|find|show|construct|formalize)\b",t): ck=SemanticClaimKind.TASK_REQUEST
 if ck==SemanticClaimKind.UNKNOWN and any(x in t for x in ("therefore","hence","contradiction")): ck=SemanticClaimKind.PROOF_SKETCH
 if ck==SemanticClaimKind.UNKNOWN and any(x in t for x in ("because","means","intuition","explanation")): ck=SemanticClaimKind.EXPLANATION
 dk=SemanticDomainKind.UNKNOWN
 domains=[(("magma","x*y","◇"),SemanticDomainKind.MAGMA_THEORY),(("equation","identity","implies"),SemanticDomainKind.EQUATIONAL_LOGIC),(("lean","coq","isabelle",":="),SemanticDomainKind.PROOF_ASSISTANT),(("category","functor","morphism","adjunction"),SemanticDomainKind.CATEGORY_THEORY),(("graph","node","edge"),SemanticDomainKind.GRAPH_THEORY),(("topology","continuous","open set","compact"),SemanticDomainKind.TOPOLOGY),(("poset","lattice","monotone"),SemanticDomainKind.ORDER_THEORY),(("prime","integer","congruence"),SemanticDomainKind.NUMBER_THEORY),(("limit","derivative","integral","convergence"),SemanticDomainKind.ANALYSIS),(("probability","random","expectation"),SemanticDomainKind.PROBABILITY),(("algorithm","computable","complexity"),SemanticDomainKind.COMPUTATION)]
 for words,kind in domains:
  if any(w in t for w in words): dk=kind; break
 risk=SemanticRiskLevel.CRITICAL if any(x in t for x in ("verified successfully","certificate proves","proved true")) else SemanticRiskLevel.HIGH if ck in {SemanticClaimKind.THEOREM,SemanticClaimKind.LEMMA,SemanticClaimKind.PROPOSITION,SemanticClaimKind.COROLLARY,SemanticClaimKind.PROOF_SKETCH,SemanticClaimKind.CONJECTURE} else SemanticRiskLevel.LOW if ck in {SemanticClaimKind.EXPLANATION,SemanticClaimKind.TASK_REQUEST} else SemanticRiskLevel.MEDIUM
 return SemanticClaimClassification(make_semantic_claim_classification_id(seg.segment_id,ck.value,dk.value),seg.segment_id,seg.source_id,ck,dk,risk,.8 if ck!=SemanticClaimKind.UNKNOWN else .2,tuple(why),tuple(why),criticals=("natural_language_truth_claim",) if risk==SemanticRiskLevel.CRITICAL else ())
def detect_semantic_ambiguities(seg,c=None):
 t=seg.text.lower(); out=[]; add=lambda k,span,desc: out.append(SemanticAmbiguity(make_semantic_ambiguity_id(seg.segment_id,k.value,span),seg.segment_id,seg.source_id,k,span,desc,c.risk_level if c else SemanticRiskLevel.MEDIUM))
 if any(x in t for x in ("called","defined","structure","object")) and "=" not in t: add(SemanticAmbiguityKind.MISSING_DEFINITION,None,"definition body unclear")
 if any(x in seg.text for x in ("*","◇","<=","~","≅")) and "define" not in t: add(SemanticAmbiguityKind.AMBIGUOUS_SYMBOL,None,"operator lacks local definition")
 if any(x in t for x in ("all ","every ","some ","exists")) and c and c.domain_kind==SemanticDomainKind.UNKNOWN: add(SemanticAmbiguityKind.AMBIGUOUS_QUANTIFIER,None,"quantifier domain unclear")
 if any(x in t for x in ("clearly","obvious","easy to see","left to reader")): add(SemanticAmbiguityKind.INFORMAL_PROOF_GAP,None,"informal proof gap")
 if c and c.claim_kind in {SemanticClaimKind.THEOREM,SemanticClaimKind.PROOF_SKETCH,SemanticClaimKind.CONJECTURE}: add(SemanticAmbiguityKind.NATURAL_LANGUAGE_ONLY,None,"requires formalization"); add(SemanticAmbiguityKind.FORMALIZATION_REQUIRED,None,"theorem-like text"); add(SemanticAmbiguityKind.COUNTERMODEL_REQUIRED,None,"general claim may be false")
 if c and c.domain_kind==SemanticDomainKind.PROOF_ASSISTANT: add(SemanticAmbiguityKind.VERIFIER_REQUIRED,None,"proof-system text needs checker")
 return out
def extract_semantic_items(seg,c=None):
 t=seg.text; out=[]
 def add(k,v,role=None): out.append(SemanticExtraction(make_semantic_extraction_id(seg.segment_id,k.value,v),seg.segment_id,seg.source_id,k,v,v.lower(),role,.7))
 for v in sorted(set(re.findall(r"\b[x-zabcnmkij]\b",t))): add(SemanticExtractionKind.VARIABLE,v)
 for v in ("*","◇","<=",">=","=>","->"):
  if v in t: add(SemanticExtractionKind.OPERATOR,v)
 for m in re.findall(r"[^.;\n]*=[^.;\n]*",t):
  if m.strip(): add(SemanticExtractionKind.EQUATION,m.strip())
 if "implies" in t.lower() or "=>" in t: add(SemanticExtractionKind.IMPLICATION,"implies")
 for marker in ("assume","suppose","if"):
  if marker in t.lower(): add(SemanticExtractionKind.HYPOTHESIS,marker)
 for marker in ("therefore","hence","then","it follows"):
  if marker in t.lower(): add(SemanticExtractionKind.CONCLUSION,marker)
 for marker in ("proof","induction","contradiction","qed"):
  if marker in t.lower(): add(SemanticExtractionKind.PROOF_MARKER,marker)
 return out
def formalization_requests_from_semantic(seg,c,ambiguities=(),extractions=()):
 kinds=[]
 if c.claim_kind in {SemanticClaimKind.THEOREM,SemanticClaimKind.LEMMA,SemanticClaimKind.PROPOSITION,SemanticClaimKind.COROLLARY}: kinds.append(FormalizationRequestKind.FORMALIZE_THEOREM)
 if c.claim_kind==SemanticClaimKind.DEFINITION: kinds.append(FormalizationRequestKind.FORMALIZE_DEFINITION)
 if c.claim_kind==SemanticClaimKind.PROOF_SKETCH: kinds.append(FormalizationRequestKind.FORMALIZE_PROOF_SKETCH)
 if c.claim_kind==SemanticClaimKind.EXAMPLE: kinds.append(FormalizationRequestKind.FORMALIZE_EXAMPLE)
 if c.claim_kind==SemanticClaimKind.COUNTEREXAMPLE: kinds.append(FormalizationRequestKind.FORMALIZE_COUNTEREXAMPLE)
 if c.domain_kind in {SemanticDomainKind.EQUATIONAL_LOGIC,SemanticDomainKind.MAGMA_THEORY} and any(x.extraction_kind==SemanticExtractionKind.IMPLICATION for x in extractions): kinds.append(FormalizationRequestKind.FORMALIZE_EQUATIONAL_IMPLICATION)
 if c.domain_kind==SemanticDomainKind.PROOF_ASSISTANT: kinds.append(FormalizationRequestKind.FORMALIZE_PROOF_ASSISTANT_FILE)
 if ambiguities and c.risk_level in {SemanticRiskLevel.HIGH,SemanticRiskLevel.CRITICAL}: kinds.append(FormalizationRequestKind.REQUEST_CLARIFICATION)
 return [FormalizationRequest(make_formalization_request_id(seg.segment_id,k.value),seg.segment_id,seg.source_id,k,"magma_equational" if k==FormalizationRequestKind.FORMALIZE_EQUATIONAL_IMPLICATION else None,"lean_like" if k==FormalizationRequestKind.FORMALIZE_PROOF_ASSISTANT_FILE else None,seg.text,required_clarifications=tuple(a.ambiguity_kind.value for a in ambiguities),required_boundaries=("verifier",) if k in {FormalizationRequestKind.FORMALIZE_THEOREM,FormalizationRequestKind.FORMALIZE_PROOF_SKETCH} else (),priority=.8 if c.risk_level in {SemanticRiskLevel.HIGH,SemanticRiskLevel.CRITICAL} else .4) for k in dict.fromkeys(kinds)]
def semantic_routing_hints_from_semantic(seg,c,ambiguities=(),requests=()):
 out=[]; add=lambda target,route=None,reason=None: out.append(SemanticRoutingHint(make_semantic_routing_hint_id(seg.segment_id,target.value,route),seg.segment_id,seg.source_id,target,route,reason,.7))
 if c.domain_kind in {SemanticDomainKind.EQUATIONAL_LOGIC,SemanticDomainKind.MAGMA_THEORY}: add(SemanticRouteTarget.FORMAL_WORLD_ADAPTER,"magma_equational","equational text")
 if c.domain_kind==SemanticDomainKind.PROOF_ASSISTANT: add(SemanticRouteTarget.PROOF_SYSTEM_INTEGRATION,"proof_assistant","proof-system syntax")
 if c.claim_kind==SemanticClaimKind.PROOF_SKETCH: add(SemanticRouteTarget.PROOF_DIGESTION,"proof_text","proof sketch")
 if c.claim_kind in {SemanticClaimKind.THEOREM,SemanticClaimKind.CONJECTURE,SemanticClaimKind.LEMMA}: add(SemanticRouteTarget.CONTINUATION_ACTIONS); add(SemanticRouteTarget.CONTINUATION_CURRICULUM)
 if ambiguities: add(SemanticRouteTarget.HUMAN_REVIEW,"review","ambiguity"); 
 if c.risk_level in {SemanticRiskLevel.HIGH,SemanticRiskLevel.CRITICAL} and ambiguities: add(SemanticRouteTarget.HOLD_IN_CHORA,"hold","high risk")
 return out
def semantic_tasks_from_semantic(seg,c,ambiguities=(),requests=(),routing_hints=()):
 ks=[]
 for a in ambiguities:
  ks += [SemanticIntakeTaskKind.CLARIFY_DEFINITION] if a.ambiguity_kind==SemanticAmbiguityKind.MISSING_DEFINITION else [SemanticIntakeTaskKind.CLARIFY_SYMBOL] if a.ambiguity_kind==SemanticAmbiguityKind.AMBIGUOUS_SYMBOL else [SemanticIntakeTaskKind.CLARIFY_QUANTIFIER] if a.ambiguity_kind==SemanticAmbiguityKind.AMBIGUOUS_QUANTIFIER else [SemanticIntakeTaskKind.SEARCH_COUNTERMODEL] if a.ambiguity_kind==SemanticAmbiguityKind.COUNTERMODEL_REQUIRED else []
 for r in requests:
  ks += [SemanticIntakeTaskKind.FORMALIZE_DEFINITION] if r.request_kind==FormalizationRequestKind.FORMALIZE_DEFINITION else [SemanticIntakeTaskKind.FORMALIZE_PROOF] if r.request_kind==FormalizationRequestKind.FORMALIZE_PROOF_SKETCH else [SemanticIntakeTaskKind.FORMALIZE_CLAIM]
 if c.claim_kind==SemanticClaimKind.PROOF_SKETCH: ks += [SemanticIntakeTaskKind.DIGEST_PROOF_TEXT,SemanticIntakeTaskKind.REQUEST_PROOF]
 if c.claim_kind in {SemanticClaimKind.THEOREM,SemanticClaimKind.CONJECTURE,SemanticClaimKind.LEMMA}: ks.append(SemanticIntakeTaskKind.BUILD_CURRICULUM)
 for h in routing_hints:
  ks += [SemanticIntakeTaskKind.ROUTE_TO_ADAPTER] if h.target==SemanticRouteTarget.FORMAL_WORLD_ADAPTER else [SemanticIntakeTaskKind.ROUTE_TO_PROOF_SYSTEM] if h.target==SemanticRouteTarget.PROOF_SYSTEM_INTEGRATION else [SemanticIntakeTaskKind.ROUTE_TO_REVIEW] if h.target==SemanticRouteTarget.HUMAN_REVIEW else [SemanticIntakeTaskKind.HOLD_IN_CHORA] if h.target==SemanticRouteTarget.HOLD_IN_CHORA else []
 return [SemanticIntakeTask(make_semantic_intake_task_id(seg.segment_id,k.value),seg.segment_id,seg.source_id,k,k.value.replace("_"," ").title(),required_route=SemanticRouteTarget.HUMAN_REVIEW if k in {SemanticIntakeTaskKind.ROUTE_TO_REVIEW,SemanticIntakeTaskKind.HOLD_IN_CHORA} else SemanticRouteTarget.UNKNOWN,metadata={"semantic_advisory_only":True}) for k in dict.fromkeys(ks)]
def build_semantic_intake_report(objects=(),sources=(),*,segment=True,classify=True,detect_ambiguity=True,extract=True,create_formalization_requests=True,create_routing_hints=True,create_tasks=True):
 ss=list(sources)+[x for o in objects for x in semantic_sources_from_object(o)]; segs=segment_semantic_sources(ss) if segment else []; cls=[classify_semantic_segment(x,next((s for s in ss if s.source_id==x.source_id),None)) for x in segs] if classify else []; amb=[]; ext=[]; req=[]; hints=[]; tasks=[]
 for sg,c in zip(segs,cls):
  aa=detect_semantic_ambiguities(sg,c) if detect_ambiguity else []; ee=extract_semantic_items(sg,c) if extract else []; rr=formalization_requests_from_semantic(sg,c,aa,ee) if create_formalization_requests else []; hh=semantic_routing_hints_from_semantic(sg,c,aa,rr) if create_routing_hints else []; tt=semantic_tasks_from_semantic(sg,c,aa,rr,hh) if create_tasks else []; amb+=aa; ext+=ee; req+=rr; hints+=hh; tasks+=tt
 r=SemanticIntakeReport(make_semantic_intake_report_id([s.source_id for s in ss]),ss,segs,cls,amb,ext,req,hints,tasks); r.summarize(); r.status=SemanticIntakeReportStatus.HAS_CRITICALS if r.critical_count() else SemanticIntakeReportStatus.TASKS_EMITTED if tasks else SemanticIntakeReportStatus.ROUTING_HINTS_CREATED if hints else SemanticIntakeReportStatus.FORMALIZATION_REQUESTS_CREATED if req else SemanticIntakeReportStatus.EXTRACTIONS_CREATED if ext else SemanticIntakeReportStatus.AMBIGUITIES_RECORDED if amb else SemanticIntakeReportStatus.CLASSIFIED if cls else SemanticIntakeReportStatus.SEGMENTS_CREATED if segs else SemanticIntakeReportStatus.SOURCES_RECORDED if ss else SemanticIntakeReportStatus.EMPTY; return r
def semantic_report_to_formal_world_inputs(r): return [{"text":q.informal_text,"source_object_id":q.request_id,"source_kind":"FormalizationRequest","semantic_advisory_only":True} for q in r.formalization_requests if q.target_world]
def semantic_report_to_proof_system_inputs(r): return [{"text":q.informal_text,"source_object_id":q.request_id,"source_kind":"FormalizationRequest","semantic_advisory_only":True} for q in r.formalization_requests if q.target_proof_system or q.request_kind in {FormalizationRequestKind.FORMALIZE_THEOREM,FormalizationRequestKind.FORMALIZE_PROOF_SKETCH}]
def semantic_report_to_lawbook_candidates(r): return [LawbookEntry(make_lawbook_entry_id("semantic",r.report_id,s.segment_id),LawbookEntryKind.ROUTE_RULE_ENTRY,LawbookEntryStatus.CANDIDATE,raw=s.text,metadata={"semantic_intake_not_truth":True,"semantic_report_id":r.report_id,"natural_language_not_verification":True},advisory=True) for s in r.segments]
def semantic_report_to_continuation_outputs(r): return [ContinuationActionOutput(make_continuation_output_id({"semantic":t.task_id}),"semantic_intake",ContinuationOutputKind.TASK,ContinuationActionStatus.ADVISORY_ONLY,task_payload={"task":t.task_kind.value.lower()},advisory=True) for t in r.tasks]
def semantic_report_to_curriculum(r): return ContinuationCurriculum(make_curriculum_id("semantic",r.report_id),strategy=CurriculumBuildStrategy.MIXED,stages=[CurriculumStage(make_curriculum_stage_id("semantic",x),CurriculumStageKind.RESIDUAL_REVIEW,CurriculumStageStatus.ADVISORY_ONLY,title=x,advisory=True) for x in ("read text","segment","classify","clarify","formalize","route to adapter","route to proof system","verify/import/finite validate","digest/explain")],status=CurriculumTraceStatus.ADVISORY_ONLY)
def semantic_report_to_discovery_value_scores(r):
 out=[]
 for c in r.classifications:
  val=.7 if c.risk_level in {SemanticRiskLevel.HIGH,SemanticRiskLevel.CRITICAL} else .3; sig=DiscoveryValueSignal(content_id("semantic-signal",c.classification_id),DiscoveryValueSignalKind.REUSE_VALUE,val,source_object_kind=DiscoveryValueObjectKind.RAW_TASK); s=DiscoveryValueScore(content_id("semantic-score",c.classification_id),c.classification_id,DiscoveryValueObjectKind.RAW_TASK,signals=[sig],metadata={"semantic_advisory_only":True}); s.recompute(); out.append(s)
 return out
def semantic_report_to_process_episodes(r): return [ProcessEpisodeRecord(make_process_episode_id("semantic",s.segment_id),ProcessEpisodeStatus.ADVISORY_ONLY,contexts=[ProcessContextItem(content_id("semantic-context",s.segment_id),ProcessContextKind.RAW_EVENT,ProcessContextRole.ADVISORY_ONLY,s.segment_id)],advisory=True) for s in r.segments]
def semantic_report_to_verifier_feedback(r): return [VerifierFeedback(make_verifier_feedback_id("semantic",c.classification_id),status=VerifierFeedbackStatus.ADVISORY_ONLY,flaw_severity=FlawSeverity.MAJOR,raw_message="natural language claims truth without boundary",metadata={"semantic_advisory_only":True}) for c in r.classifications if c.risk_level==SemanticRiskLevel.CRITICAL]
def semantic_report_to_repair_traces(r): return [RepairLoopTrace(content_id("semantic-repair",a.ambiguity_id)) for a in r.ambiguities if a.ambiguity_kind in {SemanticAmbiguityKind.MISSING_DEFINITION,SemanticAmbiguityKind.AMBIGUOUS_SYMBOL}]
def semantic_report_to_proof_digestion_inputs(r):
 proof_segments={x.segment_id for x in r.extractions if x.extraction_kind==SemanticExtractionKind.PROOF_MARKER}
 return [{"segment_id":s.segment_id,"text":s.text,"semantic_advisory_only":True} for s,c in zip(r.segments,r.classifications) if c.claim_kind==SemanticClaimKind.PROOF_SKETCH or s.segment_id in proof_segments]
def semantic_report_to_structure_descriptors(r): return [structure_descriptor_from_mapping({"domain":c.domain_kind.value,"claim":c.claim_kind.value},object_id=c.classification_id,object_kind=StructureObjectKind.RAW_EVENT) for c in r.classifications]
def semantic_report_to_typed_projection_candidates(r): return [TypedProjectionCandidate(make_typed_projection_candidate_id("semantic",q.request_id),q.request_id,status=TypedProjectionStatus.NEEDS_FORMALIZATION,compatibility=ProjectionCompatibility.NEEDS_FORMALIZATION,required_review=True,metadata={"semantic_advisory_only":True}) for q in r.formalization_requests]
def semantic_report_to_role_signatures(r): return [RoleSignature(make_role_signature_id("semantic",c.classification_id),RoleSourceKind.RAW_EVENT,c.classification_id,RoleObjectKind.PROCESS_ROLE,(c.claim_kind.value.lower(),c.domain_kind.value.lower()),metadata={"semantic_advisory_only":True}) for c in r.classifications]
def semantic_report_to_analogy_sources(r): return [analogy_source_from_mapping(c.to_dict(),source_kind=AnalogySourceKind.RAW_EVENT,object_id=c.classification_id) for c in r.classifications]
def semantic_report_to_habit_observations(r): return [HabitObservation(content_id("semantic-habit",c.classification_id),HabitObservationKind.RAW_EVENT,route="semantic_intake",outcome=HabitOutcome.ADVISORY_ONLY,object_id=c.classification_id,metadata={"semantic_advisory_only":True}) for c in r.classifications]
def semantic_report_to_reason_observations(r): return [ReasonObservation(make_reason_observation_id("semantic",c.classification_id),ReasonObservationKind.RAW_EVENT,c.classification_id,"semantic_intake",*extract_atoms_from_mapping(c.to_dict()),metadata={"semantic_advisory_only":True}) for c in r.classifications]
def semantic_report_to_structural_identity_objects(r): return [{"classification_id":c.classification_id,"claim_kind":c.claim_kind.value,"domain_kind":c.domain_kind.value,"semantic_advisory_only":True} for c in r.classifications]
def semantic_report_to_alchemical_trace(r):
 t=AlchemicalTrace(make_alchemical_trace_id("semantic",r.report_id))
 for p in (AlchemicalPhase.RAW_MATTER,AlchemicalPhase.CALCINATION,AlchemicalPhase.SOLUTION,AlchemicalPhase.SUBLIMATION,AlchemicalPhase.DESCENSION,AlchemicalPhase.DISTILLATION): t.add_step(phase=p,status=AlchemicalStatus.ADVISORY_ONLY)
 return t
def semantic_report_to_agent_experiences(r,agent_id=None): return [AgentExperience(content_id("semantic-exp",c.classification_id),agent_id or "semantic-intake",None,None,"semantic_intake",None,AgentExperienceOutcome.ADVISORY_ONLY,metadata={"classification_id":c.classification_id}) for c in r.classifications]
def semantic_report_to_route_telemetry_events(r): return [{"event_id":content_id("semantic-telemetry",t.task_id),"route_kind":"semantic_intake","outcome":t.task_kind.value,"semantic_advisory_only":True} for t in r.tasks]
def audit_semantic_source(x): return _audit_adv(x,x.source_id,"SEMANTIC_SOURCE_NON_ADVISORY")
def audit_semantic_claim_segment(x): return _audit_adv(x,x.segment_id,"SEMANTIC_SEGMENT_NON_ADVISORY")
def audit_semantic_claim_classification(x): return _audit_adv(x,x.classification_id,"SEMANTIC_CLASSIFICATION_NON_ADVISORY")+([_f("CRITICAL","SEMANTIC_CLASSIFICATION_AS_PROOF","natural-language truth claim",x.classification_id)] if x.risk_level==SemanticRiskLevel.CRITICAL else [])
def audit_semantic_ambiguity(x): return _audit_adv(x,x.ambiguity_id,"SEMANTIC_AMBIGUITY_NON_ADVISORY")
def audit_semantic_extraction(x): return _audit_adv(x,x.extraction_id,"SEMANTIC_EXTRACTION_NON_ADVISORY")
def audit_formalization_request(x): return _audit_adv(x,x.request_id,"SEMANTIC_REQUEST_NON_ADVISORY")+([_f("CRITICAL","SEMANTIC_REQUEST_AS_BOUNDARY","formalization request claims boundary",x.request_id)] if x.metadata.get("verifier_boundary_crossed") or x.metadata.get("certificate_id") else [])
def audit_semantic_routing_hint(x): return _audit_adv(x,x.routing_id,"SEMANTIC_ROUTE_NON_ADVISORY")+([_f("CRITICAL","SEMANTIC_ROUTE_AS_BOUNDARY","routing hint claims boundary",x.routing_id)] if x.metadata.get("verifier_boundary_crossed") else [])
def audit_semantic_intake_task(x): return _audit_adv(x,x.task_id,"SEMANTIC_TASK_NON_ADVISORY")+([_f("CRITICAL","SEMANTIC_TASK_AS_TRUTH","semantic task carries truth fields",x.task_id)] if x.metadata.get("certificate_id") or x.metadata.get("terminal_form") else [])
def audit_semantic_intake_report(r):
 out=[y for xs in (r.sources,r.segments,r.classifications,r.ambiguities,r.extractions,r.formalization_requests,r.routing_hints,r.tasks) for x in xs for y in (audit_semantic_source(x) if isinstance(x,SemanticSource) else audit_semantic_claim_segment(x) if isinstance(x,SemanticClaimSegment) else audit_semantic_claim_classification(x) if isinstance(x,SemanticClaimClassification) else audit_semantic_ambiguity(x) if isinstance(x,SemanticAmbiguity) else audit_semantic_extraction(x) if isinstance(x,SemanticExtraction) else audit_formalization_request(x) if isinstance(x,FormalizationRequest) else audit_semantic_routing_hint(x) if isinstance(x,SemanticRoutingHint) else audit_semantic_intake_task(x))]
 if not r.advisory: out.append(_f("CRITICAL","SEMANTIC_REPORT_NON_ADVISORY","semantic report non-advisory",r.report_id))
 return out
def _audit_adv(x,oid,code): return [_f("CRITICAL",code,"semantic object non-advisory",oid)] if not x.advisory else []
def _s(x): return None if x is None else str(x)
def _now(): return datetime.now(timezone.utc).isoformat()
def _j(x): return json.dumps(x,sort_keys=True,separators=(",",":"),default=str)
def _w(p,t): path=Path(p); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(t,encoding="utf-8")
def _f(sev,code,msg,obj): return {"severity":sev,"code":code,"message":msg,"object_id":obj}
