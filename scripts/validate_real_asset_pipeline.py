#!/usr/bin/env python
"""Validate the real-asset discovery and chewing smoke pipeline."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mathgraph.progress import ProgressLogger, stream_subprocess


COUNT_KEYS = [
    "primitive_count_before",
    "derived_count_before",
    "outcome_row_count_before",
    "frontier_count",
    "scheduled_count",
    "task_count",
    "finite_task_count",
    "finite_executor_verified_count",
    "imported_count",
    "primitive_count_after",
    "derived_count_after",
    "outcome_row_count_after",
    "oracle_probe_success_count",
]


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    run_id = _run_id()
    out_dir = Path(args.out_dir).resolve() if args.out_dir else repo_root / "artifacts" / "real_asset_validation" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    logs_dir = out_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    failed: list[dict[str, Any]] = []
    warnings: list[str] = []
    install_passed: bool | None = None
    pytest_passed: bool | None = None
    progress = ProgressLogger(
        "validate_real_asset_pipeline",
        args.progress_jsonl,
        args.heartbeat_sec,
        args.progress,
        args.quiet,
    )

    if (repo_root / ".git").exists():
        _run_stage("git_status", ["git", "status", "--short"], repo_root, logs_dir, failed, progress, args, allow_fail=True)

    if args.skip_install:
        install_passed = None
    else:
        install = _run_stage(
            "pip_install_editable",
            [sys.executable, "-m", "pip", "install", "-e", ".[dev]"],
            repo_root,
            logs_dir,
            failed,
            progress,
            args,
        )
        install_passed = install.returncode == 0

    if args.run_pytest:
        pytest = _run_stage(
            "pytest",
            [sys.executable, "-m", "pytest"],
            repo_root,
            logs_dir,
            failed,
            progress,
            args,
            allow_fail=True,
        )
        pytest_passed = pytest.returncode == 0
        if not pytest_passed:
            failed.append({"stage": "pytest", "returncode": pytest.returncode, "reason": "pytest failed"})

    discovery_dir = out_dir / "asset_discovery"
    discovery_cmd = [
        sys.executable,
        "scripts/discover_mathgraph_assets.py",
        "--out-dir",
        str(discovery_dir),
    ]
    _append_optional(discovery_cmd, "--traces-json", args.traces_json)
    _append_optional(discovery_cmd, "--equations-path", args.equations_path)
    _append_optional(discovery_cmd, "--matrix-path", args.matrix_path)
    discovery = _run_stage("asset_discovery", discovery_cmd, repo_root, logs_dir, failed, progress, args, allow_fail=True)
    asset_report_path = discovery_dir / "asset_discovery_report.json"
    asset_report = _read_json(asset_report_path)
    asset_discovery_ok = discovery.returncode == 0 and bool(asset_report)

    real_dir = out_dir / "real_chewing_smoke"
    real_cmd = [
        sys.executable,
        "scripts/run_real_chewing_smoke.py",
        "--out-dir",
        str(real_dir),
        "--max-frontier-pairs",
        str(args.max_frontier_pairs),
        "--top-k-schedule",
        str(args.top_k_schedule),
        "--max-tasks",
        str(args.max_tasks),
        "--max-countermodel-order",
        str(args.max_countermodel_order),
        "--random-tables-per-order",
        str(args.random_tables_per_order),
    ]
    _append_optional(real_cmd, "--traces-json", args.traces_json)
    _append_optional(real_cmd, "--equations-path", args.equations_path)
    _append_optional(real_cmd, "--matrix-path", args.matrix_path)
    real = _run_stage("real_chewing_smoke", real_cmd, repo_root, logs_dir, failed, progress, args, allow_fail=True)
    real_report_path = real_dir / "real_chewing_smoke_report.json"
    real_report = _read_json(real_report_path)
    real_summary = parse_smoke_summary(real_report)
    missing_assets = list(real_summary.get("missing_assets", []))
    real_assets_found = not missing_assets
    real_crashed = real.returncode != 0 and not real_report
    real_smoke_ok = bool(real_report) and not real_crashed

    fallback_report_path: Path | None = None
    fallback_smoke_ok: bool | None = None
    fallback_summary: dict[str, Any] = {}
    if missing_assets and args.allow_synthetic_fallback:
        fallback_dir = out_dir / "fallback_chewing_smoke"
        fallback_cmd = [
            sys.executable,
            "scripts/run_real_chewing_smoke.py",
            "--out-dir",
            str(fallback_dir),
            "--max-frontier-pairs",
            str(min(args.max_frontier_pairs, 50)),
            "--top-k-schedule",
            str(min(args.top_k_schedule, 20)),
            "--max-tasks",
            str(min(args.max_tasks, 20)),
            "--max-countermodel-order",
            str(args.max_countermodel_order),
            "--random-tables-per-order",
            str(args.random_tables_per_order),
            "--allow-synthetic-fallback",
        ]
        fallback = _run_stage("fallback_chewing_smoke", fallback_cmd, repo_root, logs_dir, failed, progress, args, allow_fail=True)
        fallback_report_path = fallback_dir / "real_chewing_smoke_report.json"
        fallback_report = _read_json(fallback_report_path)
        fallback_summary = parse_smoke_summary(fallback_report)
        fallback_smoke_ok = (
            fallback.returncode == 0
            and bool(fallback_report)
            and fallback_summary.get("synthetic_fallback_used") is True
            and fallback_summary.get("real_asset_mode") is False
        )
        if not fallback_smoke_ok:
            failed.append({"stage": "fallback_chewing_smoke", "reason": "fallback did not pass synthetic checks"})

    if not asset_discovery_ok:
        failed.append({"stage": "asset_discovery", "reason": "asset discovery did not produce a report"})
    if real_crashed:
        failed.append({"stage": "real_chewing_smoke", "reason": "real smoke crashed without a clean report"})
    if missing_assets and not args.allow_missing_assets:
        failed.append({"stage": "missing_assets", "reason": "assets missing and --allow-missing-assets not set"})
    if real_assets_found:
        if not real_report.get("ok"):
            failed.append({"stage": "real_chewing_smoke", "reason": "real assets present but smoke not ok"})
        if real_summary.get("real_asset_mode") is not True:
            failed.append({"stage": "real_asset_mode", "reason": "real assets present but real_asset_mode is not true"})
        if real_summary.get("synthetic_fallback_used") is not False:
            failed.append({"stage": "synthetic_fallback", "reason": "fallback used during real asset mode"})
    if fallback_summary.get("synthetic_fallback_used") and fallback_summary.get("real_asset_mode"):
        failed.append({"stage": "fallback_mode", "reason": "fallback reported as real asset mode"})

    counts = {key: real_summary.get(key) for key in COUNT_KEYS}
    synthetic_fallback_used = bool(real_summary.get("synthetic_fallback_used")) or bool(
        fallback_summary.get("synthetic_fallback_used")
    )
    summary = {
        "overall_ok": False,
        "run_id": run_id,
        "repo_root": str(repo_root),
        "out_dir": str(out_dir),
        "pytest_passed": pytest_passed,
        "install_passed": install_passed,
        "asset_discovery_ok": asset_discovery_ok,
        "real_assets_found": real_assets_found,
        "real_smoke_ok": real_smoke_ok,
        "fallback_smoke_ok": fallback_smoke_ok,
        "synthetic_fallback_used": synthetic_fallback_used,
        "missing_assets": missing_assets,
        "counts": counts,
        "paths": {
            "asset_discovery_report": str(asset_report_path) if asset_report_path.exists() else None,
            "real_smoke_report": str(real_report_path) if real_report_path.exists() else None,
            "fallback_smoke_report": str(fallback_report_path) if fallback_report_path and fallback_report_path.exists() else None,
            "validation_report_md": str(out_dir / "validation_report.md"),
            "validation_summary_json": str(out_dir / "validation_summary.json"),
        },
        "failed_stages": failed,
        "warnings": warnings,
    }
    required_ok = (
        (install_passed is not False)
        and (pytest_passed is not False)
        and asset_discovery_ok
        and real_smoke_ok
    )
    summary["overall_ok"] = required_ok and not failed
    _write_json(summary, out_dir / "validation_summary.json")
    _write_markdown(summary, asset_report, real_report, fallback_summary, out_dir / "validation_report.md")
    if not args.quiet:
        print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["overall_ok"] else 1


def parse_smoke_summary(report: dict[str, Any]) -> dict[str, Any]:
    if not report:
        return {}
    summary = dict(report.get("summary", {}))
    summary.setdefault("real_asset_mode", False)
    summary.setdefault("synthetic_fallback_used", False)
    summary.setdefault("missing_assets", [])
    return summary


def _run_stage(
    name: str,
    cmd: list[str],
    cwd: Path,
    logs_dir: Path,
    failed: list[dict[str, Any]],
    progress: ProgressLogger,
    args: argparse.Namespace,
    allow_fail: bool = False,
) -> subprocess.CompletedProcess[str]:
    if args.progress:
        result = stream_subprocess(
            cmd,
            cwd=cwd,
            log_path=logs_dir / f"{name}.stdout.txt",
            timeout_sec=args.timeout_sec,
            heartbeat_sec=args.heartbeat_sec,
            logger=progress,
            stage=name,
        )
        (logs_dir / f"{name}.stderr.txt").write_text("", encoding="utf-8")
        proc = subprocess.CompletedProcess(cmd, int(result["returncode"]), "", "")
        if proc.returncode != 0 and not allow_fail:
            failed.append({"stage": name, "returncode": proc.returncode, "reason": "subprocess failed"})
        return proc
    proc = subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True, check=False)
    (logs_dir / f"{name}.stdout.txt").write_text(proc.stdout, encoding="utf-8")
    (logs_dir / f"{name}.stderr.txt").write_text(proc.stderr, encoding="utf-8")
    if proc.returncode != 0 and not allow_fail:
        failed.append({"stage": name, "returncode": proc.returncode, "reason": "subprocess failed"})
    return proc


def _append_optional(cmd: list[str], flag: str, value: str | None) -> None:
    if value:
        cmd.extend([flag, value])


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_markdown(
    summary: dict[str, Any],
    asset_report: dict[str, Any],
    real_report: dict[str, Any],
    fallback_summary: dict[str, Any],
    path: Path,
) -> None:
    lines = [
        "# MathGraph Real Asset Pipeline Validation",
        "",
        f"- overall_ok: `{summary['overall_ok']}`",
        f"- pytest_passed: `{summary['pytest_passed']}`",
        f"- install_passed: `{summary['install_passed']}`",
        f"- asset_discovery_ok: `{summary['asset_discovery_ok']}`",
        f"- real_assets_found: `{summary['real_assets_found']}`",
        f"- real_smoke_ok: `{summary['real_smoke_ok']}`",
        f"- fallback_smoke_ok: `{summary['fallback_smoke_ok']}`",
        f"- synthetic_fallback_used: `{summary['synthetic_fallback_used']}`",
        f"- missing_assets: `{summary['missing_assets']}`",
        "",
        "## Counts",
        "",
        "```json",
        json.dumps(summary["counts"], indent=2, sort_keys=True),
        "```",
        "",
        "## Selected Assets",
        "",
        "```json",
        json.dumps(asset_report.get("selected", {}), indent=2, sort_keys=True),
        "```",
        "",
        "Scheduler output is search pressure only. Synthetic fallback is never real asset mode.",
    ]
    if real_report:
        lines.extend(["", "## Real Smoke Summary", "", "```json", json.dumps(real_report.get("summary", {}), indent=2, sort_keys=True), "```"])
    if fallback_summary:
        lines.extend(["", "## Fallback Smoke Summary", "", "```json", json.dumps(fallback_summary, indent=2, sort_keys=True), "```"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("run_%Y%m%d_%H%M%S_utc")


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--out-dir", default=None)
    parser.add_argument("--traces-json", default=None)
    parser.add_argument("--equations-path", default=None)
    parser.add_argument("--matrix-path", default=None)
    parser.add_argument("--run-pytest", action="store_true")
    parser.add_argument("--skip-install", action="store_true")
    parser.add_argument("--allow-missing-assets", action="store_true")
    parser.add_argument("--allow-synthetic-fallback", action="store_true")
    parser.add_argument("--max-frontier-pairs", type=int, default=250)
    parser.add_argument("--top-k-schedule", type=int, default=100)
    parser.add_argument("--max-tasks", type=int, default=100)
    parser.add_argument("--max-countermodel-order", type=int, default=3)
    parser.add_argument("--random-tables-per-order", type=int, default=100)
    parser.add_argument("--progress", action="store_true")
    parser.add_argument("--heartbeat-sec", type=float, default=10.0)
    parser.add_argument("--progress-jsonl", default=None)
    parser.add_argument("--timeout-sec", type=float, default=None)
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(main())
