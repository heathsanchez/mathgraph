import json
import subprocess
import sys
from pathlib import Path

from mathgraph.alchemy import AlchemicalPhase
from mathgraph.certificates import TerminalForm
from mathgraph.projection import (
    ProjectionCandidate,
    ProjectionResult,
    ProjectionRuleKind,
    ProjectionStatus,
    ProjectionTrace,
    exact_known_projection,
    projection_trace_to_agent_experiences,
    projection_trace_to_alchemical_trace,
    run_projection_engine,
)
from mathgraph.roadmap_alignment import check_roadmap_alignment


ROOT = Path(__file__).resolve().parents[1]


def test_projection_candidate_serializes_deserializes():
    candidate = ProjectionCandidate(
        candidate_id="pc-1",
        source_claim_id="claim-a",
        target_claim_id="claim-b",
        source_idx=1,
        target_idx=2,
        source="A",
        target="B",
        rule_kind=ProjectionRuleKind.ADVISORY_SIMILARITY,
        confidence=0.25,
        advisory=True,
        reason="nearby residual",
    )

    restored = ProjectionCandidate.from_json(candidate.to_json())

    assert restored.to_dict() == candidate.to_dict()


def test_projection_result_serializes_deserializes():
    result = ProjectionResult(
        result_id="pr-1",
        candidate_id="pc-1",
        status=ProjectionStatus.KNOWN_SKIP,
        terminal_form=TerminalForm.VERIFIED_PROOF,
        verifier_boundary_crossed=True,
        lawbook_entry_id="law-1",
        residual_delta=-1,
        compression_gain=1.0,
        projection_gain=1.0,
    )

    restored = ProjectionResult.from_json(result.to_json())

    assert restored.to_dict() == result.to_dict()
    assert restored.is_terminal()


def test_advisory_projection_is_never_terminal():
    result = ProjectionResult(
        result_id="pr-adv",
        candidate_id="pc-1",
        status=ProjectionStatus.ADVISORY_ONLY,
        terminal_form=TerminalForm.VERIFIED_PROOF,
        verifier_boundary_crossed=True,
    )

    assert not result.is_terminal()
    assert result.is_advisory()


def test_exact_known_projection_can_produce_known_skip_safely():
    pair = {"source": "A", "target": "B"}
    entries = [
        {
            "lawbook_entry_id": "law-1",
            "certificate_id": "cert-1",
            "source": "A",
            "target": "B",
            "terminal_form": "VERIFIED_PROOF",
            "verification_status": "VERIFIED",
        }
    ]

    result = exact_known_projection(pair, entries)

    assert result is not None
    assert result.status == ProjectionStatus.KNOWN_SKIP
    assert result.terminal_form == TerminalForm.VERIFIED_PROOF
    assert result.verifier_boundary_crossed
    assert result.is_terminal()


def test_derived_certificate_result_terminal_only_with_id():
    unsafe = ProjectionResult(
        result_id="pr-derived-bad",
        candidate_id="pc-1",
        status=ProjectionStatus.DERIVED_CERTIFICATE,
        terminal_form=TerminalForm.FINITE_COUNTERMODEL,
    )
    safe = ProjectionResult(
        result_id="pr-derived-good",
        candidate_id="pc-1",
        status=ProjectionStatus.DERIVED_CERTIFICATE,
        terminal_form=TerminalForm.FINITE_COUNTERMODEL,
        derived_certificate_id="derived-1",
    )

    assert not unsafe.is_terminal()
    assert safe.is_terminal()


def test_projection_trace_summarizes_counts_and_gains():
    trace = ProjectionTrace(
        trace_id="pt-1",
        episode_id="episode-1",
        agent_id="agent-1",
        candidates=[
            ProjectionCandidate("pc-1", None, None, source="A", target="B"),
            ProjectionCandidate("pc-2", None, None, source="B", target="C"),
        ],
        results=[
            ProjectionResult(
                "pr-1",
                "pc-1",
                ProjectionStatus.KNOWN_SKIP,
                terminal_form=TerminalForm.VERIFIED_PROOF,
                verifier_boundary_crossed=True,
                residual_delta=-1,
                compression_gain=1.0,
                projection_gain=1.0,
            ),
            ProjectionResult(
                "pr-2",
                "pc-2",
                ProjectionStatus.RESIDUAL_SPLIT,
                residual_delta=-1,
                compression_gain=0.25,
                projection_gain=0.5,
            ),
        ],
    )

    assert trace.terminal_count() == 1
    assert trace.advisory_count() == 1
    assert trace.residual_delta_total() == -2
    assert trace.compression_gain_total() == 1.25
    assert trace.projection_gain_total() == 1.5


def test_projection_trace_to_alchemical_trace_creates_multiplication_and_projection():
    trace = run_projection_engine(
        lawbook_entries=[
            {
                "source": "A",
                "target": "B",
                "terminal_form": "VERIFIED_PROOF",
                "verification_status": "VERIFIED",
            }
        ],
        residual_pairs=[{"source": "A", "target": "C"}],
        agent_id="agent-1",
        episode_id="episode-1",
    )

    alchemical = projection_trace_to_alchemical_trace(trace)

    assert alchemical.has_phase(AlchemicalPhase.MULTIPLICATION)
    assert alchemical.has_phase(AlchemicalPhase.PROJECTION)


def test_projection_trace_to_agent_experiences_keeps_advisory_attempts_unpromoted():
    trace = run_projection_engine(
        lawbook_entries=[],
        residual_pairs=[{"source": "A", "target": "C"}],
        agent_id="agent-1",
        episode_id="episode-1",
    )

    experiences = projection_trace_to_agent_experiences(trace)

    assert experiences
    assert all(not exp.verifier_boundary_crossed for exp in experiences)
    assert all(exp.terminal_form is None for exp in experiences)


def test_roadmap_alignment_catches_unsafe_projection_terminal_claims():
    trace = ProjectionTrace(
        trace_id="pt-bad",
        episode_id="episode-1",
        agent_id="agent-1",
        candidates=[],
        results=[
            ProjectionResult(
                "pr-bad",
                "pc-bad",
                ProjectionStatus.RESIDUAL_SPLIT,
                terminal_form=TerminalForm.VERIFIED_PROOF,
            )
        ],
    )

    report = check_roadmap_alignment(projection_traces=[trace])

    assert not report.is_aligned()
    assert {
        "PROJECTION_TERMINAL_WITHOUT_BOUNDARY",
        "ADVISORY_PROJECTION_CLAIMS_TERMINAL",
    }.issubset({finding.code for finding in report.findings})


def test_projection_cli_runs_on_empty_inputs_and_produces_aligned_report(tmp_path):
    out_json = tmp_path / "projection.json"
    report_json = tmp_path / "alignment.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_projection_engine.py"),
            "--out-json",
            str(out_json),
            "--alignment-report-json",
            str(report_json),
            "--fail-on-critical",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    trace = json.loads(out_json.read_text(encoding="utf-8"))
    report = json.loads(report_json.read_text(encoding="utf-8"))
    assert trace["candidates"] == []
    assert trace["results"] == []
    assert report["is_aligned"] is True
