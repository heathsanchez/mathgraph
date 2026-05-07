from mathgraph.embedding_strategies import (
    AutomationBias,
    EmbeddingStrategy,
    EmbeddingStrategyProfile,
)


def test_embedding_strategy_profile_shallow_deep_summary():
    shallow = EmbeddingStrategyProfile("p1", strategy=EmbeddingStrategy.SHALLOW_SEMANTIC_EMBEDDING)
    deep = EmbeddingStrategyProfile("p2", strategy=EmbeddingStrategy.DEEP_SYNTAX_EMBEDDING)
    assert shallow.is_shallow()
    assert not shallow.is_deep()
    assert deep.is_deep()
    assert AutomationBias.PROVER_FRIENDLY.value == "PROVER_FRIENDLY"
    assert shallow.summary()["strategy"] == "SHALLOW_SEMANTIC_EMBEDDING"
