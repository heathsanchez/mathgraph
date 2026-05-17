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
from mathgraph.roadmap_alignment import check_roadmap_alignment
from mathgraph.verifier_execution import *
def main(argv=None):
 p=argparse.ArgumentParser(); p.add_argument("--system",default="lean"); p.add_argument("--input-text",action="append",default=[]); p.add_argument("--input-file",action="append",default=[]); p.add_argument("--proof-system-report-json",action="append",default=[]); p.add_argument("--workspace-root"); p.add_argument("--allow-execution",action="store_true"); p.add_argument("--timeout-sec",type=float,default=20); p.add_argument("--include-version-probe",action="store_true"); p.add_argument("--expected-theorem",action="append",default=[])
 for n in ("out-report-json","out-report-jsonl","out-contracts-jsonl","out-requests-jsonl","out-results-jsonl","out-boundary-evidence-jsonl","out-lawbook-candidates-jsonl","out-api-response-json","out-process-episodes-jsonl","out-verifier-feedback-jsonl","out-repair-traces-jsonl","out-proof-digestion-inputs-jsonl","out-discovery-value-scores-jsonl","out-alchemical-trace-json","out-agent-experiences-jsonl","out-route-telemetry-jsonl","alignment-report-json","alignment-report-md"): p.add_argument("--"+n)
 p.add_argument("--fail-on-critical",action="store_true"); a=p.parse_args(argv); root=a.workspace_root; objs=list(a.input_text)+[{"path":x} for x in a.input_file]
 rep=build_verifier_execution_report(objs,workspace_root=root,allow_execution=a.allow_execution,timeout_sec=a.timeout_sec,include_version_probe=a.include_version_probe)
 align=check_roadmap_alignment(verifier_execution_reports=[rep],verifier_execution_results=rep.results,verifier_boundary_evidence=rep.boundary_evidence)
 if a.out_report_json:rep.write_json(a.out_report_json)
 if a.out_report_jsonl:rep.write_jsonl(a.out_report_jsonl)
 for path,rows in ((a.out_contracts_jsonl,rep.contracts),(a.out_requests_jsonl,rep.requests),(a.out_results_jsonl,rep.results),(a.out_boundary_evidence_jsonl,rep.boundary_evidence),(a.out_lawbook_candidates_jsonl,verifier_execution_report_to_lawbook_candidates(rep)),(a.out_process_episodes_jsonl,verifier_execution_report_to_process_episodes(rep)),(a.out_verifier_feedback_jsonl,verifier_execution_report_to_verifier_feedback(rep)),(a.out_repair_traces_jsonl,verifier_execution_report_to_repair_traces(rep)),(a.out_proof_digestion_inputs_jsonl,verifier_execution_report_to_proof_digestion_inputs(rep)),(a.out_discovery_value_scores_jsonl,verifier_execution_report_to_discovery_value_scores(rep)),(a.out_agent_experiences_jsonl,verifier_execution_report_to_agent_experiences(rep)),(a.out_route_telemetry_jsonl,verifier_execution_report_to_route_telemetry_events(rep))):
  if path:_wjl(path,[x.to_dict() if hasattr(x,"to_dict") else x for x in rows])
 if a.out_api_response_json:_w(a.out_api_response_json,verifier_execution_report_to_api_response(rep).to_json())
 if a.out_alchemical_trace_json:_w(a.out_alchemical_trace_json,verifier_execution_report_to_alchemical_trace(rep).to_json())
 if a.alignment_report_json:align.write_json(a.alignment_report_json)
 if a.alignment_report_md:align.write_markdown(a.alignment_report_md)
 if not any(v for k,v in vars(a).items() if k.startswith("out_") or k.startswith("alignment_report")): sys.stdout.write(rep.to_json()+"\n")
 return 1 if a.fail_on_critical and (rep.critical_count() or align.critical_count()) else 0
def _wjl(p,rows): _w(p,"".join(json.dumps(x,sort_keys=True,default=str)+"\n" for x in rows))
def _w(p,t): path=Path(p); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(t)
if __name__=="__main__": raise SystemExit(main())
