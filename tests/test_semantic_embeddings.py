from mathgraph.semantic_embeddings import ArtifactRisk, EmbeddingKind, ProofTransportStatus, SemanticEmbedding


def test_native_kernel_safe_when_verified_low_risk():
    embedding = SemanticEmbedding(
        embedding_id="e",
        domain_kernel_id="etp_magma",
        embedding_kind=EmbeddingKind.NATIVE_KERNEL,
        artifact_risk=ArtifactRisk.LOW,
        object_theory_verified=True,
    )
    assert embedding.is_promotion_safe()


def test_shallow_embedding_requires_low_risk_transport_and_faithfulness():
    unsafe = SemanticEmbedding(
        embedding_id="aot",
        domain_kernel_id="aot",
        embedding_kind=EmbeddingKind.SHALLOW_SEMANTIC_EMBEDDING,
        artifact_risk=ArtifactRisk.UNKNOWN,
        object_theory_verified=True,
    )
    assert not unsafe.is_promotion_safe()
    assert "artifact risk" in unsafe.advisory_warning()

    pending = SemanticEmbedding(
        embedding_id="aot2",
        domain_kernel_id="aot",
        embedding_kind=EmbeddingKind.SHALLOW_SEMANTIC_EMBEDDING,
        artifact_risk=ArtifactRisk.LOW,
        object_theory_verified=True,
        proof_transport_status=ProofTransportStatus.TRANSPORT_PENDING,
    )
    assert not pending.is_promotion_safe()

    transported_without_faithfulness = SemanticEmbedding(
        embedding_id="aot3",
        domain_kernel_id="aot",
        embedding_kind=EmbeddingKind.SHALLOW_SEMANTIC_EMBEDDING,
        artifact_risk=ArtifactRisk.LOW,
        object_theory_verified=True,
        proof_transport_status=ProofTransportStatus.TRANSPORT_VALIDATED,
    )
    assert not transported_without_faithfulness.is_promotion_safe()

    safe = SemanticEmbedding(
        embedding_id="aot4",
        domain_kernel_id="aot",
        embedding_kind=EmbeddingKind.SHALLOW_SEMANTIC_EMBEDDING,
        artifact_risk=ArtifactRisk.LOW,
        object_theory_verified=True,
        proof_transport_status=ProofTransportStatus.TRANSPORT_VALIDATED,
        faithfulness_assessment_id="faithfulness_aot",
    )
    assert safe.is_promotion_safe()
