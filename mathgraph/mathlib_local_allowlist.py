"""Local-only Mathlib-style micro-allowlist ingestion over strict verifier boundaries."""
from __future__ import annotations
import json,os,re,shutil,subprocess,tempfile
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
from mathgraph.lean_project_subset import LeanProjectDependencyEdge,LeanProjectDependencyKind,LeanProjectEntry,LeanProjectEntryStatus,LeanProjectFailureKind,LeanProjectFile,LeanProjectFileStatus,LeanProjectIngestionReport,LeanProjectIngestionStatus
from mathgraph.mathlib_micro_subset import MathlibMicroDependencyEdge,MathlibMicroDependencyKind,MathlibMicroEntry,MathlibMicroEntryStatus,MathlibMicroEnvironmentStatus,MathlibMicroFailureKind,MathlibMicroFile,MathlibMicroFileStatus,MathlibMicroIngestionReport,MathlibMicroIngestionStatus,MathlibMicroManifest,MathlibEnvironmentReport as MathlibMicroEnvironmentReport,ensure_default_mathlib_micro_subset,load_mathlib_micro_manifest
from mathgraph.process_memory import ProcessContextItem,ProcessContextKind,ProcessContextRole,ProcessEpisodeRecord,ProcessEpisodeStatus,make_process_episode_id
from mathgraph.verified_corpus import *
from mathgraph.verifier_execution import *
def _enum(n,v): return Enum(n,{x:x for x in v.split()},type=str)
MathlibLocalSourceKind=_enum("MathlibLocalSourceKind","LOCAL_MATHLIB_PROJECT LOCAL_LEAN_PROJECT SYNTHETIC_LOCAL_PROJECT EXTERNAL_REFERENCE UNKNOWN")
MathlibLocalTrustPolicy=_enum("MathlibLocalTrustPolicy","LOCAL_VERIFIER_REQUIRED TRUSTED_IMPORT_REQUIRED ADVISORY_ONLY UNKNOWN")
MathlibLocalEnvironmentStatus=_enum("MathlibLocalEnvironmentStatus","READY READY_SYNTHETIC MISSING_PROJECT_ROOT MISSING_LEAN MISSING_LAKE MISSING_MANIFEST MISSING_ALLOWLIST_FILES MATHLIB_MARKER_NOT_FOUND TOOLCHAIN_MISMATCH_WARNING NOT_A_LEAN_PROJECT SKIPPED UNKNOWN")
MathlibLocalFileStatus=_enum("MathlibLocalFileStatus","ADVISORY_EXTRACTED VERIFIED_BY_LOCAL_VERIFIER REJECTED_UNSAFE REJECTED_EXPECTED_MISSING REJECTED_VERIFIER_FAILED SKIPPED_MISSING_VERIFIER SKIPPED_ENVIRONMENT_NOT_READY SKIPPED_EMPTY_ALLOWLIST BLOCKED ERROR UNKNOWN")
MathlibLocalEntryStatus=_enum("MathlibLocalEntryStatus","ADVISORY_EXTRACTED VERIFIED_BY_LOCAL_VERIFIER REJECTED_UNSAFE REJECTED_EXPECTED_MISSING REJECTED_VERIFIER_FAILED SKIPPED_MISSING_VERIFIER SKIPPED_ENVIRONMENT_NOT_READY SKIPPED_EMPTY_ALLOWLIST BLOCKED ERROR UNKNOWN")
MathlibLocalDependencyKind=_enum("MathlibLocalDependencyKind","IMPORTS_MODULE REFERENCES_DECLARATION EXPECTED_REFERENCE TEXT_REFERENCE UNKNOWN")
MathlibLocalIngestionStatus=_enum("MathlibLocalIngestionStatus","NOT_RUN DRY_RUN COMPLETED COMPLETED_WITH_WARNINGS SKIPPED_ENVIRONMENT SKIPPED_EMPTY_ALLOWLIST FAILED ERROR UNKNOWN")
MathlibLocalFailureKind=_enum("MathlibLocalFailureKind","NONE MISSING_PROJECT_ROOT MISSING_LEAN MISSING_LAKE MISSING_MANIFEST MISSING_ALLOWLIST_FILE EMPTY_EXPECTED_DECLARATIONS UNSAFE_MARKER EXPECTED_DECLARATION_MISSING IMPORT_ERROR TYPE_ERROR VERIFIER_FAILED ENVIRONMENT_NOT_READY TRUST_POLICY_BLOCKED MANIFEST_INVALID MODULE_RESOLUTION_FAILED UNKNOWN")
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
   if f.name in enums and v is not None and not isinstance(v,Enum): v=globals()[str(f.type)](str(v))
   if getattr(f.type,"__origin__",None) is tuple and v is not None: v=tuple(tuple(x) if isinstance(x,list) else x for x in v)
   vals.append(v)
  return c(*vals)
 cls.to_dict=td; cls.from_dict=fd; cls.to_json=lambda self:_j(self.to_dict()); cls.from_json=classmethod(lambda c,t:c.from_dict(json.loads(t))); return cls
@_serial
@dataclass
class MathlibLocalAllowlistManifest:
 manifest_id:str; allowlist_id:str; name:str; version:str="0.1"; source_kind:MathlibLocalSourceKind=MathlibLocalSourceKind.LOCAL_MATHLIB_PROJECT; trust_policy:MathlibLocalTrustPolicy=MathlibLocalTrustPolicy.LOCAL_VERIFIER_REQUIRED; proof_system:str="lean"; project_root:str|None=None; module_prefix:str="Mathlib"; files:list[dict[str,Any]]=field(default_factory=list); pinned_revision:str|None=None; lean_toolchain:str|None=None; source_uri:str|None=None; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def write_json(self,p): _w(p,self.to_json())
 @classmethod
 def read_json(c,p): return c.from_json(Path(p).read_text())
@_serial
@dataclass
class MathlibLocalEnvironmentReport:
 environment_id:str; allowlist_id:str; project_root:str|None=None; lean_path:str|None=None; lake_path:str|None=None; lean_version:str|None=None; lake_version:str|None=None; lean_toolchain_file:str|None=None; manifest_path:str|None=None; checked_files:tuple[str,...]=(); missing_files:tuple[str,...]=(); project_markers:tuple[str,...]=(); status:MathlibLocalEnvironmentStatus=MathlibLocalEnvironmentStatus.UNKNOWN; warnings:tuple[str,...]=(); criticals:tuple[str,...]=(); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def ready(self): return self.status in {MathlibLocalEnvironmentStatus.READY,MathlibLocalEnvironmentStatus.READY_SYNTHETIC}
@_serial
@dataclass
class MathlibLocalFile:
 file_id:str; allowlist_id:str; path:str; module_name:str; text_hash:str|None=None; expected_declaration_names:tuple[str,...]=(); expected_short_names:tuple[str,...]=(); declared_names:tuple[str,...]=(); declared_full_names:tuple[str,...]=(); imports:tuple[str,...]=(); expected_imports:tuple[str,...]=(); unsafe_markers:tuple[str,...]=(); expected_reference_dependencies:tuple[tuple[str,str],...]=(); status:MathlibLocalFileStatus=MathlibLocalFileStatus.ADVISORY_EXTRACTED; failure_kind:MathlibLocalFailureKind=MathlibLocalFailureKind.NONE; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
@_serial
@dataclass
class MathlibLocalEntry:
 entry_id:str; allowlist_id:str; file_id:str; module_name:str; name:str; full_name:str; entry_kind:str="theorem"; status:MathlibLocalEntryStatus=MathlibLocalEntryStatus.ADVISORY_EXTRACTED; theorem_statement_excerpt:str=""; referenced_names:tuple[str,...]=(); boundary_evidence_id:str|None=None; certificate_id:str|None=None; terminal_form:str|None=None; verifier_boundary_crossed:bool=False; failure_kind:MathlibLocalFailureKind=MathlibLocalFailureKind.NONE; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def has_boundary_evidence(self): return bool(self.verifier_boundary_crossed and self.boundary_evidence_id and self.certificate_id and self.terminal_form==TerminalForm.VERIFIED_PROOF.value and self.status==MathlibLocalEntryStatus.VERIFIED_BY_LOCAL_VERIFIER)
@_serial
@dataclass
class MathlibLocalDependencyEdge:
 edge_id:str; allowlist_id:str; source_kind:str; source_id:str; target_kind:str; target_id:str; dependency_kind:MathlibLocalDependencyKind; source_name:str=""; target_name:str=""; evidence:str=""; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
@dataclass
class MathlibLocalIngestionReport:
 report_id:str; allowlist_id:str; manifest:MathlibLocalAllowlistManifest|None=None; environment_report:MathlibLocalEnvironmentReport|None=None; files:list[MathlibLocalFile]=field(default_factory=list); entries:list[MathlibLocalEntry]=field(default_factory=list); dependency_edges:list[MathlibLocalDependencyEdge]=field(default_factory=list); verifier_execution_report:Any|None=None; lawbook_replay_summary:dict[str,Any]=field(default_factory=dict); created_at:str=field(default_factory=lambda:_now()); status:MathlibLocalIngestionStatus=MathlibLocalIngestionStatus.UNKNOWN; summary:dict[str,Any]=field(default_factory=dict); warnings:tuple[str,...]=(); criticals:tuple[str,...]=(); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def file_count(self): return len(self.files)
 def entry_count(self): return len(self.entries)
 def verified_entry_count(self): return sum(e.has_boundary_evidence() for e in self.entries)
 def boundary_evidence_count(self): return self.verified_entry_count()
 def dependency_edge_count(self): return len(self.dependency_edges)
 def import_edge_count(self): return sum(e.dependency_kind==MathlibLocalDependencyKind.IMPORTS_MODULE for e in self.dependency_edges)
 def reference_edge_count(self): return sum(e.dependency_kind in {MathlibLocalDependencyKind.REFERENCES_DECLARATION,MathlibLocalDependencyKind.EXPECTED_REFERENCE,MathlibLocalDependencyKind.TEXT_REFERENCE} for e in self.dependency_edges)
 def warning_count(self): return len(self.warnings)
 def critical_count(self): return len(self.criticals)
 def summarize(self):
  self.summary={"file_total":len(self.files),"entry_total":len(self.entries),"verified_entry_total":self.verified_entry_count(),"boundary_evidence_total":self.boundary_evidence_count(),"dependency_edge_total":len(self.dependency_edges),"import_edge_total":self.import_edge_count(),"reference_edge_total":self.reference_edge_count(),"status_counts":_counts(e.status.value for e in self.entries),"failure_kind_counts":_counts(e.failure_kind.value for e in self.entries),"warning_total":len(self.warnings),"critical_total":len(self.criticals),"environment_status":self.environment_report.status.value if self.environment_report else "UNKNOWN"}; return self.summary
 def ok(self): return self.critical_count()==0 and self.status not in {MathlibLocalIngestionStatus.FAILED,MathlibLocalIngestionStatus.ERROR} and not any(e.has_boundary_evidence() and e.failure_kind!=MathlibLocalFailureKind.NONE for e in self.entries)
 def to_dict(self): return {**self.__dict__,"manifest":self.manifest.to_dict() if self.manifest else None,"environment_report":self.environment_report.to_dict() if self.environment_report else None,"files":[x.to_dict() for x in self.files],"entries":[x.to_dict() for x in self.entries],"dependency_edges":[x.to_dict() for x in self.dependency_edges],"verifier_execution_report":self.verifier_execution_report.to_dict() if hasattr(self.verifier_execution_report,"to_dict") else self.verifier_execution_report,"status":self.status.value,"warnings":list(self.warnings),"criticals":list(self.criticals)}
 @classmethod
 def from_dict(c,d): return c(str(d["report_id"]),str(d["allowlist_id"]),MathlibLocalAllowlistManifest.from_dict(d["manifest"]) if d.get("manifest") else None,MathlibLocalEnvironmentReport.from_dict(d["environment_report"]) if d.get("environment_report") else None,[MathlibLocalFile.from_dict(x) for x in d.get("files",())],[MathlibLocalEntry.from_dict(x) for x in d.get("entries",())],[MathlibLocalDependencyEdge.from_dict(x) for x in d.get("dependency_edges",())],VerifierExecutionReport.from_dict(d["verifier_execution_report"]) if d.get("verifier_execution_report") else None,dict(d.get("lawbook_replay_summary",{})),str(d.get("created_at",_now())),MathlibLocalIngestionStatus(str(d.get("status","UNKNOWN"))),dict(d.get("summary",{})),tuple(d.get("warnings",())),tuple(d.get("criticals",())),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
 def write_json(self,p): _w(p,self.to_json())
 @classmethod
 def read_json(c,p): return c.from_json(Path(p).read_text())
 def write_jsonl(self,p): _w(p,self.to_json()+"\n")
 @classmethod
 def read_jsonl(c,p): return [c.from_json(x) for x in Path(p).read_text().splitlines() if x.strip()]
for _c,_e in [(MathlibLocalAllowlistManifest,("source_kind","trust_policy")),(MathlibLocalEnvironmentReport,("status",)),(MathlibLocalFile,("status","failure_kind")),(MathlibLocalEntry,("status","failure_kind")),(MathlibLocalDependencyEdge,("dependency_kind",))]: _serial(_c,_e)
def make_mathlib_local_manifest_id(*x): return content_id("mathlib-local-manifest",x)
def make_mathlib_environment_id(*x): return content_id("mathlib-environment",x)
def make_mathlib_local_file_id(*x): return content_id("mathlib-local-file",x)
def make_mathlib_local_entry_id(*x): return content_id("mathlib-local-entry",x)
def make_mathlib_local_dependency_edge_id(*x): return content_id("mathlib-local-edge",x)
def make_mathlib_local_ingestion_report_id(*x): return content_id("mathlib-local-report",x)
def default_mathlib_local_allowlist_manifest_dict():
 return {"allowlist_id":"example-real-local-mathlib-allowlist","name":"Example Real Local Mathlib Allowlist","version":"0.1","source_kind":"LOCAL_MATHLIB_PROJECT","trust_policy":"LOCAL_VERIFIER_REQUIRED","proof_system":"lean","project_root":None,"module_prefix":"Mathlib","pinned_revision":None,"lean_toolchain":None,"source_uri":"local-path-only","files":[{"path":"Mathlib/Data/Nat/Basic.lean","module_name":"Mathlib.Data.Nat.Basic","expected_declaration_names":[],"expected_short_names":[],"expected_imports":[],"expected_reference_dependencies":[],"expected_status":"environment_dependent","category":"safe"}],"metadata":{"note":"Template only. Fill expected_declaration_names for your local Mathlib revision."}}
def synthetic_external_allowlist_manifest_from_mathlib_micro(synthetic_root):
 micro=load_mathlib_micro_manifest(Path(synthetic_root)/"mathlib_micro_manifest.json")
 d=micro.to_dict(); return {"allowlist_id":"synthetic-external-mathlib-allowlist","name":"Synthetic external Mathlib allowlist","version":d["version"],"source_kind":"SYNTHETIC_LOCAL_PROJECT","trust_policy":d["trust_policy"],"proof_system":d["proof_system"],"project_root":str(Path(synthetic_root).resolve()),"module_prefix":d["module_prefix"],"files":d["files"],"source_uri":"synthetic-local-fixture","metadata":{"source_subset_id":micro.subset_id}}
def ensure_default_mathlib_local_allowlist_examples(root,*,overwrite=False):
 root=Path(root); root.mkdir(parents=True,exist_ok=True); synthetic_root=Path(__file__).resolve().parents[1]/"examples"/"mathlib_micro_subset"; ensure_default_mathlib_micro_subset(synthetic_root)
 p1=root/"local_mathlib_allowlist_manifest.example.json"; p2=root/"synthetic_external_allowlist_manifest.json"
 if overwrite or not p1.exists(): p1.write_text(json.dumps(default_mathlib_local_allowlist_manifest_dict(),indent=2)+"\n",encoding="utf-8")
 if overwrite or not p2.exists():
  d=synthetic_external_allowlist_manifest_from_mathlib_micro(synthetic_root); d["project_root"]="../mathlib_micro_subset"; p2.write_text(json.dumps(d,indent=2)+"\n",encoding="utf-8")
 return p1,p2
def load_mathlib_local_allowlist_manifest(path):
 p=Path(path); d=json.loads(p.read_text()); root=(p.parent/str(d.get("project_root","."))).resolve()
 return MathlibLocalAllowlistManifest(make_mathlib_local_manifest_id(d),d["allowlist_id"],d["name"],d.get("version","0.1"),MathlibLocalSourceKind(d.get("source_kind","LOCAL_MATHLIB_PROJECT")),MathlibLocalTrustPolicy(d.get("trust_policy","LOCAL_VERIFIER_REQUIRED")),d.get("proof_system","lean"),str(root) if d.get("project_root") is not None else None,d.get("module_prefix","Mathlib"),list(d.get("files",())),d.get("pinned_revision"),d.get("lean_toolchain"),d.get("source_uri"),dict(d.get("metadata",{})))
def build_synthetic_external_allowlist_manifest(synthetic_root=None,*,ensure_synthetic_subset=True):
 root=Path(synthetic_root or Path(__file__).resolve().parents[1]/"examples"/"mathlib_micro_subset")
 if ensure_synthetic_subset: ensure_default_mathlib_micro_subset(root)
 return MathlibLocalAllowlistManifest.from_dict({"manifest_id":make_mathlib_local_manifest_id("synthetic",str(root)),**synthetic_external_allowlist_manifest_from_mathlib_micro(root)})
def detect_mathlib_local_environment(manifest,*,project_root=None,require_lake=False,require_mathlib_marker=False,timeout_sec=10.0):
 m=manifest if isinstance(manifest,MathlibLocalAllowlistManifest) else load_mathlib_local_allowlist_manifest(manifest) if isinstance(manifest,(str,Path)) else MathlibLocalAllowlistManifest.from_dict({"manifest_id":make_mathlib_local_manifest_id(manifest),**dict(manifest)})
 if project_root: m.project_root=str(Path(project_root).resolve())
 root=Path(m.project_root or "."); lean=shutil.which("lean"); lake=shutil.which("lake"); miss=tuple(str(root/x["path"]) for x in m.files if not (root/x["path"]).exists()); warns=[]; crit=[]
 markers=tuple(x for x in ("Mathlib","lakefile.lean","lakefile.toml","lake-manifest.json","lean-toolchain") if (root/x).exists()); tc=str(root/"lean-toolchain") if (root/"lean-toolchain").exists() else None
 if not root.exists(): status=MathlibLocalEnvironmentStatus.MISSING_PROJECT_ROOT; warns.append("project root missing")
 elif miss: status=MathlibLocalEnvironmentStatus.MISSING_ALLOWLIST_FILES; crit.append("manifest allowlist files missing")
 elif not lean: status=MathlibLocalEnvironmentStatus.MISSING_LEAN; warns.append("lean missing")
 elif require_lake and not lake: status=MathlibLocalEnvironmentStatus.MISSING_LAKE; warns.append("lake missing")
 elif require_mathlib_marker and not markers: status=MathlibLocalEnvironmentStatus.MATHLIB_MARKER_NOT_FOUND; warns.append("mathlib marker missing")
 else: status=MathlibLocalEnvironmentStatus.READY_SYNTHETIC if m.source_kind==MathlibLocalSourceKind.SYNTHETIC_LOCAL_PROJECT else MathlibLocalEnvironmentStatus.READY
 return MathlibLocalEnvironmentReport(make_mathlib_environment_id(m.allowlist_id,str(root)),m.allowlist_id,str(root),lean,lake,_version([lean,"--version"]) if lean else None,_version([lake,"--version"]) if lake else None,tc,None,tuple(str(root/x["path"]) for x in m.files),miss,markers,status,tuple(warns),tuple(crit))
def mathlib_local_module_name_from_path(path,*,project_root=None):
 p=Path(path)
 if project_root is not None:
  try:p=p.resolve().relative_to(Path(project_root).resolve())
  except ValueError: pass
 return ".".join(p.with_suffix("").parts)
def mathlib_local_path_from_module_name(module_name,*,project_root): return Path(project_root).joinpath(*module_name.split(".")).with_suffix(".lean")
def extract_imports_from_lean_text(text): return tuple(re.findall(r"(?m)^\s*import\s+([A-Za-z0-9_.]+)",text))
def extract_namespace_stack_from_lean_text(text): return tuple(re.findall(r"(?m)^\s*namespace\s+([A-Za-z_][A-Za-z0-9_]*)",text))
def qualify_declaration_name(short_name,*,module_name,namespace_stack=(),module_prefix=""):
 return short_name if "." in short_name else f"{module_prefix}.{short_name}" if module_prefix else ".".join((*namespace_stack,short_name)) if namespace_stack else short_name
def extract_declared_entries_from_mathlib_local_text(text,*,allowlist_id,file_id,module_name,module_prefix="Mathlib.MathGraph"):
 out=[]
 for name in extract_theorem_declarations(text):
  m=re.search(rf"(?ms)^(?:theorem|lemma)\s+{re.escape(name)}\b.*?(?=^\s*(?:theorem|lemma|def)\s+|\Z)",text)
  full=qualify_declaration_name(name,module_name=module_name,namespace_stack=extract_namespace_stack_from_lean_text(text),module_prefix=module_prefix)
  out.append(MathlibLocalEntry(make_mathlib_local_entry_id(allowlist_id,file_id,full),allowlist_id,file_id,module_name,name,full,theorem_statement_excerpt=(m.group(0).strip()[:240] if m else name)))
 return out
def extract_referenced_names_from_lean_text(text,candidate_names): return tuple(n for n in candidate_names if re.search(rf"\b{re.escape(n.split('.')[-1])}\b",text))
def build_mathlib_local_file(m,r):
 root=Path(m.project_root or "."); p=root/r["path"]; t=p.read_text(); short=extract_theorem_declarations(t); full=tuple(qualify_declaration_name(x,module_name=r.get("module_name",""),namespace_stack=extract_namespace_stack_from_lean_text(t),module_prefix=m.module_prefix) for x in short)
 return MathlibLocalFile(make_mathlib_local_file_id(m.allowlist_id,r["path"]),m.allowlist_id,str(p.resolve()),r.get("module_name") or mathlib_local_module_name_from_path(p,project_root=root),_hash(t),tuple(r.get("expected_declaration_names",())),tuple(r.get("expected_short_names",())),short,full,extract_imports_from_lean_text(t),tuple(r.get("expected_imports",())),extract_unsafe_markers(t),tuple(tuple(x) for x in r.get("expected_reference_dependencies",())),metadata={"expected_status":r.get("expected_status",""),"category":r.get("category","")})
def build_mathlib_local_dependency_edges(allowlist_id,entries,files):
 out=[]; by_module={f.module_name:f for f in files}; by_name={e.name:e for e in entries}; by_full={e.full_name:e for e in entries}
 for f in files:
  for imp in f.imports:
   if imp in by_module:
    target=by_module[imp]; out.append(MathlibLocalDependencyEdge(make_mathlib_local_dependency_edge_id(f.file_id,target.file_id,"import"),allowlist_id,"module",f.file_id,"module",target.file_id,MathlibLocalDependencyKind.IMPORTS_MODULE,f.module_name,target.module_name,"import"))
  own={e.name for e in entries if e.file_id==f.file_id}
  for e in [x for x in entries if x.file_id==f.file_id]:
   refs=tuple(n for n in extract_referenced_names_from_lean_text(e.theorem_statement_excerpt,by_name) if n not in own); e.referenced_names=refs
   for n in refs:
    target=by_name[n]; out.append(MathlibLocalDependencyEdge(make_mathlib_local_dependency_edge_id(e.entry_id,target.entry_id,"text"),allowlist_id,"entry",e.entry_id,"entry",target.entry_id,MathlibLocalDependencyKind.REFERENCES_DECLARATION,e.name,target.name,"text_reference"))
  for a,b in f.expected_reference_dependencies:
   if a in by_name and b in by_name: out.append(MathlibLocalDependencyEdge(make_mathlib_local_dependency_edge_id(a,b,"expected"),allowlist_id,"entry",by_name[a].entry_id,"entry",by_name[b].entry_id,MathlibLocalDependencyKind.EXPECTED_REFERENCE,a,b,"manifest_expected_reference"))
 return out
def _contract(f,root,build_root,allow_execution,timeout_sec):
 out=build_root.joinpath(*f.module_name.split(".")).with_suffix(".olean"); out.parent.mkdir(parents=True,exist_ok=True)
 return VerifierCommandContract(make_verifier_command_contract_id(f.path,f.expected_short_names,allow_execution),VerifierSystemKind.LEAN,VerifierExecutionMode.CHECK_FILE,("lean","-o",str(out),f.path),str(root),f.path,f.text_hash,timeout_sec,allow_execution,False,False,str(root),f.expected_short_names,{"lean_path":str(build_root)})
def ingest_mathlib_local_allowlist(manifest,*,project_root=None,workspace_root=None,allow_execution=False,allow_missing_verifier=True,timeout_sec=20.0,accept_verified_entries_in_memory=False,require_lake=False,require_mathlib_marker=False):
 m=manifest if isinstance(manifest,MathlibLocalAllowlistManifest) else load_mathlib_local_allowlist_manifest(manifest) if isinstance(manifest,(str,Path)) else MathlibLocalAllowlistManifest.from_dict({"manifest_id":make_mathlib_local_manifest_id(manifest),**dict(manifest)})
 if project_root: m.project_root=str(Path(project_root).resolve())
 env=detect_mathlib_local_environment(m,require_lake=require_lake,require_mathlib_marker=require_mathlib_marker); root=Path(m.project_root or ".").resolve()
 files=[build_mathlib_local_file(m,x) for x in m.files if (root/x["path"]).exists()]; entries=[e for f in files for e in extract_declared_entries_from_mathlib_local_text(Path(f.path).read_text(),allowlist_id=m.allowlist_id,file_id=f.file_id,module_name=f.module_name,module_prefix=m.module_prefix)]; edges=build_mathlib_local_dependency_edges(m.allowlist_id,entries,files); warnings=list(env.warnings); crit=list(env.criticals)
 vr=VerifierExecutionReport(make_verifier_execution_report_id([],allow_execution))
 if allow_execution and env.ready():
  build_root=Path(workspace_root or Path(tempfile.gettempdir())/"mathgraph_mathlib_local_tmp").resolve()/"olean"; vr=build_verifier_execution_report(contracts=[_contract(f,root,build_root,allow_execution,timeout_sec) for f in files if f.expected_declaration_names],allow_execution=True,timeout_sec=timeout_sec)
 for i,f in enumerate(files):
  res=vr.results[i] if i<len(vr.results) and f.expected_declaration_names else None; ev=next((e for e in vr.boundary_evidence if res and e.result_id==res.result_id),None); expected_full=set(f.expected_declaration_names); expected_short=set(f.expected_short_names)
  if f.unsafe_markers: f.status=MathlibLocalFileStatus.REJECTED_UNSAFE; f.failure_kind=MathlibLocalFailureKind.UNSAFE_MARKER
  elif not expected_full: f.status=MathlibLocalFileStatus.SKIPPED_EMPTY_ALLOWLIST; f.failure_kind=MathlibLocalFailureKind.EMPTY_EXPECTED_DECLARATIONS; warnings.append("empty expected declaration allowlist")
  elif expected_full and not expected_full.issubset(set(f.declared_full_names)) and expected_short and not expected_short.issubset(set(f.declared_names)): f.status=MathlibLocalFileStatus.REJECTED_EXPECTED_MISSING; f.failure_kind=MathlibLocalFailureKind.EXPECTED_DECLARATION_MISSING
  elif allow_execution and not env.ready():
   f.status=MathlibLocalFileStatus.SKIPPED_MISSING_VERIFIER if env.status==MathlibLocalEnvironmentStatus.MISSING_LEAN else MathlibLocalFileStatus.SKIPPED_ENVIRONMENT_NOT_READY; f.failure_kind=MathlibLocalFailureKind.MISSING_VERIFIER if env.status==MathlibLocalEnvironmentStatus.MISSING_LEAN else MathlibLocalFailureKind.ENVIRONMENT_NOT_READY
  elif res and res.failure_kind==VerifierFailureKind.IMPORT_ERROR: f.status=MathlibLocalFileStatus.REJECTED_VERIFIER_FAILED; f.failure_kind=MathlibLocalFailureKind.IMPORT_ERROR
  elif ev: f.status=MathlibLocalFileStatus.VERIFIED_BY_LOCAL_VERIFIER
  elif allow_execution and res and res.status!=VerifierExecutionStatus.SUCCESS: f.status=MathlibLocalFileStatus.REJECTED_VERIFIER_FAILED; f.failure_kind=MathlibLocalFailureKind.VERIFIER_FAILED
  for e in [x for x in entries if x.file_id==f.file_id]:
   if f.status==MathlibLocalFileStatus.REJECTED_UNSAFE: e.status=MathlibLocalEntryStatus.REJECTED_UNSAFE; e.failure_kind=MathlibLocalFailureKind.UNSAFE_MARKER
   elif f.status==MathlibLocalFileStatus.SKIPPED_EMPTY_ALLOWLIST: e.status=MathlibLocalEntryStatus.SKIPPED_EMPTY_ALLOWLIST; e.failure_kind=MathlibLocalFailureKind.EMPTY_EXPECTED_DECLARATIONS
   elif f.status==MathlibLocalFileStatus.REJECTED_EXPECTED_MISSING: e.status=MathlibLocalEntryStatus.REJECTED_EXPECTED_MISSING; e.failure_kind=MathlibLocalFailureKind.EXPECTED_DECLARATION_MISSING
   elif f.status==MathlibLocalFileStatus.SKIPPED_MISSING_VERIFIER: e.status=MathlibLocalEntryStatus.SKIPPED_MISSING_VERIFIER; e.failure_kind=MathlibLocalFailureKind.MISSING_VERIFIER
   elif f.status==MathlibLocalFileStatus.SKIPPED_ENVIRONMENT_NOT_READY: e.status=MathlibLocalEntryStatus.SKIPPED_ENVIRONMENT_NOT_READY; e.failure_kind=MathlibLocalFailureKind.ENVIRONMENT_NOT_READY
   elif f.failure_kind in {MathlibLocalFailureKind.IMPORT_ERROR,MathlibLocalFailureKind.TYPE_ERROR,MathlibLocalFailureKind.VERIFIER_FAILED}: e.status=MathlibLocalEntryStatus.REJECTED_VERIFIER_FAILED; e.failure_kind=f.failure_kind
   elif ev and (e.full_name in expected_full or e.name in expected_short): e.status=MathlibLocalEntryStatus.VERIFIED_BY_LOCAL_VERIFIER; e.boundary_evidence_id=ev.evidence_id; e.certificate_id=ev.certificate_id; e.terminal_form=ev.terminal_form; e.verifier_boundary_crossed=True
 rep=MathlibLocalIngestionReport(make_mathlib_local_ingestion_report_id(m.allowlist_id,[f.file_id for f in files],allow_execution),m.allowlist_id,m,env,files,entries,edges,vr,warnings=tuple(dict.fromkeys(warnings)),criticals=tuple(crit))
 rep.status=MathlibLocalIngestionStatus.DRY_RUN if not allow_execution else MathlibLocalIngestionStatus.SKIPPED_ENVIRONMENT if not env.ready() else MathlibLocalIngestionStatus.SKIPPED_EMPTY_ALLOWLIST if files and all(not f.expected_declaration_names for f in files) else MathlibLocalIngestionStatus.COMPLETED_WITH_WARNINGS if warnings else MathlibLocalIngestionStatus.COMPLETED
 rep.lawbook_replay_summary=review_and_optionally_accept_mathlib_local_entries(rep,accept_in_memory=accept_verified_entries_in_memory); rep.summarize(); return rep
def mathlib_local_report_to_lawbook_candidates(r): return [LawbookEntry(make_lawbook_entry_id("mathlib-local",e.entry_id),LawbookEntryKind.VERIFIED_PROOF_ENTRY,LawbookEntryStatus.CANDIDATE,claim_id=e.full_name,raw=e.theorem_statement_excerpt,terminal_form=TerminalForm.VERIFIED_PROOF,certificate_id=e.certificate_id,verifier_boundary_crossed=True,acceptance_boundary=LawbookAcceptanceBoundary.VERIFIED_PROOF,metadata={"mathlib_local_report_id":r.report_id,"mathlib_local_entry_id":e.entry_id}) for e in r.entries if e.has_boundary_evidence()]
def review_and_optionally_accept_mathlib_local_entries(r,*,accept_in_memory=False):
 cs=mathlib_local_report_to_lawbook_candidates(r); reviews=[review_lawbook_candidate(x) for x in cs]; accepted=[accept_lawbook_entry(e,v,accepted_by="mathlib-local-replay") for e,v in zip(cs,reviews) if accept_in_memory and v.decision.value=="ACCEPT"]; store=LawbookStore(make_lawbook_store_id("mathlib-local-replay",r.report_id),entries=accepted,reviews=reviews); answers=[query_lawbook_store_by_certificate(store,x.certificate_id) for x in cs if x.certificate_id]; return {"candidate_total":len(cs),"review_total":len(reviews),"accepted_total":len(accepted),"query_total":len(answers),"known_skip_total":sum(a.known_skip_decision.value.startswith("SKIP_") for a in answers),"warnings":[],"criticals":[]}
def mathlib_local_report_to_markdown(r):
 s=r.summarize(); env=r.environment_report; lines=["# Mathlib Local Allowlist Ingestion","",f"- Subset: `{r.allowlist_id}`",f"- Name: {r.manifest.name if r.manifest else ''}",f"- Version: {r.manifest.version if r.manifest else ''}",f"- Source kind: {r.manifest.source_kind.value if r.manifest else ''}",f"- Trust policy: {r.manifest.trust_policy.value if r.manifest else ''}",f"- Environment: {env.status.value if env else 'UNKNOWN'}",f"- Lean: {env.lean_path if env else ''}",f"- Lake: {env.lake_path if env else ''}",f"- Status: {r.status.value}",f"- Files: {s['file_total']}",f"- Entries: {s['entry_total']}",f"- Verified entries: {s['verified_entry_total']}",f"- Boundary evidence: {s['boundary_evidence_total']}",f"- Dependency edges: {s['dependency_edge_total']}",f"- Import edges: {s['import_edge_total']}",f"- Reference edges: {s['reference_edge_total']}","", "| file/module | declared | expected | imports | status | boundary | failure |","| --- | --- | --- | --- | --- | --- | --- |"]
 for f in r.files:
  xs=[e for e in r.entries if e.file_id==f.file_id]; lines.append(f"| {Path(f.path).name} / {f.module_name} | {', '.join(f.declared_full_names)} | {', '.join(f.expected_declaration_names)} | {', '.join(f.imports)} | {', '.join(dict.fromkeys(e.status.value for e in xs))} | {'yes' if any(e.has_boundary_evidence() for e in xs) else 'no'} | {', '.join(dict.fromkeys(e.failure_kind.value for e in xs))} |")
 lines+=["",f"Dependency summary: imports={r.import_edge_count()}, references={r.reference_edge_count()}",f"Lawbook replay: `{r.lawbook_replay_summary}`","","Boundary policy: environment checks, declarations, imports, and reference graphs are advisory; only valid verifier/importer/finite-validator/chain-audit evidence promotes truth."]; return "\n".join(lines)+"\n"
def mathlib_local_report_to_dependency_graph(r): return {"nodes":[{"id":f.file_id,"kind":"module","name":f.module_name} for f in r.files]+[{"id":e.entry_id,"kind":"entry","name":e.full_name,"status":e.status.value} for e in r.entries],"edges":[x.to_dict() for x in r.dependency_edges],"metadata":{"allowlist_id":r.allowlist_id,"advisory":True}}
def write_dependency_graph_json(r,p): _w(p,_j(mathlib_local_report_to_dependency_graph(r)))
def write_dependency_graph_jsonl(r,p):
 g=mathlib_local_report_to_dependency_graph(r); _w(p,"".join(_j({"kind":"node",**x})+"\n" for x in g["nodes"])+"".join(_j({"kind":"edge",**x})+"\n" for x in g["edges"]))
def mathlib_local_report_to_api_response(r):
 from mathgraph.api_service import _resp
 req=ApiRequest(make_api_request_id("mathlib-local",r.report_id),ApiRoute.MATHLIB_LOCAL_ALLOWLIST); truth=ApiTruthStatus.BOUNDARY_EVIDENCE_PRESENT if r.verified_entry_count() else ApiTruthStatus.BOUNDARY_REQUIRED; return _resp(req,route_result_from_artifacts(req.route,[r],truth_status=truth,safety=ApiSafetyLevel.SAFE_REVIEW_REQUIRED))
def mathlib_local_report_to_lean_project_report(r):
 files=[LeanProjectFile(f.file_id,r.allowlist_id,f.path,f.module_name,f.text_hash,f.expected_short_names,f.declared_names,f.imports,f.expected_imports,f.unsafe_markers,f.expected_reference_dependencies,LeanProjectFileStatus(f.status.value.replace("SKIPPED_ENVIRONMENT_NOT_READY","BLOCKED")),LeanProjectFailureKind("MISSING_VERIFIER" if f.failure_kind==MathlibLocalFailureKind.ENVIRONMENT_NOT_READY else f.failure_kind.value.replace("EXPECTED_DECLARATION_MISSING","EXPECTED_THEOREM_MISSING")),dict(f.metadata),f.advisory) for f in r.files]
 ents=[LeanProjectEntry(e.entry_id,r.allowlist_id,e.file_id,e.module_name,e.name,e.entry_kind,LeanProjectEntryStatus(e.status.value.replace("SKIPPED_ENVIRONMENT_NOT_READY","BLOCKED")),e.theorem_statement_excerpt,e.referenced_names,e.boundary_evidence_id,e.certificate_id,e.terminal_form,e.verifier_boundary_crossed,LeanProjectFailureKind("MISSING_VERIFIER" if e.failure_kind==MathlibLocalFailureKind.ENVIRONMENT_NOT_READY else e.failure_kind.value.replace("EXPECTED_DECLARATION_MISSING","EXPECTED_THEOREM_MISSING")),dict(e.metadata),e.advisory) for e in r.entries]
 edges=[LeanProjectDependencyEdge(x.edge_id,r.allowlist_id,x.source_kind,x.source_id,x.target_kind,x.target_id,LeanProjectDependencyKind(x.dependency_kind.value),x.source_name,x.target_name,x.evidence,dict(x.metadata),x.advisory) for x in r.dependency_edges]
 rep=LeanProjectIngestionReport(content_id("lean-project-from-mathlib",r.report_id),r.allowlist_id,None,files,ents,edges,r.verifier_execution_report,dict(r.lawbook_replay_summary),r.created_at,LeanProjectIngestionStatus.DRY_RUN if r.status==MathlibLocalIngestionStatus.DRY_RUN else LeanProjectIngestionStatus.COMPLETED,warnings=r.warnings,criticals=r.criticals,metadata={"source_mathlib_local_report_id":r.report_id}); rep.summarize(); return rep
def mathlib_local_report_to_verified_corpus_report(r): return mathlib_local_report_to_lean_project_report(r) and __import__("mathgraph.lean_project_subset",fromlist=["lean_project_report_to_verified_corpus_report"]).lean_project_report_to_verified_corpus_report(mathlib_local_report_to_lean_project_report(r))
def mathlib_local_report_to_mathlib_micro_report(r):
 files=[MathlibMicroFile(f.file_id,r.allowlist_id,f.path,f.module_name,f.text_hash,f.expected_declaration_names,f.expected_short_names,f.declared_names,f.declared_full_names,f.imports,f.expected_imports,f.unsafe_markers,f.expected_reference_dependencies,MathlibMicroFileStatus(f.status.value.replace("SKIPPED_EMPTY_ALLOWLIST","BLOCKED")),MathlibMicroFailureKind("NONE" if f.failure_kind==MathlibLocalFailureKind.EMPTY_EXPECTED_DECLARATIONS else f.failure_kind.value),dict(f.metadata),f.advisory) for f in r.files]
 ents=[MathlibMicroEntry(e.entry_id,r.allowlist_id,e.file_id,e.module_name,e.name,e.full_name,e.entry_kind,MathlibMicroEntryStatus(e.status.value.replace("SKIPPED_EMPTY_ALLOWLIST","BLOCKED")),e.theorem_statement_excerpt,e.referenced_names,e.boundary_evidence_id,e.certificate_id,e.terminal_form,e.verifier_boundary_crossed,MathlibMicroFailureKind("NONE" if e.failure_kind==MathlibLocalFailureKind.EMPTY_EXPECTED_DECLARATIONS else e.failure_kind.value),dict(e.metadata),e.advisory) for e in r.entries]
 edges=[MathlibMicroDependencyEdge(x.edge_id,r.allowlist_id,x.source_kind,x.source_id,x.target_kind,x.target_id,MathlibMicroDependencyKind(x.dependency_kind.value),x.source_name,x.target_name,x.evidence,dict(x.metadata),x.advisory) for x in r.dependency_edges]
 env=MathlibMicroEnvironmentReport(r.environment_report.environment_id,r.allowlist_id,r.environment_report.project_root,r.environment_report.lean_path,r.environment_report.lake_path,r.environment_report.lean_version,r.environment_report.lake_version,None,r.environment_report.checked_files,r.environment_report.missing_files,MathlibMicroEnvironmentStatus.READY if r.environment_report.ready() else MathlibMicroEnvironmentStatus.SKIPPED,r.environment_report.warnings,r.environment_report.criticals) if r.environment_report else None
 rep=MathlibMicroIngestionReport(content_id("mathlib-micro-from-local",r.report_id),r.allowlist_id,None,env,files,ents,edges,r.verifier_execution_report,dict(r.lawbook_replay_summary),r.created_at,MathlibMicroIngestionStatus.DRY_RUN if r.status==MathlibLocalIngestionStatus.DRY_RUN else MathlibMicroIngestionStatus.COMPLETED,warnings=r.warnings,criticals=r.criticals,metadata={"source_mathlib_local_report_id":r.report_id}); rep.summarize(); return rep
def mathlib_local_report_to_process_episodes(r): return [ProcessEpisodeRecord(make_process_episode_id("mathlib-local",e.entry_id),ProcessEpisodeStatus.TERMINAL_VERIFIED_PROOF if e.has_boundary_evidence() else ProcessEpisodeStatus.ADVISORY_ONLY,contexts=[ProcessContextItem(content_id("mathlib-local-context",e.entry_id),ProcessContextKind.RAW_EVENT,ProcessContextRole.ADVISORY_ONLY,e.full_name)],terminal_form=TerminalForm.VERIFIED_PROOF if e.has_boundary_evidence() else None,certificate_id=e.certificate_id,verifier_boundary_crossed=e.verifier_boundary_crossed) for e in r.entries]
def mathlib_local_report_to_proof_digestion_inputs(r): return [{"entry_id":e.entry_id,"proof_text":e.theorem_statement_excerpt,"boundary_backed":e.has_boundary_evidence(),"advisory":not e.has_boundary_evidence()} for e in r.entries]
def mathlib_local_report_to_discovery_value_scores(r):
 out=[]
 for e in r.entries:
  sig=DiscoveryValueSignal(content_id("mathlib-local-signal",e.entry_id),DiscoveryValueSignalKind.REUSE_VALUE,1.0 if e.has_boundary_evidence() else .1,source_object_kind=DiscoveryValueObjectKind.RAW_TASK); s=DiscoveryValueScore(content_id("mathlib-local-score",e.entry_id),e.entry_id,DiscoveryValueObjectKind.RAW_TASK,signals=[sig]); s.recompute(); out.append(s)
 return out
def mathlib_local_report_to_structural_identity_objects(r): return [{"object_id":e.entry_id,"name":e.full_name,"kind":e.entry_kind,"advisory":not e.has_boundary_evidence()} for e in r.entries]
def mathlib_local_report_to_route_telemetry_events(r): return [{"event_id":content_id("mathlib-local-telemetry",e.entry_id),"route_kind":"mathlib_local_allowlist","outcome":e.status.value,"certificate_id":e.certificate_id,"verifier_boundary_crossed":e.verifier_boundary_crossed} for e in r.entries]
def mathlib_local_report_to_alchemical_trace(r):
 t=AlchemicalTrace(make_alchemical_trace_id("mathlib-local",r.report_id))
 for p in (AlchemicalPhase.RAW_MATTER,AlchemicalPhase.CALCINATION,AlchemicalPhase.DESCENSION): t.add_step(phase=p,status=AlchemicalStatus.ADVISORY_ONLY)
 if r.verified_entry_count(): t.add_step(phase=AlchemicalPhase.FIXATION,status=AlchemicalStatus.PROMOTED_BY_VERIFIER)
 for p in (AlchemicalPhase.DISTILLATION,AlchemicalPhase.COAGULATION): t.add_step(phase=p,status=AlchemicalStatus.ADVISORY_ONLY)
 return t
def mathlib_local_report_to_agent_experiences(r): return [AgentExperience(content_id("mathlib-local-exp",e.entry_id),"mathlib-local",None,None,"project",None,AgentExperienceOutcome.VERIFIED_PROOF if e.has_boundary_evidence() else AgentExperienceOutcome.INVALID_CANDIDATE if e.failure_kind!=MathlibLocalFailureKind.NONE else AgentExperienceOutcome.ADVISORY_ONLY,terminal_form=TerminalForm.VERIFIED_PROOF if e.has_boundary_evidence() else None,certificate_id=e.certificate_id,verifier_boundary_crossed=e.verifier_boundary_crossed) for e in r.entries]
def audit_mathlib_local_manifest(x): return [_af("CRITICAL","MATHLIB_LOCAL_MANIFEST_NON_ADVISORY","manifest non-advisory",x.manifest_id)] if not x.advisory else []
def audit_mathlib_local_environment_report(x): return [_af("CRITICAL","MATHLIB_LOCAL_ENVIRONMENT_NON_ADVISORY","environment readiness treated as proof",x.environment_id)] if not x.advisory else []
def audit_mathlib_local_file(x): return [_af("CRITICAL","MATHLIB_LOCAL_FILE_NON_ADVISORY","file extraction claims truth",x.file_id)] if not x.advisory else []
def audit_mathlib_local_entry(x):
 out=[]
 if x.status==MathlibLocalEntryStatus.VERIFIED_BY_LOCAL_VERIFIER and not x.has_boundary_evidence(): out.append(_af("CRITICAL","MATHLIB_LOCAL_VERIFIED_WITHOUT_BOUNDARY","verified entry lacks boundary",x.entry_id))
 if x.has_boundary_evidence() and x.failure_kind!=MathlibLocalFailureKind.NONE: out.append(_af("CRITICAL","MATHLIB_LOCAL_BAD_ENTRY_VERIFIED","failed entry verified",x.entry_id))
 if x.has_boundary_evidence() and x.failure_kind==MathlibLocalFailureKind.EMPTY_EXPECTED_DECLARATIONS: out.append(_af("CRITICAL","MATHLIB_LOCAL_EMPTY_ALLOWLIST_VERIFIED","empty allowlist entry verified",x.entry_id))
 return out
def audit_mathlib_local_dependency_edge(x): return [_af("CRITICAL","MATHLIB_LOCAL_EDGE_NON_ADVISORY","dependency edge treated as proof",x.edge_id)] if not x.advisory else []
def audit_mathlib_local_ingestion_report(x):
 out=sum((audit_mathlib_local_entry(e) for e in x.entries),[])
 if x.ok() and x.critical_count(): out.append(_af("CRITICAL","MATHLIB_LOCAL_OK_WITH_CRITICAL","report hides criticals",x.report_id))
 if x.lawbook_replay_summary.get("known_skip_total",0) and not x.lawbook_replay_summary.get("accepted_total",0): out.append(_af("CRITICAL","MATHLIB_LOCAL_SKIP_WITHOUT_ACCEPTANCE","known skip without accepted replay",x.report_id))
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
def _version(argv):
 try:return subprocess.run(argv,capture_output=True,text=True,timeout=5).stdout[:200].strip()
 except Exception:return None
