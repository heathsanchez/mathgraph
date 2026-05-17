import subprocess,sys
from mathgraph.e2e_testdrive import *
from mathgraph.roadmap_alignment import check_roadmap_alignment
def test_roundtrip_and_advisory_drive(tmp_path):
 s=E2ETestDriveStep("s",E2EStepKind.SEMANTIC_INTAKE); r=run_e2e_testdrive(workspace_root=tmp_path)
 assert s.from_json(s.to_json()).to_dict()==s.to_dict()
 assert r.from_json(r.to_json()).to_dict()==r.to_dict()
 kinds={x.step_kind for x in r.steps}; assert {E2EStepKind.SEMANTIC_INTAKE,E2EStepKind.FORMAL_WORLD_ADAPTER,E2EStepKind.PROOF_SYSTEM_INTEGRATION,E2EStepKind.VERIFIER_EXECUTION,E2EStepKind.API_SUBMIT,E2EStepKind.AGENT_ECOLOGY,E2EStepKind.HARDENING,E2EStepKind.FINAL_AUDIT}<=kinds
 assert r.ok() and not r.boundary_evidence and r.hardening_report.ok()
 assert check_roadmap_alignment(e2e_testdrive_reports=[r]).critical_count()==0
def test_live_mode_and_audits(tmp_path):
 r=run_e2e_testdrive(mode=E2ETestDriveMode.LIVE_VERIFIER,workspace_root=tmp_path,allow_execution=True,allow_missing_verifier=True); assert r.ok()
 bad=run_e2e_testdrive(workspace_root=tmp_path/"bad"); bad.boundary_evidence=[VerifierBoundaryEvidence("e",result_id="r",certificate_id="c",terminal_form="VERIFIED_PROOF",verifier_boundary_crossed=True,artifact_hash="h")]
 assert audit_e2e_testdrive_report(bad)
def test_cli(tmp_path):
 out=tmp_path/"e2e.json"; subprocess.run([sys.executable,"scripts/run_e2e_testdrive.py","--out-report-json",str(out)],check=True); assert out.exists()
