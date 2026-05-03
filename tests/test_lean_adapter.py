from pathlib import Path

from adapters import lean_adapter
from mathgraph import TerminalForm


EXPECTED_DETECT_KEYS = {
    "lean_path",
    "lake_path",
    "lean_available",
    "lake_available",
    "lean_version",
    "lake_version",
}


def test_detect_lean_returns_expected_keys() -> None:
    result = lean_adapter.detect_lean()

    assert set(result) == EXPECTED_DETECT_KEYS
    assert isinstance(result["lean_available"], bool)
    assert isinstance(result["lake_available"], bool)


def test_verify_lean_file_missing_returns_status(tmp_path: Path) -> None:
    result = lean_adapter.verify_lean_file(tmp_path / "missing.lean")

    assert result["status"] in {"lean_file_missing", "lean_unavailable"}
    assert result["exit_code"] is None


def test_verify_lean_code_handles_unavailable_gracefully(monkeypatch) -> None:
    monkeypatch.setattr(
        lean_adapter,
        "detect_lean",
        lambda: {
            "lean_path": None,
            "lake_path": None,
            "lean_available": False,
            "lake_available": False,
            "lean_version": None,
            "lake_version": None,
        },
    )

    result = lean_adapter.verify_lean_code("theorem t : True := True.intro")

    assert result["status"] == "lean_unavailable"
    assert result["exit_code"] is None


def test_verify_lean_code_success_when_available() -> None:
    if not lean_adapter.detect_lean()["lean_available"]:
        return

    result = lean_adapter.verify_lean_code("theorem t : True := True.intro")

    assert result["status"] == "lean_verified"
    assert result["exit_code"] == 0


def test_verify_lean_code_failure_when_available_is_not_proof() -> None:
    if not lean_adapter.detect_lean()["lean_available"]:
        return

    result = lean_adapter.verify_lean_code("theorem bad : False := by trivial")

    assert result["status"] == "lean_failed"
    assert result["status"] != TerminalForm.VERIFIED_PROOF.value
