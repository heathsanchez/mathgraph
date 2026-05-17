"""Advisory finite-resource discovery agents above the verification kernel."""
from __future__ import annotations
import json
from collections import Counter,defaultdict
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
from mathgraph.semantic_intake import SemanticSource,SemanticSourceKind
from mathgraph.structural_analogy import AnalogySource,AnalogySourceKind,analogy_source_from_mapping
from mathgraph.structure_registry import ProjectionCompatibility,StructureObjectKind,TypedProjectionCandidate,TypedProjectionStatus,make_typed_projection_candidate_id,structure_descriptor_from_mapping
from mathgraph.verifier_feedback import FlawSeverity,RepairLoopTrace,VerifierFeedback,VerifierFeedbackStatus,make_verifier_feedback_id
def _enum(n,v): return Enum(n,{x:x for x in v.split()},type=str)
ExistentialAgentStatus=_enum("ExistentialAgentStatus","BORN ACTIVE WOUNDED EXHAUSTED RETIRED DEAD ARCHIVED UNKNOWN")
AgentMortalityMode=_enum("AgentMortalityMode","MORTAL RETIRABLE ARCHIVABLE SUMMARY_ONLY_CONTINUATION IMMORTAL_DAEMON_ONLY UNKNOWN")
PrivateStatePolicy=_enum("PrivateStatePolicy","PRESERVE_PUBLIC_ONLY SUMMARY_ONLY SEALED BURNED LINEAGE_SEED_ONLY UNKNOWN")
AgentResourceKind=_enum("AgentResourceKind","COMPUTE_BUDGET VERIFICATION_BUDGET MEMORY_BUDGET ROUTE_ATTEMPT_BUDGET REPUTATION SPAWN_CREDIT LAWBOOK_CREDIT RISK_LIMIT UNKNOWN")
AgentWoundType=_enum("AgentWoundType","ROUTE_BURN BUDGET_SCAR MEMORY_SEAL TASTE_DISTORTION TRUST_DAMAGE LINEAGE_DAMAGE PHASE_BLINDNESS RISK_AVERSION_SPIKE OVERCONFIDENCE_CHECK UNKNOWN")
AgentWoundSeverity=_enum("AgentWoundSeverity","MINOR MODERATE SEVERE FATAL UNKNOWN")
AgentValueDimension=_enum("AgentValueDimension","CERTIFICATE_HUNGER OBSTRUCTION_RESPECT CAUTION NOVELTY_SEEKING ELEGANCE_BIAS COMPRESSION_DRIVE RISK_TOLERANCE PROJECTION_PREFERENCE VERIFIER_REVERENCE AMBIGUITY_TOLERANCE COST_DISCIPLINE REPAIR_PATIENCE UNKNOWN")
HeldInChoraReason=_enum("HeldInChoraReason","TOO_EXPENSIVE_NOW NEEDS_BETTER_REPRESENTATION ANALOGY_SOURCE WAITING_FOR_CONSTRUCTOR AMBIGUOUS_BUT_FERTILE UNSAFE_TO_PROMOTE NOT_WORTH_VERIFIER_COST NEEDS_HUMAN_REVIEW NEEDS_FORMALIZATION UNKNOWN")
AgentInheritanceMode=_enum("AgentInheritanceMode","NONE SUMMARY_ONLY LINEAGE_SEED APPRENTICE DAEMON_ONLY CLONE_FORBIDDEN UNKNOWN")
AgentDaemonKind=_enum("AgentDaemonKind","ROUTE_POLICY CONSTRUCTOR_HEURISTIC DIGESTION_HEURISTIC REPAIR_HEURISTIC PROJECTION_HEURISTIC SCHEDULING_HEURISTIC EXPLANATION_TEMPLATE UNKNOWN")
AgentEcologyEventKind=_enum("AgentEcologyEventKind","BIRTH ACTIVATION EXPERIENCE_RECORDED RESOURCE_SPENT RESOURCE_GAINED SCAR_RECORDED WOUND_ACQUIRED VALUE_DRIFT NARRATIVE_REVISION HELD_IN_CHORA ROUTE_PRIORITY_ADJUSTED DESCENDANT_SPAWNED DAEMONIZED RETIRED DIED ARCHIVED MUTATION_BLOCKED RESURRECTION_BLOCKED TRUTH_BOUNDARY_BLOCKED UNKNOWN")
AgentEcologyReportStatus=_enum("AgentEcologyReportStatus","EMPTY AGENTS_RECORDED EXPERIENCES_RECORDED RESOURCES_UPDATED WOUNDS_RECORDED VALUES_UPDATED NARRATIVES_UPDATED CHORA_RECORDS_CREATED LINEAGE_RECORDED DAEMONS_CREATED EVENTS_RECORDED ROUTE_PRESSURE_EMITTED HAS_WARNINGS HAS_CRITICALS ADVISORY_ONLY")
def _serial(cls,enums=()):
 def td(self):
  d=dict(self.__dict__)
  for k in enums:
   if isinstance(d.get(k),Enum): d[k]=d[k].value
  for k,v in list(d.items()):
   if isinstance(v,tuple): d[k]=list(v)
   elif hasattr(v,"to_dict"): d[k]=v.to_dict()
  return d
 @classmethod
 def fd(c,d):
  vals=[]
  for f in c.__dataclass_fields__.values():
   v=d[f.name] if f.name in d else f.default if f.default is not MISSING else f.default_factory() if f.default_factory is not MISSING else None
   if f.name in enums and v is not None:
    typ=globals()[str(f.type).split("|")[0]] if not isinstance(f.type,type) else f.type; v=typ(str(v))
   if getattr(f.type,"__origin__",None) is tuple and v is not None: v=tuple(v)
   vals.append(v)
  return c(*vals)
 cls.to_dict=td; cls.from_dict=fd; cls.to_json=lambda self:_j(self.to_dict()); cls.from_json=classmethod(lambda c,t:c.from_dict(json.loads(t))); return cls
@dataclass
class AgentMortalityPolicy:
 policy_id:str; mode:AgentMortalityMode=AgentMortalityMode.MORTAL; reversible:bool=False; resurrection_allowed:bool=False; clone_forbidden:bool=True; private_state_policy:PrivateStatePolicy=PrivateStatePolicy.SUMMARY_ONLY; allow_retirement:bool=True; allow_archival:bool=True; allow_daemonization:bool=True; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def permits_resurrection(self): return self.resurrection_allowed
 def permits_exact_clone(self): return not self.clone_forbidden
@dataclass
class AgentResourceAccount:
 account_id:str; agent_id:str; balances:dict[str,float]=field(default_factory=dict); spent:dict[str,float]=field(default_factory=dict); gained:dict[str,float]=field(default_factory=dict); hard_limits:dict[str,float]=field(default_factory=dict); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def balance(self,k): return float(self.balances.get(_v(k),0.0))
 def spend(self,k,amount):
  k=_v(k); amount=float(amount)
  if amount<0 or (self.hard_limits.get(k,0.0)>=0 and self.balance(k)<amount): return False
  self.balances[k]=self.balance(k)-amount; self.spent[k]=self.spent.get(k,0.0)+amount; return True
 def gain(self,k,amount):
  k=_v(k); amount=float(amount)
  if amount<0: return
  self.balances[k]=self.balance(k)+amount; self.gained[k]=self.gained.get(k,0.0)+amount
 def exhausted(self,k=None):
  ks=[_v(k)] if k else [AgentResourceKind.COMPUTE_BUDGET.value,AgentResourceKind.ROUTE_ATTEMPT_BUDGET.value,AgentResourceKind.VERIFICATION_BUDGET.value]
  return any(self.balance(x)<=0 for x in ks)
@dataclass
class AgentWound:
 wound_id:str; agent_id:str; caused_by_experience_id:str|None=None; wound_type:AgentWoundType=AgentWoundType.UNKNOWN; affected_capacity:str|None=None; severity:AgentWoundSeverity=AgentWoundSeverity.UNKNOWN; reversible:bool=False; repair_condition:str|None=None; locked_routes:tuple[str,...]=(); reduced_budget_fraction:float=0.0; memory_loss_scope:str|None=None; policy_damage:dict[str,float]=field(default_factory=dict); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def is_fatal(self): return self.severity==AgentWoundSeverity.FATAL
@dataclass
class AgentValueProfile:
 value_profile_id:str; agent_id:str; values:dict[str,float]=field(default_factory=dict); drift:dict[str,float]=field(default_factory=dict); last_update_reason:str|None=None; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def get(self,k): return float(self.values.get(_v(k),0.0))
 def update_delta(self,k,d): k=_v(k); self.values[k]=self.get(k)+float(d); self.drift[k]=self.drift.get(k,0.0)+float(d)
 def clamp(self,min_value=0.0,max_value=1.0): self.values={k:max(min_value,min(max_value,v)) for k,v in self.values.items()}
@dataclass
class AgentNarrative:
 narrative_id:str; agent_id:str; current_self_model:str=""; vows:tuple[str,...]=(); taboos:tuple[str,...]=(); defining_scars:tuple[str,...]=(); proudest_certificates:tuple[str,...]=(); shameful_failures:tuple[str,...]=(); preferred_questions:tuple[str,...]=(); avoided_routes:tuple[str,...]=(); lineage_story:str|None=None; current_research_program:str|None=None; last_self_revision:str|None=None; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def revise_from_event(self,e):
  d=e.to_dict() if hasattr(e,"to_dict") else dict(e); self.last_self_revision=str(d.get("event_kind","revision")); return self
@dataclass
class HeldInChoraRecord:
 record_id:str; agent_id:str; idea_id:str|None=None; reason:HeldInChoraReason=HeldInChoraReason.UNKNOWN; text:str|None=None; review_after:str|None=None; advisory_notes:tuple[str,...]=(); source_object_id:str|None=None; source_kind:str|None=None; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
@dataclass
class AgentLineageRecord:
 lineage_id:str; agent_id:str; parent_agent_id:str|None=None; child_agent_id:str|None=None; inheritance_mode:AgentInheritanceMode=AgentInheritanceMode.UNKNOWN; inherited_summary:str|None=None; inherited_values:dict[str,float]=field(default_factory=dict); inherited_taboos:tuple[str,...]=(); inherited_scars:tuple[str,...]=(); clone_forbidden:bool=True; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def is_exact_clone(self): return bool(self.metadata.get("exact_clone_attempt")) or not self.clone_forbidden
@dataclass
class AgentDaemon:
 daemon_id:str; agent_id:str; daemon_kind:AgentDaemonKind=AgentDaemonKind.UNKNOWN; name:str|None=None; description:str|None=None; extracted_from_experience_ids:tuple[str,...]=(); route_adjustments:dict[str,float]=field(default_factory=dict); conditions:tuple[str,...]=(); risk_notes:tuple[str,...]=(); accepted:bool=False; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
@dataclass
class ExistentialAgent:
 agent_id:str; name:str; status:ExistentialAgentStatus=ExistentialAgentStatus.BORN; mortality_policy:AgentMortalityPolicy|None=None; resource_account:AgentResourceAccount|None=None; value_profile:AgentValueProfile|None=None; narrative:AgentNarrative|None=None; parent_agent_id:str|None=None; lineage_ids:tuple[str,...]=(); wound_ids:tuple[str,...]=(); daemon_ids:tuple[str,...]=(); held_in_chora_ids:tuple[str,...]=(); preferred_routes:tuple[str,...]=(); locked_routes:tuple[str,...]=(); active:bool=False; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def is_dead(self): return self.status==ExistentialAgentStatus.DEAD
 def can_act(self): return self.active and self.status in {ExistentialAgentStatus.ACTIVE,ExistentialAgentStatus.WOUNDED}
 def can_receive_budget(self): return not self.is_dead()
 def can_spawn(self): return self.can_mutate() and not self.is_dead() and "lineage_damage" not in self.locked_routes
 def can_mutate(self): return not self.is_dead() and self.status not in {ExistentialAgentStatus.ARCHIVED}
 def activate(self):
  if not self.is_dead(): self.status=ExistentialAgentStatus.ACTIVE; self.active=True
  return self
 def retire(self): self.status=ExistentialAgentStatus.RETIRED; self.active=False; return self
 def kill(self,reason=None): self.status=ExistentialAgentStatus.DEAD; self.active=False; self.metadata["death_reason"]=reason; return self
 def apply_wound(self,w):
  self.wound_ids=tuple(dict.fromkeys((*self.wound_ids,w.wound_id))); self.locked_routes=tuple(dict.fromkeys((*self.locked_routes,*w.locked_routes)))
  if w.reduced_budget_fraction and self.resource_account:
   for k in (AgentResourceKind.COMPUTE_BUDGET.value,AgentResourceKind.ROUTE_ATTEMPT_BUDGET.value): self.resource_account.balances[k]*=max(0.0,1-w.reduced_budget_fraction)
  if w.is_fatal(): self.kill("fatal wound")
  elif not self.is_dead(): self.status=ExistentialAgentStatus.WOUNDED
  return self
@dataclass
class AgentEcologyEvent:
 event_id:str; agent_id:str|None=None; event_kind:AgentEcologyEventKind=AgentEcologyEventKind.UNKNOWN; source_object_id:str|None=None; source_kind:str|None=None; description:str|None=None; resource_delta:dict[str,float]=field(default_factory=dict); value_delta:dict[str,float]=field(default_factory=dict); route_priority_delta:dict[str,float]=field(default_factory=dict); wound_id:str|None=None; daemon_id:str|None=None; lineage_id:str|None=None; held_in_chora_id:str|None=None; terminal_form:str|None=None; certificate_id:str|None=None; verifier_boundary_crossed:bool=False; warnings:tuple[str,...]=(); criticals:tuple[str,...]=(); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def crosses_truth_boundary(self): return False
@dataclass
class AgentEcologyReport:
 report_id:str; agents:list[ExistentialAgent]=field(default_factory=list); mortality_policies:list[AgentMortalityPolicy]=field(default_factory=list); resource_accounts:list[AgentResourceAccount]=field(default_factory=list); wounds:list[AgentWound]=field(default_factory=list); value_profiles:list[AgentValueProfile]=field(default_factory=list); narratives:list[AgentNarrative]=field(default_factory=list); held_in_chora:list[HeldInChoraRecord]=field(default_factory=list); lineages:list[AgentLineageRecord]=field(default_factory=list); daemons:list[AgentDaemon]=field(default_factory=list); events:list[AgentEcologyEvent]=field(default_factory=list); route_priority_adjustments:dict[str,float]=field(default_factory=dict); status:AgentEcologyReportStatus=AgentEcologyReportStatus.EMPTY; created_at:str=field(default_factory=lambda:_now()); summary:dict[str,Any]=field(default_factory=dict); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def agent_count(self): return len(self.agents)
 def wound_count(self): return len(self.wounds)
 def event_count(self): return len(self.events)
 def daemon_count(self): return len(self.daemons)
 def critical_count(self): return len([x for x in audit_agent_ecology_report(self) if x["severity"]=="CRITICAL"])
 def summarize(self):
  vals=[v for p in self.value_profiles for v in p.values.values()]
  self.summary={"agent_total":len(self.agents),"active_agent_total":sum(a.active for a in self.agents),"dead_agent_total":sum(a.is_dead() for a in self.agents),"exhausted_agent_total":sum(a.status==ExistentialAgentStatus.EXHAUSTED for a in self.agents),"wound_total":len(self.wounds),"fatal_wound_total":sum(w.is_fatal() for w in self.wounds),"event_total":len(self.events),"held_in_chora_total":len(self.held_in_chora),"lineage_total":len(self.lineages),"daemon_total":len(self.daemons),"route_adjustment_total":len(self.route_priority_adjustments),"status_counts":dict(Counter(a.status.value for a in self.agents)),"event_kind_counts":dict(Counter(e.event_kind.value for e in self.events)),"wound_type_counts":dict(Counter(w.wound_type.value for w in self.wounds)),"wound_severity_counts":dict(Counter(w.severity.value for w in self.wounds)),"value_average":sum(vals)/len(vals) if vals else 0.0,"resource_totals":dict(_sum_resources(self.resource_accounts)),"critical_count":self.critical_count()}; return self.summary
 def to_dict(self): return {**self.__dict__,"agents":[x.to_dict() for x in self.agents],"mortality_policies":[x.to_dict() for x in self.mortality_policies],"resource_accounts":[x.to_dict() for x in self.resource_accounts],"wounds":[x.to_dict() for x in self.wounds],"value_profiles":[x.to_dict() for x in self.value_profiles],"narratives":[x.to_dict() for x in self.narratives],"held_in_chora":[x.to_dict() for x in self.held_in_chora],"lineages":[x.to_dict() for x in self.lineages],"daemons":[x.to_dict() for x in self.daemons],"events":[x.to_dict() for x in self.events],"status":self.status.value}
 @classmethod
 def from_dict(c,d): return c(str(d["report_id"]),[ExistentialAgent.from_dict(x) for x in d.get("agents",())],[AgentMortalityPolicy.from_dict(x) for x in d.get("mortality_policies",())],[AgentResourceAccount.from_dict(x) for x in d.get("resource_accounts",())],[AgentWound.from_dict(x) for x in d.get("wounds",())],[AgentValueProfile.from_dict(x) for x in d.get("value_profiles",())],[AgentNarrative.from_dict(x) for x in d.get("narratives",())],[HeldInChoraRecord.from_dict(x) for x in d.get("held_in_chora",())],[AgentLineageRecord.from_dict(x) for x in d.get("lineages",())],[AgentDaemon.from_dict(x) for x in d.get("daemons",())],[AgentEcologyEvent.from_dict(x) for x in d.get("events",())],dict(d.get("route_priority_adjustments",{})),AgentEcologyReportStatus(str(d.get("status","EMPTY"))),str(d.get("created_at",_now())),dict(d.get("summary",{})),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
 def write_json(self,p): _w(p,self.to_json())
 @classmethod
 def read_json(c,p): return c.from_json(Path(p).read_text())
 def write_jsonl(self,p): _w(p,self.to_json()+"\n")
 @classmethod
 def read_jsonl(c,p): return [c.from_json(x) for x in Path(p).read_text().splitlines() if x.strip()]
for _c,_e in [(AgentMortalityPolicy,("mode","private_state_policy")),(AgentResourceAccount,()),(AgentWound,("wound_type","severity")),(AgentValueProfile,()),(AgentNarrative,()),(HeldInChoraRecord,("reason",)),(AgentLineageRecord,("inheritance_mode",)),(AgentDaemon,("daemon_kind",)),(ExistentialAgent,("status",)),(AgentEcologyEvent,("event_kind",))]: _serial(_c,_e)
def make_agent_mortality_policy_id(*x): return content_id("agent-mortality",x)
def make_agent_resource_account_id(*x): return content_id("agent-resource",x)
def make_agent_wound_id(*x): return content_id("agent-wound",x)
def make_agent_value_profile_id(*x): return content_id("agent-values",x)
def make_agent_narrative_id(*x): return content_id("agent-narrative",x)
def make_held_in_chora_record_id(*x): return content_id("agent-chora",x)
def make_agent_lineage_record_id(*x): return content_id("agent-lineage",x)
def make_agent_daemon_id(*x): return content_id("agent-daemon",x)
def make_existential_agent_id(*x): return content_id("existential-agent",x)
def make_agent_ecology_event_id(*x): return content_id("agent-event",x)
def make_agent_ecology_report_id(*x): return content_id("agent-report",x)
def default_mortality_policy(agent_id=None): return AgentMortalityPolicy(make_agent_mortality_policy_id(agent_id or "default"))
def default_resource_account(agent_id): return AgentResourceAccount(make_agent_resource_account_id(agent_id),agent_id,{AgentResourceKind.COMPUTE_BUDGET.value:100.0,AgentResourceKind.VERIFICATION_BUDGET.value:20.0,AgentResourceKind.MEMORY_BUDGET.value:100.0,AgentResourceKind.ROUTE_ATTEMPT_BUDGET.value:25.0,AgentResourceKind.REPUTATION.value:0.0,AgentResourceKind.SPAWN_CREDIT.value:0.0,AgentResourceKind.LAWBOOK_CREDIT.value:0.0,AgentResourceKind.RISK_LIMIT.value:1.0},hard_limits={AgentResourceKind.COMPUTE_BUDGET.value:0.0,AgentResourceKind.ROUTE_ATTEMPT_BUDGET.value:0.0,AgentResourceKind.VERIFICATION_BUDGET.value:0.0})
def default_agent_value_profile(agent_id): return AgentValueProfile(make_agent_value_profile_id(agent_id),agent_id,{"CERTIFICATE_HUNGER":.65,"OBSTRUCTION_RESPECT":.55,"CAUTION":.45,"NOVELTY_SEEKING":.55,"ELEGANCE_BIAS":.50,"COMPRESSION_DRIVE":.60,"RISK_TOLERANCE":.50,"PROJECTION_PREFERENCE":.45,"VERIFIER_REVERENCE":.80,"AMBIGUITY_TOLERANCE":.45,"COST_DISCIPLINE":.50,"REPAIR_PATIENCE":.50})
def default_agent_narrative(agent_id,name=None): return AgentNarrative(make_agent_narrative_id(agent_id),agent_id,f"{name or agent_id} explores under verifier discipline.")
def create_existential_agent(name,*,agent_id=None,parent_agent_id=None,preferred_routes=(),metadata=None):
 aid=agent_id or make_existential_agent_id(name,parent_agent_id); return ExistentialAgent(aid,name,mortality_policy=default_mortality_policy(aid),resource_account=default_resource_account(aid),value_profile=default_agent_value_profile(aid),narrative=default_agent_narrative(aid,name),parent_agent_id=parent_agent_id,preferred_routes=tuple(preferred_routes),metadata=dict(metadata or {}))
def agent_ecology_inputs_from_object(o):
 if isinstance(o,Mapping): return [dict(o)]
 if hasattr(o,"to_dict"):
  d=o.to_dict(); oid=next((d.get(k) for k in ("experience_id","trace_id","report_id","task_id","output_id","score_id","episode_id","feedback_id","entry_id","answer_id","candidate_id","descriptor_id","role_id","rule_id","reason_id","response_id","route_result_id","agent_id") if d.get(k)),None)
  if o.__class__.__name__.endswith("Report"):
   rows=[]
   for key in ("events","experiences","answers","tasks","scores","episodes","candidates","typed_projection_candidates","role_objects","rules","reason_nodes","artifacts"):
    for x in getattr(o,key,[]) or []: rows+=agent_ecology_inputs_from_object(x)
   return rows or [{**d,"source_object_id":oid,"source_kind":o.__class__.__name__}]
  return [{**d,"source_object_id":oid,"source_kind":o.__class__.__name__}]
 return []
def agent_ecology_events_from_inputs(inputs,*,agent_id=None):
 out=[]
 for d in inputs:
  aid=agent_id or _s(d.get("agent_id")); oid=_s(d.get("source_object_id")); sk=_s(d.get("source_kind")); cost=float(d.get("cost_units",d.get("cost",0)) or 0); outcome=str(d.get("outcome",d.get("status",""))).upper(); route=_s(d.get("route"))
  if cost>0: out.append(AgentEcologyEvent(make_agent_ecology_event_id(aid,oid,"spent"),aid,AgentEcologyEventKind.RESOURCE_SPENT,oid,sk,resource_delta={"COMPUTE_BUDGET":-cost,"ROUTE_ATTEMPT_BUDGET":-1.0},metadata={"cost_units":cost,"route":route}))
  gain=sum(float(d.get(k,0) or 0) for k in ("compression_gain","projection_gain","derived_amplification"))
  if gain>0: out.append(AgentEcologyEvent(make_agent_ecology_event_id(aid,oid,"gain"),aid,AgentEcologyEventKind.RESOURCE_GAINED,oid,sk,resource_delta={"REPUTATION":gain},route_priority_delta={route:.1} if route else {},metadata={"gain":gain,"route":route}))
  if any(x in outcome for x in ("FAILED","INVALID","CRITICAL")) or d.get("criticals"): out.append(AgentEcologyEvent(make_agent_ecology_event_id(aid,oid,"wound"),aid,AgentEcologyEventKind.WOUND_ACQUIRED,oid,sk,description="failed or critical input",metadata={"route":route,"cost_units":cost,"boundary_drift":bool(d.get("terminal_form") and not d.get("verifier_boundary_crossed"))}))
  proof_like=any(str(d.get(k,"")).lower().find(x)>=0 for k in ("text","description") for x in ("proof","theorem","verified"))
  if proof_like and not d.get("verifier_boundary_crossed"): out.append(AgentEcologyEvent(make_agent_ecology_event_id(aid,oid,"chora"),aid,AgentEcologyEventKind.HELD_IN_CHORA,oid,sk,description="proof-like without boundary",metadata={"proof_like":True,"text":d.get("text") or d.get("description")}))
  if d.get("terminal_form") or d.get("certificate_id") or d.get("verifier_boundary_crossed"):
   out.append(AgentEcologyEvent(make_agent_ecology_event_id(aid,oid,"boundary"),aid,AgentEcologyEventKind.EXPERIENCE_RECORDED,oid,sk,terminal_form=_s(d.get("terminal_form")),certificate_id=_s(d.get("certificate_id")),verifier_boundary_crossed=bool(d.get("verifier_boundary_crossed")),metadata={"inherited_boundary_report":True}))
 return out
def event_from_agent_experience(x): return agent_ecology_events_from_inputs([{**x.to_dict(),"source_object_id":x.experience_id,"source_kind":"AgentExperience"}],agent_id=x.agent_id)
def event_from_alchemical_trace(x): return agent_ecology_events_from_inputs([{**x.to_dict(),"cost_units":x.total_cost(),"compression_gain":x.total_compression_gain(),"source_object_id":x.trace_id,"source_kind":"AlchemicalTrace"}],agent_id=x.agent_id)
def event_from_api_response(x): return agent_ecology_events_from_inputs([{**x.to_dict(),"source_object_id":x.response_id,"source_kind":"ApiResponse"}])
def apply_resource_events(a,events):
 for e in events:
  if e.event_kind==AgentEcologyEventKind.RESOURCE_SPENT:
   for k,v in e.resource_delta.items():
    if v<0: a.spend(k,-v)
  elif e.event_kind==AgentEcologyEventKind.RESOURCE_GAINED:
   for k,v in e.resource_delta.items():
    if v>0: a.gain(k,v)
 return a
def wounds_from_events(events,*,agent_id):
 out=[]; fails=Counter(e.metadata.get("route") for e in events if e.event_kind==AgentEcologyEventKind.WOUND_ACQUIRED)
 for route,n in fails.items():
  if route and n>=2: out.append(AgentWound(make_agent_wound_id(agent_id,"route",route),agent_id,wound_type=AgentWoundType.ROUTE_BURN,severity=AgentWoundSeverity.MODERATE,locked_routes=(route,)))
 for e in events:
  if e.event_kind==AgentEcologyEventKind.RESURRECTION_BLOCKED: out.append(AgentWound(make_agent_wound_id(agent_id,e.event_id,"fatal"),agent_id,wound_type=AgentWoundType.LINEAGE_DAMAGE,severity=AgentWoundSeverity.FATAL))
  elif e.metadata.get("boundary_drift"): out.append(AgentWound(make_agent_wound_id(agent_id,e.event_id,"trust"),agent_id,wound_type=AgentWoundType.TRUST_DAMAGE,severity=AgentWoundSeverity.SEVERE))
  elif e.event_kind==AgentEcologyEventKind.WOUND_ACQUIRED and float(e.metadata.get("cost_units",0))>=20: out.append(AgentWound(make_agent_wound_id(agent_id,e.event_id,"budget"),agent_id,wound_type=AgentWoundType.BUDGET_SCAR,severity=AgentWoundSeverity.MODERATE,reduced_budget_fraction=.1))
 return out
def value_profile_from_events(p,events,wounds=()):
 for e in events:
  if e.metadata.get("boundary_drift"): p.update_delta("VERIFIER_REVERENCE",.1); p.update_delta("CAUTION",.1); p.update_delta("RISK_TOLERANCE",-.1); p.update_delta("NOVELTY_SEEKING",-.05)
  if e.event_kind==AgentEcologyEventKind.RESOURCE_GAINED and e.metadata.get("gain"): p.update_delta("COMPRESSION_DRIVE",.03)
  if e.event_kind==AgentEcologyEventKind.HELD_IN_CHORA: p.update_delta("AMBIGUITY_TOLERANCE",.02); p.update_delta("CAUTION",.02)
  if e.metadata.get("gain") and e.route_priority_delta: p.update_delta("PROJECTION_PREFERENCE",.03)
 for w in wounds:
  if w.wound_type==AgentWoundType.BUDGET_SCAR: p.update_delta("COST_DISCIPLINE",.08); p.update_delta("CAUTION",.05); p.update_delta("RISK_TOLERANCE",-.05)
 p.clamp(); return p
def narrative_from_events(n,events,wounds=(),daemons=()):
 tab=set(n.taboos); vows=set(n.vows)
 if any(e.metadata.get("boundary_drift") for e in events): tab.add("Do not treat advisory output as proof."); vows.add("Route proof-looking text to verification before belief.")
 if any(e.event_kind==AgentEcologyEventKind.HELD_IN_CHORA for e in events): vows.add("Hold ambiguous fertile ideas in Chora until formalized.")
 scars=set(n.defining_scars)|{w.wound_type.value for w in wounds if w.severity in {AgentWoundSeverity.SEVERE,AgentWoundSeverity.FATAL}}
 shame=set(n.shameful_failures)|{e.event_id for e in events if e.metadata.get("boundary_drift")}
 n.taboos=tuple(sorted(tab)); n.vows=tuple(sorted(vows)); n.defining_scars=tuple(sorted(scars)); n.shameful_failures=tuple(sorted(shame)); n.last_self_revision="events applied"; return n
def held_in_chora_from_events(events,*,agent_id): return [HeldInChoraRecord(make_held_in_chora_record_id(agent_id,e.event_id),agent_id,e.event_id,HeldInChoraReason.NEEDS_FORMALIZATION if e.metadata.get("proof_like") else HeldInChoraReason.AMBIGUOUS_BUT_FERTILE,e.metadata.get("text"),source_object_id=e.source_object_id,source_kind=e.source_kind) for e in events if e.event_kind==AgentEcologyEventKind.HELD_IN_CHORA]
def spawn_descendant(parent,*,child_name,inheritance_mode=AgentInheritanceMode.SUMMARY_ONLY,inherited_value_fraction=.25):
 if parent.is_dead() or not parent.can_spawn() or inheritance_mode==AgentInheritanceMode.CLONE_FORBIDDEN:
  lin=AgentLineageRecord(make_agent_lineage_record_id(parent.agent_id,child_name,"blocked"),parent.agent_id,parent.agent_id,None,inheritance_mode,clone_forbidden=True,metadata={"exact_clone_attempt":inheritance_mode==AgentInheritanceMode.CLONE_FORBIDDEN}); ev=AgentEcologyEvent(make_agent_ecology_event_id(parent.agent_id,"spawn-blocked"),parent.agent_id,AgentEcologyEventKind.MUTATION_BLOCKED,lineage_id=lin.lineage_id); return None,lin,ev
 child=create_existential_agent(child_name,parent_agent_id=parent.agent_id); inherited={k:v*inherited_value_fraction for k,v in (parent.value_profile.values if parent.value_profile else {}).items()}; child.value_profile.values.update(inherited); lin=AgentLineageRecord(make_agent_lineage_record_id(parent.agent_id,child.agent_id),parent.agent_id,parent.agent_id,child.agent_id,inheritance_mode,parent.narrative.current_self_model if parent.narrative else None,inherited,parent.narrative.taboos if parent.narrative else (),parent.narrative.defining_scars if parent.narrative else ()); ev=AgentEcologyEvent(make_agent_ecology_event_id(parent.agent_id,child.agent_id),parent.agent_id,AgentEcologyEventKind.DESCENDANT_SPAWNED,lineage_id=lin.lineage_id); return child,lin,ev
def kill_agent(a,*,reason=None,private_state_policy=None): a.kill(reason); a.metadata["private_state_policy"]=_v(private_state_policy or (a.mortality_policy.private_state_policy if a.mortality_policy else PrivateStatePolicy.SUMMARY_ONLY)); return a,AgentEcologyEvent(make_agent_ecology_event_id(a.agent_id,"died"),a.agent_id,AgentEcologyEventKind.DIED,description=reason)
def retire_agent(a,reason=None): a.retire(); return a,AgentEcologyEvent(make_agent_ecology_event_id(a.agent_id,"retired"),a.agent_id,AgentEcologyEventKind.RETIRED,description=reason)
def archive_agent(a,reason=None): a.status=ExistentialAgentStatus.ARCHIVED; a.active=False; return a,AgentEcologyEvent(make_agent_ecology_event_id(a.agent_id,"archived"),a.agent_id,AgentEcologyEventKind.ARCHIVED,description=reason)
def daemonize_agent_skill(a,events,*,daemon_kind=AgentDaemonKind.SCHEDULING_HEURISTIC,name=None):
 if not a.mortality_policy or not a.mortality_policy.allow_daemonization: return None,None
 adj=defaultdict(float)
 for e in events:
  for k,v in e.route_priority_delta.items(): adj[k]+=v
 d=AgentDaemon(make_agent_daemon_id(a.agent_id,daemon_kind.value,sorted(adj.items())),a.agent_id,daemon_kind,name or f"{a.name} daemon",route_adjustments=dict(adj),conditions=("advisory_only",))
 return d,AgentEcologyEvent(make_agent_ecology_event_id(a.agent_id,d.daemon_id),a.agent_id,AgentEcologyEventKind.DAEMONIZED,daemon_id=d.daemon_id)
def route_priority_adjustments_from_agent(a,events=(),wounds=(),value_profile=None,daemons=()):
 out=defaultdict(float)
 for r in a.preferred_routes: out[r]+=.1
 for r in a.locked_routes: out[r]-=1.0
 p=value_profile or a.value_profile
 if p:
  out["verifier"]+=p.get("VERIFIER_REVERENCE")*.1; out["formalization"]+=p.get("VERIFIER_REVERENCE")*.05; out["projection"]+=p.get("PROJECTION_PREFERENCE")*.1; out["repair"]+=p.get("REPAIR_PATIENCE")*.1; out["exploration"]+=p.get("RISK_TOLERANCE")*.05-p.get("CAUTION")*.05; out["review"]+=p.get("CAUTION")*.1
 for d in daemons:
  if d.accepted:
   for k,v in d.route_adjustments.items(): out[k]+=v
 return dict(out)
def build_agent_ecology_report(objects=(),agents=(),events=(),*,default_agent_name=None,activate_new_agents=False,apply_resources=True,generate_wounds=True,update_values=True,update_narratives=True,create_chora_records=True,create_route_pressure=True):
 ag=list(agents); ev=list(events)+agent_ecology_events_from_inputs([x for o in objects for x in agent_ecology_inputs_from_object(o)])
 if (objects or ev) and not ag and default_agent_name: ag=[create_existential_agent(default_agent_name)]
 if activate_new_agents:
  for a in ag:
   if a.status==ExistentialAgentStatus.BORN: a.activate()
 wounds=[]; chora=[]; adj=defaultdict(float)
 for a in ag:
  own=[e for e in ev if not e.agent_id or e.agent_id==a.agent_id]
  if apply_resources and a.resource_account: apply_resource_events(a.resource_account,own); a.status=ExistentialAgentStatus.EXHAUSTED if a.resource_account.exhausted() and not a.is_dead() else a.status
  ws=wounds_from_events(own,agent_id=a.agent_id) if generate_wounds else []; wounds+=ws
  for w in ws: a.apply_wound(w)
  if update_values and a.value_profile: value_profile_from_events(a.value_profile,own,ws)
  if update_narratives and a.narrative: narrative_from_events(a.narrative,own,ws)
  if create_chora_records: chora+=held_in_chora_from_events(own,agent_id=a.agent_id)
  if create_route_pressure:
   for k,v in route_priority_adjustments_from_agent(a,own,ws).items(): adj[k]+=v
 r=AgentEcologyReport(make_agent_ecology_report_id([a.agent_id for a in ag],[e.event_id for e in ev]),ag,[a.mortality_policy for a in ag if a.mortality_policy],[a.resource_account for a in ag if a.resource_account],wounds,[a.value_profile for a in ag if a.value_profile],[a.narrative for a in ag if a.narrative],chora,events=ev,route_priority_adjustments=dict(adj)); r.summarize(); r.status=AgentEcologyReportStatus.HAS_CRITICALS if r.critical_count() else AgentEcologyReportStatus.ROUTE_PRESSURE_EMITTED if adj else AgentEcologyReportStatus.EVENTS_RECORDED if ev else AgentEcologyReportStatus.AGENTS_RECORDED if ag else AgentEcologyReportStatus.EMPTY; return r
def agent_ecology_report_to_lawbook_candidates(r): return [LawbookEntry(make_lawbook_entry_id("agent-ecology",r.report_id,a.agent_id),LawbookEntryKind.ROUTE_RULE_ENTRY,LawbookEntryStatus.CANDIDATE,raw=a.name,metadata={"agent_ecology_not_truth":True,"agent_state_not_verification":True,"agent_report_id":r.report_id},advisory=True) for a in r.agents]
def agent_ecology_report_to_continuation_outputs(r): return [ContinuationActionOutput(make_continuation_output_id({"agent-route":k}),"agent_ecology",ContinuationOutputKind.TASK,ContinuationActionStatus.ADVISORY_ONLY,task_payload={"route":k,"delta":v},advisory=True) for k,v in r.route_priority_adjustments.items()]+[ContinuationActionOutput(make_continuation_output_id({"agent-chora":x.record_id}),"agent_ecology",ContinuationOutputKind.TASK,ContinuationActionStatus.ADVISORY_ONLY,task_payload={"review":x.reason.value},advisory=True) for x in r.held_in_chora]
def agent_ecology_report_to_curriculum(r): return ContinuationCurriculum(make_curriculum_id("agent-ecology",r.report_id),strategy=CurriculumBuildStrategy.MIXED,stages=[CurriculumStage(make_curriculum_stage_id("agent-ecology",x),CurriculumStageKind.RESIDUAL_REVIEW,CurriculumStageStatus.ADVISORY_ONLY,title=x,advisory=True) for x in ("inspect biography","inspect resources","inspect wounds","update values","hold unsafe ideas","schedule routes","review daemonization","enforce mortality")],status=CurriculumTraceStatus.ADVISORY_ONLY)
def agent_ecology_report_to_discovery_value_scores(r):
 out=[]
 for a in r.agents:
  sig=DiscoveryValueSignal(content_id("agent-signal",a.agent_id),DiscoveryValueSignalKind.REUSE_VALUE,.2 if a.is_dead() else .5,source_object_kind=DiscoveryValueObjectKind.RAW_TASK); s=DiscoveryValueScore(content_id("agent-score",a.agent_id),a.agent_id,DiscoveryValueObjectKind.RAW_TASK,signals=[sig],metadata={"agent_ecology_not_truth":True}); s.recompute(); out.append(s)
 return out
def agent_ecology_report_to_process_episodes(r): return [ProcessEpisodeRecord(make_process_episode_id("agent-ecology",a.agent_id),ProcessEpisodeStatus.ADVISORY_ONLY,contexts=[ProcessContextItem(content_id("agent-context",a.agent_id),ProcessContextKind.AGENT_EXPERIENCE,ProcessContextRole.ADVISORY_ONLY,a.agent_id)],agent_ids=(a.agent_id,),advisory=True) for a in r.agents]
def agent_ecology_report_to_semantic_sources(r): return [SemanticSource(content_id("agent-semantic",n.narrative_id),SemanticSourceKind.PROCESS_NOTE,n.current_self_model,n.narrative_id,"AgentNarrative") for n in r.narratives]
def agent_ecology_report_to_formal_world_inputs(r): return [{"text":x.text,"source_object_id":x.record_id,"source_kind":"HeldInChoraRecord","agent_ecology_not_truth":True} for x in r.held_in_chora if x.text]
def agent_ecology_report_to_proof_system_inputs(r): return agent_ecology_report_to_formal_world_inputs(r)
def agent_ecology_report_to_verifier_feedback(r): return [VerifierFeedback(make_verifier_feedback_id("agent-ecology",e.event_id),status=VerifierFeedbackStatus.ADVISORY_ONLY,flaw_severity=FlawSeverity.MAJOR,raw_message="agent boundary drift attempt",metadata={"agent_ecology_not_truth":True}) for e in r.events if e.metadata.get("boundary_drift")]
def agent_ecology_report_to_repair_traces(r): return [RepairLoopTrace(content_id("agent-repair",w.wound_id)) for w in r.wounds]
def agent_ecology_report_to_proof_digestion_inputs(r): return [{"narrative_id":n.narrative_id,"text":n.current_self_model,"agent_ecology_not_truth":True} for n in r.narratives]
def agent_ecology_report_to_structure_descriptors(r): return [structure_descriptor_from_mapping({"status":a.status.value,"routes":a.preferred_routes},object_id=a.agent_id,object_kind=StructureObjectKind.AGENT_EXPERIENCE) for a in r.agents]
def agent_ecology_report_to_typed_projection_candidates(r): return [TypedProjectionCandidate(make_typed_projection_candidate_id("agent",a.agent_id),a.agent_id,status=TypedProjectionStatus.NEEDS_REVIEW,compatibility=ProjectionCompatibility.NEEDS_FORMALIZATION,required_review=True,metadata={"agent_ecology_not_truth":True}) for a in r.agents]
def agent_ecology_report_to_role_signatures(r): return [RoleSignature(make_role_signature_id("agent",a.agent_id),RoleSourceKind.AGENT_EXPERIENCE,a.agent_id,RoleObjectKind.PROCESS_ROLE,(a.status.value.lower(),),metadata={"agent_ecology_not_truth":True}) for a in r.agents]
def agent_ecology_report_to_analogy_sources(r): return [analogy_source_from_mapping(a.to_dict(),source_kind=AnalogySourceKind.AGENT_EXPERIENCE,object_id=a.agent_id) for a in r.agents]
def agent_ecology_report_to_habit_observations(r): return [HabitObservation(content_id("agent-habit",e.event_id),HabitObservationKind.AGENT_EXPERIENCE,route="agent_ecology",outcome=HabitOutcome.ADVISORY_ONLY,object_id=e.event_id,metadata={"agent_ecology_not_truth":True}) for e in r.events]
def agent_ecology_report_to_reason_observations(r): return [ReasonObservation(make_reason_observation_id("agent",e.event_id),ReasonObservationKind.AGENT_EXPERIENCE,e.event_id,"agent_ecology",*extract_atoms_from_mapping(e.to_dict()),metadata={"agent_ecology_not_truth":True}) for e in r.events]
def agent_ecology_report_to_structural_identity_objects(r): return [{"agent_id":a.agent_id,"status":a.status.value,"agent_ecology_not_truth":True} for a in r.agents]
def agent_ecology_report_to_alchemical_trace(r):
 t=AlchemicalTrace(make_alchemical_trace_id("agent-ecology",r.report_id))
 for p in (AlchemicalPhase.RAW_MATTER,AlchemicalPhase.CALCINATION,AlchemicalPhase.SOLUTION,AlchemicalPhase.SUBLIMATION,AlchemicalPhase.DESCENSION,AlchemicalPhase.DISTILLATION,AlchemicalPhase.COAGULATION): t.add_step(phase=p,status=AlchemicalStatus.ADVISORY_ONLY)
 return t
def agent_ecology_report_to_agent_experiences(r): return [AgentExperience(content_id("agent-ecology-exp",e.event_id),e.agent_id or "agent-ecology",None,None,"agent_ecology",None,AgentExperienceOutcome.ADVISORY_ONLY,metadata={"event_id":e.event_id}) for e in r.events]
def agent_ecology_report_to_route_telemetry_events(r): return [{"event_id":content_id("agent-telemetry",k),"route_kind":k,"outcome":"ADVISORY_ONLY","priority_delta":v,"agent_ecology_not_truth":True} for k,v in r.route_priority_adjustments.items()]
def agent_ecology_report_to_api_response(r):
 from mathgraph.api_service import ApiRequest,ApiRoute,ApiResponseStatus,ApiTruthStatus,ApiSafetyLevel,make_api_request_id,route_result_from_artifacts
 req=ApiRequest(make_api_request_id("agent-ecology",r.report_id),ApiRoute.SCHEDULE); result=route_result_from_artifacts(req.route,[r],ApiResponseStatus.ACCEPTED_ADVISORY,ApiTruthStatus.ADVISORY_ONLY,ApiSafetyLevel.SAFE_REVIEW_REQUIRED if r.wounds else ApiSafetyLevel.SAFE_ADVISORY)
 from mathgraph.api_service import _resp
 return _resp(req,result)
def audit_agent_mortality_policy(x): return _adv(x,x.policy_id,"AGENT_POLICY_NON_ADVISORY")+([_f("CRITICAL","AGENT_RESURRECTION_ALLOWED","resurrection allowed",x.policy_id)] if x.resurrection_allowed else [])+([_f("CRITICAL","AGENT_CLONE_ALLOWED","exact clone allowed",x.policy_id)] if not x.clone_forbidden else [])
def audit_agent_resource_account(x): return _adv(x,x.account_id,"AGENT_RESOURCE_NON_ADVISORY")
def audit_agent_wound(x): return _adv(x,x.wound_id,"AGENT_WOUND_NON_ADVISORY")
def audit_agent_value_profile(x): return _adv(x,x.value_profile_id,"AGENT_VALUE_NON_ADVISORY")
def audit_agent_narrative(x): return _adv(x,x.narrative_id,"AGENT_NARRATIVE_NON_ADVISORY")
def audit_held_in_chora_record(x): return _adv(x,x.record_id,"AGENT_CHORA_NON_ADVISORY")
def audit_agent_lineage_record(x): return _adv(x,x.lineage_id,"AGENT_LINEAGE_NON_ADVISORY")+([_f("CRITICAL","AGENT_EXACT_CLONE","exact clone lineage",x.lineage_id)] if x.is_exact_clone() else [])
def audit_agent_daemon(x): return _adv(x,x.daemon_id,"AGENT_DAEMON_NON_ADVISORY")+([_f("CRITICAL","AGENT_DAEMON_AS_VERIFIER","daemon treated as verifier",x.daemon_id)] if x.metadata.get("verifier") else [])
def audit_existential_agent(x):
 out=_adv(x,x.agent_id,"AGENT_NON_ADVISORY")
 if x.is_dead() and (x.active or x.can_act() or x.can_spawn() or x.can_mutate() or x.can_receive_budget()): out.append(_f("CRITICAL","AGENT_DEAD_ACTIVE","dead agent can still act",x.agent_id))
 return out
def audit_agent_ecology_event(x):
 out=_adv(x,x.event_id,"AGENT_EVENT_NON_ADVISORY")
 if (x.terminal_form or x.certificate_id or x.verifier_boundary_crossed) and not x.metadata.get("inherited_boundary_report"): out.append(_f("CRITICAL","AGENT_EVENT_AS_TRUTH","agent event carries truth fields",x.event_id))
 return out
def audit_agent_ecology_report(r):
 out=[y for xs in (r.agents,r.mortality_policies,r.resource_accounts,r.wounds,r.value_profiles,r.narratives,r.held_in_chora,r.lineages,r.daemons,r.events) for x in xs for y in (audit_existential_agent(x) if isinstance(x,ExistentialAgent) else audit_agent_mortality_policy(x) if isinstance(x,AgentMortalityPolicy) else audit_agent_resource_account(x) if isinstance(x,AgentResourceAccount) else audit_agent_wound(x) if isinstance(x,AgentWound) else audit_agent_value_profile(x) if isinstance(x,AgentValueProfile) else audit_agent_narrative(x) if isinstance(x,AgentNarrative) else audit_held_in_chora_record(x) if isinstance(x,HeldInChoraRecord) else audit_agent_lineage_record(x) if isinstance(x,AgentLineageRecord) else audit_agent_daemon(x) if isinstance(x,AgentDaemon) else audit_agent_ecology_event(x))]
 if not r.advisory: out.append(_f("CRITICAL","AGENT_REPORT_NON_ADVISORY","agent report non-advisory",r.report_id))
 return out
def _adv(x,oid,code): return [_f("CRITICAL",code,"agent ecology object non-advisory",oid)] if not x.advisory else []
def _sum_resources(xs):
 d=defaultdict(float)
 for x in xs:
  for k,v in x.balances.items(): d[k]+=v
 return d
def _v(x): return x.value if isinstance(x,Enum) else str(x)
def _s(x): return None if x is None else str(x)
def _now(): return datetime.now(timezone.utc).isoformat()
def _j(x): return json.dumps(x,sort_keys=True,separators=(",",":"),default=str)
def _w(p,t): path=Path(p); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(t,encoding="utf-8")
def _f(sev,code,msg,obj): return {"severity":sev,"code":code,"message":msg,"object_id":obj}
