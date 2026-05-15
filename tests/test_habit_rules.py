import subprocess, sys
from mathgraph.agent_biography import AgentExperience, AgentExperienceOutcome
from mathgraph.alchemy import AlchemicalPhase
from mathgraph.discovery_value import DiscoveryValueDecision, DiscoveryValueObjectKind, DiscoveryValueReport, DiscoveryValueScore
from mathgraph.habit_rules import *
from mathgraph.lawbook_query import KnownSkipDecision, LawbookQueryAnswer, LawbookQueryReport, LawbookQueryStatus, LawbookTrustLevel
from mathgraph.roadmap_alignment import check_roadmap_alignment
from mathgraph.structural_identity import StructuralIdentityReport, StructuralMergeCandidate, StructuralMatchKind, StructuralMergeDecision, StructuralObjectKind

def _obs(i, outcome=HabitOutcome.PROJECTION_GAIN, cond="basin:x", route="projection"):
 return HabitObservation(f"o{i}",HabitObservationKind.RAW_EVENT,route,cond,outcome,gain_units=2.0)
def test_serialization():
 o=_obs(1); c=build_habit_candidates([o])[0]; r=HabitReview("rev",c.candidate_id,HabitReviewDecision.ACCEPT); rule=HabitRule("rule",HabitRuleKind.ROUTE_PRIORITY,"r"); s=HabitStore("s",[o],[c],[rule],[r]); rep=HabitFormationReport("rep",[o],[c],[r],[rule],s)
 assert HabitObservation.from_json(o.to_json()).observation_id=="o1"; assert HabitCandidate.from_json(c.to_json()).candidate_id==c.candidate_id; assert HabitReview.from_json(r.to_json()).review_id=="rev"; assert HabitRule.from_json(rule.to_json()).rule_id=="rule"; assert HabitStore.from_json(s.to_json()).store_id=="s"; assert HabitFormationReport.from_json(rep.to_json()).report_id=="rep"
def test_builders():
 assert habit_observations_from_mapping({"route":"x","outcome":"KNOWN_SKIP"})[0].outcome==HabitOutcome.KNOWN_SKIP
 ans=LawbookQueryAnswer("a","q",LawbookQueryStatus.FOUND_ACCEPTED_TRUTH,LawbookTrustLevel.VERIFIED_TRUTH,KnownSkipDecision.SKIP_VERIFIED_PROOF)
 assert habit_observations_from_lawbook_query_report(LawbookQueryReport("r",answers=[ans]))[0].outcome==HabitOutcome.KNOWN_SKIP
 score=DiscoveryValueScore("s","o",DiscoveryValueObjectKind.RAW_TASK,decision=DiscoveryValueDecision.PROJECT)
 assert habit_observations_from_discovery_value_report(DiscoveryValueReport("d",[score]))[0].outcome==HabitOutcome.PROJECTION_GAIN
 cand=StructuralMergeCandidate("m","l","r",StructuralObjectKind.RAW_OBJECT,StructuralObjectKind.RAW_OBJECT,StructuralMatchKind.NEAR_DUPLICATE,StructuralMergeDecision.REVIEW_RECOMMENDED)
 assert habit_observations_from_structural_identity_report(StructuralIdentityReport("sr",merge_candidates=[cand]))[0].outcome==HabitOutcome.STRUCTURAL_REVIEW
 exp=AgentExperience("e","a",None,None,"route","phase",AgentExperienceOutcome.ADVISORY_ONLY,cost_units=1,projection_gain=2)
 assert habit_observations_from_agent_experience(exp)[0].net_gain()==1
def test_inference_and_candidates():
 xs=[_obs(1),_obs(2),_obs(3),_obs(4,HabitOutcome.FAILED_SEARCH)]
 c=build_habit_candidates(xs)[0]
 assert infer_condition_key(xs[0])=="basin:x"; assert infer_rule_kind("known_skip",xs)==HabitRuleKind.KNOWN_SKIP_FIRST; assert infer_rule_kind("projection",xs)==HabitRuleKind.PROJECTION_FIRST; assert infer_rule_kind("repair",xs)==HabitRuleKind.REPAIR_FIRST
 assert c.support_count==4 and c.success_count==3 and c.failure_count==1 and c.success_rate==.75 and c.risk_score==.25
 assert not build_habit_candidates(xs[:2])[0].is_promotable()
 assert not build_habit_candidates([_obs(1,cond="global"),_obs(2,cond="global"),_obs(3,cond="global")])[0].is_promotable()
 assert not build_habit_candidates([_obs(1,HabitOutcome.FAILED_SEARCH),_obs(2,HabitOutcome.FAILED_SEARCH),_obs(3)])[0].is_promotable()
def test_review_promotion_apply():
 good=build_habit_candidates([_obs(1),_obs(2),_obs(3)])[0]
 assert review_habit_candidate(good).decision==HabitReviewDecision.ACCEPT
 assert review_habit_candidate(build_habit_candidates([_obs(1)])[0]).decision==HabitReviewDecision.NEEDS_MORE_EVIDENCE
 assert review_habit_candidate(build_habit_candidates([_obs(1,cond="global"),_obs(2,cond="global"),_obs(3,cond="global")])[0]).decision==HabitReviewDecision.NEEDS_CONDITIONS
 bad=build_habit_candidates([_obs(1,HabitOutcome.FAILED_SEARCH),_obs(2,HabitOutcome.FAILED_SEARCH),_obs(3)])[0]; assert review_habit_candidate(bad).decision==HabitReviewDecision.NEEDS_LOWER_RISK
 rule=promote_habit_candidate(good,review_habit_candidate(good)); assert rule.is_accepted() and rule.advisory and rule.applies_to({"basin":"x"})
 assert not HabitRule("n",HabitRuleKind.ROUTE_PRIORITY,"r").applies_to({})
 ranked=rank_routes_with_habits([rule],[{"route":"projection","basin":"x","score":1},{"route":"z","score":1}]); assert ranked[0]["habit_advisory_only"] and ranked[0]["habit_adjusted_score"]>ranked[1]["habit_adjusted_score"]
def test_report_bridges_audit_alignment():
 rep=build_habit_formation_report(observations=[_obs(1),_obs(2),_obs(3)],auto_promote=True)
 assert rep.advisory and rep.accepted_rule_count()==1
 assert habit_report_to_lawbook_candidates(rep)[0].status.value=="CANDIDATE"
 assert all(x.advisory and not x.is_terminal() for x in habit_report_to_continuation_outputs(rep))
 assert all(x.advisory for x in habit_report_to_curriculum(rep).stages)
 assert all(x.advisory for x in habit_report_to_discovery_value_scores(rep))
 assert AlchemicalPhase.FIXATION not in habit_report_to_alchemical_trace(rep).phases_seen()
 assert all(x.outcome not in {AgentExperienceOutcome.VERIFIED_PROOF,AgentExperienceOutcome.FINITE_COUNTERMODEL} for x in habit_report_to_agent_experiences(rep))
 assert isinstance(habit_report_to_route_telemetry_events(rep)[0],dict)
 bad=HabitRule("bad",HabitRuleKind.ROUTE_PRIORITY,"r",HabitStatus.ACCEPTED,risk_score=.8,advisory=False)
 assert {x["code"] for x in audit_habit_rule(bad)} >= {"HABIT_RULE_NON_ADVISORY","HABIT_ACCEPTED_WITHOUT_CONDITIONS","HABIT_ACCEPTED_HIGH_RISK"}
 assert check_roadmap_alignment(habit_rules=[bad]).critical_count()>=3
def test_cli(tmp_path):
 raw=tmp_path/"raw.jsonl"; raw.write_text('{"route":"projection","condition_key":"basin:x","outcome":"PROJECTION_GAIN","gain_units":2}\n'*3)
 scores=tmp_path/"scores.jsonl"; scores.write_text('{"route":"projection","basin":"x","score":1}\n')
 for args in (["--out-report-json",str(tmp_path/"empty.json")],["--raw-event-jsonl",str(raw),"--auto-promote","--route-scores-jsonl",str(scores),"--out-candidates-jsonl",str(tmp_path/"c.jsonl"),"--out-rules-jsonl",str(tmp_path/"r.jsonl"),"--out-ranked-routes-jsonl",str(tmp_path/"rank.jsonl"),"--out-lawbook-candidates-jsonl",str(tmp_path/"l.jsonl"),"--out-continuation-outputs-jsonl",str(tmp_path/"o.jsonl"),"--out-curriculum-json",str(tmp_path/"cur.json"),"--out-discovery-value-scores-jsonl",str(tmp_path/"v.jsonl")]):
  assert subprocess.run([sys.executable,"scripts/run_habit_rules.py",*args]).returncode==0
