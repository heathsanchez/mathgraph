from __future__ import annotations

import json
import subprocess
import sys

from mathgraph.kernel_oracle import KernelOracle
from mathgraph.lawbook_store import LawbookStore
from mathgraph.m0_certificate_factory import M0EpisodeConfig, run_m0_episode


def _write_pairs(path, rows):
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def _false_pair():
    return {
        "source": "(x*x)=x",
        "target": "(x*y)=x",
        "source_idx": 1,
        "target_idx": 2,
    }


def test_m0_promotes_known_false_pair(tmp_path):
    pairs = tmp_path / "pairs.jsonl"
    store = tmp_path / "m0.sqlite"
    ledger = tmp_path / "ledger.jsonl"
    report = tmp_path / "report.json"
    history = tmp_path / "metrics.jsonl"
    _write_pairs(pairs, [_false_pair()])

    result = run_m0_episode(
        M0EpisodeConfig(
            pairs_jsonl=str(pairs),
            store_path=str(store),
            ledger_jsonl=str(ledger),
            report_json=str(report),
            metrics_history_jsonl=str(history),
            episode_id="m0_test_first",
            max_countermodel_order=3,
        )
    )

    assert result.metrics.attempted == 1
    assert result.metrics.verified_false == 1
    assert result.metrics.promoted == 1
    assert result.metrics.new_unique_certificates == 1
    assert result.metrics.compounding_confirmed is True
    row = result.results[0]
    assert row.status == "verified_false"
    assert row.terminal_form == "FINITE_COUNTERMODEL"
    assert row.trust_level == "finite_verified"
    assert row.provenance_type == "primitive"
    assert row.certificate_id
    assert report.exists()
    assert store.exists()


def test_m0_rerun_skips_known_certificate_without_duplicate(tmp_path):
    pairs = tmp_path / "pairs.jsonl"
    store_path = tmp_path / "m0.sqlite"
    history = tmp_path / "metrics.jsonl"
    _write_pairs(pairs, [_false_pair()])

    first = run_m0_episode(
        {
            "pairs_jsonl": str(pairs),
            "store_path": str(store_path),
            "metrics_history_jsonl": str(history),
            "episode_id": "m0_first",
        }
    )
    second = run_m0_episode(
        {
            "pairs_jsonl": str(pairs),
            "store_path": str(store_path),
            "metrics_history_jsonl": str(history),
            "episode_id": "m0_second",
        }
    )

    assert first.metrics.new_unique_certificates == 1
    assert second.metrics.known_skipped == 1
    assert second.metrics.new_unique_certificates == 0
    assert second.results[0].status == "known_certificate_found"
    assert second.results[0].certificate_id
    store = LawbookStore(store_path)
    try:
        store.init_schema()
        assert store.stats().trace_count == 1
        assert KernelOracle(store).query(_false_pair()["source"], _false_pair()["target"]).status == "REFUTED"
    finally:
        store.close()


def test_m0_finite_miss_is_not_proof(tmp_path):
    pairs = tmp_path / "pairs.jsonl"
    store = tmp_path / "m0.sqlite"
    _write_pairs(pairs, [{"source": "(x*x)=x", "target": "(x*x)=x"}])

    result = run_m0_episode(
        {
            "pairs_jsonl": str(pairs),
            "store_path": str(store),
            "episode_id": "m0_miss",
            "max_countermodel_order": 1,
            "exhaustive_order_limit": 1,
        }
    )

    assert result.metrics.verified_true == 0
    assert result.metrics.promoted == 0
    assert result.results[0].status in {"constructor_failed", "residual"}
    assert result.results[0].terminal_form is None


def test_m0_bad_parse_does_not_crash_or_promote(tmp_path):
    pairs = tmp_path / "pairs.jsonl"
    store = tmp_path / "m0.sqlite"
    _write_pairs(pairs, [{"source": "not an equation", "target": "(x*x)=x"}])

    result = run_m0_episode({"pairs_jsonl": str(pairs), "store_path": str(store)})

    assert result.metrics.parse_failed == 1
    assert result.metrics.promoted == 0
    assert result.results[0].status == "parse_failed"


def test_m0_cli_smoke(tmp_path):
    pairs = tmp_path / "pairs.jsonl"
    store = tmp_path / "m0.sqlite"
    ledger = tmp_path / "ledger.jsonl"
    report = tmp_path / "report.json"
    history = tmp_path / "metrics.jsonl"
    _write_pairs(pairs, [_false_pair()])

    proc = subprocess.run(
        [
            sys.executable,
            "scripts/chew_certificate_tasks.py",
            "--pairs",
            str(pairs),
            "--store",
            str(store),
            "--ledger",
            str(ledger),
            "--report",
            str(report),
            "--metrics-history",
            str(history),
            "--episode-id",
            "m0_cli",
            "--max-tasks",
            "10",
            "--max-countermodel-order",
            "3",
        ],
        text=True,
        capture_output=True,
        timeout=20,
    )

    assert proc.returncode == 0, proc.stderr
    summary = json.loads(proc.stdout)
    assert summary["verified_false"] == 1
    assert report.exists()
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["metrics"]["promoted"] == 1
    assert payload["results"][0]["warnings"]

