"""Curated local-path-only real Mathlib demo workflow."""
from __future__ import annotations
import json,shutil,subprocess
from dataclasses import MISSING,dataclass,field
from datetime import datetime,timezone
from enum import Enum
from pathlib import Path
from typing import Any,Mapping
from mathgraph.agent_biography import AgentExperience,AgentExperienceOutcome
from mathgraph.alchemy import AlchemicalPhase,AlchemicalStatus,AlchemicalTrace,make_alchemical_trace_id
from mathgraph.api_service import ApiRequest,ApiRoute,ApiSafetyLevel,ApiTruthStatus,make_api_request_id,route_result_from_artifacts
from mathgraph.certificates import TerminalForm
from mathgraph.discovery_value import DiscoveryValueObjectKind,DiscoveryValueScore,DiscoveryValueSignal,DiscoveryValueSignalKind
from mathgraph.hashing import content_id
from mathgraph.mathlib_declaration_discovery import MathlibDeclarationDiscoveryReport,MathlibDiscoveryRequest,MathlibDiscoverySourceKind,MathlibSelectionStatus,build_allowlist_manifest_from_discovery,mathlib_discovery_report_to_reference_graph,run_mathlib_declaration_discovery
from mathgraph.mathlib_local_allowlist import MathlibLocalAllowlistManifest,MathlibLocalFailureKind
from mathgraph.process_memory import ProcessContextItem,ProcessContextKind,ProcessContextRole,ProcessEpisodeRecord,ProcessEpisodeStatus,make_process_episode_id
def _enum(n,v): return Enum(n,{x:x for x in v.split()},type=str)
RealMathlibDemoStatus=_enum("RealMathlibDemoStatus","NOT_RUN COMPLETED COMPLETED_WITH_WARNINGS SKIPPED_ENVIRONMENT SKIPPED_NO_SELECTION FAILED ERROR UNKNOWN")
RealMathlibDemoTruthStatus=_enum("RealMathlibDemoTruthStatus","ADVISORY_ONLY BOUNDARY_EVIDENCE_PRESENT KNOWN_SKIP_AVAILABLE SKIPPED_NO_ENVIRONMENT SKIPPED_NO_VERIFIER UNKNOWN")
RealMathlibEnvironmentStatus=_enum("RealMathlibEnvironmentStatus","READY MISSING_PROJECT_ROOT MISSING_LEAN MISSING_LAKE MISSING_GIT MISSING_MATHLIB_MARKER MISSING_SELECTED_MODULES REVISION_MISMATCH_WARNING TOOLCHAIN_MISMATCH_WARNING SKIPPED UNKNOWN")
RealMathlibDemoStage=_enum("RealMathlibDemoStage","CONFIG ENVIRONMENT DISCOVERY SELECTION MANIFEST ALLOWLIST_INGESTION LAWBOOK_REPLAY REPORT UNKNOWN")
RealMathlibDemoRisk=_enum("RealMathlibDemoRisk","NONE MISSING_ENVIRONMENT EMPTY_SELECTION DISCOVERY_ONLY DOWNSTREAM_NOT_RUN MISSING_VERIFIER UNSAFE_REJECTED EXPECTED_MISSING_REJECTED IMPORT_FAILURE_REJECTED UNKNOWN")
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
class RealMathlibDemoConfig:
 demo_id:str; name:str; version:str="0.1"; project_root:str|None=None; expected_revision:str|None=None; expected_lean_toolchain:str|None=None; require_mathlib_marker:bool=True; discovery_modules:list[dict[str,Any]]=field(default_factory=list); selection_policy:dict[str,Any]=field(default_factory=dict); selected_declaration_names:tuple[str,...]=(); build_manifest:bool=True; run_allowlist_ingestion:bool=False; accept_verified_entries_in_memory:bool=False; allow_execution_default:bool=False; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def write_json(self,p): _w(p,self.to_json())
 @classmethod
 def read_json(c,p): return c.from_json(Path(p).read_text())
@_serial
@dataclass
class RealMathlibEnvironmentReport:
 environment_id:str; demo_id:str; project_root:str|None=None; lean_path:str|None=None; lake_path:str|None=None; git_path:str|None=None; detected_revision:str|None=None; expected_revision:str|None=None; detected_lean_toolchain:str|None=None; expected_lean_toolchain:str|None=None; project_markers:tuple[str,...]=(); checked_modules:tuple[str,...]=(); missing_modules:tuple[str,...]=(); status:RealMathlibEnvironmentStatus=RealMathlibEnvironmentStatus.UNKNOWN; warnings:tuple[str,...]=(); criticals:tuple[str,...]=(); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def ready(self): return self.status in {RealMathlibEnvironmentStatus.READY,RealMathlibEnvironmentStatus.REVISION_MISMATCH_WARNING,RealMathlibEnvironmentStatus.TOOLCHAIN_MISMATCH_WARNING}
@_serial
@dataclass
class RealMathlibDemoStageResult:
 stage_id:str; demo_id:str; stage:RealMathlibDemoStage; status:RealMathlibDemoStatus=RealMathlibDemoStatus.UNKNOWN; truth_status:RealMathlibDemoTruthStatus=RealMathlibDemoTruthStatus.ADVISORY_ONLY; summary:dict[str,Any]=field(default_factory=dict); artifact_paths:tuple[str,...]=(); warnings:tuple[str,...]=(); criticals:tuple[str,...]=(); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
@dataclass
class RealMathlibDemoReport:
 report_id:str; demo_id:str; config:RealMathlibDemoConfig|None=None; environment_report:RealMathlibEnvironmentReport|None=None; discovery_report:Any|None=None; generated_manifest:Any|None=None; allowlist_ingestion_report:Any|None=None; module_verification_report:Any|None=None; lawbook_replay_summary:dict[str,Any]=field(default_factory=dict); stage_results:list[RealMathlibDemoStageResult]=field(default_factory=list); created_at:str=field(default_factory=lambda:_now()); status:RealMathlibDemoStatus=RealMathlibDemoStatus.UNKNOWN; truth_status:RealMathlibDemoTruthStatus=RealMathlibDemoTruthStatus.UNKNOWN; summary:dict[str,Any]=field(default_factory=dict); warnings:tuple[str,...]=(); criticals:tuple[str,...]=(); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def module_count(self): return self.discovery_report.module_count() if self.discovery_report else 0
 def declaration_count(self): return self.discovery_report.declaration_count() if self.discovery_report else 0
 def selected_count(self): return self.discovery_report.selected_declaration_count() if self.discovery_report else 0
 def generated_manifest_file_count(self): return len(self.generated_manifest.files) if self.generated_manifest else 0
 def verified_count(self): return (self.module_verification_report.verified_count() if self.module_verification_report else 0)+(self.allowlist_ingestion_report.verified_entry_count() if self.allowlist_ingestion_report else 0)
 def boundary_evidence_count(self): return (self.module_verification_report.boundary_evidence_count() if self.module_verification_report else 0)+(self.allowlist_ingestion_report.boundary_evidence_count() if self.allowlist_ingestion_report else 0)
 def known_skip_count(self): return int(self.lawbook_replay_summary.get("known_skip_total",0))
 def dependency_edge_count(self): return len(real_mathlib_demo_report_to_reference_graph(self).get("edges",()))
 def import_edge_count(self): return sum(e.get("kind")=="import" for e in real_mathlib_demo_report_to_reference_graph(self).get("edges",()))
 def reference_edge_count(self): return sum(e.get("kind")=="reference_hint" for e in real_mathlib_demo_report_to_reference_graph(self).get("edges",()))
 def warning_count(self): return len(self.warnings)+(len(self.environment_report.warnings) if self.environment_report else 0)
 def critical_count(self): return len(self.criticals)+(len(self.environment_report.criticals) if self.environment_report else 0)
 def summarize(self):
  es=self.allowlist_ingestion_report.entries if self.allowlist_ingestion_report else []
  mv=self.module_verification_report
  self.summary={"module_total":self.module_count(),"declaration_total":self.declaration_count(),"selected_total":self.selected_count(),"generated_manifest_file_total":self.generated_manifest_file_count(),"verified_total":self.verified_count(),"boundary_evidence_total":self.boundary_evidence_count(),"known_skip_total":self.known_skip_count(),"module_verification_target_total":mv.target_count() if mv else 0,"module_verification_declaration_total":mv.declaration_count() if mv else 0,"module_verification_verified_total":mv.verified_count() if mv else 0,"module_verification_boundary_evidence_total":mv.boundary_evidence_count() if mv else 0,"module_verification_known_skip_total":mv.known_skip_count() if mv else 0,"dependency_edge_total":self.dependency_edge_count(),"import_edge_total":self.import_edge_count(),"reference_edge_total":self.reference_edge_count(),"unsafe_verified_total":sum(e.has_boundary_evidence() and e.failure_kind==MathlibLocalFailureKind.UNSAFE_MARKER for e in es),"expected_missing_verified_total":sum(e.has_boundary_evidence() and e.failure_kind==MathlibLocalFailureKind.EXPECTED_DECLARATION_MISSING for e in es),"import_failure_verified_total":sum(e.has_boundary_evidence() and e.failure_kind==MathlibLocalFailureKind.IMPORT_ERROR for e in es),"warning_total":self.warning_count(),"critical_total":self.critical_count()}; return self.summary
 def ok(self):
  s=self.summarize(); return self.critical_count()==0 and self.status not in {RealMathlibDemoStatus.FAILED,RealMathlibDemoStatus.ERROR} and not any(s[k] for k in ("unsafe_verified_total","expected_missing_verified_total","import_failure_verified_total"))
 def to_dict(self): return {**self.__dict__,"config":self.config.to_dict() if self.config else None,"environment_report":self.environment_report.to_dict() if self.environment_report else None,"discovery_report":self.discovery_report.to_dict() if self.discovery_report else None,"generated_manifest":self.generated_manifest.to_dict() if self.generated_manifest else None,"allowlist_ingestion_report":self.allowlist_ingestion_report.to_dict() if self.allowlist_ingestion_report else None,"module_verification_report":self.module_verification_report.to_dict() if self.module_verification_report else None,"stage_results":[x.to_dict() for x in self.stage_results],"status":self.status.value,"truth_status":self.truth_status.value,"warnings":list(self.warnings),"criticals":list(self.criticals)}
 @classmethod
 def from_dict(c,d):
  from mathgraph.mathlib_local_allowlist import MathlibLocalIngestionReport
  from mathgraph.mathlib_module_verification import MathlibModuleVerificationReport
  return c(str(d["report_id"]),str(d["demo_id"]),RealMathlibDemoConfig.from_dict(d["config"]) if d.get("config") else None,RealMathlibEnvironmentReport.from_dict(d["environment_report"]) if d.get("environment_report") else None,MathlibDeclarationDiscoveryReport.from_dict(d["discovery_report"]) if d.get("discovery_report") else None,MathlibLocalAllowlistManifest.from_dict(d["generated_manifest"]) if d.get("generated_manifest") else None,MathlibLocalIngestionReport.from_dict(d["allowlist_ingestion_report"]) if d.get("allowlist_ingestion_report") else None,MathlibModuleVerificationReport.from_dict(d["module_verification_report"]) if d.get("module_verification_report") else None,dict(d.get("lawbook_replay_summary",{})),[RealMathlibDemoStageResult.from_dict(x) for x in d.get("stage_results",())],str(d.get("created_at",_now())),RealMathlibDemoStatus(str(d.get("status","UNKNOWN"))),RealMathlibDemoTruthStatus(str(d.get("truth_status","UNKNOWN"))),dict(d.get("summary",{})),tuple(d.get("warnings",())),tuple(d.get("criticals",())),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
 def write_json(self,p): _w(p,self.to_json())
 @classmethod
 def read_json(c,p): return c.from_json(Path(p).read_text())
 def write_jsonl(self,p): _w(p,self.to_json()+"\n")
 @classmethod
 def read_jsonl(c,p): return [c.from_json(x) for x in Path(p).read_text().splitlines() if x.strip()]
for _c,_e in [(RealMathlibDemoConfig,()),(RealMathlibEnvironmentReport,("status",)),(RealMathlibDemoStageResult,("stage","status","truth_status"))]: _serial(_c,_e)
def make_real_mathlib_demo_config_id(*x): return content_id("real-mathlib-demo-config",x)
def make_real_mathlib_environment_id(*x): return content_id("real-mathlib-demo-environment",x)
def make_real_mathlib_stage_id(*x): return content_id("real-mathlib-demo-stage",x)
def make_real_mathlib_demo_report_id(*x): return content_id("real-mathlib-demo-report",x)
def default_real_mathlib_demo_config_dict(): return {"demo_id":"curated-real-mathlib-demo-example","name":"Curated Real Local Mathlib Demo Example","version":"0.1","project_root":"/path/to/local/mathlib","expected_revision":None,"expected_lean_toolchain":None,"require_mathlib_marker":True,"discovery_modules":[{"path":"Mathlib/Data/Nat/Basic.lean","module_name":"Mathlib.Data.Nat.Basic","max_declarations":10,"include_kinds":["theorem","lemma"],"name_contains":[],"exclude_name_contains":["deprecated","aux","_match","_proof"]}],"selection_policy":{"max_total_declarations":10,"prefer_kinds":["theorem","lemma"],"name_contains":[],"exclude_name_contains":["deprecated","aux","_match","_proof"]},"selected_declaration_names":[],"build_manifest":True,"run_allowlist_ingestion":False,"accept_verified_entries_in_memory":False,"allow_execution_default":False,"metadata":{"description":"Template only. Requires an already-working local Mathlib checkout. No downloads are performed."}}
def synthetic_standin_real_mathlib_demo_config_dict(): return {"demo_id":"synthetic-standin-real-mathlib-demo","name":"Synthetic Stand-In Real Mathlib Demo","version":"0.1","project_root":None,"expected_revision":None,"expected_lean_toolchain":None,"require_mathlib_marker":True,"discovery_modules":[{"path":"Mathlib/MathGraph/Basic.lean","module_name":"Mathlib.MathGraph.Basic","max_declarations":10,"include_kinds":["theorem","lemma"],"name_contains":[],"exclude_name_contains":["deprecated","aux","_match","_proof"]},{"path":"Mathlib/MathGraph/Logic.lean","module_name":"Mathlib.MathGraph.Logic","max_declarations":10,"include_kinds":["theorem","lemma"],"name_contains":[],"exclude_name_contains":["deprecated","aux","_match","_proof"]}],"selection_policy":{"max_total_declarations":10,"prefer_kinds":["theorem","lemma"],"name_contains":[],"exclude_name_contains":["deprecated","aux","_match","_proof"]},"selected_declaration_names":[],"build_manifest":True,"run_allowlist_ingestion":False,"accept_verified_entries_in_memory":False,"allow_execution_default":False,"metadata":{"description":"Synthetic stand-in for real Mathlib demo testing. Uses repo-local Mathlib.MathGraph modules. No downloads."}}
def ensure_default_real_mathlib_demo_examples(root,*,overwrite=False):
 root=Path(root); root.mkdir(parents=True,exist_ok=True); a=root/"curated_real_mathlib_demo_config.example.json"; b=root/"curated_real_mathlib_manifest.example.json"; c=root/"synthetic_standin_real_mathlib_demo_config.json"
 if overwrite or not a.exists(): _w(a,_j(default_real_mathlib_demo_config_dict()))
 if overwrite or not b.exists(): _w(b,_j({"allowlist_id":"curated-real-mathlib-manifest-example","name":"Curated Real Mathlib Manifest Example","version":"0.1","source_kind":"LOCAL_MATHLIB_PROJECT","trust_policy":"LOCAL_VERIFIER_REQUIRED","proof_system":"lean","project_root":None,"module_prefix":"Mathlib","files":[],"metadata":{"note":"Template only; no declarations are verified by this manifest."}}))
 if overwrite or not c.exists(): _w(c,_j(synthetic_standin_real_mathlib_demo_config_dict()))
 return a,b,c
def load_real_mathlib_demo_config(path): return RealMathlibDemoConfig.from_json(Path(path).read_text())
def detect_real_mathlib_demo_environment(config,*,project_root=None,timeout_sec=10.0):
 c=_cfg(config); root=Path(project_root or c.project_root) if (project_root or c.project_root) else None; lean=shutil.which("lean"); lake=shutil.which("lake"); git=shutil.which("git"); warns=[]; crit=[]; markers=[]; mods=tuple(x.get("path","") for x in c.discovery_modules); missing=()
 if not root or not root.exists(): return RealMathlibEnvironmentReport(make_real_mathlib_environment_id(c.demo_id,"missing"),c.demo_id,str(root) if root else None,lean,lake,git,status=RealMathlibEnvironmentStatus.MISSING_PROJECT_ROOT,warnings=("Supply --project-root pointing at an existing local Mathlib checkout.",))
 for n in ("Mathlib","lakefile.lean","lakefile.toml","lake-manifest.json","lean-toolchain"):
  if (root/n).exists(): markers.append(n)
 missing=tuple(m for m in mods if not (root/m).exists()); rev=None
 if git and (root/".git").exists():
  try: rev=subprocess.run([git,"-C",str(root),"rev-parse","HEAD"],capture_output=True,text=True,timeout=timeout_sec,check=True).stdout.strip()
  except Exception: warns.append("git revision unavailable")
 else: warns.append("git metadata unavailable")
 tool=(root/"lean-toolchain").read_text().strip() if (root/"lean-toolchain").exists() else None
 status=RealMathlibEnvironmentStatus.READY
 if missing: status=RealMathlibEnvironmentStatus.MISSING_SELECTED_MODULES
 elif c.require_mathlib_marker and not markers: status=RealMathlibEnvironmentStatus.MISSING_MATHLIB_MARKER
 elif not lean: status=RealMathlibEnvironmentStatus.MISSING_LEAN; warns.append("Lean not found; live verification will skip.")
 elif c.expected_revision and rev and c.expected_revision!=rev: status=RealMathlibEnvironmentStatus.REVISION_MISMATCH_WARNING; warns.append("revision mismatch")
 elif c.expected_lean_toolchain and tool and c.expected_lean_toolchain!=tool: status=RealMathlibEnvironmentStatus.TOOLCHAIN_MISMATCH_WARNING; warns.append("lean-toolchain mismatch")
 if not lake: warns.append("Lake not found; not required for this demo.")
 return RealMathlibEnvironmentReport(make_real_mathlib_environment_id(c.demo_id,str(root),rev),c.demo_id,str(root.resolve()),lean,lake,git,rev,c.expected_revision,tool,c.expected_lean_toolchain,tuple(markers),mods,missing,status,tuple(warns),tuple(crit))
def build_discovery_request_from_real_mathlib_demo_config(c,*,project_root=None):
 return MathlibDiscoveryRequest(content_id("real-mathlib-discovery-request",c.demo_id),f"Discovery for {c.name}",source_kind=MathlibDiscoverySourceKind.LOCAL_MATHLIB_PROJECT,project_root=str(project_root or c.project_root) if (project_root or c.project_root) else None,module_prefix="Mathlib",module_files=list(c.discovery_modules),selection_policy=dict(c.selection_policy),metadata={"real_mathlib_demo_id":c.demo_id})
def build_curated_allowlist_manifest_from_real_demo(r,*,allowlist_id=None): return build_allowlist_manifest_from_discovery(r.discovery_report,allowlist_id=allowlist_id) if r.discovery_report else None
def run_real_mathlib_demo(config=None,*,out_dir=None,project_root=None,allow_execution=False,allow_missing_verifier=True,run_allowlist_ingestion=None,run_module_verification=False,accept_verified_entries_in_memory=None,timeout_sec=20.0):
 c=_cfg(config); env=detect_real_mathlib_demo_environment(c,project_root=project_root); stages=[RealMathlibDemoStageResult(make_real_mathlib_stage_id(c.demo_id,"environment"),c.demo_id,RealMathlibDemoStage.ENVIRONMENT,RealMathlibDemoStatus.COMPLETED if env.ready() else RealMathlibDemoStatus.SKIPPED_ENVIRONMENT,summary={"status":env.status.value},warnings=env.warnings)]
 if env.status in {RealMathlibEnvironmentStatus.MISSING_PROJECT_ROOT,RealMathlibEnvironmentStatus.MISSING_SELECTED_MODULES,RealMathlibEnvironmentStatus.MISSING_MATHLIB_MARKER}:
  r=RealMathlibDemoReport(make_real_mathlib_demo_report_id(c.demo_id,env.status.value),c.demo_id,c,env,stage_results=stages,status=RealMathlibDemoStatus.SKIPPED_ENVIRONMENT,truth_status=RealMathlibDemoTruthStatus.SKIPPED_NO_ENVIRONMENT,warnings=env.warnings); r.summarize()
  if out_dir: write_real_mathlib_demo_artifacts(r,out_dir)
  return r
 req=build_discovery_request_from_real_mathlib_demo_config(c,project_root=env.project_root); downstream=c.run_allowlist_ingestion if run_allowlist_ingestion is None else run_allowlist_ingestion; accept=c.accept_verified_entries_in_memory if accept_verified_entries_in_memory is None else accept_verified_entries_in_memory
 dr=run_mathlib_declaration_discovery(req,project_root=env.project_root,build_manifest=True,run_allowlist_ingestion=False,allow_execution=False,allow_missing_verifier=allow_missing_verifier,timeout_sec=timeout_sec,require_mathlib_marker=c.require_mathlib_marker)
 if c.selected_declaration_names:
  chosen=set(c.selected_declaration_names)
  for d in dr.declarations:
   if d.selection_status==MathlibSelectionStatus.SELECTED and d.name not in chosen and d.full_name not in chosen: d.selection_status=MathlibSelectionStatus.EXCLUDED_BY_NAME
  dr.generated_manifest=build_allowlist_manifest_from_discovery(dr); dr.summarize()
 if downstream and dr.generated_manifest:
  from mathgraph.mathlib_local_allowlist import ingest_mathlib_local_allowlist
  ar=ingest_mathlib_local_allowlist(dr.generated_manifest,allow_execution=allow_execution,allow_missing_verifier=allow_missing_verifier,timeout_sec=timeout_sec,accept_verified_entries_in_memory=accept)
 else: ar=None
 if run_module_verification:
  from mathgraph.mathlib_module_verification import build_module_verification_request_from_real_demo_report,run_mathlib_module_verification
  shell=RealMathlibDemoReport("bridge",c.demo_id,c,env,dr,dr.generated_manifest,ar)
  mv=run_mathlib_module_verification(build_module_verification_request_from_real_demo_report(shell),allow_execution=allow_execution,allow_missing_verifier=allow_missing_verifier,accept_verified_entries_in_memory=accept,timeout_sec=timeout_sec)
 else: mv=None
 replay=dict(mv.lawbook_replay_summary) if mv and mv.lawbook_replay_summary else dict(ar.lawbook_replay_summary) if ar else {}; truth=RealMathlibDemoTruthStatus.KNOWN_SKIP_AVAILABLE if replay.get("known_skip_total") else RealMathlibDemoTruthStatus.BOUNDARY_EVIDENCE_PRESENT if (mv and mv.verified_count()) or (ar and ar.verified_entry_count()) else RealMathlibDemoTruthStatus.ADVISORY_ONLY
 status=RealMathlibDemoStatus.SKIPPED_NO_SELECTION if not dr.selected_declaration_count() else RealMathlibDemoStatus.COMPLETED_WITH_WARNINGS if env.warnings or dr.warnings else RealMathlibDemoStatus.COMPLETED
 r=RealMathlibDemoReport(make_real_mathlib_demo_report_id(c.demo_id,dr.report_id,allow_execution,downstream,run_module_verification,accept),c.demo_id,c,env,dr,dr.generated_manifest,ar,mv,replay,stages,status=status,truth_status=truth,warnings=tuple(env.warnings)+tuple(dr.warnings),criticals=dr.criticals); r.summarize()
 if out_dir: write_real_mathlib_demo_artifacts(r,out_dir)
 return r
def real_mathlib_demo_report_to_markdown(r):
 s=r.summarize(); e=r.environment_report; lines=["# Curated Real Mathlib Demo Report","",f"- Demo status: {r.status.value}",f"- Truth status: {r.truth_status.value}",f"- Project root: {e.project_root if e else ''}","", "## Environment Diagnosis",f"- Environment status: {e.status.value if e else 'UNKNOWN'}",f"- Detected revision: {e.detected_revision if e else ''}",f"- Expected revision: {e.expected_revision if e else ''}",f"- Detected lean-toolchain: {e.detected_lean_toolchain if e else ''}",f"- Expected lean-toolchain: {e.expected_lean_toolchain if e else ''}","", "## Selected Modules"]
 lines += [f"- `{m.module_name}`" for m in (r.discovery_report.modules if r.discovery_report else [])] or ["- No modules available."]
 lines += ["", "## Discovered Declarations"]+[f"- `{d.full_name}` ({d.selection_status.value})" for d in (r.discovery_report.declarations if r.discovery_report else [])]+["", "## Generated Manifest Summary",f"- Files: {s['generated_manifest_file_total']}","", "## Module-Aware Verification Summary",f"- Targets: {s['module_verification_target_total']}",f"- Declarations: {s['module_verification_declaration_total']}",f"- Verified imported declarations: {s['module_verification_verified_total']}","", "## Downstream Verifier Summary",f"- Verified entries: {s['verified_total']}",f"- Boundary evidence: {s['boundary_evidence_total']}","", "## Lawbook Replay Summary",f"- Known skips: {s['known_skip_total']}","", "## Dependency/Reference Graph Summary",f"- Edges: {s['dependency_edge_total']} total, {s['import_edge_total']} imports, {s['reference_edge_total']} references","", "## What Crossed The Verifier Boundary"]
 lines += [f"- `{x.full_name}`" for x in (r.allowlist_ingestion_report.entries if r.allowlist_ingestion_report else []) if x.has_boundary_evidence()] or ["- Nothing crossed the verifier boundary."]
 lines += ["", "## What Stayed Advisory","- Local path, revision, toolchain, discovery, manifests, graphs, and reports remain advisory."]
 if r.status==RealMathlibDemoStatus.SKIPPED_ENVIRONMENT: lines += ["", "## Missing Environment Instructions","- Supply `--project-root /path/to/local/mathlib` with the explicitly configured modules present."]
 lines += ["", "## Boundary Discipline","A local Mathlib checkout is candidate structured memory.","Only allowlisted declarations with explicit verifier boundary evidence become proof evidence.","", "## Next Recommended Action","- Select a tiny module/declaration set first; run verifier-bound ingestion only when the local project is already working."]
 return "\n".join(lines)+"\n"
def concise_real_mathlib_demo_summary(r,artifact_paths=None):
 p=artifact_paths or {}; s=r.summarize()
 return "\n".join(["MathGraph Real Mathlib Demo",f"status: {r.status.value}",f"truth_status: {r.truth_status.value}",f"modules: {s['module_total']}",f"declarations: {s['declaration_total']}",f"selected: {s['selected_total']}",f"verified: {s['verified_total']}",f"known_skips: {s['known_skip_total']}",f"boundary_evidence: {s['boundary_evidence_total']}",f"markdown: {p.get('markdown','-')}",f"json: {p.get('report','-')}"])+"\n"
def real_mathlib_demo_report_to_reference_graph(r): return mathlib_discovery_report_to_reference_graph(r.discovery_report) if r.discovery_report else {"nodes":[],"edges":[],"metadata":{"advisory":True}}
def write_real_mathlib_demo_artifacts(r,out):
 out=Path(out); paths={"report":out/"real_mathlib_demo_report.json","markdown":out/"real_mathlib_demo_report.md","environment":out/"environment_report.json","discovery":out/"discovery_report.json","generated_manifest":out/"generated_allowlist_manifest.json","allowlist_ingestion":out/"allowlist_ingestion_report.json","module_verification":out/"module_verification_report.json","reference_graph":out/"reference_graph.json","api_response":out/"api_response.json"}
 r.write_json(paths["report"]); _w(paths["markdown"],real_mathlib_demo_report_to_markdown(r))
 if r.environment_report:_w(paths["environment"],r.environment_report.to_json())
 if r.discovery_report:r.discovery_report.write_json(paths["discovery"])
 if r.generated_manifest:r.generated_manifest.write_json(paths["generated_manifest"])
 if r.allowlist_ingestion_report:r.allowlist_ingestion_report.write_json(paths["allowlist_ingestion"])
 if r.module_verification_report:r.module_verification_report.write_json(paths["module_verification"])
 _w(paths["reference_graph"],_j(real_mathlib_demo_report_to_reference_graph(r))); _w(paths["api_response"],real_mathlib_demo_report_to_api_response(r).to_json()); return {k:str(v) for k,v in paths.items() if v.exists()}
def real_mathlib_demo_report_to_api_response(r):
 from mathgraph.api_service import _resp
 req=ApiRequest(make_api_request_id("real-mathlib-demo",r.report_id),ApiRoute.REAL_MATHLIB_DEMO); truth=ApiTruthStatus.KNOWN_SKIP_AVAILABLE if r.known_skip_count() else ApiTruthStatus.BOUNDARY_EVIDENCE_PRESENT if r.verified_count() else ApiTruthStatus.ADVISORY_ONLY; return _resp(req,route_result_from_artifacts(req.route,[r],truth_status=truth,safety=ApiSafetyLevel.SAFE_REVIEW_REQUIRED))
def _names(r): return {e.name for e in (r.allowlist_ingestion_report.entries if r.allowlist_ingestion_report else []) if e.has_boundary_evidence()}|{x.declaration_name for x in (r.module_verification_report.declaration_results if r.module_verification_report else []) if x.verified}
def _decls(r): return r.discovery_report.declarations if r.discovery_report else []
def real_mathlib_demo_report_to_process_episodes(r): return [ProcessEpisodeRecord(make_process_episode_id("real-mathlib-demo",d.declaration_id),ProcessEpisodeStatus.TERMINAL_VERIFIED_PROOF if d.name in _names(r) else ProcessEpisodeStatus.ADVISORY_ONLY,contexts=[ProcessContextItem(content_id("real-mathlib-demo-context",d.declaration_id),ProcessContextKind.RAW_EVENT,ProcessContextRole.ADVISORY_ONLY,d.full_name)],terminal_form=TerminalForm.VERIFIED_PROOF if d.name in _names(r) else None,verifier_boundary_crossed=d.name in _names(r)) for d in _decls(r)]
def real_mathlib_demo_report_to_discovery_value_scores(r):
 out=[]
 for d in _decls(r):
  sig=DiscoveryValueSignal(content_id("real-mathlib-demo-signal",d.declaration_id),DiscoveryValueSignalKind.REUSE_VALUE,1.0 if d.name in _names(r) else .1,source_object_kind=DiscoveryValueObjectKind.RAW_TASK); s=DiscoveryValueScore(content_id("real-mathlib-demo-score",d.declaration_id),d.declaration_id,DiscoveryValueObjectKind.RAW_TASK,signals=[sig]); s.recompute(); out.append(s)
 return out
def real_mathlib_demo_report_to_structural_identity_objects(r): return [{"object_id":d.declaration_id,"name":d.full_name,"advisory":d.name not in _names(r)} for d in _decls(r)]
def real_mathlib_demo_report_to_route_telemetry_events(r): return [{"event_id":content_id("real-mathlib-demo-telemetry",d.declaration_id),"route_kind":"real_mathlib_demo","verifier_boundary_crossed":d.name in _names(r)} for d in _decls(r)]
def real_mathlib_demo_report_to_alchemical_trace(r):
 t=AlchemicalTrace(make_alchemical_trace_id("real-mathlib-demo",r.report_id))
 for p in (AlchemicalPhase.RAW_MATTER,AlchemicalPhase.CALCINATION,AlchemicalPhase.SOLUTION,AlchemicalPhase.DESCENSION): t.add_step(phase=p,status=AlchemicalStatus.ADVISORY_ONLY)
 if _names(r): t.add_step(phase=AlchemicalPhase.FIXATION,status=AlchemicalStatus.PROMOTED_BY_VERIFIER)
 for p in (AlchemicalPhase.DISTILLATION,AlchemicalPhase.COAGULATION): t.add_step(phase=p,status=AlchemicalStatus.ADVISORY_ONLY)
 return t
def real_mathlib_demo_report_to_agent_experiences(r): return [AgentExperience(content_id("real-mathlib-demo-exp",d.declaration_id),"real-mathlib-demo",None,None,"project",None,AgentExperienceOutcome.VERIFIED_PROOF if d.name in _names(r) else AgentExperienceOutcome.ADVISORY_ONLY,terminal_form=TerminalForm.VERIFIED_PROOF if d.name in _names(r) else None,verifier_boundary_crossed=d.name in _names(r)) for d in _decls(r)]
def audit_real_mathlib_demo_config(x): return [_af("CRITICAL","REAL_MATHLIB_DEMO_CONFIG_NON_ADVISORY","config non-advisory",x.demo_id)] if not x.advisory else []
def audit_real_mathlib_environment_report(x): return [_af("CRITICAL","REAL_MATHLIB_ENV_NON_ADVISORY","environment non-advisory",x.environment_id)] if not x.advisory else []
def audit_real_mathlib_stage_result(x): return [_af("CRITICAL","REAL_MATHLIB_STAGE_NON_ADVISORY","stage non-advisory",x.stage_id)] if not x.advisory else []
def audit_real_mathlib_demo_report(x):
 out=[]
 if not x.advisory: out.append(_af("CRITICAL","REAL_MATHLIB_DEMO_REPORT_NON_ADVISORY","report non-advisory",x.report_id))
 if x.status==RealMathlibDemoStatus.SKIPPED_ENVIRONMENT and x.truth_status not in {RealMathlibDemoTruthStatus.SKIPPED_NO_ENVIRONMENT,RealMathlibDemoTruthStatus.ADVISORY_ONLY}: out.append(_af("CRITICAL","REAL_MATHLIB_DEMO_SKIP_AS_PROOF","missing environment treated as proof",x.report_id))
 if x.truth_status not in {RealMathlibDemoTruthStatus.ADVISORY_ONLY,RealMathlibDemoTruthStatus.SKIPPED_NO_ENVIRONMENT} and not x.boundary_evidence_count(): out.append(_af("CRITICAL","REAL_MATHLIB_DEMO_PROOF_WITHOUT_BOUNDARY","proof claim lacks boundary",x.report_id))
 if x.known_skip_count() and not x.lawbook_replay_summary.get("accepted_total",0): out.append(_af("CRITICAL","REAL_MATHLIB_DEMO_SKIP_WITHOUT_ACCEPTANCE","known skip without accepted replay",x.report_id))
 s=x.summarize()
 if any(s[k] for k in ("unsafe_verified_total","expected_missing_verified_total","import_failure_verified_total")): out.append(_af("CRITICAL","REAL_MATHLIB_DEMO_FAILED_ENTRY_VERIFIED","failed entry verified",x.report_id))
 return out
def _cfg(x):
 if x is None: return RealMathlibDemoConfig.from_dict(default_real_mathlib_demo_config_dict())
 if isinstance(x,RealMathlibDemoConfig): return x
 if isinstance(x,(str,Path)): return load_real_mathlib_demo_config(x)
 return RealMathlibDemoConfig.from_dict(x)
def _af(sev,code,msg,obj): return {"severity":sev,"code":code,"message":msg,"object_id":obj}
def _now(): return datetime.now(timezone.utc).isoformat()
def _j(x): return json.dumps(x,sort_keys=True,separators=(",",":"),default=str)
def _w(p,t): path=Path(p); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(t,encoding="utf-8")
