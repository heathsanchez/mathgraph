#!/usr/bin/env python
"""Run a robust synthetic finite-countermodel vision smoke."""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from _bootstrap import ensure_repo_root_on_path
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
else:
    ensure_repo_root_on_path(__file__)

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

from mathgraph import (  # noqa: E402
    CountermodelImportConfig,
    FiniteCountermodelConfig,
    HTiltScheduler,
    KernelOracle,
    LawbookStore,
    SchedulerInputPair,
    TaskQueueConfig,
    build_task_queue,
    import_finite_countermodel_results,
    run_finite_countermodel_tasks,
)


SYNTHETIC_PAIRS = [
    {
        "source": "x = x ◇ y",
        "target": "x = y ◇ x",
        "source_idx": 0,
        "target_idx": 1,
        "label": "synthetic_false_left_projection",
        "metadata": {"candidate_origin": "vision_smoke_synthetic"},
    },
    {
        "source": "x = y ◇ x",
        "target": "x = x ◇ y",
        "source_idx": 1,
        "target_idx": 0,
        "label": "synthetic_false_right_projection",
        "metadata": {"candidate_origin": "vision_smoke_synthetic"},
    },
    {
        "source": "(x ◇ y) ◇ z = x ◇ (y ◇ z)",
        "target": "x ◇ y = y ◇ x",
        "source_idx": 2,
        "target_idx": 3,
        "label": "synthetic_false_associative_noncommutative",
        "metadata": {"candidate_origin": "vision_smoke_synthetic"},
    },
]


def run_vision_smoke(out_dir: str | Path, max_order: int = 3, max_tasks: int = 10) -> dict[str, Any]:
    started = time.perf_counter()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths = _paths(out)

    store = LawbookStore(paths["lawbook"])
    try:
        store.init_schema()
        scheduler = HTiltScheduler(oracle=KernelOracle(store))
        schedule = scheduler.schedule([SchedulerInputPair.from_dict(row) for row in SYNTHETIC_PAIRS], top_k=len(SYNTHETIC_PAIRS))
        scheduler.save_tasks_jsonl(paths["schedule"], schedule)
        schedule_summary = scheduler.stats(schedule).to_dict()
        _write_json(schedule_summary, paths["schedule_summary"])
    finally:
        store.close()

    queue_result = build_task_queue(
        TaskQueueConfig(
            schedule_jsonl=str(paths["schedule"]),
            out_jsonl=str(paths["task_queue"]),
            max_tasks=max_tasks,
        )
    )
    queue_rows = _read_jsonl(paths["task_queue"])
    initial_distribution = _task_distribution(queue_rows)
    fallback_used = False
    if initial_distribution["by_task_kind"].get("finite_countermodel_search", 0) == 0:
        fallback_used = True
        queue_rows = fallback_finite_countermodel_tasks()
        _write_jsonl(queue_rows, paths["task_queue"])
        queue_summary = _queue_summary(queue_rows, skipped=0, fallback_used=True)
        _write_json(queue_summary, paths["task_queue_summary"])
    else:
        queue_summary = dict(queue_result.summary)
        queue_summary["fallback_used"] = False

    finite_run = run_finite_countermodel_tasks(
        FiniteCountermodelConfig(
            task_queue_jsonl=str(paths["task_queue"]),
            out_jsonl=str(paths["finite_results"]),
            max_tasks=max_tasks,
            max_order=max_order,
            exhaustive_order_limit=min(max_order, 3),
            random_tables_per_order=0,
            include_deterministic_tables=True,
            stop_after_first=True,
        )
    )
    import_run = import_finite_countermodel_results(
        CountermodelImportConfig(
            results_jsonl=str(paths["finite_results"]),
            store_path=str(paths["lawbook"]),
            out_json=str(paths["import_summary"]),
            revalidate=True,
            allow_duplicate_certificates=False,
        )
    )
    oracle_probe = _oracle_probe(paths["lawbook"], import_run.to_dict()["results"])
    _write_json(oracle_probe, paths["oracle_probe"])

    promoted_rows = [row for row in import_run.to_dict()["results"] if row.get("imported")]
    promoted_are_finite = all(
        row.get("terminal_form") == "FINITE_COUNTERMODEL"
        and row.get("verification_status") in {"REFUTED", "FINITE_VERIFIED"}
        for row in promoted_rows
    )
    summary = {
        "schedule_count": len(schedule),
        "task_queue_count": len(queue_rows),
        "fallback_used": fallback_used,
        "initial_task_distribution": initial_distribution,
        "task_distribution": _task_distribution(queue_rows),
        "finite_executor_verified_count": int(finite_run.summary.get("found_count", 0)),
        "finite_executor_skipped_count": int(finite_run.summary.get("skipped_count", 0)),
        "imported_count": int(import_run.summary.get("imported_count", 0)),
        "duplicate_count": int(import_run.summary.get("duplicate_count", 0)),
        "oracle_probe_count": oracle_probe["summary"]["oracle_probe_count"],
        "oracle_probe_success_count": oracle_probe["summary"]["oracle_probe_success_count"],
        "promoted_rows_are_finite_countermodels": promoted_are_finite,
        "elapsed_sec": time.perf_counter() - started,
    }
    ok = (
        summary["schedule_count"] > 0
        and summary["task_queue_count"] > 0
        and summary["finite_executor_verified_count"] >= 1
        and summary["imported_count"] >= 1
        and summary["oracle_probe_success_count"] >= 1
        and promoted_are_finite
    )
    report = {
        "ok": ok,
        "summary": summary,
        "paths": {key: str(value) for key, value in paths.items()},
        "warnings": [
            "Scheduler output is search pressure only.",
            "Obstruction analysis is not proof or refutation.",
            "Finite search failure is obstruction evidence only.",
            "Only verified finite countermodel rows are importable/promotable.",
        ],
    }
    _write_json(report, paths["report_json"])
    _write_report_md(report, paths["report_md"])
    return report


def fallback_finite_countermodel_tasks() -> list[dict[str, Any]]:
    tasks = []
    for rank, row in enumerate(SYNTHETIC_PAIRS, start=1):
        tasks.append(
            {
                "task_id": f"vision_finite_{rank}",
                "source": row["source"],
                "target": row["target"],
                "source_idx": row["source_idx"],
                "target_idx": row["target_idx"],
                "route": "finite_countermodel",
                "task_kind": "finite_countermodel_search",
                "terminal_goal": "FINITE_COUNTERMODEL",
                "priority": 1.0 / rank,
                "schedule_rank": rank,
                "candidate_origin": "vision_smoke_fallback",
                "label": row["label"],
                "required_inputs": ["source equation", "target equation", "finite magma table family"],
                "steps": [
                    "Parse source and target equations.",
                    "Search only tables satisfying source.",
                    "Check whether target is violated.",
                    "Emit finite countermodel certificate if found.",
                ],
                "success_criteria": [
                    "A finite table satisfies the source for all assignments.",
                    "The same table violates the target on a recorded witness.",
                ],
                "failure_modes": [
                    "Finite search failure is obstruction evidence only, not proof.",
                ],
                "evidence": {
                    "fallback_reason": "scheduled task queue contained zero finite_countermodel_search tasks",
                    "original_pair": row,
                },
                "warnings": [
                    "This task is not a proof or refutation until verified.",
                    "Do not promote without a verified proof or finite countermodel.",
                    "Finite search failure is obstruction evidence only.",
                ],
            }
        )
    return tasks


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--max-order", type=int, default=3)
    parser.add_argument("--max-tasks", type=int, default=10)
    args = parser.parse_args(argv)

    report = run_vision_smoke(args.out_dir, max_order=args.max_order, max_tasks=args.max_tasks)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


def _oracle_probe(store_path: Path, import_results: list[dict[str, Any]]) -> dict[str, Any]:
    store = LawbookStore(store_path)
    probes = []
    success = 0
    try:
        oracle = KernelOracle(store)
        for row in [item for item in import_results if item.get("imported")][:5]:
            answer = oracle.query(str(row.get("source", "")), str(row.get("target", "")))
            answer_dict = answer.to_dict()
            ok = answer.status == "REFUTED" and answer.terminal_form == "FINITE_COUNTERMODEL"
            success += int(ok)
            probes.append(
                {
                    "source": row.get("source"),
                    "target": row.get("target"),
                    "ok": ok,
                    "oracle_answer": answer_dict,
                }
            )
    finally:
        store.close()
    return {
        "summary": {
            "oracle_probe_count": len(probes),
            "oracle_probe_success_count": success,
        },
        "probes": probes,
    }


def _task_distribution(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    return {
        "by_task_kind": dict(Counter(str(row.get("task_kind")) for row in rows)),
        "by_route": dict(Counter(str(row.get("route")) for row in rows)),
    }


def _queue_summary(rows: list[dict[str, Any]], skipped: int, fallback_used: bool) -> dict[str, Any]:
    priorities = [float(row.get("priority", 0.0)) for row in rows]
    return {
        "task_count": len(rows),
        "skipped_count": skipped,
        "by_task_kind": _task_distribution(rows)["by_task_kind"],
        "by_route": _task_distribution(rows)["by_route"],
        "by_terminal_goal": dict(Counter(str(row.get("terminal_goal")) for row in rows)),
        "priority_min": min(priorities, default=0.0),
        "priority_max": max(priorities, default=0.0),
        "priority_mean": sum(priorities) / len(priorities) if priorities else 0.0,
        "fallback_used": fallback_used,
        "warnings": [
            "Fallback tasks are synthetic finite-countermodel checks, not proof or refutation until verified.",
        ],
    }


def _paths(out_dir: Path) -> dict[str, Path]:
    return {
        "lawbook": out_dir / "lawbook.sqlite",
        "schedule": out_dir / "schedule.jsonl",
        "schedule_summary": out_dir / "schedule_summary.json",
        "task_queue": out_dir / "task_queue.jsonl",
        "task_queue_summary": out_dir / "task_queue_summary.json",
        "finite_results": out_dir / "finite_results.jsonl",
        "import_summary": out_dir / "countermodel_import_summary.json",
        "oracle_probe": out_dir / "oracle_probe.json",
        "report_json": out_dir / "vision_smoke_report.json",
        "report_md": out_dir / "vision_smoke_report.md",
    }


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _write_json(payload: Any, path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_jsonl(rows: list[dict[str, Any]], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def _write_report_md(report: dict[str, Any], path: str | Path) -> None:
    summary = report["summary"]
    lines = [
        "# MathGraph Vision Smoke Report",
        "",
        f"- ok: {report['ok']}",
        f"- scheduled candidates: {summary['schedule_count']}",
        f"- task queue rows: {summary['task_queue_count']}",
        f"- fallback used: {summary['fallback_used']}",
        f"- finite countermodels verified: {summary['finite_executor_verified_count']}",
        f"- imported countermodels: {summary['imported_count']}",
        f"- oracle probe success: {summary['oracle_probe_success_count']} / {summary['oracle_probe_count']}",
        "",
        "Scheduler output is search pressure only; only revalidated finite countermodels are imported.",
    ]
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
