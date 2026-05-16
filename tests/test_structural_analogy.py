import subprocess,sys
from mathgraph.agent_biography import AgentExperienceOutcome
from mathgraph.lawbook import LawbookEntryStatus
from mathgraph.role_objects import RoleObject,RoleObjectKind,RoleSignature,RoleSourceKind
from mathgraph.structural_analogy import *
from mathgraph.structure_registry import StructureDescriptor,StructureFamily,StructureObjectKind
def _src(i="a",**kw): return analogy_source_from_mapping({"id":i,"family":"algebraic","role":"projection_role","projection":"compatible","feature":"operation",**kw},object_id=i)
def test_roundtrips():
 a=_src("a"); b=_src("b"); m=compute_analogy_feature_map(a,b); br=AnalogyBreak("br",m.map_id); c=structural_analogy_candidate_from_map(m,[br]); n=exposition_notes_from_candidate(c,m,[br])[0]; rv=review_structural_analogy_candidate(c,[br]); rep=StructuralAnalogyReport("rep",[a,b],[m],[br],[c],[n],[rv])
 for x in (a,m,br,c,n,rv,rep): assert x.from_json(x.to_json()).to_dict()==x.to_dict()
def test_features_and_sources():
 assert normalize_analogy_atom(" Role Name ")=="role_name"
 assert classify_analogy_feature("algebraic")==AnalogyFeatureKind.STRUCTURE_FAMILY
 assert classify_analogy_feature("projection_role")==AnalogyFeatureKind.ROLE_CONDITION
 atoms,_=extract_analogy_features_from_mapping({"route":"r","status":"ok","family":"algebraic","role":"projection_role"})
 assert {"route","status","family","role"}<=set(atoms)
 role=RoleObject("r",RoleObjectKind.PROJECTION_ROLE,"r",("projection",))
 desc=StructureDescriptor("d","o",StructureObjectKind.RAW_EVENT,("ALGEBRAIC",),StructureFamily.ALGEBRAIC,("operation",),{"operation":"STRUCTURE_FEATURE"})
 assert analogy_source_from_role_object(role).source_kind==AnalogySourceKind.ROLE_OBJECT
 assert analogy_source_from_structure_descriptor(desc).source_kind==AnalogySourceKind.STRUCTURE_DESCRIPTOR
 assert analogy_source_from_role_signature(RoleSignature("s",RoleSourceKind.RAW_EVENT)).source_kind==AnalogySourceKind.ROLE_SIGNATURE
def test_maps_breaks_candidates_and_notes():
 a=_src("a"); b=_src("b"); m=compute_analogy_feature_map(a,b)
 assert infer_analogy_relation_kind(a,b,m.shared_features) in {AnalogyRelationKind.SAME_ROLE,AnalogyRelationKind.SAME_STRUCTURE_FAMILY}
 assert m.shared_features and build_analogy_feature_maps([a,b],max_pairs=1)
 mismatch=compute_analogy_feature_map(_src("x",family="algebraic"),analogy_source_from_mapping({"family":"topological"},object_id="y")); bs=identify_analogy_breaks(mismatch,_src("x",family="algebraic"),analogy_source_from_mapping({"family":"topological"},object_id="y")); assert any(x.break_kind==AnalogyBreakKind.TYPE_MISMATCH for x in bs)
 strong=structural_analogy_candidate_from_map(m,[]); assert strong.status in {AnalogyCandidateStatus.STRONG_ADVISORY,AnalogyCandidateStatus.WEAK_ADVISORY}
 blocked=structural_analogy_candidate_from_map(m,[AnalogyBreak("x",m.map_id,break_kind=AnalogyBreakKind.CONFLICTING_FEATURE,blocks_projection=True)]); assert blocked.status==AnalogyCandidateStatus.BLOCKED_CONFLICT
 notes=exposition_notes_from_candidate(blocked,m,[AnalogyBreak("x",m.map_id,break_kind=AnalogyBreakKind.MISSING_FEATURE)]); assert any(n.kind==ExpositionNoteKind.SUMMARY for n in notes) and all(n.metadata["analogy_advisory_only"] for n in notes)
 assert review_structural_analogy_candidate(blocked).decision==AnalogyReviewDecision.REJECT
def test_report_bridges_and_routes():
 rep=build_structural_analogy_report(sources=[_src("a"),_src("b")])
 assert rep.sources and rep.feature_maps and rep.candidates and rep.exposition_notes
 assert all(x.status==LawbookEntryStatus.CANDIDATE for x in analogy_report_to_lawbook_candidates(rep))
 assert all(x.advisory for x in analogy_report_to_continuation_outputs(rep))
 assert all(x.advisory for x in analogy_report_to_curriculum(rep).stages)
 assert analogy_report_to_discovery_value_scores(rep)
 assert not any(x.has_truth_boundary() for x in analogy_report_to_process_episodes(rep))
 assert analogy_report_to_role_signatures(rep)
 assert analogy_report_to_structure_descriptors(rep)
 assert analogy_report_to_habit_observations(rep)
 assert analogy_report_to_reason_observations(rep)
 assert analogy_report_to_structural_identity_objects(rep)
 assert all(s.phase.value!="FIXATION" for s in analogy_report_to_alchemical_trace(rep).steps)
 assert all(x.outcome not in {AgentExperienceOutcome.VERIFIED_PROOF,AgentExperienceOutcome.FINITE_COUNTERMODEL} for x in analogy_report_to_agent_experiences(rep))
 assert isinstance(analogy_report_to_route_telemetry_events(rep)[0],dict)
 ranked=rank_routes_with_analogies(rep.candidates,[{"score":1,"relation":"same_role"}]); assert ranked[0]["analogy_advisory_only"]
def test_audit_and_cli(tmp_path):
 bad=StructuralAnalogyCandidate("c","a","b","m",metadata={"certificate_id":"bad"})
 assert any(x["severity"]=="CRITICAL" for x in audit_structural_analogy_candidate(bad))
 note=ExpositionNote("n",ExpositionNoteKind.SUMMARY,text="verified proof")
 assert audit_exposition_note(note)
 raw=tmp_path/"raw.jsonl"; raw.write_text('{"event_id":"a","family":"algebraic","role":"projection_role","projection":"compatible","feature":"operation"}\n{"event_id":"b","family":"algebraic","role":"projection_role","projection":"compatible","feature":"operation"}\n')
 cand=tmp_path/"cand.jsonl"; cont=tmp_path/"cont.jsonl"; roles=tmp_path/"roles.jsonl"
 subprocess.run([sys.executable,"scripts/run_structural_analogy.py","--raw-event-jsonl",str(raw),"--out-candidates-jsonl",str(cand),"--out-continuation-outputs-jsonl",str(cont),"--out-role-signatures-jsonl",str(roles)],check=True)
 assert cand.read_text() and cont.read_text() and roles.exists()
