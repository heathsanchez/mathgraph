from mathgraph.lawbook_store import LawbookStore
from mathgraph.lean_artifacts import LeanArtifact, LeanArtifactKind
from mathgraph.lemma_candidates import LemmaCandidate
from mathgraph.proof_atlas import ProofAtlas
from mathgraph.proof_motifs import ProofMotif, ProofMotifKind


def test_lawbook_store_persists_proof_atlas_objects(tmp_path):
    store = LawbookStore(tmp_path / "lawbook.sqlite")
    try:
        motif = ProofMotif("pm", ProofMotifKind.VARIABLE_IDENTIFICATION, support_count=2)
        candidate = LemmaCandidate("lc", "mg_candidate", proof_motif_id="pm")
        artifact = LeanArtifact("la", LeanArtifactKind.PROOF_SKETCH, "mg_candidate")
        atlas = ProofAtlas("atlas", "etp_magma", None, [motif], [candidate], [artifact])
        store.add_proof_motif(motif)
        store.add_lemma_candidate(candidate)
        store.add_lean_artifact(artifact)
        store.add_proof_atlas(atlas)

        assert store.get_proof_motif("pm")["proof_motif_id"] == "pm"
        assert store.get_lemma_candidate("lc")["candidate_name"] == "mg_candidate"
        assert store.get_lean_artifact("la")["name"] == "mg_candidate"
        assert store.get_proof_atlas("atlas")["atlas_id"] == "atlas"
        summary = store.summary()["warehouse"]
        assert summary["proof_motifs"] == 1
        assert summary["lemma_candidates"] == 1
        assert summary["lean_artifacts"] == 1
        assert summary["proof_atlases"] == 1
    finally:
        store.close()
