import json
import math
import subprocess
import sys

from mathgraph.route_telemetry import (
    RouteTelemetryEvent,
    RouteTelemetryKind,
    RouteTelemetryOutcome,
    build_route_telemetry_ledger,
)
from mathgraph.roadmap_alignment import check_roadmap_alignment
from mathgraph.spectral_htilt import (
    SpectralHTiltConfig,
    build_generator_K,
    build_killing_pressure_from_ledger,
    build_transition_matrix_from_ledger,
    compute_multiplicative_bridge,
    compute_survivor_distribution,
    estimate_left_support_q,
    estimate_right_survival_h,
    estimate_spectral_htilt,
    normalize_vector,
    route_priorities_from_estimate,
)


def test_config_serializes_through_estimate():
    ledger = _sample_ledger()
    estimate = estimate_spectral_htilt(ledger, config=SpectralHTiltConfig(beta=2.0, damping=0.7))

    loaded = estimate.from_json(estimate.to_json())

    assert loaded.config.beta == 2.0
    assert loaded.config.damping == 0.7


def test_transition_matrix_from_ledger_is_row_normalized():
    L = build_transition_matrix_from_ledger(_sample_ledger(), smoothing=0.0)

    assert L["input"]["route_selected"] == 1.0
    assert math.isclose(sum(L["input"].values()), 1.0)
    assert math.isclose(sum(L["root_constructor"].values()), 1.0)


def test_killing_pressure_from_ledger_uses_killed_events():
    V = build_killing_pressure_from_ledger(_sample_ledger(), smoothing=0.0)

    assert V["root_constructor"] == 1.0
    assert V["input"] == 0.0


def test_generator_k_includes_killing_pressure():
    L = {"a": {"b": 1.0}, "b": {"b": 1.0}}
    K = build_generator_K(L, {"b": 0.25})

    assert K["a"]["b"] == 1.0
    assert K["b"]["b"] == 0.75


def test_normalize_vector_handles_zero_vectors_safely():
    normalized = normalize_vector({"a": 0.0, "b": -1.0})

    assert normalized == {"a": 0.5, "b": 0.5}


def test_right_and_left_iterations_produce_normalized_positive_vectors():
    K = build_generator_K(build_transition_matrix_from_ledger(_sample_ledger()), build_killing_pressure_from_ledger(_sample_ledger()))

    h, _, _, _ = estimate_right_survival_h(K, sorted(K), max_iterations=25, tolerance=1e-12, damping=0.85)
    q, _, _, _ = estimate_left_support_q(K, sorted(K), max_iterations=25, tolerance=1e-12, damping=0.85)

    assert all(value >= 0 for value in h.values())
    assert all(value >= 0 for value in q.values())
    assert math.isclose(sum(h.values()), 1.0)
    assert math.isclose(sum(q.values()), 1.0)


def test_survivor_distribution_sums_to_one():
    pi = compute_survivor_distribution({"a": 0.25, "b": 0.75}, {"a": 0.5, "b": 0.5})

    assert math.isclose(sum(pi.values()), 1.0)
    assert pi["b"] > pi["a"]


def test_multiplicative_bridge_changes_with_beta():
    q = {"a": 0.5, "b": 0.5}
    h = {"a": 0.25, "b": 0.75}

    low = compute_multiplicative_bridge(q, h, 1.0)
    high = compute_multiplicative_bridge(q, h, 3.0)

    assert high["b"] > low["b"]


def test_estimate_spectral_htilt_returns_advisory_components():
    estimate = estimate_spectral_htilt(_sample_ledger())

    assert estimate.advisory is True
    assert estimate.transition_L
    assert estimate.killing_V
    assert estimate.generator_K
    assert estimate.state_estimates
    assert any(state.survival_h for state in estimate.state_estimates)
    assert any(state.support_q for state in estimate.state_estimates)
    assert any(state.survivor_pi for state in estimate.state_estimates)
    assert any(state.tilted_mu_beta for state in estimate.state_estimates)
    assert estimate.metadata["not_truth_authority"] is True


def test_route_priorities_from_estimate_returns_sorted_scores():
    estimate = estimate_spectral_htilt(_sample_ledger())

    priorities = route_priorities_from_estimate(estimate, top_n=2)

    assert len(priorities) == 2
    assert priorities[0][1] >= priorities[1][1]


def test_empty_ledger_produces_valid_advisory_estimate():
    estimate = estimate_spectral_htilt(build_route_telemetry_ledger())

    assert estimate.states == ()
    assert estimate.transition_L == {}
    assert estimate.killing_V == {}
    assert estimate.generator_K == {}
    assert estimate.advisory is True
    assert estimate.converged is True


def test_roadmap_alignment_catches_estimate_claiming_verifier_authority():
    estimate = estimate_spectral_htilt(_sample_ledger())
    estimate.metadata["verifier_authority"] = True

    report = check_roadmap_alignment(spectral_htilt_estimates=[estimate])

    assert report.critical_count() >= 1
    assert any(finding.code == "SPECTRAL_HTILT_CLAIMS_VERIFIER_AUTHORITY" for finding in report.findings)


def test_cli_runs_empty_inputs_and_produces_aligned_report(tmp_path):
    out_path = tmp_path / "estimate.json"
    report_path = tmp_path / "alignment.json"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_spectral_htilt.py",
            "--out-json",
            str(out_path),
            "--alignment-report-json",
            str(report_path),
            "--fail-on-critical",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(out_path.read_text(encoding="utf-8"))["advisory"] is True
    assert json.loads(report_path.read_text(encoding="utf-8"))["critical_count"] == 0


def _sample_ledger():
    events = [
        RouteTelemetryEvent(
            event_id="evt-input",
            episode_id="ep",
            claim_id="claim",
            route_kind=RouteTelemetryKind.PROJECTION,
            outcome=RouteTelemetryOutcome.ADVISORY_ONLY,
            from_state="input",
            to_state="route_selected",
            support_weight=1.0,
        ),
        RouteTelemetryEvent(
            event_id="evt-projection",
            episode_id="ep",
            claim_id="claim",
            route_kind=RouteTelemetryKind.PROJECTION,
            outcome=RouteTelemetryOutcome.RESIDUAL,
            from_state="route_selected",
            to_state="projection",
            projection_gain=0.5,
        ),
        RouteTelemetryEvent(
            event_id="evt-root",
            episode_id="ep",
            claim_id="claim",
            route_kind=RouteTelemetryKind.ROOT_CONSTRUCTOR,
            outcome=RouteTelemetryOutcome.SEARCH_MISS,
            from_state="root_constructor",
            to_state="killed",
            killed=True,
            kill_reason="search_miss",
            cost_units=1.0,
        ),
    ]
    return build_route_telemetry_ledger(events=events)

