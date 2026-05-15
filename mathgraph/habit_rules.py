"""Advisory habit formation and route-priority adjustment for MathGraph."""

from __future__ import annotations

import json
from collections import defaultdict
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
from mathgraph.discovery_value import DiscoveryValueDecision, DiscoveryValueObjectKind, DiscoveryValueScore, DiscoveryValueSignal, DiscoveryValueSignalKind
from mathgraph.hashing import content_id
from mathgraph.lawbook import LawbookEntry, LawbookEntryKind, LawbookEntryStatus, LawbookStore, make_lawbook_entry_id


class HabitObservationKind(str, Enum):
    ROUTE_TELEMETRY = "ROUTE_TELEMETRY"; DISCOVERY_VALUE = "DISCOVERY_VALUE"; LAWBOOK_QUERY = "LAWBOOK_QUERY"; LAWBOOK_ACCEPTANCE = "LAWBOOK_ACCEPTANCE"; PROJECTION = "PROJECTION"; STRUCTURAL_IDENTITY = "STRUCTURAL_IDENTITY"; CURRICULUM = "CURRICULUM"; VERIFICATION_EPISODE = "VERIFICATION_EPISODE"; PROOF_DIGESTION = "PROOF_DIGESTION"; VERIFIER_FEEDBACK = "VERIFIER_FEEDBACK"; REPAIR_LOOP = "REPAIR_LOOP"; ALCHEMICAL_TRACE = "ALCHEMICAL_TRACE"; AGENT_EXPERIENCE = "AGENT_EXPERIENCE"; RAW_EVENT = "RAW_EVENT"; UNKNOWN = "UNKNOWN"


class HabitOutcome(str, Enum):
    VERIFIED_PROOF = "VERIFIED_PROOF"; FINITE_COUNTERMODEL = "FINITE_COUNTERMODEL"; NAMED_OBSTRUCTION = "NAMED_OBSTRUCTION"; KNOWN_SKIP = "KNOWN_SKIP"; ACCEPTED_MEMORY = "ACCEPTED_MEMORY"; PROJECTION_GAIN = "PROJECTION_GAIN"; DIGESTION_GAIN = "DIGESTION_GAIN"; REPAIR_SUCCESS = "REPAIR_SUCCESS"; STRUCTURAL_REVIEW = "STRUCTURAL_REVIEW"; RESIDUAL_SHARPENED = "RESIDUAL_SHARPENED"; FAILED_SEARCH = "FAILED_SEARCH"; INVALID_CANDIDATE = "INVALID_CANDIDATE"; KILLED_ROUTE = "KILLED_ROUTE"; AMBIGUOUS = "AMBIGUOUS"; ADVISORY_ONLY = "ADVISORY_ONLY"; UNKNOWN = "UNKNOWN"


class HabitRuleKind(str, Enum):
    ROUTE_PRIORITY = "ROUTE_PRIORITY"; KNOWN_SKIP_FIRST = "KNOWN_SKIP_FIRST"; PROJECTION_FIRST = "PROJECTION_FIRST"; REPAIR_FIRST = "REPAIR_FIRST"; DIGESTION_FIRST = "DIGESTION_FIRST"; CURRICULUM_TEMPLATE = "CURRICULUM_TEMPLATE"; STRUCTURAL_REVIEW_FIRST = "STRUCTURAL_REVIEW_FIRST"; COUNTERMODEL_ROUTE = "COUNTERMODEL_ROUTE"; PROOF_ROUTE = "PROOF_ROUTE"; OBSTRUCTION_ROUTE = "OBSTRUCTION_ROUTE"; COST_AVOIDANCE = "COST_AVOIDANCE"; RISK_AVOIDANCE = "RISK_AVOIDANCE"; HOLD_IN_CHORA = "HOLD_IN_CHORA"; UNKNOWN = "UNKNOWN"


class HabitStatus(str, Enum):
    CANDIDATE = "CANDIDATE"; ACCEPTED = "ACCEPTED"; REJECTED = "REJECTED"; RETIRED = "RETIRED"; SUPERSEDED = "SUPERSEDED"; NEEDS_MORE_EVIDENCE = "NEEDS_MORE_EVIDENCE"; NEEDS_REVIEW = "NEEDS_REVIEW"; INVALID = "INVALID"; UNKNOWN = "UNKNOWN"


class HabitReviewDecision(str, Enum):
    ACCEPT = "ACCEPT"; REJECT = "REJECT"; NEEDS_MORE_EVIDENCE = "NEEDS_MORE_EVIDENCE"; NEEDS_CONDITIONS = "NEEDS_CONDITIONS"; NEEDS_LOWER_RISK = "NEEDS_LOWER_RISK"; HOLD_IN_CHORA = "HOLD_IN_CHORA"; UNKNOWN = "UNKNOWN"


class HabitFormationReportStatus(str, Enum):
    EMPTY = "EMPTY"; OBSERVED = "OBSERVED"; CANDIDATES_FOUND = "CANDIDATES_FOUND"; REVIEWED = "REVIEWED"; ACCEPTED_RULES = "ACCEPTED_RULES"; HAS_WARNINGS = "HAS_WARNINGS"; HAS_CRITICALS = "HAS_CRITICALS"; ADVISORY_ONLY = "ADVISORY_ONLY"


SUCCESS = {HabitOutcome.VERIFIED_PROOF, HabitOutcome.FINITE_COUNTERMODEL, HabitOutcome.NAMED_OBSTRUCTION, HabitOutcome.KNOWN_SKIP, HabitOutcome.ACCEPTED_MEMORY, HabitOutcome.PROJECTION_GAIN, HabitOutcome.DIGESTION_GAIN, HabitOutcome.REPAIR_SUCCESS, HabitOutcome.STRUCTURAL_REVIEW, HabitOutcome.RESIDUAL_SHARPENED}
FAILURE = {HabitOutcome.FAILED_SEARCH, HabitOutcome.INVALID_CANDIDATE, HabitOutcome.KILLED_ROUTE, HabitOutcome.AMBIGUOUS}


@dataclass
class HabitObservation:
    observation_id: str; kind: HabitObservationKind; route: str | None = None; condition_key: str | None = None; outcome: HabitOutcome = HabitOutcome.UNKNOWN; object_id: str | None = None; source_kind: str | None = None; cost_units: float = 0.0; gain_units: float = 0.0; residual_delta: int = 0; compression_gain: float = 0.0; projection_gain: float = 0.0; derived_amplification: float = 0.0; verifier_boundary_crossed: bool = False; certificate_id: str | None = None; terminal_form: TerminalForm | None = None; killed: bool = False; kill_reason: str | None = None; risk_tags: tuple[str, ...] = (); metadata: dict[str, Any] = field(default_factory=dict); advisory: bool = True
    def is_success(self) -> bool: return self.outcome in SUCCESS
    def is_failure(self) -> bool: return self.outcome in FAILURE
    def net_gain(self) -> float: return self.gain_units + self.compression_gain + self.projection_gain + self.derived_amplification - self.cost_units
    def to_dict(self): return {**self.__dict__, "kind": self.kind.value, "outcome": self.outcome.value, "terminal_form": self.terminal_form.value if self.terminal_form else None, "risk_tags": list(self.risk_tags)}
    @classmethod
    def from_dict(cls,d): return cls(str(d["observation_id"]), HabitObservationKind(str(d.get("kind","UNKNOWN"))), _s(d.get("route")), _s(d.get("condition_key")), HabitOutcome(str(d.get("outcome","UNKNOWN"))), _s(d.get("object_id")), _s(d.get("source_kind")), float(d.get("cost_units",0) or 0), float(d.get("gain_units",0) or 0), int(d.get("residual_delta",0) or 0), float(d.get("compression_gain",0) or 0), float(d.get("projection_gain",0) or 0), float(d.get("derived_amplification",0) or 0), bool(d.get("verifier_boundary_crossed",False)), _s(d.get("certificate_id")), TerminalForm(str(d["terminal_form"])) if d.get("terminal_form") else None, bool(d.get("killed",False)), _s(d.get("kill_reason")), tuple(map(str,d.get("risk_tags",()))), dict(d.get("metadata",{})), bool(d.get("advisory",True)))
    def to_json(self): return _j(self.to_dict())
    @classmethod
    def from_json(cls,t): return cls.from_dict(json.loads(t))


@dataclass
class HabitCandidate:
    candidate_id: str; rule_kind: HabitRuleKind; route: str; condition_key: str | None = None; observations: tuple[str,...]=(); support_count:int=0; success_count:int=0; failure_count:int=0; killed_count:int=0; ambiguity_count:int=0; avg_cost:float=0.0; avg_gain:float=0.0; total_gain:float=0.0; success_rate:float=0.0; cost_per_gain:float|None=None; confidence:float=0.0; risk_score:float=0.0; explicit_conditions:tuple[str,...]=(); status:HabitStatus=HabitStatus.CANDIDATE; reason:str|None=None; warnings:tuple[str,...]=(); criticals:tuple[str,...]=(); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
    def is_promotable(self,min_support=3,min_success_rate=0.6,max_risk=0.5,require_conditions=True): return self.advisory and not self.criticals and self.support_count>=min_support and self.success_rate>=min_success_rate and self.risk_score<=max_risk and (bool(self.explicit_conditions) or not require_conditions)
    def to_dict(self): return {**self.__dict__, "rule_kind":self.rule_kind.value,"observations":list(self.observations),"explicit_conditions":list(self.explicit_conditions),"status":self.status.value,"warnings":list(self.warnings),"criticals":list(self.criticals)}
    @classmethod
    def from_dict(cls,d): return cls(str(d["candidate_id"]),HabitRuleKind(str(d.get("rule_kind","UNKNOWN"))),str(d["route"]),_s(d.get("condition_key")),tuple(map(str,d.get("observations",()))),int(d.get("support_count",0)),int(d.get("success_count",0)),int(d.get("failure_count",0)),int(d.get("killed_count",0)),int(d.get("ambiguity_count",0)),float(d.get("avg_cost",0)),float(d.get("avg_gain",0)),float(d.get("total_gain",0)),float(d.get("success_rate",0)),d.get("cost_per_gain"),float(d.get("confidence",0)),float(d.get("risk_score",0)),tuple(map(str,d.get("explicit_conditions",()))),HabitStatus(str(d.get("status","CANDIDATE"))),_s(d.get("reason")),tuple(map(str,d.get("warnings",()))),tuple(map(str,d.get("criticals",()))),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
    def to_json(self): return _j(self.to_dict())
    @classmethod
    def from_json(cls,t): return cls.from_dict(json.loads(t))


@dataclass
class HabitRule:
    rule_id:str; rule_kind:HabitRuleKind; route:str; status:HabitStatus=HabitStatus.CANDIDATE; condition_key:str|None=None; conditions:tuple[str,...]=(); priority_delta:float=0.0; confidence:float=0.0; support_count:int=0; success_rate:float=0.0; avg_cost:float=0.0; avg_gain:float=0.0; risk_score:float=0.0; source_candidate_id:str|None=None; observation_ids:tuple[str,...]=(); accepted_at:str|None=None; accepted_by:str|None=None; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
    def is_accepted(self): return self.status==HabitStatus.ACCEPTED
    def applies_to(self,mapping_or_metadata:Mapping[str,Any]): 
        text=_j(dict(mapping_or_metadata)).lower()
        return bool(self.conditions) and any(cond.lower() in text or (_condition_pair_applies(cond, mapping_or_metadata)) for cond in self.conditions)
    def to_dict(self): return {**self.__dict__,"rule_kind":self.rule_kind.value,"status":self.status.value,"conditions":list(self.conditions),"observation_ids":list(self.observation_ids)}
    @classmethod
    def from_dict(cls,d): return cls(str(d["rule_id"]),HabitRuleKind(str(d.get("rule_kind","UNKNOWN"))),str(d["route"]),HabitStatus(str(d.get("status","CANDIDATE"))),_s(d.get("condition_key")),tuple(map(str,d.get("conditions",()))),float(d.get("priority_delta",0)),float(d.get("confidence",0)),int(d.get("support_count",0)),float(d.get("success_rate",0)),float(d.get("avg_cost",0)),float(d.get("avg_gain",0)),float(d.get("risk_score",0)),_s(d.get("source_candidate_id")),tuple(map(str,d.get("observation_ids",()))),_s(d.get("accepted_at")),_s(d.get("accepted_by")),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
    def to_json(self): return _j(self.to_dict())
    @classmethod
    def from_json(cls,t): return cls.from_dict(json.loads(t))


@dataclass
class HabitReview:
    review_id:str; candidate_id:str; decision:HabitReviewDecision; reviewer:str|None=None; reason:str|None=None; required_evidence:tuple[str,...]=(); created_at:str=field(default_factory=lambda:_now()); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
    def to_dict(self): return {**self.__dict__,"decision":self.decision.value,"required_evidence":list(self.required_evidence)}
    @classmethod
    def from_dict(cls,d): return cls(str(d["review_id"]),str(d["candidate_id"]),HabitReviewDecision(str(d.get("decision","UNKNOWN"))),_s(d.get("reviewer")),_s(d.get("reason")),tuple(map(str,d.get("required_evidence",()))),str(d.get("created_at") or _now()),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
    def to_json(self): return _j(self.to_dict())
    @classmethod
    def from_json(cls,t): return cls.from_dict(json.loads(t))


@dataclass
class HabitStore:
    store_id:str; observations:list[HabitObservation]=field(default_factory=list); candidates:list[HabitCandidate]=field(default_factory=list); rules:list[HabitRule]=field(default_factory=list); reviews:list[HabitReview]=field(default_factory=list); created_at:str=field(default_factory=lambda:_now()); summary:dict[str,Any]=field(default_factory=dict); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
    def observation_count(self): return len(self.observations)
    def candidate_count(self): return len(self.candidates)
    def rule_count(self): return len(self.rules)
    def accepted_rules(self): return [r for r in self.rules if r.is_accepted()]
    def candidate_rules(self): return [r for r in self.rules if r.status==HabitStatus.CANDIDATE]
    def add_observation(self,x): self.observations.append(x)
    def add_candidate(self,x): self.candidates.append(x)
    def add_rule(self,x): self.rules.append(x)
    def add_review(self,x): self.reviews.append(x)
    def summarize(self): self.summary={"observation_total":len(self.observations),"candidate_total":len(self.candidates),"rule_total":len(self.rules),"accepted_rule_count":len(self.accepted_rules()),"review_total":len(self.reviews),"advisory_count":sum(x.advisory for x in self.rules)}; return dict(self.summary)
    def to_dict(self): return {"store_id":self.store_id,"observations":[x.to_dict() for x in self.observations],"candidates":[x.to_dict() for x in self.candidates],"rules":[x.to_dict() for x in self.rules],"reviews":[x.to_dict() for x in self.reviews],"created_at":self.created_at,"summary":dict(self.summary),"metadata":dict(self.metadata),"advisory":self.advisory}
    @classmethod
    def from_dict(cls,d): return cls(str(d["store_id"]),[HabitObservation.from_dict(x) for x in d.get("observations",[])],[HabitCandidate.from_dict(x) for x in d.get("candidates",[])],[HabitRule.from_dict(x) for x in d.get("rules",[])],[HabitReview.from_dict(x) for x in d.get("reviews",[])],str(d.get("created_at") or _now()),dict(d.get("summary",{})),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
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
class HabitFormationReport:
    report_id:str; observations:list[HabitObservation]=field(default_factory=list); candidates:list[HabitCandidate]=field(default_factory=list); reviews:list[HabitReview]=field(default_factory=list); rules:list[HabitRule]=field(default_factory=list); store:HabitStore|None=None; status:HabitFormationReportStatus=HabitFormationReportStatus.EMPTY; created_at:str=field(default_factory=lambda:_now()); summary:dict[str,Any]=field(default_factory=dict); metadata:dict[str,Any]=field(default_factory=lambda:{"advisory_only":True}); advisory:bool=True
    def observation_count(self): return len(self.observations)
    def candidate_count(self): return len(self.candidates)
    def accepted_rule_count(self): return sum(r.is_accepted() for r in self.rules)
    def critical_count(self): return sum(len(c.criticals) for c in self.candidates)
    def summarize(self): self.summary={"observation_total":len(self.observations),"candidate_total":len(self.candidates),"review_total":len(self.reviews),"rule_total":len(self.rules),"accepted_rule_count":self.accepted_rule_count(),"critical_count":self.critical_count(),"advisory_count":sum(x.advisory for x in self.candidates+self.rules)}; return dict(self.summary)
    def to_dict(self): return {"report_id":self.report_id,"observations":[x.to_dict() for x in self.observations],"candidates":[x.to_dict() for x in self.candidates],"reviews":[x.to_dict() for x in self.reviews],"rules":[x.to_dict() for x in self.rules],"store":self.store.to_dict() if self.store else None,"status":self.status.value,"created_at":self.created_at,"summary":dict(self.summary),"metadata":dict(self.metadata),"advisory":self.advisory}
    @classmethod
    def from_dict(cls,d): return cls(str(d["report_id"]),[HabitObservation.from_dict(x) for x in d.get("observations",[])],[HabitCandidate.from_dict(x) for x in d.get("candidates",[])],[HabitReview.from_dict(x) for x in d.get("reviews",[])],[HabitRule.from_dict(x) for x in d.get("rules",[])],HabitStore.from_dict(d["store"]) if d.get("store") else None,HabitFormationReportStatus(str(d.get("status","EMPTY"))),str(d.get("created_at") or _now()),dict(d.get("summary",{})),dict(d.get("metadata",{"advisory_only":True})),bool(d.get("advisory",True)))
    def to_json(self): return _j(self.to_dict())
    @classmethod
    def from_json(cls,t): return cls.from_dict(json.loads(t))
    def write_json(self,p): _w(p,self.to_json()+"\n")
    @classmethod
    def read_json(cls,p): return cls.from_json(Path(p).read_text())
    def write_jsonl(self,p): _w(p,self.to_json()+"\n")
    @classmethod
    def read_jsonl(cls,p): return [cls.from_json(x) for x in Path(p).read_text().splitlines() if x.strip()]


def make_habit_observation_id(*x): return content_id("habit-observation",x)
def make_habit_candidate_id(*x): return content_id("habit-candidate",x)
def make_habit_rule_id(*x): return content_id("habit-rule",x)
def make_habit_review_id(*x): return content_id("habit-review",x)
def make_habit_store_id(*x): return content_id("habit-store",x)
def make_habit_formation_report_id(*x): return content_id("habit-report",x)


def _obs(kind, route, outcome, object_id=None, **kw): return HabitObservation(make_habit_observation_id(kind.value,route,outcome.value,object_id,kw),kind,route,object_id=object_id,outcome=outcome,**kw)
def habit_observations_from_route_telemetry_event(e):
    outcome=_outcome(e.get("outcome") or e.get("status"), bool(e.get("killed")))
    return [_obs(HabitObservationKind.ROUTE_TELEMETRY,_s(e.get("route") or e.get("route_kind") or e.get("action_kind") or e.get("decision")),outcome,_s(e.get("event_id")),condition_key=_s(e.get("condition_key")),cost_units=float(e.get("cost_units",0) or 0),gain_units=float(e.get("gain_units",0) or 0),residual_delta=int(e.get("residual_delta",0) or 0),compression_gain=float(e.get("compression_gain",0) or 0),projection_gain=float(e.get("projection_gain",0) or 0),derived_amplification=float(e.get("derived_amplification",0) or 0),killed=bool(e.get("killed",False)),kill_reason=_s(e.get("kill_reason")),metadata=dict(e))]
def habit_observations_from_discovery_value_report(r):
    return [_obs(HabitObservationKind.DISCOVERY_VALUE,s.decision.value.lower(),HabitOutcome.PROJECTION_GAIN if s.decision==DiscoveryValueDecision.PROJECT else HabitOutcome.ADVISORY_ONLY,s.score_id,condition_key=s.object_kind.value,metadata={"decision":s.decision.value,"object_kind":s.object_kind.value}) for s in r.scores]
def habit_observations_from_lawbook_query_report(r):
    return [_obs(HabitObservationKind.LAWBOOK_QUERY,a.known_skip_decision.value.lower(),HabitOutcome.KNOWN_SKIP if a.is_known_skip() else HabitOutcome.AMBIGUOUS if a.status.value=="AMBIGUOUS" else HabitOutcome.ADVISORY_ONLY,a.answer_id,condition_key=a.status.value,metadata={"query_status":a.status.value,"trust_level":a.trust_level.value}) for a in r.answers]
def habit_observations_from_lawbook_store(s):
    return [_obs(HabitObservationKind.LAWBOOK_ACCEPTANCE,"lawbook_acceptance",HabitOutcome.ACCEPTED_MEMORY if e.is_accepted() else HabitOutcome.ADVISORY_ONLY,e.entry_id,condition_key=e.kind.value,metadata={"entry_kind":e.kind.value}) for e in s.entries]
def habit_observations_from_projection_candidates(cs):
    return [_obs(HabitObservationKind.PROJECTION,c.rule_kind.value.lower(),HabitOutcome.PROJECTION_GAIN,c.candidate_id,condition_key=c.rule_kind.value,projection_gain=c.confidence,metadata={"rule_kind":c.rule_kind.value}) for c in cs]
def habit_observations_from_structural_identity_report(r):
    return [_obs(HabitObservationKind.STRUCTURAL_IDENTITY,c.decision.value.lower(),HabitOutcome.AMBIGUOUS if c.match_kind.value=="CONFLICTING_DUPLICATE" else HabitOutcome.STRUCTURAL_REVIEW,c.candidate_id,condition_key=c.match_kind.value,metadata={"match_kind":c.match_kind.value}) for c in r.merge_candidates]
def habit_observations_from_curriculum(c):
    return [_obs(HabitObservationKind.CURRICULUM,st.kind.value.lower(),HabitOutcome.ADVISORY_ONLY,st.stage_id,condition_key=st.kind.value,metadata={"stage_kind":st.kind.value}) for st in c.stages]
def habit_observations_from_verification_episode(t):
    return [_obs(HabitObservationKind.VERIFICATION_EPISODE,t.status.value.lower(),_outcome(t.terminal_form.value if t.terminal_form else t.status.value),t.trace_id,condition_key=t.status.value,certificate_id=t.certificate_id,terminal_form=t.terminal_form,verifier_boundary_crossed=t.is_terminal(),metadata={"status":t.status.value})]
def habit_observations_from_proof_digestion_trace(t):
    return [_obs(HabitObservationKind.PROOF_DIGESTION,"digestion",HabitOutcome.DIGESTION_GAIN,t.trace_id,condition_key=t.status.value,gain_units=float(len(t.key_ideas)+len(t.reusable_schemas)),projection_gain=float(len(t.projection_candidates)),metadata={"object_kind":"proof_digestion"})]
def habit_observations_from_verifier_feedback(f):
    return [_obs(HabitObservationKind.VERIFIER_FEEDBACK,"repair" if f.is_repairable() else "feedback",HabitOutcome.REPAIR_SUCCESS if f.is_repairable() else HabitOutcome.ADVISORY_ONLY,f.feedback_id,condition_key=f.flaw_severity.value,metadata={"flaw_severity":f.flaw_severity.value})]
def habit_observations_from_repair_loop(t):
    return [_obs(HabitObservationKind.REPAIR_LOOP,"repair_loop",HabitOutcome.REPAIR_SUCCESS if t.repair_plans else HabitOutcome.ADVISORY_ONLY,t.trace_id,condition_key=t.status.value,metadata={"status":t.status.value})]
def habit_observations_from_alchemical_trace(t):
    return [_obs(HabitObservationKind.ALCHEMICAL_TRACE,"alchemy",_outcome(t.terminal_form.value if t.is_promoted() and t.terminal_form else "advisory"),t.trace_id,condition_key="phases:"+",".join(p.value for p in t.phases_seen()),compression_gain=t.total_compression_gain(),verifier_boundary_crossed=t.is_promoted(),metadata={"phases":[p.value for p in t.phases_seen()]})]
def habit_observations_from_agent_experience(e):
    return [_obs(HabitObservationKind.AGENT_EXPERIENCE,e.route or "agent",_outcome(e.outcome.value),e.experience_id,condition_key=e.phase,cost_units=e.cost_units,residual_delta=e.residual_delta,compression_gain=e.compression_gain,projection_gain=e.projection_gain,derived_amplification=e.derived_amplification,verifier_boundary_crossed=e.verifier_boundary_crossed,certificate_id=e.certificate_id,terminal_form=e.terminal_form,metadata={"outcome":e.outcome.value})]
def habit_observations_from_mapping(d): return habit_observations_from_route_telemetry_event(d) if any(k in d for k in ("route","route_kind","outcome","status")) else [_obs(HabitObservationKind.RAW_EVENT,"raw_event",HabitOutcome.ADVISORY_ONLY,_s(d.get("id")),metadata=dict(d))]


def habit_observations_from_object(o):
    from mathgraph.discovery_value import DiscoveryValueReport
    from mathgraph.lawbook_query import LawbookQueryReport
    from mathgraph.projection import ProjectionCandidate
    from mathgraph.proof_digestion import ProofDigestionTrace
    from mathgraph.structural_identity import StructuralIdentityReport
    from mathgraph.verification_episode import VerificationEpisodeTrace
    from mathgraph.verifier_feedback import RepairLoopTrace, VerifierFeedback
    if isinstance(o,DiscoveryValueReport): return habit_observations_from_discovery_value_report(o)
    if isinstance(o,LawbookQueryReport): return habit_observations_from_lawbook_query_report(o)
    if isinstance(o,LawbookStore): return habit_observations_from_lawbook_store(o)
    if isinstance(o,ProjectionCandidate): return habit_observations_from_projection_candidates([o])
    if isinstance(o,StructuralIdentityReport): return habit_observations_from_structural_identity_report(o)
    if isinstance(o,ContinuationCurriculum): return habit_observations_from_curriculum(o)
    if isinstance(o,VerificationEpisodeTrace): return habit_observations_from_verification_episode(o)
    if isinstance(o,ProofDigestionTrace): return habit_observations_from_proof_digestion_trace(o)
    if isinstance(o,VerifierFeedback): return habit_observations_from_verifier_feedback(o)
    if isinstance(o,RepairLoopTrace): return habit_observations_from_repair_loop(o)
    if isinstance(o,AlchemicalTrace): return habit_observations_from_alchemical_trace(o)
    if isinstance(o,AgentExperience): return habit_observations_from_agent_experience(o)
    if isinstance(o,Mapping): return habit_observations_from_mapping(o)
    return []


def infer_condition_key(o):
    if o.condition_key: return o.condition_key
    for key in ("basin","route","stage_kind","query_status","trust_level","object_kind","match_kind","decision","terminal_form"):
        if o.metadata.get(key): return f"{key}:{o.metadata[key]}"
    return o.source_kind or "global"
def infer_rule_kind(route, obs):
    text=(route+" "+" ".join(o.outcome.value for o in obs)).lower()
    if "known_skip" in text: return HabitRuleKind.KNOWN_SKIP_FIRST
    if "repair" in text: return HabitRuleKind.REPAIR_FIRST
    if "projection" in text or "project" in text: return HabitRuleKind.PROJECTION_FIRST
    if "digestion" in text: return HabitRuleKind.DIGESTION_FIRST
    if "curriculum" in text or "stage" in text: return HabitRuleKind.CURRICULUM_TEMPLATE
    if "structural" in text or "merge" in text or "review" in text: return HabitRuleKind.STRUCTURAL_REVIEW_FIRST
    if any(o.outcome==HabitOutcome.FINITE_COUNTERMODEL for o in obs): return HabitRuleKind.COUNTERMODEL_ROUTE
    if any(o.outcome==HabitOutcome.VERIFIED_PROOF for o in obs): return HabitRuleKind.PROOF_ROUTE
    if any(o.outcome==HabitOutcome.NAMED_OBSTRUCTION for o in obs): return HabitRuleKind.OBSTRUCTION_ROUTE
    if sum(o.is_failure() for o in obs)>sum(o.is_success() for o in obs): return HabitRuleKind.RISK_AVOIDANCE
    return HabitRuleKind.ROUTE_PRIORITY
def build_habit_candidates(observations,min_support=2):
    groups=defaultdict(list)
    for o in observations: groups[(o.route or "unknown", infer_condition_key(o))].append(o)
    out=[]
    for (route,cond), xs in groups.items():
        support=len(xs); success=sum(x.is_success() for x in xs); failure=sum(x.is_failure() for x in xs); killed=sum(x.killed or x.outcome==HabitOutcome.KILLED_ROUTE for x in xs); amb=sum(x.outcome==HabitOutcome.AMBIGUOUS for x in xs); gains=[x.net_gain() for x in xs]; avg_cost=mean(x.cost_units for x in xs); avg_gain=mean(gains); risk=min(1.0,(failure+killed+amb)/support); rate=success/support; conf=max(0,min(1,0.25+0.15*support+0.4*rate-0.3*risk)); warnings=tuple(x for x,ok in (("low support",support<min_support),("high risk",risk>0.5),("no explicit conditions",not cond or cond=="global"),("high cost low gain",avg_cost>0 and avg_gain<=0)) if ok); criticals=tuple("terminal without verifier boundary" for x in xs if x.terminal_form and not x.verifier_boundary_crossed)
        out.append(HabitCandidate(make_habit_candidate_id(route,cond,[x.observation_id for x in xs]),infer_rule_kind(route,xs),route,cond,tuple(x.observation_id for x in xs),support,success,failure,killed,amb,avg_cost,avg_gain,sum(gains),rate,(avg_cost/max(avg_gain,1e-9) if avg_gain>0 else None),conf,risk,(() if cond=="global" else (cond,)),warnings=warnings,criticals=criticals,reason="repeated route outcomes",metadata={"habit_advisory_only":True}))
    return out


def review_habit_candidate(c,*,reviewer=None,min_support=3,min_success_rate=0.6,max_risk=0.5,require_conditions=True):
    if not c.advisory or c.criticals: decision=HabitReviewDecision.REJECT
    elif c.support_count<min_support: decision=HabitReviewDecision.NEEDS_MORE_EVIDENCE
    elif require_conditions and not c.explicit_conditions: decision=HabitReviewDecision.NEEDS_CONDITIONS
    elif c.risk_score>max_risk: decision=HabitReviewDecision.NEEDS_LOWER_RISK
    elif c.success_rate>=min_success_rate: decision=HabitReviewDecision.ACCEPT
    else: decision=HabitReviewDecision.HOLD_IN_CHORA
    return HabitReview(make_habit_review_id(c.candidate_id,decision.value),c.candidate_id,decision,reviewer,required_evidence=tuple(c.warnings))
def promote_habit_candidate(c,r,*,accepted_by=None):
    if r.decision==HabitReviewDecision.ACCEPT and c.criticals: raise ValueError("cannot accept critical habit candidate")
    accepted=r.decision==HabitReviewDecision.ACCEPT
    return HabitRule(make_habit_rule_id(c.candidate_id,r.review_id),c.rule_kind,c.route,HabitStatus.ACCEPTED if accepted else HabitStatus.REJECTED if r.decision==HabitReviewDecision.REJECT else HabitStatus.NEEDS_REVIEW,c.condition_key,c.explicit_conditions,max(0,min(1,c.confidence*c.success_rate*(1-c.risk_score))) if accepted else 0.0,c.confidence,c.support_count,c.success_rate,c.avg_cost,c.avg_gain,c.risk_score,c.candidate_id,c.observations,_now() if accepted else None,accepted_by,{"habit_rule_not_truth":True},True)
def build_habit_store(*,observations=(),candidates=(),reviews=(),rules=(),auto_candidates=False,auto_review=False,auto_promote=False,reviewer=None,min_support=3,min_success_rate=0.6,max_risk=0.5,require_conditions=True):
    cs=list(candidates) or (build_habit_candidates(observations) if auto_candidates else []); rs=list(reviews) or ([review_habit_candidate(c,reviewer=reviewer,min_support=min_support,min_success_rate=min_success_rate,max_risk=max_risk,require_conditions=require_conditions) for c in cs] if auto_review else []); rules2=list(rules)
    if auto_promote: rules2 += [promote_habit_candidate(c,r,accepted_by=reviewer) for c in cs for r in rs if r.candidate_id==c.candidate_id and r.decision==HabitReviewDecision.ACCEPT]
    s=HabitStore(make_habit_store_id([o.observation_id for o in observations]),list(observations),cs,rules2,rs,metadata={"advisory_only":True}); s.summarize(); return s
def build_habit_formation_report(objects=(),observations=(),*,auto_candidates=True,auto_review=True,auto_promote=False,reviewer=None,min_support=3,min_success_rate=0.6,max_risk=0.5,require_conditions=True):
    obs=list(observations)+[x for o in objects for x in habit_observations_from_object(o)]
    store=build_habit_store(observations=obs,auto_candidates=auto_candidates,auto_review=auto_review,auto_promote=auto_promote,reviewer=reviewer,min_support=min_support,min_success_rate=min_success_rate,max_risk=max_risk,require_conditions=require_conditions)
    rep=HabitFormationReport(make_habit_formation_report_id([o.observation_id for o in obs]),obs,store.candidates,store.reviews,store.rules,store)
    rep.summarize()
    rep.status=HabitFormationReportStatus.EMPTY if not obs else HabitFormationReportStatus.HAS_CRITICALS if rep.critical_count() else HabitFormationReportStatus.ACCEPTED_RULES if rep.accepted_rule_count() else HabitFormationReportStatus.REVIEWED if rep.reviews else HabitFormationReportStatus.CANDIDATES_FOUND if rep.candidates else HabitFormationReportStatus.OBSERVED
    return rep


def apply_habit_rules(rules, route_scores):
    out=[]
    for row in route_scores:
        hits=[r for r in rules if r.is_accepted() and r.applies_to(row)]
        delta=sum(r.priority_delta for r in hits); base=float(row.get("score",row.get("raw_score",0)) or 0)
        out.append({**dict(row),"habit_rule_ids":[r.rule_id for r in hits],"habit_priority_delta":delta,"habit_adjusted_score":base+delta,"habit_advisory_only":True})
    return out
def rank_routes_with_habits(rules,route_scores): return sorted(apply_habit_rules(rules,route_scores),key=lambda x:x["habit_adjusted_score"],reverse=True)


def habit_report_to_lawbook_candidates(r):
    return [LawbookEntry(make_lawbook_entry_id("habit",x.rule_id),LawbookEntryKind.ROUTE_RULE_ENTRY,LawbookEntryStatus.CANDIDATE,conditions=x.conditions,metadata={"habit_rule_not_truth":True,"habit_rule_id":x.rule_id,"habit_advisory_only":True},advisory=True) for x in r.rules if x.is_accepted()]
def habit_report_to_continuation_outputs(r):
    return [ContinuationActionOutput(make_continuation_output_id({"habit":x.candidate_id}),"habit_rules",ContinuationOutputKind.TASK,ContinuationActionStatus.ADVISORY_ONLY,task_payload={"task":"review habit","candidate_id":x.candidate_id},advisory=True) for x in r.candidates]
def habit_report_to_curriculum(r):
    stages=[CurriculumStage(make_curriculum_stage_id("habit",x.rule_id),CurriculumStageKind.HELD_IN_CHORA if x.is_accepted() else CurriculumStageKind.RESIDUAL_REVIEW,CurriculumStageStatus.ADVISORY_ONLY,title="Apply advisory habit",metadata={"habit_rule_id":x.rule_id},advisory=True) for x in r.rules]
    return ContinuationCurriculum(make_curriculum_id("habit",r.report_id),strategy=CurriculumBuildStrategy.MIXED,stages=stages,status=CurriculumTraceStatus.TASKS_EMITTED if stages else CurriculumTraceStatus.EMPTY,metadata={"advisory_only":True})
def habit_report_to_discovery_value_scores(r):
    out=[]
    for c in r.candidates:
        sig=DiscoveryValueSignal(content_id("habit-signal",c.candidate_id),DiscoveryValueSignalKind.ROUTE_SURVIVAL_VALUE,c.confidence,reason="habit candidate",source_object_kind=DiscoveryValueObjectKind.RAW_TASK)
        out.append(DiscoveryValueScore(content_id("habit-score",c.candidate_id),c.candidate_id,DiscoveryValueObjectKind.RAW_TASK,signals=[sig],metadata={"habit_advisory_only":True},advisory=True))
        out[-1].recompute()
    return out
def habit_report_to_alchemical_trace(r):
    t=AlchemicalTrace(make_alchemical_trace_id("habit",r.report_id))
    for p in (AlchemicalPhase.RAW_MATTER,AlchemicalPhase.SUBLIMATION,AlchemicalPhase.DISTILLATION,AlchemicalPhase.COAGULATION): t.add_step(phase=p,status=AlchemicalStatus.ADVISORY_ONLY)
    return t
def habit_report_to_agent_experiences(r,agent_id=None):
    return [AgentExperience(content_id("habit-exp",(r.report_id,c.candidate_id)),agent_id or "habit-rules",None,None,"habit_rules",None,AgentExperienceOutcome.ADVISORY_ONLY,metadata={"candidate_id":c.candidate_id}) for c in r.candidates]
def habit_report_to_route_telemetry_events(r): return [{"event_id":content_id("habit-telemetry",(r.report_id,c.candidate_id)),"route_kind":"habit_rules","outcome":c.status.value,"habit_advisory_only":True} for c in r.candidates]


def audit_habit_candidate(c):
    fs=[]
    if not c.advisory: fs.append(_f("CRITICAL","HABIT_NON_ADVISORY","habit candidate is non-advisory",c.candidate_id))
    if c.criticals: fs.append(_f("CRITICAL","HABIT_CANDIDATE_CRITICALS","habit candidate has criticals",c.candidate_id))
    if c.support_count<3: fs.append(_f("WARNING","HABIT_LOW_SUPPORT","habit candidate has low support",c.candidate_id))
    if not c.explicit_conditions: fs.append(_f("WARNING","HABIT_NO_CONDITIONS","habit candidate has no explicit conditions",c.candidate_id))
    return fs
def audit_habit_rule(r,max_risk=0.5):
    fs=[]
    if not r.advisory: fs.append(_f("CRITICAL","HABIT_RULE_NON_ADVISORY","habit rule is non-advisory",r.rule_id))
    if r.is_accepted() and not r.conditions: fs.append(_f("CRITICAL","HABIT_ACCEPTED_WITHOUT_CONDITIONS","accepted habit lacks conditions",r.rule_id))
    if r.is_accepted() and r.risk_score>max_risk: fs.append(_f("CRITICAL","HABIT_ACCEPTED_HIGH_RISK","accepted habit is high risk",r.rule_id))
    if r.metadata.get("verifier_boundary"): fs.append(_f("CRITICAL","HABIT_AS_BOUNDARY","habit claims verifier boundary",r.rule_id))
    return fs
def audit_habit_report(r): return [x for c in r.candidates for x in audit_habit_candidate(c)]+[x for rule in r.rules for x in audit_habit_rule(rule)]

def _outcome(v,killed=False):
    if killed: return HabitOutcome.KILLED_ROUTE
    text=str(v or "").upper()
    return HabitOutcome[text] if text in HabitOutcome.__members__ else HabitOutcome.ADVISORY_ONLY
def _s(x): return None if x is None else str(x)
def _now(): return datetime.now(timezone.utc).isoformat()
def _j(x): return json.dumps(x,sort_keys=True,separators=(",",":"))
def _w(p,t): path=Path(p); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(t,encoding="utf-8")
def _f(sev,code,msg,obj): return {"severity":sev,"code":code,"message":msg,"object_id":obj}
def _condition_pair_applies(cond,m):
    if ":" not in cond: return False
    key, value = cond.split(":", 1)
    return str(m.get(key, "")).lower() == value.lower()
