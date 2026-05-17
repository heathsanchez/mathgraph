import shutil,subprocess,sys
from mathgraph.verifier_fixtures import *
from mathgraph.roadmap_alignment import check_roadmap_alignment
def test_fixture_roundtrips_files_and_suite(tmp_path):
 paths=ensure_default_lean_fixtures(tmp_path/"fixtures"); suite=build_default_lean_fixture_suite(tmp_path/"fixtures")
 assert len(paths)==10 and len(suite.fixtures)==10
 assert {"mathgraph_smoke_true.lean","mathgraph_bad_sorry.lean"}<=set(default_lean_fixture_texts())
 assert all(f.expected_theorem_names for f in suite.fixtures if f.should_create_boundary)
 assert all(not f.should_create_boundary for f in suite.fixtures if f.risk!=VerifierFixtureRisk.SAFE)
 r=run_verifier_fixture_suite(suite,workspace_root=tmp_path/"dry")
 for x in (suite.fixtures[0],r.results[0],suite,r): assert x.from_json(x.to_json()).to_dict()==x.to_dict()
 assert r.ok() and not r.boundary_evidence_count()
 assert "fixture" in verifier_fixture_suite_result_to_markdown(r).lower()
def test_fixture_rejections_and_live_behavior(tmp_path):
 suite=build_default_lean_fixture_suite(tmp_path/"fixtures"); dry=run_verifier_fixture_suite(suite,workspace_root=tmp_path/"dry")
 by_name={x.fixture_name:x for x in dry.results}
 for name in ("mathgraph_bad_sorry","mathgraph_bad_axiom","mathgraph_bad_admit","mathgraph_bad_expected_missing"): assert not by_name[name].actual_boundary
 live=run_verifier_fixture_suite(suite,workspace_root=tmp_path/"live",allow_execution=True,allow_missing_verifier=True)
 if shutil.which("lean"):
  assert live.ok()
  assert sum(x.actual_boundary for x in live.results if x.metadata["risk"]=="SAFE")==4
  assert not any(x.actual_boundary for x in live.results if x.metadata["risk"]!="SAFE")
 else: assert live.summary["skipped_total"]>=4
 replay=review_and_optionally_accept_verified_fixture_evidence(live,accept_in_memory=False); assert replay["known_skip_total"]==0
 accepted=review_and_optionally_accept_verified_fixture_evidence(live,accept_in_memory=True); assert accepted["known_skip_total"]==accepted["accepted_total"]
def test_fixture_audits_alignment_and_cli(tmp_path):
 bad=VerifierFixtureResult("r","f","bad",VerifierFixtureStatus.UNEXPECTED_BOUNDARY,expected_boundary=False,actual_boundary=True,metadata={"risk":"UNSAFE_MARKER"})
 assert audit_verifier_fixture_result(bad)
 assert check_roadmap_alignment(verifier_fixture_results=[bad]).critical_count()
 md=tmp_path/"suite.md"; subprocess.run([sys.executable,"scripts/run_verifier_fixtures.py","--ensure-fixtures","--fixture-root",str(tmp_path/"fixtures"),"--out-markdown",str(md)],check=True); assert md.exists()
