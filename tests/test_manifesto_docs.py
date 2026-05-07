from pathlib import Path


def test_manifesto_glossary_and_readme_links_exist():
    root = Path(__file__).resolve().parents[1]
    assert (root / "docs" / "manifesto.md").exists()
    assert (root / "docs" / "glossary.md").exists()
    readme = (root / "README.md").read_text(encoding="utf-8")
    assert "docs/manifesto.md" in readme
    assert "docs/glossary.md" in readme
