from mathgraph import HostVerifier, SemanticEmbeddingKind, make_aot_domain_kernel
from mathgraph.domain_kernels import DomainKernel


def test_make_aot_domain_kernel_metadata():
    kernel = make_aot_domain_kernel("abc123")
    assert kernel.host_verifier is HostVerifier.ISABELLE_HOL
    assert kernel.embedding_kind is SemanticEmbeddingKind.SHALLOW_SEMANTIC_EMBEDDING
    ontology = set(kernel.ontology_summary)
    assert {"abstract objects", "properties", "possible worlds", "encoding", "exemplification"} <= ontology
    assert kernel.source_commit == "abc123"
    assert "github.com/ekpyron/AOT" in kernel.source_uri


def test_domain_kernel_roundtrip_and_validate():
    kernel = make_aot_domain_kernel()
    roundtrip = DomainKernel.from_dict(kernel.to_dict())
    assert roundtrip.kernel_id == kernel.kernel_id
    assert roundtrip.validate() == roundtrip
