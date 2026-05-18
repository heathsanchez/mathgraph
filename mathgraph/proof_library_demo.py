"""Curated advisory proof-library demos over discovery and local allowlist ingestion."""
from __future__ import annotations
import json
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
from mathgraph.mathlib_declaration_discovery import MathlibDiscoveryRequest,MathlibDiscoverySourceKind,build_synthetic_mathlib_discovery_request,load_mathlib_discovery_request,mathlib_discovery_report_to_reference_graph,run_mathlib_declaration_discovery
from mathgraph.mathlib_local_allowlist import MathlibLocalFailureKind,mathlib_local_report_to_dependency_graph
from mathgraph.process_memory import ProcessContextItem,ProcessContextKind,ProcessContextRole,ProcessEpisodeRecord,ProcessEpisodeStatus,make_process_episode_id
def _enum(n,v): return Enum(n,{x:x for x in v.split()},type=str)
ProofLibraryDemoKind=_enum("ProofLibraryDemoKind","SYNTHETIC REAL_LOCAL_MATHLIB REAL_LOCAL_LEAN_PROJECT UNKNOWN")
ProofLibraryDemoStatus=_enum("ProofLibraryDemoStatus","NOT_RUN COMPLETED COMPLETED_WITH_WARNINGS SKIPPED_ENVIRONMENT FAILED ERROR UNKNOWN")
ProofLibraryDemoStage=_enum("ProofLibraryDemoStage","CONFIG ENVIRONMENT DISCOVERY MANIFEST ALLOWLIST_INGESTION LAWBOOK_REPLAY DEPENDENCY_GRAPH REPORT HARDENING_SUMMARY UNKNOWN")
ProofLibraryDemoTruthStatus=_enum("ProofLibraryDemoTruthStatus","ADVISORY_ONLY BOUNDARY_EVIDENCE_PRESENT KNOWN_SKIP_AVAILABLE SKIPPED_NO_VERIFIER SKIPPED_NO_ENVIRONMENT UNKNOWN")
ProofLibraryDemoRisk=_enum("ProofLibraryDemoRisk","NONE DISCOVERY_ONLY MISSING_ENVIRONMENT MISSING_VERIFIER EMPTY_SELECTION DOWNSTREAM_NOT_RUN UNSAFE_REJECTED EXPECTED_MISSING_REJECTED IMPORT_FAILURE_REJECTED UNKNOWN")
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
class ProofLibraryDemoConfig:
 demo_id:str; name:str; version:str="0.1"; demo_kind:ProofLibraryDemoKind=ProofLibraryDemoKind.SYNTHETIC; project_root:str|None=None; discovery_request_path:str|None=None; module_files:list[dict[str,Any]]=field(default_factory=list); selection_policy:dict[str,Any]=field(default_factory=dict); use_synthetic_request:bool=False; build_manifest:bool=True; run_allowlist_ingestion:bool=True; accept_verified_entries_in_memory:bool=True; allow_execution_default:bool=False; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def write_json(self,p): _w(p,self.to_json())
 @classmethod
 def read_json(c,p): return c.from_json(Path(p).read_text())
@_serial
@dataclass
class ProofLibraryDemoStageResult:
 stage_id:str; demo_id:str; stage:ProofLibraryDemoStage; status:ProofLibraryDemoStatus=ProofLibraryDemoStatus.UNKNOWN; truth_status:ProofLibraryDemoTruthStatus=ProofLibraryDemoTruthStatus.ADVISORY_ONLY; summary:dict[str,Any]=field(default_factory=dict); artifact_paths:tuple[str,...]=(); warnings:tuple[str,...]=(); criticals:tuple[str,...]=(); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
@dataclass
class ProofLibraryDemoReport:
 report_id:str; demo_id:str; config:ProofLibraryDemoConfig|None=None; discovery_report:Any|None=None; generated_manifest:Any|None=None; allowlist_ingestion_report:Any|None=None; lawbook_replay_summary:dict[str,Any]=field(default_factory=dict); dependency_graph:dict[str,Any]=field(default_factory=dict); stage_results:list[ProofLibraryDemoStageResult]=field(default_factory=list); created_at:str=field(default_factory=lambda:_now()); status:ProofLibraryDemoStatus=ProofLibraryDemoStatus.UNKNOWN; truth_status:ProofLibraryDemoTruthStatus=ProofLibraryDemoTruthStatus.UNKNOWN; summary:dict[str,Any]=field(default_factory=dict); warnings:tuple[str,...]=(); criticals:tuple[str,...]=(); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def stage_count(self): return len(self.stage_results)
 def module_count(self): return self.discovery_report.module_count() if self.discovery_report else 0
 def declaration_count(self): return self.discovery_report.declaration_count() if self.discovery_report else 0
 def selected_count(self): return self.discovery_report.selected_declaration_count() if self.discovery_report else 0
 def generated_manifest_file_count(self): return len(self.generated_manifest.files) if self.generated_manifest else 0
 def downstream_verified_count(self): return self.allowlist_ingestion_report.verified_entry_count() if self.allowlist_ingestion_report else 0
 def boundary_evidence_count(self): return self.allowlist_ingestion_report.boundary_evidence_count() if self.allowlist_ingestion_report else 0
 def known_skip_count(self): return int(self.lawbook_replay_summary.get("known_skip_total",0))
 def dependency_edge_count(self): return len(self.dependency_graph.get("edges",()))
 def import_edge_count(self): return sum((x.get("dependency_kind") or x.get("kind")) in {"IMPORTS_MODULE","import"} for x in self.dependency_graph.get("edges",()))
 def reference_edge_count(self): return sum((x.get("dependency_kind") or x.get("kind")) in {"REFERENCES_DECLARATION","EXPECTED_REFERENCE","TEXT_REFERENCE","reference_hint"} for x in self.dependency_graph.get("edges",()))
 def warning_count(self): return len(self.warnings)
 def critical_count(self): return len(self.criticals)
 def summarize(self):
  es=self.allowlist_ingestion_report.entries if self.allowlist_ingestion_report else []
  self.summary={"stage_total":len(self.stage_results),"module_total":self.module_count(),"declaration_total":self.declaration_count(),"selected_total":self.selected_count(),"generated_manifest_file_total":self.generated_manifest_file_count(),"downstream_verified_total":self.downstream_verified_count(),"boundary_evidence_total":self.boundary_evidence_count(),"dependency_edge_total":self.dependency_edge_count(),"import_edge_total":self.import_edge_count(),"reference_edge_total":self.reference_edge_count(),"candidate_total":self.lawbook_replay_summary.get("candidate_total",0),"accepted_total":self.lawbook_replay_summary.get("accepted_total",0),"known_skip_total":self.known_skip_count(),"unsafe_verified_total":sum(e.has_boundary_evidence() and e.failure_kind==MathlibLocalFailureKind.UNSAFE_MARKER for e in es),"expected_missing_verified_total":sum(e.has_boundary_evidence() and e.failure_kind==MathlibLocalFailureKind.EXPECTED_DECLARATION_MISSING for e in es),"import_failure_verified_total":sum(e.has_boundary_evidence() and e.failure_kind==MathlibLocalFailureKind.IMPORT_ERROR for e in es),"warning_total":len(self.warnings),"critical_total":len(self.criticals)}; return self.summary
 def ok(self):
  s=self.summarize(); return self.critical_count()==0 and self.status not in {ProofLibraryDemoStatus.FAILED,ProofLibraryDemoStatus.ERROR} and not any(s[k] for k in ("unsafe_verified_total","expected_missing_verified_total","import_failure_verified_total"))
 def to_dict(self): return {**self.__dict__,"config":self.config.to_dict() if self.config else None,"discovery_report":self.discovery_report.to_dict() if self.discovery_report else None,"generated_manifest":self.generated_manifest.to_dict() if self.generated_manifest else None,"allowlist_ingestion_report":self.allowlist_ingestion_report.to_dict() if self.allowlist_ingestion_report else None,"stage_results":[x.to_dict() for x in self.stage_results],"status":self.status.value,"truth_status":self.truth_status.value,"warnings":list(self.warnings),"criticals":list(self.criticals)}
 @classmethod
 def from_dict(c,d):
  from mathgraph.mathlib_declaration_discovery import MathlibDeclarationDiscoveryReport
  from mathgraph.mathlib_local_allowlist import MathlibLocalAllowlistManifest,MathlibLocalIngestionReport
  return c(str(d["report_id"]),str(d["demo_id"]),ProofLibraryDemoConfig.from_dict(d["config"]) if d.get("config") else None,MathlibDeclarationDiscoveryReport.from_dict(d["discovery_report"]) if d.get("discovery_report") else None,MathlibLocalAllowlistManifest.from_dict(d["generated_manifest"]) if d.get("generated_manifest") else None,MathlibLocalIngestionReport.from_dict(d["allowlist_ingestion_report"]) if d.get("allowlist_ingestion_report") else None,dict(d.get("lawbook_replay_summary",{})),dict(d.get("dependency_graph",{})),[ProofLibraryDemoStageResult.from_dict(x) for x in d.get("stage_results",())],str(d.get("created_at",_now())),ProofLibraryDemoStatus(str(d.get("status","UNKNOWN"))),ProofLibraryDemoTruthStatus(str(d.get("truth_status","UNKNOWN"))),dict(d.get("summary",{})),tuple(d.get("warnings",())),tuple(d.get("criticals",())),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
 def write_json(self,p): _w(p,self.to_json())
 @classmethod
 def read_json(c,p): return c.from_json(Path(p).read_text())
 def write_jsonl(self,p): _w(p,self.to_json()+"\n")
 @classmethod
 def read_jsonl(c,p): return [c.from_json(x) for x in Path(p).read_text().splitlines() if x.strip()]
for _c,_e in [(ProofLibraryDemoConfig,("demo_kind",)),(ProofLibraryDemoStageResult,("stage","status","truth_status"))]: _serial(_c,_e)
def make_proof_library_demo_config_id(*x): return content_id("proof-library-demo-config",x)
def make_proof_library_demo_stage_id(*x): return content_id("proof-library-demo-stage",x)
def make_proof_library_demo_report_id(*x): return content_id("proof-library-demo-report",x)
def default_synthetic_proof_library_demo_config_dict(): return {"demo_id":"synthetic-proof-library-demo","name":"Synthetic Proof-Library Demo","version":"0.1","demo_kind":"SYNTHETIC","project_root":None,"discovery_request_path":None,"use_synthetic_request":True,"build_manifest":True,"run_allowlist_ingestion":True,"accept_verified_entries_in_memory":True,"allow_execution_default":False,"metadata":{"description":"Runs the full discovery -> manifest -> verifier-bound ingestion -> Lawbook replay flow on the repo-local synthetic Mathlib-style subset."}}
def default_real_mathlib_demo_config_dict(): return {"demo_id":"real-local-mathlib-demo-example","name":"Real Local Mathlib Demo Example","version":"0.1","demo_kind":"REAL_LOCAL_MATHLIB","project_root":"/path/to/local/mathlib/or/lean/project","module_files":[{"path":"Mathlib/Data/Nat/Basic.lean","module_name":"Mathlib.Data.Nat.Basic","max_declarations":5,"include_kinds":["theorem","lemma"],"name_contains":[],"exclude_name_contains":["deprecated","aux"]}],"selection_policy":{"max_total_declarations":5,"prefer_kinds":["theorem","lemma"]},"build_manifest":True,"run_allowlist_ingestion":False,"accept_verified_entries_in_memory":False,"allow_execution_default":False,"metadata":{"description":"Template only. Requires an already-working local Mathlib checkout. No downloads are performed."}}
def ensure_default_proof_library_demo_configs(root,*,overwrite=False):
 root=Path(root); root.mkdir(parents=True,exist_ok=True); a=root/"synthetic_demo_config.json"; b=root/"real_mathlib_demo_config.example.json"
 if overwrite or not a.exists(): _w(a,json.dumps(default_synthetic_proof_library_demo_config_dict(),indent=2)+"\n")
 if overwrite or not b.exists(): _w(b,json.dumps(default_real_mathlib_demo_config_dict(),indent=2)+"\n")
 return a,b
def load_proof_library_demo_config(path): return ProofLibraryDemoConfig.from_dict(json.loads(Path(path).read_text()))
def build_synthetic_proof_library_demo_config(): return ProofLibraryDemoConfig.from_dict(default_synthetic_proof_library_demo_config_dict())
def _request_from_config(c):
 if c.use_synthetic_request or c.demo_kind==ProofLibraryDemoKind.SYNTHETIC: return build_synthetic_mathlib_discovery_request()
 if c.discovery_request_path: return load_mathlib_discovery_request(c.discovery_request_path)
 source=MathlibDiscoverySourceKind.LOCAL_LEAN_PROJECT if c.demo_kind==ProofLibraryDemoKind.REAL_LOCAL_LEAN_PROJECT else MathlibDiscoverySourceKind.LOCAL_MATHLIB_PROJECT
 return MathlibDiscoveryRequest(f"{c.demo_id}-discovery",f"{c.name} discovery",source_kind=source,project_root=c.project_root,module_files=c.module_files,selection_policy=c.selection_policy)
def _stage(demo_id,stage,summary,status=ProofLibraryDemoStatus.COMPLETED,truth=ProofLibraryDemoTruthStatus.ADVISORY_ONLY,warnings=()): return ProofLibraryDemoStageResult(make_proof_library_demo_stage_id(demo_id,stage.value,summary),demo_id,stage,status,truth,dict(summary),warnings=tuple(warnings))
def run_proof_library_demo(config=None,*,out_dir=None,project_root=None,use_synthetic_request=None,allow_execution=False,allow_missing_verifier=True,run_allowlist_ingestion=None,accept_verified_entries_in_memory=None,timeout_sec=20.0,require_mathlib_marker=False):
 c=build_synthetic_proof_library_demo_config() if config is None else load_proof_library_demo_config(config) if isinstance(config,(str,Path)) else ProofLibraryDemoConfig.from_dict(dict(config)) if isinstance(config,Mapping) else config
 if project_root: c.project_root=str(Path(project_root).resolve())
 if use_synthetic_request is not None: c.use_synthetic_request=use_synthetic_request
 downstream=c.run_allowlist_ingestion if run_allowlist_ingestion is None else run_allowlist_ingestion; accept=c.accept_verified_entries_in_memory if accept_verified_entries_in_memory is None else accept_verified_entries_in_memory
 req=_request_from_config(c); dr=run_mathlib_declaration_discovery(req,project_root=c.project_root,build_manifest=c.build_manifest,run_allowlist_ingestion=downstream,allow_execution=allow_execution,allow_missing_verifier=allow_missing_verifier,timeout_sec=timeout_sec,accept_verified_entries_in_memory=accept,require_mathlib_marker=require_mathlib_marker); ar=dr.allowlist_ingestion_report; graph=mathlib_local_report_to_dependency_graph(ar) if ar else mathlib_discovery_report_to_reference_graph(dr); replay=dict(ar.lawbook_replay_summary) if ar else {}
 stages=[_stage(c.demo_id,ProofLibraryDemoStage.CONFIG,{"demo_kind":c.demo_kind.value}),_stage(c.demo_id,ProofLibraryDemoStage.ENVIRONMENT,{"environment_status":dr.environment_status.value},ProofLibraryDemoStatus.SKIPPED_ENVIRONMENT if dr.status.value=="SKIPPED_ENVIRONMENT" else ProofLibraryDemoStatus.COMPLETED,ProofLibraryDemoTruthStatus.SKIPPED_NO_ENVIRONMENT if dr.status.value=="SKIPPED_ENVIRONMENT" else ProofLibraryDemoTruthStatus.ADVISORY_ONLY),_stage(c.demo_id,ProofLibraryDemoStage.DISCOVERY,dr.summary),_stage(c.demo_id,ProofLibraryDemoStage.MANIFEST,{"generated_manifest_file_total":len(dr.generated_manifest.files) if dr.generated_manifest else 0}),_stage(c.demo_id,ProofLibraryDemoStage.ALLOWLIST_INGESTION,ar.summary if ar else {"run":False},truth=ProofLibraryDemoTruthStatus.BOUNDARY_EVIDENCE_PRESENT if ar and ar.verified_entry_count() else ProofLibraryDemoTruthStatus.ADVISORY_ONLY),_stage(c.demo_id,ProofLibraryDemoStage.LAWBOOK_REPLAY,replay,truth=ProofLibraryDemoTruthStatus.KNOWN_SKIP_AVAILABLE if replay.get("known_skip_total",0) else ProofLibraryDemoTruthStatus.ADVISORY_ONLY),_stage(c.demo_id,ProofLibraryDemoStage.DEPENDENCY_GRAPH,{"edge_total":len(graph.get("edges",()))}),_stage(c.demo_id,ProofLibraryDemoStage.REPORT,{})]
 truth=ProofLibraryDemoTruthStatus.KNOWN_SKIP_AVAILABLE if replay.get("known_skip_total",0) else ProofLibraryDemoTruthStatus.BOUNDARY_EVIDENCE_PRESENT if ar and ar.verified_entry_count() else ProofLibraryDemoTruthStatus.SKIPPED_NO_ENVIRONMENT if dr.status.value=="SKIPPED_ENVIRONMENT" else ProofLibraryDemoTruthStatus.ADVISORY_ONLY
 status=ProofLibraryDemoStatus.SKIPPED_ENVIRONMENT if dr.status.value=="SKIPPED_ENVIRONMENT" else ProofLibraryDemoStatus.COMPLETED_WITH_WARNINGS if dr.warnings else ProofLibraryDemoStatus.COMPLETED
 rep=ProofLibraryDemoReport(make_proof_library_demo_report_id(c.demo_id,dr.report_id,allow_execution,downstream,accept),c.demo_id,c,dr,dr.generated_manifest,ar,replay,graph,stages,status=status,truth_status=truth,warnings=dr.warnings,criticals=dr.criticals); rep.summarize()
 if out_dir: write_proof_library_demo_artifacts(rep,out_dir)
 return rep
def proof_library_demo_report_to_markdown(r):
 s=r.summarize(); mode="known-skip replay" if s["known_skip_total"] else "verifier-bound" if s["downstream_verified_total"] else "discovery-only"; dr=r.discovery_report; ar=r.allowlist_ingestion_report
 lines=["# Proof-Library Demo Pack","",f"- Demo: `{r.demo_id}`",f"- Created: `{r.created_at}`",f"- Demo kind: {r.config.demo_kind.value if r.config else ''}",f"- Mode: {mode}",f"- Environment: {dr.environment_status.value if dr else 'UNKNOWN'}",f"- Boundary status: {r.truth_status.value}","", "## Counts",f"- Modules: {s['module_total']}",f"- Declarations: {s['declaration_total']}",f"- Selected declarations: {s['selected_total']}",f"- Generated manifest files: {s['generated_manifest_file_total']}",f"- Verified entries: {s['downstream_verified_total']}",f"- Boundary evidence: {s['boundary_evidence_total']}",f"- Dependency edges: {s['dependency_edge_total']}",f"- Import edges: {s['import_edge_total']}",f"- Reference edges: {s['reference_edge_total']}",f"- Known skips: {s['known_skip_total']}","", "## What Was Discovered"]
 lines += [f"- `{m.module_name}`: {m.declaration_count} declarations, imports {', '.join(m.imports) or 'none'}" for m in (dr.modules if dr else [])] or ["- No modules discovered."]
 lines += ["", "## What Was Selected"]+[f"- `{d.full_name}` ({d.declaration_kind.value})" for d in (dr.declarations if dr else []) if d.selection_status.value=="SELECTED"]+["", "## Generated Allowlist Manifest",f"- Files: {s['generated_manifest_file_total']}","", "## What Crossed The Verifier Boundary"]
 lines += [f"- `{e.full_name}`" for e in (ar.entries if ar else []) if e.has_boundary_evidence()] or ["- Nothing crossed the verifier boundary."]
 lines += ["", "## What Was Rejected Or Stayed Advisory",f"- Unsafe verified: {s['unsafe_verified_total']}",f"- Expected-missing verified: {s['expected_missing_verified_total']}",f"- Import-failure verified: {s['import_failure_verified_total']}","", "## Dependency/Reference Graph Summary",f"- Edges: {s['dependency_edge_total']} total, {s['import_edge_total']} imports, {s['reference_edge_total']} references","", "## Lawbook Replay",f"- Candidates: {s['candidate_total']}",f"- Accepted in memory: {s['accepted_total']}",f"- Known skips: {s['known_skip_total']}","", "## Boundary Discipline","Discovery, generated manifests, dependency graphs, reports, and API success are advisory.","Only explicit verifier/importer/finite-validator/chain-audit evidence promotes truth.","", "## Next Recommended Action", "- Run the live verifier-bound demo if you want evidence-backed entries; supply a real local Mathlib config only after choosing explicit modules and declarations."]
 return "\n".join(lines)+"\n"
def proof_library_demo_report_to_dependency_graph(r): return dict(r.dependency_graph)
def write_proof_library_demo_artifacts(r,out_dir):
 out=Path(out_dir); paths={"config":out/"config.json","discovery_report":out/"discovery_report.json","generated_manifest":out/"generated_allowlist_manifest.json","allowlist_ingestion_report":out/"allowlist_ingestion_report.json","dependency_graph":out/"dependency_graph.json","demo_report":out/"demo_report.json","demo_markdown":out/"demo_report.md"}
 r.config.write_json(paths["config"])
 if r.discovery_report:r.discovery_report.write_json(paths["discovery_report"])
 if r.generated_manifest:r.generated_manifest.write_json(paths["generated_manifest"])
 if r.allowlist_ingestion_report:r.allowlist_ingestion_report.write_json(paths["allowlist_ingestion_report"])
 _w(paths["dependency_graph"],_j(r.dependency_graph)); r.write_json(paths["demo_report"]); _w(paths["demo_markdown"],proof_library_demo_report_to_markdown(r)); return {k:str(v) for k,v in paths.items() if v.exists()}
def proof_library_demo_report_to_api_response(r):
 from mathgraph.api_service import _resp
 req=ApiRequest(make_api_request_id("proof-library-demo",r.report_id),ApiRoute.PROOF_LIBRARY_DEMO); truth=ApiTruthStatus.KNOWN_SKIP_AVAILABLE if r.known_skip_count() else ApiTruthStatus.BOUNDARY_EVIDENCE_PRESENT if r.downstream_verified_count() else ApiTruthStatus.ADVISORY_ONLY; return _resp(req,route_result_from_artifacts(req.route,[r],truth_status=truth,safety=ApiSafetyLevel.SAFE_REVIEW_REQUIRED))
def _verified_entries(r): return [e for e in (r.allowlist_ingestion_report.entries if r.allowlist_ingestion_report else []) if e.has_boundary_evidence()]
def proof_library_demo_report_to_process_episodes(r): return [ProcessEpisodeRecord(make_process_episode_id("proof-library-demo",d.declaration_id),ProcessEpisodeStatus.TERMINAL_VERIFIED_PROOF if d.name in {e.name for e in _verified_entries(r)} else ProcessEpisodeStatus.ADVISORY_ONLY,contexts=[ProcessContextItem(content_id("proof-library-demo-context",d.declaration_id),ProcessContextKind.RAW_EVENT,ProcessContextRole.ADVISORY_ONLY,d.full_name)],terminal_form=TerminalForm.VERIFIED_PROOF if d.name in {e.name for e in _verified_entries(r)} else None,verifier_boundary_crossed=d.name in {e.name for e in _verified_entries(r)}) for d in (r.discovery_report.declarations if r.discovery_report else [])]
def proof_library_demo_report_to_discovery_value_scores(r):
 out=[]; names={e.name for e in _verified_entries(r)}
 for d in (r.discovery_report.declarations if r.discovery_report else []):
  sig=DiscoveryValueSignal(content_id("proof-library-demo-signal",d.declaration_id),DiscoveryValueSignalKind.REUSE_VALUE,1.0 if d.name in names else .1,source_object_kind=DiscoveryValueObjectKind.RAW_TASK); s=DiscoveryValueScore(content_id("proof-library-demo-score",d.declaration_id),d.declaration_id,DiscoveryValueObjectKind.RAW_TASK,signals=[sig]); s.recompute(); out.append(s)
 return out
def proof_library_demo_report_to_structural_identity_objects(r): return [{"object_id":d.declaration_id,"name":d.full_name,"kind":d.declaration_kind.value,"advisory":d.name not in {e.name for e in _verified_entries(r)}} for d in (r.discovery_report.declarations if r.discovery_report else [])]
def proof_library_demo_report_to_route_telemetry_events(r): return [{"event_id":content_id("proof-library-demo-telemetry",d.declaration_id),"route_kind":"proof_library_demo","outcome":d.selection_status.value,"verifier_boundary_crossed":d.name in {e.name for e in _verified_entries(r)}} for d in (r.discovery_report.declarations if r.discovery_report else [])]
def proof_library_demo_report_to_alchemical_trace(r):
 t=AlchemicalTrace(make_alchemical_trace_id("proof-library-demo",r.report_id))
 for p in (AlchemicalPhase.RAW_MATTER,AlchemicalPhase.CALCINATION,AlchemicalPhase.SOLUTION): t.add_step(phase=p,status=AlchemicalStatus.ADVISORY_ONLY)
 if r.allowlist_ingestion_report: t.add_step(phase=AlchemicalPhase.DESCENSION,status=AlchemicalStatus.ADVISORY_ONLY)
 if _verified_entries(r): t.add_step(phase=AlchemicalPhase.FIXATION,status=AlchemicalStatus.PROMOTED_BY_VERIFIER)
 for p in (AlchemicalPhase.DISTILLATION,AlchemicalPhase.COAGULATION): t.add_step(phase=p,status=AlchemicalStatus.ADVISORY_ONLY)
 return t
def proof_library_demo_report_to_agent_experiences(r): return [AgentExperience(content_id("proof-library-demo-exp",d.declaration_id),"proof-library-demo",None,None,"project",None,AgentExperienceOutcome.VERIFIED_PROOF if d.name in {e.name for e in _verified_entries(r)} else AgentExperienceOutcome.ADVISORY_ONLY,terminal_form=TerminalForm.VERIFIED_PROOF if d.name in {e.name for e in _verified_entries(r)} else None,verifier_boundary_crossed=d.name in {e.name for e in _verified_entries(r)}) for d in (r.discovery_report.declarations if r.discovery_report else [])]
def audit_proof_library_demo_config(x): return [_af("CRITICAL","PROOF_LIBRARY_DEMO_CONFIG_NON_ADVISORY","config non-advisory",x.demo_id)] if not x.advisory else []
def audit_proof_library_demo_stage_result(x): return [_af("CRITICAL","PROOF_LIBRARY_DEMO_STAGE_NON_ADVISORY","stage non-advisory",x.stage_id)] if not x.advisory else []
def audit_proof_library_demo_report(x):
 out=[]
 if not x.advisory: out.append(_af("CRITICAL","PROOF_LIBRARY_DEMO_REPORT_NON_ADVISORY","report non-advisory",x.report_id))
 if x.truth_status!=ProofLibraryDemoTruthStatus.ADVISORY_ONLY and not x.allowlist_ingestion_report: out.append(_af("CRITICAL","PROOF_LIBRARY_DEMO_DISCOVERY_ONLY_PROOF","discovery-only demo claims proof",x.report_id))
 if x.known_skip_count() and not x.lawbook_replay_summary.get("accepted_total",0): out.append(_af("CRITICAL","PROOF_LIBRARY_DEMO_SKIP_WITHOUT_ACCEPTANCE","known skip without accepted replay",x.report_id))
 s=x.summarize()
 if any(s[k] for k in ("unsafe_verified_total","expected_missing_verified_total","import_failure_verified_total")): out.append(_af("CRITICAL","PROOF_LIBRARY_DEMO_FAILED_ENTRY_VERIFIED","failed entry verified",x.report_id))
 if x.ok() and x.critical_count(): out.append(_af("CRITICAL","PROOF_LIBRARY_DEMO_OK_WITH_CRITICAL","report hides criticals",x.report_id))
 return out
def _af(sev,code,msg,obj): return {"severity":sev,"code":code,"message":msg,"object_id":obj}
def _now(): return datetime.now(timezone.utc).isoformat()
def _j(x): return json.dumps(x,sort_keys=True,separators=(",",":"),default=str)
def _w(p,t): path=Path(p); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(t,encoding="utf-8")
