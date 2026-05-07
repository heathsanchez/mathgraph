import json
import subprocess
import sys

from mathgraph.metabolic_cycle import MetabolicCycleConfig, run_metabolic_cycle


def test_cycle_query_integration(tmp_path):
    db = tmp_path / "cycle.sqlite"
    out_dir = tmp_path / "cycle"
    result = run_metabolic_cycle(MetabolicCycleConfig(store_path=str(db), out_dir=str(out_dir)))

    summary = subprocess.run(
        [sys.executable, "scripts/query_lawbook.py", "--db", str(db), "--summary"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "primitive" in json.loads(summary.stdout)

    recent = subprocess.run(
        [sys.executable, "scripts/query_lawbook.py", "--db", str(db), "--recent-certificates", "5"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "truth_boundary" in json.loads(recent.stdout)

    next_frontier = subprocess.run(
        [
            sys.executable,
            "scripts/query_lawbook.py",
            "--db",
            str(db),
            "--next-frontier",
            result.artifacts["next_frontier"],
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert isinstance(json.loads(next_frontier.stdout), list)

