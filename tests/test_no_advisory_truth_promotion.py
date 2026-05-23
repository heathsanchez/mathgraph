from mathgraph.invariants import check_no_advisory_truth_promotion


def test_route_score_cannot_promote_verified_proof():
    report = check_no_advisory_truth_promotion(
        {
            "status": "ACCEPTED",
            "terminal_form": "VERIFIED_PROOF",
            "source": "route_score",
            "advisory": False,
        }
    )
    assert not report.ok
    assert report.violations[0].code == "advisory_source_truth_promotion"


def test_model_output_advisory_truth_fails():
    report = check_no_advisory_truth_promotion(
        {
            "status": "ACCEPTED",
            "terminal_form": "FINITE_COUNTERMODEL",
            "source": "model_output",
            "advisory": True,
        }
    )
    assert not report.ok
