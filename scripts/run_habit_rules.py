#!/usr/bin/env python
"""Build advisory habit rules from repeated MathGraph route observations."""
from __future__ import annotations
import sys
from pathlib import Path

try:
    from _bootstrap import ensure_repo_root_on_path
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
else:
    ensure_repo_root_on_path(__file__)

import argparse, json, sys
from pathlib import Path
from mathgraph.agent_biography import AgentExperience
from mathgraph.alchemy import AlchemicalTrace
from mathgraph.continuation_curriculum import ContinuationCurriculum
from mathgraph.discovery_value import DiscoveryValueReport
from mathgraph.habit_rules import *
from mathgraph.lawbook import LawbookStore
from mathgraph.lawbook_query import LawbookQueryReport
from mathgraph.projection import ProjectionCandidate
from mathgraph.proof_digestion import ProofDigestionTrace
from mathgraph.roadmap_alignment import check_roadmap_alignment
from mathgraph.structural_identity import StructuralIdentityReport
from mathgraph.verification_episode import VerificationEpisodeTrace
from mathgraph.verifier_feedback import RepairLoopTrace, VerifierFeedback

def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__)
 for name in ("route-telemetry-jsonl","projection-candidates-jsonl","verifier-feedback-jsonl","agent-experiences-jsonl","raw-event-jsonl","route-scores-jsonl"): p.add_argument("--"+name)
 for name in ("discovery-value-report-json","lawbook-query-report-json","lawbook-store-json","structural-identity-report-json","curriculum-json","verification-episode-json","proof-digestion-json","repair-trace-json","alchemical-trace-json","raw-event-json"): p.add_argument("--"+name,action="append",default=[])
 p.add_argument("--auto-candidates",action=argparse.BooleanOptionalAction,default=True); p.add_argument("--auto-review",action=argparse.BooleanOptionalAction,default=True); p.add_argument("--auto-promote",action="store_true"); p.add_argument("--reviewer"); p.add_argument("--min-support",type=int,default=3); p.add_argument("--min-success-rate",type=float,default=0.6); p.add_argument("--max-risk",type=float,default=0.5); p.add_argument("--no-require-conditions",action="store_true")
 for name in ("out-ranked-routes-jsonl","out-report-json","out-report-jsonl","out-observations-jsonl","out-candidates-jsonl","out-reviews-jsonl","out-rules-jsonl","out-store-json","out-lawbook-candidates-jsonl","out-continuation-outputs-jsonl","out-curriculum-json","out-discovery-value-scores-jsonl","out-alchemical-trace-json","out-agent-experiences-jsonl","out-route-telemetry-jsonl","alignment-report-json","alignment-report-md"): p.add_argument("--"+name)
 p.add_argument("--fail-on-critical",action="store_true"); a=p.parse_args(argv)
 objects=[]
 objects += _jl(a.route_telemetry_jsonl, dict); objects += [_j(path,DiscoveryValueReport) for path in a.discovery_value_report_json]; objects += [_j(path,LawbookQueryReport) for path in a.lawbook_query_report_json]; objects += [LawbookStore.read_json(path) for path in a.lawbook_store_json]; objects += _jl(a.projection_candidates_jsonl,ProjectionCandidate); objects += [_j(path,StructuralIdentityReport) for path in a.structural_identity_report_json]; objects += [_j(path,ContinuationCurriculum) for path in a.curriculum_json]; objects += [_j(path,VerificationEpisodeTrace) for path in a.verification_episode_json]; objects += [_j(path,ProofDigestionTrace) for path in a.proof_digestion_json]; objects += _jl(a.verifier_feedback_jsonl,VerifierFeedback); objects += [_j(path,RepairLoopTrace) for path in a.repair_trace_json]; objects += [_j(path,AlchemicalTrace) for path in a.alchemical_trace_json]; objects += _jl(a.agent_experiences_jsonl,AgentExperience); objects += [json.loads(Path(path).read_text()) for path in a.raw_event_json]; objects += _jl(a.raw_event_jsonl,dict)
 r=build_habit_formation_report(objects,auto_candidates=a.auto_candidates,auto_review=a.auto_review,auto_promote=a.auto_promote,reviewer=a.reviewer,min_support=a.min_support,min_success_rate=a.min_success_rate,max_risk=a.max_risk,require_conditions=not a.no_require_conditions)
 ranked=rank_routes_with_habits(r.rules,_jl(a.route_scores_jsonl,dict)) if a.route_scores_jsonl else []
 laws=habit_report_to_lawbook_candidates(r); outs=habit_report_to_continuation_outputs(r); cur=habit_report_to_curriculum(r); vals=habit_report_to_discovery_value_scores(r); alc=habit_report_to_alchemical_trace(r); exps=habit_report_to_agent_experiences(r); tele=habit_report_to_route_telemetry_events(r)
 align=check_roadmap_alignment(habit_reports=[r],habit_candidates=r.candidates,habit_rules=r.rules,habit_reviews=r.reviews,lawbook_entries=laws)
 if a.out_ranked_routes_jsonl:_wjl(a.out_ranked_routes_jsonl,ranked)
 if a.out_report_json:r.write_json(a.out_report_json)
 if a.out_report_jsonl:r.write_jsonl(a.out_report_jsonl)
 for path,rows in ((a.out_observations_jsonl,r.observations),(a.out_candidates_jsonl,r.candidates),(a.out_reviews_jsonl,r.reviews),(a.out_rules_jsonl,r.rules),(a.out_lawbook_candidates_jsonl,laws),(a.out_continuation_outputs_jsonl,outs),(a.out_discovery_value_scores_jsonl,vals),(a.out_agent_experiences_jsonl,exps)):
  if path:_wjl(path,[x.to_dict() for x in rows])
 if a.out_store_json and r.store:r.store.write_json(a.out_store_json)
 if a.out_curriculum_json:cur.write_json(a.out_curriculum_json)
 if a.out_alchemical_trace_json:alc.write_json(a.out_alchemical_trace_json)
 if a.out_route_telemetry_jsonl:_wjl(a.out_route_telemetry_jsonl,tele)
 if a.alignment_report_json:align.write_json(a.alignment_report_json)
 if a.alignment_report_md:align.write_markdown(a.alignment_report_md)
 if not any(v for k,v in vars(a).items() if k.startswith("out_") or k.startswith("alignment_report")): sys.stdout.write(r.to_json()+"\n")
 return 1 if a.fail_on_critical and align.critical_count() else 0
def _j(p,c): return c.from_json(Path(p).read_text())
def _jl(p,c):
 if not p:return []
 return [json.loads(x) if c is dict else c.from_dict(json.loads(x)) for x in Path(p).read_text().splitlines() if x.strip()]
def _wjl(p,rows): path=Path(p);path.parent.mkdir(parents=True,exist_ok=True);path.write_text("".join(json.dumps(x,sort_keys=True)+"\n" for x in rows),encoding="utf-8")
if __name__=="__main__": raise SystemExit(main())
