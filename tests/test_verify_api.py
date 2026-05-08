import json
import subprocess
import sys
from pathlib import Path

from mathgraph import (
    CertificateLawbook,
    Kernel,
    LawbookStore,
    MathGraphVerifier,
    VerifyConfig,
    VerifyRequest,
    VerifyResult,
)
from mathgraph.terminal_contract import ProvenanceType, TerminalForm, TrustLevel, VerifierBoundary


ROOT = Path(__file__).resolve().parents[1]


def _store_with_traces(path: Path) -> LawbookStore:
    proof = Kernel().prove("x = x", "x = x")
    proof.metadata["compiled_route"] = "exact_equation"
    counter = Kernel().prove("x = x", "x * x = x")
    counter.metadata["compiled_route"] = "finite_countermodel"
    store = LawbookStore(path)
    store.import_lawbook(CertificateLawbook.from_traces([proof, counter]), replace=True)
    return store


def test_dataclass_roundtrip() -> None:
    request = VerifyRequest("x = x", "x = y", source_idx=1, target_idx=2)
    assert VerifyRequest.from_dict(request.to_dict()) == request
    config = VerifyConfig(store_path="lawbook.sqlite")
    assert VerifyConfig.from_dict(config.to_dict()) == config
    result = VerifyResult(
        status="UNKNOWN",
        terminal_form=TerminalForm.NAMED_OBSTRUCTION,
        trust_level=TrustLevel.ADVISORY_ROUTE,
        source="x = x",
        target="x = y",
        claim="x = x => x = y",
        certificate_id=None,
        route=None,
        explanation="unknown",
    )
    assert VerifyResult.from_dict(result.to_dict()) == result


def test_known_lawbook_hits_return_verified_and_refuted(tmp_path: Path) -> None:
    store = _store_with_traces(tmp_path / "lawbook.sqlite")
    store.close()
    verifier = MathGraphVerifier(VerifyConfig(store_path=str(tmp_path / "lawbook.sqlite")))
    proof = verifier.verify(VerifyRequest("x = x", "x = x", allow_construction=False))
    assert proof.status == "VERIFIED"
    assert proof.terminal_form == "VERIFIED_PROOF"
    assert proof.trust_level == TrustLevel.LEAN_VERIFIED
    assert proof.provenance_type == ProvenanceType.PRIMITIVE
    assert proof.verifier_boundary == VerifierBoundary.LEAN_TYPECHECKED
    counter = verifier.verify(VerifyRequest("x = x", "(x * x) = x", allow_construction=False))
    assert counter.status == "REFUTED"
    assert counter.terminal_form == TerminalForm.REFUTATION_CERTIFICATE
    assert counter.trust_level == TrustLevel.FINITE_VERIFIED
    assert counter.verifier_boundary == VerifierBoundary.IMPORTER_REVALIDATED


def test_unknown_false_magma_pair_can_produce_finite_countermodel() -> None:
    result = MathGraphVerifier().verify(
        VerifyRequest("x = x", "x = y", max_countermodel_order=2)
    )
    assert result.status == "REFUTED"
    assert result.terminal_form == TerminalForm.REFUTATION_CERTIFICATE
    assert result.trust_level == TrustLevel.FINITE_VERIFIED
    assert result.provenance_type == ProvenanceType.PRIMITIVE
    assert result.verifier_boundary == VerifierBoundary.IMPORTER_REVALIDATED
    assert result.certificate_chain == [result.certificate_id]
    assert result.evidence["countermodel_result"]["verification_status"] == "FINITE_VERIFIED"


def test_no_found_countermodel_is_not_verified() -> None:
    result = MathGraphVerifier().verify(
        VerifyRequest("x = x", "x = x", max_countermodel_order=2)
    )
    assert result.status in {"UNKNOWN", "OBSTRUCTED"}
    assert result.terminal_form == "NAMED_OBSTRUCTION"
    assert result.status != "VERIFIED"
    assert "Finite search failure is not proof." in result.warnings


def test_allow_construction_false_only_queries_memory(tmp_path: Path) -> None:
    verifier = MathGraphVerifier(VerifyConfig(store_path=str(tmp_path / "empty.sqlite")))
    result = verifier.verify(VerifyRequest("x = x", "x = y", allow_construction=False))
    assert result.status == "UNKNOWN"
    assert result.terminal_form == "NAMED_OBSTRUCTION"
    assert result.trust_level == TrustLevel.ADVISORY_ROUTE
    assert result.provenance_type == ProvenanceType.SYSTEM
    assert result.verifier_boundary == VerifierBoundary.NOT_VERIFIED


def test_malformed_equation_returns_error_without_promotion() -> None:
    result = MathGraphVerifier().verify(VerifyRequest("x = ", "x = y"))
    assert result.status in {"ERROR", "OBSTRUCTED", "UNKNOWN"}
    assert result.terminal_form in {"NONE", "NAMED_OBSTRUCTION"}
    assert result.status != "VERIFIED"
    assert result.terminal_form != "VERIFIED_PROOF"


def test_cli_smoke(tmp_path: Path) -> None:
    out = tmp_path / "result.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "verify_claim.py"),
            "--source",
            "x = x",
            "--target",
            "x = y",
            "--out",
            str(out),
            "--max-countermodel-order",
            "2",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    compact = json.loads(completed.stdout)
    assert compact["status"] == "REFUTED"
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["terminal_form"] == TerminalForm.REFUTATION_CERTIFICATE
    assert payload["provenance_type"] == ProvenanceType.PRIMITIVE
    assert payload["verifier_boundary"] == VerifierBoundary.IMPORTER_REVALIDATED
    assert payload["certificate_chain"]
