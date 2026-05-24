from mathgraph.lean_artifacts import generate_true_congruence_lean_skeleton, write_lean_artifacts
from mathgraph.proof_congruence import explain_bounded_congruence


def test_true_congruence_lean_skeleton_is_unverified(tmp_path):
    trace = explain_bounded_congruence("(x * y) = x", "(x * y) = x", max_depth=2)
    artifact = generate_true_congruence_lean_skeleton(trace)

    assert "Generated candidate artifact" in artifact.content
    assert "Not promoted unless verified by Lean" in artifact.content
    assert artifact.verified is False
    assert artifact.can_promote_truth is False

    rows = write_lean_artifacts(tmp_path, [artifact])
    assert (tmp_path / artifact.filename).exists()
    assert rows[0]["verified"] is False
