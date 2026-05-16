#!/usr/bin/env python
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from mathgraph.agent_biography import AgentExperience
from mathgraph.alchemy import AlchemicalTrace
from mathgraph.continuation_curriculum import ContinuationCurriculum,CurriculumStage
from mathgraph.domain_claims import DomainClaim
from mathgraph.formal_world_adapters import *
from mathgraph.habit_rules import HabitFormationReport,HabitRule
from mathgraph.lawbook import LawbookEntry
from mathgraph.lawbook_query import LawbookQueryReport
from mathgraph.process_memory import ProcessEpisodeRecord,ProcessMemoryReport
from mathgraph.projection import ProjectionCandidate
from mathgraph.proof_digestion import ProofDigestionTrace
from mathgraph.reason_compression import ReasonCompressionReport,ReasonNode
from mathgraph.roadmap_alignment import check_roadmap_alignment
from mathgraph.role_objects import RoleConjectureCandidate,RoleDefinitionCandidate,RoleObject,RoleObjectReport
from mathgraph.structural_analogy import StructuralAnalogyCandidate,StructuralAnalogyReport
from mathgraph.structure_registry import StructureDescriptor,StructureRegistryReport,TypedProjectionCandidate
from mathgraph.verifier_feedback import RepairLoopTrace,VerifierFeedback
def main(argv=None):
 p=argparse.ArgumentParser()
 p.add_argument("--input-text",action="append",default=[])
 for n in ("input-json","adapter-spec-json","domain-claim-json","lawbook-entry-json","lawbook-query-report-json","structure-report-json","role-report-json","analogy-report-json","reason-report-json","habit-report-json","process-memory-report-json","proof-digestion-json","repair-trace-json","curriculum-json","alchemical-trace-json","raw-event-json"): p.add_argument("--"+n,action="append",default=[])
 for n in ("input-jsonl","adapter-spec-jsonl","projection-candidates-jsonl","typed-projections-jsonl","structure-descriptors-jsonl","role-objects-jsonl","role-definitions-jsonl","role-conjectures-jsonl","analogy-candidates-jsonl","reason-nodes-jsonl","habit-rules-jsonl","process-episodes-jsonl","verifier-feedback-jsonl","agent-experiences-jsonl","route-telemetry-jsonl","raw-event-jsonl"): p.add_argument("--"+n)
 for n in ("default-specs","parse","normalize","validate","tasks","handoffs"): p.add_argument("--"+n,action=argparse.BooleanOptionalAction,default=True)
 for n in ("out-report-json","out-report-jsonl","out-specs-jsonl","out-capabilities-jsonl","out-parses-jsonl","out-normalizations-jsonl","out-validations-jsonl","out-tasks-jsonl","out-handoffs-jsonl","out-lawbook-candidates-jsonl","out-continuation-outputs-jsonl","out-curriculum-json","out-discovery-value-scores-jsonl","out-process-episodes-jsonl","out-structure-descriptors-jsonl","out-typed-projections-jsonl","out-role-signatures-jsonl","out-analogy-sources-jsonl","out-habit-observations-jsonl","out-reason-observations-jsonl","out-structural-objects-jsonl","out-alchemical-trace-json","out-agent-experiences-jsonl","out-route-telemetry-jsonl","alignment-report-json","alignment-report-md"): p.add_argument("--"+n)
 p.add_argument("--fail-on-critical",action="store_true"); a=p.parse_args(argv); specs=[_jr(x,FormalWorldAdapterSpec) for x in a.adapter_spec_json]+_jl(a.adapter_spec_jsonl,FormalWorldAdapterSpec); objs=list(a.input_text)+[json.loads(Path(x).read_text()) for x in a.input_json]+_jl(a.input_jsonl,dict)
 for paths,cls in ((a.domain_claim_json,DomainClaim),(a.lawbook_entry_json,LawbookEntry),(a.lawbook_query_report_json,LawbookQueryReport),(a.structure_report_json,StructureRegistryReport),(a.role_report_json,RoleObjectReport),(a.analogy_report_json,StructuralAnalogyReport),(a.reason_report_json,ReasonCompressionReport),(a.habit_report_json,HabitFormationReport),(a.process_memory_report_json,ProcessMemoryReport),(a.proof_digestion_json,ProofDigestionTrace),(a.repair_trace_json,RepairLoopTrace),(a.curriculum_json,ContinuationCurriculum),(a.alchemical_trace_json,AlchemicalTrace)):
  objs += [_jr(x,cls) for x in paths]
 objs += _jl(a.projection_candidates_jsonl,ProjectionCandidate)+_jl(a.typed_projections_jsonl,TypedProjectionCandidate)+_jl(a.structure_descriptors_jsonl,StructureDescriptor)+_jl(a.role_objects_jsonl,RoleObject)+_jl(a.role_definitions_jsonl,RoleDefinitionCandidate)+_jl(a.role_conjectures_jsonl,RoleConjectureCandidate)+_jl(a.analogy_candidates_jsonl,StructuralAnalogyCandidate)+_jl(a.reason_nodes_jsonl,ReasonNode)+_jl(a.habit_rules_jsonl,HabitRule)+_jl(a.process_episodes_jsonl,ProcessEpisodeRecord)+_jl(a.verifier_feedback_jsonl,VerifierFeedback)+_jl(a.agent_experiences_jsonl,AgentExperience)+_jl(a.route_telemetry_jsonl,dict)+[json.loads(Path(x).read_text()) for x in a.raw_event_json]+_jl(a.raw_event_jsonl,dict)
 r=build_formal_world_adapter_report(objs,specs,include_default_specs=a.default_specs,parse=a.parse,normalize=a.normalize,validate=a.validate,emit_tasks=a.tasks,emit_handoffs=a.handoffs)
 laws=adapter_report_to_lawbook_candidates(r); outs=adapter_report_to_continuation_outputs(r); cur=adapter_report_to_curriculum(r); vals=adapter_report_to_discovery_value_scores(r); eps=adapter_report_to_process_episodes(r); desc=adapter_report_to_structure_descriptors(r); typed=adapter_report_to_typed_projection_candidates(r); roles=adapter_report_to_role_signatures(r); analogies=adapter_report_to_analogy_sources(r); habits=adapter_report_to_habit_observations(r); reasons=adapter_report_to_reason_observations(r); structs=adapter_report_to_structural_identity_objects(r); alc=adapter_report_to_alchemical_trace(r); exps=adapter_report_to_agent_experiences(r); tele=adapter_report_to_route_telemetry_events(r); align=check_roadmap_alignment(formal_world_adapter_reports=[r],formal_world_adapter_specs=r.specs,formal_world_adapter_capabilities=r.capabilities,formal_world_parse_results=r.parses,formal_world_normalize_results=r.normalizations,formal_world_validation_results=r.validations,formal_world_tasks=r.tasks,formal_world_handoffs=r.handoffs,lawbook_entries=laws)
 if a.out_report_json:r.write_json(a.out_report_json)
 if a.out_report_jsonl:r.write_jsonl(a.out_report_jsonl)
 for path,rows in ((a.out_specs_jsonl,r.specs),(a.out_capabilities_jsonl,r.capabilities),(a.out_parses_jsonl,r.parses),(a.out_normalizations_jsonl,r.normalizations),(a.out_validations_jsonl,r.validations),(a.out_tasks_jsonl,r.tasks),(a.out_handoffs_jsonl,r.handoffs),(a.out_lawbook_candidates_jsonl,laws),(a.out_continuation_outputs_jsonl,outs),(a.out_discovery_value_scores_jsonl,vals),(a.out_process_episodes_jsonl,eps),(a.out_structure_descriptors_jsonl,desc),(a.out_typed_projections_jsonl,typed),(a.out_role_signatures_jsonl,roles),(a.out_analogy_sources_jsonl,analogies),(a.out_habit_observations_jsonl,habits),(a.out_reason_observations_jsonl,reasons),(a.out_structural_objects_jsonl,structs),(a.out_agent_experiences_jsonl,exps),(a.out_route_telemetry_jsonl,tele)):
  if path:_wjl(path,[x.to_dict() if hasattr(x,"to_dict") else x for x in rows])
 if a.out_curriculum_json:cur.write_json(a.out_curriculum_json)
 if a.out_alchemical_trace_json:alc.write_json(a.out_alchemical_trace_json)
 if a.alignment_report_json:align.write_json(a.alignment_report_json)
 if a.alignment_report_md:align.write_markdown(a.alignment_report_md)
 if not any(v for k,v in vars(a).items() if k.startswith("out_") or k.startswith("alignment_report")): sys.stdout.write(r.to_json()+"\n")
 return 1 if a.fail_on_critical and align.critical_count() else 0
def _jr(p,c): return c.from_json(Path(p).read_text())
def _jl(p,c):
 if not p:return []
 return [json.loads(x) if c is dict else c.from_dict(json.loads(x)) for x in Path(p).read_text().splitlines() if x.strip()]
def _wjl(p,rows): path=Path(p); path.parent.mkdir(parents=True,exist_ok=True); path.write_text("".join(json.dumps(x,sort_keys=True)+"\n" for x in rows))
if __name__=="__main__": raise SystemExit(main())
