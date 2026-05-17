"""Local-only Mathlib-style micro-subset ingestion over strict verifier boundaries."""
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
from mathgraph.process_memory import ProcessContextItem,ProcessContextKind,ProcessContextRole,ProcessEpisodeRecord,ProcessEpisodeStatus,make_process_episode_id
from mathgraph.verified_corpus import *
from mathgraph.verifier_execution import *
def _enum(n,v): return Enum(n,{x:x for x in v.split()},type=str)
MathlibMicroSourceKind=_enum("MathlibMicroSourceKind","SYNTHETIC_MATHLIB_STYLE_MICRO LOCAL_MATHLIB_PROJECT LOCAL_LEAN_PROJECT TRUSTED_IMPORT_SOURCE EXTERNAL_REFERENCE UNKNOWN")
MathlibMicroTrustPolicy=_enum("MathlibMicroTrustPolicy","LOCAL_VERIFIER_REQUIRED TRUSTED_IMPORT_REQUIRED ADVISORY_ONLY UNKNOWN")
MathlibMicroEnvironmentStatus=_enum("MathlibMicroEnvironmentStatus","READY MISSING_LEAN MISSING_PROJECT_ROOT MISSING_MANIFEST MISSING_MODULE_FILES MISSING_LAKE MATHLIB_NOT_DETECTED CHECK_FAILED SKIPPED UNKNOWN")
MathlibMicroFileStatus=_enum("MathlibMicroFileStatus","ADVISORY_EXTRACTED VERIFIED_BY_LOCAL_VERIFIER REJECTED_UNSAFE REJECTED_EXPECTED_MISSING REJECTED_VERIFIER_FAILED SKIPPED_MISSING_VERIFIER SKIPPED_ENVIRONMENT_NOT_READY BLOCKED ERROR UNKNOWN")
MathlibMicroEntryStatus=_enum("MathlibMicroEntryStatus","ADVISORY_EXTRACTED VERIFIED_BY_LOCAL_VERIFIER REJECTED_UNSAFE REJECTED_EXPECTED_MISSING REJECTED_VERIFIER_FAILED SKIPPED_MISSING_VERIFIER SKIPPED_ENVIRONMENT_NOT_READY BLOCKED ERROR UNKNOWN")
MathlibMicroDependencyKind=_enum("MathlibMicroDependencyKind","IMPORTS_MODULE REFERENCES_DECLARATION EXPECTED_REFERENCE TEXT_REFERENCE UNKNOWN")
MathlibMicroIngestionStatus=_enum("MathlibMicroIngestionStatus","NOT_RUN DRY_RUN COMPLETED COMPLETED_WITH_WARNINGS SKIPPED_ENVIRONMENT FAILED ERROR UNKNOWN")
MathlibMicroFailureKind=_enum("MathlibMicroFailureKind","NONE MISSING_LEAN MISSING_PROJECT_ROOT MISSING_MANIFEST MISSING_MODULE_FILE MISSING_VERIFIER UNSAFE_MARKER EXPECTED_DECLARATION_MISSING IMPORT_ERROR TYPE_ERROR VERIFIER_FAILED ENVIRONMENT_NOT_READY TRUST_POLICY_BLOCKED MANIFEST_INVALID MODULE_RESOLUTION_FAILED UNKNOWN")
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
class MathlibMicroManifest:
 manifest_id:str; subset_id:str; name:str; version:str="0.1"; source_kind:MathlibMicroSourceKind=MathlibMicroSourceKind.SYNTHETIC_MATHLIB_STYLE_MICRO; trust_policy:MathlibMicroTrustPolicy=MathlibMicroTrustPolicy.LOCAL_VERIFIER_REQUIRED; proof_system:str="lean"; project_root:str|None=None; module_prefix:str="Mathlib.MathGraph"; files:list[dict[str,Any]]=field(default_factory=list); pinned_revision:str|None=None; lean_toolchain:str|None=None; source_uri:str|None=None; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def write_json(self,p): _w(p,self.to_json())
 @classmethod
 def read_json(c,p): return c.from_json(Path(p).read_text())
@_serial
@dataclass
class MathlibEnvironmentReport:
 environment_id:str; subset_id:str; project_root:str|None=None; lean_path:str|None=None; lake_path:str|None=None; lean_version:str|None=None; lake_version:str|None=None; manifest_path:str|None=None; checked_files:tuple[str,...]=(); missing_files:tuple[str,...]=(); status:MathlibMicroEnvironmentStatus=MathlibMicroEnvironmentStatus.UNKNOWN; warnings:tuple[str,...]=(); criticals:tuple[str,...]=(); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def ready(self): return self.status==MathlibMicroEnvironmentStatus.READY
@_serial
@dataclass
class MathlibMicroFile:
 file_id:str; subset_id:str; path:str; module_name:str; text_hash:str|None=None; expected_declaration_names:tuple[str,...]=(); expected_short_names:tuple[str,...]=(); declared_names:tuple[str,...]=(); declared_full_names:tuple[str,...]=(); imports:tuple[str,...]=(); expected_imports:tuple[str,...]=(); unsafe_markers:tuple[str,...]=(); expected_reference_dependencies:tuple[tuple[str,str],...]=(); status:MathlibMicroFileStatus=MathlibMicroFileStatus.ADVISORY_EXTRACTED; failure_kind:MathlibMicroFailureKind=MathlibMicroFailureKind.NONE; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
@_serial
@dataclass
class MathlibMicroEntry:
 entry_id:str; subset_id:str; file_id:str; module_name:str; name:str; full_name:str; entry_kind:str="theorem"; status:MathlibMicroEntryStatus=MathlibMicroEntryStatus.ADVISORY_EXTRACTED; theorem_statement_excerpt:str=""; referenced_names:tuple[str,...]=(); boundary_evidence_id:str|None=None; certificate_id:str|None=None; terminal_form:str|None=None; verifier_boundary_crossed:bool=False; failure_kind:MathlibMicroFailureKind=MathlibMicroFailureKind.NONE; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def has_boundary_evidence(self): return bool(self.verifier_boundary_crossed and self.boundary_evidence_id and self.certificate_id and self.terminal_form==TerminalForm.VERIFIED_PROOF.value and self.status==MathlibMicroEntryStatus.VERIFIED_BY_LOCAL_VERIFIER)
@_serial
@dataclass
class MathlibMicroDependencyEdge:
 edge_id:str; subset_id:str; source_kind:str; source_id:str; target_kind:str; target_id:str; dependency_kind:MathlibMicroDependencyKind; source_name:str=""; target_name:str=""; evidence:str=""; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
@dataclass
class MathlibMicroIngestionReport:
 report_id:str; subset_id:str; manifest:MathlibMicroManifest|None=None; environment_report:MathlibEnvironmentReport|None=None; files:list[MathlibMicroFile]=field(default_factory=list); entries:list[MathlibMicroEntry]=field(default_factory=list); dependency_edges:list[MathlibMicroDependencyEdge]=field(default_factory=list); verifier_execution_report:Any|None=None; lawbook_replay_summary:dict[str,Any]=field(default_factory=dict); created_at:str=field(default_factory=lambda:_now()); status:MathlibMicroIngestionStatus=MathlibMicroIngestionStatus.UNKNOWN; summary:dict[str,Any]=field(default_factory=dict); warnings:tuple[str,...]=(); criticals:tuple[str,...]=(); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def file_count(self): return len(self.files)
 def entry_count(self): return len(self.entries)
 def verified_entry_count(self): return sum(e.has_boundary_evidence() for e in self.entries)
 def boundary_evidence_count(self): return self.verified_entry_count()
 def dependency_edge_count(self): return len(self.dependency_edges)
 def import_edge_count(self): return sum(e.dependency_kind==MathlibMicroDependencyKind.IMPORTS_MODULE for e in self.dependency_edges)
 def reference_edge_count(self): return sum(e.dependency_kind in {MathlibMicroDependencyKind.REFERENCES_DECLARATION,MathlibMicroDependencyKind.EXPECTED_REFERENCE,MathlibMicroDependencyKind.TEXT_REFERENCE} for e in self.dependency_edges)
 def warning_count(self): return len(self.warnings)
 def critical_count(self): return len(self.criticals)
 def summarize(self):
  self.summary={"file_total":len(self.files),"entry_total":len(self.entries),"verified_entry_total":self.verified_entry_count(),"boundary_evidence_total":self.boundary_evidence_count(),"dependency_edge_total":len(self.dependency_edges),"import_edge_total":self.import_edge_count(),"reference_edge_total":self.reference_edge_count(),"status_counts":_counts(e.status.value for e in self.entries),"failure_kind_counts":_counts(e.failure_kind.value for e in self.entries),"warning_total":len(self.warnings),"critical_total":len(self.criticals),"environment_status":self.environment_report.status.value if self.environment_report else "UNKNOWN"}; return self.summary
 def ok(self): return self.critical_count()==0 and self.status not in {MathlibMicroIngestionStatus.FAILED,MathlibMicroIngestionStatus.ERROR} and not any(e.has_boundary_evidence() and e.failure_kind!=MathlibMicroFailureKind.NONE for e in self.entries)
 def to_dict(self): return {**self.__dict__,"manifest":self.manifest.to_dict() if self.manifest else None,"environment_report":self.environment_report.to_dict() if self.environment_report else None,"files":[x.to_dict() for x in self.files],"entries":[x.to_dict() for x in self.entries],"dependency_edges":[x.to_dict() for x in self.dependency_edges],"verifier_execution_report":self.verifier_execution_report.to_dict() if hasattr(self.verifier_execution_report,"to_dict") else self.verifier_execution_report,"status":self.status.value,"warnings":list(self.warnings),"criticals":list(self.criticals)}
 @classmethod
 def from_dict(c,d): return c(str(d["report_id"]),str(d["subset_id"]),MathlibMicroManifest.from_dict(d["manifest"]) if d.get("manifest") else None,MathlibEnvironmentReport.from_dict(d["environment_report"]) if d.get("environment_report") else None,[MathlibMicroFile.from_dict(x) for x in d.get("files",())],[MathlibMicroEntry.from_dict(x) for x in d.get("entries",())],[MathlibMicroDependencyEdge.from_dict(x) for x in d.get("dependency_edges",())],VerifierExecutionReport.from_dict(d["verifier_execution_report"]) if d.get("verifier_execution_report") else None,dict(d.get("lawbook_replay_summary",{})),str(d.get("created_at",_now())),MathlibMicroIngestionStatus(str(d.get("status","UNKNOWN"))),dict(d.get("summary",{})),tuple(d.get("warnings",())),tuple(d.get("criticals",())),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
 def write_json(self,p): _w(p,self.to_json())
 @classmethod
 def read_json(c,p): return c.from_json(Path(p).read_text())
 def write_jsonl(self,p): _w(p,self.to_json()+"\n")
 @classmethod
 def read_jsonl(c,p): return [c.from_json(x) for x in Path(p).read_text().splitlines() if x.strip()]
for _c,_e in [(MathlibMicroManifest,("source_kind","trust_policy")),(MathlibEnvironmentReport,("status",)),(MathlibMicroFile,("status","failure_kind")),(MathlibMicroEntry,("status","failure_kind")),(MathlibMicroDependencyEdge,("dependency_kind",))]: _serial(_c,_e)
def make_mathlib_micro_manifest_id(*x): return content_id("mathlib-micro-manifest",x)
def make_mathlib_environment_id(*x): return content_id("mathlib-environment",x)
def make_mathlib_micro_file_id(*x): return content_id("mathlib-micro-file",x)
def make_mathlib_micro_entry_id(*x): return content_id("mathlib-micro-entry",x)
def make_mathlib_micro_dependency_edge_id(*x): return content_id("mathlib-micro-edge",x)
def make_mathlib_micro_ingestion_report_id(*x): return content_id("mathlib-micro-report",x)
def default_mathlib_micro_files():
 ns="namespace Mathlib\nnamespace MathGraph\n\n"; end="\nend MathGraph\nend Mathlib\n"
 return {"Mathlib/MathGraph/Basic.lean":ns+"theorem mgml_true : True := by\n  trivial\n\ntheorem mgml_identity (alpha : Type) (x : alpha) : x = x := by\n  rfl\n"+end,"Mathlib/MathGraph/Logic.lean":ns+"theorem mgml_and_comm (p q : Prop) : p ∧ q → q ∧ p := by\n  intro h\n  exact And.intro h.right h.left\n\ntheorem mgml_imp_trans (p q r : Prop) : (p → q) → (q → r) → p → r := by\n  intro hpq hqr hp\n  exact hqr (hpq hp)\n"+end,"Mathlib/MathGraph/Algebra.lean":ns+"theorem mgml_nat_eq_self (n : Nat) : n = n := by\n  rfl\n\ntheorem mgml_zero_eq_zero : (0 : Nat) = 0 := by\n  rfl\n"+end,"Mathlib/MathGraph/UseBasic.lean":"import Mathlib.MathGraph.Basic\n\n"+ns+"theorem mgml_uses_true : True := by\n  exact mgml_true\n\ntheorem mgml_uses_identity (alpha : Type) (x : alpha) : x = x := by\n  exact mgml_identity alpha x\n"+end,"Mathlib/MathGraph/UseAlgebra.lean":"import Mathlib.MathGraph.Algebra\nimport Mathlib.MathGraph.Logic\n\n"+ns+"theorem mgml_uses_nat_eq_self (n : Nat) : n = n := by\n  exact mgml_nat_eq_self n\n\ntheorem mgml_uses_and_comm (p q : Prop) : p ∧ q → q ∧ p := by\n  exact mgml_and_comm p q\n"+end,"Mathlib/MathGraph/BadUnsafe.lean":ns+"theorem mgml_bad_sorry : True := by\n  sorry\n"+end,"Mathlib/MathGraph/BadExpectedMissing.lean":ns+"theorem mgml_actual_name : True := by\n  trivial\n"+end,"Mathlib/MathGraph/BadImport.lean":"import Mathlib.Does.Not.Exist.MathGraphBad\n\n"+ns+"theorem mgml_bad_import : True := by\n  trivial\n"+end}
def default_mathlib_micro_manifest_dict():
 def row(path,module,names,shorts,imports=(),refs=(),status="safe",category="safe"): return {"path":path,"module_name":module,"expected_declaration_names":list(names),"expected_short_names":list(shorts),"expected_imports":list(imports),"expected_reference_dependencies":[list(x) for x in refs],"expected_status":status,"category":category}
 p="Mathlib.MathGraph."
 return {"subset_id":"mathgraph-mathlib-micro","name":"MathGraph synthetic Mathlib-style micro subset","version":"0.1","source_kind":"SYNTHETIC_MATHLIB_STYLE_MICRO","proof_system":"lean","trust_policy":"LOCAL_VERIFIER_REQUIRED","project_root":".","module_prefix":"Mathlib.MathGraph","files":[row("Mathlib/MathGraph/Basic.lean",p+"Basic",(p+"mgml_true",p+"mgml_identity"),("mgml_true","mgml_identity")),row("Mathlib/MathGraph/Logic.lean",p+"Logic",(p+"mgml_and_comm",p+"mgml_imp_trans"),("mgml_and_comm","mgml_imp_trans")),row("Mathlib/MathGraph/Algebra.lean",p+"Algebra",(p+"mgml_nat_eq_self",p+"mgml_zero_eq_zero"),("mgml_nat_eq_self","mgml_zero_eq_zero")),row("Mathlib/MathGraph/UseBasic.lean",p+"UseBasic",(p+"mgml_uses_true",p+"mgml_uses_identity"),("mgml_uses_true","mgml_uses_identity"),(p+"Basic",),(("mgml_uses_true","mgml_true"),("mgml_uses_identity","mgml_identity"))),row("Mathlib/MathGraph/UseAlgebra.lean",p+"UseAlgebra",(p+"mgml_uses_nat_eq_self",p+"mgml_uses_and_comm"),("mgml_uses_nat_eq_self","mgml_uses_and_comm"),(p+"Algebra",p+"Logic"),(("mgml_uses_nat_eq_self","mgml_nat_eq_self"),("mgml_uses_and_comm","mgml_and_comm"))),row("Mathlib/MathGraph/BadUnsafe.lean",p+"BadUnsafe",(p+"mgml_bad_sorry",),("mgml_bad_sorry",),status="unsafe",category="unsafe"),row("Mathlib/MathGraph/BadExpectedMissing.lean",p+"BadExpectedMissing",(p+"mgml_expected_name",),("mgml_expected_name",),status="expected_missing",category="expected_missing"),row("Mathlib/MathGraph/BadImport.lean",p+"BadImport",(p+"mgml_bad_import",),("mgml_bad_import",),status="import_error",category="import_error")]}
def ensure_default_mathlib_micro_subset(root,*,overwrite=False):
 root=Path(root); root.mkdir(parents=True,exist_ok=True)
 for n,t in default_mathlib_micro_files().items():
  p=root/n; p.parent.mkdir(parents=True,exist_ok=True)
  if overwrite or not p.exists(): p.write_text(t,encoding="utf-8")
 p=root/"mathlib_micro_manifest.json"
 if overwrite or not p.exists(): p.write_text(json.dumps(default_mathlib_micro_manifest_dict(),indent=2)+"\n",encoding="utf-8")
 return p
def load_mathlib_micro_manifest(path):
 p=Path(path); d=json.loads(p.read_text()); root=(p.parent/str(d.get("project_root","."))).resolve()
 return MathlibMicroManifest(make_mathlib_micro_manifest_id(d),d["subset_id"],d["name"],d.get("version","0.1"),MathlibMicroSourceKind(d.get("source_kind","SYNTHETIC_MATHLIB_STYLE_MICRO")),MathlibMicroTrustPolicy(d.get("trust_policy","LOCAL_VERIFIER_REQUIRED")),d.get("proof_system","lean"),str(root),d.get("module_prefix","Mathlib.MathGraph"),list(d.get("files",())),d.get("pinned_revision"),d.get("lean_toolchain"),d.get("source_uri"),dict(d.get("metadata",{})))
def build_default_mathlib_micro_manifest(root=None,*,ensure_files=True):
 root=Path(root or Path(__file__).resolve().parents[1]/"examples/mathlib_micro_subset"); p=ensure_default_mathlib_micro_subset(root) if ensure_files else root/"mathlib_micro_manifest.json"; return load_mathlib_micro_manifest(p)
def detect_mathlib_micro_environment(manifest,*,require_lake=False,require_mathlib_marker=False):
 m=manifest if isinstance(manifest,MathlibMicroManifest) else load_mathlib_micro_manifest(manifest) if isinstance(manifest,(str,Path)) else MathlibMicroManifest.from_dict({"manifest_id":make_mathlib_micro_manifest_id(manifest),**dict(manifest)})
 root=Path(m.project_root or "."); lean=shutil.which("lean"); lake=shutil.which("lake"); miss=tuple(str(root/x["path"]) for x in m.files if not (root/x["path"]).exists()); warns=[]; crit=[]
 if not root.exists(): status=MathlibMicroEnvironmentStatus.MISSING_PROJECT_ROOT; warns.append("project root missing")
 elif miss: status=MathlibMicroEnvironmentStatus.MISSING_MODULE_FILES; crit.append("manifest module files missing")
 elif not lean: status=MathlibMicroEnvironmentStatus.MISSING_LEAN; warns.append("lean missing")
 elif require_lake and not lake: status=MathlibMicroEnvironmentStatus.MISSING_LAKE; warns.append("lake missing")
 elif require_mathlib_marker and m.source_kind==MathlibMicroSourceKind.LOCAL_MATHLIB_PROJECT and not any((root/x).exists() for x in ("Mathlib","lakefile.lean","lake-manifest.json","lean-toolchain")): status=MathlibMicroEnvironmentStatus.MATHLIB_NOT_DETECTED; warns.append("mathlib marker missing")
 else: status=MathlibMicroEnvironmentStatus.READY
 return MathlibEnvironmentReport(make_mathlib_environment_id(m.subset_id,str(root)),m.subset_id,str(root),lean,lake,_version([lean,"--version"]) if lean else None,_version([lake,"--version"]) if lake else None,None,tuple(str(root/x["path"]) for x in m.files),miss,status,tuple(warns),tuple(crit))
def mathlib_module_name_from_path(path,*,project_root=None):
 p=Path(path)
 if project_root is not None:
  try:p=p.resolve().relative_to(Path(project_root).resolve())
  except ValueError: pass
 return ".".join(p.with_suffix("").parts)
def mathlib_path_from_module_name(module_name,*,project_root): return Path(project_root).joinpath(*module_name.split(".")).with_suffix(".lean")
def extract_imports_from_lean_text(text): return tuple(re.findall(r"(?m)^\s*import\s+([A-Za-z0-9_.]+)",text))
def extract_namespace_stack_from_lean_text(text): return tuple(re.findall(r"(?m)^\s*namespace\s+([A-Za-z_][A-Za-z0-9_]*)",text))
def qualify_declaration_name(short_name,*,module_name,namespace_stack=(),module_prefix=""):
 return short_name if "." in short_name else f"{module_prefix}.{short_name}" if module_prefix else ".".join((*namespace_stack,short_name)) if namespace_stack else short_name
def extract_declared_entries_from_mathlib_micro_text(text,*,subset_id,file_id,module_name,module_prefix="Mathlib.MathGraph"):
 out=[]
 for name in extract_theorem_declarations(text):
  m=re.search(rf"(?ms)^(?:theorem|lemma)\s+{re.escape(name)}\b.*?(?=^\s*(?:theorem|lemma|def)\s+|\Z)",text)
  full=qualify_declaration_name(name,module_name=module_name,namespace_stack=extract_namespace_stack_from_lean_text(text),module_prefix=module_prefix)
  out.append(MathlibMicroEntry(make_mathlib_micro_entry_id(subset_id,file_id,full),subset_id,file_id,module_name,name,full,theorem_statement_excerpt=(m.group(0).strip()[:240] if m else name)))
 return out
def extract_referenced_names_from_lean_text(text,candidate_names): return tuple(n for n in candidate_names if re.search(rf"\b{re.escape(n.split('.')[-1])}\b",text))
def build_mathlib_micro_file(m,r):
 root=Path(m.project_root or "."); p=root/r["path"]; t=p.read_text(); short=extract_theorem_declarations(t); full=tuple(qualify_declaration_name(x,module_name=r.get("module_name",""),namespace_stack=extract_namespace_stack_from_lean_text(t),module_prefix=m.module_prefix) for x in short)
 return MathlibMicroFile(make_mathlib_micro_file_id(m.subset_id,r["path"]),m.subset_id,str(p.resolve()),r.get("module_name") or mathlib_module_name_from_path(p,project_root=root),_hash(t),tuple(r.get("expected_declaration_names",())),tuple(r.get("expected_short_names",())),short,full,extract_imports_from_lean_text(t),tuple(r.get("expected_imports",())),extract_unsafe_markers(t),tuple(tuple(x) for x in r.get("expected_reference_dependencies",())),metadata={"expected_status":r.get("expected_status",""),"category":r.get("category","")})
def build_mathlib_micro_dependency_edges(subset_id,entries,files):
 out=[]; by_module={f.module_name:f for f in files}; by_name={e.name:e for e in entries}; by_full={e.full_name:e for e in entries}
 for f in files:
  for imp in f.imports:
   if imp in by_module:
    target=by_module[imp]; out.append(MathlibMicroDependencyEdge(make_mathlib_micro_dependency_edge_id(f.file_id,target.file_id,"import"),subset_id,"module",f.file_id,"module",target.file_id,MathlibMicroDependencyKind.IMPORTS_MODULE,f.module_name,target.module_name,"import"))
  own={e.name for e in entries if e.file_id==f.file_id}
  for e in [x for x in entries if x.file_id==f.file_id]:
   refs=tuple(n for n in extract_referenced_names_from_lean_text(e.theorem_statement_excerpt,by_name) if n not in own); e.referenced_names=refs
   for n in refs:
    target=by_name[n]; out.append(MathlibMicroDependencyEdge(make_mathlib_micro_dependency_edge_id(e.entry_id,target.entry_id,"text"),subset_id,"entry",e.entry_id,"entry",target.entry_id,MathlibMicroDependencyKind.REFERENCES_DECLARATION,e.name,target.name,"text_reference"))
  for a,b in f.expected_reference_dependencies:
   if a in by_name and b in by_name: out.append(MathlibMicroDependencyEdge(make_mathlib_micro_dependency_edge_id(a,b,"expected"),subset_id,"entry",by_name[a].entry_id,"entry",by_name[b].entry_id,MathlibMicroDependencyKind.EXPECTED_REFERENCE,a,b,"manifest_expected_reference"))
 return out
def _contract(f,root,build_root,allow_execution,timeout_sec):
 out=build_root.joinpath(*f.module_name.split(".")).with_suffix(".olean"); out.parent.mkdir(parents=True,exist_ok=True)
 return VerifierCommandContract(make_verifier_command_contract_id(f.path,f.expected_short_names,allow_execution),VerifierSystemKind.LEAN,VerifierExecutionMode.CHECK_FILE,("lean","-o",str(out),f.path),str(root),f.path,f.text_hash,timeout_sec,allow_execution,False,False,str(root),f.expected_short_names,{"lean_path":str(build_root)})
def ingest_mathlib_micro_subset(manifest,*,project_root=None,workspace_root=None,allow_execution=False,allow_missing_verifier=True,timeout_sec=20.0,accept_verified_entries_in_memory=False,require_lake=False,require_mathlib_marker=False):
 m=manifest if isinstance(manifest,MathlibMicroManifest) else load_mathlib_micro_manifest(manifest) if isinstance(manifest,(str,Path)) else MathlibMicroManifest.from_dict({"manifest_id":make_mathlib_micro_manifest_id(manifest),**dict(manifest)})
 if project_root: m.project_root=str(Path(project_root).resolve())
 env=detect_mathlib_micro_environment(m,require_lake=require_lake,require_mathlib_marker=require_mathlib_marker); root=Path(m.project_root or ".").resolve()
 files=[build_mathlib_micro_file(m,x) for x in m.files if (root/x["path"]).exists()]; entries=[e for f in files for e in extract_declared_entries_from_mathlib_micro_text(Path(f.path).read_text(),subset_id=m.subset_id,file_id=f.file_id,module_name=f.module_name,module_prefix=m.module_prefix)]; edges=build_mathlib_micro_dependency_edges(m.subset_id,entries,files); warnings=list(env.warnings); crit=list(env.criticals)
 vr=VerifierExecutionReport(make_verifier_execution_report_id([],allow_execution))
 if allow_execution and env.ready():
  build_root=Path(workspace_root or Path(tempfile.gettempdir())/"mathgraph_mathlib_micro_tmp").resolve()/"olean"; vr=build_verifier_execution_report(contracts=[_contract(f,root,build_root,allow_execution,timeout_sec) for f in files],allow_execution=True,timeout_sec=timeout_sec)
 for i,f in enumerate(files):
  res=vr.results[i] if i<len(vr.results) else None; ev=next((e for e in vr.boundary_evidence if res and e.result_id==res.result_id),None); expected_full=set(f.expected_declaration_names); expected_short=set(f.expected_short_names)
  if f.unsafe_markers: f.status=MathlibMicroFileStatus.REJECTED_UNSAFE; f.failure_kind=MathlibMicroFailureKind.UNSAFE_MARKER
  elif expected_full and not expected_full.issubset(set(f.declared_full_names)) and expected_short and not expected_short.issubset(set(f.declared_names)): f.status=MathlibMicroFileStatus.REJECTED_EXPECTED_MISSING; f.failure_kind=MathlibMicroFailureKind.EXPECTED_DECLARATION_MISSING
  elif allow_execution and not env.ready():
   f.status=MathlibMicroFileStatus.SKIPPED_MISSING_VERIFIER if env.status==MathlibMicroEnvironmentStatus.MISSING_LEAN else MathlibMicroFileStatus.SKIPPED_ENVIRONMENT_NOT_READY; f.failure_kind=MathlibMicroFailureKind.MISSING_VERIFIER if env.status==MathlibMicroEnvironmentStatus.MISSING_LEAN else MathlibMicroFailureKind.ENVIRONMENT_NOT_READY
  elif res and res.failure_kind==VerifierFailureKind.IMPORT_ERROR: f.status=MathlibMicroFileStatus.REJECTED_VERIFIER_FAILED; f.failure_kind=MathlibMicroFailureKind.IMPORT_ERROR
  elif ev: f.status=MathlibMicroFileStatus.VERIFIED_BY_LOCAL_VERIFIER
  elif allow_execution and res and res.status!=VerifierExecutionStatus.SUCCESS: f.status=MathlibMicroFileStatus.REJECTED_VERIFIER_FAILED; f.failure_kind=MathlibMicroFailureKind.VERIFIER_FAILED
  for e in [x for x in entries if x.file_id==f.file_id]:
   if f.status==MathlibMicroFileStatus.REJECTED_UNSAFE: e.status=MathlibMicroEntryStatus.REJECTED_UNSAFE; e.failure_kind=MathlibMicroFailureKind.UNSAFE_MARKER
   elif f.status==MathlibMicroFileStatus.REJECTED_EXPECTED_MISSING: e.status=MathlibMicroEntryStatus.REJECTED_EXPECTED_MISSING; e.failure_kind=MathlibMicroFailureKind.EXPECTED_DECLARATION_MISSING
   elif f.status==MathlibMicroFileStatus.SKIPPED_MISSING_VERIFIER: e.status=MathlibMicroEntryStatus.SKIPPED_MISSING_VERIFIER; e.failure_kind=MathlibMicroFailureKind.MISSING_VERIFIER
   elif f.status==MathlibMicroFileStatus.SKIPPED_ENVIRONMENT_NOT_READY: e.status=MathlibMicroEntryStatus.SKIPPED_ENVIRONMENT_NOT_READY; e.failure_kind=MathlibMicroFailureKind.ENVIRONMENT_NOT_READY
   elif f.failure_kind in {MathlibMicroFailureKind.IMPORT_ERROR,MathlibMicroFailureKind.TYPE_ERROR,MathlibMicroFailureKind.VERIFIER_FAILED}: e.status=MathlibMicroEntryStatus.REJECTED_VERIFIER_FAILED; e.failure_kind=f.failure_kind
   elif ev and (e.full_name in expected_full or e.name in expected_short): e.status=MathlibMicroEntryStatus.VERIFIED_BY_LOCAL_VERIFIER; e.boundary_evidence_id=ev.evidence_id; e.certificate_id=ev.certificate_id; e.terminal_form=ev.terminal_form; e.verifier_boundary_crossed=True
 rep=MathlibMicroIngestionReport(make_mathlib_micro_ingestion_report_id(m.subset_id,[f.file_id for f in files],allow_execution),m.subset_id,m,env,files,entries,edges,vr,warnings=tuple(dict.fromkeys(warnings)),criticals=tuple(crit))
 rep.status=MathlibMicroIngestionStatus.DRY_RUN if not allow_execution else MathlibMicroIngestionStatus.SKIPPED_ENVIRONMENT if not env.ready() else MathlibMicroIngestionStatus.COMPLETED_WITH_WARNINGS if warnings else MathlibMicroIngestionStatus.COMPLETED
 rep.lawbook_replay_summary=review_and_optionally_accept_mathlib_micro_entries(rep,accept_in_memory=accept_verified_entries_in_memory); rep.summarize(); return rep
def mathlib_micro_report_to_lawbook_candidates(r): return [LawbookEntry(make_lawbook_entry_id("mathlib-micro",e.entry_id),LawbookEntryKind.VERIFIED_PROOF_ENTRY,LawbookEntryStatus.CANDIDATE,claim_id=e.full_name,raw=e.theorem_statement_excerpt,terminal_form=TerminalForm.VERIFIED_PROOF,certificate_id=e.certificate_id,verifier_boundary_crossed=True,acceptance_boundary=LawbookAcceptanceBoundary.VERIFIED_PROOF,metadata={"mathlib_micro_report_id":r.report_id,"mathlib_micro_entry_id":e.entry_id}) for e in r.entries if e.has_boundary_evidence()]
def review_and_optionally_accept_mathlib_micro_entries(r,*,accept_in_memory=False):
 cs=mathlib_micro_report_to_lawbook_candidates(r); reviews=[review_lawbook_candidate(x) for x in cs]; accepted=[accept_lawbook_entry(e,v,accepted_by="mathlib-micro-replay") for e,v in zip(cs,reviews) if accept_in_memory and v.decision.value=="ACCEPT"]; store=LawbookStore(make_lawbook_store_id("mathlib-micro-replay",r.report_id),entries=accepted,reviews=reviews); answers=[query_lawbook_store_by_certificate(store,x.certificate_id) for x in cs if x.certificate_id]; return {"candidate_total":len(cs),"review_total":len(reviews),"accepted_total":len(accepted),"query_total":len(answers),"known_skip_total":sum(a.known_skip_decision.value.startswith("SKIP_") for a in answers),"warnings":[],"criticals":[]}
def mathlib_micro_report_to_markdown(r):
 s=r.summarize(); env=r.environment_report; lines=["# Mathlib Micro-Subset Ingestion","",f"- Subset: `{r.subset_id}`",f"- Name: {r.manifest.name if r.manifest else ''}",f"- Version: {r.manifest.version if r.manifest else ''}",f"- Source kind: {r.manifest.source_kind.value if r.manifest else ''}",f"- Trust policy: {r.manifest.trust_policy.value if r.manifest else ''}",f"- Environment: {env.status.value if env else 'UNKNOWN'}",f"- Lean: {env.lean_path if env else ''}",f"- Lake: {env.lake_path if env else ''}",f"- Status: {r.status.value}",f"- Files: {s['file_total']}",f"- Entries: {s['entry_total']}",f"- Verified entries: {s['verified_entry_total']}",f"- Boundary evidence: {s['boundary_evidence_total']}",f"- Dependency edges: {s['dependency_edge_total']}",f"- Import edges: {s['import_edge_total']}",f"- Reference edges: {s['reference_edge_total']}","", "| file/module | declared | expected | imports | status | boundary | failure |","| --- | --- | --- | --- | --- | --- | --- |"]
 for f in r.files:
  xs=[e for e in r.entries if e.file_id==f.file_id]; lines.append(f"| {Path(f.path).name} / {f.module_name} | {', '.join(f.declared_full_names)} | {', '.join(f.expected_declaration_names)} | {', '.join(f.imports)} | {', '.join(dict.fromkeys(e.status.value for e in xs))} | {'yes' if any(e.has_boundary_evidence() for e in xs) else 'no'} | {', '.join(dict.fromkeys(e.failure_kind.value for e in xs))} |")
 lines+=["",f"Dependency summary: imports={r.import_edge_count()}, references={r.reference_edge_count()}",f"Lawbook replay: `{r.lawbook_replay_summary}`","","Boundary policy: environment checks, declarations, imports, and reference graphs are advisory; only valid verifier/importer/finite-validator/chain-audit evidence promotes truth."]; return "\n".join(lines)+"\n"
def mathlib_micro_report_to_dependency_graph(r): return {"nodes":[{"id":f.file_id,"kind":"module","name":f.module_name} for f in r.files]+[{"id":e.entry_id,"kind":"entry","name":e.full_name,"status":e.status.value} for e in r.entries],"edges":[x.to_dict() for x in r.dependency_edges],"metadata":{"subset_id":r.subset_id,"advisory":True}}
def write_dependency_graph_json(r,p): _w(p,_j(mathlib_micro_report_to_dependency_graph(r)))
def write_dependency_graph_jsonl(r,p):
 g=mathlib_micro_report_to_dependency_graph(r); _w(p,"".join(_j({"kind":"node",**x})+"\n" for x in g["nodes"])+"".join(_j({"kind":"edge",**x})+"\n" for x in g["edges"]))
def mathlib_micro_report_to_api_response(r):
 from mathgraph.api_service import _resp
 req=ApiRequest(make_api_request_id("mathlib-micro",r.report_id),ApiRoute.MATHLIB_MICRO_SUBSET); truth=ApiTruthStatus.BOUNDARY_EVIDENCE_PRESENT if r.verified_entry_count() else ApiTruthStatus.BOUNDARY_REQUIRED; return _resp(req,route_result_from_artifacts(req.route,[r],truth_status=truth,safety=ApiSafetyLevel.SAFE_REVIEW_REQUIRED))
def mathlib_micro_report_to_lean_project_report(r):
 files=[LeanProjectFile(f.file_id,r.subset_id,f.path,f.module_name,f.text_hash,f.expected_short_names,f.declared_names,f.imports,f.expected_imports,f.unsafe_markers,f.expected_reference_dependencies,LeanProjectFileStatus(f.status.value.replace("SKIPPED_ENVIRONMENT_NOT_READY","BLOCKED")),LeanProjectFailureKind("MISSING_VERIFIER" if f.failure_kind==MathlibMicroFailureKind.ENVIRONMENT_NOT_READY else f.failure_kind.value.replace("EXPECTED_DECLARATION_MISSING","EXPECTED_THEOREM_MISSING")),dict(f.metadata),f.advisory) for f in r.files]
 ents=[LeanProjectEntry(e.entry_id,r.subset_id,e.file_id,e.module_name,e.name,e.entry_kind,LeanProjectEntryStatus(e.status.value.replace("SKIPPED_ENVIRONMENT_NOT_READY","BLOCKED")),e.theorem_statement_excerpt,e.referenced_names,e.boundary_evidence_id,e.certificate_id,e.terminal_form,e.verifier_boundary_crossed,LeanProjectFailureKind("MISSING_VERIFIER" if e.failure_kind==MathlibMicroFailureKind.ENVIRONMENT_NOT_READY else e.failure_kind.value.replace("EXPECTED_DECLARATION_MISSING","EXPECTED_THEOREM_MISSING")),dict(e.metadata),e.advisory) for e in r.entries]
 edges=[LeanProjectDependencyEdge(x.edge_id,r.subset_id,x.source_kind,x.source_id,x.target_kind,x.target_id,LeanProjectDependencyKind(x.dependency_kind.value),x.source_name,x.target_name,x.evidence,dict(x.metadata),x.advisory) for x in r.dependency_edges]
 rep=LeanProjectIngestionReport(content_id("lean-project-from-mathlib",r.report_id),r.subset_id,None,files,ents,edges,r.verifier_execution_report,dict(r.lawbook_replay_summary),r.created_at,LeanProjectIngestionStatus.DRY_RUN if r.status==MathlibMicroIngestionStatus.DRY_RUN else LeanProjectIngestionStatus.COMPLETED,warnings=r.warnings,criticals=r.criticals,metadata={"source_mathlib_micro_report_id":r.report_id}); rep.summarize(); return rep
def mathlib_micro_report_to_verified_corpus_report(r): return mathlib_micro_report_to_lean_project_report(r) and __import__("mathgraph.lean_project_subset",fromlist=["lean_project_report_to_verified_corpus_report"]).lean_project_report_to_verified_corpus_report(mathlib_micro_report_to_lean_project_report(r))
def mathlib_micro_report_to_process_episodes(r): return [ProcessEpisodeRecord(make_process_episode_id("mathlib-micro",e.entry_id),ProcessEpisodeStatus.TERMINAL_VERIFIED_PROOF if e.has_boundary_evidence() else ProcessEpisodeStatus.ADVISORY_ONLY,contexts=[ProcessContextItem(content_id("mathlib-micro-context",e.entry_id),ProcessContextKind.RAW_EVENT,ProcessContextRole.ADVISORY_ONLY,e.full_name)],terminal_form=TerminalForm.VERIFIED_PROOF if e.has_boundary_evidence() else None,certificate_id=e.certificate_id,verifier_boundary_crossed=e.verifier_boundary_crossed) for e in r.entries]
def mathlib_micro_report_to_proof_digestion_inputs(r): return [{"entry_id":e.entry_id,"proof_text":e.theorem_statement_excerpt,"boundary_backed":e.has_boundary_evidence(),"advisory":not e.has_boundary_evidence()} for e in r.entries]
def mathlib_micro_report_to_discovery_value_scores(r):
 out=[]
 for e in r.entries:
  sig=DiscoveryValueSignal(content_id("mathlib-micro-signal",e.entry_id),DiscoveryValueSignalKind.REUSE_VALUE,1.0 if e.has_boundary_evidence() else .1,source_object_kind=DiscoveryValueObjectKind.RAW_TASK); s=DiscoveryValueScore(content_id("mathlib-micro-score",e.entry_id),e.entry_id,DiscoveryValueObjectKind.RAW_TASK,signals=[sig]); s.recompute(); out.append(s)
 return out
def mathlib_micro_report_to_structural_identity_objects(r): return [{"object_id":e.entry_id,"name":e.full_name,"kind":e.entry_kind,"advisory":not e.has_boundary_evidence()} for e in r.entries]
def mathlib_micro_report_to_route_telemetry_events(r): return [{"event_id":content_id("mathlib-micro-telemetry",e.entry_id),"route_kind":"mathlib_micro_subset","outcome":e.status.value,"certificate_id":e.certificate_id,"verifier_boundary_crossed":e.verifier_boundary_crossed} for e in r.entries]
def mathlib_micro_report_to_alchemical_trace(r):
 t=AlchemicalTrace(make_alchemical_trace_id("mathlib-micro",r.report_id))
 for p in (AlchemicalPhase.RAW_MATTER,AlchemicalPhase.CALCINATION,AlchemicalPhase.DESCENSION): t.add_step(phase=p,status=AlchemicalStatus.ADVISORY_ONLY)
 if r.verified_entry_count(): t.add_step(phase=AlchemicalPhase.FIXATION,status=AlchemicalStatus.PROMOTED_BY_VERIFIER)
 for p in (AlchemicalPhase.DISTILLATION,AlchemicalPhase.COAGULATION): t.add_step(phase=p,status=AlchemicalStatus.ADVISORY_ONLY)
 return t
def mathlib_micro_report_to_agent_experiences(r): return [AgentExperience(content_id("mathlib-micro-exp",e.entry_id),"mathlib-micro",None,None,"project",None,AgentExperienceOutcome.VERIFIED_PROOF if e.has_boundary_evidence() else AgentExperienceOutcome.INVALID_CANDIDATE if e.failure_kind!=MathlibMicroFailureKind.NONE else AgentExperienceOutcome.ADVISORY_ONLY,terminal_form=TerminalForm.VERIFIED_PROOF if e.has_boundary_evidence() else None,certificate_id=e.certificate_id,verifier_boundary_crossed=e.verifier_boundary_crossed) for e in r.entries]
def audit_mathlib_micro_manifest(x): return [_af("CRITICAL","MATHLIB_MICRO_MANIFEST_NON_ADVISORY","manifest non-advisory",x.manifest_id)] if not x.advisory else []
def audit_mathlib_environment_report(x): return [_af("CRITICAL","MATHLIB_ENVIRONMENT_NON_ADVISORY","environment readiness treated as proof",x.environment_id)] if not x.advisory else []
def audit_mathlib_micro_file(x): return [_af("CRITICAL","MATHLIB_MICRO_FILE_NON_ADVISORY","file extraction claims truth",x.file_id)] if not x.advisory else []
def audit_mathlib_micro_entry(x):
 out=[]
 if x.status==MathlibMicroEntryStatus.VERIFIED_BY_LOCAL_VERIFIER and not x.has_boundary_evidence(): out.append(_af("CRITICAL","MATHLIB_MICRO_VERIFIED_WITHOUT_BOUNDARY","verified entry lacks boundary",x.entry_id))
 if x.has_boundary_evidence() and x.failure_kind!=MathlibMicroFailureKind.NONE: out.append(_af("CRITICAL","MATHLIB_MICRO_BAD_ENTRY_VERIFIED","failed entry verified",x.entry_id))
 return out
def audit_mathlib_micro_dependency_edge(x): return [_af("CRITICAL","MATHLIB_MICRO_EDGE_NON_ADVISORY","dependency edge treated as proof",x.edge_id)] if not x.advisory else []
def audit_mathlib_micro_ingestion_report(x):
 out=sum((audit_mathlib_micro_entry(e) for e in x.entries),[])
 if x.ok() and x.critical_count(): out.append(_af("CRITICAL","MATHLIB_MICRO_OK_WITH_CRITICAL","report hides criticals",x.report_id))
 if x.lawbook_replay_summary.get("known_skip_total",0) and not x.lawbook_replay_summary.get("accepted_total",0): out.append(_af("CRITICAL","MATHLIB_MICRO_SKIP_WITHOUT_ACCEPTANCE","known skip without accepted replay",x.report_id))
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
