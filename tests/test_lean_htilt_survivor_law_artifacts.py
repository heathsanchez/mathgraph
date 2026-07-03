from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
LEAN_FILE = ROOT / "examples" / "verifier_fixtures" / "lean" / "htilt_survivor_law.lean"
LAB = ROOT / "experiments" / "continuation_claim_audit_lab"
LEDGER = LAB / "lean_htilt_survivor_law_ledger.json"
REPORT = LAB / "lean_htilt_survivor_law_report.md"
UPDATE = LAB / "claim_ledger_lean_update.json"
PROJECT = LAB / "lean_project"
ALLOWED = {"VERIFIED_PROOF", "NOT_ATTEMPTED", "OBSTRUCTED"}


def _ledger() -> dict:
    return json.loads(LEDGER.read_text())


def test_lean_htilt_artifacts_exist() -> None:
    assert LEAN_FILE.is_file()
    assert LEDGER.is_file()
    assert REPORT.is_file()
    assert UPDATE.is_file()


def test_ledger_statuses_are_gated_by_compile_evidence() -> None:
    ledger = _ledger()
    assert ledger["status"] in ALLOWED
    assert set(ledger["theorems"].values()) <= ALLOWED
    if "VERIFIED_PROOF" in ledger["theorems"].values():
        assert ledger["compiled"] is True
        assert ledger["returncode"] == 0
        assert ledger["no_sorry"] is True
        assert ledger["no_admit"] is True
        assert ledger["no_target_axiom"] is True


def test_source_has_no_untrusted_proof_markers() -> None:
    source = LEAN_FILE.read_text()
    assert re.search(r"\b(sorry|admit|axiom|unsafe)\b", source) is None
    assert "multiplicativeBridgeNat" in source
    assert "multiplicative_bridge_nat_one_eq_piStar" in source


def test_bridge_alignment_is_explicit_and_resolved() -> None:
    ledger = _ledger()
    alignment = ledger["bridge_alignment"]
    assert alignment["resolved"] is True
    assert alignment["geometric_bridge"] == "geometricBridge"
    assert "multiplicativeBridgeNat" in alignment["paper_native_bridge"]
    assert alignment["geometric_bridge"] not in alignment["paper_native_bridge"]


def test_non_claims_and_command_are_explicit() -> None:
    ledger = _ledger()
    report = REPORT.read_text()
    joined = " ".join(ledger["non_claims"]).lower()
    for boundary in (
        "consciousness",
        "empirical h-band",
        "scheduler",
        "perron-frobenius",
    ):
        assert boundary in joined
    if "VERIFIED_PROOF" in report:
        assert "lake env lean" in report
        assert ledger["command"].startswith("lake env lean")


def test_only_algebraic_claims_are_promoted() -> None:
    update = json.loads(UPDATE.read_text())
    assert update["empirical_claims_promoted"] == []
    assert update["scheduler_claims_promoted"] == []
    assert update["metaphysical_claims_promoted"] == []
    assert set(update["claims"]) == {
        "C_HTILT_001_exact_survivor_law",
        "C_HTILT_002_power_bridge_exact_contains",
        "C_HTILT_003_log_exp_equivalence",
    }
    assert all(
        row["current_status"] == "VERIFIED_PROOF"
        for row in update["claims"].values()
    )
    assert "paper-native multiplicative bridge" in update["claims"][
        "C_HTILT_002_power_bridge_exact_contains"
    ]["verified_scope"].lower()
    if (
        update["claims"]["C_HTILT_003_log_exp_equivalence"]["current_status"]
        == "VERIFIED_PROOF"
    ):
        assert "multiplicative_log_exp_pointwise_eq" in LEAN_FILE.read_text()


def test_report_records_bridge_alignment_and_non_claims() -> None:
    report = REPORT.read_text()
    assert "## Bridge Alignment Patch" in report
    assert "## Corrected Claim Boundary" in report
    assert "`geometricBridge`" in report
    assert "`multiplicativeBridgeNat`" in report


def test_lean_fixture_recompiles_when_pinned_mathlib_is_present() -> None:
    mathlib_olean = (
        PROJECT
        / ".lake"
        / "packages"
        / "mathlib"
        / ".lake"
        / "build"
        / "lib"
        / "lean"
        / "Mathlib"
        / "Analysis"
        / "SpecialFunctions"
        / "Pow"
        / "Real.olean"
    )
    if shutil.which("lake") is None or not mathlib_olean.is_file():
        pytest.skip("pinned local Mathlib build is unavailable")
    completed = subprocess.run(
        ["lake", "env", "lean", str(LEAN_FILE)],
        cwd=PROJECT,
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
