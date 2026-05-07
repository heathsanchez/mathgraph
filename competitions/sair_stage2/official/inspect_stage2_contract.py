#!/usr/bin/env python
"""Inspect the official SAIR Stage 2 repository contract."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPO = ROOT / "official" / "equational-theories-lean-stage2"
JSON_PATH = ROOT / "artifacts" / "official_stage2_contract.json"
MD_PATH = ROOT / "artifacts" / "OFFICIAL_STAGE2_CONTRACT.md"

REQUIRED_KEYS = [
    "readme_instructions",
    "submission_file_names",
    "expected_solver_location",
    "allowed_imports",
    "size_limit_bytes",
    "invocation_commands",
    "input_format",
    "output_format",
    "lean_version_or_lake_setup",
    "test_commands",
    "example_problems",
    "scoring_or_evaluation_scripts",
    "pyproject_pytest_ci_files",
    "hidden_assumptions",
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=str(DEFAULT_REPO))
    args = parser.parse_args(argv)
    report = inspect_contract(Path(args.repo))
    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    MD_PATH.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0


def inspect_contract(repo: str | Path) -> dict:
    repo = Path(repo)
    texts = _read_text_files(repo)
    contract_texts = [(path, text) for path, text in texts if _is_contract_source(path)]
    files = [str(path.relative_to(repo)) for path in repo.rglob("*") if path.is_file() and ".git" not in path.parts]
    all_text = "\n".join(text for _, text in contract_texts)
    readmes = [{"path": path, "excerpt": text[:4000]} for path, text in contract_texts if Path(path).name.lower().startswith("readme")]
    contract = {
        "repo_path": str(repo),
        "repo_exists": repo.exists(),
        "official_summary": _official_summary(all_text),
        "readme_instructions": _field(readmes, "README files found" if readmes else "No README found"),
        "submission_file_names": _detect_submission_files(files, all_text),
        "expected_solver_location": _detect_solver_location(files, all_text),
        "allowed_imports": _detect_allowed_imports(all_text),
        "size_limit_bytes": _detect_size_limit(all_text),
        "invocation_commands": _detect_commands(all_text),
        "input_format": _detect_format(all_text, "input"),
        "output_format": _detect_format(all_text, "output"),
        "lean_version_or_lake_setup": _detect_lake(files, all_text),
        "test_commands": _detect_test_commands(files, all_text),
        "example_problems": _detect_examples(files, all_text),
        "scoring_or_evaluation_scripts": _detect_scoring(files),
        "pyproject_pytest_ci_files": [f for f in files if f in {"pyproject.toml", "pytest.ini"} or f.startswith(".github/")],
        "hidden_assumptions": _detect_hidden_assumptions(files, all_text),
        "evidence_files": files[:200],
        "contract_source_files": [path for path, _ in contract_texts],
    }
    for key in REQUIRED_KEYS:
        contract.setdefault(key, _unknown("not inspected"))
    return contract


def render_markdown(report: dict) -> str:
    lines = ["# Official SAIR Stage 2 Contract", ""]
    for key in REQUIRED_KEYS:
        lines.append(f"## {key}")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(report.get(key), indent=2, sort_keys=True))
        lines.append("```")
        lines.append("")
    return "\n".join(lines)


def _read_text_files(repo: Path) -> list[tuple[str, str]]:
    if not repo.exists():
        return []
    wanted = {".md", ".txt", ".py", ".toml", ".yml", ".yaml", ".lean", ".json"}
    out = []
    for path in repo.rglob("*"):
        if not path.is_file() or ".git" in path.parts or path.suffix.lower() not in wanted:
            continue
        try:
            out.append((str(path.relative_to(repo)), path.read_text(encoding="utf-8", errors="replace")))
        except OSError:
            pass
    return out


def _is_contract_source(path: str) -> bool:
    name = Path(path).name.lower()
    return (
        name.startswith("readme")
        or path.startswith("docs/")
        or path.startswith("rules/")
        or path in {"pipeline/config.json", "pipeline/proxy.py", "pipeline/runner.py", "pipeline/marathon_runner.py"}
        or path.startswith("examples/solo/")
        or path.startswith("examples/marathon/")
        or path.startswith("scripts/")
    )


def _field(value, evidence):
    return {"status": "found", "value": value, "evidence": evidence} if value else _unknown(evidence)


def _unknown(evidence):
    return {"status": "unknown", "value": None, "evidence": evidence}


def _detect_submission_files(files, text):
    hits = sorted({f for f in files if Path(f).name in {"solver.py", "submission.py", "Solution.lean"}})
    for name in re.findall(r"[\w./-]*(?:solver|submission)[\w./-]*\.py", text, flags=re.I):
        hits.append(name)
    return _field(sorted(set(hits)), "solver/submission filename mentions")


def _detect_solver_location(files, text):
    patterns = re.findall(r"[\w./-]*solver\.py", text, flags=re.I)
    hits = sorted(set([f for f in files if f.endswith("solver.py")] + patterns))
    return _field(hits, "solver.py path mentions")


def _detect_allowed_imports(text):
    lines = [line.strip() for line in text.splitlines() if "import" in line.lower() and ("allow" in line.lower() or "forbid" in line.lower() or "stdlib" in line.lower())]
    return _field(lines, "import policy lines")


def _detect_size_limit(text):
    matches = re.findall(r"(\d+(?:\.\d+)?)\s*(KB|KiB|MB|MiB|bytes?)", text, flags=re.I)
    values = []
    for number, unit in matches:
        n = float(number)
        u = unit.lower()
        if u.startswith("k"):
            values.append(int(n * 1000))
        elif u.startswith("m"):
            values.append(int(n * 1000 * 1000))
        else:
            values.append(int(n))
    return _field(values, "size limit numeric mentions")


def _detect_commands(text):
    commands = []
    for line in text.splitlines():
        stripped = line.strip().strip("`")
        if stripped.startswith(("python ", "pytest", "lake ", "./")) or "solver.py" in stripped:
            commands.append(stripped)
    return _field(commands[:80], "command-like README/code lines")


def _detect_format(text, label):
    lines = [line.strip() for line in text.splitlines() if label in line.lower() and any(word in line.lower() for word in ("format", "json", "stdin", "stdout", "return", "print"))]
    return _field(lines[:80], f"{label} format lines")


def _detect_lake(files, text):
    hits = [f for f in files if Path(f).name in {"lakefile.lean", "lakefile.toml", "lean-toolchain", "lake-manifest.json"}]
    lines = [line.strip() for line in text.splitlines() if "lean" in line.lower() or "lake" in line.lower()]
    return _field({"files": hits, "mentions": lines[:80]}, "Lean/Lake files and mentions")


def _detect_test_commands(files, text):
    commands = [line.strip().strip("`") for line in text.splitlines() if any(tok in line for tok in ("pytest", "unittest", "lake test", "python -m"))]
    files_hit = [f for f in files if "test" in f.lower() or "eval" in f.lower()]
    return _field({"commands": commands[:80], "files": files_hit[:120]}, "tests/evaluation files and commands")


def _detect_examples(files, text):
    files_hit = [f for f in files if "example" in f.lower() or "sample" in f.lower()]
    lines = [line.strip() for line in text.splitlines() if "example" in line.lower() or "sample" in line.lower()]
    return _field({"files": files_hit[:120], "mentions": lines[:80]}, "example/sample mentions")


def _detect_scoring(files):
    hits = [f for f in files if any(word in f.lower() for word in ("score", "eval", "grade", "judge", "validate", "test"))]
    return _field(hits[:200], "scoring/evaluation-like filenames")


def _detect_hidden_assumptions(files, text):
    lines = [line.strip() for line in text.splitlines() if any(word in line.lower() for word in ("must", "required", "assume", "timeout", "limit", "offline", "internet", "network"))]
    return _field(lines[:120], "requirement/assumption language")


def _official_summary(text: str) -> dict:
    lower = text.lower()
    return {
        "submission": "single solver.py file" if "single `solver.py`" in lower or "single python file" in lower else "unknown",
        "solver_size_limit_bytes": 500000 if "500 kb" in lower or "500kb" in lower else None,
        "solo_invocation": "one solver subprocess per problem; stdin start JSON; stdout judge/llm JSON requests",
        "solo_start_message": {
            "type": "start",
            "problem_keys": ["id", "eq1_id", "eq2_id", "equation1", "equation2"],
            "budget_keys": ["timeout_seconds", "max_code_length", "max_false_cert_bytes"],
        },
        "solver_to_proxy_calls": ["judge", "llm"],
        "judge_answer_format": {"call": "judge", "verdict": "true|false", "code": "<full Lean source>"},
        "accepted_status": "accepted",
        "marathon_invocation": "env-var/file protocol via JUDGE_MARATHON_MANIFEST and JUDGE_MARATHON_OUTPUT" if "judge_marathon_manifest" in lower else "unknown",
        "mathgraph_conformance": "partial: standalone solver.py, size compliant, solo protocol can emit false Lean judge calls; TRUE Lean proof rendering remains future",
    }


if __name__ == "__main__":
    raise SystemExit(main())
