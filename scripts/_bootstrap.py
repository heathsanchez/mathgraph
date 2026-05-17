"""Small shared import-path bootstrap for repo-local CLI scripts."""
from __future__ import annotations

import sys
from pathlib import Path


def repo_root_from_file(file: str | Path) -> Path:
    """Return the repository root for a file living under `scripts/`."""
    return Path(file).resolve().parent.parent


def ensure_repo_root_on_path(file: str | Path) -> Path:
    """Place the repository root first on `sys.path` and return it."""
    root = repo_root_from_file(file)
    text = str(root)
    if text in sys.path:
        sys.path.remove(text)
    sys.path.insert(0, text)
    return root
