import json
import subprocess
import sys
from pathlib import Path

from mathgraph import (
    Certificate,
    CertificateLawbook,
    DerivedCertificate,
    DerivedCertificateGenerator,
    KernelOracle,
    LawbookStore,
    TerminalForm,
    Trace,
    VerificationStatus,
)


ROOT = Path(__file__).resolve().parents[1]


def _trace(source: str, target: str, terminal_form: str, route: str = "primitive") -> Trace:
    terminal = TerminalForm(terminal_form)
    status = (
        VerificationStatus.VERIFIED
        if terminal == TerminalForm.VERIFIED_PROOF
        else VerificationStatus.REFUTED
    )
    return Trace(
        claim=f"{source}=>{target}",
        source=source,
        target=target,
        routes_tried=[route],
        terminal_form=terminal,
        verification_status=status,
        certificate=Certificate(
            terminal_form=terminal,
            claim=f"{source}=>{target}",
            payload={
                "source_idx": source,
                "target_idx": target,
                "compiled_route": route,
                "claim_hash": f"{source}->{target}",
            },
        ),
        metadata={
            "source_idx": source,
            "target_idx": target,
            "compiled_route": route,
            "claim_hash": f"{source}->{target}",
        },
    )


def _store(path: Path, traces: list[Trace]) -> LawbookStore:
    store = LawbookStore(path)
    store.import_lawbook(CertificateLawbook.from_traces(traces), replace=True)
    return store


def test_true_transitivity_derives_verified_proof(tmp_path: Path) -> None:
    store = _store(
        tmp_path / "lawbook.sqlite",
        [
            _trace("A", "B", "VERIFIED_PROOF"),
            _trace("B", "C", "VERIFIED_PROOF"),
        ],
    )
    try:
        certs = DerivedCertificateGenerator(store).derive_true_transitivity()
        assert len(certs) == 1
        assert certs[0].source == "A"
        assert certs[0].target == "C"
        assert certs[0].terminal_form == "VERIFIED_PROOF"
        assert certs[0].verification_status == "DERIVED_VERIFIED"
    finally:
        store.close()


def test_false_source_weakening_uses_sound_direction(tmp_path: Path) -> None:
    store = _store(
        tmp_path / "lawbook.sqlite",
        [
            _trace("B", "A", "VERIFIED_PROOF"),
            _trace("B", "C", "FINITE_COUNTERMODEL"),
        ],
    )
    try:
        certs = DerivedCertificateGenerator(store).derive_false_source_weakening()
        assert [(cert.source, cert.target) for cert in certs] == [("A", "C")]
        assert certs[0].terminal_form == "FINITE_COUNTERMODEL"
        assert certs[0].verification_status == "DERIVED_REFUTED"
    finally:
        store.close()


def test_false_source_weakening_wrong_direction_not_used(tmp_path: Path) -> None:
    store = _store(
        tmp_path / "lawbook.sqlite",
        [
            _trace("A", "B", "VERIFIED_PROOF"),
            _trace("B", "C", "FINITE_COUNTERMODEL"),
        ],
    )
    try:
        certs = DerivedCertificateGenerator(store).derive_false_source_weakening()
        assert not any(cert.source == "A" and cert.target == "C" for cert in certs)
    finally:
        store.close()


def test_false_target_strengthening_uses_sound_direction(tmp_path: Path) -> None:
    store = _store(
        tmp_path / "lawbook.sqlite",
        [
            _trace("A", "B", "FINITE_COUNTERMODEL"),
            _trace("C", "B", "VERIFIED_PROOF"),
        ],
    )
    try:
        certs = DerivedCertificateGenerator(store).derive_false_target_strengthening()
        assert [(cert.source, cert.target) for cert in certs] == [("A", "C")]
        assert certs[0].derivation_rule == "false_target_strengthening"
    finally:
        store.close()


def test_false_target_strengthening_wrong_direction_not_used(tmp_path: Path) -> None:
    store = _store(
        tmp_path / "lawbook.sqlite",
        [
            _trace("A", "B", "FINITE_COUNTERMODEL"),
            _trace("B", "C", "VERIFIED_PROOF"),
        ],
    )
    try:
        certs = DerivedCertificateGenerator(store).derive_false_target_strengthening()
        assert not any(cert.source == "A" and cert.target == "C" for cert in certs)
    finally:
        store.close()


def test_existing_primitive_exact_trace_is_not_duplicated(tmp_path: Path) -> None:
    store = _store(
        tmp_path / "lawbook.sqlite",
        [
            _trace("A", "B", "VERIFIED_PROOF"),
            _trace("B", "C", "VERIFIED_PROOF"),
            _trace("A", "C", "VERIFIED_PROOF"),
        ],
    )
    try:
        certs = DerivedCertificateGenerator(store).derive_true_transitivity()
        assert certs == []
    finally:
        store.close()


def test_save_jsonl_and_json(tmp_path: Path) -> None:
    store = _store(
        tmp_path / "lawbook.sqlite",
        [_trace("A", "B", "VERIFIED_PROOF"), _trace("B", "C", "VERIFIED_PROOF")],
    )
    jsonl_path = tmp_path / "derived.jsonl"
    json_path = tmp_path / "derived.json"
    try:
        generator = DerivedCertificateGenerator(store)
        certs = generator.derive_true_transitivity()
        generator.save_jsonl(certs, jsonl_path)
        generator.save_json(certs, json_path)
        assert len(jsonl_path.read_text(encoding="utf-8").splitlines()) == 1
        assert json.loads(json_path.read_text(encoding="utf-8"))[0]["source"] == "A"
    finally:
        store.close()


def test_import_derived_and_derived_stats(tmp_path: Path) -> None:
    store = _store(
        tmp_path / "lawbook.sqlite",
        [_trace("A", "B", "VERIFIED_PROOF"), _trace("B", "C", "VERIFIED_PROOF")],
    )
    try:
        certs = DerivedCertificateGenerator(store).derive_true_transitivity()
        stats = store.import_derived_certificates(certs)
        assert stats.total_derived_count == 1
        assert store.derived_stats()["rule_counts"]["true_transitivity"] == 1
        assert store.get_derived_by_pair("A", "C")["terminal_form"] == "VERIFIED_PROOF"
    finally:
        store.close()


def test_kernel_oracle_prefers_primitive_exact_hit(tmp_path: Path) -> None:
    store = _store(tmp_path / "lawbook.sqlite", [_trace("A", "C", "VERIFIED_PROOF")])
    try:
        derived = DerivedCertificate(
            derived_claim="derived-conflict",
            source="A",
            target="C",
            source_idx=None,
            target_idx=None,
            terminal_form="FINITE_COUNTERMODEL",
            verification_status="DERIVED_REFUTED",
            derivation_rule="test_conflict",
            trust_level="derived_from_verified_traces",
            parent_claims=[],
            parent_pairs=[],
            route="derived_test",
            explanation="conflicting derived test",
            evidence={},
            warnings=[],
        )
        store.import_derived_certificates([derived])
        answer = KernelOracle(store).query("A", "C")
        assert answer.status == "VERIFIED"
        assert answer.trust_level == "verified_trace"
    finally:
        store.close()


def test_kernel_oracle_returns_derived_hit_when_primitive_missing(tmp_path: Path) -> None:
    store = _store(
        tmp_path / "lawbook.sqlite",
        [_trace("B", "A", "VERIFIED_PROOF"), _trace("B", "C", "FINITE_COUNTERMODEL")],
    )
    try:
        certs = DerivedCertificateGenerator(store).derive_false_source_weakening()
        store.import_derived_certificates(certs)
        answer = KernelOracle(store).query("A", "C")
        assert answer.status == "REFUTED"
        assert answer.terminal_form == "FINITE_COUNTERMODEL"
        assert answer.trust_level == "derived_from_verified_traces"
        assert answer.evidence["derivation_rule"] == "false_source_weakening"
    finally:
        store.close()


def test_derive_certificates_cli(tmp_path: Path) -> None:
    store = _store(
        tmp_path / "lawbook.sqlite",
        [_trace("A", "B", "VERIFIED_PROOF"), _trace("B", "C", "VERIFIED_PROOF")],
    )
    store.close()
    jsonl_path = tmp_path / "derived.jsonl"
    json_path = tmp_path / "derived.json"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "derive_certificates.py"),
            "--store",
            str(tmp_path / "lawbook.sqlite"),
            "--out-jsonl",
            str(jsonl_path),
            "--out-json",
            str(json_path),
            "--import-to-store",
            "--max-per-rule",
            "10",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["stats"]["rule_counts"]["true_transitivity"] == 1
    assert jsonl_path.exists()
    assert json_path.exists()
