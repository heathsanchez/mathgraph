def test_v1611_public_exports():
    import mathgraph

    names = [
        "LogicWorkbench",
        "WorkbenchLayer",
        "EmbeddingStrategyProfile",
        "FaithfulnessAssessment",
        "LogicCombination",
        "VerifierBackendProfile",
        "ProofFinderResult",
        "ModelFinderResult",
        "BenchmarkSuite",
        "CorrespondenceClaim",
        "InterpretationChoicePoint",
        "build_reference_logic_workbench_bundle",
    ]
    for name in names:
        assert hasattr(mathgraph, name)
