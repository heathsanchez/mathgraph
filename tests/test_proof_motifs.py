from mathgraph.proof_motifs import ProofMotif, ProofMotifKind, infer_proof_motif_kind


def test_proof_motif_inference_and_authority():
    assert infer_proof_motif_kind({"proof_route": "variable_identification"}) == "VARIABLE_IDENTIFICATION"
    assert infer_proof_motif_kind({"proof_route": "transitivity_chain"}) == "TRANSITIVITY_CHAIN"
    assert infer_proof_motif_kind({"proof_route": "projection_left"}) == "PROJECTION_FORCED"
    assert infer_proof_motif_kind({"proof_route": "source_collapse"}) == "SOURCE_COLLAPSE"
    assert infer_proof_motif_kind({"proof_route": "mystery"}) == "UNKNOWN"

    motif = ProofMotif("pm", ProofMotifKind.VARIABLE_IDENTIFICATION)
    assert not motif.is_authoritative()
    assert "advisory" in motif.advisory_warning()
    verified = ProofMotif("pm2", ProofMotifKind.TERM_REWRITE, trust_level="LEAN_VERIFIED")
    assert verified.is_authoritative()
    assert verified.summary()["authoritative"]
