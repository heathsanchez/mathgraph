"""Milestone 0 certificate-factory loop.

This module is intentionally small glue: it wires LawbookStore, KernelOracle,
the finite countermodel executor, and the revalidating importer into one
repeatable episode.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from mathgraph.countermodel_importer import import_finite_countermodel_results
from mathgraph.equations import parse_equation
from mathgraph.finite_countermodel_executor import run_finite_countermodel_tasks
from mathgraph.hashing import sha256_hex
from mathgraph.kernel_oracle import KernelOracle
from mathgraph.lawbook_store import LawbookStore

M0_WARNINGS = [
    "Finite search failure is not proof.",
    "Only importer-revalidated finite countermodels may be promoted.",
    "Advisory routes are never truth.",
]


@dataclass(frozen=True)
class M0EpisodeConfig:
    pairs_jsonl: str
    store_path: str
    ledger_jsonl: str | None = None
    report_json: str | None = None
    metrics_history_jsonl: str | None = None
    episode_id: str | None = None
    max_tasks: int | None = None
    max_countermodel_order: int = 3
    random_tables_per_order: int = 0
    exhaustive_order_limit: int = 3
    working_dir: str | None = None
    allow_construction: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "M0EpisodeConfig":
        return cls(**dict(data))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class M0PairResult:
    episode_id: str
    pair_index: int
    source: str
    target: str
    source_idx: int | None
    target_idx: int | None
    pair_hash: str
    status: str
    terminal_form: str | None
    trust_level: str | None
    provenance_type: str | None
    certificate_id: str | None
    promoted: bool
    known_skipped: bool
    tables_tried: int
    elapsed_sec: float
    explanation: str
    warnings: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class M0EpisodeMetrics:
    episode_id: str
    attempted: int
    known_skipped: int
    unknown_attempted: int
    verified_false: int
    verified_true: int
    constructor_failed: int
    parse_failed: int
    verification_failed: int
    residual: int
    new_unique_certificates: int
    promoted: int
    unknown_pair_fraction: float
    obstruction_coverage_rate: float
    compounding_confirmed: bool
    elapsed_seconds: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class M0EpisodeResult:
    config: dict[str, Any]
    metrics: M0EpisodeMetrics
    results: list[M0PairResult]
    outputs: dict[str, str | None]

    def to_dict(self) -> dict[str, Any]:
        return {
            "episode_id": self.metrics.episode_id,
            "config": dict(self.config),
            "metrics": self.metrics.to_dict(),
            "results": [result.to_dict() for result in self.results],
            "outputs": dict(self.outputs),
        }


def run_m0_episode(config: M0EpisodeConfig | dict[str, Any]) -> M0EpisodeResult:
    config = config if isinstance(config, M0EpisodeConfig) else M0EpisodeConfig.from_dict(config)
    started = time.perf_counter()
    episode_id = config.episode_id or _episode_id()
    rows = _read_jsonl(config.pairs_jsonl)
    if config.max_tasks is not None:
        rows = rows[: config.max_tasks]
    working_parent = Path(config.working_dir) if config.working_dir else None
    if working_parent:
        working_parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="m0_certificate_factory_", dir=working_parent) as tmp:
        result = _run_with_workdir(config, episode_id, rows, Path(tmp), started)
    return result


def _run_with_workdir(
    config: M0EpisodeConfig,
    episode_id: str,
    rows: list[dict[str, Any]],
    workdir: Path,
    started: float,
) -> M0EpisodeResult:
    store = LawbookStore(config.store_path)
    try:
        store.init_schema()
    finally:
        store.close()

    prior_metrics = _read_metrics_history(config.metrics_history_jsonl)
    queue_rows: list[dict[str, Any]] = []
    pending: dict[int, dict[str, Any]] = {}
    results_by_index: dict[int, M0PairResult] = {}

    for index, row in enumerate(rows):
        pair_started = time.perf_counter()
        source = str(row.get("source") or row.get("equation1") or "")
        target = str(row.get("target") or row.get("equation2") or "")
        source_idx = _optional_int(row.get("source_idx", row.get("eq1_id")))
        target_idx = _optional_int(row.get("target_idx", row.get("eq2_id")))
        pair_hash = _pair_hash(source, target, source_idx, target_idx)
        try:
            parse_equation(_normalize_equation(source))
            parse_equation(_normalize_equation(target))
        except Exception as exc:
            results_by_index[index] = _pair_result(
                episode_id,
                index,
                source,
                target,
                source_idx,
                target_idx,
                pair_hash,
                status="parse_failed",
                elapsed=time.perf_counter() - pair_started,
                explanation=str(exc),
            )
            continue

        known = _oracle_query(config.store_path, source, target)
        if _is_known_terminal(known):
            results_by_index[index] = _pair_result(
                episode_id,
                index,
                source,
                target,
                source_idx,
                target_idx,
                pair_hash,
                status="known_certificate_found",
                terminal_form=known.terminal_form,
                trust_level=known.trust_level,
                provenance_type=_provenance_from_answer(known),
                certificate_id=known.certificate_id,
                known_skipped=True,
                elapsed=time.perf_counter() - pair_started,
                explanation=known.explanation,
                evidence=known.to_dict(),
            )
            continue

        if not config.allow_construction:
            results_by_index[index] = _pair_result(
                episode_id,
                index,
                source,
                target,
                source_idx,
                target_idx,
                pair_hash,
                status="residual",
                elapsed=time.perf_counter() - pair_started,
                explanation="Construction disabled.",
            )
            continue

        task = {
            "task_id": f"{episode_id}_{index}_{pair_hash[:12]}",
            "source": source,
            "target": target,
            "source_idx": source_idx,
            "target_idx": target_idx,
            "route": "finite_countermodel",
            "task_kind": "finite_countermodel_search",
            "priority": row.get("priority", 1.0),
        }
        pending[index] = {
            "row": row,
            "source": source,
            "target": target,
            "source_idx": source_idx,
            "target_idx": target_idx,
            "pair_hash": pair_hash,
            "started": pair_started,
            "task_id": task["task_id"],
        }
        queue_rows.append(task)

    queue_path = workdir / "queue.jsonl"
    finite_results_path = workdir / "finite_results.jsonl"
    import_summary_path = workdir / "import_summary.json"
    _write_jsonl(queue_rows, queue_path)

    executor_by_task: dict[str, dict[str, Any]] = {}
    importer_by_task: dict[str, dict[str, Any]] = {}
    if queue_rows:
        run_finite_countermodel_tasks(
            {
                "task_queue_jsonl": str(queue_path),
                "out_jsonl": str(finite_results_path),
                "max_tasks": len(queue_rows),
                "max_order": config.max_countermodel_order,
                "random_tables_per_order": config.random_tables_per_order,
                "exhaustive_order_limit": config.exhaustive_order_limit,
                "stop_after_first": True,
            }
        )
        executor_rows = _read_jsonl(finite_results_path)
        executor_by_task = {str(row.get("task_id")): row for row in executor_rows}
        import_run = import_finite_countermodel_results(
            {
                "results_jsonl": str(finite_results_path),
                "store_path": config.store_path,
                "out_json": str(import_summary_path),
                "revalidate": True,
                "allow_duplicate_certificates": False,
            }
        )
        importer_by_task = {str(row.task_id): row.to_dict() for row in import_run.results}

    for index, info in pending.items():
        executor_row = executor_by_task.get(info["task_id"], {})
        import_row = importer_by_task.get(info["task_id"], {})
        after = _oracle_query(config.store_path, info["source"], info["target"])
        tables_tried = int(executor_row.get("tables_tried", 0) or 0)
        elapsed = time.perf_counter() - info["started"]
        if import_row.get("imported") and after.terminal_form == "FINITE_COUNTERMODEL":
            results_by_index[index] = _pair_result(
                episode_id,
                index,
                info["source"],
                info["target"],
                info["source_idx"],
                info["target_idx"],
                info["pair_hash"],
                status="verified_false",
                terminal_form="FINITE_COUNTERMODEL",
                trust_level="finite_verified",
                provenance_type="primitive",
                certificate_id=after.certificate_id or import_row.get("certificate_id"),
                promoted=True,
                tables_tried=tables_tried,
                elapsed=elapsed,
                explanation="Finite countermodel found, importer revalidated it, and LawbookStore now remembers the pair.",
                evidence={
                    "executor": executor_row,
                    "importer": import_row,
                    "oracle_after": after.to_dict(),
                },
            )
        elif executor_row.get("status") == "finite_countermodel_found":
            results_by_index[index] = _pair_result(
                episode_id,
                index,
                info["source"],
                info["target"],
                info["source_idx"],
                info["target_idx"],
                info["pair_hash"],
                status="verification_failed",
                tables_tried=tables_tried,
                elapsed=elapsed,
                explanation=import_row.get("reason") or "Countermodel candidate was not imported.",
                evidence={"executor": executor_row, "importer": import_row, "oracle_after": after.to_dict()},
            )
        elif executor_row.get("status") in {"no_countermodel_found", "parse_failed"}:
            status = "constructor_failed" if executor_row.get("status") == "no_countermodel_found" else "parse_failed"
            results_by_index[index] = _pair_result(
                episode_id,
                index,
                info["source"],
                info["target"],
                info["source_idx"],
                info["target_idx"],
                info["pair_hash"],
                status=status,
                tables_tried=tables_tried,
                elapsed=elapsed,
                explanation=executor_row.get("failure_reason") or "No finite countermodel was found within configured bounds.",
                evidence={"executor": executor_row, "importer": import_row, "oracle_after": after.to_dict()},
            )
        else:
            results_by_index[index] = _pair_result(
                episode_id,
                index,
                info["source"],
                info["target"],
                info["source_idx"],
                info["target_idx"],
                info["pair_hash"],
                status="error" if executor_row.get("status") == "error" else "residual",
                tables_tried=tables_tried,
                elapsed=elapsed,
                explanation=executor_row.get("failure_reason") or "No terminal certificate was produced.",
                evidence={"executor": executor_row, "importer": import_row, "oracle_after": after.to_dict()},
            )

    results = [results_by_index[index] for index in sorted(results_by_index)]
    metrics = _metrics(episode_id, results, prior_metrics, time.perf_counter() - started)
    outputs = {
        "store_path": config.store_path,
        "ledger_jsonl": config.ledger_jsonl,
        "report_json": config.report_json,
        "metrics_history_jsonl": config.metrics_history_jsonl,
    }
    episode = M0EpisodeResult(config=config.to_dict(), metrics=metrics, results=results, outputs=outputs)
    if config.ledger_jsonl:
        _write_jsonl([result.to_dict() for result in results], config.ledger_jsonl)
    if config.report_json:
        _write_json(episode.to_dict(), config.report_json)
    if config.metrics_history_jsonl:
        _append_jsonl(metrics.to_dict(), config.metrics_history_jsonl)
    return episode


def _metrics(
    episode_id: str,
    results: list[M0PairResult],
    prior_metrics: list[dict[str, Any]],
    elapsed: float,
) -> M0EpisodeMetrics:
    attempted = len(results)
    known_skipped = sum(1 for item in results if item.known_skipped)
    verified_false = sum(1 for item in results if item.status == "verified_false")
    verified_true = sum(1 for item in results if item.terminal_form == "VERIFIED_PROOF")
    constructor_failed = sum(1 for item in results if item.status == "constructor_failed")
    parse_failed = sum(1 for item in results if item.status == "parse_failed")
    verification_failed = sum(1 for item in results if item.status == "verification_failed")
    residual = sum(1 for item in results if item.status in {"residual", "error"})
    promoted = sum(1 for item in results if item.promoted)
    new_unique = len({item.certificate_id for item in results if item.promoted and item.certificate_id})
    unresolved = constructor_failed + parse_failed + verification_failed + residual
    unknown_fraction = unresolved / attempted if attempted else 0.0
    compounding = new_unique > 0
    if not compounding and prior_metrics:
        last = prior_metrics[-1]
        compounding = known_skipped > int(last.get("known_skipped", 0) or 0) or unknown_fraction < float(
            last.get("unknown_pair_fraction", 1.0) or 1.0
        )
    return M0EpisodeMetrics(
        episode_id=episode_id,
        attempted=attempted,
        known_skipped=known_skipped,
        unknown_attempted=attempted - known_skipped,
        verified_false=verified_false,
        verified_true=verified_true,
        constructor_failed=constructor_failed,
        parse_failed=parse_failed,
        verification_failed=verification_failed,
        residual=residual,
        new_unique_certificates=new_unique,
        promoted=promoted,
        unknown_pair_fraction=unknown_fraction,
        obstruction_coverage_rate=0.0,
        compounding_confirmed=compounding,
        elapsed_seconds=elapsed,
    )


def _oracle_query(store_path: str, source: str, target: str):
    store = LawbookStore(store_path)
    try:
        store.init_schema()
        return KernelOracle(store).query(source, target)
    finally:
        store.close()


def _is_known_terminal(answer: Any) -> bool:
    return answer.status in {"REFUTED", "VERIFIED"} and answer.terminal_form in {
        "FINITE_COUNTERMODEL",
        "VERIFIED_PROOF",
    }


def _pair_result(
    episode_id: str,
    pair_index: int,
    source: str,
    target: str,
    source_idx: int | None,
    target_idx: int | None,
    pair_hash: str,
    *,
    status: str,
    terminal_form: str | None = None,
    trust_level: str | None = None,
    provenance_type: str | None = None,
    certificate_id: str | None = None,
    promoted: bool = False,
    known_skipped: bool = False,
    tables_tried: int = 0,
    elapsed: float = 0.0,
    explanation: str = "",
    evidence: dict[str, Any] | None = None,
) -> M0PairResult:
    return M0PairResult(
        episode_id=episode_id,
        pair_index=pair_index,
        source=source,
        target=target,
        source_idx=source_idx,
        target_idx=target_idx,
        pair_hash=pair_hash,
        status=status,
        terminal_form=terminal_form,
        trust_level=trust_level,
        provenance_type=provenance_type,
        certificate_id=certificate_id,
        promoted=promoted,
        known_skipped=known_skipped,
        tables_tried=tables_tried,
        elapsed_sec=elapsed,
        explanation=explanation,
        warnings=list(M0_WARNINGS),
        evidence=dict(evidence or {}),
    )


def _pair_hash(source: str, target: str, source_idx: int | None, target_idx: int | None) -> str:
    return sha256_hex(
        {
            "source": str(source),
            "target": str(target),
            "source_idx": source_idx,
            "target_idx": target_idx,
        }
    )


def _provenance_from_answer(answer: Any) -> str:
    if answer.trust_level == "derived_from_verified_traces":
        return "derived"
    return "primitive"


def _normalize_equation(source: str) -> str:
    return source.replace("◇", "*").replace("·", "*")


def _episode_id() -> str:
    return "m0_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _write_jsonl(rows: list[dict[str, Any]], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def _append_jsonl(row: dict[str, Any], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def _write_json(payload: dict[str, Any], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _read_metrics_history(path: str | None) -> list[dict[str, Any]]:
    if not path or not Path(path).exists():
        return []
    return _read_jsonl(path)


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

