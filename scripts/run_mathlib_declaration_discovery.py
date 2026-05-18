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
from mathgraph.mathlib_declaration_discovery import *
from mathgraph.roadmap_alignment import check_roadmap_alignment
def main(argv=None):
 p=argparse.ArgumentParser(); p.add_argument("--request"); p.add_argument("--project-root"); p.add_argument("--ensure-examples",action="store_true"); p.add_argument("--overwrite-examples",action="store_true"); p.add_argument("--use-synthetic-request",action="store_true"); p.add_argument("--build-manifest",action="store_true"); p.add_argument("--run-allowlist-ingestion",action="store_true"); p.add_argument("--allow-execution",action="store_true"); p.add_argument("--allow-missing-verifier",action="store_true"); p.add_argument("--timeout-sec",type=float,default=20.0); p.add_argument("--accept-verified-entries-in-memory",action="store_true"); p.add_argument("--require-mathlib-marker",action="store_true")
 for n in ("out-request-json","out-report-json","out-report-jsonl","out-modules-jsonl","out-declarations-jsonl","out-reference-hints-jsonl","out-generated-manifest-json","out-allowlist-ingestion-report-json","out-reference-graph-json","out-reference-graph-jsonl","out-proof-digestion-inputs-jsonl","out-process-episodes-jsonl","out-discovery-value-scores-jsonl","out-structural-identity-objects-jsonl","out-route-telemetry-jsonl","out-alchemical-trace-json","out-agent-experiences-jsonl","out-markdown","out-api-response-json","alignment-report-json","alignment-report-md"): p.add_argument("--"+n)
 p.add_argument("--fail-on-critical",action="store_true"); a=p.parse_args(argv); examples=Path(__file__).resolve().parents[1]/"examples"/"mathlib_declaration_discovery"
 if a.ensure_examples: ensure_default_mathlib_discovery_examples(examples,overwrite=a.overwrite_examples)
 req=load_mathlib_discovery_request(a.request) if a.request else build_synthetic_mathlib_discovery_request() if a.use_synthetic_request else MathlibDiscoveryRequest.from_dict(default_mathlib_discovery_request_dict())
 r=run_mathlib_declaration_discovery(req,project_root=a.project_root,build_manifest=a.build_manifest or a.run_allowlist_ingestion,run_allowlist_ingestion=a.run_allowlist_ingestion,allow_execution=a.allow_execution,allow_missing_verifier=a.allow_missing_verifier,timeout_sec=a.timeout_sec,accept_verified_entries_in_memory=a.accept_verified_entries_in_memory,require_mathlib_marker=a.require_mathlib_marker)
 align=check_roadmap_alignment(mathlib_discovery_requests=[req],mathlib_discovered_modules=r.modules,mathlib_discovered_declarations=r.declarations,mathlib_reference_hints=r.reference_hints,mathlib_discovery_reports=[r])
 if a.out_request_json:req.write_json(a.out_request_json)
 if a.out_report_json:r.write_json(a.out_report_json)
 if a.out_report_jsonl:r.write_jsonl(a.out_report_jsonl)
 for path,rows in ((a.out_modules_jsonl,r.modules),(a.out_declarations_jsonl,r.declarations),(a.out_reference_hints_jsonl,r.reference_hints),(a.out_process_episodes_jsonl,mathlib_discovery_report_to_process_episodes(r)),(a.out_discovery_value_scores_jsonl,mathlib_discovery_report_to_discovery_value_scores(r)),(a.out_agent_experiences_jsonl,mathlib_discovery_report_to_agent_experiences(r))):
  if path:_wjl(path,[x.to_dict() for x in rows])
 if a.out_generated_manifest_json and r.generated_manifest: write_generated_allowlist_manifest(r,a.out_generated_manifest_json)
 if a.out_allowlist_ingestion_report_json and r.allowlist_ingestion_report:r.allowlist_ingestion_report.write_json(a.out_allowlist_ingestion_report_json)
 if a.out_reference_graph_json: write_reference_graph_json(r,a.out_reference_graph_json)
 if a.out_reference_graph_jsonl: write_reference_graph_jsonl(r,a.out_reference_graph_jsonl)
 if a.out_proof_digestion_inputs_jsonl:_wjl(a.out_proof_digestion_inputs_jsonl,mathlib_discovery_report_to_proof_digestion_inputs(r))
 if a.out_structural_identity_objects_jsonl:_wjl(a.out_structural_identity_objects_jsonl,mathlib_discovery_report_to_structural_identity_objects(r))
 if a.out_route_telemetry_jsonl:_wjl(a.out_route_telemetry_jsonl,mathlib_discovery_report_to_route_telemetry_events(r))
 if a.out_alchemical_trace_json:_w(a.out_alchemical_trace_json,mathlib_discovery_report_to_alchemical_trace(r).to_json())
 if a.out_markdown:_w(a.out_markdown,mathlib_discovery_report_to_markdown(r))
 if a.out_api_response_json:_w(a.out_api_response_json,mathlib_discovery_report_to_api_response(r).to_json())
 if a.alignment_report_json:align.write_json(a.alignment_report_json)
 if a.alignment_report_md:align.write_markdown(a.alignment_report_md)
 if not any(v for k,v in vars(a).items() if k.startswith("out_") or k.startswith("alignment_report")): sys.stdout.write(r.to_json()+"\n")
 return 1 if a.fail_on_critical and (r.critical_count() or align.critical_count()) else 0
def _wjl(p,rows): _w(p,"".join(json.dumps(x,sort_keys=True,default=str)+"\n" for x in rows))
def _w(p,t): path=Path(p); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(t,encoding="utf-8")
if __name__=="__main__": raise SystemExit(main())
