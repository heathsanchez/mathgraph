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
import argparse,json,tempfile
from mathgraph.mathlib_local_allowlist import *
from mathgraph.roadmap_alignment import check_roadmap_alignment
def main(argv=None):
 p=argparse.ArgumentParser(); p.add_argument("--manifest"); p.add_argument("--project-root"); p.add_argument("--ensure-examples",action="store_true"); p.add_argument("--overwrite-examples",action="store_true"); p.add_argument("--use-synthetic-external",action="store_true"); p.add_argument("--workspace-root"); p.add_argument("--allow-execution",action="store_true"); p.add_argument("--allow-missing-verifier",action="store_true"); p.add_argument("--timeout-sec",type=float,default=20.0); p.add_argument("--accept-verified-entries-in-memory",action="store_true"); p.add_argument("--require-lake",action="store_true"); p.add_argument("--require-mathlib-marker",action="store_true")
 for n in ("out-manifest-json","out-environment-json","out-report-json","out-report-jsonl","out-files-jsonl","out-entries-jsonl","out-dependency-edges-jsonl","out-dependency-graph-json","out-dependency-graph-jsonl","out-lawbook-candidates-jsonl","out-lawbook-replay-json","out-proof-digestion-inputs-jsonl","out-process-episodes-jsonl","out-discovery-value-scores-jsonl","out-structural-identity-objects-jsonl","out-route-telemetry-jsonl","out-alchemical-trace-json","out-agent-experiences-jsonl","out-mathlib-micro-report-json","out-lean-project-report-json","out-verified-corpus-report-json","out-markdown","out-api-response-json","alignment-report-json","alignment-report-md"): p.add_argument("--"+n)
 p.add_argument("--fail-on-critical",action="store_true"); a=p.parse_args(argv); root=Path(__file__).resolve().parents[1]/"examples"/"mathlib_local_allowlist"
 if a.ensure_examples: ensure_default_mathlib_local_allowlist_examples(root,overwrite=a.overwrite_examples)
 if a.manifest: m=load_mathlib_local_allowlist_manifest(a.manifest)
 elif a.use_synthetic_external: m=build_synthetic_external_allowlist_manifest()
 else: m=MathlibLocalAllowlistManifest.from_dict({"manifest_id":make_mathlib_local_manifest_id("template"),**default_mathlib_local_allowlist_manifest_dict()})
 r=ingest_mathlib_local_allowlist(m,project_root=a.project_root,workspace_root=a.workspace_root or Path(tempfile.gettempdir())/"mathgraph_mathlib_local_tmp",allow_execution=a.allow_execution,allow_missing_verifier=a.allow_missing_verifier,timeout_sec=a.timeout_sec,accept_verified_entries_in_memory=a.accept_verified_entries_in_memory,require_lake=a.require_lake,require_mathlib_marker=a.require_mathlib_marker)
 align=check_roadmap_alignment(mathlib_local_manifests=[m],mathlib_environment_reports=[r.environment_report] if r.environment_report else [],mathlib_local_files=r.files,mathlib_local_entries=r.entries,mathlib_local_dependency_edges=r.dependency_edges,mathlib_local_reports=[r])
 if a.out_manifest_json:m.write_json(a.out_manifest_json)
 if a.out_environment_json and r.environment_report:_w(a.out_environment_json,r.environment_report.to_json())
 if a.out_report_json:r.write_json(a.out_report_json)
 if a.out_report_jsonl:r.write_jsonl(a.out_report_jsonl)
 for path,rows in ((a.out_files_jsonl,r.files),(a.out_entries_jsonl,r.entries),(a.out_dependency_edges_jsonl,r.dependency_edges),(a.out_lawbook_candidates_jsonl,mathlib_local_report_to_lawbook_candidates(r)),(a.out_process_episodes_jsonl,mathlib_local_report_to_process_episodes(r)),(a.out_discovery_value_scores_jsonl,mathlib_local_report_to_discovery_value_scores(r)),(a.out_agent_experiences_jsonl,mathlib_local_report_to_agent_experiences(r))):
  if path:_wjl(path,[x.to_dict() for x in rows])
 if a.out_dependency_graph_json: write_dependency_graph_json(r,a.out_dependency_graph_json)
 if a.out_dependency_graph_jsonl: write_dependency_graph_jsonl(r,a.out_dependency_graph_jsonl)
 if a.out_lawbook_replay_json:_w(a.out_lawbook_replay_json,json.dumps(r.lawbook_replay_summary,sort_keys=True))
 if a.out_proof_digestion_inputs_jsonl:_wjl(a.out_proof_digestion_inputs_jsonl,mathlib_local_report_to_proof_digestion_inputs(r))
 if a.out_structural_identity_objects_jsonl:_wjl(a.out_structural_identity_objects_jsonl,mathlib_local_report_to_structural_identity_objects(r))
 if a.out_route_telemetry_jsonl:_wjl(a.out_route_telemetry_jsonl,mathlib_local_report_to_route_telemetry_events(r))
 if a.out_alchemical_trace_json:_w(a.out_alchemical_trace_json,mathlib_local_report_to_alchemical_trace(r).to_json())
 if a.out_mathlib_micro_report_json: mathlib_local_report_to_mathlib_micro_report(r).write_json(a.out_mathlib_micro_report_json)
 if a.out_lean_project_report_json: mathlib_local_report_to_lean_project_report(r).write_json(a.out_lean_project_report_json)
 if a.out_verified_corpus_report_json: mathlib_local_report_to_verified_corpus_report(r).write_json(a.out_verified_corpus_report_json)
 if a.out_markdown:_w(a.out_markdown,mathlib_local_report_to_markdown(r))
 if a.out_api_response_json:_w(a.out_api_response_json,mathlib_local_report_to_api_response(r).to_json())
 if a.alignment_report_json:align.write_json(a.alignment_report_json)
 if a.alignment_report_md:align.write_markdown(a.alignment_report_md)
 if not any(v for k,v in vars(a).items() if k.startswith("out_") or k.startswith("alignment_report")): sys.stdout.write(r.to_json()+"\n")
 return 1 if a.fail_on_critical and (r.critical_count() or align.critical_count()) else 0
def _wjl(p,rows): _w(p,"".join(json.dumps(x,sort_keys=True,default=str)+"\n" for x in rows))
def _w(p,t): path=Path(p); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(t,encoding="utf-8")
if __name__=="__main__": raise SystemExit(main())
