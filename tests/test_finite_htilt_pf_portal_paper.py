from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAPER_DIR = ROOT / "papers" / "finite_htilt_pf_portal"
PAPER_PATH = PAPER_DIR / "finite_htilt_pf_portal.tex"
TABLE_PATH = PAPER_DIR / "theorem_tower_table.tex"
APPENDIX_PATH = PAPER_DIR / "artifact_appendix.tex"


def test_companion_paper_bundle_exists() -> None:
    for path in (
        PAPER_PATH,
        TABLE_PATH,
        APPENDIX_PATH,
        PAPER_DIR / "README.md",
    ):
        assert path.is_file(), path


def test_paper_contains_theorem_tower_and_axiom_audit() -> None:
    paper = PAPER_PATH.read_text(encoding="utf-8")
    table = TABLE_PATH.read_text(encoding="utf-8")
    appendix = APPENDIX_PATH.read_text(encoding="utf-8")

    assert "\\input{theorem_tower_table}" in paper
    assert "Conditional killed-generator algebra" in table
    assert "Conditional discrete Doob algebra" in table
    assert "Discrete PF portal" in table
    assert "sorryAx" in paper
    assert "not claimed globally" in paper
    assert "\\#print axioms" in appendix


def test_paper_states_required_nonclaims() -> None:
    text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (PAPER_PATH, TABLE_PATH, APPENDIX_PATH)
    ).lower()

    for topic in (
        "killed-generator bridge",
        "convergence",
        "empirical h-band",
        "consciousness",
        "scheduler performance",
    ):
        assert topic in text


def test_paper_avoids_forbidden_positive_claims() -> None:
    text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (PAPER_PATH, TABLE_PATH, APPENDIX_PATH)
    ).lower()

    for forbidden in (
        "proves consciousness",
        "proves h-band universality",
        "proves scheduler performance",
        "proves markov convergence",
        "proves killed-generator pf existence",
    ):
        assert forbidden not in text
