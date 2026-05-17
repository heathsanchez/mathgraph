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
from mathgraph.hardening import *
from mathgraph.roadmap_alignment import check_roadmap_alignment
def main(argv=None):
 p=argparse.ArgumentParser(); p.add_argument("--repo-root"); p.add_argument("--artifact-dir"); p.add_argument("--include-cli",action="store_true"); p.add_argument("--include-slow-cli",action="store_true"); p.add_argument("--performance",action=argparse.BooleanOptionalAction,default=True); p.add_argument("--full-pipeline",action=argparse.BooleanOptionalAction,default=True); p.add_argument("--verifier-execution",action=argparse.BooleanOptionalAction,default=True); p.add_argument("--include-rich-verifier-fixtures",action=argparse.BooleanOptionalAction,default=True); p.add_argument("--include-verified-corpus",action=argparse.BooleanOptionalAction,default=True); p.add_argument("--include-lean-project-subset",action=argparse.BooleanOptionalAction,default=True); p.add_argument("--extra-object-json",action="append",default=[]); p.add_argument("--extra-object-jsonl")
 for n in ("out-report-json","out-report-jsonl","out-findings-jsonl","out-scenarios-jsonl","out-cli-results-jsonl","out-replay-manifest-json","out-api-response-json","out-process-episodes-jsonl","out-discovery-value-scores-jsonl","out-agent-experiences-jsonl","out-alchemical-trace-json","out-route-telemetry-jsonl","out-lawbook-candidates-jsonl","alignment-report-json","alignment-report-md"): p.add_argument("--"+n)
 p.add_argument("--fail-on-critical",action="store_true"); a=p.parse_args(argv); extra=[json.loads(Path(x).read_text()) for x in a.extra_object_json]+_jl(a.extra_object_jsonl)
 r=build_hardening_report(repo_root=a.repo_root,include_cli=a.include_cli or a.include_slow_cli,include_slow_cli=a.include_slow_cli,include_performance=a.performance,include_full_pipeline=a.full_pipeline,include_verifier_execution=a.verifier_execution,include_rich_verifier_fixtures=a.include_rich_verifier_fixtures,include_verified_corpus=a.include_verified_corpus,include_lean_project_subset=a.include_lean_project_subset,extra_objects=extra,artifact_dir=a.artifact_dir)
 bridges=[hardening_report_to_process_episodes(r),hardening_report_to_discovery_value_scores(r),hardening_report_to_agent_experiences(r),hardening_report_to_route_telemetry_events(r),hardening_report_to_lawbook_candidates(r)]
 align=check_roadmap_alignment(hardening_findings=r.findings,hardening_scenarios=r.scenarios,hardening_cli_results=r.cli_results,hardening_replay_manifests=[r.replay_manifest] if r.replay_manifest else [],hardening_reports=[r])
 if a.out_report_json:r.write_json(a.out_report_json)
 if a.out_report_jsonl:r.write_jsonl(a.out_report_jsonl)
 for path,rows in ((a.out_findings_jsonl,r.findings),(a.out_scenarios_jsonl,r.scenarios),(a.out_cli_results_jsonl,r.cli_results),(a.out_process_episodes_jsonl,bridges[0]),(a.out_discovery_value_scores_jsonl,bridges[1]),(a.out_agent_experiences_jsonl,bridges[2]),(a.out_route_telemetry_jsonl,bridges[3]),(a.out_lawbook_candidates_jsonl,bridges[4])):
  if path:_wjl(path,[x.to_dict() if hasattr(x,"to_dict") else x for x in rows])
 if a.out_replay_manifest_json and r.replay_manifest:r.replay_manifest.write_json(a.out_replay_manifest_json)
 if a.out_api_response_json:_w(a.out_api_response_json,hardening_report_to_api_response(r).to_json())
 if a.out_alchemical_trace_json:_w(a.out_alchemical_trace_json,hardening_report_to_alchemical_trace(r).to_json())
 if a.alignment_report_json:align.write_json(a.alignment_report_json)
 if a.alignment_report_md:align.write_markdown(a.alignment_report_md)
 if not any(v for k,v in vars(a).items() if k.startswith("out_") or k.startswith("alignment_report")): sys.stdout.write(r.to_json()+"\n")
 return 1 if a.fail_on_critical and (r.critical_count() or r.fail_count()) else 0
def _jl(p): return [] if not p else [json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]
def _wjl(p,rows): _w(p,"".join(json.dumps(x,sort_keys=True,default=str)+"\n" for x in rows))
def _w(p,t): path=Path(p); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(t)
if __name__=="__main__": raise SystemExit(main())
