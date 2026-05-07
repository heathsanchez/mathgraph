from mathgraph.benchmarking import BenchmarkSuite
from mathgraph.logical_workbench import LogicWorkbench
from mathgraph.verifier_backends import VerifierBackendProfile
from mathgraph.workbench_presets import (
    build_logikey_style_workbench_bundle,
    build_mathgraph_etp_workbench_bundle,
)


def test_workbench_bundles_are_in_memory_only():
    logikey = build_logikey_style_workbench_bundle()
    etp = build_mathgraph_etp_workbench_bundle()
    assert isinstance(logikey["logical_workbenches"][0], LogicWorkbench)
    assert isinstance(logikey["verifier_backend_profiles"][0], VerifierBackendProfile)
    assert isinstance(etp["benchmark_suites"][0], BenchmarkSuite)
