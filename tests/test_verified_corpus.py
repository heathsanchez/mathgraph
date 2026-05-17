import subprocess,sys
from mathgraph.verified_corpus import *
from mathgraph.roadmap_alignment import check_roadmap_alignment

def test_roundtrips_and_defaults(tmp_path):
 m=build_default_micro_corpus_manifest(tmp_path/"corpus"); f=build_verified_corpus_file(m,m.files[0]); e=VerifiedCorpusEntry("e",m.corpus_id,f.file_id,"x",VerifiedCorpusEntryKind.THEOREM); edge=VerifiedCorpusDependencyEdge("d",m.corpus_id,"a","b"); r=ingest_verified_corpus(m,workspace_root=tmp_path/"w")
 for x in (m,f,e,edge,r): assert x.from_json(x.to_json()).to_dict()==x.to_dict()
 assert {"CorpusBasic.lean","CorpusBadUnsafe.lean"}<=set(default_micro_corpus_files())
 assert load_verified_corpus_manifest(tmp_path/"corpus"/"corpus_manifest.json").corpus_id==m.corpus_id

def test_extract_build_and_dry_run(tmp_path):
 m=build_default_micro_corpus_manifest(tmp_path/"corpus"); f=build_verified_corpus_file(m,m.files[-1])
 assert extract_imports_from_lean_text("import A.B\n")==("A.B",)
 assert [x.name for x in extract_declared_entries_from_lean_text("theorem foo : True := by\n trivial",corpus_id="c",file_id="f")]==["foo"]
 assert f.imports and f.declared_names
 r=ingest_verified_corpus(m,workspace_root=tmp_path/"w"); assert r.ok() and not r.verified_entry_count()
 assert any(e.status==VerifiedCorpusEntryStatus.REJECTED_UNSAFE for e in r.entries)
 assert isinstance(build_dependency_edges(m.corpus_id,r.entries,r.files),list)
 assert "Verified Corpus" in verified_corpus_report_to_markdown(r)
 assert verified_corpus_report_to_dependency_graph(r)["metadata"]["advisory"]

def test_live_ingestion_replay_and_bridges(tmp_path):
 r=ingest_verified_corpus(build_default_micro_corpus_manifest(tmp_path/"corpus"),workspace_root=tmp_path/"w",allow_execution=True,allow_missing_verifier=True)
 assert not any(e.has_boundary_evidence() for e in r.entries if e.failure_kind!=VerifiedCorpusFailureKind.NONE)
 assert r.summary["file_total"]==6 and r.summary["entry_total"]>=6
 assert len(verified_corpus_report_to_lawbook_candidates(r))==r.verified_entry_count()
 no=review_and_optionally_accept_verified_corpus_entries(r); yes=review_and_optionally_accept_verified_corpus_entries(r,accept_in_memory=True)
 assert no["known_skip_total"]==0 and yes["known_skip_total"]==yes["accepted_total"]
 assert verified_corpus_report_to_api_response(r).truth_status in {ApiTruthStatus.BOUNDARY_REQUIRED,ApiTruthStatus.BOUNDARY_EVIDENCE_PRESENT}
 assert verified_corpus_report_to_process_episodes(r) and verified_corpus_report_to_proof_digestion_inputs(r)
 assert verified_corpus_report_to_discovery_value_scores(r) and verified_corpus_report_to_structural_identity_objects(r)
 assert verified_corpus_report_to_route_telemetry_events(r) and verified_corpus_report_to_agent_experiences(r)

def test_audits_alignment_and_cli(tmp_path):
 bad=VerifiedCorpusEntry("e","c","f","bad",VerifiedCorpusEntryKind.THEOREM,VerifiedCorpusEntryStatus.VERIFIED_BY_LOCAL_VERIFIER)
 assert audit_verified_corpus_entry(bad)
 assert audit_verified_corpus_dependency_edge(VerifiedCorpusDependencyEdge("d","c","a","b",advisory=False))
 assert check_roadmap_alignment(verified_corpus_entries=[bad]).critical_count()
 clean=ingest_verified_corpus(build_default_micro_corpus_manifest(tmp_path/"corpus"),workspace_root=tmp_path/"w"); assert check_roadmap_alignment(verified_corpus_reports=[clean]).critical_count()==0
 md=tmp_path/"corpus.md"; graph=tmp_path/"graph.json"
 subprocess.run([sys.executable,"scripts/run_verified_corpus.py","--ensure-micro-corpus","--corpus-root",str(tmp_path/"cli"),"--out-markdown",str(md),"--out-dependency-graph-json",str(graph)],check=True)
 assert md.exists() and graph.exists()
