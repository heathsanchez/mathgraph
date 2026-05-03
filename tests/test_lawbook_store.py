import json
import subprocess
import sys
from pathlib import Path

from mathgraph import CertificateLawbook, Kernel, LawbookStore


ROOT = Path(__file__).resolve().parents[1]


def _traces():
    proof = Kernel().prove("x = x", "x = x")
    proof.metadata.update({"source_idx": "1", "target_idx": "2", "compiled_route": "variable_identification", "claim_hash": "claim-proof"})
    counter = Kernel().prove("x = x", "x * x = x")
    counter.metadata.update({"source_idx": "1", "target_idx": "3", "compiled_route": "finite_countermodel", "claim_hash": "claim-counter"})
    missing_optional = Kernel().prove("y = y")
    return [proof, counter, missing_optional]


def _write_traces(path: Path) -> None:
    path.write_text(json.dumps([trace.to_dict() for trace in _traces()]), encoding="utf-8")


def _store(path: Path) -> LawbookStore:
    store = LawbookStore(path)
    store.init_schema()
    store.import_lawbook(CertificateLawbook.from_traces(_traces()), replace=True)
    return store


def test_schema_initializes(tmp_path: Path) -> None:
    store = LawbookStore(tmp_path / "lawbook.sqlite")
    try:
        store.init_schema()
        assert store.stats().trace_count == 0
    finally:
        store.close()


def test_import_and_stats(tmp_path: Path) -> None:
    traces = tmp_path / "traces.json"
    _write_traces(traces)
    store = LawbookStore(tmp_path / "lawbook.sqlite")
    try:
        stats = store.import_traces_json(traces, replace=True)
        assert stats.trace_count == 3
        assert stats.certificate_count == 3
        assert stats.terminal_form_counts["VERIFIED_PROOF"] == 2
        assert stats.terminal_form_counts["FINITE_COUNTERMODEL"] == 1
        assert stats.route_counts["finite_countermodel"] == 1
    finally:
        store.close()


def test_get_by_claim_and_pair(tmp_path: Path) -> None:
    store = _store(tmp_path / "lawbook.sqlite")
    try:
        assert store.get_by_claim("claim-proof")["terminal_form"] == "VERIFIED_PROOF"
        assert store.get_by_pair("1", "3")["terminal_form"] == "FINITE_COUNTERMODEL"
        assert store.get_by_pair("x = x", "(x * x) = x")["verification_status"] == "REFUTED"
    finally:
        store.close()


def test_missing_pair_returns_obstruction_style(tmp_path: Path) -> None:
    store = _store(tmp_path / "lawbook.sqlite")
    try:
        missing = store.explain_pair("missing", "pair")
        assert missing["status"] == "missing"
        assert missing["terminal_form"] == "NAMED_OBSTRUCTION"
        assert missing["verification_status"] == "UNKNOWN"
    finally:
        store.close()


def test_find_helpers(tmp_path: Path) -> None:
    store = _store(tmp_path / "lawbook.sqlite")
    try:
        assert len(store.find_by_source("1")) == 2
        assert len(store.find_by_target("3")) == 1
        assert store.find_by_route("finite_countermodel")[0]["terminal_form"] == "FINITE_COUNTERMODEL"
        assert len(store.find_by_terminal_form("VERIFIED_PROOF")) == 2
    finally:
        store.close()


def test_replace_clears_old_data(tmp_path: Path) -> None:
    store = LawbookStore(tmp_path / "lawbook.sqlite")
    try:
        store.import_lawbook(CertificateLawbook.from_traces(_traces()), replace=True)
        assert store.stats().trace_count == 3
        store.import_lawbook(CertificateLawbook.from_traces(_traces()[:1]), replace=True)
        assert store.stats().trace_count == 1
    finally:
        store.close()


def test_build_lawbook_store_cli(tmp_path: Path) -> None:
    traces = tmp_path / "traces.json"
    sqlite_path = tmp_path / "lawbook.sqlite"
    summary_path = tmp_path / "summary.json"
    _write_traces(traces)

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_lawbook_store.py"),
            "--traces-json",
            str(traces),
            "--out",
            str(sqlite_path),
            "--replace",
            "--summary-json",
            str(summary_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert sqlite_path.exists()
    assert json.loads(summary_path.read_text(encoding="utf-8"))["trace_count"] == 3
