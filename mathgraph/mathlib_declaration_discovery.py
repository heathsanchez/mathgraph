"""Advisory local Mathlib declaration discovery and allowlist-manifest building."""
from __future__ import annotations
import json,re,shutil
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
from mathgraph.mathlib_local_allowlist import MathlibLocalAllowlistManifest,MathlibLocalSourceKind,MathlibLocalTrustPolicy,ingest_mathlib_local_allowlist,make_mathlib_local_manifest_id
from mathgraph.mathlib_micro_subset import ensure_default_mathlib_micro_subset
from mathgraph.process_memory import ProcessContextItem,ProcessContextKind,ProcessContextRole,ProcessEpisodeRecord,ProcessEpisodeStatus,make_process_episode_id

def _enum(n,v): return Enum(n,{x:x for x in v.split()},type=str)
MathlibDiscoverySourceKind=_enum("MathlibDiscoverySourceKind","LOCAL_MATHLIB_PROJECT LOCAL_LEAN_PROJECT SYNTHETIC_LOCAL_PROJECT UNKNOWN")
MathlibDeclarationKind=_enum("MathlibDeclarationKind","THEOREM LEMMA DEF EXAMPLE INSTANCE UNKNOWN")
MathlibDiscoveryEnvironmentStatus=_enum("MathlibDiscoveryEnvironmentStatus","READY READY_SYNTHETIC MISSING_PROJECT_ROOT MISSING_MODULE_FILES MISSING_LEAN MATHLIB_MARKER_NOT_FOUND NOT_A_LEAN_PROJECT SKIPPED UNKNOWN")
MathlibDiscoveryStatus=_enum("MathlibDiscoveryStatus","NOT_RUN DISCOVERED DISCOVERED_WITH_WARNINGS SKIPPED_ENVIRONMENT EMPTY FAILED ERROR UNKNOWN")
MathlibSelectionStatus=_enum("MathlibSelectionStatus","SELECTED FILTERED_OUT DUPLICATE EXCLUDED_UNSAFE EXCLUDED_BY_KIND EXCLUDED_BY_NAME EXCLUDED_BY_LIMIT UNKNOWN")
MathlibManifestBuildStatus=_enum("MathlibManifestBuildStatus","NOT_RUN BUILT BUILT_EMPTY FAILED UNKNOWN")
MathlibDiscoveryFailureKind=_enum("MathlibDiscoveryFailureKind","NONE MISSING_PROJECT_ROOT MISSING_MODULE_FILE ENVIRONMENT_NOT_READY PARSE_EMPTY UNSAFE_MARKER NO_DECLARATIONS EMPTY_SELECTION UNKNOWN")
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
   if f.name in enums and v is not None and not isinstance(v,Enum): v=globals()[str(f.type)](str(v))
   if getattr(f.type,"__origin__",None) is tuple and v is not None: v=tuple(v)
   vals.append(v)
  return c(*vals)
 cls.to_dict=td; cls.from_dict=fd; cls.to_json=lambda self:_j(self.to_dict()); cls.from_json=classmethod(lambda c,t:c.from_dict(json.loads(t))); return cls
@_serial
@dataclass
class MathlibDiscoveryRequest:
 request_id:str; name:str; version:str="0.1"; source_kind:MathlibDiscoverySourceKind=MathlibDiscoverySourceKind.LOCAL_MATHLIB_PROJECT; project_root:str|None=None; module_prefix:str="Mathlib"; module_files:list[dict[str,Any]]=field(default_factory=list); selection_policy:dict[str,Any]=field(default_factory=dict); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def write_json(self,p): _w(p,self.to_json())
 @classmethod
 def read_json(c,p): return c.from_json(Path(p).read_text())
@_serial
@dataclass
class MathlibDiscoveredModule:
 module_id:str; request_id:str; path:str; module_name:str; text_hash:str|None=None; imports:tuple[str,...]=(); unsafe_markers:tuple[str,...]=(); declaration_count:int=0; selected_count:int=0; status:MathlibDiscoveryStatus=MathlibDiscoveryStatus.UNKNOWN; failure_kind:MathlibDiscoveryFailureKind=MathlibDiscoveryFailureKind.NONE; warnings:tuple[str,...]=(); criticals:tuple[str,...]=(); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
@_serial
@dataclass
class MathlibDiscoveredDeclaration:
 declaration_id:str; request_id:str; module_id:str; module_name:str; name:str; full_name:str; declaration_kind:MathlibDeclarationKind=MathlibDeclarationKind.UNKNOWN; statement_excerpt:str=""; line_number:int|None=None; referenced_names:tuple[str,...]=(); selection_status:MathlibSelectionStatus=MathlibSelectionStatus.UNKNOWN; failure_kind:MathlibDiscoveryFailureKind=MathlibDiscoveryFailureKind.NONE; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
@_serial
@dataclass
class MathlibDeclarationReferenceHint:
 hint_id:str; request_id:str; source_declaration_id:str; target_name:str; target_declaration_id:str|None=None; evidence:str=""; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
@dataclass
class MathlibDeclarationDiscoveryReport:
 report_id:str; request_id:str; request:MathlibDiscoveryRequest|None=None; environment_status:MathlibDiscoveryEnvironmentStatus=MathlibDiscoveryEnvironmentStatus.UNKNOWN; project_root:str|None=None; lean_path:str|None=None; modules:list[MathlibDiscoveredModule]=field(default_factory=list); declarations:list[MathlibDiscoveredDeclaration]=field(default_factory=list); reference_hints:list[MathlibDeclarationReferenceHint]=field(default_factory=list); generated_manifest:Any|None=None; allowlist_ingestion_report:Any|None=None; created_at:str=field(default_factory=lambda:_now()); status:MathlibDiscoveryStatus=MathlibDiscoveryStatus.UNKNOWN; manifest_build_status:MathlibManifestBuildStatus=MathlibManifestBuildStatus.NOT_RUN; summary:dict[str,Any]=field(default_factory=dict); warnings:tuple[str,...]=(); criticals:tuple[str,...]=(); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def module_count(self): return len(self.modules)
 def declaration_count(self): return len(self.declarations)
 def selected_declaration_count(self): return sum(x.selection_status==MathlibSelectionStatus.SELECTED for x in self.declarations)
 def reference_hint_count(self): return len(self.reference_hints)
 def warning_count(self): return len(self.warnings)
 def critical_count(self): return len(self.criticals)
 def summarize(self): self.summary={"module_total":len(self.modules),"declaration_total":len(self.declarations),"selected_total":self.selected_declaration_count(),"reference_hint_total":len(self.reference_hints),"generated_manifest_file_total":len(self.generated_manifest.files) if self.generated_manifest else 0,"downstream_verified_total":self.allowlist_ingestion_report.verified_entry_count() if self.allowlist_ingestion_report else 0,"warning_total":len(self.warnings),"critical_total":len(self.criticals)}; return self.summary
 def ok(self): return self.critical_count()==0 and self.status not in {MathlibDiscoveryStatus.FAILED,MathlibDiscoveryStatus.ERROR}
 def to_dict(self): return {**self.__dict__,"request":self.request.to_dict() if self.request else None,"environment_status":self.environment_status.value,"modules":[x.to_dict() for x in self.modules],"declarations":[x.to_dict() for x in self.declarations],"reference_hints":[x.to_dict() for x in self.reference_hints],"generated_manifest":self.generated_manifest.to_dict() if hasattr(self.generated_manifest,"to_dict") else self.generated_manifest,"allowlist_ingestion_report":self.allowlist_ingestion_report.to_dict() if hasattr(self.allowlist_ingestion_report,"to_dict") else self.allowlist_ingestion_report,"status":self.status.value,"manifest_build_status":self.manifest_build_status.value,"warnings":list(self.warnings),"criticals":list(self.criticals)}
 @classmethod
 def from_dict(c,d):
  from mathgraph.mathlib_local_allowlist import MathlibLocalIngestionReport
  return c(str(d["report_id"]),str(d["request_id"]),MathlibDiscoveryRequest.from_dict(d["request"]) if d.get("request") else None,MathlibDiscoveryEnvironmentStatus(str(d.get("environment_status","UNKNOWN"))),d.get("project_root"),d.get("lean_path"),[MathlibDiscoveredModule.from_dict(x) for x in d.get("modules",())],[MathlibDiscoveredDeclaration.from_dict(x) for x in d.get("declarations",())],[MathlibDeclarationReferenceHint.from_dict(x) for x in d.get("reference_hints",())],MathlibLocalAllowlistManifest.from_dict(d["generated_manifest"]) if d.get("generated_manifest") else None,MathlibLocalIngestionReport.from_dict(d["allowlist_ingestion_report"]) if d.get("allowlist_ingestion_report") else None,str(d.get("created_at",_now())),MathlibDiscoveryStatus(str(d.get("status","UNKNOWN"))),MathlibManifestBuildStatus(str(d.get("manifest_build_status","NOT_RUN"))),dict(d.get("summary",{})),tuple(d.get("warnings",())),tuple(d.get("criticals",())),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
 def write_json(self,p): _w(p,self.to_json())
 @classmethod
 def read_json(c,p): return c.from_json(Path(p).read_text())
 def write_jsonl(self,p): _w(p,self.to_json()+"\n")
 @classmethod
 def read_jsonl(c,p): return [c.from_json(x) for x in Path(p).read_text().splitlines() if x.strip()]
for _c,_e in [(MathlibDiscoveryRequest,("source_kind",)),(MathlibDiscoveredModule,("status","failure_kind")),(MathlibDiscoveredDeclaration,("declaration_kind","selection_status","failure_kind"))]: _serial(_c,_e)
def make_mathlib_discovery_request_id(*x): return content_id("mathlib-discovery-request",x)
def make_mathlib_discovered_module_id(*x): return content_id("mathlib-discovery-module",x)
def make_mathlib_discovered_declaration_id(*x): return content_id("mathlib-discovery-declaration",x)
def make_mathlib_reference_hint_id(*x): return content_id("mathlib-reference-hint",x)
def make_mathlib_declaration_discovery_report_id(*x): return content_id("mathlib-discovery-report",x)
def default_mathlib_discovery_request_dict(): return {"request_id":"example-real-local-mathlib-discovery","name":"Example Real Local Mathlib Declaration Discovery","version":"0.1","source_kind":"LOCAL_MATHLIB_PROJECT","project_root":None,"module_prefix":"Mathlib","module_files":[{"path":"Mathlib/Data/Nat/Basic.lean","module_name":"Mathlib.Data.Nat.Basic","max_declarations":10,"include_kinds":["theorem","lemma"],"name_contains":[],"exclude_name_contains":[]}],"selection_policy":{"max_total_declarations":10,"prefer_kinds":["theorem","lemma"],"name_contains":[],"exclude_name_contains":["deprecated","aux"]},"metadata":{"note":"Template only. Point project_root at an existing local Mathlib checkout."}}
def synthetic_mathlib_discovery_request_dict(synthetic_root):
 paths=["Basic","Logic","Algebra","UseBasic","UseAlgebra"]
 return {"request_id":"synthetic-mathlib-discovery","name":"Synthetic Mathlib discovery","version":"0.1","source_kind":"SYNTHETIC_LOCAL_PROJECT","project_root":str(Path(synthetic_root).resolve()),"module_prefix":"Mathlib.MathGraph","module_files":[{"path":f"Mathlib/MathGraph/{x}.lean","module_name":f"Mathlib.MathGraph.{x}","max_declarations":2,"include_kinds":["theorem","lemma"],"name_contains":[],"exclude_name_contains":[]} for x in paths],"selection_policy":{"max_total_declarations":10,"prefer_kinds":["theorem","lemma"],"name_contains":[],"exclude_name_contains":[]},"metadata":{"synthetic":True}}
def ensure_default_mathlib_discovery_examples(root,*,overwrite=False):
 root=Path(root); root.mkdir(parents=True,exist_ok=True); synthetic=Path(__file__).resolve().parents[1]/"examples"/"mathlib_micro_subset"; ensure_default_mathlib_micro_subset(synthetic); p1=root/"discovery_request.example.json"; p2=root/"synthetic_discovery_request.json"
 if overwrite or not p1.exists(): p1.write_text(json.dumps(default_mathlib_discovery_request_dict(),indent=2)+"\n")
 if overwrite or not p2.exists():
  d=synthetic_mathlib_discovery_request_dict(synthetic); d["project_root"]="../mathlib_micro_subset"; p2.write_text(json.dumps(d,indent=2)+"\n")
 return p1,p2
def load_mathlib_discovery_request(path):
 p=Path(path); d=json.loads(p.read_text()); root=(p.parent/str(d.get("project_root","."))).resolve() if d.get("project_root") is not None else None; d["project_root"]=str(root) if root else None; return MathlibDiscoveryRequest.from_dict(d)
def build_synthetic_mathlib_discovery_request(synthetic_root=None,*,ensure_synthetic_subset=True):
 root=Path(synthetic_root or Path(__file__).resolve().parents[1]/"examples"/"mathlib_micro_subset")
 if ensure_synthetic_subset: ensure_default_mathlib_micro_subset(root)
 return MathlibDiscoveryRequest.from_dict(synthetic_mathlib_discovery_request_dict(root))
def detect_mathlib_discovery_environment(request,*,project_root=None,require_mathlib_marker=False):
 r=request if isinstance(request,MathlibDiscoveryRequest) else load_mathlib_discovery_request(request) if isinstance(request,(str,Path)) else MathlibDiscoveryRequest.from_dict(dict(request)); root=Path(project_root or r.project_root or "."); lean=shutil.which("lean"); miss=tuple(str(root/x["path"]) for x in r.module_files if not (root/x["path"]).exists()); warns=[]; crit=[]; markers=tuple(x for x in ("Mathlib","lakefile.lean","lakefile.toml","lake-manifest.json","lean-toolchain") if (root/x).exists())
 if not root.exists(): status=MathlibDiscoveryEnvironmentStatus.MISSING_PROJECT_ROOT; warns.append("project root missing")
 elif miss: status=MathlibDiscoveryEnvironmentStatus.MISSING_MODULE_FILES; warns.append("module files missing")
 elif not lean: status=MathlibDiscoveryEnvironmentStatus.MISSING_LEAN; warns.append("lean missing")
 elif require_mathlib_marker and not markers: status=MathlibDiscoveryEnvironmentStatus.MATHLIB_MARKER_NOT_FOUND; warns.append("mathlib marker missing")
 else: status=MathlibDiscoveryEnvironmentStatus.READY_SYNTHETIC if r.source_kind==MathlibDiscoverySourceKind.SYNTHETIC_LOCAL_PROJECT else MathlibDiscoveryEnvironmentStatus.READY
 return status,tuple(warns),tuple(crit),lean
def strip_lean_comments(text): return re.sub(r"/-.*?-/","",re.sub(r"--.*$","",text,flags=re.M),flags=re.S)
def extract_imports_from_lean_text(text): return tuple(re.findall(r"(?m)^\s*import\s+([A-Za-z0-9_.]+)",text))
def extract_namespace_stack_from_lean_text(text): return tuple(re.findall(r"(?m)^\s*namespace\s+([A-Za-z_][A-Za-z0-9_]*)",text))
def extract_declaration_blocks_from_lean_text(text):
 clean=strip_lean_comments(text); ms=list(re.finditer(r"(?m)^\s*(theorem|lemma|def|example|instance)(?:\s+([A-Za-z_][A-Za-z0-9_.']*))?",clean)); out=[]
 for i,m in enumerate(ms):
  kind=m.group(1); name=m.group(2) or f"example_{i+1}"; end=ms[i+1].start() if i+1<len(ms) else len(clean); out.append({"kind":kind,"name":name,"line_number":clean.count("\n",0,m.start())+1,"statement_excerpt":clean[m.start():end].strip()[:240]})
 return out
def qualify_declaration_name(short_name,*,module_name,namespace_stack=(),module_prefix=""):
 return short_name if "." in short_name else f"{module_prefix}.{short_name}" if module_prefix and not short_name.startswith(module_prefix+".") else ".".join((*namespace_stack,short_name)) if namespace_stack else short_name
def extract_referenced_names_from_lean_text(text,candidate_names,*,self_name=None): return tuple(n for n in candidate_names if n!=self_name and re.search(rf"\b{re.escape(n.split('.')[-1])}\b",text))
def discover_module_declarations(request,module_record):
 root=Path(request.project_root or "."); p=root/module_record["path"]; text=p.read_text(); clean=strip_lean_comments(text); blocks=extract_declaration_blocks_from_lean_text(clean); mid=make_mathlib_discovered_module_id(request.request_id,module_record["path"]); unsafe=tuple(x for x in ("sorry","admit","axiom") if re.search(rf"\b{x}\b",clean)); inc={x.upper() for x in module_record.get("include_kinds",())}; contains=tuple(module_record.get("name_contains",())); excl=tuple(module_record.get("exclude_name_contains",())); cap=int(module_record.get("max_declarations",999999)); decls=[]; selected=0
 for b in blocks:
  kind=MathlibDeclarationKind[b["kind"].upper()] if b["kind"].upper() in MathlibDeclarationKind.__members__ else MathlibDeclarationKind.UNKNOWN; status=MathlibSelectionStatus.SELECTED
  if unsafe: status=MathlibSelectionStatus.EXCLUDED_UNSAFE
  elif inc and kind.name not in inc: status=MathlibSelectionStatus.EXCLUDED_BY_KIND
  elif contains and not any(x in b["name"] for x in contains): status=MathlibSelectionStatus.EXCLUDED_BY_NAME
  elif excl and any(x in b["name"] for x in excl): status=MathlibSelectionStatus.EXCLUDED_BY_NAME
  elif selected>=cap: status=MathlibSelectionStatus.EXCLUDED_BY_LIMIT
  if status==MathlibSelectionStatus.SELECTED: selected+=1
  full=qualify_declaration_name(b["name"],module_name=module_record.get("module_name",""),namespace_stack=extract_namespace_stack_from_lean_text(clean),module_prefix=request.module_prefix)
  decls.append(MathlibDiscoveredDeclaration(make_mathlib_discovered_declaration_id(request.request_id,mid,full),request.request_id,mid,module_record.get("module_name",""),b["name"],full,kind,b["statement_excerpt"],b["line_number"],selection_status=status,failure_kind=MathlibDiscoveryFailureKind.UNSAFE_MARKER if status==MathlibSelectionStatus.EXCLUDED_UNSAFE else MathlibDiscoveryFailureKind.NONE))
 mod=MathlibDiscoveredModule(mid,request.request_id,str(p.resolve()),module_record.get("module_name",""),_hash(text),extract_imports_from_lean_text(clean),unsafe,len(decls),selected,MathlibDiscoveryStatus.DISCOVERED if decls else MathlibDiscoveryStatus.EMPTY,MathlibDiscoveryFailureKind.UNSAFE_MARKER if unsafe else MathlibDiscoveryFailureKind.NO_DECLARATIONS if not decls else MathlibDiscoveryFailureKind.NONE,metadata=dict(module_record))
 return mod,decls
def _apply_global_policy(request,declarations):
 pol=request.selection_policy; max_total=int(pol.get("max_total_declarations",999999)); contains=tuple(pol.get("name_contains",())); excl=tuple(pol.get("exclude_name_contains",())); chosen=0; seen=set()
 for d in declarations:
  if d.selection_status!=MathlibSelectionStatus.SELECTED: continue
  if d.full_name in seen: d.selection_status=MathlibSelectionStatus.DUPLICATE
  elif contains and not any(x in d.name for x in contains): d.selection_status=MathlibSelectionStatus.EXCLUDED_BY_NAME
  elif excl and any(x in d.name for x in excl): d.selection_status=MathlibSelectionStatus.EXCLUDED_BY_NAME
  elif chosen>=max_total: d.selection_status=MathlibSelectionStatus.EXCLUDED_BY_LIMIT
  else: chosen+=1; seen.add(d.full_name)
def run_mathlib_declaration_discovery(request,*,project_root=None,build_manifest=True,run_allowlist_ingestion=False,allow_execution=False,allow_missing_verifier=True,timeout_sec=20.0,accept_verified_entries_in_memory=False,require_mathlib_marker=False):
 r=request if isinstance(request,MathlibDiscoveryRequest) else load_mathlib_discovery_request(request) if isinstance(request,(str,Path)) else MathlibDiscoveryRequest.from_dict(dict(request));
 if project_root: r.project_root=str(Path(project_root).resolve())
 env,warns,crit,lean=detect_mathlib_discovery_environment(r,require_mathlib_marker=require_mathlib_marker); mods=[]; decls=[]
 root=Path(r.project_root or ".")
 for rec in r.module_files:
  if (root/rec["path"]).exists(): m,ds=discover_module_declarations(r,rec); mods.append(m); decls.extend(ds)
 _apply_global_policy(r,decls)
 for m in mods: m.selected_count=sum(d.module_id==m.module_id and d.selection_status==MathlibSelectionStatus.SELECTED for d in decls)
 by_name={d.name:d for d in decls}; hints=[]
 for d in decls:
  refs=extract_referenced_names_from_lean_text(d.statement_excerpt,by_name,self_name=d.name); d.referenced_names=refs
  for n in refs: hints.append(MathlibDeclarationReferenceHint(make_mathlib_reference_hint_id(d.declaration_id,n),r.request_id,d.declaration_id,n,by_name[n].declaration_id,"text_reference"))
 rep=MathlibDeclarationDiscoveryReport(make_mathlib_declaration_discovery_report_id(r.request_id,[m.module_id for m in mods]),r.request_id,r,env,str(root.resolve()),lean,mods,decls,hints,warnings=warns,criticals=crit)
 if build_manifest: rep.generated_manifest=build_allowlist_manifest_from_discovery(rep); rep.manifest_build_status=MathlibManifestBuildStatus.BUILT if rep.generated_manifest.files else MathlibManifestBuildStatus.BUILT_EMPTY
 if run_allowlist_ingestion and rep.generated_manifest: rep.allowlist_ingestion_report=ingest_mathlib_local_allowlist(rep.generated_manifest,allow_execution=allow_execution,allow_missing_verifier=allow_missing_verifier,timeout_sec=timeout_sec,accept_verified_entries_in_memory=accept_verified_entries_in_memory)
 rep.status=MathlibDiscoveryStatus.SKIPPED_ENVIRONMENT if env not in {MathlibDiscoveryEnvironmentStatus.READY,MathlibDiscoveryEnvironmentStatus.READY_SYNTHETIC} and not mods else MathlibDiscoveryStatus.EMPTY if not decls else MathlibDiscoveryStatus.DISCOVERED_WITH_WARNINGS if warns else MathlibDiscoveryStatus.DISCOVERED; rep.summarize(); return rep
def build_allowlist_manifest_from_discovery(report,*,allowlist_id=None,name=None):
 rows=[]
 for m in report.modules:
  ds=[d for d in report.declarations if d.module_id==m.module_id and d.selection_status==MathlibSelectionStatus.SELECTED]
  if not ds: continue
  rows.append({"path":str(Path(m.path).resolve().relative_to(Path(report.project_root).resolve())),"module_name":m.module_name,"expected_declaration_names":[d.full_name for d in ds],"expected_short_names":[d.name for d in ds],"expected_imports":list(m.imports),"expected_reference_dependencies":[[d.name,n] for d in ds for n in d.referenced_names],"expected_status":"safe","category":"safe" if not m.unsafe_markers else "unsafe"})
 return MathlibLocalAllowlistManifest(make_mathlib_local_manifest_id(report.report_id),allowlist_id or f"generated-{report.request_id}",name or f"Generated allowlist for {report.request_id}",source_kind=MathlibLocalSourceKind.SYNTHETIC_LOCAL_PROJECT if report.request and report.request.source_kind==MathlibDiscoverySourceKind.SYNTHETIC_LOCAL_PROJECT else MathlibLocalSourceKind.LOCAL_MATHLIB_PROJECT,trust_policy=MathlibLocalTrustPolicy.LOCAL_VERIFIER_REQUIRED,project_root=report.project_root,module_prefix=report.request.module_prefix if report.request else "Mathlib",files=rows,metadata={"source_discovery_report_id":report.report_id})
def write_generated_allowlist_manifest(report,path): report.generated_manifest.write_json(path)
def mathlib_discovery_report_to_markdown(r):
 s=r.summarize(); lines=["# Mathlib Declaration Discovery","",f"- Request: `{r.request_id}`",f"- Name: {r.request.name if r.request else ''}",f"- Environment: {r.environment_status.value}",f"- Project root: {r.project_root}",f"- Lean: {r.lean_path}",f"- Modules: {s['module_total']}",f"- Declarations: {s['declaration_total']}",f"- Selected: {s['selected_total']}",f"- Reference hints: {s['reference_hint_total']}",f"- Manifest build: {r.manifest_build_status.value}",f"- Downstream verified: {s['downstream_verified_total']}","","| module | imports | declarations | selected | status |","| --- | --- | --- | --- | --- |"]
 for m in r.modules: lines.append(f"| {m.module_name} | {', '.join(m.imports)} | {m.declaration_count} | {m.selected_count} | {m.status.value} |")
 lines += ["","| declaration | kind | full name | selection | line |","| --- | --- | --- | --- | --- |"]
 for d in r.declarations: lines.append(f"| {d.name} | {d.declaration_kind.value} | {d.full_name} | {d.selection_status.value} | {d.line_number or ''} |")
 lines += ["",f"Generated manifest files: {len(r.generated_manifest.files) if r.generated_manifest else 0}","","Boundary policy: discovery, reference hints, and generated manifests are advisory; only downstream verifier/importer/finite-validator/chain-audit evidence promotes truth."]
 return "\n".join(lines)+"\n"
def mathlib_discovery_report_to_reference_graph(r):
 return {"nodes":[{"id":m.module_id,"kind":"module","name":m.module_name} for m in r.modules]+[{"id":d.declaration_id,"kind":"declaration","name":d.full_name} for d in r.declarations],"edges":[{"kind":"import","source":m.module_id,"target_name":i,"advisory":True} for m in r.modules for i in m.imports]+[{"kind":"reference_hint",**h.to_dict()} for h in r.reference_hints],"metadata":{"request_id":r.request_id,"advisory":True}}
def write_reference_graph_json(r,p): _w(p,_j(mathlib_discovery_report_to_reference_graph(r)))
def write_reference_graph_jsonl(r,p):
 g=mathlib_discovery_report_to_reference_graph(r); _w(p,"".join(_j({"kind":"node",**x})+"\n" for x in g["nodes"])+"".join(_j({"kind":"edge",**x})+"\n" for x in g["edges"]))
def _verified_names(r): return {e.name for e in (r.allowlist_ingestion_report.entries if r.allowlist_ingestion_report else []) if e.has_boundary_evidence()}
def mathlib_discovery_report_to_api_response(r):
 from mathgraph.api_service import _resp
 req=ApiRequest(make_api_request_id("mathlib-discovery",r.report_id),ApiRoute.MATHLIB_DECLARATION_DISCOVERY); truth=ApiTruthStatus.BOUNDARY_EVIDENCE_PRESENT if _verified_names(r) else ApiTruthStatus.ADVISORY_ONLY; return _resp(req,route_result_from_artifacts(req.route,[r],truth_status=truth,safety=ApiSafetyLevel.SAFE_REVIEW_REQUIRED))
def mathlib_discovery_report_to_process_episodes(r): return [ProcessEpisodeRecord(make_process_episode_id("mathlib-discovery",d.declaration_id),ProcessEpisodeStatus.TERMINAL_VERIFIED_PROOF if d.name in _verified_names(r) else ProcessEpisodeStatus.ADVISORY_ONLY,contexts=[ProcessContextItem(content_id("mathlib-discovery-context",d.declaration_id),ProcessContextKind.RAW_EVENT,ProcessContextRole.ADVISORY_ONLY,d.full_name)],terminal_form=TerminalForm.VERIFIED_PROOF if d.name in _verified_names(r) else None,verifier_boundary_crossed=d.name in _verified_names(r)) for d in r.declarations]
def mathlib_discovery_report_to_proof_digestion_inputs(r): return [{"declaration_id":d.declaration_id,"proof_text":d.statement_excerpt,"boundary_backed":d.name in _verified_names(r),"advisory":d.name not in _verified_names(r)} for d in r.declarations]
def mathlib_discovery_report_to_discovery_value_scores(r):
 out=[]
 for d in r.declarations:
  sig=DiscoveryValueSignal(content_id("mathlib-discovery-signal",d.declaration_id),DiscoveryValueSignalKind.REUSE_VALUE,1.0 if d.name in _verified_names(r) else .1,source_object_kind=DiscoveryValueObjectKind.RAW_TASK); s=DiscoveryValueScore(content_id("mathlib-discovery-score",d.declaration_id),d.declaration_id,DiscoveryValueObjectKind.RAW_TASK,signals=[sig]); s.recompute(); out.append(s)
 return out
def mathlib_discovery_report_to_structural_identity_objects(r): return [{"object_id":d.declaration_id,"name":d.full_name,"kind":d.declaration_kind.value,"advisory":d.name not in _verified_names(r)} for d in r.declarations]
def mathlib_discovery_report_to_route_telemetry_events(r): return [{"event_id":content_id("mathlib-discovery-telemetry",d.declaration_id),"route_kind":"mathlib_declaration_discovery","outcome":d.selection_status.value,"verifier_boundary_crossed":d.name in _verified_names(r)} for d in r.declarations]
def mathlib_discovery_report_to_alchemical_trace(r):
 t=AlchemicalTrace(make_alchemical_trace_id("mathlib-discovery",r.report_id))
 for p in (AlchemicalPhase.RAW_MATTER,AlchemicalPhase.CALCINATION,AlchemicalPhase.DESCENSION): t.add_step(phase=p,status=AlchemicalStatus.ADVISORY_ONLY)
 if _verified_names(r): t.add_step(phase=AlchemicalPhase.FIXATION,status=AlchemicalStatus.PROMOTED_BY_VERIFIER)
 for p in (AlchemicalPhase.DISTILLATION,AlchemicalPhase.COAGULATION): t.add_step(phase=p,status=AlchemicalStatus.ADVISORY_ONLY)
 return t
def mathlib_discovery_report_to_agent_experiences(r): return [AgentExperience(content_id("mathlib-discovery-exp",d.declaration_id),"mathlib-discovery",None,None,"project",None,AgentExperienceOutcome.VERIFIED_PROOF if d.name in _verified_names(r) else AgentExperienceOutcome.ADVISORY_ONLY,terminal_form=TerminalForm.VERIFIED_PROOF if d.name in _verified_names(r) else None,verifier_boundary_crossed=d.name in _verified_names(r)) for d in r.declarations]
def audit_mathlib_discovery_request(x): return [_af("CRITICAL","MATHLIB_DISCOVERY_REQUEST_NON_ADVISORY","request non-advisory",x.request_id)] if not x.advisory else []
def audit_mathlib_discovered_module(x): return [_af("CRITICAL","MATHLIB_DISCOVERY_MODULE_NON_ADVISORY","module non-advisory",x.module_id)] if not x.advisory else []
def audit_mathlib_discovered_declaration(x): return [_af("CRITICAL","MATHLIB_DISCOVERY_DECLARATION_NON_ADVISORY","discovered declaration treated as proof",x.declaration_id)] if not x.advisory else []
def audit_mathlib_reference_hint(x): return [_af("CRITICAL","MATHLIB_DISCOVERY_HINT_NON_ADVISORY","reference hint treated as proof",x.hint_id)] if not x.advisory else []
def audit_mathlib_declaration_discovery_report(x):
 out=sum((audit_mathlib_discovered_declaration(d) for d in x.declarations),[])+sum((audit_mathlib_reference_hint(h) for h in x.reference_hints),[])
 if x.ok() and x.critical_count(): out.append(_af("CRITICAL","MATHLIB_DISCOVERY_OK_WITH_CRITICAL","report hides criticals",x.report_id))
 if x.allowlist_ingestion_report and x.allowlist_ingestion_report.lawbook_replay_summary.get("known_skip_total",0) and not x.allowlist_ingestion_report.lawbook_replay_summary.get("accepted_total",0): out.append(_af("CRITICAL","MATHLIB_DISCOVERY_SKIP_WITHOUT_ACCEPTANCE","known skip without accepted review",x.report_id))
 return out
def _af(sev,code,msg,obj): return {"severity":sev,"code":code,"message":msg,"object_id":obj}
def _hash(t): return sha256(t.encode()).hexdigest()
def _now(): return datetime.now(timezone.utc).isoformat()
def _j(x): return json.dumps(x,sort_keys=True,separators=(",",":"),default=str)
def _w(p,t): path=Path(p); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(t,encoding="utf-8")
