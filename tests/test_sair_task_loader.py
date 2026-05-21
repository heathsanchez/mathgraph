from pathlib import Path

import pytest

from mathgraph.sair_task_loader import (
    SAIRTaskLoadConfig,
    load_sair_equations,
    load_sair_matrix,
    make_sair_eval_sample,
    make_sair_false_tasks,
    normalize_sair_equation,
)


def test_equation_normalization():
    assert normalize_sair_equation("x = x ◇ y") == "x = x * y"


def test_small_equations_load(tmp_path):
    path = tmp_path / "equations.txt"
    path.write_text("x = x\nx = x ◇ y\nbad line\n", encoding="utf-8")
    assert load_sair_equations(path) == ["x = x", "x = x * y"]


def test_small_bool_matrix_load_and_false_tasks(tmp_path):
    np = pytest.importorskip("numpy")
    matrix_path = tmp_path / "m.npy"
    np.save(matrix_path, np.array([[1, 0], [1, 1]], dtype=bool))
    matrix = load_sair_matrix(matrix_path)
    tasks = make_sair_false_tasks(["x = x", "x = y"], matrix, max_tasks=10, random_seed=1)
    assert len(tasks) == 1
    assert tasks[0].eq1_id == 0
    assert tasks[0].eq2_id == 1
    assert tasks[0].expected_matrix_label is False


def test_sampling_deterministic(tmp_path):
    np = pytest.importorskip("numpy")
    matrix_path = tmp_path / "m.npy"
    np.save(matrix_path, np.zeros((4, 4), dtype=bool))
    matrix = load_sair_matrix(matrix_path)
    equations = ["x = x", "x = y", "x = x * y", "x = y * x"]
    a = [task.to_dict() for task in make_sair_false_tasks(equations, matrix, max_tasks=5, random_seed=7)]
    b = [task.to_dict() for task in make_sair_false_tasks(equations, matrix, max_tasks=5, random_seed=7)]
    assert a == b


def test_missing_files_fallback_safe(tmp_path):
    assert load_sair_equations(tmp_path / "missing.txt") == []
    assert load_sair_matrix(tmp_path / "missing.npy") is None
    tasks = make_sair_eval_sample(SAIRTaskLoadConfig(equations_path=tmp_path / "missing.txt", matrix_path=tmp_path / "missing.npy"))
    assert tasks == []
