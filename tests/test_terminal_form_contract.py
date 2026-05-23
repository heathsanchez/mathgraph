from mathgraph.invariants import check_terminal_form_contract


def test_accepted_claim_requires_exactly_one_terminal_form():
    assert check_terminal_form_contract({"status": "ACCEPTED", "terminal_form": "FINITE_COUNTERMODEL"}).ok
    assert not check_terminal_form_contract({"status": "ACCEPTED"}).ok
    assert not check_terminal_form_contract({"status": "ACCEPTED", "terminal_forms": ["VERIFIED_PROOF", "FINITE_COUNTERMODEL"]}).ok


def test_invalid_terminal_form_rejected():
    report = check_terminal_form_contract({"status": "ACCEPTED", "terminal_form": "TRUE"})
    assert not report.ok
    assert report.violations[0].code == "invalid_terminal_form"
