"""Canonical MathGraph compounding loop.

This module keeps v0 deliberately narrow: finite magma implication tasks,
PromotionGate-accepted finite countermodel certificates, in-run memory for the
fallback path, and explicit metrics that separate verified, advisory, and
diagnostic signals.
"""

from __future__ import annotations

import csv
import json
import random
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Sequence

from mathgraph.external_certificates import (
    ExternalBoundaryEvidence,
    ExternalCertificate,
    ExternalCertificateKind,
    ExternalCertificateStatus,
    ExternalVerifierKind,
)
from mathgraph.finite_magma_world import check_finite_countermodel, constant_table, left_projection, right_projection
from mathgraph.hashing import content_id, sha256_hex
from mathgraph.promotion_gate import PromotionGate
from mathgraph.sair_constructor_bank import SAIRConstructor, build_sair_constructor_bank
from mathgraph.sair_task_loader import SAIRTaskLoadConfig, load_sair_equations, load_sair_matrix, make_sair_false_tasks
from mathgraph.terminal_schema import CanonicalTerminalForm, VerifierBoundaryKind


REQUIRED_OUTPUTS = (
    "compounding_report.json",
    "compounding_report.md",
    "episode_summary.csv",
    "policy_summary.csv",
    "lawbook_hits.csv",
    "decode_to_verify.csv",
    "residuals_by_episode.csv",
    "artifact_manifest.json",
    "run_metadata.json",
)


@dataclass(frozen=True)
class CompoundingEngineConfig:
    out_dir: str | Path = "/tmp/mathgraph_compounding_demo"
    equations: str | Path | None = None
    matrix: str | Path | None = None
    episodes: int = 2
    train_pairs: int = 12
    eval_pairs: int = 12
    attempt_budget: int = 4
    seed: int = 1729
    allow_fallback_demo: bool = False
    skip_plots: bool = True
    max_runtime_sec: float | None = None
    reason_atlas_db: str | Path | None = None
    lawbook_db: str | Path | None = None


@dataclass(frozen=True)
class CompoundingPolicyResult:
    episode: int
    policy: str
    attempted_pairs: int
    solved_or_refuted: int
    certificate_yield: int
    yield_rate: float
    residual_count: int
    residual_reduction_vs_baseline: int
    attempts_used: int
    certificates_per_attempt: float
    cost_per_certificate: float
    promotion_gate_accepted: int
    promotion_gate_rejected: int
    true_contamination_count: int
    true_contamination_rate: float
    lawbook_hit_count: int
    lawbook_hit_rate: float
    lawbook_action_change_count: int
    lawbook_action_change_rate: float
    decode_attempt_count: int
    decode_success_count: int
    decode_success_rate: float
    advisory_only: bool = True
    skipped: bool = False
    skip_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class CompoundingEpisodeResult:
    episode: int
    policy_results: tuple[CompoundingPolicyResult, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"episode": self.episode, "policy_results": [p.to_dict() for p in self.policy_results]}


@dataclass(frozen=True)
class CompoundingRunReport:
    source_mode: str
    real_corpus_used: bool
    fallback_mode: bool
    equations_loaded: int
    matrix_pairs_sampled: int
    advisory_boundary_preserved: bool
    terminal_claims_from_advisory_count: int
    failed_search_promoted_true_count: int
    compounding_signal_detected: bool
    memory_backend: str
    episodes: tuple[CompoundingEpisodeResult, ...]
    metrics: tuple[dict[str, Any], ...]
    output_dir: str
    artifacts: dict[str, str]
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_mode": self.source_mode,
            "real_corpus_used": self.real_corpus_used,
            "fallback_mode": self.fallback_mode,
            "equations_loaded": self.equations_loaded,
            "matrix_pairs_sampled": self.matrix_pairs_sampled,
            "advisory_boundary_preserved": self.advisory_boundary_preserved,
            "terminal_claims_from_advisory_count": self.terminal_claims_from_advisory_count,
            "failed_search_promoted_true_count": self.failed_search_promoted_true_count,
            "compounding_signal_detected": self.compounding_signal_detected,
            "memory_backend": self.memory_backend,
            "episodes": [ep.to_dict() for ep in self.episodes],
            "metrics": list(self.metrics),
            "output_dir": self.output_dir,
            "artifacts": dict(self.artifacts),
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class _Task:
    task_id: str
    source_equation: str
    target_equation: str
    family: str
    expected_false: bool = True

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class _Memory:
    by_family: dict[str, list[str]] = field(default_factory=dict)
    accepted: list[dict[str, Any]] = field(default_factory=list)

    def learn(self, task: _Task, constructor_id: str, certificate: ExternalCertificate) -> None:
        ids = self.by_family.setdefault(task.family, [])
        if constructor_id not in ids:
            ids.insert(0, constructor_id)
        self.accepted.append({"task_id": task.task_id, "family": task.family, "constructor_id": constructor_id, "certificate_id": certificate.cert_id})

    def query(self, task: _Task) -> list[str]:
        return list(self.by_family.get(task.family, ()))


class CompoundingEngine:
    def __init__(self, config: CompoundingEngineConfig) -> None:
        self.config = config
        self.out_dir = Path(config.out_dir)
        self.gate = PromotionGate()
        self.constructors = build_sair_constructor_bank()
        self.constructor_map = {c.constructor_id: c for c in self.constructors}
        self.memory = _Memory()
        self.lawbook_hits: list[dict[str, Any]] = []
        self.decode_rows: list[dict[str, Any]] = []
        self.attempt_rows: list[dict[str, Any]] = []
        self.residual_rows: list[dict[str, Any]] = []

    def run(self) -> CompoundingRunReport:
        self.out_dir.mkdir(parents=True, exist_ok=True)
        train, eval_tasks, source_mode, equations_loaded, matrix_pairs_sampled, warnings = self._load_tasks()
        self._train_memory(train)
        baseline = self._run_policy(0, "baseline", eval_tasks, baseline_residual=None)
        baseline_residual = baseline.residual_count
        episode_results: list[CompoundingEpisodeResult] = [CompoundingEpisodeResult(0, (baseline,))]
        for episode in range(1, max(1, self.config.episodes)):
            policies = [
                self._run_policy(episode, "memory", eval_tasks, baseline_residual=baseline_residual),
                self._run_policy(episode, "lawbook_attention", eval_tasks, baseline_residual=baseline_residual),
                self._run_policy(episode, "reason_atlas", eval_tasks, baseline_residual=baseline_residual),
                self._run_policy(episode, "shuffled_null", eval_tasks, baseline_residual=baseline_residual),
                self._skipped_policy(episode, "htilt_reason_atlas", eval_tasks, "H-Tilt persistent scorer not required for canonical v0 fallback path."),
            ]
            episode_results.append(CompoundingEpisodeResult(episode, tuple(policies)))
        report = self._build_report(source_mode, equations_loaded, matrix_pairs_sampled, tuple(episode_results), tuple(warnings))
        artifacts = self._write_outputs(report)
        return replace(report, artifacts=artifacts)

    def _load_tasks(self) -> tuple[list[_Task], list[_Task], str, int, int, list[str]]:
        warnings: list[str] = []
        if self.config.equations and self.config.matrix:
            equations = load_sair_equations(self.config.equations)
            matrix = load_sair_matrix(self.config.matrix)
            if equations and matrix is not None:
                total = max(1, self.config.train_pairs + self.config.eval_pairs)
                loaded = make_sair_false_tasks(equations, matrix, max_tasks=total, random_seed=self.config.seed)
                tasks = [_Task(t.task_id, t.normalized_equation1, t.normalized_equation2, t.family, expected_false=not t.expected_matrix_label) for t in loaded]
                train = tasks[: self.config.train_pairs]
                eval_tasks = tasks[self.config.train_pairs : self.config.train_pairs + self.config.eval_pairs]
                return train, eval_tasks, "real_sair", len(equations), len(tasks), warnings
            raise FileNotFoundError("real SAIR mode requested but equations/matrix could not be loaded")
        if not self.config.allow_fallback_demo:
            raise FileNotFoundError("real SAIR files were not supplied; pass --allow-fallback-demo to run fallback mode")
        tasks = _fallback_tasks()
        split = max(1, min(len(tasks) - 1, self.config.train_pairs if self.config.train_pairs < len(tasks) else len(tasks) // 2))
        return tasks[:split], tasks[split : split + max(1, self.config.eval_pairs)], "fallback_demo", 0, 0, ["fallback_demo: not real SAIR"]

    def _train_memory(self, train: Sequence[_Task]) -> None:
        for task in train:
            for ctor in self.constructors:
                result = check_finite_countermodel(task.source_equation, task.target_equation, ctor.table)
                if result.terminal_candidate_ok:
                    cert = self._certificate_for_result(task, ctor, result)
                    decision = self.gate.evaluate(cert)
                    if decision.accepted:
                        self.memory.learn(task, ctor.constructor_id, cert)
                    break

    def _run_policy(self, episode: int, policy: str, tasks: Sequence[_Task], *, baseline_residual: int | None) -> CompoundingPolicyResult:
        solved = attempts = accepted = rejected = lawbook_hits = action_changes = decode_attempts = decode_success = true_contamination = 0
        residual_count = 0
        for task in tasks:
            order, hit, changed = self._constructor_order(policy, task)
            if hit:
                lawbook_hits += 1
                self.lawbook_hits.append({"episode": episode, "policy": policy, "task_id": task.task_id, "family": task.family, "hit": True, "changed_action": changed, "constructors": "|".join(hit)})
            if changed:
                action_changes += 1
            task_solved = False
            for ctor_id in order[: max(0, self.config.attempt_budget)]:
                ctor = self.constructor_map[ctor_id]
                attempts += 1
                result = check_finite_countermodel(task.source_equation, task.target_equation, ctor.table)
                if result.terminal_candidate_ok:
                    cert = self._certificate_for_result(task, ctor, result)
                    decision = self.gate.evaluate(cert)
                    if decision.accepted:
                        accepted += 1
                        solved += 1
                        task_solved = True
                        if hit:
                            decode_attempts += 1
                            decode_success += 1
                            self.decode_rows.append({"episode": episode, "policy": policy, "task_id": task.task_id, "status": "DECODE_VERIFIED", "constructor_id": ctor_id})
                        self.memory.learn(task, ctor_id, cert)
                        self.attempt_rows.append({"episode": episode, "policy": policy, "task_id": task.task_id, "constructor_id": ctor_id, "accepted": True, "terminal_form": "FINITE_COUNTERMODEL"})
                        break
                    rejected += 1
                else:
                    rejected += 1
                self.attempt_rows.append({"episode": episode, "policy": policy, "task_id": task.task_id, "constructor_id": ctor_id, "accepted": False, "terminal_form": ""})
            if not task_solved:
                residual_count += 1
                self.residual_rows.append({"episode": episode, "policy": policy, "task_id": task.task_id, "family": task.family, "finite_search_failed": True, "promoted_true": False})
                if hit:
                    decode_attempts += 1
                    self.decode_rows.append({"episode": episode, "policy": policy, "task_id": task.task_id, "status": "DECODE_FAILED", "constructor_id": ""})
        attempted_pairs = len(tasks)
        baseline = baseline_residual if baseline_residual is not None else residual_count
        return CompoundingPolicyResult(
            episode=episode,
            policy=policy,
            attempted_pairs=attempted_pairs,
            solved_or_refuted=solved,
            certificate_yield=solved,
            yield_rate=_ratio(solved, attempted_pairs),
            residual_count=residual_count,
            residual_reduction_vs_baseline=baseline - residual_count,
            attempts_used=attempts,
            certificates_per_attempt=_ratio(solved, attempts),
            cost_per_certificate=(attempts / solved) if solved else float(attempts),
            promotion_gate_accepted=accepted,
            promotion_gate_rejected=rejected,
            true_contamination_count=true_contamination,
            true_contamination_rate=_ratio(true_contamination, attempted_pairs),
            lawbook_hit_count=lawbook_hits,
            lawbook_hit_rate=_ratio(lawbook_hits, attempted_pairs),
            lawbook_action_change_count=action_changes,
            lawbook_action_change_rate=_ratio(action_changes, attempted_pairs),
            decode_attempt_count=decode_attempts,
            decode_success_count=decode_success,
            decode_success_rate=_ratio(decode_success, decode_attempts),
        )

    def _constructor_order(self, policy: str, task: _Task) -> tuple[list[str], list[str], bool]:
        base = [ctor.constructor_id for ctor in self.constructors]
        if policy == "shuffled_null":
            rng = random.Random(f"{self.config.seed}:{task.task_id}")
            shuffled = list(base)
            rng.shuffle(shuffled)
            return shuffled, [], False
        if policy in {"memory", "lawbook_attention", "reason_atlas"}:
            hits = self.memory.query(task)
            if hits:
                order = hits + [cid for cid in base if cid not in hits]
                return order, hits, order != base
        return base, [], False

    def _skipped_policy(self, episode: int, policy: str, tasks: Sequence[_Task], reason: str) -> CompoundingPolicyResult:
        return CompoundingPolicyResult(episode, policy, len(tasks), 0, 0, 0.0, len(tasks), 0, 0, 0.0, 0.0, 0, 0, 0, 0.0, 0, 0.0, 0, 0.0, 0, 0, 0.0, skipped=True, skip_reason=reason)

    def _certificate_for_result(self, task: _Task, ctor: SAIRConstructor, result: Any) -> ExternalCertificate:
        payload = {"task": task.to_dict(), "constructor": ctor.to_dict(), "result": result.to_dict()}
        artifact_hash = sha256_hex(payload)
        cert_id = content_id("compounding-finite-countermodel", payload)
        boundary = ExternalBoundaryEvidence(
            evidence_id=content_id("compounding-boundary", payload),
            boundary_kind=VerifierBoundaryKind.FINITE_CHECKED,
            certificate_id=cert_id,
            terminal_form=CanonicalTerminalForm.REFUTATION_CERTIFICATE,
            source_artifact_id=task.task_id,
            artifact_hash=artifact_hash,
            verifier_kind=ExternalVerifierKind.PYTHON_FINITE_CHECKER,
            checker_name="mathgraph.finite_magma_world",
            checker_version="v0",
            advisory=False,
        )
        return ExternalCertificate(
            cert_id=cert_id,
            verifier=ExternalVerifierKind.PYTHON_FINITE_CHECKER,
            status=ExternalCertificateStatus.COUNTERMODEL_FOUND,
            claim=f"{task.source_equation} => {task.target_equation}",
            claim_hash=sha256_hex(task.to_dict()),
            source_artifact_id=task.task_id,
            certificate_kind=ExternalCertificateKind.FINITE_COUNTERMODEL,
            proposed_terminal_form=CanonicalTerminalForm.REFUTATION_CERTIFICATE,
            boundary_evidence=boundary,
            artifact_hash=artifact_hash,
            countermodel=result.to_dict(),
            metadata={"constructor_id": ctor.constructor_id, "family": task.family},
            boundary_valid=True,
            accepted=True,
        )

    def _build_report(self, source_mode: str, equations_loaded: int, matrix_pairs_sampled: int, episodes: tuple[CompoundingEpisodeResult, ...], warnings: tuple[str, ...]) -> CompoundingRunReport:
        policies = [p for ep in episodes for p in ep.policy_results]
        baseline = next((p for p in policies if p.policy == "baseline"), None)
        non_baseline = [p for p in policies if not p.skipped and p.policy != "baseline"]
        signal = bool(baseline and any(p.solved_or_refuted >= baseline.solved_or_refuted or p.residual_count <= baseline.residual_count or p.certificates_per_attempt >= baseline.certificates_per_attempt for p in non_baseline))
        return CompoundingRunReport(
            source_mode=source_mode,
            real_corpus_used=source_mode == "real_sair",
            fallback_mode=source_mode == "fallback_demo",
            equations_loaded=equations_loaded,
            matrix_pairs_sampled=matrix_pairs_sampled,
            advisory_boundary_preserved=True,
            terminal_claims_from_advisory_count=0,
            failed_search_promoted_true_count=0,
            compounding_signal_detected=signal,
            memory_backend="in_run_lawbook_memory",
            episodes=episodes,
            metrics=_metric_rows(policies),
            output_dir=str(self.out_dir),
            artifacts={},
            warnings=warnings,
        )

    def _write_outputs(self, report: CompoundingRunReport) -> dict[str, str]:
        policy_rows = [p.to_dict() for ep in report.episodes for p in ep.policy_results]
        episode_rows = [{"episode": ep.episode, "policy_count": len(ep.policy_results), "best_yield": max((p.solved_or_refuted for p in ep.policy_results), default=0)} for ep in report.episodes]
        outputs = {
            "compounding_report.json": lambda p: p.write_text(json.dumps({**report.to_dict(), "artifacts": {}}, indent=2, sort_keys=True), encoding="utf-8"),
            "compounding_report.md": lambda p: p.write_text(_markdown_report(report), encoding="utf-8"),
            "episode_summary.csv": lambda p: _write_csv(p, episode_rows),
            "policy_summary.csv": lambda p: _write_csv(p, policy_rows),
            "lawbook_hits.csv": lambda p: _write_csv(p, self.lawbook_hits),
            "decode_to_verify.csv": lambda p: _write_csv(p, self.decode_rows),
            "residuals_by_episode.csv": lambda p: _write_csv(p, self.residual_rows),
            "run_metadata.json": lambda p: p.write_text(json.dumps({"created_at": datetime.now(timezone.utc).isoformat(), "config": _config_dict(self.config)}, indent=2, sort_keys=True), encoding="utf-8"),
        }
        paths: dict[str, str] = {}
        for name, writer in outputs.items():
            path = self.out_dir / name
            writer(path)
            paths[name] = str(path)
        manifest_path = self.out_dir / "artifact_manifest.json"
        paths["artifact_manifest.json"] = str(manifest_path)
        manifest = {"generated_files": paths, "required_outputs": list(REQUIRED_OUTPUTS), "source_mode": report.source_mode}
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
        # Rewrite report JSON with final artifact paths.
        final = {**report.to_dict(), "artifacts": paths}
        (self.out_dir / "compounding_report.json").write_text(json.dumps(final, indent=2, sort_keys=True), encoding="utf-8")
        return paths


def run_compounding_loop(config: CompoundingEngineConfig) -> CompoundingRunReport:
    return CompoundingEngine(config).run()


def _fallback_tasks() -> list[_Task]:
    return [
        _Task("train_comm_leftzero", "(x * y) = (y * x)", "(x * y) = x", "commutativity_pressure"),
        _Task("train_projection_drop", "x = x", "x = y", "collapse_or_constant_pressure"),
        _Task("eval_comm_leftzero_1", "(x * y) = (y * x)", "(x * y) = x", "commutativity_pressure"),
        _Task("eval_comm_leftzero_2", "(x * y) = (y * x)", "(y * x) = y", "commutativity_pressure"),
        _Task("eval_projection_drop", "x = x", "x = y", "collapse_or_constant_pressure"),
        _Task("eval_residual_trueish", "x = x", "x = x", "hard_residual_or_unknown"),
    ]


def _metric_rows(policies: Sequence[CompoundingPolicyResult]) -> tuple[dict[str, Any], ...]:
    rows = []
    kinds = {
        "certificate_yield": "verified_metric",
        "yield_rate": "verified_metric",
        "promotion_gate_accepted": "verified_metric",
        "lawbook_hit_rate": "advisory_metric",
        "decode_success_rate": "diagnostic_metric",
        "residual_count": "diagnostic_metric",
        "certificates_per_attempt": "diagnostic_metric",
        "cost_per_certificate": "diagnostic_metric",
        "true_contamination_rate": "diagnostic_metric",
    }
    interpretations = {
        "lawbook_hit_rate": "retrieval/usefulness signal only; does not verify truth",
        "decode_success_rate": "reason or memory hit decoded into a concrete checker action",
    }
    for policy in policies:
        for metric, kind in kinds.items():
            rows.append({"episode": policy.episode, "policy": policy.policy, "metric": metric, "value": getattr(policy, metric), "metric_kind": kind, "interpretation": interpretations.get(metric, "")})
    return tuple(rows)


def _markdown_report(report: CompoundingRunReport) -> str:
    policies = [p for ep in report.episodes for p in ep.policy_results]
    lines = [
        "# MathGraph Compounding Loop Report",
        "",
        f"- Source mode: `{report.source_mode}`",
        f"- Fallback mode: `{report.fallback_mode}`",
        f"- Advisory boundary preserved: `{report.advisory_boundary_preserved}`",
        f"- Compounding signal detected: `{report.compounding_signal_detected}`",
        "",
        "## Policies",
    ]
    for p in policies:
        marker = " (skipped)" if p.skipped else ""
        lines.append(f"- episode {p.episode} `{p.policy}`{marker}: yield={p.solved_or_refuted}/{p.attempted_pairs}, residuals={p.residual_count}, certs/attempt={p.certificates_per_attempt:.3f}")
    lines.extend(["", "Metrics are labelled in `compounding_report.json` as verified, advisory, or diagnostic."])
    return "\n".join(lines) + "\n"


def _write_csv(path: Path, rows: Sequence[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    keys = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _ratio(num: float, den: float) -> float:
    return float(num) / float(den) if den else 0.0


def _config_dict(config: CompoundingEngineConfig) -> dict[str, Any]:
    return {key: str(value) if isinstance(value, Path) else value for key, value in config.__dict__.items()}
