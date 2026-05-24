from mathgraph.proof_congruence import explain_bounded_congruence
from mathgraph.true_proof_templates import build_true_proof_template_inventory, classify_true_pair


def test_classify_reflexive_true_pair_is_advisory_template():
    row = classify_true_pair("(x * y) = x", "(x * y) = x")

    assert row["template_family"] == "reflexive_same_equation"
    assert row["proof_status"] == "proof_template_generated"
    assert row["advisory_only"] is True
    assert row["can_promote_truth"] is False
    assert row["needs_lean"] is True


def test_classify_bounded_trace_as_bounded_not_lean_verified():
    trace = explain_bounded_congruence("(x * y) = x", "(x * y) = x", max_depth=2)
    row = classify_true_pair("(x * y) = x", "(x * y) = x", closure_trace=trace)

    assert row["trust_level"] == "BOUNDED_CONGRUENCE_TRACE"
    assert row["proof_status"] == "bounded_congruence_trace"
    assert row["can_promote_truth"] is False


def test_inventory_builds_rows():
    equations = ["x = x", "(x * y) = x"]
    rows = build_true_proof_template_inventory([(0, 0), (1, 1)], equations)

    assert len(rows) == 2
    assert all(row["advisory_only"] for row in rows)
