from mathgraph.denotation import DenotationRecord, DenotationStatus
from mathgraph.formal_worlds import etp_magma_formal_world
from mathgraph.language_fragments import etp_magma_equations_fragment
from mathgraph.lawbook_store import LawbookStore
from mathgraph.paradox_guards import set_collapse_guard
from mathgraph.predication import encodes
from mathgraph.reason_containment import ReasonContainmentRecord
from mathgraph.semantic_embeddings import ArtifactRisk, EmbeddingKind, SemanticEmbedding
from mathgraph.theory_objectification import (
    AnalyticTruth,
    TheoryDenotation,
    TheoryObjectKind,
    TheoryObjectificationMap,
    TheoryReading,
)
from mathgraph.types import TypedObject


def test_lawbook_store_persists_v1610_objects(tmp_path):
    store = LawbookStore(tmp_path / "lawbook.sqlite")
    try:
        obj = TypedObject(object_id="root1", type_expr="i", object_kind="RootNode")
        store.add_typed_object(obj)
        store.add_predication_fact(encodes("root1", "projection_left"))
        store.add_denotation_record(
            DenotationRecord(
                denotation_id="den1",
                object_id="root1",
                domain_kernel_id="etp_magma",
                formal_world_id="formal_world_etp_magma",
                denotation_status=DenotationStatus.DENOTES,
            )
        )
        store.add_semantic_embedding(
            SemanticEmbedding(
                embedding_id="emb",
                domain_kernel_id="etp_magma",
                embedding_kind=EmbeddingKind.NATIVE_KERNEL,
                artifact_risk=ArtifactRisk.LOW,
            )
        )
        store.add_language_fragment(etp_magma_equations_fragment())
        store.add_formal_world(etp_magma_formal_world())
        store.add_paradox_guard(set_collapse_guard())
        store.add_theory_objectification_map(
            TheoryObjectificationMap("map1", "etp_magma", "formal_world_etp_magma", "T")
        )
        store.add_theory_denotation(
            TheoryDenotation(
                "td1",
                "etp_magma",
                "formal_world_etp_magma",
                "T",
                "x",
                TheoryObjectKind.INDIVIDUAL_TERM,
                "x_T",
                "i",
                DenotationStatus.DENOTES,
            )
        )
        store.add_theory_reading(
            TheoryReading("tr1", "etp_magma", "formal_world_etp_magma", "T", "x=x", "x_T=x_T", "<>")
        )
        store.add_analytic_truth(
            AnalyticTruth("at1", "etp_magma", "formal_world_etp_magma", "T", "x=x", "tr1")
        )
        store.add_reason_containment_record(
            ReasonContainmentRecord("rc1", "reason1", "etp_magma", "formal_world_etp_magma", "s", "t")
        )

        assert store.get_typed_object("root1")["object_id"] == "root1"
        assert len(store.list_predication_facts(subject_id="root1")) == 1
        assert len(store.list_denotation_records(object_id="root1")) == 1
        assert len(store.list_semantic_embeddings("etp_magma")) == 1
        assert len(store.list_language_fragments("etp_magma")) == 1
        assert len(store.list_formal_worlds("etp_magma")) == 1
        assert len(store.list_paradox_guards()) == 1
        assert len(store.list_theory_objectification_maps("etp_magma")) == 1
        assert len(store.list_theory_denotations("etp_magma")) == 1
        assert len(store.list_theory_readings("etp_magma")) == 1
        assert len(store.list_analytic_truths("etp_magma")) == 1
        assert len(store.list_reason_containment_records("reason1")) == 1
        summary = store.summary()
        assert summary["warehouse"]["typed_objects"] == 1
        assert summary["warehouse"]["predication_facts"] == 1
    finally:
        store.close()
