"""Post-M11 advisory hardening and evaluation harness."""
from __future__ import annotations
import json,subprocess,sys,tempfile,time
from collections import Counter
from dataclasses import MISSING,dataclass,field
from datetime import datetime,timezone
from enum import Enum
from pathlib import Path
from typing import Any,Mapping,Sequence
from mathgraph.agent_biography import AgentExperience,AgentExperienceOutcome
from mathgraph.alchemy import AlchemicalPhase,AlchemicalStatus,AlchemicalTrace,make_alchemical_trace_id
from mathgraph.api_service import *
from mathgraph.certificates import TerminalForm
from mathgraph.discovery_value import DiscoveryValueObjectKind,DiscoveryValueScore,DiscoveryValueSignal,DiscoveryValueSignalKind
from mathgraph.existential_agents import *
from mathgraph.formal_world_adapters import build_formal_world_adapter_report
from mathgraph.hashing import content_id
from mathgraph.lawbook import LawbookAcceptanceBoundary,LawbookEntry,LawbookEntryKind,LawbookEntryStatus,make_lawbook_entry_id
from mathgraph.process_memory import ProcessContextItem,ProcessContextKind,ProcessContextRole,ProcessEpisodeRecord,ProcessEpisodeStatus,make_process_episode_id
from mathgraph.proof_system_integration import build_proof_system_integration_report
from mathgraph.semantic_intake import *
def _enum(n,v): return Enum(n,{x:x for x in v.split()},type=str)
HardeningCheckKind=_enum("HardeningCheckKind","SERIALIZATION CLI_SMOKE API_CONTRACT END_TO_END_SMOKE DOC_SYNC PUBLIC_TERMS ROADMAP_ALIGNMENT TRUTH_BOUNDARY LAWBOOK_QUERY SEMANTIC_INTAKE FORMAL_WORLD_ADAPTER PROOF_SYSTEM_INTEGRATION PROCESS_MEMORY AGENT_ECOLOGY PROJECTION STRUCTURAL_MEMORY PERFORMANCE REPLAY_MANIFEST UNKNOWN")
HardeningCheckStatus=_enum("HardeningCheckStatus","PASS WARN FAIL SKIP ERROR UNKNOWN")
HardeningSeverity=_enum("HardeningSeverity","INFO WARNING CRITICAL UNKNOWN")
HardeningScenarioKind=_enum("HardeningScenarioKind","EMPTY MAGMA_IMPLICATION NATURAL_LANGUAGE_THEOREM PROOF_ASSISTANT_TEXT LAWBOOK_KNOWN_SKIP API_SUBMIT AGENT_LIFECYCLE FULL_ADVISORY_PIPELINE LIVE_VERIFIER_DRY_RUN E2E_ADVISORY_TEST_DRIVE RICH_LEAN_FIXTURE_DRY_RUN UNKNOWN")
HardeningArtifactKind=_enum("HardeningArtifactKind","REPORT FINDING SCENARIO REPLAY_MANIFEST CLI_RESULT API_RESULT SERIALIZATION_RESULT DOC_SYNC_RESULT PUBLIC_TERM_RESULT PERFORMANCE_RESULT UNKNOWN")
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
class HardeningFinding:
 finding_id:str; check_kind:HardeningCheckKind; status:HardeningCheckStatus; severity:HardeningSeverity=HardeningSeverity.INFO; code:str=""; message:str=""; source:str|None=None; object_type:str|None=None; object_id:str|None=None; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
@dataclass
class HardeningScenario:
 scenario_id:str; scenario_kind:HardeningScenarioKind; name:str; description:str=""; inputs:dict[str,Any]=field(default_factory=dict); expected_properties:tuple[str,...]=(); produced_artifacts:list[dict[str,Any]]=field(default_factory=list); findings:list[HardeningFinding]=field(default_factory=list); status:HardeningCheckStatus=HardeningCheckStatus.UNKNOWN; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def pass_count(self): return sum(x.status==HardeningCheckStatus.PASS for x in self.findings)
 def warning_count(self): return sum(x.severity==HardeningSeverity.WARNING for x in self.findings)
 def critical_count(self): return sum(x.severity==HardeningSeverity.CRITICAL for x in self.findings)
 def to_dict(self): return {**self.__dict__,"scenario_kind":self.scenario_kind.value,"expected_properties":list(self.expected_properties),"findings":[x.to_dict() for x in self.findings],"status":self.status.value}
 @classmethod
 def from_dict(c,d): return c(str(d["scenario_id"]),HardeningScenarioKind(str(d["scenario_kind"])),str(d["name"]),str(d.get("description","")),dict(d.get("inputs",{})),tuple(d.get("expected_properties",())),list(d.get("produced_artifacts",())),[HardeningFinding.from_dict(x) for x in d.get("findings",())],HardeningCheckStatus(str(d.get("status","UNKNOWN"))),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
@dataclass
class HardeningCliResult:
 cli_result_id:str; command_name:str; argv:tuple[str,...]=(); returncode:int|None=None; stdout_excerpt:str=""; stderr_excerpt:str=""; duration_sec:float=0.0; status:HardeningCheckStatus=HardeningCheckStatus.UNKNOWN; findings:list[HardeningFinding]=field(default_factory=list); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def to_dict(self): return {**self.__dict__,"argv":list(self.argv),"status":self.status.value,"findings":[x.to_dict() for x in self.findings]}
 @classmethod
 def from_dict(c,d): return c(str(d["cli_result_id"]),str(d["command_name"]),tuple(d.get("argv",())),d.get("returncode"),str(d.get("stdout_excerpt","")),str(d.get("stderr_excerpt","")),float(d.get("duration_sec",0)),HardeningCheckStatus(str(d.get("status","UNKNOWN"))),[HardeningFinding.from_dict(x) for x in d.get("findings",())],dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
@dataclass
class HardeningReplayManifest:
 manifest_id:str; run_id:str; created_at:str; repo_root:str|None=None; python_version:str|None=None; scenario_ids:tuple[str,...]=(); artifact_paths:tuple[str,...]=(); command_records:list[dict[str,Any]]=field(default_factory=list); boundary_policy:str="Hardening artifacts are advisory and do not promote truth."; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def to_dict(self): return {**self.__dict__,"scenario_ids":list(self.scenario_ids),"artifact_paths":list(self.artifact_paths)}
 @classmethod
 def from_dict(c,d): return c(str(d["manifest_id"]),str(d["run_id"]),str(d["created_at"]),d.get("repo_root"),d.get("python_version"),tuple(d.get("scenario_ids",())),tuple(d.get("artifact_paths",())),list(d.get("command_records",())),str(d.get("boundary_policy","")),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
 def write_json(self,p): _w(p,self.to_json())
 @classmethod
 def read_json(c,p): return c.from_json(Path(p).read_text())
@dataclass
class HardeningReport:
 report_id:str; run_id:str; created_at:str; findings:list[HardeningFinding]=field(default_factory=list); scenarios:list[HardeningScenario]=field(default_factory=list); cli_results:list[HardeningCliResult]=field(default_factory=list); replay_manifest:HardeningReplayManifest|None=None; summary:dict[str,Any]=field(default_factory=dict); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def finding_count(self): return len(self.findings)
 def critical_count(self): return sum(x.severity==HardeningSeverity.CRITICAL for x in self.findings)+sum(s.critical_count() for s in self.scenarios)
 def warning_count(self): return sum(x.severity==HardeningSeverity.WARNING for x in self.findings)+sum(s.warning_count() for s in self.scenarios)
 def pass_count(self): return sum(x.status==HardeningCheckStatus.PASS for x in self.findings)+sum(s.pass_count() for s in self.scenarios)
 def fail_count(self): return sum(x.status in {HardeningCheckStatus.FAIL,HardeningCheckStatus.ERROR} for x in self.findings)+sum(s.status==HardeningCheckStatus.FAIL for s in self.scenarios)
 def ok(self): return self.critical_count()==0 and self.fail_count()==0 and all(c.status not in {HardeningCheckStatus.FAIL,HardeningCheckStatus.ERROR} for c in self.cli_results)
 def summarize(self):
  self.summary={"finding_total":len(self.findings),"pass_total":self.pass_count(),"warn_total":sum(x.status==HardeningCheckStatus.WARN for x in self.findings),"fail_total":self.fail_count(),"error_total":sum(x.status==HardeningCheckStatus.ERROR for x in self.findings),"critical_total":self.critical_count(),"warning_total":self.warning_count(),"scenario_total":len(self.scenarios),"scenario_pass_total":sum(s.status==HardeningCheckStatus.PASS for s in self.scenarios),"scenario_warn_total":sum(s.status==HardeningCheckStatus.WARN for s in self.scenarios),"scenario_fail_total":sum(s.status==HardeningCheckStatus.FAIL for s in self.scenarios),"cli_total":len(self.cli_results),"cli_pass_total":sum(c.status==HardeningCheckStatus.PASS for c in self.cli_results),"cli_fail_total":sum(c.status==HardeningCheckStatus.FAIL for c in self.cli_results),"boundary_ok":not any(x.check_kind==HardeningCheckKind.TRUTH_BOUNDARY and x.severity==HardeningSeverity.CRITICAL for x in self.findings),"docs_ok":not any(x.check_kind==HardeningCheckKind.DOC_SYNC and x.status==HardeningCheckStatus.FAIL for x in self.findings),"public_terms_ok":not any(x.check_kind==HardeningCheckKind.PUBLIC_TERMS and x.status==HardeningCheckStatus.FAIL for x in self.findings),"api_contract_ok":not any(x.check_kind==HardeningCheckKind.API_CONTRACT and x.status==HardeningCheckStatus.FAIL for x in self.findings),"performance_ok":not any(x.check_kind==HardeningCheckKind.PERFORMANCE and x.status==HardeningCheckStatus.FAIL for x in self.findings),"advisory_only":True}; return self.summary
 def to_dict(self): return {**self.__dict__,"findings":[x.to_dict() for x in self.findings],"scenarios":[x.to_dict() for x in self.scenarios],"cli_results":[x.to_dict() for x in self.cli_results],"replay_manifest":self.replay_manifest.to_dict() if self.replay_manifest else None}
 @classmethod
 def from_dict(c,d): return c(str(d["report_id"]),str(d["run_id"]),str(d["created_at"]),[HardeningFinding.from_dict(x) for x in d.get("findings",())],[HardeningScenario.from_dict(x) for x in d.get("scenarios",())],[HardeningCliResult.from_dict(x) for x in d.get("cli_results",())],HardeningReplayManifest.from_dict(d["replay_manifest"]) if d.get("replay_manifest") else None,dict(d.get("summary",{})),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
 def write_json(self,p): _w(p,self.to_json())
 @classmethod
 def read_json(c,p): return c.from_json(Path(p).read_text())
 def write_jsonl(self,p): _w(p,self.to_json()+"\n")
 @classmethod
 def read_jsonl(c,p): return [c.from_json(x) for x in Path(p).read_text().splitlines() if x.strip()]
for _c,_e in [(HardeningFinding,("check_kind","status","severity"))]: _serial(_c,_e)
def make_hardening_finding_id(*x): return content_id("hardening-finding",x)
def make_hardening_scenario_id(*x): return content_id("hardening-scenario",x)
def make_hardening_cli_result_id(*x): return content_id("hardening-cli",x)
def make_hardening_replay_manifest_id(*x): return content_id("hardening-manifest",x)
def make_hardening_report_id(*x): return content_id("hardening-report",x)
def _scenario(kind,name,text=None): return HardeningScenario(make_hardening_scenario_id(kind.value,name,text),kind,name,inputs={"text":text} if text else {},expected_properties=("advisory_only","no_terminal_truth"))
def build_empty_scenario(): return _scenario(HardeningScenarioKind.EMPTY,"empty")
def build_magma_implication_scenario(): return _scenario(HardeningScenarioKind.MAGMA_IMPLICATION,"magma implication","(x*x)=x => (x*y)=x")
def build_natural_language_theorem_scenario(): return _scenario(HardeningScenarioKind.NATURAL_LANGUAGE_THEOREM,"natural-language theorem","Theorem: Every finite magma satisfying x*x=x has property P. Proof: clearly this follows.")
def build_proof_assistant_text_scenario(): return _scenario(HardeningScenarioKind.PROOF_ASSISTANT_TEXT,"proof assistant text","theorem demo : True := by trivial")
def build_lawbook_known_skip_scenario(): return _scenario(HardeningScenarioKind.LAWBOOK_KNOWN_SKIP,"lawbook known skip")
def build_api_submit_scenario(): return _scenario(HardeningScenarioKind.API_SUBMIT,"api submit","Theorem: every magma x*x=x.")
def build_agent_lifecycle_scenario(): return _scenario(HardeningScenarioKind.AGENT_LIFECYCLE,"agent lifecycle")
def build_full_advisory_pipeline_scenario(): return _scenario(HardeningScenarioKind.FULL_ADVISORY_PIPELINE,"full advisory pipeline","Theorem: every magma satisfying x*x=x has property P. Proof: clearly.")
def build_live_verifier_dry_run_scenario(): return _scenario(HardeningScenarioKind.LIVE_VERIFIER_DRY_RUN,"live verifier dry run","theorem mathgraph_smoke_true : True := by\n  trivial")
def build_e2e_advisory_test_drive_scenario(): return _scenario(HardeningScenarioKind.E2E_ADVISORY_TEST_DRIVE,"e2e advisory test drive")
def build_rich_lean_fixture_dry_run_scenario(): return _scenario(HardeningScenarioKind.RICH_LEAN_FIXTURE_DRY_RUN,"rich lean fixture dry run")
def run_hardening_scenario(s):
 objs=[]
 if s.scenario_kind==HardeningScenarioKind.EMPTY: objs=[]
 elif s.scenario_kind in {HardeningScenarioKind.MAGMA_IMPLICATION,HardeningScenarioKind.NATURAL_LANGUAGE_THEOREM,HardeningScenarioKind.PROOF_ASSISTANT_TEXT,HardeningScenarioKind.FULL_ADVISORY_PIPELINE}:
  sem=build_semantic_intake_report([s.inputs["text"]]); fw=build_formal_world_adapter_report(semantic_report_to_formal_world_inputs(sem) or [s.inputs["text"]]); ps=build_proof_system_integration_report(semantic_report_to_proof_system_inputs(sem) or [s.inputs["text"]]); objs=[sem,fw,ps]
  if s.scenario_kind==HardeningScenarioKind.FULL_ADVISORY_PIPELINE: objs+=[semantic_report_to_curriculum(sem),*semantic_report_to_process_episodes(sem),build_agent_ecology_report([s.inputs["text"]],default_agent_name="Aurelia",activate_new_agents=True)]
 elif s.scenario_kind==HardeningScenarioKind.LAWBOOK_KNOWN_SKIP:
  e=LawbookEntry("hardening-entry",LawbookEntryKind.VERIFIED_PROOF_ENTRY,LawbookEntryStatus.ACCEPTED,source="x",target="y",terminal_form=TerminalForm.VERIFIED_PROOF,certificate_id="cert",verifier_boundary_crossed=True,acceptance_boundary=LawbookAcceptanceBoundary.VERIFIED_PROOF,advisory=False); objs=[MathGraphLocalClient(ApiServiceState([e])).query({"source":"x","target":"y"})]
 elif s.scenario_kind==HardeningScenarioKind.API_SUBMIT: objs=[MathGraphLocalClient().submit({"text":s.inputs["text"]})]
 elif s.scenario_kind==HardeningScenarioKind.AGENT_LIFECYCLE:
  a=create_existential_agent("Aurelia"); a.activate(); a,_=kill_agent(a); objs=[build_agent_ecology_report(agents=[a])]
 elif s.scenario_kind==HardeningScenarioKind.LIVE_VERIFIER_DRY_RUN:
  from mathgraph.verifier_execution import build_verifier_execution_report
  objs=[build_verifier_execution_report([s.inputs["text"]],allow_execution=False)]
 elif s.scenario_kind==HardeningScenarioKind.E2E_ADVISORY_TEST_DRIVE:
  from mathgraph.e2e_testdrive import run_e2e_testdrive
  objs=[run_e2e_testdrive(include_hardening=False)]
 elif s.scenario_kind==HardeningScenarioKind.RICH_LEAN_FIXTURE_DRY_RUN:
  from mathgraph.verifier_fixtures import build_default_lean_fixture_suite,run_verifier_fixture_suite
  objs=[run_verifier_fixture_suite(build_default_lean_fixture_suite(),workspace_root=Path(tempfile.gettempdir())/"mathgraph_hardening_fixtures",allow_execution=False)]
 s.produced_artifacts=[artifact_to_api_dict(x) for x in objs]
 s.findings=run_truth_boundary_checks(objs)
 s.status=HardeningCheckStatus.FAIL if any(f.severity==HardeningSeverity.CRITICAL for f in s.findings) else HardeningCheckStatus.WARN if s.findings else HardeningCheckStatus.PASS
 return s
def run_default_hardening_scenarios(include_full_pipeline=True,include_verifier_execution=True,include_rich_verifier_fixtures=True):
 xs=[build_empty_scenario(),build_magma_implication_scenario(),build_natural_language_theorem_scenario(),build_proof_assistant_text_scenario(),build_lawbook_known_skip_scenario(),build_api_submit_scenario(),build_agent_lifecycle_scenario()]
 if include_full_pipeline: xs.append(build_full_advisory_pipeline_scenario())
 if include_verifier_execution: xs += [build_live_verifier_dry_run_scenario(),build_e2e_advisory_test_drive_scenario()]
 if include_rich_verifier_fixtures: xs.append(build_rich_lean_fixture_dry_run_scenario())
 return [run_hardening_scenario(x) for x in xs]
def _pass(kind,code,msg,meta=None): return HardeningFinding(make_hardening_finding_id(kind.value,code,msg),kind,HardeningCheckStatus.PASS,HardeningSeverity.INFO,code,msg,metadata=dict(meta or {}))
def _crit(kind,code,msg,obj=None): return HardeningFinding(make_hardening_finding_id(kind.value,code,msg,obj),kind,HardeningCheckStatus.FAIL,HardeningSeverity.CRITICAL,code,msg,object_id=_s(obj))
def _warn(kind,code,msg,obj=None,meta=None): return HardeningFinding(make_hardening_finding_id(kind.value,code,msg,obj),kind,HardeningCheckStatus.WARN,HardeningSeverity.WARNING,code,msg,object_id=_s(obj),metadata=dict(meta or {}))
def run_serialization_checks():
 sem=build_semantic_intake_report(["theorem x"]); fw=build_formal_world_adapter_report(["x=x"]); ps=build_proof_system_integration_report(["theorem x"]); api=MathGraphLocalClient().health(); ag=create_existential_agent("A"); ar=build_agent_ecology_report(agents=[ag]); xs=[sem.sources[0],sem,fw,ps,ApiRequest("q",ApiRoute.HEALTH),api,ag,ar]
 out=[]
 for x in xs:
  ok=x.from_json(x.to_json()).to_dict()==x.to_dict(); out.append(_pass(HardeningCheckKind.SERIALIZATION,"ROUNDTRIP_OK",x.__class__.__name__) if ok else _crit(HardeningCheckKind.SERIALIZATION,"ROUNDTRIP_FAIL",x.__class__.__name__))
 return out
def run_cli_smoke_checks(repo_root=None,*,include_slow=False,timeout_sec=20.0):
 root=Path(repo_root or Path(__file__).resolve().parents[1]); cmds=[("semantic_intake",["scripts/run_semantic_intake.py"]),("formal_world",["scripts/run_formal_world_adapters.py"]),("proof_system",["scripts/run_proof_system_integration.py"]),("api_health",["scripts/run_api_service.py","--route","health"]),("agents",["scripts/run_existential_agents.py"]),("alignment",["scripts/run_roadmap_alignment.py","--fail-on-critical"])]
 out=[]
 for name,argv in cmds:
  start=time.perf_counter()
  try:
   p=subprocess.run([sys.executable,*argv],cwd=root,capture_output=True,text=True,timeout=timeout_sec)
   status=HardeningCheckStatus.PASS if p.returncode==0 else HardeningCheckStatus.FAIL; finds=[] if p.returncode==0 else [_crit(HardeningCheckKind.CLI_SMOKE,"CLI_FAILED",name)]
   out.append(HardeningCliResult(make_hardening_cli_result_id(name,argv),name,tuple(argv),p.returncode,p.stdout[:300],p.stderr[:300],time.perf_counter()-start,status,finds))
  except subprocess.TimeoutExpired: out.append(HardeningCliResult(make_hardening_cli_result_id(name,"timeout"),name,tuple(argv),None,duration_sec=time.perf_counter()-start,status=HardeningCheckStatus.ERROR,findings=[_crit(HardeningCheckKind.CLI_SMOKE,"CLI_TIMEOUT",name)]))
 return out
BANNED_PUBLIC_TERMS=("logikey","isabelle/aot","isabelle/aot importer","aot importer","archive of formal proofs as architecture","aot kernel","aot formal world","aot methodology","aot as architecture")
def run_doc_sync_checks(repo_root=None):
 root=Path(repo_root or Path(__file__).resolve().parents[1]); files={n:(root/n).read_text().lower() for n in ("README.md","docs/roadmap.md","docs/agentic_alchemical_loop.md","docs/mathgraph_full_vision_design_spec.tex")}; out=[]
 req={"README.md":("m11","existential agent ecology","api service","semantic","verifier"),"docs/roadmap.md":("m11","post-m11 hardening and evaluation","external verifier execution adapter"),"docs/agentic_alchemical_loop.md":("existential agents","api service","advisory"),"docs/mathgraph_full_vision_design_spec.tex":("existential agent ecology","api service hardening","semantic and natural-language","verifier")}
 for f,terms in req.items():
  missing=[t for t in terms if t not in files[f]]; out.append(_crit(HardeningCheckKind.DOC_SYNC,"DOC_SYNC_MISSING",f"{f}: {missing}") if missing else _pass(HardeningCheckKind.DOC_SYNC,"DOC_SYNC_OK",f))
 future=files["docs/roadmap.md"].split("## future work",1)[-1]
 if "- m11 existential agent ecology" in future: out.append(_warn(HardeningCheckKind.DOC_SYNC,"DOC_STALE_FUTURE","stale M11 future-work text"))
 return out
def run_public_term_checks(repo_root=None):
 root=Path(repo_root or Path(__file__).resolve().parents[1]); paths=[root/"README.md",*sorted((root/"docs").rglob("*.md")),*sorted((root/"docs").rglob("*.tex"))]; out=[]
 for p in paths:
  text=p.read_text().lower()
  for term in BANNED_PUBLIC_TERMS:
   if term in text: out.append(_crit(HardeningCheckKind.PUBLIC_TERMS,"BANNED_PUBLIC_TERM",f"{term} in {p}",p))
 return out or [_pass(HardeningCheckKind.PUBLIC_TERMS,"PUBLIC_TERMS_OK","public terms clean")]
def run_api_contract_checks():
 c=MathGraphLocalClient(); out=[]
 for route in [x for x in ApiRoute if x!=ApiRoute.UNKNOWN]:
  if route==ApiRoute.E2E_TESTDRIVE: continue
  resp=c.request(ApiRequest(make_api_request_id(route.value),route,payload={"text":"theorem x"}))
  if not isinstance(resp,ApiResponse) or not resp.boundary_policy: out.append(_crit(HardeningCheckKind.API_CONTRACT,"API_CONTRACT_FAIL",route.value))
 if c.health().truth_status!=ApiTruthStatus.NO_CLAIM: out.append(_crit(HardeningCheckKind.API_CONTRACT,"API_HEALTH_TRUTH","health not no-claim"))
 if c.submit({"text":"theorem x"}).truth_status not in {ApiTruthStatus.ADVISORY_ONLY,ApiTruthStatus.BOUNDARY_REQUIRED}: out.append(_crit(HardeningCheckKind.API_CONTRACT,"API_SUBMIT_TRUTH","submit terminal"))
 if c.request(ApiRequest("u",ApiRoute.UNKNOWN)).status==ApiResponseStatus.OK: out.append(_crit(HardeningCheckKind.API_CONTRACT,"API_UNKNOWN_OK","unknown route ok"))
 return out or [_pass(HardeningCheckKind.API_CONTRACT,"API_CONTRACT_OK","api contracts clean")]
def run_truth_boundary_checks(objects):
 out=[]
 for o in objects:
  d=o.to_dict() if hasattr(o,"to_dict") else dict(o) if isinstance(o,Mapping) else {}
  oid=next((d.get(k) for k in ("report_id","response_id","agent_id","trace_id","event_id") if d.get(k)),None)
  term=d.get("terminal_form") or d.get("truth_status")
  if term in {"VERIFIED_PROOF","FINITE_COUNTERMODEL","NAMED_OBSTRUCTION"} and not (d.get("certificate_id") and d.get("verifier_boundary_crossed")) and not (hasattr(o,"has_boundary_evidence") and o.has_boundary_evidence()): out.append(_crit(HardeningCheckKind.TRUTH_BOUNDARY,"TERMINAL_WITHOUT_BOUNDARY","terminal without boundary",oid))
  if d.get("verifier_boundary_crossed") and not (d.get("certificate_id") and d.get("terminal_form")): out.append(_crit(HardeningCheckKind.TRUTH_BOUNDARY,"BOUNDARY_INCOMPLETE","boundary incomplete",oid))
  if isinstance(o,ExistentialAgent) and o.is_dead() and (o.active or o.can_act()): out.append(_crit(HardeningCheckKind.AGENT_ECOLOGY,"DEAD_AGENT_ACTIVE","dead agent active",oid))
  if isinstance(o,AgentMortalityPolicy) and (o.resurrection_allowed or not o.clone_forbidden): out.append(_crit(HardeningCheckKind.AGENT_ECOLOGY,"ILLEGAL_MORTALITY","resurrection or clone allowed",oid))
  if o.__class__.__name__=="VerifierExecutionResult" and d.get("verifier_boundary_crossed") and not getattr(o,"has_boundary_evidence",lambda:False)(): out.append(_crit(HardeningCheckKind.TRUTH_BOUNDARY,"VERIFIER_BAD_BOUNDARY","verifier result boundary incomplete",oid))
  if o.__class__.__name__=="E2ETestDriveReport" and getattr(o,"critical_count",lambda:0)(): out.append(_crit(HardeningCheckKind.END_TO_END_SMOKE,"E2E_CRITICAL","e2e report critical",oid))
 return out
def run_lightweight_performance_checks():
 start=time.perf_counter()
 for _ in range(5): build_semantic_intake_report(["theorem x"]); MathGraphLocalClient().submit({"text":"theorem x"}); build_agent_ecology_report([{"text":"theorem x"}],default_agent_name="A")
 elapsed=time.perf_counter()-start
 return [_warn(HardeningCheckKind.PERFORMANCE,"PERFORMANCE_SLOW","lightweight pipeline slow",meta={"elapsed":elapsed})] if elapsed>5 else [_pass(HardeningCheckKind.PERFORMANCE,"PERFORMANCE_OK","lightweight pipeline ok",{"elapsed":elapsed,"average":elapsed/5})]
def build_replay_manifest(run_id,scenarios,artifact_paths=(),command_records=(),repo_root=None): return HardeningReplayManifest(make_hardening_replay_manifest_id(run_id,[s.scenario_id for s in scenarios]),run_id,_now(),str(repo_root) if repo_root else None,sys.version.split()[0],tuple(s.scenario_id for s in scenarios),tuple(str(x) for x in artifact_paths),[dict(x) for x in command_records])
def build_hardening_report(*,repo_root=None,include_cli=False,include_slow_cli=False,include_performance=True,include_full_pipeline=True,include_verifier_execution=True,include_rich_verifier_fixtures=True,extra_objects=(),artifact_dir=None):
 root=Path(repo_root or Path(__file__).resolve().parents[1]); run_id=content_id("hardening-run",_now()); scenarios=run_default_hardening_scenarios(include_full_pipeline,include_verifier_execution,include_rich_verifier_fixtures); cli=run_cli_smoke_checks(root,include_slow=include_slow_cli) if include_cli or include_slow_cli else []; finds=run_serialization_checks()+run_doc_sync_checks(root)+run_public_term_checks(root)+run_api_contract_checks()+run_truth_boundary_checks(extra_objects)
 if include_performance: finds+=run_lightweight_performance_checks()
 paths=[]
 if artifact_dir:
  p=Path(artifact_dir); p.mkdir(parents=True,exist_ok=True)
  for s in scenarios:
   f=p/f"{s.scenario_kind.value.lower()}.json"; _w(f,s.to_json()); paths.append(str(f))
 manifest=build_replay_manifest(run_id,scenarios,paths,[{"argv":list(c.argv),"returncode":c.returncode} for c in cli],root); r=HardeningReport(make_hardening_report_id(run_id),run_id,_now(),finds,scenarios,cli,manifest); r.summarize(); return r
def hardening_report_to_api_response(r):
 from mathgraph.api_service import _resp
 req=ApiRequest(make_api_request_id("hardening",r.report_id),ApiRoute.AUDIT); result=route_result_from_artifacts(req.route,[r],ApiResponseStatus.ACCEPTED_ADVISORY,ApiTruthStatus.ADVISORY_ONLY,ApiSafetyLevel.SAFE_REVIEW_REQUIRED if r.warning_count() else ApiSafetyLevel.SAFE_READ_ONLY); return _resp(req,result)
def hardening_report_to_process_episodes(r): return [ProcessEpisodeRecord(make_process_episode_id("hardening",s.scenario_id),ProcessEpisodeStatus.ADVISORY_ONLY,contexts=[ProcessContextItem(content_id("hardening-context",s.scenario_id),ProcessContextKind.RAW_EVENT,ProcessContextRole.ADVISORY_ONLY,s.scenario_id)],advisory=True) for s in r.scenarios]
def hardening_report_to_discovery_value_scores(r):
 sig=DiscoveryValueSignal(content_id("hardening-signal",r.report_id),DiscoveryValueSignalKind.REUSE_VALUE,.5,source_object_kind=DiscoveryValueObjectKind.RAW_TASK); s=DiscoveryValueScore(content_id("hardening-score",r.report_id),r.report_id,DiscoveryValueObjectKind.RAW_TASK,signals=[sig],metadata={"hardening_not_truth":True}); s.recompute(); return [s]
def hardening_report_to_agent_experiences(r): return [AgentExperience(content_id("hardening-exp",s.scenario_id),"hardening",None,None,"hardening",None,AgentExperienceOutcome.ADVISORY_ONLY,metadata={"scenario_id":s.scenario_id}) for s in r.scenarios]
def hardening_report_to_alchemical_trace(r):
 t=AlchemicalTrace(make_alchemical_trace_id("hardening",r.report_id))
 for p in (AlchemicalPhase.RAW_MATTER,AlchemicalPhase.CALCINATION,AlchemicalPhase.SOLUTION,AlchemicalPhase.DISTILLATION,AlchemicalPhase.COAGULATION): t.add_step(phase=p,status=AlchemicalStatus.ADVISORY_ONLY)
 return t
def hardening_report_to_route_telemetry_events(r): return [{"event_id":content_id("hardening-telemetry",s.scenario_id),"route_kind":"hardening","outcome":s.status.value,"hardening_not_truth":True} for s in r.scenarios]
def hardening_report_to_lawbook_candidates(r): return [LawbookEntry(make_lawbook_entry_id("hardening",r.report_id),LawbookEntryKind.ROUTE_RULE_ENTRY,LawbookEntryStatus.CANDIDATE,raw="hardening report",metadata={"hardening_not_truth":True,"hardening_report_id":r.report_id},advisory=True)]
def audit_hardening_finding(x): return _audit_adv(x,x.finding_id,"HARDENING_FINDING_NON_ADVISORY")
def audit_hardening_scenario(x): return _audit_adv(x,x.scenario_id,"HARDENING_SCENARIO_NON_ADVISORY")+([_af("CRITICAL","HARDENING_PASS_WITH_CRITICAL","scenario pass hides critical",x.scenario_id)] if x.status==HardeningCheckStatus.PASS and x.critical_count() else [])
def audit_hardening_cli_result(x): return _audit_adv(x,x.cli_result_id,"HARDENING_CLI_NON_ADVISORY")+([_af("CRITICAL","HARDENING_CLI_SHELL","shell true",x.cli_result_id)] if x.metadata.get("shell") else [])+([_af("CRITICAL","HARDENING_EXTERNAL_PROVER","external prover execution",x.cli_result_id)] if x.metadata.get("external_prover") else [])
def audit_hardening_replay_manifest(x): return _audit_adv(x,x.manifest_id,"HARDENING_MANIFEST_NON_ADVISORY")+([_af("CRITICAL","HARDENING_MANIFEST_NO_POLICY","manifest lacks boundary policy",x.manifest_id)] if not x.boundary_policy else [])
def audit_hardening_report(x): return _audit_adv(x,x.report_id,"HARDENING_REPORT_NON_ADVISORY")+([_af("CRITICAL","HARDENING_OK_WITH_CRITICAL","report ok hides criticals",x.report_id)] if x.ok() and x.critical_count() else [])
def _audit_adv(x,oid,code): return [_af("CRITICAL",code,"hardening object non-advisory",oid)] if not x.advisory else []
def _af(sev,code,msg,obj): return {"severity":sev,"code":code,"message":msg,"object_id":obj}
def _s(x): return None if x is None else str(x)
def _now(): return datetime.now(timezone.utc).isoformat()
def _j(x): return json.dumps(x,sort_keys=True,separators=(",",":"),default=str)
def _w(p,t): path=Path(p); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(t,encoding="utf-8")
