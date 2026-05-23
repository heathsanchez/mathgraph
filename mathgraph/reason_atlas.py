"""Reason Atlas export for persistent Mathlib digest Lawbooks."""

from __future__ import annotations

import csv
import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping

from mathgraph.certificates import TerminalForm
from mathgraph.lawbook_accumulator import connect_lawbook, json_loads
from mathgraph.semantic_validation import SemanticValidationStatus


class ReasonAtlasTrustLevel(str, Enum):
    ADVISORY = "ADVISORY"
    VERIFIER_BACKED = "VERIFIER_BACKED"
    RETIRED = "RETIRED"


class ReasonAtlasPromotionStatus(str, Enum):
    EXPLORATORY = "EXPLORATORY"
    ADVISORY_ROUTING_KNOWLEDGE = "ADVISORY_ROUTING_KNOWLEDGE"
    VERIFIER_BACKED_ROUTING = "VERIFIER_BACKED_ROUTING"
    RETIRED = "RETIRED"


@dataclass(frozen=True)
class ReasonAtlasViolation:
    code: str
    message: str
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code, "message": self.message, "context": dict(self.context)}


@dataclass(frozen=True)
class ReasonAtlasEvidenceRef:
    evidence_id: str
    claim_id: str = ""
    terminal_form: str = ""
    manifest_path: str = ""
    manifest_hash: str = ""
    lawbook_entry_id: str = ""
    verifier_backed: bool = False
    advisory_only: bool = True
    replay_status: str = ""
    semantic_validation_status: str = SemanticValidationStatus.MISSING.value
    outcome: str = "unknown"

    def __post_init__(self) -> None:
        if self.terminal_form:
            TerminalForm(str(self.terminal_form))
        if self.semantic_validation_status:
            SemanticValidationStatus(str(self.semantic_validation_status))
        if self.verifier_backed and self.advisory_only:
            object.__setattr__(self, "advisory_only", False)

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class ReasonAtlasMetricReport:
    support_count: int = 0
    verifier_backed_count: int = 0
    advisory_only_count: int = 0
    success_count_by_terminal_form: dict[str, int] = field(default_factory=dict)
    failure_count: int = 0
    replayable_count: int = 0
    heldout_gain: float = 0.0
    new_losses: int = 0
    known_limits: tuple[str, ...] = ()
    evidence_coverage_ratio: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "support_count": self.support_count,
            "verifier_backed_count": self.verifier_backed_count,
            "advisory_only_count": self.advisory_only_count,
            "success_count_by_terminal_form": dict(self.success_count_by_terminal_form),
            "failure_count": self.failure_count,
            "replayable_count": self.replayable_count,
            "heldout_gain": self.heldout_gain,
            "new_losses": self.new_losses,
            "known_limits": list(self.known_limits),
            "evidence_coverage_ratio": self.evidence_coverage_ratio,
        }


@dataclass(frozen=True)
class ReasonAtlasValidationReport:
    ok: bool
    advisory_only: bool = True
    violations: tuple[ReasonAtlasViolation, ...] = ()
    metrics: ReasonAtlasMetricReport = field(default_factory=ReasonAtlasMetricReport)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "advisory_only": self.advisory_only,
            "violations": [v.to_dict() for v in self.violations],
            "metrics": self.metrics.to_dict(),
        }


@dataclass(frozen=True)
class ReasonBasin:
    basin_id: str
    signature: str
    basin_name: str
    known_limits: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class ConstructorFamily:
    family_id: str
    family_name: str
    operators: tuple[str, ...] = ()
    known_limits: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class RoutePolicy:
    policy_id: str
    policy_name: str
    route_priority: float = 0.0
    advisory_only: bool = True

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class ResidualSignature:
    signature_id: str
    signature: str
    residual_count: int = 0
    known_limits: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class VerificationOutcome:
    outcome_id: str
    terminal_form: str
    verifier_backed: bool
    evidence_ref: str
    residual_delta: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class RoutePolicyEvidence:
    evidence_id: str
    support_count: int = 0
    heldout_gain: float = 0.0
    new_losses: int = 0
    true_control_countermodels: int = 0
    evidence_refs: tuple[str, ...] = ()
    verifier_backed_outcomes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class ReasonAtlasEntry:
    basin_id: str
    signature: str
    basin_name: str
    constructor_family: str
    route_priority: float
    support_count: int
    heldout_gain: float
    new_losses: int
    true_control_countermodels: int
    trust_level: ReasonAtlasTrustLevel = ReasonAtlasTrustLevel.ADVISORY
    evidence_refs: tuple[str, ...] = ()
    evidence: tuple[ReasonAtlasEvidenceRef, ...] = ()
    known_limits: tuple[str, ...] = ()
    promotion_status: str = ReasonAtlasPromotionStatus.ADVISORY_ROUTING_KNOWLEDGE.value
    verifier_backed_count: int = 0
    advisory_only_count: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.trust_level, ReasonAtlasTrustLevel):
            object.__setattr__(self, "trust_level", ReasonAtlasTrustLevel(str(self.trust_level)))
        object.__setattr__(self, "promotion_status", ReasonAtlasPromotionStatus(str(self.promotion_status)).value)
        object.__setattr__(
            self,
            "evidence",
            tuple(ev if isinstance(ev, ReasonAtlasEvidenceRef) else ReasonAtlasEvidenceRef(**dict(ev)) for ev in self.evidence),
        )

    @property
    def is_truth_claim(self) -> bool:
        return False

    def to_dict(self) -> dict[str, Any]:
        return {
            "basin_id": self.basin_id,
            "signature": self.signature,
            "basin_name": self.basin_name,
            "constructor_family": self.constructor_family,
            "route_priority": self.route_priority,
            "support_count": self.support_count,
            "heldout_gain": self.heldout_gain,
            "new_losses": self.new_losses,
            "true_control_countermodels": self.true_control_countermodels,
            "trust_level": self.trust_level.value,
            "evidence_refs": list(self.evidence_refs),
            "evidence": [ev.to_dict() for ev in self.evidence],
            "known_limits": list(self.known_limits),
            "promotion_status": self.promotion_status,
            "verifier_backed_count": self.verifier_backed_count,
            "advisory_only_count": self.advisory_only_count,
            "advisory_only": True,
            "truth_status": "not_truth",
        }


def validate_reason_atlas_entry(entry: ReasonAtlasEntry | Mapping[str, Any]) -> ReasonAtlasValidationReport:
    entry_obj = entry if isinstance(entry, ReasonAtlasEntry) else _entry_from_mapping(entry)
    violations: list[ReasonAtlasViolation] = []
    metrics = compute_reason_atlas_metrics(entry_obj.evidence, heldout_gain=entry_obj.heldout_gain, new_losses=entry_obj.new_losses, known_limits=entry_obj.known_limits)
    violations.extend(check_reason_atlas_advisory_only(entry_obj).violations)
    violations.extend(check_reason_atlas_no_truth_promotion(entry_obj).violations)
    violations.extend(check_reason_atlas_evidence_refs(entry_obj).violations)
    if entry_obj.trust_level == ReasonAtlasTrustLevel.VERIFIER_BACKED and metrics.verifier_backed_count == 0:
        violations.append(ReasonAtlasViolation("verifier_backed_without_evidence", "Verifier-backed Reason Atlas routing requires verifier-backed evidence refs."))
    return ReasonAtlasValidationReport(ok=not violations, advisory_only=True, violations=tuple(violations), metrics=metrics)


def check_reason_atlas_advisory_only(entry: ReasonAtlasEntry | Mapping[str, Any]) -> ReasonAtlasValidationReport:
    data = entry.to_dict() if isinstance(entry, ReasonAtlasEntry) else dict(entry)
    violations: list[ReasonAtlasViolation] = []
    if data.get("advisory_only") is False:
        violations.append(ReasonAtlasViolation("reason_atlas_not_advisory", "Reason Atlas entries must remain advisory routing knowledge."))
    return ReasonAtlasValidationReport(ok=not violations, violations=tuple(violations))


def check_reason_atlas_no_truth_promotion(entry: ReasonAtlasEntry | Mapping[str, Any]) -> ReasonAtlasValidationReport:
    data = entry.to_dict() if isinstance(entry, ReasonAtlasEntry) else dict(entry)
    violations: list[ReasonAtlasViolation] = []
    terminal = data.get("terminal_form") or data.get("truth_terminal_form")
    if terminal in {form.value for form in TerminalForm}:
        violations.append(ReasonAtlasViolation("reason_atlas_truth_promotion", "Reason Atlas entries cannot create terminal forms."))
    if data.get("claims_truth") or data.get("lawbook_acceptance") == "ACCEPTED":
        violations.append(ReasonAtlasViolation("reason_atlas_lawbook_bypass", "Route priority cannot bypass Lawbook acceptance."))
    return ReasonAtlasValidationReport(ok=not violations, violations=tuple(violations))


def check_reason_atlas_evidence_refs(entry: ReasonAtlasEntry | Mapping[str, Any]) -> ReasonAtlasValidationReport:
    entry_obj = entry if isinstance(entry, ReasonAtlasEntry) else _entry_from_mapping(entry)
    violations: list[ReasonAtlasViolation] = []
    for ev in entry_obj.evidence:
        if not ev.evidence_id:
            violations.append(ReasonAtlasViolation("missing_evidence_id", "Reason Atlas evidence refs require evidence_id."))
        if ev.verifier_backed and not (ev.manifest_hash or ev.manifest_path or ev.lawbook_entry_id):
            violations.append(ReasonAtlasViolation("verifier_backed_ref_missing_manifest_or_lawbook", "Verifier-backed refs require manifest or Lawbook linkage."))
        if ev.terminal_form and ev.terminal_form not in {form.value for form in TerminalForm}:
            violations.append(ReasonAtlasViolation("invalid_terminal_form_ref", "Evidence ref terminal_form is not a known terminal form."))
    if entry_obj.trust_level == ReasonAtlasTrustLevel.VERIFIER_BACKED and not entry_obj.evidence:
        violations.append(ReasonAtlasViolation("missing_verifier_backed_evidence_refs", "Verifier-backed Reason Atlas entries require evidence refs."))
    return ReasonAtlasValidationReport(ok=not violations, violations=tuple(violations))


def compute_reason_atlas_metrics(
    outcomes: tuple[ReasonAtlasEvidenceRef, ...] | list[ReasonAtlasEvidenceRef | Mapping[str, Any]],
    *,
    heldout_gain: float = 0.0,
    new_losses: int = 0,
    known_limits: tuple[str, ...] = (),
) -> ReasonAtlasMetricReport:
    refs = tuple(ev if isinstance(ev, ReasonAtlasEvidenceRef) else ReasonAtlasEvidenceRef(**dict(ev)) for ev in outcomes)
    terminal_counts = Counter(ev.terminal_form for ev in refs if ev.verifier_backed and ev.terminal_form)
    failure_count = sum(1 for ev in refs if str(ev.outcome).lower() in {"failure", "rejected", "failed"})
    replayable_count = sum(1 for ev in refs if str(ev.replay_status).lower() in {"replayable", "pass", "passed"})
    support = len(refs)
    covered = sum(1 for ev in refs if ev.evidence_id)
    return ReasonAtlasMetricReport(
        support_count=support,
        verifier_backed_count=sum(1 for ev in refs if ev.verifier_backed),
        advisory_only_count=sum(1 for ev in refs if ev.advisory_only),
        success_count_by_terminal_form=dict(terminal_counts),
        failure_count=failure_count,
        replayable_count=replayable_count,
        heldout_gain=float(heldout_gain),
        new_losses=int(new_losses),
        known_limits=tuple(known_limits),
        evidence_coverage_ratio=(covered / support) if support else 0.0,
    )


def build_reason_atlas_entry_from_outcomes(
    *,
    basin_id: str,
    signature: str,
    basin_name: str,
    constructor_family: str,
    outcomes: list[ReasonAtlasEvidenceRef | Mapping[str, Any]],
    route_priority: float = 0.0,
    heldout_gain: float = 0.0,
    new_losses: int = 0,
    known_limits: tuple[str, ...] = (),
) -> ReasonAtlasEntry:
    refs = tuple(ev if isinstance(ev, ReasonAtlasEvidenceRef) else ReasonAtlasEvidenceRef(**dict(ev)) for ev in outcomes)
    metrics = compute_reason_atlas_metrics(refs, heldout_gain=heldout_gain, new_losses=new_losses, known_limits=known_limits)
    trust = ReasonAtlasTrustLevel.VERIFIER_BACKED if metrics.verifier_backed_count else ReasonAtlasTrustLevel.ADVISORY
    status = ReasonAtlasPromotionStatus.VERIFIER_BACKED_ROUTING if metrics.verifier_backed_count else ReasonAtlasPromotionStatus.EXPLORATORY
    return ReasonAtlasEntry(
        basin_id=basin_id,
        signature=signature,
        basin_name=basin_name,
        constructor_family=constructor_family,
        route_priority=float(route_priority),
        support_count=metrics.support_count,
        heldout_gain=float(heldout_gain),
        new_losses=int(new_losses),
        true_control_countermodels=metrics.success_count_by_terminal_form.get(TerminalForm.FINITE_COUNTERMODEL.value, 0),
        trust_level=trust,
        evidence_refs=tuple(ev.evidence_id for ev in refs),
        evidence=refs,
        known_limits=tuple(known_limits),
        promotion_status=status.value,
        verifier_backed_count=metrics.verifier_backed_count,
        advisory_only_count=metrics.advisory_only_count,
    )


def summarize_constructor_family_performance(entries: list[ReasonAtlasEntry | Mapping[str, Any]]) -> dict[str, Any]:
    summary: dict[str, dict[str, Any]] = {}
    for item in entries:
        entry = item if isinstance(item, ReasonAtlasEntry) else _entry_from_mapping(item)
        metrics = compute_reason_atlas_metrics(entry.evidence, heldout_gain=entry.heldout_gain, new_losses=entry.new_losses, known_limits=entry.known_limits)
        row = summary.setdefault(entry.constructor_family, {"support_count": 0, "verifier_backed_count": 0, "advisory_only_count": 0, "failure_count": 0, "heldout_gain": 0.0})
        row["support_count"] += metrics.support_count
        row["verifier_backed_count"] += metrics.verifier_backed_count
        row["advisory_only_count"] += metrics.advisory_only_count
        row["failure_count"] += metrics.failure_count
        row["heldout_gain"] += metrics.heldout_gain
    return summary


def reason_atlas_report(entry: ReasonAtlasEntry | Mapping[str, Any]) -> dict[str, Any]:
    entry_obj = entry if isinstance(entry, ReasonAtlasEntry) else _entry_from_mapping(entry)
    validation = validate_reason_atlas_entry(entry_obj)
    return {"entry": entry_obj.to_dict(), "validation": validation.to_dict()}


def _entry_from_mapping(data: Mapping[str, Any]) -> ReasonAtlasEntry:
    return ReasonAtlasEntry(
        basin_id=str(data.get("basin_id", "")),
        signature=str(data.get("signature", "")),
        basin_name=str(data.get("basin_name", "")),
        constructor_family=str(data.get("constructor_family", "")),
        route_priority=float(data.get("route_priority", 0.0) or 0.0),
        support_count=int(data.get("support_count", 0) or 0),
        heldout_gain=float(data.get("heldout_gain", 0.0) or 0.0),
        new_losses=int(data.get("new_losses", 0) or 0),
        true_control_countermodels=int(data.get("true_control_countermodels", 0) or 0),
        trust_level=ReasonAtlasTrustLevel(str(data.get("trust_level", ReasonAtlasTrustLevel.ADVISORY.value))),
        evidence_refs=tuple(str(x) for x in data.get("evidence_refs", ()) or ()),
        evidence=tuple(ReasonAtlasEvidenceRef(**dict(x)) for x in data.get("evidence", ()) or ()),
        known_limits=tuple(str(x) for x in data.get("known_limits", ()) or ()),
        promotion_status=str(data.get("promotion_status", ReasonAtlasPromotionStatus.ADVISORY_ROUTING_KNOWLEDGE.value)),
        verifier_backed_count=int(data.get("verifier_backed_count", 0) or 0),
        advisory_only_count=int(data.get("advisory_only_count", 0) or 0),
    )


def build_reason_atlas(conn: sqlite3.Connection) -> dict[str, Any]:
    reasons = [dict(r) for r in conn.execute("SELECT * FROM reason_basins ORDER BY reason_id")]
    roots_by_reason: dict[str, set[str]] = defaultdict(set)
    edges = [dict(r) for r in conn.execute("SELECT * FROM target_reason_edges")]
    target_to_reason = {row["target_id"]: row["reason_id"] for row in edges}
    for row in conn.execute("SELECT target_id, root_name FROM root_observations"):
        rid = target_to_reason.get(row["target_id"])
        if rid:
            roots_by_reason[rid].add(row["root_name"])
    verified_by_reason = Counter(row["reason_id"] for row in conn.execute("SELECT reason_id FROM verified_constructors"))
    attempts_by_reason = Counter(row["reason_id"] for row in conn.execute("SELECT reason_id FROM constructor_attempts"))
    obstructions_by_reason: dict[str, Counter[str]] = defaultdict(Counter)
    for row in conn.execute("SELECT reason_id, obstruction_class FROM obstructions"):
        obstructions_by_reason[row["reason_id"]][row["obstruction_class"]] += 1
    records = []
    root_rows = []
    for reason in reasons:
        rid = reason["reason_id"]
        roots = sorted(set(json_loads(reason["root_nodes_json"], [])) | roots_by_reason[rid])
        for root in roots:
            root_rows.append({"reason_id": rid, "root_name": root})
        attempts = attempts_by_reason[rid]
        verified = verified_by_reason[rid]
        records.append(
            {
                "reason_id": rid,
                "reason_name": reason["reason_name"],
                "basin_class": reason["basin_class"],
                "support_count": reason["support_count"],
                "root_nodes": roots,
                "axiom_profile": json_loads(reason["axiom_profile_json"], {}),
                "verified_constructor_count": verified,
                "constructor_success_rate": (verified / attempts) if attempts else 0.0,
                "best_constructors": best_constructors(conn, rid),
                "obstruction_classes": dict(obstructions_by_reason[rid]),
                "trust_level": reason["trust_level"],
                "explanation": reason["explanation"],
            }
        )
    return {"reason_atlas": records, "root_atlas": root_rows, "target_reason_edges": edges}


def best_constructors(conn: sqlite3.Connection, reason_id: str) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in conn.execute(
            "SELECT template_id, proof_body, success_count, target_examples_json FROM verified_constructors WHERE reason_id=? ORDER BY success_count DESC, LENGTH(proof_body) ASC LIMIT 5",
            (reason_id,),
        )
    ]


def write_csv(path: str | Path, rows: list[Mapping[str, Any]], fieldnames: list[str]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow({k: json.dumps(v, sort_keys=True) if isinstance(v, (dict, list)) else v for k, v in row.items() if k in fieldnames})


def export_reason_atlas(lawbook: str | Path, out_dir: str | Path) -> dict[str, str]:
    conn = connect_lawbook(lawbook)
    atlas = build_reason_atlas(conn)
    conn.close()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": out / "reason_atlas.json",
        "csv": out / "reason_atlas.csv",
        "roots": out / "root_atlas.csv",
        "edges": out / "target_reason_edges.csv",
        "report": out / "reason_atlas_report.md",
    }
    paths["json"].write_text(json.dumps(atlas, indent=2, sort_keys=True, default=str), encoding="utf-8")
    write_csv(paths["csv"], atlas["reason_atlas"], ["reason_id", "reason_name", "basin_class", "support_count", "root_nodes", "axiom_profile", "verified_constructor_count", "constructor_success_rate", "best_constructors", "obstruction_classes", "trust_level", "explanation"])
    write_csv(paths["roots"], atlas["root_atlas"], ["reason_id", "root_name"])
    write_csv(paths["edges"], atlas["target_reason_edges"], ["edge_id", "target_id", "reason_id", "confidence", "evidence_json"])
    paths["report"].write_text(render_reason_report(atlas), encoding="utf-8")
    return {k: str(v) for k, v in paths.items()}


def render_reason_report(atlas: Mapping[str, Any]) -> str:
    lines = ["# Reason Atlas Report", "", f"- Reasons: {len(atlas['reason_atlas'])}", ""]
    for row in atlas["reason_atlas"]:
        lines.append(f"- `{row['reason_id']}`: support={row['support_count']} verified_constructors={row['verified_constructor_count']} trust={row['trust_level']}")
    return "\n".join(lines) + "\n"
