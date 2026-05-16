import subprocess,sys
from pathlib import Path
from mathgraph.agent_biography import AgentExperienceOutcome
from mathgraph.certificates import TerminalForm
from mathgraph.proof_system_integration import *
from mathgraph.roadmap_alignment import check_roadmap_alignment
def _lean(): return proof_artifact_manifest_from_text("import Foo\ntheorem foo : True := by trivial",path="Foo.lean")
def test_roundtrips():
 s=default_proof_system_specs()[0]; a=_lean(); p=build_proof_project_manifest(artifacts=[a],spec=s); g=build_proof_import_graph(p,[a]); c=default_check_command_contract_for_artifact(a,s); q=create_check_request(a,c); z=parse_check_result(q); i=trusted_import_record_from_mapping({"artifact_id":a.artifact_id}); e=ProofBoundaryEvidence("e",ProofBoundaryKind.NONE); t=proof_system_tasks_from_artifacts([a])[0]; r=ProofSystemIntegrationReport("r",[s],[p],[a],[g],[c],[q],[z],[i],[e],[t])
 for x in (s,p,a,g,c,q,z,i,e,t,r): assert x.from_json(x.to_json()).to_dict()==x.to_dict()
def test_defaults_detection_extractors_and_artifacts(tmp_path):
 assert {x.name for x in default_proof_system_specs()} >= {"lean","isabelle","coq","generic_proof_assistant","proof_text_import"}
 s=default_proof_system_specs()[0]; assert s.recognizes_path("Foo.lean") and s.detects_placeholder("by sorry")
 assert detect_proof_system_kind("Foo.lean")==ProofSystemKind.LEAN
 assert detect_proof_system_kind("theory X imports Main begin")==ProofSystemKind.ISABELLE
 assert detect_proof_system_kind("Lemma foo : True. Proof. exact I. Qed.")==ProofSystemKind.COQ
 assert detect_proof_system_kind("Proof. Suppose x. Therefore y.")==ProofSystemKind.PROOF_TEXT_IMPORT
 assert proof_system_spec_for_kind(ProofSystemKind.UNKNOWN).kind==ProofSystemKind.GENERIC_PROOF_ASSISTANT
 assert extract_lean_imports("import Foo") and extract_lean_theorem_names("theorem foo : True := by trivial")
 assert extract_isabelle_imports("imports Main") and extract_isabelle_theorem_names("theorem foo")
 assert extract_coq_imports("Require Import Foo.") and extract_coq_theorem_names("Lemma foo")
 assert _lean().theorem_names
 assert proof_artifact_manifest_from_text("theorem foo : True := by sorry").has_placeholder()
 assert proof_artifact_manifest_from_path(tmp_path/"missing.lean").status==ProofArtifactStatus.MISSING
 p=tmp_path/"A.lean"; p.write_text("theorem a : True := by trivial"); assert proof_artifact_manifest_from_path(p).theorem_names
def test_projects_graphs_contracts_requests(tmp_path):
 a=proof_artifact_manifest_from_text("import B\ntheorem a : True := by trivial",path=str(tmp_path/"A.lean")); b=proof_artifact_manifest_from_text("import A\ntheorem b : True := by trivial",path=str(tmp_path/"B.lean"))
 (tmp_path/"A.lean").write_text(a.metadata["text"]); (tmp_path/"B.lean").write_text(b.metadata["text"])
 p=build_proof_project_manifest(tmp_path,[a,b],spec=default_proof_system_specs()[0],scan_files=True,max_files=2); assert p.artifact_ids
 g=build_proof_import_graph(p,[a,b]); assert g.edges and g.cycles
 unsafe=ProofCheckCommandContract("c","lean",ProofSystemKind.LEAN,CheckCommandKind.LEAN_CHECK,("lean",";"),True); assert not unsafe.is_safe()
 safe=default_check_command_contract_for_artifact(a,allow_execution=True); assert safe.is_safe()
 assert default_check_command_contract_for_artifact(a).allowed is False
 assert create_check_request(proof_artifact_manifest_from_text("theorem a : True := by sorry",path=str(tmp_path/"S.lean")),safe).status==CheckRequestStatus.BLOCKED_PLACEHOLDER
 assert create_check_request(proof_artifact_manifest_from_path(tmp_path/"missing.lean"),safe).status==CheckRequestStatus.BLOCKED_MISSING_ARTIFACT
 assert create_check_request(a,unsafe).status==CheckRequestStatus.BLOCKED_UNSAFE_COMMAND
 assert create_check_request(a,default_check_command_contract_for_artifact(a)).status==CheckRequestStatus.RUN_NOT_ALLOWED
 assert create_check_request(a,safe).status==CheckRequestStatus.READY
def test_results_imports_tasks_report_and_bridges(tmp_path):
 p=tmp_path/"A.lean"; p.write_text("theorem a : True := by trivial"); a=proof_artifact_manifest_from_path(p); q=create_check_request(a,default_check_command_contract_for_artifact(a,allow_execution=True))
 assert parse_check_result(q,stderr="error: failed",exit_code=1).status==CheckResultStatus.FAILED
 assert parse_check_result(q,stdout="sorry",exit_code=0).status==CheckResultStatus.PLACEHOLDER_FOUND
 ok=parse_check_result(q,exit_code=0); assert ok.status==CheckResultStatus.PASSED and not ok.crosses_boundary()
 good=parse_check_result(q,exit_code=0,certificate_id="c",terminal_form=TerminalForm.VERIFIED_PROOF,verifier_boundary_crossed=True); assert good.crosses_boundary() and proof_boundary_evidence_from_check_result(good)
 raw=parse_check_result(q,stdout="verified successfully",exit_code=0); assert not raw.crosses_boundary()
 imp=trusted_import_record_from_mapping({"artifact_id":a.artifact_id,"certificate_id":"c","terminal_form":"VERIFIED_PROOF","verifier_boundary_crossed":True,"provenance":["repo"]}); assert imp.crosses_boundary() and proof_boundary_evidence_from_trusted_import(imp)
 assert not trusted_import_record_from_mapping({"artifact_id":a.artifact_id,"certificate_id":"c","terminal_form":"VERIFIED_PROOF","verifier_boundary_crossed":True}).crosses_boundary()
 assert any(x.task_kind==ProofSystemTaskKind.CHECK_THEOREM_FILE for x in proof_system_tasks_from_artifacts([a]))
 assert any(x.task_kind==ProofSystemTaskKind.REPAIR_PROOF for x in proof_system_tasks_from_check_results([parse_check_result(q,stderr="failed",exit_code=1)]))
 r=build_proof_system_integration_report([{"text":"theorem foo : True := by trivial"}]); assert r.specs and r.artifacts and r.check_requests and r.tasks
 r2=build_proof_system_integration_report(artifacts=[a],check_results=[good]); assert r2.boundary_evidence
 assert all(x.status==LawbookEntryStatus.CANDIDATE for x in proof_system_report_to_lawbook_candidates(r))
 assert proof_system_report_to_continuation_outputs(r) and proof_system_report_to_curriculum(r).stages and proof_system_report_to_discovery_value_scores(r)
 assert proof_system_report_to_process_episodes(r) and proof_system_report_to_proof_digestion_inputs(r)
 assert proof_system_report_to_structure_descriptors(r) and proof_system_report_to_typed_projection_candidates(r) and proof_system_report_to_role_signatures(r) and proof_system_report_to_analogy_sources(r)
 assert proof_system_report_to_habit_observations(r) and proof_system_report_to_reason_observations(r) and proof_system_report_to_structural_identity_objects(r)
 assert all(x.phase.value!="FIXATION" for x in proof_system_report_to_alchemical_trace(r).steps)
 assert any(x.phase.value=="FIXATION" for x in proof_system_report_to_alchemical_trace(r2).steps)
 assert all(x.outcome not in {AgentExperienceOutcome.VERIFIED_PROOF,AgentExperienceOutcome.FINITE_COUNTERMODEL} for x in proof_system_report_to_agent_experiences(r))
def test_inputs_audits_alignment_and_cli(tmp_path):
 assert proof_system_inputs_from_object({"text":"theorem x"})
 a=ProofArtifactManifest("a","lean",ProofSystemKind.LEAN,ProofArtifactKind.THEOREM_FILE,placeholders=("sorry",),status=ProofArtifactStatus.CHECK_PASSED,advisory=False)
 assert audit_proof_artifact_manifest(a)
 assert audit_proof_check_command_contract(ProofCheckCommandContract("c","lean",ProofSystemKind.LEAN,CheckCommandKind.LEAN_CHECK,("lean",";"),True))
 bad=ProofCheckResult("r","q",status=CheckResultStatus.PASSED,verifier_boundary_crossed=True); assert audit_proof_check_result(bad)
 assert audit_trusted_proof_import_record(TrustedProofImportRecord("i","lean",ProofSystemKind.LEAN,status=TrustedImportStatus.ACCEPTED_WITH_BOUNDARY))
 assert audit_proof_boundary_evidence(ProofBoundaryEvidence("e",ProofBoundaryKind.VERIFIER_CHECK))
 rep=check_roadmap_alignment(proof_artifact_manifests=[a]); assert rep.critical_count()
 out=tmp_path/"artifacts.jsonl"; subprocess.run([sys.executable,"scripts/run_proof_system_integration.py","--input-text","theorem foo : True := by trivial","--out-artifacts-jsonl",str(out)],check=True); assert out.read_text()
