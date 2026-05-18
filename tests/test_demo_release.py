import subprocess,sys
import shutil
from pathlib import Path
from mathgraph.demo_release import *
from mathgraph.roadmap_alignment import check_roadmap_alignment
def test_roundtrips_configs_reports(tmp_path):
 pub,real,cur=ensure_default_demo_release_configs(tmp_path)
 c=load_public_demo_config(pub); rc=load_real_mathlib_revision_demo_config(real); r=run_public_demo(c); rr=run_real_mathlib_revision_demo(rc)
 for x in (c,rc,ReleaseCheckResult("x",DemoReleaseCheckKind.IMPORTS,DemoReleaseCheckStatus.PASS,"x"),r,rr): assert x.from_json(x.to_json()).to_dict()==x.to_dict()
 assert default_public_demo_config_dict()["use_synthetic"] and default_real_mathlib_revision_demo_config_dict()["module_files"] and cur.exists()
 assert r.boundary_evidence_count()==0 and "Boundary Discipline" in public_demo_report_to_markdown(r)
 assert rr.status==DemoReleaseStatus.SKIPPED_ENVIRONMENT and rr.truth_status==DemoReleaseTruthStatus.SKIPPED_NO_ENVIRONMENT
 assert check_roadmap_alignment(public_demo_reports=[r],real_mathlib_revision_reports=[rr]).critical_count()==0
def test_live_bridges_audits_artifacts(tmp_path):
 live=run_public_demo(allow_execution=True,allow_missing_verifier=True); assert live.summary["verified_total"] in {0,10}
 replay=run_public_demo(allow_execution=True,allow_missing_verifier=True,accept_verified_entries_in_memory=True); assert replay.known_skip_count() in {0,10}
 paths=write_public_demo_artifacts(run_public_demo(),tmp_path/"pub"); assert "markdown" in paths
 assert "MathGraph Public Demo" in concise_public_demo_summary(run_public_demo(),paths)
 assert public_demo_report_to_api_response(run_public_demo()).truth_status==ApiTruthStatus.ADVISORY_ONLY
 assert public_demo_report_to_process_episodes(replay) and public_demo_report_to_discovery_value_scores(replay) and public_demo_report_to_structural_identity_objects(replay)
 assert public_demo_report_to_route_telemetry_events(replay) and public_demo_report_to_agent_experiences(replay)
 assert any(x.phase.value=="FIXATION" for x in public_demo_report_to_alchemical_trace(replay).steps) if replay.boundary_evidence_count() else True
 bad=run_public_demo(); bad.truth_status=DemoReleaseTruthStatus.BOUNDARY_EVIDENCE_PRESENT; assert audit_public_demo_report(bad)
 rr=run_real_mathlib_revision_demo(RealMathlibRevisionDemoConfig("x","x",project_root="/missing")); assert not audit_real_mathlib_revision_report(rr)
 assert check_roadmap_alignment(public_demo_reports=[bad]).critical_count()
def test_live_public_demo_missing_lean(monkeypatch):
 monkeypatch.setattr(shutil,"which",lambda name: None if name=="lean" else "/bin/x")
 r=run_public_demo(allow_execution=True,allow_missing_verifier=True,accept_verified_entries_in_memory=True)
 assert r.boundary_evidence_count()==0
def test_cli_notebook(tmp_path):
 subprocess.run([sys.executable,"scripts/run_public_demo.py","--help"],check=True,capture_output=True)
 subprocess.run([sys.executable,"scripts/run_public_demo.py","--ensure-configs"],check=True,capture_output=True)
 subprocess.run([sys.executable,"scripts/run_public_demo.py","--out-report-json",str(tmp_path/"r.json")],check=True)
 subprocess.run([sys.executable,"scripts/run_release_check.py","--quick","--out-report-json",str(tmp_path/"c.json")],check=True)
 assert (tmp_path/"r.json").exists() and (tmp_path/"c.json").exists() and Path("notebooks/mathgraph_public_demo.py").exists()
