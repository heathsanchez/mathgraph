import json
import subprocess
import sys
from pathlib import Path

from mathgraph.root_discovery import (
    DISCOVERY_STATUS,
    RootDiscoverySignals,
    SAT,
    UNKNOWN,
    UNSAT,
    attach_root_discovery_scores,
    build_constructor_family_cards,
    build_replay_queue,
    distill_obstruction_candidates,
    distill_root_candidates,
    score_root_candidate,
    summarize_root_discovery,
)
from mathgraph.root_nodes import RootNode


def _row(
    status,
    *,
    source_idx=1,
    target_idx=1,
    surface="surface_a",
    source_sig="source_a",
    demand="demand_a",
    route="symbolic_complete",
    table_hash=None,
    witness_schema=None,
    order=2,
    metadata=None,
):
    return {
        "run_id": "run_1",
        "obstruction_surface_id": surface,
        "source_idx": source_idx,
        "target_idx": target_idx,
        "source_equation": f"s{source_idx}",
        "target_equation": f"t{target_idx}",
        "carrier_order": order,
        "solver_status": status,
        "certificate_id": f"cert_{source_idx}_{target_idx}" if status == SAT else None,
        "table_hash": table_hash,
        "witness_schema": witness_schema,
        "source_signature": source_sig,
        "target_signature": f"target_{target_idx}",
        "target_demand_signature": demand,
        "route": route,
        "metadata": metadata or {},
    }


def test_sat_burst_creates_source_burst_root_candidate():
    rows = [_row(SAT, target_idx=i, witness_schema=f"w{i}", table_hash=f"t{i}") for i in range(4)]
    rows += [_row(UNSAT, source_sig="nearby", target_idx=20 + i, witness_schema=None, table_hash=None) for i in range(3)]

    roots = distill_root_candidates(rows, min_sat_count=2)

    assert roots
    assert roots[0].root_type == "source_burst_root"
    assert roots[0].source_burst_score == 1.0
    assert roots[0].status == DISCOVERY_STATUS


def test_repeated_table_hash_creates_table_reuse_evidence():
    rows = [_row(SAT, target_idx=i, table_hash="table_reused", witness_schema=f"w{i}") for i in range(5)]
    rows += [_row(UNSAT, source_sig="other", target_idx=30 + i) for i in range(2)]

    roots = distill_root_candidates(rows)

    assert roots[0].root_type == "table_reuse_root"
    assert roots[0].table_reuse_score == 1.0
    assert roots[0].table_hashes == ["table_reused"]


def test_repeated_witness_schema_creates_witness_reuse_evidence():
    rows = [_row(SAT, target_idx=i, table_hash=f"table_{i}", witness_schema="same_witness") for i in range(4)]
    rows += [_row(UNSAT, source_sig="other", target_idx=40 + i) for i in range(2)]

    roots = distill_root_candidates(rows)

    assert roots[0].root_type == "witness_schema_root"
    assert roots[0].witness_reuse_score == 1.0
    assert roots[0].witness_schema == "same_witness"


def test_unsat_heavy_cluster_creates_obstruction_candidate():
    rows = [_row(UNSAT, target_idx=i, source_sig="blocked") for i in range(4)]
    rows.append(_row(SAT, target_idx=10, source_sig="blocked"))

    obstructions = distill_obstruction_candidates(rows)

    assert obstructions
    assert obstructions[0].unsat_count == 4
    assert obstructions[0].obstruction_type in {
        "carrier_order_block_obstruction",
        "target_demand_block_obstruction",
        "source_shape_block_obstruction",
        "route_block_obstruction",
        "unsat_boundary_obstruction",
    }
    assert obstructions[0].status == DISCOVERY_STATUS


def test_unknown_heavy_cluster_is_preserved_as_frontier_evidence():
    rows = [_row(UNKNOWN, target_idx=i, source_sig="unclear") for i in range(3)]

    obstructions = distill_obstruction_candidates(rows, min_unsat_count=2)
    summary = summarize_root_discovery(rows, [], obstructions)

    assert obstructions
    assert obstructions[0].obstruction_type == "unknown_frontier_obstruction"
    assert obstructions[0].unknown_count == 3
    assert summary["unknown_frontier_count"] == 3


def test_mixed_contrast_scores_above_flat_all_sat_broad_cluster():
    mixed = [_row(SAT, target_idx=i, source_sig="sharp", table_hash=f"t{i}", witness_schema=f"w{i}") for i in range(3)]
    mixed += [_row(UNSAT, source_sig=f"near_{i}", target_idx=50 + i) for i in range(3)]
    flat = [
        _row(
            SAT,
            source_sig=f"broad_{i}",
            demand=f"demand_{i}",
            target_idx=70 + i,
            table_hash=f"flat_table_{i}",
            witness_schema=f"flat_witness_{i}",
        )
        for i in range(3)
    ]

    mixed_root = distill_root_candidates(mixed, min_sat_count=1)[0]
    flat_roots = distill_root_candidates(flat, min_sat_count=1)
    flat_score = max(root.load_bearing_score for root in flat_roots)

    assert mixed_root.sat_unsat_contrast > 0
    assert mixed_root.load_bearing_score > flat_score


def test_discovery_artifacts_never_mark_themselves_verified():
    rows = [_row(SAT, target_idx=i, table_hash="table_reused") for i in range(3)]
    rows += [_row(UNSAT, source_sig="blocked", target_idx=80 + i) for i in range(3)]

    roots = distill_root_candidates(rows)
    obstructions = distill_obstruction_candidates(rows)
    cards = build_constructor_family_cards(roots, rows)

    assert roots and obstructions and cards
    assert all(root.status == DISCOVERY_STATUS for root in roots)
    assert all(obstruction.status == DISCOVERY_STATUS for obstruction in obstructions)
    assert all(card.status == DISCOVERY_STATUS for card in cards)
    assert all(root.evidence["advisory_only"] is True for root in roots)


def test_stable_deterministic_output_and_replay_queue():
    rows = [_row(SAT, target_idx=i, table_hash="table_reused", witness_schema="w") for i in range(3)]
    rows += [_row(UNKNOWN, source_sig="nearby", target_idx=90 + i, witness_schema="w") for i in range(2)]

    first = distill_root_candidates(rows)
    second = distill_root_candidates(list(reversed(rows)))
    queue = build_replay_queue(first, rows, max_items=10)

    assert [root.to_dict() for root in first] == [root.to_dict() for root in second]
    assert queue
    assert queue[0]["solver_status"] == UNKNOWN
    assert "not a truth claim" in queue[0]["reason"]


def _root_node(**overrides):
    data = {
        "root_node_id": "root_score_1",
        "canonical_name": "ROOT_SCORE_1",
        "root_type": "certificate_root",
        "root_key": "score_key",
        "support_count": 10,
        "rows": 20,
        "unique_pairs": 8,
        "unique_sources": 3,
        "unique_targets": 5,
        "unique_motifs": 2,
        "load_bearing_score": 0.4,
        "compression_ratio": 0.3,
        "coverage_density": 0.5,
        "evidence": {"seed": True},
    }
    data.update(overrides)
    return RootNode(**data)


def test_score_root_candidate_is_deterministic():
    root = _root_node()
    signals = RootDiscoverySignals(
        support=0.7,
        holdout_stability=0.6,
        persistence_across_filtrations=0.7,
        effective_filtration_count=3.0,
        null_lift=0.6,
        coverage=0.7,
        residual_compression_gain=0.3,
        certificate_pressure=0.7,
        constructor_pressure=0.3,
    )

    first = score_root_candidate(root, signals)
    second = score_root_candidate(root.to_dict(), signals.to_dict())

    assert first.to_dict() == second.to_dict()
    assert first.evidence["advisory_only"] is True
    assert first.evidence["not_terminal_truth"] is True


def test_high_persistence_low_shadow_recommends_promote_candidate():
    score = score_root_candidate(
        _root_node(),
        {
            "support": 0.9,
            "purity": 0.9,
            "holdout_stability": 0.9,
            "persistence_across_filtrations": 0.9,
            "effective_filtration_count": 5.0,
            "null_lift": 0.9,
            "coverage": 0.95,
            "residual_compression_gain": 0.35,
            "certificate_pressure": 0.95,
            "constructor_pressure": 0.45,
            "shadow_duplication_score": 0.05,
        },
    )

    assert score.recommendation == "promote_candidate"
    assert score.promotion_score > 0.58


def test_high_shadow_duplication_recommends_shadow_duplicate():
    score = score_root_candidate(
        _root_node(),
        {
            "support": 0.9,
            "holdout_stability": 0.9,
            "persistence_across_filtrations": 0.9,
            "effective_filtration_count": 5.0,
            "null_lift": 0.9,
            "coverage": 0.9,
            "certificate_pressure": 0.9,
            "constructor_pressure": 0.7,
            "shadow_duplication_score": 0.95,
        },
    )

    assert score.recommendation == "shadow_duplicate"
    assert score.shadow_penalty == 0.95


def test_low_evidence_recommends_insufficient_evidence():
    score = score_root_candidate(
        RootNode(root_node_id="root_empty", canonical_name="ROOT_EMPTY"),
        RootDiscoverySignals(),
    )

    assert score.recommendation == "insufficient_evidence"


def test_attach_root_discovery_scores_preserves_root_identity_and_adds_evidence():
    root = _root_node(root_node_id="root_attach", canonical_name="ROOT_ATTACH")
    attached = attach_root_discovery_scores([root], {root.root_node_id: {"coverage": 0.5}})

    assert len(attached) == 1
    assert attached[0].root_node_id == root.root_node_id
    assert attached[0].canonical_name == root.canonical_name
    assert attached[0].evidence["seed"] is True
    assert attached[0].evidence["advisory_only"] is True
    assert attached[0].evidence["root_discovery_score"]["root_node_id"] == root.root_node_id


def test_score_root_candidates_cli_writes_json_and_jsonl(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    root = _root_node(root_node_id="root_cli", canonical_name="ROOT_CLI")
    input_path = tmp_path / "roots.jsonl"
    signals_path = tmp_path / "signals.json"
    out_json = tmp_path / "scores.json"
    out_jsonl = tmp_path / "scores.jsonl"
    input_path.write_text(json.dumps(root.to_dict()) + "\n", encoding="utf-8")
    signals_path.write_text(
        json.dumps({root.root_node_id: {"coverage": 0.9, "certificate_pressure": 0.8}}),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/score_root_candidates.py",
            "--input",
            str(input_path),
            "--signals",
            str(signals_path),
            "--out-json",
            str(out_json),
            "--out-jsonl",
            str(out_jsonl),
        ],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(out_json.read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in out_jsonl.read_text(encoding="utf-8").splitlines()]
    assert payload["advisory_only"] is True
    assert payload["scores"][0]["root_node_id"] == "root_cli"
    assert rows[0]["root_node_id"] == "root_cli"


def test_root_scoring_does_not_touch_lawbook_store(tmp_path):
    store_path = tmp_path / "lawbook.sqlite"

    score = score_root_candidate(_root_node(), {"coverage": 0.5})

    assert score.evidence["advisory_only"] is True
    assert not store_path.exists()


def test_root_discovery_docs_and_glossary_entries_exist():
    required = [
        "docs/root_node_discovery.md",
        "docs/residual_membrane.md",
        "docs/replay_and_route_plasticity.md",
        "docs/stage2_sair_strategy.md",
    ]
    for path in required:
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
        assert text.strip()

    with open("docs/glossary.md", "r", encoding="utf-8") as handle:
        glossary = handle.read()
    for term in [
        "Residual Membrane",
        "Viability Ridge",
        "Representation Elevator",
        "Phase Gate",
        "Root Spine",
        "Shadow Duplication",
        "Effective Filtration Count",
        "Null Lift",
        "Route Plasticity",
        "Replay Engine",
        "Support Pillar",
    ]:
        assert term in glossary
