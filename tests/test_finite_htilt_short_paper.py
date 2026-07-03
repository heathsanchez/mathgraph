from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAPER_DIR = ROOT / "papers" / "finite_htilt_survivor_law"
MAIN = PAPER_DIR / "finite_htilt_survivor_law.tex"
README = PAPER_DIR / "README.md"
BOUNDARY = PAPER_DIR / "claim_boundary_table.tex"
APPENDIX = PAPER_DIR / "artifact_appendix.tex"

THEOREMS = {
    "htilt_unnormalized_stationary",
    "htilt_normalized_stationary",
    "doob_row_sum_zero",
    "geometric_bridge_one_eq_piStar",
    "geometric_bridge_nat_one_eq_piStar",
    "geometric_log_exp_bridge_eq_geometric_bridge",
    "multiplicative_bridge_nat_one_eq_piStar",
    "multiplicative_bridge_real_one_eq_piStar",
    "multiplicative_log_exp_pointwise_eq",
}


def _paper_text() -> str:
    return "\n".join(
        path.read_text() for path in (MAIN, BOUNDARY, APPENDIX)
    )


def test_short_paper_files_exist() -> None:
    for path in (MAIN, README, BOUNDARY, APPENDIX):
        assert path.is_file()


def test_title_abstract_and_sections_are_present() -> None:
    text = MAIN.read_text()
    assert "A Lean-Verified Biorthogonal Stationarity Law" in text
    assert "\\begin{abstract}" in text
    for section in (
        "Introduction",
        "Finite Algebraic Setup",
        "The Survivor Law",
        "Bridge Alignment",
        "Lean Formalization",
        "Claim Boundary",
        "Discussion and Future Work",
    ):
        assert f"\\section{{{section}}}" in text


def test_all_verified_theorem_names_are_included() -> None:
    text = _paper_text().replace("\\_", "_")
    assert THEOREMS <= {name for name in THEOREMS if name in text}


def test_claim_boundary_table_contains_required_rows() -> None:
    text = BOUNDARY.read_text()
    for row in (
        "Exact survivor law",
        "Multiplicative bridge",
        "Log-exp equivalence",
        "Perron--Frobenius existence",
        "Empirical h-band",
        "Consciousness",
        "Scheduler performance",
        "Shared viability geometry",
    ):
        assert row in text


def test_nonclaims_are_explicit_without_forbidden_overclaims() -> None:
    text = _paper_text().lower()
    for term in (
        "perron--frobenius existence",
        "empirical h-band",
        "consciousness",
        "scheduler performance",
        "markov convergence",
        "bridge optimality",
    ):
        assert term in text
    for phrase in (
        "proves consciousness",
        "universal consciousness",
        "solves consciousness",
        "proves h-band universality",
        "proves h-tilt scheduler",
    ):
        assert phrase not in text


def test_inputs_and_artifact_paths_are_wired_into_paper() -> None:
    main = MAIN.read_text()
    appendix = APPENDIX.read_text()
    assert "\\input{claim_boundary_table}" in main
    assert "\\input{artifact_appendix}" in main
    assert "lake env lean" in appendix
    assert "finite_htilt_survivor_law_v1.json" in appendix
    assert "finite_htilt_survivor_law_bundle_manifest.json" in appendix
    assert "theorem htilt_unnormalized_stationary" in appendix
    assert "theorem multiplicative_bridge_real_one_eq_piStar" in appendix


def test_readme_states_status_and_nonclaims() -> None:
    text = README.read_text()
    assert "finite_htilt_survivor_law.tex" in text
    assert "VERIFIED_PROOF" in text
    assert "Perron-Frobenius existence" in text
