#!/usr/bin/env python
"""Clone or update the official SAIR Stage 2 repository."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_URL = "https://github.com/SAIRcompetition/equational-theories-lean-stage2"
DEFAULT_CLONE = ROOT / "official" / "equational-theories-lean-stage2"
INFO_PATH = ROOT / "artifacts" / "official_stage2_repo_info.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-url", default=DEFAULT_URL)
    parser.add_argument("--clone-path", default=str(DEFAULT_CLONE))
    args = parser.parse_args(argv)
    info = clone_or_update(args.repo_url, Path(args.clone_path))
    INFO_PATH.parent.mkdir(parents=True, exist_ok=True)
    INFO_PATH.write_text(json.dumps(info, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(info, sort_keys=True))
    return 0 if info["status"] in {"cloned", "updated"} else 2


def clone_or_update(repo_url: str = DEFAULT_URL, clone_path: Path = DEFAULT_CLONE) -> dict:
    clone_path = Path(clone_path)
    if clone_path.exists() and not (clone_path / ".git").exists():
        shutil.rmtree(clone_path)
    if not clone_path.exists():
        _run(["git", "clone", repo_url, str(clone_path)], cwd=ROOT)
        status = "cloned"
    else:
        _run(["git", "fetch", "--all", "--prune"], cwd=clone_path)
        _run(["git", "pull", "--ff-only"], cwd=clone_path)
        status = "updated"
    commit = _run(["git", "rev-parse", "HEAD"], cwd=clone_path).strip()
    branch = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=clone_path).strip()
    porcelain = _run(["git", "status", "--short"], cwd=clone_path)
    return {
        "repo_url": repo_url,
        "clone_path": str(clone_path),
        "commit": commit,
        "branch": branch,
        "git_status": porcelain.strip(),
        "status": status,
    }


def _run(cmd: list[str], cwd: Path) -> str:
    result = subprocess.run(cmd, cwd=str(cwd), check=True, capture_output=True, text=True)
    return result.stdout


if __name__ == "__main__":
    raise SystemExit(main())

