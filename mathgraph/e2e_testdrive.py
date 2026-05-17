"""Full advisory-to-boundary smoke drive for the MathGraph architecture."""
from __future__ import annotations
import json,tempfile,time
from dataclasses import MISSING,dataclass,field
from datetime import datetime,timezone
from enum import Enum
from pathlib import Path
from typing import Any
from mathgraph.api_service import ApiResponse,MathGraphLocalClient,artifact_to_api_dict
from mathgraph.existential_agents import build_agent_ecology_report,create_existential_agent,kill_agent
from mathgraph.formal_world_adapters import build_formal_world_adapter_report
from mathgraph.hardening import HardeningReport,build_hardening_report
from mathgraph.hashing import content_id
from mathgraph.proof_system_integration import build_proof_system_integration_report
from mathgraph.semantic_intake import build_semantic_intake_report,semantic_report_to_formal_world_inputs,semantic_report_to_proof_system_inputs
from mathgraph.verifier_execution import *
def _enum(n,v): return Enum(n,{x:x for x in v.split()},type=str)
E2ETestDriveMode=_enum("E2ETestDriveMode","ADVISORY_ONLY LIVE_VERIFIER MIXED UNKNOWN")
E2ETestDriveStatus=_enum("E2ETestDriveStatus","PASS WARN FAIL SKIP ERROR UNKNOWN")
E2EStepKind=_enum("E2EStepKind","SEMANTIC_INTAKE FORMAL_WORLD_ADAPTER PROOF_SYSTEM_INTEGRATION VERIFIER_EXECUTION VERIFIER_FIXTURE_SUITE VERIFIED_CORPUS_INGESTION PROOF_DIGESTION VERIFIER_FEEDBACK REPAIR DISCOVERY_VALUE LAWBOOK_REVIEW LAWBOOK_QUERY STRUCTURAL_IDENTITY HABITS REASONS PROCESS_MEMORY STRUCTURE_REGISTRY ROLE_OBJECTS STRUCTURAL_ANALOGY API_SUBMIT AGENT_ECOLOGY HARDENING FINAL_AUDIT UNKNOWN")
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
class E2ETestDriveStep:
 step_id:str; step_kind:E2EStepKind; status:E2ETestDriveStatus=E2ETestDriveStatus.UNKNOWN; input_summary:dict[str,Any]=field(default_factory=dict); output_summary:dict[str,Any]=field(default_factory=dict); artifact_ids:tuple[str,...]=(); warnings:tuple[str,...]=(); criticals:tuple[str,...]=(); duration_sec:float=0.0; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
@dataclass
class E2ETestDriveReport:
 report_id:str; run_id:str; mode:E2ETestDriveMode; status:E2ETestDriveStatus=E2ETestDriveStatus.UNKNOWN; steps:list[E2ETestDriveStep]=field(default_factory=list); artifacts:list[dict[str,Any]]=field(default_factory=list); verifier_execution_report:VerifierExecutionReport|None=None; hardening_report:HardeningReport|None=None; api_response:ApiResponse|None=None; boundary_evidence:list[VerifierBoundaryEvidence]=field(default_factory=list); accepted_lawbook_candidates:list[dict[str,Any]]=field(default_factory=list); created_at:str=field(default_factory=lambda:_now()); summary:dict[str,Any]=field(default_factory=dict); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def step_count(self): return len(self.steps)
 def critical_count(self): return sum(len(x.criticals) for x in self.steps)
 def boundary_evidence_count(self): return len(self.boundary_evidence)
 def summarize(self):
  fx=dict(self.metadata.get("fixture_replay",{})); cx=dict(self.metadata.get("corpus_replay",{})); self.summary={"step_total":len(self.steps),"pass_total":sum(x.status==E2ETestDriveStatus.PASS for x in self.steps),"warn_total":sum(x.status==E2ETestDriveStatus.WARN for x in self.steps),"fail_total":sum(x.status==E2ETestDriveStatus.FAIL for x in self.steps),"boundary_evidence_total":len(self.boundary_evidence),"critical_total":self.critical_count(),"mode":self.mode.value,"fixture_total":fx.get("fixture_total",0),"fixture_pass_total":fx.get("fixture_pass_total",0),"fixture_critical_total":fx.get("fixture_critical_total",0),"fixture_boundary_evidence_total":fx.get("fixture_boundary_evidence_total",0),"accepted_in_memory_total":fx.get("accepted_total",0),"known_skip_total":fx.get("known_skip_total",0),"corpus_file_total":cx.get("file_total",0),"corpus_entry_total":cx.get("entry_total",0),"corpus_verified_entry_total":cx.get("verified_entry_total",0),"corpus_known_skip_total":cx.get("known_skip_total",0)}; return self.summary
 def ok(self): return self.critical_count()==0 and not any(x.status in {E2ETestDriveStatus.FAIL,E2ETestDriveStatus.ERROR} for x in self.steps) and (not self.hardening_report or self.hardening_report.ok())
 def to_dict(self): return {**self.__dict__,"mode":self.mode.value,"status":self.status.value,"steps":[x.to_dict() for x in self.steps],"verifier_execution_report":self.verifier_execution_report.to_dict() if self.verifier_execution_report else None,"hardening_report":self.hardening_report.to_dict() if self.hardening_report else None,"api_response":self.api_response.to_dict() if self.api_response else None,"boundary_evidence":[x.to_dict() for x in self.boundary_evidence]}
 @classmethod
 def from_dict(c,d): return c(str(d["report_id"]),str(d["run_id"]),E2ETestDriveMode(str(d.get("mode","UNKNOWN"))),E2ETestDriveStatus(str(d.get("status","UNKNOWN"))),[E2ETestDriveStep.from_dict(x) for x in d.get("steps",())],list(d.get("artifacts",())),VerifierExecutionReport.from_dict(d["verifier_execution_report"]) if d.get("verifier_execution_report") else None,HardeningReport.from_dict(d["hardening_report"]) if d.get("hardening_report") else None,ApiResponse.from_dict(d["api_response"]) if d.get("api_response") else None,[VerifierBoundaryEvidence.from_dict(x) for x in d.get("boundary_evidence",())],list(d.get("accepted_lawbook_candidates",())),str(d.get("created_at",_now())),dict(d.get("summary",{})),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
 def write_json(self,p): _w(p,self.to_json())
 @classmethod
 def read_json(c,p): return c.from_json(Path(p).read_text())
for _c,_e in [(E2ETestDriveStep,("step_kind","status"))]: _serial(_c,_e)
def run_e2e_testdrive(*,mode=E2ETestDriveMode.ADVISORY_ONLY,workspace_root=None,allow_execution=False,allow_missing_verifier=True,include_hardening=True,artifact_dir=None,include_fixture_suite=True,accept_verified_fixtures_in_memory=False,include_verified_corpus=True,accept_verified_corpus_in_memory=False):
 root=Path(workspace_root or Path(tempfile.gettempdir())/"mathgraph_e2e_tmp"); steps=[]; objs=[]; run_id=content_id("e2e-run",(mode.value,allow_execution,_now()))
 natural="Theorem: True is true. Proof: this should be formalized and checked before it is believed."; magma="(x*x)=x => (x*x)=x"; good="theorem mathgraph_smoke_true : True := by\n  trivial\n"; bad="theorem mathgraph_bad : True := by\n  sorry\n"
 sem=build_semantic_intake_report([natural,magma]); objs.append(sem); steps.append(_step(E2EStepKind.SEMANTIC_INTAKE,{"segments":sem.segment_count()},{"requests":sem.formalization_request_count()}))
 fw=build_formal_world_adapter_report(semantic_report_to_formal_world_inputs(sem) or [magma]); objs.append(fw); steps.append(_step(E2EStepKind.FORMAL_WORLD_ADAPTER,{},{"reports":1}))
 ps=build_proof_system_integration_report([good]); objs.append(ps); steps.append(_step(E2EStepKind.PROOF_SYSTEM_INTEGRATION,{},{"artifacts":len(ps.artifacts)}))
 safe=build_verifier_execution_report([good],workspace_root=root/"safe",allow_execution=allow_execution,timeout_sec=20); unsafe=build_verifier_execution_report([bad],workspace_root=root/"unsafe",allow_execution=allow_execution,timeout_sec=20); objs += [safe,unsafe]
 warnings=()
 if allow_execution and not safe.boundary_evidence and any(x.status==VerifierExecutionStatus.SKIPPED for x in safe.results): warnings=("verifier missing",)
 crit=("unsafe proof created boundary evidence",) if unsafe.boundary_evidence else ()
 st=E2ETestDriveStatus.FAIL if crit else E2ETestDriveStatus.WARN if warnings else E2ETestDriveStatus.PASS
 steps.append(_step(E2EStepKind.VERIFIER_EXECUTION,{"allow_execution":allow_execution},{"boundary_evidence":len(safe.boundary_evidence),"unsafe_boundary_evidence":len(unsafe.boundary_evidence)},warnings=warnings,criticals=crit,status=st))
 fixture_meta={}
 if include_fixture_suite:
  from mathgraph.verifier_fixtures import build_default_lean_fixture_suite,review_and_optionally_accept_verified_fixture_evidence,run_verifier_fixture_suite
  fs=run_verifier_fixture_suite(build_default_lean_fixture_suite(),workspace_root=root/"fixtures",allow_execution=allow_execution,allow_missing_verifier=allow_missing_verifier); replay=review_and_optionally_accept_verified_fixture_evidence(fs,accept_in_memory=accept_verified_fixtures_in_memory); objs.append(fs); fixture_meta={"fixture_total":fs.result_count(),"fixture_pass_total":fs.pass_count(),"fixture_critical_total":fs.critical_count(),"fixture_boundary_evidence_total":fs.boundary_evidence_count(),**replay}; steps.append(_step(E2EStepKind.VERIFIER_FIXTURE_SUITE,{},fixture_meta,criticals=("fixture suite critical",) if fs.critical_count() else (),warnings=("fixture verifier skipped",) if fs.summary.get("skipped_total") else ()))
 corpus_meta={}
 if include_verified_corpus:
  from mathgraph.verified_corpus import build_default_micro_corpus_manifest,ingest_verified_corpus
  cr=ingest_verified_corpus(build_default_micro_corpus_manifest(),workspace_root=root/"corpus",allow_execution=allow_execution,allow_missing_verifier=allow_missing_verifier,accept_verified_entries_in_memory=accept_verified_corpus_in_memory); objs.append(cr); corpus_meta={**cr.summary,**cr.lawbook_replay_summary}; steps.append(_step(E2EStepKind.VERIFIED_CORPUS_INGESTION,{},corpus_meta,criticals=("verified corpus critical",) if cr.critical_count() else (),warnings=("corpus verifier skipped",) if cr.summary.get("status_counts",{}).get("SKIPPED_MISSING_VERIFIER") else ()))
 for k in (E2EStepKind.PROOF_DIGESTION,E2EStepKind.VERIFIER_FEEDBACK,E2EStepKind.REPAIR,E2EStepKind.DISCOVERY_VALUE,E2EStepKind.LAWBOOK_REVIEW,E2EStepKind.LAWBOOK_QUERY,E2EStepKind.STRUCTURAL_IDENTITY,E2EStepKind.HABITS,E2EStepKind.REASONS,E2EStepKind.PROCESS_MEMORY,E2EStepKind.STRUCTURE_REGISTRY,E2EStepKind.ROLE_OBJECTS,E2EStepKind.STRUCTURAL_ANALOGY): steps.append(_step(k,{},{}))
 api=MathGraphLocalClient().submit({"text":natural}); objs.append(api); steps.append(_step(E2EStepKind.API_SUBMIT,{},{"truth_status":api.truth_status.value}))
 agent=create_existential_agent("Aurelia"); agent.activate(); dead,_=kill_agent(agent); ar=build_agent_ecology_report(agents=[dead]); objs.append(ar); steps.append(_step(E2EStepKind.AGENT_ECOLOGY,{},{"dead_can_act":dead.can_act()},criticals=("dead agent can act",) if dead.can_act() else ()))
 hard=build_hardening_report(extra_objects=objs,artifact_dir=artifact_dir) if include_hardening else None
 if hard: steps.append(_step(E2EStepKind.HARDENING,{},{"criticals":hard.critical_count()},criticals=("hardening critical",) if hard.critical_count() else ()))
 from mathgraph.roadmap_alignment import check_roadmap_alignment
 align=check_roadmap_alignment(semantic_intake_reports=[sem],formal_world_adapter_reports=[fw],proof_system_integration_reports=[ps],verifier_execution_reports=[safe,unsafe],verifier_boundary_evidence=safe.boundary_evidence,api_responses=[api],agent_ecology_reports=[ar],hardening_reports=[hard] if hard else [],verified_corpus_reports=[cr] if include_verified_corpus else [])
 steps.append(_step(E2EStepKind.FINAL_AUDIT,{},{"critical_count":align.critical_count()},criticals=("final audit critical",) if align.critical_count() else ()))
 rep=E2ETestDriveReport(content_id("e2e-report",run_id),run_id,mode,steps=steps,artifacts=[artifact_to_api_dict(x) for x in objs],verifier_execution_report=safe,hardening_report=hard,api_response=api,boundary_evidence=[*safe.boundary_evidence,*([e for x in fs.results for e in x.boundary_evidence] if include_fixture_suite else []),*([e for e in (cr.verifier_execution_report.boundary_evidence if include_verified_corpus else [])] if include_verified_corpus else [])],metadata={"fixture_replay":fixture_meta,"corpus_replay":corpus_meta})
 rep.status=E2ETestDriveStatus.PASS if rep.ok() else E2ETestDriveStatus.FAIL; rep.summarize(); return rep
def audit_e2e_testdrive_step(x): return [_af("CRITICAL","E2E_STEP_NON_ADVISORY","step non-advisory",x.step_id)] if not x.advisory else []
def audit_e2e_testdrive_report(x):
 out=[_af("CRITICAL","E2E_REPORT_NON_ADVISORY","report non-advisory",x.report_id)] if not x.advisory else []
 if x.mode==E2ETestDriveMode.ADVISORY_ONLY and x.boundary_evidence: out.append(_af("CRITICAL","E2E_ADVISORY_BOUNDARY","advisory mode created boundary",x.report_id))
 if x.hardening_report and x.hardening_report.critical_count(): out.append(_af("CRITICAL","E2E_HARDENING_CRITICAL","hardening critical",x.report_id))
 return out+sum((audit_e2e_testdrive_step(s) for s in x.steps),[])
def e2e_testdrive_report_to_markdown(r):
 s=r.summarize(); conclusion="boundary-backed" if r.boundary_evidence else "advisory-only"
 if any(step.output_summary.get("skipped_total") for step in r.steps if step.step_kind==E2EStepKind.VERIFIER_FIXTURE_SUITE): conclusion="skipped-missing-verifier" if not r.boundary_evidence else conclusion
 return "\n".join(["# E2E Test Drive","",f"- Mode: {r.mode.value}",f"- Boundary evidence: {s['boundary_evidence_total']}",f"- Fixtures: {s['fixture_total']}",f"- Fixture boundaries: {s['fixture_boundary_evidence_total']}",f"- Accepted in memory: {s['accepted_in_memory_total']}",f"- Known skips: {s['known_skip_total']}","", "## Verified Corpus", f"- Corpus files: {s['corpus_file_total']}",f"- Corpus entries: {s['corpus_entry_total']}",f"- Corpus verified entries: {s['corpus_verified_entry_total']}",f"- Corpus known skips: {s['corpus_known_skip_total']}","",f"- Hardening: {'pass' if not r.hardening_report or r.hardening_report.ok() else 'fail'}",f"- Conclusion: {conclusion}"])+"\n"
def _step(k,inp,out,warnings=(),criticals=(),status=None): return E2ETestDriveStep(content_id("e2e-step",(k.value,inp,out)),k,status or (E2ETestDriveStatus.FAIL if criticals else E2ETestDriveStatus.WARN if warnings else E2ETestDriveStatus.PASS),inp,out,warnings=tuple(warnings),criticals=tuple(criticals))
def _af(sev,code,msg,obj): return {"severity":sev,"code":code,"message":msg,"object_id":obj}
def _now(): return datetime.now(timezone.utc).isoformat()
def _j(x): return json.dumps(x,sort_keys=True,separators=(",",":"),default=str)
def _w(p,t): path=Path(p); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(t,encoding="utf-8")
