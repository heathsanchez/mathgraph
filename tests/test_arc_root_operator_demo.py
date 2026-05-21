from mathgraph.arc_root_operator_demo import base_search, generate_demo_tasks, run_arc_root_operator_demo


def test_demo_task_generation_deterministic():
    assert [task.to_dict() for task in generate_demo_tasks()] == [task.to_dict() for task in generate_demo_tasks()]


def test_base_search_solves_simple_primitive_tasks():
    tasks = generate_demo_tasks()
    metrics = base_search(tasks)
    assert "t6" in metrics["solved"]


def test_root_schema_library_improves_over_base_on_tiny_held_out():
    summary = run_arc_root_operator_demo()
    assert summary["root_schema_solve_rate"] >= summary["base_solve_rate"]
    assert summary["promoted_schema_count"] >= 1


def test_smoke_output_contains_expected_fields(tmp_path):
    out = tmp_path / "smoke.json"
    summary = run_arc_root_operator_demo(out)
    assert out.exists()
    for key in ("overall", "base_solve_rate", "root_schema_solve_rate", "oracle_fraction_captured"):
        assert key in summary
