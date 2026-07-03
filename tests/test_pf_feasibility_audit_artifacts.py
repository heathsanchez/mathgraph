import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "experiments" / "continuation_claim_audit_lab"
AUDIT_PATH = LAB / "pf_feasibility_audit.json"
REPORT_PATH = LAB / "pf_feasibility_audit_report.md"
SOURCES_PATH = LAB / "pf_external_sources.md"
PROBE_PATH = LAB / "pf_import_probe_status.json"
OBSTRUCTION_PATH = (
    ROOT
    / "artifacts"
    / "obstruction_atlas"
    / "finite_htilt_pf_existence_obstruction_v1.json"
)

ALLOWED_STATUSES = {
    "READY_TO_IMPORT_FROM_MATHLIB",
    "READY_TO_VENDOR_EXTERNAL_REPO",
    "WAIT_FOR_MATHLIB_PR",
    "REQUIRES_CUSTOM_PF_FORMALIZATION",
    "INSUFFICIENT_INFORMATION",
}


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_required_pf_audit_artifacts_exist() -> None:
    for path in (AUDIT_PATH, REPORT_PATH, SOURCES_PATH, PROBE_PATH, OBSTRUCTION_PATH):
        assert path.is_file(), path


def test_audit_status_and_paper_metadata() -> None:
    audit = _read_json(AUDIT_PATH)

    assert audit["status"] in ALLOWED_STATUSES
    assert audit["external_paper"]["arxiv"] == "2512.07766"
    assert audit["external_paper"]["title"] == (
        "Formalized Hopfield Networks and Boltzmann Machines"
    )
    assert audit["mathlib_status"]["pinned_revision"] == (
        "8f9d9cff6bd728b17a24e163c9402775d9e6a365"
    )


def test_report_has_required_interface_and_target_sections() -> None:
    report = REPORT_PATH.read_text(encoding="utf-8")

    assert "## Interface to Existing Survivor Law" in report
    assert "## Recommended First Formal Target" in report
    assert "`WAIT_FOR_MATHLIB_PR`" in report


def test_external_source_record_is_specific_and_auditable() -> None:
    sources = SOURCES_PATH.read_text(encoding="utf-8")

    assert "https://arxiv.org/abs/2512.07766" in sources
    assert "https://github.com/mkaratarakis/HopfieldNet" in sources
    assert "39920" in sources
    assert "39922" in sources
    assert "exists_positive_eigenvector_of_irreducible" in sources


def test_obstruction_preserves_conditional_boundary() -> None:
    obstruction = _read_json(OBSTRUCTION_PATH)

    assert obstruction["status"] == "ACTIVE_OBSTRUCTION"
    assert "assumes left and right eigenmodes q,h" in obstruction["obstruction"]
    assert any(
        "imported or vendored and compiled" in condition
        for condition in obstruction["blocked_until"]
    )
    assert "No Perron-Frobenius existence is claimed yet." in obstruction["non_claims"]


def test_no_unverified_pf_lawbook_promotion() -> None:
    audit = _read_json(AUDIT_PATH)
    report = REPORT_PATH.read_text(encoding="utf-8")
    obstruction = _read_json(OBSTRUCTION_PATH)

    assert audit["import_probe"]["compiled"] is False
    assert "finite_htilt_pf_existence_v1" not in report
    assert obstruction["feasibility_classification"] != "VERIFIED_PROOF"

    candidate_lawbook = (
        ROOT / "artifacts" / "lawbook" / "finite_htilt_pf_existence_v1.json"
    )
    assert not candidate_lawbook.exists()
