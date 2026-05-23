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

from mathgraph.lawbook_accumulator import connect_lawbook, json_loads


class ReasonAtlasTrustLevel(str, Enum):
    ADVISORY = "ADVISORY"
    VERIFIER_BACKED = "VERIFIER_BACKED"
    RETIRED = "RETIRED"


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
    known_limits: tuple[str, ...] = ()
    promotion_status: str = "ADVISORY_ROUTING_KNOWLEDGE"

    def __post_init__(self) -> None:
        if not isinstance(self.trust_level, ReasonAtlasTrustLevel):
            object.__setattr__(self, "trust_level", ReasonAtlasTrustLevel(str(self.trust_level)))

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
            "known_limits": list(self.known_limits),
            "promotion_status": self.promotion_status,
            "advisory_only": self.trust_level != ReasonAtlasTrustLevel.VERIFIER_BACKED,
            "truth_status": "not_truth",
        }


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
