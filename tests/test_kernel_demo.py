import subprocess
import sys
from pathlib import Path

from adapters.finite_magma_adapter import FiniteMagma
from adapters.lean_adapter import detect_lean
from mathgraph import Kernel, TerminalForm, VerificationStatus


ROOT = Path(__file__).resolve().parents[1]


def test_kernel_records_finite_countermodel() -> None:
    kernel = Kernel()
    magma = FiniteMagma.from_table([[0, 1], [1, 0]], name="xor")
    cert = kernel.check_finite_magma_implication([], "x * x = x", magma)
    assert cert.terminal_form == TerminalForm.FINITE_COUNTERMODEL
    assert kernel.store.list_nodes("certificate")


def test_kernel_prove_returns_finite_countermodel_trace() -> None:
    trace = Kernel().prove("x = x", "x * x = x")
    assert trace.terminal_form == TerminalForm.FINITE_COUNTERMODEL
    assert trace.verification_status == VerificationStatus.REFUTED
    assert trace.verify()
    assert not trace.is_verified_proof()
    assert trace.certificate.payload["model"]["carrier_order"] == 2
    assert trace.certificate.payload["model"]["assignment"] == {"x": 1}
    assert trace.certificate.payload["model"]["table"] == [[0, 1], [1, 0]]
    assert trace.certificate.payload["model"]["source_satisfied"] is True
    assert trace.certificate.payload["model"]["target_violated"] is True
    assert "table_invariants" in trace.certificate.payload["model"]


def test_kernel_prove_returns_structural_proof_trace() -> None:
    trace = Kernel().prove("x * y = y * x", "a * b = b * a")
    assert trace.terminal_form == TerminalForm.VERIFIED_PROOF
    assert trace.verification_status == VerificationStatus.VERIFIED
    assert trace.certificate.payload["proof_id"] == "structural_variable_renaming"
    assert trace.verify()
    assert trace.is_verified_proof()


def test_kernel_prove_returns_named_obstruction_not_proof() -> None:
    kernel = Kernel(finite_magmas=[FiniteMagma.from_table([[0]], name="trivial")])
    trace = kernel.prove("(x * y) * z = x * (y * z)", "x * y = y * x")
    assert trace.terminal_form == TerminalForm.NAMED_OBSTRUCTION
    assert trace.verification_status == VerificationStatus.OBSTRUCTED
    assert trace.certificate is None
    assert trace.obstruction is not None
    assert not trace.verify()
    assert not trace.is_verified_proof()


def test_obstruction_verify_is_not_a_true_proof() -> None:
    kernel = Kernel(finite_magmas=[FiniteMagma.from_table([[0]], name="trivial")])
    trace = kernel.prove("x * y = x", "x * y = y")
    assert not trace.verify()
    assert trace.terminal_form == TerminalForm.NAMED_OBSTRUCTION
    assert trace.verification_status != VerificationStatus.VERIFIED
    assert not trace.is_verified_proof()


def test_finite_search_failure_never_becomes_proof() -> None:
    kernel = Kernel(finite_magmas=[FiniteMagma.from_table([[0]], name="trivial")])
    trace = kernel.prove("x * y = x", "x * y = y")
    assert "finite_magma_countermodel" in trace.routes_tried
    assert trace.terminal_form == TerminalForm.NAMED_OBSTRUCTION
    assert trace.verification_status == VerificationStatus.OBSTRUCTED
    assert trace.certificate is None


def test_structural_routes_reject_unsafe_cases() -> None:
    trace = Kernel(finite_magmas=[]).prove("x * y = x", "a * b = b")
    assert "structural_variable_renaming" in trace.routes_tried
    assert trace.terminal_form == TerminalForm.NAMED_OBSTRUCTION
    assert not trace.is_verified_proof()


def test_kernel_prove_attaches_lean_code_external_verification() -> None:
    trace = Kernel().prove(
        "x = x",
        "x * x = x",
        lean_code="theorem t : True := True.intro",
    )
    assert trace.terminal_form == TerminalForm.FINITE_COUNTERMODEL
    assert len(trace.external_verifications) == 1
    assert "status" in trace.external_verifications[0]
    if detect_lean()["lean_available"]:
        assert trace.external_verifications[0]["status"] == "lean_verified"
    else:
        assert trace.external_verifications[0]["status"] == "lean_unavailable"


def test_lean_verified_unrelated_theorem_does_not_promote_obstruction() -> None:
    trace = Kernel(finite_magmas=[]).prove(
        "x * y = x",
        "x * y = y",
        lean_code="theorem t : True := True.intro",
    )
    assert trace.external_verifications
    assert trace.terminal_form == TerminalForm.NAMED_OBSTRUCTION
    assert trace.verification_status == VerificationStatus.OBSTRUCTED
    assert not trace.verify()
    assert not trace.is_verified_proof()


def test_kernel_prove_rejects_both_lean_code_and_lean_file() -> None:
    try:
        Kernel().prove("x = x", lean_code="theorem t : True := True.intro", lean_file="x.lean")
    except ValueError as exc:
        assert "at most one" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_basic_kernel_demo_runs() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "examples" / "basic_kernel_demo.py")],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "FINITE_COUNTERMODEL" in result.stdout
    assert "VERIFIED_PROOF" in result.stdout
    assert "NAMED_OBSTRUCTION" in result.stdout
