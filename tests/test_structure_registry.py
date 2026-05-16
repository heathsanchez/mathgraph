import json,subprocess,sys
from mathgraph.agent_biography import AgentExperienceOutcome
from mathgraph.lawbook import LawbookEntry,LawbookEntryKind,LawbookEntryStatus
from mathgraph.structure_registry import *
def _d(i,fam,atoms):
 return StructureDescriptor(i,i,StructureObjectKind.RAW_EVENT,(fam.value,),fam,tuple(atoms),{a:classify_structure_feature(a).value for a in atoms},confidence=.8)
def test_core_roundtrips():
 objs=[default_structure_types()[0],_d("d",StructureFamily.ALGEBRAIC,("operation","term")),StructureRegistryEntry("e",_d("d2",StructureFamily.LOGICAL,("proof",))),compute_structure_mapping(_d("a",StructureFamily.ALGEBRAIC,("operation","term")),_d("b",StructureFamily.ALGEBRAIC,("operation","term")))]
 objs.append(typed_projection_candidate_from_mapping(objs[-1]))
 for o in objs: assert o.from_json(o.to_json()).to_dict()==o.to_dict()
 s=build_structure_registry_store(descriptors=[objs[1]]); assert StructureRegistryStore.from_json(s.to_json()).to_dict()==s.to_dict()
 r=build_structure_registry_report(descriptors=[objs[1]]); assert StructureRegistryReport.from_json(r.to_json()).to_dict()==r.to_dict()
def test_defaults_features_and_inference():
 fams={x.family for x in default_structure_types()}; assert {StructureFamily.ALGEBRAIC,StructureFamily.ORDER,StructureFamily.TOPOLOGICAL,StructureFamily.COMPUTATIONAL,StructureFamily.MIXED}<=fams
 assert normalize_structure_atom(" Binary Op ")=="binary_op"
 assert classify_structure_feature("operation")==StructureFeatureKind.OPERATION
 assert classify_structure_feature("partial_order")==StructureFeatureKind.ORDER_RELATION
 atoms,kinds=extract_structure_features_from_mapping({"route":"proof","claim":"x=y","source":"magma","target":"formula"})
 assert {"route","claim","source","target"}<=set(atoms)
 assert infer_structure_families(("operation","term"),{"operation":"OPERATION","term":"TERM"})[1]==StructureFamily.ALGEBRAIC
 assert infer_structure_families(("proof",),{"proof":"PROOF"})[1]==StructureFamily.LOGICAL
def test_descriptors_and_mappings():
 raw=structure_descriptor_from_mapping({"operation":"*", "term":"x*x"})
 entry=structure_descriptor_from_lawbook_entry(LawbookEntry("e",LawbookEntryKind.VERIFIED_PROOF_ENTRY,LawbookEntryStatus.CANDIDATE,raw="equation"))
 assert raw.feature_atoms and entry.object_kind==StructureObjectKind.LAWBOOK_ENTRY
 exact=compute_structure_mapping(_d("a",StructureFamily.ALGEBRAIC,("operation","term")),_d("b",StructureFamily.ALGEBRAIC,("operation","term")))
 cross=compute_structure_mapping(_d("c",StructureFamily.ALGEBRAIC,("operation","term","formula")),_d("d",StructureFamily.LOGICAL,("formula","proof")))
 mismatch=compute_structure_mapping(_d("e",StructureFamily.ORDER,("order",)),_d("f",StructureFamily.PROBABILISTIC,("probability",)))
 assert exact.compatibility==ProjectionCompatibility.EXACT_SAME_STRUCTURE
 assert cross.compatibility==ProjectionCompatibility.CROSS_FAMILY_COMPATIBLE
 assert mismatch.compatibility in {ProjectionCompatibility.TYPE_MISMATCH,ProjectionCompatibility.TOO_WEAK}
 assert typed_projection_candidate_from_mapping(mismatch).is_blocked() or typed_projection_candidate_from_mapping(mismatch).status==TypedProjectionStatus.NEEDS_REVIEW
def test_store_report_and_bridges():
 r=build_structure_registry_report(descriptors=[_d("a",StructureFamily.ALGEBRAIC,("operation","term")),_d("b",StructureFamily.ALGEBRAIC,("operation","term"))])
 assert r.descriptors and r.mappings and r.typed_projection_candidates
 assert all(x.status==LawbookEntryStatus.CANDIDATE for x in structure_report_to_lawbook_candidates(r))
 assert structure_report_to_projection_candidates(r)
 assert all(x.advisory for x in structure_report_to_continuation_outputs(r))
 assert all(x.advisory for x in structure_report_to_curriculum(r).stages)
 assert structure_report_to_discovery_value_scores(r)
 assert not any(x.has_truth_boundary() for x in structure_report_to_process_episodes(r))
 assert structure_report_to_habit_observations(r) and structure_report_to_reason_observations(r)
 assert structure_report_to_structural_identity_objects(r)
 assert all(step.phase.value!="FIXATION" for step in structure_report_to_alchemical_trace(r).steps)
 assert all(x.outcome not in {AgentExperienceOutcome.VERIFIED_PROOF,AgentExperienceOutcome.FINITE_COUNTERMODEL} for x in structure_report_to_agent_experiences(r))
 assert isinstance(structure_report_to_route_telemetry_events(r)[0],dict)
def test_audit_and_cli(tmp_path):
 bad=_d("bad",StructureFamily.UNKNOWN,()); bad.advisory=False
 assert any(x["severity"]=="CRITICAL" for x in audit_structure_descriptor(bad))
 tp=TypedProjectionCandidate("t","m",status=TypedProjectionStatus.BLOCKED_CONFLICT,route="bad",metadata={"terminal_form":"VERIFIED_PROOF"})
 assert len(audit_typed_projection_candidate(tp))>=2
 raw=tmp_path/"raw.jsonl"; raw.write_text('{"operation":"*","term":"x*x"}\n{"operation":"*","term":"y*y"}\n')
 typed=tmp_path/"typed.jsonl"; projs=tmp_path/"projs.jsonl"; cont=tmp_path/"cont.jsonl"; eps=tmp_path/"eps.jsonl"
 subprocess.run([sys.executable,"scripts/run_structure_registry.py","--raw-event-jsonl",str(raw),"--out-typed-projections-jsonl",str(typed),"--out-projection-candidates-jsonl",str(projs),"--out-continuation-outputs-jsonl",str(cont),"--out-process-episodes-jsonl",str(eps)],check=True)
 assert typed.read_text() and projs.read_text() and cont.read_text() and eps.read_text()
