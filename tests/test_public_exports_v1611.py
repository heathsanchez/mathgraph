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
        "build_logikey_style_workbench_bundle",
    ]
    for name in names:
        assert hasattr(mathgraph, name)
