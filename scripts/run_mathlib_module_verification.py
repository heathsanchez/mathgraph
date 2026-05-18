#!/usr/bin/env python
from __future__ import annotations
import json,sys
from pathlib import Path
try:
 from _bootstrap import ensure_repo_root_on_path
except ImportError: sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
else: ensure_repo_root_on_path(__file__)
import argparse
from mathgraph.mathlib_module_verification import *
from mathgraph.roadmap_alignment import check_roadmap_alignment
def main(argv=None):
 p=argparse.ArgumentParser(); p.add_argument("--request"); p.add_argument("--project-root"); p.add_argument("--workspace-root"); p.add_argument("--use-synthetic-request",action="store_true"); p.add_argument("--ensure-examples",action="store_true"); p.add_argument("--overwrite-examples",action="store_true"); p.add_argument("--allow-execution",action="store_true"); p.add_argument("--allow-missing-verifier",action="store_true"); p.add_argument("--accept-verified-entries-in-memory",action="store_true"); p.add_argument("--timeout-sec",type=float,default=20.0); p.add_argument("--out-dir"); p.add_argument("--print-json",action="store_true"); p.add_argument("--quiet",action="store_true"); p.add_argument("--fail-on-critical",action="store_true")
 for n in ("out-report-json","out-markdown","out-check-files-jsonl","out-declaration-results-jsonl","out-boundary-evidence-jsonl","out-api-response-json","alignment-report-json","alignment-report-md"): p.add_argument("--"+n)
 a=p.parse_args(argv); ex=Path(__file__).resolve().parents[1]/"examples"/"mathlib_module_verification"
 if a.ensure_examples: ensure_module_verification_examples(ex,overwrite=a.overwrite_examples)
 req=default_synthetic_module_verification_request(a.project_root or Path(__file__).resolve().parents[1]/"examples"/"mathlib_micro_subset") if a.use_synthetic_request else MathlibModuleVerificationRequest.read_json(a.request) if a.request else MathlibModuleVerificationRequest("empty-module-verification-request")
 r=run_mathlib_module_verification(req,project_root=a.project_root,workspace_root=a.workspace_root,allow_execution=a.allow_execution,allow_missing_verifier=a.allow_missing_verifier,accept_verified_entries_in_memory=a.accept_verified_entries_in_memory,timeout_sec=a.timeout_sec); paths=write_mathlib_module_verification_artifacts(r,a.out_dir) if a.out_dir else {}; align=check_roadmap_alignment(mathlib_module_verification_reports=[r])
 if a.out_report_json:r.write_json(a.out_report_json)
 if a.out_markdown:_w(a.out_markdown,mathlib_module_verification_report_to_markdown(r))
 if a.out_check_files_jsonl:_w(a.out_check_files_jsonl,"".join(x.to_json()+"\n" for x in r.check_files))
 if a.out_declaration_results_jsonl:_w(a.out_declaration_results_jsonl,"".join(x.to_json()+"\n" for x in r.declaration_results))
 if a.out_boundary_evidence_jsonl:_w(a.out_boundary_evidence_jsonl,"".join(e.to_json()+"\n" for x in r.declaration_results for e in x.boundary_evidence))
 if a.out_api_response_json:_w(a.out_api_response_json,mathlib_module_verification_report_to_api_response(r).to_json())
 if a.alignment_report_json:align.write_json(a.alignment_report_json)
 if a.alignment_report_md:align.write_markdown(a.alignment_report_md)
 if not a.quiet: print(r.to_json() if a.print_json else concise_summary(r,paths),end="" if not a.print_json else "\n")
 return 1 if a.fail_on_critical and (r.critical_count() or align.critical_count()) else 0
def concise_summary(r,paths):
 s=r.summarize(); return "\n".join(["MathGraph Mathlib Module Verification",f"status: {r.status.value}",f"truth_status: {r.truth_status.value}",f"targets: {s['target_total']}",f"declarations: {s['declaration_total']}",f"verified: {s['verified_total']}",f"known_skips: {s['known_skip_total']}",f"boundary_evidence: {s['boundary_evidence_total']}",f"markdown: {paths.get('markdown','-')}",f"json: {paths.get('report','-')}"])+"\n"
def _w(p,t): path=Path(p); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(t,encoding="utf-8")
if __name__=="__main__": raise SystemExit(main())
