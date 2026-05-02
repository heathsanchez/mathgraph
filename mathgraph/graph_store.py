"""Small in-memory semantic hypergraph store."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Node:
    node_id: str
    kind: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class Edge:
    edge_id: str
    kind: str
    source: str
    target: str
    payload: dict[str, Any] = field(default_factory=dict)


class InMemoryGraphStore:
    """Append-friendly store for early kernel experiments."""

    def __init__(self) -> None:
        self.nodes: dict[str, Node] = {}
        self.edges: dict[str, Edge] = {}

    def add_node(self, node_id: str, kind: str, **payload: Any) -> Node:
        node = Node(node_id=node_id, kind=kind, payload=dict(payload))
        self.nodes[node_id] = node
        return node

    def add_edge(self, edge_id: str, kind: str, source: str, target: str, **payload: Any) -> Edge:
        if source not in self.nodes or target not in self.nodes:
            raise KeyError("edge endpoints must already exist")
        edge = Edge(edge_id=edge_id, kind=kind, source=source, target=target, payload=dict(payload))
        self.edges[edge_id] = edge
        return edge

    def get_node(self, node_id: str) -> Node:
        return self.nodes[node_id]

    def list_nodes(self, kind: str | None = None) -> list[Node]:
        if kind is None:
            return list(self.nodes.values())
        return [node for node in self.nodes.values() if node.kind == kind]

    def query_nodes(self, kind: str | None = None, **payload_filters: Any) -> list[Node]:
        nodes = self.list_nodes(kind)
        return [
            node
            for node in nodes
            if all(node.payload.get(key) == value for key, value in payload_filters.items())
        ]

    def to_dict(self) -> dict[str, list[dict[str, Any]]]:
        return {
            "nodes": [
                {"node_id": node.node_id, "kind": node.kind, "payload": node.payload}
                for node in self.nodes.values()
            ],
            "edges": [
                {
                    "edge_id": edge.edge_id,
                    "kind": edge.kind,
                    "source": edge.source,
                    "target": edge.target,
                    "payload": edge.payload,
                }
                for edge in self.edges.values()
            ],
        }
