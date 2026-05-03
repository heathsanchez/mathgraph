"""Replay and audit helpers for serialized MathGraph traces."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mathgraph.certificates import TerminalForm, VerificationStatus
from mathgraph.hashing import hash_trace
from mathgraph.ledger import JsonlLedger
from mathgraph.merkle import merkle_root
from mathgraph.trace import Trace


def replay_trace(trace_or_dict: Trace | dict[str, Any]) -> dict[str, Any]:
    trace = trace_or_dict if isinstance(trace_or_dict, Trace) else Trace.from_dict(trace_or_dict)
    trace_hash = hash_trace(trace)
    errors: list[str] = []

    if trace.terminal_form == TerminalForm.VERIFIED_PROOF:
        if trace.verification_status != VerificationStatus.VERIFIED:
            errors.append("verified_proof_status_mismatch")
        if trace.certificate is None or not trace.certificate.payload:
            errors.append("verified_proof_missing_certificate_payload")

    elif trace.terminal_form == TerminalForm.FINITE_COUNTERMODEL:
        if trace.verification_status != VerificationStatus.REFUTED:
            errors.append("finite_countermodel_status_mismatch")
        if trace.certificate is None or not trace.certificate.payload.get("model"):
            errors.append("finite_countermodel_missing_certificate_payload")

    elif trace.terminal_form == TerminalForm.NAMED_OBSTRUCTION:
        if trace.verification_status == VerificationStatus.VERIFIED or trace.certificate is not None:
            errors.append("obstruction_treated_as_proof")
        if trace.obstruction is None:
            errors.append("obstruction_missing_payload")

    else:
        errors.append("unknown_terminal_form")

    return {
        "passed": not errors,
        "trace_hash": trace_hash,
        "claim": trace.claim,
        "terminal_form": trace.terminal_form.value,
        "verification_status": trace.verification_status.value,
        "errors": errors,
    }


def replay_ledger(path: str | Path) -> dict[str, Any]:
    ledger = JsonlLedger(path)
    entries = list(ledger.iter_entries())
    trace_audits: list[dict[str, Any]] = []
    bad_entries: list[dict[str, Any]] = []
    trace_hashes: list[str] = []

    for index, entry in enumerate(entries):
        if entry.get("bad_entry"):
            bad_entries.append(entry)
            continue
        try:
            trace = Trace.from_dict(entry["trace"])
            audit = replay_trace(trace)
        except (KeyError, TypeError, ValueError) as exc:
            bad_entries.append({"index": index, "error": str(exc)})
            continue

        stored_hash = entry.get("trace_hash")
        if stored_hash != audit["trace_hash"]:
            audit["passed"] = False
            audit["errors"].append("trace_hash_mismatch")
        trace_audits.append(audit)
        if audit["passed"]:
            trace_hashes.append(audit["trace_hash"])

    summary = ledger.audit()
    passed = not bad_entries and not summary["bad_entries"] and all(a["passed"] for a in trace_audits)
    return {
        "passed": passed,
        "path": str(Path(path)),
        "entry_count": len(entries),
        "trace_count": len(trace_audits),
        "bad_entries": bad_entries + list(summary["bad_entries"]),
        "trace_hashes": trace_hashes,
        "merkle_root": merkle_root(trace_hashes),
        "terminal_form_counts": summary["terminal_form_counts"],
        "verification_status_counts": summary["verification_status_counts"],
        "trace_audits": trace_audits,
    }
