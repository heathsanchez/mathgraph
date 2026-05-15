"""Convenience bundles for registering meta-logical workbench metadata."""

from __future__ import annotations

from mathgraph.benchmarking import (
    etp_matrix_benchmark_suite_metadata,
    logikey_methodology_benchmark_suite_metadata,
)
from mathgraph.embedding_strategies import (
    AutomationBias,
    EmbeddingStrategy,
    EmbeddingStrategyProfile,
    SemanticsRepresentation,
    SyntaxRepresentation,
)
from mathgraph.faithfulness import (
    CompletenessStatus,
    FaithfulnessAssessment,
    FaithfulnessStatus,
    SoundnessStatus,
)
from mathgraph.logical_workbench import logikey_style_workbench, mathgraph_default_workbench
from mathgraph.verifier_backends import (
    isabelle_nitpick_backend_placeholder,
    isabelle_nunchaku_backend_placeholder,
    isabelle_sledgehammer_backend_placeholder,
    lean_backend_placeholder,
    python_finite_table_checker_backend,
)


def build_logikey_style_workbench_bundle() -> dict[str, list[object]]:
    """Return formal-workbench methodology metadata without importing theories."""

    return {
        "logical_workbenches": [logikey_style_workbench()],
        "embedding_strategy_profiles": [
            EmbeddingStrategyProfile(
                profile_id="strategy_logikey_shallow_hol",
                domain_kernel_id="aot",
                formal_world_id="formal_world_aot_precedent",
                strategy=EmbeddingStrategy.SHALLOW_SEMANTIC_EMBEDDING,
                syntax_representation=SyntaxRepresentation.SHALLOW_HOST_TERMS,
                semantics_representation=SemanticsRepresentation.HOST_LAMBDA_SEMANTICS,
                automation_bias=AutomationBias.PROVER_FRIENDLY,
                expected_strengths=["HOL automation", "object-logic experimentation", "benchmarkable embeddings"],
                expected_risks=["host/object theorem boundary", "faithfulness must be assessed"],
                notes="LogiKEy-style shallow embedding strategy metadata only.",
            )
        ],
        "verifier_backend_profiles": [
            isabelle_sledgehammer_backend_placeholder(),
            isabelle_nitpick_backend_placeholder(),
            isabelle_nunchaku_backend_placeholder(),
        ],
        "faithfulness_assessments": [
            FaithfulnessAssessment(
                assessment_id="faithfulness_logikey_style_placeholder",
                domain_kernel_id="aot",
                formal_world_id="formal_world_aot_precedent",
                embedding_id="embedding_aot_isabelle_shallow",
                object_logic="AOT / object logic",
                host_logic="Isabelle/HOL",
                status=FaithfulnessStatus.UNKNOWN,
                soundness_status=SoundnessStatus.UNKNOWN,
                completeness_status=CompletenessStatus.UNKNOWN,
                benchmark_suite_id="benchmark_logikey_methodology",
                notes="Placeholder: no MathGraph mechanized faithfulness proof imported.",
            )
        ],
        "benchmark_suites": [logikey_methodology_benchmark_suite_metadata()],
    }


def build_mathgraph_etp_workbench_bundle() -> dict[str, list[object]]:
    """Return native MathGraph ETP workbench metadata."""

    return {
        "logical_workbenches": [mathgraph_default_workbench()],
        "embedding_strategy_profiles": [
            EmbeddingStrategyProfile(
                profile_id="strategy_etp_native_finite_checker",
                embedding_id="embedding_etp_native_finite_checker",
                domain_kernel_id="etp_magma",
                formal_world_id="formal_world_etp_magma",
                strategy=EmbeddingStrategy.NATIVE_KERNEL,
                syntax_representation=SyntaxRepresentation.NATIVE_OBJECTS,
                semantics_representation=SemanticsRepresentation.FINITE_CHECKER,
                automation_bias=AutomationBias.CERTIFICATE_FRIENDLY,
                expected_strengths=["replayable finite countermodels", "small pure-Python checker"],
                expected_risks=["finite search misses are residual evidence only"],
                notes="Native finite refutation workbench metadata.",
            )
        ],
        "verifier_backend_profiles": [python_finite_table_checker_backend(), lean_backend_placeholder()],
        "faithfulness_assessments": [
            FaithfulnessAssessment(
                assessment_id="faithfulness_etp_native_not_applicable",
                domain_kernel_id="etp_magma",
                formal_world_id="formal_world_etp_magma",
                embedding_id="embedding_etp_native_finite_checker",
                object_logic="universal equational logic over finite magmas",
                host_logic="Python finite checker",
                status=FaithfulnessStatus.NOT_APPLICABLE,
                soundness_status=SoundnessStatus.NOT_APPLICABLE,
                completeness_status=CompletenessStatus.NOT_APPLICABLE,
                benchmark_suite_id="benchmark_etp_matrix_metadata",
                notes="Native checker path; matrix remains benchmark/evaluation data, not proof.",
            )
        ],
        "benchmark_suites": [etp_matrix_benchmark_suite_metadata()],
    }
