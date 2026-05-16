"""Lightweight advisory formal-world adapters and explicit handoff contracts."""
from __future__ import annotations
import json,re
from collections import Counter
from dataclasses import dataclass,field
from datetime import datetime,timezone
from enum import Enum
from pathlib import Path
from typing import Any,Mapping,Sequence
from mathgraph.agent_biography import AgentExperience,AgentExperienceOutcome
from mathgraph.alchemy import AlchemicalPhase,AlchemicalStatus,AlchemicalTrace,make_alchemical_trace_id
from mathgraph.certificates import TerminalForm
from mathgraph.continuation_actions import ContinuationActionOutput,ContinuationActionStatus,ContinuationOutputKind,make_continuation_output_id
from mathgraph.continuation_curriculum import ContinuationCurriculum,CurriculumBuildStrategy,CurriculumStage,CurriculumStageKind,CurriculumStageStatus,CurriculumTraceStatus,make_curriculum_id,make_curriculum_stage_id
from mathgraph.discovery_value import DiscoveryValueObjectKind,DiscoveryValueScore,DiscoveryValueSignal,DiscoveryValueSignalKind
from mathgraph.hashing import content_id
from mathgraph.habit_rules import HabitObservation,HabitObservationKind,HabitOutcome
from mathgraph.lawbook import LawbookEntry,LawbookEntryKind,LawbookEntryStatus,make_lawbook_entry_id
from mathgraph.process_memory import ProcessContextItem,ProcessContextKind,ProcessContextRole,ProcessEpisodeRecord,ProcessEpisodeStatus,make_process_episode_id
from mathgraph.reason_compression import ReasonObservation,ReasonObservationKind,extract_atoms_from_mapping,make_reason_observation_id
from mathgraph.role_objects import RoleSignature,RoleSourceKind,RoleObjectKind,make_role_signature_id
from mathgraph.structural_analogy import AnalogySource,AnalogySourceKind,analogy_source_from_mapping
from mathgraph.structure_registry import StructureDescriptor,StructureObjectKind,TypedProjectionCandidate,TypedProjectionStatus,ProjectionCompatibility,structure_descriptor_from_mapping,make_typed_projection_candidate_id
def _enum(n,v): return Enum(n,{x:x for x in v.split()},type=str)
FormalWorldKind=_enum("FormalWorldKind","MAGMA_EQUATIONAL LEAN_LIKE PROOF_TEXT FINITE_STRUCTURE SMT_LIKE GRAPH_LIKE CATEGORY_LIKE GENERIC_FORMAL UNKNOWN")
AdapterOperation=_enum("AdapterOperation","PARSE NORMALIZE VALIDATE EMIT_PROOF_TASK EMIT_COUNTERMODEL_TASK EMIT_FINITE_VALIDATION_TASK EMIT_FORMALIZATION_TASK EMIT_ADAPTER_TASK EMIT_PROJECTION_TASK EMIT_REPAIR_TASK EMIT_DIGESTION_TASK EMIT_REVIEW_TASK HANDOFF_TO_VERIFIER HANDOFF_TO_IMPORTER HANDOFF_TO_FINITE_VALIDATOR HANDOFF_TO_CHAIN_AUDIT UNKNOWN")
AdapterSupportLevel=_enum("AdapterSupportLevel","SUPPORTED PARTIAL ADVISORY_ONLY UNSUPPORTED REQUIRES_EXTERNAL_VERIFIER REQUIRES_TRUSTED_IMPORTER REQUIRES_FINITE_VALIDATOR UNKNOWN")
ParseStatus=_enum("ParseStatus","PARSED PARTIAL FAILED UNSUPPORTED EMPTY UNKNOWN")
NormalizeStatus=_enum("NormalizeStatus","NORMALIZED PARTIAL FAILED UNSUPPORTED EMPTY UNKNOWN")
ValidationStatus=_enum("ValidationStatus","VALID_SHAPE INVALID_SHAPE PARTIAL NEEDS_FORMALIZATION NEEDS_VERIFIER NEEDS_IMPORTER NEEDS_FINITE_VALIDATOR UNSUPPORTED UNKNOWN")
FormalWorldTaskKind=_enum("FormalWorldTaskKind","PROOF_TASK COUNTERMODEL_TASK FINITE_VALIDATION_TASK FORMALIZATION_TASK ADAPTER_TASK PROJECTION_TASK REPAIR_TASK DIGESTION_TASK REVIEW_TASK NORMALIZATION_TASK PARSE_REPAIR_TASK UNKNOWN")
HandoffKind=_enum("HandoffKind","VERIFIER TRUSTED_IMPORTER FINITE_VALIDATOR CHAIN_AUDIT HUMAN_REVIEW NONE UNKNOWN")
HandoffStatus=_enum("HandoffStatus","REQUESTED READY MISSING_ARTIFACT MISSING_BOUNDARY UNSUPPORTED COMPLETED_WITH_BOUNDARY COMPLETED_WITHOUT_BOUNDARY FAILED UNKNOWN")
FormalWorldAdapterReportStatus=_enum("FormalWorldAdapterReportStatus","EMPTY CAPABILITIES_REPORTED PARSED NORMALIZED VALIDATED TASKS_EMITTED HANDOFFS_EMITTED HAS_WARNINGS HAS_CRITICALS ADVISORY_ONLY")
@dataclass
class FormalWorldAdapterSpec:
 adapter_id:str; world_kind:FormalWorldKind; name:str; description:str|None=None; supported_operations:tuple[str,...]=(); input_patterns:tuple[str,...]=(); output_contracts:tuple[str,...]=(); verifier_boundary_operations:tuple[str,...]=(); requires_external_tool:bool=False; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def supports(self,o): return (o.value if hasattr(o,"value") else str(o)) in self.supported_operations
 def to_dict(self): return {**self.__dict__,"world_kind":self.world_kind.value,"supported_operations":list(self.supported_operations),"input_patterns":list(self.input_patterns),"output_contracts":list(self.output_contracts),"verifier_boundary_operations":list(self.verifier_boundary_operations)}
 @classmethod
 def from_dict(c,d): return c(str(d["adapter_id"]),FormalWorldKind(str(d.get("world_kind","UNKNOWN"))),str(d["name"]),_s(d.get("description")),tuple(d.get("supported_operations",())),tuple(d.get("input_patterns",())),tuple(d.get("output_contracts",())),tuple(d.get("verifier_boundary_operations",())),bool(d.get("requires_external_tool",False)),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
@dataclass
class FormalWorldAdapterCapability:
 capability_id:str; adapter_id:str; operation:AdapterOperation; support_level:AdapterSupportLevel; world_kind:FormalWorldKind; description:str|None=None; limitations:tuple[str,...]=(); required_boundary:HandoffKind=HandoffKind.NONE; metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def to_dict(self): return {**self.__dict__,"operation":self.operation.value,"support_level":self.support_level.value,"world_kind":self.world_kind.value,"limitations":list(self.limitations),"required_boundary":self.required_boundary.value}
 @classmethod
 def from_dict(c,d): return c(str(d["capability_id"]),str(d["adapter_id"]),AdapterOperation(str(d.get("operation","UNKNOWN"))),AdapterSupportLevel(str(d.get("support_level","UNKNOWN"))),FormalWorldKind(str(d.get("world_kind","UNKNOWN"))),_s(d.get("description")),tuple(d.get("limitations",())),HandoffKind(str(d.get("required_boundary","NONE"))),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
@dataclass
class FormalWorldParseResult:
 parse_id:str; adapter_id:str; world_kind:FormalWorldKind; source_object_id:str|None=None; source_kind:str|None=None; raw_text:str|None=None; parse_status:ParseStatus=ParseStatus.UNKNOWN; parsed_object:dict[str,Any]=field(default_factory=dict); symbols:tuple[str,...]=(); variables:tuple[str,...]=(); operators:tuple[str,...]=(); warnings:tuple[str,...]=(); criticals:tuple[str,...]=(); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def to_dict(self): return {**self.__dict__,"world_kind":self.world_kind.value,"parse_status":self.parse_status.value,"symbols":list(self.symbols),"variables":list(self.variables),"operators":list(self.operators),"warnings":list(self.warnings),"criticals":list(self.criticals)}
 @classmethod
 def from_dict(c,d): return c(str(d["parse_id"]),str(d["adapter_id"]),FormalWorldKind(str(d.get("world_kind","UNKNOWN"))),_s(d.get("source_object_id")),_s(d.get("source_kind")),_s(d.get("raw_text")),ParseStatus(str(d.get("parse_status","UNKNOWN"))),dict(d.get("parsed_object",{})),tuple(d.get("symbols",())),tuple(d.get("variables",())),tuple(d.get("operators",())),tuple(d.get("warnings",())),tuple(d.get("criticals",())),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
@dataclass
class FormalWorldNormalizeResult:
 normalize_id:str; adapter_id:str; world_kind:FormalWorldKind; parse_id:str|None=None; source_object_id:str|None=None; normalize_status:NormalizeStatus=NormalizeStatus.UNKNOWN; normalized_text:str|None=None; normalized_object:dict[str,Any]=field(default_factory=dict); canonical_key:str|None=None; warnings:tuple[str,...]=(); criticals:tuple[str,...]=(); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def to_dict(self): return {**self.__dict__,"world_kind":self.world_kind.value,"normalize_status":self.normalize_status.value,"warnings":list(self.warnings),"criticals":list(self.criticals)}
 @classmethod
 def from_dict(c,d): return c(str(d["normalize_id"]),str(d["adapter_id"]),FormalWorldKind(str(d.get("world_kind","UNKNOWN"))),_s(d.get("parse_id")),_s(d.get("source_object_id")),NormalizeStatus(str(d.get("normalize_status","UNKNOWN"))),_s(d.get("normalized_text")),dict(d.get("normalized_object",{})),_s(d.get("canonical_key")),tuple(d.get("warnings",())),tuple(d.get("criticals",())),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
@dataclass
class FormalWorldValidationResult:
 validation_id:str; adapter_id:str; world_kind:FormalWorldKind; parse_id:str|None=None; normalize_id:str|None=None; source_object_id:str|None=None; validation_status:ValidationStatus=ValidationStatus.UNKNOWN; valid_shape:bool=False; validation_notes:tuple[str,...]=(); required_tasks:tuple[str,...]=(); inherited_certificate_id:str|None=None; inherited_terminal_form:TerminalForm|None=None; inherited_verifier_boundary:bool=False; warnings:tuple[str,...]=(); criticals:tuple[str,...]=(); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def has_inherited_boundary(self): return bool(self.inherited_certificate_id and self.inherited_terminal_form and self.inherited_verifier_boundary)
 def to_dict(self): return {**self.__dict__,"world_kind":self.world_kind.value,"validation_status":self.validation_status.value,"validation_notes":list(self.validation_notes),"required_tasks":list(self.required_tasks),"inherited_terminal_form":self.inherited_terminal_form.value if self.inherited_terminal_form else None,"warnings":list(self.warnings),"criticals":list(self.criticals)}
 @classmethod
 def from_dict(c,d): return c(str(d["validation_id"]),str(d["adapter_id"]),FormalWorldKind(str(d.get("world_kind","UNKNOWN"))),_s(d.get("parse_id")),_s(d.get("normalize_id")),_s(d.get("source_object_id")),ValidationStatus(str(d.get("validation_status","UNKNOWN"))),bool(d.get("valid_shape",False)),tuple(d.get("validation_notes",())),tuple(d.get("required_tasks",())),_s(d.get("inherited_certificate_id")), _term(d.get("inherited_terminal_form")),bool(d.get("inherited_verifier_boundary",False)),tuple(d.get("warnings",())),tuple(d.get("criticals",())),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
@dataclass
class FormalWorldTask:
 task_id:str; adapter_id:str; world_kind:FormalWorldKind; task_kind:FormalWorldTaskKind; source_object_id:str|None=None; parse_id:str|None=None; normalize_id:str|None=None; validation_id:str|None=None; title:str|None=None; description:str|None=None; route:str|None=None; priority:float=0.0; required_handoff:HandoffKind=HandoffKind.NONE; required_adapter:str|None=None; warnings:tuple[str,...]=(); criticals:tuple[str,...]=(); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def to_dict(self): return {**self.__dict__,"world_kind":self.world_kind.value,"task_kind":self.task_kind.value,"required_handoff":self.required_handoff.value,"warnings":list(self.warnings),"criticals":list(self.criticals)}
 @classmethod
 def from_dict(c,d): return c(str(d["task_id"]),str(d["adapter_id"]),FormalWorldKind(str(d.get("world_kind","UNKNOWN"))),FormalWorldTaskKind(str(d.get("task_kind","UNKNOWN"))),_s(d.get("source_object_id")),_s(d.get("parse_id")),_s(d.get("normalize_id")),_s(d.get("validation_id")),_s(d.get("title")),_s(d.get("description")),_s(d.get("route")),float(d.get("priority",0)),HandoffKind(str(d.get("required_handoff","NONE"))),_s(d.get("required_adapter")),tuple(d.get("warnings",())),tuple(d.get("criticals",())),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
@dataclass
class FormalWorldHandoff:
 handoff_id:str; adapter_id:str; world_kind:FormalWorldKind; handoff_kind:HandoffKind; status:HandoffStatus=HandoffStatus.REQUESTED; source_object_id:str|None=None; task_id:str|None=None; artifact_id:str|None=None; certificate_id:str|None=None; terminal_form:TerminalForm|None=None; verifier_boundary_crossed:bool=False; notes:tuple[str,...]=(); warnings:tuple[str,...]=(); criticals:tuple[str,...]=(); metadata:dict[str,Any]=field(default_factory=dict); advisory:bool=True
 def crosses_boundary(self): return self.status==HandoffStatus.COMPLETED_WITH_BOUNDARY and bool(self.certificate_id and self.terminal_form and self.verifier_boundary_crossed)
 def to_dict(self): return {**self.__dict__,"world_kind":self.world_kind.value,"handoff_kind":self.handoff_kind.value,"status":self.status.value,"terminal_form":self.terminal_form.value if self.terminal_form else None,"notes":list(self.notes),"warnings":list(self.warnings),"criticals":list(self.criticals)}
 @classmethod
 def from_dict(c,d): return c(str(d["handoff_id"]),str(d["adapter_id"]),FormalWorldKind(str(d.get("world_kind","UNKNOWN"))),HandoffKind(str(d.get("handoff_kind","UNKNOWN"))),HandoffStatus(str(d.get("status","REQUESTED"))),_s(d.get("source_object_id")),_s(d.get("task_id")),_s(d.get("artifact_id")),_s(d.get("certificate_id")),_term(d.get("terminal_form")),bool(d.get("verifier_boundary_crossed",False)),tuple(d.get("notes",())),tuple(d.get("warnings",())),tuple(d.get("criticals",())),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
@dataclass
class FormalWorldAdapterReport:
 report_id:str; specs:list[FormalWorldAdapterSpec]=field(default_factory=list); capabilities:list[FormalWorldAdapterCapability]=field(default_factory=list); parses:list[FormalWorldParseResult]=field(default_factory=list); normalizations:list[FormalWorldNormalizeResult]=field(default_factory=list); validations:list[FormalWorldValidationResult]=field(default_factory=list); tasks:list[FormalWorldTask]=field(default_factory=list); handoffs:list[FormalWorldHandoff]=field(default_factory=list); status:FormalWorldAdapterReportStatus=FormalWorldAdapterReportStatus.EMPTY; created_at:str=field(default_factory=lambda:_now()); summary:dict[str,Any]=field(default_factory=dict); metadata:dict[str,Any]=field(default_factory=lambda:{"adapter_advisory_only":True}); advisory:bool=True
 def spec_count(self): return len(self.specs)
 def capability_count(self): return len(self.capabilities)
 def parse_count(self): return len(self.parses)
 def normalization_count(self): return len(self.normalizations)
 def validation_count(self): return len(self.validations)
 def task_count(self): return len(self.tasks)
 def handoff_count(self): return len(self.handoffs)
 def critical_count(self): return sum(len(x.criticals) for x in self.parses+self.normalizations+self.validations+self.tasks+self.handoffs)
 def summarize(self):
  self.summary={"spec_total":len(self.specs),"capability_total":len(self.capabilities),"parse_total":len(self.parses),"normalization_total":len(self.normalizations),"validation_total":len(self.validations),"task_total":len(self.tasks),"handoff_total":len(self.handoffs),"world_kind_counts":dict(Counter(x.world_kind.value for x in self.parses)),"parse_status_counts":dict(Counter(x.parse_status.value for x in self.parses)),"normalize_status_counts":dict(Counter(x.normalize_status.value for x in self.normalizations)),"validation_status_counts":dict(Counter(x.validation_status.value for x in self.validations)),"task_kind_counts":dict(Counter(x.task_kind.value for x in self.tasks)),"handoff_kind_counts":dict(Counter(x.handoff_kind.value for x in self.handoffs)),"boundary_crossed_count":sum(x.crosses_boundary() for x in self.handoffs),"critical_count":self.critical_count()}; return dict(self.summary)
 def to_dict(self): return {"report_id":self.report_id,"specs":[x.to_dict() for x in self.specs],"capabilities":[x.to_dict() for x in self.capabilities],"parses":[x.to_dict() for x in self.parses],"normalizations":[x.to_dict() for x in self.normalizations],"validations":[x.to_dict() for x in self.validations],"tasks":[x.to_dict() for x in self.tasks],"handoffs":[x.to_dict() for x in self.handoffs],"status":self.status.value,"created_at":self.created_at,"summary":dict(self.summary),"metadata":dict(self.metadata),"advisory":self.advisory}
 @classmethod
 def from_dict(c,d): return c(str(d["report_id"]),[FormalWorldAdapterSpec.from_dict(x) for x in d.get("specs",[])],[FormalWorldAdapterCapability.from_dict(x) for x in d.get("capabilities",[])],[FormalWorldParseResult.from_dict(x) for x in d.get("parses",[])],[FormalWorldNormalizeResult.from_dict(x) for x in d.get("normalizations",[])],[FormalWorldValidationResult.from_dict(x) for x in d.get("validations",[])],[FormalWorldTask.from_dict(x) for x in d.get("tasks",[])],[FormalWorldHandoff.from_dict(x) for x in d.get("handoffs",[])],FormalWorldAdapterReportStatus(str(d.get("status","EMPTY"))),str(d.get("created_at") or _now()),dict(d.get("summary",{})),dict(d.get("metadata",{})),bool(d.get("advisory",True)))
 def to_json(self): return _j(self.to_dict())
 @classmethod
 def from_json(c,t): return c.from_dict(json.loads(t))
 def write_json(self,p): _w(p,self.to_json()+"\n")
 @classmethod
 def read_json(c,p): return c.from_json(Path(p).read_text())
 def write_jsonl(self,p): _w(p,self.to_json()+"\n")
 @classmethod
 def read_jsonl(c,p): return [c.from_json(x) for x in Path(p).read_text().splitlines() if x.strip()]
def make_adapter_spec_id(*x): return content_id("adapter-spec",x)
def make_adapter_capability_id(*x): return content_id("adapter-capability",x)
def make_formal_world_parse_id(*x): return content_id("formal-world-parse",x)
def make_formal_world_normalize_id(*x): return content_id("formal-world-normalize",x)
def make_formal_world_validation_id(*x): return content_id("formal-world-validation",x)
def make_formal_world_task_id(*x): return content_id("formal-world-task",x)
def make_formal_world_handoff_id(*x): return content_id("formal-world-handoff",x)
def make_formal_world_adapter_report_id(*x): return content_id("formal-world-adapter-report",x)
def default_formal_world_adapter_specs():
 def s(name,world,ops,tool=False): return FormalWorldAdapterSpec(make_adapter_spec_id(name,world),world,name,supported_operations=tuple(x.value for x in ops),requires_external_tool=tool,metadata={"adapter_advisory_only":True})
 return [s("magma_equational",FormalWorldKind.MAGMA_EQUATIONAL,(AdapterOperation.PARSE,AdapterOperation.NORMALIZE,AdapterOperation.VALIDATE,AdapterOperation.EMIT_PROOF_TASK,AdapterOperation.EMIT_COUNTERMODEL_TASK,AdapterOperation.EMIT_FINITE_VALIDATION_TASK,AdapterOperation.EMIT_FORMALIZATION_TASK,AdapterOperation.HANDOFF_TO_FINITE_VALIDATOR)),s("lean_like",FormalWorldKind.LEAN_LIKE,(AdapterOperation.PARSE,AdapterOperation.NORMALIZE,AdapterOperation.VALIDATE,AdapterOperation.EMIT_PROOF_TASK,AdapterOperation.EMIT_FORMALIZATION_TASK,AdapterOperation.HANDOFF_TO_VERIFIER),True),s("proof_text",FormalWorldKind.PROOF_TEXT,(AdapterOperation.PARSE,AdapterOperation.NORMALIZE,AdapterOperation.VALIDATE,AdapterOperation.EMIT_DIGESTION_TASK,AdapterOperation.EMIT_FORMALIZATION_TASK,AdapterOperation.EMIT_REVIEW_TASK)),s("finite_structure",FormalWorldKind.FINITE_STRUCTURE,(AdapterOperation.PARSE,AdapterOperation.NORMALIZE,AdapterOperation.VALIDATE,AdapterOperation.EMIT_COUNTERMODEL_TASK,AdapterOperation.HANDOFF_TO_FINITE_VALIDATOR)),s("generic_formal_world",FormalWorldKind.GENERIC_FORMAL,(AdapterOperation.PARSE,AdapterOperation.NORMALIZE,AdapterOperation.VALIDATE,AdapterOperation.EMIT_ADAPTER_TASK,AdapterOperation.EMIT_REVIEW_TASK))]
def default_formal_world_adapter_capabilities(specs=None):
 out=[]
 for s in specs or default_formal_world_adapter_specs():
  for op in map(AdapterOperation,s.supported_operations):
   if op==AdapterOperation.HANDOFF_TO_VERIFIER: lvl,b=AdapterSupportLevel.REQUIRES_EXTERNAL_VERIFIER,HandoffKind.VERIFIER
   elif op==AdapterOperation.HANDOFF_TO_IMPORTER: lvl,b=AdapterSupportLevel.REQUIRES_TRUSTED_IMPORTER,HandoffKind.TRUSTED_IMPORTER
   elif op==AdapterOperation.HANDOFF_TO_FINITE_VALIDATOR: lvl,b=AdapterSupportLevel.REQUIRES_FINITE_VALIDATOR,HandoffKind.FINITE_VALIDATOR
   else: lvl,b=AdapterSupportLevel.ADVISORY_ONLY,HandoffKind.NONE
   out.append(FormalWorldAdapterCapability(make_adapter_capability_id(s.adapter_id,op.value),s.adapter_id,op,lvl,s.world_kind,required_boundary=b,metadata={"adapter_advisory_only":True}))
 return out
def detect_formal_world_kind(x):
 d=x if isinstance(x,Mapping) else {}; t=(str(x) if not isinstance(x,Mapping) else _j(x)).lower()
 if any(k in d for k in ("table","carrier","operation_table","multiplication_table","witness")) or "operation table" in t or "finite carrier" in t:return FormalWorldKind.FINITE_STRUCTURE
 if any(k in d for k in ("source","target","equation1","equation2")) or (("=>" in t or "implies" in t) and any(k in t for k in ("=","*","◇"))):return FormalWorldKind.MAGMA_EQUATIONAL
 if any(k in t for k in ("assert","declare-fun","check-sat","set-logic")):return FormalWorldKind.SMT_LIKE
 if any(k in t for k in ("import ","namespace "," := "," by","variable ","example ","theorem ","lemma ")) and ("proof" not in t or "by" in t or ":=" in t):return FormalWorldKind.LEAN_LIKE
 if any(k in t for k in ("graph","node","edge","adjacency")):return FormalWorldKind.GRAPH_LIKE
 if any(k in t for k in ("morphism","functor","natural transformation","adjunction")):return FormalWorldKind.CATEGORY_LIKE
 if any(k in t for k in ("proof","suppose","therefore","hence","contradiction","lemma","theorem")):return FormalWorldKind.PROOF_TEXT
 if t.strip(): return FormalWorldKind.GENERIC_FORMAL
 return FormalWorldKind.UNKNOWN
def adapter_spec_for_world(w,specs=None):
 specs=list(specs or default_formal_world_adapter_specs())
 return next((x for x in specs if x.world_kind==w),next(x for x in specs if x.world_kind==FormalWorldKind.GENERIC_FORMAL))
def parse_formal_world_input(x,*,adapter_spec=None,source_object_id=None,source_kind=None):
 spec=adapter_spec or adapter_spec_for_world(detect_formal_world_kind(x)); f={FormalWorldKind.MAGMA_EQUATIONAL:parse_magma_equational,FormalWorldKind.LEAN_LIKE:parse_lean_like,FormalWorldKind.PROOF_TEXT:parse_proof_text,FormalWorldKind.FINITE_STRUCTURE:parse_finite_structure}.get(spec.world_kind,parse_generic_formal)
 return f(x,spec,source_object_id,source_kind)
def parse_magma_equational(x,spec=None,oid=None,sk=None):
 d=x if isinstance(x,Mapping) else {}; text=str(d.get("text") or d.get("raw") or x if not isinstance(x,Mapping) else d.get("text") or d.get("raw") or "")
 src=d.get("source") or d.get("equation1") or d.get("eq1") or d.get("lhs"); tgt=d.get("target") or d.get("equation2") or d.get("eq2") or d.get("rhs")
 if not (src or tgt) and text:
  parts=re.split(r"\s*(?:=>|implies)\s*",text,maxsplit=1)
  if len(parts)==2: src,tgt=parts
 vars=tuple(dict.fromkeys(re.findall(r"\b[a-z]\b",f"{src or ''} {tgt or ''}"))); ops=tuple(x for x in ("*","◇") if x in f"{src or ''} {tgt or ''}")
 st=ParseStatus.EMPTY if not (src or tgt or text) else ParseStatus.PARSED if src and tgt else ParseStatus.PARTIAL if src or tgt else ParseStatus.FAILED
 po={"source_text":_s(src),"target_text":_s(tgt),"equations":[z for z in (_s(src),_s(tgt)) if z],"implication_like":bool(src and tgt)}
 return FormalWorldParseResult(make_formal_world_parse_id("magma",oid,text,src,tgt),spec.adapter_id if spec else "magma_equational",FormalWorldKind.MAGMA_EQUATIONAL,oid,sk,text,st,po,variables=vars,operators=ops,metadata=dict(d))
def parse_lean_like(x,spec=None,oid=None,sk=None):
 text=str(x.get("text") or x.get("raw") or _j(x) if isinstance(x,Mapping) else x); names=re.findall(r"\b(?:theorem|lemma|example)\s+([A-Za-z_][A-Za-z0-9_]*)",text); imports=re.findall(r"^\s*import\s+([^\n]+)",text,re.M); ns=re.findall(r"\bnamespace\s+([A-Za-z_][A-Za-z0-9_]*)",text)
 st=ParseStatus.EMPTY if not text.strip() else ParseStatus.PARSED if names or imports else ParseStatus.PARTIAL if detect_formal_world_kind(text)==FormalWorldKind.LEAN_LIKE else ParseStatus.FAILED
 return FormalWorldParseResult(make_formal_world_parse_id("lean",oid,text),spec.adapter_id if spec else "lean_like",FormalWorldKind.LEAN_LIKE,oid,sk,text,st,{"names":names,"imports":imports,"namespaces":ns,"has_by":" by" in text,"has_sorry":"sorry" in text},symbols=tuple(names),warnings=("contains_sorry",) if "sorry" in text else (),metadata=x if isinstance(x,Mapping) else {})
def parse_proof_text(x,spec=None,oid=None,sk=None):
 text=str(x.get("text") or x.get("raw") or _j(x) if isinstance(x,Mapping) else x); low=text.lower(); markers=tuple(k for k in ("proof","suppose","therefore","hence","lemma","theorem","contradiction") if k in low); st=ParseStatus.EMPTY if not text.strip() else ParseStatus.PARSED if markers else ParseStatus.FAILED
 return FormalWorldParseResult(make_formal_world_parse_id("proof-text",oid,text),spec.adapter_id if spec else "proof_text",FormalWorldKind.PROOF_TEXT,oid,sk,text,st,{"markers":list(markers)},symbols=markers,metadata=x if isinstance(x,Mapping) else {})
def parse_finite_structure(x,spec=None,oid=None,sk=None):
 d=dict(x) if isinstance(x,Mapping) else {}; carrier=d.get("carrier",()); table=d.get("table") or d.get("operation_table") or d.get("multiplication_table"); st=ParseStatus.PARSED if table is not None or carrier else ParseStatus.PARTIAL if d else ParseStatus.EMPTY
 return FormalWorldParseResult(make_formal_world_parse_id("finite",oid,d),spec.adapter_id if spec else "finite_structure",FormalWorldKind.FINITE_STRUCTURE,oid,sk,_j(d) if d else _s(x),st,{"carrier_size":len(carrier) if hasattr(carrier,"__len__") else None,"table":table,"witness":d.get("witness")},metadata=d)
def parse_generic_formal(x,spec=None,oid=None,sk=None):
 d=dict(x) if isinstance(x,Mapping) else {"text":str(x)}; st=ParseStatus.EMPTY if not _j(d).strip("{}\" ") else ParseStatus.PARTIAL
 return FormalWorldParseResult(make_formal_world_parse_id("generic",oid,d),spec.adapter_id if spec else "generic_formal_world",spec.world_kind if spec else detect_formal_world_kind(d),oid,sk,d.get("text"),st,d,symbols=tuple(d.keys()),metadata=d)
def normalize_formal_world_parse(p):
 return {FormalWorldKind.MAGMA_EQUATIONAL:normalize_magma_equational_parse,FormalWorldKind.LEAN_LIKE:normalize_lean_like_parse,FormalWorldKind.PROOF_TEXT:normalize_proof_text_parse,FormalWorldKind.FINITE_STRUCTURE:normalize_finite_structure_parse}.get(p.world_kind,normalize_generic_formal_parse)(p)
def _clean(s): return re.sub(r"\s+"," ",str(s or "").replace("◇","*").strip().lower())
def normalize_magma_equational_parse(p):
 src=_clean(p.parsed_object.get("source_text")); tgt=_clean(p.parsed_object.get("target_text")); seen={}
 def canon(t):
  def repl(m): seen.setdefault(m.group(),f"v{len(seen)}"); return seen[m.group()]
  return re.sub(r"\b[a-z]\b",repl,t)
 obj={"source":canon(src),"target":canon(tgt)}; txt=f"{obj['source']} => {obj['target']}".strip(); st=NormalizeStatus.NORMALIZED if src and tgt else NormalizeStatus.PARTIAL if src or tgt else NormalizeStatus.EMPTY
 return FormalWorldNormalizeResult(make_formal_world_normalize_id(p.parse_id,txt),p.adapter_id,p.world_kind,p.parse_id,p.source_object_id,st,txt,obj,content_id("magma-canonical",obj),metadata=p.metadata)
def normalize_lean_like_parse(p):
 txt=re.sub(r"\s+"," ",p.raw_text or "").strip(); return FormalWorldNormalizeResult(make_formal_world_normalize_id(p.parse_id,txt),p.adapter_id,p.world_kind,p.parse_id,p.source_object_id,NormalizeStatus.NORMALIZED if txt else NormalizeStatus.EMPTY,txt,dict(p.parsed_object),content_id("lean-canonical",txt),metadata=p.metadata)
def normalize_proof_text_parse(p):
 txt=_clean(p.raw_text); return FormalWorldNormalizeResult(make_formal_world_normalize_id(p.parse_id,txt),p.adapter_id,p.world_kind,p.parse_id,p.source_object_id,NormalizeStatus.NORMALIZED if txt else NormalizeStatus.EMPTY,txt,dict(p.parsed_object),content_id("proof-text-canonical",txt),metadata=p.metadata)
def normalize_finite_structure_parse(p):
 obj=dict(p.parsed_object); return FormalWorldNormalizeResult(make_formal_world_normalize_id(p.parse_id,obj),p.adapter_id,p.world_kind,p.parse_id,p.source_object_id,NormalizeStatus.NORMALIZED if obj else NormalizeStatus.EMPTY,_j(obj),obj,content_id("finite-canonical",obj),metadata=p.metadata)
def normalize_generic_formal_parse(p):
 obj=dict(p.parsed_object); return FormalWorldNormalizeResult(make_formal_world_normalize_id(p.parse_id,obj),p.adapter_id,p.world_kind,p.parse_id,p.source_object_id,NormalizeStatus.PARTIAL if obj else NormalizeStatus.EMPTY,_j(obj),obj,content_id("generic-canonical",obj),metadata=p.metadata)
def validate_formal_world_normalization(n,p=None):
 md=dict(n.metadata); cert=_s(md.get("certificate_id")); tf=_term(md.get("terminal_form")); vb=bool(md.get("verifier_boundary_crossed",False)); notes=[]; tasks=[]
 if n.world_kind==FormalWorldKind.MAGMA_EQUATIONAL:
  src=n.normalized_object.get("source"); tgt=n.normalized_object.get("target"); balanced=lambda s:str(s).count("(")==str(s).count(")")
  valid=bool(src and tgt and balanced(src) and balanced(tgt)); st=ValidationStatus.VALID_SHAPE if valid else ValidationStatus.PARTIAL; tasks=["PROOF_TASK","COUNTERMODEL_TASK"]
 elif n.world_kind==FormalWorldKind.LEAN_LIKE:
  valid=bool(n.normalized_object.get("names")); st=ValidationStatus.NEEDS_VERIFIER if valid else ValidationStatus.PARTIAL; tasks=["PROOF_TASK"]; 
  if n.normalized_object.get("has_sorry"): notes.append("contains_sorry")
 elif n.world_kind==FormalWorldKind.PROOF_TEXT:
  valid=bool(n.normalized_object.get("markers")); st=ValidationStatus.NEEDS_FORMALIZATION if valid else ValidationStatus.PARTIAL; tasks=["DIGESTION_TASK","FORMALIZATION_TASK"]
 elif n.world_kind==FormalWorldKind.FINITE_STRUCTURE:
  valid=bool(n.normalized_object.get("table") is not None or n.normalized_object.get("carrier_size")); st=ValidationStatus.NEEDS_FINITE_VALIDATOR if valid else ValidationStatus.PARTIAL; tasks=["FINITE_VALIDATION_TASK"]
 else: valid=False; st=ValidationStatus.PARTIAL if n.normalized_object else ValidationStatus.UNSUPPORTED; tasks=["ADAPTER_TASK","REVIEW_TASK"]
 return FormalWorldValidationResult(make_formal_world_validation_id(n.normalize_id,st.value),n.adapter_id,n.world_kind,n.parse_id,n.normalize_id,n.source_object_id,st,valid,tuple(notes),tuple(tasks),cert,tf,vb,metadata=md)
def tasks_from_validation(v,p=None,n=None):
 ks=[]
 if v.world_kind==FormalWorldKind.MAGMA_EQUATIONAL: ks=[FormalWorldTaskKind.PROOF_TASK,FormalWorldTaskKind.COUNTERMODEL_TASK]+([FormalWorldTaskKind.FINITE_VALIDATION_TASK] if any(k in _j(v.metadata).lower() for k in ("table","witness")) else [])
 elif v.world_kind==FormalWorldKind.LEAN_LIKE: ks=[FormalWorldTaskKind.PROOF_TASK]+([FormalWorldTaskKind.REVIEW_TASK] if p and "contains_sorry" in p.warnings else [])
 elif v.world_kind==FormalWorldKind.PROOF_TEXT: ks=[FormalWorldTaskKind.DIGESTION_TASK,FormalWorldTaskKind.FORMALIZATION_TASK,FormalWorldTaskKind.REVIEW_TASK]
 elif v.world_kind==FormalWorldKind.FINITE_STRUCTURE: ks=[FormalWorldTaskKind.FINITE_VALIDATION_TASK,FormalWorldTaskKind.COUNTERMODEL_TASK]
 else: ks=[FormalWorldTaskKind.ADAPTER_TASK,FormalWorldTaskKind.REVIEW_TASK]
 out=[]
 for k in ks:
  h=HandoffKind.VERIFIER if k==FormalWorldTaskKind.PROOF_TASK else HandoffKind.FINITE_VALIDATOR if k==FormalWorldTaskKind.FINITE_VALIDATION_TASK else HandoffKind.NONE
  out.append(FormalWorldTask(make_formal_world_task_id(v.validation_id,k.value),v.adapter_id,v.world_kind,k,v.source_object_id,v.parse_id,v.normalize_id,v.validation_id,k.value.replace("_"," ").title(),required_handoff=h,required_adapter="formal-world adapter" if k==FormalWorldTaskKind.ADAPTER_TASK else None,metadata={"adapter_advisory_only":True}))
 return out
def handoffs_from_tasks(tasks,validations=()):
 by={v.validation_id:v for v in validations}; out=[]
 for t in tasks:
  if t.required_handoff==HandoffKind.NONE: continue
  v=by.get(t.validation_id); md=dict(v.metadata) if v else {}; cert=_s(md.get("certificate_id")); tf=_term(md.get("terminal_form")); vb=bool(md.get("verifier_boundary_crossed",False)); art=_s(md.get("artifact_id")); st=HandoffStatus.COMPLETED_WITH_BOUNDARY if cert and tf and vb else HandoffStatus.READY if art else HandoffStatus.REQUESTED
  out.append(FormalWorldHandoff(make_formal_world_handoff_id(t.task_id,t.required_handoff.value),t.adapter_id,t.world_kind,t.required_handoff,st,t.source_object_id,t.task_id,art,cert,tf,vb,metadata={"adapter_advisory_only":True,**md}))
 return out
def formal_world_inputs_from_object(o):
 from mathgraph.domain_claims import DomainClaim
 if isinstance(o,Mapping): return [dict(o)]
 if isinstance(o,str): return [{"text":o,"source_kind":"text"}]
 if isinstance(o,DomainClaim): return [{"source_object_id":o.claim_id,"source_kind":"DomainClaim","text":o.raw,"source":o.source,"target":o.target,"metadata":o.metadata}]
 if hasattr(o,"to_dict"):
  d=o.to_dict(); oid=next((d.get(k) for k in ("claim_id","entry_id","answer_id","candidate_id","descriptor_id","role_id","conjecture_id","reason_id","rule_id","episode_id","trace_id","stage_id","experience_id","report_id") if d.get(k)),None)
  if o.__class__.__name__.endswith("Report"):
   rows=[]
   for key in ("answers","typed_projection_candidates","role_objects","definition_candidates","conjecture_candidates","candidates","reason_nodes","rules","episodes","stages"):
    for x in getattr(o,key,[]) or []: rows+=formal_world_inputs_from_object(x)
   if getattr(o,"store",None): rows += [y for x in getattr(o.store,"episodes",[]) for y in formal_world_inputs_from_object(x)]
   return rows or [{"source_object_id":oid,"source_kind":o.__class__.__name__,"text":_j(d),"metadata":d}]
  return [{"source_object_id":oid,"source_kind":o.__class__.__name__,"text":d.get("raw") or d.get("statement") or d.get("text") or d.get("description") or _j(d),"source":d.get("source"),"target":d.get("target"),"statement":d.get("statement"),"route":d.get("route"),"metadata":d,**{k:d.get(k) for k in ("certificate_id","terminal_form","verifier_boundary_crossed") if d.get(k) is not None}}]
 return []
def build_formal_world_adapter_report(objects=(),specs=(),*,include_default_specs=True,parse=True,normalize=True,validate=True,emit_tasks=True,emit_handoffs=True):
 ss=list(specs)+(default_formal_world_adapter_specs() if include_default_specs else []); seen={s.adapter_id:s for s in ss}; ss=list(seen.values()); caps=default_formal_world_adapter_capabilities(ss); inputs=[x for o in objects for x in formal_world_inputs_from_object(o)]; ps=[]; ns=[]; vs=[]; ts=[]; hs=[]
 if parse:
  for d in inputs:
   w=detect_formal_world_kind(d); ps.append(parse_formal_world_input(d,adapter_spec=adapter_spec_for_world(w,ss),source_object_id=_s(d.get("source_object_id")),source_kind=_s(d.get("source_kind"))))
 if normalize: ns=[normalize_formal_world_parse(p) for p in ps]
 if validate: vs=[validate_formal_world_normalization(n,next((p for p in ps if p.parse_id==n.parse_id),None)) for n in ns]
 if emit_tasks: ts=[t for v in vs for t in tasks_from_validation(v,next((p for p in ps if p.parse_id==v.parse_id),None),next((n for n in ns if n.normalize_id==v.normalize_id),None))]
 if emit_handoffs: hs=handoffs_from_tasks(ts,vs)
 r=FormalWorldAdapterReport(make_formal_world_adapter_report_id([x.parse_id for x in ps]),ss,caps,ps,ns,vs,ts,hs); r.summarize(); r.status=FormalWorldAdapterReportStatus.HAS_CRITICALS if r.critical_count() else FormalWorldAdapterReportStatus.HANDOFFS_EMITTED if hs else FormalWorldAdapterReportStatus.TASKS_EMITTED if ts else FormalWorldAdapterReportStatus.VALIDATED if vs else FormalWorldAdapterReportStatus.NORMALIZED if ns else FormalWorldAdapterReportStatus.PARSED if ps else FormalWorldAdapterReportStatus.CAPABILITIES_REPORTED if caps else FormalWorldAdapterReportStatus.EMPTY; return r
def adapter_report_to_lawbook_candidates(r): return [LawbookEntry(make_lawbook_entry_id("adapter",r.report_id,x.handoff_id if isinstance(x,FormalWorldHandoff) else x.validation_id),LawbookEntryKind.ROUTE_RULE_ENTRY,LawbookEntryStatus.CANDIDATE,metadata={"formal_world_adapter_not_truth":True,"adapter_report_id":r.report_id,"adapter_advisory_only":True},advisory=True) for x in list(r.handoffs)+list(r.validations)]
def adapter_report_to_continuation_outputs(r): return [ContinuationActionOutput(make_continuation_output_id({"adapter":t.task_id}),"formal_world_adapters",ContinuationOutputKind.TASK,ContinuationActionStatus.ADVISORY_ONLY,task_payload={"task":t.task_kind.value.lower(),"task_id":t.task_id},advisory=True) for t in r.tasks]
def adapter_report_to_curriculum(r):
 stages=[CurriculumStage(make_curriculum_stage_id("adapter",x),CurriculumStageKind.RESIDUAL_REVIEW,CurriculumStageStatus.ADVISORY_ONLY,title=x,metadata={"adapter_advisory_only":True},advisory=True) for x in ("parse","normalize","validate","formalize","handoff","repair/review")]
 return ContinuationCurriculum(make_curriculum_id("adapter",r.report_id),strategy=CurriculumBuildStrategy.MIXED,stages=stages,status=CurriculumTraceStatus.ADVISORY_ONLY,metadata={"adapter_advisory_only":True})
def adapter_report_to_discovery_value_scores(r):
 out=[]
 for v in r.validations:
  val=.4 if v.valid_shape else .1; sig=DiscoveryValueSignal(content_id("adapter-signal",v.validation_id),DiscoveryValueSignalKind.REUSE_VALUE,val,source_object_kind=DiscoveryValueObjectKind.RAW_TASK); s=DiscoveryValueScore(content_id("adapter-score",v.validation_id),v.validation_id,DiscoveryValueObjectKind.RAW_TASK,signals=[sig],metadata={"adapter_advisory_only":True}); s.recompute(); out.append(s)
 return out
def adapter_report_to_process_episodes(r): return [ProcessEpisodeRecord(make_process_episode_id("adapter",v.validation_id),ProcessEpisodeStatus.ADVISORY_ONLY,contexts=[ProcessContextItem(content_id("adapter-context",v.validation_id),ProcessContextKind.RAW_EVENT,ProcessContextRole.ADVISORY_ONLY,v.validation_id)],advisory=True) for v in r.validations]
def adapter_report_to_structure_descriptors(r): return [structure_descriptor_from_mapping({"world_kind":s.world_kind.value,"operations":list(s.supported_operations)},object_id=s.adapter_id,object_kind=StructureObjectKind.FORMAL_WORLD) for s in r.specs]
def adapter_report_to_typed_projection_candidates(r): return [TypedProjectionCandidate(make_typed_projection_candidate_id("adapter",t.task_id),t.task_id,status=TypedProjectionStatus.NEEDS_REVIEW if t.task_kind==FormalWorldTaskKind.PROJECTION_TASK else TypedProjectionStatus.NEEDS_ADAPTER,compatibility=ProjectionCompatibility.NEEDS_ADAPTER,required_review=True,metadata={"adapter_advisory_only":True}) for t in r.tasks if t.task_kind in {FormalWorldTaskKind.PROJECTION_TASK,FormalWorldTaskKind.ADAPTER_TASK}]
def adapter_report_to_role_signatures(r): return [RoleSignature(make_role_signature_id("adapter",v.validation_id),RoleSourceKind.RAW_EVENT,v.validation_id,RoleObjectKind.PROCESS_ROLE,(v.world_kind.value.lower(),v.validation_status.value.lower()),metadata={"adapter_advisory_only":True}) for v in r.validations]
def adapter_report_to_analogy_sources(r): return [analogy_source_from_mapping(v.to_dict(),source_kind=AnalogySourceKind.RAW_EVENT,object_id=v.validation_id) for v in r.validations]
def adapter_report_to_habit_observations(r): return [HabitObservation(content_id("adapter-habit",v.validation_id),HabitObservationKind.RAW_EVENT,route="formal_world_adapter",outcome=HabitOutcome.ADVISORY_ONLY,object_id=v.validation_id,metadata={"adapter_advisory_only":True}) for v in r.validations]
def adapter_report_to_reason_observations(r): return [ReasonObservation(make_reason_observation_id("adapter",v.validation_id),ReasonObservationKind.RAW_EVENT,v.validation_id,"formal_world_adapters",*extract_atoms_from_mapping(v.to_dict()),metadata={"adapter_advisory_only":True}) for v in r.validations]
def adapter_report_to_structural_identity_objects(r): return [{"validation_id":v.validation_id,"world_kind":v.world_kind.value,"status":v.validation_status.value,"adapter_advisory_only":True} for v in r.validations]
def adapter_report_to_alchemical_trace(r):
 t=AlchemicalTrace(make_alchemical_trace_id("adapter",r.report_id))
 for p in (AlchemicalPhase.RAW_MATTER,AlchemicalPhase.CALCINATION,AlchemicalPhase.SOLUTION,AlchemicalPhase.DESCENSION,AlchemicalPhase.DISTILLATION): t.add_step(phase=p,status=AlchemicalStatus.ADVISORY_ONLY)
 return t
def adapter_report_to_agent_experiences(r,agent_id=None): return [AgentExperience(content_id("adapter-exp",v.validation_id),agent_id or "formal-world-adapters",None,None,"formal_world_adapter",None,AgentExperienceOutcome.ADVISORY_ONLY,metadata={"validation_id":v.validation_id}) for v in r.validations]
def adapter_report_to_route_telemetry_events(r): return [{"event_id":content_id("adapter-telemetry",t.task_id),"route_kind":"formal_world_adapter","outcome":t.task_kind.value,"adapter_advisory_only":True} for t in r.tasks]
def audit_adapter_spec(x): return [_f("CRITICAL","ADAPTER_SPEC_NON_ADVISORY","adapter spec non-advisory",x.adapter_id)] if not x.advisory else []
def audit_adapter_capability(x): return [_f("CRITICAL","ADAPTER_CAPABILITY_NON_ADVISORY","adapter capability non-advisory",x.capability_id)] if not x.advisory else []
def audit_parse_result(x):
 out=[]
 if not x.advisory: out.append(_f("CRITICAL","ADAPTER_PARSE_NON_ADVISORY","parse non-advisory",x.parse_id))
 if x.metadata.get("terminal_form") and x.parse_status==ParseStatus.PARSED: out.append(_f("CRITICAL","ADAPTER_PARSE_AS_PROOF","parse success represented as proof",x.parse_id))
 if x.parse_status==ParseStatus.FAILED: out.append(_f("WARNING","ADAPTER_PARSE_FAILED","parse failed",x.parse_id))
 return out
def audit_normalize_result(x):
 out=[]
 if not x.advisory: out.append(_f("CRITICAL","ADAPTER_NORMALIZE_NON_ADVISORY","normalization non-advisory",x.normalize_id))
 if x.metadata.get("terminal_form") and x.normalize_status==NormalizeStatus.NORMALIZED: out.append(_f("CRITICAL","ADAPTER_NORMALIZE_AS_PROOF","normalization represented as proof",x.normalize_id))
 return out
def audit_validation_result(x):
 out=[]
 if not x.advisory: out.append(_f("CRITICAL","ADAPTER_VALIDATION_NON_ADVISORY","validation non-advisory",x.validation_id))
 if x.inherited_terminal_form and not x.has_inherited_boundary(): out.append(_f("CRITICAL","ADAPTER_BAD_INHERITED_BOUNDARY","validation inherited boundary incomplete",x.validation_id))
 if x.metadata.get("verifier_boundary") and not x.has_inherited_boundary(): out.append(_f("CRITICAL","ADAPTER_VALIDATION_AS_BOUNDARY","validation represented as verifier boundary",x.validation_id))
 return out
def audit_formal_world_task(x):
 out=[]
 if not x.advisory: out.append(_f("CRITICAL","ADAPTER_TASK_NON_ADVISORY","task non-advisory",x.task_id))
 if x.metadata.get("certificate_id") or x.metadata.get("terminal_form"): out.append(_f("CRITICAL","ADAPTER_TASK_AS_TRUTH","task carries truth fields",x.task_id))
 return out
def audit_formal_world_handoff(x):
 out=[]
 if not x.advisory: out.append(_f("CRITICAL","ADAPTER_HANDOFF_NON_ADVISORY","handoff non-advisory",x.handoff_id))
 if x.status==HandoffStatus.COMPLETED_WITH_BOUNDARY and not x.crosses_boundary(): out.append(_f("CRITICAL","ADAPTER_BAD_HANDOFF_BOUNDARY","handoff boundary incomplete",x.handoff_id))
 if x.status==HandoffStatus.REQUESTED and not x.artifact_id: out.append(_f("WARNING","ADAPTER_HANDOFF_MISSING_ARTIFACT","handoff requested without artifact",x.handoff_id))
 return out
def audit_formal_world_adapter_report(r): return [y for xs in (r.specs,r.capabilities,r.parses,r.normalizations,r.validations,r.tasks,r.handoffs) for x in xs for y in (audit_adapter_spec(x) if isinstance(x,FormalWorldAdapterSpec) else audit_adapter_capability(x) if isinstance(x,FormalWorldAdapterCapability) else audit_parse_result(x) if isinstance(x,FormalWorldParseResult) else audit_normalize_result(x) if isinstance(x,FormalWorldNormalizeResult) else audit_validation_result(x) if isinstance(x,FormalWorldValidationResult) else audit_formal_world_task(x) if isinstance(x,FormalWorldTask) else audit_formal_world_handoff(x))]
def _term(x):
 try:return TerminalForm(str(x)) if x else None
 except ValueError:return None
def _s(x): return None if x is None else str(x)
def _now(): return datetime.now(timezone.utc).isoformat()
def _j(x): return json.dumps(x,sort_keys=True,separators=(",",":"),default=str)
def _w(p,t): path=Path(p); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(t,encoding="utf-8")
def _f(sev,code,msg,obj): return {"severity":sev,"code":code,"message":msg,"object_id":obj}
