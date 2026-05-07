from mathgraph.denotation import DenotationRecord, DenotationStatus
from mathgraph.formal_worlds import etp_magma_formal_world
from mathgraph.language_fragments import etp_magma_equations_fragment
from mathgraph.lawbook_store import LawbookStore
from mathgraph.paradox_guards import set_collapse_guard
from mathgraph.predication import encodes
from mathgraph.reason_containment import ReasonContainmentRecord
from mathgraph.semantic_embeddings import ArtifactRisk, EmbeddingKind, SemanticEmbedding
from mathgraph.object_language import ObjectLanguageFormula, ObjectLanguageTerm
from mathgraph.theory_objectification import (
    AnalyticTruth,
    TheoryDenotation,
    TheoryObjectKind,
    TheoryObjectificationMap,
    TheoryReading,
)
from mathgraph.theory_registry import (
    InferenceRule,
    ProofMethod,
    ProofMethodKind,
    TheoryDeclaration,
    TheoryDeclarationKind,
)
from mathgraph.isabelle_exports import HostObjectTheoremLink, IsabelleExportRecord
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
        store.add_object_language_term(
            ObjectLanguageTerm("term1", "etp_magma", "formal_world_etp_magma", "x")
        )
        store.add_object_language_formula(
            ObjectLanguageFormula("formula1", "etp_magma", "formal_world_etp_magma", "x = x")
        )
        store.add_theory_declaration(
            TheoryDeclaration(
                "decl1",
                "etp_magma",
                "formal_world_etp_magma",
                "T",
                TheoryDeclarationKind.THEOREM,
                "refl",
            )
        )
        store.add_proof_method(
            ProofMethod(
                "pm1",
                "etp_magma",
                "formal_world_etp_magma",
                "T",
                "simp",
                ProofMethodKind.REWRITE_RULE,
            )
        )
        store.add_inference_rule(
            InferenceRule(
                "ir1",
                "etp_magma",
                "formal_world_etp_magma",
                "T",
                "intro",
                ProofMethodKind.INTRO_RULE,
            )
        )
        store.add_isabelle_export_record(
            IsabelleExportRecord("ex1", "aot", "formal_world_aot_precedent", "AOT", "foo")
        )
        store.add_host_object_theorem_link(
            HostObjectTheoremLink("link1", "aot", "formal_world_aot_precedent", "AOT", "host.foo", "obj.foo")
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
        assert len(store.list_object_language_terms("etp_magma")) == 1
        assert len(store.list_object_language_formulas("etp_magma")) == 1
        assert len(store.list_theory_declarations("etp_magma")) == 1
        assert len(store.list_proof_methods("etp_magma")) == 1
        assert len(store.list_inference_rules("etp_magma")) == 1
        assert len(store.list_isabelle_export_records("aot")) == 1
        assert len(store.list_host_object_theorem_links("aot")) == 1
        summary = store.summary()
        assert summary["warehouse"]["typed_objects"] == 1
        assert summary["warehouse"]["predication_facts"] == 1
        assert summary["warehouse"]["theory_declarations"] == 1
    finally:
        store.close()
