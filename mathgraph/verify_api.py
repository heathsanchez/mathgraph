"""High-level MathGraph verification API."""

from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mathgraph.countermodel_importer import (
    CountermodelImportConfig,
    import_finite_countermodel_results,
)
from mathgraph.finite_countermodel_executor import (
    FiniteCountermodelConfig,
    run_finite_countermodel_tasks,
)
from mathgraph.hashing import content_id
from mathgraph.kernel_oracle import KernelOracle
from mathgraph.lawbook_store import LawbookStore
from mathgraph.terminal_contract import ProvenanceType, TerminalForm, TrustLevel, VerifierBoundary


VERIFY_WARNINGS = [
    "Scheduler/advisory scores are search pressure only, never truth.",
    "Finite search failure is not proof.",
    "Only verified proof traces or revalidated finite countermodels are terminal certificates.",
]


@dataclass(frozen=True)
class VerifyRequest:
    source: str
    target: str
    source_idx: int | None = None
    target_idx: int | None = None
    domain: str = "magma_equation"
    allow_construction: bool = True
    max_countermodel_order: int = 3

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "source_idx": self.source_idx,
            "target_idx": self.target_idx,
            "domain": self.domain,
            "allow_construction": self.allow_construction,
            "max_countermodel_order": self.max_countermodel_order,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VerifyRequest":
        return cls(
            source=str(data["source"]),
            target=str(data["target"]),
            source_idx=_optional_int(data.get("source_idx")),
            target_idx=_optional_int(data.get("target_idx")),
            domain=str(data.get("domain", "magma_equation")),
            allow_construction=bool(data.get("allow_construction", True)),
            max_countermodel_order=int(data.get("max_countermodel_order", 3)),
        )


@dataclass(frozen=True)
class VerifyConfig:
    store_path: str | None = None
    working_dir: str | None = None
    random_tables_per_order: int = 0
    exhaustive_order_limit: int = 3

    def to_dict(self) -> dict[str, Any]:
        return {
            "store_path": self.store_path,
            "working_dir": self.working_dir,
            "random_tables_per_order": self.random_tables_per_order,
            "exhaustive_order_limit": self.exhaustive_order_limit,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VerifyConfig":
        return cls(
            store_path=data.get("store_path"),
            working_dir=data.get("working_dir"),
            random_tables_per_order=int(data.get("random_tables_per_order", 0)),
            exhaustive_order_limit=int(data.get("exhaustive_order_limit", 3)),
        )


@dataclass(frozen=True)
class VerifyResult:
    status: str
    terminal_form: str
    trust_level: str
    source: str
    target: str
    claim: str
    certificate_id: str | None
    route: str | None
    explanation: str
    provenance_type: str = ProvenanceType.SYSTEM
    verifier_boundary: str = VerifierBoundary.NOT_VERIFIED
    certificate_chain: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    trace: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "terminal_form": self.terminal_form,
            "trust_level": self.trust_level,
            "provenance_type": self.provenance_type,
            "verifier_boundary": self.verifier_boundary,
            "certificate_chain": list(self.certificate_chain),
            "source": self.source,
            "target": self.target,
            "claim": self.claim,
            "certificate_id": self.certificate_id,
            "route": self.route,
            "explanation": self.explanation,
            "evidence": dict(self.evidence),
            "warnings": list(self.warnings),
            "trace": self.trace,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VerifyResult":
        return cls(
            status=str(data["status"]),
            terminal_form=str(data["terminal_form"]),
            trust_level=str(data["trust_level"]),
            provenance_type=str(data.get("provenance_type", ProvenanceType.SYSTEM)),
            verifier_boundary=str(data.get("verifier_boundary", VerifierBoundary.NOT_VERIFIED)),
            certificate_chain=[str(item) for item in data.get("certificate_chain", [])],
            source=str(data.get("source", "")),
            target=str(data.get("target", "")),
            claim=str(data.get("claim", "")),
            certificate_id=data.get("certificate_id"),
            route=data.get("route"),
            explanation=str(data.get("explanation", "")),
            evidence=dict(data.get("evidence", {})),
            warnings=[str(item) for item in data.get("warnings", [])],
            trace=data.get("trace"),
        )


class MathGraphVerifier:
    def __init__(self, config: VerifyConfig | dict[str, Any] | None = None) -> None:
        self.config = config if isinstance(config, VerifyConfig) else VerifyConfig.from_dict(config or {})

    def verify(self, request: VerifyRequest | dict[str, Any]) -> VerifyResult:
        request = request if isinstance(request, VerifyRequest) else VerifyRequest.from_dict(request)
        claim = _claim(request.source, request.target)
        try:
            oracle_result = self._oracle_lookup(request)
            if oracle_result is not None and oracle_result.status in {"VERIFIED", "REFUTED"}:
                return _from_oracle(request, oracle_result)
            if not request.allow_construction:
                return _safe_unknown(
                    request,
                    status="UNKNOWN",
                    explanation="No exact verified lawbook trace found and construction is disabled.",
                    evidence={"oracle": oracle_result.to_dict() if oracle_result else None},
                )
            if request.domain != "magma_equation":
                return _safe_unknown(
                    request,
                    status="OBSTRUCTED",
                    explanation=f"Unsupported verification domain: {request.domain}",
                    evidence={"domain": request.domain},
                )
            return self._construct_finite_countermodel(request)
        except Exception as exc:
            return VerifyResult(
                status="ERROR",
                terminal_form=TerminalForm.NONE,
                trust_level=TrustLevel.ERROR,
                source=request.source,
                target=request.target,
                claim=claim,
                certificate_id=None,
                route=None,
                explanation=str(exc),
                provenance_type=ProvenanceType.SYSTEM,
                verifier_boundary=VerifierBoundary.ERROR,
                evidence={"error_type": type(exc).__name__},
                warnings=list(VERIFY_WARNINGS),
                trace=None,
            )

    def _oracle_lookup(self, request: VerifyRequest):
        if not self.config.store_path:
            return None
        store = LawbookStore(self.config.store_path)
        try:
            store.init_schema()
            return KernelOracle(store).query(request.source, request.target)
        finally:
            store.close()

    def _construct_finite_countermodel(self, request: VerifyRequest) -> VerifyResult:
        working_root = Path(self.config.working_dir) if self.config.working_dir else None
        with tempfile.TemporaryDirectory(dir=str(working_root) if working_root else None) as tmp:
            tmp_path = Path(tmp)
            queue = tmp_path / "queue.jsonl"
            results = tmp_path / "finite_results.jsonl"
            store_path = tmp_path / "verify_store.sqlite"
            _write_jsonl([_queue_task(request)], queue)
            run = run_finite_countermodel_tasks(
                FiniteCountermodelConfig(
                    task_queue_jsonl=str(queue),
                    out_jsonl=str(results),
                    max_tasks=1,
                    max_order=request.max_countermodel_order,
                    random_tables_per_order=self.config.random_tables_per_order,
                    exhaustive_order_limit=min(
                        request.max_countermodel_order,
                        self.config.exhaustive_order_limit,
                    ),
                    include_deterministic_tables=True,
                    stop_after_first=True,
                )
            )
            found = [row for row in run.results if row.get("status") == "finite_countermodel_found"]
            if not found:
                return _safe_unknown(
                    request,
                    status="UNKNOWN",
                    explanation="No finite countermodel found within the configured bounded search.",
                    evidence={"finite_executor": run.summary},
                )
            imported = import_finite_countermodel_results(
                CountermodelImportConfig(
                    results_jsonl=str(results),
                    store_path=str(store_path),
                    revalidate=True,
                )
            )
            imported_rows = [row.to_dict() for row in imported.results if row.imported]
            if not imported_rows:
                return _safe_unknown(
                    request,
                    status="OBSTRUCTED",
                    explanation="A finite countermodel candidate was found but did not pass importer revalidation.",
                    evidence={
                        "finite_executor": run.summary,
                        "importer": imported.summary,
                        "import_results": [row.to_dict() for row in imported.results],
                    },
                )
            row = imported_rows[0]
            return VerifyResult(
                status="REFUTED",
                terminal_form=TerminalForm.REFUTATION_CERTIFICATE,
                trust_level=TrustLevel.FINITE_VERIFIED,
                source=request.source,
                target=request.target,
                claim=_claim(request.source, request.target),
                certificate_id=row.get("certificate_id"),
                route="finite_countermodel",
                explanation="A finite magma countermodel was found and revalidated for this exact source/target claim.",
                provenance_type=ProvenanceType.PRIMITIVE,
                verifier_boundary=VerifierBoundary.IMPORTER_REVALIDATED,
                certificate_chain=[row.get("certificate_id")] if row.get("certificate_id") else [],
                evidence={
                    "finite_executor": run.summary,
                    "importer": imported.summary,
                    "countermodel_result": found[0],
                    "import_result": row,
                },
                warnings=list(VERIFY_WARNINGS),
                trace=None,
            )


def _from_oracle(request: VerifyRequest, answer: Any) -> VerifyResult:
    trust = TrustLevel.FINITE_VERIFIED if answer.terminal_form == "FINITE_COUNTERMODEL" else TrustLevel.LEAN_VERIFIED
    terminal = TerminalForm.REFUTATION_CERTIFICATE if answer.terminal_form == "FINITE_COUNTERMODEL" else answer.terminal_form
    boundary = VerifierBoundary.IMPORTER_REVALIDATED if answer.terminal_form == "FINITE_COUNTERMODEL" else VerifierBoundary.LEAN_TYPECHECKED
    provenance = ProvenanceType.PRIMITIVE
    if answer.trust_level == "derived_from_verified_traces":
        trust = TrustLevel.DERIVED_CHAIN_VERIFIED
        boundary = VerifierBoundary.CHAIN_AUDITED
        provenance = ProvenanceType.DERIVED
    return VerifyResult(
        status=answer.status,
        terminal_form=terminal,
        trust_level=trust,
        source=request.source,
        target=request.target,
        claim=answer.claim or _claim(request.source, request.target),
        certificate_id=answer.certificate_id,
        route=answer.route,
        explanation=answer.explanation,
        provenance_type=provenance,
        verifier_boundary=boundary,
        certificate_chain=[answer.certificate_id] if answer.certificate_id else [],
        evidence=answer.evidence,
        warnings=[*list(answer.warnings), *VERIFY_WARNINGS],
        trace=None,
    )


def _safe_unknown(
    request: VerifyRequest,
    *,
    status: str,
    explanation: str,
    evidence: dict[str, Any],
) -> VerifyResult:
    return VerifyResult(
        status=status,
        terminal_form=TerminalForm.NAMED_OBSTRUCTION,
        trust_level=TrustLevel.ADVISORY_ROUTE,
        source=request.source,
        target=request.target,
        claim=_claim(request.source, request.target),
        certificate_id=None,
        route=None,
        explanation=explanation,
        provenance_type=ProvenanceType.SYSTEM,
        verifier_boundary=VerifierBoundary.NOT_VERIFIED,
        certificate_chain=[],
        evidence=evidence,
        warnings=list(VERIFY_WARNINGS),
        trace=None,
    )


def _queue_task(request: VerifyRequest) -> dict[str, Any]:
    return {
        "task_id": content_id("verify_task", request.to_dict()),
        "source": request.source,
        "target": request.target,
        "source_idx": request.source_idx,
        "target_idx": request.target_idx,
        "route": "finite_countermodel",
        "task_kind": "finite_countermodel_search",
        "terminal_goal": "FINITE_COUNTERMODEL",
        "priority": 1.0,
        "schedule_rank": 1,
        "candidate_origin": "verify_api",
        "label": "verify_api_direct_countermodel_check",
        "warnings": list(VERIFY_WARNINGS),
    }


def _write_jsonl(rows: list[dict[str, Any]], path: Path) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def _claim(source: str, target: str) -> str:
    return f"{source} => {target}"


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
