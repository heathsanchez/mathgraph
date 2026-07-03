import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "experiments" / "pf_port_lab"
STATUS_PATH = LAB / "pf_port_lab_status.json"
REPORT_PATH = LAB / "pf_port_lab_report.md"
TRACE_PATH = LAB / "pf_port_obstruction_trace.md"
OBSTRUCTION_PATH = (
    ROOT
    / "artifacts"
    / "obstruction_atlas"
    / "finite_htilt_pf_port_obstruction_v1.json"
)
CONDITIONAL_LEAN = (
    ROOT / "examples" / "verifier_fixtures" / "lean" / "htilt_discrete_doob_stationary.lean"
)
PF_LEAN = (
    ROOT / "examples" / "verifier_fixtures" / "lean" / "htilt_pf_discrete_survivor_law.lean"
)
CONDITIONAL_LAWBOOK = (
    ROOT / "artifacts" / "lawbook" / "finite_htilt_discrete_doob_stationary_v1.json"
)
PF_LAWBOOK = (
    ROOT / "artifacts" / "lawbook" / "finite_htilt_pf_discrete_survivor_law_v1.json"
)
EXISTING_LAWBOOK = (
    ROOT / "artifacts" / "lawbook" / "finite_htilt_survivor_law_v1.json"
)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_required_port_lab_artifacts_exist() -> None:
    for path in (
        STATUS_PATH,
        REPORT_PATH,
        TRACE_PATH,
        OBSTRUCTION_PATH,
        CONDITIONAL_LEAN,
        PF_LEAN,
    ):
        assert path.is_file(), path


def test_status_classification_is_allowed() -> None:
    status = _read_json(STATUS_PATH)
    assert status["classification"] in {
        "NEW_VERIFIED_DISCRETE_KERNEL",
        "NEW_VERIFIED_PF_PORTAL",
        "SHARPENED_OBSTRUCTION_ONLY",
    }
    assert status["pf_port_status"] in {
        "PORTED_AND_COMPILED",
        "PARTIAL_PORT",
        "FAILED_TO_PORT",
        "KILLED_BY_SCOPE",
        "NOT_ATTEMPTED",
    }


def test_conditional_lawbook_claim_requires_compiled_source() -> None:
    status = _read_json(STATUS_PATH)["conditional_discrete_theorem"]
    assert status["compiled"] is True
    assert status["lawbook_created"] is True
    assert CONDITIONAL_LEAN.is_file()
    lawbook = _read_json(CONDITIONAL_LAWBOOK)
    assert lawbook["status"] == "VERIFIED_PROOF"
    assert lawbook["sha256"]["lean_file"] == _sha256(CONDITIONAL_LEAN)


def test_pf_lawbook_claim_requires_compiled_clean_dependency_graph() -> None:
    status = _read_json(STATUS_PATH)["pf_existence_theorem"]
    assert status["compiled"] is True
    assert status["lawbook_created"] is True
    assert status["depends_on_sorryAx"] is False
    assert PF_LEAN.is_file()
    lawbook = _read_json(PF_LAWBOOK)
    assert lawbook["status"] == "VERIFIED_PROOF"
    assert lawbook["boundary"]["excluded_axioms"] == ["sorryAx"]
    assert lawbook["dependency_precision"]["portal_theorem_depends_on_upstream_sorry"] is False
    assert lawbook["sha256"]["lean_file"] == _sha256(PF_LEAN)


def test_new_local_lean_files_have_no_placeholder_tokens() -> None:
    forbidden = re.compile(r"\b(sorry|admit|axiom|unsafe)\b")
    for path in (CONDITIONAL_LEAN, PF_LEAN):
        source_without_comments = re.sub(
            r"/-.*?-/", "", path.read_text(encoding="utf-8"), flags=re.DOTALL
        )
        assert forbidden.search(source_without_comments) is None


def test_existing_survivor_lawbook_remains_conditional() -> None:
    lawbook = _read_json(EXISTING_LAWBOOK)
    assert lawbook["artifact_id"] == "finite_htilt_survivor_law_v1"
    assert lawbook["status"] == "VERIFIED_PROOF"
    assert "Does not prove Perron-Frobenius existence." in lawbook["non_claims"]


def test_nonclaims_block_markov_convergence() -> None:
    pf_lawbook = _read_json(PF_LAWBOOK)
    obstruction = _read_json(OBSTRUCTION_PATH)
    report = REPORT_PATH.read_text(encoding="utf-8")

    assert any("Markov convergence" in claim for claim in pf_lawbook["non_claims"])
    assert "No Markov convergence is proved." in obstruction["non_claims"]
    assert "No killed-generator" in report


def test_obstruction_records_verified_portal_and_remaining_packaging_boundary() -> None:
    obstruction = _read_json(OBSTRUCTION_PATH)
    assert obstruction["status"] == "PORTAL_VERIFIED"
    assert obstruction["conditional_discrete_kernel"] == "VERIFIED_PROOF"
    assert obstruction["pf_existence_kernel"] == "VERIFIED_PROOF"
    assert "Lean 4.28.0" in obstruction["remaining_obstruction"]
