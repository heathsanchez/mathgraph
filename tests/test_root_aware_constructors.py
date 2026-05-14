import json
import subprocess
import sys
from pathlib import Path

from mathgraph.alchemy import AlchemicalPhase
from mathgraph.certificates import TerminalForm
from mathgraph.roadmap_alignment import check_roadmap_alignment
from mathgraph.root_constructors import (
    ConstructorAttempt,
    ConstructorPlan,
    RootConstructorKind,
    RootConstructorStatus,
    RootConstructorTrace,
    RootSignal,
    compile_constructor_plans,
    root_constructor_trace_to_agent_experiences,
    root_constructor_trace_to_alchemical_trace,
    run_root_aware_constructors,
)


ROOT = Path(__file__).resolve().parents[1]


def test_root_signal_serializes_deserializes():
    signal = RootSignal(
        root_id="root-1",
        name="diagonal",
        basin="duplication",
        support=7,
        confidence=0.8,
        features={"motif": "diagonal"},
    )

    restored = RootSignal.from_json(signal.to_json())

    assert restored.to_dict() == signal.to_dict()


def test_constructor_plan_serializes_deserializes():
    plan = ConstructorPlan(
        plan_id="plan-1",
        root_id="root-1",
        source="x=x",
        target="x*y=x",
        source_idx=1,
        target_idx=2,
        kind=RootConstructorKind.DIAGONAL_PRESSURE,
        max_order=3,
        expected_gain=1.2,
    )

    restored = ConstructorPlan.from_json(plan.to_json())

    assert restored.to_dict() == plan.to_dict()


def test_constructor_attempt_serializes_deserializes():
    attempt = ConstructorAttempt(
        attempt_id="attempt-1",
        plan_id="plan-1",
        status=RootConstructorStatus.CANDIDATE_TABLE_FOUND,
        candidate_artifact_id="candidate-1",
        table_order=2,
        witness={"x": 0},
        advisory_notes=("not terminal",),
    )

    restored = ConstructorAttempt.from_json(attempt.to_json())

    assert restored.to_dict() == attempt.to_dict()


def test_candidate_table_is_not_terminal_without_importer_verification():
    attempt = ConstructorAttempt(
        attempt_id="attempt-1",
        plan_id="plan-1",
        status=RootConstructorStatus.CANDIDATE_TABLE_FOUND,
        candidate_artifact_id="candidate-1",
        terminal_form=TerminalForm.FINITE_COUNTERMODEL,
        certificate_id="candidate-cert",
        verifier_boundary_crossed=False,
    )

    assert attempt.is_candidate_only()
    assert not attempt.is_terminal()


def test_importer_verified_attempt_is_terminal_only_with_certificate_and_boundary():
    unsafe = ConstructorAttempt(
        attempt_id="attempt-bad",
        plan_id="plan-1",
        status=RootConstructorStatus.IMPORTER_VERIFIED,
        terminal_form=TerminalForm.FINITE_COUNTERMODEL,
        verifier_boundary_crossed=True,
    )
    safe = ConstructorAttempt(
        attempt_id="attempt-good",
        plan_id="plan-1",
        status=RootConstructorStatus.IMPORTER_VERIFIED,
        terminal_form=TerminalForm.FINITE_COUNTERMODEL,
        certificate_id="cert-1",
        verifier_boundary_crossed=True,
    )

    assert not unsafe.is_terminal()
    assert safe.is_terminal()


def test_search_miss_is_not_proof():
    attempt = ConstructorAttempt(
        attempt_id="attempt-miss",
        plan_id="plan-1",
        status=RootConstructorStatus.SEARCH_MISS,
        terminal_form=TerminalForm.VERIFIED_PROOF,
    )

    assert attempt.is_residual()
    assert not attempt.is_terminal()


def test_compile_constructor_plans_creates_advisory_plans_from_roots_and_residual_pairs():
    signals = [
        RootSignal(
            root_id="root-1",
            name="diagonal pressure",
            basin="duplication",
            support=10,
            confidence=0.75,
            features={"pattern": "diagonal"},
        )
    ]
    residuals = [
        {
            "source": "x=x",
            "target": "x*y=x",
            "basin": "duplication",
        }
    ]

    plans = compile_constructor_plans(root_signals=signals, residual_pairs=residuals, max_order=3)

    assert len(plans) == 1
    assert plans[0].advisory
    assert plans[0].kind == RootConstructorKind.DIAGONAL_PRESSURE


def test_run_root_aware_constructors_dry_run_produces_advisory_attempts_only():
    trace = run_root_aware_constructors(
        root_signals=[RootSignal(root_id="root-1", confidence=0.5)],
        residual_pairs=[{"source": "x=x", "target": "x*y=x"}],
        agent_id="agent-1",
        episode_id="episode-1",
        dry_run=True,
    )

    assert trace.plans
    assert trace.attempts
    assert trace.terminal_count() == 0
    assert all(attempt.status == RootConstructorStatus.ADVISORY_ONLY for attempt in trace.attempts)


def test_root_constructor_trace_to_alchemical_trace_includes_descension_and_preserves_boundary():
    trace = run_root_aware_constructors(
        root_signals=[RootSignal(root_id="root-1", confidence=0.5)],
        residual_pairs=[{"source": "x=x", "target": "x*y=x"}],
        agent_id="agent-1",
        episode_id="episode-1",
        dry_run=True,
    )

    alchemical = root_constructor_trace_to_alchemical_trace(trace)

    assert alchemical.has_phase(AlchemicalPhase.DESCENSION)
    assert not alchemical.is_promoted()


def test_root_constructor_trace_to_agent_experiences_does_not_promote_failed_attempts():
    trace = RootConstructorTrace(
        trace_id="rct-1",
        episode_id="episode-1",
        agent_id="agent-1",
        attempts=[
            ConstructorAttempt(
                attempt_id="attempt-miss",
                plan_id="plan-1",
                status=RootConstructorStatus.SEARCH_MISS,
                failure_reason="bounded miss",
            )
        ],
    )

    experiences = root_constructor_trace_to_agent_experiences(trace)

    assert experiences
    assert experiences[0].terminal_form is None
    assert not experiences[0].verifier_boundary_crossed


def test_roadmap_alignment_catches_unsafe_constructor_terminal_claim():
    trace = RootConstructorTrace(
        trace_id="rct-bad",
        episode_id="episode-1",
        agent_id="agent-1",
        attempts=[
            ConstructorAttempt(
                attempt_id="attempt-bad",
                plan_id="plan-1",
                status=RootConstructorStatus.CANDIDATE_TABLE_FOUND,
                terminal_form=TerminalForm.FINITE_COUNTERMODEL,
                certificate_id="candidate-cert",
                verifier_boundary_crossed=False,
            )
        ],
    )

    report = check_roadmap_alignment(root_constructor_traces=[trace])

    assert not report.is_aligned()
    assert {
        "CONSTRUCTOR_FINITE_COUNTERMODEL_WITHOUT_IMPORTER",
        "CANDIDATE_TABLE_TREATED_AS_TERMINAL",
    }.issubset({finding.code for finding in report.findings})


def test_root_constructor_cli_runs_empty_inputs_and_produces_aligned_report(tmp_path):
    out_json = tmp_path / "root_constructors.json"
    report_json = tmp_path / "alignment.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_root_aware_constructors.py"),
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
    assert trace["root_signals"] == []
    assert trace["plans"] == []
    assert trace["attempts"] == []
    assert report["is_aligned"] is True
