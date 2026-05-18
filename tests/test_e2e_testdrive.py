import subprocess,sys
from mathgraph.e2e_testdrive import *
from mathgraph.roadmap_alignment import check_roadmap_alignment
def test_roundtrip_and_advisory_drive(tmp_path):
 s=E2ETestDriveStep("s",E2EStepKind.SEMANTIC_INTAKE); r=run_e2e_testdrive(workspace_root=tmp_path)
 assert s.from_json(s.to_json()).to_dict()==s.to_dict()
 assert r.from_json(r.to_json()).to_dict()==r.to_dict()
 kinds={x.step_kind for x in r.steps}; assert {E2EStepKind.SEMANTIC_INTAKE,E2EStepKind.FORMAL_WORLD_ADAPTER,E2EStepKind.PROOF_SYSTEM_INTEGRATION,E2EStepKind.VERIFIER_EXECUTION,E2EStepKind.VERIFIER_FIXTURE_SUITE,E2EStepKind.VERIFIED_CORPUS_INGESTION,E2EStepKind.LEAN_PROJECT_SUBSET_INGESTION,E2EStepKind.MATHLIB_MICRO_SUBSET_INGESTION,E2EStepKind.API_SUBMIT,E2EStepKind.AGENT_ECOLOGY,E2EStepKind.HARDENING,E2EStepKind.FINAL_AUDIT}<=kinds
 assert r.ok() and not r.boundary_evidence and r.hardening_report.ok()
 assert r.summary["fixture_total"]==10 and r.summary["corpus_file_total"]==6 and r.summary["lean_project_file_total"]==7 and r.summary["mathlib_micro_file_total"]==8 and "Mathlib Micro-Subset" in e2e_testdrive_report_to_markdown(r)
 assert "Mathlib Declaration Discovery" not in e2e_testdrive_report_to_markdown(r)
 assert check_roadmap_alignment(e2e_testdrive_reports=[r]).critical_count()==0
def test_live_mode_and_audits(tmp_path):
 r=run_e2e_testdrive(mode=E2ETestDriveMode.LIVE_VERIFIER,workspace_root=tmp_path,allow_execution=True,allow_missing_verifier=True,accept_verified_fixtures_in_memory=True); assert r.ok()
 assert r.summary["known_skip_total"]==r.summary["accepted_in_memory_total"]
 bad=run_e2e_testdrive(workspace_root=tmp_path/"bad"); bad.boundary_evidence=[VerifierBoundaryEvidence("e",result_id="r",certificate_id="c",terminal_form="VERIFIED_PROOF",verifier_boundary_crossed=True,artifact_hash="h")]
 assert audit_e2e_testdrive_report(bad)
def test_optional_mathlib_local_allowlist(tmp_path):
 r=run_e2e_testdrive(workspace_root=tmp_path,include_mathlib_local_allowlist=True)
 assert any(x.step_kind==E2EStepKind.MATHLIB_LOCAL_ALLOWLIST_INGESTION for x in r.steps)
 assert r.summary["mathlib_local_dependency_edge_total"]>0
 assert "Mathlib Local Allowlist" in e2e_testdrive_report_to_markdown(r)
def test_optional_mathlib_declaration_discovery(tmp_path):
 r=run_e2e_testdrive(workspace_root=tmp_path,include_mathlib_declaration_discovery=True)
 assert any(x.step_kind==E2EStepKind.MATHLIB_DECLARATION_DISCOVERY for x in r.steps)
 assert r.summary["mathlib_discovery_selected_total"]>0
 assert "Mathlib Declaration Discovery" in e2e_testdrive_report_to_markdown(r)
def test_optional_proof_library_demo(tmp_path):
 r=run_e2e_testdrive(workspace_root=tmp_path,include_proof_library_demo=True)
 assert any(x.step_kind==E2EStepKind.PROOF_LIBRARY_DEMO for x in r.steps)
 assert r.summary["proof_library_demo_selected_total"]>0
 assert "Proof-Library Demo" in e2e_testdrive_report_to_markdown(r)
def test_optional_public_and_real_revision_demo(tmp_path):
 r=run_e2e_testdrive(workspace_root=tmp_path,include_public_demo=True,include_real_mathlib_revision_demo=True)
 assert any(x.step_kind==E2EStepKind.PUBLIC_DEMO for x in r.steps)
 assert any(x.step_kind==E2EStepKind.REAL_MATHLIB_REVISION_DEMO for x in r.steps)
 md=e2e_testdrive_report_to_markdown(r); assert "Public Demo" in md and "Real Mathlib Revision Demo" in md
def test_optional_curated_real_mathlib_demo(tmp_path):
 r=run_e2e_testdrive(workspace_root=tmp_path,include_real_mathlib_demo=True)
 assert any(x.step_kind==E2EStepKind.CURATED_REAL_MATHLIB_DEMO for x in r.steps)
def test_cli(tmp_path):
 out=tmp_path/"e2e.json"; subprocess.run([sys.executable,"scripts/run_e2e_testdrive.py","--out-report-json",str(out)],check=True); assert out.exists()
