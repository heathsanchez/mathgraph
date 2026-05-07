import json
import subprocess
import sys


def test_register_logical_workbench_cli_presets(tmp_path):
    db = tmp_path / "workbench.sqlite"
    for preset in ("logikey", "etp", "mathgraph"):
        result = subprocess.run(
            [sys.executable, "scripts/register_logical_workbench.py", "--db", str(db), "--preset", preset],
            check=True,
            text=True,
            capture_output=True,
        )
        payload = json.loads(result.stdout)
        assert payload["status"] == "registered"

    for flag in ("--logical-workbenches", "--verifier-backends", "--faithfulness", "--benchmark-suites"):
        result = subprocess.run(
            [sys.executable, "scripts/query_lawbook.py", "--db", str(db), flag],
            check=True,
            text=True,
            capture_output=True,
        )
        assert json.loads(result.stdout) is not None
