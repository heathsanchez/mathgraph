import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEAN = ROOT / "examples" / "verifier_fixtures" / "lean" / "htilt_shift_bridge.lean"
LAWBOOK = ROOT / "artifacts" / "lawbook" / "finite_htilt_shift_bridge_v1.json"
LAWBOOK_MD = ROOT / "artifacts" / "lawbook" / "finite_htilt_shift_bridge_v1.md"
REASON = (
    ROOT / "artifacts" / "reason_atlas" / "finite_htilt_shift_bridge_reason.json"
)
BOUNDARIES = (
    ROOT
    / "artifacts"
    / "obstruction_atlas"
    / "finite_htilt_shift_bridge_boundaries_v1.json"
)
DOCS = ROOT / "docs" / "finite_htilt_shift_bridge_v1.md"
MANIFEST = (
    ROOT
    / "experiments"
    / "continuation_claim_audit_lab"
    / "finite_htilt_shift_bridge_manifest.json"
)
FROZEN_RELEASE = (
    ROOT / "releases" / "finite_htilt_theorem_tower_v1" / "release_manifest.json"
)

FROZEN_RELEASE_SHA256 = (
    "9a272f6354fa55d4e00fb9d2e3c1885a49af6d777524bb06027f00e9c85ba471"
)


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_lean_source_contains_required_declarations() -> None:
    assert LEAN.is_file()
    text = LEAN.read_text(encoding="utf-8")
    assert "namespace HTiltShiftBridge" in text
    for declaration in (
        "shiftedOperator",
        "shifted_right_eigen",
        "shifted_left_eigen",
        "shifted_doob_bridge",
        "shiftedOperator_nonneg",
    ):
        assert declaration in text


def test_lean_source_has_no_placeholders() -> None:
    text = LEAN.read_text(encoding="utf-8")
    for placeholder in ("sorry", "admit", "axiom", "unsafe"):
        assert placeholder not in text


def test_lawbook_records_verified_proof_and_source_hash() -> None:
    lawbook = _json(LAWBOOK)
    assert lawbook["status"] == "VERIFIED_PROOF"
    assert lawbook["artifact_id"] == "finite_htilt_shift_bridge_v1"
    assert (
        hashlib.sha256(LEAN.read_bytes()).hexdigest()
        == lawbook["lean"]["sha256"]
    )


def test_lawbook_does_not_promote_pf_or_irreducibility() -> None:
    lawbook = _json(LAWBOOK)
    nonclaims = " ".join(lawbook["claim_boundary"]["does_not_prove"]).lower()
    assert "perron-frobenius existence" in nonclaims
    assert "irreducibility transfer" in nonclaims
    assert lawbook["optional_verified_declarations"] == []


def test_obstruction_record_keeps_remaining_bridge_open() -> None:
    boundaries = _json(BOUNDARIES)
    records = {
        item["id"]: item for item in boundaries["remaining_obstructions"]
    }
    assert records["irreducibility_transfer_for_shifted_operator"]["status"] == "OPEN"
    assert records["pf_application_to_shifted_operator"]["status"] == "OPEN"
    assert (
        records["killed_generator_bridge_from_discrete_pf"]["status"]
        == "PARTIALLY_CLOSED"
    )


def test_docs_and_companion_artifacts_record_exact_bridge() -> None:
    assert "D^A_{ij}" in DOCS.read_text(encoding="utf-8")
    assert "c+\\lambda" in DOCS.read_text(encoding="utf-8")
    assert LAWBOOK_MD.is_file()
    assert REASON.is_file()
    assert _json(MANIFEST)["status"] == "VERIFIED_PROOF"


def test_frozen_v1_release_manifest_is_unchanged() -> None:
    assert hashlib.sha256(FROZEN_RELEASE.read_bytes()).hexdigest() == (
        FROZEN_RELEASE_SHA256
    )


def test_created_artifacts_avoid_forbidden_overclaims() -> None:
    paths = (LEAN, LAWBOOK, LAWBOOK_MD, REASON, BOUNDARIES, DOCS, MANIFEST)
    text = "\n".join(path.read_text(encoding="utf-8") for path in paths).lower()
    for forbidden in (
        "proves consciousness",
        "proves h-band universality",
        "proves scheduler performance",
        "proves markov convergence",
        "proves killed-generator pf existence",
        "solves killed-generator bridge",
        "full killed-generator bridge closed",
    ):
        assert forbidden not in text
