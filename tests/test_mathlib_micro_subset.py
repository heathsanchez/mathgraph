import subprocess,sys
from mathgraph.mathlib_micro_subset import *
from mathgraph.roadmap_alignment import check_roadmap_alignment
def test_roundtrips_defaults_and_environment(tmp_path):
 m=build_default_mathlib_micro_manifest(tmp_path/"subset"); env=detect_mathlib_micro_environment(m); f=build_mathlib_micro_file(m,m.files[0]); e=MathlibMicroEntry("e",m.subset_id,f.file_id,f.module_name,"x","Mathlib.MathGraph.x"); edge=MathlibMicroDependencyEdge("d",m.subset_id,"entry","a","entry","b",MathlibMicroDependencyKind.REFERENCES_DECLARATION); r=ingest_mathlib_micro_subset(m,workspace_root=tmp_path/"w")
 for x in (m,env,f,e,edge,r): assert x.from_json(x.to_json()).to_dict()==x.to_dict()
 assert {"Mathlib/MathGraph/Basic.lean","Mathlib/MathGraph/UseBasic.lean","Mathlib/MathGraph/BadUnsafe.lean"}<=set(default_mathlib_micro_files())
 assert load_mathlib_micro_manifest(tmp_path/"subset"/"mathlib_micro_manifest.json").subset_id==m.subset_id
 assert detect_mathlib_micro_environment({"subset_id":"x","name":"x","project_root":str(tmp_path/"missing"),"files":[]}).status==MathlibMicroEnvironmentStatus.MISSING_PROJECT_ROOT
 assert mathlib_module_name_from_path("Mathlib/MathGraph/Basic.lean")=="Mathlib.MathGraph.Basic"
 assert mathlib_path_from_module_name("Mathlib.MathGraph.Basic",project_root=tmp_path)==tmp_path/"Mathlib"/"MathGraph"/"Basic.lean"
 assert qualify_declaration_name("x",module_name="M",module_prefix="Mathlib.MathGraph")=="Mathlib.MathGraph.x"
def test_extract_edges_and_dry_run(tmp_path):
 m=build_default_mathlib_micro_manifest(tmp_path/"subset"); f=build_mathlib_micro_file(m,m.files[3])
 assert extract_imports_from_lean_text("import A.B\n")==("A.B",)
 es=extract_declared_entries_from_mathlib_micro_text("namespace Mathlib\nnamespace MathGraph\ntheorem foo : True := by\n trivial",subset_id="s",file_id="f",module_name="M")
 assert es[0].name=="foo" and es[0].full_name=="Mathlib.MathGraph.foo"
 assert "mgml_true" in extract_referenced_names_from_lean_text("exact mgml_true",["mgml_true"])
 assert f.imports and f.declared_names and f.declared_full_names
 r=ingest_mathlib_micro_subset(m,workspace_root=tmp_path/"w"); assert r.ok() and not r.verified_entry_count()
 assert r.dependency_edge_count() and r.import_edge_count() and r.reference_edge_count()
 assert any(e.status==MathlibMicroEntryStatus.REJECTED_UNSAFE for e in r.entries)
 assert "Mathlib Micro-Subset" in mathlib_micro_report_to_markdown(r)
 assert mathlib_micro_report_to_dependency_graph(r)["metadata"]["advisory"]
def test_live_bridges_and_audits(tmp_path):
 r=ingest_mathlib_micro_subset(build_default_mathlib_micro_manifest(tmp_path/"subset"),workspace_root=tmp_path/"w",allow_execution=True,allow_missing_verifier=True)
 assert not any(e.has_boundary_evidence() for e in r.entries if e.failure_kind!=MathlibMicroFailureKind.NONE)
 assert r.summary["file_total"]==8 and r.summary["entry_total"]>=8
 assert len(mathlib_micro_report_to_lawbook_candidates(r))==r.verified_entry_count()
 no=review_and_optionally_accept_mathlib_micro_entries(r); yes=review_and_optionally_accept_mathlib_micro_entries(r,accept_in_memory=True)
 assert no["known_skip_total"]==0 and yes["known_skip_total"]==yes["accepted_total"]
 assert mathlib_micro_report_to_api_response(r).truth_status in {ApiTruthStatus.BOUNDARY_REQUIRED,ApiTruthStatus.BOUNDARY_EVIDENCE_PRESENT}
 assert mathlib_micro_report_to_process_episodes(r) and mathlib_micro_report_to_proof_digestion_inputs(r)
 assert mathlib_micro_report_to_discovery_value_scores(r) and mathlib_micro_report_to_structural_identity_objects(r)
 assert mathlib_micro_report_to_route_telemetry_events(r) and mathlib_micro_report_to_agent_experiences(r)
 assert mathlib_micro_report_to_lean_project_report(r).entry_count()==r.entry_count()
 assert mathlib_micro_report_to_verified_corpus_report(r).entry_count()==r.entry_count()
 bad=MathlibMicroEntry("b","s","f","M","bad","Mathlib.MathGraph.bad",status=MathlibMicroEntryStatus.VERIFIED_BY_LOCAL_VERIFIER)
 assert audit_mathlib_micro_entry(bad) and audit_mathlib_micro_dependency_edge(MathlibMicroDependencyEdge("d","s","entry","a","entry","b",MathlibMicroDependencyKind.REFERENCES_DECLARATION,advisory=False))
 assert audit_mathlib_environment_report(MathlibEnvironmentReport("env","s",advisory=False))
 assert check_roadmap_alignment(mathlib_micro_entries=[bad]).critical_count()
 assert check_roadmap_alignment(mathlib_micro_reports=[ingest_mathlib_micro_subset(build_default_mathlib_micro_manifest(tmp_path/"clean"),workspace_root=tmp_path/"cw")]).critical_count()==0
def test_cli(tmp_path):
 md=tmp_path/"subset.md"; graph=tmp_path/"graph.json"
 subprocess.run([sys.executable,"scripts/run_mathlib_micro_subset.py","--ensure-synthetic-subset","--project-root",str(tmp_path/"cli"),"--out-markdown",str(md),"--out-dependency-graph-json",str(graph)],check=True)
 assert md.exists() and graph.exists()
