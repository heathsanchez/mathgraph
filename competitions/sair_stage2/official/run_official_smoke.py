#!/usr/bin/env python
"""Run lightweight official Stage 2 smoke checks when available."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPO = ROOT / "official" / "equational-theories-lean-stage2"
DEFAULT_SOLVER = ROOT / "dist" / "solver.py"
JSON_PATH = ROOT / "artifacts" / "official_smoke_report.json"
MD_PATH = ROOT / "artifacts" / "OFFICIAL_SMOKE_REPORT.md"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=str(DEFAULT_REPO))
    parser.add_argument("--solver", default=str(DEFAULT_SOLVER))
    args = parser.parse_args(argv)
    report = run_smoke(Path(args.repo), Path(args.solver))
    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    MD_PATH.write_text(_md(report), encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] in {"completed", "partial", "skipped"} else 2


def run_smoke(repo: Path, solver: Path) -> dict:
    if not repo.exists():
        return {"status": "skipped", "reason": "official repo not found", "repo": str(repo)}
    checks = []
    if (repo / "pyproject.toml").exists() or list(repo.rglob("test*.py")):
        checks.append(_run_optional([sys.executable, "-m", "pytest", "-q"], repo, "pytest"))
    if (repo / "lakefile.lean").exists() or (repo / "lakefile.toml").exists():
        if shutil.which("lake"):
            checks.append(_run_optional(["lake", "env", "lean", "--version"], repo, "lake_env_lean_version"))
        else:
            checks.append({"name": "lake_env_lean_version", "status": "skipped", "reason": "lake not found"})
    solver_check = _run_solver_like_official(repo, solver)
    checks.append(solver_check)
    checks.append(_run_official_solo_protocol_simulation(solver))
    status = "completed" if all(item["status"] in {"passed", "skipped"} for item in checks) else "partial"
    return {"status": status, "repo": str(repo), "solver": str(solver), "checks": checks}


def _run_solver_like_official(repo: Path, solver: Path) -> dict:
    if not solver.exists():
        return {"name": "mathgraph_solver", "status": "failed", "reason": "solver.py not found"}
    candidates = []
    for path in repo.rglob("*"):
        if path.is_file() and path.suffix in {".py", ".md", ".txt"}:
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if "solver.py" in text:
                candidates.append(str(path.relative_to(repo)))
    result = _run_optional(
        [sys.executable, str(solver), "--equation1", "x = x * y", "--equation2", "x = x * (y * z)"],
        ROOT,
        "mathgraph_solver_cli_smoke",
    )
    result["official_evidence_files_mentioning_solver"] = candidates[:50]
    return result


def _run_official_solo_protocol_simulation(solver: Path) -> dict:
    startup = {
        "type": "start",
        "problem": {
            "id": "mathgraph_smoke_false",
            "eq1_id": 1,
            "eq2_id": 2,
            "equation1": "x = x",
            "equation2": "x * x = x",
        },
        "budget": {"timeout_seconds": 10, "max_code_length": 100000, "max_false_cert_bytes": 20000},
    }
    stdin = json.dumps(startup) + "\n{}\n"
    try:
        result = subprocess.run(
            [sys.executable, str(solver)],
            input=stdin,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception as exc:
        return {"name": "official_solo_protocol_simulation", "status": "failed", "reason": str(exc)}
    first = result.stdout.splitlines()[0] if result.stdout.splitlines() else ""
    try:
        msg = json.loads(first)
    except Exception:
        msg = {}
    ok = result.returncode == 0 and msg.get("call") == "judge" and msg.get("verdict") in {"true", "false"} and "code" in msg
    return {
        "name": "official_solo_protocol_simulation",
        "status": "passed" if ok else "failed",
        "returncode": result.returncode,
        "first_message": msg,
        "stderr_tail": result.stderr[-1000:],
    }


def _run_optional(cmd: list[str], cwd: Path, name: str) -> dict:
    try:
        result = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, timeout=60)
    except Exception as exc:
        return {"name": name, "status": "skipped", "reason": str(exc), "command": cmd}
    return {
        "name": name,
        "status": "passed" if result.returncode == 0 else "failed",
        "command": cmd,
        "returncode": result.returncode,
        "stdout_tail": result.stdout[-2000:],
        "stderr_tail": result.stderr[-2000:],
    }


def _md(report: dict) -> str:
    return "# Official Smoke Report\n\n```json\n%s\n```\n" % json.dumps(report, indent=2, sort_keys=True)


if __name__ == "__main__":
    raise SystemExit(main())
