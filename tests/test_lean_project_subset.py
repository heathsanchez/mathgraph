import subprocess,sys
from mathgraph.lean_project_subset import *
from mathgraph.roadmap_alignment import check_roadmap_alignment
def test_roundtrips_defaults_and_paths(tmp_path):
 m=build_default_micro_project_manifest(tmp_path/"project"); f=build_lean_project_file(m,m.files[0]); e=LeanProjectEntry("e",m.project_id,f.file_id,f.module_name,"x"); edge=LeanProjectDependencyEdge("d",m.project_id,"entry","a","entry","b",LeanProjectDependencyKind.REFERENCES_DECLARATION); r=ingest_lean_project_subset(m,workspace_root=tmp_path/"w")
 for x in (m,f,e,edge,r): assert x.from_json(x.to_json()).to_dict()==x.to_dict()
 assert {"MathGraphMicro/Basic.lean","MathGraphMicro/UseBasic.lean","MathGraphMicro/BadUnsafe.lean"}<=set(default_micro_project_files())
 assert load_lean_project_manifest(tmp_path/"project"/"project_manifest.json").project_id==m.project_id
 assert module_name_from_path("MathGraphMicro/Basic.lean")=="MathGraphMicro.Basic"
 assert path_from_module_name("MathGraphMicro.Basic",project_root=tmp_path)==tmp_path/"MathGraphMicro"/"Basic.lean"
def test_extract_edges_and_dry_run(tmp_path):
 m=build_default_micro_project_manifest(tmp_path/"project"); f=build_lean_project_file(m,m.files[2])
 assert extract_imports_from_lean_text("import A.B\n")==("A.B",)
 assert [x.name for x in extract_declared_entries_from_lean_project_text("theorem foo : True := by\n trivial",project_id="p",file_id="f",module_name="M")]==["foo"]
 assert "mg_basic_true" in extract_referenced_names_from_lean_text("exact mg_basic_true",["mg_basic_true"])
 assert f.imports and f.declared_names
 r=ingest_lean_project_subset(m,workspace_root=tmp_path/"w"); assert r.ok() and not r.verified_entry_count()
 assert r.dependency_edge_count() and r.import_edge_count() and r.reference_edge_count()
 assert any(e.status==LeanProjectEntryStatus.REJECTED_UNSAFE for e in r.entries)
 assert "Lean Project Subset" in lean_project_report_to_markdown(r)
 assert lean_project_report_to_dependency_graph(r)["metadata"]["advisory"]
def test_live_replay_bridges_and_audits(tmp_path):
 r=ingest_lean_project_subset(build_default_micro_project_manifest(tmp_path/"project"),workspace_root=tmp_path/"w",allow_execution=True,allow_missing_verifier=True)
 assert not any(e.has_boundary_evidence() for e in r.entries if e.failure_kind!=LeanProjectFailureKind.NONE)
 assert r.summary["file_total"]==7 and r.summary["entry_total"]>=7
 assert len(lean_project_report_to_lawbook_candidates(r))==r.verified_entry_count()
 no=review_and_optionally_accept_lean_project_entries(r); yes=review_and_optionally_accept_lean_project_entries(r,accept_in_memory=True)
 assert no["known_skip_total"]==0 and yes["known_skip_total"]==yes["accepted_total"]
 assert lean_project_report_to_api_response(r).truth_status in {ApiTruthStatus.BOUNDARY_REQUIRED,ApiTruthStatus.BOUNDARY_EVIDENCE_PRESENT}
 assert lean_project_report_to_process_episodes(r) and lean_project_report_to_proof_digestion_inputs(r)
 assert lean_project_report_to_discovery_value_scores(r) and lean_project_report_to_structural_identity_objects(r)
 assert lean_project_report_to_route_telemetry_events(r) and lean_project_report_to_agent_experiences(r)
 assert lean_project_report_to_verified_corpus_report(r).entry_count()==r.entry_count()
 bad=LeanProjectEntry("b","p","f","M","bad",status=LeanProjectEntryStatus.VERIFIED_BY_LOCAL_VERIFIER)
 assert audit_lean_project_entry(bad)
 assert audit_lean_project_dependency_edge(LeanProjectDependencyEdge("d","p","entry","a","entry","b",LeanProjectDependencyKind.REFERENCES_DECLARATION,advisory=False))
 assert check_roadmap_alignment(lean_project_entries=[bad]).critical_count()
 assert check_roadmap_alignment(lean_project_reports=[ingest_lean_project_subset(build_default_micro_project_manifest(tmp_path/"clean"),workspace_root=tmp_path/"cw")]).critical_count()==0
def test_cli(tmp_path):
 md=tmp_path/"project.md"; graph=tmp_path/"graph.json"
 subprocess.run([sys.executable,"scripts/run_lean_project_subset.py","--ensure-micro-project","--project-root",str(tmp_path/"cli"),"--out-markdown",str(md),"--out-dependency-graph-json",str(graph)],check=True)
 assert md.exists() and graph.exists()
