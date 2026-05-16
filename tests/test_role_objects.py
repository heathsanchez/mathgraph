import json,subprocess,sys
from mathgraph.role_objects import *
from mathgraph.structure_registry import StructureDescriptor,StructureFamily,StructureObjectKind
from mathgraph.lawbook import LawbookEntryStatus
from mathgraph.agent_biography import AgentExperienceOutcome
def _sig(i="s",atoms=("projection","algebraic","witness")): return role_signature_from_mapping({"id":i,"projection":"same","family":"algebraic","witness":"table",**{a:a for a in atoms}},source_object_id=i)
def test_roundtrips():
 sig=_sig(); d=build_role_definition_candidates([sig,sig])[0]; w=build_role_witness_candidates([d],[sig])[0]; c=build_role_conjecture_candidates([d],[w])[0]; rv=RoleReview("r",d.candidate_id,RoleReviewDecision.ACCEPT_ADVISORY); ro=promote_role_definition_candidate(d,rv,[w],[c]); rep=RoleObjectReport("rep",[sig],[d],[w],[c],[rv],[ro])
 for x in (sig,d,w,c,ro,rv,rep): assert x.from_json(x.to_json()).to_dict()==x.to_dict()
def test_atoms_and_kinds():
 assert normalize_role_atom(" Role Name ")=="role_name"
 assert classify_role_condition("algebraic")==RoleConditionKind.STRUCTURE_FAMILY
 assert classify_role_condition("projection_compatibility")==RoleConditionKind.PROJECTION_COMPATIBILITY
 atoms,kinds=extract_role_conditions_from_mapping({"route":"r","status":"ok","family":"algebraic","feature":"operation"})
 assert {"route","status","family","feature"}<=set(atoms)
 assert infer_role_kind(("constructor","table"),{}) in {RoleObjectKind.MIXED_ROLE,RoleObjectKind.CONSTRUCTOR_ROLE}
 assert propose_role_name(RoleObjectKind.PROJECTION_ROLE,("algebraic","logical"))=="projection_role_algebraic_logical"
def test_signatures_and_candidates():
 desc=StructureDescriptor("d","o",StructureObjectKind.RAW_EVENT,("ALGEBRAIC",),StructureFamily.ALGEBRAIC,("operation",),{"operation":"STRUCTURE_FEATURE"})
 assert role_signature_from_structure_descriptor(desc).source_kind==RoleSourceKind.STRUCTURE_DESCRIPTOR
 sigs=[_sig("a"),_sig("b"),_sig("c")]
 defs=build_role_definition_candidates(sigs); assert defs and defs[0].support_count==3
 wits=build_role_witness_candidates(defs,sigs); assert wits
 conjs=build_role_conjecture_candidates(defs,wits); assert conjs
 review=review_role_definition_candidate(defs[0],wits); assert review.decision==RoleReviewDecision.ACCEPT_ADVISORY
 role=promote_role_definition_candidate(defs[0],review,wits,conjs); assert role.is_accepted() and role.advisory and role.matches({"projection":"same"})
def test_report_and_bridges():
 rep=build_role_object_report(signatures=[_sig("a"),_sig("b"),_sig("c")],auto_promote=True)
 assert rep.signatures and rep.definition_candidates and rep.witness_candidates
 assert all(x.status==LawbookEntryStatus.CANDIDATE for x in role_report_to_lawbook_candidates(rep))
 assert all(x.advisory for x in role_report_to_continuation_outputs(rep))
 assert all(x.advisory for x in role_report_to_curriculum(rep).stages)
 assert role_report_to_discovery_value_scores(rep)
 assert not any(x.has_truth_boundary() for x in role_report_to_process_episodes(rep))
 assert role_report_to_structure_descriptors(rep)
 assert role_report_to_habit_observations(rep)
 assert role_report_to_reason_observations(rep)
 assert role_report_to_structural_identity_objects(rep)
 assert all(s.phase.value!="FIXATION" for s in role_report_to_alchemical_trace(rep).steps)
 assert all(x.outcome not in {AgentExperienceOutcome.VERIFIED_PROOF,AgentExperienceOutcome.FINITE_COUNTERMODEL} for x in role_report_to_agent_experiences(rep))
 assert isinstance(role_report_to_route_telemetry_events(rep)[0],dict)
 ranked=rank_routes_with_role_objects(rep.role_objects,[{"score":1,"projection":"same"}]); assert ranked[0]["role_advisory_only"]
def test_audit_and_cli(tmp_path):
 bad=RoleObject("bad",RoleObjectKind.ABSTRACT_STRUCTURE,"bad",advisory=False)
 assert any(x["severity"]=="CRITICAL" for x in audit_role_object(bad))
 wit=RoleWitnessCandidate("w","c",witness_status=RoleWitnessStatus.VERIFIED_EXISTING_CERTIFICATE)
 assert audit_role_witness_candidate(wit)
 raw=tmp_path/"raw.jsonl"; raw.write_text('{"projection":"same","family":"algebraic","witness":"table"}\n'*3)
 defs=tmp_path/"defs.jsonl"; laws=tmp_path/"laws.jsonl"; cont=tmp_path/"cont.jsonl"; desc=tmp_path/"desc.jsonl"
 subprocess.run([sys.executable,"scripts/run_role_objects.py","--raw-event-jsonl",str(raw),"--out-definitions-jsonl",str(defs),"--out-lawbook-candidates-jsonl",str(laws),"--out-continuation-outputs-jsonl",str(cont),"--out-structure-descriptors-jsonl",str(desc)],check=True)
 assert defs.read_text() and laws.read_text() and cont.read_text() and desc.exists()
