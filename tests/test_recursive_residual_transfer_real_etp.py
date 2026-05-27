import json
import sqlite3
import subprocess
import sys

import numpy as np

from mathgraph.recursive_residual_transfer import (
    RealEtpTransferConfig,
    build_vectorized_sat_cache,
    compare_to_frozen_recursive_transfer_evidence,
    generate_base_magmas,
    load_frozen_recursive_transfer_evidence,
    load_etp_equations,
    load_etp_matrix,
    run_real_etp_recursive_residual_transfer,
    write_frozen_evidence_comparison,
)


def _tiny_inputs(tmp_path):
    equations = tmp_path / "equations.txt"
    equations.write_text(
        "\n".join(
            [
                "x = x",
                "x ◇ y = x",
                "x ∙ y = y",
                "x · x = x",
                "(x * y) * z = x * (y * z)",
                "x ⋆ y = y * x",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    matrix = np.zeros((6, 6), dtype=bool)
    matrix[:, 0] = True
    np.fill_diagonal(matrix, True)
    matrix_path = tmp_path / "matrix.npy"
    np.save(matrix_path, matrix)
    return equations, matrix_path


def test_real_etp_loader_normalizes_operators_and_loads_matrix(tmp_path) -> None:
    equations, matrix_path = _tiny_inputs(tmp_path)

    loaded = load_etp_equations(equations)
    matrix = load_etp_matrix(matrix_path)

    assert len(loaded) == 6
    assert loaded[1].to_string() == "x * y = x"
    assert matrix.shape == (6, 6)
    assert matrix.dtype == bool


def test_vectorized_sat_cache_matches_expected_projection_behavior(tmp_path) -> None:
    equations, _matrix_path = _tiny_inputs(tmp_path)
    loaded = load_etp_equations(equations)
    magmas = generate_base_magmas(
        RealEtpTransferConfig(equations, _matrix_path, tmp_path, profile="tiny", seeds=(1729,)).effective(),
        seed=1729,
    )
    by_source = {m.source: i for i, m in enumerate(magmas)}
    sat = build_vectorized_sat_cache(loaded, magmas)

    assert sat.shape == (len(magmas), len(loaded))
    assert bool(sat[by_source["left_projection"], 1]) is True
    assert bool(sat[by_source["left_projection"], 2]) is False
    assert bool(sat[by_source["right_projection"], 2]) is True
    assert bool(sat[by_source["right_projection"], 1]) is False


def test_real_etp_tiny_run_emits_full_artifacts_and_preserves_boundary(tmp_path) -> None:
    equations, matrix_path = _tiny_inputs(tmp_path)
    result = run_real_etp_recursive_residual_transfer(
        RealEtpTransferConfig(
            equations_path=equations,
            matrix_path=matrix_path,
            out_dir=tmp_path / "out",
            profile="tiny",
            seeds=(1729, 42),
            write_report=True,
        )
    )

    assert result.summary.real_etp_used is True
    assert result.summary.classification == "real_etp_recursive_residual_transfer"
    assert result.summary.advisory_boundary_ok is True
    assert result.route_evaluations
    assert all(row.advisory_only and not row.can_promote_truth for row in result.route_evaluations)
    for name in [
        "recursive_transfer_summary.json",
        "seed_summary.csv",
        "generation_summary.csv",
        "constructor_manifest.csv",
        "candidate_generation_scores.csv",
        "constructor_attribution.csv",
        "route_eval_by_seed_split.csv",
        "route_summary.csv",
        "best_compact_by_seed_split.csv",
        "gate_results.csv",
        "recursive_transfer_report.md",
        "recursive_transfer.sqlite",
    ]:
        assert (tmp_path / "out" / name).exists()
    payload = json.loads((tmp_path / "out" / "recursive_transfer_summary.json").read_text(encoding="utf-8"))
    assert payload["real_etp_used"] is True
    with sqlite3.connect(tmp_path / "out" / "recursive_transfer.sqlite") as con:
        tables = {row[0] for row in con.execute("select name from sqlite_master where type='table'")}
    assert {"generation_summary", "candidate_generation_scores", "route_summary"} <= tables


def test_cli_real_etp_smoke_with_tiny_inputs(tmp_path) -> None:
    equations, matrix_path = _tiny_inputs(tmp_path)
    out = tmp_path / "cli_out"

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/run_recursive_residual_transfer.py",
            "--equations",
            str(equations),
            "--matrix",
            str(matrix_path),
            "--out-dir",
            str(out),
            "--profile",
            "tiny",
            "--seeds",
            "1729",
            "42",
            "--real-etp",
            "--strict-advisory-boundary",
            "--write-report",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "real_etp_used: True" in completed.stdout
    assert json.loads((out / "recursive_transfer_summary.json").read_text(encoding="utf-8"))["real_etp_used"] is True


def test_frozen_evidence_loads_and_comparison_preserves_trust_boundary(tmp_path) -> None:
    frozen = load_frozen_recursive_transfer_evidence("recursive_residual_transfer_v1_20260523")
    assert frozen["original_run_id"] == "mathgraph_recursive_residual_transfer_v1_transfer_fast_20260523_055739"
    assert frozen["advisory_boundary_ok"] is True
    equations, matrix_path = _tiny_inputs(tmp_path)
    result = run_real_etp_recursive_residual_transfer(
        RealEtpTransferConfig(
            equations_path=equations,
            matrix_path=matrix_path,
            out_dir=tmp_path / "out",
            profile="tiny",
            seeds=(1729,),
            write_report=True,
        )
    )

    comparison = compare_to_frozen_recursive_transfer_evidence(result.summary, result.route_summary_rows, frozen)
    path = write_frozen_evidence_comparison(tmp_path / "out", comparison)

    assert (tmp_path / "out" / "frozen_evidence_comparison.json").exists()
    assert path.endswith("frozen_evidence_comparison.json")
    assert "reproduced_breakthrough_shape" in comparison
    assert "reproduced_original_magnitude" in comparison
    assert comparison["trust_boundary"]["advisory_boundary_ok"] is True
    assert comparison["trust_boundary"]["route_memory_advisory_only"] is True
    assert comparison["trust_boundary"]["can_promote_truth"] is False


def test_cli_real_etp_writes_frozen_evidence_comparison(tmp_path) -> None:
    equations, matrix_path = _tiny_inputs(tmp_path)
    out = tmp_path / "compare_out"

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/run_recursive_residual_transfer.py",
            "--equations",
            str(equations),
            "--matrix",
            str(matrix_path),
            "--out-dir",
            str(out),
            "--profile",
            "tiny",
            "--seeds",
            "1729",
            "--real-etp",
            "--compare-frozen-evidence",
            "recursive_residual_transfer_v1_20260523",
            "--strict-advisory-boundary",
            "--write-report",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads((out / "frozen_evidence_comparison.json").read_text(encoding="utf-8"))
    assert "frozen_evidence_comparison_json" in completed.stdout
    assert payload["frozen_original_run_id"] == "mathgraph_recursive_residual_transfer_v1_transfer_fast_20260523_055739"
    assert payload["trust_boundary"]["advisory_boundary_ok"] is True
