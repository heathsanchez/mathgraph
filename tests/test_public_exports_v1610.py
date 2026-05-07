import mathgraph


def test_v1610_public_exports():
    for name in [
        "MathGraphType",
        "TypedObject",
        "parse_type_expr",
        "PredicationFact",
        "encodes",
        "DenotationStatus",
        "SemanticEmbedding",
        "EmbeddingKind",
        "LanguageFragment",
        "TheoryObjectificationMap",
        "FormalWorld",
        "ParadoxGuard",
        "ReasonContainmentRecord",
        "make_etp_domain_kernel",
        "should_merge_objects",
    ]:
        assert hasattr(mathgraph, name)
