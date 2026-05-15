import subprocess,sys
from mathgraph.agent_biography import AgentExperience,AgentExperienceOutcome
from mathgraph.alchemy import AlchemicalPhase
from mathgraph.reason_compression import *
from mathgraph.roadmap_alignment import check_roadmap_alignment
def _obs(i,atoms=("route:projection","basin:x"),gain=2,risk=0): return ReasonObservation(f"o{i}",ReasonObservationKind.RAW_EVENT,atoms=atoms,gain_units=gain,risk_score=risk)
def test_serialization():
 o=_obs(1); c=ReasonCandidate("c",ReasonCandidateKind.SUFFICIENT_REASON,("a",)); n=ReasonNode("n",ReasonCandidateKind.SUFFICIENT_REASON); rv=ReasonReview("r","c",ReasonReviewDecision.ACCEPT); rep=ReasonCompressionReport("rep",[o],[c],[rv],[n])
 assert ReasonObservation.from_json(o.to_json()).observation_id=="o1"; assert ReasonCandidate.from_json(c.to_json()).candidate_id=="c"; assert ReasonNode.from_json(n.to_json()).reason_id=="n"; assert ReasonReview.from_json(rv.to_json()).review_id=="r"; assert ReasonCompressionReport.from_json(rep.to_json()).report_id=="rep"
def test_atoms():
 assert normalize_reason_atom(" Route X ")=="route_x"; atoms,k=extract_atoms_from_mapping({"route":"projection","status":"ok","certificate_id":"c","trust_level":"verified"}); assert any("route" in a for a in atoms) and classify_atom_kind("route:x")==ReasonAtomKind.ROUTE
def test_candidates_and_minimality():
 cs=build_reason_candidates([_obs(1),_obs(2),_obs(3)])
 assert cs and cs[0].support_count>=3 and cs[0].coverage_ratio>0 and cs[0].complexity>=1
 single=[c for c in cs if c.atoms==("basin:x",)][0]; assert single.load_bearing_atoms
 multi=ReasonCandidate("m",ReasonCandidateKind.SUFFICIENT_REASON,("route:projection","basin:x"),support_count=3,sufficiency_score=1); checked=check_reason_minimality(multi,[_obs(1),_obs(2),_obs(3)]); assert checked.decorative_atoms
 assert not build_reason_candidates([_obs(1)],min_support=1)[0].is_promotable()
 assert not ReasonCandidate("x",ReasonCandidateKind.SUFFICIENT_REASON,tuple(str(i) for i in range(7)),support_count=3,coverage_ratio=1,sufficiency_score=1,load_bearing_atoms=("1",)).is_promotable()
 assert not ReasonCandidate("x",ReasonCandidateKind.SUFFICIENT_REASON,("a",),support_count=3,coverage_ratio=1,sufficiency_score=1,load_bearing_atoms=("a",),risk_score=.9).is_promotable()
def test_review_promote_apply():
 good=[c for c in build_reason_candidates([_obs(1),_obs(2),_obs(3)]) if c.atoms==("basin:x",)][0]
 assert review_reason_candidate(good).decision==ReasonReviewDecision.ACCEPT
 assert review_reason_candidate(ReasonCandidate("l",ReasonCandidateKind.SUFFICIENT_REASON,("a",),support_count=1,coverage_ratio=1,load_bearing_atoms=("a",))).decision==ReasonReviewDecision.NEEDS_MORE_EVIDENCE
 assert review_reason_candidate(ReasonCandidate("m",ReasonCandidateKind.SUFFICIENT_REASON,("a",),support_count=3,coverage_ratio=1,sufficiency_score=1)).decision==ReasonReviewDecision.NEEDS_MINIMALITY_CHECK
 assert review_reason_candidate(ReasonCandidate("t",ReasonCandidateKind.SUFFICIENT_REASON,("a",),support_count=3,coverage_ratio=1,sufficiency_score=1,load_bearing_atoms=("a",),reason_text="this is proof")).decision==ReasonReviewDecision.NEEDS_FORMALIZATION
 node=promote_reason_candidate(good,review_reason_candidate(good)); assert node.is_accepted() and node.advisory and node.explains({"basin":"x"}); assert not ReasonNode("z",ReasonCandidateKind.SUFFICIENT_REASON).explains({})
 ranked=rank_routes_with_reasons([node],[{"basin":"x","score":1},{"score":1}]); assert ranked[0]["reason_advisory_only"] and ranked[0]["reason_adjusted_score"]>ranked[1]["reason_adjusted_score"]
def test_bridges_audit_alignment():
 rep=build_reason_compression_report(observations=[_obs(1),_obs(2),_obs(3)],auto_promote=True)
 assert rep.advisory and rep.accepted_reason_count()>0
 assert all(x.status.value=="CANDIDATE" for x in reason_report_to_lawbook_candidates(rep))
 assert all(x.advisory and not x.is_terminal() for x in reason_report_to_continuation_outputs(rep))
 assert all(x.advisory for x in reason_report_to_curriculum(rep).stages)
 assert all(x.advisory for x in reason_report_to_discovery_value_scores(rep))
 assert isinstance(reason_report_to_structural_identity_objects(rep)[0],dict)
 assert AlchemicalPhase.FIXATION not in reason_report_to_alchemical_trace(rep).phases_seen()
 assert all(x.outcome not in {AgentExperienceOutcome.VERIFIED_PROOF,AgentExperienceOutcome.FINITE_COUNTERMODEL} for x in reason_report_to_agent_experiences(rep))
 bad=ReasonNode("bad",ReasonCandidateKind.SUFFICIENT_REASON,ReasonStatus.ACCEPTED,advisory=False,reason_text="proof")
 assert {x["code"] for x in audit_reason_node(bad)} >= {"REASON_NODE_NON_ADVISORY","REASON_ACCEPTED_WITHOUT_LOAD_BEARING","REASON_TEXT_CLAIMS_PROOF"}
 assert check_roadmap_alignment(reason_nodes=[bad]).critical_count()>=3
def test_cli(tmp_path):
 raw=tmp_path/"raw.jsonl"; raw.write_text('{"route":"projection","basin":"x","gain_units":2}\n'*3); scores=tmp_path/"scores.jsonl"; scores.write_text('{"basin":"x","score":1}\n')
 for args in (["--out-report-json",str(tmp_path/"empty.json")],["--raw-event-jsonl",str(raw),"--auto-promote","--route-scores-jsonl",str(scores),"--out-candidates-jsonl",str(tmp_path/"c.jsonl"),"--out-reason-nodes-jsonl",str(tmp_path/"n.jsonl"),"--out-ranked-routes-jsonl",str(tmp_path/"rank.jsonl"),"--out-lawbook-candidates-jsonl",str(tmp_path/"l.jsonl"),"--out-continuation-outputs-jsonl",str(tmp_path/"o.jsonl"),"--out-curriculum-json",str(tmp_path/"cur.json"),"--out-discovery-value-scores-jsonl",str(tmp_path/"v.jsonl"),"--out-structural-objects-jsonl",str(tmp_path/"s.jsonl")]):
  assert subprocess.run([sys.executable,"scripts/run_reason_compression.py",*args]).returncode==0
