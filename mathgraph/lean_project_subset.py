"""Tiny local Lean project ingestion over strict verifier boundaries."""
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
from mathgraph.verified_corpus import *
from mathgraph.verifier_execution import *
def _enum(n,v): return Enum(n,{x:x for x in v.split()},type=str)
LeanProjectSourceKind=_enum("LeanProjectSourceKind","LOCAL_PROJECT LOCAL_MICRO_PROJECT TRUSTED_IMPORT_SOURCE EXTERNAL_REFERENCE UNKNOWN")
LeanProjectTrustPolicy=_enum("LeanProjectTrustPolicy","LOCAL_VERIFIER_REQUIRED TRUSTED_IMPORT_REQUIRED ADVISORY_ONLY UNKNOWN")
LeanProjectFileStatus=_enum("LeanProjectFileStatus","ADVISORY_EXTRACTED VERIFIED_BY_LOCAL_VERIFIER REJECTED_UNSAFE REJECTED_EXPECTED_MISSING REJECTED_VERIFIER_FAILED SKIPPED_MISSING_VERIFIER BLOCKED ERROR UNKNOWN")
LeanProjectEntryStatus=_enum("LeanProjectEntryStatus","ADVISORY_EXTRACTED VERIFIED_BY_LOCAL_VERIFIER REJECTED_UNSAFE REJECTED_EXPECTED_MISSING REJECTED_VERIFIER_FAILED SKIPPED_MISSING_VERIFIER BLOCKED ERROR UNKNOWN")
LeanProjectDependencyKind=_enum("LeanProjectDependencyKind","IMPORTS_MODULE REFERENCES_DECLARATION EXPECTED_REFERENCE TEXT_REFERENCE UNKNOWN")
LeanProjectIngestionStatus=_enum("LeanProjectIngestionStatus","NOT_RUN DRY_RUN COMPLETED COMPLETED_WITH_WARNINGS FAILED SKIPPED ERROR UNKNOWN")
LeanProjectFailureKind=_enum("LeanProjectFailureKind","NONE MISSING_VERIFIER UNSAFE_MARKER EXPECTED_THEOREM_MISSING IMPORT_ERROR TYPE_ERROR VERIFIER_FAILED TRUST_POLICY_BLOCKED MANIFEST_INVALID FILE_MISSING MODULE_RESOLUTION_FAILED UNKNOWN")
def _serial(cls,enums=()):
 def td(self):
  d=dict(self.__dict__)
  for k in enums:
   if isinstance(d.get(k),Enum): d[k]=d[k].value
  for k,v in list(d.items()):
   if isinstance(v,tuple): d[k]=[list(x) if isinstance(x,tuple) else x for x in v]
   elif hasattr(v,"to_dict"): d[k]=v.to_dict()
   elif isinstance(v,list): d[k]=[x.to_dict() if hasattr(x,"to_dict") else x for x in v]
  return d
 @classmethod
 def fd(c,d):
  vals=[]
  for f in c.__dataclass_fields__.values():
   v=d[f.name] if f.name in d else f.default if f.default is not MISSING else f.default_factory() if f.default_factory is not MISSING else None
   if f.name in enums and v is not None: v=globals()[str(f.type)](str(v))
   if getattr(f.type,"__origin__",None) is tuple and v is not None: v=tuple(tuple(x) if isinstance(x,list) else x for x in v)
   vals.append(v)
  return c(*vals)
 cls.to_dict=td; cls.from_dict=fd; cls.to_json=lambda self:_j(self.to_dict()); cls.from_json=classmethod(lambda c,t:c.from_dict(json.loads(t))); return cls
@_serial
@dataclass
class LeanProjectManifest:
 manifest_id:str; project_id:str; name:str; version:str="0.1"; source_kind:LeanProjectSourceKind=LeanProjectSourceKind.LOCAL_MICRO_PROJECT; trust_policy:LeanProjectTrustPolicy=LeanProjectTrustPolicy.LOCAL_VERIFIER_REQUIRED; proof_system:str="lean"; project_root:str|None=None; module_root:str="MathGraphMicro"; files:list[dict[str,Any]]=field(default_factory=list); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def write_json(self,p): _w(p,self.to_json())
 @classmethod
 def read_json(c,p): return c.from_json(Path(p).read_text())
@_serial
@dataclass
class LeanProjectFile:
 file_id:str; project_id:str; path:str; module_name:str; text_hash:str|None=None; expected_theorem_names:tuple[str,...]=(); declared_names:tuple[str,...]=(); imports:tuple[str,...]=(); expected_imports:tuple[str,...]=(); unsafe_markers:tuple[str,...]=(); expected_reference_dependencies:tuple[tuple[str,str],...]=(); status:LeanProjectFileStatus=LeanProjectFileStatus.ADVISORY_EXTRACTED; failure_kind:LeanProjectFailureKind=LeanProjectFailureKind.NONE; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
@_serial
@dataclass
class LeanProjectEntry:
 entry_id:str; project_id:str; file_id:str; module_name:str; name:str; entry_kind:str="theorem"; status:LeanProjectEntryStatus=LeanProjectEntryStatus.ADVISORY_EXTRACTED; theorem_statement_excerpt:str=""; referenced_names:tuple[str,...]=(); boundary_evidence_id:str|None=None; certificate_id:str|None=None; terminal_form:str|None=None; verifier_boundary_crossed:bool=False; failure_kind:LeanProjectFailureKind=LeanProjectFailureKind.NONE; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def has_boundary_evidence(self): return bool(self.verifier_boundary_crossed and self.boundary_evidence_id and self.certificate_id and self.terminal_form==TerminalForm.VERIFIED_PROOF.value and self.status==LeanProjectEntryStatus.VERIFIED_BY_LOCAL_VERIFIER)
@_serial
@dataclass
class LeanProjectDependencyEdge:
 edge_id:str; project_id:str; source_kind:str; source_id:str; target_kind:str; target_id:str; dependency_kind:LeanProjectDependencyKind; source_name:str=""; target_name:str=""; evidence:str=""; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
@dataclass
class LeanProjectIngestionReport:
 report_id:str; project_id:str; manifest:LeanProjectManifest|None=None; files:list[LeanProjectFile]=field(default_factory=list); entries:list[LeanProjectEntry]=field(default_factory=list); dependency_edges:list[LeanProjectDependencyEdge]=field(default_factory=list); verifier_execution_report:Any|None=None; lawbook_replay_summary:dict[str,Any]=field(default_factory=dict); created_at:str=field(default_factory=lambda:_now()); status:LeanProjectIngestionStatus=LeanProjectIngestionStatus.UNKNOWN; summary:dict[str,Any]=field(default_factory=dict); warnings:tuple[str,...]=(); criticals:tuple[str,...]=(); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def file_count(self): return len(self.files)
 def entry_count(self): return len(self.entries)
 def verified_entry_count(self): return sum(e.has_boundary_evidence() for e in self.entries)
 def boundary_evidence_count(self): return self.verified_entry_count()
 def dependency_edge_count(self): return len(self.dependency_edges)
 def import_edge_count(self): return sum(e.dependency_kind==LeanProjectDependencyKind.IMPORTS_MODULE for e in self.dependency_edges)
 def reference_edge_count(self): return sum(e.dependency_kind in {LeanProjectDependencyKind.REFERENCES_DECLARATION,LeanProjectDependencyKind.EXPECTED_REFERENCE,LeanProjectDependencyKind.TEXT_REFERENCE} for e in self.dependency_edges)
 def warning_count(self): return len(self.warnings)
 def critical_count(self): return len(self.criticals)
 def summarize(self):
  self.summary={"file_total":len(self.files),"entry_total":len(self.entries),"verified_entry_total":self.verified_entry_count(),"boundary_evidence_total":self.boundary_evidence_count(),"dependency_edge_total":len(self.dependency_edges),"import_edge_total":self.import_edge_count(),"reference_edge_total":self.reference_edge_count(),"status_counts":_counts(e.status.value for e in self.entries),"failure_kind_counts":_counts(e.failure_kind.value for e in self.entries),"warning_total":len(self.warnings),"critical_total":len(self.criticals)}; return self.summary
 def ok(self): return self.critical_count()==0 and self.status not in {LeanProjectIngestionStatus.FAILED,LeanProjectIngestionStatus.ERROR} and not any(e.has_boundary_evidence() and e.failure_kind!=LeanProjectFailureKind.NONE for e in self.entries)
 def to_dict(self): return {**self.__dict__,"manifest":self.manifest.to_dict() if self.manifest else None,"files":[x.to_dict() for x in self.files],"entries":[x.to_dict() for x in self.entries],"dependency_edges":[x.to_dict() for x in self.dependency_edges],"verifier_execution_report":self.verifier_execution_report.to_dict() if hasattr(self.verifier_execution_report,"to_dict") else self.verifier_execution_report,"status":self.status.value,"warnings":list(self.warnings),"criticals":list(self.criticals)}
 @classmethod
 def from_dict(c,d): return c(str(d["report_id"]),str(d["project_id"]),LeanProjectManifest.from_dict(d["manifest"]) if d.get("manifest") else None,[LeanProjectFile.from_dict(x) for x in d.get("files",())],[LeanProjectEntry.from_dict(x) for x in d.get("entries",())],[LeanProjectDependencyEdge.from_dict(x) for x in d.get("dependency_edges",())],VerifierExecutionReport.from_dict(d["verifier_execution_report"]) if d.get("verifier_execution_report") else None,dict(d.get("lawbook_replay_summary",{})),str(d.get("created_at",_now())),LeanProjectIngestionStatus(str(d.get("status","UNKNOWN"))),dict(d.get("summary",{})),tuple(d.get("warnings",())),tuple(d.get("criticals",())),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
 def write_json(self,p): _w(p,self.to_json())
 @classmethod
 def read_json(c,p): return c.from_json(Path(p).read_text())
 def write_jsonl(self,p): _w(p,self.to_json()+"\n")
 @classmethod
 def read_jsonl(c,p): return [c.from_json(x) for x in Path(p).read_text().splitlines() if x.strip()]
for _c,_e in [(LeanProjectManifest,("source_kind","trust_policy")),(LeanProjectFile,("status","failure_kind")),(LeanProjectEntry,("status","failure_kind")),(LeanProjectDependencyEdge,("dependency_kind",))]: _serial(_c,_e)
def make_lean_project_manifest_id(*x): return content_id("lean-project-manifest",x)
def make_lean_project_file_id(*x): return content_id("lean-project-file",x)
def make_lean_project_entry_id(*x): return content_id("lean-project-entry",x)
def make_lean_project_dependency_edge_id(*x): return content_id("lean-project-edge",x)
def make_lean_project_ingestion_report_id(*x): return content_id("lean-project-report",x)
def default_micro_project_files():
 return {"MathGraphMicro/Basic.lean":"theorem mg_basic_true : True := by\n  trivial\n\ntheorem mg_identity (alpha : Type) (x : alpha) : x = x := by\n  rfl\n","MathGraphMicro/Logic.lean":"theorem mg_and_comm (p q : Prop) : p ∧ q → q ∧ p := by\n  intro h\n  exact And.intro h.right h.left\n\ntheorem mg_imp_trans (p q r : Prop) : (p → q) → (q → r) → p → r := by\n  intro hpq hqr hp\n  exact hqr (hpq hp)\n","MathGraphMicro/UseBasic.lean":"import MathGraphMicro.Basic\n\ntheorem mg_uses_basic_true : True := by\n  exact mg_basic_true\n\ntheorem mg_uses_identity (alpha : Type) (x : alpha) : x = x := by\n  exact mg_identity alpha x\n","MathGraphMicro/UseLogic.lean":"import MathGraphMicro.Logic\n\ntheorem mg_uses_and_comm (p q : Prop) : p ∧ q → q ∧ p := by\n  exact mg_and_comm p q\n\ntheorem mg_uses_imp_trans (p q r : Prop) : (p → q) → (q → r) → p → r := by\n  exact mg_imp_trans p q r\n","MathGraphMicro/BadUnsafe.lean":"theorem mg_bad_sorry : True := by\n  sorry\n","MathGraphMicro/BadExpectedMissing.lean":"theorem mg_actual_name : True := by\n  trivial\n","MathGraphMicro/BadImport.lean":"import Definitely.Does.Not.Exist.MathGraphMicro\n\ntheorem mg_bad_import : True := by\n  trivial\n"}
def default_micro_project_manifest_dict():
 return json.loads((Path(__file__).resolve().parents[1]/"examples/lean_project_micro/project_manifest.json").read_text())
def ensure_default_micro_project(root,*,overwrite=False):
 root=Path(root); root.mkdir(parents=True,exist_ok=True)
 for n,t in default_micro_project_files().items():
  p=root/n; p.parent.mkdir(parents=True,exist_ok=True)
  if overwrite or not p.exists(): p.write_text(t,encoding="utf-8")
 p=root/"project_manifest.json"
 if overwrite or not p.exists(): p.write_text(json.dumps(default_micro_project_manifest_dict(),indent=2)+"\n",encoding="utf-8")
 return p
def load_lean_project_manifest(path):
 p=Path(path); d=json.loads(p.read_text()); root=(p.parent/str(d.get("project_root","."))).resolve(); d["project_root"]=str(root); return LeanProjectManifest(make_lean_project_manifest_id(d),d["project_id"],d["name"],d.get("version","0.1"),LeanProjectSourceKind(d.get("source_kind","LOCAL_MICRO_PROJECT")),LeanProjectTrustPolicy(d.get("trust_policy","LOCAL_VERIFIER_REQUIRED")),d.get("proof_system","lean"),str(root),d.get("module_root","MathGraphMicro"),list(d.get("files",())),dict(d.get("metadata",{})))
def build_default_micro_project_manifest(root=None,*,ensure_files=True):
 root=Path(root or Path(__file__).resolve().parents[1]/"examples/lean_project_micro")
 p=ensure_default_micro_project(root) if ensure_files else root/"project_manifest.json"; return load_lean_project_manifest(p)
def module_name_from_path(path,*,project_root=None):
 p=Path(path)
 if project_root is not None:
  try:p=p.resolve().relative_to(Path(project_root).resolve())
  except ValueError: pass
 return ".".join(p.with_suffix("").parts)
def path_from_module_name(module_name,*,project_root): return Path(project_root).joinpath(*module_name.split(".")).with_suffix(".lean")
def extract_imports_from_lean_text(text): return tuple(re.findall(r"(?m)^\s*import\s+([A-Za-z0-9_.]+)",text))
def extract_declared_entries_from_lean_project_text(text,*,project_id,file_id,module_name):
 out=[]
 for name in extract_theorem_declarations(text):
  m=re.search(rf"(?ms)^(?:theorem|lemma)\s+{re.escape(name)}\b.*?(?=^\s*(?:theorem|lemma|def)\s+|\Z)",text)
  out.append(LeanProjectEntry(make_lean_project_entry_id(project_id,file_id,name),project_id,file_id,module_name,name,theorem_statement_excerpt=(m.group(0).strip()[:240] if m else name)))
 return out
def extract_referenced_names_from_lean_text(text,candidate_names):
 return tuple(n for n in candidate_names if len(re.findall(rf"\b{re.escape(n)}\b",text))>0)
def build_lean_project_file(m,r):
 root=Path(m.project_root or "."); p=root/r["path"]; t=p.read_text(); return LeanProjectFile(make_lean_project_file_id(m.project_id,r["path"]),m.project_id,str(p.resolve()),r.get("module_name") or module_name_from_path(p,project_root=root),_hash(t),tuple(r.get("expected_theorem_names",())),extract_theorem_declarations(t),extract_imports_from_lean_text(t),tuple(r.get("expected_imports",())),extract_unsafe_markers(t),tuple(tuple(x) for x in r.get("expected_reference_dependencies",())),metadata={"expected_status":r.get("expected_status",""),"category":r.get("category","")})
def build_project_dependency_edges(project_id,entries,files):
 out=[]; by_module={f.module_name:f for f in files}; by_name={e.name:e for e in entries}
 for f in files:
  for imp in f.imports:
   if imp in by_module:
    target=by_module[imp]; out.append(LeanProjectDependencyEdge(make_lean_project_dependency_edge_id(f.file_id,target.file_id,"import"),project_id,"module",f.file_id,"module",target.file_id,LeanProjectDependencyKind.IMPORTS_MODULE,f.module_name,target.module_name,"import"))
  own={e.name for e in entries if e.file_id==f.file_id}
  for e in [x for x in entries if x.file_id==f.file_id]:
   refs=tuple(n for n in extract_referenced_names_from_lean_text(e.theorem_statement_excerpt,by_name) if n not in own)
   e.referenced_names=refs
   for n in refs:
    target=by_name[n]; out.append(LeanProjectDependencyEdge(make_lean_project_dependency_edge_id(e.entry_id,target.entry_id,"text"),project_id,"entry",e.entry_id,"entry",target.entry_id,LeanProjectDependencyKind.REFERENCES_DECLARATION,e.name,target.name,"text_reference"))
  for a,b in f.expected_reference_dependencies:
   if a in by_name and b in by_name: out.append(LeanProjectDependencyEdge(make_lean_project_dependency_edge_id(a,b,"expected"),project_id,"entry",by_name[a].entry_id,"entry",by_name[b].entry_id,LeanProjectDependencyKind.EXPECTED_REFERENCE,a,b,"manifest_expected_reference"))
 return out
def _project_contract(f,root,build_root,allow_execution,timeout_sec):
 out=build_root.joinpath(*f.module_name.split(".")).with_suffix(".olean"); out.parent.mkdir(parents=True,exist_ok=True)
 return VerifierCommandContract(make_verifier_command_contract_id(f.path,f.expected_theorem_names,allow_execution),VerifierSystemKind.LEAN,VerifierExecutionMode.CHECK_FILE,("lean","-o",str(out),f.path),str(root),f.path,f.text_hash,timeout_sec,allow_execution,False,False,str(root),f.expected_theorem_names,{"lean_path":str(build_root)})
def ingest_lean_project_subset(manifest,*,workspace_root=None,allow_execution=False,allow_missing_verifier=True,timeout_sec=20.0,accept_verified_entries_in_memory=False):
 m=manifest if isinstance(manifest,LeanProjectManifest) else load_lean_project_manifest(manifest) if isinstance(manifest,(str,Path)) else LeanProjectManifest.from_dict({"manifest_id":make_lean_project_manifest_id(manifest),**dict(manifest)})
 root=Path(m.project_root or ".").resolve(); build_root=Path(workspace_root or Path(tempfile.gettempdir())/"mathgraph_lean_project_tmp").resolve()/"olean"; files=[build_lean_project_file(m,x) for x in m.files]; entries=[e for f in files for e in extract_declared_entries_from_lean_project_text(Path(f.path).read_text(),project_id=m.project_id,file_id=f.file_id,module_name=f.module_name)]; edges=build_project_dependency_edges(m.project_id,entries,files); contracts=[_project_contract(f,root,build_root,allow_execution,timeout_sec) for f in files]; vr=build_verifier_execution_report(contracts=contracts,allow_execution=allow_execution,timeout_sec=timeout_sec); warnings=[]
 for f,res in zip(files,vr.results):
  ev=next((e for e in vr.boundary_evidence if e.result_id==res.result_id),None); expected=set(f.expected_theorem_names)
  if f.unsafe_markers: f.status=LeanProjectFileStatus.REJECTED_UNSAFE; f.failure_kind=LeanProjectFailureKind.UNSAFE_MARKER
  elif expected and not expected.issubset(set(f.declared_names)): f.status=LeanProjectFileStatus.REJECTED_EXPECTED_MISSING; f.failure_kind=LeanProjectFailureKind.EXPECTED_THEOREM_MISSING
  elif res.failure_kind==VerifierFailureKind.MISSING_EXECUTABLE: f.status=LeanProjectFileStatus.SKIPPED_MISSING_VERIFIER; f.failure_kind=LeanProjectFailureKind.MISSING_VERIFIER
  elif res.failure_kind==VerifierFailureKind.IMPORT_ERROR: f.status=LeanProjectFileStatus.REJECTED_VERIFIER_FAILED; f.failure_kind=LeanProjectFailureKind.IMPORT_ERROR
  elif ev: f.status=LeanProjectFileStatus.VERIFIED_BY_LOCAL_VERIFIER
  elif allow_execution and res.status!=VerifierExecutionStatus.SUCCESS: f.status=LeanProjectFileStatus.REJECTED_VERIFIER_FAILED; f.failure_kind=LeanProjectFailureKind.VERIFIER_FAILED
  for e in [x for x in entries if x.file_id==f.file_id]:
   if f.status==LeanProjectFileStatus.REJECTED_UNSAFE: e.status=LeanProjectEntryStatus.REJECTED_UNSAFE; e.failure_kind=LeanProjectFailureKind.UNSAFE_MARKER
   elif f.status==LeanProjectFileStatus.REJECTED_EXPECTED_MISSING: e.status=LeanProjectEntryStatus.REJECTED_EXPECTED_MISSING; e.failure_kind=LeanProjectFailureKind.EXPECTED_THEOREM_MISSING
   elif f.status==LeanProjectFileStatus.SKIPPED_MISSING_VERIFIER: e.status=LeanProjectEntryStatus.SKIPPED_MISSING_VERIFIER; e.failure_kind=LeanProjectFailureKind.MISSING_VERIFIER
   elif f.failure_kind in {LeanProjectFailureKind.IMPORT_ERROR,LeanProjectFailureKind.TYPE_ERROR,LeanProjectFailureKind.VERIFIER_FAILED}: e.status=LeanProjectEntryStatus.REJECTED_VERIFIER_FAILED; e.failure_kind=f.failure_kind
   elif ev and e.name in expected: e.status=LeanProjectEntryStatus.VERIFIED_BY_LOCAL_VERIFIER; e.boundary_evidence_id=ev.evidence_id; e.certificate_id=ev.certificate_id; e.terminal_form=ev.terminal_form; e.verifier_boundary_crossed=True
  if res.failure_kind==VerifierFailureKind.MISSING_EXECUTABLE and allow_missing_verifier: warnings.append("verifier missing")
 rep=LeanProjectIngestionReport(make_lean_project_ingestion_report_id(m.project_id,[f.file_id for f in files],allow_execution),m.project_id,m,files,entries,edges,vr,warnings=tuple(dict.fromkeys(warnings)))
 rep.status=LeanProjectIngestionStatus.DRY_RUN if not allow_execution else LeanProjectIngestionStatus.COMPLETED_WITH_WARNINGS if warnings else LeanProjectIngestionStatus.COMPLETED
 rep.lawbook_replay_summary=review_and_optionally_accept_lean_project_entries(rep,accept_in_memory=accept_verified_entries_in_memory); rep.summarize(); return rep
def lean_project_report_to_lawbook_candidates(r):
 return [LawbookEntry(make_lawbook_entry_id("lean-project",e.entry_id),LawbookEntryKind.VERIFIED_PROOF_ENTRY,LawbookEntryStatus.CANDIDATE,claim_id=e.name,raw=e.theorem_statement_excerpt,terminal_form=TerminalForm.VERIFIED_PROOF,certificate_id=e.certificate_id,verifier_boundary_crossed=True,acceptance_boundary=LawbookAcceptanceBoundary.VERIFIED_PROOF,metadata={"lean_project_report_id":r.report_id,"lean_project_entry_id":e.entry_id}) for e in r.entries if e.has_boundary_evidence()]
def review_and_optionally_accept_lean_project_entries(r,*,accept_in_memory=False):
 cs=lean_project_report_to_lawbook_candidates(r); reviews=[review_lawbook_candidate(x) for x in cs]; accepted=[accept_lawbook_entry(e,v,accepted_by="lean-project-replay") for e,v in zip(cs,reviews) if accept_in_memory and v.decision.value=="ACCEPT"]; store=LawbookStore(make_lawbook_store_id("lean-project-replay",r.report_id),entries=accepted,reviews=reviews); answers=[query_lawbook_store_by_certificate(store,x.certificate_id) for x in cs if x.certificate_id]; return {"candidate_total":len(cs),"review_total":len(reviews),"accepted_total":len(accepted),"query_total":len(answers),"known_skip_total":sum(a.known_skip_decision.value.startswith("SKIP_") for a in answers),"warnings":[],"criticals":[]}
def lean_project_report_to_markdown(r):
 s=r.summarize(); lines=["# Lean Project Subset Ingestion","",f"- Project: `{r.project_id}`",f"- Name: {r.manifest.name if r.manifest else ''}",f"- Version: {r.manifest.version if r.manifest else ''}",f"- Status: {r.status.value}",f"- Files: {s['file_total']}",f"- Entries: {s['entry_total']}",f"- Verified entries: {s['verified_entry_total']}",f"- Boundary evidence: {s['boundary_evidence_total']}",f"- Dependency edges: {s['dependency_edge_total']}",f"- Import edges: {s['import_edge_total']}",f"- Reference edges: {s['reference_edge_total']}","", "| file/module | declared | expected | imports | status | boundary | failure |","| --- | --- | --- | --- | --- | --- | --- |"]
 for f in r.files:
  xs=[e for e in r.entries if e.file_id==f.file_id]; lines.append(f"| {Path(f.path).name} / {f.module_name} | {', '.join(f.declared_names)} | {', '.join(f.expected_theorem_names)} | {', '.join(f.imports)} | {', '.join(dict.fromkeys(e.status.value for e in xs))} | {'yes' if any(e.has_boundary_evidence() for e in xs) else 'no'} | {', '.join(dict.fromkeys(e.failure_kind.value for e in xs))} |")
 lines+=["",f"Dependency summary: imports={r.import_edge_count()}, references={r.reference_edge_count()}",f"Lawbook replay: `{r.lawbook_replay_summary}`","","Boundary policy: declarations, imports, and reference graphs are advisory; only valid verifier/importer/finite-validator/chain-audit evidence promotes truth."]; return "\n".join(lines)+"\n"
def lean_project_report_to_dependency_graph(r): return {"nodes":[{"id":f.file_id,"kind":"module","name":f.module_name} for f in r.files]+[{"id":e.entry_id,"kind":"entry","name":e.name,"status":e.status.value} for e in r.entries],"edges":[x.to_dict() for x in r.dependency_edges],"metadata":{"project_id":r.project_id,"advisory":True}}
def write_dependency_graph_json(r,p): _w(p,_j(lean_project_report_to_dependency_graph(r)))
def write_dependency_graph_jsonl(r,p):
 g=lean_project_report_to_dependency_graph(r); _w(p,"".join(_j({"kind":"node",**x})+"\n" for x in g["nodes"])+"".join(_j({"kind":"edge",**x})+"\n" for x in g["edges"]))
def lean_project_report_to_api_response(r):
 from mathgraph.api_service import _resp
 req=ApiRequest(make_api_request_id("lean-project",r.report_id),ApiRoute.LEAN_PROJECT_SUBSET); truth=ApiTruthStatus.BOUNDARY_EVIDENCE_PRESENT if r.verified_entry_count() else ApiTruthStatus.BOUNDARY_REQUIRED; return _resp(req,route_result_from_artifacts(req.route,[r],truth_status=truth,safety=ApiSafetyLevel.SAFE_REVIEW_REQUIRED))
def lean_project_report_to_verified_corpus_report(r):
 files=[VerifiedCorpusFile(f.file_id,r.project_id,f.path,f.module_name,f.text_hash,f.expected_theorem_names,f.declared_names,f.imports,f.unsafe_markers,f.metadata.get("expected_status",""),dict(f.metadata)) for f in r.files]
 ents=[VerifiedCorpusEntry(e.entry_id,r.project_id,e.file_id,e.name,VerifiedCorpusEntryKind.THEOREM,VerifiedCorpusEntryStatus(e.status.value),e.theorem_statement_excerpt,e.referenced_names,e.boundary_evidence_id,e.certificate_id,e.terminal_form,e.verifier_boundary_crossed,VerifiedCorpusFailureKind(e.failure_kind.value),dict(e.metadata),e.advisory) for e in r.entries]
 edges=[VerifiedCorpusDependencyEdge(x.edge_id,r.project_id,x.source_id,x.target_id,relation=x.dependency_kind.value.lower(),evidence=x.evidence,metadata=dict(x.metadata),advisory=x.advisory) for x in r.dependency_edges if x.source_kind=="entry" and x.target_kind=="entry"]
 rep=VerifiedCorpusIngestionReport(content_id("verified-corpus-from-project",r.report_id),r.project_id,None,files,ents,edges,r.verifier_execution_report,dict(r.lawbook_replay_summary),r.created_at,VerifiedCorpusIngestionStatus(r.status.value),warnings=r.warnings,criticals=r.criticals,metadata={"source_lean_project_report_id":r.report_id}); rep.summarize(); return rep
def lean_project_report_to_process_episodes(r): return [ProcessEpisodeRecord(make_process_episode_id("lean-project",e.entry_id),ProcessEpisodeStatus.TERMINAL_VERIFIED_PROOF if e.has_boundary_evidence() else ProcessEpisodeStatus.ADVISORY_ONLY,contexts=[ProcessContextItem(content_id("lean-project-context",e.entry_id),ProcessContextKind.RAW_EVENT,ProcessContextRole.ADVISORY_ONLY,e.name)],terminal_form=TerminalForm.VERIFIED_PROOF if e.has_boundary_evidence() else None,certificate_id=e.certificate_id,verifier_boundary_crossed=e.verifier_boundary_crossed) for e in r.entries]
def lean_project_report_to_proof_digestion_inputs(r): return [{"entry_id":e.entry_id,"proof_text":e.theorem_statement_excerpt,"boundary_backed":e.has_boundary_evidence(),"advisory":not e.has_boundary_evidence()} for e in r.entries]
def lean_project_report_to_discovery_value_scores(r):
 out=[]
 for e in r.entries:
  sig=DiscoveryValueSignal(content_id("lean-project-signal",e.entry_id),DiscoveryValueSignalKind.REUSE_VALUE,1.0 if e.has_boundary_evidence() else .1,source_object_kind=DiscoveryValueObjectKind.RAW_TASK); s=DiscoveryValueScore(content_id("lean-project-score",e.entry_id),e.entry_id,DiscoveryValueObjectKind.RAW_TASK,signals=[sig]); s.recompute(); out.append(s)
 return out
def lean_project_report_to_structural_identity_objects(r): return [{"object_id":e.entry_id,"name":e.name,"kind":e.entry_kind,"advisory":not e.has_boundary_evidence()} for e in r.entries]
def lean_project_report_to_route_telemetry_events(r): return [{"event_id":content_id("lean-project-telemetry",e.entry_id),"route_kind":"lean_project_subset","outcome":e.status.value,"certificate_id":e.certificate_id,"verifier_boundary_crossed":e.verifier_boundary_crossed} for e in r.entries]
def lean_project_report_to_alchemical_trace(r):
 t=AlchemicalTrace(make_alchemical_trace_id("lean-project",r.report_id))
 for p in (AlchemicalPhase.RAW_MATTER,AlchemicalPhase.CALCINATION,AlchemicalPhase.DESCENSION): t.add_step(phase=p,status=AlchemicalStatus.ADVISORY_ONLY)
 if r.verified_entry_count(): t.add_step(phase=AlchemicalPhase.FIXATION,status=AlchemicalStatus.PROMOTED_BY_VERIFIER)
 for p in (AlchemicalPhase.DISTILLATION,AlchemicalPhase.COAGULATION): t.add_step(phase=p,status=AlchemicalStatus.ADVISORY_ONLY)
 return t
def lean_project_report_to_agent_experiences(r): return [AgentExperience(content_id("lean-project-exp",e.entry_id),"lean-project",None,None,"project",None,AgentExperienceOutcome.VERIFIED_PROOF if e.has_boundary_evidence() else AgentExperienceOutcome.INVALID_CANDIDATE if e.failure_kind!=LeanProjectFailureKind.NONE else AgentExperienceOutcome.ADVISORY_ONLY,terminal_form=TerminalForm.VERIFIED_PROOF if e.has_boundary_evidence() else None,certificate_id=e.certificate_id,verifier_boundary_crossed=e.verifier_boundary_crossed) for e in r.entries]
def audit_lean_project_manifest(x): return [_af("CRITICAL","LEAN_PROJECT_MANIFEST_NON_ADVISORY","manifest non-advisory",x.manifest_id)] if not x.advisory else []
def audit_lean_project_file(x): return [_af("CRITICAL","LEAN_PROJECT_FILE_NON_ADVISORY","file extraction claims truth",x.file_id)] if not x.advisory else []
def audit_lean_project_entry(x):
 out=[]
 if x.status==LeanProjectEntryStatus.VERIFIED_BY_LOCAL_VERIFIER and not x.has_boundary_evidence(): out.append(_af("CRITICAL","LEAN_PROJECT_VERIFIED_WITHOUT_BOUNDARY","verified entry lacks boundary",x.entry_id))
 if x.has_boundary_evidence() and x.failure_kind!=LeanProjectFailureKind.NONE: out.append(_af("CRITICAL","LEAN_PROJECT_BAD_ENTRY_VERIFIED","failed entry verified",x.entry_id))
 return out
def audit_lean_project_dependency_edge(x): return [_af("CRITICAL","LEAN_PROJECT_EDGE_NON_ADVISORY","dependency edge treated as proof",x.edge_id)] if not x.advisory else []
def audit_lean_project_ingestion_report(x):
 out=sum((audit_lean_project_entry(e) for e in x.entries),[])
 if x.ok() and x.critical_count(): out.append(_af("CRITICAL","LEAN_PROJECT_OK_WITH_CRITICAL","report hides criticals",x.report_id))
 if x.lawbook_replay_summary.get("known_skip_total",0) and not x.lawbook_replay_summary.get("accepted_total",0): out.append(_af("CRITICAL","LEAN_PROJECT_SKIP_WITHOUT_ACCEPTANCE","known skip without accepted replay",x.report_id))
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
