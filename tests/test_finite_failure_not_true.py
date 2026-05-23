from mathgraph.invariants import check_finite_failure_not_true


def test_failed_finite_search_cannot_be_verified_proof():
    report = check_finite_failure_not_true({"finite_search_failed": True, "terminal_form": "VERIFIED_PROOF"})
    assert not report.ok
    assert report.violations[0].code == "finite_failure_as_truth"


def test_failed_finite_search_cannot_claim_true():
    report = check_finite_failure_not_true({"finite_search_miss": True, "truth_value": "TRUE"})
    assert not report.ok
