import json
import subprocess
import sys


def test_scan_aot_theory_cli_imports_metadata(tmp_path):
    repo = tmp_path / "AOT"
    repo.mkdir()
    (repo / "AOT_Test.thy").write_text(
        "\n".join(
            [
                "theory AOT_Test",
                "AOT_theorem test_theorem",
                "AOT_lemma test_lemma",
                "AOT_define test_definition",
                "AOT_axiom test_axiom",
                "AOT_world test_world",
            ]
        )
    )
    db = tmp_path / "lawbook.sqlite"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/scan_aot_theory.py",
            "--aot-dir",
            str(repo),
            "--db",
            str(db),
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    payload = json.loads(result.stdout)
    assert payload["stored_declarations"] >= 6

    query = subprocess.run(
        [sys.executable, "scripts/query_lawbook.py", "--db", str(db), "--theory-declarations"],
        check=True,
        text=True,
        capture_output=True,
    )
    rows = json.loads(query.stdout)
    assert any(row["name"] == "test_theorem" for row in rows)
    assert all(row["trust_level"] == "ADVISORY_ROUTE" for row in rows)
