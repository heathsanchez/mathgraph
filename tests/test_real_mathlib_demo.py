import subprocess,sys
from pathlib import Path
from mathgraph.api_service import ApiTruthStatus,MathGraphLocalClient
from mathgraph.real_mathlib_demo import *
from mathgraph.roadmap_alignment import check_roadmap_alignment
ROOT=Path(__file__).resolve().parents[1]
def _synthetic_config():
 return RealMathlibDemoConfig("synthetic","Synthetic",project_root="examples/mathlib_micro_subset",require_mathlib_marker=True,discovery_modules=[{"path":"Mathlib/MathGraph/Basic.lean","module_name":"Mathlib.MathGraph.Basic","include_kinds":["theorem","lemma"],"max_declarations":10},{"path":"Mathlib/MathGraph/UseBasic.lean","module_name":"Mathlib.MathGraph.UseBasic","include_kinds":["theorem","lemma"],"max_declarations":10}],selection_policy={"max_total_declarations":10,"prefer_kinds":["theorem","lemma"]})
def test_roundtrips_examples_and_skip(tmp_path):
 c=RealMathlibDemoConfig.from_dict(default_real_mathlib_demo_config_dict()); env=detect_real_mathlib_demo_environment(c); r=run_real_mathlib_demo(c)
 st=RealMathlibDemoStageResult("s","d",RealMathlibDemoStage.CONFIG); p,q=ensure_default_real_mathlib_demo_examples(tmp_path)
 for x in (c,env,st,r): assert x.from_json(x.to_json()).to_dict()==x.to_dict()
 assert p.exists() and q.exists() and load_real_mathlib_demo_config(p).demo_id
 assert r.status==RealMathlibDemoStatus.SKIPPED_ENVIRONMENT and r.boundary_evidence_count()==0 and "Boundary Discipline" in real_mathlib_demo_report_to_markdown(r)
 assert real_mathlib_demo_report_to_api_response(r).truth_status==ApiTruthStatus.ADVISORY_ONLY
 assert check_roadmap_alignment(real_mathlib_demo_reports=[r]).critical_count()==0
 assert write_real_mathlib_demo_artifacts(r,tmp_path/"artifacts")["markdown"]
def test_synthetic_standin_and_audits():
 c=_synthetic_config(); req=build_discovery_request_from_real_mathlib_demo_config(c); dry=run_real_mathlib_demo(c); down=run_real_mathlib_demo(c,run_allowlist_ingestion=True); live=run_real_mathlib_demo(c,run_allowlist_ingestion=True,allow_execution=True,allow_missing_verifier=True); replay=run_real_mathlib_demo(c,run_allowlist_ingestion=True,allow_execution=True,allow_missing_verifier=True,accept_verified_entries_in_memory=True)
 assert req.module_files and dry.module_count()>0 and dry.selected_count()>0 and dry.boundary_evidence_count()==0 and down.boundary_evidence_count()==0
 assert live.verified_count() in {0,dry.selected_count()} and replay.known_skip_count() in {0,replay.verified_count()} and dry.dependency_edge_count()>0
 assert all(live.summary[k]==0 for k in ("unsafe_verified_total","expected_missing_verified_total","import_failure_verified_total"))
 assert real_mathlib_demo_report_to_process_episodes(dry) and real_mathlib_demo_report_to_discovery_value_scores(dry) and real_mathlib_demo_report_to_route_telemetry_events(dry)
 bad=run_real_mathlib_demo(); bad.truth_status=RealMathlibDemoTruthStatus.BOUNDARY_EVIDENCE_PRESENT; assert audit_real_mathlib_demo_report(bad)
 assert audit_real_mathlib_demo_config(RealMathlibDemoConfig("x","x",advisory=False))
 assert check_roadmap_alignment(real_mathlib_demo_reports=[bad]).critical_count()
def test_cli_and_api(tmp_path):
 subprocess.run([sys.executable,"scripts/run_real_mathlib_demo.py","--help"],check=True,capture_output=True)
 subprocess.run([sys.executable,"scripts/run_real_mathlib_demo.py","--ensure-examples"],check=True,capture_output=True)
 subprocess.run([sys.executable,"scripts/run_real_mathlib_demo.py","--out-markdown",str(tmp_path/"r.md")],check=True,capture_output=True)
 assert (tmp_path/"r.md").exists()
 assert MathGraphLocalClient().real_mathlib_demo({}).truth_status==ApiTruthStatus.ADVISORY_ONLY
