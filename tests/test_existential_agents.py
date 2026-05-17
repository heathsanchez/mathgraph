import json,subprocess,sys
from mathgraph.existential_agents import *
from mathgraph.roadmap_alignment import check_roadmap_alignment
from mathgraph.agent_biography import AgentExperience,AgentExperienceOutcome
def _report():
 a=create_existential_agent("Aurelia",preferred_routes=("projection",)); a.activate()
 return build_agent_ecology_report([{"route":"search","cost_units":30,"status":"FAILED","text":"Proof: clearly true"},{"route":"search","status":"FAILED","terminal_form":"VERIFIED_PROOF"}],[a])
def test_roundtrips_defaults_and_lifecycle():
 a=create_existential_agent("Aurelia"); xs=[a.mortality_policy,a.resource_account,AgentWound("w",a.agent_id),a.value_profile,a.narrative,HeldInChoraRecord("h",a.agent_id),AgentLineageRecord("l",a.agent_id),AgentDaemon("d",a.agent_id),a,AgentEcologyEvent("e"),_report()]
 for x in xs: assert x.from_json(x.to_json()).to_dict()==x.to_dict()
 assert not a.mortality_policy.permits_resurrection() and not a.mortality_policy.permits_exact_clone()
 assert a.resource_account.balance("COMPUTE_BUDGET")==100 and a.resource_account.spend("COMPUTE_BUDGET",5) and not a.resource_account.spend("COMPUTE_BUDGET",-1)
 assert a.value_profile.get("VERIFIER_REVERENCE")>.5 and not a.active
 a.activate(); assert a.can_act(); kill_agent(a); assert a.is_dead() and not a.can_act() and not a.can_spawn() and not a.can_mutate() and not a.can_receive_budget()
def test_events_wounds_values_lineage_daemon_route_pressure():
 r=_report(); assert r.events and r.wounds and r.held_in_chora and r.route_priority_adjustments
 kinds={e.event_kind for e in r.events}; assert {AgentEcologyEventKind.RESOURCE_SPENT,AgentEcologyEventKind.WOUND_ACQUIRED,AgentEcologyEventKind.HELD_IN_CHORA}<=kinds
 assert any(w.wound_type in {AgentWoundType.ROUTE_BURN,AgentWoundType.BUDGET_SCAR,AgentWoundType.TRUST_DAMAGE} for w in r.wounds)
 a=r.agents[0]; assert a.value_profile.get("CAUTION")>.45 and "Do not treat advisory output as proof." in a.narrative.taboos
 child,lin,_=spawn_descendant(a,child_name="B"); assert child and child.status==ExistentialAgentStatus.BORN and not lin.is_exact_clone()
 dead,_=kill_agent(a); child2,_,_=spawn_descendant(dead,child_name="C"); assert child2 is None
 d,_=daemonize_agent_skill(child,[AgentEcologyEvent("e",child.agent_id,route_priority_delta={"projection":.2})]); assert d and not d.accepted
 assert route_priority_adjustments_from_agent(child,daemons=[d]).get("projection",0)>=0
def test_inputs_bridges_audits_alignment():
 exp=AgentExperience("x","a",None,None,"route",None,AgentExperienceOutcome.FAILED_SEARCH,cost_units=2)
 assert agent_ecology_inputs_from_object({"cost_units":1}) and event_from_agent_experience(exp)
 r=_report(); assert all(x.status==LawbookEntryStatus.CANDIDATE for x in agent_ecology_report_to_lawbook_candidates(r))
 assert agent_ecology_report_to_continuation_outputs(r) and agent_ecology_report_to_curriculum(r).stages and agent_ecology_report_to_discovery_value_scores(r)
 assert agent_ecology_report_to_process_episodes(r) and agent_ecology_report_to_semantic_sources(r) and agent_ecology_report_to_formal_world_inputs(r)
 assert agent_ecology_report_to_structure_descriptors(r) and agent_ecology_report_to_typed_projection_candidates(r) and agent_ecology_report_to_role_signatures(r) and agent_ecology_report_to_analogy_sources(r)
 assert agent_ecology_report_to_habit_observations(r) and agent_ecology_report_to_reason_observations(r) and agent_ecology_report_to_structural_identity_objects(r)
 assert all(x.phase.value!="FIXATION" for x in agent_ecology_report_to_alchemical_trace(r).steps)
 assert all(x.outcome==AgentExperienceOutcome.ADVISORY_ONLY for x in agent_ecology_report_to_agent_experiences(r))
 assert agent_ecology_report_to_api_response(r).truth_status.value=="ADVISORY_ONLY"
 assert audit_agent_mortality_policy(AgentMortalityPolicy("p",resurrection_allowed=True))
 assert audit_agent_ecology_event(AgentEcologyEvent("e",terminal_form="VERIFIED_PROOF"))
 assert check_roadmap_alignment(agent_mortality_policies=[AgentMortalityPolicy("p",resurrection_allowed=True)]).critical_count()
def test_cli(tmp_path):
 ev=tmp_path/"events.jsonl"; ev.write_text(json.dumps({"route":"search","cost_units":2,"status":"FAILED","text":"Proof: clearly"})+"\n"); out=tmp_path/"report.json"; agents=tmp_path/"agents.jsonl"
 subprocess.run([sys.executable,"scripts/run_existential_agents.py","--default-agent-name","Aurelia","--activate-new-agents","--raw-event-jsonl",str(ev),"--out-report-json",str(out),"--out-agents-jsonl",str(agents)],check=True)
 assert out.exists() and agents.read_text()
