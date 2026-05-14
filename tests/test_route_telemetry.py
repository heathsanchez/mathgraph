import json
import subprocess
import sys

from mathgraph.certificates import TerminalForm
from mathgraph.proof_verification import ProofArtifactKind
from mathgraph.root_constructors import ConstructorAttempt, RootConstructorStatus, RootConstructorTrace
from mathgraph.route_telemetry import (
    HTiltTelemetrySummary,
    RouteTelemetryEvent,
    RouteTelemetryKind,
    RouteTelemetryLedger,
    RouteTelemetryOutcome,
    build_route_telemetry_ledger,
    summarize_h_tilt_telemetry,
    telemetry_events_from_episode,
)
from mathgraph.roadmap_alignment import check_roadmap_alignment
from mathgraph.verification_episode import (
    VerificationEpisodeInput,
    VerificationEpisodeStatus,
    VerificationEpisodeTrace,
    run_verification_episode,
)


def test_route_telemetry_event_serializes_roundtrip():
    event = RouteTelemetryEvent(
        event_id="evt-1",
        episode_id="ep-1",
        claim_id="claim-1",
        route_kind=RouteTelemetryKind.PROJECTION,
        outcome=RouteTelemetryOutcome.KNOWN_SKIP,
        terminal_form=TerminalForm.VERIFIED_PROOF,
        certificate_id="cert-1",
        verifier_boundary_crossed=True,
        from_state="projection",
        to_state="terminal",
        projection_gain=1.0,
        advisory=False,
    )

    assert RouteTelemetryEvent.from_json(event.to_json()).to_dict() == event.to_dict()
    assert RouteTelemetryEvent.from_jsonl_line(event.to_jsonl_line()).is_terminal()


def test_route_telemetry_ledger_serializes_roundtrip():
    ledger = build_route_telemetry_ledger(events=[_advisory_event("ep-1")])

    loaded = RouteTelemetryLedger.from_json(ledger.to_json())

    assert loaded.to_dict() == ledger.to_dict()
    assert loaded.summary["events_total"] == 1


def test_empty_ledger_is_valid_and_advisory():
    ledger = build_route_telemetry_ledger()
    summary = summarize_h_tilt_telemetry(ledger)

    assert ledger.events == []
    assert ledger.advisory_count() == 0
    assert summary.advisory is True
    assert summary.metadata["full_spectral_h_tilt_future_work"] is True


def test_telemetry_events_from_episode_extracts_route_decisions():
    episode = run_verification_episode(episode_input=VerificationEpisodeInput(claim_id="claim-route"), run_alignment=False)

    events = telemetry_events_from_episode(episode)

    assert any(event.from_state == "input" and event.to_state == "route_selected" for event in events)
    assert all(event.advisory for event in events)


def test_terminal_episode_creates_terminal_telemetry_only_with_certificate_boundary():
    episode = VerificationEpisodeTrace(
        episode_id="ep-terminal",
        input=VerificationEpisodeInput(claim_id="claim-terminal"),
        status=VerificationEpisodeStatus.TERMINAL_VERIFIED_PROOF,
        terminal_form=TerminalForm.VERIFIED_PROOF,
        certificate_id="cert-terminal",
        verifier_boundary_crossed=True,
    )

    events = telemetry_events_from_episode(episode)

    assert any(event.outcome == RouteTelemetryOutcome.TERMINAL_VERIFIED_PROOF and event.is_terminal() for event in events)


def test_proof_skeleton_episode_creates_advisory_skeleton_telemetry():
    episode = run_verification_episode(
        episode_input=VerificationEpisodeInput(claim_id="claim-proof", source="x=x", target="x=x"),
        run_alignment=False,
    )

    events = telemetry_events_from_episode(episode)

    skeleton_events = [event for event in events if event.outcome == RouteTelemetryOutcome.PROOF_SKELETON]
    assert skeleton_events
    assert all(not event.is_terminal() for event in skeleton_events)
    assert any(event.metadata["proof_artifact"]["kind"] == ProofArtifactKind.LEAN_SKELETON.value for event in skeleton_events)


def test_search_miss_creates_killed_event_but_not_proof():
    episode = VerificationEpisodeTrace(
        episode_id="ep-miss",
        input=VerificationEpisodeInput(claim_id="claim-miss"),
        status=VerificationEpisodeStatus.RESIDUAL,
        root_constructor_trace=RootConstructorTrace(
            trace_id="root-trace",
            episode_id="ep-miss",
            agent_id=None,
            attempts=[
                ConstructorAttempt(
                    attempt_id="attempt-miss",
                    plan_id="plan-1",
                    status=RootConstructorStatus.SEARCH_MISS,
                    failure_reason="bounded miss",
                )
            ],
        ),
    )

    events = telemetry_events_from_episode(episode)

    miss = [event for event in events if event.outcome == RouteTelemetryOutcome.SEARCH_MISS][0]
    assert miss.killed is True
    assert miss.terminal_form is None
    assert not miss.is_terminal()


def test_build_route_telemetry_ledger_summarizes_counts():
    events = [
        _advisory_event("ep-1"),
        RouteTelemetryEvent(
            event_id="evt-kill",
            episode_id="ep-1",
            claim_id="claim-1",
            route_kind=RouteTelemetryKind.ROOT_CONSTRUCTOR,
            outcome=RouteTelemetryOutcome.SEARCH_MISS,
            from_state="root_constructor",
            to_state="killed",
            cost_units=2.0,
            killed=True,
            kill_reason="search_miss",
        ),
    ]

    ledger = build_route_telemetry_ledger(events=events)

    assert ledger.summary["events_total"] == 2
    assert ledger.summary["route_counts"][RouteTelemetryKind.PROJECTION.value] == 1
    assert ledger.summary["outcome_counts"][RouteTelemetryOutcome.SEARCH_MISS.value] == 1
    assert ledger.summary["transition_counts"]["root_constructor->killed"] == 1
    assert ledger.summary["killing_counts"]["search_miss"] == 1


def test_summarize_h_tilt_telemetry_creates_advisory_route_scores():
    ledger = build_route_telemetry_ledger(events=[_advisory_event("ep-1")])

    summary = summarize_h_tilt_telemetry(ledger, beta=2.0)

    assert isinstance(summary, HTiltTelemetrySummary)
    assert RouteTelemetryKind.PROJECTION.value in summary.route_scores
    assert summary.advisory is True
    assert summary.metadata["full_spectral_h_tilt_future_work"] is True


def test_htilt_summary_does_not_claim_full_spectral_htilt():
    summary = summarize_h_tilt_telemetry(build_route_telemetry_ledger())

    data = json.dumps(summary.to_dict()).lower()

    assert "full_spectral_h_tilt_future_work" in data
    assert "spectral_h_tilt_complete" not in data


def test_roadmap_alignment_catches_unsafe_terminal_telemetry():
    unsafe = RouteTelemetryEvent(
        event_id="evt-unsafe",
        episode_id="ep-unsafe",
        claim_id="claim-unsafe",
        route_kind=RouteTelemetryKind.PROJECTION,
        outcome=RouteTelemetryOutcome.TERMINAL_VERIFIED_PROOF,
        terminal_form=TerminalForm.VERIFIED_PROOF,
        verifier_boundary_crossed=False,
    )
    ledger = build_route_telemetry_ledger(events=[unsafe])

    report = check_roadmap_alignment(route_telemetry_ledgers=[ledger])

    assert report.critical_count() >= 1
    assert any(finding.code == "TELEMETRY_TERMINAL_WITHOUT_BOUNDARY" for finding in report.findings)


def test_cli_runs_empty_inputs_and_produces_aligned_report(tmp_path):
    ledger_path = tmp_path / "ledger.json"
    report_path = tmp_path / "alignment.json"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_route_telemetry.py",
            "--out-ledger-json",
            str(ledger_path),
            "--alignment-report-json",
            str(report_path),
            "--fail-on-critical",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["critical_count"] == 0
    assert json.loads(ledger_path.read_text(encoding="utf-8"))["events"] == []


def _advisory_event(episode_id: str) -> RouteTelemetryEvent:
    return RouteTelemetryEvent(
        event_id=f"evt-{episode_id}",
        episode_id=episode_id,
        claim_id="claim",
        route_kind=RouteTelemetryKind.PROJECTION,
        outcome=RouteTelemetryOutcome.RESIDUAL,
        from_state="projection",
        to_state="residual",
        compression_gain=0.5,
        projection_gain=0.25,
        advisory=True,
    )

