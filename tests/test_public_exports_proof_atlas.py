def test_proof_atlas_public_exports():
    import mathgraph

    for name in (
        "ProofMotif",
        "ProofMotifKind",
        "ProofRouteStatus",
        "LemmaCandidate",
        "LemmaCandidateStatus",
        "CutIntroductionKind",
        "LeanArtifact",
        "LeanArtifactKind",
        "LeanVerificationStatus",
        "ProofAtlas",
        "build_proof_atlas_from_true_rows",
        "discover_true_proof_artifacts",
        "load_true_proof_rows",
        "normalize_true_proof_row",
        "import_true_proof_artifacts_to_store",
    ):
        assert hasattr(mathgraph, name)
