from mathgraph.invariants import check_terminal_form_contract
from mathgraph.terminal_form_contract import TerminalForm, boundary_preserved, decide_terminal_form


def test_accepted_claim_requires_exactly_one_terminal_form():
    assert check_terminal_form_contract({"status": "ACCEPTED", "terminal_form": "FINITE_COUNTERMODEL"}).ok
    assert not check_terminal_form_contract({"status": "ACCEPTED"}).ok
    assert not check_terminal_form_contract({"status": "ACCEPTED", "terminal_forms": ["VERIFIED_PROOF", "FINITE_COUNTERMODEL"]}).ok


def test_invalid_terminal_form_rejected():
    report = check_terminal_form_contract({"status": "ACCEPTED", "terminal_form": "TRUE"})
    assert not report.ok
    assert report.violations[0].code == "invalid_terminal_form"


def test_finite_countermodel_can_promote_false_terminal():
    decision = decide_terminal_form({"status": "finite_countermodel_found", "eq1_holds": True, "eq2_violated": True})
    assert decision.accepted
    assert decision.terminal_form == TerminalForm.FINITE_COUNTERMODEL
    assert decision.can_promote_truth


def test_failed_search_is_residual_not_true():
    decision = decide_terminal_form({"status": "failed_search", "finite_search_miss": True})
    assert not decision.accepted
    assert decision.terminal_form == TerminalForm.NONE
    assert not decision.can_promote_truth


def test_boundary_preserved_for_advisory_rows():
    assert boundary_preserved([{"status": "named_obstruction_advisory", "obstruction_name": "x"}, {"status": "failed_search"}])
