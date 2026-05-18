import subprocess,sys
from mathgraph.mathlib_declaration_discovery import *
from mathgraph.roadmap_alignment import check_roadmap_alignment
def test_roundtrip_requests_and_extractors(tmp_path):
 req=build_synthetic_mathlib_discovery_request(tmp_path/"synthetic"); r=run_mathlib_declaration_discovery(req); m=r.modules[0]; d=r.declarations[0]; h=MathlibDeclarationReferenceHint("h",req.request_id,d.declaration_id,"x")
 for x in (req,m,d,h,r): assert x.from_json(x.to_json()).to_dict()==x.to_dict()
 assert default_mathlib_discovery_request_dict()["module_files"]
 assert synthetic_mathlib_discovery_request_dict(tmp_path)["module_files"]
 a,b=ensure_default_mathlib_discovery_examples(tmp_path/"examples"); assert a.exists() and b.exists()
 assert load_mathlib_discovery_request(a).request_id
 assert detect_mathlib_discovery_environment({"request_id":"x","name":"x","project_root":str(tmp_path/"missing"),"module_files":[]})[0]==MathlibDiscoveryEnvironmentStatus.MISSING_PROJECT_ROOT
 assert "-- hi" not in strip_lean_comments("theorem x -- hi\n/- bye -/")
 assert extract_imports_from_lean_text("import A.B\n")==("A.B",)
 assert extract_namespace_stack_from_lean_text("namespace A\nnamespace B\n")==("A","B")
 assert {x["kind"] for x in extract_declaration_blocks_from_lean_text("theorem a : True := by trivial\nlemma b : True := by trivial\ndef c := 1\nexample : True := by trivial")}=={"theorem","lemma","def","example"}
 assert qualify_declaration_name("x",module_name="M",module_prefix="Mathlib")=="Mathlib.x"
 assert extract_referenced_names_from_lean_text("exact foo",["foo","bar"])==("foo",)
def test_discovery_manifest_downstream_and_audits(tmp_path):
 req=build_synthetic_mathlib_discovery_request(tmp_path/"synthetic"); r=run_mathlib_declaration_discovery(req)
 assert r.declaration_count()==10 and r.selected_declaration_count()==10 and r.reference_hint_count()>0
 assert r.generated_manifest and len(r.generated_manifest.files)==5
 assert r.summary["downstream_verified_total"]==0
 dry=run_mathlib_declaration_discovery(req,run_allowlist_ingestion=True); assert dry.allowlist_ingestion_report.boundary_evidence_count()==0
 live=run_mathlib_declaration_discovery(req,run_allowlist_ingestion=True,allow_execution=True,allow_missing_verifier=True)
 assert live.allowlist_ingestion_report.verified_entry_count() in {0,10}
 assert "Mathlib Declaration Discovery" in mathlib_discovery_report_to_markdown(r)
 assert mathlib_discovery_report_to_reference_graph(r)["metadata"]["advisory"]
 assert mathlib_discovery_report_to_api_response(r).truth_status==ApiTruthStatus.ADVISORY_ONLY
 assert mathlib_discovery_report_to_process_episodes(r) and mathlib_discovery_report_to_proof_digestion_inputs(r)
 assert mathlib_discovery_report_to_discovery_value_scores(r) and mathlib_discovery_report_to_structural_identity_objects(r)
 assert mathlib_discovery_report_to_route_telemetry_events(r) and mathlib_discovery_report_to_agent_experiences(r)
 assert all(x.selection_status==MathlibSelectionStatus.SELECTED for x in r.declarations)
 bad=MathlibDiscoveredDeclaration("d","r","m","M","x","M.x",advisory=False)
 assert audit_mathlib_discovered_declaration(bad)
 assert audit_mathlib_reference_hint(MathlibDeclarationReferenceHint("h","r","d","x",advisory=False))
 assert check_roadmap_alignment(mathlib_discovered_declarations=[bad]).critical_count()
 assert check_roadmap_alignment(mathlib_discovery_reports=[r]).critical_count()==0
def test_filters_and_cli(tmp_path):
 req=build_synthetic_mathlib_discovery_request(tmp_path/"synthetic"); req.module_files[0]["include_kinds"]=["lemma"]; m,ds=discover_module_declarations(req,req.module_files[0]); assert all(d.selection_status==MathlibSelectionStatus.EXCLUDED_BY_KIND for d in ds)
 req=build_synthetic_mathlib_discovery_request(tmp_path/"synthetic2"); req.module_files[0]["name_contains"]=["identity"]; _,ds=discover_module_declarations(req,req.module_files[0]); assert sum(d.selection_status==MathlibSelectionStatus.SELECTED for d in ds)==1
 md=tmp_path/"d.md"; graph=tmp_path/"g.json"; manifest=tmp_path/"m.json"
 subprocess.run([sys.executable,"scripts/run_mathlib_declaration_discovery.py","--ensure-examples"],check=True)
 subprocess.run([sys.executable,"scripts/run_mathlib_declaration_discovery.py","--use-synthetic-request","--build-manifest","--out-markdown",str(md),"--out-reference-graph-json",str(graph),"--out-generated-manifest-json",str(manifest)],check=True)
 assert md.exists() and graph.exists() and manifest.exists()
