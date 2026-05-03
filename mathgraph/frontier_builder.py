"""Candidate frontier generation for MathGraph scheduling."""

from __future__ import annotations

import json
import random
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from adapters.etp_adapter import load_equations, load_matrix
from mathgraph.hashing import content_id
from mathgraph.kernel_oracle import KernelOracle
from mathgraph.lawbook_store import LawbookStore
from mathgraph.outcome_dataset import extract_pair_features


@dataclass(frozen=True)
class FrontierCandidate:
    source: str
    target: str
    source_idx: int | None
    target_idx: int | None
    label: str
    candidate_origin: str
    frontier_score: float
    frontier_reason_codes: list[str]
    features: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "source_idx": self.source_idx,
            "target_idx": self.target_idx,
            "label": self.label,
            "candidate_origin": self.candidate_origin,
            "frontier_score": self.frontier_score,
            "frontier_reason_codes": list(self.frontier_reason_codes),
            "features": dict(self.features),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FrontierCandidate":
        return cls(
            source=str(data["source"]),
            target=str(data["target"]),
            source_idx=_optional_int(data.get("source_idx")),
            target_idx=_optional_int(data.get("target_idx")),
            label=str(data.get("label", "structural_unknown")),
            candidate_origin=str(data.get("candidate_origin", "structural")),
            frontier_score=float(data.get("frontier_score", 0.0)),
            frontier_reason_codes=[str(item) for item in data.get("frontier_reason_codes", [])],
            features=dict(data.get("features", {})),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass(frozen=True)
class FrontierBuilderConfig:
    equations_path: str
    out_jsonl: str
    store_path: str | None = None
    matrix_path: str | None = None
    max_candidates: int = 1000
    source_limit: int | None = None
    target_limit: int | None = None
    include_matrix_false: bool = True
    include_matrix_true: bool = False
    include_unknown_matrix_missing: bool = True
    skip_known: bool = True
    random_seed: int = 42

    def to_dict(self) -> dict[str, Any]:
        return {
            "equations_path": self.equations_path,
            "out_jsonl": self.out_jsonl,
            "store_path": self.store_path,
            "matrix_path": self.matrix_path,
            "max_candidates": self.max_candidates,
            "source_limit": self.source_limit,
            "target_limit": self.target_limit,
            "include_matrix_false": self.include_matrix_false,
            "include_matrix_true": self.include_matrix_true,
            "include_unknown_matrix_missing": self.include_unknown_matrix_missing,
            "skip_known": self.skip_known,
            "random_seed": self.random_seed,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FrontierBuilderConfig":
        return cls(
            equations_path=str(data["equations_path"]),
            out_jsonl=str(data["out_jsonl"]),
            store_path=data.get("store_path"),
            matrix_path=data.get("matrix_path"),
            max_candidates=int(data.get("max_candidates", 1000)),
            source_limit=_optional_int(data.get("source_limit")),
            target_limit=_optional_int(data.get("target_limit")),
            include_matrix_false=bool(data.get("include_matrix_false", True)),
            include_matrix_true=bool(data.get("include_matrix_true", False)),
            include_unknown_matrix_missing=bool(data.get("include_unknown_matrix_missing", True)),
            skip_known=bool(data.get("skip_known", True)),
            random_seed=int(data.get("random_seed", 42)),
        )


@dataclass(frozen=True)
class FrontierBuilderResult:
    candidates: list[dict[str, Any]]
    summary: dict[str, Any]
    outputs: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidates": list(self.candidates),
            "summary": dict(self.summary),
            "outputs": dict(self.outputs),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FrontierBuilderResult":
        return cls(
            candidates=list(data.get("candidates", [])),
            summary=dict(data.get("summary", {})),
            outputs=dict(data.get("outputs", {})),
        )


def build_candidate_frontier(
    config: FrontierBuilderConfig | dict[str, Any],
) -> FrontierBuilderResult:
    config = config if isinstance(config, FrontierBuilderConfig) else FrontierBuilderConfig.from_dict(config)
    equations = load_equations(config.equations_path)
    source_indices = list(range(len(equations)))[: config.source_limit]
    target_indices = list(range(len(equations)))[: config.target_limit]
    matrix = None
    matrix_loaded = False
    warnings: list[str] = []
    if config.matrix_path:
        try:
            matrix = load_matrix(config.matrix_path)
            matrix_loaded = True
        except ImportError as exc:
            warnings.append(str(exc))

    store = LawbookStore(config.store_path) if config.store_path else None
    oracle = KernelOracle(store) if store is not None else None
    skipped_known = 0
    attempted = 0
    candidates: dict[tuple[int, int, str], FrontierCandidate] = {}
    rng = random.Random(config.random_seed)

    try:
        pair_order = [(i, j) for i in source_indices for j in target_indices]
        rng.shuffle(pair_order)
        for i, j in pair_order:
            if i >= len(equations) or j >= len(equations):
                continue
            labels = _labels_for_pair(matrix, i, j, config)
            for label, origin in labels:
                attempted += 1
                if oracle is not None and config.skip_known:
                    answer = oracle.query(equations[i], equations[j])
                    if answer.status in {"VERIFIED", "REFUTED"}:
                        skipped_known += 1
                        continue
                candidate = _candidate(
                    equations=equations,
                    source_idx=i,
                    target_idx=j,
                    label=label,
                    origin=origin,
                )
                candidates[(i, j, label)] = candidate

        selected = sorted(
            candidates.values(),
            key=lambda item: (-item.frontier_score, item.source_idx or -1, item.target_idx or -1, item.label),
        )[: config.max_candidates]
        _write_jsonl(selected, config.out_jsonl)
        summary_path = str(Path(config.out_jsonl).with_name("frontier_summary.json"))
        summary = _summary(
            selected,
            skipped_known=skipped_known,
            attempted_pair_count=attempted,
            equations_count=len(equations),
            matrix_loaded=matrix_loaded,
            store_loaded=store is not None,
            warnings=warnings,
        )
        _write_json(summary, summary_path)
        return FrontierBuilderResult(
            candidates=[candidate.to_dict() for candidate in selected],
            summary=summary,
            outputs={"jsonl": str(config.out_jsonl), "summary": summary_path},
        )
    finally:
        if store is not None:
            store.close()


def score_frontier_pair(source: str, target: str, label: str = "structural_unknown") -> tuple[float, list[str], dict[str, Any]]:
    features = extract_pair_features(source, target)
    score = 0.0
    reasons: list[str] = []
    if features["new_target_vars"]:
        score += 0.30
        reasons.append("target_introduces_new_variables")
    if features["target_op_count"] > features["source_op_count"]:
        score += 0.20
        reasons.append("target_more_operations")
    if features["same_skeleton_rough"] and not features["same_text"]:
        score += 0.15
        reasons.append("same_skeleton_different_text")
    if features["target_has_repeated_vars"]:
        score += 0.15
        reasons.append("target_repeat_pressure")
    if label == "matrix_false_unverified":
        score += 0.10
        reasons.append("matrix_false_unverified")
    if features["source_op_count"] > 0 and features["target_op_count"] > 0:
        score += 0.05
        reasons.append("both_nontrivial")
    if features["same_text"]:
        score -= 0.50
        reasons.append("same_text_low_priority")
    return max(0.0, min(1.0, score)), reasons, features


def _labels_for_pair(matrix: Any, i: int, j: int, config: FrontierBuilderConfig) -> list[tuple[str, str]]:
    labels: list[tuple[str, str]] = []
    if matrix is not None:
        if i < matrix.shape[0] and j < matrix.shape[1]:
            value = bool(matrix[i, j])
            if not value and config.include_matrix_false:
                labels.append(("matrix_false_unverified", "matrix_false_frontier"))
            if value and config.include_matrix_true:
                labels.append(("matrix_true_unverified", "matrix_true_frontier"))
    if matrix is None or config.include_unknown_matrix_missing:
        labels.append(("structural_unknown", "structural_frontier"))
    return labels


def _candidate(
    equations: list[str],
    source_idx: int,
    target_idx: int,
    label: str,
    origin: str,
) -> FrontierCandidate:
    source = equations[source_idx]
    target = equations[target_idx]
    score, reasons, features = score_frontier_pair(source, target, label=label)
    return FrontierCandidate(
        source=source,
        target=target,
        source_idx=source_idx,
        target_idx=target_idx,
        label=label,
        candidate_origin=origin,
        frontier_score=score,
        frontier_reason_codes=reasons,
        features=features,
        metadata={
            "frontier_candidate_id": content_id(
                "frontier", {"source_idx": source_idx, "target_idx": target_idx, "label": label}
            ),
            "truth_status": "unverified_candidate",
        },
    )


def _summary(
    candidates: list[FrontierCandidate],
    *,
    skipped_known: int,
    attempted_pair_count: int,
    equations_count: int,
    matrix_loaded: bool,
    store_loaded: bool,
    warnings: list[str],
) -> dict[str, Any]:
    scores = [candidate.frontier_score for candidate in candidates]
    reason_counts = Counter(
        reason for candidate in candidates for reason in candidate.frontier_reason_codes
    )
    return {
        "candidate_count": len(candidates),
        "skipped_known_count": skipped_known,
        "attempted_pair_count": attempted_pair_count,
        "by_label": dict(Counter(candidate.label for candidate in candidates)),
        "by_origin": dict(Counter(candidate.candidate_origin for candidate in candidates)),
        "top_reason_codes": dict(reason_counts.most_common(10)),
        "score_min": min(scores) if scores else 0.0,
        "score_max": max(scores) if scores else 0.0,
        "score_mean": sum(scores) / len(scores) if scores else 0.0,
        "equations_count": equations_count,
        "matrix_loaded": matrix_loaded,
        "store_loaded": store_loaded,
        "warnings": list(warnings),
    }


def _write_jsonl(candidates: list[FrontierCandidate], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for candidate in candidates:
            handle.write(json.dumps(candidate.to_dict(), sort_keys=True) + "\n")


def _write_json(payload: Any, path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
