"""Tiny local verified-corpus ingestion over strict verifier boundaries."""
from __future__ import annotations
import json,re,tempfile
from dataclasses import MISSING,dataclass,field
from datetime import datetime,timezone
from enum import Enum
from hashlib import sha256
from pathlib import Path
from typing import Any,Mapping,Sequence
from mathgraph.agent_biography import AgentExperience,AgentExperienceOutcome
from mathgraph.alchemy import AlchemicalPhase,AlchemicalStatus,AlchemicalTrace,make_alchemical_trace_id
from mathgraph.api_service import ApiRequest,ApiRoute,ApiSafetyLevel,ApiTruthStatus,make_api_request_id,route_result_from_artifacts
from mathgraph.certificates import TerminalForm
from mathgraph.discovery_value import DiscoveryValueObjectKind,DiscoveryValueScore,DiscoveryValueSignal,DiscoveryValueSignalKind
from mathgraph.hashing import content_id
from mathgraph.lawbook import LawbookAcceptanceBoundary,LawbookEntry,LawbookEntryKind,LawbookEntryStatus,LawbookStore,accept_lawbook_entry,make_lawbook_entry_id,make_lawbook_store_id,review_lawbook_candidate
from mathgraph.lawbook_query import query_lawbook_store_by_certificate
from mathgraph.process_memory import ProcessContextItem,ProcessContextKind,ProcessContextRole,ProcessEpisodeRecord,ProcessEpisodeStatus,make_process_episode_id
from mathgraph.verifier_execution import *
def _enum(n,v): return Enum(n,{x:x for x in v.split()},type=str)
VerifiedCorpusSourceKind=_enum("VerifiedCorpusSourceKind","LOCAL_FILES LOCAL_MICRO_CORPUS TRUSTED_IMPORT_SOURCE EXTERNAL_REFERENCE UNKNOWN")
VerifiedCorpusTrustPolicy=_enum("VerifiedCorpusTrustPolicy","LOCAL_VERIFIER_REQUIRED TRUSTED_IMPORT_REQUIRED ADVISORY_ONLY UNKNOWN")
VerifiedCorpusEntryKind=_enum("VerifiedCorpusEntryKind","THEOREM LEMMA EXAMPLE DEFINITION AXIOM IMPORT MODULE UNKNOWN")
VerifiedCorpusEntryStatus=_enum("VerifiedCorpusEntryStatus","ADVISORY_EXTRACTED VERIFIED_BY_LOCAL_VERIFIER TRUSTED_IMPORTED REJECTED_UNSAFE REJECTED_EXPECTED_MISSING REJECTED_VERIFIER_FAILED SKIPPED_MISSING_VERIFIER BLOCKED ERROR UNKNOWN")
VerifiedCorpusIngestionStatus=_enum("VerifiedCorpusIngestionStatus","NOT_RUN DRY_RUN COMPLETED COMPLETED_WITH_WARNINGS FAILED SKIPPED ERROR UNKNOWN")
VerifiedCorpusFailureKind=_enum("VerifiedCorpusFailureKind","NONE MISSING_VERIFIER UNSAFE_MARKER EXPECTED_THEOREM_MISSING IMPORT_ERROR TYPE_ERROR VERIFIER_FAILED TRUST_POLICY_BLOCKED MANIFEST_INVALID FILE_MISSING UNKNOWN")
def _serial(cls,enums=()):
 def td(self):
  d=dict(self.__dict__)
  for k in enums:
   if isinstance(d.get(k),Enum): d[k]=d[k].value
  for k,v in list(d.items()):
   if isinstance(v,tuple): d[k]=list(v)
   elif hasattr(v,"to_dict"): d[k]=v.to_dict()
   elif isinstance(v,list): d[k]=[x.to_dict() if hasattr(x,"to_dict") else x for x in v]
  return d
 @classmethod
 def fd(c,d):
  vals=[]
  for f in c.__dataclass_fields__.values():
   v=d[f.name] if f.name in d else f.default if f.default is not MISSING else f.default_factory() if f.default_factory is not MISSING else None
   if f.name in enums and v is not None:
    typ=globals()[str(f.type).split("|")[0]] if not isinstance(f.type,type) else f.type; v=typ(str(v))
   if getattr(f.type,"__origin__",None) is tuple and v is not None:v=tuple(v)
   vals.append(v)
  return c(*vals)
 cls.to_dict=td; cls.from_dict=fd; cls.to_json=lambda self:_j(self.to_dict()); cls.from_json=classmethod(lambda c,t:c.from_dict(json.loads(t))); return cls
@_serial
@dataclass
class VerifiedCorpusManifest:
 manifest_id:str; corpus_id:str; name:str; version:str="0.1"; source_kind:VerifiedCorpusSourceKind=VerifiedCorpusSourceKind.LOCAL_MICRO_CORPUS; trust_policy:VerifiedCorpusTrustPolicy=VerifiedCorpusTrustPolicy.LOCAL_VERIFIER_REQUIRED; proof_system:str="lean"; root_path:str|None=None; files:list[dict[str,Any]]=field(default_factory=list); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def write_json(self,p): _w(p,self.to_json())
 @classmethod
 def read_json(c,p): return c.from_json(Path(p).read_text())
@_serial
@dataclass
class VerifiedCorpusFile:
 file_id:str; corpus_id:str; path:str; module_name:str|None=None; text_hash:str|None=None; expected_theorem_names:tuple[str,...]=(); declared_names:tuple[str,...]=(); imports:tuple[str,...]=(); unsafe_markers:tuple[str,...]=(); expected_status:str=""; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
@_serial
@dataclass
class VerifiedCorpusEntry:
 entry_id:str; corpus_id:str; file_id:str; name:str; entry_kind:VerifiedCorpusEntryKind; status:VerifiedCorpusEntryStatus=VerifiedCorpusEntryStatus.ADVISORY_EXTRACTED; theorem_statement_excerpt:str=""; dependencies:tuple[str,...]=(); boundary_evidence_id:str|None=None; certificate_id:str|None=None; terminal_form:str|None=None; verifier_boundary_crossed:bool=False; failure_kind:VerifiedCorpusFailureKind=VerifiedCorpusFailureKind.NONE; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def has_boundary_evidence(self): return bool(self.verifier_boundary_crossed and self.boundary_evidence_id and self.certificate_id and self.terminal_form==TerminalForm.VERIFIED_PROOF.value and self.status in {VerifiedCorpusEntryStatus.VERIFIED_BY_LOCAL_VERIFIER,VerifiedCorpusEntryStatus.TRUSTED_IMPORTED})
@_serial
@dataclass
class VerifiedCorpusDependencyEdge:
 edge_id:str; corpus_id:str; source_entry_id:str; target_entry_id:str; relation:str="depends_on"; evidence:str="import_or_text_reference"; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
@dataclass
class VerifiedCorpusIngestionReport:
 report_id:str; corpus_id:str; manifest:VerifiedCorpusManifest|None=None; files:list[VerifiedCorpusFile]=field(default_factory=list); entries:list[VerifiedCorpusEntry]=field(default_factory=list); dependency_edges:list[VerifiedCorpusDependencyEdge]=field(default_factory=list); verifier_execution_report:Any|None=None; lawbook_replay_summary:dict[str,Any]=field(default_factory=dict); created_at:str=field(default_factory=lambda:_now()); status:VerifiedCorpusIngestionStatus=VerifiedCorpusIngestionStatus.UNKNOWN; summary:dict[str,Any]=field(default_factory=dict); warnings:tuple[str,...]=(); criticals:tuple[str,...]=(); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def file_count(self): return len(self.files)
 def entry_count(self): return len(self.entries)
 def verified_entry_count(self): return sum(e.has_boundary_evidence() for e in self.entries)
 def boundary_evidence_count(self): return self.verified_entry_count()
 def warning_count(self): return len(self.warnings)
 def critical_count(self): return len(self.criticals)
 def summarize(self):
  self.summary={"file_total":len(self.files),"entry_total":len(self.entries),"verified_entry_total":self.verified_entry_count(),"boundary_evidence_total":self.boundary_evidence_count(),"dependency_edge_total":len(self.dependency_edges),"status_counts":_counts(e.status.value for e in self.entries),"failure_kind_counts":_counts(e.failure_kind.value for e in self.entries),"warning_total":len(self.warnings),"critical_total":len(self.criticals)}; return self.summary
 def ok(self): return self.critical_count()==0 and self.status not in {VerifiedCorpusIngestionStatus.FAILED,VerifiedCorpusIngestionStatus.ERROR} and not any(e.has_boundary_evidence() and e.failure_kind!=VerifiedCorpusFailureKind.NONE for e in self.entries)
 def to_dict(self): return {**self.__dict__,"manifest":self.manifest.to_dict() if self.manifest else None,"files":[x.to_dict() for x in self.files],"entries":[x.to_dict() for x in self.entries],"dependency_edges":[x.to_dict() for x in self.dependency_edges],"verifier_execution_report":self.verifier_execution_report.to_dict() if hasattr(self.verifier_execution_report,"to_dict") else self.verifier_execution_report,"status":self.status.value,"warnings":list(self.warnings),"criticals":list(self.criticals)}
 @classmethod
 def from_dict(c,d): return c(str(d["report_id"]),str(d["corpus_id"]),VerifiedCorpusManifest.from_dict(d["manifest"]) if d.get("manifest") else None,[VerifiedCorpusFile.from_dict(x) for x in d.get("files",())],[VerifiedCorpusEntry.from_dict(x) for x in d.get("entries",())],[VerifiedCorpusDependencyEdge.from_dict(x) for x in d.get("dependency_edges",())],VerifierExecutionReport.from_dict(d["verifier_execution_report"]) if d.get("verifier_execution_report") else None,dict(d.get("lawbook_replay_summary",{})),str(d.get("created_at",_now())),VerifiedCorpusIngestionStatus(str(d.get("status","UNKNOWN"))),dict(d.get("summary",{})),tuple(d.get("warnings",())),tuple(d.get("criticals",())),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
 def write_json(self,p): _w(p,self.to_json())
 @classmethod
 def read_json(c,p): return c.from_json(Path(p).read_text())
 def write_jsonl(self,p): _w(p,self.to_json()+"\n")
 @classmethod
 def read_jsonl(c,p): return [c.from_json(x) for x in Path(p).read_text().splitlines() if x.strip()]
for _c,_e in [(VerifiedCorpusManifest,("source_kind","trust_policy")),(VerifiedCorpusEntry,("entry_kind","status","failure_kind")),(VerifiedCorpusFile,()),(VerifiedCorpusDependencyEdge,())]: _serial(_c,_e)
def make_verified_corpus_manifest_id(*x): return content_id("verified-corpus-manifest",x)
def make_verified_corpus_file_id(*x): return content_id("verified-corpus-file",x)
def make_verified_corpus_entry_id(*x): return content_id("verified-corpus-entry",x)
def make_verified_corpus_dependency_edge_id(*x): return content_id("verified-corpus-edge",x)
def make_verified_corpus_ingestion_report_id(*x): return content_id("verified-corpus-report",x)
def default_micro_corpus_files():
 return {"CorpusBasic.lean":"theorem corpus_true : True := by\n  trivial\n\ntheorem corpus_identity (alpha : Type) (x : alpha) : x = x := by\n  rfl\n","CorpusLogic.lean":"theorem corpus_and_comm (p q : Prop) : p ∧ q → q ∧ p := by\n  intro h\n  exact And.intro h.right h.left\n\ntheorem corpus_imp_trans (p q r : Prop) : (p → q) → (q → r) → p → r := by\n  intro hpq hqr hp\n  exact hqr (hpq hp)\n","CorpusNat.lean":"theorem corpus_nat_eq_self (n : Nat) : n = n := by\n  rfl\n\ntheorem corpus_nat_zero_eq_zero : (0 : Nat) = 0 := by\n  rfl\n","CorpusBadUnsafe.lean":"theorem corpus_bad_sorry : True := by\n  sorry\n","CorpusBadExpectedMissing.lean":"theorem corpus_actual_name : True := by\n  trivial\n","CorpusBadImport.lean":"import Definitely.Does.Not.Exist.MathGraphCorpus\n\ntheorem corpus_bad_import : True := by\n  trivial\n"}
def default_micro_corpus_manifest_dict():
 return {"corpus_id":"mathgraph-lean-micro","name":"MathGraph Lean Micro Corpus","version":"0.1","source_kind":"LOCAL_MICRO_CORPUS","trust_policy":"LOCAL_VERIFIER_REQUIRED","proof_system":"lean","files":[{"path":"CorpusBasic.lean","expected_theorem_names":["corpus_true","corpus_identity"],"expected_status":"safe","category":"safe"},{"path":"CorpusLogic.lean","expected_theorem_names":["corpus_and_comm","corpus_imp_trans"],"expected_status":"safe","category":"safe"},{"path":"CorpusNat.lean","expected_theorem_names":["corpus_nat_eq_self","corpus_nat_zero_eq_zero"],"expected_status":"safe","category":"safe"},{"path":"CorpusBadUnsafe.lean","expected_theorem_names":["corpus_bad_sorry"],"expected_status":"unsafe","category":"unsafe_marker"},{"path":"CorpusBadExpectedMissing.lean","expected_theorem_names":["corpus_expected_name"],"expected_status":"expected_missing","category":"expected_name_mismatch"},{"path":"CorpusBadImport.lean","expected_theorem_names":["corpus_bad_import"],"expected_status":"import_failure","category":"import_error"}]}
def ensure_default_micro_corpus(root,*,overwrite=False):
 root=Path(root); root.mkdir(parents=True,exist_ok=True)
 for n,t in default_micro_corpus_files().items():
  p=root/n
  if overwrite or not p.exists(): p.write_text(t,encoding="utf-8")
 p=root/"corpus_manifest.json"
 if overwrite or not p.exists(): p.write_text(json.dumps(default_micro_corpus_manifest_dict(),indent=2)+"\n",encoding="utf-8")
 return p
def load_verified_corpus_manifest(path):
 p=Path(path); d=json.loads(p.read_text()); d["root_path"]=str(p.parent); d["manifest_id"]=d.get("manifest_id") or make_verified_corpus_manifest_id(d.get("corpus_id"),d.get("version"),d.get("files")); return VerifiedCorpusManifest.from_dict(d)
def build_default_micro_corpus_manifest(root=None,*,ensure_files=True):
 root=Path(root or Path(__file__).resolve().parents[1]/"examples"/"verified_corpus"/"lean_micro"); p=root/"corpus_manifest.json"
 if ensure_files: p=ensure_default_micro_corpus(root)
 return load_verified_corpus_manifest(p)
def extract_imports_from_lean_text(text): return tuple(re.findall(r"^\s*import\s+([A-Za-z0-9_.]+)",text,flags=re.M))
def extract_declared_entries_from_lean_text(text,*,corpus_id,file_id):
 entries=[]; clean=re.sub(r"--.*?$","",text,flags=re.M)
 for kind,name in re.findall(r"\b(theorem|lemma|def)\s+([A-Za-z_][A-Za-z0-9_]*)",clean):
  line=next((x.strip() for x in clean.splitlines() if re.search(rf"\b{kind}\s+{name}\b",x)),name)
  entries.append(VerifiedCorpusEntry(make_verified_corpus_entry_id(corpus_id,file_id,name),corpus_id,file_id,name,{"theorem":VerifiedCorpusEntryKind.THEOREM,"lemma":VerifiedCorpusEntryKind.LEMMA,"def":VerifiedCorpusEntryKind.DEFINITION}[kind],theorem_statement_excerpt=line))
 if re.search(r"\bexample\b",clean): entries.append(VerifiedCorpusEntry(make_verified_corpus_entry_id(corpus_id,file_id,"anonymous_example"),corpus_id,file_id,"anonymous_example",VerifiedCorpusEntryKind.EXAMPLE))
 return entries
def build_verified_corpus_file(manifest,file_record):
 p=(Path(manifest.root_path or ".")/str(file_record["path"])).resolve(); text=p.read_text(encoding="utf-8"); fid=make_verified_corpus_file_id(manifest.corpus_id,str(p),_hash(text)); names=extract_theorem_declarations(text); return VerifiedCorpusFile(fid,manifest.corpus_id,str(p),p.stem,_hash(text),tuple(file_record.get("expected_theorem_names",())),names,extract_imports_from_lean_text(text),extract_unsafe_markers(text),str(file_record.get("expected_status","")),dict(file_record))
def build_dependency_edges(corpus_id,entries,files):
 out=[]; by_name={e.name:e for e in entries}; by_mod={f.module_name:f for f in files}
 for f in files:
  src=[e for e in entries if e.file_id==f.file_id]
  for imp in f.imports:
   target_file=by_mod.get(imp.split(".")[-1])
   if target_file:
    for a in src:
     for b in entries:
      if b.file_id==target_file.file_id: out.append(VerifiedCorpusDependencyEdge(make_verified_corpus_dependency_edge_id(a.entry_id,b.entry_id),corpus_id,a.entry_id,b.entry_id))
  for a in src:
   for name,b in by_name.items():
    if a.entry_id!=b.entry_id and re.search(rf"\b{name}\b",a.theorem_statement_excerpt): out.append(VerifiedCorpusDependencyEdge(make_verified_corpus_dependency_edge_id(a.entry_id,b.entry_id,"text"),corpus_id,a.entry_id,b.entry_id,evidence="text_reference"))
 return out
def ingest_verified_corpus(manifest,*,workspace_root=None,allow_execution=False,allow_missing_verifier=True,timeout_sec=20.0,accept_verified_entries_in_memory=False):
 m=manifest if isinstance(manifest,VerifiedCorpusManifest) else load_verified_corpus_manifest(manifest) if isinstance(manifest,(str,Path)) else VerifiedCorpusManifest.from_dict({"manifest_id":make_verified_corpus_manifest_id(manifest),**dict(manifest)})
 files=[build_verified_corpus_file(m,x) for x in m.files]; entries=[e for f in files for e in extract_declared_entries_from_lean_text(Path(f.path).read_text(),corpus_id=m.corpus_id,file_id=f.file_id)]
 cs=[]
 for f in files:
  c,_=build_lean_check_contract_from_text(Path(f.path).read_text(),workspace_root=Path(workspace_root or Path(tempfile.gettempdir())/"mathgraph_corpus_tmp")/f.module_name,filename=Path(f.path).name,allow_execution=allow_execution,timeout_sec=timeout_sec,expected_theorem_names=f.expected_theorem_names); cs.append(c)
 vr=build_verifier_execution_report(contracts=cs,allow_execution=allow_execution,timeout_sec=timeout_sec); warnings=[]
 for f,res in zip(files,vr.results):
  ev=next((e for e in vr.boundary_evidence if e.result_id==res.result_id),None); expected=set(f.expected_theorem_names); category=f.metadata.get("category")
  for e in [x for x in entries if x.file_id==f.file_id]:
   if f.unsafe_markers: e.status=VerifiedCorpusEntryStatus.REJECTED_UNSAFE; e.failure_kind=VerifiedCorpusFailureKind.UNSAFE_MARKER
   elif expected and not expected.issubset(set(f.declared_names)): e.status=VerifiedCorpusEntryStatus.REJECTED_EXPECTED_MISSING; e.failure_kind=VerifiedCorpusFailureKind.EXPECTED_THEOREM_MISSING
   elif res.failure_kind==VerifierFailureKind.MISSING_EXECUTABLE: e.status=VerifiedCorpusEntryStatus.SKIPPED_MISSING_VERIFIER; e.failure_kind=VerifiedCorpusFailureKind.MISSING_VERIFIER
   elif res.failure_kind==VerifierFailureKind.EXPECTED_THEOREM_MISSING: e.status=VerifiedCorpusEntryStatus.REJECTED_EXPECTED_MISSING; e.failure_kind=VerifiedCorpusFailureKind.EXPECTED_THEOREM_MISSING
   elif res.failure_kind==VerifierFailureKind.IMPORT_ERROR: e.status=VerifiedCorpusEntryStatus.REJECTED_VERIFIER_FAILED; e.failure_kind=VerifiedCorpusFailureKind.IMPORT_ERROR
   elif res.failure_kind==VerifierFailureKind.TYPE_ERROR: e.status=VerifiedCorpusEntryStatus.REJECTED_VERIFIER_FAILED; e.failure_kind=VerifiedCorpusFailureKind.TYPE_ERROR
   elif ev and e.name in expected:
    e.status=VerifiedCorpusEntryStatus.VERIFIED_BY_LOCAL_VERIFIER; e.boundary_evidence_id=ev.evidence_id; e.certificate_id=ev.certificate_id; e.terminal_form=ev.terminal_form; e.verifier_boundary_crossed=True
   elif allow_execution and res.status!=VerifierExecutionStatus.SUCCESS:
    e.status=VerifiedCorpusEntryStatus.REJECTED_VERIFIER_FAILED; e.failure_kind=VerifiedCorpusFailureKind.VERIFIER_FAILED
  if res.failure_kind==VerifierFailureKind.MISSING_EXECUTABLE and allow_missing_verifier: warnings.append("verifier missing")
 edges=build_dependency_edges(m.corpus_id,entries,files); report=VerifiedCorpusIngestionReport(make_verified_corpus_ingestion_report_id(m.corpus_id,[f.file_id for f in files],allow_execution),m.corpus_id,m,files,entries,edges,vr,warnings=tuple(dict.fromkeys(warnings)))
 report.status=VerifiedCorpusIngestionStatus.DRY_RUN if not allow_execution else VerifiedCorpusIngestionStatus.COMPLETED_WITH_WARNINGS if warnings else VerifiedCorpusIngestionStatus.COMPLETED
 report.lawbook_replay_summary=review_and_optionally_accept_verified_corpus_entries(report,accept_in_memory=accept_verified_entries_in_memory); report.summarize(); return report
def verified_corpus_report_to_lawbook_candidates(r):
 return [LawbookEntry(make_lawbook_entry_id("verified-corpus",e.entry_id),LawbookEntryKind.VERIFIED_PROOF_ENTRY,LawbookEntryStatus.CANDIDATE,claim_id=e.name,raw=e.theorem_statement_excerpt,terminal_form=TerminalForm.VERIFIED_PROOF,certificate_id=e.certificate_id,verifier_boundary_crossed=True,acceptance_boundary=LawbookAcceptanceBoundary.VERIFIED_PROOF,metadata={"verified_corpus_report_id":r.report_id,"verified_corpus_entry_id":e.entry_id}) for e in r.entries if e.has_boundary_evidence()]
def review_and_optionally_accept_verified_corpus_entries(r,*,accept_in_memory=False):
 candidates=verified_corpus_report_to_lawbook_candidates(r); reviews=[review_lawbook_candidate(x) for x in candidates]; accepted=[accept_lawbook_entry(e,v,accepted_by="verified-corpus-replay") for e,v in zip(candidates,reviews) if accept_in_memory and v.decision.value=="ACCEPT"]; store=LawbookStore(make_lawbook_store_id("verified-corpus-replay",r.report_id),entries=accepted,reviews=reviews); answers=[query_lawbook_store_by_certificate(store,x.certificate_id) for x in candidates if x.certificate_id]; return {"candidate_total":len(candidates),"review_total":len(reviews),"accepted_total":len(accepted),"query_total":len(answers),"known_skip_total":sum(a.known_skip_decision.value.startswith("SKIP_") for a in answers),"warnings":[],"criticals":[]}
def verified_corpus_report_to_markdown(r):
 s=r.summarize(); lines=["# Verified Corpus Ingestion","",f"- Corpus: `{r.corpus_id}`",f"- Name: {r.manifest.name if r.manifest else ''}",f"- Version: {r.manifest.version if r.manifest else ''}",f"- Status: {r.status.value}",f"- Files: {s['file_total']}",f"- Entries: {s['entry_total']}",f"- Verified entries: {s['verified_entry_total']}",f"- Boundary evidence: {s['boundary_evidence_total']}","", "| file | declared | expected | status | boundary | failure |","| --- | --- | --- | --- | --- | --- |"]
 for f in r.files:
  xs=[e for e in r.entries if e.file_id==f.file_id]; lines.append(f"| {Path(f.path).name} | {', '.join(f.declared_names)} | {', '.join(f.expected_theorem_names)} | {', '.join(dict.fromkeys(e.status.value for e in xs))} | {'yes' if any(e.has_boundary_evidence() for e in xs) else 'no'} | {', '.join(dict.fromkeys(e.failure_kind.value for e in xs))} |")
 lines+=["",f"Lawbook replay: `{r.lawbook_replay_summary}`","","Boundary policy: extraction and dependency graphs are advisory; only valid verifier/importer/finite-validator/chain-audit evidence promotes truth."]; return "\n".join(lines)+"\n"
def verified_corpus_report_to_dependency_graph(r): return {"nodes":[{"id":e.entry_id,"name":e.name,"status":e.status.value} for e in r.entries],"edges":[x.to_dict() for x in r.dependency_edges],"metadata":{"corpus_id":r.corpus_id,"advisory":True}}
def write_dependency_graph_json(r,p): _w(p,_j(verified_corpus_report_to_dependency_graph(r)))
def write_dependency_graph_jsonl(r,p):
 g=verified_corpus_report_to_dependency_graph(r); _w(p,"".join(_j({"kind":"node",**x})+"\n" for x in g["nodes"])+"".join(_j({"kind":"edge",**x})+"\n" for x in g["edges"]))
def verified_corpus_report_to_api_response(r):
 from mathgraph.api_service import _resp
 req=ApiRequest(make_api_request_id("verified-corpus",r.report_id),ApiRoute.VERIFIED_CORPUS); truth=ApiTruthStatus.BOUNDARY_EVIDENCE_PRESENT if r.verified_entry_count() else ApiTruthStatus.BOUNDARY_REQUIRED; return _resp(req,route_result_from_artifacts(req.route,[r],truth_status=truth,safety=ApiSafetyLevel.SAFE_REVIEW_REQUIRED))
def verified_corpus_report_to_process_episodes(r): return [ProcessEpisodeRecord(make_process_episode_id("verified-corpus",e.entry_id),ProcessEpisodeStatus.TERMINAL_VERIFIED_PROOF if e.has_boundary_evidence() else ProcessEpisodeStatus.ADVISORY_ONLY,contexts=[ProcessContextItem(content_id("verified-corpus-context",e.entry_id),ProcessContextKind.RAW_EVENT,ProcessContextRole.ADVISORY_ONLY,e.name)],terminal_form=TerminalForm.VERIFIED_PROOF if e.has_boundary_evidence() else None,certificate_id=e.certificate_id,verifier_boundary_crossed=e.verifier_boundary_crossed) for e in r.entries]
def verified_corpus_report_to_proof_digestion_inputs(r): return [{"entry_id":e.entry_id,"proof_text":e.theorem_statement_excerpt,"boundary_backed":e.has_boundary_evidence(),"advisory":not e.has_boundary_evidence()} for e in r.entries]
def verified_corpus_report_to_discovery_value_scores(r):
 out=[]
 for e in r.entries:
  sig=DiscoveryValueSignal(content_id("verified-corpus-signal",e.entry_id),DiscoveryValueSignalKind.REUSE_VALUE,1.0 if e.has_boundary_evidence() else .1,source_object_kind=DiscoveryValueObjectKind.RAW_TASK); s=DiscoveryValueScore(content_id("verified-corpus-score",e.entry_id),e.entry_id,DiscoveryValueObjectKind.RAW_TASK,signals=[sig]); s.recompute(); out.append(s)
 return out
def verified_corpus_report_to_structural_identity_objects(r): return [{"object_id":e.entry_id,"name":e.name,"kind":e.entry_kind.value,"advisory":not e.has_boundary_evidence()} for e in r.entries]
def verified_corpus_report_to_route_telemetry_events(r): return [{"event_id":content_id("verified-corpus-telemetry",e.entry_id),"route_kind":"verified_corpus","outcome":e.status.value,"certificate_id":e.certificate_id,"verifier_boundary_crossed":e.verifier_boundary_crossed} for e in r.entries]
def verified_corpus_report_to_alchemical_trace(r):
 t=AlchemicalTrace(make_alchemical_trace_id("verified-corpus",r.report_id))
 for p in (AlchemicalPhase.RAW_MATTER,AlchemicalPhase.CALCINATION,AlchemicalPhase.DESCENSION): t.add_step(phase=p,status=AlchemicalStatus.ADVISORY_ONLY)
 if r.verified_entry_count(): t.add_step(phase=AlchemicalPhase.FIXATION,status=AlchemicalStatus.PROMOTED_BY_VERIFIER)
 for p in (AlchemicalPhase.DISTILLATION,AlchemicalPhase.COAGULATION): t.add_step(phase=p,status=AlchemicalStatus.ADVISORY_ONLY)
 return t
def verified_corpus_report_to_agent_experiences(r): return [AgentExperience(content_id("verified-corpus-exp",e.entry_id),"verified-corpus",None,None,"corpus",None,AgentExperienceOutcome.VERIFIED_PROOF if e.has_boundary_evidence() else AgentExperienceOutcome.INVALID_CANDIDATE if e.failure_kind!=VerifiedCorpusFailureKind.NONE else AgentExperienceOutcome.ADVISORY_ONLY,terminal_form=TerminalForm.VERIFIED_PROOF if e.has_boundary_evidence() else None,certificate_id=e.certificate_id,verifier_boundary_crossed=e.verifier_boundary_crossed) for e in r.entries]
def audit_verified_corpus_manifest(x): return [_af("CRITICAL","CORPUS_MANIFEST_NON_ADVISORY","manifest non-advisory",x.manifest_id)] if not x.advisory else []
def audit_verified_corpus_file(x): return [_af("CRITICAL","CORPUS_FILE_NON_ADVISORY","file extraction claims truth",x.file_id)] if not x.advisory else []
def audit_verified_corpus_entry(x):
 out=[]
 if x.status==VerifiedCorpusEntryStatus.VERIFIED_BY_LOCAL_VERIFIER and not x.has_boundary_evidence(): out.append(_af("CRITICAL","CORPUS_VERIFIED_WITHOUT_BOUNDARY","verified entry lacks boundary",x.entry_id))
 if x.has_boundary_evidence() and x.failure_kind!=VerifiedCorpusFailureKind.NONE: out.append(_af("CRITICAL","CORPUS_BAD_ENTRY_VERIFIED","failed entry verified",x.entry_id))
 return out
def audit_verified_corpus_dependency_edge(x): return [_af("CRITICAL","CORPUS_EDGE_NON_ADVISORY","dependency edge treated as proof",x.edge_id)] if not x.advisory else []
def audit_verified_corpus_ingestion_report(x):
 out=sum((audit_verified_corpus_entry(e) for e in x.entries),[])
 if x.ok() and x.critical_count(): out.append(_af("CRITICAL","CORPUS_OK_WITH_CRITICAL","report hides criticals",x.report_id))
 if x.lawbook_replay_summary.get("known_skip_total",0) and not x.lawbook_replay_summary.get("accepted_total",0): out.append(_af("CRITICAL","CORPUS_SKIP_WITHOUT_ACCEPTANCE","known skip without accepted replay",x.report_id))
 return out
def _counts(xs):
 out={}
 for x in xs: out[x]=out.get(x,0)+1
 return out
def _hash(t): return sha256(str(t).encode()).hexdigest()
def _af(sev,code,msg,obj): return {"severity":sev,"code":code,"message":msg,"object_id":obj}
def _now(): return datetime.now(timezone.utc).isoformat()
def _j(x): return json.dumps(x,sort_keys=True,separators=(",",":"),default=str)
def _w(p,t): path=Path(p); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(t,encoding="utf-8")
