import json
import subprocess
import sys
from pathlib import Path

from mathgraph.mathlib_digest import *

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "examples" / "mathlib_digest_nat_small" / "config.json"


def test_config_parsers_and_classifiers():
    cfg = load_digest_config(CONFIG)
    assert cfg.pack_id == "nat_basic_focused_v1"
    assert len(cfg.target_names()) == 14
    out = "Nat.succ_injective : Function.Injective Nat.succ\n[propext, Classical.choice]\nEq.mpr Nat.add_comm HAdd.hAdd _private.foo target._proof"
    assert parse_check_type(out, "Nat.succ_injective").startswith("Nat.succ_injective")
    assert parse_axioms(out) == ["Classical.choice", "propext"]
    assert classify_reference("Eq.mpr", target="Nat.succ_injective") == "equality_transport_root"
    assert classify_reference("HAdd.hAdd", target="Nat.succ_injective") == "typeclass_or_notation_root"
    refs = extract_reference_hints(out, "Nat.succ_injective")
    assert "Function.Injective" in refs


def test_constructor_templates_and_obstruction_classifier():
    roots = ["Eq.mpr", "Nat.add_comm", "HAdd.hAdd", "Foo.bar", "_private.x"]
    assert valid_simp_roots(roots) == ["Nat.add_comm", "Foo.bar"]
    assert "exact Nat.succ_injective" in constructor_proof_body("exact_existing", "Nat.succ_injective", roots)
    assert "Nat.add_comm" in constructor_proof_body("simp_all_refs", "Nat.succ_injective", roots)
    assert classify_constructor_error("unsolved goals") == "unsolved_goals"
    assert classify_constructor_error("unknown identifier") == "unknown_reference"
    assert classify_constructor_error("", returncode=0) == "verified"


def test_accumulator_cli_dry_run_without_lean(tmp_path):
    db = tmp_path / "lawbook.sqlite"
    out = tmp_path / "runs"
    p = subprocess.run(
        [
            sys.executable,
            "scripts/run_mathlib_digest_accumulator.py",
            "--lawbook",
            str(db),
            "--pack-config",
            str(CONFIG),
            "--out-base",
            str(out),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "MathGraph Mathlib Digest Accumulator" in p.stdout
    assert db.exists()
    summaries = list(out.glob("*/digest_summary.json"))
    assert summaries
    data = json.loads(summaries[0].read_text())
    assert data["target_count"] == 14
    assert data["accepted_target_count"] == 0
