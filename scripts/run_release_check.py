#!/usr/bin/env python
from __future__ import annotations
import sys,json
from pathlib import Path
try:
 from _bootstrap import ensure_repo_root_on_path
except ImportError: sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
else: ensure_repo_root_on_path(__file__)
import argparse
from datetime import datetime,timezone
from mathgraph.demo_release import *
def main(argv=None):
 p=argparse.ArgumentParser(); p.add_argument("--out-dir"); p.add_argument("--quick",action="store_true"); p.add_argument("--include-public-demo",action="store_true"); p.add_argument("--allow-live-verifier",action="store_true"); p.add_argument("--allow-missing-verifier",action="store_true"); p.add_argument("--out-report-json"); p.add_argument("--out-markdown"); p.add_argument("--fail-on-critical",action="store_true"); a=p.parse_args(argv); checks=run_release_checks(include_public_demo=a.include_public_demo,allow_live_verifier=a.allow_live_verifier,allow_missing_verifier=a.allow_missing_verifier); ok=all(x.ok() for x in checks); report={"created_at":datetime.now(timezone.utc).isoformat(),"advisory":True,"checks":[x.to_dict() for x in checks],"summary":{"check_total":len(checks),"pass_total":sum(x.status==DemoReleaseCheckStatus.PASS for x in checks),"critical_total":sum(len(x.criticals) for x in checks)}}
 if a.out_dir:
  out=Path(a.out_dir); _w(out/"release_check_report.json",json.dumps(report,sort_keys=True)+"\n"); _w(out/"release_check_report.md",_md(report))
 if a.out_report_json:_w(a.out_report_json,json.dumps(report,sort_keys=True)+"\n")
 if a.out_markdown:_w(a.out_markdown,_md(report))
 if not (a.out_report_json or a.out_markdown or a.out_dir): print(json.dumps(report,sort_keys=True))
 return 1 if a.fail_on_critical and not ok else 0
def _md(r): return "\n".join(["# Release Check","", "Release checks are advisory; success is not proof.","",*[f"- {x['name']}: {x['status']}" for x in r["checks"]]])+"\n"
def _w(p,t): path=Path(p); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(t,encoding="utf-8")
if __name__=="__main__": raise SystemExit(main())
