from mathgraph.verification import verify_external_artifact


def test_verify_external_artifact_unknown_kind() -> None:
    result = verify_external_artifact("unknown", {"path": "x"})

    assert result["status"] == "unknown_verification_adapter"
    assert result["kind"] == "unknown"


def test_verify_external_artifact_lean_code_dispatch_returns_status() -> None:
    result = verify_external_artifact("lean_code", {"code": "theorem t : True := True.intro"})

    assert "status" in result
