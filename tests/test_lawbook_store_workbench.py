from mathgraph.backend_results import ModelFinderResult, ModelFinderStatus, ProofFinderResult, ProofFinderStatus
from mathgraph.benchmarking import BenchmarkCase, BenchmarkResult, BenchmarkRun, etp_matrix_benchmark_suite_metadata
from mathgraph.correspondence import CorrespondenceClaim
from mathgraph.embedding_strategies import EmbeddingStrategy, EmbeddingStrategyProfile
from mathgraph.faithfulness import FaithfulnessAssessment
from mathgraph.interpretation_choice import InterpretationChoicePoint
from mathgraph.lawbook_store import LawbookStore
from mathgraph.logic_combinations import LogicCombination
from mathgraph.logical_workbench import mathgraph_default_workbench
from mathgraph.verifier_backends import python_finite_table_checker_backend


def test_lawbook_store_persists_workbench_objects(tmp_path):
    store = LawbookStore(tmp_path / "lawbook.sqlite")
    try:
        store.add_logical_workbench(mathgraph_default_workbench())
        store.add_embedding_strategy_profile(
            EmbeddingStrategyProfile("profile", strategy=EmbeddingStrategy.NATIVE_KERNEL, domain_kernel_id="etp")
        )
        store.add_faithfulness_assessment(FaithfulnessAssessment("faith", "etp", None, "emb", "obj", "host"))
        store.add_logic_combination(LogicCombination("combo", "combo", ["etp"]))
        store.add_verifier_backend_profile(python_finite_table_checker_backend())
        store.add_proof_finder_result(ProofFinderResult("proof", "claim", "backend", "etp", None, ProofFinderStatus.UNKNOWN))
        store.add_model_finder_result(ModelFinderResult("model", "claim", "backend", "etp", None, ModelFinderStatus.UNKNOWN))
        suite = etp_matrix_benchmark_suite_metadata()
        store.add_benchmark_suite(suite)
        store.add_benchmark_case(BenchmarkCase("case", suite.suite_id))
        store.add_benchmark_run(BenchmarkRun("run", suite.suite_id))
        store.add_benchmark_result(BenchmarkResult("result", "run", "case"))
        store.add_correspondence_claim(CorrespondenceClaim("corr", "etp", None, "motif", "family"))
        store.add_interpretation_choice_point(InterpretationChoicePoint("choice", "etp", None, "◇"))

        assert store.get_logical_workbench("workbench_mathgraph_default")
        assert store.get_embedding_strategy_profile("profile")
        assert store.get_faithfulness_assessment("faith")
        assert store.get_logic_combination("combo")
        assert store.get_verifier_backend_profile("backend_python_finite_table_checker")
        assert len(store.list_proof_finder_results("claim")) == 1
        assert len(store.list_model_finder_results("claim")) == 1
        assert store.get_benchmark_suite(suite.suite_id)
        assert len(store.list_benchmark_cases(suite.suite_id)) == 1
        assert len(store.list_benchmark_runs(suite.suite_id)) == 1
        assert len(store.list_benchmark_results("run")) == 1
        assert store.get_correspondence_claim("corr")
        assert store.get_interpretation_choice_point("choice")
        summary = store.summary()["warehouse"]
        assert summary["logical_workbenches"] == 1
        assert summary["faithfulness_assessments"] == 1
        assert summary["benchmark_suites"] == 1
    finally:
        store.close()
