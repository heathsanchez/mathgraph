"""Public local SDK client for the Milestone 0 MathGraph middleware boundary."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from mathgraph.kernel_oracle import KernelOracle, OracleAnswer
from mathgraph.lawbook_store import LawbookStore
from mathgraph.m0_audit import audit_m0_store
from mathgraph.m0_certificate_factory import M0EpisodeConfig, M0PairResult, run_m0_episode
from mathgraph.terminal_contract import (
    ProvenanceType,
    Status,
    TerminalContractResult,
    TerminalForm,
    TrustLevel,
    VerifierBoundary,
)


@dataclass(frozen=True)
class MathGraphClientConfig:
    store_path: str
    working_dir: str | None = None
    ledger_jsonl: str | None = None
    metrics_history_jsonl: str | None = None
    default_domain: str = "magma_equation"
    default_max_countermodel_order: int = 3
    random_tables_per_order: int = 0
    exhaustive_order_limit: int = 3
    audit_after_write: bool = True
    fail_on_critical_audit: bool = True

    @classmethod
    def from_value(cls, value: "MathGraphClientConfig | str | Path") -> "MathGraphClientConfig":
        if isinstance(value, cls):
            return value
        return cls(store_path=str(value))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MathGraphAnswer:
    status: str
    terminal_form: str
    trust_level: str
    provenance_type: str
    verifier_boundary: str
    certificate_id: str | None
    certificate_chain: list[str]
    source: str
    target: str
    source_idx: int | None
    target_idx: int | None
    claim: str
    explanation: str
    warnings: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)
    audit: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "terminal_form": self.terminal_form,
            "trust_level": self.trust_level,
            "provenance_type": self.provenance_type,
            "verifier_boundary": self.verifier_boundary,
            "certificate_id": self.certificate_id,
            "certificate_chain": list(self.certificate_chain),
            "source": self.source,
            "target": self.target,
            "source_idx": self.source_idx,
            "target_idx": self.target_idx,
            "claim": self.claim,
            "explanation": self.explanation,
            "warnings": list(self.warnings),
            "evidence": dict(self.evidence),
            "audit": dict(self.audit) if self.audit is not None else None,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)


class MathGraphAuditError(RuntimeError):
    """Raised when an SDK write is followed by a critical M0 audit failure."""

    def __init__(self, audit_report: dict[str, Any]) -> None:
        super().__init__("MathGraph M0 audit found critical trust-boundary findings.")
        self.audit_report = dict(audit_report)


class MathGraphClient:
    def __init__(self, config_or_store_path: MathGraphClientConfig | str | Path) -> None:
        self.config = MathGraphClientConfig.from_value(config_or_store_path)

    def query_claim(
        self,
        source: str,
        target: str,
        source_idx: int | None = None,
        target_idx: int | None = None,
    ) -> MathGraphAnswer:
        store = LawbookStore(self.config.store_path)
        try:
            store.init_schema()
            answer = KernelOracle(store).query(source, target)
            if _is_known_oracle_answer(answer):
                return _answer_from_oracle(answer, source_idx=source_idx, target_idx=target_idx)
            return _safe_unknown(source, target, source_idx, target_idx, answer.explanation, answer.to_dict())
        finally:
            store.close()

    def submit_claim(
        self,
        source: str,
        target: str,
        source_idx: int | None = None,
        target_idx: int | None = None,
        allow_construction: bool = True,
        max_countermodel_order: int | None = None,
    ) -> MathGraphAnswer:
        known = self.query_claim(source, target, source_idx=source_idx, target_idx=target_idx)
        if known.certificate_id:
            return known
        if not allow_construction:
            return _safe_unknown(
                source,
                target,
                source_idx,
                target_idx,
                "Construction disabled.",
                {"allow_construction": False},
            )

        with TemporaryDirectory(prefix="mathgraph_client_", dir=self.config.working_dir) as tmp:
            pair_path = Path(tmp) / "pair.jsonl"
            pair_path.write_text(
                json.dumps(
                    {
                        "source": source,
                        "target": target,
                        "source_idx": source_idx,
                        "target_idx": target_idx,
                        "domain": self.config.default_domain,
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            result = run_m0_episode(
                M0EpisodeConfig(
                    pairs_jsonl=str(pair_path),
                    store_path=self.config.store_path,
                    ledger_jsonl=self.config.ledger_jsonl,
                    metrics_history_jsonl=self.config.metrics_history_jsonl,
                    max_tasks=1,
                    max_countermodel_order=max_countermodel_order
                    if max_countermodel_order is not None
                    else self.config.default_max_countermodel_order,
                    random_tables_per_order=self.config.random_tables_per_order,
                    exhaustive_order_limit=self.config.exhaustive_order_limit,
                    working_dir=self.config.working_dir,
                    allow_construction=True,
                )
            )

        audit_payload = None
        if self.config.audit_after_write:
            audit_payload = self.audit()
            if self.config.fail_on_critical_audit and audit_payload.get("critical_count", 0) > 0:
                raise MathGraphAuditError(audit_payload)
        if result.results:
            return _answer_from_m0_result(result.results[0], audit_payload)
        return _safe_unknown(source, target, source_idx, target_idx, "No M0 result row was produced.", {}, audit_payload)

    def audit(self) -> dict[str, Any]:
        return audit_m0_store(self.config.store_path).to_dict()

    def stats(self) -> dict[str, Any]:
        store = LawbookStore(self.config.store_path)
        try:
            store.init_schema()
            if hasattr(store, "full_certificate_stats"):
                return store.full_certificate_stats()
            return store.stats().to_dict()
        finally:
            store.close()

    def close(self) -> None:
        return None


def _answer_from_m0_result(result: M0PairResult, audit_payload: dict[str, Any] | None) -> MathGraphAnswer:
    contract = TerminalContractResult(
        status=result.status,
        terminal_form=result.terminal_form or TerminalForm.NONE,
        trust_level=result.trust_level or TrustLevel.ADVISORY_ROUTE,
        provenance_type=result.provenance_type or ProvenanceType.SYSTEM,
        verifier_boundary=result.verifier_boundary or VerifierBoundary.NOT_VERIFIED,
        certificate_id=result.certificate_id,
        certificate_chain=list(result.certificate_chain),
        warnings=list(result.warnings),
        evidence=dict(result.evidence),
    )
    return MathGraphAnswer(
        status=contract.status,
        terminal_form=contract.terminal_form,
        trust_level=contract.trust_level,
        provenance_type=contract.provenance_type,
        verifier_boundary=contract.verifier_boundary,
        certificate_id=contract.certificate_id,
        certificate_chain=contract.certificate_chain,
        source=result.source,
        target=result.target,
        source_idx=result.source_idx,
        target_idx=result.target_idx,
        claim=_claim(result.source, result.target),
        explanation=result.explanation,
        warnings=contract.warnings,
        evidence=contract.evidence,
        audit=audit_payload,
    )


def _answer_from_oracle(
    answer: OracleAnswer,
    source_idx: int | None = None,
    target_idx: int | None = None,
) -> MathGraphAnswer:
    terminal = _public_terminal_form(answer.terminal_form)
    trust = _public_trust(answer)
    provenance = _public_provenance(answer)
    boundary = _public_boundary(answer)
    chain = list(answer.certificate_chain or ([answer.certificate_id] if answer.certificate_id else []))
    contract = TerminalContractResult(
        status=answer.status,
        terminal_form=terminal,
        trust_level=trust,
        provenance_type=provenance,
        verifier_boundary=boundary,
        certificate_id=answer.certificate_id,
        certificate_chain=chain,
        warnings=list(answer.warnings),
        evidence=dict(answer.evidence),
    )
    evidence = dict(contract.evidence)
    return MathGraphAnswer(
        status=contract.status,
        terminal_form=contract.terminal_form,
        trust_level=contract.trust_level,
        provenance_type=contract.provenance_type,
        verifier_boundary=contract.verifier_boundary,
        certificate_id=contract.certificate_id,
        certificate_chain=contract.certificate_chain,
        source=answer.source or "",
        target=answer.target or "",
        source_idx=source_idx if source_idx is not None else _optional_int(evidence.get("source_idx")),
        target_idx=target_idx if target_idx is not None else _optional_int(evidence.get("target_idx")),
        claim=answer.claim or _claim(answer.source or "", answer.target or ""),
        explanation=answer.explanation,
        warnings=contract.warnings,
        evidence=evidence,
    )


def _safe_unknown(
    source: str,
    target: str,
    source_idx: int | None,
    target_idx: int | None,
    explanation: str,
    evidence: dict[str, Any],
    audit_payload: dict[str, Any] | None = None,
) -> MathGraphAnswer:
    contract = TerminalContractResult(
        status=Status.UNKNOWN,
        terminal_form=TerminalForm.NAMED_OBSTRUCTION,
        trust_level=TrustLevel.ADVISORY_ROUTE,
        provenance_type=ProvenanceType.SYSTEM,
        verifier_boundary=VerifierBoundary.NOT_VERIFIED,
        certificate_id=None,
        certificate_chain=[],
        warnings=[
            "No exact verified lawbook certificate found.",
            "Finite search failure is not proof.",
            "Advisory routes are never truth.",
        ],
        evidence=dict(evidence),
    )
    return MathGraphAnswer(
        status=contract.status,
        terminal_form=contract.terminal_form,
        trust_level=contract.trust_level,
        provenance_type=contract.provenance_type,
        verifier_boundary=contract.verifier_boundary,
        certificate_id=None,
        certificate_chain=[],
        source=source,
        target=target,
        source_idx=source_idx,
        target_idx=target_idx,
        claim=_claim(source, target),
        explanation=explanation,
        warnings=contract.warnings,
        evidence=contract.evidence,
        audit=audit_payload,
    )


def _is_known_oracle_answer(answer: OracleAnswer) -> bool:
    return bool(answer.certificate_id and answer.status in {"VERIFIED", "REFUTED"})


def _public_terminal_form(terminal_form: str) -> str:
    if terminal_form == "FINITE_COUNTERMODEL":
        return TerminalForm.REFUTATION_CERTIFICATE
    if terminal_form == TerminalForm.VERIFIED_PROOF:
        return TerminalForm.VERIFIED_PROOF
    if terminal_form == TerminalForm.NAMED_OBSTRUCTION:
        return TerminalForm.NAMED_OBSTRUCTION
    return TerminalForm.NONE


def _public_trust(answer: OracleAnswer) -> str:
    if answer.terminal_form == "FINITE_COUNTERMODEL":
        return TrustLevel.FINITE_VERIFIED
    if answer.trust_level == "derived_from_verified_traces":
        return TrustLevel.DERIVED_CHAIN_VERIFIED
    if answer.terminal_form == TerminalForm.VERIFIED_PROOF:
        return TrustLevel.LEAN_VERIFIED
    return TrustLevel.ADVISORY_ROUTE


def _public_provenance(answer: OracleAnswer) -> str:
    if answer.trust_level == "derived_from_verified_traces":
        return ProvenanceType.DERIVED
    if answer.provenance_type in {
        ProvenanceType.PRIMITIVE,
        ProvenanceType.DERIVED,
        ProvenanceType.IMPORTED,
        ProvenanceType.HUMAN_REVIEWED,
        ProvenanceType.ADVISORY,
        ProvenanceType.SYSTEM,
    }:
        return answer.provenance_type
    return ProvenanceType.PRIMITIVE if answer.certificate_id else ProvenanceType.SYSTEM


def _public_boundary(answer: OracleAnswer) -> str:
    if answer.terminal_form == "FINITE_COUNTERMODEL":
        return VerifierBoundary.IMPORTER_REVALIDATED
    if answer.trust_level == "derived_from_verified_traces":
        return VerifierBoundary.CHAIN_AUDITED
    if answer.terminal_form == TerminalForm.VERIFIED_PROOF:
        return VerifierBoundary.LEAN_TYPECHECKED
    return VerifierBoundary.NOT_VERIFIED


def _claim(source: str, target: str) -> str:
    return f"{source} => {target}"


def _optional_int(value: Any) -> int | None:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None
