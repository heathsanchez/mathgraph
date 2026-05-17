#!/usr/bin/env python
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from mathgraph.e2e_testdrive import *
from mathgraph.roadmap_alignment import check_roadmap_alignment
def main(argv=None):
 p=argparse.ArgumentParser(); p.add_argument("--mode",default="advisory-only"); p.add_argument("--workspace-root"); p.add_argument("--artifact-dir"); p.add_argument("--allow-execution",action="store_true"); p.add_argument("--allow-missing-verifier",action="store_true"); p.add_argument("--hardening",action=argparse.BooleanOptionalAction,default=True)
 for n in ("out-report-json","out-steps-jsonl","out-artifacts-jsonl","out-verifier-report-json","out-boundary-evidence-jsonl","out-hardening-report-json","out-api-response-json","alignment-report-json","alignment-report-md"): p.add_argument("--"+n)
 p.add_argument("--fail-on-critical",action="store_true"); a=p.parse_args(argv); mode=E2ETestDriveMode[a.mode.upper().replace("-","_")]
 r=run_e2e_testdrive(mode=mode,workspace_root=a.workspace_root,allow_execution=a.allow_execution,allow_missing_verifier=a.allow_missing_verifier,include_hardening=a.hardening,artifact_dir=a.artifact_dir)
 align=check_roadmap_alignment(e2e_testdrive_steps=r.steps,e2e_testdrive_reports=[r])
 if a.out_report_json:r.write_json(a.out_report_json)
 if a.out_steps_jsonl:_wjl(a.out_steps_jsonl,[x.to_dict() for x in r.steps])
 if a.out_artifacts_jsonl:_wjl(a.out_artifacts_jsonl,r.artifacts)
 if a.out_verifier_report_json and r.verifier_execution_report:r.verifier_execution_report.write_json(a.out_verifier_report_json)
 if a.out_boundary_evidence_jsonl:_wjl(a.out_boundary_evidence_jsonl,[x.to_dict() for x in r.boundary_evidence])
 if a.out_hardening_report_json and r.hardening_report:r.hardening_report.write_json(a.out_hardening_report_json)
 if a.out_api_response_json and r.api_response:Path(a.out_api_response_json).write_text(r.api_response.to_json())
 if a.alignment_report_json:align.write_json(a.alignment_report_json)
 if a.alignment_report_md:align.write_markdown(a.alignment_report_md)
 if not any(v for k,v in vars(a).items() if k.startswith("out_") or k.startswith("alignment_report")): sys.stdout.write(r.to_json()+"\n")
 return 1 if a.fail_on_critical and (r.critical_count() or align.critical_count()) else 0
def _wjl(p,rows): path=Path(p); path.parent.mkdir(parents=True,exist_ok=True); path.write_text("".join(json.dumps(x,sort_keys=True,default=str)+"\n" for x in rows))
if __name__=="__main__": raise SystemExit(main())
