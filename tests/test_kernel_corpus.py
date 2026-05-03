from pathlib import Path

from adapters.sair_stage2_adapter import row_to_trace
from mathgraph import CertificateCorpus, JsonlLedger, Kernel, TerminalForm, VerificationStatus


def _proof_trace(**extra):
    row = {
        "source_idx": "10",
        "target_idx": "20",
        "source_equation": "x * y = x",
        "target_equation": "x * y = y",
        "claim_hash": "claim-proof",
        "compiled_route": "routelean_v19_1",
        "lean_verified_true_v19_1": "true",
        "promotion_status_v19_1": "lean_verified_true_promotable",
    }
    row.update(extra)
    return row_to_trace(row)


def _countermodel_trace(**extra):
    row = {
        "source_idx": "30",
        "target_idx": "40",
        "source_equation": "x = x",
        "target_equation": "x * x = x",
        "claim_hash": "claim-false",
        "compiled_route": "finite_magma",
        "lean_verified_false_v19_1": "true",
        "promotion_status_v19_1": "lean_verified_false_promotable",
        "countermodel": "small model",
    }
    row.update(extra)
    return row_to_trace(row)


def test_kernel_returns_verified_proof_from_corpus_by_pair_indices() -> None:
    corpus = CertificateCorpus.from_traces([_proof_trace()])
    kernel = Kernel(corpus=corpus, finite_magmas=[])

    trace = kernel.prove("x * y = x", "x * y = y", source_idx=10, target_idx=20)

    assert trace.terminal_form == TerminalForm.VERIFIED_PROOF
    assert trace.verification_status == VerificationStatus.VERIFIED
    assert trace.metadata["corpus_hit"] is True
    assert trace.metadata["corpus_lookup_mode"] == "pair_indices"
    assert trace.metadata["corpus_trace_hash"]
    assert trace.routes_tried[0] == "certificate_corpus_lookup"


def test_kernel_returns_finite_countermodel_from_corpus_by_pair_indices() -> None:
    corpus = CertificateCorpus.from_traces([_countermodel_trace()])
    kernel = Kernel(corpus=corpus, finite_magmas=[])

    trace = kernel.prove("x = x", "x * x = x", source_idx="30", target_idx="40")

    assert trace.terminal_form == TerminalForm.FINITE_COUNTERMODEL
    assert trace.verification_status == VerificationStatus.REFUTED
    assert trace.verify()
    assert trace.metadata["corpus_lookup_mode"] == "pair_indices"


def test_kernel_returns_verified_proof_from_corpus_by_equation_strings() -> None:
    corpus = CertificateCorpus.from_traces([_proof_trace()])
    kernel = Kernel(corpus=corpus, finite_magmas=[])

    trace = kernel.prove("x * y = x", "x * y = y")

    assert trace.terminal_form == TerminalForm.VERIFIED_PROOF
    assert trace.verification_status == VerificationStatus.VERIFIED
    assert trace.metadata["corpus_lookup_mode"] == "equation_strings"


def test_kernel_returns_verified_proof_from_corpus_by_claim_hash() -> None:
    corpus = CertificateCorpus.from_traces([_proof_trace()])
    kernel = Kernel(corpus=corpus, finite_magmas=[])

    trace = kernel.prove("a * b = a", "a * b = b", claim_hash="claim-proof")

    assert trace.terminal_form == TerminalForm.VERIFIED_PROOF
    assert trace.metadata["corpus_lookup_mode"] == "claim_hash"


def test_named_obstruction_in_corpus_is_not_promoted() -> None:
    obstruction = row_to_trace(
        {
            "source_idx": "1",
            "target_idx": "2",
            "source_equation": "x * y = x",
            "target_equation": "x * y = y",
            "claim_hash": "claim-obstructed",
            "promotion_status_v19_1": "pending",
        }
    )
    corpus = CertificateCorpus.from_traces([obstruction])
    kernel = Kernel(corpus=corpus, finite_magmas=[])

    trace = kernel.prove("x * y = x", "x * y = y", source_idx=1, target_idx=2)

    assert trace.terminal_form == TerminalForm.NAMED_OBSTRUCTION
    assert trace.verification_status == VerificationStatus.OBSTRUCTED
    assert trace.metadata.get("corpus_hit") is None
    assert not trace.is_verified_proof()


def test_conflicting_corpus_hits_return_named_obstruction() -> None:
    proof = _proof_trace(source_idx="7", target_idx="8", claim_hash="claim-proof")
    countermodel = _countermodel_trace(
        source_idx="7",
        target_idx="8",
        source_equation="x * y = x",
        target_equation="x * y = y",
        claim_hash="claim-false",
    )
    corpus = CertificateCorpus.from_traces([proof, countermodel])
    kernel = Kernel(corpus=corpus, finite_magmas=[])

    trace = kernel.prove("x * y = x", "x * y = y", source_idx=7, target_idx=8)

    assert trace.terminal_form == TerminalForm.NAMED_OBSTRUCTION
    assert trace.verification_status == VerificationStatus.OBSTRUCTED
    assert trace.metadata["corpus_conflict"] is True
    assert trace.metadata["corpus_conflict_count"] == 2
    assert not trace.verify()


def test_kernel_without_corpus_still_uses_existing_routes() -> None:
    trace = Kernel().prove("x = x", "x * x = x")

    assert trace.terminal_form == TerminalForm.FINITE_COUNTERMODEL
    assert trace.verification_status == VerificationStatus.REFUTED
    assert trace.metadata == {}


def test_ledger_appends_returned_trace_on_corpus_hit(tmp_path: Path) -> None:
    corpus = CertificateCorpus.from_traces([_proof_trace()])
    ledger = JsonlLedger(tmp_path / "ledger.jsonl")
    kernel = Kernel(corpus=corpus, finite_magmas=[], ledger=ledger)

    trace = kernel.prove("x * y = x", "x * y = y", source_idx=10, target_idx=20)
    loaded = ledger.load_all()

    assert len(loaded) == 1
    assert loaded[0].terminal_form == trace.terminal_form
    assert loaded[0].metadata["corpus_hit"] is True
