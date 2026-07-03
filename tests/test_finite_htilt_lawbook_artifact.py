from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAWBOOK_JSON = ROOT / "artifacts" / "lawbook" / "finite_htilt_survivor_law_v1.json"
LAWBOOK_MD = ROOT / "artifacts" / "lawbook" / "finite_htilt_survivor_law_v1.md"
REASON = ROOT / "artifacts" / "reason_atlas" / "finite_htilt_survivor_law_reason.json"
BOUNDARY = (
    ROOT
    / "artifacts"
    / "obstruction_atlas"
    / "finite_htilt_nonclaims_and_boundaries.json"
)
LAB = ROOT / "experiments" / "continuation_claim_audit_lab"
MANIFEST = LAB / "finite_htilt_survivor_law_bundle_manifest.json"
OUTLINE = LAB / "short_paper_outline_finite_htilt_survivor_law.md"
TABLE = LAB / "short_paper_claim_boundary_table.md"
DOC = ROOT / "docs" / "finite_htilt_survivor_law_verified_kernel.md"

REQUIRED_THEOREMS = {
    "htilt_unnormalized_stationary",
    "htilt_normalized_stationary",
    "doob_row_sum_zero",
    "geometric_bridge_one_eq_piStar",
    "geometric_bridge_nat_one_eq_piStar",
    "geometric_log_exp_bridge_eq_geometric_bridge",
    "multiplicative_bridge_nat_one_eq_piStar",
    "multiplicative_bridge_real_one_eq_piStar",
    "multiplicative_log_exp_pointwise_eq",
    "sum_delta_left",
    "sum_delta_right",
    "sum_mul_delta",
    "sum_delta_mul",
}


def _json(path: Path) -> dict:
    return json.loads(path.read_text())


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_lawbook_entry_is_verified_and_complete() -> None:
    entry = _json(LAWBOOK_JSON)
    assert entry["record_type"] == "LAWBOOK_ENTRY"
    assert entry["status"] == "VERIFIED_PROOF"
    theorem_names = {
        name
        for family in entry["verified_theorems"].values()
        for name in family
    }
    assert REQUIRED_THEOREMS <= theorem_names
    assert entry["bridge_alignment"]["resolved"] is True
    assert len(entry["non_claims"]) >= 7


def test_lawbook_sources_exist_and_hashes_replay() -> None:
    entry = _json(LAWBOOK_JSON)
    sources = entry["source_files"]
    for path in sources.values():
        assert (ROOT / path).is_file()
    assert entry["sha256"]["lean_file"] == _sha256(ROOT / sources["lean_file"])
    assert entry["sha256"]["ledger"] == _sha256(ROOT / sources["lean_ledger"])
    assert entry["sha256"]["report"] == _sha256(ROOT / sources["lean_report"])
    assert LAWBOOK_MD.is_file()


def test_reason_atlas_records_the_finite_cancellation() -> None:
    reason = _json(REASON)
    assert reason["record_type"] == "REASON_ATLAS_ENTRY"
    assert reason["status"] == "ACTIVE_REASON"
    assert len(reason["core_calculation"]) == 6
    assert reason["core_calculation"][-1] == "= 0"


def test_boundary_record_blocks_every_overclaim() -> None:
    boundary = _json(BOUNDARY)
    assert boundary["record_type"] == "BOUNDARY_AND_NONCLAIM_RECORD"
    assert all(row["status"] == "BLOCKED" for row in boundary["blocked_overclaims"])
    claims = " ".join(row["claim"].lower() for row in boundary["blocked_overclaims"])
    for term in (
        "consciousness",
        "h-band",
        "scheduler",
        "perron-frobenius",
        "markov convergence",
        "empirically optimal",
    ):
        assert term in claims


def test_bundle_is_replayable_and_paper_ready() -> None:
    manifest = _json(MANIFEST)
    assert manifest["ready_for_short_paper"] is True
    assert manifest["statuses"]["lean"] == "passed"
    assert manifest["statuses"]["no_placeholder_audit"] == "passed"
    for artifact in manifest["artifacts"]:
        path = ROOT / artifact["path"]
        assert path.is_file()
        assert artifact["sha256"] == _sha256(path)


def test_short_paper_material_has_required_structure() -> None:
    outline = OUTLINE.read_text()
    assert "# Short Paper Outline" in outline
    assert "## Abstract" in outline
    for section in range(1, 8):
        assert f"## {section}." in outline
    table = TABLE.read_text()
    for row in (
        "Exact survivor law",
        "Power/multiplicative bridge β=1",
        "Log-exp equivalence",
        "Perron-Frobenius existence",
        "Empirical h-band",
        "Consciousness",
        "Scheduler performance",
        "Shared viability geometry",
    ):
        assert row in table


def test_docs_include_exact_rerun_commands() -> None:
    text = DOC.read_text()
    assert "lake env lean" in text
    assert "test_finite_htilt_lawbook_artifact.py" in text
    assert "## Boundary / Non-Claims" in text


def test_verified_entry_does_not_promote_blocked_claims() -> None:
    entry = _json(LAWBOOK_JSON)
    nonclaims = " ".join(entry["non_claims"]).lower()
    for term in ("perron-frobenius", "h-band", "consciousness", "scheduler"):
        assert term in nonclaims
    assert entry["claim_ids_promoted"] == [
        "C_HTILT_001_exact_survivor_law",
        "C_HTILT_002_power_bridge_exact_contains",
        "C_HTILT_003_log_exp_equivalence",
    ]
    lean = (ROOT / entry["source_files"]["lean_file"]).read_text()
    assert "theorem perron" not in lean.lower()
