from pathlib import Path

from mathgraph.metabolic_cycle import MetabolicCycleConfig, run_metabolic_cycle


def test_metabolic_cycle_synthetic_writes_artifacts(tmp_path):
    result = run_metabolic_cycle(
        MetabolicCycleConfig(
            store_path=str(tmp_path / "cycle.sqlite"),
            out_dir=str(tmp_path / "cycle"),
            max_tasks=20,
            allow_synthetic_seed=True,
        )
    )
    assert result.summary["initial_claim_count"] > 0
    assert result.stages
    assert result.summary["contradiction_count"] == 0
    assert (
        result.summary["primitive_countermodels_added"]
        + result.summary["primitive_proofs_added"]
        + result.summary["obstructions_added"]
        > 0
    )
    assert result.summary["authoritative_artifact_count"] >= (
        result.summary["primitive_countermodels_added"] + result.summary["primitive_proofs_added"]
    )
    for key in ("metabolic_cycle_report", "metabolic_cycle_summary", "next_frontier"):
        assert key in result.artifacts
        assert Path(result.artifacts[key]).exists()

