from mathgraph.aot_scanner import scan_aot_repository
from mathgraph.theory_registry import TheoryDeclarationKind


def test_aot_scanner_finds_advisory_declarations(tmp_path):
    theory = tmp_path / "AOT_Test.thy"
    theory.write_text(
        "\n".join(
            [
                "theory AOT_Test",
                "AOT_theorem test_theorem",
                "AOT_lemma test_lemma",
                "AOT_define test_definition",
                "AOT_axiom test_axiom",
                "AOT_world test_world",
                "named_theorems aot_simp",
            ]
        )
    )
    result = scan_aot_repository(tmp_path)
    names = {decl.name for decl in result.declarations}
    assert {"test_theorem", "test_lemma", "test_definition", "test_axiom", "test_world"} <= names
    assert any(decl.declaration_kind is TheoryDeclarationKind.THEOREM for decl in result.declarations)
    assert result.proof_methods
    converted = result.declarations[0].to_theory_declaration()
    assert converted.trust_level.value == "ADVISORY_ROUTE"
    assert not converted.is_verified_inside_mathgraph()
