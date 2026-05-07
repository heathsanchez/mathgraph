from mathgraph.formal_worlds import FormalWorldKind, aot_formal_world_precedent, etp_magma_formal_world


def test_formal_world_presets_summarize_context_not_truth():
    etp = etp_magma_formal_world()
    assert etp.domain_kernel_id == "etp_magma"
    assert etp.world_kind is FormalWorldKind.EQUATIONAL_THEORY_WORLD
    assert "not proof" in etp.summary()["truth_boundary"]

    aot = aot_formal_world_precedent()
    assert aot.domain_kernel_id == "aot"
    assert aot.denotation_policy == "negative_free_logic_guarded"
