from pathlib import Path

from adapters.finite_magma_adapter import FiniteMagma
from mathgraph import Kernel, TerminalForm, VerificationStatus
from mathgraph.certificates import Certificate, verified_proof
from mathgraph.ledger import JsonlLedger
from mathgraph.trace import Trace


def test_certificate_to_dict_from_dict_roundtrip() -> None:
    cert = Certificate(
        terminal_form=TerminalForm.VERIFIED_PROOF,
        claim="x = x",
        payload={"proof_id": "demo"},
        external_verification={"status": "lean_verified"},
    )

    restored = Certificate.from_dict(cert.to_dict())

    assert restored == cert
    assert restored.external_status() == "lean_verified"


def test_trace_to_dict_from_dict_roundtrip_preserves_external_verifications() -> None:
    cert = verified_proof("x = x", "structural_reflexive")
    trace = Trace(
        claim="x = x",
        source="x = x",
        target=None,
        routes_tried=["structural_reflexive"],
        terminal_form=TerminalForm.VERIFIED_PROOF,
        verification_status=VerificationStatus.VERIFIED,
        certificate=cert,
        external_verifications=[{"status": "lean_verified"}],
    )

    restored = Trace.from_dict(trace.to_dict())

    assert restored.claim == trace.claim
    assert restored.source == "x = x"
    assert restored.target is None
    assert restored.terminal_form == TerminalForm.VERIFIED_PROOF
    assert restored.verification_status == VerificationStatus.VERIFIED
    assert restored.certificate == cert
    assert restored.external_verifications == [{"status": "lean_verified"}]
    assert restored.created


def test_jsonl_ledger_append_and_load(tmp_path: Path) -> None:
    ledger = JsonlLedger(tmp_path / "runs" / "ledger.jsonl")
    trace = Kernel().prove("x = x", "x * x = x")

    ledger.append_trace(trace)
    loaded = ledger.load_all()

    assert len(loaded) == 1
    assert loaded[0].terminal_form == TerminalForm.FINITE_COUNTERMODEL
    assert loaded[0].claim == trace.claim


def test_kernel_with_ledger_appends_one_trace_per_prove_call(tmp_path: Path) -> None:
    ledger = JsonlLedger(tmp_path / "ledger.jsonl")
    kernel = Kernel(
        finite_magmas=[FiniteMagma.from_table([[0]], name="trivial")],
        ledger=ledger,
    )

    kernel.prove("x = x")
    kernel.prove("x * y = x", "x * y = y")

    loaded = ledger.load_all()
    assert len(loaded) == 2
    assert [trace.terminal_form for trace in loaded] == [
        TerminalForm.VERIFIED_PROOF,
        TerminalForm.NAMED_OBSTRUCTION,
    ]


def test_kernel_ledger_preserves_external_verifications(tmp_path: Path) -> None:
    ledger = JsonlLedger(tmp_path / "ledger.jsonl")
    kernel = Kernel(ledger=ledger)

    trace = kernel.prove("x = x", lean_code="theorem t : True := True.intro")
    loaded = ledger.load_all()

    assert len(loaded) == 1
    assert loaded[0].external_verifications == trace.external_verifications
    assert "status" in loaded[0].external_verifications[0]
