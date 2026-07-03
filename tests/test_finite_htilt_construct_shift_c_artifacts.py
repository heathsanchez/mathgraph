import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEAN = ROOT / "examples" / "verifier_fixtures" / "lean" / "htilt_shift_bridge.lean"
LAWBOOK = ROOT / "artifacts" / "lawbook" / "finite_htilt_construct_shift_c_v1.json"
LAWBOOK_MD = (
    ROOT / "artifacts" / "lawbook" / "finite_htilt_construct_shift_c_v1.md"
)
REASON = (
    ROOT / "artifacts" / "reason_atlas" / "finite_htilt_construct_shift_c_reason.json"
)
BOUNDARIES = (
    ROOT
    / "artifacts"
    / "obstruction_atlas"
    / "finite_htilt_construct_shift_c_boundaries_v1.json"
)
DOCS = ROOT / "docs" / "finite_htilt_construct_shift_c_v1.md"
MANIFEST = (
    ROOT
    / "experiments"
    / "continuation_claim_audit_lab"
    / "finite_htilt_construct_shift_c_manifest.json"
)
FROZEN_RELEASE = (
    ROOT / "releases" / "finite_htilt_theorem_tower_v1" / "release_manifest.json"
)

FROZEN_RELEASE_SHA256 = (
    "9a272f6354fa55d4e00fb9d2e3c1885a49af6d777524bb06027f00e9c85ba471"
)


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_lean_source_contains_construct_shift_declarations() -> None:
    assert LEAN.is_file()
    text = LEAN.read_text(encoding="utf-8")
    for declaration in (
        "diagonalAbsShift",
        "diagonal_shift_nonneg_of_diagonalAbsShift",
        "exists_shift_makes_diagonal_nonneg",
        "shiftedOperator_nonneg_of_offdiag_with_diagonalAbsShift",
        "exists_shift_makes_shiftedOperator_nonneg",
    ):
        assert declaration in text


def test_lean_source_has_no_placeholders() -> None:
    text = LEAN.read_text(encoding="utf-8")
    for placeholder in ("sorry", "admit", "axiom", "unsafe"):
        assert placeholder not in text


def test_lawbook_records_verified_proof_and_source_hash() -> None:
    lawbook = _json(LAWBOOK)
    assert lawbook["status"] == "VERIFIED_PROOF"
    assert lawbook["artifact_id"] == "finite_htilt_construct_shift_c_v1"
    assert (
        hashlib.sha256(LEAN.read_bytes()).hexdigest()
        == lawbook["lean"]["sha256"]
    )


def test_lawbook_dependency_and_nonclaim_boundary_is_precise() -> None:
    lawbook = _json(LAWBOOK)
    assert "finite_htilt_shift_bridge_v1" in lawbook["depends_on"]
    assert (
        "finite_htilt_pf_discrete_survivor_law_v1"
        in lawbook["does_not_depend_on"]
    )
    nonclaims = " ".join(lawbook["claim_boundary"]["does_not_prove"]).lower()
    assert "irreducibility transfer" in nonclaims
    assert "perron-frobenius invocation" in nonclaims
    assert "full killed-generator bridge" in nonclaims


def test_obstruction_record_keeps_larger_bridge_partial() -> None:
    records = {
        item["id"]: item
        for item in _json(BOUNDARIES)["remaining_obstructions"]
    }
    assert records["irreducibility_transfer_for_shifted_operator"]["status"] == "OPEN"
    assert records["pf_application_to_shifted_operator"]["status"] == "OPEN"
    assert (
        records["killed_generator_bridge_from_discrete_pf"]["status"]
        == "PARTIALLY_CLOSED"
    )


def test_docs_record_explicit_absolute_diagonal_sum() -> None:
    text = DOCS.read_text(encoding="utf-8")
    assert "c=\\sum_i |K_{ii}|" in text
    assert LAWBOOK_MD.is_file()
    assert REASON.is_file()
    manifest = _json(MANIFEST)
    assert manifest["status"] == "VERIFIED_PROOF"
    assert manifest["next_boundary"] == "irreducibility_transfer_for_shifted_operator"


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
        "pf invocation on a=ci+k is proved",
        "irreducibility transfer is proved",
        "c+lambda is the perron root",
    ):
        assert forbidden not in text
