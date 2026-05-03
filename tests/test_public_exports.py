def test_task_planner_public_exports() -> None:
    from mathgraph import CertificateTask
    from mathgraph import plan_certificate_task
    from mathgraph import plan_many_certificate_tasks

    assert CertificateTask.__name__ == "CertificateTask"
    assert callable(plan_certificate_task)
    assert callable(plan_many_certificate_tasks)


def test_task_runner_public_exports() -> None:
    from mathgraph import TaskOutcome
    from mathgraph import TaskRunSummary
    from mathgraph import execute_certificate_task
    from mathgraph import execute_many_certificate_tasks
    from mathgraph import read_outcomes_json
    from mathgraph import read_outcomes_jsonl
    from mathgraph import residual_outcomes
    from mathgraph import summarize_task_outcomes
    from mathgraph import write_outcomes_json
    from mathgraph import write_outcomes_jsonl

    assert TaskOutcome.__name__ == "TaskOutcome"
    assert TaskRunSummary.__name__ == "TaskRunSummary"
    assert callable(execute_certificate_task)
    assert callable(execute_many_certificate_tasks)
    assert callable(summarize_task_outcomes)
    assert callable(residual_outcomes)
    assert callable(read_outcomes_json)
    assert callable(write_outcomes_json)
    assert callable(read_outcomes_jsonl)
    assert callable(write_outcomes_jsonl)
