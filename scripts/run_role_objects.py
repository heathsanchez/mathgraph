#!/usr/bin/env python
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from mathgraph.agent_biography import AgentExperience
from mathgraph.alchemy import AlchemicalTrace
from mathgraph.continuation_curriculum import ContinuationCurriculum
from mathgraph.habit_rules import HabitFormationReport,HabitRule
from mathgraph.lawbook import LawbookEntry,LawbookStore
from mathgraph.lawbook_query import LawbookQueryReport
from mathgraph.process_memory import ProcessEpisodeRecord,ProcessMemoryReport
from mathgraph.projection import ProjectionCandidate
from mathgraph.proof_digestion import ProofDigestionTrace
from mathgraph.reason_compression import ReasonCompressionReport,ReasonNode
from mathgraph.roadmap_alignment import check_roadmap_alignment
from mathgraph.role_objects import *
from mathgraph.structural_identity import StructuralIdentityReport
from mathgraph.structure_registry import StructureDescriptor,StructureMapping,StructureRegistryReport,TypedProjectionCandidate
from mathgraph.verifier_feedback import RepairLoopTrace,VerifierFeedback
def main(argv=None):
 p=argparse.ArgumentParser()
 for n in ("signature-jsonl","definition-jsonl","witness-jsonl","conjecture-jsonl","role-object-jsonl","structure-descriptors-jsonl","structure-mappings-jsonl","typed-projections-jsonl","reason-nodes-jsonl","habit-rules-jsonl","process-episodes-jsonl","projection-candidates-jsonl","verifier-feedback-jsonl","agent-experiences-jsonl","route-telemetry-jsonl","raw-event-jsonl","route-scores-jsonl"): p.add_argument("--"+n)
 for n in ("signature-json","definition-json","structure-report-json","reason-report-json","habit-report-json","process-memory-report-json","lawbook-entry-json","lawbook-store-json","lawbook-query-report-json","structural-identity-report-json","proof-digestion-json","repair-trace-json","curriculum-json","alchemical-trace-json","raw-event-json"): p.add_argument("--"+n,action="append",default=[])
 p.add_argument("--auto-definitions",action=argparse.BooleanOptionalAction,default=True); p.add_argument("--auto-witnesses",action=argparse.BooleanOptionalAction,default=True); p.add_argument("--auto-conjectures",action=argparse.BooleanOptionalAction,default=True); p.add_argument("--auto-review",action=argparse.BooleanOptionalAction,default=True); p.add_argument("--auto-promote",action="store_true"); p.add_argument("--reviewer"); p.add_argument("--min-support",type=int,default=3); p.add_argument("--min-confidence",type=float,default=.4); p.add_argument("--max-complexity",type=int,default=10); p.add_argument("--max-risk",type=float,default=.5); p.add_argument("--require-witness",action=argparse.BooleanOptionalAction,default=True)
 for n in ("out-ranked-routes-jsonl","out-report-json","out-report-jsonl","out-signatures-jsonl","out-definitions-jsonl","out-witnesses-jsonl","out-conjectures-jsonl","out-reviews-jsonl","out-role-objects-jsonl","out-lawbook-candidates-jsonl","out-continuation-outputs-jsonl","out-curriculum-json","out-discovery-value-scores-jsonl","out-process-episodes-jsonl","out-structure-descriptors-jsonl","out-typed-projections-jsonl","out-habit-observations-jsonl","out-reason-observations-jsonl","out-structural-objects-jsonl","out-alchemical-trace-json","out-agent-experiences-jsonl","out-route-telemetry-jsonl","alignment-report-json","alignment-report-md"): p.add_argument("--"+n)
 p.add_argument("--fail-on-critical",action="store_true"); a=p.parse_args(argv); sigs=[_jr(x,RoleSignature) for x in a.signature_json]+_jl(a.signature_jsonl,RoleSignature); objs=[]
 for paths,cls in ((a.structure_report_json,StructureRegistryReport),(a.reason_report_json,ReasonCompressionReport),(a.habit_report_json,HabitFormationReport),(a.process_memory_report_json,ProcessMemoryReport),(a.lawbook_entry_json,LawbookEntry),(a.lawbook_store_json,LawbookStore),(a.lawbook_query_report_json,LawbookQueryReport),(a.structural_identity_report_json,StructuralIdentityReport),(a.proof_digestion_json,ProofDigestionTrace),(a.repair_trace_json,RepairLoopTrace),(a.curriculum_json,ContinuationCurriculum),(a.alchemical_trace_json,AlchemicalTrace)):
  objs += [_jr(x,cls) for x in paths]
 objs += _jl(a.structure_descriptors_jsonl,StructureDescriptor)+_jl(a.structure_mappings_jsonl,StructureMapping)+_jl(a.typed_projections_jsonl,TypedProjectionCandidate)+_jl(a.reason_nodes_jsonl,ReasonNode)+_jl(a.habit_rules_jsonl,HabitRule)+_jl(a.process_episodes_jsonl,ProcessEpisodeRecord)+_jl(a.projection_candidates_jsonl,ProjectionCandidate)+_jl(a.verifier_feedback_jsonl,VerifierFeedback)+_jl(a.agent_experiences_jsonl,AgentExperience)+_jl(a.route_telemetry_jsonl,dict)+[json.loads(Path(x).read_text()) for x in a.raw_event_json]+_jl(a.raw_event_jsonl,dict)
 r=build_role_object_report(objs,sigs,auto_definitions=a.auto_definitions,auto_witnesses=a.auto_witnesses,auto_conjectures=a.auto_conjectures,auto_review=a.auto_review,auto_promote=a.auto_promote,reviewer=a.reviewer,min_support=a.min_support,min_confidence=a.min_confidence,max_complexity=a.max_complexity,max_risk=a.max_risk,require_witness=a.require_witness); ranked=rank_routes_with_role_objects(r.role_objects,_jl(a.route_scores_jsonl,dict)) if a.route_scores_jsonl else []
 laws=role_report_to_lawbook_candidates(r); outs=role_report_to_continuation_outputs(r); cur=role_report_to_curriculum(r); vals=role_report_to_discovery_value_scores(r); eps=role_report_to_process_episodes(r); desc=role_report_to_structure_descriptors(r); typed=role_report_to_typed_projection_candidates(r); habits=role_report_to_habit_observations(r); reasons=role_report_to_reason_observations(r); structs=role_report_to_structural_identity_objects(r); alc=role_report_to_alchemical_trace(r); exps=role_report_to_agent_experiences(r); tele=role_report_to_route_telemetry_events(r); align=check_roadmap_alignment(role_object_reports=[r],role_objects=r.role_objects,role_definition_candidates=r.definition_candidates,role_witness_candidates=r.witness_candidates,role_conjecture_candidates=r.conjecture_candidates,lawbook_entries=laws)
 if a.out_report_json:r.write_json(a.out_report_json)
 if a.out_report_jsonl:r.write_jsonl(a.out_report_jsonl)
 for path,rows in ((a.out_ranked_routes_jsonl,ranked),(a.out_signatures_jsonl,r.signatures),(a.out_definitions_jsonl,r.definition_candidates),(a.out_witnesses_jsonl,r.witness_candidates),(a.out_conjectures_jsonl,r.conjecture_candidates),(a.out_reviews_jsonl,r.reviews),(a.out_role_objects_jsonl,r.role_objects),(a.out_lawbook_candidates_jsonl,laws),(a.out_continuation_outputs_jsonl,outs),(a.out_discovery_value_scores_jsonl,vals),(a.out_process_episodes_jsonl,eps),(a.out_structure_descriptors_jsonl,desc),(a.out_typed_projections_jsonl,typed),(a.out_habit_observations_jsonl,habits),(a.out_reason_observations_jsonl,reasons),(a.out_structural_objects_jsonl,structs),(a.out_agent_experiences_jsonl,exps),(a.out_route_telemetry_jsonl,tele)):
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
