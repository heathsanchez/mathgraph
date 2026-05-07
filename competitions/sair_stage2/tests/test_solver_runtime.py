from competitions.sair_stage2.src.solver_runtime import solve, solve_problem


def test_solver_true_false_unknown():
    assert solve("x * y = x", "a * b = a")["verdict"] == "TRUE"
    false = solve("x = x", "x * x = x")
    assert false["verdict"] == "FALSE"
    assert false["terminal_form"] == "FINITE_COUNTERMODEL"
    unknown = solve("(x * y) * z = x * (y * z)", "x * y = y * x")
    assert unknown["verdict"] in {"FALSE", "UNKNOWN"}
    assert solve_problem({"equation1": "x = x", "equation2": "y = y"})["verdict"] == "TRUE"

