import csv
import json

import numpy as np

from mathgraph.sair_compounding_loop import (
    build_fallback_demo_tasks,
    run_sair_compounding_loop,
    sample_real_etp_light_tasks,
)


def test_fallback_demo_emits_sair_outputs_and_preserves_boundaries(tmp_path) -> None:
    report = run_sair_compounding_loop(tmp_path / "run", fallback_demo=True, seed=1729)
    assert report.mode == "fallback-demo"
    assert report.task_count == len(build_fallback_demo_tasks())
    assert report.lawbook_hit_rate > 0.0
    assert report.action_change_rate > 0.0
    assert report.decode_supported_rate > 0.0
    assert report.candidate_certificate_count > 0
    assert report.verified_certificate_count == 1
    assert report.prohibited_promotion_count == 0
    assert report.failed_search_promoted_to_true_count == 0
    assert report.advisory_boundary_ok is True

    out = tmp_path / "run"
    for name in (
        "sair_compounding_report.json",
        "sair_compounding_report.md",
        "sair_policy_eval.csv",
        "sair_task_ledger.csv",
        "sair_residual_delta.csv",
        "sair_boundary_audit.csv",
    ):
        assert (out / name).exists()

    data = json.loads((out / "sair_compounding_report.json").read_text(encoding="utf-8"))
    assert data["failed_search_promoted_to_true_count"] == 0
    assert data["advisory_boundary_ok"] is True
    report_md = (out / "sair_compounding_report.md").read_text(encoding="utf-8")
    assert "advisory route memory is not truth" in report_md
    assert "Failed finite search is never TRUE" in report_md

    audit = list(csv.DictReader((out / "sair_boundary_audit.csv").open(encoding="utf-8")))
    assert audit
    assert {row["advisory_boundary_ok"] for row in audit} == {"True"}
    assert {row["failed_search_promoted_to_true"] for row in audit} == {"False"}


def test_real_etp_light_sampling_is_bounded_and_reproducible(tmp_path) -> None:
    equations = tmp_path / "equations.txt"
    equations.write_text("\n".join(["x=x", "x*y=x", "x*y=y", "(x*y)*z=x*(y*z)"]) + "\n", encoding="utf-8")
    matrix = np.asarray(
        [
            [True, True, False, True],
            [False, True, False, True],
            [True, False, True, False],
            [False, True, False, True],
        ],
        dtype=bool,
    )
    matrix_path = tmp_path / "matrix.npy"
    np.save(matrix_path, matrix)

    first = sample_real_etp_light_tasks(equations, matrix_path, seed=7, sample_size=4)
    second = sample_real_etp_light_tasks(equations, matrix_path, seed=7, sample_size=4)
    assert [row.to_dict() for row in first] == [row.to_dict() for row in second]
    assert len(first) == 4
    assert {row.matrix_label for row in first} == {"FALSE", "TRUE"}
    assert all(row.finite_checked_witness is False for row in first)

    report = run_sair_compounding_loop(
        tmp_path / "real",
        equations_path=equations,
        matrix_path=matrix_path,
        seed=7,
        sample_size=4,
    )
    assert report.mode == "real-etp-light"
    assert report.task_count == 4
    assert report.verified_certificate_count == 0
    assert report.prohibited_promotion_count == 0
    assert report.failed_search_promoted_to_true_count == 0
    assert report.advisory_boundary_ok is True
