from mathgraph.terminal_schema import (
    CanonicalTerminalForm,
    RefutationKind,
    can_promote_terminal_form,
    refutation_kind_from_legacy,
    terminal_form_from_legacy,
)


def test_finite_countermodel_maps_to_refutation_certificate():
    assert terminal_form_from_legacy("FINITE_COUNTERMODEL") == CanonicalTerminalForm.REFUTATION_CERTIFICATE
    assert refutation_kind_from_legacy("FINITE_COUNTERMODEL") == RefutationKind.FINITE_COUNTERMODEL


def test_verified_proof_cannot_promote_from_advisory_only():
    assert not can_promote_terminal_form("VERIFIED_PROOF", "HIGH", "ADVISORY_ONLY", "cert1")


def test_finite_refutation_promotes_with_finite_boundary_and_certificate():
    assert can_promote_terminal_form("REFUTATION_CERTIFICATE", "HIGH", "FINITE_CHECKED", "cert1")
    assert can_promote_terminal_form("FINITE_COUNTERMODEL", "HIGH", "FINITE_CHECKED", "cert1")


def test_refutation_without_certificate_cannot_promote():
    assert not can_promote_terminal_form("REFUTATION_CERTIFICATE", "HIGH", "FINITE_CHECKED", None)


def test_named_obstruction_is_not_proof_or_refutation():
    assert can_promote_terminal_form("NAMED_OBSTRUCTION", "OBSTRUCTION_TRACE", "ADVISORY_ONLY")
    assert not can_promote_terminal_form("NAMED_OBSTRUCTION", "VERIFIED_PROOF", "LEAN_TYPECHECKED")


def test_unknown_legacy_strings_map_to_none():
    assert terminal_form_from_legacy("mystery") == CanonicalTerminalForm.NONE
