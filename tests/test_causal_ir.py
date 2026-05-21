from mathgraph.causal_ir import CausalClaim, CausalClaimKind, CausalEdge, CausalVariable, Intervention


def test_observational_claim_passes_simple_check():
    claim = CausalClaim("c1", CausalClaimKind.OBSERVATIONAL, [CausalVariable("x")], [], "P(x)")
    ok, _ = claim.simple_identifiability_check()
    assert ok


def test_interventional_no_confound_claim_passes_as_probable():
    claim = CausalClaim(
        "c2",
        CausalClaimKind.INTERVENTIONAL,
        [CausalVariable("x"), CausalVariable("y")],
        [CausalEdge("x", "y")],
        "effect",
        interventions=[Intervention("x", 1)],
    )
    ok, reason = claim.simple_identifiability_check()
    assert ok
    assert "probably" in reason


def test_confounded_interventional_claim_fails():
    claim = CausalClaim(
        "c3",
        CausalClaimKind.INTERVENTIONAL,
        [CausalVariable("x"), CausalVariable("y")],
        [CausalEdge("x", "y", is_confounded=True)],
        "effect",
    )
    ok, _ = claim.simple_identifiability_check()
    assert not ok


def test_latent_variable_claim_fails():
    claim = CausalClaim("c4", CausalClaimKind.INTERVENTIONAL, [CausalVariable("u", is_latent=True)], [], "effect")
    ok, _ = claim.simple_identifiability_check()
    assert not ok


def test_obstruction_payload_is_named_obstruction_and_advisory():
    claim = CausalClaim("c5", CausalClaimKind.COUNTERFACTUAL, [], [], "counterfactual")
    payload = claim.to_named_obstruction("blocked")
    assert payload["terminal_form"] == "NAMED_OBSTRUCTION"
    assert payload["advisory"] is True
