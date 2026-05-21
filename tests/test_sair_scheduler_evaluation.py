import json

import pandas as pd

from mathgraph.sair_constructor_bank import attach_preferred_constructors
from mathgraph.sair_scheduler_evaluation import (
    SAIRSchedulerEvalConfig,
    compute_constructor_entropy,
    compute_oracle_fraction_captured,
    compute_residual_compression,
    evaluate_scheduler_policies,
)


def _tasks():
    rows = [
        {"task_id": "p1", "family": "projection_pressure", "source_equation": "(x * x) = x", "target_equation": "(x * y) = (y * x)"},
        {"task_id": "p2", "family": "projection_pressure", "source_equation": "(x * x) = x", "target_equation": "(x * y) = x"},
        {"task_id": "c1", "family": "collapse_or_constant_pressure", "source_equation": "((x * y) * z) = (x * (y * z))", "target_equation": "(x * x) = x"},
    ]
    return attach_preferred_constructors(rows)


def _motifs():
    return pd.DataFrame(
        [
            {"motif_id": "m1", "atoms_json": json.dumps(["constructor:left_projection_n2", "basin:projection_pressure"]), "support": 3, "score": 5.0, "advisory_only": True},
            {"motif_id": "m2", "atoms_json": json.dumps(["constructor:constant_n2_0", "basin:collapse_or_constant_pressure"]), "support": 2, "score": 4.0, "advisory_only": True},
        ]
    )


def test_scheduler_policies_run_and_guided_ties_or_beats_base():
    report = evaluate_scheduler_policies(_tasks(), _motifs(), SAIRSchedulerEvalConfig(attempt_budget=8))
    assert report.overall == "PASS"
    by_policy = {row["policy"]: row for row in report.policy_results}
    assert by_policy["clean_motif_guided_order"]["certificate_yield"] >= by_policy["base_constructor_order"]["certificate_yield"]
    assert by_policy["reason_atlas_guided_order"]["certificate_yield"] >= by_policy["base_constructor_order"]["certificate_yield"]


def test_metrics_helpers():
    assert compute_oracle_fraction_captured(0.2, 0.6, 1.0) == 0.49999999999999994
    assert compute_residual_compression(10, 4) == 6
    assert compute_constructor_entropy(["a", "a", "b"]) > 0


def test_policy_outputs_are_advisory():
    report = evaluate_scheduler_policies(_tasks(), _motifs(), SAIRSchedulerEvalConfig(attempt_budget=4))
    assert all(row["advisory_only"] for row in report.policy_results)
    assert all(row["advisory_only"] for row in report.task_results)
    text = json.dumps(report.to_dict())
    assert "VERIFIED_PROOF" not in text
