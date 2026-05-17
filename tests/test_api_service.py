import json,subprocess,sys,threading,urllib.request
from mathgraph.api_service import *
from mathgraph.certificates import TerminalForm
from mathgraph.lawbook import LawbookAcceptanceBoundary,LawbookEntry,LawbookEntryKind,LawbookEntryStatus
from mathgraph.roadmap_alignment import check_roadmap_alignment
def _entry():
    return LawbookEntry("e",LawbookEntryKind.VERIFIED_PROOF_ENTRY,LawbookEntryStatus.ACCEPTED,source="x",target="y",terminal_form=TerminalForm.VERIFIED_PROOF,certificate_id="c",verifier_boundary_crossed=True,acceptance_boundary=LawbookAcceptanceBoundary.VERIFIED_PROOF,advisory=False)
def test_roundtrips_and_health():
 req=ApiRequest("q",ApiRoute.HEALTH); health=ApiHealth(); audit=ApiAuditResult("a"); rr=ApiRouteResult("r",ApiRoute.HEALTH,ApiResponseStatus.OK); resp=ApiResponse("x","q",ApiRoute.HEALTH,ApiResponseStatus.OK); state=ApiServiceState()
 for x in (req,health,audit,rr,resp): assert x.from_json(x.to_json()).to_dict()==x.to_dict()
 assert ApiServiceState.from_dict(state.to_dict()).to_dict()==state.to_dict()
 h=MathGraphLocalClient().health(); assert h.truth_status==ApiTruthStatus.NO_CLAIM and h.health.implemented_routes
def test_routes_boundaries_and_payloads():
 c=MathGraphLocalClient(ApiServiceState([_entry()])); assert c.query({"source":"z"}).status==ApiResponseStatus.NOT_FOUND
 q=c.query({"source":"x","target":"y"}); assert q.truth_status==ApiTruthStatus.VERIFIED_PROOF and q.has_boundary_evidence()
 before=c.state.accepted_entry_count(); s=c.submit({"text":"Theorem: every magma x*x=x."}); assert s.truth_status==ApiTruthStatus.BOUNDARY_REQUIRED and c.state.accepted_entry_count()==before
 assert c.semantic_intake({"text":"theorem x"}).result.artifact_kinds[0]==ApiArtifactKind.SEMANTIC_REPORT.value
 assert c.formal_world_adapters({"source":"x=x","target":"y=y"}).result
 assert c.proof_system_integration({"text":"theorem foo : True := by trivial"}).result
 v=c.verifier_execution({"text":"theorem foo : True := by trivial"}); assert v.result and v.truth_status==ApiTruthStatus.BOUNDARY_REQUIRED
 assert c.verifier_fixtures({}).result and c.verified_corpus({}).result and c.e2e_testdrive({}).result
 for name in ("schedule","project","explain","process_memory","discovery_value","lawbook_acceptance_review","structural_identity","habits","reasons","structures","roles","analogies"):
  assert getattr(c,name)({"text":"theorem x"}).boundary_policy
 assert c.request(ApiRequest("u",ApiRoute.UNKNOWN)).status==ApiResponseStatus.UNSUPPORTED_ROUTE
 assert api_payload_to_objects({"text":"x"}) and api_payload_to_objects({"texts":["x"]}) and api_payload_to_objects({"source":"x","target":"y"})
 assert not extract_boundary_evidence_from_objects([{"stdout":"verified successfully"}])["verifier_boundary_crossed"]
 assert artifact_to_api_dict({"x":1})["artifact_kind"]
def test_audits_alignment_cli_http(tmp_path):
 bad=ApiResponse("x",None,ApiRoute.SUBMIT,ApiResponseStatus.OK,ApiTruthStatus.VERIFIED_PROOF)
 assert audit_api_response(bad)
 assert audit_api_route_result(ApiRouteResult("r",ApiRoute.SUBMIT,ApiResponseStatus.OK,verifier_boundary_crossed=True))
 assert not audit_api_service_state(ApiServiceState())
 assert check_roadmap_alignment(api_responses=[bad]).critical_count()
 out=tmp_path/"resp.json"; subprocess.run([sys.executable,"scripts/run_api_service.py","--route","semantic-intake","--input-text","theorem x","--out-response-json",str(out)],check=True); assert out.exists()
 srv=serve_localhost(port=0); th=threading.Thread(target=srv.serve_forever,daemon=True); th.start(); host,port=srv.server_address
 try:
  assert json.loads(urllib.request.urlopen(f"http://{host}:{port}/health").read())["status"]=="OK"
  req=urllib.request.Request(f"http://{host}:{port}/semantic-intake",data=b'{"text":"theorem x"}',headers={"Content-Type":"application/json"}); assert json.loads(urllib.request.urlopen(req).read())["route"]=="SEMANTIC_INTAKE"
 finally: srv.shutdown()
