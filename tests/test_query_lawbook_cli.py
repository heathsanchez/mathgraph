import json
import subprocess
import sys

from mathgraph import LawbookStore


def test_query_lawbook_cli_summary_and_claim(tmp_path):
    db = tmp_path / "lawbook.sqlite"
    store = LawbookStore(db)
    try:
        store.import_claims(
            [
                {
                    "claim_id": "c1",
                    "source_idx": 0,
                    "target_idx": 1,
                    "terminal_form": "FINITE_COUNTERMODEL",
                    "verification_status": "FINITE_VERIFIED",
                }
            ]
        )
    finally:
        store.close()
    summary = subprocess.run(
        [sys.executable, "scripts/query_lawbook.py", "--db", str(db), "--summary"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(summary.stdout)["warehouse"]["claims"] == 1
    claim = subprocess.run(
        [sys.executable, "scripts/query_lawbook.py", "--db", str(db), "--claim", "0", "1"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(claim.stdout)["claim_id"] == "c1"


def test_build_lawbook_store_cli_with_v1662_dir(tmp_path):
    artifact_dir = tmp_path / "v1662"
    artifact_dir.mkdir()
    (artifact_dir / "elevated_derived_false_certificates_v16_6_2.csv").write_text(
        "certificate_id,source_idx,target_idx,table_hash,table,witness,verification_status\n"
        "c1,1,2,h1,\"[[0,1],[1,0]]\",\"{\\\"x\\\":0}\",FINITE_VERIFIED\n",
        encoding="utf-8",
    )
    db = tmp_path / "store.sqlite"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/build_lawbook_store.py",
            "--out-db",
            str(db),
            "--v1662-dir",
            str(artifact_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["summary"]["warehouse"]["refutations"] == 1
