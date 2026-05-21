"""MathGraph Breakthrough Loop v1: finite-checker metabolism demo."""

from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

from mathgraph.external_certificates import (
    ExternalBoundaryEvidence,
    ExternalCertificate,
    ExternalCertificateKind,
    ExternalCertificateStatus,
    ExternalVerifierKind,
)
from mathgraph.finite_magma_world import check_finite_countermodel, normalize_table
from mathgraph.hashing import content_id
from mathgraph.promotion_gate import PromotionGate, PromotionGateDecision
from mathgraph.reason_atlas_feedback_loop import ReasonAtlasFeedbackLoop, ReasonAtlasFeedbackLoopConfig
from mathgraph.reason_atlas_store import ReasonAtlasEntry, ReasonAtlasEntryKind, ReasonAtlasTrust
from mathgraph.terminal_schema import CanonicalTerminalForm, VerifierBoundaryKind


@dataclass(frozen=True)
class BreakthroughTask:
    task_id: str
    source_equation: str
    target_equation: str
    family: str = "unknown"
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BreakthroughTask":
        return cls(
            task_id=str(data["task_id"]),
            source_equation=str(data["source_equation"]),
            target_equation=str(data["target_equation"]),
            family=str(data.get("family", "unknown")),
            metadata=dict(data.get("metadata", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "source_equation": self.source_equation,
            "target_equation": self.target_equation,
            "family": self.family,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class BreakthroughAttempt:
    attempt_id: str
    episode_index: int
    task_id: str
    family: str
    constructor_name: str
    entry_id: str
    checker_ok: bool
    promotion_accepted: bool
    diagnostic: str
    certificate: dict[str, Any] | None = None
    promotion_decision: dict[str, Any] | None = None
    lawbook_candidate: dict[str, Any] | None = None
    advisory_only: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "attempt_id": self.attempt_id,
            "episode_index": self.episode_index,
            "task_id": self.task_id,
            "family": self.family,
            "constructor_name": self.constructor_name,
            "entry_id": self.entry_id,
            "checker_ok": self.checker_ok,
            "promotion_accepted": self.promotion_accepted,
            "diagnostic": self.diagnostic,
            "certificate": self.certificate,
            "promotion_decision": self.promotion_decision,
            "lawbook_candidate": self.lawbook_candidate,
            "advisory_only": True,
        }


@dataclass(frozen=True)
class BreakthroughEpisodeResult:
    episode_index: int
    attempted_count: int
    accepted_terminal_count: int
    rejected_count: int
    residual_count: int
    solved_or_refuted_count: int
    residual_entropy_by_family: float
    constructor_success_rates: dict[str, float]
    queue_priority_before_after: list[dict[str, Any]]
    lawbook_candidate_count: int
    feedback_event_count: int
    route_or_constructor_gain: float
    breakthrough_score: float
    attempts: list[BreakthroughAttempt]
    residual_task_ids: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "episode_index": self.episode_index,
            "attempted_count": self.attempted_count,
            "accepted_terminal_count": self.accepted_terminal_count,
            "rejected_count": self.rejected_count,
            "residual_count": self.residual_count,
            "solved_or_refuted_count": self.solved_or_refuted_count,
            "residual_entropy_by_family": self.residual_entropy_by_family,
            "constructor_success_rates": dict(self.constructor_success_rates),
            "queue_priority_before_after": list(self.queue_priority_before_after),
            "lawbook_candidate_count": self.lawbook_candidate_count,
            "feedback_event_count": self.feedback_event_count,
            "route_or_constructor_gain": self.route_or_constructor_gain,
            "breakthrough_score": self.breakthrough_score,
            "attempts": [attempt.to_dict() for attempt in self.attempts],
            "residual_task_ids": list(self.residual_task_ids),
        }


@dataclass(frozen=True)
class BreakthroughLoopConfig:
    episodes: int = 4
    attempts_per_task: int = 1
    out_dir: str | Path | None = None
    reason_atlas_db: str | Path | None = None
    checker_name: str = "mathgraph_finite_magma_checker"
    checker_version: str = "v1"


class BreakthroughLoop:
    def __init__(
        self,
        tasks: Sequence[BreakthroughTask | dict[str, Any]],
        constructor_families: dict[str, Sequence[Sequence[int]]],
        config: BreakthroughLoopConfig | None = None,
    ) -> None:
        self.tasks = [task if isinstance(task, BreakthroughTask) else BreakthroughTask.from_dict(task) for task in tasks]
        self.constructor_families = {name: normalize_table(table) for name, table in constructor_families.items()}
        self.config = config or BreakthroughLoopConfig()
        db_path = self.config.reason_atlas_db or Path("/tmp/mathgraph_breakthrough_loop_demo/reason_atlas.sqlite")
        self.reason_loop = ReasonAtlasFeedbackLoop(ReasonAtlasFeedbackLoopConfig(db_path))
        self.gate = PromotionGate()
        self.solved: dict[str, BreakthroughAttempt] = {}
        self.all_attempts: list[BreakthroughAttempt] = []
        self.lawbook_candidates: list[dict[str, Any]] = []
        self.accepted_certificates: list[dict[str, Any]] = []
        self.rejected_attempts: list[dict[str, Any]] = []
        self.feedback_rows: list[dict[str, Any]] = []
        self.queue_rows: list[dict[str, Any]] = []
        self._seed_reason_atlas_entries()

    def run(self) -> dict[str, Any]:
        episodes: list[BreakthroughEpisodeResult] = []
        previous_solved = 0
        for idx in range(self.config.episodes):
            episodes.append(self.run_episode(idx, previous_solved))
            previous_solved = episodes[-1].solved_or_refuted_count
        summary = self._summary(episodes)
        if self.config.out_dir:
            write_breakthrough_outputs(self.config.out_dir, summary, episodes, self)
        return summary

    def run_episode(self, episode_index: int, previous_solved: int = 0) -> BreakthroughEpisodeResult:
        before = self._priority_snapshot()
        attempts: list[BreakthroughAttempt] = []
        for task in self.tasks:
            if task.task_id in self.solved:
                continue
            for constructor_name in self._ranked_constructors(task)[: self.config.attempts_per_task]:
                attempt = self._attempt(task, constructor_name, episode_index)
                attempts.append(attempt)
                self.all_attempts.append(attempt)
                if attempt.promotion_accepted:
                    self.solved[task.task_id] = attempt
                    break
        self.reason_loop.rescore()
        after = self._priority_snapshot()
        queue_shift = _queue_shift(before, after)
        residuals = [task for task in self.tasks if task.task_id not in self.solved]
        solved_count = len(self.solved)
        constructor_rates = self._constructor_success_rates()
        feedback_count = self.reason_loop.store.stats().feedback_count
        result = BreakthroughEpisodeResult(
            episode_index=episode_index,
            attempted_count=len(attempts),
            accepted_terminal_count=sum(1 for attempt in attempts if attempt.promotion_accepted),
            rejected_count=sum(1 for attempt in attempts if not attempt.promotion_accepted),
            residual_count=len(residuals),
            solved_or_refuted_count=solved_count,
            residual_entropy_by_family=_entropy([task.family for task in residuals]),
            constructor_success_rates=constructor_rates,
            queue_priority_before_after=queue_shift,
            lawbook_candidate_count=len(self.lawbook_candidates),
            feedback_event_count=feedback_count,
            route_or_constructor_gain=float(solved_count - previous_solved),
            breakthrough_score=float(solved_count - 0.25 * len(residuals) + 0.1 * sum(constructor_rates.values())),
            attempts=attempts,
            residual_task_ids=[task.task_id for task in residuals],
        )
        return result

    def _attempt(self, task: BreakthroughTask, constructor_name: str, episode_index: int) -> BreakthroughAttempt:
        table = self.constructor_families[constructor_name]
        result = check_finite_countermodel(task.source_equation, task.target_equation, table)
        entry_id = self._entry_id(task.family, constructor_name)
        cert: ExternalCertificate | None = None
        decision: PromotionGateDecision
        if result.terminal_candidate_ok:
            cert = self._certificate_for_countermodel(task, constructor_name, result.to_dict())
            decision = self.gate.evaluate(cert)
        else:
            cert = self._advisory_failure_certificate(task, constructor_name, result.diagnostic)
            decision = self.gate.evaluate(cert)
        if decision.accepted and decision.lawbook_candidate:
            self.lawbook_candidates.append(decision.lawbook_candidate)
            self.accepted_certificates.append(cert.to_dict())
            self.reason_loop.record_verifier_result(entry_id, True, metadata={"task_id": task.task_id, "constructor": constructor_name})
            self.reason_loop.record_transfer_result(entry_id, True, residual_before=len(self.tasks) - len(self.solved), residual_after=max(0, len(self.tasks) - len(self.solved) - 1))
        else:
            self.rejected_attempts.append({"task": task.to_dict(), "constructor": constructor_name, "decision": decision.to_dict(), "diagnostic": result.diagnostic})
            self.reason_loop.record_verifier_result(entry_id, False, metadata={"task_id": task.task_id, "constructor": constructor_name, "diagnostic": result.diagnostic})
            self.reason_loop.record_obstruction(entry_id, "FINITE_COUNTERMODEL_NOT_FOUND_OR_BOUNDARY_REJECTED", metadata={"task_id": task.task_id})
        self.feedback_rows.extend(event.to_dict() for event in self.reason_loop.store.feedback_for_entry(entry_id)[-2:])
        return BreakthroughAttempt(
            attempt_id=content_id("breakthrough-attempt", [episode_index, task.task_id, constructor_name]),
            episode_index=episode_index,
            task_id=task.task_id,
            family=task.family,
            constructor_name=constructor_name,
            entry_id=entry_id,
            checker_ok=result.terminal_candidate_ok,
            promotion_accepted=decision.accepted,
            diagnostic=result.diagnostic,
            certificate=cert.to_dict(),
            promotion_decision=decision.to_dict(),
            lawbook_candidate=decision.lawbook_candidate,
        )

    def _certificate_for_countermodel(self, task: BreakthroughTask, constructor_name: str, result: dict[str, Any]) -> ExternalCertificate:
        artifact = {
            "task": task.to_dict(),
            "constructor_name": constructor_name,
            "finite_countermodel": result,
            "checker_name": self.config.checker_name,
            "checker_version": self.config.checker_version,
        }
        artifact_hash = content_id("finite-countermodel-artifact", artifact)
        cert_id = content_id("finite-countermodel-certificate", artifact)
        boundary = ExternalBoundaryEvidence(
            evidence_id=content_id("finite-countermodel-boundary", [cert_id, artifact_hash]),
            boundary_kind=VerifierBoundaryKind.FINITE_CHECKED,
            certificate_id=cert_id,
            terminal_form=CanonicalTerminalForm.REFUTATION_CERTIFICATE,
            source_artifact_id=task.task_id,
            artifact_hash=artifact_hash,
            verifier_kind=ExternalVerifierKind.FINITE_COUNTERMODEL_CHECKER,
            checker_name=self.config.checker_name,
            checker_version=self.config.checker_version,
            metadata={
                "source_satisfied_global": True,
                "target_violated_at_witness": True,
                "constructor_name": constructor_name,
            },
        )
        return ExternalCertificate(
            cert_id=cert_id,
            verifier=ExternalVerifierKind.FINITE_COUNTERMODEL_CHECKER,
            status=ExternalCertificateStatus.COUNTERMODEL_FOUND,
            claim=f"{task.source_equation} does not imply {task.target_equation}",
            claim_hash=content_id("breakthrough-claim", task.to_dict()),
            source_artifact_id=task.task_id,
            certificate_kind=ExternalCertificateKind.FINITE_COUNTERMODEL,
            proposed_terminal_form=CanonicalTerminalForm.REFUTATION_CERTIFICATE,
            boundary_evidence=boundary,
            raw_output_hash=artifact_hash,
            artifact_hash=artifact_hash,
            checker_name=self.config.checker_name,
            checker_version=self.config.checker_version,
            countermodel=result,
            metadata=artifact,
            boundary_valid=True,
        )

    def _advisory_failure_certificate(self, task: BreakthroughTask, constructor_name: str, diagnostic: str) -> ExternalCertificate:
        payload = {"task": task.to_dict(), "constructor_name": constructor_name, "diagnostic": diagnostic, "finite_search_miss": True}
        return ExternalCertificate(
            cert_id=content_id("advisory-failed-breakthrough-attempt", payload),
            verifier=ExternalVerifierKind.FINITE_COUNTERMODEL_CHECKER,
            status=ExternalCertificateStatus.REJECTED,
            claim=f"No finite countermodel found for {task.task_id} with {constructor_name}",
            claim_hash=content_id("breakthrough-claim", task.to_dict()),
            certificate_kind=ExternalCertificateKind.ADVISORY_ONLY,
            metadata=payload,
        )

    def _seed_reason_atlas_entries(self) -> None:
        entries = []
        for family in sorted({task.family for task in self.tasks}):
            for constructor_name in self.constructor_families:
                entry_id = self._entry_id(family, constructor_name)
                entries.append(
                    ReasonAtlasEntry(
                        entry_id=entry_id,
                        kind=ReasonAtlasEntryKind.CONSTRUCTOR_HINT,
                        name=f"{family}:{constructor_name}",
                        atoms=[family, constructor_name, "finite_magma_countermodel"],
                        pattern=f"use {constructor_name} for {family}",
                        payload={"family": family, "constructor_name": constructor_name},
                        evidence_kind="ADVISORY_CONSTRUCTOR_HINT",
                        trust=ReasonAtlasTrust.CANDIDATE,
                        support=1,
                        family_count=1,
                    )
                )
        self.reason_loop.ingest_entries(entries)

    def _ranked_constructors(self, task: BreakthroughTask) -> list[str]:
        rows = []
        for constructor_name in self.constructor_families:
            entry = self.reason_loop.store.get_entry(self._entry_id(task.family, constructor_name))
            score = _entry_rank_score(entry)
            rows.append((score + _initial_constructor_bias(constructor_name), constructor_name))
        rows.sort(key=lambda item: (-item[0], item[1]))
        return [name for _score, name in rows]

    def _priority_snapshot(self) -> dict[str, float]:
        out = {}
        for task in self.tasks:
            for constructor_name in self.constructor_families:
                entry_id = self._entry_id(task.family, constructor_name)
                entry = self.reason_loop.store.get_entry(entry_id)
                out[entry_id] = float(_entry_rank_score(entry) + _initial_constructor_bias(constructor_name))
        return out

    def _constructor_success_rates(self) -> dict[str, float]:
        counts: dict[str, list[int]] = {}
        for attempt in self.all_attempts:
            counts.setdefault(attempt.constructor_name, [0, 0])
            counts[attempt.constructor_name][1] += 1
            if attempt.promotion_accepted:
                counts[attempt.constructor_name][0] += 1
        return {name: successes / total for name, (successes, total) in counts.items() if total}

    def _entry_id(self, family: str, constructor_name: str) -> str:
        return content_id("breakthrough-constructor-hint", [family, constructor_name])

    def _summary(self, episodes: Sequence[BreakthroughEpisodeResult]) -> dict[str, Any]:
        first = episodes[0]
        final = episodes[-1]
        improved = final.solved_or_refuted_count > first.solved_or_refuted_count or final.residual_count < first.residual_count
        boundary_ok = all(row.get("advisory_only", True) for row in self.reason_loop.next_advisory_tasks(limit=500))
        self.queue_rows = self.reason_loop.next_advisory_tasks(limit=500)
        return {
            "overall": "PASS" if improved and self.lawbook_candidates and self.rejected_attempts and boundary_ok else "FAIL",
            "episode_count": len(episodes),
            "initial_solved_or_refuted_count": first.solved_or_refuted_count,
            "final_solved_or_refuted_count": final.solved_or_refuted_count,
            "initial_residual_count": first.residual_count,
            "final_residual_count": final.residual_count,
            "accepted_terminal_certificates": len(self.accepted_certificates),
            "promotion_gate_accepted": len(self.lawbook_candidates),
            "promotion_gate_rejected": len(self.rejected_attempts),
            "feedback_event_count": self.reason_loop.store.stats().feedback_count,
            "lawbook_candidate_count": len(self.lawbook_candidates),
            "breakthrough_score": final.breakthrough_score - first.breakthrough_score,
            "residual_entropy_before": first.residual_entropy_by_family,
            "residual_entropy_after": final.residual_entropy_by_family,
            "route_or_constructor_gain": final.solved_or_refuted_count - first.solved_or_refuted_count,
            "advisory_boundary_ok": boundary_ok,
            "episodes": [episode.to_dict() for episode in episodes],
        }


def _initial_constructor_bias(constructor_name: str) -> float:
    order = {
        "left_projection_2": 5.0,
        "constant0_2": 4.0,
        "right_projection_2": 3.0,
        "xor_mod_2": 2.0,
        "add_mod_3": 1.5,
        "sub_mod_3": 1.0,
        "min_3": 0.8,
        "max_3": 0.7,
        "rectangular_band_4": 0.6,
        "comm_nonassoc_3": 0.5,
        "perturbation_3": 0.4,
    }
    return order.get(constructor_name, 0.0)


def _entry_rank_score(entry: Any) -> float:
    if entry is None:
        return 0.0
    return (
        float(getattr(entry, "priority_score", 0.0) or 0.0)
        - 8.0 * float(getattr(entry, "verifier_failures", 0) or 0)
        - 2.0 * float(getattr(entry, "obstruction_count", 0) or 0)
        + 3.0 * float(getattr(entry, "verifier_successes", 0) or 0)
    )


def _entropy(labels: Sequence[str]) -> float:
    if not labels:
        return 0.0
    counts = {label: labels.count(label) for label in set(labels)}
    total = float(len(labels))
    return -sum((count / total) * math.log(count / total, 2) for count in counts.values())


def _queue_shift(before: dict[str, float], after: dict[str, float]) -> list[dict[str, Any]]:
    rows = []
    for entry_id in sorted(before):
        rows.append({"entry_id": entry_id, "priority_before": before[entry_id], "priority_after": after.get(entry_id, 0.0), "delta": after.get(entry_id, 0.0) - before[entry_id]})
    rows.sort(key=lambda row: abs(float(row["delta"])), reverse=True)
    return rows[:20]


def write_breakthrough_outputs(out_dir: str | Path, summary: dict[str, Any], episodes: Sequence[BreakthroughEpisodeResult], loop: BreakthroughLoop) -> dict[str, str]:
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = {
        "summary": output / "breakthrough_summary.json",
        "episode_metrics": output / "episode_metrics.csv",
        "attempts": output / "attempts.csv",
        "accepted_certificates": output / "accepted_certificates.jsonl",
        "rejected_attempts": output / "rejected_attempts.jsonl",
        "residual_tasks": output / "residual_tasks.csv",
        "reason_atlas_feedback": output / "reason_atlas_feedback.jsonl",
        "lawbook_candidates": output / "lawbook_candidates.jsonl",
        "queue_before_after": output / "queue_before_after.csv",
        "report": output / "report.md",
    }
    paths["summary"].write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    _write_csv(paths["episode_metrics"], [_episode_metric_row(ep) for ep in episodes])
    _write_csv(paths["attempts"], [_attempt_row(a) for a in loop.all_attempts])
    _write_jsonl(paths["accepted_certificates"], loop.accepted_certificates)
    _write_jsonl(paths["rejected_attempts"], loop.rejected_attempts)
    residual_rows = [task.to_dict() for task in loop.tasks if task.task_id not in loop.solved]
    _write_csv(paths["residual_tasks"], residual_rows)
    _write_jsonl(paths["reason_atlas_feedback"], loop.feedback_rows)
    _write_jsonl(paths["lawbook_candidates"], loop.lawbook_candidates)
    shift_rows = [row for ep in episodes for row in ep.queue_priority_before_after]
    _write_csv(paths["queue_before_after"], shift_rows)
    paths["report"].write_text(render_breakthrough_report(summary), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def render_breakthrough_report(summary: dict[str, Any]) -> str:
    return f"""# MathGraph Breakthrough Loop v1

## BREAKTHROUGH LOOP RESULT

- Episode 0 solved/refuted: `{summary['initial_solved_or_refuted_count']}`
- Final episode solved/refuted: `{summary['final_solved_or_refuted_count']}`
- Residuals: `{summary['initial_residual_count']}` -> `{summary['final_residual_count']}`
- Residual entropy: `{summary['residual_entropy_before']:.3f}` -> `{summary['residual_entropy_after']:.3f}`
- Accepted terminal certificates: `{summary['accepted_terminal_certificates']}`
- PromotionGate accepted: `{summary['promotion_gate_accepted']}`
- PromotionGate rejected: `{summary['promotion_gate_rejected']}`
- Feedback events: `{summary['feedback_event_count']}`
- Constructor priority shift / gain: `{summary['route_or_constructor_gain']}`
- Breakthrough score delta: `{summary['breakthrough_score']:.3f}`
- Overall: `{summary['overall']}`

## Boundary

Finite magma tables are checked by the deterministic finite checker. Successful
checks become `ExternalCertificate` objects and cross into Lawbook candidates
only through `PromotionGate`. Failed searches and advisory queue rows remain
feedback, not truth.
"""


def _episode_metric_row(ep: BreakthroughEpisodeResult) -> dict[str, Any]:
    row = ep.to_dict()
    row.pop("attempts", None)
    row.pop("queue_priority_before_after", None)
    row["constructor_success_rates"] = json.dumps(row["constructor_success_rates"], sort_keys=True)
    row["residual_task_ids"] = json.dumps(row["residual_task_ids"], sort_keys=True)
    return row


def _attempt_row(attempt: BreakthroughAttempt) -> dict[str, Any]:
    row = attempt.to_dict()
    row["certificate"] = json.dumps(row["certificate"], sort_keys=True)
    row["promotion_decision"] = json.dumps(row["promotion_decision"], sort_keys=True)
    row["lawbook_candidate"] = json.dumps(row["lawbook_candidate"], sort_keys=True)
    return row


def _write_jsonl(path: Path, rows: Sequence[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def _write_csv(path: Path, rows: Sequence[dict[str, Any]]) -> None:
    fieldnames = sorted({key for row in rows for key in row}) if rows else ["empty"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})
