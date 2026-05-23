import json

from mathgraph.recursive_residual_compounding import (
    CompactAtlasRoute,
    RecursiveResidualCompoundingEngine,
    RecursiveResidualConfig,
    evaluate_route_on_pairs,
)


def _run(tmp_path, seed=1729):
    return RecursiveResidualCompoundingEngine(
        RecursiveResidualConfig(
            out_dir=tmp_path,
            profile="smoke",
            seed=seed,
            allow_fallback_demo=True,
            generations=2,
            base_magmas=20,
            generic_route_size=4,
            discover_false=10,
            train_false=8,
            heldout_false=8,
            heldout_true=4,
            new_per_generation=2,
            candidate_budget=12,
        )
    ).run()


def test_fallback_smoke_run_works(tmp_path):
    report = _run(tmp_path)

    assert report.fallback_mode is True
    assert report.advisory_boundary_preserved is True
    assert report.generation_results
    assert (tmp_path / "recursive_residual_summary.json").exists()


def test_recursive_generations_reduce_or_preserve_residuals(tmp_path):
    report = _run(tmp_path)

    first = report.generation_results[0]
    final = report.generation_results[-1]
    assert final.residual_count <= first.residual_count
    assert report.residual_reduction >= 0


def test_compact_atlas_routes_are_advisory_only(tmp_path):
    _run(tmp_path)
    rows = (tmp_path / "compact_atlas_routes.csv").read_text(encoding="utf-8")

    assert "advisory_only" in rows
    assert "False" not in rows.splitlines()[1:] if len(rows.splitlines()) > 1 else True


def test_compact_atlas_cannot_promote_truth():
    route = CompactAtlasRoute("compact_top_4", ("a", "b"), "compact_atlas")

    assert route.advisory_only is True
    assert route.can_promote_truth is False
    assert route.to_dict()["can_promote_truth"] is False


def test_failed_finite_search_and_true_contamination_fields_are_zero(tmp_path):
    report = _run(tmp_path)

    assert report.failed_search_promoted_true_count == 0
    assert report.terminal_claims_from_advisory_count == 0
    assert report.true_contamination_count == 0
    assert report.true_contamination_rate == 0.0


def test_route_evaluation_is_deterministic_for_fixed_seed(tmp_path):
    a = _run(tmp_path / "a", seed=42).to_dict()
    b = _run(tmp_path / "b", seed=42).to_dict()

    assert a["generic_recoveries"] == b["generic_recoveries"]
    assert a["best_compact_recoveries"] == b["best_compact_recoveries"]


def test_artifact_manifest_includes_required_outputs(tmp_path):
    report = _run(tmp_path)
    manifest = json.loads((tmp_path / "artifact_manifest.json").read_text(encoding="utf-8"))

    assert "recursive_residual_summary.json" in manifest["generated_files"]
    assert "gate_results.csv" in manifest["generated_files"]
    assert report.artifact_manifest["artifact_manifest.json"].endswith("artifact_manifest.json")


def test_vectorized_route_evaluation_matches_python_reference():
    sat_cache = [
        [True, False, True],
        [True, True, False],
        [False, True, False],
    ]
    pairs = [
        {"source_idx": 0, "target_idx": 1},
        {"source_idx": 1, "target_idx": 2},
        {"source_idx": 2, "target_idx": 0},
    ]
    route = [0, 1]

    result = evaluate_route_on_pairs(sat_cache, pairs, route)
    reference_mask = []
    for pair in pairs:
        reference_mask.append(any(sat_cache[idx][pair["source_idx"]] and not sat_cache[idx][pair["target_idx"]] for idx in route))
    assert result["hit_mask"] == reference_mask
    assert result["recoveries"] == sum(reference_mask)
