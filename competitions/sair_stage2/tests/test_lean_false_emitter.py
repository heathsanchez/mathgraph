import json
import subprocess
import sys

from competitions.sair_stage2.src.lean_false_emitter import (
    build_false_certificate,
    emit_false_judge_call,
)
from competitions.sair_stage2.src.lean_templates import render_false_countermodel_lean


def test_build_false_certificate_requires_python_verified_countermodel():
    cert = build_false_certificate(
        1,
        2,
        "x = x",
        "x * x = x",
        [[0, 0], [0, 0]],
    )
    assert cert is not None
    assert cert.source_holds_verified_python
    assert cert.target_fails_verified_python
    assert cert.witness == {"x": 1}


def test_bad_table_does_not_create_certificate():
    cert = build_false_certificate(
        1,
        2,
        "x = x * y",
        "x * y = y",
        [[0, 1], [0, 1]],
    )
    assert cert is None


def test_render_false_countermodel_lean_contains_official_shape():
    cert = build_false_certificate(1, 2, "x = x", "x * x = x", [[0, 0], [0, 0]])
    code = render_false_countermodel_lean(cert)
    assert code
    assert "import JudgeProblem" in code
    assert "def submission : Goal := by" in code
    assert "let candidateMagma : Magma (Fin 2)" in code
    assert "refine ⟨Fin 2, candidateMagma, ?_⟩" in code
    assert "decideFin!" in code
    assert "finOpTable" in code


def test_render_false_countermodel_lean_has_no_extra_top_level_magma_def():
    cert = build_false_certificate(1, 2, "x = x", "x * x = x", [[0, 0], [0, 0]])
    code = render_false_countermodel_lean(cert)
    assert "def mg_false" not in code
    assert "mg_false_" not in code
    assert "let candidateMagma" in code


def test_emit_false_judge_call_exact_keys():
    cert = build_false_certificate(1, 2, "x = x", "x * x = x", [[0, 0], [0, 0]])
    call = emit_false_judge_call(cert)
    assert set(call) == {"call", "verdict", "code"}
    assert call["call"] == "judge"
    assert call["verdict"] == "false"


def test_invalid_or_empty_certificates_do_not_emit_judge_calls():
    assert build_false_certificate(1, 2, "x = x", "x = x", []) is None
    assert build_false_certificate(1, 2, "x = x", "x = x", [[0]]) is None
    assert build_false_certificate(1, 2, "x = x", "x = x", [[0, 0]]) is None
    assert emit_false_judge_call({"carrier_size": 0, "table": [], "violating_assignment": {}}) is None
    assert emit_false_judge_call({"carrier_size": 1, "table": [[0]], "violating_assignment": {"x": 0}}) is None


def test_emitted_false_lean_uses_nontrivial_fin_carrier():
    cert = build_false_certificate(1, 2, "x = x", "x * x = x", [[0, 0], [0, 0]])
    code = emit_false_judge_call(cert)["code"]
    assert "Fin 0" not in code
    assert "Fin 1" not in code
    assert "Fin 2" in code


def test_solver_official_solo_emits_valid_json_for_false_case(tmp_path):
    solver = tmp_path / "solver.py"
    subprocess.run(
        [sys.executable, "competitions/sair_stage2/scripts/build_solver.py", "--out", str(solver)],
        check=True,
    )
    startup = {
        "type": "start",
        "problem": {
            "id": "p",
            "eq1_id": 1,
            "eq2_id": 2,
            "equation1": "x = x",
            "equation2": "x * x = x",
        },
        "budget": {},
    }
    proc = subprocess.run(
        [sys.executable, str(solver)],
        input=json.dumps(startup) + "\n{}\n",
        text=True,
        capture_output=True,
        timeout=10,
        check=True,
    )
    msg = json.loads(proc.stdout.splitlines()[0])
    assert set(msg) == {"call", "verdict", "code"}
    assert msg["verdict"] == "false"
    assert "def submission" in msg["code"]
    assert "let candidateMagma" in msg["code"]
    assert "mg_false_" not in msg["code"]
