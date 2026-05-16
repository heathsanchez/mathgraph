from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DOCS = [
    ROOT / "README.md",
    *sorted((ROOT / "docs").rglob("*.md")),
    *sorted((ROOT / "docs").rglob("*.tex")),
]
BANNED_TERMS = (
    "logikey",
    "isabelle/aot",
    "isabelle/aot importer",
    "aot importer",
    "archive of formal proofs as architecture",
    "aot kernel",
    "aot formal world",
    "aot methodology",
    "aot as architecture",
)


def test_public_docs_avoid_external_branded_architecture_terms() -> None:
    for path in PUBLIC_DOCS:
        text = path.read_text(encoding="utf-8").lower()
        for term in BANNED_TERMS:
            assert term not in text, f"{term!r} leaked into {path}"


def test_public_exports_avoid_branded_helper_names() -> None:
    import mathgraph

    exported = {name.lower() for name in mathgraph.__all__}
    assert not any("logikey" in name or "aot" in name for name in exported)


def test_neutral_adapter_terms_remain_allowed() -> None:
    allowed = "Lean Isabelle Coq SMT Z3 proof assistant theorem prover formal verifier trusted importer external verified source reference workbench external theory kernel proof-system adapter formal-world adapter"
    for term in ("lean", "isabelle", "coq", "smt", "z3"):
        assert term in allowed.lower()
