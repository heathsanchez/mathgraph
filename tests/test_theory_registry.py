from mathgraph.semantic_embeddings import ArtifactRisk
from mathgraph.theory_registry import (
    InferenceRule,
    ProofMethod,
    ProofMethodKind,
    TheoryDeclaration,
    TheoryDeclarationKind,
)


def test_theory_registry_records_are_advisory():
    declaration = TheoryDeclaration(
        declaration_id="d",
        domain_kernel_id="aot",
        formal_world_id="w",
        theory_id="AOT_Test",
        declaration_kind=TheoryDeclarationKind.THEOREM,
        name="test_theorem",
        statement="AOT_theorem test_theorem",
        artifact_risk=ArtifactRisk.UNKNOWN,
    )
    assert not declaration.is_verified_inside_mathgraph()
    assert declaration.to_dict()["trust_level"] == "ADVISORY_ROUTE"

    method = ProofMethod(
        proof_method_id="pm",
        domain_kernel_id="aot",
        formal_world_id="w",
        theory_id="AOT_Test",
        name="named_theorems",
        method_kind=ProofMethodKind.CUSTOM_METHOD,
    )
    assert method.to_dict()["method_kind"] == "CUSTOM_METHOD"

    rule = InferenceRule(
        inference_rule_id="ir",
        domain_kernel_id="aot",
        formal_world_id="w",
        theory_id="AOT_Test",
        name="intro",
        rule_kind=ProofMethodKind.INTRO_RULE,
        statement="intro rule metadata",
    )
    assert rule.to_dict()["provenance_type"] == "IMPORTED"
