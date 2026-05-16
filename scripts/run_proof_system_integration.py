#!/usr/bin/env python
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from mathgraph.proof_system_integration import *
from mathgraph.roadmap_alignment import check_roadmap_alignment
def main(argv=None):
 p=argparse.ArgumentParser()
 p.add_argument("--input-text",action="append",default=[])
 for n in ("input-json","spec-json","artifact-json","project-json","check-result-json","trusted-import-json","formal-world-adapter-report-json","domain-claim-json","proof-digestion-json","repair-trace-json","curriculum-json","lawbook-entry-json","lawbook-query-report-json","structure-report-json","role-report-json","analogy-report-json","reason-report-json","habit-report-json","process-memory-report-json","alchemical-trace-json","raw-event-json"): p.add_argument("--"+n,action="append",default=[])
 for n in ("input-jsonl","spec-jsonl","artifact-jsonl","project-jsonl","check-result-jsonl","trusted-import-jsonl","formal-world-handoffs-jsonl","formal-world-tasks-jsonl","verifier-feedback-jsonl","projection-candidates-jsonl","typed-projections-jsonl","agent-experiences-jsonl","route-telemetry-jsonl","raw-event-jsonl"): p.add_argument("--"+n)
 p.add_argument("--proof-file",action="append",default=[]); p.add_argument("--project-root",action="append",default=[]); p.add_argument("--scan-project-files",action="store_true"); p.add_argument("--max-files",type=int,default=500)
 p.add_argument("--no-default-specs",action="store_true"); p.add_argument("--no-check-requests",action="store_true"); p.add_argument("--no-boundary-evidence",action="store_true"); p.add_argument("--allow-execution",action="store_true")
 for n in ("out-report-json","out-report-jsonl","out-specs-jsonl","out-projects-jsonl","out-artifacts-jsonl","out-import-graphs-jsonl","out-command-contracts-jsonl","out-check-requests-jsonl","out-check-results-jsonl","out-trusted-imports-jsonl","out-boundary-evidence-jsonl","out-tasks-jsonl","out-lawbook-candidates-jsonl","out-continuation-outputs-jsonl","out-curriculum-json","out-discovery-value-scores-jsonl","out-process-episodes-jsonl","out-verifier-feedback-jsonl","out-repair-traces-jsonl","out-proof-digestion-inputs-jsonl","out-structure-descriptors-jsonl","out-typed-projections-jsonl","out-role-signatures-jsonl","out-analogy-sources-jsonl","out-habit-observations-jsonl","out-reason-observations-jsonl","out-structural-objects-jsonl","out-alchemical-trace-json","out-agent-experiences-jsonl","out-route-telemetry-jsonl","alignment-report-json","alignment-report-md"): p.add_argument("--"+n)
 p.add_argument("--fail-on-critical",action="store_true"); a=p.parse_args(argv)
 specs=[_jr(x,ProofSystemSpec) for x in a.spec_json]+_jl(a.spec_jsonl,ProofSystemSpec); arts=[_jr(x,ProofArtifactManifest) for x in a.artifact_json]+_jl(a.artifact_jsonl,ProofArtifactManifest)+[proof_artifact_manifest_from_path(x) for x in a.proof_file]; projs=[_jr(x,ProofProjectManifest) for x in a.project_json]+_jl(a.project_jsonl,ProofProjectManifest); results=[_jr(x,ProofCheckResult) for x in a.check_result_json]+_jl(a.check_result_jsonl,ProofCheckResult); imports=[_jr(x,TrustedProofImportRecord) for x in a.trusted_import_json]+_jl(a.trusted_import_jsonl,TrustedProofImportRecord)
 objs=list(a.input_text)+[json.loads(Path(x).read_text()) for x in a.input_json]+_jl(a.input_jsonl,dict)+[json.loads(Path(x).read_text()) for x in a.raw_event_json]+_jl(a.raw_event_jsonl,dict)
 for root in a.project_root: projs.append(build_proof_project_manifest(root,scan_files=a.scan_project_files,max_files=a.max_files))
 r=build_proof_system_integration_report(objs,specs,arts,projs,results,imports,include_default_specs=not a.no_default_specs,scan_project_files=a.scan_project_files,allow_execution=a.allow_execution,create_check_requests=not a.no_check_requests,create_boundary_evidence=not a.no_boundary_evidence)
 laws=proof_system_report_to_lawbook_candidates(r); outs=proof_system_report_to_continuation_outputs(r); cur=proof_system_report_to_curriculum(r); vals=proof_system_report_to_discovery_value_scores(r); eps=proof_system_report_to_process_episodes(r); fb=proof_system_report_to_verifier_feedback(r); repairs=proof_system_report_to_repair_traces(r); dig=proof_system_report_to_proof_digestion_inputs(r); desc=proof_system_report_to_structure_descriptors(r); typed=proof_system_report_to_typed_projection_candidates(r); roles=proof_system_report_to_role_signatures(r); analogies=proof_system_report_to_analogy_sources(r); habits=proof_system_report_to_habit_observations(r); reasons=proof_system_report_to_reason_observations(r); structs=proof_system_report_to_structural_identity_objects(r); alc=proof_system_report_to_alchemical_trace(r); exps=proof_system_report_to_agent_experiences(r); tele=proof_system_report_to_route_telemetry_events(r)
 align=check_roadmap_alignment(proof_system_specs=r.specs,proof_project_manifests=r.projects,proof_artifact_manifests=r.artifacts,proof_import_graphs=r.import_graphs,proof_check_command_contracts=r.command_contracts,proof_check_requests=r.check_requests,proof_check_results=r.check_results,trusted_proof_import_records=r.trusted_imports,proof_boundary_evidence=r.boundary_evidence,proof_system_tasks=r.tasks,proof_system_integration_reports=[r],lawbook_entries=laws)
 if a.out_report_json:r.write_json(a.out_report_json)
 if a.out_report_jsonl:r.write_jsonl(a.out_report_jsonl)
 for path,rows in ((a.out_specs_jsonl,r.specs),(a.out_projects_jsonl,r.projects),(a.out_artifacts_jsonl,r.artifacts),(a.out_import_graphs_jsonl,r.import_graphs),(a.out_command_contracts_jsonl,r.command_contracts),(a.out_check_requests_jsonl,r.check_requests),(a.out_check_results_jsonl,r.check_results),(a.out_trusted_imports_jsonl,r.trusted_imports),(a.out_boundary_evidence_jsonl,r.boundary_evidence),(a.out_tasks_jsonl,r.tasks),(a.out_lawbook_candidates_jsonl,laws),(a.out_continuation_outputs_jsonl,outs),(a.out_discovery_value_scores_jsonl,vals),(a.out_process_episodes_jsonl,eps),(a.out_verifier_feedback_jsonl,fb),(a.out_repair_traces_jsonl,repairs),(a.out_proof_digestion_inputs_jsonl,dig),(a.out_structure_descriptors_jsonl,desc),(a.out_typed_projections_jsonl,typed),(a.out_role_signatures_jsonl,roles),(a.out_analogy_sources_jsonl,analogies),(a.out_habit_observations_jsonl,habits),(a.out_reason_observations_jsonl,reasons),(a.out_structural_objects_jsonl,structs),(a.out_agent_experiences_jsonl,exps),(a.out_route_telemetry_jsonl,tele)):
  if path:_wjl(path,[x.to_dict() if hasattr(x,"to_dict") else x for x in rows])
 if a.out_curriculum_json:cur.write_json(a.out_curriculum_json)
 if a.out_alchemical_trace_json:alc.write_json(a.out_alchemical_trace_json)
 if a.alignment_report_json:align.write_json(a.alignment_report_json)
 if a.alignment_report_md:align.write_markdown(a.alignment_report_md)
 if not any(v for k,v in vars(a).items() if k.startswith("out_") or k.startswith("alignment_report")): sys.stdout.write(r.to_json()+"\n")
 return 1 if a.fail_on_critical and align.critical_count() else 0
def _jr(p,c): return c.from_json(Path(p).read_text())
def _jl(p,c):
 if not p:return []
 return [json.loads(x) if c is dict else c.from_dict(json.loads(x)) for x in Path(p).read_text().splitlines() if x.strip()]
def _wjl(p,rows): path=Path(p); path.parent.mkdir(parents=True,exist_ok=True); path.write_text("".join(json.dumps(x,sort_keys=True)+"\n" for x in rows))
if __name__=="__main__": raise SystemExit(main())
