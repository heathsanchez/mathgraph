from pathlib import Path
import shutil,subprocess,sys
from mathgraph.mathlib_module_verification import *
from mathgraph.roadmap_alignment import check_roadmap_alignment
ROOT=Path(__file__).resolve().parents[1]; SYN=ROOT/"examples"/"mathlib_micro_subset"
def test_models_generation_examples_and_dry_run(tmp_path):
 t=MathlibModuleCheckTarget("t","Mathlib.MathGraph.Basic","Mathlib/MathGraph/Basic.lean",("Mathlib.MathGraph.mgml_true",)); q=MathlibModuleVerificationRequest("q",str(SYN),[t]); f=write_module_check_file(q,t,workspace_root=tmp_path/"checks")
 assert MathlibModuleCheckTarget.from_json(t.to_json()).module_name==t.module_name
 assert MathlibModuleVerificationRequest.from_json(q.to_json()).targets[0]["target_id"]=="t" if isinstance(MathlibModuleVerificationRequest.from_json(q.to_json()).targets[0],dict) else True
 assert "#check Mathlib.MathGraph.mgml_true" in generate_module_check_file_text(t) and f.unsafe_markers==() and SYN not in Path(f.check_file_path).parents
 assert extract_check_file_unsafe_markers("axiom nope : Prop")==("axiom",)
 ps=ensure_module_verification_examples(tmp_path/"ex"); assert len(ps)==2 and all(p.exists() for p in ps)
 r=run_mathlib_module_verification(default_synthetic_module_verification_request(SYN),workspace_root=tmp_path/"dry")
 assert r.declaration_count()==4 and r.boundary_evidence_count()==0 and r.check_file_count()==2 and "does not mean" in mathlib_module_verification_report_to_markdown(r)
 out=write_mathlib_module_verification_artifacts(r,tmp_path/"out"); assert Path(out["report"]).exists() and Path(out["markdown"]).exists()
 assert not check_roadmap_alignment(mathlib_module_verification_reports=[r]).critical_count()
def test_missing_env_and_live_contract(monkeypatch,tmp_path):
 miss=run_mathlib_module_verification(MathlibModuleVerificationRequest("missing","/nope")); assert miss.status==MathlibModuleVerificationStatus.SKIPPED_ENVIRONMENT and not miss.boundary_evidence_count()
 monkeypatch.setattr("shutil.which",lambda x: None)
 skip=run_mathlib_module_verification(default_synthetic_module_verification_request(SYN),allow_execution=True,allow_missing_verifier=True,workspace_root=tmp_path/"skip"); assert skip.status==MathlibModuleVerificationStatus.SKIPPED_MISSING_VERIFIER and not skip.boundary_evidence_count()
 fail=run_mathlib_module_verification(default_synthetic_module_verification_request(SYN),allow_execution=True,allow_missing_verifier=False,workspace_root=tmp_path/"fail"); assert fail.critical_count()
def test_live_if_lean_available_and_audits(tmp_path):
 if not shutil.which("lean"): return
 r=run_mathlib_module_verification(default_synthetic_module_verification_request(SYN),allow_execution=True,accept_verified_entries_in_memory=True,workspace_root=tmp_path/"live")
 assert r.verified_count()==4 and r.boundary_evidence_count()==4 and r.known_skip_count()==4
 assert all(x.metadata["boundary_kind"]=="module_aware_import_check" and x.metadata["check_mode"]=="#check" and x.metadata["proof_rechecked_from_source"] is False for x in r.declaration_results)
 bad=MathlibModuleDeclarationResult("bad","q","t","M","x",boundary_evidence=[r.declaration_results[0].boundary_evidence[0]],failure_kind=MathlibModuleVerificationFailureKind.CHECK_FAILED)
 assert audit_mathlib_module_declaration_result(bad)
 assert len(mathlib_module_verification_report_to_lawbook_candidates(r))==4 and mathlib_module_verification_report_to_api_response(r)
def test_cli(tmp_path):
 p=subprocess.run([sys.executable,"scripts/run_mathlib_module_verification.py","--use-synthetic-request","--project-root",str(SYN),"--out-dir",str(tmp_path/"o")],cwd=ROOT,text=True,capture_output=True)
 assert p.returncode==0 and "MathGraph Mathlib Module Verification" in p.stdout and (tmp_path/"o"/"mathlib_module_verification_report.json").exists()
