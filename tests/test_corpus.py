import json
from pathlib import Path

from adapters.sair_stage2_adapter import row_to_trace
from mathgraph import CertificateCorpus, JsonlLedger, TerminalForm, VerificationStatus


def _sample_traces():
    return [
        row_to_trace(
            {
                "source_idx": "1",
                "target_idx": "2",
                "source_equation": "x=x",
                "target_equation": "x=x",
                "claim_hash": "claim-true",
                "compiled_route": "routelean_v19_1",
                "lean_verified_true_v19_1": "true",
                "promotion_status_v19_1": "lean_verified_true_promotable",
            }
        ),
        row_to_trace(
            {
                "source_idx": "3",
                "target_idx": "4",
                "source_equation": "x=x",
                "target_equation": "x*x=x",
                "claim_hash": "claim-false",
                "compiled_route": "finite_magma",
                "lean_verified_false_v19_1": "true",
                "promotion_status_v19_1": "lean_verified_false_promotable",
            }
        ),
        row_to_trace(
            {
                "source_idx": "5",
                "target_idx": "6",
                "source_equation": "x=x",
                "target_equation": "y=y",
                "claim_hash": "claim-pending",
                "compiled_route": "candidate_route",
                "promotion_status_v19_1": "pending",
            }
        ),
    ]


def test_corpus_from_trace_dictionaries() -> None:
    traces = _sample_traces()
    corpus = CertificateCorpus.from_traces([trace.to_dict() for trace in traces])

    assert len(corpus.traces) == 3
    assert corpus.terminal_form_counts() == {
        "VERIFIED_PROOF": 1,
        "FINITE_COUNTERMODEL": 1,
        "NAMED_OBSTRUCTION": 1,
    }
    assert corpus.verification_status_counts() == {
        "VERIFIED": 1,
        "REFUTED": 1,
        "OBSTRUCTED": 1,
    }


def test_corpus_from_json(tmp_path: Path) -> None:
    path = tmp_path / "traces.json"
    traces = _sample_traces()
    path.write_text(
        json.dumps([trace.to_dict() for trace in traces], sort_keys=True),
        encoding="utf-8",
    )

    corpus = CertificateCorpus.from_json(path)

    assert corpus.summary()["trace_count"] == 3
    assert corpus.query(terminal_form=TerminalForm.VERIFIED_PROOF)[0].claim == "claim-true"


def test_corpus_to_json_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "corpus.json"
    corpus = CertificateCorpus.from_traces(_sample_traces())

    corpus.to_json(path)
    loaded = CertificateCorpus.from_json(path)

    assert loaded.summary()["trace_count"] == 3
    assert loaded.get_by_claim_hash("claim-false")[0].terminal_form == TerminalForm.FINITE_COUNTERMODEL


def test_corpus_from_jsonl_ledger(tmp_path: Path) -> None:
    ledger_path = tmp_path / "traces.jsonl"
    ledger = JsonlLedger(ledger_path)
    for trace in _sample_traces():
        ledger.append_trace(trace)

    corpus = CertificateCorpus.from_jsonl_ledger(ledger_path)

    assert corpus.summary()["trace_count"] == 3
    assert corpus.query(verification_status=VerificationStatus.REFUTED)[0].claim == "claim-false"


def test_corpus_query_by_terminal_form_and_route() -> None:
    corpus = CertificateCorpus.from_traces(_sample_traces())

    countermodels = corpus.query(terminal_form="FINITE_COUNTERMODEL")
    finite_route = corpus.query(compiled_route="finite_magma")

    assert len(countermodels) == 1
    assert countermodels == finite_route
    assert corpus.route_counts() == {
        "routelean_v19_1": 1,
        "finite_magma": 1,
        "candidate_route": 1,
    }


def test_corpus_lookup_by_claim_hash_and_pair() -> None:
    corpus = CertificateCorpus.from_traces(_sample_traces())

    assert corpus.get_by_claim_hash("claim-true")[0].verification_status == VerificationStatus.VERIFIED
    pair = corpus.get_by_pair("3", "4")

    assert len(pair) == 1
    assert pair[0].terminal_form == TerminalForm.FINITE_COUNTERMODEL


def test_corpus_query_limit() -> None:
    corpus = CertificateCorpus.from_traces(_sample_traces())

    assert len(corpus.query(limit=2)) == 2


def test_corpus_audit_hashes_detects_duplicates() -> None:
    trace = _sample_traces()[0]
    corpus = CertificateCorpus.from_traces([trace, trace.to_dict()])

    audit = corpus.audit_hashes()

    assert audit["trace_count"] == 2
    assert audit["hash_count"] == 2
    assert audit["duplicate_count"] == 1
    assert len(audit["trace_hashes"]) == 2
    assert isinstance(audit["merkle_root"], str)


def test_corpus_import_does_not_require_pandas(monkeypatch) -> None:
    import builtins

    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name == "pandas":
            raise AssertionError("CertificateCorpus should not import pandas")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)

    corpus = CertificateCorpus.from_traces([trace.to_dict() for trace in _sample_traces()])

    assert corpus.summary()["trace_count"] == 3
