"""Advisory oracle for root, reason, and obstruction atlases."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mathgraph.obstruction_atlas import ObstructionNode
from mathgraph.reason_nodes import ReasonNode
from mathgraph.root_nodes import RootNode


class RootNodeOracle:
    """Query-only atlas memory. It never verifies or refutes claims."""

    def __init__(
        self,
        roots: list[RootNode] | None = None,
        reasons: list[ReasonNode] | None = None,
        obstructions: list[ObstructionNode] | None = None,
        reason_links: list[dict[str, Any]] | None = None,
        obstruction_links: list[dict[str, Any]] | None = None,
    ) -> None:
        self.roots = list(roots or [])
        self.reasons = list(reasons or [])
        self.obstructions = list(obstructions or [])
        self.reason_links = list(reason_links or [])
        self.obstruction_links = list(obstruction_links or [])
        self._root_by_id = {root.root_node_id: root for root in self.roots}

    @classmethod
    def from_json_dir(cls, path: str | Path) -> "RootNodeOracle":
        directory = Path(path)
        roots = _load_nodes(directory / "canonical_root_nodes.json", RootNode)
        if not roots:
            roots = _load_nodes(directory / "root_nodes.json", RootNode)
        reasons = _load_nodes(directory / "reason_nodes.json", ReasonNode)
        obstructions = _load_nodes(directory / "obstructions.json", ObstructionNode)
        reason_links = _load_dicts(directory / "root_reason_links.json")
        obstruction_links = _load_dicts(directory / "root_obstruction_links.json")
        return cls(roots, reasons, obstructions, reason_links, obstruction_links)

    def summary(self) -> dict[str, Any]:
        return {
            "root_count": len(self.roots),
            "reason_count": len(self.reasons),
            "obstruction_count": len(self.obstructions),
            "advisory_only": True,
        }

    def top_roots(self, n: int = 20) -> list[dict[str, Any]]:
        return [root.to_dict() for root in sorted(self.roots, key=_root_score, reverse=True)[:n]]

    def top_reasons(self, n: int = 20) -> list[dict[str, Any]]:
        return [
            reason.to_dict()
            for reason in sorted(self.reasons, key=lambda item: item.reason_score, reverse=True)[:n]
        ]

    def top_obstructions(self, n: int = 20) -> list[dict[str, Any]]:
        return [
            obstruction.to_dict()
            for obstruction in sorted(
                self.obstructions,
                key=lambda item: item.obstruction_pressure_score,
                reverse=True,
            )[:n]
        ]

    def get_root(self, root_node_id: str) -> dict[str, Any] | None:
        root = self._root_by_id.get(root_node_id)
        if root is None:
            for candidate in self.roots:
                if candidate.canonical_name == root_node_id:
                    root = candidate
                    break
        return root.to_dict() if root else None

    def explain_root(self, root_node_id: str) -> dict[str, Any]:
        root = self.get_root(root_node_id)
        if root is None:
            return {
                "status": "missing",
                "root_node_id": root_node_id,
                "advisory_only": True,
                "explanation": "No root node found.",
            }
        reasons = self.reasons_for_root(root["root_node_id"])
        obstructions = self.obstructions_for_root(root["root_node_id"])
        return {
            "status": "hit",
            "advisory_only": True,
            "root": root,
            "reasons": reasons,
            "obstructions": obstructions,
            "explanation": (
                f"{root['canonical_name']} is an advisory root supported by "
                f"{root.get('unique_pairs', 0)} certificate pairs, "
                f"{root.get('unique_tables', 0)} tables, and "
                f"{root.get('unique_motifs', 0)} motifs. It suggests constructor "
                "pressure but does not prove or refute any unknown claim."
            ),
            "constructor_next": _constructor_hint(root, obstructions),
        }

    def find_roots_by_motif(self, motif: str) -> list[dict[str, Any]]:
        needle = str(motif).lower()
        return [root.to_dict() for root in self.roots if needle in root.table_motif.lower()]

    def find_roots_by_basin_transition(
        self, source_basin: str, target_basin: str
    ) -> list[dict[str, Any]]:
        source = str(source_basin).lower()
        target = str(target_basin).lower()
        return [
            root.to_dict()
            for root in self.roots
            if source in root.source_target_basin.lower()
            and target in root.source_target_basin.lower()
        ]

    def reasons_for_root(self, root_node_id: str) -> list[dict[str, Any]]:
        linked_ids = {
            str(link.get("reason_node_id"))
            for link in self.reason_links
            if link.get("root_node_id") == root_node_id
        }
        if linked_ids:
            return [reason.to_dict() for reason in self.reasons if reason.reason_node_id in linked_ids]
        root = self._root_by_id.get(root_node_id)
        if root is None:
            return []
        return [
            reason.to_dict()
            for reason in self.reasons
            if reason.table_motif and reason.table_motif == root.table_motif
        ]

    def obstructions_for_root(self, root_node_id: str) -> list[dict[str, Any]]:
        linked_ids = {
            str(link.get("obstruction_id"))
            for link in self.obstruction_links
            if link.get("root_node_id") == root_node_id
        }
        if linked_ids:
            return [
                obstruction.to_dict()
                for obstruction in self.obstructions
                if obstruction.obstruction_id in linked_ids
            ]
        root = self._root_by_id.get(root_node_id)
        if root is None:
            return []
        return [
            obstruction.to_dict()
            for obstruction in self.obstructions
            if obstruction.table_motif and obstruction.table_motif == root.table_motif
        ]


def _load_nodes(path: Path, cls: Any) -> list[Any]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("rows", data.get("items", []))
    return [cls.from_dict(row) for row in data if isinstance(row, dict)]


def _load_dicts(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [dict(row) for row in data if isinstance(row, dict)]


def _root_score(root: RootNode) -> float:
    return float(root.evidence.get("canonical_root_score", root.load_bearing_score))


def _constructor_hint(root: dict[str, Any], obstructions: list[dict[str, Any]]) -> str:
    if obstructions:
        return "Split residual basin or build source-preserving countermodel constructor."
    motif = str(root.get("table_motif", "")).lower()
    if "projection" in motif:
        return "Try projection-family finite countermodel constructors."
    if "add" in motif or "parity" in motif:
        return "Try modular/parity finite countermodel constructors."
    return "Use root pressure as advisory constructor routing only."
