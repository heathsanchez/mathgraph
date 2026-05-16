import subprocess,sys
from mathgraph.agent_biography import AgentExperienceOutcome
from mathgraph.formal_world_adapters import *
from mathgraph.lawbook import LawbookEntryStatus
def _magma(): return parse_magma_equational({"source":"x*x=x","target":"x*y=x"})
def test_roundtrips():
 s=default_formal_world_adapter_specs()[0]; c=default_formal_world_adapter_capabilities([s])[0]; p=_magma(); n=normalize_formal_world_parse(p); v=validate_formal_world_normalization(n,p); t=tasks_from_validation(v,p,n)[0]; h=handoffs_from_tasks([t],[v])[0]; r=FormalWorldAdapterReport("r",[s],[c],[p],[n],[v],[t],[h])
 for x in (s,c,p,n,v,t,h,r): assert x.from_json(x.to_json()).to_dict()==x.to_dict()
def test_detection_parse_normalize_validate():
 assert {s.name for s in default_formal_world_adapter_specs()} >= {"magma_equational","lean_like","proof_text","finite_structure","generic_formal_world"}
 assert all(c.advisory for c in default_formal_world_adapter_capabilities())
 assert detect_formal_world_kind("(x*x)=x => (x*y)=x")==FormalWorldKind.MAGMA_EQUATIONAL
 assert detect_formal_world_kind("theorem foo : True := by trivial")==FormalWorldKind.LEAN_LIKE
 assert detect_formal_world_kind("Proof. Suppose x. Therefore y.")==FormalWorldKind.PROOF_TEXT
 assert detect_formal_world_kind({"carrier":[0,1],"table":[[0,1],[1,0]]})==FormalWorldKind.FINITE_STRUCTURE
 assert detect_formal_world_kind("(assert true) (check-sat)")==FormalWorldKind.SMT_LIKE
 assert _magma().parse_status==ParseStatus.PARSED
 assert parse_magma_equational("(x*x)=x => (x*y)=x").parse_status==ParseStatus.PARSED
 assert parse_magma_equational({"source":"x*x=x"}).parse_status==ParseStatus.PARTIAL
 lean=parse_lean_like("theorem foo : True := by sorry"); assert lean.parsed_object["names"] and "contains_sorry" in lean.warnings
 assert parse_proof_text("Proof. Suppose x. Hence y.").parse_status==ParseStatus.PARSED
 assert parse_finite_structure({"carrier":[0],"table":[[0]],"witness":"w"}).parse_status==ParseStatus.PARSED
 n=normalize_formal_world_parse(parse_magma_equational("(x◇x)=x => (x*y)=x")); assert "*" in n.normalized_text and n.canonical_key==normalize_formal_world_parse(parse_magma_equational("(x◇x)=x => (x*y)=x")).canonical_key
 v=validate_formal_world_normalization(normalize_formal_world_parse(_magma())); assert v.valid_shape
 assert validate_formal_world_normalization(normalize_formal_world_parse(parse_lean_like("theorem foo : True := by trivial"))).validation_status==ValidationStatus.NEEDS_VERIFIER
 assert validate_formal_world_normalization(normalize_formal_world_parse(parse_proof_text("Proof. Hence done."))).validation_status==ValidationStatus.NEEDS_FORMALIZATION
 assert validate_formal_world_normalization(normalize_formal_world_parse(parse_finite_structure({"table":[[0]]}))).validation_status==ValidationStatus.NEEDS_FINITE_VALIDATOR
def test_tasks_handoffs_report_and_bridges():
 p=_magma(); n=normalize_formal_world_parse(p); v=validate_formal_world_normalization(n,p); tasks=tasks_from_validation(v,p,n)
 assert {x.task_kind for x in tasks}>={FormalWorldTaskKind.PROOF_TASK,FormalWorldTaskKind.COUNTERMODEL_TASK}
 assert any(x.task_kind==FormalWorldTaskKind.FORMALIZATION_TASK for x in tasks_from_validation(validate_formal_world_normalization(normalize_formal_world_parse(parse_proof_text("Proof. Hence done.")))))
 h=handoffs_from_tasks(tasks,[v]); assert any(x.handoff_kind==HandoffKind.VERIFIER for x in h)
 assert not FormalWorldHandoff("h","a",FormalWorldKind.MAGMA_EQUATIONAL,HandoffKind.VERIFIER,HandoffStatus.COMPLETED_WITH_BOUNDARY).crosses_boundary()
 r=build_formal_world_adapter_report([{"source":"x*x=x","target":"x*y=x"}]); assert r.specs and r.parses and r.normalizations and r.validations and r.tasks and r.handoffs
 assert all(x.status==LawbookEntryStatus.CANDIDATE for x in adapter_report_to_lawbook_candidates(r))
 assert all(x.advisory for x in adapter_report_to_continuation_outputs(r))
 assert adapter_report_to_curriculum(r).stages
 assert adapter_report_to_discovery_value_scores(r)
 assert not any(x.has_truth_boundary() for x in adapter_report_to_process_episodes(r))
 assert adapter_report_to_structure_descriptors(r)
 assert adapter_report_to_role_signatures(r)
 assert adapter_report_to_analogy_sources(r)
 assert adapter_report_to_habit_observations(r)
 assert adapter_report_to_reason_observations(r)
 assert adapter_report_to_structural_identity_objects(r)
 assert all(s.phase.value!="FIXATION" for s in adapter_report_to_alchemical_trace(r).steps)
 assert all(x.outcome not in {AgentExperienceOutcome.VERIFIED_PROOF,AgentExperienceOutcome.FINITE_COUNTERMODEL} for x in adapter_report_to_agent_experiences(r))
def test_audit_inputs_and_cli(tmp_path):
 assert formal_world_inputs_from_object({"source":"x=x","target":"y=y"})
 assert audit_parse_result(FormalWorldParseResult("p","a",FormalWorldKind.GENERIC_FORMAL,parse_status=ParseStatus.PARSED,metadata={"terminal_form":"VERIFIED_PROOF"}))
 assert audit_normalize_result(FormalWorldNormalizeResult("n","a",FormalWorldKind.GENERIC_FORMAL,normalize_status=NormalizeStatus.NORMALIZED,metadata={"terminal_form":"VERIFIED_PROOF"}))
 assert audit_validation_result(FormalWorldValidationResult("v","a",FormalWorldKind.GENERIC_FORMAL,inherited_terminal_form=TerminalForm.VERIFIED_PROOF))
 assert audit_formal_world_handoff(FormalWorldHandoff("h","a",FormalWorldKind.GENERIC_FORMAL,HandoffKind.VERIFIER,HandoffStatus.COMPLETED_WITH_BOUNDARY))
 out=tmp_path/"parses.jsonl"; tasks=tmp_path/"tasks.jsonl"; roles=tmp_path/"roles.jsonl"
 subprocess.run([sys.executable,"scripts/run_formal_world_adapters.py","--input-text","(x*x)=x => (x*y)=x","--out-parses-jsonl",str(out),"--out-tasks-jsonl",str(tasks),"--out-role-signatures-jsonl",str(roles)],check=True)
 assert out.read_text() and tasks.read_text() and roles.exists()
