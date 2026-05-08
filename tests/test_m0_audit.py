import json
import subprocess
import sys

from mathgraph.lawbook_store import LawbookStore
from mathgraph.m0_audit import audit_m0_store
from mathgraph.m0_certificate_factory import run_m0_episode


def _write_pairs(path):
    path.write_text(
        json.dumps({"source": "(x*x)=x", "target": "(x*y)=x", "source_idx": 1, "target_idx": 2})
        + "\n",
        encoding="utf-8",
    )


def test_audit_passes_after_normal_m0_run(tmp_path):
    pairs = tmp_path / "pairs.jsonl"
    store = tmp_path / "m0.sqlite"
    _write_pairs(pairs)
    run_m0_episode({"pairs_jsonl": str(pairs), "store_path": str(store)})

    report = audit_m0_store(str(store))

    assert report.passed is True
    assert report.critical_count == 0
    assert report.checked_certificates >= 1


def test_audit_detects_advisory_candidate_certificate_row(tmp_path):
    store = LawbookStore(tmp_path / "poison.sqlite")
    try:
        store.init_schema()
        store.conn.execute(
            """
            INSERT INTO certificates (
                certificate_id, claim_id, terminal_form, verification_status,
                trust_level, provenance_type, payload_json, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "candidate_cert",
                "claim",
                "REFUTATION_CERTIFICATE",
                "NOT_VERIFIED",
                "CANDIDATE_CERTIFICATE",
                "ADVISORY",
                json.dumps({"candidate": True}),
                json.dumps({}),
            ),
        )
        store.conn.commit()
    finally:
        store.close()

    report = audit_m0_store(str(tmp_path / "poison.sqlite"))

    assert report.passed is False
    assert report.critical_count > 0
    assert any(finding.code == "CANDIDATE_CERTIFICATE_ROW" for finding in report.findings)


def test_audit_detects_refutation_missing_witness_or_table(tmp_path):
    store = LawbookStore(tmp_path / "bad_refutation.sqlite")
    try:
        store.init_schema()
        store.conn.execute(
            """
            INSERT INTO refutations (
                refutation_id, source, target, terminal_form, verification_status,
                trust_level, provenance_type, table_hash, table_json, witness_json, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "bad_ref",
                "x=x",
                "x=y",
                "FINITE_COUNTERMODEL",
                "FINITE_VERIFIED",
                "FINITE_VERIFIED",
                "IMPORTED",
                "",
                None,
                None,
                json.dumps({}),
            ),
        )
        store.conn.commit()
    finally:
        store.close()

    report = audit_m0_store(str(tmp_path / "bad_refutation.sqlite"))

    assert report.passed is False
    assert any(finding.code == "REFUTATION_MISSING_TABLE_OR_WITNESS" for finding in report.findings)


def test_audit_cli_writes_report_and_can_fail_on_critical(tmp_path):
    store = LawbookStore(tmp_path / "poison_cli.sqlite")
    try:
        store.init_schema()
        store.conn.execute(
            """
            INSERT INTO certificates (
                certificate_id, claim_id, terminal_form, verification_status,
                trust_level, provenance_type, payload_json, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "advisory_cert",
                "claim",
                "REFUTATION_CERTIFICATE",
                "REFUTED",
                "ADVISORY_ROUTE",
                "ADVISORY",
                json.dumps({"candidate": True}),
                json.dumps({}),
            ),
        )
        store.conn.commit()
    finally:
        store.close()
    report_path = tmp_path / "audit.json"

    proc = subprocess.run(
        [
            sys.executable,
            "scripts/audit_m0_store.py",
            "--store",
            str(tmp_path / "poison_cli.sqlite"),
            "--report",
            str(report_path),
            "--fail-on-critical",
        ],
        text=True,
        capture_output=True,
    )

    assert proc.returncode == 2
    assert report_path.exists()
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["critical_count"] > 0
