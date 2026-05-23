from mathgraph.invariants import (
    TrustBoundaryEvidence,
    check_all_core_invariants,
    check_boundary_evidence_required,
    check_unsafe_artifact_rejected,
)


def test_htilt_cannot_promote_finite_countermodel():
    entry = {
        "status": "ACCEPTED",
        "terminal_form": "FINITE_COUNTERMODEL",
        "source": "htilt_score",
        "advisory": True,
        "provenance": ("htilt",),
        "replay_manifest": {"artifact_hashes": ["h"], "replay_instructions": ["r"]},
    }
    report = check_all_core_invariants(entry, TrustBoundaryEvidence(advisory=True))
    assert not report.ok
    assert any(v.code == "advisory_truth_promotion" for v in report.violations)


def test_unsafe_lean_artifact_rejected():
    report = check_unsafe_artifact_rejected({"artifact_text": "theorem bad : True := by sorry"})
    assert not report.ok
    assert report.violations[0].code == "unsafe_lean_marker"


def test_raw_returncode_success_without_expected_theorem_fails():
    entry = {
        "status": "ACCEPTED",
        "terminal_form": "VERIFIED_PROOF",
        "advisory": False,
        "provenance": ("lean",),
        "replay_manifest": {"artifact_hashes": ["h"], "replay_instructions": ["lake env lean f.lean"]},
    }
    evidence = TrustBoundaryEvidence(replayable=True, advisory=False, raw_returncode_only=True, artifact_hashes=("h",))
    report = check_boundary_evidence_required(entry, evidence)
    assert not report.ok
    assert {v.code for v in report.violations} >= {"raw_returncode_only", "proof_boundary_incomplete"}


def test_valid_finite_countermodel_passes_all_core_invariants():
    entry = {
        "status": "ACCEPTED",
        "terminal_form": "FINITE_COUNTERMODEL",
        "advisory": False,
        "provenance": ("finite_checker",),
        "replay_manifest": {"artifact_hashes": ["h"], "replay_instructions": ["python demo.py"]},
    }
    evidence = TrustBoundaryEvidence(
        verifier_boundary="finite_model_checker",
        replayable=True,
        advisory=False,
        artifact_hashes=("h",),
        witness_checked=True,
        source_satisfied=True,
        target_violated=True,
        provenance=("finite_checker",),
    )
    assert check_all_core_invariants(entry, evidence).ok

def test_valid_named_obstruction_passes():
    entry = {
        "status": "ACCEPTED",
        "terminal_form": "NAMED_OBSTRUCTION",
        "advisory": False,
        "provenance": ("obstruction_audit",),
        "replay_manifest": {"artifact_hashes": ["h"], "replay_instructions": ["inspect residual"]},
    }
    evidence = TrustBoundaryEvidence(
        verifier_boundary="obstruction_audit",
        replayable=True,
        advisory=False,
        artifact_hashes=("h",),
        obstruction_id="obs-1",
        structured_obstruction=True,
        provenance=("obstruction_audit",),
    )
    assert check_all_core_invariants(entry, evidence).ok
