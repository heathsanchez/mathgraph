import csv
import subprocess
import sys


def test_heldout_benchmark_writes_exact_attribution_columns(tmp_path):
    out_dir = tmp_path / "heldout"
    subprocess.run(
        [
            sys.executable,
            "scripts/run_heldout_lawbook_compounding_benchmark.py",
            "--out-dir",
            str(out_dir),
            "--fallback-demo",
            "--seeds",
            "1729",
            "--train-pairs",
            "50",
            "--heldout-pairs",
            "50",
            "--true-pairs",
            "20",
            "--episodes",
            "2",
            "--repair-budget",
            "10",
            "--max-n",
            "3",
        ],
        check=True,
        text=True,
        capture_output=True,
    )

    rows = list(csv.DictReader((out_dir / "heldout_recovery_eval.csv").open(newline="", encoding="utf-8")))
    assert rows
    columns = set(rows[0])
    for column in [
        "generic_first_constructor_id",
        "heldout_lawbook_first_constructor_id",
        "lawbook_gain_hit",
        "lawbook_gain_constructor_family",
        "exact_attribution_available",
        "attribution_mode",
    ]:
        assert column in columns
    assert {row["attribution_mode"] for row in rows} == {"exact_constructor"}
