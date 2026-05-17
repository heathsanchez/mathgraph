#!/usr/bin/env python
from __future__ import annotations
import sys
from pathlib import Path

try:
    from _bootstrap import ensure_repo_root_on_path
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
else:
    ensure_repo_root_on_path(__file__)

import argparse,json,sys
from pathlib import Path
from mathgraph.agent_biography import AgentExperience
from mathgraph.alchemy import AlchemicalTrace
from mathgraph.continuation_curriculum import ContinuationCurriculum
from mathgraph.discovery_value import DiscoveryValueReport
from mathgraph.habit_rules import HabitFormationReport
from mathgraph.lawbook import LawbookStore
from mathgraph.lawbook_query import LawbookQueryReport
from mathgraph.process_memory import *
from mathgraph.projection import ProjectionCandidate
from mathgraph.proof_digestion import ProofDigestionTrace
from mathgraph.reason_compression import ReasonCompressionReport
from mathgraph.roadmap_alignment import check_roadmap_alignment
from mathgraph.structural_identity import StructuralIdentityReport
from mathgraph.verification_episode import VerificationEpisodeTrace
from mathgraph.verifier_feedback import RepairLoopTrace,VerifierFeedback
def main(argv=None):
 p=argparse.ArgumentParser()
 for n in ("episode-jsonl","projection-candidates-jsonl","verifier-feedback-jsonl","agent-experiences-jsonl","route-telemetry-jsonl","raw-event-jsonl","query-jsonl"): p.add_argument("--"+n)
 for n in ("episode-json","verification-episode-json","alchemical-trace-json","curriculum-json","lawbook-query-report-json","lawbook-store-json","proof-digestion-json","repair-trace-json","discovery-value-report-json","structural-identity-report-json","habit-report-json","reason-report-json","raw-event-json","query-json"): p.add_argument("--"+n,action="append",default=[])
 for n in ("query-episode-id","query-claim-id","query-route","query-certificate-id","query-lawbook-entry-id","query-habit-rule-id","query-reason-node-id","query-agent-id","query-text"): p.add_argument("--"+n)
 p.add_argument("--trust-summary",action="store_true")
 for n in ("out-store-json","out-store-jsonl","out-report-json","out-report-jsonl","out-episodes-jsonl","out-answers-jsonl","out-lawbook-candidates-jsonl","out-continuation-outputs-jsonl","out-curriculum-json","out-discovery-value-scores-jsonl","out-habit-observations-jsonl","out-reason-observations-jsonl","out-structural-objects-jsonl","out-alchemical-trace-json","out-agent-experiences-jsonl","out-route-telemetry-jsonl","out-elimination-summary-json","out-route-summary-json","alignment-report-json","alignment-report-md"): p.add_argument("--"+n)
 p.add_argument("--fail-on-critical",action="store_true"); a=p.parse_args(argv); objs=[]
 objs += [_jr(x,ProcessEpisodeRecord) for x in a.episode_json]+_jl(a.episode_jsonl,ProcessEpisodeRecord)
 for paths,cls in ((a.verification_episode_json,VerificationEpisodeTrace),(a.alchemical_trace_json,AlchemicalTrace),(a.curriculum_json,ContinuationCurriculum),(a.lawbook_query_report_json,LawbookQueryReport),(a.lawbook_store_json,LawbookStore),(a.proof_digestion_json,ProofDigestionTrace),(a.repair_trace_json,RepairLoopTrace),(a.discovery_value_report_json,DiscoveryValueReport),(a.structural_identity_report_json,StructuralIdentityReport),(a.habit_report_json,HabitFormationReport),(a.reason_report_json,ReasonCompressionReport)):
  objs += [_jr(x,cls) for x in paths]
 objs += _jl(a.projection_candidates_jsonl,ProjectionCandidate)+_jl(a.verifier_feedback_jsonl,VerifierFeedback)+_jl(a.agent_experiences_jsonl,AgentExperience)+_jl(a.route_telemetry_jsonl,dict)+[json.loads(Path(x).read_text()) for x in a.raw_event_json]+_jl(a.raw_event_jsonl,dict)
 store=build_process_memory_store(objs); qs=[_jr(x,ProcessMemoryQuery) for x in a.query_json]+_jl(a.query_jsonl,ProcessMemoryQuery)
 for val,fn in ((a.query_episode_id,make_process_query_by_episode),(a.query_claim_id,make_process_query_by_claim),(a.query_route,make_process_query_by_route),(a.query_certificate_id,make_process_query_by_certificate),(a.query_lawbook_entry_id,make_process_query_by_lawbook_entry),(a.query_habit_rule_id,make_process_query_by_habit_rule),(a.query_reason_node_id,make_process_query_by_reason_node),(a.query_agent_id,make_process_query_by_agent),(a.query_text,make_process_text_query)):
  if val: qs.append(fn(val))
 if a.trust_summary: qs.append(make_process_trust_summary_query())
 report=query_process_memory_store_many(store,qs) if qs else ProcessMemoryReport(make_process_memory_report_id(store.store_id),store,status=ProcessMemoryReportStatus.RECORDED); report.summarize()
 laws=process_report_to_lawbook_candidates(report); outs=process_report_to_continuation_outputs(report); cur=process_report_to_curriculum(report); vals=process_report_to_discovery_value_scores(report); habits=process_report_to_habit_observations(report); reasons=process_report_to_reason_observations(report); structs=process_report_to_structural_identity_objects(report); alc=process_report_to_alchemical_trace(report); exps=process_report_to_agent_experiences(report); tele=process_report_to_route_telemetry_events(report)
 align=check_roadmap_alignment(process_memory_stores=[store],process_memory_reports=[report],process_memory_answers=report.answers,lawbook_entries=laws)
 if a.out_store_json: store.write_json(a.out_store_json)
 if a.out_store_jsonl: store.write_jsonl(a.out_store_jsonl)
 if a.out_report_json: report.write_json(a.out_report_json)
 if a.out_report_jsonl: report.write_jsonl(a.out_report_jsonl)
 for path,rows in ((a.out_episodes_jsonl,store.episodes),(a.out_answers_jsonl,report.answers),(a.out_lawbook_candidates_jsonl,laws),(a.out_continuation_outputs_jsonl,outs),(a.out_discovery_value_scores_jsonl,vals),(a.out_habit_observations_jsonl,habits),(a.out_reason_observations_jsonl,reasons),(a.out_structural_objects_jsonl,structs),(a.out_agent_experiences_jsonl,exps),(a.out_route_telemetry_jsonl,tele)):
  if path:_wjl(path,[x.to_dict() if hasattr(x,"to_dict") else x for x in rows])
 if a.out_curriculum_json: cur.write_json(a.out_curriculum_json)
 if a.out_alchemical_trace_json: alc.write_json(a.out_alchemical_trace_json)
 if a.out_elimination_summary_json:_wj(a.out_elimination_summary_json,summarize_eliminations(store))
 if a.out_route_summary_json:_wj(a.out_route_summary_json,summarize_route_processes(store))
 if a.alignment_report_json: align.write_json(a.alignment_report_json)
 if a.alignment_report_md: align.write_markdown(a.alignment_report_md)
 if not any(v for k,v in vars(a).items() if k.startswith("out_") or k.startswith("alignment_report")): sys.stdout.write(report.to_json()+"\n")
 return 1 if a.fail_on_critical and align.critical_count() else 0
def _jr(p,c): return c.from_json(Path(p).read_text())
def _jl(p,c):
 if not p:return []
 return [json.loads(x) if c is dict else c.from_dict(json.loads(x)) for x in Path(p).read_text().splitlines() if x.strip()]
def _wjl(p,rows): path=Path(p); path.parent.mkdir(parents=True,exist_ok=True); path.write_text("".join(json.dumps(x,sort_keys=True)+"\n" for x in rows))
def _wj(p,row): path=Path(p); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(row,sort_keys=True)+"\n")
if __name__=="__main__": raise SystemExit(main())
