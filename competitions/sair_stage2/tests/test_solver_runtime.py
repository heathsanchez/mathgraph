import json
import os
import subprocess
import sys

from competitions.sair_stage2.src.solver_runtime import solve, solve_problem


def test_solver_true_false_unknown():
    assert solve("x * y = x", "a * b = a")["verdict"] == "TRUE"
    false = solve("x = x", "x * x = x")
    assert false["verdict"] == "FALSE"
    assert false["terminal_form"] == "FINITE_COUNTERMODEL"
    unknown = solve("(x * y) * z = x * (y * z)", "x * y = y * x")
    assert unknown["verdict"] in {"FALSE", "UNKNOWN"}
    assert solve_problem({"equation1": "x = x", "equation2": "y = y"})["verdict"] == "TRUE"


def test_known_unsound_pairs_are_not_predicted_true():
    bad_pairs = [
        (4100, 3274, "x * x = ((y * z) * x) * y", "x * x = y * (x * (z * y))"),
        (1285, 2300, "x = y * (((x * y) * x) * y)", "x = (y * (x * (y * x))) * y"),
        (103, 204, "x = x * ((y * x) * x)", "x = (x * (x * y)) * x"),
    ]
    for eq1_id, eq2_id, source, target in bad_pairs:
        assert solve(source, target, eq1_id, eq2_id)["verdict"] != "TRUE"


def test_marathon_mode_writes_only_certified_false_answers(tmp_path):
    manifest = tmp_path / "manifest.jsonl"
    output = tmp_path / "answers.jsonl"
    rows = [
        {"id": "false_case", "eq1_id": 1, "eq2_id": 2, "equation1": "x = x", "equation2": "x * x = x"},
        {"id": "unknown_case", "eq1_id": 3, "eq2_id": 4, "equation1": "(x * y) * z = x * (y * z)", "equation2": "x * y = y * x"},
    ]
    manifest.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    env = dict(os.environ)
    env["JUDGE_MARATHON_MANIFEST"] = str(manifest)
    env["JUDGE_MARATHON_OUTPUT"] = str(output)
    proc = subprocess.run([sys.executable, "competitions/sair_stage2/dist/solver.py"], env=env, text=True, capture_output=True, timeout=10)
    assert proc.returncode == 0
    answers = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert answers
    assert answers[0]["id"] == "false_case"
    assert answers[0]["verdict"] == "false"
    assert "def submission" in answers[0]["code"]
