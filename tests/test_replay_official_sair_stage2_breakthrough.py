from __future__ import annotations

import subprocess
import sys

from scripts.replay_official_sair_stage2_breakthrough import build_replay_command


def test_help_runs():
    result = subprocess.run(
        [sys.executable, "scripts/replay_official_sair_stage2_breakthrough.py", "--help"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "--quick" in result.stdout
    assert "--full" in result.stdout


def test_default_command_has_strict_admission_and_fail_gate():
    command = build_replay_command(equations="/e.txt", matrix="/m.npy", out_dir="/out")
    assert "--strict-admission" in command
    assert "--max-n" in command
    assert "4" in command
    assert "--fail-if-no-compounding" in command
    assert "--train-false" in command
    assert command[command.index("--train-false") + 1] == "2500"


def test_quick_changes_budget_sizes():
    command = build_replay_command(equations="/e.txt", matrix="/m.npy", out_dir="/out", quick=True)
    assert command[command.index("--train-false") + 1] == "1000"
    assert command[command.index("--heldout-false") + 1] == "1000"
    assert command[command.index("--sample-true") + 1] == "500"
    assert command[command.index("--episodes") + 1] == "3"
    assert command[command.index("--policy-search-rounds") + 1] == "3"


def test_no_fail_flag_omits_fail_if_no_compounding():
    command = build_replay_command(equations="/e.txt", matrix="/m.npy", out_dir="/out", fail_if_no_compounding=False)
    assert "--fail-if-no-compounding" not in command
