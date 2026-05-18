import json,subprocess,sys
from mathgraph.hardening import *
from mathgraph.existential_agents import create_existential_agent,kill_agent
def finding(status=HardeningCheckStatus.PASS,severity=HardeningSeverity.INFO):
 return HardeningFinding("f",HardeningCheckKind.SERIALIZATION,status,severity,"OK","ok")
def test_roundtrips_and_report_ok():
 f=finding(); s=build_empty_scenario(); c=HardeningCliResult("c","cli"); m=build_replay_manifest("r",[s]); r=HardeningReport("h","run","now",[f],[s],[c],m)
 for x in (f,s,c,m,r): assert x.from_json(x.to_json()).to_dict()==x.to_dict()
 assert HardeningReport("x","r","n",[finding(HardeningCheckStatus.FAIL,HardeningSeverity.CRITICAL)]).ok() is False
 assert HardeningReport("x","r","n",[f]).ok() is True
def test_scenarios_and_checks():
 builders=[build_empty_scenario,build_magma_implication_scenario,build_natural_language_theorem_scenario,build_proof_assistant_text_scenario,build_lawbook_known_skip_scenario,build_api_submit_scenario,build_agent_lifecycle_scenario,build_full_advisory_pipeline_scenario,build_rich_lean_fixture_dry_run_scenario,build_verified_corpus_dry_run_scenario,build_lean_project_subset_dry_run_scenario,build_mathlib_micro_subset_dry_run_scenario,build_mathlib_local_allowlist_dry_run_scenario,build_mathlib_declaration_discovery_dry_run_scenario,build_proof_library_demo_dry_run_scenario]
 xs=[run_hardening_scenario(b()) for b in builders]; assert all(x.status in {HardeningCheckStatus.PASS,HardeningCheckStatus.WARN} for x in xs)
 assert len(run_default_hardening_scenarios())>=7 and all(x.status==HardeningCheckStatus.PASS for x in xs)
 assert all(x.status==HardeningCheckStatus.PASS for x in run_serialization_checks())
 assert not [x for x in run_doc_sync_checks() if x.status==HardeningCheckStatus.FAIL]
 assert run_public_term_checks()[0].status==HardeningCheckStatus.PASS
 assert run_api_contract_checks()[0].status==HardeningCheckStatus.PASS
 assert run_truth_boundary_checks([{"terminal_form":"VERIFIED_PROOF"}])
 a=create_existential_agent("A"); a.activate(); kill_agent(a); a.active=True; assert run_truth_boundary_checks([a])
 assert run_lightweight_performance_checks()
def test_report_bridges_audits_alignment(tmp_path):
 r=build_hardening_report(artifact_dir=tmp_path); assert r.ok() and r.summary["advisory_only"] and r.replay_manifest.boundary_policy and list(tmp_path.iterdir())
 bad=build_hardening_report(extra_objects=[{"terminal_form":"VERIFIED_PROOF"}]); assert bad.critical_count()
 assert hardening_report_to_api_response(r).truth_status==ApiTruthStatus.ADVISORY_ONLY
 assert hardening_report_to_process_episodes(r) and hardening_report_to_discovery_value_scores(r) and all(x.outcome==AgentExperienceOutcome.ADVISORY_ONLY for x in hardening_report_to_agent_experiences(r))
 assert all(x.phase.value!="FIXATION" for x in hardening_report_to_alchemical_trace(r).steps)
 assert hardening_report_to_route_telemetry_events(r) and all(x.status==LawbookEntryStatus.CANDIDATE for x in hardening_report_to_lawbook_candidates(r))
 assert audit_hardening_scenario(HardeningScenario("s",HardeningScenarioKind.EMPTY,"x",findings=[finding(HardeningCheckStatus.FAIL,HardeningSeverity.CRITICAL)],status=HardeningCheckStatus.PASS))
 assert audit_hardening_cli_result(HardeningCliResult("c","cli",metadata={"shell":True}))
 from mathgraph.roadmap_alignment import check_roadmap_alignment
 assert check_roadmap_alignment(hardening_reports=[r]).critical_count()==0
def test_cli(tmp_path):
 out=tmp_path/"report.json"; finds=tmp_path/"finds.jsonl"; manifest=tmp_path/"manifest.json"; subprocess.run([sys.executable,"scripts/run_hardening.py","--out-report-json",str(out),"--out-findings-jsonl",str(finds),"--out-replay-manifest-json",str(manifest)],check=True); assert out.exists() and finds.exists() and manifest.exists()
