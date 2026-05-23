from mathgraph.semantic_validation import (
    FormalClaim,
    InformalClaim,
    SemanticValidationEvidence,
    SemanticValidationStatus,
    check_formal_verification_not_informal_solution,
    check_model_translation_not_truth,
    check_semantic_validation_required,
    validate_claim_translation,
)


def test_formal_only_verified_artifact_passes_semantic_requirement():
    report = check_semantic_validation_required({"formal_verified": True}, None)
    assert report.ok


def test_informal_claim_missing_validation_cannot_claim_solved():
    report = check_semantic_validation_required({"informal_claim_id": "i", "claims_informal_solution": True})
    assert not report.ok
    assert report.violations[0].code == "informal_solution_without_validation"


def test_model_generated_translation_marked_truth_fails():
    report = check_model_translation_not_truth({"model_generated_translation": True, "claims_truth": True})
    assert not report.ok
    assert report.violations[0].code == "model_translation_truth"


def test_human_review_is_validation_evidence_not_formal_verification():
    report = validate_claim_translation(
        InformalClaim("i", "A commutative operation need not be left-zero."),
        FormalClaim("f", "x*y=y*x does not imply x*y=x"),
        evidence=(SemanticValidationEvidence("h", "human_review", reviewer="reviewer"),),
    )
    assert report.ok
    assert report.status == SemanticValidationStatus.VALIDATED


def test_formal_verification_alone_not_informal_solution():
    report = check_formal_verification_not_informal_solution(
        {"formal_verified": True, "claims_informal_solution": True, "semantic_validation_status": "MISSING"}
    )
    assert not report.ok
    assert report.violations[0].code == "formal_verification_not_informal_solution"
