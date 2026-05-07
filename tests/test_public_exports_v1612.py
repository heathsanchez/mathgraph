def test_public_exports_v1612():
    import mathgraph

    for name in [
        "MetabolicCycleConfig",
        "MetabolicCycleResult",
        "MetabolicCycleStageResult",
        "run_metabolic_cycle",
        "MetabolicDiagnostics",
        "build_synthetic_metabolic_frontier",
        "compute_residual_compression_gain",
        "compute_derived_amplification_factor",
        "evaluate_better_shaped_unknown",
    ]:
        assert hasattr(mathgraph, name)

