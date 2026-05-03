"""Lightweight Lean adapter.

This adapter detects and runs local Lean only. It does not generate proofs,
create Lake projects, add Mathlib, or interpret failed Lean as mathematical
falsehood.
"""

from __future__ import annotations

import subprocess
import tempfile
import time
from pathlib import Path
from shutil import which
from typing import Any

from mathgraph.certificates import Certificate, named_obstruction


class LeanUnavailableError(RuntimeError):
    """Raised by callers that require Lean when it is not installed."""


class LeanVerificationError(RuntimeError):
    """Raised by callers that choose exception-based Lean verification."""


def _version(command_path: str | None) -> str | None:
    if command_path is None:
        return None
    try:
        result = subprocess.run(
            [command_path, "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    text = (result.stdout or result.stderr).strip()
    return text or None


def detect_lean() -> dict[str, str | bool | None]:
    lean_path = which("lean")
    lake_path = which("lake")
    return {
        "lean_path": lean_path,
        "lake_path": lake_path,
        "lean_available": lean_path is not None,
        "lake_available": lake_path is not None,
        "lean_version": _version(lean_path),
        "lake_version": _version(lake_path),
    }


def verify_lean_file(path: str | Path, timeout_sec: int = 30) -> dict[str, Any]:
    lean_info = detect_lean()
    file_path = Path(path)

    if not lean_info["lean_available"]:
        return {
            "status": "lean_unavailable",
            "path": str(file_path),
            "lean": lean_info,
            "stdout": "",
            "stderr": "Lean executable was not found on PATH.",
            "exit_code": None,
            "elapsed_sec": 0.0,
        }

    if not file_path.exists():
        return {
            "status": "lean_file_missing",
            "path": str(file_path),
            "lean": lean_info,
            "stdout": "",
            "stderr": "Lean file does not exist.",
            "exit_code": None,
            "elapsed_sec": 0.0,
        }

    started = time.monotonic()
    try:
        result = subprocess.run(
            [str(lean_info["lean_path"]), str(file_path)],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
        elapsed = time.monotonic() - started
        status = "lean_verified" if result.returncode == 0 else "lean_failed"
        return {
            "status": status,
            "path": str(file_path),
            "lean": lean_info,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
            "elapsed_sec": elapsed,
        }
    except subprocess.TimeoutExpired as exc:
        elapsed = time.monotonic() - started
        return {
            "status": "lean_failed",
            "path": str(file_path),
            "lean": lean_info,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or f"Lean timed out after {timeout_sec} seconds.",
            "exit_code": None,
            "elapsed_sec": elapsed,
        }


def verify_lean_code(code: str, timeout_sec: int = 30) -> dict[str, Any]:
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".lean", encoding="utf-8", delete=False) as handle:
            handle.write(code)
            temp_path = Path(handle.name)
        result = verify_lean_file(temp_path, timeout_sec=timeout_sec)
        result["code"] = code
        return result
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def unavailable(claim: str) -> Certificate:
    return named_obstruction(claim, "LEAN_ADAPTER_NOT_CONFIGURED")
