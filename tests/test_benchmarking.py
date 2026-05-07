from mathgraph.benchmarking import (
    BenchmarkCase,
    BenchmarkExpectedStatus,
    BenchmarkObservedStatus,
    BenchmarkResult,
    BenchmarkRun,
    etp_matrix_benchmark_suite_metadata,
    logikey_methodology_benchmark_suite_metadata,
)


def test_benchmark_records_and_presets():
    case = BenchmarkCase("case1", "suite", expected_status=BenchmarkExpectedStatus.EXPECT_PROOF)
    result = BenchmarkResult(
        "res1",
        "run",
        case.case_id,
        observed_status=BenchmarkObservedStatus.PROOF_FOUND,
        expected_status=case.expected_status,
    )
    assert result.matches_expectation()
    run = BenchmarkRun("run", "suite", total_cases=4, passed_cases=3)
    assert run.pass_rate() == 0.75
    assert etp_matrix_benchmark_suite_metadata().payload["truth_boundary"]
    assert logikey_methodology_benchmark_suite_metadata().payload["advisory_only"]
