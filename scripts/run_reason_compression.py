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
from mathgraph.habit_rules import HabitFormationReport,HabitRule
from mathgraph.lawbook import LawbookEntry,LawbookStore
from mathgraph.lawbook_query import LawbookQueryReport
from mathgraph.projection import ProjectionCandidate
from mathgraph.proof_digestion import ProofDigestionTrace
from mathgraph.reason_compression import *
from mathgraph.roadmap_alignment import check_roadmap_alignment
from mathgraph.structural_identity import StructuralIdentityReport
from mathgraph.verifier_feedback import RepairLoopTrace,VerifierFeedback
def main(argv=None):
 p=argparse.ArgumentParser()
 for n in ("habit-rules-jsonl","projection-candidates-jsonl","verifier-feedback-jsonl","agent-experiences-jsonl","route-telemetry-jsonl","raw-event-jsonl","route-scores-jsonl"):p.add_argument("--"+n)
 for n in ("lawbook-store-json","lawbook-entry-json","lawbook-query-report-json","structural-identity-report-json","habit-report-json","discovery-value-report-json","proof-digestion-json","repair-trace-json","curriculum-json","alchemical-trace-json","raw-event-json"):p.add_argument("--"+n,action="append",default=[])
 p.add_argument("--auto-candidates",action=argparse.BooleanOptionalAction,default=True);p.add_argument("--auto-review",action=argparse.BooleanOptionalAction,default=True);p.add_argument("--auto-promote",action="store_true");p.add_argument("--reviewer");p.add_argument("--min-support",type=int,default=3);p.add_argument("--min-coverage-ratio",type=float,default=.2);p.add_argument("--min-sufficiency",type=float,default=.5);p.add_argument("--max-complexity",type=int,default=6);p.add_argument("--max-risk",type=float,default=.5);p.add_argument("--max-atom-set-size",type=int,default=4)
 for n in ("out-ranked-routes-jsonl","out-report-json","out-report-jsonl","out-observations-jsonl","out-candidates-jsonl","out-reviews-jsonl","out-reason-nodes-jsonl","out-lawbook-candidates-jsonl","out-continuation-outputs-jsonl","out-curriculum-json","out-discovery-value-scores-jsonl","out-structural-objects-jsonl","out-alchemical-trace-json","out-agent-experiences-jsonl","out-route-telemetry-jsonl","alignment-report-json","alignment-report-md"):p.add_argument("--"+n)
 p.add_argument("--fail-on-critical",action="store_true");a=p.parse_args(argv);objs=[]
 for paths,cls in ((a.lawbook_store_json,LawbookStore),(a.lawbook_entry_json,LawbookEntry),(a.lawbook_query_report_json,LawbookQueryReport),(a.structural_identity_report_json,StructuralIdentityReport),(a.habit_report_json,HabitFormationReport),(a.discovery_value_report_json,DiscoveryValueReport),(a.proof_digestion_json,ProofDigestionTrace),(a.repair_trace_json,RepairLoopTrace),(a.curriculum_json,ContinuationCurriculum),(a.alchemical_trace_json,AlchemicalTrace)):
  objs += [_jr(x,cls) for x in paths]
 objs += _jl(a.habit_rules_jsonl,HabitRule)+_jl(a.projection_candidates_jsonl,ProjectionCandidate)+_jl(a.verifier_feedback_jsonl,VerifierFeedback)+_jl(a.agent_experiences_jsonl,AgentExperience)+_jl(a.route_telemetry_jsonl,dict)+[json.loads(Path(x).read_text()) for x in a.raw_event_json]+_jl(a.raw_event_jsonl,dict)
 r=build_reason_compression_report(objs,auto_candidates=a.auto_candidates,auto_review=a.auto_review,auto_promote=a.auto_promote,reviewer=a.reviewer,min_support=a.min_support,min_coverage_ratio=a.min_coverage_ratio,min_sufficiency=a.min_sufficiency,max_complexity=a.max_complexity,max_risk=a.max_risk,max_atom_set_size=a.max_atom_set_size)
 ranked=rank_routes_with_reasons(r.reason_nodes,_jl(a.route_scores_jsonl,dict)) if a.route_scores_jsonl else []; laws=reason_report_to_lawbook_candidates(r); outs=reason_report_to_continuation_outputs(r); cur=reason_report_to_curriculum(r); vals=reason_report_to_discovery_value_scores(r); structs=reason_report_to_structural_identity_objects(r); alc=reason_report_to_alchemical_trace(r); exps=reason_report_to_agent_experiences(r); tele=reason_report_to_route_telemetry_events(r); align=check_roadmap_alignment(reason_reports=[r],reason_candidates=r.candidates,reason_nodes=r.reason_nodes,reason_reviews=r.reviews,lawbook_entries=laws)
 if a.out_report_json:r.write_json(a.out_report_json)
 if a.out_report_jsonl:r.write_jsonl(a.out_report_jsonl)
 for path,rows in ((a.out_ranked_routes_jsonl,ranked),(a.out_observations_jsonl,r.observations),(a.out_candidates_jsonl,r.candidates),(a.out_reviews_jsonl,r.reviews),(a.out_reason_nodes_jsonl,r.reason_nodes),(a.out_lawbook_candidates_jsonl,laws),(a.out_continuation_outputs_jsonl,outs),(a.out_discovery_value_scores_jsonl,vals),(a.out_structural_objects_jsonl,structs),(a.out_agent_experiences_jsonl,exps),(a.out_route_telemetry_jsonl,tele)):
  if path:_wjl(path,[x.to_dict() if hasattr(x,"to_dict") else x for x in rows])
 if a.out_curriculum_json:cur.write_json(a.out_curriculum_json)
 if a.out_alchemical_trace_json:alc.write_json(a.out_alchemical_trace_json)
 if a.alignment_report_json:align.write_json(a.alignment_report_json)
 if a.alignment_report_md:align.write_markdown(a.alignment_report_md)
 if not any(v for k,v in vars(a).items() if k.startswith("out_") or k.startswith("alignment_report")):sys.stdout.write(r.to_json()+"\n")
 return 1 if a.fail_on_critical and align.critical_count() else 0
def _jr(p,c):return c.from_json(Path(p).read_text())
def _jl(p,c):
 if not p:return []
 return [json.loads(x) if c is dict else c.from_dict(json.loads(x)) for x in Path(p).read_text().splitlines() if x.strip()]
def _wjl(p,rows):path=Path(p);path.parent.mkdir(parents=True,exist_ok=True);path.write_text("".join(json.dumps(x,sort_keys=True)+"\n" for x in rows))
if __name__=="__main__":raise SystemExit(main())
