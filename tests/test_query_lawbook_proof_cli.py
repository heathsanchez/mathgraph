import json
import subprocess
import sys

from mathgraph.lawbook_store import LawbookStore
from mathgraph.lean_artifacts import LeanArtifact, LeanArtifactKind, LeanVerificationStatus
from mathgraph.lemma_candidates import LemmaCandidate
from mathgraph.proof_atlas import ProofAtlas
from mathgraph.proof_motifs import ProofMotif, ProofMotifKind


def test_query_lawbook_proof_flags(tmp_path):
    db = tmp_path / "lawbook.sqlite"
    store = LawbookStore(db)
    try:
        motif = ProofMotif("pm", ProofMotifKind.TRANSITIVITY_CHAIN, support_count=5)
        candidate = LemmaCandidate("lc", "mg_chain", expected_covered_claims=5)
        artifact = LeanArtifact(
            "la",
            LeanArtifactKind.COMPLETE_PROOF,
            "mg_chain",
            verification_status=LeanVerificationStatus.LEAN_VERIFIED,
            trust_level="LEAN_VERIFIED",
        )
        store.add_proof_motif(motif)
        store.add_lemma_candidate(candidate)
        store.add_lean_artifact(artifact)
        store.add_proof_atlas(ProofAtlas("atlas", "etp_magma", None, [motif], [candidate], [artifact]))
    finally:
        store.close()

    flags = (
        "--proof-motifs",
        "--lemma-candidates",
        "--lean-artifacts",
        "--proof-atlases",
        "--top-proof-motifs",
        "10",
        "--top-lemma-candidates",
        "10",
        "--verified-lean-artifacts",
    )
    commands = [
        ("--proof-motifs",),
        ("--lemma-candidates",),
        ("--lean-artifacts",),
        ("--proof-atlases",),
        ("--top-proof-motifs", "10"),
        ("--top-lemma-candidates", "10"),
        ("--verified-lean-artifacts",),
    ]
    for command in commands:
        result = subprocess.run(
            [sys.executable, "scripts/query_lawbook.py", "--db", str(db), *command],
            check=True,
            text=True,
            capture_output=True,
        )
        assert json.loads(result.stdout) is not None
    summary = subprocess.run(
        [sys.executable, "scripts/query_lawbook.py", "--db", str(db), "--summary"],
        check=True,
        text=True,
        capture_output=True,
    )
    assert json.loads(summary.stdout)["warehouse"]["proof_motifs"] == 1
