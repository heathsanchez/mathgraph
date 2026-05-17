import shutil,subprocess,sys
from mathgraph.verifier_execution import *
from mathgraph.roadmap_alignment import check_roadmap_alignment
GOOD="theorem mathgraph_smoke_true : True := by\n  trivial\n"
BAD="theorem mathgraph_bad : True := by\n  sorry\n"
def test_roundtrips_defaults_and_validation(tmp_path):
 c,p=build_lean_check_contract_from_text(GOOD,workspace_root=tmp_path,expected_theorem_names=["mathgraph_smoke_true"]); exe=discover_verifier_executable("lean"); f=VerifierSafetyFinding("f",VerifierSafetyFindingKind.RAW_SUCCESS_NOT_ENOUGH); q=VerifierExecutionRequest("q",c); r=VerifierExecutionResult("r","q",VerifierSystemKind.LEAN); e=VerifierBoundaryEvidence("e",result_id="r",certificate_id="c",terminal_form="VERIFIED_PROOF",verifier_boundary_crossed=True,artifact_hash="h"); rep=VerifierExecutionReport("rep",[exe],[c],[q],[r],[e])
 for x in (exe,c,f,q,r,e,rep): assert x.from_json(x.to_json()).to_dict()==x.to_dict()
 assert not c.allow_execution and not c.allow_shell and not c.allow_network and p.exists()
 assert validate_verifier_command_contract(VerifierCommandContract("x",VerifierSystemKind.LEAN,VerifierExecutionMode.CHECK_FILE,("lean","x"),allow_shell=True))
 assert any(x.finding_kind==VerifierSafetyFindingKind.UNSAFE_SORRY for x in validate_verifier_command_contract(build_lean_check_contract_from_text(BAD,workspace_root=tmp_path/"bad")[0]))
def test_execution_boundary_and_bridges(tmp_path):
 c,_=build_lean_check_contract_from_text(GOOD,workspace_root=tmp_path/"safe",allow_execution=False,expected_theorem_names=["mathgraph_smoke_true"]); q=VerifierExecutionRequest("q",c); blocked=execute_verifier_request(q); assert blocked.status==VerifierExecutionStatus.BLOCKED and not blocked.has_boundary_evidence()
 dry=build_verifier_execution_report([GOOD],workspace_root=tmp_path/"dry"); assert dry.contracts and dry.requests and not dry.boundary_evidence
 unsafe=build_verifier_execution_report([BAD],workspace_root=tmp_path/"unsafe",allow_execution=True); assert not unsafe.boundary_evidence
 live=build_verifier_execution_report([GOOD],workspace_root=tmp_path/"live",allow_execution=True)
 if shutil.which("lean"): assert live.boundary_evidence and live.boundary_evidence[0].is_valid_boundary_evidence()
 else: assert live.results[0].status==VerifierExecutionStatus.SKIPPED
 assert verifier_execution_report_to_api_response(dry).truth_status!=ApiTruthStatus.BOUNDARY_EVIDENCE_PRESENT
 assert all(x.status==LawbookEntryStatus.CANDIDATE for x in verifier_execution_report_to_lawbook_candidates(live))
 assert any(x.phase.value=="FIXATION" for x in verifier_execution_report_to_alchemical_trace(live).steps) == bool(live.boundary_evidence)
 assert extract_theorem_declarations(GOOD)==("mathgraph_smoke_true",)
 assert extract_unsafe_markers(BAD)==("sorry",)
 assert validate_expected_theorems(GOOD,["mathgraph_smoke_true"])[0]
 assert not validate_expected_theorems(GOOD,["missing"])[0]
 miss=VerifierExecutionResult("m","q",VerifierSystemKind.LEAN,VerifierExecutionStatus.SKIPPED,safety_findings=(VerifierSafetyFinding("f",VerifierSafetyFindingKind.MISSING_EXECUTABLE),))
 assert classify_verifier_failure(miss)==VerifierFailureKind.MISSING_EXECUTABLE
 assert "Boundary policy" in verifier_execution_report_to_markdown(dry)
 assert audit_verifier_command_contract(VerifierCommandContract("x",VerifierSystemKind.LEAN,VerifierExecutionMode.CHECK_FILE,("lean","x"),allow_shell=True))
 assert check_roadmap_alignment(verifier_execution_reports=[unsafe]).critical_count()==0
def test_cli(tmp_path):
 out=tmp_path/"r.json"; subprocess.run([sys.executable,"scripts/run_verifier_execution.py","--input-text",BAD,"--out-report-json",str(out)],check=True); assert out.exists() and not VerifierExecutionReport.read_json(out).boundary_evidence
