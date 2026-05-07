import json
import subprocess
import sys


def test_register_domain_kernel_cli_registers_workbench_metadata(tmp_path):
    db = tmp_path / "lawbook.sqlite"
    for preset in ("aot", "etp", "logikey"):
        result = subprocess.run(
            [sys.executable, "scripts/register_domain_kernel.py", "--db", str(db), "--preset", preset],
            check=True,
            text=True,
            capture_output=True,
        )
        payload = json.loads(result.stdout)
        assert payload["status"] == "registered"
        assert payload["extras"]["logical_workbenches"] >= 1

    for flag in ("--logical-workbenches", "--verifier-backends", "--faithfulness", "--benchmark-suites"):
        result = subprocess.run(
            [sys.executable, "scripts/query_lawbook.py", "--db", str(db), flag],
            check=True,
            text=True,
            capture_output=True,
        )
        assert json.loads(result.stdout) is not None
