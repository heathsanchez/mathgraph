"""Synthetic frontier data for the v16.12 metabolic cycle testbed."""

from __future__ import annotations

import random
from typing import Any


def build_synthetic_metabolic_frontier(
    limit: int | None = None,
    random_seed: int = 42,
) -> list[dict[str, Any]]:
    """Return a deterministic SAIR/ETP-like frontier for local cycle tests.

    The rows deliberately mix structural proofs, finite-countermodel-friendly
    implications, and residual pressure. They are examples for exercising the
    loop, not a benchmark universe.
    """

    rows: list[dict[str, Any]] = [
        {
            "task_id": "synthetic_cycle_0001_structural_exact",
            "source": "x = x",
            "target": "x = x",
            "source_idx": 1001,
            "target_idx": 1001,
            "route": "structural_exact",
            "task_kind": "structural_true",
            "terminal_goal": "VERIFIED_PROOF",
            "priority": 1.0,
            "candidate_origin": "synthetic_v16_12",
            "label": "reflexive exact proof",
        },
        {
            "task_id": "synthetic_cycle_0002_alpha_true",
            "source": "x * y = x",
            "target": "a * b = a",
            "source_idx": 1002,
            "target_idx": 1003,
            "route": "structural_variable_renaming",
            "task_kind": "structural_true",
            "terminal_goal": "VERIFIED_PROOF",
            "priority": 0.95,
            "candidate_origin": "synthetic_v16_12",
            "label": "alpha-equivalent implication",
        },
        {
            "task_id": "synthetic_cycle_0003_projection_false",
            "source": "x * y = x",
            "target": "x * y = y",
            "source_idx": 1002,
            "target_idx": 1004,
            "route": "finite_countermodel",
            "task_kind": "finite_countermodel_search",
            "terminal_goal": "FINITE_COUNTERMODEL",
            "priority": 0.9,
            "candidate_origin": "synthetic_v16_12",
            "label": "projection-left does not force projection-right",
        },
        {
            "task_id": "synthetic_cycle_0004_projection_deep_false",
            "source": "x * y = x",
            "target": "x * (y * z) = z",
            "source_idx": 1002,
            "target_idx": 1005,
            "route": "finite_countermodel",
            "task_kind": "finite_countermodel_search",
            "terminal_goal": "FINITE_COUNTERMODEL",
            "priority": 0.85,
            "candidate_origin": "synthetic_v16_12",
            "label": "projection-left does not force right tail",
        },
        {
            "task_id": "synthetic_cycle_0005_idempotence_false",
            "source": "x = x",
            "target": "x * x = x",
            "source_idx": 1001,
            "target_idx": 1010,
            "route": "finite_countermodel",
            "task_kind": "finite_countermodel_search",
            "terminal_goal": "FINITE_COUNTERMODEL",
            "priority": 0.82,
            "candidate_origin": "synthetic_v16_12",
            "label": "trivial equation does not force idempotence",
        },
        {
            "task_id": "synthetic_cycle_0006_idempotent_motif",
            "source": "x * x = x",
            "target": "x * (x * x) = x",
            "source_idx": 1006,
            "target_idx": 1007,
            "route": "proof_motif_candidate",
            "task_kind": "proof_motif_candidate",
            "terminal_goal": "VERIFIED_PROOF",
            "priority": 0.7,
            "candidate_origin": "synthetic_v16_12",
            "label": "idempotent repetition proof-shape candidate",
        },
        {
            "task_id": "synthetic_cycle_0007_assoc_to_comm_residual",
            "source": "(x * y) * z = x * (y * z)",
            "target": "x * y = y * x",
            "source_idx": 1008,
            "target_idx": 1009,
            "route": "residual_probe",
            "task_kind": "residual_probe",
            "terminal_goal": "UNKNOWN_OR_OBSTRUCTION",
            "priority": 0.55,
            "candidate_origin": "synthetic_v16_12",
            "label": "associativity does not obviously force commutativity",
        },
    ]
    rng = random.Random(random_seed)
    for row in rows:
        row["priority_jitter"] = round(rng.random() * 0.0001, 8)
    selected = rows[:limit] if limit is not None else rows
    return [dict(row) for row in selected]
