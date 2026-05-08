import json
import subprocess
import sys

from mathgraph.persistent_filtration import build_filtration_evidence, summarize_persistence
from mathgraph.root_compiler import compile_constructor_plans
from mathgraph.root_discovery import SAT, UNKNOWN, UNSAT, distill_root_candidates
from mathgraph.root_promotion import RootPromotionPolicy, promote_roots
from mathgraph.root_shadow_collapse import collapse_root_shadows


def _row(status, i, source="source_a", demand="demand_a", table="table_a", witness="witness_a"):
    return {
        "run_id": "run",
        "obstruction_surface_id": "surface_a",
        "source_idx": i,
        "target_idx": 100 + i,
        "source_equation": f"s{i}",
        "target_equation": f"t{i}",
        "carrier_order": 2,
        "solver_status": status,
        "certificate_id": f"cert_{i}" if status == SAT else None,
        "table_hash": table if status == SAT else None,
        "witness_schema": witness if status == SAT else None,
        "source_signature": source,
        "target_signature": f"target_{i}",
        "target_demand_signature": demand,
        "route": "symbolic_complete",
        "metadata": {"residual_compression_gain": 0.4, "replay_gain": 2.0},
    }


def _roots_and_rows():
    rows = [_row(SAT, i) for i in range(5)]
    rows += [_row(UNSAT, 20 + i, source=f"near_{i}", table=None, witness=None) for i in range(4)]
    rows += [_row(UNKNOWN, 40 + i, source=f"frontier_{i}", table=None, witness=None) for i in range(2)]
    roots = distill_root_candidates(rows, min_sat_count=2)
    return roots, rows


def test_persistent_filtration_scores_mixed_boundary_rows():
    roots, rows = _roots_and_rows()

    evidence = build_filtration_evidence(rows, roots)
    summaries = summarize_persistence(roots, evidence)

    assert evidence
    assert summaries[0].effective_filtration_count >= 2.0
    assert summaries[0].persistence_score > 2.0
    assert summaries[0].evidence["advisory_only"] is True


def test_shadow_collapse_preserves_alias_for_duplicate_root():
    roots, _ = _roots_and_rows()
    duplicate = roots[0].to_dict()
    duplicate["root_node_id"] = "shadow_root"
    duplicate["canonical_name"] = "ROOT_SHADOW_ALIAS"
    duplicate["load_bearing_score"] = roots[0].load_bearing_score - 0.5

    result = collapse_root_shadows([roots[0], duplicate], overlap_threshold=0.7)

    assert len(result.canonical_roots) == 1
    assert result.shadow_links
    assert result.alias_records
    assert result.canonical_by_shadow["shadow_root"] == roots[0].root_node_id


def test_root_promotion_refuses_shadows_and_promotes_persistent_non_shadow():
    roots, rows = _roots_and_rows()
    duplicate = roots[0].to_dict()
    duplicate["root_node_id"] = "shadow_root"
    duplicate["canonical_name"] = "ROOT_SHADOW_ALIAS"
    all_roots = [roots[0], duplicate]
    evidence = build_filtration_evidence(rows, all_roots)
    persistence = summarize_persistence(all_roots, evidence)
    shadows = collapse_root_shadows(all_roots, overlap_threshold=0.7)

    records = promote_roots(
        all_roots,
        persistence,
        shadows,
        policy=RootPromotionPolicy(min_persistence_score=1.0, min_effective_filtration_count=1.0),
    )

    by_id = {record.root_node_id: record for record in records}
    assert by_id[roots[0].root_node_id].promoted is True
    assert by_id["shadow_root"].promoted is False
    assert by_id["shadow_root"].status == "retired_shadow"


def test_root_compiler_creates_advisory_constructor_plan_only():
    roots, rows = _roots_and_rows()
    evidence = build_filtration_evidence(rows, roots)
    persistence = summarize_persistence(roots, evidence)
    shadows = collapse_root_shadows(roots)
    records = promote_roots(
        roots,
        persistence,
        shadows,
        policy=RootPromotionPolicy(min_persistence_score=1.0, min_effective_filtration_count=1.0),
    )

    plans = compile_constructor_plans(roots, records, rows=rows)

    assert plans
    assert plans[0].advisory_only is True
    assert "not a certificate" in plans[0].verifier_requirements[-1]
    assert plans[0].constructor_type.endswith("_constructor")


def test_root_discovery_cycle_cli_smoke(tmp_path):
    roots, rows = _roots_and_rows()
    telemetry = tmp_path / "telemetry.jsonl"
    roots_json = tmp_path / "roots.json"
    out_dir = tmp_path / "cycle"
    telemetry.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    roots_json.write_text(json.dumps([root.to_dict() for root in roots], sort_keys=True), encoding="utf-8")

    proc = subprocess.run(
        [
            sys.executable,
            "scripts/run_root_discovery_cycle.py",
            "--telemetry-jsonl",
            str(telemetry),
            "--roots-json",
            str(roots_json),
            "--out-dir",
            str(out_dir),
        ],
        text=True,
        capture_output=True,
    )

    assert proc.returncode == 0, proc.stderr
    summary = json.loads((out_dir / "root_discovery_cycle_summary.json").read_text(encoding="utf-8"))
    assert summary["advisory_only"] is True
    assert summary["verifier_boundary_unchanged"] is True
    assert (out_dir / "constructor_plans.json").exists()
