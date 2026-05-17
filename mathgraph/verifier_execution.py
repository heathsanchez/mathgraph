"""Strict local verifier execution contracts and evidence records."""
from __future__ import annotations
import json,os,re,shutil,subprocess,tempfile,time
from collections import Counter
from dataclasses import MISSING,dataclass,field
from datetime import datetime,timezone
from enum import Enum
from hashlib import sha256
from pathlib import Path
from typing import Any,Mapping,Sequence
from mathgraph.agent_biography import AgentExperience,AgentExperienceOutcome
from mathgraph.alchemy import AlchemicalPhase,AlchemicalStatus,AlchemicalTrace,make_alchemical_trace_id
from mathgraph.api_service import ApiRequest,ApiRoute,ApiResponseStatus,ApiSafetyLevel,ApiTruthStatus,make_api_request_id,route_result_from_artifacts
from mathgraph.certificates import TerminalForm
from mathgraph.discovery_value import DiscoveryValueObjectKind,DiscoveryValueScore,DiscoveryValueSignal,DiscoveryValueSignalKind
from mathgraph.hashing import content_id
from mathgraph.lawbook import LawbookAcceptanceBoundary,LawbookEntry,LawbookEntryKind,LawbookEntryStatus,make_lawbook_entry_id
from mathgraph.process_memory import ProcessContextItem,ProcessContextKind,ProcessContextRole,ProcessEpisodeRecord,ProcessEpisodeStatus,make_process_episode_id
from mathgraph.proof_system_integration import ProofArtifactManifest,ProofSystemIntegrationReport
from mathgraph.verifier_feedback import FlawSeverity,RepairLoopTrace,VerifierFeedback,VerifierFeedbackStatus,make_verifier_feedback_id
def _enum(n,v): return Enum(n,{x:x for x in v.split()},type=str)
VerifierSystemKind=_enum("VerifierSystemKind","LEAN COQ ISABELLE GENERIC UNKNOWN")
VerifierExecutableStatus=_enum("VerifierExecutableStatus","AVAILABLE MISSING DISABLED UNSUPPORTED BLOCKED UNKNOWN")
VerifierExecutionMode=_enum("VerifierExecutionMode","DRY_RUN CHECK_FILE CHECK_PROJECT CHECK_TEXT_TEMPFILE IMPORT_ONLY UNKNOWN")
VerifierExecutionStatus=_enum("VerifierExecutionStatus","NOT_RUN SKIPPED SUCCESS FAILED TIMEOUT BLOCKED UNSUPPORTED ERROR UNKNOWN")
VerifierBoundaryStatus=_enum("VerifierBoundaryStatus","NO_BOUNDARY BOUNDARY_EVIDENCE_CREATED BOUNDARY_EVIDENCE_REJECTED BOUNDARY_REQUIRED BOUNDARY_BLOCKED UNKNOWN")
VerifierSafetyFindingKind=_enum("VerifierSafetyFindingKind","SHELL_FORBIDDEN COMMAND_NOT_ALLOWLISTED EXECUTION_NOT_ALLOWED PATH_OUTSIDE_WORKSPACE FILE_TOO_LARGE UNSAFE_PLACEHOLDER UNSAFE_AXIOM UNSAFE_ADMIT UNSAFE_SORRY TIMEOUT_TOO_LARGE NETWORK_FORBIDDEN MISSING_EXECUTABLE RAW_SUCCESS_NOT_ENOUGH RETURN_CODE_NOT_ENOUGH UNKNOWN")
VerifierEvidenceKind=_enum("VerifierEvidenceKind","LOCAL_VERIFIER_ACCEPTED TRUSTED_IMPORT FINITE_VALIDATION CHAIN_AUDIT NONE UNKNOWN")
VerifierFailureKind=_enum("VerifierFailureKind","NONE MISSING_EXECUTABLE SAFETY_BLOCKED UNSAFE_MARKER EXPECTED_THEOREM_MISSING TYPE_ERROR IMPORT_ERROR TIMEOUT NONZERO_EXIT EXECUTION_DISABLED UNKNOWN")
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
   if getattr(f.type,"__origin__",None) is tuple and v is not None: v=tuple(v)
   vals.append(v)
  return c(*vals)
 cls.to_dict=td; cls.from_dict=fd; cls.to_json=lambda self:_j(self.to_dict()); cls.from_json=classmethod(lambda c,t:c.from_dict(json.loads(t))); return cls
@_serial
@dataclass
class VerifierExecutable:
 executable_id:str; system_kind:VerifierSystemKind; command:str; resolved_path:str|None=None; version_text:str|None=None; status:VerifierExecutableStatus=VerifierExecutableStatus.UNKNOWN; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
@_serial
@dataclass
class VerifierCommandContract:
 contract_id:str; system_kind:VerifierSystemKind; mode:VerifierExecutionMode; argv:tuple[str,...]=(); cwd:str|None=None; input_file:str|None=None; input_text_hash:str|None=None; timeout_sec:float=20.0; allow_execution:bool=False; allow_shell:bool=False; allow_network:bool=False; workspace_root:str|None=None; expected_theorem_names:tuple[str,...]=(); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
@_serial
@dataclass
class VerifierSafetyFinding:
 finding_id:str; finding_kind:VerifierSafetyFindingKind; severity:str="warning"; message:str=""; contract_id:str|None=None; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def is_critical(self): return self.severity=="critical"
@_serial
@dataclass
class VerifierExecutionRequest:
 request_id:str; contract:VerifierCommandContract; source_artifact_id:str|None=None; proof_system_report_id:str|None=None; created_at:str=field(default_factory=lambda:_now()); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def to_dict(self): return {**self.__dict__,"contract":self.contract.to_dict()}
 @classmethod
 def from_dict(c,d): return c(str(d["request_id"]),VerifierCommandContract.from_dict(d["contract"]),d.get("source_artifact_id"),d.get("proof_system_report_id"),str(d.get("created_at",_now())),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
@dataclass
class VerifierExecutionResult:
 result_id:str; request_id:str; system_kind:VerifierSystemKind; status:VerifierExecutionStatus=VerifierExecutionStatus.NOT_RUN; returncode:int|None=None; stdout_excerpt:str=""; stderr_excerpt:str=""; duration_sec:float=0.0; timed_out:bool=False; executed:bool=False; safety_findings:tuple[VerifierSafetyFinding,...]=(); parsed_theorem_names:tuple[str,...]=(); unsafe_markers:tuple[str,...]=(); boundary_status:VerifierBoundaryStatus=VerifierBoundaryStatus.NO_BOUNDARY; boundary_evidence_id:str|None=None; certificate_id:str|None=None; terminal_form:str|None=None; verifier_boundary_crossed:bool=False; failure_kind:VerifierFailureKind=VerifierFailureKind.NONE; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def has_boundary_evidence(self): return bool(self.verifier_boundary_crossed and self.boundary_status==VerifierBoundaryStatus.BOUNDARY_EVIDENCE_CREATED and self.certificate_id and self.terminal_form and self.boundary_evidence_id and self.status==VerifierExecutionStatus.SUCCESS and self.executed and not any(x.is_critical() for x in self.safety_findings) and not self.unsafe_markers)
 def to_dict(self): return {**self.__dict__,"system_kind":self.system_kind.value,"status":self.status.value,"safety_findings":[x.to_dict() for x in self.safety_findings],"parsed_theorem_names":list(self.parsed_theorem_names),"unsafe_markers":list(self.unsafe_markers),"boundary_status":self.boundary_status.value,"failure_kind":self.failure_kind.value}
 @classmethod
 def from_dict(c,d): return c(str(d["result_id"]),str(d["request_id"]),VerifierSystemKind(str(d.get("system_kind","UNKNOWN"))),VerifierExecutionStatus(str(d.get("status","NOT_RUN"))),d.get("returncode"),str(d.get("stdout_excerpt","")),str(d.get("stderr_excerpt","")),float(d.get("duration_sec",0)),bool(d.get("timed_out",False)),bool(d.get("executed",False)),tuple(VerifierSafetyFinding.from_dict(x) for x in d.get("safety_findings",())),tuple(d.get("parsed_theorem_names",())),tuple(d.get("unsafe_markers",())),VerifierBoundaryStatus(str(d.get("boundary_status","NO_BOUNDARY"))),d.get("boundary_evidence_id"),d.get("certificate_id"),d.get("terminal_form"),bool(d.get("verifier_boundary_crossed",False)),VerifierFailureKind(str(d.get("failure_kind","NONE"))),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
@dataclass
class VerifierBoundaryEvidence:
 evidence_id:str; evidence_kind:VerifierEvidenceKind=VerifierEvidenceKind.LOCAL_VERIFIER_ACCEPTED; system_kind:VerifierSystemKind=VerifierSystemKind.UNKNOWN; result_id:str|None=None; certificate_id:str|None=None; terminal_form:str|None=None; theorem_names:tuple[str,...]=(); verifier_boundary_crossed:bool=False; artifact_hash:str|None=None; command_contract_hash:str|None=None; created_at:str=field(default_factory=lambda:_now()); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=False
 def is_valid_boundary_evidence(self): return bool(self.certificate_id and self.terminal_form and self.verifier_boundary_crossed and self.result_id and (self.artifact_hash or self.command_contract_hash))
 def to_dict(self): return {**self.__dict__,"evidence_kind":self.evidence_kind.value,"system_kind":self.system_kind.value,"theorem_names":list(self.theorem_names)}
 @classmethod
 def from_dict(c,d): return c(str(d["evidence_id"]),VerifierEvidenceKind(str(d.get("evidence_kind","LOCAL_VERIFIER_ACCEPTED"))),VerifierSystemKind(str(d.get("system_kind","UNKNOWN"))),d.get("result_id"),d.get("certificate_id"),d.get("terminal_form"),tuple(d.get("theorem_names",())),bool(d.get("verifier_boundary_crossed",False)),d.get("artifact_hash"),d.get("command_contract_hash"),str(d.get("created_at",_now())),dict(d.get("metadata",{})),bool(d.get("advisory",False)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
@dataclass
class VerifierExecutionReport:
 report_id:str; executables:list[VerifierExecutable]=field(default_factory=list); contracts:list[VerifierCommandContract]=field(default_factory=list); requests:list[VerifierExecutionRequest]=field(default_factory=list); results:list[VerifierExecutionResult]=field(default_factory=list); boundary_evidence:list[VerifierBoundaryEvidence]=field(default_factory=list); safety_findings:list[VerifierSafetyFinding]=field(default_factory=list); created_at:str=field(default_factory=lambda:_now()); summary:dict[str,Any]=field(default_factory=dict); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def result_count(self): return len(self.results)
 def boundary_evidence_count(self): return len(self.boundary_evidence)
 def critical_count(self): return sum(x.is_critical() for x in self.safety_findings)
 def summarize(self):
  self.summary={"executable_total":len(self.executables),"contract_total":len(self.contracts),"request_total":len(self.requests),"result_total":len(self.results),"executed_total":sum(x.executed for x in self.results),"success_total":sum(x.status==VerifierExecutionStatus.SUCCESS for x in self.results),"failed_total":sum(x.status==VerifierExecutionStatus.FAILED for x in self.results),"skipped_total":sum(x.status==VerifierExecutionStatus.SKIPPED for x in self.results),"timeout_total":sum(x.status==VerifierExecutionStatus.TIMEOUT for x in self.results),"blocked_total":sum(x.status==VerifierExecutionStatus.BLOCKED for x in self.results),"boundary_evidence_total":len(self.boundary_evidence),"critical_total":self.critical_count(),"verifier_missing_total":sum(x.finding_kind==VerifierSafetyFindingKind.MISSING_EXECUTABLE for x in self.safety_findings),"unsafe_marker_total":sum(bool(x.unsafe_markers) for x in self.results),"allow_execution":any(x.allow_execution for x in self.contracts)}; return self.summary
 def to_dict(self): return {**self.__dict__,"executables":[x.to_dict() for x in self.executables],"contracts":[x.to_dict() for x in self.contracts],"requests":[x.to_dict() for x in self.requests],"results":[x.to_dict() for x in self.results],"boundary_evidence":[x.to_dict() for x in self.boundary_evidence],"safety_findings":[x.to_dict() for x in self.safety_findings]}
 @classmethod
 def from_dict(c,d): return c(str(d["report_id"]),[VerifierExecutable.from_dict(x) for x in d.get("executables",())],[VerifierCommandContract.from_dict(x) for x in d.get("contracts",())],[VerifierExecutionRequest.from_dict(x) for x in d.get("requests",())],[VerifierExecutionResult.from_dict(x) for x in d.get("results",())],[VerifierBoundaryEvidence.from_dict(x) for x in d.get("boundary_evidence",())],[VerifierSafetyFinding.from_dict(x) for x in d.get("safety_findings",())],str(d.get("created_at",_now())),dict(d.get("summary",{})),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
 def write_json(self,p): _w(p,self.to_json())
 @classmethod
 def read_json(c,p): return c.from_json(Path(p).read_text())
 def write_jsonl(self,p): _w(p,self.to_json()+"\n")
 @classmethod
 def read_jsonl(c,p): return [c.from_json(x) for x in Path(p).read_text().splitlines() if x.strip()]
for _c,_e in [(VerifierExecutable,("system_kind","status")),(VerifierCommandContract,("system_kind","mode")),(VerifierSafetyFinding,("finding_kind",))]: _serial(_c,_e)
def make_verifier_executable_id(*x): return content_id("verifier-executable",x)
def make_verifier_command_contract_id(*x): return content_id("verifier-contract",x)
def make_verifier_safety_finding_id(*x): return content_id("verifier-safety",x)
def make_verifier_execution_request_id(*x): return content_id("verifier-request",x)
def make_verifier_execution_result_id(*x): return content_id("verifier-result",x)
def make_verifier_boundary_evidence_id(*x): return content_id("verifier-evidence",x)
def make_verifier_execution_report_id(*x): return content_id("verifier-report",x)
def discover_verifier_executable(system_kind,*,command=None,allow_discovery=True):
 k=system_kind if isinstance(system_kind,VerifierSystemKind) else VerifierSystemKind(str(system_kind).upper()); cmd=command or {VerifierSystemKind.LEAN:"lean",VerifierSystemKind.COQ:"coqc",VerifierSystemKind.ISABELLE:"isabelle"}.get(k,"")
 if not allow_discovery:return VerifierExecutable(make_verifier_executable_id(k.value,cmd),k,cmd,status=VerifierExecutableStatus.DISABLED)
 if not cmd or k==VerifierSystemKind.GENERIC:return VerifierExecutable(make_verifier_executable_id(k.value,cmd),k,cmd,status=VerifierExecutableStatus.UNSUPPORTED)
 path=shutil.which(cmd); return VerifierExecutable(make_verifier_executable_id(k.value,cmd),k,cmd,path,status=VerifierExecutableStatus.AVAILABLE if path else VerifierExecutableStatus.MISSING)
def probe_verifier_version(e,timeout_sec=5.0,allow_execution=False):
 if not allow_execution or e.status!=VerifierExecutableStatus.AVAILABLE:return e
 args={VerifierSystemKind.LEAN:["lean","--version"],VerifierSystemKind.COQ:["coqc","--version"],VerifierSystemKind.ISABELLE:["isabelle","version"]}.get(e.system_kind)
 if not args:return e
 try: e.version_text=subprocess.run(args,capture_output=True,text=True,timeout=timeout_sec).stdout[:200].strip()
 except Exception as ex: e.metadata["version_probe_error"]=str(ex)
 return e
def build_lean_check_contract_from_text(lean_text,*,workspace_root,filename="MathGraphSmoke.lean",allow_execution=False,timeout_sec=20.0,expected_theorem_names=()):
 root=Path(workspace_root).resolve(); root.mkdir(parents=True,exist_ok=True); p=(root/filename).resolve(); p.write_text(lean_text,encoding="utf-8")
 c=VerifierCommandContract(make_verifier_command_contract_id("lean",str(p),lean_text,allow_execution),VerifierSystemKind.LEAN,VerifierExecutionMode.CHECK_TEXT_TEMPFILE,("lean",str(p)),str(root),str(p),_hash(lean_text),timeout_sec,allow_execution,False,False,str(root),tuple(expected_theorem_names),{"input_text":lean_text})
 return c,p
def build_verifier_contract_from_proof_artifact(artifact,*,workspace_root,allow_execution=False,timeout_sec=20.0):
 if isinstance(artifact,str): return build_lean_check_contract_from_text(artifact,workspace_root=workspace_root,allow_execution=allow_execution,timeout_sec=timeout_sec)[0]
 d=artifact.to_dict() if hasattr(artifact,"to_dict") else dict(artifact); text=d.get("metadata",{}).get("text") or d.get("text")
 if text:return build_lean_check_contract_from_text(text,workspace_root=workspace_root,filename=Path(d.get("path") or "MathGraphSmoke.lean").name,allow_execution=allow_execution,timeout_sec=timeout_sec,expected_theorem_names=d.get("theorem_names",()))[0]
 path=d.get("path"); root=Path(workspace_root).resolve()
 return VerifierCommandContract(make_verifier_command_contract_id(path,allow_execution),VerifierSystemKind.LEAN,VerifierExecutionMode.CHECK_FILE,("lean",str(path)),str(root),str(path),timeout_sec=timeout_sec,allow_execution=allow_execution,workspace_root=str(root),expected_theorem_names=tuple(d.get("theorem_names",())))
def build_verifier_contracts_from_proof_system_report(report,*,workspace_root,allow_execution=False,timeout_sec=20.0):
 arts=report.artifacts if hasattr(report,"artifacts") else report.get("artifacts",())
 return [build_verifier_contract_from_proof_artifact(a,workspace_root=workspace_root,allow_execution=allow_execution,timeout_sec=timeout_sec) for a in arts]
def _finding(kind,severity,msg,c): return VerifierSafetyFinding(make_verifier_safety_finding_id(kind.value,msg,getattr(c,"contract_id",None)),kind,severity,msg,getattr(c,"contract_id",None))
def validate_verifier_command_contract(c,*,max_timeout_sec=60.0,max_file_bytes=1_000_000):
 out=[]; allow={VerifierSystemKind.LEAN:"lean",VerifierSystemKind.COQ:"coqc",VerifierSystemKind.ISABELLE:"isabelle"}
 if c.allow_shell: out.append(_finding(VerifierSafetyFindingKind.SHELL_FORBIDDEN,"critical","shell execution forbidden",c))
 if c.allow_network: out.append(_finding(VerifierSafetyFindingKind.NETWORK_FORBIDDEN,"critical","network execution forbidden",c))
 if not c.allow_execution: out.append(_finding(VerifierSafetyFindingKind.EXECUTION_NOT_ALLOWED,"info","execution disabled",c))
 if not c.argv or c.argv[0]!=allow.get(c.system_kind): out.append(_finding(VerifierSafetyFindingKind.COMMAND_NOT_ALLOWLISTED,"critical","command not allowlisted",c))
 if any(any(x in tok for x in (";","&&","||","|",">","<","`","$(")) for tok in c.argv): out.append(_finding(VerifierSafetyFindingKind.COMMAND_NOT_ALLOWLISTED,"critical","shell metacharacter in argv",c))
 if c.timeout_sec>max_timeout_sec: out.append(_finding(VerifierSafetyFindingKind.TIMEOUT_TOO_LARGE,"critical","timeout too large",c))
 root=Path(c.workspace_root).resolve() if c.workspace_root else None
 for p in (c.cwd,c.input_file):
  if root and p and root not in Path(p).resolve().parents and Path(p).resolve()!=root: out.append(_finding(VerifierSafetyFindingKind.PATH_OUTSIDE_WORKSPACE,"critical","path outside workspace",c))
 if c.input_file and Path(c.input_file).exists():
  p=Path(c.input_file)
  if p.stat().st_size>max_file_bytes: out.append(_finding(VerifierSafetyFindingKind.FILE_TOO_LARGE,"critical","file too large",c))
  text=_strip_comments(p.read_text(encoding="utf-8")); 
  for marker,kind in (("sorry",VerifierSafetyFindingKind.UNSAFE_SORRY),("admit",VerifierSafetyFindingKind.UNSAFE_ADMIT),("axiom",VerifierSafetyFindingKind.UNSAFE_AXIOM),("unsafe",VerifierSafetyFindingKind.UNSAFE_PLACEHOLDER)):
   if re.search(rf"\b{marker}\b",text,re.I): out.append(_finding(kind,"critical",f"unsafe marker: {marker}",c))
 if not c.expected_theorem_names: out.append(_finding(VerifierSafetyFindingKind.RAW_SUCCESS_NOT_ENOUGH,"warning","expected theorem names absent",c))
 return out
def execute_verifier_request(req,*,allow_execution=False,max_timeout_sec=60.0):
 c=req.contract; finds=validate_verifier_command_contract(c,max_timeout_sec=max_timeout_sec); crit=any(x.is_critical() for x in finds)
 if not allow_execution or not c.allow_execution: return VerifierExecutionResult(make_verifier_execution_result_id(req.request_id,"blocked"),req.request_id,c.system_kind,VerifierExecutionStatus.BLOCKED,safety_findings=tuple(finds),boundary_status=VerifierBoundaryStatus.BOUNDARY_BLOCKED,failure_kind=VerifierFailureKind.EXECUTION_DISABLED)
 if crit:return VerifierExecutionResult(make_verifier_execution_result_id(req.request_id,"unsafe"),req.request_id,c.system_kind,VerifierExecutionStatus.BLOCKED,safety_findings=tuple(finds),boundary_status=VerifierBoundaryStatus.BOUNDARY_BLOCKED,unsafe_markers=tuple(x.finding_kind.value for x in finds if x.finding_kind.name.startswith("UNSAFE_")),failure_kind=VerifierFailureKind.SAFETY_BLOCKED)
 exe=discover_verifier_executable(c.system_kind)
 if exe.status!=VerifierExecutableStatus.AVAILABLE:
  miss=_finding(VerifierSafetyFindingKind.MISSING_EXECUTABLE,"warning","verifier executable missing",c); return VerifierExecutionResult(make_verifier_execution_result_id(req.request_id,"missing"),req.request_id,c.system_kind,VerifierExecutionStatus.SKIPPED,safety_findings=tuple([*finds,miss]),failure_kind=VerifierFailureKind.MISSING_EXECUTABLE)
 start=time.perf_counter()
 try:
  env=None
  if c.metadata.get("lean_path"):
   env=dict(os.environ); env["LEAN_PATH"]=str(c.metadata["lean_path"])
  p=subprocess.run(list(c.argv),cwd=c.cwd,capture_output=True,text=True,timeout=min(c.timeout_sec,max_timeout_sec),env=env)
  raw={"returncode":p.returncode,"executed":True}; b,names,unsafe=parse_verifier_success(req,raw); st=VerifierExecutionStatus.SUCCESS if p.returncode==0 else VerifierExecutionStatus.FAILED
  md={"expected_theorem_missing":bool(c.expected_theorem_names and not set(c.expected_theorem_names).issubset(names))}
  r=VerifierExecutionResult(make_verifier_execution_result_id(req.request_id,p.returncode,p.stdout,p.stderr),req.request_id,c.system_kind,st,p.returncode,p.stdout[:400],p.stderr[:400],time.perf_counter()-start,False,True,tuple(finds),names,unsafe,b,metadata=md)
  r.failure_kind=classify_verifier_failure(r,p.stderr,p.stdout)
  if b==VerifierBoundaryStatus.BOUNDARY_EVIDENCE_CREATED:
   r.certificate_id=content_id("local-verifier-certificate",(c.input_text_hash,names)); r.terminal_form=TerminalForm.VERIFIED_PROOF.value; r.verifier_boundary_crossed=True; r.boundary_evidence_id=make_verifier_boundary_evidence_id(r.result_id)
  return r
 except subprocess.TimeoutExpired as ex: return VerifierExecutionResult(make_verifier_execution_result_id(req.request_id,"timeout"),req.request_id,c.system_kind,VerifierExecutionStatus.TIMEOUT,stdout_excerpt=str(ex.stdout or "")[:400],stderr_excerpt=str(ex.stderr or "")[:400],duration_sec=time.perf_counter()-start,timed_out=True,executed=True,safety_findings=tuple(finds),failure_kind=VerifierFailureKind.TIMEOUT)
 except Exception as ex: return VerifierExecutionResult(make_verifier_execution_result_id(req.request_id,"error"),req.request_id,c.system_kind,VerifierExecutionStatus.ERROR,stderr_excerpt=str(ex),duration_sec=time.perf_counter()-start,safety_findings=tuple(finds))
def extract_theorem_declarations(text):
 clean=_strip_comments(text); names=tuple(re.findall(r"\b(?:theorem|lemma)\s+([A-Za-z_][A-Za-z0-9_]*)",clean)); return names or (("anonymous_example",) if re.search(r"\bexample\b",clean) else ())
def extract_unsafe_markers(text):
 clean=_strip_comments(text); return tuple(x for x in ("sorry","admit","axiom","unsafe") if re.search(rf"\b{x}\b",clean,re.I))
def validate_expected_theorems(text,expected_theorem_names):
 names=extract_theorem_declarations(text); missing=tuple(x for x in expected_theorem_names if x not in names); return not missing,missing
def parse_verifier_success(req,raw_result):
 d=raw_result.to_dict() if hasattr(raw_result,"to_dict") else dict(raw_result); c=req.contract
 if not d.get("executed") or d.get("returncode")!=0 or not c.input_file or not Path(c.input_file).exists(): return VerifierBoundaryStatus.NO_BOUNDARY,(),()
 text=Path(c.input_file).read_text(encoding="utf-8"); unsafe=extract_unsafe_markers(text); names=extract_theorem_declarations(text)
 if unsafe:return VerifierBoundaryStatus.BOUNDARY_EVIDENCE_REJECTED,names,unsafe
 ok,_=validate_expected_theorems(text,c.expected_theorem_names)
 if c.expected_theorem_names and not ok: return VerifierBoundaryStatus.BOUNDARY_REQUIRED,names,()
 return (VerifierBoundaryStatus.BOUNDARY_EVIDENCE_CREATED if names else VerifierBoundaryStatus.BOUNDARY_REQUIRED),names,()
def create_boundary_evidence_from_result(req,r):
 if not r.has_boundary_evidence(): return None
 return VerifierBoundaryEvidence(r.boundary_evidence_id or make_verifier_boundary_evidence_id(r.result_id),VerifierEvidenceKind.LOCAL_VERIFIER_ACCEPTED,r.system_kind,r.result_id,r.certificate_id,r.terminal_form,r.parsed_theorem_names,True,req.contract.input_text_hash,_hash(req.contract.to_json()))
def classify_verifier_failure(result,stderr_text="",stdout_text=""):
 text=f"{stderr_text}\n{stdout_text}".lower()
 if any(x.finding_kind==VerifierSafetyFindingKind.MISSING_EXECUTABLE for x in result.safety_findings): return VerifierFailureKind.MISSING_EXECUTABLE
 if any(x.is_critical() for x in result.safety_findings): return VerifierFailureKind.UNSAFE_MARKER if result.unsafe_markers else VerifierFailureKind.SAFETY_BLOCKED
 if result.unsafe_markers:return VerifierFailureKind.UNSAFE_MARKER
 if result.timed_out:return VerifierFailureKind.TIMEOUT
 if any(x in text for x in ("unknown module","object file","does not exist","unknown package")): return VerifierFailureKind.IMPORT_ERROR
 if any(x in text for x in ("type mismatch","application type mismatch","invalid")): return VerifierFailureKind.TYPE_ERROR
 if result.metadata.get("expected_theorem_missing"): return VerifierFailureKind.EXPECTED_THEOREM_MISSING
 if result.status==VerifierExecutionStatus.BLOCKED and not result.executed:return VerifierFailureKind.EXECUTION_DISABLED
 if result.returncode not in (None,0): return VerifierFailureKind.NONZERO_EXIT
 return VerifierFailureKind.NONE if result.status==VerifierExecutionStatus.SUCCESS else VerifierFailureKind.UNKNOWN
def build_verifier_execution_report(objects=(),contracts=(),*,workspace_root=None,allow_execution=False,timeout_sec=20.0,include_version_probe=False):
 root=Path(workspace_root or Path(tempfile.gettempdir())/"mathgraph_verifier_tmp").resolve(); cs=list(contracts)
 for o in objects:
  if isinstance(o,ProofSystemIntegrationReport): cs+=build_verifier_contracts_from_proof_system_report(o,workspace_root=root,allow_execution=allow_execution,timeout_sec=timeout_sec)
  else: cs.append(build_verifier_contract_from_proof_artifact(o,workspace_root=root,allow_execution=allow_execution,timeout_sec=timeout_sec))
 exes=[]
 for k in dict.fromkeys(c.system_kind for c in cs):
  e=discover_verifier_executable(k); exes.append(probe_verifier_version(e,allow_execution=include_version_probe and allow_execution))
 reqs=[VerifierExecutionRequest(make_verifier_execution_request_id(c.contract_id),c) for c in cs]; results=[execute_verifier_request(q,allow_execution=allow_execution) for q in reqs]; ev=[x for q,r in zip(reqs,results) if (x:=create_boundary_evidence_from_result(q,r))]
 safety=[x for c in cs for x in validate_verifier_command_contract(c)]+[x for r in results for x in r.safety_findings if x.finding_kind==VerifierSafetyFindingKind.MISSING_EXECUTABLE]
 rep=VerifierExecutionReport(make_verifier_execution_report_id([c.contract_id for c in cs],allow_execution),exes,cs,reqs,results,ev,safety); rep.summarize(); return rep
def verifier_execution_report_to_proof_system_report(r): return {"verifier_execution_report_id":r.report_id,"boundary_evidence":[x.to_dict() for x in r.boundary_evidence],"advisory":not bool(r.boundary_evidence)}
def verifier_execution_report_to_lawbook_candidates(r):
 return [LawbookEntry(make_lawbook_entry_id("verifier-execution",e.evidence_id),LawbookEntryKind.VERIFIED_PROOF_ENTRY,LawbookEntryStatus.CANDIDATE,terminal_form=TerminalForm.VERIFIED_PROOF,certificate_id=e.certificate_id,verifier_boundary_crossed=True,acceptance_boundary=LawbookAcceptanceBoundary.VERIFIED_PROOF,metadata={"verifier_execution_report_id":r.report_id,"local_verifier_boundary_evidence":True,"raw_success_text_not_enough":True}) for e in r.boundary_evidence]
def verifier_execution_report_to_api_response(r):
 from mathgraph.api_service import _resp
 req=ApiRequest(make_api_request_id("verifier-execution",r.report_id),ApiRoute.VERIFIER_EXECUTION); truth=ApiTruthStatus.BOUNDARY_EVIDENCE_PRESENT if r.boundary_evidence else ApiTruthStatus.BOUNDARY_REQUIRED; return _resp(req,route_result_from_artifacts(req.route,[r,*r.boundary_evidence],truth_status=truth,safety=ApiSafetyLevel.SAFE_REVIEW_REQUIRED if not r.boundary_evidence else ApiSafetyLevel.SAFE_ADVISORY))
def verifier_execution_report_to_process_episodes(r): return [ProcessEpisodeRecord(make_process_episode_id("verifier-execution",x.result_id),ProcessEpisodeStatus.TERMINAL_VERIFIED_PROOF if x.has_boundary_evidence() else ProcessEpisodeStatus.ADVISORY_ONLY,contexts=[ProcessContextItem(content_id("verifier-context",x.result_id),ProcessContextKind.RAW_EVENT,ProcessContextRole.ADVISORY_ONLY,x.result_id)],terminal_form=TerminalForm.VERIFIED_PROOF if x.has_boundary_evidence() else None,certificate_id=x.certificate_id,verifier_boundary_crossed=x.verifier_boundary_crossed) for x in r.results]
def verifier_execution_report_to_verifier_feedback(r): return [VerifierFeedback(make_verifier_feedback_id(x.result_id),status=VerifierFeedbackStatus.FAILED if x.status in {VerifierExecutionStatus.FAILED,VerifierExecutionStatus.BLOCKED} else VerifierFeedbackStatus.NOT_RUN,flaw_severity=FlawSeverity.STRUCTURAL_GAP if x.status==VerifierExecutionStatus.FAILED else FlawSeverity.MINOR_REPAIRABLE,raw_message=x.stderr_excerpt or x.status.value) for x in r.results if not x.has_boundary_evidence()]
def verifier_execution_report_to_repair_traces(r): return [RepairLoopTrace(content_id("verifier-repair",x.result_id)) for x in r.results if x.status in {VerifierExecutionStatus.FAILED,VerifierExecutionStatus.BLOCKED}]
def verifier_execution_report_to_proof_digestion_inputs(r): return [{"result_id":x.result_id,"proof_text":x.stdout_excerpt,"advisory":not x.has_boundary_evidence()} for x in r.results]
def verifier_execution_report_to_discovery_value_scores(r):
 out=[]
 for x in r.results:
  sig=DiscoveryValueSignal(content_id("verifier-signal",x.result_id),DiscoveryValueSignalKind.REUSE_VALUE,1.0 if x.has_boundary_evidence() else .2,source_object_kind=DiscoveryValueObjectKind.RAW_TASK); s=DiscoveryValueScore(content_id("verifier-score",x.result_id),x.result_id,DiscoveryValueObjectKind.RAW_TASK,signals=[sig]); s.recompute(); out.append(s)
 return out
def verifier_execution_report_to_alchemical_trace(r):
 t=AlchemicalTrace(make_alchemical_trace_id("verifier-execution",r.report_id))
 for p in (AlchemicalPhase.RAW_MATTER,AlchemicalPhase.CALCINATION,AlchemicalPhase.DESCENSION): t.add_step(phase=p,status=AlchemicalStatus.ADVISORY_ONLY)
 if r.boundary_evidence:t.add_step(phase=AlchemicalPhase.FIXATION,status=AlchemicalStatus.PROMOTED_BY_VERIFIER)
 for p in (AlchemicalPhase.DISTILLATION,AlchemicalPhase.COAGULATION): t.add_step(phase=p,status=AlchemicalStatus.ADVISORY_ONLY)
 return t
def verifier_execution_report_to_agent_experiences(r): return [AgentExperience(content_id("verifier-exp",x.result_id),"verifier-execution",None,None,"verifier",None,AgentExperienceOutcome.VERIFIED_PROOF if x.has_boundary_evidence() else AgentExperienceOutcome.INVALID_CANDIDATE if x.status in {VerifierExecutionStatus.FAILED,VerifierExecutionStatus.BLOCKED} else AgentExperienceOutcome.ADVISORY_ONLY,terminal_form=TerminalForm.VERIFIED_PROOF if x.has_boundary_evidence() else None,certificate_id=x.certificate_id,verifier_boundary_crossed=x.verifier_boundary_crossed) for x in r.results]
def verifier_execution_report_to_route_telemetry_events(r): return [{"event_id":content_id("verifier-telemetry",x.result_id),"route_kind":"verifier_execution","outcome":x.status.value,"certificate_id":x.certificate_id,"verifier_boundary_crossed":x.verifier_boundary_crossed} for x in r.results]
def verifier_execution_report_to_markdown(r):
 s=r.summarize(); kinds=Counter(x.failure_kind.value for x in r.results)
 lines=["# Verifier Execution Report","",f"- Results: {s['result_total']}","- Executed: {0}".format(s["executed_total"]),f"- Successes: {s['success_total']}",f"- Failures: {s['failed_total']}",f"- Skipped: {s['skipped_total']}",f"- Boundary evidence: {s['boundary_evidence_total']}","", "Boundary policy: raw success text and return code alone never promote truth.", "", "| argv | status | failure kind | boundary |", "| --- | --- | --- | --- |"]
 for c,res in zip(r.contracts,r.results): lines.append(f"| `{' '.join(c.argv)}` | {res.status.value} | {res.failure_kind.value} | {'yes' if res.has_boundary_evidence() else 'no'} |")
 if r.safety_findings:
  lines+=["","## Safety Findings"]+[f"- {x.severity}: {x.finding_kind.value}" for x in r.safety_findings]
 if kinds: lines+=["","## Failure Kinds"]+[f"- {k}: {v}" for k,v in sorted(kinds.items())]
 return "\n".join(lines)+"\n"
def audit_verifier_executable(x): return []
def audit_verifier_command_contract(x):
 return [_af("CRITICAL","VERIFIER_SHELL_ALLOWED","shell allowed",x.contract_id)]*bool(x.allow_shell)+[_af("CRITICAL","VERIFIER_NETWORK_ALLOWED","network allowed",x.contract_id)]*bool(x.allow_network)
def audit_verifier_safety_finding(x): return []
def audit_verifier_execution_request(x): return []
def audit_verifier_execution_result(x):
 out=[]
 if x.verifier_boundary_crossed and not x.has_boundary_evidence(): out.append(_af("CRITICAL","VERIFIER_RESULT_BAD_BOUNDARY","boundary result incomplete",x.result_id))
 if x.unsafe_markers and x.has_boundary_evidence(): out.append(_af("CRITICAL","VERIFIER_UNSAFE_BOUNDARY","unsafe marker crossed boundary",x.result_id))
 return out
def audit_verifier_boundary_evidence(x): return [_af("CRITICAL","VERIFIER_EVIDENCE_INVALID","invalid verifier evidence",x.evidence_id)] if x.advisory or not x.is_valid_boundary_evidence() else []
def audit_verifier_execution_report(x):
 out=[]
 if x.boundary_evidence and not any(r.has_boundary_evidence() for r in x.results): out.append(_af("CRITICAL","VERIFIER_REPORT_ORPHAN_EVIDENCE","evidence without result",x.report_id))
 return out+sum((audit_verifier_execution_result(r) for r in x.results),[])+sum((audit_verifier_boundary_evidence(e) for e in x.boundary_evidence),[])
def _strip_comments(t): return re.sub(r"--.*?$","",t,flags=re.M)
def _hash(x): return sha256(str(x).encode()).hexdigest()
def _af(sev,code,msg,obj): return {"severity":sev,"code":code,"message":msg,"object_id":obj}
def _now(): return datetime.now(timezone.utc).isoformat()
def _j(x): return json.dumps(x,sort_keys=True,separators=(",",":"),default=str)
def _w(p,t): path=Path(p); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(t,encoding="utf-8")
