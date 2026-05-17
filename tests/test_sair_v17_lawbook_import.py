from mathgraph.sair_v17_lawbook import (
    SAIR_V17_PACKAGE_COUNTS,
    TERMINAL_FORM_CONTRACT,
    pair_key,
    parse_pair_key,
)


def test_pair_key_roundtrip():
    key = pair_key(3303, 4269)
    assert key == "3303_4269"
    assert parse_pair_key(key) == (3303, 4269)


def test_terminal_contract_present():
    assert "VERIFIED_PROOF" in TERMINAL_FORM_CONTRACT
    assert "FINITE_COUNTERMODEL" in TERMINAL_FORM_CONTRACT
    assert "NAMED_OBSTRUCTION" in TERMINAL_FORM_CONTRACT


def test_package_counts_present():
    assert "combined_terminal_count" in SAIR_V17_PACKAGE_COUNTS
    assert SAIR_V17_PACKAGE_COUNTS["combined_terminal_count"] >= 0
