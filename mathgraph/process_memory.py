"""Replayable advisory process memory for MathGraph work histories."""
from __future__ import annotations
import json
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
from mathgraph.reason_compression import ReasonObservation,ReasonObservationKind,extract_atoms_from_mapping,make_reason_observation_id

def _enum(name,vals): return Enum(name,{v:v for v in vals},type=str)
ProcessContextKind=_enum("ProcessContextKind","CLAIM ROUTE LAWBOOK_ENTRY CERTIFICATE OBSTRUCTION PROJECTION DIGESTION REPAIR FEEDBACK CURRICULUM STRUCTURAL_IDENTITY HABIT REASON DISCOVERY_VALUE ALCHEMICAL_PHASE AGENT_EXPERIENCE TELEMETRY RAW_EVENT UNKNOWN".split())
ProcessContextRole=_enum("ProcessContextRole","INCLUDED EXCLUDED USED IGNORED KILLED BLOCKED GENERATED PROMOTED_BY_VERIFIER ACCEPTED_BY_REVIEW CANDIDATE_ONLY ADVISORY_ONLY PRIOR_CONTEXT NEXT_CONTEXT UNKNOWN".split())
ProcessEliminationKind=_enum("ProcessEliminationKind","VERIFIER_FAILURE FINITE_VALIDATION_FAILURE IMPORTER_FAILURE CHAIN_AUDIT_FAILURE SOURCE_NOT_PRESERVED TARGET_NOT_SEPARATED INVALID_CANDIDATE FAILED_SEARCH KILLED_ROUTE OVER_BUDGET HIGH_RISK LOW_VALUE DUPLICATE_MEMORY AMBIGUOUS_MEMORY NEEDS_REPAIR NEEDS_DIGESTION NEEDS_FORMALIZATION HELD_IN_CHORA HUMAN_REVIEW_REQUIRED UNKNOWN".split())
ProcessTransitionKind=_enum("ProcessTransitionKind","CLAIM_TO_ACTION ACTION_TO_CURRICULUM CURRICULUM_TO_EPISODE EPISODE_TO_VERIFIER VERIFIER_TO_CERTIFICATE VERIFIER_TO_FEEDBACK FEEDBACK_TO_REPAIR PROOF_TO_DIGESTION DIGESTION_TO_LAWBOOK_CANDIDATE VALUE_TO_ROUTE_PRIORITY LAWBOOK_ACCEPTANCE LAWBOOK_QUERY QUERY_TO_KNOWN_SKIP STRUCTURAL_IDENTITY_TO_REVIEW HABIT_TO_ROUTE_PRIORITY REASON_TO_EXPLANATION PROJECTION_TO_RESIDUAL ALCHEMY_PHASE_STEP AGENT_EXPERIENCE_UPDATE RAW_TO_PROCESS UNKNOWN".split())
ProcessEpisodeStatus=_enum("ProcessEpisodeStatus","CREATED RUNNING TERMINAL_VERIFIED_PROOF TERMINAL_FINITE_COUNTERMODEL TERMINAL_NAMED_OBSTRUCTION RESIDUAL ADVISORY_ONLY FAILED AMBIGUOUS HELD_IN_CHORA HAS_WARNINGS HAS_CRITICALS UNKNOWN".split())
ProcessMemoryQueryKind=_enum("ProcessMemoryQueryKind","EPISODE CLAIM ROUTE ARTIFACT CERTIFICATE OBSTRUCTION LAWBOOK_ENTRY PROJECTION DIGESTION REPAIR HABIT REASON ELIMINATION STATUS AGENT TEXT TRUST_SUMMARY UNKNOWN".split())
ProcessMemoryAnswerStatus=_enum("ProcessMemoryAnswerStatus","FOUND FOUND_TERMINAL_BOUNDARY FOUND_ADVISORY FOUND_RESIDUAL FOUND_ELIMINATION FOUND_AMBIGUOUS NOT_FOUND INVALID_QUERY HAS_WARNINGS HAS_CRITICALS UNKNOWN".split())
ProcessMemoryReportStatus=_enum("ProcessMemoryReportStatus","EMPTY RECORDED QUERIED ANSWERED HAS_WARNINGS HAS_CRITICALS ADVISORY_ONLY".split())

@dataclass
class ProcessContextItem:
 context_id:str; kind:ProcessContextKind; role:ProcessContextRole; object_id:str|None=None; label:str|None=None; source_kind:str|None=None; route:str|None=None; claim_id:str|None=None; certificate_id:str|None=None; terminal_form:TerminalForm|None=None; verifier_boundary_crossed:bool=False; accepted_public_memory:bool=False; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def has_truth_boundary(self): return self.terminal_form is not None and bool(self.certificate_id) and self.verifier_boundary_crossed
 def to_dict(self): return {**self.__dict__,"kind":self.kind.value,"role":self.role.value,"terminal_form":self.terminal_form.value if self.terminal_form else None}
 @classmethod
 def from_dict(cls,d): return cls(str(d["context_id"]),ProcessContextKind(str(d.get("kind","UNKNOWN"))),ProcessContextRole(str(d.get("role","UNKNOWN"))),_s(d.get("object_id")),_s(d.get("label")),_s(d.get("source_kind")),_s(d.get("route")),_s(d.get("claim_id")),_s(d.get("certificate_id")),TerminalForm(str(d["terminal_form"])) if d.get("terminal_form") else None,bool(d.get("verifier_boundary_crossed",False)),bool(d.get("accepted_public_memory",False)),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(cls,t): return cls.from_dict(json.loads(t))
@dataclass
class ProcessElimination:
 elimination_id:str; kind:ProcessEliminationKind; object_id:str|None=None; route:str|None=None; reason:str|None=None; killed_by:str|None=None; claim_id:str|None=None; cost_units:float=0.0; risk_score:float=0.0; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def to_dict(self): return {**self.__dict__,"kind":self.kind.value}
 @classmethod
 def from_dict(cls,d): return cls(str(d["elimination_id"]),ProcessEliminationKind(str(d.get("kind","UNKNOWN"))),_s(d.get("object_id")),_s(d.get("route")),_s(d.get("reason")),_s(d.get("killed_by")),_s(d.get("claim_id")),float(d.get("cost_units",0)),float(d.get("risk_score",0)),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(cls,t): return cls.from_dict(json.loads(t))
@dataclass
class ProcessTransition:
 transition_id:str; kind:ProcessTransitionKind; from_id:str|None=None; to_id:str|None=None; route:str|None=None; claim_id:str|None=None; cost_units:float=0.0; gain_units:float=0.0; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def to_dict(self): return {**self.__dict__,"kind":self.kind.value}
 @classmethod
 def from_dict(cls,d): return cls(str(d["transition_id"]),ProcessTransitionKind(str(d.get("kind","UNKNOWN"))),_s(d.get("from_id")),_s(d.get("to_id")),_s(d.get("route")),_s(d.get("claim_id")),float(d.get("cost_units",0)),float(d.get("gain_units",0)),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(cls,t): return cls.from_dict(json.loads(t))
@dataclass
class ProcessEpisodeRecord:
 episode_id:str; status:ProcessEpisodeStatus=ProcessEpisodeStatus.CREATED; claim_id:str|None=None; route:str|None=None; terminal_form:TerminalForm|None=None; certificate_id:str|None=None; verifier_boundary_crossed:bool=False; obstruction_id:str|None=None; contexts:list[ProcessContextItem]=field(default_factory=list); eliminations:list[ProcessElimination]=field(default_factory=list); transitions:list[ProcessTransition]=field(default_factory=list); artifact_ids:tuple[str,...]=(); lawbook_entry_ids:tuple[str,...]=(); habit_rule_ids:tuple[str,...]=(); reason_node_ids:tuple[str,...]=(); projection_candidate_ids:tuple[str,...]=(); agent_ids:tuple[str,...]=(); cost_units:float=0.0; gain_units:float=0.0; residual_delta:int=0; compression_gain:float=0.0; projection_gain:float=0.0; created_at:str=field(default_factory=lambda:_now()); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def has_truth_boundary(self): return self.terminal_form is not None and bool(self.certificate_id) and self.verifier_boundary_crossed
 def context_count(self): return len(self.contexts)
 def elimination_count(self): return len(self.eliminations)
 def transition_count(self): return len(self.transitions)
 def total_gain(self): return self.gain_units+self.compression_gain+self.projection_gain-self.cost_units
 def to_dict(self): return {**self.__dict__,"status":self.status.value,"terminal_form":self.terminal_form.value if self.terminal_form else None,"contexts":[x.to_dict() for x in self.contexts],"eliminations":[x.to_dict() for x in self.eliminations],"transitions":[x.to_dict() for x in self.transitions],"artifact_ids":list(self.artifact_ids),"lawbook_entry_ids":list(self.lawbook_entry_ids),"habit_rule_ids":list(self.habit_rule_ids),"reason_node_ids":list(self.reason_node_ids),"projection_candidate_ids":list(self.projection_candidate_ids),"agent_ids":list(self.agent_ids)}
 @classmethod
 def from_dict(cls,d): return cls(str(d["episode_id"]),ProcessEpisodeStatus(str(d.get("status","CREATED"))),_s(d.get("claim_id")),_s(d.get("route")),TerminalForm(str(d["terminal_form"])) if d.get("terminal_form") else None,_s(d.get("certificate_id")),bool(d.get("verifier_boundary_crossed",False)),_s(d.get("obstruction_id")),[ProcessContextItem.from_dict(x) for x in d.get("contexts",[])],[ProcessElimination.from_dict(x) for x in d.get("eliminations",[])],[ProcessTransition.from_dict(x) for x in d.get("transitions",[])],tuple(map(str,d.get("artifact_ids",()))),tuple(map(str,d.get("lawbook_entry_ids",()))),tuple(map(str,d.get("habit_rule_ids",()))),tuple(map(str,d.get("reason_node_ids",()))),tuple(map(str,d.get("projection_candidate_ids",()))),tuple(map(str,d.get("agent_ids",()))),float(d.get("cost_units",0)),float(d.get("gain_units",0)),int(d.get("residual_delta",0)),float(d.get("compression_gain",0)),float(d.get("projection_gain",0)),str(d.get("created_at") or _now()),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(cls,t): return cls.from_dict(json.loads(t))
@dataclass
class ProcessMemoryQuery:
 query_id:str; kind:ProcessMemoryQueryKind; episode_id:str|None=None; claim_id:str|None=None; route:str|None=None; object_id:str|None=None; certificate_id:str|None=None; lawbook_entry_id:str|None=None; habit_rule_id:str|None=None; reason_node_id:str|None=None; agent_id:str|None=None; text:str|None=None; include_advisory:bool=True; include_eliminations:bool=True; include_context:bool=True; metadata:dict[str,Any]=field(default_factory=dict)
 def to_dict(self): return {**self.__dict__,"kind":self.kind.value}
 @classmethod
 def from_dict(cls,d): return cls(str(d["query_id"]),ProcessMemoryQueryKind(str(d.get("kind","UNKNOWN"))),*[_s(d.get(k)) for k in ("episode_id","claim_id","route","object_id","certificate_id","lawbook_entry_id","habit_rule_id","reason_node_id","agent_id","text")],bool(d.get("include_advisory",True)),bool(d.get("include_eliminations",True)),bool(d.get("include_context",True)),dict(d.get("metadata",{})))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(cls,t): return cls.from_dict(json.loads(t))
@dataclass
class ProcessMemoryAnswer:
 answer_id:str; query_id:str; status:ProcessMemoryAnswerStatus; matched_episode_ids:tuple[str,...]=(); matched_context_ids:tuple[str,...]=(); matched_elimination_ids:tuple[str,...]=(); matched_transition_ids:tuple[str,...]=(); terminal_form:TerminalForm|None=None; certificate_id:str|None=None; verifier_boundary_crossed:bool=False; explanation:str|None=None; warnings:tuple[str,...]=(); criticals:tuple[str,...]=(); evidence:dict[str,Any]=field(default_factory=dict); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def has_truth_boundary(self): return self.terminal_form is not None and bool(self.certificate_id) and self.verifier_boundary_crossed
 def to_dict(self): return {**self.__dict__,"status":self.status.value,"matched_episode_ids":list(self.matched_episode_ids),"matched_context_ids":list(self.matched_context_ids),"matched_elimination_ids":list(self.matched_elimination_ids),"matched_transition_ids":list(self.matched_transition_ids),"terminal_form":self.terminal_form.value if self.terminal_form else None,"warnings":list(self.warnings),"criticals":list(self.criticals)}
 @classmethod
 def from_dict(cls,d): return cls(str(d["answer_id"]),str(d["query_id"]),ProcessMemoryAnswerStatus(str(d.get("status","UNKNOWN"))),tuple(map(str,d.get("matched_episode_ids",()))),tuple(map(str,d.get("matched_context_ids",()))),tuple(map(str,d.get("matched_elimination_ids",()))),tuple(map(str,d.get("matched_transition_ids",()))),TerminalForm(str(d["terminal_form"])) if d.get("terminal_form") else None,_s(d.get("certificate_id")),bool(d.get("verifier_boundary_crossed",False)),_s(d.get("explanation")),tuple(map(str,d.get("warnings",()))),tuple(map(str,d.get("criticals",()))),dict(d.get("evidence",{})),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(cls,t): return cls.from_dict(json.loads(t))
@dataclass
class ProcessMemoryStore:
 store_id:str; episodes:list[ProcessEpisodeRecord]=field(default_factory=list); created_at:str=field(default_factory=lambda:_now()); summary:dict[str,Any]=field(default_factory=dict); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def episode_count(self): return len(self.episodes)
 def context_count(self): return sum(len(e.contexts) for e in self.episodes)
 def elimination_count(self): return sum(len(e.eliminations) for e in self.episodes)
 def transition_count(self): return sum(len(e.transitions) for e in self.episodes)
 def add_episode(self,e): self.episodes.append(e)
 def find_by_episode_id(self,x): return [e for e in self.episodes if e.episode_id==x]
 def find_by_claim_id(self,x): return [e for e in self.episodes if e.claim_id==x]
 def find_by_route(self,x): return [e for e in self.episodes if e.route==x or (e.route and x in e.route)]
 def find_by_certificate_id(self,x): return [e for e in self.episodes if e.certificate_id==x]
 def find_by_lawbook_entry_id(self,x): return [e for e in self.episodes if x in e.lawbook_entry_ids]
 def find_by_habit_rule_id(self,x): return [e for e in self.episodes if x in e.habit_rule_ids]
 def find_by_reason_node_id(self,x): return [e for e in self.episodes if x in e.reason_node_ids]
 def find_by_agent_id(self,x): return [e for e in self.episodes if x in e.agent_ids]
 def summarize(self):
  self.summary={"episode_total":len(self.episodes),"context_total":self.context_count(),"elimination_total":self.elimination_count(),"transition_total":self.transition_count(),"terminal_boundary_count":sum(e.has_truth_boundary() for e in self.episodes),"verified_proof_count":sum(e.terminal_form==TerminalForm.VERIFIED_PROOF for e in self.episodes),"finite_countermodel_count":sum(e.terminal_form==TerminalForm.FINITE_COUNTERMODEL for e in self.episodes),"named_obstruction_count":sum(e.terminal_form==TerminalForm.NAMED_OBSTRUCTION for e in self.episodes),"advisory_episode_count":sum(not e.has_truth_boundary() for e in self.episodes),"residual_episode_count":sum(e.status==ProcessEpisodeStatus.RESIDUAL for e in self.episodes),"failed_episode_count":sum(e.status==ProcessEpisodeStatus.FAILED for e in self.episodes),"route_count":len({e.route for e in self.episodes if e.route}),"claim_count":len({e.claim_id for e in self.episodes if e.claim_id}),"certificate_count":len({e.certificate_id for e in self.episodes if e.certificate_id}),"lawbook_entry_count":len({x for e in self.episodes for x in e.lawbook_entry_ids}),"habit_rule_count":len({x for e in self.episodes for x in e.habit_rule_ids}),"reason_node_count":len({x for e in self.episodes for x in e.reason_node_ids}),"agent_count":len({x for e in self.episodes for x in e.agent_ids})}; return dict(self.summary)
 def to_dict(self): return {"store_id":self.store_id,"episodes":[e.to_dict() for e in self.episodes],"created_at":self.created_at,"summary":dict(self.summary),"metadata":dict(self.metadata),"advisory":self.advisory}
 @classmethod
 def from_dict(cls,d): return cls(str(d["store_id"]),[ProcessEpisodeRecord.from_dict(x) for x in d.get("episodes",[])],str(d.get("created_at") or _now()),dict(d.get("summary",{})),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(cls,t): return cls.from_dict(json.loads(t))
 def write_json(self,p): _w(p,self.to_json()+"\n")
 @classmethod
 def read_json(cls,p): return cls.from_json(Path(p).read_text())
 def write_jsonl(self,p): _w(p,self.to_json()+"\n")
 @classmethod
 def read_jsonl(cls,p): return [cls.from_json(x) for x in Path(p).read_text().splitlines() if x.strip()]
@dataclass
class ProcessMemoryReport:
 report_id:str; store:ProcessMemoryStore|None=None; queries:list[ProcessMemoryQuery]=field(default_factory=list); answers:list[ProcessMemoryAnswer]=field(default_factory=list); status:ProcessMemoryReportStatus=ProcessMemoryReportStatus.EMPTY; created_at:str=field(default_factory=lambda:_now()); summary:dict[str,Any]=field(default_factory=dict); metadata:dict[str,Any]=field(default_factory=lambda:{"advisory_only":True}); advisory:bool=True
 def query_count(self): return len(self.queries)
 def answer_count(self): return len(self.answers)
 def critical_count(self): return sum(len(a.criticals) for a in self.answers)
 def summarize(self): self.summary={"query_total":len(self.queries),"answer_total":len(self.answers),"critical_count":self.critical_count(),**(self.store.summary if self.store else {})}; return dict(self.summary)
 def to_dict(self): return {"report_id":self.report_id,"store":self.store.to_dict() if self.store else None,"queries":[q.to_dict() for q in self.queries],"answers":[a.to_dict() for a in self.answers],"status":self.status.value,"created_at":self.created_at,"summary":dict(self.summary),"metadata":dict(self.metadata),"advisory":self.advisory}
 @classmethod
 def from_dict(cls,d): return cls(str(d["report_id"]),ProcessMemoryStore.from_dict(d["store"]) if d.get("store") else None,[ProcessMemoryQuery.from_dict(x) for x in d.get("queries",[])],[ProcessMemoryAnswer.from_dict(x) for x in d.get("answers",[])],ProcessMemoryReportStatus(str(d.get("status","EMPTY"))),str(d.get("created_at") or _now()),dict(d.get("summary",{})),dict(d.get("metadata",{"advisory_only":True})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(cls,t): return cls.from_dict(json.loads(t))
 def write_json(self,p): _w(p,self.to_json()+"\n")
 @classmethod
 def read_json(cls,p): return cls.from_json(Path(p).read_text())
 def write_jsonl(self,p): _w(p,self.to_json()+"\n")
 @classmethod
 def read_jsonl(cls,p): return [cls.from_json(x) for x in Path(p).read_text().splitlines() if x.strip()]

def make_process_context_id(*x): return content_id("process-context",x)
def make_process_elimination_id(*x): return content_id("process-elimination",x)
def make_process_transition_id(*x): return content_id("process-transition",x)
def make_process_episode_id(*x): return content_id("process-episode",x)
def make_process_memory_query_id(*x): return content_id("process-query",x)
def make_process_memory_answer_id(*x): return content_id("process-answer",x)
def make_process_memory_store_id(*x): return content_id("process-store",x)
def make_process_memory_report_id(*x): return content_id("process-report",x)
def _ctx(kind,role,obj=None,**kw): return ProcessContextItem(make_process_context_id(kind.value,role.value,obj,kw),kind,role,obj,**kw)
def _tr(kind,frm=None,to=None,**kw): return ProcessTransition(make_process_transition_id(kind.value,frm,to,kw),kind,frm,to,**kw)
def _elim(kind,obj=None,**kw): return ProcessElimination(make_process_elimination_id(kind.value,obj,kw),kind,obj,**kw)
def process_episode_from_verification_episode(t):
 ctx=[_ctx(ProcessContextKind.CLAIM,ProcessContextRole.INCLUDED,t.input.claim_id,claim_id=t.input.claim_id)]+[_ctx(ProcessContextKind.ROUTE,ProcessContextRole.USED,d.decision_id,route=d.route_kind.value,label=d.reason) for d in t.route_decisions]
 trs=[_tr(ProcessTransitionKind.CURRICULUM_TO_EPISODE,None,t.episode_id,claim_id=t.input.claim_id)]+[_tr(ProcessTransitionKind.EPISODE_TO_VERIFIER,t.episode_id,d.decision_id,route=d.route_kind.value) for d in t.route_decisions]
 st=ProcessEpisodeStatus["TERMINAL_"+t.terminal_form.value] if t.terminal_form and t.is_terminal() else ProcessEpisodeStatus.ADVISORY_ONLY
 return ProcessEpisodeRecord(t.episode_id,st,t.input.claim_id,t.route_decisions[0].route_kind.value if t.route_decisions else None,t.terminal_form,t.certificate_id,t.verifier_boundary_crossed,contexts=ctx,transitions=trs,agent_ids=tuple(e.agent_id for e in t.agent_experiences))
def process_episode_from_alchemical_trace(t):
 ctx=[_ctx(ProcessContextKind.ALCHEMICAL_PHASE,ProcessContextRole.USED,f"{t.trace_id}:{i}",label=s.phase.value) for i,s in enumerate(t.steps)]
 trs=[_tr(ProcessTransitionKind.ALCHEMY_PHASE_STEP,ctx[i-1].context_id if i else None,c.context_id) for i,c in enumerate(ctx)]
 return ProcessEpisodeRecord(make_process_episode_id("alchemy",t.trace_id),ProcessEpisodeStatus.TERMINAL_VERIFIED_PROOF if t.is_promoted() and t.terminal_form==TerminalForm.VERIFIED_PROOF else ProcessEpisodeStatus.ADVISORY_ONLY,t.claim_id,None,t.terminal_form,t.promoted_certificate_id,t.is_promoted(),contexts=ctx,transitions=trs)
def process_episode_from_curriculum(c): return ProcessEpisodeRecord(make_process_episode_id("curriculum",c.curriculum_id),ProcessEpisodeStatus.ADVISORY_ONLY,c.target_claim_id,contexts=[_ctx(ProcessContextKind.CURRICULUM,ProcessContextRole.INCLUDED,s.stage_id,label=s.kind.value) for s in c.stages],transitions=[_tr(ProcessTransitionKind.ACTION_TO_CURRICULUM,c.curriculum_id,s.stage_id) for s in c.stages])
def process_episode_from_lawbook_query_report(r):
 ctx=[_ctx(ProcessContextKind.LAWBOOK_ENTRY,ProcessContextRole.USED,a.answer_id,certificate_id=a.certificate_id,terminal_form=a.terminal_form,verifier_boundary_crossed=a.verifier_boundary_crossed) for a in r.answers]
 truth=next((a for a in r.answers if getattr(a,"is_terminal_answer",lambda:False)()),None)
 elims=[_elim(ProcessEliminationKind.AMBIGUOUS_MEMORY,a.answer_id,reason=a.status.value) for a in r.answers if a.status.value in {"AMBIGUOUS","FOUND_CANDIDATE_ONLY","NOT_FOUND"}]
 status=_status_for_boundary(truth.terminal_form) if truth else ProcessEpisodeStatus.ADVISORY_ONLY
 return ProcessEpisodeRecord(make_process_episode_id("lawbook-query",r.report_id),status,terminal_form=truth.terminal_form if truth else None,certificate_id=truth.certificate_id if truth else None,verifier_boundary_crossed=bool(truth),contexts=ctx,eliminations=elims,lawbook_entry_ids=tuple(x for a in r.answers for x in a.matched_entry_ids),transitions=[_tr(ProcessTransitionKind.LAWBOOK_QUERY,r.report_id,a.answer_id) for a in r.answers])
def process_episode_from_lawbook_store(s):
 ctx=[_ctx(ProcessContextKind.LAWBOOK_ENTRY,ProcessContextRole.ACCEPTED_BY_REVIEW if e.is_accepted() else ProcessContextRole.CANDIDATE_ONLY,e.entry_id,claim_id=e.claim_id,certificate_id=e.certificate_id,terminal_form=e.terminal_form,verifier_boundary_crossed=e.verifier_boundary_crossed,accepted_public_memory=e.is_accepted()) for e in s.entries]
 return ProcessEpisodeRecord(make_process_episode_id("lawbook-store",s.store_id),ProcessEpisodeStatus.ADVISORY_ONLY,contexts=ctx,lawbook_entry_ids=tuple(e.entry_id for e in s.entries))
def process_episode_from_projection_candidates(cs):
 return ProcessEpisodeRecord(make_process_episode_id("projection",[c.candidate_id for c in cs]),ProcessEpisodeStatus.ADVISORY_ONLY,contexts=[_ctx(ProcessContextKind.PROJECTION,ProcessContextRole.GENERATED,c.candidate_id,label=getattr(c.kind,"value",str(getattr(c,"kind","projection")))) for c in cs],transitions=[_tr(ProcessTransitionKind.PROJECTION_TO_RESIDUAL,c.candidate_id,None) for c in cs],projection_candidate_ids=tuple(c.candidate_id for c in cs))
def process_episode_from_proof_digestion_trace(t):
 ctx=[_ctx(ProcessContextKind.DIGESTION,ProcessContextRole.USED,t.trace_id,certificate_id=t.certificate_id,terminal_form=t.terminal_form,verifier_boundary_crossed=t.verifier_boundary_crossed)]
 ctx += [_ctx(ProcessContextKind.DIGESTION,ProcessContextRole.GENERATED,getattr(x,"schema_id",getattr(x,"candidate_id",None))) for x in list(getattr(t,"reusable_schemas",[]))+list(getattr(t,"lawbook_assimilation_candidates",[]))]
 return ProcessEpisodeRecord(make_process_episode_id("digestion",t.trace_id),_status_for_boundary(t.terminal_form) if getattr(t,"is_truth_terminal",lambda:False)() else ProcessEpisodeStatus.ADVISORY_ONLY,terminal_form=t.terminal_form,certificate_id=t.certificate_id,verifier_boundary_crossed=t.verifier_boundary_crossed,contexts=ctx,transitions=[_tr(ProcessTransitionKind.PROOF_TO_DIGESTION,t.certificate_id,t.trace_id)])
def process_episode_from_verifier_feedback(f):
 ctx=[_ctx(ProcessContextKind.FEEDBACK,ProcessContextRole.USED,f.feedback_id,label=f.status.value)]
 flaws=getattr(f,"flaws",[])
 elims=[_elim(ProcessEliminationKind.NEEDS_REPAIR,getattr(x,"flaw_id",None),reason=getattr(x,"message",None)) for x in flaws if str(getattr(getattr(x,"severity",None),"value",getattr(x,"severity",""))).upper() in {"CRITICAL","STRUCTURAL"}]
 return ProcessEpisodeRecord(make_process_episode_id("feedback",f.feedback_id),ProcessEpisodeStatus.RESIDUAL if elims else ProcessEpisodeStatus.ADVISORY_ONLY,contexts=ctx,eliminations=elims,transitions=[_tr(ProcessTransitionKind.VERIFIER_TO_FEEDBACK,None,f.feedback_id)])
def process_episode_from_repair_loop(t):
 plans=getattr(t,"repair_plans",[])
 return ProcessEpisodeRecord(make_process_episode_id("repair",t.trace_id),ProcessEpisodeStatus.ADVISORY_ONLY,contexts=[_ctx(ProcessContextKind.REPAIR,ProcessContextRole.USED,getattr(p,"plan_id",None),label=getattr(getattr(p,"action_kind",None),"value",None)) for p in plans],eliminations=[_elim(ProcessEliminationKind.NEEDS_REPAIR,getattr(p,"plan_id",None),reason=getattr(getattr(p,"action_kind",None),"value",None)) for p in plans],transitions=[_tr(ProcessTransitionKind.FEEDBACK_TO_REPAIR,getattr(t,"feedback_id",None),getattr(p,"plan_id",None)) for p in plans])
def process_episode_from_discovery_value_report(r):
 scores=getattr(r,"scores",[])
 return ProcessEpisodeRecord(make_process_episode_id("value",r.report_id),ProcessEpisodeStatus.ADVISORY_ONLY,contexts=[_ctx(ProcessContextKind.DISCOVERY_VALUE,ProcessContextRole.USED,s.score_id,label=str(getattr(getattr(s,"decision",None),"value",getattr(s,"decision",None)))) for s in scores],eliminations=[_elim(ProcessEliminationKind.LOW_VALUE,s.score_id,reason=str(getattr(getattr(s,"decision",None),"value",getattr(s,"decision",None)))) for s in scores if str(getattr(getattr(s,"decision",None),"value",getattr(s,"decision",None))) in {"DROP","HOLD_IN_CHORA"}],transitions=[_tr(ProcessTransitionKind.VALUE_TO_ROUTE_PRIORITY,s.score_id,None) for s in scores])
def process_episode_from_structural_identity_report(r):
 cs=getattr(r,"merge_candidates",[])
 return ProcessEpisodeRecord(make_process_episode_id("structural",r.report_id),ProcessEpisodeStatus.ADVISORY_ONLY,contexts=[_ctx(ProcessContextKind.STRUCTURAL_IDENTITY,ProcessContextRole.CANDIDATE_ONLY,c.candidate_id,label=c.match_kind.value) for c in cs],eliminations=[_elim(ProcessEliminationKind.DUPLICATE_MEMORY,c.candidate_id,reason=c.decision.value) for c in cs if c.decision.value=="CONFLICT_REVIEW"],transitions=[_tr(ProcessTransitionKind.STRUCTURAL_IDENTITY_TO_REVIEW,c.candidate_id,None) for c in cs])
def process_episode_from_habit_report(r):
 ids=tuple(x.rule_id for x in getattr(r,"rules",[]) if getattr(x,"is_accepted",lambda:False)())
 return ProcessEpisodeRecord(make_process_episode_id("habit",r.report_id),ProcessEpisodeStatus.ADVISORY_ONLY,contexts=[_ctx(ProcessContextKind.HABIT,ProcessContextRole.ACCEPTED_BY_REVIEW if getattr(x,"is_accepted",lambda:False)() else ProcessContextRole.CANDIDATE_ONLY,getattr(x,"rule_id",getattr(x,"candidate_id",None))) for x in list(getattr(r,"candidates",[]))+list(getattr(r,"rules",[]))],transitions=[_tr(ProcessTransitionKind.HABIT_TO_ROUTE_PRIORITY,x,None) for x in ids],habit_rule_ids=ids)
def process_episode_from_reason_report(r):
 ids=tuple(x.reason_id for x in getattr(r,"reason_nodes",[]) if getattr(x,"is_accepted",lambda:False)())
 return ProcessEpisodeRecord(make_process_episode_id("reason",r.report_id),ProcessEpisodeStatus.ADVISORY_ONLY,contexts=[_ctx(ProcessContextKind.REASON,ProcessContextRole.ACCEPTED_BY_REVIEW if getattr(x,"is_accepted",lambda:False)() else ProcessContextRole.CANDIDATE_ONLY,getattr(x,"reason_id",getattr(x,"candidate_id",None))) for x in list(getattr(r,"candidates",[]))+list(getattr(r,"reason_nodes",[]))],transitions=[_tr(ProcessTransitionKind.REASON_TO_EXPLANATION,x,None) for x in ids],reason_node_ids=ids)
def process_episode_from_agent_experience(e):
 ok=getattr(e,"outcome",None) in {AgentExperienceOutcome.VERIFIED_PROOF,AgentExperienceOutcome.FINITE_COUNTERMODEL}
 return ProcessEpisodeRecord(make_process_episode_id("agent",e.experience_id),_status_for_boundary(e.terminal_form) if ok and getattr(e,"certificate_id",None) else ProcessEpisodeStatus.ADVISORY_ONLY,terminal_form=getattr(e,"terminal_form",None),certificate_id=getattr(e,"certificate_id",None),verifier_boundary_crossed=bool(ok and getattr(e,"certificate_id",None)),contexts=[_ctx(ProcessContextKind.AGENT_EXPERIENCE,ProcessContextRole.USED,e.experience_id)],agent_ids=(e.agent_id,))
def process_episode_from_route_telemetry_event(e): return process_episode_from_mapping(e)
def process_episode_from_mapping(d):
 tf=_terminal(d.get("terminal_form")); boundary=bool(d.get("verifier_boundary_crossed",False)); cert=_s(d.get("certificate_id")); killed=bool(d.get("killed",False))
 return ProcessEpisodeRecord(make_process_episode_id("raw",d),_status_for_boundary(tf) if tf and cert and boundary else ProcessEpisodeStatus.FAILED if killed else ProcessEpisodeStatus.ADVISORY_ONLY,_s(d.get("claim_id")),_s(d.get("route") or d.get("route_kind")),tf,cert,boundary,contexts=[_ctx(ProcessContextKind.RAW_EVENT,ProcessContextRole.USED,_s(d.get("event_id") or d.get("object_id")),route=_s(d.get("route") or d.get("route_kind")),claim_id=_s(d.get("claim_id")),metadata=dict(d))],eliminations=[_elim(ProcessEliminationKind.KILLED_ROUTE,_s(d.get("event_id")),route=_s(d.get("route") or d.get("route_kind")),reason=_s(d.get("kill_reason")),claim_id=_s(d.get("claim_id"))) ] if killed else [],cost_units=float(d.get("cost_units",0) or 0),gain_units=float(d.get("gain_units",0) or 0),metadata=dict(d))
def process_episode_from_object(o):
 from mathgraph.discovery_value import DiscoveryValueReport
 from mathgraph.habit_rules import HabitFormationReport
 from mathgraph.lawbook_query import LawbookQueryReport
 from mathgraph.projection import ProjectionCandidate
 from mathgraph.proof_digestion import ProofDigestionTrace
 from mathgraph.reason_compression import ReasonCompressionReport
 from mathgraph.structural_identity import StructuralIdentityReport
 from mathgraph.verification_episode import VerificationEpisodeTrace
 from mathgraph.verifier_feedback import RepairLoopTrace,VerifierFeedback
 if isinstance(o,ProcessEpisodeRecord): return o
 if isinstance(o,VerificationEpisodeTrace): return process_episode_from_verification_episode(o)
 if isinstance(o,AlchemicalTrace): return process_episode_from_alchemical_trace(o)
 if isinstance(o,ContinuationCurriculum): return process_episode_from_curriculum(o)
 if isinstance(o,LawbookQueryReport): return process_episode_from_lawbook_query_report(o)
 if isinstance(o,LawbookStore): return process_episode_from_lawbook_store(o)
 if isinstance(o,ProjectionCandidate): return process_episode_from_projection_candidates([o])
 if isinstance(o,ProofDigestionTrace): return process_episode_from_proof_digestion_trace(o)
 if isinstance(o,VerifierFeedback): return process_episode_from_verifier_feedback(o)
 if isinstance(o,RepairLoopTrace): return process_episode_from_repair_loop(o)
 if isinstance(o,DiscoveryValueReport): return process_episode_from_discovery_value_report(o)
 if isinstance(o,StructuralIdentityReport): return process_episode_from_structural_identity_report(o)
 if isinstance(o,HabitFormationReport): return process_episode_from_habit_report(o)
 if isinstance(o,ReasonCompressionReport): return process_episode_from_reason_report(o)
 if isinstance(o,AgentExperience): return process_episode_from_agent_experience(o)
 if isinstance(o,Mapping): return process_episode_from_mapping(o)
 return None
def build_process_memory_store(objects=(),episodes=()):
 xs=[e for e in list(episodes)+[process_episode_from_object(o) for o in objects] if e is not None]; ded={e.episode_id:e for e in xs}; s=ProcessMemoryStore(make_process_memory_store_id(sorted(ded)),list(ded.values())); s.summarize(); return s
def make_process_query_by_episode(x): return ProcessMemoryQuery(make_process_memory_query_id("episode",x),ProcessMemoryQueryKind.EPISODE,episode_id=x)
def make_process_query_by_claim(x): return ProcessMemoryQuery(make_process_memory_query_id("claim",x),ProcessMemoryQueryKind.CLAIM,claim_id=x)
def make_process_query_by_route(x): return ProcessMemoryQuery(make_process_memory_query_id("route",x),ProcessMemoryQueryKind.ROUTE,route=x)
def make_process_query_by_certificate(x): return ProcessMemoryQuery(make_process_memory_query_id("certificate",x),ProcessMemoryQueryKind.CERTIFICATE,certificate_id=x)
def make_process_query_by_lawbook_entry(x): return ProcessMemoryQuery(make_process_memory_query_id("lawbook",x),ProcessMemoryQueryKind.LAWBOOK_ENTRY,lawbook_entry_id=x)
def make_process_query_by_habit_rule(x): return ProcessMemoryQuery(make_process_memory_query_id("habit",x),ProcessMemoryQueryKind.HABIT,habit_rule_id=x)
def make_process_query_by_reason_node(x): return ProcessMemoryQuery(make_process_memory_query_id("reason",x),ProcessMemoryQueryKind.REASON,reason_node_id=x)
def make_process_query_by_agent(x): return ProcessMemoryQuery(make_process_memory_query_id("agent",x),ProcessMemoryQueryKind.AGENT,agent_id=x)
def make_process_trust_summary_query(): return ProcessMemoryQuery(make_process_memory_query_id("trust"),ProcessMemoryQueryKind.TRUST_SUMMARY)
def make_process_text_query(x): return ProcessMemoryQuery(make_process_memory_query_id("text",x),ProcessMemoryQueryKind.TEXT,text=x)
def query_process_memory_store(s,q):
 if q.kind==ProcessMemoryQueryKind.TRUST_SUMMARY: return ProcessMemoryAnswer(make_process_memory_answer_id(q.query_id,"trust"),q.query_id,ProcessMemoryAnswerStatus.FOUND_ADVISORY,evidence={"summary":s.summarize()},explanation="This is advisory process-memory summary, not a new truth boundary.")
 if q.kind==ProcessMemoryQueryKind.EPISODE and q.episode_id: eps=s.find_by_episode_id(q.episode_id)
 elif q.kind==ProcessMemoryQueryKind.CLAIM and q.claim_id: eps=s.find_by_claim_id(q.claim_id)
 elif q.kind==ProcessMemoryQueryKind.ROUTE and q.route: eps=s.find_by_route(q.route)
 elif q.kind==ProcessMemoryQueryKind.CERTIFICATE and q.certificate_id: eps=s.find_by_certificate_id(q.certificate_id)
 elif q.kind==ProcessMemoryQueryKind.LAWBOOK_ENTRY and q.lawbook_entry_id: eps=s.find_by_lawbook_entry_id(q.lawbook_entry_id)
 elif q.kind==ProcessMemoryQueryKind.HABIT and q.habit_rule_id: eps=s.find_by_habit_rule_id(q.habit_rule_id)
 elif q.kind==ProcessMemoryQueryKind.REASON and q.reason_node_id: eps=s.find_by_reason_node_id(q.reason_node_id)
 elif q.kind==ProcessMemoryQueryKind.AGENT and q.agent_id: eps=s.find_by_agent_id(q.agent_id)
 elif q.kind==ProcessMemoryQueryKind.TEXT and q.text: eps=[e for e in s.episodes if q.text.lower() in _j(e.to_dict()).lower()]
 elif q.kind==ProcessMemoryQueryKind.STATUS and q.text: eps=[e for e in s.episodes if e.status.value==q.text]
 elif q.kind==ProcessMemoryQueryKind.ELIMINATION and (q.text or q.object_id): eps=[e for e in s.episodes if any((q.text and q.text.lower() in _j(x.to_dict()).lower()) or (q.object_id and x.object_id==q.object_id) for x in e.eliminations)]
 else: return ProcessMemoryAnswer(make_process_memory_answer_id(q.query_id,"invalid"),q.query_id,ProcessMemoryAnswerStatus.INVALID_QUERY,explanation="This process-memory query has no usable lookup key.")
 if not eps: return ProcessMemoryAnswer(make_process_memory_answer_id(q.query_id,"none"),q.query_id,ProcessMemoryAnswerStatus.NOT_FOUND,explanation="No matching process memory was found.")
 truth=next((e for e in eps if e.has_truth_boundary()),None); elims=[x for e in eps for x in e.eliminations]
 status=ProcessMemoryAnswerStatus.FOUND_TERMINAL_BOUNDARY if truth else ProcessMemoryAnswerStatus.FOUND_ELIMINATION if elims else ProcessMemoryAnswerStatus.FOUND_RESIDUAL if any(e.status==ProcessEpisodeStatus.RESIDUAL for e in eps) else ProcessMemoryAnswerStatus.FOUND_ADVISORY
 ans=ProcessMemoryAnswer(make_process_memory_answer_id(q.query_id,[e.episode_id for e in eps]),q.query_id,status,tuple(e.episode_id for e in eps),tuple(x.context_id for e in eps for x in e.contexts),tuple(x.elimination_id for x in elims),tuple(x.transition_id for e in eps for x in e.transitions),truth.terminal_form if truth else None,truth.certificate_id if truth else None,bool(truth),evidence={"episode_count":len(eps)})
 ans.explanation=explain_process_memory_answer(ans); return ans
def query_process_memory_store_many(s,qs):
 ans=[query_process_memory_store(s,q) for q in qs]; r=ProcessMemoryReport(make_process_memory_report_id(s.store_id,[q.query_id for q in qs]),s,list(qs),ans,ProcessMemoryReportStatus.ANSWERED if ans else ProcessMemoryReportStatus.RECORDED); r.summarize(); return r
def explain_process_memory_answer(a):
 if a.has_truth_boundary(): return "This answer replays inherited terminal boundary evidence already backed by a certificate and verifier boundary."
 if a.status==ProcessMemoryAnswerStatus.FOUND_ELIMINATION: return "This answer records elimination history. Eliminations explain failed routes; they do not prove claims."
 if a.status==ProcessMemoryAnswerStatus.FOUND_RESIDUAL: return "This answer records residual process history, not terminal truth."
 if a.status==ProcessMemoryAnswerStatus.NOT_FOUND: return "No matching process memory was found."
 return "This answer is advisory process memory describing how work unfolded, not a truth boundary."
def trace_episode_lineage(s,episode_id,*,max_depth=4):
 by={e.episode_id:e for e in s.episodes}; out=[]; seen=set(); frontier=[episode_id]
 for _ in range(max_depth+1):
  nxt=[]
  for eid in frontier:
   if eid in seen or eid not in by: continue
   seen.add(eid); e=by[eid]; out.append(e)
   nxt += [x for t in e.transitions for x in (t.from_id,t.to_id) if x in by]
   nxt += [c.object_id for c in e.contexts if c.object_id in by]
  frontier=nxt
 return out
def summarize_eliminations(s):
 return {"by_kind":dict(Counter(x.kind.value for e in s.episodes for x in e.eliminations)),"by_route":dict(Counter(x.route for e in s.episodes for x in e.eliminations if x.route)),"by_claim":dict(Counter(x.claim_id for e in s.episodes for x in e.eliminations if x.claim_id)),"by_killed_by":dict(Counter(x.killed_by for e in s.episodes for x in e.eliminations if x.killed_by))}
def summarize_route_processes(s):
 out=defaultdict(lambda:{"episode_count":0,"terminal_count":0,"advisory_count":0,"elimination_count":0,"total_cost":0.0,"total_gain":0.0})
 for e in s.episodes:
  if not e.route: continue
  d=out[e.route]; d["episode_count"]+=1; d["terminal_count"]+=int(e.has_truth_boundary()); d["advisory_count"]+=int(not e.has_truth_boundary()); d["elimination_count"]+=len(e.eliminations); d["total_cost"]+=e.cost_units; d["total_gain"]+=e.total_gain()
 for d in out.values(): d["avg_gain"]=d["total_gain"]/d["episode_count"] if d["episode_count"] else 0
 return dict(out)
def process_report_to_lawbook_candidates(r): return [LawbookEntry(make_lawbook_entry_id("process",r.report_id,a.answer_id),LawbookEntryKind.REUSABLE_SCHEMA_ENTRY,LawbookEntryStatus.CANDIDATE,metadata={"process_memory_not_truth":True,"process_report_id":r.report_id,"process_advisory_only":True},advisory=True) for a in r.answers]
def process_report_to_continuation_outputs(r): return [ContinuationActionOutput(make_continuation_output_id({"process":a.answer_id}),"process_memory",ContinuationOutputKind.TASK,ContinuationActionStatus.ADVISORY_ONLY,task_payload={"task":"reuse known process" if a.has_truth_boundary() else "avoid or repair route" if a.status==ProcessMemoryAnswerStatus.FOUND_ELIMINATION else "investigate process gap","answer_id":a.answer_id},advisory=True) for a in r.answers]
def process_report_to_curriculum(r):
 stages=[CurriculumStage(make_curriculum_stage_id("process",a.answer_id),CurriculumStageKind.REPAIR_TASK if a.status==ProcessMemoryAnswerStatus.FOUND_ELIMINATION else CurriculumStageKind.DIGESTION_TASK if a.has_truth_boundary() else CurriculumStageKind.RESIDUAL_REVIEW,CurriculumStageStatus.ADVISORY_ONLY,title="Reuse process memory",metadata={"answer_id":a.answer_id},advisory=True) for a in r.answers]
 return ContinuationCurriculum(make_curriculum_id("process",r.report_id),strategy=CurriculumBuildStrategy.MIXED,stages=stages,status=CurriculumTraceStatus.TASKS_EMITTED if stages else CurriculumTraceStatus.EMPTY,metadata={"advisory_only":True})
def process_report_to_discovery_value_scores(r):
 out=[]
 for a in r.answers:
  sig=DiscoveryValueSignal(content_id("process-signal",a.answer_id),DiscoveryValueSignalKind.REUSE_VALUE,1.0 if a.has_truth_boundary() else 0.25,reason="process memory",source_object_kind=DiscoveryValueObjectKind.RAW_TASK); score=DiscoveryValueScore(content_id("process-score",a.answer_id),a.answer_id,DiscoveryValueObjectKind.RAW_TASK,signals=[sig],metadata={"process_advisory_only":True}); score.recompute(); out.append(score)
 return out
def process_report_to_habit_observations(r): return [HabitObservation(content_id("process-habit",a.answer_id),HabitObservationKind.RAW_EVENT,route="process_memory",outcome=HabitOutcome.VERIFIED_PROOF if a.has_truth_boundary() and a.terminal_form==TerminalForm.VERIFIED_PROOF else HabitOutcome.ADVISORY_ONLY,object_id=a.answer_id,certificate_id=a.certificate_id,terminal_form=a.terminal_form,verifier_boundary_crossed=a.verifier_boundary_crossed,metadata={"process_advisory_only":True}) for a in r.answers]
def process_report_to_reason_observations(r): return [ReasonObservation(make_reason_observation_id("process",a.answer_id),ReasonObservationKind.RAW_EVENT,a.answer_id,"process_memory",*extract_atoms_from_mapping(a.to_dict()),terminal_form=a.terminal_form,certificate_id=a.certificate_id,verifier_boundary_crossed=a.verifier_boundary_crossed,metadata={"process_advisory_only":True}) for a in r.answers]
def process_report_to_structural_identity_objects(r): return [{"answer_id":a.answer_id,"status":a.status.value,"episodes":list(a.matched_episode_ids),"process_advisory_only":True} for a in r.answers]
def process_report_to_alchemical_trace(r):
 t=AlchemicalTrace(make_alchemical_trace_id("process",r.report_id))
 for p in (AlchemicalPhase.RAW_MATTER,AlchemicalPhase.SOLUTION,AlchemicalPhase.DISTILLATION,AlchemicalPhase.COAGULATION): t.add_step(phase=p,status=AlchemicalStatus.ADVISORY_ONLY)
 return t
def process_report_to_agent_experiences(r,agent_id=None):
 return [AgentExperience(content_id("process-exp",a.answer_id),agent_id or "process-memory",None,None,"process_memory",None,AgentExperienceOutcome.VERIFIED_PROOF if a.has_truth_boundary() and a.terminal_form==TerminalForm.VERIFIED_PROOF else AgentExperienceOutcome.FINITE_COUNTERMODEL if a.has_truth_boundary() and a.terminal_form==TerminalForm.FINITE_COUNTERMODEL else AgentExperienceOutcome.ADVISORY_ONLY,certificate_id=a.certificate_id,terminal_form=a.terminal_form,metadata={"process_advisory_only":True}) for a in r.answers]
def process_report_to_route_telemetry_events(r): return [{"event_id":content_id("process-telemetry",a.answer_id),"route_kind":"process_memory","outcome":a.status.value,"process_advisory_only":True} for a in r.answers]
def audit_process_context_item(i): return [_f("CRITICAL","PROCESS_CONTEXT_NON_ADVISORY","process context non-advisory",i.context_id)] if not i.advisory else []
def audit_process_episode_record(e):
 fs=[]
 if not e.advisory: fs.append(_f("CRITICAL","PROCESS_RECORD_NON_ADVISORY","process record non-advisory",e.episode_id))
 if e.terminal_form in {TerminalForm.VERIFIED_PROOF,TerminalForm.FINITE_COUNTERMODEL} and not e.has_truth_boundary(): fs.append(_f("CRITICAL","PROCESS_TERMINAL_WITHOUT_BOUNDARY","terminal process record lacks inherited boundary",e.episode_id))
 if not e.contexts: fs.append(_f("WARNING","PROCESS_NO_CONTEXT","episode has no contexts",e.episode_id))
 if not e.transitions: fs.append(_f("WARNING","PROCESS_NO_TRANSITIONS","episode has no transitions",e.episode_id))
 if e.status in {ProcessEpisodeStatus.FAILED,ProcessEpisodeStatus.RESIDUAL} and not e.eliminations: fs.append(_f("WARNING","PROCESS_NO_ELIMINATIONS","failed/residual episode lacks eliminations",e.episode_id))
 return fs
def audit_process_memory_answer(a):
 fs=[]
 if a.terminal_form in {TerminalForm.VERIFIED_PROOF,TerminalForm.FINITE_COUNTERMODEL} and not a.has_truth_boundary(): fs.append(_f("CRITICAL","PROCESS_ANSWER_WITHOUT_BOUNDARY","process answer terminal lacks boundary",a.answer_id))
 if not a.explanation: fs.append(_f("WARNING","PROCESS_ANSWER_NO_EXPLANATION","process answer lacks explanation",a.answer_id))
 return fs
def audit_process_memory_report(r):
 return [x for e in (r.store.episodes if r.store else []) for x in audit_process_episode_record(e)]+[x for a in r.answers for x in audit_process_memory_answer(a)]
def _status_for_boundary(tf):
 return ProcessEpisodeStatus.TERMINAL_VERIFIED_PROOF if tf==TerminalForm.VERIFIED_PROOF else ProcessEpisodeStatus.TERMINAL_FINITE_COUNTERMODEL if tf==TerminalForm.FINITE_COUNTERMODEL else ProcessEpisodeStatus.TERMINAL_NAMED_OBSTRUCTION if tf==TerminalForm.NAMED_OBSTRUCTION else ProcessEpisodeStatus.ADVISORY_ONLY
def _terminal(x):
 try:return TerminalForm(str(x)) if x else None
 except ValueError:return None
def _s(x): return None if x is None else str(x)
def _now(): return datetime.now(timezone.utc).isoformat()
def _j(x): return json.dumps(x,sort_keys=True,separators=(",",":"))
def _w(p,t): path=Path(p); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(t,encoding="utf-8")
def _f(sev,code,msg,obj): return {"severity":sev,"code":code,"message":msg,"object_id":obj}
