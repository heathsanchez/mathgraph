#!/usr/bin/env python
from __future__ import annotations
import sys
from pathlib import Path
try:
 from _bootstrap import ensure_repo_root_on_path
except ImportError: sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
else: ensure_repo_root_on_path(__file__)
import argparse
from mathgraph.demo_release import *
from mathgraph.roadmap_alignment import check_roadmap_alignment
def main(argv=None):
 p=argparse.ArgumentParser(); p.add_argument("--config"); p.add_argument("--out-dir"); p.add_argument("--ensure-configs",action="store_true"); p.add_argument("--overwrite-configs",action="store_true"); p.add_argument("--allow-execution",action="store_true"); p.add_argument("--allow-missing-verifier",action="store_true"); p.add_argument("--accept-verified-entries-in-memory",action="store_true"); p.add_argument("--timeout-sec",type=float,default=20.0); p.add_argument("--print-json",action="store_true"); p.add_argument("--quiet",action="store_true"); p.add_argument("--summary-only",action="store_true")
 for n in ("out-report-json","out-markdown","out-api-response-json","alignment-report-json","alignment-report-md"): p.add_argument("--"+n)
 p.add_argument("--fail-on-critical",action="store_true"); a=p.parse_args(argv); root=Path(__file__).resolve().parents[1]/"examples"
 if a.ensure_configs: ensure_default_demo_release_configs(root,overwrite=a.overwrite_configs)
 c=load_public_demo_config(a.config) if a.config else None; r=run_public_demo(c,out_dir=a.out_dir,allow_execution=a.allow_execution,allow_missing_verifier=a.allow_missing_verifier,accept_verified_entries_in_memory=a.accept_verified_entries_in_memory,timeout_sec=a.timeout_sec); align=check_roadmap_alignment(public_demo_reports=[r]); paths=write_public_demo_artifacts(r,a.out_dir) if a.out_dir else {}
 if a.out_report_json:r.write_json(a.out_report_json)
 if a.out_markdown:_w(a.out_markdown,public_demo_report_to_markdown(r))
 if a.out_api_response_json:_w(a.out_api_response_json,public_demo_report_to_api_response(r).to_json())
 if a.alignment_report_json:align.write_json(a.alignment_report_json)
 if a.alignment_report_md:align.write_markdown(a.alignment_report_md)
 if not a.quiet:
  if a.print_json: print(r.to_json())
  else: print(concise_public_demo_summary(r,paths),end="")
 return 1 if a.fail_on_critical and (r.critical_count() or align.critical_count()) else 0
def _w(p,t): path=Path(p); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(t,encoding="utf-8")
if __name__=="__main__": raise SystemExit(main())
