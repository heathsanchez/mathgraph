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
import argparse,json
from mathgraph.proof_library_demo import *
from mathgraph.roadmap_alignment import check_roadmap_alignment
def main(argv=None):
 p=argparse.ArgumentParser(); p.add_argument("--config"); p.add_argument("--out-dir"); p.add_argument("--ensure-configs",action="store_true"); p.add_argument("--overwrite-configs",action="store_true"); p.add_argument("--use-synthetic",action="store_true"); p.add_argument("--project-root"); p.add_argument("--allow-execution",action="store_true"); p.add_argument("--allow-missing-verifier",action="store_true"); p.add_argument("--run-allowlist-ingestion",action="store_true"); p.add_argument("--accept-verified-entries-in-memory",action="store_true"); p.add_argument("--timeout-sec",type=float,default=20.0); p.add_argument("--require-mathlib-marker",action="store_true")
 for n in ("out-report-json","out-report-jsonl","out-markdown","out-api-response-json","out-dependency-graph-json","out-process-episodes-jsonl","out-discovery-value-scores-jsonl","out-structural-identity-objects-jsonl","out-route-telemetry-jsonl","out-alchemical-trace-json","out-agent-experiences-jsonl","alignment-report-json","alignment-report-md"): p.add_argument("--"+n)
 p.add_argument("--fail-on-critical",action="store_true"); a=p.parse_args(argv); examples=Path(__file__).resolve().parents[1]/"examples"/"proof_library_demo"
 if a.ensure_configs: ensure_default_proof_library_demo_configs(examples,overwrite=a.overwrite_configs)
 c=load_proof_library_demo_config(a.config) if a.config else build_synthetic_proof_library_demo_config()
 r=run_proof_library_demo(c,out_dir=a.out_dir,project_root=a.project_root,use_synthetic_request=True if a.use_synthetic else None,allow_execution=a.allow_execution,allow_missing_verifier=a.allow_missing_verifier,run_allowlist_ingestion=a.run_allowlist_ingestion,accept_verified_entries_in_memory=a.accept_verified_entries_in_memory,timeout_sec=a.timeout_sec,require_mathlib_marker=a.require_mathlib_marker)
 align=check_roadmap_alignment(proof_library_demo_configs=[c],proof_library_demo_stage_results=r.stage_results,proof_library_demo_reports=[r])
 if a.out_report_json:r.write_json(a.out_report_json)
 if a.out_report_jsonl:r.write_jsonl(a.out_report_jsonl)
 if a.out_markdown:_w(a.out_markdown,proof_library_demo_report_to_markdown(r))
 if a.out_api_response_json:_w(a.out_api_response_json,proof_library_demo_report_to_api_response(r).to_json())
 if a.out_dependency_graph_json:_w(a.out_dependency_graph_json,_j(proof_library_demo_report_to_dependency_graph(r)))
 for path,rows in ((a.out_process_episodes_jsonl,proof_library_demo_report_to_process_episodes(r)),(a.out_discovery_value_scores_jsonl,proof_library_demo_report_to_discovery_value_scores(r)),(a.out_agent_experiences_jsonl,proof_library_demo_report_to_agent_experiences(r))):
  if path:_wjl(path,[x.to_dict() for x in rows])
 if a.out_structural_identity_objects_jsonl:_wjl(a.out_structural_identity_objects_jsonl,proof_library_demo_report_to_structural_identity_objects(r))
 if a.out_route_telemetry_jsonl:_wjl(a.out_route_telemetry_jsonl,proof_library_demo_report_to_route_telemetry_events(r))
 if a.out_alchemical_trace_json:_w(a.out_alchemical_trace_json,proof_library_demo_report_to_alchemical_trace(r).to_json())
 if a.alignment_report_json:align.write_json(a.alignment_report_json)
 if a.alignment_report_md:align.write_markdown(a.alignment_report_md)
 if not any(v for k,v in vars(a).items() if k.startswith("out_") or k.startswith("alignment_report")): sys.stdout.write(r.to_json()+"\n")
 return 1 if a.fail_on_critical and (r.critical_count() or align.critical_count()) else 0
def _wjl(p,rows): _w(p,"".join(json.dumps(x,sort_keys=True,default=str)+"\n" for x in rows))
def _j(x): return json.dumps(x,sort_keys=True,separators=(",",":"),default=str)
def _w(p,t): path=Path(p); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(t,encoding="utf-8")
if __name__=="__main__": raise SystemExit(main())
