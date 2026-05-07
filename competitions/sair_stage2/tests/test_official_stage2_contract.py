import importlib
import json
import subprocess
import sys

from competitions.sair_stage2.official.inspect_stage2_contract import REQUIRED_KEYS, inspect_contract


def test_clone_script_can_be_imported():
    mod = importlib.import_module("competitions.sair_stage2.official.clone_stage2_repo")
    assert mod.DEFAULT_URL == "https://github.com/SAIRcompetition/equational-theories-lean-stage2"


def test_contract_inspector_on_fake_repo(tmp_path):
    repo = tmp_path / "official"
    repo.mkdir()
    (repo / "README.md").write_text(
        """
# Stage 2
Submit solver.py under 500KB.
Run: python solver.py --equation1 "x=x" --equation2 "x=x"
Input format is CLI equations. Output format is stdout verdict.
Use lake test for Lean checks.
""",
        encoding="utf-8",
    )
    (repo / "solver.py").write_text("# example\n", encoding="utf-8")
    (repo / "lakefile.lean").write_text("-- lake\n", encoding="utf-8")
    report = inspect_contract(repo)
    for key in REQUIRED_KEYS:
        assert key in report
    assert "solver.py" in json.dumps(report["submission_file_names"])
    assert report["size_limit_bytes"]["value"]


def test_build_solver_without_contract(tmp_path):
    out = tmp_path / "solver.py"
    result = subprocess.run(
        [
            sys.executable,
            "competitions/sair_stage2/scripts/build_solver.py",
            "--contract",
            str(tmp_path / "missing_contract.json"),
            "--out",
            str(out),
            "--max-bytes",
            "500000",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["official_contract"]["status"] == "absent"
    assert out.exists()


def test_built_solver_exposes_official_compatible_api(tmp_path):
    out = tmp_path / "solver.py"
    subprocess.run(
        [sys.executable, "competitions/sair_stage2/scripts/build_solver.py", "--out", str(out)],
        check=True,
    )
    result = subprocess.run(
        [sys.executable, str(out), "--equation1", "x = x", "--equation2", "y = y"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(result.stdout)["verdict"] == "TRUE"
    startup = {
        "type": "start",
        "problem": {"id": "p", "eq1_id": 1, "eq2_id": 2, "equation1": "x = x", "equation2": "x * x = x"},
        "budget": {},
    }
    official = subprocess.run(
        [sys.executable, str(out)],
        input=json.dumps(startup) + "\n{}\n",
        check=True,
        capture_output=True,
        text=True,
    )
    first = json.loads(official.stdout.splitlines()[0])
    assert first["call"] == "judge"
    assert first["verdict"] == "false"
    assert "import JudgeProblem" in first["code"]
