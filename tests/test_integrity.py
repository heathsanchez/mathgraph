from pathlib import Path
import subprocess
import sys

from mathgraph import Kernel
from mathgraph.hashing import (
    canonical_json,
    content_id,
    hash_certificate,
    hash_file,
    hash_trace,
    sha256_json,
    short_hash,
)
from mathgraph.ledger import JsonlLedger
from mathgraph.merkle import merkle_proof, merkle_root, verify_merkle_proof
from mathgraph.replay import replay_ledger, replay_trace


ROOT = Path(__file__).resolve().parents[1]


def test_stable_json_hash_is_deterministic() -> None:
    left = {"b": [2, 1], "a": {"z": True}}
    right = {"a": {"z": True}, "b": [2, 1]}

    assert canonical_json(left) == canonical_json(right)
    assert sha256_json(left) == sha256_json(right)


def test_hash_changes_when_payload_changes() -> None:
    assert sha256_json({"payload": 1}) != sha256_json({"payload": 2})


def test_trace_and_certificate_hashes_change_with_payload() -> None:
    trace_a = Kernel().prove("x = x")
    trace_b = Kernel().prove("y = y")

    assert hash_trace(trace_a) != hash_trace(trace_b)
    assert hash_certificate(trace_a.certificate) != hash_certificate(trace_b.certificate)


def test_short_hash_and_hash_file(tmp_path: Path) -> None:
    path = tmp_path / "asset.txt"
    path.write_text("mathgraph", encoding="utf-8")
    digest = hash_file(path)

    assert len(digest) == 64
    assert short_hash("mathgraph", 8) == sha256_json("mathgraph")[:8]
    assert content_id("trace", {"claim": "x = x"}).startswith("trace_")


def test_merkle_root_deterministic_and_proof_verifies() -> None:
    leaves = [sha256_json({"i": i}) for i in range(5)]
    root = merkle_root(leaves)
    proof = merkle_proof(leaves, 3)

    assert root == merkle_root(list(leaves))
    assert verify_merkle_proof(leaves[3], proof, root)
    assert not verify_merkle_proof(leaves[2], proof, root)
    assert not verify_merkle_proof(leaves[3], proof, sha256_json("tampered-root"))


def test_merkle_empty_root_is_stable() -> None:
    assert merkle_root([]) == sha256_json([])


def test_jsonl_ledger_merkle_root_after_appending_traces(tmp_path: Path) -> None:
    ledger = JsonlLedger(tmp_path / "ledger.jsonl")
    kernel = Kernel(ledger=ledger)

    kernel.prove("x = x")
    kernel.prove("x = x", "x * x = x")

    hashes = ledger.ledger_hashes()
    summary = ledger.audit()

    assert len(hashes) == 2
    assert ledger.merkle_root() == merkle_root(hashes)
    assert summary["trace_count"] == 2
    assert summary["merkle_root"] == ledger.merkle_root()


def test_replay_obstruction_is_never_proof() -> None:
    trace = Kernel(finite_magmas=[]).prove("x * y = x", "x * y = y")
    audit = replay_trace(trace)

    assert audit["terminal_form"] == "NAMED_OBSTRUCTION"
    assert audit["passed"]
    assert trace.verify() is False
    assert trace.is_verified_proof() is False


def test_finite_countermodel_has_reproducible_certificate_hash() -> None:
    trace = Kernel().prove("x = x", "x * x = x")

    assert trace.certificate is not None
    assert trace.certificate.content_hash() == hash_certificate(trace.certificate.to_dict())
    assert trace.content_hash() == hash_trace(trace.to_dict())


def test_cli_audit_works_on_temp_ledger(tmp_path: Path) -> None:
    ledger = JsonlLedger(tmp_path / "ledger.jsonl")
    Kernel(ledger=ledger).prove("x = x")

    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "audit_ledger.py"), str(ledger.path)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert '"passed": true' in result.stdout


def test_replay_ledger_summary(tmp_path: Path) -> None:
    ledger = JsonlLedger(tmp_path / "ledger.jsonl")
    Kernel(ledger=ledger).prove("x = x")

    summary = replay_ledger(ledger.path)

    assert summary["passed"] is True
    assert summary["trace_count"] == 1
    assert summary["merkle_root"] == ledger.merkle_root()
