from competitions.sair_stage2.src.certificate_models import (
    FiniteMagmaCertificate,
    LeanJudgeResult,
    stable_certificate_hash,
)


def test_finite_magma_certificate_roundtrip_and_hash_stable():
    cert = FiniteMagmaCertificate(
        eq1_id=1,
        eq2_id=2,
        equation1="x = x",
        equation2="x * x = x",
        n=2,
        table=[[0, 0], [0, 0]],
        witness={"x": 1},
        source_holds_verified_python=True,
        target_fails_verified_python=True,
        family="constant",
    )
    data = cert.to_dict()
    assert data["certificate_hash"] == stable_certificate_hash(cert.to_dict(include_hash=False))
    assert FiniteMagmaCertificate.from_dict(data).to_dict() == data


def test_lean_judge_result_roundtrip():
    result = LeanJudgeResult(eq1_id=1, eq2_id=2, verdict="false", status="accepted", stdout="ok")
    assert LeanJudgeResult.from_dict(result.to_dict()).to_dict()["status"] == "accepted"

