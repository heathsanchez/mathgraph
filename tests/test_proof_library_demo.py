import subprocess,sys
from mathgraph.proof_library_demo import *
from mathgraph.roadmap_alignment import check_roadmap_alignment
def test_roundtrip_configs_and_run(tmp_path):
 c=build_synthetic_proof_library_demo_config(); r=run_proof_library_demo(c); st=r.stage_results[0]
 for x in (c,st,r): assert x.from_json(x.to_json()).to_dict()==x.to_dict()
 assert default_synthetic_proof_library_demo_config_dict()["use_synthetic_request"]
 assert default_real_mathlib_demo_config_dict()["module_files"]
 a,b=ensure_default_proof_library_demo_configs(tmp_path/"configs"); assert a.exists() and b.exists() and load_proof_library_demo_config(a).demo_id
 assert r.module_count()==5 and r.declaration_count()==10 and r.selected_count()==10 and r.generated_manifest_file_count()==5
 assert r.boundary_evidence_count()==0 and r.dependency_edge_count()>0
 assert "## Boundary Discipline" in proof_library_demo_report_to_markdown(r)
 assert proof_library_demo_report_to_api_response(r).truth_status==ApiTruthStatus.ADVISORY_ONLY
 assert check_roadmap_alignment(proof_library_demo_reports=[r]).critical_count()==0
def test_downstream_bridges_audits_and_artifacts(tmp_path):
 dry=run_proof_library_demo(run_allowlist_ingestion=True); assert dry.boundary_evidence_count()==0
 live=run_proof_library_demo(run_allowlist_ingestion=True,allow_execution=True,allow_missing_verifier=True)
 assert live.downstream_verified_count() in {0,10}
 replay=run_proof_library_demo(run_allowlist_ingestion=True,allow_execution=True,allow_missing_verifier=True,accept_verified_entries_in_memory=True)
 assert replay.known_skip_count() in {0,10}
 assert replay.summary["unsafe_verified_total"]==replay.summary["expected_missing_verified_total"]==replay.summary["import_failure_verified_total"]==0
 paths=write_proof_library_demo_artifacts(dry,tmp_path/"artifacts"); assert {"config","demo_markdown","dependency_graph"}<=set(paths)
 assert proof_library_demo_report_to_process_episodes(dry) and proof_library_demo_report_to_discovery_value_scores(dry) and proof_library_demo_report_to_structural_identity_objects(dry)
 assert proof_library_demo_report_to_route_telemetry_events(dry) and proof_library_demo_report_to_agent_experiences(dry)
 assert not any(x.phase.value=="FIXATION" for x in proof_library_demo_report_to_alchemical_trace(dry).steps)
 bad=run_proof_library_demo(run_allowlist_ingestion=False); bad.truth_status=ProofLibraryDemoTruthStatus.BOUNDARY_EVIDENCE_PRESENT; assert audit_proof_library_demo_report(bad)
 assert audit_proof_library_demo_config(ProofLibraryDemoConfig("x","x",advisory=False))
 assert check_roadmap_alignment(proof_library_demo_reports=[bad]).critical_count()
def test_cli(tmp_path):
 md=tmp_path/"demo.md"; graph=tmp_path/"graph.json"; subprocess.run([sys.executable,"scripts/run_proof_library_demo.py","--ensure-configs"],check=True)
 subprocess.run([sys.executable,"scripts/run_proof_library_demo.py","--use-synthetic","--run-allowlist-ingestion","--out-markdown",str(md),"--out-dependency-graph-json",str(graph)],check=True)
 assert md.exists() and graph.exists()
