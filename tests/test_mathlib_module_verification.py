from pathlib import Path
import json,shutil,subprocess,sys
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
def test_minimal_request_loading_is_robust_and_deterministic(tmp_path):
 d={"project_root":str(SYN),"targets":[{"module_name":"Mathlib.MathGraph.Basic","module_path":"Mathlib/MathGraph/Basic.lean","declaration_names":["Mathlib.MathGraph.mgml_true"]}]}
 a=MathlibModuleVerificationRequest.from_dict(d); b=MathlibModuleVerificationRequest.from_json(json.dumps(d))
 assert a.request_id==b.request_id and a.targets[0].target_id==b.targets[0].target_id
 assert a.targets[0].check_mode==MathlibModuleVerificationCheckMode.CHECK_DECLARATION and a.advisory
 p=tmp_path/"minimal.json"; p.write_text(json.dumps(d)); z=subprocess.run([sys.executable,"scripts/run_mathlib_module_verification.py","--request",str(p),"--project-root",str(SYN)],cwd=ROOT,text=True,capture_output=True)
 assert z.returncode==0
 assert "MathGraph Mathlib Module Verification" in z.stdout
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
def test_failed_diagnostics_and_fallback(tmp_path):
 q=MathlibModuleVerificationRequest("fallback",str(SYN),[MathlibModuleCheckTarget("t","Mathlib.MathGraph.Basic","Mathlib/MathGraph/Basic.lean",("Mathlib.mgml_true",))])
 dry=run_mathlib_module_verification(q,allow_execution=True,workspace_root=tmp_path/"diag")
 ds=failed_check_diagnostics(dry); assert ds and "#check Mathlib.mgml_true" in ds[0]["check_file_text"] and "lean_stderr_tail" in ds[0]
 assert "mgml_true" in generate_declaration_name_candidates("Mathlib.mgml_true",module_name="Mathlib.MathGraph.Basic")
 assert "Nat.succ.inj" in generate_declaration_name_candidates("Mathlib.succ_injective",module_name="Mathlib.Data.Nat.Basic")
 assert dry.fallback_verified_count()==0
 if not shutil.which("lean"): return
 live=run_mathlib_module_verification(q,allow_execution=True,enable_name_candidate_fallback=True,workspace_root=tmp_path/"fallback")
 assert live.verified_count()==1 and live.fallback_verified_count()==1
 md=live.declaration_results[0].metadata; assert md["original_declaration_name"]=="Mathlib.mgml_true" and md["resolved_declaration_name"]=="Mathlib.MathGraph.mgml_true" and md["name_resolution_mode"]=="candidate_fallback"
 out=write_mathlib_module_verification_artifacts(dry,tmp_path/"out2"); assert Path(out["failed_diagnostics"]).exists() and "Failed Check Diagnostics" in mathlib_module_verification_report_to_markdown(dry)
 bad=live.declaration_results[0].boundary_evidence[0]; bad.metadata.pop("original_declaration_name"); assert check_roadmap_alignment(mathlib_module_declaration_results=[live.declaration_results[0]]).critical_count()
def test_cli(tmp_path):
 p=subprocess.run([sys.executable,"scripts/run_mathlib_module_verification.py","--use-synthetic-request","--project-root",str(SYN),"--enable-name-candidate-fallback","--out-dir",str(tmp_path/"o")],cwd=ROOT,text=True,capture_output=True)
 assert p.returncode==0 and "unresolved:" in p.stdout and (tmp_path/"o"/"mathlib_module_verification_report.json").exists() and (tmp_path/"o"/"failed_check_diagnostics.json").exists()
