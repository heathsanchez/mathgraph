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
from mathgraph.progress import ProgressLogger


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
    frontier_mode: str = "small_sample"
    frontier_scan_limit: int | None = None
    duplicate_filter: bool = True

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
            "frontier_mode": self.frontier_mode,
            "frontier_scan_limit": self.frontier_scan_limit,
            "duplicate_filter": self.duplicate_filter,
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
            frontier_mode=str(data.get("frontier_mode", "small_sample")),
            frontier_scan_limit=_optional_int(data.get("frontier_scan_limit")),
            duplicate_filter=bool(data.get("duplicate_filter", True)),
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
    progress: ProgressLogger | None = None,
) -> FrontierBuilderResult:
    config = config if isinstance(config, FrontierBuilderConfig) else FrontierBuilderConfig.from_dict(config)
    if config.frontier_mode not in {"small_sample", "matrix_false", "structural", "mixed"}:
        raise ValueError(f"unknown frontier_mode: {config.frontier_mode}")
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
    known_filter = KnownPairFilter.from_store(store) if store is not None and config.duplicate_filter else KnownPairFilter()
    skipped_known = 0
    episode_duplicate_skipped = 0
    attempted = 0
    emitted = 0
    pairs_considered = 0
    equations_scanned: set[int] = set()
    candidates: dict[tuple[int, int, str], FrontierCandidate] = {}
    emitted_pairs: set[tuple[str, str] | tuple[int, int]] = set()
    rng = random.Random(config.random_seed)
    total_pairs = len(source_indices) * len(target_indices)
    scan_limit = _effective_scan_limit(config, total_pairs)
    every = max(1, min(250, max(config.max_candidates, 1)))

    try:
        for i, j in _iter_pair_order(source_indices, target_indices, rng, config.frontier_mode):
            if pairs_considered >= scan_limit:
                warnings.append(f"frontier scan stopped at scan_limit={scan_limit}")
                break
            if len(candidates) >= config.max_candidates:
                break
            pairs_considered += 1
            equations_scanned.update((i, j))
            if i >= len(equations) or j >= len(equations):
                continue
            source = equations[i]
            target = equations[j]
            if config.duplicate_filter and known_filter.contains(source, target, i, j):
                skipped_known += 1
                continue
            pair_key = _pair_key(source, target, i, j)
            if config.duplicate_filter and pair_key in emitted_pairs:
                episode_duplicate_skipped += 1
                continue
            labels = _labels_for_pair(matrix, i, j, config)
            for label, origin in labels:
                if len(candidates) >= config.max_candidates:
                    break
                attempted += 1
                candidate = _candidate(
                    equations=equations,
                    source_idx=i,
                    target_idx=j,
                    label=label,
                    origin=origin,
                )
                key = (i, j, label)
                if key not in candidates:
                    candidates[key] = candidate
                    emitted_pairs.add(pair_key)
                    emitted = len(candidates)
                    if config.duplicate_filter:
                        break
            if progress and (pairs_considered % every == 0 or emitted >= config.max_candidates):
                progress.event(
                    "frontier_progress",
                    "frontier_scan",
                    equations_scanned=len(equations_scanned),
                    pair_candidates_considered=pairs_considered,
                    known_skipped=skipped_known,
                    known_pair_skipped_count=skipped_known,
                    episode_duplicate_skipped_count=episode_duplicate_skipped,
                    emitted_frontier_rows=emitted,
                    emitted_count=emitted,
                    scan_limit=scan_limit,
                    max_candidates=config.max_candidates,
                )

        selected = sorted(
            candidates.values(),
            key=lambda item: (-item.frontier_score, item.source_idx or -1, item.target_idx or -1, item.label),
        )[: config.max_candidates]
        _write_jsonl(selected, config.out_jsonl)
        summary_path = str(Path(config.out_jsonl).with_name("frontier_summary.json"))
        summary = _summary(
            selected,
            skipped_known=skipped_known,
            episode_duplicate_skipped=episode_duplicate_skipped,
            attempted_pair_count=attempted,
            pair_candidates_considered=pairs_considered,
            equations_scanned=len(equations_scanned),
            emitted_frontier_rows=len(selected),
            scan_limit=scan_limit,
            frontier_mode=config.frontier_mode,
            duplicate_filter=config.duplicate_filter,
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


class KnownPairFilter:
    """Compact primitive-pair filter for frontier selection."""

    def __init__(self, pairs: set[tuple[str, str]] | None = None, index_pairs: set[tuple[int, int]] | None = None) -> None:
        self.pairs = pairs or set()
        self.index_pairs = index_pairs or set()

    @classmethod
    def from_store(cls, store: LawbookStore | None) -> "KnownPairFilter":
        if store is None:
            return cls()
        pairs: set[tuple[str, str]] = set()
        index_pairs: set[tuple[int, int]] = set()
        for record in store.iter_primitive_traces():
            source = record.get("source")
            target = record.get("target")
            if source is not None and target is not None:
                pairs.add((_normalize_pair_text(str(source)), _normalize_pair_text(str(target))))
            source_idx = _optional_int(record.get("source_idx"))
            target_idx = _optional_int(record.get("target_idx"))
            if source_idx is not None and target_idx is not None:
                index_pairs.add((source_idx, target_idx))
        return cls(pairs=pairs, index_pairs=index_pairs)

    @classmethod
    def from_outcome_rows(cls, rows: list[dict[str, Any]]) -> "KnownPairFilter":
        pairs: set[tuple[str, str]] = set()
        index_pairs: set[tuple[int, int]] = set()
        for row in rows:
            source = row.get("source")
            target = row.get("target")
            if source is not None and target is not None:
                pairs.add((_normalize_pair_text(str(source)), _normalize_pair_text(str(target))))
            source_idx = _optional_int(row.get("source_idx"))
            target_idx = _optional_int(row.get("target_idx"))
            if source_idx is not None and target_idx is not None:
                index_pairs.add((source_idx, target_idx))
        return cls(pairs=pairs, index_pairs=index_pairs)

    def contains(self, source: str, target: str, source_idx: int | None = None, target_idx: int | None = None) -> bool:
        if source_idx is not None and target_idx is not None and (source_idx, target_idx) in self.index_pairs:
            return True
        return (_normalize_pair_text(source), _normalize_pair_text(target)) in self.pairs


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
    if matrix is not None and config.frontier_mode in {"small_sample", "matrix_false", "mixed"}:
        if i < matrix.shape[0] and j < matrix.shape[1]:
            value = bool(matrix[i, j])
            if not value and config.include_matrix_false:
                labels.append(("matrix_false_unverified", "matrix_false_frontier"))
            if value and config.include_matrix_true and config.frontier_mode != "matrix_false":
                labels.append(("matrix_true_unverified", "matrix_true_frontier"))
    if config.frontier_mode == "matrix_false":
        return labels
    if config.frontier_mode in {"small_sample", "structural", "mixed"} and (matrix is None or config.include_unknown_matrix_missing):
        labels.append(("structural_unknown", "structural_frontier"))
    return labels


def _effective_scan_limit(config: FrontierBuilderConfig, total_pairs: int) -> int:
    if config.frontier_scan_limit is not None:
        return max(0, min(total_pairs, config.frontier_scan_limit))
    return max(config.max_candidates, min(total_pairs, max(config.max_candidates * 50, 1000)))


def _iter_pair_order(
    source_indices: list[int],
    target_indices: list[int],
    rng: random.Random,
    frontier_mode: str,
):
    if frontier_mode == "small_sample":
        sources = list(source_indices)
        targets = list(target_indices)
        rng.shuffle(sources)
        rng.shuffle(targets)
        for offset in range(max(len(sources), len(targets), 1)):
            for source_pos, i in enumerate(sources):
                if not targets:
                    return
                yield i, targets[(source_pos + offset) % len(targets)]
        return
    for i in source_indices:
        for j in target_indices:
            yield i, j


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
    episode_duplicate_skipped: int,
    attempted_pair_count: int,
    pair_candidates_considered: int,
    equations_scanned: int,
    emitted_frontier_rows: int,
    scan_limit: int,
    frontier_mode: str,
    duplicate_filter: bool,
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
        "known_pair_skipped_count": skipped_known,
        "episode_duplicate_skipped_count": episode_duplicate_skipped,
        "attempted_pair_count": attempted_pair_count,
        "pair_candidates_considered": pair_candidates_considered,
        "considered_count": pair_candidates_considered,
        "equations_scanned_count": equations_scanned,
        "emitted_frontier_rows": emitted_frontier_rows,
        "emitted_count": emitted_frontier_rows,
        "scan_limit": scan_limit,
        "frontier_mode": frontier_mode,
        "duplicate_filter": duplicate_filter,
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


def _pair_key(
    source: str, target: str, source_idx: int | None, target_idx: int | None
) -> tuple[str, str]:
    return (_normalize_pair_text(source), _normalize_pair_text(target))


def _normalize_pair_text(value: str) -> str:
    return " ".join(value.strip().split())


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
