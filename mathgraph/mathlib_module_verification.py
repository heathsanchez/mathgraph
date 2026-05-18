"""Module-aware local Mathlib declaration availability checks via import/#check."""
from __future__ import annotations
import json,os,tempfile
from dataclasses import MISSING,dataclass,field
from datetime import datetime,timezone
from enum import Enum
from hashlib import sha256
from pathlib import Path
from typing import Any,Mapping
from mathgraph.agent_biography import AgentExperience,AgentExperienceOutcome
from mathgraph.alchemy import AlchemicalPhase,AlchemicalStatus,AlchemicalTrace,make_alchemical_trace_id
from mathgraph.api_service import ApiRequest,ApiRoute,ApiSafetyLevel,ApiTruthStatus,make_api_request_id,route_result_from_artifacts
from mathgraph.certificates import TerminalForm
from mathgraph.discovery_value import DiscoveryValueObjectKind,DiscoveryValueScore,DiscoveryValueSignal,DiscoveryValueSignalKind
from mathgraph.hashing import content_id
from mathgraph.lawbook import LawbookAcceptanceBoundary,LawbookEntry,LawbookEntryKind,LawbookEntryStatus,LawbookStore,accept_lawbook_entry,make_lawbook_entry_id,make_lawbook_store_id,review_lawbook_candidate
from mathgraph.lawbook_query import query_lawbook_store_by_certificate
from mathgraph.mathlib_local_allowlist import MathlibLocalAllowlistManifest
from mathgraph.process_memory import ProcessContextItem,ProcessContextKind,ProcessContextRole,ProcessEpisodeRecord,ProcessEpisodeStatus,make_process_episode_id
from mathgraph.verifier_execution import *
def _enum(n,v): return Enum(n,{x:x for x in v.split()},type=str)
MathlibModuleVerificationStatus=_enum("MathlibModuleVerificationStatus","NOT_RUN COMPLETED COMPLETED_WITH_WARNINGS SKIPPED_ENVIRONMENT SKIPPED_MISSING_VERIFIER FAILED_CHECK FAILED_EXPECTED_DECLARATION FAILED_UNSAFE ERROR UNKNOWN")
MathlibModuleVerificationTruthStatus=_enum("MathlibModuleVerificationTruthStatus","ADVISORY_ONLY BOUNDARY_EVIDENCE_PRESENT KNOWN_SKIP_AVAILABLE SKIPPED_NO_ENVIRONMENT SKIPPED_NO_VERIFIER UNKNOWN")
MathlibModuleVerificationFailureKind=_enum("MathlibModuleVerificationFailureKind","NONE MISSING_PROJECT_ROOT MISSING_LEAN MISSING_MODULE EMPTY_DECLARATION_SELECTION UNSAFE_MARKER CHECK_FILE_WRITE_FAILED CHECK_FAILED EXPECTED_DECLARATION_MISSING IMPORT_ERROR TYPE_ERROR TIMEOUT NONZERO_EXIT EXECUTION_DISABLED SAFETY_BLOCKED UNKNOWN")
MathlibModuleVerificationCheckMode=_enum("MathlibModuleVerificationCheckMode","CHECK_DECLARATION CHECK_DECLARATION_TYPE IMPORT_ONLY UNKNOWN")
MathlibModuleVerificationRisk=_enum("MathlibModuleVerificationRisk","SAFE DISCOVERY_ONLY IMPORT_CHECK_ONLY MISSING_ENVIRONMENT MISSING_VERIFIER GENERATED_CHECK_FILE UNKNOWN")
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
class MathlibModuleCheckTarget:
 target_id:str; module_name:str; module_path:str|None=None; declaration_names:tuple[str,...]=(); check_mode:MathlibModuleVerificationCheckMode=MathlibModuleVerificationCheckMode.CHECK_DECLARATION; namespace:str|None=None; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
@_serial
@dataclass
class MathlibModuleVerificationRequest:
 request_id:str; project_root:str|None=None; targets:list[MathlibModuleCheckTarget]=field(default_factory=list); expected_revision:str|None=None; expected_lean_toolchain:str|None=None; allow_execution_default:bool=False; accept_verified_entries_in_memory:bool=False; require_mathlib_marker:bool=True; workspace_root:str|None=None; enable_name_candidate_fallback:bool=False; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def write_json(self,p): _w(p,self.to_json())
 @classmethod
 def read_json(c,p): return c.from_json(Path(p).read_text())
@_serial
@dataclass
class MathlibModuleCheckFile:
 check_file_id:str; request_id:str; target_id:str; project_root:str; module_name:str; declaration_names:tuple[str,...]; check_file_path:str; check_file_text:str; check_mode:MathlibModuleVerificationCheckMode; unsafe_markers:tuple[str,...]=(); expected_check_lines:tuple[str,...]=(); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
@dataclass
class MathlibModuleDeclarationResult:
 declaration_result_id:str; request_id:str; target_id:str; module_name:str; declaration_name:str; status:MathlibModuleVerificationStatus=MathlibModuleVerificationStatus.UNKNOWN; truth_status:MathlibModuleVerificationTruthStatus=MathlibModuleVerificationTruthStatus.ADVISORY_ONLY; failure_kind:MathlibModuleVerificationFailureKind=MathlibModuleVerificationFailureKind.NONE; boundary_evidence:list[Any]=field(default_factory=list); verifier_execution_result:Any|None=None; verified:bool=False; known_skip:bool=False; warnings:tuple[str,...]=(); criticals:tuple[str,...]=(); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def ok(self): return not self.criticals and self.failure_kind==MathlibModuleVerificationFailureKind.NONE
 def to_dict(self): return {**self.__dict__,"status":self.status.value,"truth_status":self.truth_status.value,"failure_kind":self.failure_kind.value,"boundary_evidence":[x.to_dict() if hasattr(x,"to_dict") else x for x in self.boundary_evidence],"verifier_execution_result":self.verifier_execution_result.to_dict() if hasattr(self.verifier_execution_result,"to_dict") else self.verifier_execution_result,"warnings":list(self.warnings),"criticals":list(self.criticals)}
 @classmethod
 def from_dict(c,d): return c(str(d["declaration_result_id"]),str(d["request_id"]),str(d["target_id"]),str(d["module_name"]),str(d["declaration_name"]),MathlibModuleVerificationStatus(str(d.get("status","UNKNOWN"))),MathlibModuleVerificationTruthStatus(str(d.get("truth_status","ADVISORY_ONLY"))),MathlibModuleVerificationFailureKind(str(d.get("failure_kind","NONE"))),[VerifierBoundaryEvidence.from_dict(x) if isinstance(x,dict) else x for x in d.get("boundary_evidence",())],VerifierExecutionResult.from_dict(d["verifier_execution_result"]) if d.get("verifier_execution_result") else None,bool(d.get("verified",False)),bool(d.get("known_skip",False)),tuple(d.get("warnings",())),tuple(d.get("criticals",())),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
@dataclass
class MathlibModuleVerificationReport:
 report_id:str; request_id:str; request:MathlibModuleVerificationRequest|None=None; environment_report:Any|None=None; check_files:list[MathlibModuleCheckFile]=field(default_factory=list); declaration_results:list[MathlibModuleDeclarationResult]=field(default_factory=list); verifier_execution_reports:list[Any]=field(default_factory=list); lawbook_replay_summary:dict[str,Any]=field(default_factory=dict); created_at:str=field(default_factory=lambda:_now()); status:MathlibModuleVerificationStatus=MathlibModuleVerificationStatus.UNKNOWN; truth_status:MathlibModuleVerificationTruthStatus=MathlibModuleVerificationTruthStatus.UNKNOWN; summary:dict[str,Any]=field(default_factory=dict); warnings:tuple[str,...]=(); criticals:tuple[str,...]=(); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def target_count(self): return len(self.request.targets) if self.request else 0
 def declaration_count(self): return len(self.declaration_results)
 def verified_count(self): return sum(x.verified for x in self.declaration_results)
 def boundary_evidence_count(self): return sum(len(x.boundary_evidence) for x in self.declaration_results)
 def known_skip_count(self): return sum(x.known_skip for x in self.declaration_results)
 def unresolved_count(self): return sum(not x.verified for x in self.declaration_results)
 def fallback_verified_count(self): return sum(x.verified and x.metadata.get("name_resolution_mode")=="candidate_fallback" for x in self.declaration_results)
 def check_file_count(self): return len(self.check_files)
 def warning_count(self): return len(self.warnings)
 def critical_count(self): return len(self.criticals)
 def summarize(self):
  self.summary={"target_total":self.target_count(),"declaration_total":self.declaration_count(),"verified_total":self.verified_count(),"boundary_evidence_total":self.boundary_evidence_count(),"known_skip_total":self.known_skip_count(),"unresolved_total":self.unresolved_count(),"fallback_verified_total":self.fallback_verified_count(),"check_file_total":self.check_file_count(),"warning_total":self.warning_count(),"critical_total":self.critical_count()}; return self.summary
 def ok(self): return not self.critical_count() and not any((x.failure_kind!=MathlibModuleVerificationFailureKind.NONE or not x.verified) and x.boundary_evidence for x in self.declaration_results) and not any(f.unsafe_markers and any(r.target_id==f.target_id and r.boundary_evidence for r in self.declaration_results) for f in self.check_files)
 def to_dict(self): return {**self.__dict__,"request":self.request.to_dict() if self.request else None,"environment_report":self.environment_report.to_dict() if hasattr(self.environment_report,"to_dict") else self.environment_report,"check_files":[x.to_dict() for x in self.check_files],"declaration_results":[x.to_dict() for x in self.declaration_results],"verifier_execution_reports":[x.to_dict() if hasattr(x,"to_dict") else x for x in self.verifier_execution_reports],"status":self.status.value,"truth_status":self.truth_status.value,"warnings":list(self.warnings),"criticals":list(self.criticals)}
 @classmethod
 def from_dict(c,d):
  from mathgraph.real_mathlib_demo import RealMathlibEnvironmentReport
  return c(str(d["report_id"]),str(d["request_id"]),MathlibModuleVerificationRequest.from_dict(d["request"]) if d.get("request") else None,RealMathlibEnvironmentReport.from_dict(d["environment_report"]) if d.get("environment_report") else None,[MathlibModuleCheckFile.from_dict(x) for x in d.get("check_files",())],[MathlibModuleDeclarationResult.from_dict(x) for x in d.get("declaration_results",())],[VerifierExecutionReport.from_dict(x) for x in d.get("verifier_execution_reports",())],dict(d.get("lawbook_replay_summary",{})),str(d.get("created_at",_now())),MathlibModuleVerificationStatus(str(d.get("status","UNKNOWN"))),MathlibModuleVerificationTruthStatus(str(d.get("truth_status","UNKNOWN"))),dict(d.get("summary",{})),tuple(d.get("warnings",())),tuple(d.get("criticals",())),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
 def write_json(self,p): _w(p,self.to_json())
 @classmethod
 def read_json(c,p): return c.from_json(Path(p).read_text())
 def write_jsonl(self,p): _w(p,self.to_json()+"\n")
 @classmethod
 def read_jsonl(c,p): return [c.from_json(x) for x in Path(p).read_text().splitlines() if x.strip()]
for _c,_e in [(MathlibModuleCheckTarget,("check_mode",)),(MathlibModuleVerificationRequest,()),(MathlibModuleCheckFile,("check_mode",))]: _serial(_c,_e)
def make_mathlib_module_check_target_id(*x): return content_id("mathlib-module-check-target",x)
def make_mathlib_module_verification_request_id(*x): return content_id("mathlib-module-verification-request",x)
def make_mathlib_module_check_file_id(*x): return content_id("mathlib-module-check-file",x)
def make_mathlib_module_declaration_result_id(*x): return content_id("mathlib-module-declaration-result",x)
def make_mathlib_module_verification_report_id(*x): return content_id("mathlib-module-verification-report",x)
def _target_from_dict(c,d):
 names=tuple(d.get("declaration_names") or ()); mode=d.get("check_mode",MathlibModuleVerificationCheckMode.CHECK_DECLARATION.value)
 try: mode=mode if isinstance(mode,MathlibModuleVerificationCheckMode) else MathlibModuleVerificationCheckMode(str(mode))
 except ValueError: mode=MathlibModuleVerificationCheckMode.CHECK_DECLARATION
 module=str(d.get("module_name","")); path=d.get("module_path"); tid=d.get("target_id") or make_mathlib_module_check_target_id(module,path,names)
 return c(str(tid),module,path,names,mode,d.get("namespace"),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
def _request_from_dict(c,d):
 ts=[MathlibModuleCheckTarget.from_dict(x) if isinstance(x,dict) else x for x in d.get("targets",()) or ()]; md=dict(d.get("metadata",{})); rid=d.get("request_id") or make_mathlib_module_verification_request_id(d.get("project_root"),[x.to_dict() for x in ts],md)
 return c(str(rid),d.get("project_root"),ts,d.get("expected_revision"),d.get("expected_lean_toolchain"),bool(d.get("allow_execution_default",False)),bool(d.get("accept_verified_entries_in_memory",False)),bool(d.get("require_mathlib_marker",True)),d.get("workspace_root"),bool(d.get("enable_name_candidate_fallback",False)),md,bool(d.get("advisory",True)))
MathlibModuleCheckTarget.from_dict=classmethod(_target_from_dict); MathlibModuleVerificationRequest.from_dict=classmethod(_request_from_dict)
def generate_module_check_file_text(t,*,header=None):
 lines=[header.rstrip()] if header else []; lines+=([f"import {t.module_name}",""] if t.module_name else [])
 if t.check_mode!=MathlibModuleVerificationCheckMode.IMPORT_ONLY: lines += [f"#check {x}" for x in t.declaration_names]
 return "\n".join(lines).rstrip()+"\n"
def extract_check_file_unsafe_markers(text): return extract_unsafe_markers(text)
def generate_declaration_name_candidates(declaration_name,*,module_name=None):
 last=declaration_name.split(".")[-1] if declaration_name else ""; xs=[declaration_name,last]
 if module_name and last:
  parent=".".join(module_name.split(".")[:-1]); xs.append(f"{parent}.{last}" if parent else last)
 if declaration_name=="Mathlib.succ_injective" or last=="succ_injective":
  xs+=["Nat.succ_injective","Nat.succ.inj","Nat.succ.injEq"]
 return tuple(dict.fromkeys(x for x in xs if x))
def write_module_check_file(request,target,*,workspace_root):
 root=Path(workspace_root).resolve(); root.mkdir(parents=True,exist_ok=True); text=generate_module_check_file_text(target); p=root/f"MathGraphModuleCheck_{_hash((request.request_id,target.target_id))[:16]}.lean"; p.write_text(text,encoding="utf-8"); expected=tuple(f"#check {x}" for x in target.declaration_names)
 return MathlibModuleCheckFile(make_mathlib_module_check_file_id(request.request_id,target.target_id),request.request_id,target.target_id,str(Path(request.project_root or ".").resolve()),target.module_name,tuple(target.declaration_names),str(p),text,target.check_mode,extract_check_file_unsafe_markers(text),expected)
def build_module_verification_request_from_real_demo_report(report,*,selected_only=True):
 ds=[d for d in (report.discovery_report.declarations if report.discovery_report else []) if not selected_only or d.selection_status.value=="SELECTED"]; by={}
 for d in ds:
  full=d.full_name
  if full.count(".")<d.module_name.count("."): full=".".join([*d.module_name.split(".")[:-1],d.name])
  by.setdefault(d.module_name,[]).append(full)
 paths={m.module_name:m.path for m in (report.discovery_report.modules if report.discovery_report else [])}
 ts=[MathlibModuleCheckTarget(make_mathlib_module_check_target_id(report.demo_id,m),m,paths.get(m),tuple(ns)) for m,ns in by.items()]
 env=report.environment_report; return MathlibModuleVerificationRequest(make_mathlib_module_verification_request_id(report.report_id),env.project_root if env else None,ts,getattr(env,"detected_revision",None),getattr(env,"detected_lean_toolchain",None),metadata={"real_mathlib_demo_report_id":report.report_id})
def build_module_verification_request_from_allowlist_manifest(m):
 return MathlibModuleVerificationRequest(make_mathlib_module_verification_request_id(m.manifest_id),m.project_root,[MathlibModuleCheckTarget(make_mathlib_module_check_target_id(m.manifest_id,x.get("module_name")),x.get("module_name",""),x.get("path"),tuple(x.get("expected_declaration_names",()))) for x in m.files],m.pinned_revision,m.lean_toolchain)
def default_synthetic_module_verification_request(project_root):
 root=str(Path(project_root).resolve()); return MathlibModuleVerificationRequest("synthetic-mathlib-module-verification",root,[MathlibModuleCheckTarget("synthetic-basic","Mathlib.MathGraph.Basic","Mathlib/MathGraph/Basic.lean",("Mathlib.MathGraph.mgml_true","Mathlib.MathGraph.mgml_identity")),MathlibModuleCheckTarget("synthetic-logic","Mathlib.MathGraph.Logic","Mathlib/MathGraph/Logic.lean",("Mathlib.MathGraph.mgml_and_comm","Mathlib.MathGraph.mgml_imp_trans"))],require_mathlib_marker=True)
def ensure_module_verification_examples(root,overwrite=False):
 root=Path(root); root.mkdir(parents=True,exist_ok=True); a=root/"module_check_request.example.json"; b=root/"synthetic_module_check_request.json"
 real=MathlibModuleVerificationRequest("example-real-mathlib-module-check","/path/to/mathlib4",[MathlibModuleCheckTarget("example-nat-basic","Mathlib.Data.Nat.Basic","Mathlib/Data/Nat/Basic.lean",("Mathlib.succ_injective","Mathlib.pow_left_injective"))])
 syn=default_synthetic_module_verification_request(Path(__file__).resolve().parents[1]/"examples"/"mathlib_micro_subset"); syn.project_root="../mathlib_micro_subset"
 if overwrite or not a.exists(): real.write_json(a)
 if overwrite or not b.exists(): syn.write_json(b)
 return [a,b]
def run_mathlib_module_verification(request,*,project_root=None,workspace_root=None,allow_execution=False,allow_missing_verifier=True,accept_verified_entries_in_memory=None,enable_name_candidate_fallback=None,timeout_sec=20.0):
 q=_req(request); 
 if project_root: q.project_root=str(Path(project_root).resolve())
 from mathgraph.real_mathlib_demo import RealMathlibDemoConfig,RealMathlibEnvironmentStatus,detect_real_mathlib_demo_environment
 cfg=RealMathlibDemoConfig(q.request_id,"Module-aware verification",project_root=q.project_root,expected_revision=q.expected_revision,expected_lean_toolchain=q.expected_lean_toolchain,require_mathlib_marker=q.require_mathlib_marker,discovery_modules=[{"path":t.module_path or "/".join(t.module_name.split("."))+".lean"} for t in q.targets])
 env=detect_real_mathlib_demo_environment(cfg,project_root=q.project_root); root=Path(q.project_root or "."); warnings=list(env.warnings); criticals=[]; rs=[]
 if env.status in {RealMathlibEnvironmentStatus.MISSING_PROJECT_ROOT,RealMathlibEnvironmentStatus.MISSING_SELECTED_MODULES,RealMathlibEnvironmentStatus.MISSING_MATHLIB_MARKER}:
  r=MathlibModuleVerificationReport(make_mathlib_module_verification_report_id(q.request_id,env.status.value),q.request_id,q,env,status=MathlibModuleVerificationStatus.SKIPPED_ENVIRONMENT,truth_status=MathlibModuleVerificationTruthStatus.SKIPPED_NO_ENVIRONMENT,warnings=tuple(warnings)); r.summarize(); return r
 wr=Path(workspace_root or q.workspace_root or Path(tempfile.gettempdir())/"mathgraph_module_verification_tmp").resolve()
 files=[write_module_check_file(q,t,workspace_root=wr) for t in q.targets]
 for t in q.targets:
  for n in t.declaration_names: rs.append(MathlibModuleDeclarationResult(make_mathlib_module_declaration_result_id(q.request_id,t.target_id,n),q.request_id,t.target_id,t.module_name,n,status=MathlibModuleVerificationStatus.COMPLETED_WITH_WARNINGS if not allow_execution else MathlibModuleVerificationStatus.UNKNOWN,failure_kind=MathlibModuleVerificationFailureKind.EXECUTION_DISABLED if not allow_execution else MathlibModuleVerificationFailureKind.NONE))
 if not q.targets or not rs:
  r=MathlibModuleVerificationReport(make_mathlib_module_verification_report_id(q.request_id,"empty"),q.request_id,q,env,files,rs,status=MathlibModuleVerificationStatus.COMPLETED_WITH_WARNINGS,truth_status=MathlibModuleVerificationTruthStatus.ADVISORY_ONLY,warnings=tuple([*warnings,"no selected declarations"])); r.summarize(); return r
 contracts=[]; vreps=[]
 if allow_execution:
  build_root=wr/"olean"
  for t in q.targets:
   src=root/(t.module_path or "/".join(t.module_name.split("."))+".lean"); out=build_root.joinpath(*t.module_name.split(".")).with_suffix(".olean")
   if src.exists() and not root.joinpath(*t.module_name.split(".")).with_suffix(".olean").exists():
    out.parent.mkdir(parents=True,exist_ok=True); safe_root=os.path.commonpath([str(root.resolve()),str(out.resolve())]); contracts.append(VerifierCommandContract(make_verifier_command_contract_id(q.request_id,t.target_id,"prepare"),VerifierSystemKind.LEAN,VerifierExecutionMode.CHECK_FILE,("lean","-o",str(out),str(src.resolve())),str(root.resolve()),str(src.resolve()),_hash(src.read_text()),timeout_sec,True,False,False,safe_root,(),{"lean_path":os.pathsep.join([str(build_root),str(root.resolve())]),"module_aware_prepare":True}))
  for f in files:
   safe_root=os.path.commonpath([str(root.resolve()),f.check_file_path])
   contracts.append(VerifierCommandContract(make_verifier_command_contract_id(q.request_id,f.target_id),VerifierSystemKind.LEAN,VerifierExecutionMode.CHECK_FILE,("lean",f.check_file_path),str(root.resolve()),f.check_file_path,_hash(f.check_file_text),timeout_sec,True,False,False,safe_root,f.declaration_names,{"lean_path":os.pathsep.join([str(build_root),str(root.resolve())]),"module_aware_import_check":True}))
  vr=build_verifier_execution_report(contracts=contracts,allow_execution=True,timeout_sec=timeout_sec); vreps.append(vr)
  if env.status==RealMathlibEnvironmentStatus.MISSING_LEAN and allow_missing_verifier:
   for x in rs: x.status=MathlibModuleVerificationStatus.SKIPPED_MISSING_VERIFIER; x.truth_status=MathlibModuleVerificationTruthStatus.SKIPPED_NO_VERIFIER; x.failure_kind=MathlibModuleVerificationFailureKind.MISSING_LEAN
  elif env.status==RealMathlibEnvironmentStatus.MISSING_LEAN:
   criticals.append("lean missing")
   for x in rs: x.status=MathlibModuleVerificationStatus.FAILED_CHECK; x.failure_kind=MathlibModuleVerificationFailureKind.MISSING_LEAN; x.criticals=("lean missing",)
  else:
   for t,f,res in zip(q.targets,files,vr.results[-len(files):]):
    good=res.status==VerifierExecutionStatus.SUCCESS and res.returncode==0 and not f.unsafe_markers and all(x in f.check_file_text for x in f.expected_check_lines) and not _has_check_error(res)
    fk=_result_failure(res)
    for x in [z for z in rs if z.target_id==t.target_id]:
     x.verifier_execution_result=res
     if good:
      ev=create_module_check_boundary_evidence(request=q,target=t,declaration_name=x.declaration_name,check_file=f,verifier_execution_result=res,environment_report=env); x.boundary_evidence=[ev]; x.verified=True; x.status=MathlibModuleVerificationStatus.COMPLETED; x.truth_status=MathlibModuleVerificationTruthStatus.BOUNDARY_EVIDENCE_PRESENT; x.metadata=dict(ev.metadata)
     else:
      x.status=MathlibModuleVerificationStatus.FAILED_CHECK; x.failure_kind=fk; x.metadata.update(_failed_diag(t,f,res,x.declaration_name))
   fallback=q.enable_name_candidate_fallback if enable_name_candidate_fallback is None else enable_name_candidate_fallback
   if fallback:
    for x in [z for z in rs if not z.verified]:
     t=next(a for a in q.targets if a.target_id==x.target_id); candidates=generate_declaration_name_candidates(x.declaration_name,module_name=t.module_name); x.metadata["possible_name_candidates"]=list(candidates); successes=[]
     for cand in candidates:
      if cand==x.declaration_name: continue
      ft=MathlibModuleCheckTarget(make_mathlib_module_check_target_id(t.target_id,"fallback",cand),t.module_name,t.module_path,(cand,),t.check_mode,t.namespace,{"original_declaration_name":x.declaration_name})
      ff=write_module_check_file(q,ft,workspace_root=wr); files.append(ff); safe_root=os.path.commonpath([str(root.resolve()),ff.check_file_path]); c=VerifierCommandContract(make_verifier_command_contract_id(q.request_id,ft.target_id),VerifierSystemKind.LEAN,VerifierExecutionMode.CHECK_FILE,("lean",ff.check_file_path),str(root.resolve()),ff.check_file_path,_hash(ff.check_file_text),timeout_sec,True,False,False,safe_root,(cand,),{"lean_path":os.pathsep.join([str(build_root),str(root.resolve())]),"module_aware_import_check":True,"name_resolution_mode":"candidate_fallback"})
      fr=build_verifier_execution_report(contracts=[c],allow_execution=True,timeout_sec=timeout_sec); vreps.append(fr); rr=fr.results[0]; ok=rr.status==VerifierExecutionStatus.SUCCESS and rr.returncode==0 and not ff.unsafe_markers and not _has_check_error(rr)
      if ok: successes.append((cand,ff,rr))
     if successes:
      cand,ff,rr=successes[0]; ev=create_module_check_boundary_evidence(request=q,target=t,declaration_name=cand,original_declaration_name=x.declaration_name,check_file=ff,verifier_execution_result=rr,environment_report=env,name_resolution_mode="candidate_fallback",alternative_candidates=tuple(a[0] for a in successes[1:])); x.boundary_evidence=[ev]; x.verifier_execution_result=rr; x.verified=True; x.failure_kind=MathlibModuleVerificationFailureKind.NONE; x.status=MathlibModuleVerificationStatus.COMPLETED; x.truth_status=MathlibModuleVerificationTruthStatus.BOUNDARY_EVIDENCE_PRESENT; x.metadata={**x.metadata,**ev.metadata}
 accept=q.accept_verified_entries_in_memory if accept_verified_entries_in_memory is None else accept_verified_entries_in_memory
 replay=review_and_optionally_accept_mathlib_module_results(rs,accept_in_memory=accept); accepted={x["certificate_id"] for x in replay.get("accepted",())}
 for x in rs:
  if x.verified and x.boundary_evidence and x.boundary_evidence[0].certificate_id in accepted: x.known_skip=True; x.truth_status=MathlibModuleVerificationTruthStatus.KNOWN_SKIP_AVAILABLE
 truth=MathlibModuleVerificationTruthStatus.KNOWN_SKIP_AVAILABLE if any(x.known_skip for x in rs) else MathlibModuleVerificationTruthStatus.BOUNDARY_EVIDENCE_PRESENT if any(x.verified for x in rs) else MathlibModuleVerificationTruthStatus.SKIPPED_NO_VERIFIER if allow_execution and env.status==RealMathlibEnvironmentStatus.MISSING_LEAN else MathlibModuleVerificationTruthStatus.ADVISORY_ONLY
 status=MathlibModuleVerificationStatus.SKIPPED_MISSING_VERIFIER if truth==MathlibModuleVerificationTruthStatus.SKIPPED_NO_VERIFIER else MathlibModuleVerificationStatus.FAILED_CHECK if criticals or (allow_execution and rs and not any(x.verified for x in rs)) else MathlibModuleVerificationStatus.COMPLETED_WITH_WARNINGS if warnings or not allow_execution else MathlibModuleVerificationStatus.COMPLETED
 r=MathlibModuleVerificationReport(make_mathlib_module_verification_report_id(q.request_id,allow_execution,[f.check_file_id for f in files]),q.request_id,q,env,files,rs,vreps,{k:v for k,v in replay.items() if k!="accepted"},status=status,truth_status=truth,warnings=tuple(warnings),criticals=tuple(criticals)); r.summarize(); return r
def create_module_check_boundary_evidence(*,request,target,declaration_name,check_file,verifier_execution_result,environment_report,original_declaration_name=None,name_resolution_mode="explicit_original",alternative_candidates=()):
 original=original_declaration_name or declaration_name; cert=content_id("module-aware-import-check-certificate",(request.request_id,target.target_id,original,declaration_name,check_file.check_file_text)); md={"module_name":target.module_name,"declaration_name":declaration_name,"original_declaration_name":original,"resolved_declaration_name":declaration_name,"name_resolution_mode":name_resolution_mode,"alternative_candidates":list(alternative_candidates),"project_root":request.project_root,"detected_revision":getattr(environment_report,"detected_revision",None),"detected_lean_toolchain":getattr(environment_report,"detected_lean_toolchain",None),"boundary_kind":"module_aware_import_check","check_mode":"#check","proof_rechecked_from_source":False}
 return VerifierBoundaryEvidence(make_verifier_boundary_evidence_id("module-aware",cert),VerifierEvidenceKind.LOCAL_VERIFIER_ACCEPTED,VerifierSystemKind.LEAN,verifier_execution_result.result_id,cert,TerminalForm.VERIFIED_PROOF.value,(declaration_name,),True,_hash(check_file.check_file_text),_hash(check_file.check_file_path),metadata=md)
def mathlib_module_verification_report_to_lawbook_candidates(r): return [LawbookEntry(make_lawbook_entry_id("mathlib-module-verification",x.declaration_result_id),LawbookEntryKind.VERIFIED_PROOF_ENTRY,LawbookEntryStatus.CANDIDATE,claim_id=x.declaration_name,terminal_form=TerminalForm.VERIFIED_PROOF,certificate_id=x.boundary_evidence[0].certificate_id,verifier_boundary_crossed=True,acceptance_boundary=LawbookAcceptanceBoundary.VERIFIED_PROOF,metadata={"boundary_kind":"module_aware_import_check","proof_rechecked_from_source":False}) for x in r.declaration_results if x.verified and x.boundary_evidence]
def review_and_optionally_accept_mathlib_module_results(rs,*,accept_in_memory=False):
 fake=type("R",(),{"declaration_results":rs})(); cs=mathlib_module_verification_report_to_lawbook_candidates(fake); reviews=[review_lawbook_candidate(x) for x in cs]; accepted=[accept_lawbook_entry(e,v,accepted_by="mathlib-module-verification-replay") for e,v in zip(cs,reviews) if accept_in_memory and v.decision.value=="ACCEPT"]; store=LawbookStore(make_lawbook_store_id("mathlib-module-verification-replay",[x.entry_id for x in accepted]),entries=accepted,reviews=reviews); answers=[query_lawbook_store_by_certificate(store,x.certificate_id) for x in cs if x.certificate_id]
 return {"candidate_total":len(cs),"review_total":len(reviews),"accepted_total":len(accepted),"query_total":len(answers),"known_skip_total":sum(a.known_skip_decision.value.startswith("SKIP_") for a in answers),"accepted":[{"certificate_id":x.certificate_id} for x in accepted]}
def mathlib_module_verification_report_to_markdown(r):
 s=r.summarize(); e=r.environment_report; lines=["# Mathlib Module-Aware Verification Report","",f"- Project root: {getattr(e,'project_root','')}",f"- Revision: {getattr(e,'detected_revision','')}",f"- Toolchain: {getattr(e,'detected_lean_toolchain','')}",f"- Check mode: `#check`",f"- Targets: {s['target_total']}",f"- Declarations: {s['declaration_total']}",f"- Verified: {s['verified_total']}",f"- Boundary evidence: {s['boundary_evidence_total']}",f"- Known skips: {s['known_skip_total']}","", "## Targets"]+[f"- `{t.module_name}`: {', '.join(t.declaration_names)}" for t in (r.request.targets if r.request else [])]+["", "## Generated Check Files"]+[f"- `{f.check_file_path}`" for f in r.check_files]+["", "## Declaration Results"]+[f"- `{x.declaration_name}`: {x.status.value}" for x in r.declaration_results]+["", "## What Crossed The Verifier Boundary"]
 lines += [f"- `{x.declaration_name}` imported from `{x.module_name}`" for x in r.declaration_results if x.verified] or ["- Nothing crossed the verifier boundary."]
 lines += ["", "## Failed Check Diagnostics"]
 for d in failed_check_diagnostics(r): lines += [f"- Module: `{d['module_name']}`",f"  - Failed declarations: {', '.join(d['failed_expected_declarations'])}",f"  - Check file: `{d['check_file_path']}`",f"  - Failure kind: {d['failure_kind']}",f"  - stderr tail: `{d['lean_stderr_tail']}`",f"  - Candidate spellings: {', '.join(d['possible_name_candidates']) or 'none'}"]
 if not failed_check_diagnostics(r): lines += ["- None."]
 lines += ["", "## What Stayed Advisory","- Project paths, generated check files, requests, reports, candidate diagnostics, and dry-runs stay advisory.","", "## Warning","`#check` verifies declaration availability in the imported Lean environment.","It does not mean MathGraph independently reconstructed the source proof."]
 return "\n".join(lines)+"\n"
def write_mathlib_module_verification_artifacts(r,out):
 out=Path(out); ps={"report":out/"mathlib_module_verification_report.json","markdown":out/"mathlib_module_verification_report.md","check_files":out/"module_check_files.jsonl","declaration_results":out/"declaration_results.jsonl","boundary_evidence":out/"boundary_evidence.jsonl","failed_diagnostics":out/"failed_check_diagnostics.json","lawbook":out/"lawbook_replay_summary.json","api_response":out/"api_response.json"}; r.write_json(ps["report"]); _w(ps["markdown"],mathlib_module_verification_report_to_markdown(r)); _w(ps["check_files"],"".join(x.to_json()+"\n" for x in r.check_files)); _w(ps["declaration_results"],"".join(x.to_json()+"\n" for x in r.declaration_results)); _w(ps["boundary_evidence"],"".join(e.to_json()+"\n" for x in r.declaration_results for e in x.boundary_evidence)); _w(ps["failed_diagnostics"],_j(failed_check_diagnostics(r))); _w(ps["lawbook"],_j(r.lawbook_replay_summary)); _w(ps["api_response"],mathlib_module_verification_report_to_api_response(r).to_json()); return {k:str(v) for k,v in ps.items()}
def mathlib_module_verification_report_to_api_response(r):
 from mathgraph.api_service import _resp
 req=ApiRequest(make_api_request_id("mathlib-module-verification",r.report_id),ApiRoute.MATHLIB_MODULE_VERIFICATION); truth=ApiTruthStatus.KNOWN_SKIP_AVAILABLE if r.known_skip_count() else ApiTruthStatus.BOUNDARY_EVIDENCE_PRESENT if r.verified_count() else ApiTruthStatus.ADVISORY_ONLY; return _resp(req,route_result_from_artifacts(req.route,[r],truth_status=truth,safety=ApiSafetyLevel.SAFE_REVIEW_REQUIRED))
def mathlib_module_verification_report_to_process_episodes(r): return [ProcessEpisodeRecord(make_process_episode_id("mathlib-module-verification",x.declaration_result_id),ProcessEpisodeStatus.TERMINAL_VERIFIED_PROOF if x.verified else ProcessEpisodeStatus.ADVISORY_ONLY,contexts=[ProcessContextItem(content_id("mathlib-module-context",x.declaration_result_id),ProcessContextKind.RAW_EVENT,ProcessContextRole.ADVISORY_ONLY,x.declaration_name)],terminal_form=TerminalForm.VERIFIED_PROOF if x.verified else None,certificate_id=x.boundary_evidence[0].certificate_id if x.boundary_evidence else None,verifier_boundary_crossed=x.verified) for x in r.declaration_results]
def mathlib_module_verification_report_to_discovery_value_scores(r):
 out=[]
 for x in r.declaration_results:
  sig=DiscoveryValueSignal(content_id("mathlib-module-signal",x.declaration_result_id),DiscoveryValueSignalKind.REUSE_VALUE,1.0 if x.verified else .1,source_object_kind=DiscoveryValueObjectKind.RAW_TASK); s=DiscoveryValueScore(content_id("mathlib-module-score",x.declaration_result_id),x.declaration_result_id,DiscoveryValueObjectKind.RAW_TASK,signals=[sig]); s.recompute(); out.append(s)
 return out
def mathlib_module_verification_report_to_route_telemetry_events(r): return [{"event_id":content_id("mathlib-module-telemetry",x.declaration_result_id),"route_kind":"mathlib_module_verification","verifier_boundary_crossed":x.verified} for x in r.declaration_results]
def mathlib_module_verification_report_to_alchemical_trace(r):
 t=AlchemicalTrace(make_alchemical_trace_id("mathlib-module-verification",r.report_id))
 for p in (AlchemicalPhase.RAW_MATTER,AlchemicalPhase.CALCINATION,AlchemicalPhase.DESCENSION): t.add_step(phase=p,status=AlchemicalStatus.ADVISORY_ONLY)
 if r.verified_count(): t.add_step(phase=AlchemicalPhase.FIXATION,status=AlchemicalStatus.PROMOTED_BY_VERIFIER)
 for p in (AlchemicalPhase.DISTILLATION,AlchemicalPhase.COAGULATION): t.add_step(phase=p,status=AlchemicalStatus.ADVISORY_ONLY)
 return t
def mathlib_module_verification_report_to_agent_experiences(r): return [AgentExperience(content_id("mathlib-module-exp",x.declaration_result_id),"mathlib-module-verification",None,None,"project",None,AgentExperienceOutcome.VERIFIED_PROOF if x.verified else AgentExperienceOutcome.ADVISORY_ONLY,terminal_form=TerminalForm.VERIFIED_PROOF if x.verified else None,certificate_id=x.boundary_evidence[0].certificate_id if x.boundary_evidence else None,verifier_boundary_crossed=x.verified) for x in r.declaration_results]
def audit_mathlib_module_verification_request(x): return [_af("CRITICAL","MATHLIB_MODULE_REQUEST_NON_ADVISORY","request non-advisory",x.request_id)] if not x.advisory else []
def audit_mathlib_module_check_file(x): return [_af("CRITICAL","MATHLIB_MODULE_CHECK_NON_ADVISORY","check file non-advisory",x.check_file_id)] if not x.advisory else []
def audit_mathlib_module_declaration_result(x):
 out=[]
 if x.failure_kind!=MathlibModuleVerificationFailureKind.NONE and x.boundary_evidence: out.append(_af("CRITICAL","MATHLIB_MODULE_FAILED_RESULT_EVIDENCE","failed result has evidence",x.declaration_result_id))
 for e in x.boundary_evidence:
  if e.metadata.get("boundary_kind")!="module_aware_import_check" or e.metadata.get("check_mode")!="#check" or e.metadata.get("proof_rechecked_from_source") is not False: out.append(_af("CRITICAL","MATHLIB_MODULE_EVIDENCE_METADATA","module-aware evidence metadata incomplete",x.declaration_result_id))
  if e.metadata.get("name_resolution_mode")=="candidate_fallback" and (not e.metadata.get("original_declaration_name") or not e.metadata.get("resolved_declaration_name")): out.append(_af("CRITICAL","MATHLIB_MODULE_FALLBACK_METADATA","fallback evidence lacks names",x.declaration_result_id))
 return out
def audit_mathlib_module_verification_report(x):
 out=[]
 if not x.advisory: out.append(_af("CRITICAL","MATHLIB_MODULE_REPORT_NON_ADVISORY","report non-advisory",x.report_id))
 if x.truth_status in {MathlibModuleVerificationTruthStatus.ADVISORY_ONLY,MathlibModuleVerificationTruthStatus.SKIPPED_NO_VERIFIER} and x.boundary_evidence_count(): out.append(_af("CRITICAL","MATHLIB_MODULE_ADVISORY_EVIDENCE","advisory report has evidence",x.report_id))
 if x.known_skip_count() and not x.lawbook_replay_summary.get("accepted_total"): out.append(_af("CRITICAL","MATHLIB_MODULE_SKIP_WITHOUT_ACCEPTANCE","known skip without acceptance",x.report_id))
 return out+sum((audit_mathlib_module_declaration_result(r) for r in x.declaration_results),[])
def _req(x):
 if isinstance(x,MathlibModuleVerificationRequest): return x
 if isinstance(x,(str,Path)): return MathlibModuleVerificationRequest.read_json(x)
 return MathlibModuleVerificationRequest.from_dict(x)
def _result_failure(r):
 return {VerifierFailureKind.IMPORT_ERROR:MathlibModuleVerificationFailureKind.IMPORT_ERROR,VerifierFailureKind.TYPE_ERROR:MathlibModuleVerificationFailureKind.TYPE_ERROR,VerifierFailureKind.TIMEOUT:MathlibModuleVerificationFailureKind.TIMEOUT,VerifierFailureKind.NONZERO_EXIT:MathlibModuleVerificationFailureKind.NONZERO_EXIT,VerifierFailureKind.SAFETY_BLOCKED:MathlibModuleVerificationFailureKind.SAFETY_BLOCKED,VerifierFailureKind.EXECUTION_DISABLED:MathlibModuleVerificationFailureKind.EXECUTION_DISABLED}.get(r.failure_kind,MathlibModuleVerificationFailureKind.CHECK_FAILED)
def _has_check_error(r): return any(s in f"{r.stdout_excerpt}\n{r.stderr_excerpt}".lower() for s in ("unknown constant","unknown declaration","unknown identifier","unknown module","does not exist"))
def _failed_diag(t,f,r,name): return {"check_file_path":f.check_file_path,"check_file_text":f.check_file_text,"lean_stdout_tail":r.stdout_excerpt[-400:],"lean_stderr_tail":r.stderr_excerpt[-400:],"returncode":r.returncode,"failed_expected_declarations":list(f.declaration_names),"unresolved_declarations":[name],"failure_kind":_result_failure(r).value,"module_name":t.module_name,"project_root":f.project_root,"possible_name_candidates":list(generate_declaration_name_candidates(name,module_name=t.module_name))}
def failed_check_diagnostics(r):
 out=[]
 for x in r.declaration_results:
  if not x.verified and x.metadata.get("check_file_path"):
   out.append({k:x.metadata.get(k) for k in ("check_file_path","check_file_text","lean_stdout_tail","lean_stderr_tail","returncode","failed_expected_declarations","unresolved_declarations","failure_kind","module_name","project_root","possible_name_candidates")})
 return out
def _hash(x): return sha256(str(x).encode()).hexdigest()
def _af(sev,code,msg,obj): return {"severity":sev,"code":code,"message":msg,"object_id":obj}
def _now(): return datetime.now(timezone.utc).isoformat()
def _j(x): return json.dumps(x,sort_keys=True,separators=(",",":"),default=str)
def _w(p,t): path=Path(p); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(t,encoding="utf-8")
