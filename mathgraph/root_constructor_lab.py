"""Advisory validation lab for root-driven constructor families.

The lab asks whether a root hypothesis is generative: does its basin route
nearby pairs into existing certificate constructors better than a null basin?
It never validates roots as truth. Finite refutations, when found, are produced
through the M0 certificate-factory/importer boundary.
"""

from __future__ import annotations

import json
import random
import re
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

from mathgraph.continuation_traces import ContinuationTrace, ContinuationTraceStore, make_trace_id
from mathgraph.equations import Equation, parse_equation
from mathgraph.m0_certificate_factory import M0EpisodeConfig, run_m0_episode
from mathgraph.terms import Term

ROOT_LABELS = [
    "duplication_repetition_demand_obstruction",
    "new_variable_freedom_obstruction",
    "left_boundary_break_obstruction",
    "right_boundary_break_obstruction",
    "trivialization_escape_obstruction",
]

ROOT_THRESHOLD = 0.45

ROOT_WARNINGS = [
    "Root validation is advisory.",
    "Root recommendations do not verify or refute claims.",
    "Finite countermodels are verified only through the existing M0/importer path.",
    "Finite search failure is not proof.",
]


@dataclass(frozen=True)
class RootHypothesis:
    root_label: str
    description: str
    detector_name: str
    constructor_families: list[str]
    expected_obstruction: str
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RootBasinPair:
    source: str
    target: str
    source_idx: int | None
    target_idx: int | None
    root_label: str
    detector_score: float
    detector_evidence: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ConstructorFamilyResult:
    root_label: str
    constructor_family: str
    attempted: int
    verified_false: int
    constructor_failed: int
    parse_failed: int
    residual: int
    verification_failed: int
    certificate_ids: list[str]
    elapsed_sec: float
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RootValidationResult:
    root_label: str
    candidate_pairs: int
    attempted_pairs: int
    verified_false: int
    constructor_failed: int
    parse_failed: int
    residual: int
    null_attempted_pairs: int
    null_verified_false: int
    basin_purity: float
    null_lift: float
    certificate_yield: float
    residual_compression_gain: float
    constructor_reuse_score: float
    verification_success_rate: float
    root_value_score: float
    recommendation: str
    constructor_results: list[ConstructorFamilyResult]
    warnings: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["constructor_results"] = [result.to_dict() for result in self.constructor_results]
        return payload


@dataclass(frozen=True)
class RootConstructorLabReport:
    run_id: str
    status: str
    results: list[RootValidationResult]
    summary: dict[str, Any]
    outputs: dict[str, str]
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "status": self.status,
            "results": [result.to_dict() for result in self.results],
            "summary": dict(self.summary),
            "outputs": dict(self.outputs),
            "warnings": list(self.warnings),
        }


def default_root_hypotheses() -> list[RootHypothesis]:
    return [
        RootHypothesis(
            root_label="duplication_repetition_demand_obstruction",
            description="Target asks for repeated-variable behavior not forced by the source.",
            detector_name="duplication_repetition_detector",
            constructor_families=[
                "affine_parity_or_repeat_sensitive_countermodel_family",
                "projection_or_boundary_breaking_table_family",
            ],
            expected_obstruction="repeated target demand not carried by source law",
        ),
        RootHypothesis(
            root_label="new_variable_freedom_obstruction",
            description="Target introduces independent variables absent from the source.",
            detector_name="new_variable_freedom_detector",
            constructor_families=[
                "free_variable_separating_countermodel_family",
                "projection_or_boundary_breaking_table_family",
            ],
            expected_obstruction="free target variable can separate in a finite magma",
        ),
        RootHypothesis(
            root_label="left_boundary_break_obstruction",
            description="Source constrains left-boundary behavior while target escapes to the other side.",
            detector_name="left_boundary_break_detector",
            constructor_families=[
                "projection_or_boundary_breaking_table_family",
                "residual_search_family",
            ],
            expected_obstruction="left boundary role is not preserved by the target",
        ),
        RootHypothesis(
            root_label="right_boundary_break_obstruction",
            description="Source constrains right-boundary behavior while target escapes to the other side.",
            detector_name="right_boundary_break_detector",
            constructor_families=[
                "projection_or_boundary_breaking_table_family",
                "residual_search_family",
            ],
            expected_obstruction="right boundary role is not preserved by the target",
        ),
        RootHypothesis(
            root_label="trivialization_escape_obstruction",
            description="A simple or collapsing source is asked to enforce more complex target behavior.",
            detector_name="trivialization_escape_detector",
            constructor_families=[
                "residual_search_family",
                "affine_parity_or_repeat_sensitive_countermodel_family",
            ],
            expected_obstruction="target complexity escapes source trivialization",
        ),
    ]


def score_pair_for_root(source: str, target: str, root_label: str) -> tuple[float, dict[str, Any]]:
    features = _pair_features(source, target)
    if root_label == "duplication_repetition_demand_obstruction":
        return _score_duplication_repetition(features)
    if root_label == "new_variable_freedom_obstruction":
        return _score_new_variable_freedom(features)
    if root_label == "left_boundary_break_obstruction":
        return _score_boundary_break(features, side="left")
    if root_label == "right_boundary_break_obstruction":
        return _score_boundary_break(features, side="right")
    if root_label == "trivialization_escape_obstruction":
        return _score_trivialization_escape(features)
    return 0.0, {"unknown_root_label": root_label, "advisory_only": True}


def detect_root_basin(source: str, target: str) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    for hypothesis in default_root_hypotheses():
        score, evidence = score_pair_for_root(source, target, hypothesis.root_label)
        if score > 0.0:
            signals.append(
                {
                    "root_label": hypothesis.root_label,
                    "detector_score": score,
                    "detector_evidence": evidence,
                    "advisory_only": True,
                }
            )
    return sorted(signals, key=lambda row: (-float(row["detector_score"]), row["root_label"]))


def run_root_constructor_lab(
    pairs: Iterable[dict[str, Any]],
    out_dir: str,
    *,
    root_labels: list[str] | None = None,
    max_pairs_per_root: int = 50,
    null_pairs_per_root: int = 50,
    max_countermodel_order: int = 3,
    random_seed: int = 0,
    trace_store_path: str | None = None,
) -> RootConstructorLabReport:
    started = time.perf_counter()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    run_id = f"root_lab_{int(time.time() * 1000)}"
    pair_rows = [_normalize_pair(row) for row in pairs]
    selected_labels = list(root_labels or ROOT_LABELS)
    hypotheses = {item.root_label: item for item in default_root_hypotheses()}
    for label in selected_labels:
        if label not in hypotheses:
            hypotheses[label] = RootHypothesis(
                root_label=label,
                description="User-provided root label.",
                detector_name="user_label_detector",
                constructor_families=["residual_search_family"],
                expected_obstruction="unknown user-provided basin",
                notes="No built-in detector; pairs require explicit root_label matches.",
            )

    basin_rows_by_root: dict[str, list[RootBasinPair]] = defaultdict(list)
    for row in pair_rows:
        for label in selected_labels:
            score, evidence = score_pair_for_root(row["source"], row["target"], label)
            if row.get("root_label") == label:
                score = max(score, float(row.get("detector_score", ROOT_THRESHOLD)))
                evidence = {**evidence, "explicit_root_label": True}
            if score >= ROOT_THRESHOLD:
                basin_rows_by_root[label].append(
                    RootBasinPair(
                        source=row["source"],
                        target=row["target"],
                        source_idx=row.get("source_idx"),
                        target_idx=row.get("target_idx"),
                        root_label=label,
                        detector_score=round(score, 6),
                        detector_evidence=evidence,
                    )
                )

    all_basin_rows = [item for rows in basin_rows_by_root.values() for item in rows]
    _write_jsonl([row.to_dict() for row in all_basin_rows], out / "root_basin_pairs.jsonl")

    rng = random.Random(random_seed)
    results: list[RootValidationResult] = []
    constructor_output_rows: list[dict[str, Any]] = []
    verified_output_rows: list[dict[str, Any]] = []
    for label in selected_labels:
        hypothesis = hypotheses[label]
        basin = sorted(
            basin_rows_by_root.get(label, []),
            key=lambda item: (-item.detector_score, item.source_idx if item.source_idx is not None else 10**9, item.target_idx if item.target_idx is not None else 10**9, item.source, item.target),
        )
        selected = basin[: max(0, max_pairs_per_root)]
        null_rows = _select_null_rows(pair_rows, selected, label, null_pairs_per_root, rng)
        constructor_results: list[ConstructorFamilyResult] = []
        for family in hypothesis.constructor_families:
            family_result, verified_rows = _run_family(
                run_id=run_id,
                root_label=label,
                family=family,
                pairs=[item.to_dict() for item in selected],
                out_dir=out,
                max_countermodel_order=max_countermodel_order,
                trace_store_path=trace_store_path,
                basin_label="root_basin",
            )
            constructor_results.append(family_result)
            constructor_output_rows.append(family_result.to_dict())
            verified_output_rows.extend(verified_rows)

        null_verified_false = 0
        if null_rows:
            null_result, _ = _run_family(
                run_id=run_id,
                root_label=label,
                family="null_comparison_family",
                pairs=null_rows,
                out_dir=out,
                max_countermodel_order=max_countermodel_order,
                trace_store_path=trace_store_path,
                basin_label="null_comparison",
            )
            null_verified_false = null_result.verified_false
            constructor_output_rows.append(null_result.to_dict())

        result = _root_validation_result(
            hypothesis=hypothesis,
            candidate_pairs=len(basin),
            selected=selected,
            constructor_results=constructor_results,
            null_attempted=len(null_rows),
            null_verified_false=null_verified_false,
        )
        results.append(result)

    _write_jsonl(constructor_output_rows, out / "constructor_results.jsonl")
    _write_jsonl(verified_output_rows, out / "verified_certificates.jsonl")
    results = sorted(results, key=lambda item: (-item.root_value_score, item.root_label))
    summary = _summary(run_id, pair_rows, results, time.perf_counter() - started)
    outputs = {
        "root_constructor_lab_report_json": str(out / "root_constructor_lab_report.json"),
        "root_constructor_lab_report_md": str(out / "root_constructor_lab_report.md"),
        "root_basin_pairs_jsonl": str(out / "root_basin_pairs.jsonl"),
        "constructor_results_jsonl": str(out / "constructor_results.jsonl"),
        "verified_certificates_jsonl": str(out / "verified_certificates.jsonl"),
    }
    if trace_store_path:
        outputs["continuation_traces_jsonl"] = trace_store_path
    report = RootConstructorLabReport(
        run_id=run_id,
        status="completed",
        results=results,
        summary=summary,
        outputs=outputs,
        warnings=list(ROOT_WARNINGS),
    )
    _write_json(report.to_dict(), out / "root_constructor_lab_report.json")
    _write_report_md(report, hypotheses, out / "root_constructor_lab_report.md")
    return report


def _run_family(
    *,
    run_id: str,
    root_label: str,
    family: str,
    pairs: list[dict[str, Any]],
    out_dir: Path,
    max_countermodel_order: int,
    trace_store_path: str | None = None,
    basin_label: str = "root_basin",
) -> tuple[ConstructorFamilyResult, list[dict[str, Any]]]:
    started = time.perf_counter()
    safe_root = _safe_name(root_label)
    safe_family = _safe_name(family)
    family_dir = out_dir / "m0_runs" / safe_root / safe_family
    family_dir.mkdir(parents=True, exist_ok=True)
    pairs_path = family_dir / "pairs.jsonl"
    report_path = family_dir / "m0_report.json"
    ledger_path = family_dir / "m0_ledger.jsonl"
    store_path = family_dir / "lawbook.sqlite"
    _write_jsonl([_m0_pair(row) for row in pairs], pairs_path)
    order = _family_max_order(family, max_countermodel_order)
    if pairs:
        episode = run_m0_episode(
            M0EpisodeConfig(
                pairs_jsonl=str(pairs_path),
                store_path=str(store_path),
                ledger_jsonl=str(ledger_path),
                report_json=str(report_path),
                episode_id=f"{run_id}_{safe_root}_{safe_family}",
                max_countermodel_order=order,
                exhaustive_order_limit=min(order, 3),
                random_tables_per_order=0,
                allow_construction=True,
            )
        )
        results = episode.results
    else:
        results = []
    if trace_store_path:
        traces = [
            _trace_from_m0_result(
                run_id=run_id,
                root_label=root_label,
                family=family,
                basin_label=basin_label,
                pair=pairs[index],
                result=result,
                constructor_config={"max_countermodel_order": order, "family": family},
            )
            for index, result in enumerate(results)
        ]
        ContinuationTraceStore(trace_store_path).append_many(traces)
    cert_ids = sorted({result.certificate_id for result in results if result.certificate_id})
    verified_rows = [
        {
            "root_label": root_label,
            "constructor_family": family,
            "certificate_id": result.certificate_id,
            "source": result.source,
            "target": result.target,
            "source_idx": result.source_idx,
            "target_idx": result.target_idx,
            "terminal_form": result.terminal_form,
            "trust_level": result.trust_level,
            "verifier_boundary": result.verifier_boundary,
        }
        for result in results
        if result.status == "VERIFIED_FALSE" and result.certificate_id
    ]
    return (
        ConstructorFamilyResult(
            root_label=root_label,
            constructor_family=family,
            attempted=len(pairs),
            verified_false=sum(1 for result in results if result.status == "VERIFIED_FALSE"),
            constructor_failed=sum(1 for result in results if result.status == "CONSTRUCTOR_FAILED"),
            parse_failed=sum(1 for result in results if result.status == "PARSE_FAILED"),
            residual=sum(1 for result in results if result.status in {"RESIDUAL", "ERROR"}),
            verification_failed=sum(1 for result in results if result.status == "VERIFICATION_FAILED"),
            certificate_ids=cert_ids,
            elapsed_sec=round(time.perf_counter() - started, 6),
            evidence={
                "advisory_family_wrapper": True,
                "m0_store_path": str(store_path),
                "m0_report_path": str(report_path),
                "max_countermodel_order": order,
                "truth_boundary": "M0 importer decides finite refutations.",
            },
        ),
        verified_rows,
    )


def _root_validation_result(
    *,
    hypothesis: RootHypothesis,
    candidate_pairs: int,
    selected: list[RootBasinPair],
    constructor_results: list[ConstructorFamilyResult],
    null_attempted: int,
    null_verified_false: int,
) -> RootValidationResult:
    attempted_pairs = len(selected)
    raw_verified_false = sum(result.verified_false for result in constructor_results)
    verified_false = min(raw_verified_false, attempted_pairs)
    constructor_failed = sum(result.constructor_failed for result in constructor_results)
    parse_failed = sum(result.parse_failed for result in constructor_results)
    residual = sum(result.residual for result in constructor_results)
    verification_failed = sum(result.verification_failed for result in constructor_results)
    certificate_yield = verified_false / max(attempted_pairs, 1)
    null_yield = null_verified_false / max(null_attempted, 1)
    null_lift = certificate_yield - null_yield
    basin_purity = sum(1 for item in selected if item.detector_score >= ROOT_THRESHOLD) / max(attempted_pairs, 1)
    residual_compression_gain = verified_false / max(candidate_pairs, 1)
    attempted_families = len(constructor_results)
    constructor_reuse_score = sum(1 for item in constructor_results if item.verified_false > 0) / max(
        attempted_families, 1
    )
    verification_success_rate = verified_false / max(verified_false + verification_failed + constructor_failed, 1)
    root_value_score = (
        certificate_yield
        * max(null_lift, 0.0)
        * max(basin_purity, 0.0)
        * max(residual_compression_gain, 0.0)
        * max(constructor_reuse_score, 0.0)
        * max(verification_success_rate, 0.0)
    )
    additive = (
        certificate_yield
        + null_lift
        + basin_purity
        + residual_compression_gain
        + constructor_reuse_score
        + verification_success_rate
    )
    recommendation = _recommend(
        attempted_pairs=attempted_pairs,
        verified_false=verified_false,
        null_lift=null_lift,
        constructor_reuse_score=constructor_reuse_score,
        root_value_score=root_value_score,
        candidate_pairs=candidate_pairs,
        constructor_failed=constructor_failed,
        residual=residual,
    )
    return RootValidationResult(
        root_label=hypothesis.root_label,
        candidate_pairs=candidate_pairs,
        attempted_pairs=attempted_pairs,
        verified_false=verified_false,
        constructor_failed=constructor_failed,
        parse_failed=parse_failed,
        residual=residual,
        null_attempted_pairs=null_attempted,
        null_verified_false=null_verified_false,
        basin_purity=round(basin_purity, 6),
        null_lift=round(null_lift, 6),
        certificate_yield=round(certificate_yield, 6),
        residual_compression_gain=round(residual_compression_gain, 6),
        constructor_reuse_score=round(constructor_reuse_score, 6),
        verification_success_rate=round(verification_success_rate, 6),
        root_value_score=round(root_value_score, 6),
        recommendation=recommendation,
        constructor_results=constructor_results,
        warnings=list(ROOT_WARNINGS),
        evidence={
            "advisory_only": True,
            "not_verified_root_truth": True,
            "root_value_additive": round(additive, 6),
            "raw_constructor_verified_false": raw_verified_false,
            "threshold": ROOT_THRESHOLD,
            "detector_name": hypothesis.detector_name,
            "constructor_families": list(hypothesis.constructor_families),
            "selected_detector_scores": [item.detector_score for item in selected],
        },
    )


def _trace_from_m0_result(
    *,
    run_id: str,
    root_label: str,
    family: str,
    basin_label: str,
    pair: dict[str, Any],
    result: Any,
    constructor_config: dict[str, Any],
) -> ContinuationTrace:
    status = _trace_status(result.status)
    root_score = _optional_float(pair.get("detector_score"))
    detector_evidence = dict(pair.get("detector_evidence") or {})
    near_miss_score = 0.0
    if status in {"constructor_failed", "verification_failed", "residual"}:
        near_miss_score = round((root_score or 0.0) * 0.75, 6)
    payload = {
        "episode_id": run_id,
        "claim_id": result.pair_hash,
        "source": result.source,
        "target": result.target,
        "source_idx": result.source_idx,
        "target_idx": result.target_idx,
        "root_label": root_label,
        "root_score": root_score,
        "basin_label": basin_label,
        "detector_evidence": detector_evidence,
        "route_type": "finite_countermodel_search",
        "constructor_family": family,
        "constructor_config": constructor_config,
        "status": status,
        "terminal_form": result.terminal_form,
        "trust_level": result.trust_level,
        "provenance_type": result.provenance_type,
        "verifier_boundary": result.verifier_boundary,
        "certificate_id": result.certificate_id,
        "obstruction_label": None if result.certificate_id else _obstruction_label(root_label, family, status),
        "attempted": True,
        "verified": status in {"verified_false", "verified_true", "known_certificate_found"},
        "promoted": bool(result.promoted),
        "known_skipped": bool(result.known_skipped),
        "near_miss_score": near_miss_score,
        "residual_compression_delta": 1.0 if status in {"verified_false", "verified_true"} else 0.0,
        "novelty_score": 1.0 if result.promoted else 0.0,
        "elapsed_sec": result.elapsed_sec,
        "warnings": list(result.warnings) + ["Continuation traces are memory, not truth."],
        "evidence": {
            "root_lab_run_id": run_id,
            "m0_result": result.to_dict(),
            "basin_membership": basin_label,
            "advisory_only": True,
        },
    }
    payload["trace_id"] = make_trace_id(payload)
    return ContinuationTrace.from_dict(payload)


def _trace_status(status: str) -> str:
    lowered = str(status).lower()
    if lowered == "verified_false":
        return "verified_false"
    if lowered == "verified_true":
        return "verified_true"
    if lowered == "known_certificate_found":
        return "known_certificate_found"
    if lowered == "constructor_failed":
        return "constructor_failed"
    if lowered == "parse_failed":
        return "parse_failed"
    if lowered == "verification_failed":
        return "verification_failed"
    if lowered == "error":
        return "error"
    if lowered == "residual":
        return "residual"
    return "residual"


def _obstruction_label(root_label: str, family: str, status: str) -> str | None:
    if status in {"verified_false", "verified_true", "known_certificate_found"}:
        return None
    return f"{root_label}:{family}:{status}"


def _recommend(
    *,
    attempted_pairs: int,
    verified_false: int,
    null_lift: float,
    constructor_reuse_score: float,
    root_value_score: float,
    candidate_pairs: int,
    constructor_failed: int,
    residual: int,
) -> str:
    if (
        attempted_pairs >= 5
        and verified_false >= 2
        and null_lift > 0
        and constructor_reuse_score > 0
        and root_value_score > 0
    ):
        return "promote_constructor_root_candidate"
    if attempted_pairs < 5 and candidate_pairs > 0 and (verified_false > 0 or constructor_reuse_score > 0):
        return "hold_for_more_pairs"
    if candidate_pairs > 0 and verified_false == 0 and (constructor_failed + residual) > 0:
        return "obstruction_pressure_only"
    if null_lift <= 0 and verified_false > 0:
        return "shadow_or_low_lift"
    return "insufficient_evidence"


def _score_duplication_repetition(features: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    source_max = features["source_repeat_max"]
    target_max = features["target_repeat_max"]
    delta = max(0, target_max - source_max)
    score = min(1.0, 0.25 * delta + (0.25 if target_max >= 2 else 0.0) + (0.25 if features["target_nodes"] > features["source_nodes"] else 0.0))
    evidence = {
        "source_var_counts": features["source_var_counts"],
        "target_var_counts": features["target_var_counts"],
        "source_repeat_max": source_max,
        "target_repeat_max": target_max,
        "repeat_delta": delta,
        "advisory_only": True,
    }
    return round(score, 6), evidence


def _score_new_variable_freedom(features: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    source_vars = set(features["source_vars"])
    target_vars = set(features["target_vars"])
    new_vars = sorted(target_vars - source_vars)
    overlap = len(source_vars & target_vars) / max(1, len(source_vars | target_vars))
    score = min(1.0, 0.45 * len(new_vars) + 0.25 * max(0, len(target_vars) - len(source_vars)) + 0.30 * (1.0 - overlap))
    evidence = {
        "source_vars": sorted(source_vars),
        "target_vars": sorted(target_vars),
        "new_target_vars": new_vars,
        "var_overlap": round(overlap, 6),
        "advisory_only": True,
    }
    return round(score, 6), evidence


def _score_boundary_break(features: dict[str, Any], *, side: str) -> tuple[float, dict[str, Any]]:
    source_role = features[f"source_{side}_role_pressure"]
    other = "right" if side == "left" else "left"
    target_escape = features[f"target_{other}_role_pressure"]
    role_delta = max(0.0, target_escape - source_role)
    source_simple = 0.2 if source_role >= 0.5 else 0.0
    score = min(1.0, 0.50 * source_role + 0.35 * target_escape + 0.15 * role_delta + source_simple)
    evidence = {
        "source_lhs_signature": features["source_lhs_signature"],
        "source_rhs_signature": features["source_rhs_signature"],
        "target_lhs_signature": features["target_lhs_signature"],
        "target_rhs_signature": features["target_rhs_signature"],
        f"{side}_role_pressure": round(source_role, 6),
        f"{other}_role_escape": round(target_escape, 6),
        "advisory_only": True,
    }
    return round(score, 6), evidence


def _score_trivialization_escape(features: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    complexity_delta = max(0, features["target_nodes"] - features["source_nodes"])
    source_unique = len(features["source_vars"])
    target_unique = len(features["target_vars"])
    simple_source = 1.0 if features["source_nodes"] <= 3 or features["source_repeat_max"] >= 2 else 0.0
    score = min(1.0, 0.18 * complexity_delta + 0.25 * simple_source + 0.15 * max(0, target_unique - source_unique))
    evidence = {
        "source_nodes": features["source_nodes"],
        "target_nodes": features["target_nodes"],
        "complexity_delta": complexity_delta,
        "source_unique_vars": source_unique,
        "target_unique_vars": target_unique,
        "advisory_only": True,
    }
    return round(score, 6), evidence


def _pair_features(source: str, target: str) -> dict[str, Any]:
    source_eq = _parse_or_none(source)
    target_eq = _parse_or_none(target)
    source_counts = _equation_var_counts(source_eq) if source_eq else _fallback_var_counts(source)
    target_counts = _equation_var_counts(target_eq) if target_eq else _fallback_var_counts(target)
    source_vars = sorted(source_counts)
    target_vars = sorted(target_counts)
    return {
        "source_vars": source_vars,
        "target_vars": target_vars,
        "source_var_counts": dict(sorted(source_counts.items())),
        "target_var_counts": dict(sorted(target_counts.items())),
        "source_repeat_max": max(source_counts.values(), default=0),
        "target_repeat_max": max(target_counts.values(), default=0),
        "source_nodes": _equation_size(source_eq) if source_eq else _fallback_size(source),
        "target_nodes": _equation_size(target_eq) if target_eq else _fallback_size(target),
        "source_lhs_signature": _term_side_signature(source_eq.lhs if source_eq else None),
        "source_rhs_signature": _term_side_signature(source_eq.rhs if source_eq else None),
        "target_lhs_signature": _term_side_signature(target_eq.lhs if target_eq else None),
        "target_rhs_signature": _term_side_signature(target_eq.rhs if target_eq else None),
        "source_left_role_pressure": _boundary_pressure(source_eq, "left"),
        "source_right_role_pressure": _boundary_pressure(source_eq, "right"),
        "target_left_role_pressure": _boundary_pressure(target_eq, "left"),
        "target_right_role_pressure": _boundary_pressure(target_eq, "right"),
    }


def _parse_or_none(text: str) -> Equation | None:
    try:
        return parse_equation(_normalize_equation_text(text))
    except Exception:
        return None


def _normalize_equation_text(text: str) -> str:
    return str(text).replace("◇", "*").replace("⋄", "*").replace("·", "*")


def _equation_var_counts(eq: Equation) -> Counter[str]:
    counts: Counter[str] = Counter()
    _count_term_vars(eq.lhs, counts)
    _count_term_vars(eq.rhs, counts)
    return counts


def _count_term_vars(term: Term, counts: Counter[str]) -> None:
    if term.is_variable:
        counts[term.symbol] += 1
        return
    for arg in term.args:
        _count_term_vars(arg, counts)


def _equation_size(eq: Equation) -> int:
    return _term_size(eq.lhs) + _term_size(eq.rhs)


def _term_size(term: Term) -> int:
    if term.is_variable:
        return 1
    return 1 + sum(_term_size(arg) for arg in term.args)


def _term_side_signature(term: Term | None) -> dict[str, Any]:
    if term is None:
        return {"kind": "unknown"}
    if term.is_variable:
        return {"kind": "variable", "var": term.symbol}
    left, right = term.args
    return {
        "kind": "binary",
        "left": str(left),
        "right": str(right),
        "left_vars": sorted(left.variables()),
        "right_vars": sorted(right.variables()),
    }


def _boundary_pressure(eq: Equation | None, side: str) -> float:
    if eq is None:
        return 0.0
    if eq.rhs.is_variable and not eq.lhs.is_variable:
        left, right = eq.lhs.args
        boundary = left if side == "left" else right
        return 1.0 if str(boundary) == str(eq.rhs) else 0.0
    if eq.lhs.is_variable and not eq.rhs.is_variable:
        left, right = eq.rhs.args
        boundary = left if side == "left" else right
        return 1.0 if str(boundary) == str(eq.lhs) else 0.0
    return 0.0


def _fallback_var_counts(text: str) -> Counter[str]:
    return Counter(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", str(text)))


def _fallback_size(text: str) -> int:
    return max(1, len(re.findall(r"[A-Za-z_][A-Za-z0-9_]*|\*", str(text))))


def _select_null_rows(
    pairs: list[dict[str, Any]],
    selected: list[RootBasinPair],
    root_label: str,
    limit: int,
    rng: random.Random,
) -> list[dict[str, Any]]:
    selected_keys = {(item.source, item.target, item.source_idx, item.target_idx) for item in selected}
    candidates: list[dict[str, Any]] = []
    for row in pairs:
        key = (row["source"], row["target"], row.get("source_idx"), row.get("target_idx"))
        if key in selected_keys:
            continue
        score, _ = score_pair_for_root(row["source"], row["target"], root_label)
        if score < ROOT_THRESHOLD:
            candidates.append(row)
    candidates = list(candidates)
    rng.shuffle(candidates)
    return candidates[: max(0, limit)]


def _normalize_pair(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "source": str(row.get("source") or row.get("equation1") or ""),
        "target": str(row.get("target") or row.get("equation2") or ""),
        "source_idx": _optional_int(row.get("source_idx", row.get("eq1_id"))),
        "target_idx": _optional_int(row.get("target_idx", row.get("eq2_id"))),
        "root_label": row.get("root_label"),
        "detector_score": row.get("detector_score"),
    }


def _m0_pair(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "source": row["source"],
        "target": row["target"],
        "source_idx": row.get("source_idx"),
        "target_idx": row.get("target_idx"),
    }


def _family_max_order(family: str, configured: int) -> int:
    if family == "affine_parity_or_repeat_sensitive_countermodel_family":
        return max(configured, 4)
    return configured


def _summary(run_id: str, pairs: list[dict[str, Any]], results: list[RootValidationResult], elapsed: float) -> dict[str, Any]:
    top = results[0] if results else None
    return {
        "run_id": run_id,
        "input_pairs": len(pairs),
        "root_count": len(results),
        "attempted_pairs": sum(result.attempted_pairs for result in results),
        "verified_false": sum(result.verified_false for result in results),
        "top_root": top.root_label if top else None,
        "top_root_value_score": top.root_value_score if top else 0.0,
        "recommendation_counts": dict(sorted(Counter(result.recommendation for result in results).items())),
        "elapsed_sec": round(elapsed, 6),
        "advisory_only": True,
    }


def _write_report_md(report: RootConstructorLabReport, hypotheses: dict[str, RootHypothesis], path: Path) -> None:
    lines = [
        "# Root Constructor Validation Lab Report",
        "",
        "## Summary",
        "",
        "| root | attempted | verified_false | null_lift | root_value_score | recommendation |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for result in report.results:
        lines.append(
            f"| `{result.root_label}` | {result.attempted_pairs} | {result.verified_false} | "
            f"{result.null_lift:.3f} | {result.root_value_score:.6f} | {result.recommendation} |"
        )
    lines.extend(["", "## Root Details", ""])
    for result in report.results:
        hypothesis = hypotheses.get(result.root_label)
        lines.extend(
            [
                f"### {result.root_label}",
                "",
                hypothesis.description if hypothesis else "User-provided root.",
                "",
                f"- Candidate pairs: {result.candidate_pairs}",
                f"- Attempted pairs: {result.attempted_pairs}",
                f"- Certificate yield: {result.certificate_yield:.3f}",
                f"- Null comparison: {result.null_verified_false}/{result.null_attempted_pairs}",
                f"- Recommendation: {result.recommendation}",
                f"- Constructor families attempted: {', '.join(item.constructor_family for item in result.constructor_results) or 'none'}",
                "",
            ]
        )
    lines.extend(
        [
            "## Trust Boundary",
            "",
            "- Root validation is advisory.",
            "- Finite countermodels are verified only through the existing M0/importer path.",
            "- Root recommendations do not verify/refute claims.",
            "- Finite search failure is not proof.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_jsonl(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value)


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _optional_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
