import subprocess,sys
from mathgraph.mathlib_local_allowlist import *
from mathgraph.roadmap_alignment import check_roadmap_alignment

def test_roundtrips_defaults_and_environment(tmp_path):
    m=build_synthetic_external_allowlist_manifest(tmp_path/"synthetic")
    template=MathlibLocalAllowlistManifest.from_dict({"manifest_id":"m",**default_mathlib_local_allowlist_manifest_dict()})
    env=detect_mathlib_local_environment(m); f=build_mathlib_local_file(m,m.files[0]); e=MathlibLocalEntry("e",m.allowlist_id,f.file_id,f.module_name,"x","Mathlib.MathGraph.x"); edge=MathlibLocalDependencyEdge("d",m.allowlist_id,"entry","a","entry","b",MathlibLocalDependencyKind.REFERENCES_DECLARATION); r=ingest_mathlib_local_allowlist(m,workspace_root=tmp_path/"w")
    for x in (m,template,env,f,e,edge,r): assert x.from_json(x.to_json()).to_dict()==x.to_dict()
    assert not template.files[0]["expected_declaration_names"]
    a,b=ensure_default_mathlib_local_allowlist_examples(tmp_path/"examples"); assert a.exists() and b.exists()
    assert detect_mathlib_local_environment({"allowlist_id":"x","name":"x","project_root":str(tmp_path/"missing"),"files":[]}).status==MathlibLocalEnvironmentStatus.MISSING_PROJECT_ROOT
    assert mathlib_local_module_name_from_path("Mathlib/MathGraph/Basic.lean")=="Mathlib.MathGraph.Basic"
    assert mathlib_local_path_from_module_name("Mathlib.MathGraph.Basic",project_root=tmp_path)==tmp_path/"Mathlib"/"MathGraph"/"Basic.lean"

def test_extract_edges_and_dry_run(tmp_path):
    m=build_synthetic_external_allowlist_manifest(tmp_path/"synthetic"); f=build_mathlib_local_file(m,m.files[3])
    assert extract_imports_from_lean_text("import A.B\n")==("A.B",)
    es=extract_declared_entries_from_mathlib_local_text("namespace Mathlib\nnamespace MathGraph\ntheorem foo : True := by\n trivial",allowlist_id="s",file_id="f",module_name="M")
    assert es[0].full_name=="Mathlib.foo" or es[0].full_name.endswith(".foo")
    assert "mgml_true" in extract_referenced_names_from_lean_text("exact mgml_true",["mgml_true"])
    assert f.imports and f.declared_names and f.declared_full_names
    r=ingest_mathlib_local_allowlist(m,workspace_root=tmp_path/"w"); assert r.ok() and not r.verified_entry_count()
    assert r.dependency_edge_count() and r.import_edge_count() and r.reference_edge_count()
    assert any(e.status==MathlibLocalEntryStatus.REJECTED_UNSAFE for e in r.entries)
    assert "Mathlib Local Allowlist" in mathlib_local_report_to_markdown(r)
    assert mathlib_local_report_to_dependency_graph(r)["metadata"]["advisory"]

def test_empty_allowlist_live_bridges_and_audits(tmp_path):
    template=MathlibLocalAllowlistManifest.from_dict({"manifest_id":"m",**default_mathlib_local_allowlist_manifest_dict()})
    empty=ingest_mathlib_local_allowlist(template,workspace_root=tmp_path/"empty")
    assert empty.verified_entry_count()==0
    r=ingest_mathlib_local_allowlist(build_synthetic_external_allowlist_manifest(tmp_path/"synthetic"),workspace_root=tmp_path/"w",allow_execution=True,allow_missing_verifier=True)
    assert not any(e.has_boundary_evidence() for e in r.entries if e.failure_kind!=MathlibLocalFailureKind.NONE)
    assert len(mathlib_local_report_to_lawbook_candidates(r))==r.verified_entry_count()
    no=review_and_optionally_accept_mathlib_local_entries(r); yes=review_and_optionally_accept_mathlib_local_entries(r,accept_in_memory=True)
    assert no["known_skip_total"]==0 and yes["known_skip_total"]==yes["accepted_total"]
    assert mathlib_local_report_to_mathlib_micro_report(r).entry_count()==r.entry_count()
    assert mathlib_local_report_to_lean_project_report(r).entry_count()==r.entry_count()
    assert mathlib_local_report_to_verified_corpus_report(r).entry_count()==r.entry_count()
    bad=MathlibLocalEntry("b","s","f","M","bad","Mathlib.bad",status=MathlibLocalEntryStatus.VERIFIED_BY_LOCAL_VERIFIER)
    assert audit_mathlib_local_entry(bad)
    assert audit_mathlib_local_dependency_edge(MathlibLocalDependencyEdge("d","s","entry","a","entry","b",MathlibLocalDependencyKind.REFERENCES_DECLARATION,advisory=False))
    assert audit_mathlib_local_environment_report(MathlibLocalEnvironmentReport("env","s",advisory=False))
    assert check_roadmap_alignment(mathlib_local_entries=[bad]).critical_count()
def test_missing_verifier_skip(monkeypatch,tmp_path):
    assert hasattr(MathlibLocalFailureKind,"MISSING_VERIFIER")
    monkeypatch.setattr(shutil,"which",lambda name: None if name=="lean" else "/bin/x")
    r=ingest_mathlib_local_allowlist(build_synthetic_external_allowlist_manifest(tmp_path/"synthetic"),workspace_root=tmp_path/"w",allow_execution=True,allow_missing_verifier=True)
    assert any(e.status==MathlibLocalEntryStatus.SKIPPED_MISSING_VERIFIER and e.failure_kind==MathlibLocalFailureKind.MISSING_VERIFIER for e in r.entries)
    assert not r.boundary_evidence_count()

def test_cli(tmp_path):
    md=tmp_path/"allowlist.md"; graph=tmp_path/"graph.json"
    subprocess.run([sys.executable,"scripts/run_mathlib_local_allowlist.py","--ensure-examples"],check=True)
    subprocess.run([sys.executable,"scripts/run_mathlib_local_allowlist.py","--use-synthetic-external","--out-markdown",str(md),"--out-dependency-graph-json",str(graph)],check=True)
    assert md.exists() and graph.exists()
