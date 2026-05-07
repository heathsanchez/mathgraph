from mathgraph.verifier_backends import (
    BackendRole,
    isabelle_nitpick_backend_placeholder,
    python_finite_table_checker_backend,
)


def test_backend_presets_authority_boundary():
    finite = python_finite_table_checker_backend()
    assert finite.is_verifier_authoritative_for_native()
    assert BackendRole.CERTIFICATE_CHECKER in finite.roles
    assert finite.summary()["supports_models"]

    nitpick = isabelle_nitpick_backend_placeholder()
    assert not nitpick.is_verifier_authoritative_for_native()
    assert BackendRole.MODEL_FINDER in nitpick.roles
