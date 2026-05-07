import json
import subprocess
import sys

from mathgraph.benchmarking import BenchmarkResult, BenchmarkRun, etp_matrix_benchmark_suite_metadata
from mathgraph.lawbook_store import LawbookStore
from mathgraph.workbench_presets import build_mathgraph_etp_workbench_bundle


def test_query_lawbook_workbench_flags(tmp_path):
    db = tmp_path / "lawbook.sqlite"
    store = LawbookStore(db)
    try:
        bundle = build_mathgraph_etp_workbench_bundle()
        for item in bundle["logical_workbenches"]:
            store.add_logical_workbench(item)
        for item in bundle["embedding_strategy_profiles"]:
            store.add_embedding_strategy_profile(item)
        for item in bundle["verifier_backend_profiles"]:
            store.add_verifier_backend_profile(item)
        for item in bundle["faithfulness_assessments"]:
            store.add_faithfulness_assessment(item)
        suite = etp_matrix_benchmark_suite_metadata()
        store.add_benchmark_suite(suite)
        store.add_benchmark_run(BenchmarkRun("run", suite.suite_id))
        store.add_benchmark_result(BenchmarkResult("res", "run", "case"))
    finally:
        store.close()

    flags = (
        "--logical-workbenches",
        "--embedding-strategies",
        "--faithfulness",
        "--logic-combinations",
        "--verifier-backends",
        "--proof-results",
        "--model-results",
        "--benchmark-suites",
        "--benchmark-runs",
        "--benchmark-results",
        "--correspondences",
        "--interpretation-choices",
    )
    for flag in flags:
        result = subprocess.run(
            [sys.executable, "scripts/query_lawbook.py", "--db", str(db), flag],
            check=True,
            text=True,
            capture_output=True,
        )
        assert json.loads(result.stdout) is not None

    result = subprocess.run(
        [sys.executable, "scripts/query_lawbook.py", "--db", str(db), "--summary"],
        check=True,
        text=True,
        capture_output=True,
    )
    summary = json.loads(result.stdout)
    assert "logical_workbenches" in summary["warehouse"]
