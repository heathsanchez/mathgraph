import json

import pandas as pd

from mathgraph.breakthrough_loop import BreakthroughLoop, BreakthroughLoopConfig
from mathgraph.breakthrough_demo import builtin_breakthrough_tasks
from mathgraph.sair_constructor_bank import attach_preferred_constructors, constructor_table_dict
from mathgraph.sair_motif_hygiene import (
    clean_breakthrough_trace_rows,
    extract_clean_mechanism_atoms,
    filter_to_accepted_finite_countermodel_rows,
    normalize_carrier_name,
    normalize_constructor_name,
    normalize_equation_shape_atoms,
    reject_leaky_or_junk_atom,
)


def _attempt_df(tmp_path):
    loop = BreakthroughLoop(
        attach_preferred_constructors(builtin_breakthrough_tasks()),
        constructor_table_dict(),
        BreakthroughLoopConfig(episodes=2, attempts_per_task=8, out_dir=tmp_path, reason_atlas_db=tmp_path / "ra.sqlite"),
    )
    loop.run()
    return pd.read_csv(tmp_path / "attempts.csv")


def test_junk_atoms_rejected():
    for atom in ("nan", "unknown_constructor", "carrier:nan", "hint:constructor", "success", "breakthrough-constructor-hint_abc", "{'x': 1}", "x = y"):
        rejected, _reason = reject_leaky_or_junk_atom(atom, reason=True)
        assert rejected


def test_valid_atoms_kept_and_inferred():
    assert normalize_constructor_name("left_projection_n2") == "left_projection_n2"
    assert normalize_carrier_name("left_projection_n2") == "n2"
    rejected, _reason = reject_leaky_or_junk_atom("constructor:left_projection_n2", reason=True)
    assert not rejected


def test_equation_shape_atoms_compact_non_leaky():
    atoms = normalize_equation_shape_atoms("(x * x) = x", "(x * y) = (y * x)")
    assert all(atom.startswith("eq_shape:") for atom in atoms)
    assert all("=" not in atom for atom in atoms)


def test_filter_accepted_and_hygiene_report(tmp_path):
    df = _attempt_df(tmp_path)
    accepted = filter_to_accepted_finite_countermodel_rows(df)
    assert not accepted.empty
    clean_df, report = clean_breakthrough_trace_rows(df)
    assert len(clean_df) == len(accepted)
    assert report.accepted_rows == len(accepted)
    assert report.total_atoms_after > 0
    assert report.advisory_boundary_ok
    assert "constructor" in report.accepted_atom_family_counts


def test_extract_clean_mechanism_atoms(tmp_path):
    df = _attempt_df(tmp_path)
    row = filter_to_accepted_finite_countermodel_rows(df).iloc[0]
    atoms = extract_clean_mechanism_atoms(row)
    assert any(atom.startswith("constructor:") for atom in atoms)
    assert any(atom.startswith("basin:") for atom in atoms)
    assert all(not reject_leaky_or_junk_atom(atom, reason=False) for atom in atoms)
