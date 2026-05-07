import json
import subprocess
import sys

from mathgraph.denotation import DenotationRecord, DenotationStatus
from mathgraph.lawbook_store import LawbookStore
from mathgraph.object_language import ObjectLanguageFormula, ObjectLanguageTerm
from mathgraph.predication import encodes
from mathgraph.reason_containment import ReasonContainmentRecord
from mathgraph.theory_objectification import AnalyticTruth, TheoryObjectificationMap
from mathgraph.theory_registry import ProofMethod, TheoryDeclaration, TheoryDeclarationKind, InferenceRule
from mathgraph.types import TypedObject


def test_query_lawbook_v1610_tables(tmp_path):
    db = tmp_path / "lawbook.sqlite"
    store = LawbookStore(db)
    try:
        store.add_typed_object(TypedObject("o", "i", "RootNode"))
        store.add_predication_fact(encodes("o", "p"))
        store.add_denotation_record(DenotationRecord("d", "o", None, None, DenotationStatus.DENOTES))
        store.add_theory_objectification_map(TheoryObjectificationMap("m", "k", None, "T"))
        store.add_analytic_truth(AnalyticTruth("a", "k", None, "T", "S", "r"))
        store.add_reason_containment_record(ReasonContainmentRecord("c", "r", "k", None, "s", "t"))
        store.add_object_language_term(ObjectLanguageTerm("term", "k", None, "x"))
        store.add_object_language_formula(ObjectLanguageFormula("formula", "k", None, "x=x"))
        store.add_theory_declaration(TheoryDeclaration("decl", "k", None, "T", TheoryDeclarationKind.AXIOM, "ax"))
        store.add_proof_method(ProofMethod("pm", "k", None, "T", "method"))
        store.add_inference_rule(InferenceRule("ir", "k", None, "T", "rule"))
    finally:
        store.close()

    for flag in (
        "--typed-objects",
        "--predications",
        "--denotations",
        "--theory-objectification-maps",
        "--analytic-truths",
        "--reason-containment",
        "--object-language-terms",
        "--object-language-formulas",
        "--theory-declarations",
        "--proof-methods",
        "--inference-rules",
    ):
        result = subprocess.run(
            [sys.executable, "scripts/query_lawbook.py", "--db", str(db), flag],
            check=True,
            text=True,
            capture_output=True,
        )
        assert json.loads(result.stdout)

    summary = subprocess.run(
        [sys.executable, "scripts/query_lawbook.py", "--db", str(db), "--summary"],
        check=True,
        text=True,
        capture_output=True,
    )
    payload = json.loads(summary.stdout)
    assert payload["warehouse"]["typed_objects"] == 1
    assert payload["warehouse"]["predication_facts"] == 1
