import json
import subprocess
import sys

from mathgraph import LawbookStore


def test_query_lawbook_explicit_source_target_idx_prefers_refutation(tmp_path):
    db = tmp_path / "lawbook.sqlite"
    store = LawbookStore(db)
    try:
        store.import_claims([{"claim_id": "c1", "source_idx": 0, "target_idx": 1}])
        store.import_refutations(
            [
                {
                    "certificate_id": "r1",
                    "source_idx": 0,
                    "target_idx": 1,
                    "terminal_form": "FINITE_COUNTERMODEL",
                    "verification_status": "FINITE_VERIFIED",
                    "trust_level": "FINITE_VERIFIED",
                    "provenance_type": "IMPORTED",
                }
            ]
        )
    finally:
        store.close()
    result = subprocess.run(
        [
            sys.executable,
            "scripts/query_lawbook.py",
            "--db",
            str(db),
            "--source-idx",
            "0",
            "--target-idx",
            "1",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["claim_hit"] is True
    assert payload["refutation_hit"] is True
    assert payload["terminal_form"] == "FINITE_COUNTERMODEL"


def test_query_lawbook_old_claim_and_refutation_forms_still_work(tmp_path):
    db = tmp_path / "lawbook.sqlite"
    store = LawbookStore(db)
    try:
        store.import_claims([{"claim_id": "c1", "source_idx": 2, "target_idx": 3}])
        store.import_refutations([{"certificate_id": "r1", "source_idx": 2, "target_idx": 3}])
    finally:
        store.close()
    claim = subprocess.run(
        [sys.executable, "scripts/query_lawbook.py", "--db", str(db), "--claim", "2", "3"],
        check=True,
        capture_output=True,
        text=True,
    )
    refutation = subprocess.run(
        [sys.executable, "scripts/query_lawbook.py", "--db", str(db), "--refutation", "2", "3"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(claim.stdout)["claim_id"] == "c1"
    assert json.loads(refutation.stdout)["refutation_id"] == "r1"
