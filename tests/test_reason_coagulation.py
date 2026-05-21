from mathgraph.reason_coagulation import coagulate_reasons


def test_attempts_group_into_constructor_and_routing_reasons():
    attempts = [
        {"attempt_id": "a1", "artifact_id": "x", "domain": "sair", "route": "r", "success": 1},
        {"attempt_id": "a2", "artifact_id": "x", "domain": "sair", "route": "r", "success": 1},
    ]
    artifacts = [{"artifact_id": "x", "domain": "sair", "basin": "b", "terminal_form": "FINITE_COUNTERMODEL"}]
    reasons = coagulate_reasons(attempts, artifacts)
    assert reasons[0].support_count == 2
    assert reasons[0].verified_support_count == 2
    assert reasons[0].promotion_status == "SUPPORTED_REASON"
    assert reasons[0].promotion_status != "LAWBOOK_REASON"


def test_obstructions_group_into_obstruction_family():
    reasons = coagulate_reasons([], [], [{"domain": "sair", "basin": "b", "obstruction_type": "timeout", "route_killed": "r"}])
    assert reasons[0].reason_type == "obstruction_family"
