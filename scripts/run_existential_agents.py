#!/usr/bin/env python
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from mathgraph.existential_agents import *
from mathgraph.roadmap_alignment import check_roadmap_alignment
def main(argv=None):
 p=argparse.ArgumentParser(); p.add_argument("--agent-name",action="append",default=[]); p.add_argument("--activate-new-agents",action="store_true"); p.add_argument("--default-agent-name")
 for n in ("agent-json","event-json","raw-event-json"): p.add_argument("--"+n,action="append",default=[])
 for n in ("agent-jsonl","event-jsonl","raw-event-jsonl"): p.add_argument("--"+n)
 p.add_argument("--kill-agent"); p.add_argument("--retire-agent"); p.add_argument("--archive-agent"); p.add_argument("--spawn-from-agent"); p.add_argument("--child-name"); p.add_argument("--inheritance-mode",default="SUMMARY_ONLY"); p.add_argument("--daemonize-agent"); p.add_argument("--daemon-kind",default="SCHEDULING_HEURISTIC")
 for n in ("apply-resources","generate-wounds","update-values","update-narratives","chora-records","route-pressure"): p.add_argument("--"+n,action=argparse.BooleanOptionalAction,default=True)
 for n in ("out-report-json","out-report-jsonl","out-agents-jsonl","out-events-jsonl","out-wounds-jsonl","out-values-jsonl","out-narratives-jsonl","out-chora-jsonl","out-lineages-jsonl","out-daemons-jsonl","out-route-adjustments-json","out-lawbook-candidates-jsonl","out-continuation-outputs-jsonl","out-curriculum-json","out-discovery-value-scores-jsonl","out-process-episodes-jsonl","out-semantic-sources-jsonl","out-formal-world-inputs-jsonl","out-proof-system-inputs-jsonl","out-verifier-feedback-jsonl","out-repair-traces-jsonl","out-proof-digestion-inputs-jsonl","out-structure-descriptors-jsonl","out-typed-projections-jsonl","out-role-signatures-jsonl","out-analogy-sources-jsonl","out-habit-observations-jsonl","out-reason-observations-jsonl","out-structural-objects-jsonl","out-alchemical-trace-json","out-agent-experiences-jsonl","out-route-telemetry-jsonl","out-api-response-json","alignment-report-json","alignment-report-md"): p.add_argument("--"+n)
 p.add_argument("--fail-on-critical",action="store_true"); a=p.parse_args(argv)
 agents=[create_existential_agent(x) for x in a.agent_name]+[ExistentialAgent.from_json(Path(x).read_text()) for x in a.agent_json]+_jl(a.agent_jsonl,ExistentialAgent); events=[AgentEcologyEvent.from_json(Path(x).read_text()) for x in a.event_json]+_jl(a.event_jsonl,AgentEcologyEvent); objs=[json.loads(Path(x).read_text()) for x in a.raw_event_json]+_jl(a.raw_event_jsonl,dict)
 extra_events=[]; lineages=[]; daemons=[]
 for ag in list(agents):
  if ag.agent_id==a.kill_agent: _,e=kill_agent(ag,reason="cli"); extra_events.append(e)
  if ag.agent_id==a.retire_agent: _,e=retire_agent(ag,"cli"); extra_events.append(e)
  if ag.agent_id==a.archive_agent: _,e=archive_agent(ag,"cli"); extra_events.append(e)
  if ag.agent_id==a.spawn_from_agent:
   child,lin,e=spawn_descendant(ag,child_name=a.child_name or "descendant",inheritance_mode=AgentInheritanceMode(a.inheritance_mode)); lineages.append(lin); extra_events.append(e)
   if child: agents.append(child)
  if ag.agent_id==a.daemonize_agent:
   d,e=daemonize_agent_skill(ag,events,daemon_kind=AgentDaemonKind(a.daemon_kind))
   if d: daemons.append(d)
   if e: extra_events.append(e)
 r=build_agent_ecology_report(objs,agents,events+extra_events,default_agent_name=a.default_agent_name,activate_new_agents=a.activate_new_agents,apply_resources=a.apply_resources,generate_wounds=a.generate_wounds,update_values=a.update_values,update_narratives=a.update_narratives,create_chora_records=a.chora_records,create_route_pressure=a.route_pressure); r.lineages+=lineages; r.daemons+=daemons; r.summarize()
 bridges=[agent_ecology_report_to_lawbook_candidates(r),agent_ecology_report_to_continuation_outputs(r),agent_ecology_report_to_discovery_value_scores(r),agent_ecology_report_to_process_episodes(r),agent_ecology_report_to_semantic_sources(r),agent_ecology_report_to_formal_world_inputs(r),agent_ecology_report_to_proof_system_inputs(r),agent_ecology_report_to_verifier_feedback(r),agent_ecology_report_to_repair_traces(r),agent_ecology_report_to_proof_digestion_inputs(r),agent_ecology_report_to_structure_descriptors(r),agent_ecology_report_to_typed_projection_candidates(r),agent_ecology_report_to_role_signatures(r),agent_ecology_report_to_analogy_sources(r),agent_ecology_report_to_habit_observations(r),agent_ecology_report_to_reason_observations(r),agent_ecology_report_to_structural_identity_objects(r),agent_ecology_report_to_agent_experiences(r),agent_ecology_report_to_route_telemetry_events(r)]
 align=check_roadmap_alignment(agent_ecology_reports=[r],existential_agents=r.agents,agent_ecology_events=r.events)
 if a.out_report_json:r.write_json(a.out_report_json)
 if a.out_report_jsonl:r.write_jsonl(a.out_report_jsonl)
 for path,rows in ((a.out_agents_jsonl,r.agents),(a.out_events_jsonl,r.events),(a.out_wounds_jsonl,r.wounds),(a.out_values_jsonl,r.value_profiles),(a.out_narratives_jsonl,r.narratives),(a.out_chora_jsonl,r.held_in_chora),(a.out_lineages_jsonl,r.lineages),(a.out_daemons_jsonl,r.daemons),(a.out_lawbook_candidates_jsonl,bridges[0]),(a.out_continuation_outputs_jsonl,bridges[1]),(a.out_discovery_value_scores_jsonl,bridges[2]),(a.out_process_episodes_jsonl,bridges[3]),(a.out_semantic_sources_jsonl,bridges[4]),(a.out_formal_world_inputs_jsonl,bridges[5]),(a.out_proof_system_inputs_jsonl,bridges[6]),(a.out_verifier_feedback_jsonl,bridges[7]),(a.out_repair_traces_jsonl,bridges[8]),(a.out_proof_digestion_inputs_jsonl,bridges[9]),(a.out_structure_descriptors_jsonl,bridges[10]),(a.out_typed_projections_jsonl,bridges[11]),(a.out_role_signatures_jsonl,bridges[12]),(a.out_analogy_sources_jsonl,bridges[13]),(a.out_habit_observations_jsonl,bridges[14]),(a.out_reason_observations_jsonl,bridges[15]),(a.out_structural_objects_jsonl,bridges[16]),(a.out_agent_experiences_jsonl,bridges[17]),(a.out_route_telemetry_jsonl,bridges[18])):
  if path:_wjl(path,[x.to_dict() if hasattr(x,"to_dict") else x for x in rows])
 if a.out_route_adjustments_json:_w(a.out_route_adjustments_json,json.dumps(r.route_priority_adjustments,sort_keys=True))
 if a.out_curriculum_json:agent_ecology_report_to_curriculum(r).write_json(a.out_curriculum_json)
 if a.out_alchemical_trace_json:agent_ecology_report_to_alchemical_trace(r).write_json(a.out_alchemical_trace_json)
 if a.out_api_response_json:_w(a.out_api_response_json,agent_ecology_report_to_api_response(r).to_json())
 if a.alignment_report_json:align.write_json(a.alignment_report_json)
 if a.alignment_report_md:align.write_markdown(a.alignment_report_md)
 if not any(v for k,v in vars(a).items() if k.startswith("out_") or k.startswith("alignment_report")): sys.stdout.write(r.to_json()+"\n")
 return 1 if a.fail_on_critical and align.critical_count() else 0
def _jl(p,c): return [] if not p else [json.loads(x) if c is dict else c.from_dict(json.loads(x)) for x in Path(p).read_text().splitlines() if x.strip()]
def _wjl(p,rows): _w(p,"".join(json.dumps(x,sort_keys=True,default=str)+"\n" for x in rows))
def _w(p,t): path=Path(p); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(t)
if __name__=="__main__": raise SystemExit(main())
