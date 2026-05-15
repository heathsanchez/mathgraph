from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DOCS = [
    ROOT / "README.md",
    ROOT / "docs" / "roadmap.md",
    ROOT / "docs" / "agentic_alchemical_loop.md",
]
BANNED_TERMS = (
    "logikey",
    "isabelle/aot",
    "aot importer",
    "archive of formal proofs as architecture",
)


def test_public_docs_avoid_external_branded_architecture_terms() -> None:
    for path in PUBLIC_DOCS:
        text = path.read_text(encoding="utf-8").lower()
        for term in BANNED_TERMS:
            assert term not in text, f"{term!r} leaked into {path}"
