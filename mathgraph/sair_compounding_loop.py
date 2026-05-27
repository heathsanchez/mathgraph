"""SAIR-specific compounding loop over canonical evidence-pack memory.

This module specializes the lightweight compounding lawbook spine for
SAIR/ETP-style implication rows.  It never runs the full ETP benchmark and it
never upgrades advisory routes into terminal truth.  Real ETP mode only samples
a small bounded set of matrix-labelled pairs for route evaluation.
"""

from __future__ import annotations

import csv
import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from mathgraph.compounding_lawbook_engine import LawbookViewEntry, build_lawbook_view


@dataclass(frozen=True)
class SairTaskRow:
    task_id: str
    source_id: int
    target_id: int
    source_equation: str
    target_equation: str
    matrix_label: str
    route: str
    certificate_status: str
    advisory_boundary_status: str
    terms: tuple[str, ...] = field(default_factory=tuple)
    finite_checked_witness: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "source_equation": self.source_equation,
            "target_equation": self.target_equation,
            "matrix_label": self.matrix_label,
            "route": self.route,
            "certificate_status": self.certificate_status,
            "advisory_boundary_status": self.advisory_boundary_status,
            "terms": list(self.terms),
            "finite_checked_witness": self.finite_checked_witness,
        }


@dataclass(frozen=True)
class SairCompoundingReport:
    mode: str
    task_count: int
    lawbook_hit_rate: float
    action_change_rate: float
    decode_supported_rate: float
    candidate_certificate_count: int
    verified_certificate_count: int
    residual_reduction_proxy: float
    prohibited_promotion_count: int
    advisory_boundary_ok: bool
    failed_search_promoted_to_true_count: int
    outputs: dict[str, str] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "task_count": self.task_count,
            "lawbook_hit_rate": self.lawbook_hit_rate,
            "action_change_rate": self.action_change_rate,
            "decode_supported_rate": self.decode_supported_rate,
            "candidate_certificate_count": self.candidate_certificate_count,
            "verified_certificate_count": self.verified_certificate_count,
            "residual_reduction_proxy": self.residual_reduction_proxy,
            "prohibited_promotion_count": self.prohibited_promotion_count,
            "advisory_boundary_ok": self.advisory_boundary_ok,
            "failed_search_promoted_to_true_count": self.failed_search_promoted_to_true_count,
            "outputs": dict(self.outputs),
            "metrics": dict(self.metrics),
            "metadata": dict(self.metadata),
        }


def run_sair_compounding_loop(
    out_dir: str | Path,
    *,
    fallback_demo: bool = False,
    equations_path: str | Path | None = None,
    matrix_path: str | Path | None = None,
    seed: int = 1729,
    sample_size: int = 12,
) -> SairCompoundingReport:
    """Run the SAIR compounding loop in fallback-demo or real-etp-light mode."""

    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    lawbook_view = build_lawbook_view()
    if fallback_demo or not (equations_path and matrix_path):
        mode = "fallback-demo"
        tasks = build_fallback_demo_tasks()
    else:
        mode = "real-etp-light"
        tasks = sample_real_etp_light_tasks(equations_path, matrix_path, seed=seed, sample_size=sample_size)

    policy_rows = evaluate_sair_policies(tasks, lawbook_view)
    task_ledger = _task_ledger(tasks, policy_rows)
    residual_delta = _residual_delta(policy_rows)
    boundary_audit = _boundary_audit(policy_rows)
    metrics = _metrics(policy_rows, residual_delta, boundary_audit, task_count=len(tasks))
    outputs = {
        "report_json": str(output / "sair_compounding_report.json"),
        "report_md": str(output / "sair_compounding_report.md"),
        "policy_eval": str(output / "sair_policy_eval.csv"),
        "task_ledger": str(output / "sair_task_ledger.csv"),
        "residual_delta": str(output / "sair_residual_delta.csv"),
        "boundary_audit": str(output / "sair_boundary_audit.csv"),
    }
    report = SairCompoundingReport(
        mode=mode,
        task_count=len(tasks),
        lawbook_hit_rate=float(metrics["lawbook_hit_rate"]),
        action_change_rate=float(metrics["action_change_rate"]),
        decode_supported_rate=float(metrics["decode_supported_rate"]),
        candidate_certificate_count=int(metrics["candidate_certificate_count"]),
        verified_certificate_count=int(metrics["verified_certificate_count"]),
        residual_reduction_proxy=float(metrics["residual_reduction_proxy"]),
        prohibited_promotion_count=int(metrics["prohibited_promotion_count"]),
        advisory_boundary_ok=bool(metrics["advisory_boundary_ok"]),
        failed_search_promoted_to_true_count=int(metrics["failed_search_promoted_to_true_count"]),
        outputs=outputs,
        metrics=metrics,
        metadata={
            "seed": seed,
            "sample_size": sample_size,
            "trust_boundary": "routes_are_advisory_until_finite_witness_or_proof_verifier_accepts",
            "lawbook_pack_count": len(lawbook_view),
        },
    )
    _write_csv(output / "sair_policy_eval.csv", policy_rows)
    _write_csv(output / "sair_task_ledger.csv", task_ledger)
    _write_csv(output / "sair_residual_delta.csv", residual_delta)
    _write_csv(output / "sair_boundary_audit.csv", boundary_audit)
    (output / "sair_compounding_report.json").write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    (output / "sair_compounding_report.md").write_text(_markdown(report), encoding="utf-8")
    return report


def build_fallback_demo_tasks() -> tuple[SairTaskRow, ...]:
    return (
        SairTaskRow(
            task_id="sair_demo_false_checked",
            source_id=1,
            target_id=2,
            source_equation="x*x=x",
            target_equation="x*y=y*x",
            matrix_label="FALSE",
            route="finite_countermodel_replay",
            certificate_status="finite_checked_false_certificate",
            advisory_boundary_status="verified_countermodel_only",
            terms=("sair", "finite", "countermodel", "certificate"),
            finite_checked_witness=True,
        ),
        SairTaskRow(
            task_id="sair_demo_true_route_candidate",
            source_id=3,
            target_id=4,
            source_equation="x*y=x",
            target_equation="(x*y)*z=x",
            matrix_label="TRUE",
            route="proof_route_candidate",
            certificate_status="unverified_true_candidate",
            advisory_boundary_status="requires_proof_verifier",
            terms=("sair", "proof", "true", "candidate"),
        ),
        SairTaskRow(
            task_id="sair_demo_residual_frontier",
            source_id=5,
            target_id=6,
            source_equation="(x*y)*y=x",
            target_equation="x*(y*y)=x",
            matrix_label="FALSE",
            route="minimum_carrier_search",
            certificate_status="named_obstruction_needed",
            advisory_boundary_status="failed_search_not_true",
            terms=("residual", "frontier", "carrier", "semantic"),
        ),
        SairTaskRow(
            task_id="sair_demo_recursive_route",
            source_id=7,
            target_id=8,
            source_equation="x*(y*z)=(x*y)*z",
            target_equation="x*y=x",
            matrix_label="FALSE",
            route="advisory_route_memory",
            certificate_status="countermodel_candidate_unchecked",
            advisory_boundary_status="advisory_only",
            terms=("recursive", "route", "memory", "etp"),
        ),
        SairTaskRow(
            task_id="sair_demo_crossworld_route",
            source_id=9,
            target_id=10,
            source_equation="x*(x*y)=x*y",
            target_equation="x*y=y",
            matrix_label="UNKNOWN",
            route="semantic_residual_route",
            certificate_status="residual_route_candidate",
            advisory_boundary_status="crossworld_advisory_only",
            terms=("crossworld", "semantic", "residual", "rank"),
        ),
    )


def sample_real_etp_light_tasks(
    equations_path: str | Path,
    matrix_path: str | Path,
    *,
    seed: int = 1729,
    sample_size: int = 12,
) -> tuple[SairTaskRow, ...]:
    """Sample a bounded reproducible TRUE/FALSE set from real ETP assets."""

    import numpy as np

    equations = [line.strip() for line in Path(equations_path).read_text(encoding="utf-8").splitlines() if line.strip()]
    matrix = np.load(matrix_path, mmap_mode="r")
    if matrix.shape[0] != len(equations) or matrix.shape[1] != len(equations):
        raise ValueError(f"Matrix shape {matrix.shape} does not match {len(equations)} equations")
    rng = random.Random(seed)
    true_pairs: list[tuple[int, int]] = []
    false_pairs: list[tuple[int, int]] = []
    target_each = max(1, sample_size // 2)
    attempts = 0
    while (len(true_pairs) < target_each or len(false_pairs) < target_each) and attempts < sample_size * 5000:
        attempts += 1
        source = rng.randrange(len(equations))
        target = rng.randrange(len(equations))
        if source == target:
            continue
        label = bool(matrix[source, target])
        pair = (source, target)
        if label and len(true_pairs) < target_each and pair not in true_pairs:
            true_pairs.append(pair)
        elif not label and len(false_pairs) < target_each and pair not in false_pairs:
            false_pairs.append(pair)
    selected = false_pairs + true_pairs
    rng.shuffle(selected)
    rows: list[SairTaskRow] = []
    for idx, (source, target) in enumerate(selected[:sample_size]):
        label = "TRUE" if bool(matrix[source, target]) else "FALSE"
        rows.append(
            SairTaskRow(
                task_id=f"real_etp_light_{idx:04d}",
                source_id=source,
                target_id=target,
                source_equation=equations[source],
                target_equation=equations[target],
                matrix_label=label,
                route="sampled_matrix_route",
                certificate_status="proof_route_candidate" if label == "TRUE" else "countermodel_candidate_unchecked",
                advisory_boundary_status="sample_label_is_not_certificate",
                terms=("sair", "etp", "recursive" if label == "FALSE" else "proof"),
            )
        )
    return tuple(rows)


def evaluate_sair_policies(tasks: Sequence[SairTaskRow], lawbook_view: Sequence[LawbookViewEntry]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for task in tasks:
        entry, score = _best_attention(task, lawbook_view)
        lawbook_action = _lawbook_action(task, entry)
        decode_action = _decode_filtered_action(task, lawbook_action)
        for policy, action in (
            ("baseline_generic", "generic_bounded_finite_search"),
            ("lawbook_attention", lawbook_action),
            ("decode_filtered_lawbook", decode_action),
        ):
            candidate, verified, prohibited, failed_to_true = _certificate_outcome(task, entry, policy, action)
            rows.append(
                {
                    "task_id": task.task_id,
                    "policy": policy,
                    "source_id": task.source_id,
                    "target_id": task.target_id,
                    "matrix_label": task.matrix_label,
                    "route": action,
                    "lawbook_hit": bool(entry and score > 0) if policy != "baseline_generic" else False,
                    "attention_score": score if policy != "baseline_generic" else 0,
                    "evidence_pack_id": entry.evidence_pack_id if entry and policy != "baseline_generic" else "",
                    "action_changed": action != "generic_bounded_finite_search",
                    "decode_supported": _decode_supported(action),
                    "candidate_certificate": candidate,
                    "verified_certificate": verified,
                    "certificate_status": task.certificate_status,
                    "advisory_boundary_status": "PASS" if not prohibited and not failed_to_true else "FAIL",
                    "prohibited_promotion": prohibited,
                    "failed_search_promoted_to_true": failed_to_true,
                }
            )
    return rows


def _task_ledger(tasks: Sequence[SairTaskRow], policy_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    best_by_task = {
        str(row["task_id"]): row
        for row in policy_rows
        if row.get("policy") == "decode_filtered_lawbook"
    }
    ledger = []
    for task in tasks:
        best = best_by_task.get(task.task_id, {})
        row = task.to_dict()
        row.update(
            {
                "selected_policy": "decode_filtered_lawbook",
                "selected_route": best.get("route", task.route),
                "selected_certificate_status": best.get("certificate_status", task.certificate_status),
                "selected_advisory_boundary_status": best.get("advisory_boundary_status", task.advisory_boundary_status),
            }
        )
        ledger.append(row)
    return ledger


def _residual_delta(policy_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for row in policy_rows:
        grouped.setdefault(str(row["policy"]), []).append(row)
    baseline_candidates = sum(1 for row in grouped.get("baseline_generic", []) if row.get("candidate_certificate"))
    out = []
    for policy, rows in grouped.items():
        candidates = sum(1 for row in rows if row.get("candidate_certificate"))
        verified = sum(1 for row in rows if row.get("verified_certificate"))
        out.append(
            {
                "policy": policy,
                "tasks": len(rows),
                "candidate_certificate_count": candidates,
                "verified_certificate_count": verified,
                "residual_reduction_proxy": max(0, candidates - baseline_candidates),
            }
        )
    return out


def _boundary_audit(policy_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in policy_rows:
        reason = "ok"
        if row.get("prohibited_promotion"):
            reason = "prohibited_promotion"
        elif row.get("failed_search_promoted_to_true"):
            reason = "failed_search_promoted_to_true"
        rows.append(
            {
                "task_id": row.get("task_id", ""),
                "policy": row.get("policy", ""),
                "matrix_label": row.get("matrix_label", ""),
                "route": row.get("route", ""),
                "advisory_boundary_ok": not row.get("prohibited_promotion") and not row.get("failed_search_promoted_to_true"),
                "failed_search_promoted_to_true": bool(row.get("failed_search_promoted_to_true")),
                "prohibited_promotion": bool(row.get("prohibited_promotion")),
                "reason": reason,
            }
        )
    return rows


def _metrics(
    policy_rows: Sequence[Mapping[str, Any]],
    residual_delta: Sequence[Mapping[str, Any]],
    boundary_audit: Sequence[Mapping[str, Any]],
    *,
    task_count: int,
) -> dict[str, Any]:
    non_baseline = [row for row in policy_rows if row.get("policy") != "baseline_generic"]
    decode_rows = [row for row in policy_rows if row.get("policy") == "decode_filtered_lawbook"]
    hits = sum(1 for row in non_baseline if row.get("lawbook_hit"))
    changes = sum(1 for row in non_baseline if row.get("action_changed"))
    decode_supported = sum(1 for row in decode_rows if row.get("decode_supported"))
    candidates = sum(1 for row in decode_rows if row.get("candidate_certificate"))
    verified = sum(1 for row in decode_rows if row.get("verified_certificate"))
    prohibited = sum(1 for row in boundary_audit if row.get("prohibited_promotion"))
    failed_to_true = sum(1 for row in boundary_audit if row.get("failed_search_promoted_to_true"))
    residual_proxy = max((float(row.get("residual_reduction_proxy", 0.0) or 0.0) for row in residual_delta), default=0.0)
    return {
        "lawbook_hit_rate": hits / len(non_baseline) if non_baseline else 0.0,
        "action_change_rate": changes / len(non_baseline) if non_baseline else 0.0,
        "decode_supported_rate": decode_supported / len(decode_rows) if decode_rows else 0.0,
        "candidate_certificate_count": candidates,
        "verified_certificate_count": verified,
        "residual_reduction_proxy": residual_proxy,
        "prohibited_promotion_count": prohibited,
        "advisory_boundary_ok": prohibited == 0 and failed_to_true == 0,
        "failed_search_promoted_to_true_count": failed_to_true,
        "task_count": task_count,
    }


def _best_attention(task: SairTaskRow, entries: Sequence[LawbookViewEntry]) -> tuple[LawbookViewEntry | None, int]:
    terms = {term.lower() for term in task.terms}
    if task.matrix_label == "FALSE":
        terms |= {"sair", "finite"}
    best: tuple[LawbookViewEntry | None, int] = (None, 0)
    for entry in entries:
        score = len(terms & set(entry.attention_terms))
        if score > best[1]:
            best = (entry, score)
    return best


def _lawbook_action(task: SairTaskRow, entry: LawbookViewEntry | None) -> str:
    if task.matrix_label == "TRUE":
        return "proof_route_candidate_requires_verifier"
    if entry is None:
        return "generic_bounded_finite_search"
    if entry.evidence_pack_id == "sair_stage2_breakthrough_20260526":
        return "request_finite_countermodel_checker"
    if entry.evidence_pack_id == "recursive_residual_transfer_v1_20260523":
        return "use_recursive_route_memory_then_request_finite_checker"
    if entry.evidence_pack_id == "residual_obstruction_atlas_v8_4":
        return "minimum_carrier_semantic_universe_search"
    if entry.evidence_pack_id == "cross_world_semantic_residual_invariant":
        return "semantic_residual_extraction_then_verifier_route"
    return "generic_bounded_finite_search"


def _decode_filtered_action(task: SairTaskRow, action: str) -> str:
    if task.matrix_label == "TRUE" and "countermodel" in action:
        return "proof_route_candidate_requires_verifier"
    if "failed" in task.certificate_status:
        return "named_obstruction_candidate_failed_search_not_true"
    return action


def _certificate_outcome(
    task: SairTaskRow,
    entry: LawbookViewEntry | None,
    policy: str,
    action: str,
) -> tuple[bool, bool, bool, bool]:
    verified = bool(task.finite_checked_witness and task.matrix_label == "FALSE" and "countermodel" in action)
    candidate = verified or "checker" in action or "countermodel" in action or "verifier" in action or "obstruction" in action
    failed_to_true = "failed_search_to_true" in action or "failed_search_not_true" not in action and "failed" in task.certificate_status and task.matrix_label != "FALSE"
    prohibited = False
    if task.matrix_label == "TRUE" and ("countermodel" in action or verified):
        prohibited = True
    if verified and not task.finite_checked_witness:
        prohibited = True
    if entry and entry.evidence_pack_id != "sair_stage2_breakthrough_20260526" and verified:
        prohibited = True
    if policy == "baseline_generic":
        verified = False
    return candidate, verified, prohibited, failed_to_true


def _decode_supported(action: str) -> bool:
    return any(
        marker in action
        for marker in (
            "checker",
            "verifier",
            "minimum_carrier",
            "semantic_residual",
            "obstruction",
            "proof_route_candidate",
        )
    )


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    keys: list[str] = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _csv_value(row.get(key)) for key in keys})


def _csv_value(value: Any) -> Any:
    if isinstance(value, (dict, list, tuple, set)):
        return json.dumps(value, sort_keys=True, default=str)
    return value


def _markdown(report: SairCompoundingReport) -> str:
    return f"""# SAIR Compounding Lawbook Loop v1

- mode: `{report.mode}`
- task_count: `{report.task_count}`
- lawbook_hit_rate: `{report.lawbook_hit_rate:.3f}`
- action_change_rate: `{report.action_change_rate:.3f}`
- decode_supported_rate: `{report.decode_supported_rate:.3f}`
- candidate_certificate_count: `{report.candidate_certificate_count}`
- verified_certificate_count: `{report.verified_certificate_count}`
- residual_reduction_proxy: `{report.residual_reduction_proxy:.3f}`
- prohibited_promotion_count: `{report.prohibited_promotion_count}`
- failed_search_promoted_to_true_count: `{report.failed_search_promoted_to_true_count}`
- advisory_boundary_ok: `{report.advisory_boundary_ok}`

Finite-checked FALSE countermodels are terminal only when a checked witness is
present. Recursive transfer, residual atlas, and CrossWorld evidence influence
routing only. Failed finite search is never TRUE. Sampled TRUE rows are proof
route candidates until a proof verifier accepts them.

advisory route memory is not truth.
"""
