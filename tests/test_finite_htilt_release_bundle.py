import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "releases" / "finite_htilt_theorem_tower_v1"
MANIFEST_PATH = RELEASE / "release_manifest.json"
HASH_LEDGER_PATH = RELEASE / "hash_ledger.json"

KEY_FILES = {
    "examples/verifier_fixtures/lean/htilt_survivor_law.lean",
    "examples/verifier_fixtures/lean/htilt_discrete_doob_stationary.lean",
    "examples/verifier_fixtures/lean/htilt_pf_discrete_survivor_law.lean",
    "artifacts/lawbook/finite_htilt_survivor_law_v1.json",
    "artifacts/lawbook/finite_htilt_discrete_doob_stationary_v1.json",
    "artifacts/lawbook/finite_htilt_pf_discrete_survivor_law_v1.json",
    "docs/finite_htilt_theorem_tower.md",
    "artifacts/obstruction_atlas/finite_htilt_remaining_boundaries_v1.json",
}


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_release_directory_manifest_and_layers() -> None:
    assert RELEASE.is_dir()
    manifest = _read_json(MANIFEST_PATH)
    assert manifest["status"] == "RELEASE_CANDIDATE"
    assert manifest["ready_for_tag"] is True
    layers = manifest["verified_layers"]
    assert [layer["layer"] for layer in layers] == [1, 2, 3]
    assert all(layer["status"] == "VERIFIED_PROOF" for layer in layers)
    assert layers[2]["environment"]["lean"] == "4.27.0-rc1"
    assert layers[2]["environment"]["external_repo"] == "mkaratarakis/HopfieldNet"


def test_manifest_trust_boundary_is_precise() -> None:
    trust = _read_json(MANIFEST_PATH)["trust_audits"]
    assert trust["pf_portal_sorryAx"] is False
    assert trust["external_subtree_global_placeholder_free"] is False
    assert trust["main_files_no_placeholders"] is True


def test_release_notes_and_replay_cover_all_layers() -> None:
    notes = (RELEASE / "RELEASE_NOTES.md").read_text(encoding="utf-8")
    replay = (RELEASE / "replay_commands.md").read_text(encoding="utf-8")
    for layer in ("Layer 1", "Layer 2", "Layer 3"):
        assert layer in notes
    assert "htilt_survivor_law.lean" in replay
    assert "htilt_discrete_doob_stationary.lean" in replay
    assert "htilt_pf_discrete_survivor_law.lean" in replay
    assert "3218" in replay.replace(",", "")


def test_hash_ledger_contains_and_matches_all_key_files() -> None:
    ledger = _read_json(HASH_LEDGER_PATH)
    assert ledger["hash_algorithm"] == "sha256"
    assert set(ledger["files"]) == KEY_FILES
    for relative, expected in ledger["files"].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected


def test_axiom_audit_and_remaining_boundaries_are_present() -> None:
    audit = (RELEASE / "axiom_audit.md").read_text(encoding="utf-8")
    boundaries = (RELEASE / "remaining_boundaries.md").read_text(encoding="utf-8")
    assert "no `sorryAx` dependency" in audit
    assert "exists_positive_stationary_distribution_of_irreducible" in audit
    assert "killed_generator_bridge_from_discrete_pf" in boundaries
    assert "markov_convergence_not_proved" in boundaries


def test_paper_index_pr_body_tag_plan_and_public_docs() -> None:
    paper_index = (RELEASE / "paper_bundle_index.md").read_text(encoding="utf-8")
    pr_body = (RELEASE / "github_pr_body.md").read_text(encoding="utf-8")
    tag_plan = (RELEASE / "tag_plan.md").read_text(encoding="utf-8")
    assert "papers/finite_htilt_survivor_law/" in paper_index
    assert "papers/finite_htilt_pf_portal/" in paper_index
    assert "## Non-claims" in pr_body
    assert "## Do not tag if" in tag_plan
    assert (ROOT / "docs" / "finite_htilt_release_v1.md").is_file()


def test_release_files_avoid_forbidden_positive_claims() -> None:
    text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in RELEASE.rglob("*")
        if path.is_file()
    ).lower()
    for forbidden in (
        "proves consciousness",
        "proves h-band universality",
        "proves scheduler performance",
        "proves markov convergence",
        "proves killed-generator pf existence",
    ):
        assert forbidden not in text
