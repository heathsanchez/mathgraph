"""Built-in deterministic corpus for MathGraph Breakthrough Loop v1."""

from __future__ import annotations

from mathgraph.finite_magma_world import (
    add_mod_n,
    commutative_nonassociative_3,
    constant_table,
    deterministic_perturbation_3,
    left_projection,
    max_table,
    min_table,
    rectangular_band,
    right_projection,
    sub_mod_n,
    xor_mod_2,
)


def builtin_constructor_families() -> dict[str, tuple[tuple[int, ...], ...]]:
    return {
        "left_projection_2": left_projection(2),
        "constant0_2": constant_table(2, 0),
        "right_projection_2": right_projection(2),
        "xor_mod_2": xor_mod_2(),
        "add_mod_3": add_mod_n(3),
        "sub_mod_3": sub_mod_n(3),
        "min_3": min_table(3),
        "max_3": max_table(3),
        "rectangular_band_4": rectangular_band(4),
        "comm_nonassoc_3": commutative_nonassociative_3(),
        "perturbation_3": deterministic_perturbation_3(),
    }


def builtin_breakthrough_tasks() -> list[dict[str, str]]:
    tasks = [
        ("proj_comm_1", "projection_refutable", "(x * x) = x", "(x * y) = (y * x)"),
        ("proj_comm_2", "projection_refutable", "(x * x) = x", "((x * y) * y) = ((y * x) * x)"),
        ("assoc_idem_1", "constant_refutable", "((x * y) * z) = (x * (y * z))", "(x * x) = x"),
        ("assoc_idem_2", "constant_refutable", "((x * y) * z) = (x * (y * z))", "((x * x) * y) = y"),
        ("right_target_1", "right_projection_refutable", "(x * x) = x", "(x * y) = x"),
        ("right_target_2", "right_projection_refutable", "(x * x) = x", "((x * y) * z) = (x * z)"),
        ("comm_idem_1", "affine_refutable", "(x * y) = (y * x)", "(x * x) = x"),
        ("comm_idem_2", "affine_refutable", "(x * y) = (y * x)", "((x * x) * y) = y"),
        ("comm_assoc_1", "semilattice_refutable", "(x * y) = (y * x)", "((x * y) * z) = (x * (y * z))"),
        ("comm_assoc_2", "semilattice_refutable", "(x * y) = (y * x)", "((x * y) * x) = (x * (y * x))"),
        ("assoc_comm_1", "noncomm_assoc_refutable", "((x * y) * z) = (x * (y * z))", "(x * y) = (y * x)"),
        ("assoc_comm_2", "noncomm_assoc_refutable", "((x * y) * z) = (x * (y * z))", "(x * (y * z)) = (y * (x * z))"),
        ("residual_1", "hard_residual_or_unknown", "((x * y) * z) = (x * (y * z))", "((x * y) * z) = ((x * z) * y)"),
        ("residual_2", "true_or_not_refuted_small", "(x * y) = (x * y)", "(x * y) = (x * y)"),
    ]
    return [
        {"task_id": task_id, "family": family, "source_equation": source, "target_equation": target}
        for task_id, family, source, target in tasks
    ]


def expected_demo_fields() -> tuple[str, ...]:
    return (
        "overall",
        "episode_count",
        "initial_solved_or_refuted_count",
        "final_solved_or_refuted_count",
        "initial_residual_count",
        "final_residual_count",
        "accepted_terminal_certificates",
        "promotion_gate_accepted",
        "promotion_gate_rejected",
        "feedback_event_count",
        "breakthrough_score",
    )
