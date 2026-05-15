"""Advisory reason compression and minimal-sufficient-reason candidates."""
from __future__ import annotations
import itertools, json, re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from statistics import mean
from typing import Any, Mapping, Sequence
from mathgraph.agent_biography import AgentExperience, AgentExperienceOutcome
from mathgraph.alchemy import AlchemicalPhase, AlchemicalStatus, AlchemicalTrace, make_alchemical_trace_id
from mathgraph.certificates import TerminalForm
from mathgraph.continuation_actions import ContinuationActionOutput, ContinuationActionStatus, ContinuationOutputKind, make_continuation_output_id
from mathgraph.continuation_curriculum import ContinuationCurriculum, CurriculumBuildStrategy, CurriculumStage, CurriculumStageKind, CurriculumStageStatus, CurriculumTraceStatus, make_curriculum_id, make_curriculum_stage_id
from mathgraph.discovery_value import DiscoveryValueObjectKind, DiscoveryValueScore, DiscoveryValueSignal, DiscoveryValueSignalKind
from mathgraph.hashing import content_id
from mathgraph.lawbook import LawbookEntry, LawbookEntryKind, LawbookEntryStatus, LawbookStore, make_lawbook_entry_id

class ReasonObservationKind(str,Enum):
 LAWBOOK_ENTRY="LAWBOOK_ENTRY"; LAWBOOK_QUERY="LAWBOOK_QUERY"; STRUCTURAL_IDENTITY="STRUCTURAL_IDENTITY"; HABIT="HABIT"; DISCOVERY_VALUE="DISCOVERY_VALUE"; PROJECTION="PROJECTION"; PROOF_DIGESTION="PROOF_DIGESTION"; VERIFIER_FEEDBACK="VERIFIER_FEEDBACK"; REPAIR_LOOP="REPAIR_LOOP"; CURRICULUM="CURRICULUM"; ALCHEMICAL_TRACE="ALCHEMICAL_TRACE"; AGENT_EXPERIENCE="AGENT_EXPERIENCE"; ROUTE_TELEMETRY="ROUTE_TELEMETRY"; RAW_EVENT="RAW_EVENT"; UNKNOWN="UNKNOWN"
class ReasonAtomKind(str,Enum):
 CONDITION="CONDITION"; TERMINAL_FORM="TERMINAL_FORM"; CERTIFICATE="CERTIFICATE"; ROUTE="ROUTE"; BASIN="BASIN"; PHASE="PHASE"; STRUCTURAL_SIGNATURE="STRUCTURAL_SIGNATURE"; HABIT_RULE="HABIT_RULE"; PROJECTION_RULE="PROJECTION_RULE"; DIGESTION_SCHEMA="DIGESTION_SCHEMA"; OBSTRUCTION="OBSTRUCTION"; TRUST_BOUNDARY="TRUST_BOUNDARY"; FAILURE_BOUNDARY="FAILURE_BOUNDARY"; ROOT_LINK="ROOT_LINK"; REASON_LINK="REASON_LINK"; VALUE_SIGNAL="VALUE_SIGNAL"; COST_SIGNAL="COST_SIGNAL"; RISK_SIGNAL="RISK_SIGNAL"; SOURCE_PATTERN="SOURCE_PATTERN"; TARGET_PATTERN="TARGET_PATTERN"; METADATA="METADATA"; UNKNOWN="UNKNOWN"
class ReasonCandidateKind(str,Enum):
 SUFFICIENT_REASON="SUFFICIENT_REASON"; MINIMAL_REASON_CANDIDATE="MINIMAL_REASON_CANDIDATE"; LOAD_BEARING_CONDITION="LOAD_BEARING_CONDITION"; DECORATIVE_CONDITION="DECORATIVE_CONDITION"; OBSTRUCTION_EXPLANATION="OBSTRUCTION_EXPLANATION"; CONSTRUCTOR_EXPLANATION="CONSTRUCTOR_EXPLANATION"; PROOF_SCHEMA_EXPLANATION="PROOF_SCHEMA_EXPLANATION"; PROJECTION_EXPLANATION="PROJECTION_EXPLANATION"; HABIT_EXPLANATION="HABIT_EXPLANATION"; STRUCTURAL_IDENTITY_EXPLANATION="STRUCTURAL_IDENTITY_EXPLANATION"; COST_AVOIDANCE_REASON="COST_AVOIDANCE_REASON"; RISK_AVOIDANCE_REASON="RISK_AVOIDANCE_REASON"; RESIDUAL_REASON="RESIDUAL_REASON"; UNKNOWN="UNKNOWN"
class ReasonStatus(str,Enum):
 CANDIDATE="CANDIDATE"; SUPPORTED="SUPPORTED"; MINIMAL_CANDIDATE="MINIMAL_CANDIDATE"; ACCEPTED="ACCEPTED"; REJECTED="REJECTED"; REFUTED="REFUTED"; NEEDS_MORE_EVIDENCE="NEEDS_MORE_EVIDENCE"; NEEDS_FORMALIZATION="NEEDS_FORMALIZATION"; NEEDS_REVIEW="NEEDS_REVIEW"; SUPERSEDED="SUPERSEDED"; UNKNOWN="UNKNOWN"
class ReasonReviewDecision(str,Enum):
 ACCEPT="ACCEPT"; REJECT="REJECT"; NEEDS_MORE_EVIDENCE="NEEDS_MORE_EVIDENCE"; NEEDS_MINIMALITY_CHECK="NEEDS_MINIMALITY_CHECK"; NEEDS_FORMALIZATION="NEEDS_FORMALIZATION"; NEEDS_LOWER_COMPLEXITY="NEEDS_LOWER_COMPLEXITY"; HOLD_IN_CHORA="HOLD_IN_CHORA"; UNKNOWN="UNKNOWN"
class ReasonCompressionReportStatus(str,Enum):
 EMPTY="EMPTY"; OBSERVED="OBSERVED"; CANDIDATES_FOUND="CANDIDATES_FOUND"; MINIMAL_CANDIDATES_FOUND="MINIMAL_CANDIDATES_FOUND"; REVIEWED="REVIEWED"; ACCEPTED_REASONS="ACCEPTED_REASONS"; HAS_WARNINGS="HAS_WARNINGS"; HAS_CRITICALS="HAS_CRITICALS"; ADVISORY_ONLY="ADVISORY_ONLY"

@dataclass
class ReasonObservation:
 observation_id:str; kind:ReasonObservationKind; object_id:str|None=None; source_kind:str|None=None; atoms:tuple[str,...]=(); atom_kinds:dict[str,str]=field(default_factory=dict); outcome:str|None=None; terminal_form:TerminalForm|None=None; certificate_id:str|None=None; verifier_boundary_crossed:bool=False; support_weight:float=1.0; cost_units:float=0.0; gain_units:float=0.0; compression_gain:float=0.0; projection_gain:float=0.0; risk_score:float=0.0; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def total_gain(self): return self.gain_units+self.compression_gain+self.projection_gain-self.cost_units
 def has_truth_boundary(self): return self.terminal_form is not None and bool(self.certificate_id) and self.verifier_boundary_crossed
 def to_dict(self): return {**self.__dict__,"kind":self.kind.value,"atoms":list(self.atoms),"terminal_form":self.terminal_form.value if self.terminal_form else None}
 @classmethod
 def from_dict(cls,d): return cls(str(d["observation_id"]),ReasonObservationKind(str(d.get("kind","UNKNOWN"))),_s(d.get("object_id")),_s(d.get("source_kind")),tuple(map(str,d.get("atoms",()))),dict(d.get("atom_kinds",{})),_s(d.get("outcome")),TerminalForm(str(d["terminal_form"])) if d.get("terminal_form") else None,_s(d.get("certificate_id")),bool(d.get("verifier_boundary_crossed",False)),float(d.get("support_weight",1)),float(d.get("cost_units",0)),float(d.get("gain_units",0)),float(d.get("compression_gain",0)),float(d.get("projection_gain",0)),float(d.get("risk_score",0)),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(cls,t): return cls.from_dict(json.loads(t))
@dataclass
class ReasonCandidate:
 candidate_id:str; kind:ReasonCandidateKind; atoms:tuple[str,...]; status:ReasonStatus=ReasonStatus.CANDIDATE; observation_ids:tuple[str,...]=(); support_count:int=0; support_weight:float=0.0; coverage_count:int=0; coverage_ratio:float=0.0; complexity:int=0; explanatory_gain:float=0.0; compression_score:float=0.0; minimality_score:float=0.0; sufficiency_score:float=0.0; risk_score:float=0.0; load_bearing_atoms:tuple[str,...]=(); decorative_atoms:tuple[str,...]=(); explained_object_ids:tuple[str,...]=(); counterexample_object_ids:tuple[str,...]=(); reason_text:str|None=None; warnings:tuple[str,...]=(); criticals:tuple[str,...]=(); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def is_minimal_candidate(self): return self.kind==ReasonCandidateKind.MINIMAL_REASON_CANDIDATE or self.status==ReasonStatus.MINIMAL_CANDIDATE
 def is_promotable(self,min_support=3,min_coverage_ratio=.2,min_sufficiency=.5,max_complexity=6,max_risk=.5): return self.advisory and not self.criticals and self.support_count>=min_support and self.coverage_ratio>=min_coverage_ratio and self.sufficiency_score>=min_sufficiency and max(self.complexity,len(self.atoms))<=max_complexity and self.risk_score<=max_risk and bool(self.load_bearing_atoms)
 def to_dict(self): return {**self.__dict__,"kind":self.kind.value,"status":self.status.value,"atoms":list(self.atoms),"observation_ids":list(self.observation_ids),"load_bearing_atoms":list(self.load_bearing_atoms),"decorative_atoms":list(self.decorative_atoms),"explained_object_ids":list(self.explained_object_ids),"counterexample_object_ids":list(self.counterexample_object_ids),"warnings":list(self.warnings),"criticals":list(self.criticals)}
 @classmethod
 def from_dict(cls,d): return cls(str(d["candidate_id"]),ReasonCandidateKind(str(d.get("kind","UNKNOWN"))),tuple(map(str,d.get("atoms",()))),ReasonStatus(str(d.get("status","CANDIDATE"))),tuple(map(str,d.get("observation_ids",()))),int(d.get("support_count",0)),float(d.get("support_weight",0)),int(d.get("coverage_count",0)),float(d.get("coverage_ratio",0)),int(d.get("complexity",0)),float(d.get("explanatory_gain",0)),float(d.get("compression_score",0)),float(d.get("minimality_score",0)),float(d.get("sufficiency_score",0)),float(d.get("risk_score",0)),tuple(map(str,d.get("load_bearing_atoms",()))),tuple(map(str,d.get("decorative_atoms",()))),tuple(map(str,d.get("explained_object_ids",()))),tuple(map(str,d.get("counterexample_object_ids",()))),_s(d.get("reason_text")),tuple(map(str,d.get("warnings",()))),tuple(map(str,d.get("criticals",()))),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(cls,t): return cls.from_dict(json.loads(t))
@dataclass
class ReasonNode:
 reason_id:str; kind:ReasonCandidateKind; status:ReasonStatus=ReasonStatus.CANDIDATE; atoms:tuple[str,...]=(); conditions:tuple[str,...]=(); support_count:int=0; coverage_ratio:float=0.0; complexity:int=0; explanatory_gain:float=0.0; compression_score:float=0.0; minimality_score:float=0.0; sufficiency_score:float=0.0; risk_score:float=0.0; source_candidate_id:str|None=None; observation_ids:tuple[str,...]=(); accepted_at:str|None=None; accepted_by:str|None=None; reason_text:str|None=None; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def is_accepted(self): return self.status==ReasonStatus.ACCEPTED
 def explains(self,m): 
  text=_j(dict(m)).lower(); return bool(self.atoms or self.conditions) and any(a in text or _pair(a,m) for a in self.atoms+self.conditions)
 def to_dict(self): return {**self.__dict__,"kind":self.kind.value,"status":self.status.value,"atoms":list(self.atoms),"conditions":list(self.conditions),"observation_ids":list(self.observation_ids)}
 @classmethod
 def from_dict(cls,d): return cls(str(d["reason_id"]),ReasonCandidateKind(str(d.get("kind","UNKNOWN"))),ReasonStatus(str(d.get("status","CANDIDATE"))),tuple(map(str,d.get("atoms",()))),tuple(map(str,d.get("conditions",()))),int(d.get("support_count",0)),float(d.get("coverage_ratio",0)),int(d.get("complexity",0)),float(d.get("explanatory_gain",0)),float(d.get("compression_score",0)),float(d.get("minimality_score",0)),float(d.get("sufficiency_score",0)),float(d.get("risk_score",0)),_s(d.get("source_candidate_id")),tuple(map(str,d.get("observation_ids",()))),_s(d.get("accepted_at")),_s(d.get("accepted_by")),_s(d.get("reason_text")),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(cls,t): return cls.from_dict(json.loads(t))
@dataclass
class ReasonReview:
 review_id:str; candidate_id:str; decision:ReasonReviewDecision; reviewer:str|None=None; reason:str|None=None; required_evidence:tuple[str,...]=(); created_at:str=field(default_factory=lambda:_now()); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def to_dict(self): return {**self.__dict__,"decision":self.decision.value,"required_evidence":list(self.required_evidence)}
 @classmethod
 def from_dict(cls,d): return cls(str(d["review_id"]),str(d["candidate_id"]),ReasonReviewDecision(str(d.get("decision","UNKNOWN"))),_s(d.get("reviewer")),_s(d.get("reason")),tuple(map(str,d.get("required_evidence",()))),str(d.get("created_at") or _now()),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(cls,t): return cls.from_dict(json.loads(t))
@dataclass
class ReasonCompressionReport:
 report_id:str; observations:list[ReasonObservation]=field(default_factory=list); candidates:list[ReasonCandidate]=field(default_factory=list); reviews:list[ReasonReview]=field(default_factory=list); reason_nodes:list[ReasonNode]=field(default_factory=list); status:ReasonCompressionReportStatus=ReasonCompressionReportStatus.EMPTY; created_at:str=field(default_factory=lambda:_now()); summary:dict[str,Any]=field(default_factory=dict); metadata:dict[str,Any]=field(default_factory=lambda:{"advisory_only":True}); advisory:bool=True
 def observation_count(self): return len(self.observations)
 def candidate_count(self): return len(self.candidates)
 def accepted_reason_count(self): return sum(x.is_accepted() for x in self.reason_nodes)
 def critical_count(self): return sum(len(x.criticals) for x in self.candidates)
 def summarize(self): self.summary={"observation_total":len(self.observations),"candidate_total":len(self.candidates),"review_total":len(self.reviews),"reason_node_total":len(self.reason_nodes),"accepted_reason_count":self.accepted_reason_count(),"critical_count":self.critical_count()}; return dict(self.summary)
 def to_dict(self): return {"report_id":self.report_id,"observations":[x.to_dict() for x in self.observations],"candidates":[x.to_dict() for x in self.candidates],"reviews":[x.to_dict() for x in self.reviews],"reason_nodes":[x.to_dict() for x in self.reason_nodes],"status":self.status.value,"created_at":self.created_at,"summary":dict(self.summary),"metadata":dict(self.metadata),"advisory":self.advisory}
 @classmethod
 def from_dict(cls,d): return cls(str(d["report_id"]),[ReasonObservation.from_dict(x) for x in d.get("observations",[])],[ReasonCandidate.from_dict(x) for x in d.get("candidates",[])],[ReasonReview.from_dict(x) for x in d.get("reviews",[])],[ReasonNode.from_dict(x) for x in d.get("reason_nodes",[])],ReasonCompressionReportStatus(str(d.get("status","EMPTY"))),str(d.get("created_at") or _now()),dict(d.get("summary",{})),dict(d.get("metadata",{"advisory_only":True})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(cls,t): return cls.from_dict(json.loads(t))
 def write_json(self,p): _w(p,self.to_json()+"\n")
 @classmethod
 def read_json(cls,p): return cls.from_json(Path(p).read_text())
 def write_jsonl(self,p): _w(p,self.to_json()+"\n")
 @classmethod
 def read_jsonl(cls,p): return [cls.from_json(x) for x in Path(p).read_text().splitlines() if x.strip()]

def make_reason_observation_id(*x): return content_id("reason-observation",x)
def make_reason_candidate_id(*x): return content_id("reason-candidate",x)
def make_reason_node_id(*x): return content_id("reason-node",x)
def make_reason_review_id(*x): return content_id("reason-review",x)
def make_reason_compression_report_id(*x): return content_id("reason-report",x)
def normalize_reason_atom(v):
 s=re.sub(r"[^a-z0-9_:/=\\-]+","_",str(v).strip().lower().replace(" ","_")).strip("_")
 return "unknown" if not s else s if len(s)<=80 else s[:64]+":"+content_id("atom",s)[-12:]
def classify_atom_kind(a,source_key=None):
 k=(source_key or "")+" "+a
 for needle,kind in (("route",ReasonAtomKind.ROUTE),("terminal",ReasonAtomKind.TERMINAL_FORM),("certificate",ReasonAtomKind.CERTIFICATE),("boundary",ReasonAtomKind.TRUST_BOUNDARY),("basin",ReasonAtomKind.BASIN),("phase",ReasonAtomKind.PHASE),("projection",ReasonAtomKind.PROJECTION_RULE),("habit",ReasonAtomKind.HABIT_RULE),("schema",ReasonAtomKind.DIGESTION_SCHEMA),("obstruction",ReasonAtomKind.OBSTRUCTION),("failure",ReasonAtomKind.FAILURE_BOUNDARY),("root",ReasonAtomKind.ROOT_LINK),("reason",ReasonAtomKind.REASON_LINK),("risk",ReasonAtomKind.RISK_SIGNAL),("cost",ReasonAtomKind.COST_SIGNAL),("source",ReasonAtomKind.SOURCE_PATTERN),("target",ReasonAtomKind.TARGET_PATTERN),("condition",ReasonAtomKind.CONDITION)): 
  if needle in k: return kind
 return ReasonAtomKind.METADATA
def extract_atoms_from_mapping(d,*,max_depth=4,max_items=200):
 atoms=[]; kinds={}
 def visit(x,key="",depth=0):
  if depth>max_depth or len(atoms)>=max_items:return
  if isinstance(x,Mapping):
   for k,v in list(x.items())[:max_items]:
    atom=normalize_reason_atom(f"{k}:{v}" if not isinstance(v,(Mapping,list,tuple)) else k); atoms.append(atom); kinds[atom]=classify_atom_kind(atom,str(k)).value; visit(v,str(k),depth+1)
  elif isinstance(x,(list,tuple)):
   for v in list(x)[:max_items]: visit(v,key,depth+1)
  else:
   atom=normalize_reason_atom(f"{key}:{x}" if key else x); atoms.append(atom); kinds[atom]=classify_atom_kind(atom,key).value
 visit(d); uniq=tuple(dict.fromkeys(atoms)); return uniq,kinds
def _ro(kind,obj_id,data,**kw):
 atoms,kinds=extract_atoms_from_mapping(data); return ReasonObservation(make_reason_observation_id(kind.value,obj_id,atoms),kind,obj_id,atoms=atoms,atom_kinds=kinds,metadata=dict(data),**kw)
def reason_observation_from_lawbook_entry(e): return _ro(ReasonObservationKind.LAWBOOK_ENTRY,e.entry_id,e.to_dict(),terminal_form=e.terminal_form,certificate_id=e.certificate_id,verifier_boundary_crossed=e.verifier_boundary_crossed)
def reason_observations_from_lawbook_store(s): return [reason_observation_from_lawbook_entry(e) for e in s.entries]
def reason_observations_from_lawbook_query_report(r): return [_ro(ReasonObservationKind.LAWBOOK_QUERY,a.answer_id,a.to_dict(),terminal_form=a.terminal_form,certificate_id=a.certificate_id,verifier_boundary_crossed=a.verifier_boundary_crossed) for a in r.answers]
def reason_observations_from_structural_identity_report(r): return [_ro(ReasonObservationKind.STRUCTURAL_IDENTITY,c.candidate_id,c.to_dict()) for c in r.merge_candidates]
def reason_observation_from_habit_candidate(c): return _ro(ReasonObservationKind.HABIT,c.candidate_id,c.to_dict(),risk_score=c.risk_score)
def reason_observation_from_habit_rule(r): return _ro(ReasonObservationKind.HABIT,r.rule_id,r.to_dict(),risk_score=r.risk_score)
def reason_observations_from_habit_report(r): return [reason_observation_from_habit_candidate(c) for c in r.candidates]+[reason_observation_from_habit_rule(x) for x in r.rules]
def reason_observation_from_discovery_value_score(s): return _ro(ReasonObservationKind.DISCOVERY_VALUE,s.score_id,s.to_dict(),gain_units=s.expected_gain,risk_score=s.risk_estimate)
def reason_observations_from_discovery_value_report(r): return [reason_observation_from_discovery_value_score(s) for s in r.scores]
def reason_observations_from_projection_candidates(cs): return [_ro(ReasonObservationKind.PROJECTION,c.candidate_id,c.to_dict(),projection_gain=c.confidence) for c in cs]
def reason_observation_from_proof_digestion_trace(t): return _ro(ReasonObservationKind.PROOF_DIGESTION,t.trace_id,t.to_dict(),compression_gain=t.digestion_score())
def reason_observation_from_verifier_feedback(f): return _ro(ReasonObservationKind.VERIFIER_FEEDBACK,f.feedback_id,f.to_dict())
def reason_observation_from_repair_loop(t): return _ro(ReasonObservationKind.REPAIR_LOOP,t.trace_id,t.to_dict())
def reason_observation_from_curriculum_stage(s): return _ro(ReasonObservationKind.CURRICULUM,s.stage_id,s.to_dict())
def reason_observations_from_curriculum(c): return [reason_observation_from_curriculum_stage(s) for s in c.stages]
def reason_observation_from_alchemical_trace(t): return _ro(ReasonObservationKind.ALCHEMICAL_TRACE,t.trace_id,t.to_dict(),compression_gain=t.total_compression_gain())
def reason_observation_from_agent_experience(e): return _ro(ReasonObservationKind.AGENT_EXPERIENCE,e.experience_id,e.to_dict(),cost_units=e.cost_units,compression_gain=e.compression_gain,projection_gain=e.projection_gain,terminal_form=e.terminal_form,certificate_id=e.certificate_id,verifier_boundary_crossed=e.verifier_boundary_crossed)
def reason_observation_from_route_telemetry_event(e): return _ro(ReasonObservationKind.ROUTE_TELEMETRY,_s(e.get("event_id")),dict(e),cost_units=float(e.get("cost_units",0) or 0),gain_units=float(e.get("gain_units",0) or 0),compression_gain=float(e.get("compression_gain",0) or 0),projection_gain=float(e.get("projection_gain",0) or 0))
def reason_observation_from_mapping(d): return reason_observation_from_route_telemetry_event(d) if "route" in d or "route_kind" in d else _ro(ReasonObservationKind.RAW_EVENT,_s(d.get("id")),dict(d))
def reason_observations_from_object(o):
 from mathgraph.discovery_value import DiscoveryValueReport,DiscoveryValueScore
 from mathgraph.habit_rules import HabitCandidate,HabitFormationReport,HabitRule
 from mathgraph.lawbook_query import LawbookQueryReport
 from mathgraph.projection import ProjectionCandidate
 from mathgraph.proof_digestion import ProofDigestionTrace
 from mathgraph.structural_identity import StructuralIdentityReport
 from mathgraph.verifier_feedback import RepairLoopTrace,VerifierFeedback
 if isinstance(o,LawbookEntry): return [reason_observation_from_lawbook_entry(o)]
 if isinstance(o,LawbookStore): return reason_observations_from_lawbook_store(o)
 if isinstance(o,LawbookQueryReport): return reason_observations_from_lawbook_query_report(o)
 if isinstance(o,StructuralIdentityReport): return reason_observations_from_structural_identity_report(o)
 if isinstance(o,HabitFormationReport): return reason_observations_from_habit_report(o)
 if isinstance(o,HabitCandidate): return [reason_observation_from_habit_candidate(o)]
 if isinstance(o,HabitRule): return [reason_observation_from_habit_rule(o)]
 if isinstance(o,DiscoveryValueReport): return reason_observations_from_discovery_value_report(o)
 if isinstance(o,DiscoveryValueScore): return [reason_observation_from_discovery_value_score(o)]
 if isinstance(o,ProjectionCandidate): return reason_observations_from_projection_candidates([o])
 if isinstance(o,ProofDigestionTrace): return [reason_observation_from_proof_digestion_trace(o)]
 if isinstance(o,VerifierFeedback): return [reason_observation_from_verifier_feedback(o)]
 if isinstance(o,RepairLoopTrace): return [reason_observation_from_repair_loop(o)]
 if isinstance(o,ContinuationCurriculum): return reason_observations_from_curriculum(o)
 if isinstance(o,CurriculumStage): return [reason_observation_from_curriculum_stage(o)]
 if isinstance(o,AlchemicalTrace): return [reason_observation_from_alchemical_trace(o)]
 if isinstance(o,AgentExperience): return [reason_observation_from_agent_experience(o)]
 if isinstance(o,Mapping): return [reason_observation_from_mapping(o)]
 return []
def _success(o): return o.has_truth_boundary() or o.total_gain()>0 or str(o.outcome or "").upper() not in {"FAILED_SEARCH","INVALID_CANDIDATE","KILLED_ROUTE","AMBIGUOUS"}
def _kind(atoms,minimal=False):
 text=" ".join(atoms)
 if "obstruction" in text or "failure" in text:return ReasonCandidateKind.OBSTRUCTION_EXPLANATION
 if "projection" in text:return ReasonCandidateKind.PROJECTION_EXPLANATION
 if "habit" in text:return ReasonCandidateKind.HABIT_EXPLANATION
 if "structural" in text or "merge" in text:return ReasonCandidateKind.STRUCTURAL_IDENTITY_EXPLANATION
 if "schema" in text:return ReasonCandidateKind.PROOF_SCHEMA_EXPLANATION
 if "risk" in text:return ReasonCandidateKind.RISK_AVOIDANCE_REASON
 if "cost" in text:return ReasonCandidateKind.COST_AVOIDANCE_REASON
 return ReasonCandidateKind.MINIMAL_REASON_CANDIDATE if minimal else ReasonCandidateKind.SUFFICIENT_REASON
def build_reason_candidates(obs,*,min_support=2,max_atom_set_size=4):
 pool=Counter(a for o in obs for a in o.atoms); combos=Counter()
 for o in obs:
  atoms=sorted(o.atoms,key=lambda a:(-pool[a],a))[:24]
  for n in range(1,min(max_atom_set_size,len(atoms))+1):
   for c in itertools.combinations(atoms,n): combos[c]+=1
 out=[]
 for atoms,support in combos.most_common(500):
  if support<min_support: continue
  xs=[o for o in obs if set(atoms)<=set(o.atoms)]; success=sum(_success(o) for o in xs); cov=support/len(obs) if obs else 0; gain=sum(o.total_gain() for o in xs); risk=mean(o.risk_score for o in xs) if xs else 0
  c=ReasonCandidate(make_reason_candidate_id(atoms),_kind(atoms),tuple(atoms),observation_ids=tuple(o.observation_id for o in xs),support_count=support,support_weight=sum(o.support_weight for o in xs),coverage_count=support,coverage_ratio=cov,complexity=len(atoms),explanatory_gain=gain,compression_score=gain/max(1,len(atoms)),sufficiency_score=success/support,risk_score=risk,explained_object_ids=tuple(o.object_id for o in xs if o.object_id),warnings=tuple(x for x,ok in (("low support",support<3),("high complexity",len(atoms)>6),("high risk",risk>.5)) if ok),metadata={"reason_advisory_only":True})
  out.append(check_reason_minimality(c,obs))
 return out
def check_reason_minimality(c,obs):
 if len(c.atoms)==1:
  c.load_bearing_atoms=c.atoms; c.minimality_score=1; c.kind=ReasonCandidateKind.MINIMAL_REASON_CANDIDATE; c.status=ReasonStatus.MINIMAL_CANDIDATE; return c
 load=[]; deco=[]
 for atom in c.atoms:
  rem=set(c.atoms)-{atom}; xs=[o for o in obs if rem<=set(o.atoms)]; suff=(sum(_success(o) for o in xs)/len(xs)) if xs else 0
  if len(xs)>c.support_count*1.05 or suff<c.sufficiency_score-.05: load.append(atom)
  else: deco.append(atom)
 c.load_bearing_atoms=tuple(load); c.decorative_atoms=tuple(deco); c.minimality_score=len(load)/len(c.atoms)
 if load and c.minimality_score>=.5: c.kind=ReasonCandidateKind.MINIMAL_REASON_CANDIDATE; c.status=ReasonStatus.MINIMAL_CANDIDATE
 if not load: c.warnings=tuple(list(c.warnings)+["no load-bearing atoms"])
 return c
def review_reason_candidate(c,*,reviewer=None,min_support=3,min_coverage_ratio=.2,min_sufficiency=.5,max_complexity=6,max_risk=.5):
 if not c.advisory or c.criticals: d=ReasonReviewDecision.REJECT
 elif c.reason_text and any(x in c.reason_text.lower() for x in ("proof","certificate","necessity")): d=ReasonReviewDecision.NEEDS_FORMALIZATION
 elif c.support_count<min_support or c.coverage_ratio<min_coverage_ratio: d=ReasonReviewDecision.NEEDS_MORE_EVIDENCE
 elif not c.load_bearing_atoms: d=ReasonReviewDecision.NEEDS_MINIMALITY_CHECK
 elif c.complexity>max_complexity: d=ReasonReviewDecision.NEEDS_LOWER_COMPLEXITY
 elif c.risk_score<=max_risk and c.sufficiency_score>=min_sufficiency: d=ReasonReviewDecision.ACCEPT
 else: d=ReasonReviewDecision.HOLD_IN_CHORA
 return ReasonReview(make_reason_review_id(c.candidate_id,d.value),c.candidate_id,d,reviewer,required_evidence=c.warnings)
def promote_reason_candidate(c,r,*,accepted_by=None):
 if r.decision==ReasonReviewDecision.ACCEPT and c.criticals: raise ValueError("critical reason")
 ok=r.decision==ReasonReviewDecision.ACCEPT
 return ReasonNode(make_reason_node_id(c.candidate_id,r.review_id),c.kind,ReasonStatus.ACCEPTED if ok else ReasonStatus.REJECTED if r.decision==ReasonReviewDecision.REJECT else ReasonStatus.NEEDS_REVIEW,c.atoms,c.load_bearing_atoms or c.atoms,c.support_count,c.coverage_ratio,c.complexity,c.explanatory_gain,c.compression_score,c.minimality_score,c.sufficiency_score,c.risk_score,c.candidate_id,c.observation_ids,_now() if ok else None,accepted_by,c.reason_text,{"reason_node_not_truth":True},True)
def build_reason_compression_report(objects=(),observations=(),*,auto_candidates=True,auto_review=True,auto_promote=False,reviewer=None,min_support=3,min_coverage_ratio=.2,min_sufficiency=.5,max_complexity=6,max_risk=.5,max_atom_set_size=4):
 obs=list(observations)+[x for o in objects for x in reason_observations_from_object(o)]; cs=build_reason_candidates(obs,min_support=min(2,min_support),max_atom_set_size=max_atom_set_size) if auto_candidates else []; rs=[review_reason_candidate(c,reviewer=reviewer,min_support=min_support,min_coverage_ratio=min_coverage_ratio,min_sufficiency=min_sufficiency,max_complexity=max_complexity,max_risk=max_risk) for c in cs] if auto_review else []; nodes=[promote_reason_candidate(c,r,accepted_by=reviewer) for c in cs for r in rs if r.candidate_id==c.candidate_id and (auto_promote and r.decision==ReasonReviewDecision.ACCEPT)]
 rep=ReasonCompressionReport(make_reason_compression_report_id([o.observation_id for o in obs]),obs,cs,rs,nodes); rep.summarize(); rep.status=ReasonCompressionReportStatus.EMPTY if not obs else ReasonCompressionReportStatus.HAS_CRITICALS if rep.critical_count() else ReasonCompressionReportStatus.ACCEPTED_REASONS if rep.accepted_reason_count() else ReasonCompressionReportStatus.REVIEWED if rs else ReasonCompressionReportStatus.MINIMAL_CANDIDATES_FOUND if any(c.is_minimal_candidate() for c in cs) else ReasonCompressionReportStatus.CANDIDATES_FOUND if cs else ReasonCompressionReportStatus.OBSERVED; return rep
def apply_reason_nodes(reasons,scores):
 out=[]
 for row in scores:
  hits=[r for r in reasons if r.is_accepted() and r.explains(row)]; base=float(row.get("score",row.get("raw_score",0)) or 0); delta=sum(max(0,r.sufficiency_score*(1-r.risk_score)) for r in hits)
  out.append({**dict(row),"reason_node_ids":[r.reason_id for r in hits],"reason_delta":delta,"reason_adjusted_score":base+delta,"reason_advisory_only":True})
 return out
def rank_routes_with_reasons(reasons,scores): return sorted(apply_reason_nodes(reasons,scores),key=lambda x:x["reason_adjusted_score"],reverse=True)
def reason_report_to_lawbook_candidates(r): return [LawbookEntry(make_lawbook_entry_id("reason",n.reason_id),LawbookEntryKind.REUSABLE_SCHEMA_ENTRY,LawbookEntryStatus.CANDIDATE,conditions=n.conditions,metadata={"reason_node_not_truth":True,"reason_node_id":n.reason_id,"reason_advisory_only":True,"reason_atoms":list(n.atoms),"load_bearing_atoms":list(n.conditions)},advisory=True) for n in r.reason_nodes if n.is_accepted()]
def reason_report_to_continuation_outputs(r): return [ContinuationActionOutput(make_continuation_output_id({"reason":c.candidate_id}),"reason_compression",ContinuationOutputKind.TASK,ContinuationActionStatus.ADVISORY_ONLY,task_payload={"task":"review reason","candidate_id":c.candidate_id},advisory=True) for c in r.candidates]
def reason_report_to_curriculum(r):
 stages=[CurriculumStage(make_curriculum_stage_id("reason",n.reason_id),CurriculumStageKind.DIGESTION_TASK if n.is_accepted() else CurriculumStageKind.RESIDUAL_REVIEW,CurriculumStageStatus.ADVISORY_ONLY,title="Reuse advisory reason",metadata={"reason_node_id":n.reason_id},advisory=True) for n in r.reason_nodes]
 return ContinuationCurriculum(make_curriculum_id("reason",r.report_id),strategy=CurriculumBuildStrategy.MIXED,stages=stages,status=CurriculumTraceStatus.TASKS_EMITTED if stages else CurriculumTraceStatus.EMPTY,metadata={"advisory_only":True})
def reason_report_to_discovery_value_scores(r):
 out=[]
 for c in r.candidates:
  sig=DiscoveryValueSignal(content_id("reason-signal",c.candidate_id),DiscoveryValueSignalKind.REUSE_VALUE,c.compression_score,reason="reason candidate",source_object_kind=DiscoveryValueObjectKind.RAW_TASK); s=DiscoveryValueScore(content_id("reason-score",c.candidate_id),c.candidate_id,DiscoveryValueObjectKind.RAW_TASK,signals=[sig],metadata={"reason_advisory_only":True}); s.recompute(); out.append(s)
 return out
def reason_report_to_structural_identity_objects(r): return [{"reason_id":n.reason_id,"atoms":list(n.atoms),"conditions":list(n.conditions),"advisory":True} for n in r.reason_nodes]
def reason_report_to_alchemical_trace(r):
 t=AlchemicalTrace(make_alchemical_trace_id("reason",r.report_id))
 for p in (AlchemicalPhase.RAW_MATTER,AlchemicalPhase.CALCINATION,AlchemicalPhase.SUBLIMATION,AlchemicalPhase.DISTILLATION,AlchemicalPhase.COAGULATION): t.add_step(phase=p,status=AlchemicalStatus.ADVISORY_ONLY)
 return t
def reason_report_to_agent_experiences(r,agent_id=None): return [AgentExperience(content_id("reason-exp",(r.report_id,c.candidate_id)),agent_id or "reason-compression",None,None,"reason_compression",None,AgentExperienceOutcome.ADVISORY_ONLY,metadata={"candidate_id":c.candidate_id}) for c in r.candidates]
def reason_report_to_route_telemetry_events(r): return [{"event_id":content_id("reason-telemetry",(r.report_id,c.candidate_id)),"route_kind":"reason_compression","outcome":c.status.value,"reason_advisory_only":True} for c in r.candidates]
def audit_reason_candidate(c):
 fs=[]
 if not c.advisory: fs.append(_f("CRITICAL","REASON_NON_ADVISORY","reason candidate non-advisory",c.candidate_id))
 if c.support_count<3: fs.append(_f("WARNING","REASON_LOW_SUPPORT","reason candidate low support",c.candidate_id))
 if not c.load_bearing_atoms: fs.append(_f("WARNING","REASON_NO_LOAD_BEARING","reason candidate lacks load-bearing atoms",c.candidate_id))
 if c.reason_text and any(x in c.reason_text.lower() for x in ("proof","certificate","necessity")): fs.append(_f("CRITICAL","REASON_TEXT_CLAIMS_PROOF","reason text claims proof-like force",c.candidate_id))
 return fs
def audit_reason_node(n,max_risk=.5):
 fs=[]
 if not n.advisory: fs.append(_f("CRITICAL","REASON_NODE_NON_ADVISORY","reason node non-advisory",n.reason_id))
 if n.is_accepted() and not n.conditions: fs.append(_f("CRITICAL","REASON_ACCEPTED_WITHOUT_LOAD_BEARING","accepted reason lacks conditions",n.reason_id))
 if n.is_accepted() and n.risk_score>max_risk: fs.append(_f("CRITICAL","REASON_ACCEPTED_HIGH_RISK","accepted reason high risk",n.reason_id))
 if n.reason_text and any(x in n.reason_text.lower() for x in ("proof","certificate","necessity")): fs.append(_f("CRITICAL","REASON_TEXT_CLAIMS_PROOF","reason text claims proof-like force",n.reason_id))
 return fs
def audit_reason_report(r): return [x for c in r.candidates for x in audit_reason_candidate(c)]+[x for n in r.reason_nodes for x in audit_reason_node(n)]
def _pair(a,m):
 if ":" not in a:return False
 k,v=a.split(":",1); return str(m.get(k,"")).lower()==v.lower()
def _s(x): return None if x is None else str(x)
def _now(): return datetime.now(timezone.utc).isoformat()
def _j(x): return json.dumps(x,sort_keys=True,separators=(",",":"))
def _w(p,t): path=Path(p); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(t,encoding="utf-8")
def _f(sev,code,msg,obj): return {"severity":sev,"code":code,"message":msg,"object_id":obj}
