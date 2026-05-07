from mathgraph.language_fragments import aot_l23_precedent_fragment, etp_magma_equations_fragment


def test_etp_fragment_supports_magma_operation_type():
    fragment = etp_magma_equations_fragment()
    assert fragment.supports_type("<i,i>")
    assert "binary_magma_operation" in fragment.supported_term_constructors


def test_aot_fragment_has_encoding_and_guards():
    fragment = aot_l23_precedent_fragment()
    assert fragment.supports_type("<<i>>")
    assert "encoding" in fragment.supported_term_constructors
    assert fragment.blocked_term_patterns
