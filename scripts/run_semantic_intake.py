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
from mathgraph.semantic_intake import *
from mathgraph.roadmap_alignment import check_roadmap_alignment
def main(argv=None):
 p=argparse.ArgumentParser(); p.add_argument("--input-text",action="append",default=[]); p.add_argument("--input-file",action="append",default=[])
 for n in ("input-json","source-json","raw-event-json"): p.add_argument("--"+n,action="append",default=[])
 for n in ("input-jsonl","source-jsonl","raw-event-jsonl"): p.add_argument("--"+n)
 for n in ("segment","classify","ambiguity","extract","formalization-requests","routing-hints","tasks"): p.add_argument("--"+n,action=argparse.BooleanOptionalAction,default=True)
 for n in ("out-report-json","out-report-jsonl","out-sources-jsonl","out-segments-jsonl","out-classifications-jsonl","out-ambiguities-jsonl","out-extractions-jsonl","out-formalization-requests-jsonl","out-routing-hints-jsonl","out-tasks-jsonl","out-formal-world-inputs-jsonl","out-proof-system-inputs-jsonl","out-lawbook-candidates-jsonl","out-continuation-outputs-jsonl","out-curriculum-json","out-discovery-value-scores-jsonl","out-process-episodes-jsonl","out-verifier-feedback-jsonl","out-repair-traces-jsonl","out-proof-digestion-inputs-jsonl","out-structure-descriptors-jsonl","out-typed-projections-jsonl","out-role-signatures-jsonl","out-analogy-sources-jsonl","out-habit-observations-jsonl","out-reason-observations-jsonl","out-structural-objects-jsonl","out-alchemical-trace-json","out-agent-experiences-jsonl","out-route-telemetry-jsonl","alignment-report-json","alignment-report-md"): p.add_argument("--"+n)
 p.add_argument("--fail-on-critical",action="store_true"); a=p.parse_args(argv)
 objs=list(a.input_text)+[Path(x).read_text() for x in a.input_file]+[json.loads(Path(x).read_text()) for x in a.input_json]+_jl(a.input_jsonl,dict)+[json.loads(Path(x).read_text()) for x in a.raw_event_json]+_jl(a.raw_event_jsonl,dict)
 sources=[SemanticSource.from_json(Path(x).read_text()) for x in a.source_json]+_jl(a.source_jsonl,SemanticSource)
 r=build_semantic_intake_report(objs,sources,segment=a.segment,classify=a.classify,detect_ambiguity=a.ambiguity,extract=a.extract,create_formalization_requests=a.formalization_requests,create_routing_hints=a.routing_hints,create_tasks=a.tasks)
 fw=semantic_report_to_formal_world_inputs(r); ps=semantic_report_to_proof_system_inputs(r); laws=semantic_report_to_lawbook_candidates(r); outs=semantic_report_to_continuation_outputs(r); cur=semantic_report_to_curriculum(r); vals=semantic_report_to_discovery_value_scores(r); eps=semantic_report_to_process_episodes(r); fb=semantic_report_to_verifier_feedback(r); repairs=semantic_report_to_repair_traces(r); dig=semantic_report_to_proof_digestion_inputs(r); desc=semantic_report_to_structure_descriptors(r); typed=semantic_report_to_typed_projection_candidates(r); roles=semantic_report_to_role_signatures(r); analogies=semantic_report_to_analogy_sources(r); habits=semantic_report_to_habit_observations(r); reasons=semantic_report_to_reason_observations(r); structs=semantic_report_to_structural_identity_objects(r); alc=semantic_report_to_alchemical_trace(r); exps=semantic_report_to_agent_experiences(r); tele=semantic_report_to_route_telemetry_events(r)
 align=check_roadmap_alignment(semantic_sources=r.sources,semantic_claim_segments=r.segments,semantic_claim_classifications=r.classifications,semantic_ambiguities=r.ambiguities,semantic_extractions=r.extractions,formalization_requests=r.formalization_requests,semantic_routing_hints=r.routing_hints,semantic_intake_tasks=r.tasks,semantic_intake_reports=[r],lawbook_entries=laws)
 if a.out_report_json:r.write_json(a.out_report_json)
 if a.out_report_jsonl:r.write_jsonl(a.out_report_jsonl)
 for path,rows in ((a.out_sources_jsonl,r.sources),(a.out_segments_jsonl,r.segments),(a.out_classifications_jsonl,r.classifications),(a.out_ambiguities_jsonl,r.ambiguities),(a.out_extractions_jsonl,r.extractions),(a.out_formalization_requests_jsonl,r.formalization_requests),(a.out_routing_hints_jsonl,r.routing_hints),(a.out_tasks_jsonl,r.tasks),(a.out_formal_world_inputs_jsonl,fw),(a.out_proof_system_inputs_jsonl,ps),(a.out_lawbook_candidates_jsonl,laws),(a.out_continuation_outputs_jsonl,outs),(a.out_discovery_value_scores_jsonl,vals),(a.out_process_episodes_jsonl,eps),(a.out_verifier_feedback_jsonl,fb),(a.out_repair_traces_jsonl,repairs),(a.out_proof_digestion_inputs_jsonl,dig),(a.out_structure_descriptors_jsonl,desc),(a.out_typed_projections_jsonl,typed),(a.out_role_signatures_jsonl,roles),(a.out_analogy_sources_jsonl,analogies),(a.out_habit_observations_jsonl,habits),(a.out_reason_observations_jsonl,reasons),(a.out_structural_objects_jsonl,structs),(a.out_agent_experiences_jsonl,exps),(a.out_route_telemetry_jsonl,tele)):
  if path:_wjl(path,[x.to_dict() if hasattr(x,"to_dict") else x for x in rows])
 if a.out_curriculum_json:cur.write_json(a.out_curriculum_json)
 if a.out_alchemical_trace_json:alc.write_json(a.out_alchemical_trace_json)
 if a.alignment_report_json:align.write_json(a.alignment_report_json)
 if a.alignment_report_md:align.write_markdown(a.alignment_report_md)
 if not any(v for k,v in vars(a).items() if k.startswith("out_") or k.startswith("alignment_report")): sys.stdout.write(r.to_json()+"\n")
 return 1 if a.fail_on_critical and align.critical_count() else 0
def _jl(p,c):
 if not p:return []
 return [json.loads(x) if c is dict else c.from_dict(json.loads(x)) for x in Path(p).read_text().splitlines() if x.strip()]
def _wjl(p,rows): path=Path(p); path.parent.mkdir(parents=True,exist_ok=True); path.write_text("".join(json.dumps(x,sort_keys=True)+"\n" for x in rows))
if __name__=="__main__": raise SystemExit(main())
