from mathgraph.denotation import DenotationStatus
from mathgraph.object_language import (
    FormulaRole,
    ObjectLanguageFormula,
    ObjectLanguageTerm,
    normalize_object_language_text,
)


def test_object_language_term_and_formula_normalize():
    assert normalize_object_language_text("  A   B\n C ") == "A B C"
    term = ObjectLanguageTerm(
        term_id="t",
        domain_kernel_id="aot",
        formal_world_id="w",
        raw_text="  κ   ",
        denotation_status=DenotationStatus.UNKNOWN,
    )
    assert term.normalized_text == "κ"
    assert term.to_dict()["denotation_status"] == "UNKNOWN"

    formula = ObjectLanguageFormula(
        formula_id="f",
        domain_kernel_id="aot",
        formal_world_id="w",
        raw_text="AOT_theorem foo",
        formula_role=FormulaRole.THEOREM,
    )
    assert formula.type_expr == "<>"
    assert formula.normalized_text == "AOT_theorem foo"
