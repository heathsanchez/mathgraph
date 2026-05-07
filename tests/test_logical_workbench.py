from mathgraph.logical_workbench import (
    WorkbenchLifecycleStatus,
    logikey_style_workbench,
    mathgraph_default_workbench,
)


def test_logical_workbench_presets_and_readiness():
    logikey = logikey_style_workbench()
    assert logikey.summary()["truth_boundary"]
    assert not logikey.is_application_ready()
    mathgraph = mathgraph_default_workbench()
    assert mathgraph.lifecycle_status is WorkbenchLifecycleStatus.BENCHMARKED
    assert "Verifier" in mathgraph.notes or "Verifiers" in mathgraph.notes
