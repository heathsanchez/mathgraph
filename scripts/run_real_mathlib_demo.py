#!/usr/bin/env python
from __future__ import annotations
import sys
from pathlib import Path
try:
 from _bootstrap import ensure_repo_root_on_path
except ImportError: sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
else: ensure_repo_root_on_path(__file__)
import argparse
from mathgraph.real_mathlib_demo import *
from mathgraph.roadmap_alignment import check_roadmap_alignment
def main(argv=None):
 p=argparse.ArgumentParser(); p.add_argument("--config"); p.add_argument("--project-root"); p.add_argument("--out-dir"); p.add_argument("--ensure-examples",action="store_true"); p.add_argument("--overwrite-examples",action="store_true"); p.add_argument("--allow-execution",action="store_true"); p.add_argument("--allow-missing-verifier",action="store_true"); p.add_argument("--run-allowlist-ingestion",action="store_true"); p.add_argument("--accept-verified-entries-in-memory",action="store_true"); p.add_argument("--timeout-sec",type=float,default=20.0)
 for n in ("out-report-json","out-markdown","out-environment-json","out-generated-manifest-json","out-discovery-report-json","out-allowlist-ingestion-report-json","out-reference-graph-json","out-api-response-json","alignment-report-json","alignment-report-md"): p.add_argument("--"+n)
 p.add_argument("--fail-on-critical",action="store_true"); a=p.parse_args(argv); ex=Path(__file__).resolve().parents[1]/"examples"/"real_mathlib_demo"
 if a.ensure_examples: ensure_default_real_mathlib_demo_examples(ex,overwrite=a.overwrite_examples)
 c=load_real_mathlib_demo_config(a.config) if a.config else None; r=run_real_mathlib_demo(c,project_root=a.project_root,out_dir=a.out_dir,allow_execution=a.allow_execution,allow_missing_verifier=a.allow_missing_verifier,run_allowlist_ingestion=a.run_allowlist_ingestion,accept_verified_entries_in_memory=a.accept_verified_entries_in_memory,timeout_sec=a.timeout_sec); align=check_roadmap_alignment(real_mathlib_demo_reports=[r])
 if a.out_report_json:r.write_json(a.out_report_json)
 if a.out_markdown:_w(a.out_markdown,real_mathlib_demo_report_to_markdown(r))
 if a.out_environment_json and r.environment_report:_w(a.out_environment_json,r.environment_report.to_json())
 if a.out_generated_manifest_json and r.generated_manifest:r.generated_manifest.write_json(a.out_generated_manifest_json)
 if a.out_discovery_report_json and r.discovery_report:r.discovery_report.write_json(a.out_discovery_report_json)
 if a.out_allowlist_ingestion_report_json and r.allowlist_ingestion_report:r.allowlist_ingestion_report.write_json(a.out_allowlist_ingestion_report_json)
 if a.out_reference_graph_json:_w(a.out_reference_graph_json,_j(real_mathlib_demo_report_to_reference_graph(r)))
 if a.out_api_response_json:_w(a.out_api_response_json,real_mathlib_demo_report_to_api_response(r).to_json())
 if a.alignment_report_json:align.write_json(a.alignment_report_json)
 if a.alignment_report_md:align.write_markdown(a.alignment_report_md)
 print(r.to_json())
 return 1 if a.fail_on_critical and (r.critical_count() or align.critical_count()) else 0
def _j(x): return json.dumps(x,sort_keys=True,separators=(",",":"),default=str)
def _w(p,t): path=Path(p); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(t,encoding="utf-8")
import json
if __name__=="__main__": raise SystemExit(main())
