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

import argparse,json,sys,tempfile
from pathlib import Path
from mathgraph.roadmap_alignment import check_roadmap_alignment
from mathgraph.verifier_fixtures import *
def main(argv=None):
 p=argparse.ArgumentParser(); p.add_argument("--fixture-root"); p.add_argument("--workspace-root"); p.add_argument("--ensure-fixtures",action="store_true"); p.add_argument("--overwrite-fixtures",action="store_true"); p.add_argument("--allow-execution",action="store_true"); p.add_argument("--allow-missing-verifier",action="store_true"); p.add_argument("--timeout-sec",type=float,default=20.0); p.add_argument("--accept-verified-fixtures-in-memory",action="store_true")
 for n in ("out-suite-json","out-result-json","out-results-jsonl","out-verifier-report-json","out-boundary-evidence-jsonl","out-lawbook-candidates-jsonl","out-lawbook-review-json","out-process-episodes-jsonl","out-route-telemetry-jsonl","out-markdown","out-api-response-json","alignment-report-json","alignment-report-md"): p.add_argument("--"+n)
 p.add_argument("--fail-on-critical",action="store_true"); a=p.parse_args(argv)
 root=Path(a.fixture_root or Path(__file__).resolve().parents[1]/"examples"/"verifier_fixtures"/"lean")
 if a.ensure_fixtures: ensure_default_lean_fixtures(root,overwrite=a.overwrite_fixtures)
 suite=build_default_lean_fixture_suite(root); result=run_verifier_fixture_suite(suite,workspace_root=a.workspace_root or Path(tempfile.gettempdir())/"mathgraph_fixture_tmp",allow_execution=a.allow_execution,allow_missing_verifier=a.allow_missing_verifier,timeout_sec=a.timeout_sec)
 review=review_and_optionally_accept_verified_fixture_evidence(result,accept_in_memory=a.accept_verified_fixtures_in_memory); align=check_roadmap_alignment(verifier_fixtures=suite.fixtures,verifier_fixture_results=result.results,verifier_fixture_suites=[suite],verifier_fixture_suite_results=[result])
 if a.out_suite_json:_w(a.out_suite_json,suite.to_json())
 if a.out_result_json:result.write_json(a.out_result_json)
 if a.out_results_jsonl:_wjl(a.out_results_jsonl,[x.to_dict() for x in result.results])
 if a.out_verifier_report_json and result.verifier_execution_report:result.verifier_execution_report.write_json(a.out_verifier_report_json)
 if a.out_boundary_evidence_jsonl:_wjl(a.out_boundary_evidence_jsonl,[e.to_dict() for x in result.results for e in x.boundary_evidence])
 if a.out_lawbook_candidates_jsonl:_wjl(a.out_lawbook_candidates_jsonl,[x.to_dict() for x in verifier_fixture_suite_result_to_lawbook_candidates(result)])
 if a.out_lawbook_review_json:_w(a.out_lawbook_review_json,json.dumps(review,sort_keys=True))
 if a.out_process_episodes_jsonl:_wjl(a.out_process_episodes_jsonl,[x.to_dict() for x in verifier_fixture_suite_result_to_process_episodes(result)])
 if a.out_route_telemetry_jsonl:_wjl(a.out_route_telemetry_jsonl,verifier_fixture_suite_result_to_route_telemetry_events(result))
 if a.out_markdown:_w(a.out_markdown,verifier_fixture_suite_result_to_markdown(result))
 if a.out_api_response_json:_w(a.out_api_response_json,verifier_fixture_suite_result_to_api_response(result).to_json())
 if a.alignment_report_json:align.write_json(a.alignment_report_json)
 if a.alignment_report_md:align.write_markdown(a.alignment_report_md)
 if not any(v for k,v in vars(a).items() if k.startswith("out_") or k.startswith("alignment_report")): sys.stdout.write(result.to_json()+"\n")
 return 1 if a.fail_on_critical and (result.critical_count() or align.critical_count()) else 0
def _wjl(p,rows): _w(p,"".join(json.dumps(x,sort_keys=True,default=str)+"\n" for x in rows))
def _w(p,t): path=Path(p); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(t,encoding="utf-8")
if __name__=="__main__": raise SystemExit(main())
