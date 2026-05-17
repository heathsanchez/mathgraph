#!/usr/bin/env python
from __future__ import annotations
import sys
from pathlib import Path

try:
    from _bootstrap import ensure_repo_root_on_path
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
else:
    ensure_repo_root_on_path(__file__)

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
from mathgraph.role_objects import RoleDefinitionCandidate,RoleObject,RoleObjectReport,RoleSignature
from mathgraph.structural_analogy import *
from mathgraph.structural_identity import StructuralGraph,StructuralIdentityReport,StructuralSignature
from mathgraph.structure_registry import StructureDescriptor,StructureMapping,StructureRegistryReport,TypedProjectionCandidate
from mathgraph.verifier_feedback import RepairLoopTrace,VerifierFeedback
def main(argv=None):
 p=argparse.ArgumentParser()
 for n in ("source-jsonl","feature-map-jsonl","candidate-jsonl","exposition-jsonl","role-objects-jsonl","role-definitions-jsonl","role-signatures-jsonl","structure-descriptors-jsonl","structure-mappings-jsonl","typed-projections-jsonl","reason-nodes-jsonl","habit-rules-jsonl","process-episodes-jsonl","projection-candidates-jsonl","structural-signature-jsonl","verifier-feedback-jsonl","agent-experiences-jsonl","route-telemetry-jsonl","raw-event-jsonl","route-scores-jsonl"): p.add_argument("--"+n)
 for n in ("source-json","role-report-json","structure-report-json","reason-report-json","habit-report-json","process-memory-report-json","lawbook-entry-json","lawbook-store-json","lawbook-query-report-json","structural-identity-report-json","structural-graph-json","proof-digestion-json","repair-trace-json","curriculum-json","alchemical-trace-json","raw-event-json"): p.add_argument("--"+n,action="append",default=[])
 p.add_argument("--build-maps",action=argparse.BooleanOptionalAction,default=True); p.add_argument("--build-candidates",action=argparse.BooleanOptionalAction,default=True); p.add_argument("--build-exposition",action=argparse.BooleanOptionalAction,default=True); p.add_argument("--auto-review",action=argparse.BooleanOptionalAction,default=True); p.add_argument("--reviewer"); p.add_argument("--min-map-score",type=float,default=.15); p.add_argument("--max-pairs",type=int,default=2500)
 for n in ("out-ranked-routes-jsonl","out-report-json","out-report-jsonl","out-sources-jsonl","out-feature-maps-jsonl","out-breaks-jsonl","out-candidates-jsonl","out-exposition-jsonl","out-reviews-jsonl","out-lawbook-candidates-jsonl","out-continuation-outputs-jsonl","out-curriculum-json","out-discovery-value-scores-jsonl","out-process-episodes-jsonl","out-role-signatures-jsonl","out-structure-descriptors-jsonl","out-typed-projections-jsonl","out-habit-observations-jsonl","out-reason-observations-jsonl","out-structural-objects-jsonl","out-alchemical-trace-json","out-agent-experiences-jsonl","out-route-telemetry-jsonl","alignment-report-json","alignment-report-md"): p.add_argument("--"+n)
 p.add_argument("--fail-on-critical",action="store_true"); a=p.parse_args(argv); src=[_jr(x,AnalogySource) for x in a.source_json]+_jl(a.source_jsonl,AnalogySource); objs=[]
 for paths,cls in ((a.role_report_json,RoleObjectReport),(a.structure_report_json,StructureRegistryReport),(a.reason_report_json,ReasonCompressionReport),(a.habit_report_json,HabitFormationReport),(a.process_memory_report_json,ProcessMemoryReport),(a.lawbook_entry_json,LawbookEntry),(a.lawbook_store_json,LawbookStore),(a.lawbook_query_report_json,LawbookQueryReport),(a.structural_identity_report_json,StructuralIdentityReport),(a.structural_graph_json,StructuralGraph),(a.proof_digestion_json,ProofDigestionTrace),(a.repair_trace_json,RepairLoopTrace),(a.curriculum_json,ContinuationCurriculum),(a.alchemical_trace_json,AlchemicalTrace)):
  objs += [_jr(x,cls) for x in paths]
 objs += _jl(a.role_objects_jsonl,RoleObject)+_jl(a.role_definitions_jsonl,RoleDefinitionCandidate)+_jl(a.role_signatures_jsonl,RoleSignature)+_jl(a.structure_descriptors_jsonl,StructureDescriptor)+_jl(a.structure_mappings_jsonl,StructureMapping)+_jl(a.typed_projections_jsonl,TypedProjectionCandidate)+_jl(a.reason_nodes_jsonl,ReasonNode)+_jl(a.habit_rules_jsonl,HabitRule)+_jl(a.process_episodes_jsonl,ProcessEpisodeRecord)+_jl(a.projection_candidates_jsonl,ProjectionCandidate)+_jl(a.structural_signature_jsonl,StructuralSignature)+_jl(a.verifier_feedback_jsonl,VerifierFeedback)+_jl(a.agent_experiences_jsonl,AgentExperience)+_jl(a.route_telemetry_jsonl,dict)+[json.loads(Path(x).read_text()) for x in a.raw_event_json]+_jl(a.raw_event_jsonl,dict)
 r=build_structural_analogy_report(objs,src,build_maps=a.build_maps,build_candidates=a.build_candidates,build_exposition=a.build_exposition,auto_review=a.auto_review,reviewer=a.reviewer,min_map_score=a.min_map_score,max_pairs=a.max_pairs); ranked=rank_routes_with_analogies(r.candidates,_jl(a.route_scores_jsonl,dict)) if a.route_scores_jsonl else []
 laws=analogy_report_to_lawbook_candidates(r); outs=analogy_report_to_continuation_outputs(r); cur=analogy_report_to_curriculum(r); vals=analogy_report_to_discovery_value_scores(r); eps=analogy_report_to_process_episodes(r); roles=analogy_report_to_role_signatures(r); desc=analogy_report_to_structure_descriptors(r); typed=analogy_report_to_typed_projection_candidates(r); habits=analogy_report_to_habit_observations(r); reasons=analogy_report_to_reason_observations(r); structs=analogy_report_to_structural_identity_objects(r); alc=analogy_report_to_alchemical_trace(r); exps=analogy_report_to_agent_experiences(r); tele=analogy_report_to_route_telemetry_events(r); align=check_roadmap_alignment(structural_analogy_reports=[r],analogy_sources=r.sources,analogy_feature_maps=r.feature_maps,analogy_breaks=r.breaks,structural_analogy_candidates=r.candidates,exposition_notes=r.exposition_notes,analogy_reviews=r.reviews,lawbook_entries=laws)
 if a.out_report_json:r.write_json(a.out_report_json)
 if a.out_report_jsonl:r.write_jsonl(a.out_report_jsonl)
 for path,rows in ((a.out_ranked_routes_jsonl,ranked),(a.out_sources_jsonl,r.sources),(a.out_feature_maps_jsonl,r.feature_maps),(a.out_breaks_jsonl,r.breaks),(a.out_candidates_jsonl,r.candidates),(a.out_exposition_jsonl,r.exposition_notes),(a.out_reviews_jsonl,r.reviews),(a.out_lawbook_candidates_jsonl,laws),(a.out_continuation_outputs_jsonl,outs),(a.out_discovery_value_scores_jsonl,vals),(a.out_process_episodes_jsonl,eps),(a.out_role_signatures_jsonl,roles),(a.out_structure_descriptors_jsonl,desc),(a.out_typed_projections_jsonl,typed),(a.out_habit_observations_jsonl,habits),(a.out_reason_observations_jsonl,reasons),(a.out_structural_objects_jsonl,structs),(a.out_agent_experiences_jsonl,exps),(a.out_route_telemetry_jsonl,tele)):
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
