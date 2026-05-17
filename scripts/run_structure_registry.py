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
from mathgraph.domain_claims import DomainClaim
from mathgraph.habit_rules import HabitFormationReport,HabitRule
from mathgraph.lawbook import LawbookEntry,LawbookStore
from mathgraph.lawbook_query import LawbookQueryReport
from mathgraph.process_memory import ProcessEpisodeRecord,ProcessMemoryReport
from mathgraph.projection import ProjectionCandidate
from mathgraph.proof_digestion import ProofDigestionTrace
from mathgraph.reason_compression import ReasonCompressionReport,ReasonNode
from mathgraph.roadmap_alignment import check_roadmap_alignment
from mathgraph.structural_identity import StructuralGraph,StructuralIdentityReport,StructuralSignature
from mathgraph.structure_registry import *
from mathgraph.verifier_feedback import RepairLoopTrace,VerifierFeedback
def main(argv=None):
 p=argparse.ArgumentParser()
 for n in ("descriptor-jsonl","mapping-jsonl","typed-projection-jsonl","projection-candidates-jsonl","structural-signature-jsonl","habit-rules-jsonl","reason-nodes-jsonl","process-episodes-jsonl","verifier-feedback-jsonl","agent-experiences-jsonl","route-telemetry-jsonl","raw-event-jsonl"): p.add_argument("--"+n)
 for n in ("descriptor-json","domain-claim-json","lawbook-entry-json","lawbook-store-json","lawbook-query-report-json","structural-identity-report-json","structural-graph-json","habit-report-json","reason-report-json","process-memory-report-json","proof-digestion-json","repair-trace-json","curriculum-json","alchemical-trace-json","raw-event-json"): p.add_argument("--"+n,action="append",default=[])
 p.add_argument("--no-default-types",action="store_true"); p.add_argument("--no-build-mappings",action="store_true"); p.add_argument("--no-build-projection-candidates",action="store_true"); p.add_argument("--min-mapping-score",type=float,default=.2)
 for n in ("out-store-json","out-store-jsonl","out-report-json","out-report-jsonl","out-descriptors-jsonl","out-mappings-jsonl","out-typed-projections-jsonl","out-lawbook-candidates-jsonl","out-projection-candidates-jsonl","out-continuation-outputs-jsonl","out-curriculum-json","out-discovery-value-scores-jsonl","out-process-episodes-jsonl","out-habit-observations-jsonl","out-reason-observations-jsonl","out-structural-objects-jsonl","out-alchemical-trace-json","out-agent-experiences-jsonl","out-route-telemetry-jsonl","alignment-report-json","alignment-report-md"): p.add_argument("--"+n)
 p.add_argument("--fail-on-critical",action="store_true"); a=p.parse_args(argv)
 desc=[_jr(x,StructureDescriptor) for x in a.descriptor_json]+_jl(a.descriptor_jsonl,StructureDescriptor); maps=_jl(a.mapping_jsonl,StructureMapping); typed=_jl(a.typed_projection_jsonl,TypedProjectionCandidate); objs=[]
 for paths,cls in ((a.domain_claim_json,DomainClaim),(a.lawbook_entry_json,LawbookEntry),(a.lawbook_store_json,LawbookStore),(a.lawbook_query_report_json,LawbookQueryReport),(a.structural_identity_report_json,StructuralIdentityReport),(a.structural_graph_json,StructuralGraph),(a.habit_report_json,HabitFormationReport),(a.reason_report_json,ReasonCompressionReport),(a.process_memory_report_json,ProcessMemoryReport),(a.proof_digestion_json,ProofDigestionTrace),(a.repair_trace_json,RepairLoopTrace),(a.curriculum_json,ContinuationCurriculum),(a.alchemical_trace_json,AlchemicalTrace)):
  objs += [_jr(x,cls) for x in paths]
 objs += _jl(a.projection_candidates_jsonl,ProjectionCandidate)+_jl(a.structural_signature_jsonl,StructuralSignature)+_jl(a.habit_rules_jsonl,HabitRule)+_jl(a.reason_nodes_jsonl,ReasonNode)+_jl(a.process_episodes_jsonl,ProcessEpisodeRecord)+_jl(a.verifier_feedback_jsonl,VerifierFeedback)+_jl(a.agent_experiences_jsonl,AgentExperience)+_jl(a.route_telemetry_jsonl,dict)+[json.loads(Path(x).read_text()) for x in a.raw_event_json]+_jl(a.raw_event_jsonl,dict)
 store=build_structure_registry_store(objs,desc,maps,typed,not a.no_default_types,not a.no_build_mappings,not a.no_build_projection_candidates,a.min_mapping_score); report=build_structure_registry_report(descriptors=[e.descriptor for e in store.entries],build_mappings=not a.no_build_mappings,build_projection_candidates=not a.no_build_projection_candidates,min_mapping_score=a.min_mapping_score); report.store=store; report.mappings=store.mappings; report.typed_projection_candidates=store.typed_projection_candidates; report.summarize()
 laws=structure_report_to_lawbook_candidates(report); projs=structure_report_to_projection_candidates(report); outs=structure_report_to_continuation_outputs(report); cur=structure_report_to_curriculum(report); vals=structure_report_to_discovery_value_scores(report); eps=structure_report_to_process_episodes(report); habits=structure_report_to_habit_observations(report); reasons=structure_report_to_reason_observations(report); structs=structure_report_to_structural_identity_objects(report); alc=structure_report_to_alchemical_trace(report); exps=structure_report_to_agent_experiences(report); tele=structure_report_to_route_telemetry_events(report); align=check_roadmap_alignment(structure_registry_reports=[report],structure_registry_stores=[store],typed_projection_candidates=report.typed_projection_candidates,lawbook_entries=laws)
 if a.out_store_json:store.write_json(a.out_store_json)
 if a.out_store_jsonl:store.write_jsonl(a.out_store_jsonl)
 if a.out_report_json:report.write_json(a.out_report_json)
 if a.out_report_jsonl:report.write_jsonl(a.out_report_jsonl)
 for path,rows in ((a.out_descriptors_jsonl,report.descriptors),(a.out_mappings_jsonl,report.mappings),(a.out_typed_projections_jsonl,report.typed_projection_candidates),(a.out_lawbook_candidates_jsonl,laws),(a.out_projection_candidates_jsonl,projs),(a.out_continuation_outputs_jsonl,outs),(a.out_discovery_value_scores_jsonl,vals),(a.out_process_episodes_jsonl,eps),(a.out_habit_observations_jsonl,habits),(a.out_reason_observations_jsonl,reasons),(a.out_structural_objects_jsonl,structs),(a.out_agent_experiences_jsonl,exps),(a.out_route_telemetry_jsonl,tele)):
  if path:_wjl(path,[x.to_dict() if hasattr(x,"to_dict") else x for x in rows])
 if a.out_curriculum_json:cur.write_json(a.out_curriculum_json)
 if a.out_alchemical_trace_json:alc.write_json(a.out_alchemical_trace_json)
 if a.alignment_report_json:align.write_json(a.alignment_report_json)
 if a.alignment_report_md:align.write_markdown(a.alignment_report_md)
 if not any(v for k,v in vars(a).items() if k.startswith("out_") or k.startswith("alignment_report")): sys.stdout.write(report.to_json()+"\n")
 return 1 if a.fail_on_critical and align.critical_count() else 0
def _jr(p,c): return c.from_json(Path(p).read_text())
def _jl(p,c):
 if not p:return []
 return [json.loads(x) if c is dict else c.from_dict(json.loads(x)) for x in Path(p).read_text().splitlines() if x.strip()]
def _wjl(p,rows): path=Path(p); path.parent.mkdir(parents=True,exist_ok=True); path.write_text("".join(json.dumps(x,sort_keys=True)+"\n" for x in rows))
if __name__=="__main__": raise SystemExit(main())
