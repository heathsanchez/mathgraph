import subprocess,sys
from mathgraph.agent_biography import AgentExperienceOutcome
from mathgraph.lawbook import LawbookEntryStatus
from mathgraph.semantic_intake import *
from mathgraph.roadmap_alignment import check_roadmap_alignment
def _report(text="Theorem: every magma satisfying x*x=x implies x*y=x. Proof: clearly this holds."): return build_semantic_intake_report([text])
def test_roundtrips():
 r=_report(); xs=[r.sources[0],r.segments[0],r.classifications[0],r.ambiguities[0],r.extractions[0],r.formalization_requests[0],r.routing_hints[0],r.tasks[0],r]
 for x in xs: assert x.from_json(x.to_json()).to_dict()==x.to_dict()
def test_sources_segmentation_and_classification():
 assert semantic_sources_from_object("theorem x")
 assert semantic_sources_from_object({"statement":"x=y","source":"x","target":"y"})
 s=semantic_sources_from_object("Theorem: x.\n\nLemma: y.")[0]; assert len(segment_semantic_source(s))==2
 assert classify_semantic_segment(segment_semantic_source(semantic_sources_from_object("Theorem: x")[0])[0]).claim_kind==SemanticClaimKind.THEOREM
 assert classify_semantic_segment(segment_semantic_source(semantic_sources_from_object("Conjecture: graph node edge")[0])[0]).domain_kind==SemanticDomainKind.GRAPH_THEORY
 assert classify_semantic_segment(segment_semantic_source(semantic_sources_from_object("theorem foo : True := by trivial")[0])[0]).domain_kind==SemanticDomainKind.PROOF_ASSISTANT
 assert classify_semantic_segment(segment_semantic_source(semantic_sources_from_object("verified successfully")[0])[0]).risk_level==SemanticRiskLevel.CRITICAL
def test_ambiguity_extraction_requests_routes_tasks():
 r=_report(); kinds={x.ambiguity_kind for x in r.ambiguities}; assert {SemanticAmbiguityKind.AMBIGUOUS_SYMBOL,SemanticAmbiguityKind.INFORMAL_PROOF_GAP,SemanticAmbiguityKind.NATURAL_LANGUAGE_ONLY}<=kinds
 ek={x.extraction_kind for x in r.extractions}; assert {SemanticExtractionKind.OPERATOR,SemanticExtractionKind.EQUATION,SemanticExtractionKind.IMPLICATION,SemanticExtractionKind.PROOF_MARKER}<=ek
 rk={x.request_kind for x in r.formalization_requests}; assert {FormalizationRequestKind.FORMALIZE_THEOREM,FormalizationRequestKind.FORMALIZE_EQUATIONAL_IMPLICATION}<=rk
 routes={x.target for x in r.routing_hints}; assert {SemanticRouteTarget.FORMAL_WORLD_ADAPTER,SemanticRouteTarget.CONTINUATION_CURRICULUM}<=routes
 tk={x.task_kind for x in r.tasks}; assert {SemanticIntakeTaskKind.ROUTE_TO_ADAPTER,SemanticIntakeTaskKind.SEARCH_COUNTERMODEL,SemanticIntakeTaskKind.BUILD_CURRICULUM}<=tk
def test_bridges_and_audits():
 r=_report(); assert semantic_report_to_formal_world_inputs(r) and semantic_report_to_proof_system_inputs(r)
 assert all(x.status==LawbookEntryStatus.CANDIDATE for x in semantic_report_to_lawbook_candidates(r))
 assert semantic_report_to_continuation_outputs(r) and semantic_report_to_curriculum(r).stages and semantic_report_to_discovery_value_scores(r)
 assert semantic_report_to_process_episodes(r) and semantic_report_to_proof_digestion_inputs(r)
 assert semantic_report_to_structure_descriptors(r) and semantic_report_to_typed_projection_candidates(r) and semantic_report_to_role_signatures(r) and semantic_report_to_analogy_sources(r)
 assert semantic_report_to_habit_observations(r) and semantic_report_to_reason_observations(r) and semantic_report_to_structural_identity_objects(r)
 assert all(x.phase.value!="FIXATION" for x in semantic_report_to_alchemical_trace(r).steps)
 assert all(x.outcome not in {AgentExperienceOutcome.VERIFIED_PROOF,AgentExperienceOutcome.FINITE_COUNTERMODEL} for x in semantic_report_to_agent_experiences(r))
 assert audit_semantic_source(SemanticSource("s",SemanticSourceKind.RAW_TEXT,"x",advisory=False))
 assert audit_formalization_request(FormalizationRequest("q","s","o",FormalizationRequestKind.FORMALIZE_THEOREM,metadata={"verifier_boundary_crossed":True}))
 assert check_roadmap_alignment(semantic_sources=[SemanticSource("s",SemanticSourceKind.RAW_TEXT,"x",advisory=False)]).critical_count()
def test_cli(tmp_path):
 src=tmp_path/"in.txt"; src.write_text("Theorem: every magma satisfying x*x=x has property P. Proof: clearly...")
 out=tmp_path/"out.jsonl"; fw=tmp_path/"fw.jsonl"
 subprocess.run([sys.executable,"scripts/run_semantic_intake.py","--input-file",str(src),"--out-tasks-jsonl",str(out),"--out-formal-world-inputs-jsonl",str(fw)],check=True)
 assert out.read_text() and fw.exists()
