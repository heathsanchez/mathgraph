import json,subprocess,sys
from pathlib import Path
from mathgraph.certificates import TerminalForm
from mathgraph.lawbook import LawbookEntry,LawbookEntryKind,LawbookEntryStatus,LawbookStore
from mathgraph.process_memory import *

def _terminal_episode(eid="ep1"):
 return ProcessEpisodeRecord(eid,ProcessEpisodeStatus.TERMINAL_VERIFIED_PROOF,"c1","proof",TerminalForm.VERIFIED_PROOF,"cert1",True,contexts=[ProcessContextItem("ctx",ProcessContextKind.CERTIFICATE,ProcessContextRole.PROMOTED_BY_VERIFIER,certificate_id="cert1",terminal_form=TerminalForm.VERIFIED_PROOF,verifier_boundary_crossed=True)],transitions=[ProcessTransition("tr",ProcessTransitionKind.VERIFIER_TO_CERTIFICATE)])
def _advisory_episode(eid="ep2"):
 return ProcessEpisodeRecord(eid,ProcessEpisodeStatus.RESIDUAL,"c2","repair",contexts=[ProcessContextItem("ctx2",ProcessContextKind.REPAIR,ProcessContextRole.USED)],eliminations=[ProcessElimination("el",ProcessEliminationKind.NEEDS_REPAIR,route="repair")],transitions=[ProcessTransition("tr2",ProcessTransitionKind.FEEDBACK_TO_REPAIR)])
def test_serialization_roundtrip():
 objs=[ProcessContextItem("c",ProcessContextKind.CLAIM,ProcessContextRole.INCLUDED),ProcessElimination("e",ProcessEliminationKind.KILLED_ROUTE),ProcessTransition("t",ProcessTransitionKind.RAW_TO_PROCESS),_terminal_episode(),make_process_query_by_claim("c1"),query_process_memory_store(build_process_memory_store(episodes=[_terminal_episode()]),make_process_query_by_claim("c1"))]
 for obj in objs: assert obj.from_json(obj.to_json()).to_dict()==obj.to_dict()
 store=build_process_memory_store(episodes=[_terminal_episode()]); assert ProcessMemoryStore.from_json(store.to_json()).to_dict()==store.to_dict()
 report=query_process_memory_store_many(store,[make_process_query_by_claim("c1")]); assert ProcessMemoryReport.from_json(report.to_json()).to_dict()==report.to_dict()
def test_empty_store_is_advisory():
 s=build_process_memory_store(); assert s.advisory and s.episode_count()==0
def test_raw_mapping_builds_episode_and_store_dedupes():
 ep=process_episode_from_mapping({"event_id":"x","route":"r","killed":True,"kill_reason":"bad"})
 s=build_process_memory_store(episodes=[ep,ep])
 assert ep.eliminations and s.episode_count()==1 and s.summary["elimination_total"]==1
def test_lawbook_store_becomes_advisory_episode():
 entry=LawbookEntry("le",LawbookEntryKind.VERIFIED_PROOF_ENTRY,LawbookEntryStatus.ACCEPTED,claim_id="c",terminal_form=TerminalForm.VERIFIED_PROOF,certificate_id="cert",verifier_boundary_crossed=True)
 ep=process_episode_from_lawbook_store(LawbookStore("ls",[entry]))
 assert ep.lawbook_entry_ids==("le",) and not ep.has_truth_boundary()
def test_queries_cover_terminal_elimination_and_not_found():
 s=build_process_memory_store(episodes=[_terminal_episode(),_advisory_episode()])
 assert query_process_memory_store(s,make_process_query_by_episode("ep1")).status==ProcessMemoryAnswerStatus.FOUND_TERMINAL_BOUNDARY
 assert query_process_memory_store(s,make_process_query_by_claim("c1")).has_truth_boundary()
 assert query_process_memory_store(s,make_process_query_by_route("repair")).status==ProcessMemoryAnswerStatus.FOUND_ELIMINATION
 assert query_process_memory_store(s,make_process_query_by_certificate("cert1")).status==ProcessMemoryAnswerStatus.FOUND_TERMINAL_BOUNDARY
 assert query_process_memory_store(s,make_process_query_by_claim("missing")).status==ProcessMemoryAnswerStatus.NOT_FOUND
 assert query_process_memory_store(s,ProcessMemoryQuery("q",ProcessMemoryQueryKind.CLAIM)).status==ProcessMemoryAnswerStatus.INVALID_QUERY
def test_text_and_summary_queries():
 s=build_process_memory_store(episodes=[_terminal_episode(),_advisory_episode()])
 assert query_process_memory_store(s,make_process_text_query("repair")).matched_episode_ids==("ep2",)
 assert "summary" in query_process_memory_store(s,make_process_trust_summary_query()).evidence
def test_lineage_and_summaries():
 e1=_terminal_episode("a"); e2=_advisory_episode("b"); e2.transitions.append(ProcessTransition("line",ProcessTransitionKind.RAW_TO_PROCESS,"a","b"))
 s=build_process_memory_store(episodes=[e1,e2])
 assert [e.episode_id for e in trace_episode_lineage(s,"b")]==["b","a"]
 assert summarize_eliminations(s)["by_kind"]["NEEDS_REPAIR"]==1
 assert summarize_route_processes(s)["proof"]["terminal_count"]==1
def test_bridges_remain_advisory():
 s=build_process_memory_store(episodes=[_terminal_episode(),_advisory_episode()])
 r=query_process_memory_store_many(s,[make_process_query_by_claim("c1"),make_process_query_by_route("repair")])
 assert all(x.status==LawbookEntryStatus.CANDIDATE for x in process_report_to_lawbook_candidates(r))
 assert all(x.advisory for x in process_report_to_continuation_outputs(r))
 assert all(x.advisory for x in process_report_to_curriculum(r).stages)
 assert process_report_to_discovery_value_scores(r)
 assert process_report_to_habit_observations(r)
 assert process_report_to_reason_observations(r)
 assert process_report_to_structural_identity_objects(r)
 assert all(step.phase.value!="FIXATION" for step in process_report_to_alchemical_trace(r).steps)
 assert process_report_to_agent_experiences(r)
 assert isinstance(process_report_to_route_telemetry_events(r)[0],dict)
def test_audits_catch_boundary_drift():
 bad=ProcessEpisodeRecord("bad",ProcessEpisodeStatus.TERMINAL_VERIFIED_PROOF,terminal_form=TerminalForm.VERIFIED_PROOF,contexts=[ProcessContextItem("c",ProcessContextKind.CLAIM,ProcessContextRole.INCLUDED)],transitions=[ProcessTransition("t",ProcessTransitionKind.RAW_TO_PROCESS)])
 assert any(x["severity"]=="CRITICAL" for x in audit_process_episode_record(bad))
 ans=ProcessMemoryAnswer("a","q",ProcessMemoryAnswerStatus.FOUND_TERMINAL_BOUNDARY,terminal_form=TerminalForm.VERIFIED_PROOF)
 assert any(x["severity"]=="CRITICAL" for x in audit_process_memory_answer(ans))
def test_cli_empty_and_query(tmp_path):
 raw=tmp_path/"raw.jsonl"; raw.write_text(json.dumps({"event_id":"x","route":"repair","killed":True})+"\n")
 answers=tmp_path/"answers.jsonl"; habits=tmp_path/"habits.jsonl"; reasons=tmp_path/"reasons.jsonl"; elim=tmp_path/"elim.json"; routes=tmp_path/"routes.json"
 cmd=[sys.executable,"scripts/run_process_memory.py","--raw-event-jsonl",str(raw),"--query-route","repair","--out-answers-jsonl",str(answers),"--out-habit-observations-jsonl",str(habits),"--out-reason-observations-jsonl",str(reasons),"--out-elimination-summary-json",str(elim),"--out-route-summary-json",str(routes)]
 subprocess.run(cmd,check=True)
 assert answers.read_text() and habits.read_text() and reasons.read_text() and "KILLED_ROUTE" in elim.read_text() and "repair" in routes.read_text()
