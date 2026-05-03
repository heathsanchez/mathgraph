import json
import subprocess
import sys
from pathlib import Path

from mathgraph import CertificateLawbook, Kernel, KernelOracle, LawbookStore


ROOT = Path(__file__).resolve().parents[1]


def _traces():
    proof = Kernel().prove("x = x", "x = x")
    proof.metadata.update({"source_idx": "1", "target_idx": "2", "compiled_route": "variable_identification", "claim_hash": "claim-proof"})
    counter = Kernel().prove("x = x", "x * x = x")
    counter.metadata.update({"source_idx": "1", "target_idx": "3", "compiled_route": "finite_countermodel", "claim_hash": "claim-counter"})
    return [proof, counter]


def _write_traces(path: Path) -> None:
    path.write_text(json.dumps([trace.to_dict() for trace in _traces()]), encoding="utf-8")


def _oracle(path: Path) -> tuple[LawbookStore, KernelOracle]:
    store = LawbookStore(path)
    store.import_lawbook(CertificateLawbook.from_traces(_traces()), replace=True)
    return store, KernelOracle(store)


def test_exact_verified_proof_returns_verified(tmp_path: Path) -> None:
    store, oracle = _oracle(tmp_path / "lawbook.sqlite")
    try:
        answer = oracle.query("1", "2")
        assert answer.status == "VERIFIED"
        assert answer.terminal_form == "VERIFIED_PROOF"
        assert answer.trust_level == "verified_trace"
    finally:
        store.close()


def test_exact_countermodel_returns_refuted(tmp_path: Path) -> None:
    store, oracle = _oracle(tmp_path / "lawbook.sqlite")
    try:
        answer = oracle.query("1", "3")
        assert answer.status == "REFUTED"
        assert answer.terminal_form == "FINITE_COUNTERMODEL"
    finally:
        store.close()


def test_missing_pair_returns_unknown(tmp_path: Path) -> None:
    store, oracle = _oracle(tmp_path / "lawbook.sqlite")
    try:
        answer = oracle.query("missing", "pair")
        assert answer.status == "UNKNOWN"
        assert answer.terminal_form == "NAMED_OBSTRUCTION"
        assert answer.verification_status == "UNKNOWN"
        assert answer.trust_level == "no_exact_trace"
        assert "Do not promote" in answer.warnings[1]
    finally:
        store.close()


def test_lists_and_stats(tmp_path: Path) -> None:
    store, oracle = _oracle(tmp_path / "lawbook.sqlite")
    try:
        assert oracle.finite_countermodels()[0].terminal_form == "FINITE_COUNTERMODEL"
        assert oracle.verified_proofs()[0].terminal_form == "VERIFIED_PROOF"
        assert oracle.route_examples("finite_countermodel")[0].status == "REFUTED"
        assert oracle.what_does_this_imply("1")
        assert oracle.what_implies_this("3")
        assert oracle.stats()["trace_count"] == 2
    finally:
        store.close()


def test_no_missing_answer_claims_proof_or_refutation(tmp_path: Path) -> None:
    store, oracle = _oracle(tmp_path / "lawbook.sqlite")
    try:
        answer = oracle.explain_claim("missing")
        assert answer.status == "UNKNOWN"
        assert answer.terminal_form == "NAMED_OBSTRUCTION"
    finally:
        store.close()


def test_query_kernel_oracle_cli(tmp_path: Path) -> None:
    traces = tmp_path / "traces.json"
    sqlite_path = tmp_path / "lawbook.sqlite"
    _write_traces(traces)
    build = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_lawbook_store.py"),
            "--traces-json",
            str(traces),
            "--out",
            str(sqlite_path),
            "--replace",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert build.returncode == 0, build.stderr

    stats = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "query_kernel_oracle.py"), "--store", str(sqlite_path), "--stats"],
        check=False,
        capture_output=True,
        text=True,
    )
    query = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "query_kernel_oracle.py"),
            "--store",
            str(sqlite_path),
            "--source",
            "1",
            "--target",
            "3",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    finite = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "query_kernel_oracle.py"),
            "--store",
            str(sqlite_path),
            "--finite-countermodels",
            "--limit",
            "5",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    proofs = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "query_kernel_oracle.py"),
            "--store",
            str(sqlite_path),
            "--verified-proofs",
            "--limit",
            "5",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert stats.returncode == query.returncode == finite.returncode == proofs.returncode == 0
    assert json.loads(stats.stdout)["trace_count"] == 2
    assert json.loads(query.stdout)["status"] == "REFUTED"
    assert json.loads(finite.stdout)[0]["terminal_form"] == "FINITE_COUNTERMODEL"
    assert json.loads(proofs.stdout)[0]["terminal_form"] == "VERIFIED_PROOF"
