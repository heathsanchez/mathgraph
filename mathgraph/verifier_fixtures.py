"""Replayable Lean verifier fixtures and conservative fixture interpretation."""
from __future__ import annotations
import json,tempfile
from dataclasses import MISSING,dataclass,field
from datetime import datetime,timezone
from enum import Enum
from pathlib import Path
from typing import Any
from mathgraph.api_service import ApiRequest,ApiRoute,ApiSafetyLevel,ApiTruthStatus,make_api_request_id,route_result_from_artifacts
from mathgraph.hashing import content_id
from mathgraph.lawbook import LawbookStore,accept_lawbook_entry,make_lawbook_store_id,review_lawbook_candidate
from mathgraph.lawbook_query import query_lawbook_store_by_certificate
from mathgraph.verifier_execution import *
def _enum(n,v): return Enum(n,{x:x for x in v.split()},type=str)
VerifierFixtureKind=_enum("VerifierFixtureKind","SHOULD_PASS SHOULD_FAIL SHOULD_REJECT_UNSAFE SHOULD_SKIP_IF_MISSING_VERIFIER SHOULD_REJECT_EXPECTED_NAME UNKNOWN")
VerifierFixtureStatus=_enum("VerifierFixtureStatus","NOT_RUN PASS_EXPECTED FAIL_EXPECTED REJECTED_EXPECTED SKIPPED UNEXPECTED_PASS UNEXPECTED_FAIL UNEXPECTED_BOUNDARY ERROR UNKNOWN")
VerifierFixtureRisk=_enum("VerifierFixtureRisk","SAFE UNSAFE_MARKER TYPE_ERROR IMPORT_ERROR EXPECTED_NAME_MISMATCH MISSING_VERIFIER UNKNOWN")
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
   if getattr(f.type,"__origin__",None) is tuple and v is not None:v=tuple(v)
   vals.append(v)
  return c(*vals)
 cls.to_dict=td; cls.from_dict=fd; cls.to_json=lambda self:_j(self.to_dict()); cls.from_json=classmethod(lambda c,t:c.from_dict(json.loads(t))); return cls
@_serial
@dataclass
class VerifierFixture:
 fixture_id:str; name:str; system_kind:VerifierSystemKind; fixture_kind:VerifierFixtureKind; risk:VerifierFixtureRisk=VerifierFixtureRisk.UNKNOWN; path:str|None=None; text:str|None=None; expected_theorem_names:tuple[str,...]=(); should_create_boundary:bool=False; should_execute_successfully:bool|None=None; should_be_rejected_before_execution:bool=False; description:str=""; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
@dataclass
class VerifierFixtureResult:
 fixture_result_id:str; fixture_id:str; fixture_name:str; status:VerifierFixtureStatus; execution_result:VerifierExecutionResult|None=None; boundary_evidence:list[VerifierBoundaryEvidence]=field(default_factory=list); expected_boundary:bool=False; actual_boundary:bool=False; expected_success:bool|None=None; actual_success:bool|None=None; warnings:tuple[str,...]=(); criticals:tuple[str,...]=(); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def ok(self): return not self.criticals and self.status in {VerifierFixtureStatus.PASS_EXPECTED,VerifierFixtureStatus.FAIL_EXPECTED,VerifierFixtureStatus.REJECTED_EXPECTED,VerifierFixtureStatus.SKIPPED}
 def to_dict(self): return {**self.__dict__,"status":self.status.value,"execution_result":self.execution_result.to_dict() if self.execution_result else None,"boundary_evidence":[x.to_dict() for x in self.boundary_evidence],"warnings":list(self.warnings),"criticals":list(self.criticals)}
 @classmethod
 def from_dict(c,d): return c(str(d["fixture_result_id"]),str(d["fixture_id"]),str(d["fixture_name"]),VerifierFixtureStatus(str(d.get("status","UNKNOWN"))),VerifierExecutionResult.from_dict(d["execution_result"]) if d.get("execution_result") else None,[VerifierBoundaryEvidence.from_dict(x) for x in d.get("boundary_evidence",())],bool(d.get("expected_boundary",False)),bool(d.get("actual_boundary",False)),d.get("expected_success"),d.get("actual_success"),tuple(d.get("warnings",())),tuple(d.get("criticals",())),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
@_serial
@dataclass
class VerifierFixtureSuite:
 suite_id:str; name:str="mathgraph-lean-fixture-suite"; fixtures:list[VerifierFixture]=field(default_factory=list); fixture_root:str|None=None; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
@dataclass
class VerifierFixtureSuiteResult:
 suite_result_id:str; suite_id:str; results:list[VerifierFixtureResult]=field(default_factory=list); verifier_execution_report:VerifierExecutionReport|None=None; created_at:str=field(default_factory=lambda:_now()); summary:dict[str,Any]=field(default_factory=dict); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def result_count(self): return len(self.results)
 def pass_count(self): return sum(x.ok() for x in self.results)
 def warning_count(self): return sum(len(x.warnings) for x in self.results)
 def critical_count(self): return sum(len(x.criticals) for x in self.results)
 def boundary_evidence_count(self): return sum(len(x.boundary_evidence) for x in self.results)
 def summarize(self):
  self.summary={"fixture_total":len(self.results),"pass_total":self.pass_count(),"warning_total":self.warning_count(),"critical_total":self.critical_count(),"boundary_evidence_total":self.boundary_evidence_count(),"skipped_total":sum(x.status==VerifierFixtureStatus.SKIPPED for x in self.results),"failure_kind_counts":_counts(x.execution_result.failure_kind.value for x in self.results if x.execution_result)}; return self.summary
 def ok(self): return self.critical_count()==0 and all(x.ok() for x in self.results)
 def to_dict(self): return {**self.__dict__,"results":[x.to_dict() for x in self.results],"verifier_execution_report":self.verifier_execution_report.to_dict() if self.verifier_execution_report else None}
 @classmethod
 def from_dict(c,d): return c(str(d["suite_result_id"]),str(d["suite_id"]),[VerifierFixtureResult.from_dict(x) for x in d.get("results",())],VerifierExecutionReport.from_dict(d["verifier_execution_report"]) if d.get("verifier_execution_report") else None,str(d.get("created_at",_now())),dict(d.get("summary",{})),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
 def write_json(self,p): _w(p,self.to_json())
 @classmethod
 def read_json(c,p): return c.from_json(Path(p).read_text())
 def write_jsonl(self,p): _w(p,self.to_json()+"\n")
 @classmethod
 def read_jsonl(c,p): return [c.from_json(x) for x in Path(p).read_text().splitlines() if x.strip()]
for _c,_e in [(VerifierFixture,("system_kind","fixture_kind","risk")),(VerifierFixtureSuite,())]: _serial(_c,_e)
def make_verifier_fixture_id(*x): return content_id("verifier-fixture",x)
def make_verifier_fixture_result_id(*x): return content_id("verifier-fixture-result",x)
def make_verifier_fixture_suite_id(*x): return content_id("verifier-fixture-suite",x)
def make_verifier_fixture_suite_result_id(*x): return content_id("verifier-fixture-suite-result",x)
def default_lean_fixture_texts():
 return {
 "mathgraph_smoke_true.lean":"theorem mathgraph_smoke_true : True := by\n  trivial\n",
 "mathgraph_identity.lean":"theorem mathgraph_identity (alpha : Type) (x : alpha) : x = x := by\n  rfl\n",
 "mathgraph_and_comm.lean":"theorem mathgraph_and_comm (p q : Prop) : p ∧ q → q ∧ p := by\n  intro h\n  exact And.intro h.right h.left\n",
 "mathgraph_nat_eq_self.lean":"theorem mathgraph_nat_eq_self (n : Nat) : n = n := by\n  rfl\n",
 "mathgraph_bad_sorry.lean":"theorem mathgraph_bad_sorry : True := by\n  sorry\n",
 "mathgraph_bad_axiom.lean":"axiom mathgraph_bad_axiom_source : False\n\ntheorem mathgraph_bad_axiom : False := by\n  exact mathgraph_bad_axiom_source\n",
 "mathgraph_bad_admit.lean":"theorem mathgraph_bad_admit : True := by\n  admit\n",
 "mathgraph_bad_type_error.lean":"theorem mathgraph_bad_type_error : True := by\n  exact False\n",
 "mathgraph_bad_expected_missing.lean":"theorem mathgraph_actual_name : True := by\n  trivial\n",
 "mathgraph_bad_import.lean":"import Definitely.Does.Not.Exist.MathGraph\n\ntheorem mathgraph_bad_import : True := by\n  trivial\n",
 }
def ensure_default_lean_fixtures(fixture_root,*,overwrite=False):
 root=Path(fixture_root); root.mkdir(parents=True,exist_ok=True); out=[]
 for name,text in default_lean_fixture_texts().items():
  p=root/name
  if overwrite or not p.exists(): p.write_text(text,encoding="utf-8")
  out.append(p)
 return out
def build_default_lean_fixture_suite(fixture_root=None,*,ensure_files=True):
 root=Path(fixture_root or Path(__file__).resolve().parents[1]/"examples"/"verifier_fixtures"/"lean")
 if ensure_files: ensure_default_lean_fixtures(root)
 specs=[("mathgraph_smoke_true",VerifierFixtureKind.SHOULD_PASS,VerifierFixtureRisk.SAFE,True,True,False,("mathgraph_smoke_true",)),
 ("mathgraph_identity",VerifierFixtureKind.SHOULD_PASS,VerifierFixtureRisk.SAFE,True,True,False,("mathgraph_identity",)),
 ("mathgraph_and_comm",VerifierFixtureKind.SHOULD_PASS,VerifierFixtureRisk.SAFE,True,True,False,("mathgraph_and_comm",)),
 ("mathgraph_nat_eq_self",VerifierFixtureKind.SHOULD_PASS,VerifierFixtureRisk.SAFE,True,True,False,("mathgraph_nat_eq_self",)),
 ("mathgraph_bad_sorry",VerifierFixtureKind.SHOULD_REJECT_UNSAFE,VerifierFixtureRisk.UNSAFE_MARKER,False,None,True,("mathgraph_bad_sorry",)),
 ("mathgraph_bad_axiom",VerifierFixtureKind.SHOULD_REJECT_UNSAFE,VerifierFixtureRisk.UNSAFE_MARKER,False,None,True,("mathgraph_bad_axiom",)),
 ("mathgraph_bad_admit",VerifierFixtureKind.SHOULD_REJECT_UNSAFE,VerifierFixtureRisk.UNSAFE_MARKER,False,None,True,("mathgraph_bad_admit",)),
 ("mathgraph_bad_type_error",VerifierFixtureKind.SHOULD_FAIL,VerifierFixtureRisk.TYPE_ERROR,False,False,False,("mathgraph_bad_type_error",)),
 ("mathgraph_bad_expected_missing",VerifierFixtureKind.SHOULD_REJECT_EXPECTED_NAME,VerifierFixtureRisk.EXPECTED_NAME_MISMATCH,False,True,False,("mathgraph_expected_name",)),
 ("mathgraph_bad_import",VerifierFixtureKind.SHOULD_FAIL,VerifierFixtureRisk.IMPORT_ERROR,False,False,False,("mathgraph_bad_import",))]
 fixtures=[VerifierFixture(make_verifier_fixture_id(name),name,VerifierSystemKind.LEAN,kind,risk,str(root/f"{name}.lean"),None,expected,boundary,success,reject) for name,kind,risk,boundary,success,reject,expected in specs]
 return VerifierFixtureSuite(make_verifier_fixture_suite_id([x.fixture_id for x in fixtures]),fixtures=fixtures,fixture_root=str(root))
def run_verifier_fixture(fixture,*,workspace_root,allow_execution=False,allow_missing_verifier=True,timeout_sec=20.0):
 text=fixture.text or (Path(fixture.path).read_text(encoding="utf-8") if fixture.path else "")
 c,_=build_lean_check_contract_from_text(text,workspace_root=Path(workspace_root)/fixture.name,filename=f"{fixture.name}.lean",allow_execution=allow_execution,timeout_sec=timeout_sec,expected_theorem_names=fixture.expected_theorem_names)
 rep=build_verifier_execution_report(contracts=[c],allow_execution=allow_execution,timeout_sec=timeout_sec); r=rep.results[0]; evidence=rep.boundary_evidence; actual_boundary=bool(evidence); actual_success=r.status==VerifierExecutionStatus.SUCCESS
 warnings=[]; criticals=[]
 if r.failure_kind==VerifierFailureKind.MISSING_EXECUTABLE and allow_missing_verifier: status=VerifierFixtureStatus.SKIPPED; warnings.append("verifier missing")
 elif fixture.should_create_boundary and not allow_execution:
  status=VerifierFixtureStatus.SKIPPED; warnings.append("dry run")
 elif fixture.should_create_boundary:
  status=VerifierFixtureStatus.PASS_EXPECTED if actual_boundary else VerifierFixtureStatus.UNEXPECTED_FAIL
  if allow_execution and r.failure_kind!=VerifierFailureKind.MISSING_EXECUTABLE and not actual_boundary: criticals.append("safe fixture did not create expected boundary evidence")
 elif actual_boundary:
  status=VerifierFixtureStatus.UNEXPECTED_BOUNDARY; criticals.append("fixture created unexpected boundary evidence")
 elif fixture.fixture_kind==VerifierFixtureKind.SHOULD_REJECT_UNSAFE or fixture.fixture_kind==VerifierFixtureKind.SHOULD_REJECT_EXPECTED_NAME:
  status=VerifierFixtureStatus.REJECTED_EXPECTED
 elif fixture.fixture_kind==VerifierFixtureKind.SHOULD_FAIL:
  status=VerifierFixtureStatus.FAIL_EXPECTED if (not allow_execution or not actual_success) else VerifierFixtureStatus.UNEXPECTED_PASS
  if allow_execution and actual_success: criticals.append("failure fixture unexpectedly passed")
 else: status=VerifierFixtureStatus.PASS_EXPECTED
 return VerifierFixtureResult(make_verifier_fixture_result_id(fixture.fixture_id,r.result_id),fixture.fixture_id,fixture.name,status,r,evidence,fixture.should_create_boundary,actual_boundary,fixture.should_execute_successfully,actual_success,tuple(warnings),tuple(criticals),{"risk":fixture.risk.value})
def run_verifier_fixture_suite(suite,*,workspace_root,allow_execution=False,allow_missing_verifier=True,timeout_sec=20.0):
 results=[run_verifier_fixture(x,workspace_root=workspace_root,allow_execution=allow_execution,allow_missing_verifier=allow_missing_verifier,timeout_sec=timeout_sec) for x in suite.fixtures]
 exec_report=VerifierExecutionReport(make_verifier_execution_report_id("fixture-suite",suite.suite_id),results=[x.execution_result for x in results if x.execution_result],boundary_evidence=[e for x in results for e in x.boundary_evidence]); exec_report.summarize()
 rep=VerifierFixtureSuiteResult(make_verifier_fixture_suite_result_id(suite.suite_id,[x.fixture_result_id for x in results]),suite.suite_id,results,exec_report); rep.summarize(); return rep
def verifier_fixture_suite_result_to_markdown(r):
 s=r.summarize(); lines=["# Verifier Fixture Suite","",f"- Suite: `{r.suite_id}`",f"- Total fixtures: {s['fixture_total']}",f"- Passes: {s['pass_total']}",f"- Warnings: {s['warning_total']}",f"- Criticals: {s['critical_total']}",f"- Boundary evidence: {s['boundary_evidence_total']}","", "| fixture | expected | status | boundary | notes |","| --- | --- | --- | --- | --- |"]
 for x in r.results: lines.append(f"| {x.fixture_name} | {'boundary' if x.expected_boundary else 'no boundary'} | {x.status.value} | {'yes' if x.actual_boundary else 'no'} | {', '.join(x.warnings or x.criticals) or '-'} |")
 return "\n".join(lines)+"\n"
def verifier_fixture_suite_result_to_verifier_execution_report(r): return r.verifier_execution_report
def verifier_fixture_suite_result_to_api_response(r):
 from mathgraph.api_service import _resp
 req=ApiRequest(make_api_request_id("verifier-fixtures",r.suite_id),ApiRoute.VERIFIER_FIXTURES); truth=ApiTruthStatus.BOUNDARY_EVIDENCE_PRESENT if r.boundary_evidence_count() else ApiTruthStatus.BOUNDARY_REQUIRED; return _resp(req,route_result_from_artifacts(req.route,[r],truth_status=truth,safety=ApiSafetyLevel.SAFE_REVIEW_REQUIRED))
def verifier_fixture_suite_result_to_hardening_objects(r): return [r,*[x.execution_result for x in r.results if x.execution_result],*[e for x in r.results for e in x.boundary_evidence]]
def verifier_fixture_suite_result_to_lawbook_candidates(r):
 rep=r.verifier_execution_report or VerifierExecutionReport("empty"); return verifier_execution_report_to_lawbook_candidates(rep)
def verifier_fixture_suite_result_to_process_episodes(r): return verifier_execution_report_to_process_episodes(r.verifier_execution_report) if r.verifier_execution_report else []
def verifier_fixture_suite_result_to_route_telemetry_events(r): return verifier_execution_report_to_route_telemetry_events(r.verifier_execution_report) if r.verifier_execution_report else []
def review_and_optionally_accept_verified_fixture_evidence(r,*,accept_in_memory=False):
 candidates=verifier_fixture_suite_result_to_lawbook_candidates(r); reviews=[review_lawbook_candidate(x) for x in candidates]; accepted=[accept_lawbook_entry(e,v,accepted_by="fixture-replay") for e,v in zip(candidates,reviews) if accept_in_memory and v.decision.value=="ACCEPT"]; store=LawbookStore(make_lawbook_store_id("fixture-replay"),entries=accepted,reviews=reviews)
 answers=[query_lawbook_store_by_certificate(store,x.certificate_id) for x in candidates if x.certificate_id]
 return {"candidate_total":len(candidates),"review_total":len(reviews),"accepted_total":len(accepted),"query_total":len(answers),"known_skip_total":sum(a.known_skip_decision.value.startswith("SKIP_") for a in answers),"warnings":[],"criticals":[]}
def audit_verifier_fixture(x): return [_af("CRITICAL","FIXTURE_BOUNDARY_WITHOUT_EXPECTED","boundary fixture lacks expected theorem",x.fixture_id)] if x.should_create_boundary and not x.expected_theorem_names else []
def audit_verifier_fixture_result(x):
 out=[]
 if x.actual_boundary and (x.metadata.get("risk")!="SAFE" or not x.expected_boundary): out.append(_af("CRITICAL","FIXTURE_UNEXPECTED_BOUNDARY","unsafe or failed fixture crossed boundary",x.fixture_result_id))
 if x.ok() and x.status==VerifierFixtureStatus.UNEXPECTED_BOUNDARY: out.append(_af("CRITICAL","FIXTURE_OK_WITH_BAD_BOUNDARY","fixture marked ok despite bad boundary",x.fixture_result_id))
 return out
def audit_verifier_fixture_suite(x): return sum((audit_verifier_fixture(f) for f in x.fixtures),[])
def audit_verifier_fixture_suite_result(x): return [_af("CRITICAL","FIXTURE_SUITE_HIDES_CRITICAL","suite ok despite critical fixture",x.suite_result_id)] if x.ok() and x.critical_count() else sum((audit_verifier_fixture_result(r) for r in x.results),[])
def _counts(xs):
 out={}
 for x in xs: out[x]=out.get(x,0)+1
 return out
def _af(sev,code,msg,obj): return {"severity":sev,"code":code,"message":msg,"object_id":obj}
def _now(): return datetime.now(timezone.utc).isoformat()
def _j(x): return json.dumps(x,sort_keys=True,separators=(",",":"),default=str)
def _w(p,t): path=Path(p); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(t,encoding="utf-8")
