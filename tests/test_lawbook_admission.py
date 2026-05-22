from mathgraph.lawbook_admission import AdmissionLevel, ArtifactKind, LawbookAdmissionGate


def test_verified_finite_countermodel_can_be_durable():
    gate = LawbookAdmissionGate()
    decision = gate.evaluate_artifact(
        {"artifact_id": "a1", "artifact_kind": "finite_countermodel_verified", "provenance_type": "finite_checker"},
        {
            "verifier_passed": True,
            "source_satisfied": True,
            "target_violated": True,
            "concrete_witness": {"x": 0},
            "carrier_size": 2,
            "replayable": True,
            "provenance": "finite_checker",
        },
    )
    assert decision.durable is True
    assert decision.admission_level == AdmissionLevel.DURABLE_LAWBOOK
    assert decision.may_enter_durable_lawbook is True


def test_fallback_finite_looking_artifact_cannot_be_durable():
    decision = LawbookAdmissionGate().evaluate_artifact(
        {"artifact_id": "a2", "artifact_kind": "finite_countermodel_verified", "fallback_mode": True},
        {"fallback_mode": True, "verifier_passed": True, "provenance": "smoke"},
    )
    assert decision.durable is False
    assert decision.admission_level == AdmissionLevel.ADVISORY_ONLY
    assert "fallback_artifact_blocked_from_durable" in decision.reason_codes


def test_failed_finite_search_cannot_become_true():
    decision = LawbookAdmissionGate().evaluate_artifact(
        {"artifact_id": "a3", "artifact_kind": "failed_finite_search"},
        {"failed_finite_search": True, "claims_true": True, "provenance": "bounded_search"},
    )
    assert decision.accepted is False
    assert "failed_search_cannot_claim_true" in decision.reason_codes


def test_reason_motif_without_decode_or_verified_link_is_advisory():
    decision = LawbookAdmissionGate().evaluate_artifact(
        {"artifact_id": "m1", "artifact_kind": "reason_motif", "provenance_type": "trace"},
        {"provenance": "trace"},
    )
    assert decision.admission_level == AdmissionLevel.ADVISORY_ONLY
    assert decision.may_influence_scheduler is True
    assert decision.may_enter_durable_lawbook is False


def test_decode_success_alone_is_not_durable():
    decision = LawbookAdmissionGate().evaluate_artifact(
        {"artifact_id": "d1", "artifact_kind": "decode_candidate", "provenance_type": "decode"},
        {"decode_success": True, "provenance": "decode"},
    )
    assert decision.admission_level == AdmissionLevel.CANDIDATE
    assert decision.durable is False


def test_named_obstruction_requires_scope_and_trace():
    bad = LawbookAdmissionGate().evaluate_artifact(
        {"artifact_id": "o1", "artifact_kind": "named_obstruction", "provenance_type": "audit"},
        {"obstruction_name": "blocked", "provenance": "audit"},
    )
    assert bad.durable is False
    good = LawbookAdmissionGate().evaluate_artifact(
        {"artifact_id": "o2", "artifact_kind": "named_obstruction", "provenance_type": "audit"},
        {
            "obstruction_name": "blocked",
            "failure_trace": {"route": "r"},
            "scope": "basin-x",
            "supporting_failed_routes": 1,
            "bounded": True,
            "provenance": "audit",
        },
    )
    assert good.durable is True


def test_lean_verified_proof_can_be_durable():
    decision = LawbookAdmissionGate().evaluate_artifact(
        {"artifact_id": "p1", "artifact_kind": "lean_proof_verified", "provenance_type": "lean"},
        {"lean_verified": True, "proof_artifact": "theorem x", "replayable": True, "provenance": "lean"},
    )
    assert decision.durable is True


def test_missing_provenance_blocks_durable_admission():
    decision = LawbookAdmissionGate().evaluate_artifact(
        {"artifact_id": "a4", "artifact_kind": "finite_countermodel_verified"},
        {
            "verifier_passed": True,
            "source_satisfied": True,
            "target_violated": True,
            "concrete_witness": {"x": 0},
            "carrier_size": 2,
            "replayable": True,
        },
    )
    assert decision.accepted is False
    assert "missing_provenance" in decision.reason_codes


def test_summarize_decisions_counts_cases():
    gate = LawbookAdmissionGate()
    decisions = [
        gate.evaluate_artifact(
            {"artifact_id": "a1", "artifact_kind": "finite_countermodel_verified", "provenance_type": "finite"},
            {
                "verifier_passed": True,
                "source_satisfied": True,
                "target_violated": True,
                "concrete_witness": {"x": 0},
                "carrier_size": 2,
                "replayable": True,
                "provenance": "finite",
            },
        ),
        gate.evaluate_artifact({"artifact_id": "f1", "artifact_kind": "fallback_smoke_artifact"}, {"fallback_mode": True, "provenance": "smoke"}),
    ]
    summary = gate.summarize_decisions(decisions)
    assert summary["total_artifacts_reviewed"] == 2
    assert summary["promoted_durable_count"] == 1
    assert summary["fallback_artifacts_blocked_count"] == 1

