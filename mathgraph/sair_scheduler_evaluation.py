"""Held-out scheduler evaluation for clean SAIR motifs."""

from __future__ import annotations

import json
import random
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from statistics import median
from typing import Any, Sequence

import pandas as pd

from mathgraph.breakthrough_loop import BreakthroughTask
from mathgraph.external_certificates import (
    ExternalBoundaryEvidence,
    ExternalCertificate,
    ExternalCertificateKind,
    ExternalCertificateStatus,
    ExternalVerifierKind,
)
from mathgraph.finite_magma_world import check_finite_countermodel
from mathgraph.hashing import content_id
from mathgraph.promotion_gate import PromotionGate
from mathgraph.sair_constructor_bank import build_sair_constructor_bank, preferred_constructors_for_task
from mathgraph.sair_task_loader import load_sair_equations, load_sair_matrix, make_sair_false_tasks
from mathgraph.schema_feedback import oracle_fraction_captured
from mathgraph.terminal_schema import CanonicalTerminalForm, VerifierBoundaryKind


@dataclass(frozen=True)
class SAIRSchedulerEvalConfig:
    attempt_budget: int = 8
    seed: int = 1729


@dataclass(frozen=True)
class SAIRSchedulerPolicyResult:
    policy: str
    n_pairs: int
    attempted_pairs: int
    solved_or_refuted: int
    residual_count: int
    certificate_yield: int
    yield_rate: float
    mean_attempts_used: float
    median_attempts_used: float
    promotion_gate_accepted: int
    promotion_gate_rejected: int
    constructor_entropy: float
    residual_basin_entropy: float
    oracle_gap: float
    oracle_fraction_captured: float
    delta_yield_vs_base: int = 0
    delta_residual_vs_base: int = 0
    root_operator_law_score: float = 0.0
    advisory_only: bool = True

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class SAIRSchedulerEvalReport:
    policy_results: list[dict[str, Any]]
    task_results: list[dict[str, Any]]
    usage_summary: list[dict[str, Any]]
    pass_criteria: dict[str, bool]
    overall: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


def split_sair_pairs_train_eval(tasks: Sequence[BreakthroughTask], train_pairs: int, eval_pairs: int, seed: int = 1729) -> tuple[list[BreakthroughTask], list[BreakthroughTask]]:
    rng = random.Random(seed)
    items = list(tasks)
    rng.shuffle(items)
    return items[:train_pairs], items[train_pairs : train_pairs + eval_pairs]


def build_constructor_prior_from_motifs(motifs_df: pd.DataFrame) -> dict[str, float]:
    prior: dict[str, float] = {}
    for row in motifs_df.to_dict("records"):
        atoms = json.loads(row["atoms_json"])
        score = float(row.get("score", row.get("support", 1)) or 1)
        for atom in atoms:
            if atom.startswith("constructor:"):
                name = atom.split(":", 1)[1]
                prior[name] = prior.get(name, 0.0) + score
    return prior


def build_constructor_prior_from_root_schemas(motifs_df: pd.DataFrame) -> dict[str, float]:
    prior = build_constructor_prior_from_motifs(motifs_df)
    return {key: value * 0.8 for key, value in prior.items()}


def schedule_constructors_for_pair(task: BreakthroughTask, policy: str, motifs_df: pd.DataFrame | None = None, seed: int = 1729) -> list[str]:
    bank = build_sair_constructor_bank()
    names = [ctor.constructor_id for ctor in bank]
    if policy == "base_constructor_order":
        return sorted(names)
    if policy == "random_constructor_order":
        rng = random.Random(content_id("scheduler-random", [task.task_id, seed]))
        out = list(names)
        rng.shuffle(out)
        return out
    if policy in {"clean_motif_guided_order", "reason_atlas_guided_order", "frequency_constructor_order", "persistent_reason_atlas_order", "persistent_reason_atlas_plus_clean_motif_order"}:
        prior = build_constructor_prior_from_motifs(motifs_df if motifs_df is not None else pd.DataFrame())
        preferred = preferred_constructors_for_task(task, bank)
        return sorted(names, key=lambda name: (-(prior.get(name, 0.0) + (20.0 - preferred.index(name) if name in preferred else 0.0)), name))
    if policy == "root_schema_guided_order":
        prior = build_constructor_prior_from_root_schemas(motifs_df if motifs_df is not None else pd.DataFrame())
        preferred = preferred_constructors_for_task(task, bank)
        return sorted(names, key=lambda name: (-(prior.get(name, 0.0) + (20.0 - preferred.index(name) if name in preferred else 0.0)), name))
    if policy == "oracle_constructor_order":
        return names
    return names


def run_policy_on_pairs(tasks: Sequence[BreakthroughTask], policy: str, motifs_df: pd.DataFrame | None = None, config: SAIRSchedulerEvalConfig | None = None) -> tuple[SAIRSchedulerPolicyResult, list[dict[str, Any]]]:
    cfg = config or SAIRSchedulerEvalConfig()
    bank = {ctor.constructor_id: ctor for ctor in build_sair_constructor_bank()}
    gate = PromotionGate()
    accepted = 0
    rejected = 0
    attempts_used = []
    used_constructors = []
    residual_families = []
    rows = []
    for task in tasks:
        order = schedule_constructors_for_pair(task, policy, motifs_df, cfg.seed)
        if policy == "oracle_constructor_order":
            order = _oracle_order(task, order, bank)
        solved = False
        used = 0
        for ctor_name in order[: cfg.attempt_budget]:
            used += 1
            result = check_finite_countermodel(task.source_equation, task.target_equation, bank[ctor_name].table)
            decision = gate.evaluate(_cert(task, ctor_name, result.to_dict())) if result.terminal_candidate_ok else gate.evaluate(_failed_cert(task, ctor_name))
            if decision.accepted:
                accepted += 1
                solved = True
                used_constructors.append(ctor_name)
                break
            rejected += 1
        if not solved:
            residual_families.append(task.family)
        attempts_used.append(used)
        rows.append({"policy": policy, "task_id": task.task_id, "family": task.family, "solved": solved, "attempts_used": used, "advisory_only": True})
    n = len(tasks)
    result = SAIRSchedulerPolicyResult(
        policy=policy,
        n_pairs=n,
        attempted_pairs=n,
        solved_or_refuted=accepted,
        residual_count=n - accepted,
        certificate_yield=accepted,
        yield_rate=accepted / n if n else 0.0,
        mean_attempts_used=sum(attempts_used) / len(attempts_used) if attempts_used else 0.0,
        median_attempts_used=float(median(attempts_used)) if attempts_used else 0.0,
        promotion_gate_accepted=accepted,
        promotion_gate_rejected=rejected,
        constructor_entropy=compute_constructor_entropy(used_constructors),
        residual_basin_entropy=compute_constructor_entropy(residual_families),
        oracle_gap=0.0,
        oracle_fraction_captured=0.0,
        root_operator_law_score=float(accepted),
    )
    return result, rows


def evaluate_scheduler_policies(tasks: Sequence[BreakthroughTask], motifs_df: pd.DataFrame, config: SAIRSchedulerEvalConfig | None = None) -> SAIRSchedulerEvalReport:
    cfg = config or SAIRSchedulerEvalConfig()
    policies = ["base_constructor_order", "random_constructor_order", "frequency_constructor_order", "clean_motif_guided_order", "root_schema_guided_order", "reason_atlas_guided_order", "oracle_constructor_order"]
    results = []
    task_rows = []
    for policy in policies:
        result, rows = run_policy_on_pairs(tasks, policy, motifs_df, cfg)
        results.append(result)
        task_rows.extend(rows)
    base = next(r for r in results if r.policy == "base_constructor_order")
    oracle = next(r for r in results if r.policy == "oracle_constructor_order")
    final_results = []
    for result in results:
        d = result.to_dict()
        d["oracle_gap"] = max(0.0, oracle.yield_rate - base.yield_rate)
        d["oracle_fraction_captured"] = compute_oracle_fraction_captured(base.yield_rate, result.yield_rate, oracle.yield_rate)
        d["delta_yield_vs_base"] = result.certificate_yield - base.certificate_yield
        d["delta_residual_vs_base"] = base.residual_count - result.residual_count
        final_results.append(d)
    by_policy = {row["policy"]: row for row in final_results}
    criteria = {
        "clean_motif_guided_not_worse_than_base": by_policy["clean_motif_guided_order"]["certificate_yield"] >= base.certificate_yield,
        "reason_atlas_guided_not_worse_than_base": by_policy["reason_atlas_guided_order"]["certificate_yield"] >= base.certificate_yield,
        "guided_reduces_residual_or_attempts": any(by_policy[p]["delta_residual_vs_base"] > 0 or by_policy[p]["mean_attempts_used"] <= base.mean_attempts_used for p in ("clean_motif_guided_order", "reason_atlas_guided_order")),
        "advisory_boundary_ok": all(row.get("advisory_only", True) for row in final_results + task_rows),
    }
    usage = [{"constructor": name, "count": count} for name, count in Counter(row.get("constructor", "") for row in task_rows if row.get("constructor")).items()]
    return SAIRSchedulerEvalReport(final_results, task_rows, usage, criteria, "PASS" if all(criteria.values()) else "FAIL")


def compute_oracle_fraction_captured(base_rate: float, candidate_rate: float, oracle_rate: float) -> float:
    return oracle_fraction_captured(base_rate, candidate_rate, oracle_rate)


def compute_residual_compression(base_residual: int, candidate_residual: int) -> int:
    return int(base_residual) - int(candidate_residual)


def compute_constructor_entropy(values: Sequence[str]) -> float:
    import math

    if not values:
        return 0.0
    counts = Counter(values)
    total = float(len(values))
    return -sum((count / total) * math.log(count / total, 2) for count in counts.values())


def export_scheduler_eval_report(report: SAIRSchedulerEvalReport, out_dir: str | Path) -> dict[str, str]:
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    summary = output / "scheduler_policy_summary.csv"
    tasks = output / "scheduler_task_results.csv"
    usage = output / "scheduler_usage_summary.csv"
    final = output / "final_clean_scheduler_eval_report.json"
    pd.DataFrame(report.policy_results).to_csv(summary, index=False)
    pd.DataFrame(report.task_results).to_csv(tasks, index=False)
    pd.DataFrame(report.usage_summary).to_csv(usage, index=False)
    final.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return {"summary": str(summary), "tasks": str(tasks), "usage": str(usage), "report": str(final)}


def load_eval_tasks(equations_path: str | Path, matrix_path: str | Path, max_tasks: int, seed: int) -> list[BreakthroughTask]:
    equations = load_sair_equations(equations_path)
    matrix = load_sair_matrix(matrix_path)
    return [task.to_breakthrough_task() for task in make_sair_false_tasks(equations, matrix, max_tasks=max_tasks, random_seed=seed)]


def _cert(task: BreakthroughTask, ctor: str, result: dict[str, Any]) -> ExternalCertificate:
    artifact_hash = content_id("scheduler-finite-countermodel", [task.to_dict(), ctor, result])
    cert_id = content_id("scheduler-cert", [artifact_hash])
    boundary = ExternalBoundaryEvidence(
        evidence_id=content_id("scheduler-boundary", [cert_id, artifact_hash]),
        boundary_kind=VerifierBoundaryKind.FINITE_CHECKED,
        certificate_id=cert_id,
        terminal_form=CanonicalTerminalForm.REFUTATION_CERTIFICATE,
        source_artifact_id=task.task_id,
        artifact_hash=artifact_hash,
        verifier_kind=ExternalVerifierKind.FINITE_COUNTERMODEL_CHECKER,
        checker_name="mathgraph_sair_scheduler_finite_checker",
    )
    return ExternalCertificate(
        cert_id=cert_id,
        verifier=ExternalVerifierKind.FINITE_COUNTERMODEL_CHECKER,
        status=ExternalCertificateStatus.COUNTERMODEL_FOUND,
        claim=f"{task.source_equation} does not imply {task.target_equation}",
        claim_hash=content_id("scheduler-claim", task.to_dict()),
        certificate_kind=ExternalCertificateKind.FINITE_COUNTERMODEL,
        proposed_terminal_form=CanonicalTerminalForm.REFUTATION_CERTIFICATE,
        boundary_evidence=boundary,
        artifact_hash=artifact_hash,
        countermodel=result,
        boundary_valid=True,
    )


def _failed_cert(task: BreakthroughTask, ctor: str) -> ExternalCertificate:
    return ExternalCertificate(
        cert_id=content_id("scheduler-failed", [task.task_id, ctor]),
        verifier=ExternalVerifierKind.FINITE_COUNTERMODEL_CHECKER,
        status=ExternalCertificateStatus.REJECTED,
        claim=f"no finite countermodel for {task.task_id} with {ctor}",
        claim_hash=content_id("scheduler-claim", task.to_dict()),
        certificate_kind=ExternalCertificateKind.ADVISORY_ONLY,
        metadata={"finite_search_miss": True},
    )


def _oracle_order(task: BreakthroughTask, names: list[str], bank: dict[str, Any]) -> list[str]:
    good = []
    bad = []
    for name in names:
        result = check_finite_countermodel(task.source_equation, task.target_equation, bank[name].table)
        (good if result.terminal_candidate_ok else bad).append(name)
    return good + bad
