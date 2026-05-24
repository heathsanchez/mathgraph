from mathgraph.proof_congruence import ProofCongruenceClosure, explain_bounded_congruence


def test_bounded_congruence_forces_same_target_with_trace():
    trace = explain_bounded_congruence("(x * y) = x", "(x * y) = x", max_depth=3)

    assert trace.forced_equal is True
    assert trace.trust_level == "BOUNDED_CONGRUENCE_TRACE"
    assert trace.proof_status == "bounded_congruence_trace"
    assert trace.advisory_only is True
    assert trace.can_promote_truth is False
    assert trace.proof_steps


def test_bounded_congruence_candidate_when_not_forced():
    closure = ProofCongruenceClosure.from_source_equation("(x * y) = x", max_depth=2)
    trace = closure.explain_target("(x * y) = y")

    assert trace.forced_equal is False
    assert trace.trust_level == "CANDIDATE_PROOF_TEMPLATE"
    assert trace.can_promote_truth is False
