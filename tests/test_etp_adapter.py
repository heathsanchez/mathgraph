import builtins
from pathlib import Path

import pytest

from adapters import etp_adapter

np = pytest.importorskip("numpy")


def test_load_equations_strips_blank_lines(tmp_path: Path) -> None:
    path = tmp_path / "equations.txt"
    path.write_text("x = x\n\n x * y = y * x \n", encoding="utf-8")

    assert etp_adapter.load_equations(path) == ["x = x", "x * y = y * x"]


def test_load_matrix_and_summarize_assets(tmp_path: Path) -> None:
    equations_path = tmp_path / "equations.txt"
    matrix_path = tmp_path / "matrix.npy"
    equations_path.write_text("e0\ne1\ne2\n", encoding="utf-8")
    np.save(matrix_path, np.array([[True, False, True], [False, False, True]]))

    matrix = etp_adapter.load_matrix(matrix_path)
    summary = etp_adapter.summarize_assets(equations_path, matrix_path)

    assert matrix.shape == (2, 3)
    assert summary["n_equations"] == 3
    assert summary["matrix_shape"] == (2, 3)
    assert summary["true_total"] == 3
    assert summary["false_total"] == 3
    assert summary["true_rate"] == 0.5
    assert len(summary["sha256"]["equations"]) == 64
    assert len(summary["sha256"]["matrix"]) == 64


def test_sample_false_pairs_is_seeded_and_bounded() -> None:
    matrix = np.array([[True, False], [False, True], [False, False]])

    pairs = etp_adapter.sample_false_pairs(matrix, limit=3, seed=7)

    assert len(pairs) == 3
    assert all(matrix[source, target] == np.False_ for source, target in pairs)
    assert pairs == etp_adapter.sample_false_pairs(matrix, limit=3, seed=7)


def test_sample_false_pairs_rejects_negative_limit() -> None:
    with pytest.raises(ValueError, match="limit"):
        etp_adapter.sample_false_pairs(np.array([[True]]), limit=-1)


def test_load_matrix_has_clear_numpy_import_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    path = tmp_path / "matrix.npy"
    path.write_bytes(b"not used")
    original_import = builtins.__import__

    def fake_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "numpy":
            raise ImportError("blocked for test")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(ImportError, match="requires numpy"):
        etp_adapter.load_matrix(path)
