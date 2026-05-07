import json
import subprocess
import sys


def test_build_lawbook_store_imports_true_proofs(tmp_path):
    csv_path = tmp_path / "true_proofs.csv"
    csv_path.write_text(
        "source_idx,target_idx,proof_route,source_basin,target_basin\n"
        "1,2,variable_identification,same,same\n",
        encoding="utf-8",
    )
    db = tmp_path / "lawbook.sqlite"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/build_lawbook_store.py",
            "--out-db",
            str(db),
            "--true-proofs",
            str(csv_path),
            "--proof-atlas",
            "--quiet",
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    assert result.stdout == ""
    summary = subprocess.run(
        [sys.executable, "scripts/query_lawbook.py", "--db", str(db), "--summary"],
        check=True,
        text=True,
        capture_output=True,
    )
    payload = json.loads(summary.stdout)
    assert payload["warehouse"]["proof_motifs"] >= 1
    assert payload["warehouse"]["lemma_candidates"] >= 1
