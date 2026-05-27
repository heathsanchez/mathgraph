"""Canonical lightweight compounding loop over frozen evidence packs.

This module deliberately does not run real ETP, Lean, or any large search.  It
connects existing evidence-pack loaders into a small in-memory lawbook view,
then compares a generic baseline route with a memory-assisted route on a tiny
demo claim set.  The output is a decode-to-verify style trace: evidence can
change what the system tries next, but it cannot promote terminal truth.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from mathgraph.collatz_evidence import load_collatz_v12_2_evidence
from mathgraph.compounding_metrics import compute_lawbook_loop_metrics
from mathgraph.cross_world_evidence import (
    load_cross_world_semantic_residual_invariant,
    validate_cross_world_semantic_residual_invariant,
)
from mathgraph.decode_to_verify import evaluate_decode_to_verify_trace
from mathgraph.evidence_packs import EvidencePack, load_evidence_pack
from mathgraph.recursive_residual_transfer import load_frozen_recursive_transfer_evidence
from mathgraph.residual_obstruction_evidence import load_residual_obstruction_v8_4_evidence
from mathgraph.root_node_evidence import load_root_node_v16_3_evidence


CANONICAL_PACK_IDS: tuple[str, ...] = (
    "recursive_residual_transfer_v1_20260523",
    "sair_stage2_breakthrough_20260526",
    "residual_obstruction_atlas_v8_4",
    "collatz_primitive_divisor_v12_2",
    "root_node_persistent_filtration_v16_3",
    "cross_world_semantic_residual_invariant",
)


@dataclass(frozen=True)
class LawbookViewEntry:
    evidence_pack_id: str
    claim_status: str
    trust_boundary_status: str
    terminal_form_type: str
    empirical_metrics: dict[str, Any] = field(default_factory=dict)
    prohibited_promotions: tuple[str, ...] = ()
    attention_terms: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_pack_id": self.evidence_pack_id,
            "claim_status": self.claim_status,
            "trust_boundary_status": self.trust_boundary_status,
            "terminal_form_type": self.terminal_form_type,
            "empirical_metrics": dict(self.empirical_metrics),
            "prohibited_promotions": list(self.prohibited_promotions),
            "attention_terms": list(self.attention_terms),
        }


@dataclass(frozen=True)
class DemoClaim:
    claim_id: str
    description: str
    terms: tuple[str, ...]
    baseline_action: str = "generic_bounded_search"


@dataclass(frozen=True)
class CompoundingLawbookEngineReport:
    evidence_pack_count: int
    lawbook_hit_rate: float
    lawbook_action_change_rate: float
    decode_supported_rate: float
    prohibited_promotion_count: int
    advisory_boundary_ok: bool
    baseline_supported_count: int
    memory_supported_count: int
    outputs: dict[str, str] = field(default_factory=dict)
    lawbook_view: tuple[dict[str, Any], ...] = ()
    metrics: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    # Compatibility fields for older smoke callers.
    real_sair_used: bool = False
    fallback_mode: bool = True
    advisory_boundary_preserved: bool = True
    baseline_yield: float = 0.0
    lawbook_yield: float = 0.0
    htilt_yield: float = 0.0
    decode_success_rate: float = 0.0
    episode_to_episode_gain: float = 0.0
    compounding_signal_detected: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_pack_count": self.evidence_pack_count,
            "lawbook_hit_rate": self.lawbook_hit_rate,
            "lawbook_action_change_rate": self.lawbook_action_change_rate,
            "decode_supported_rate": self.decode_supported_rate,
            "prohibited_promotion_count": self.prohibited_promotion_count,
            "advisory_boundary_ok": self.advisory_boundary_ok,
            "baseline_supported_count": self.baseline_supported_count,
            "memory_supported_count": self.memory_supported_count,
            "outputs": dict(self.outputs),
            "lawbook_view": list(self.lawbook_view),
            "metrics": dict(self.metrics),
            "metadata": dict(self.metadata),
            "real_sair_used": self.real_sair_used,
            "fallback_mode": self.fallback_mode,
            "advisory_boundary_preserved": self.advisory_boundary_preserved,
            "baseline_yield": self.baseline_yield,
            "lawbook_yield": self.lawbook_yield,
            "htilt_yield": self.htilt_yield,
            "decode_success_rate": self.decode_success_rate,
            "episode_to_episode_gain": self.episode_to_episode_gain,
            "compounding_signal_detected": self.compounding_signal_detected,
        }


def run_compounding_lawbook_engine(
    out_dir: str | Path,
    equations_path: str | Path | None = None,
    matrix_path: str | Path | None = None,
    seeds: Sequence[int] = (0, 1, 2),
    max_tasks: int = 250,
    use_real_sair_if_available: bool = True,
    fallback_smoke: bool = False,
) -> CompoundingLawbookEngineReport:
    """Run the canonical demo compounding loop.

    The unused arguments are retained for CLI/API compatibility.  This loop is
    intentionally evidence-pack native and does not load real ETP files.
    """

    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    lawbook_view = build_lawbook_view()
    claims = build_demo_claims(max_tasks=max_tasks)
    attention_rows = run_memory_attention(claims, lawbook_view)
    decode_rows = evaluate_decode_to_verify_trace(attention_rows)
    metrics = compute_lawbook_loop_metrics(
        attention_rows=attention_rows,
        decode_rows=decode_rows,
        evidence_pack_count=len(lawbook_view),
    )
    advisory_boundary_ok = bool(metrics["advisory_boundary_ok"])
    outputs = {
        "report_json": str(output / "compounding_report.json"),
        "report_md": str(output / "compounding_report.md"),
        "lawbook_attention_trace": str(output / "lawbook_attention_trace.csv"),
        "decode_to_verify_eval": str(output / "decode_to_verify_eval.csv"),
    }
    report = CompoundingLawbookEngineReport(
        evidence_pack_count=len(lawbook_view),
        lawbook_hit_rate=float(metrics["lawbook_hit_rate"]),
        lawbook_action_change_rate=float(metrics["lawbook_action_change_rate"]),
        decode_supported_rate=float(metrics["decode_supported_rate"]),
        prohibited_promotion_count=int(metrics["prohibited_promotion_count"]),
        advisory_boundary_ok=advisory_boundary_ok,
        baseline_supported_count=int(metrics["baseline_supported_count"]),
        memory_supported_count=int(metrics["memory_supported_count"]),
        outputs=outputs,
        lawbook_view=tuple(entry.to_dict() for entry in lawbook_view),
        metrics=metrics,
        metadata={
            "mode": "demo_synthetic_claims",
            "trust_boundary": "evidence_changes_routes_only_verifiers_decide_terminal_truth",
            "ignored_real_etp_args": bool(equations_path or matrix_path or use_real_sair_if_available),
            "seeds": list(seeds),
            "fallback_smoke": fallback_smoke,
        },
        advisory_boundary_preserved=advisory_boundary_ok,
        baseline_yield=float(metrics["baseline_supported_count"]),
        lawbook_yield=float(metrics["memory_supported_count"]),
        htilt_yield=float(metrics["memory_supported_count"]),
        decode_success_rate=float(metrics["decode_supported_rate"]),
        episode_to_episode_gain=float(metrics["memory_supported_count"] - metrics["baseline_supported_count"]),
        compounding_signal_detected=bool(metrics["memory_supported_count"] > metrics["baseline_supported_count"] and advisory_boundary_ok),
    )
    _write_csv(output / "lawbook_attention_trace.csv", attention_rows)
    _write_csv(output / "decode_to_verify_eval.csv", decode_rows)
    (output / "compounding_report.json").write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    (output / "compounding_report.md").write_text(_markdown(report), encoding="utf-8")
    return report


def build_lawbook_view() -> tuple[LawbookViewEntry, ...]:
    recursive = load_frozen_recursive_transfer_evidence("recursive_residual_transfer_v1_20260523")
    sair = load_evidence_pack(
        "sair_stage2_breakthrough_20260526",
        required_fields=("accepted_false_certificates", "finite_checked_countermodels"),
    )
    residual = load_residual_obstruction_v8_4_evidence()
    collatz = load_collatz_v12_2_evidence()
    root = load_root_node_v16_3_evidence()
    cross_world = validate_cross_world_semantic_residual_invariant(load_cross_world_semantic_residual_invariant())
    return (
        _entry_from_recursive(recursive),
        _entry_from_pack(
            sair,
            claim_status="verified_finite_false_countermodel_pack",
            terminal_form_type="FINITE_COUNTERMODEL",
            terms=("sair", "finite", "countermodel", "false", "certificate", "strict"),
            extra_metrics=("accepted_false_certificates", "finite_checked_countermodels", "total_gain_over_baseline"),
        ),
        _entry_from_pack(
            residual,
            claim_status="advisory_residual_frontier_obstruction_atlas",
            terminal_form_type="NAMED_OBSTRUCTION_CANDIDATE",
            terms=("residual", "frontier", "obstruction", "carrier", "semantic", "atlas"),
            extra_metrics=("coverage_percent", "remaining_frontier", "top_constructor_pressure"),
        ),
        _entry_from_pack(
            collatz,
            claim_status="proof_template_obstruction_law_candidate",
            terminal_form_type="NONE_ADVISORY",
            terms=("collatz", "primitive", "divisor", "obstruction", "proof", "template"),
            extra_metrics=("primitive_growth_pairs", "pairs_processed", "total_integer_candidate_count", "main_obstruction"),
        ),
        _entry_from_pack(
            root,
            claim_status="advisory_persistent_load_bearing_root_node",
            terminal_form_type="NONE_ADVISORY",
            terms=("root", "node", "filtration", "lawbook", "continuation", "load", "bearing"),
            extra_metrics=("promoted_root_nodes", "watchlist_root_nodes", "shadow_clusters"),
        ),
        _entry_from_pack(
            cross_world,
            claim_status="empirical_cross_world_invariant_candidate",
            terminal_form_type="NONE_ADVISORY",
            terms=("crossworld", "semantic", "residual", "rank", "invariant", "closure"),
            extra_metrics=(
                "semantic_root_all_world_auc_false",
                "residual_rank_all_world_auc_false",
                "leave_one_world_out_mean_auc_false",
                "etp_false_underexplained",
            ),
        ),
    )


def build_demo_claims(max_tasks: int = 250) -> tuple[DemoClaim, ...]:
    claims = (
        DemoClaim("demo_recursive_transfer", "ETP heldout FALSE route selection", ("recursive", "route", "memory", "etp")),
        DemoClaim("demo_sair_false_certificate", "SAIR accepted FALSE finite countermodel", ("sair", "finite", "countermodel", "certificate")),
        DemoClaim("demo_residual_frontier", "Residual-zero frontier continuation", ("residual", "frontier", "carrier", "obstruction")),
        DemoClaim("demo_collatz_candidate", "Collatz primitive divisor proof-template candidate", ("collatz", "primitive", "divisor", "template")),
        DemoClaim("demo_root_node", "Persistent load-bearing root continuation", ("root", "node", "filtration", "lawbook")),
        DemoClaim("demo_crossworld_residual", "CrossWorld semantic residual invariant route", ("crossworld", "semantic", "residual", "rank")),
    )
    return claims[: max(1, min(len(claims), int(max_tasks) if max_tasks else len(claims)))]


def run_memory_attention(claims: Sequence[DemoClaim], lawbook_view: Sequence[LawbookViewEntry]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for claim in claims:
        entry, score = _best_attention(claim, lawbook_view)
        lawbook_hit = entry is not None and score > 0
        memory_action = _memory_action(entry) if entry else claim.baseline_action
        terminal_form_candidate = _terminal_candidate(entry) if entry else "NONE"
        prohibited = _prohibited_promotion(entry, terminal_form_candidate) if entry else False
        rows.append(
            {
                "claim_id": claim.claim_id,
                "description": claim.description,
                "baseline_action": claim.baseline_action,
                "memory_action": memory_action,
                "lawbook_hit": lawbook_hit,
                "attention_score": score,
                "evidence_pack_id": entry.evidence_pack_id if entry else "",
                "claim_status": entry.claim_status if entry else "",
                "terminal_form_type": entry.terminal_form_type if entry else "NONE",
                "terminal_form_candidate": terminal_form_candidate,
                "action_changed": memory_action != claim.baseline_action,
                "prohibited_promotion": prohibited,
                "advisory_boundary_ok": not prohibited,
            }
        )
    return rows


def _entry_from_recursive(metrics: Mapping[str, Any]) -> LawbookViewEntry:
    return LawbookViewEntry(
        evidence_pack_id="recursive_residual_transfer_v1_20260523",
        claim_status="empirical_advisory_route_memory",
        trust_boundary_status="PASS",
        terminal_form_type="NONE_ADVISORY",
        empirical_metrics=_metric_subset(
            metrics,
            (
                "gates_passed",
                "gates_total",
                "compact_transfer_gain_vs_generic_positive",
                "compact_beats_random_same_size",
                "compact_beats_shuffled_atlas_same_size",
                "true_contamination_max",
            ),
        ),
        prohibited_promotions=_standard_prohibited_promotions(),
        attention_terms=("recursive", "route", "memory", "etp", "transfer", "atlas"),
    )


def _entry_from_pack(
    pack: EvidencePack,
    *,
    claim_status: str,
    terminal_form_type: str,
    terms: Iterable[str],
    extra_metrics: Iterable[str],
) -> LawbookViewEntry:
    return LawbookViewEntry(
        evidence_pack_id=pack.pack_id,
        claim_status=claim_status,
        trust_boundary_status="PASS",
        terminal_form_type=terminal_form_type,
        empirical_metrics=_metric_subset(pack.metrics, tuple(extra_metrics)),
        prohibited_promotions=_standard_prohibited_promotions(),
        attention_terms=tuple(sorted(set(str(term).lower() for term in terms) | {pack.pack_id.lower()})),
    )


def _metric_subset(metrics: Mapping[str, Any], keys: Iterable[str]) -> dict[str, Any]:
    return {key: metrics[key] for key in keys if key in metrics}


def _standard_prohibited_promotions() -> tuple[str, ...]:
    return (
        "advisory_score_to_true",
        "route_score_to_certificate",
        "failed_finite_search_to_true",
        "llm_text_to_verified_proof",
        "unverified_true_candidate_to_verified_true",
    )


def _best_attention(claim: DemoClaim, entries: Sequence[LawbookViewEntry]) -> tuple[LawbookViewEntry | None, int]:
    claim_terms = {term.lower() for term in claim.terms}
    best: tuple[LawbookViewEntry | None, int] = (None, 0)
    for entry in entries:
        score = len(claim_terms & set(entry.attention_terms))
        if score > best[1]:
            best = (entry, score)
    return best


def _memory_action(entry: LawbookViewEntry | None) -> str:
    if entry is None:
        return "generic_bounded_search"
    actions = {
        "recursive_residual_transfer_v1_20260523": "use_advisory_route_memory_then_request_finite_checker",
        "sair_stage2_breakthrough_20260526": "replay_finite_checked_false_countermodel_certificate",
        "residual_obstruction_atlas_v8_4": "expand_semantic_universe_then_minimum_carrier_search",
        "collatz_primitive_divisor_v12_2": "extract_proof_template_obligation_keep_not_a_proof",
        "root_node_persistent_filtration_v16_3": "prioritize_persistent_load_bearing_root_then_verify",
        "cross_world_semantic_residual_invariant": "extract_semantic_residual_then_route_to_verifier_or_obstruction",
    }
    return actions.get(entry.evidence_pack_id, "generic_bounded_search")


def _terminal_candidate(entry: LawbookViewEntry | None) -> str:
    if entry is None:
        return "NONE"
    if entry.evidence_pack_id == "sair_stage2_breakthrough_20260526":
        return "FINITE_COUNTERMODEL"
    return "UNVERIFIED_ROUTE"


def _prohibited_promotion(entry: LawbookViewEntry | None, terminal_candidate: str) -> bool:
    if entry is None:
        return False
    if entry.evidence_pack_id == "sair_stage2_breakthrough_20260526" and terminal_candidate == "FINITE_COUNTERMODEL":
        return False
    return terminal_candidate in {"TRUE", "FALSE", "VERIFIED_PROOF", "FINITE_COUNTERMODEL"}


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


def _markdown(report: CompoundingLawbookEngineReport) -> str:
    return f"""# Compounding Lawbook Loop

- evidence_pack_count: `{report.evidence_pack_count}`
- lawbook_hit_rate: `{report.lawbook_hit_rate:.3f}`
- lawbook_action_change_rate: `{report.lawbook_action_change_rate:.3f}`
- decode_supported_rate: `{report.decode_supported_rate:.3f}`
- prohibited_promotion_count: `{report.prohibited_promotion_count}`
- advisory_boundary_ok: `{report.advisory_boundary_ok}`

This is a lightweight repo-native compounding loop. Evidence-pack memory can
change the next action, but advisory route memory is not truth, failed finite
search is not TRUE, Collatz v12.2 remains not a proof, CrossWorld remains an
empirical advisory invariant candidate, and SAIR finite-checked FALSE
countermodels remain distinct from route memory.
"""
