"""Audit helpers for the Milestone 0 LawbookStore trust boundary."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AuditFinding:
    severity: str
    code: str
    message: str
    claim_id: str | None = None
    certificate_id: str | None = None
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AuditReport:
    store_path: str
    checked_claims: int
    checked_certificates: int
    finding_count: int
    critical_count: int
    warning_count: int
    info_count: int
    passed: bool
    findings: list[AuditFinding]

    def to_dict(self) -> dict[str, Any]:
        return {
            "store_path": self.store_path,
            "checked_claims": self.checked_claims,
            "checked_certificates": self.checked_certificates,
            "finding_count": self.finding_count,
            "critical_count": self.critical_count,
            "warning_count": self.warning_count,
            "info_count": self.info_count,
            "passed": self.passed,
            "findings": [finding.to_dict() for finding in self.findings],
        }


def audit_m0_store(store_path: str) -> AuditReport:
    findings: list[AuditFinding] = []
    conn = sqlite3.connect(store_path)
    conn.row_factory = sqlite3.Row
    try:
        traces = _rows(conn, "traces")
        certificates = _rows(conn, "certificates")
        refutations = _rows(conn, "refutations")
        _audit_traces(traces, findings)
        _audit_certificates(certificates, findings)
        _audit_refutations(refutations, findings)
        _audit_duplicate_pairs(traces, refutations, findings)
    finally:
        conn.close()
    critical = sum(1 for finding in findings if finding.severity == "critical")
    warning = sum(1 for finding in findings if finding.severity == "warning")
    info = sum(1 for finding in findings if finding.severity == "info")
    return AuditReport(
        store_path=str(store_path),
        checked_claims=len(traces),
        checked_certificates=len(certificates) + len(refutations) + sum(1 for row in traces if row.get("certificate_id")),
        finding_count=len(findings),
        critical_count=critical,
        warning_count=warning,
        info_count=info,
        passed=critical == 0,
        findings=findings,
    )


def _audit_traces(rows: list[dict[str, Any]], findings: list[AuditFinding]) -> None:
    for row in rows:
        cert_id = row.get("certificate_id")
        terminal = row.get("terminal_form")
        verification = row.get("verification_status")
        cert = _json(row.get("certificate_json")) or {}
        metadata = _json(row.get("metadata_json")) or {}
        payload = cert.get("payload", {}) if isinstance(cert, dict) else {}
        if terminal in {"NONE", "", None}:
            _finding(findings, "critical", "PROMOTED_NONE_TERMINAL", "Promoted trace has no terminal form.", row, cert_id)
        if not cert_id and terminal in {"FINITE_COUNTERMODEL", "VERIFIED_PROOF"}:
            _finding(findings, "critical", "MISSING_CERTIFICATE_ID", "Verified trace is missing certificate_id.", row, cert_id)
        if terminal == "VERIFIED_PROOF" and verification == "FINITE_VERIFIED":
            _finding(findings, "critical", "PROOF_WITH_FINITE_VERIFIED", "Verified proof cannot use finite refutation trust.", row, cert_id)
        if terminal == "FINITE_COUNTERMODEL":
            model = payload.get("model", {}) if isinstance(payload, dict) else {}
            countermodel = payload.get("countermodel") or model.get("countermodel")
            witness = payload.get("witness") or model.get("witness")
            if not countermodel or not witness:
                _finding(findings, "critical", "REFUTATION_MISSING_MODEL_EVIDENCE", "Finite refutation lacks countermodel or witness payload.", row, cert_id)
            if not (model.get("importer_revalidated") or metadata.get("importer_revalidated")):
                _finding(findings, "warning", "LEGACY_OR_UNMARKED_REVALIDATION", "Finite refutation lacks explicit importer_revalidated evidence.", row, cert_id)


def _audit_certificates(rows: list[dict[str, Any]], findings: list[AuditFinding]) -> None:
    for row in rows:
        cert_id = row.get("certificate_id")
        trust = str(row.get("trust_level") or "")
        terminal = str(row.get("terminal_form") or "")
        verification = str(row.get("verification_status") or "")
        payload = _json(row.get("payload_json")) or {}
        evidence = _json(row.get("evidence_json")) or {}
        if not cert_id:
            _finding(findings, "critical", "MISSING_CERTIFICATE_ID", "Certificate row is missing certificate_id.", row, cert_id)
        if trust in {"ADVISORY_ROUTE", "advisory_only", "ADVISORY"}:
            _finding(findings, "critical", "ADVISORY_CERTIFICATE_ROW", "Advisory trust cannot cross into certificate table.", row, cert_id)
        if trust == "CANDIDATE_CERTIFICATE":
            _finding(findings, "critical", "CANDIDATE_CERTIFICATE_ROW", "Candidate certificate cannot cross into certificate table.", row, cert_id)
        if any(word in verification.upper() for word in ("FAILED", "ERROR", "UNKNOWN", "NOT_VERIFIED")):
            _finding(findings, "critical", "UNVERIFIED_CERTIFICATE_ROW", "Certificate row has non-terminal/failure verification status.", row, cert_id)
        if terminal in {"NONE", ""}:
            _finding(findings, "critical", "CERTIFICATE_NONE_TERMINAL", "Certificate row has no terminal form.", row, cert_id)
        if terminal == "VERIFIED_PROOF" and trust == "FINITE_VERIFIED":
            _finding(findings, "critical", "PROOF_WITH_FINITE_VERIFIED", "Verified proof cannot use finite refutation trust.", row, cert_id)
        if terminal in {"REFUTATION_CERTIFICATE", "FINITE_COUNTERMODEL"} and not _has_model_evidence(payload, evidence):
            _finding(findings, "critical", "REFUTATION_WITHOUT_MODEL", "Refutation certificate lacks finite/model evidence.", row, cert_id)


def _audit_refutations(rows: list[dict[str, Any]], findings: list[AuditFinding]) -> None:
    for row in rows:
        cert_id = row.get("refutation_id")
        if not cert_id:
            _finding(findings, "critical", "MISSING_REFUTATION_ID", "Refutation row is missing refutation_id.", row, cert_id)
        if not row.get("table_hash") or not row.get("witness_json"):
            _finding(findings, "critical", "REFUTATION_MISSING_TABLE_OR_WITNESS", "Refutation row lacks table hash or witness payload.", row, cert_id)
        if not row.get("payload_json"):
            _finding(findings, "critical", "REFUTATION_MISSING_PAYLOAD", "Finite verified refutation lacks payload evidence.", row, cert_id)
        trust = str(row.get("trust_level") or "")
        if trust in {"ADVISORY_ROUTE", "CANDIDATE_CERTIFICATE"}:
            _finding(findings, "critical", "UNSAFE_REFUTATION_TRUST", "Unsafe trust level in refutations table.", row, cert_id)


def _audit_duplicate_pairs(
    traces: list[dict[str, Any]],
    refutations: list[dict[str, Any]],
    findings: list[AuditFinding],
) -> None:
    by_pair: dict[tuple[str | None, str | None], set[str]] = {}
    for row in traces:
        by_pair.setdefault((row.get("source"), row.get("target")), set()).add(str(row.get("terminal_form")))
    for row in refutations:
        by_pair.setdefault((row.get("source"), row.get("target")), set()).add(str(row.get("terminal_form")))
    for pair, terminals in by_pair.items():
        cleaned = {terminal for terminal in terminals if terminal and terminal != "None"}
        if len(cleaned) > 1:
            findings.append(
                AuditFinding(
                    severity="critical",
                    code="CONFLICTING_DUPLICATE_PAIR_TERMINALS",
                    message="Duplicate primitive pair has conflicting terminal forms.",
                    evidence={"pair": list(pair), "terminal_forms": sorted(cleaned)},
                )
            )


def _has_model_evidence(payload: dict[str, Any], evidence: dict[str, Any]) -> bool:
    blobs = [payload, evidence]
    for blob in blobs:
        if not isinstance(blob, dict):
            continue
        if blob.get("countermodel") and blob.get("witness"):
            return True
        model = blob.get("model")
        if isinstance(model, dict) and model.get("countermodel") and model.get("witness"):
            return True
    return False


def _rows(conn: sqlite3.Connection, table: str) -> list[dict[str, Any]]:
    try:
        return [dict(row) for row in conn.execute(f"SELECT * FROM {table}").fetchall()]
    except sqlite3.OperationalError:
        return []


def _json(text: Any) -> Any:
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        return None


def _finding(
    findings: list[AuditFinding],
    severity: str,
    code: str,
    message: str,
    row: dict[str, Any],
    certificate_id: str | None,
) -> None:
    findings.append(
        AuditFinding(
            severity=severity,
            code=code,
            message=message,
            claim_id=row.get("claim_id") or row.get("claim"),
            certificate_id=certificate_id,
            evidence={key: row.get(key) for key in sorted(row) if key.endswith("_id") or key in {"terminal_form", "verification_status", "trust_level", "source", "target"}},
        )
    )


def write_audit_report(report: AuditReport, path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")

