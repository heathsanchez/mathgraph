import json
import subprocess
import sys

from mathgraph.denotation import DenotationRecord, DenotationStatus
from mathgraph.lawbook_store import LawbookStore
from mathgraph.predication import encodes
from mathgraph.reason_containment import ReasonContainmentRecord
from mathgraph.theory_objectification import AnalyticTruth, TheoryObjectificationMap
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
    finally:
        store.close()

    for flag in (
        "--typed-objects",
        "--predications",
        "--denotations",
        "--theory-objectification-maps",
        "--analytic-truths",
        "--reason-containment",
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
