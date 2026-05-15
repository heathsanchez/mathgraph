import json
import subprocess
import sys

from mathgraph.agent_biography import AgentExperienceOutcome
from mathgraph.alchemy import AlchemicalPhase, AlchemicalStatus, AlchemicalTrace
from mathgraph.certificates import TerminalForm
from mathgraph.lawbook import LawbookEntry, LawbookEntryKind, LawbookEntryStatus, LawbookStore
from mathgraph.lawbook_query import LawbookQueryAnswer, LawbookQueryStatus, LawbookTrustLevel
from mathgraph.roadmap_alignment import check_roadmap_alignment
from mathgraph.structural_identity import *


def _entry(entry_id: str, *, terminal: TerminalForm | None = None) -> LawbookEntry:
    return LawbookEntry(entry_id, LawbookEntryKind.VERIFIED_PROOF_ENTRY, claim_id="c1", source="x*x", target="x", terminal_form=terminal, certificate_id="cert1", artifact_ids=("a1",), conditions=("cond",))


def test_core_serialization_roundtrips() -> None:
    node = StructuralNode("n", StructuralNodeKind.CLAIM)
    edge = StructuralEdge("e", StructuralEdgeKind.LINKS_TO, "n", "m")
    graph = StructuralGraph("g", nodes=[node], edges=[edge])
    sig = StructuralSignature("s", object_id="o")
    cand = StructuralMergeCandidate("c", "l", "r", StructuralObjectKind.RAW_OBJECT, StructuralObjectKind.RAW_OBJECT, StructuralMatchKind.NEAR_DUPLICATE, StructuralMergeDecision.REVIEW_RECOMMENDED)
    report = StructuralIdentityReport("r", [graph], [sig], [cand])
    assert StructuralNode.from_json(node.to_json()).kind == node.kind
    assert StructuralEdge.from_json(edge.to_json()).kind == edge.kind
    assert StructuralGraph.from_json(graph.to_json()).graph_id == "g"
    assert StructuralSignature.from_json(sig.to_json()).signature_id == "s"
    assert StructuralMergeCandidate.from_json(cand.to_json()).candidate_id == "c"
    assert StructuralIdentityReport.from_json(report.to_json()).report_id == "r"


def test_empty_report_is_advisory() -> None:
    report = build_structural_identity_report()
    assert report.advisory and report.status == StructuralIdentityReportStatus.EMPTY


def test_graph_builders_cover_expected_structure() -> None:
    entry_graph = structural_graph_from_lawbook_entry(_entry("e1", terminal=TerminalForm.VERIFIED_PROOF))
    assert {node.kind for node in entry_graph.nodes} >= {StructuralNodeKind.SOURCE, StructuralNodeKind.TARGET, StructuralNodeKind.CERTIFICATE}
    store_graph = structural_graph_from_lawbook_store(LawbookStore("store", [_entry("e1")]))
    assert any(node.kind == StructuralNodeKind.ENTRY for node in store_graph.nodes)
    answer = LawbookQueryAnswer("a", "q", LawbookQueryStatus.FOUND_ACCEPTED_TRUTH, LawbookTrustLevel.VERIFIED_TRUTH, terminal_form=TerminalForm.VERIFIED_PROOF, certificate_id="cert1", matched_entry_ids=("e1",))
    assert any(node.kind == StructuralNodeKind.CERTIFICATE for node in structural_graph_from_lawbook_query_answer(answer).nodes)


def test_mapping_graph_limits_recursion() -> None:
    graph = structural_graph_from_mapping({"a": {"b": {"c": {"d": {"e": 1}}}}}, max_depth=2, max_items=3)
    assert graph.node_count() <= 4


def test_signatures_are_deterministic_and_label_invariant() -> None:
    left = structural_graph_from_mapping({"a": 1}, object_id="left")
    right = structural_graph_from_mapping({"z": 9}, object_id="right")
    assert compute_structural_signature(left).canonical_digest == compute_structural_signature(left).canonical_digest
    assert compute_structural_signature(left).canonical_digest == compute_structural_signature(right).canonical_digest
    assert compute_structural_signature(left, include_value_digests=True).canonical_digest != compute_structural_signature(right, include_value_digests=True).canonical_digest


def test_signature_comparison_and_conflict() -> None:
    left = compute_structural_signature(structural_graph_from_mapping({"a": 1}, object_id="l"))
    right = compute_structural_signature(structural_graph_from_mapping({"b": 2}, object_id="r"))
    assert compare_structural_signatures(left, right).decision == StructuralMergeDecision.MERGE_RECOMMENDED
    e1 = compute_structural_signature(structural_graph_from_lawbook_entry(_entry("e1", terminal=TerminalForm.VERIFIED_PROOF)))
    e2 = compute_structural_signature(structural_graph_from_lawbook_entry(_entry("e2", terminal=TerminalForm.FINITE_COUNTERMODEL)))
    conflict = compare_structural_signatures(e1, e2)
    assert conflict.match_kind == StructuralMatchKind.CONFLICTING_DUPLICATE
    assert conflict.decision == StructuralMergeDecision.CONFLICT_REVIEW


def test_report_and_bridges_remain_advisory() -> None:
    report = build_structural_identity_report([{"a": 1}, {"b": 2}])
    assert report.merge_candidate_count() == 1
    assert structural_identity_report_to_lawbook_candidates(report)[0].status == LawbookEntryStatus.CANDIDATE
    assert all(output.advisory and not output.is_terminal() for output in structural_identity_report_to_continuation_outputs(report))
    assert all(stage.advisory for stage in structural_identity_report_to_curriculum(report).stages)
    assert AlchemicalPhase.FIXATION not in structural_identity_report_to_alchemical_trace(report).phases_seen()
    assert all(exp.outcome not in {AgentExperienceOutcome.VERIFIED_PROOF, AgentExperienceOutcome.FINITE_COUNTERMODEL} for exp in structural_identity_report_to_agent_experiences(report))
    assert isinstance(structural_identity_report_to_route_telemetry_events(report)[0], dict)


def test_audit_and_alignment_catch_drift() -> None:
    bad = StructuralMergeCandidate("bad", "l", "r", StructuralObjectKind.RAW_OBJECT, StructuralObjectKind.RAW_OBJECT, StructuralMatchKind.CONFLICTING_DUPLICATE, StructuralMergeDecision.MERGE_RECOMMENDED, advisory=False, metadata={"treat_as_truth": True, "terminal_form": "VERIFIED_PROOF"})
    assert {item["code"] for item in audit_structural_merge_candidate(bad)} >= {"STRUCTURAL_MERGE_NON_ADVISORY", "STRUCTURAL_CONFLICT_MERGE"}
    report = check_roadmap_alignment(structural_merge_candidates=[bad])
    assert report.critical_count() >= 2
    accepted = structural_identity_report_to_lawbook_candidates(build_structural_identity_report([{"a": 1}, {"b": 2}]))[0]
    accepted.status = LawbookEntryStatus.ACCEPTED
    assert any(item.code == "STRUCTURAL_LAWBOOK_CANDIDATE_ACCEPTED_DIRECTLY" for item in check_roadmap_alignment(lawbook_entries=[accepted]).findings)


def test_cli_empty_and_raw_jsonl(tmp_path) -> None:
    out = tmp_path / "report.json"
    proc = subprocess.run([sys.executable, "scripts/run_structural_identity.py", "--out-report-json", str(out)], capture_output=True, text=True)
    assert proc.returncode == 0 and out.exists()
    raw = tmp_path / "raw.jsonl"
    raw.write_text('{"a":1}\n{"b":2}\n', encoding="utf-8")
    sigs = tmp_path / "sigs.jsonl"
    merges = tmp_path / "merges.jsonl"
    laws = tmp_path / "laws.jsonl"
    cont = tmp_path / "cont.jsonl"
    proc = subprocess.run([sys.executable, "scripts/run_structural_identity.py", "--raw-object-jsonl", str(raw), "--out-signatures-jsonl", str(sigs), "--out-merge-candidates-jsonl", str(merges), "--out-lawbook-candidates-jsonl", str(laws), "--out-continuation-outputs-jsonl", str(cont)], capture_output=True, text=True)
    assert proc.returncode == 0
    assert all(path.exists() for path in (sigs, merges, laws, cont))
