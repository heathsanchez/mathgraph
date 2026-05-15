"""Advisory structural identity and canonicalization for MathGraph artifacts."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from mathgraph.agent_biography import AgentExperience, AgentExperienceOutcome
from mathgraph.alchemy import AlchemicalPhase, AlchemicalStatus, AlchemicalTrace, make_alchemical_trace_id
from mathgraph.continuation_actions import (
    ContinuationActionOutput,
    ContinuationActionStatus,
    ContinuationOutputKind,
    make_continuation_output_id,
)
from mathgraph.continuation_curriculum import (
    ContinuationCurriculum,
    CurriculumBuildStrategy,
    CurriculumStage,
    CurriculumStageKind,
    CurriculumStageStatus,
    CurriculumTraceStatus,
    make_curriculum_id,
    make_curriculum_stage_id,
)
from mathgraph.hashing import content_id
from mathgraph.lawbook import LawbookEntry, LawbookEntryKind, LawbookEntryStatus, LawbookStore, make_lawbook_entry_id


class StructuralObjectKind(str, Enum):
    LAWBOOK_ENTRY = "LAWBOOK_ENTRY"
    LAWBOOK_STORE = "LAWBOOK_STORE"
    LAWBOOK_QUERY_ANSWER = "LAWBOOK_QUERY_ANSWER"
    LAWBOOK_QUERY_REPORT = "LAWBOOK_QUERY_REPORT"
    PROOF_DIGESTION_TRACE = "PROOF_DIGESTION_TRACE"
    LAWBOOK_ASSIMILATION_CANDIDATE = "LAWBOOK_ASSIMILATION_CANDIDATE"
    PROJECTION_CANDIDATE = "PROJECTION_CANDIDATE"
    DISCOVERY_VALUE_SCORE = "DISCOVERY_VALUE_SCORE"
    DISCOVERY_VALUE_REPORT = "DISCOVERY_VALUE_REPORT"
    CONTINUATION_CURRICULUM = "CONTINUATION_CURRICULUM"
    CURRICULUM_STAGE = "CURRICULUM_STAGE"
    VERIFIER_FEEDBACK = "VERIFIER_FEEDBACK"
    REPAIR_LOOP_TRACE = "REPAIR_LOOP_TRACE"
    ALCHEMICAL_TRACE = "ALCHEMICAL_TRACE"
    AGENT_EXPERIENCE = "AGENT_EXPERIENCE"
    RAW_GRAPH = "RAW_GRAPH"
    RAW_OBJECT = "RAW_OBJECT"
    UNKNOWN = "UNKNOWN"


class StructuralNodeKind(str, Enum):
    CLAIM = "CLAIM"
    SOURCE = "SOURCE"
    TARGET = "TARGET"
    CERTIFICATE = "CERTIFICATE"
    TERMINAL_FORM = "TERMINAL_FORM"
    ENTRY = "ENTRY"
    ARTIFACT = "ARTIFACT"
    TRACE = "TRACE"
    STAGE = "STAGE"
    TASK = "TASK"
    ROUTE = "ROUTE"
    PHASE = "PHASE"
    FEEDBACK = "FEEDBACK"
    REPAIR = "REPAIR"
    PROJECTION = "PROJECTION"
    DIGESTION = "DIGESTION"
    VALUE = "VALUE"
    AGENT = "AGENT"
    OBSTRUCTION = "OBSTRUCTION"
    CONDITION = "CONDITION"
    REASON = "REASON"
    ROOT = "ROOT"
    METADATA = "METADATA"
    UNKNOWN = "UNKNOWN"


class StructuralEdgeKind(str, Enum):
    HAS_SOURCE = "HAS_SOURCE"
    HAS_TARGET = "HAS_TARGET"
    HAS_CERTIFICATE = "HAS_CERTIFICATE"
    HAS_TERMINAL_FORM = "HAS_TERMINAL_FORM"
    HAS_ARTIFACT = "HAS_ARTIFACT"
    HAS_TRACE = "HAS_TRACE"
    HAS_STAGE = "HAS_STAGE"
    HAS_TASK = "HAS_TASK"
    HAS_ROUTE = "HAS_ROUTE"
    HAS_PHASE = "HAS_PHASE"
    HAS_FEEDBACK = "HAS_FEEDBACK"
    HAS_REPAIR = "HAS_REPAIR"
    HAS_PROJECTION = "HAS_PROJECTION"
    HAS_DIGESTION = "HAS_DIGESTION"
    HAS_VALUE = "HAS_VALUE"
    HAS_AGENT = "HAS_AGENT"
    HAS_OBSTRUCTION = "HAS_OBSTRUCTION"
    HAS_CONDITION = "HAS_CONDITION"
    HAS_REASON = "HAS_REASON"
    HAS_ROOT = "HAS_ROOT"
    DEPENDS_ON = "DEPENDS_ON"
    DERIVES_FROM = "DERIVES_FROM"
    ACCEPTED_BY = "ACCEPTED_BY"
    REVIEWED_BY = "REVIEWED_BY"
    PROJECTS_TO = "PROJECTS_TO"
    EXPLAINS = "EXPLAINS"
    LINKS_TO = "LINKS_TO"
    HAS_METADATA = "HAS_METADATA"
    UNKNOWN = "UNKNOWN"


class StructuralMatchKind(str, Enum):
    EXACT_DIGEST_MATCH = "EXACT_DIGEST_MATCH"
    SAME_SIGNATURE = "SAME_SIGNATURE"
    POSSIBLE_ISOMORPHIC = "POSSIBLE_ISOMORPHIC"
    SAME_SHAPE_DIFFERENT_LABELS = "SAME_SHAPE_DIFFERENT_LABELS"
    NEAR_DUPLICATE = "NEAR_DUPLICATE"
    CONFLICTING_DUPLICATE = "CONFLICTING_DUPLICATE"
    DISTINCT = "DISTINCT"
    UNKNOWN = "UNKNOWN"


class StructuralMergeDecision(str, Enum):
    MERGE_RECOMMENDED = "MERGE_RECOMMENDED"
    REVIEW_RECOMMENDED = "REVIEW_RECOMMENDED"
    KEEP_DISTINCT = "KEEP_DISTINCT"
    CONFLICT_REVIEW = "CONFLICT_REVIEW"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    UNKNOWN = "UNKNOWN"


class StructuralIdentityReportStatus(str, Enum):
    EMPTY = "EMPTY"
    SIGNED = "SIGNED"
    COMPARED = "COMPARED"
    MERGE_CANDIDATES_FOUND = "MERGE_CANDIDATES_FOUND"
    NO_MATCHES = "NO_MATCHES"
    HAS_WARNINGS = "HAS_WARNINGS"
    HAS_CRITICALS = "HAS_CRITICALS"
    ADVISORY_ONLY = "ADVISORY_ONLY"


@dataclass
class StructuralNode:
    node_id: str
    kind: StructuralNodeKind
    label: str | None = None
    value_digest: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    advisory: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {"node_id": self.node_id, "kind": self.kind.value, "label": self.label, "value_digest": self.value_digest, "metadata": dict(self.metadata), "advisory": self.advisory}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "StructuralNode":
        return cls(str(data["node_id"]), StructuralNodeKind(str(data.get("kind", StructuralNodeKind.UNKNOWN.value))), _opt(data.get("label")), _opt(data.get("value_digest")), dict(data.get("metadata", {})), bool(data.get("advisory", True)))

    def to_json(self) -> str:
        return _json(self.to_dict())

    @classmethod
    def from_json(cls, text: str) -> "StructuralNode":
        return cls.from_dict(json.loads(text))


@dataclass
class StructuralEdge:
    edge_id: str
    kind: StructuralEdgeKind
    source_node_id: str
    target_node_id: str
    label: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    advisory: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {"edge_id": self.edge_id, "kind": self.kind.value, "source_node_id": self.source_node_id, "target_node_id": self.target_node_id, "label": self.label, "metadata": dict(self.metadata), "advisory": self.advisory}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "StructuralEdge":
        return cls(str(data["edge_id"]), StructuralEdgeKind(str(data.get("kind", StructuralEdgeKind.UNKNOWN.value))), str(data["source_node_id"]), str(data["target_node_id"]), _opt(data.get("label")), dict(data.get("metadata", {})), bool(data.get("advisory", True)))

    def to_json(self) -> str:
        return _json(self.to_dict())

    @classmethod
    def from_json(cls, text: str) -> "StructuralEdge":
        return cls.from_dict(json.loads(text))


@dataclass
class StructuralGraph:
    graph_id: str
    object_id: str | None = None
    object_kind: StructuralObjectKind = StructuralObjectKind.UNKNOWN
    nodes: list[StructuralNode] = field(default_factory=list)
    edges: list[StructuralEdge] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    advisory: bool = True

    def node_count(self) -> int:
        return len(self.nodes)

    def edge_count(self) -> int:
        return len(self.edges)

    def degree_profile(self) -> tuple[int, ...]:
        degree = Counter()
        for edge in self.edges:
            degree[edge.source_node_id] += 1
            degree[edge.target_node_id] += 1
        return tuple(sorted(degree.get(node.node_id, 0) for node in self.nodes))

    def node_kind_counts(self) -> dict[str, int]:
        return dict(Counter(node.kind.value for node in self.nodes))

    def edge_kind_counts(self) -> dict[str, int]:
        return dict(Counter(edge.kind.value for edge in self.edges))

    def to_dict(self) -> dict[str, Any]:
        return {"graph_id": self.graph_id, "object_id": self.object_id, "object_kind": self.object_kind.value, "nodes": [n.to_dict() for n in self.nodes], "edges": [e.to_dict() for e in self.edges], "metadata": dict(self.metadata), "advisory": self.advisory}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "StructuralGraph":
        return cls(str(data["graph_id"]), _opt(data.get("object_id")), StructuralObjectKind(str(data.get("object_kind", StructuralObjectKind.UNKNOWN.value))), [StructuralNode.from_dict(n) for n in data.get("nodes", [])], [StructuralEdge.from_dict(e) for e in data.get("edges", [])], dict(data.get("metadata", {})), bool(data.get("advisory", True)))

    def to_json(self) -> str:
        return _json(self.to_dict())

    @classmethod
    def from_json(cls, text: str) -> "StructuralGraph":
        return cls.from_dict(json.loads(text))


@dataclass
class StructuralSignature:
    signature_id: str
    object_id: str | None = None
    object_kind: StructuralObjectKind = StructuralObjectKind.UNKNOWN
    graph_id: str | None = None
    node_count: int = 0
    edge_count: int = 0
    node_kind_counts: dict[str, int] = field(default_factory=dict)
    edge_kind_counts: dict[str, int] = field(default_factory=dict)
    degree_profile: tuple[int, ...] = ()
    wl_rounds: int = 2
    wl_color_histories: tuple[tuple[str, int], ...] = ()
    canonical_digest: str | None = None
    weak_digest: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    advisory: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {"signature_id": self.signature_id, "object_id": self.object_id, "object_kind": self.object_kind.value, "graph_id": self.graph_id, "node_count": self.node_count, "edge_count": self.edge_count, "node_kind_counts": dict(self.node_kind_counts), "edge_kind_counts": dict(self.edge_kind_counts), "degree_profile": list(self.degree_profile), "wl_rounds": self.wl_rounds, "wl_color_histories": [list(x) for x in self.wl_color_histories], "canonical_digest": self.canonical_digest, "weak_digest": self.weak_digest, "metadata": dict(self.metadata), "advisory": self.advisory}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "StructuralSignature":
        return cls(str(data["signature_id"]), _opt(data.get("object_id")), StructuralObjectKind(str(data.get("object_kind", StructuralObjectKind.UNKNOWN.value))), _opt(data.get("graph_id")), int(data.get("node_count", 0)), int(data.get("edge_count", 0)), dict(data.get("node_kind_counts", {})), dict(data.get("edge_kind_counts", {})), tuple(int(x) for x in data.get("degree_profile", ())), int(data.get("wl_rounds", 2)), tuple((str(a), int(b)) for a, b in data.get("wl_color_histories", ())), _opt(data.get("canonical_digest")), _opt(data.get("weak_digest")), dict(data.get("metadata", {})), bool(data.get("advisory", True)))

    def to_json(self) -> str:
        return _json(self.to_dict())

    @classmethod
    def from_json(cls, text: str) -> "StructuralSignature":
        return cls.from_dict(json.loads(text))


@dataclass
class StructuralMergeCandidate:
    candidate_id: str
    left_object_id: str
    right_object_id: str
    left_kind: StructuralObjectKind
    right_kind: StructuralObjectKind
    match_kind: StructuralMatchKind
    decision: StructuralMergeDecision
    confidence: float = 0.0
    shared_digest: str | None = None
    reason: str | None = None
    warnings: tuple[str, ...] = ()
    criticals: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    advisory: bool = True

    def is_actionable(self) -> bool:
        return self.decision in {StructuralMergeDecision.MERGE_RECOMMENDED, StructuralMergeDecision.REVIEW_RECOMMENDED, StructuralMergeDecision.CONFLICT_REVIEW}

    def to_dict(self) -> dict[str, Any]:
        return {"candidate_id": self.candidate_id, "left_object_id": self.left_object_id, "right_object_id": self.right_object_id, "left_kind": self.left_kind.value, "right_kind": self.right_kind.value, "match_kind": self.match_kind.value, "decision": self.decision.value, "confidence": self.confidence, "shared_digest": self.shared_digest, "reason": self.reason, "warnings": list(self.warnings), "criticals": list(self.criticals), "metadata": dict(self.metadata), "advisory": self.advisory}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "StructuralMergeCandidate":
        return cls(str(data["candidate_id"]), str(data["left_object_id"]), str(data["right_object_id"]), StructuralObjectKind(str(data.get("left_kind", StructuralObjectKind.UNKNOWN.value))), StructuralObjectKind(str(data.get("right_kind", StructuralObjectKind.UNKNOWN.value))), StructuralMatchKind(str(data.get("match_kind", StructuralMatchKind.UNKNOWN.value))), StructuralMergeDecision(str(data.get("decision", StructuralMergeDecision.UNKNOWN.value))), float(data.get("confidence", 0.0) or 0.0), _opt(data.get("shared_digest")), _opt(data.get("reason")), tuple(str(x) for x in data.get("warnings", ())), tuple(str(x) for x in data.get("criticals", ())), dict(data.get("metadata", {})), bool(data.get("advisory", True)))

    def to_json(self) -> str:
        return _json(self.to_dict())

    @classmethod
    def from_json(cls, text: str) -> "StructuralMergeCandidate":
        return cls.from_dict(json.loads(text))


@dataclass
class StructuralIdentityReport:
    report_id: str
    graphs: list[StructuralGraph] = field(default_factory=list)
    signatures: list[StructuralSignature] = field(default_factory=list)
    merge_candidates: list[StructuralMergeCandidate] = field(default_factory=list)
    status: StructuralIdentityReportStatus = StructuralIdentityReportStatus.EMPTY
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    summary: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=lambda: {"advisory_only": True})
    advisory: bool = True

    def graph_count(self) -> int:
        return len(self.graphs)

    def signature_count(self) -> int:
        return len(self.signatures)

    def merge_candidate_count(self) -> int:
        return len(self.merge_candidates)

    def critical_count(self) -> int:
        return sum(len(candidate.criticals) for candidate in self.merge_candidates)

    def summarize(self) -> dict[str, Any]:
        counts = Counter(candidate.match_kind.value for candidate in self.merge_candidates)
        self.summary = {
            "graph_total": len(self.graphs),
            "signature_total": len(self.signatures),
            "merge_candidate_total": len(self.merge_candidates),
            "exact_match_count": counts[StructuralMatchKind.EXACT_DIGEST_MATCH.value],
            "same_signature_count": counts[StructuralMatchKind.SAME_SIGNATURE.value],
            "possible_isomorphic_count": counts[StructuralMatchKind.POSSIBLE_ISOMORPHIC.value],
            "near_duplicate_count": counts[StructuralMatchKind.NEAR_DUPLICATE.value],
            "conflict_count": counts[StructuralMatchKind.CONFLICTING_DUPLICATE.value],
            "critical_count": self.critical_count(),
            "advisory_count": sum(1 for item in self.merge_candidates if item.advisory),
        }
        return self.summary

    def to_dict(self) -> dict[str, Any]:
        return {"report_id": self.report_id, "graphs": [g.to_dict() for g in self.graphs], "signatures": [s.to_dict() for s in self.signatures], "merge_candidates": [c.to_dict() for c in self.merge_candidates], "status": self.status.value, "created_at": self.created_at, "summary": dict(self.summary), "metadata": dict(self.metadata), "advisory": self.advisory}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "StructuralIdentityReport":
        return cls(str(data["report_id"]), [StructuralGraph.from_dict(x) for x in data.get("graphs", [])], [StructuralSignature.from_dict(x) for x in data.get("signatures", [])], [StructuralMergeCandidate.from_dict(x) for x in data.get("merge_candidates", [])], StructuralIdentityReportStatus(str(data.get("status", StructuralIdentityReportStatus.EMPTY.value))), str(data.get("created_at") or datetime.now(timezone.utc).isoformat()), dict(data.get("summary", {})), dict(data.get("metadata", {"advisory_only": True})), bool(data.get("advisory", True)))

    def to_json(self) -> str:
        return _json(self.to_dict())

    @classmethod
    def from_json(cls, text: str) -> "StructuralIdentityReport":
        return cls.from_dict(json.loads(text))

    def write_json(self, path: str | Path) -> None:
        _write(path, self.to_json() + "\n")

    @classmethod
    def read_json(cls, path: str | Path) -> "StructuralIdentityReport":
        return cls.from_json(Path(path).read_text(encoding="utf-8"))

    def write_jsonl(self, path: str | Path) -> None:
        _write(path, self.to_json() + "\n")

    @classmethod
    def read_jsonl(cls, path: str | Path) -> list["StructuralIdentityReport"]:
        return [cls.from_json(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def make_structural_node_id(*parts: Any) -> str: return content_id("structural-node", parts)
def make_structural_edge_id(*parts: Any) -> str: return content_id("structural-edge", parts)
def make_structural_graph_id(*parts: Any) -> str: return content_id("structural-graph", parts)
def make_structural_signature_id(*parts: Any) -> str: return content_id("structural-signature", parts)
def make_structural_merge_candidate_id(*parts: Any) -> str: return content_id("structural-merge", parts)
def make_structural_identity_report_id(*parts: Any) -> str: return content_id("structural-report", parts)


class _Builder:
    def __init__(self, object_id: str | None, object_kind: StructuralObjectKind, root_kind: StructuralNodeKind) -> None:
        self.graph = StructuralGraph(make_structural_graph_id(object_kind.value, object_id), object_id, object_kind, metadata={})
        self.root = self.node(root_kind, object_id or object_kind.value)

    def node(self, kind: StructuralNodeKind, value: Any = None, label: str | None = None) -> str:
        node_id = make_structural_node_id(self.graph.graph_id, kind.value, len(self.graph.nodes), value)
        self.graph.nodes.append(StructuralNode(node_id, kind, label, _value_digest(value) if value is not None else None))
        return node_id

    def edge(self, kind: StructuralEdgeKind, source: str, target: str) -> None:
        self.graph.edges.append(StructuralEdge(make_structural_edge_id(self.graph.graph_id, kind.value, source, target, len(self.graph.edges)), kind, source, target))

    def attach(self, edge: StructuralEdgeKind, kind: StructuralNodeKind, value: Any) -> None:
        if value is None:
            return
        node = self.node(kind, value)
        self.edge(edge, self.root, node)


def structural_graph_from_lawbook_entry(entry: LawbookEntry) -> StructuralGraph:
    b = _Builder(entry.entry_id, StructuralObjectKind.LAWBOOK_ENTRY, StructuralNodeKind.ENTRY)
    b.graph.metadata.update({"claim_id": entry.claim_id, "certificate_id": entry.certificate_id, "terminal_form": entry.terminal_form.value if entry.terminal_form else None})
    b.attach(StructuralEdgeKind.HAS_SOURCE, StructuralNodeKind.SOURCE, entry.source)
    b.attach(StructuralEdgeKind.HAS_TARGET, StructuralNodeKind.TARGET, entry.target)
    b.attach(StructuralEdgeKind.HAS_TERMINAL_FORM, StructuralNodeKind.TERMINAL_FORM, entry.terminal_form.value if entry.terminal_form else None)
    b.attach(StructuralEdgeKind.HAS_CERTIFICATE, StructuralNodeKind.CERTIFICATE, entry.certificate_id)
    for edge, kind, values in (
        (StructuralEdgeKind.HAS_ARTIFACT, StructuralNodeKind.ARTIFACT, entry.artifact_ids),
        (StructuralEdgeKind.HAS_CONDITION, StructuralNodeKind.CONDITION, entry.conditions),
        (StructuralEdgeKind.HAS_OBSTRUCTION, StructuralNodeKind.OBSTRUCTION, entry.failure_boundaries),
        (StructuralEdgeKind.HAS_REASON, StructuralNodeKind.REASON, entry.reason_links),
        (StructuralEdgeKind.HAS_ROOT, StructuralNodeKind.ROOT, entry.root_links),
        (StructuralEdgeKind.HAS_PROJECTION, StructuralNodeKind.PROJECTION, entry.projection_rule_ids),
        (StructuralEdgeKind.HAS_DIGESTION, StructuralNodeKind.DIGESTION, entry.digestion_trace_ids),
        (StructuralEdgeKind.HAS_TRACE, StructuralNodeKind.TRACE, entry.assimilation_candidate_ids),
    ):
        for value in values:
            b.attach(edge, kind, value)
    return b.graph


def structural_graph_from_lawbook_store(store: LawbookStore) -> StructuralGraph:
    b = _Builder(store.store_id, StructuralObjectKind.LAWBOOK_STORE, StructuralNodeKind.ROOT)
    for entry in store.entries:
        node = b.node(StructuralNodeKind.ENTRY, entry.entry_id)
        b.edge(StructuralEdgeKind.HAS_ARTIFACT, b.root, node)
    for review in store.reviews:
        node = b.node(StructuralNodeKind.REASON, review.review_id)
        b.edge(StructuralEdgeKind.REVIEWED_BY, b.root, node)
    return b.graph


def structural_graph_from_lawbook_query_answer(answer: Any) -> StructuralGraph:
    b = _Builder(answer.answer_id, StructuralObjectKind.LAWBOOK_QUERY_ANSWER, StructuralNodeKind.ROOT)
    b.attach(StructuralEdgeKind.HAS_CERTIFICATE, StructuralNodeKind.CERTIFICATE, answer.certificate_id)
    b.attach(StructuralEdgeKind.HAS_TERMINAL_FORM, StructuralNodeKind.TERMINAL_FORM, answer.terminal_form.value if answer.terminal_form else None)
    b.attach(StructuralEdgeKind.HAS_VALUE, StructuralNodeKind.VALUE, answer.trust_level.value)
    for value in answer.matched_entry_ids:
        b.attach(StructuralEdgeKind.LINKS_TO, StructuralNodeKind.ENTRY, value)
    for value in answer.candidate_entry_ids:
        b.attach(StructuralEdgeKind.LINKS_TO, StructuralNodeKind.ENTRY, value)
    for value in answer.projection_candidate_ids:
        b.attach(StructuralEdgeKind.HAS_PROJECTION, StructuralNodeKind.PROJECTION, value)
    for value in answer.digestion_trace_ids:
        b.attach(StructuralEdgeKind.HAS_DIGESTION, StructuralNodeKind.DIGESTION, value)
    return b.graph


def structural_graph_from_proof_digestion_trace(trace: Any) -> StructuralGraph:
    b = _Builder(trace.trace_id, StructuralObjectKind.PROOF_DIGESTION_TRACE, StructuralNodeKind.DIGESTION)
    for values, edge, kind in (
        (trace.dependency_maps, StructuralEdgeKind.HAS_DIGESTION, StructuralNodeKind.TRACE),
        (trace.key_ideas, StructuralEdgeKind.HAS_REASON, StructuralNodeKind.REASON),
        (trace.reusable_schemas, StructuralEdgeKind.HAS_ROOT, StructuralNodeKind.ROOT),
        (trace.projection_candidates, StructuralEdgeKind.HAS_PROJECTION, StructuralNodeKind.PROJECTION),
    ):
        for value in values:
            ident = getattr(value, "map_id", None) or getattr(value, "idea_id", None) or getattr(value, "schema_id", None) or getattr(value, "candidate_id", None)
            b.attach(edge, kind, ident)
    return b.graph


def structural_graph_from_projection_candidate(candidate: Any) -> StructuralGraph:
    b = _Builder(candidate.candidate_id, StructuralObjectKind.PROJECTION_CANDIDATE, StructuralNodeKind.PROJECTION)
    b.attach(StructuralEdgeKind.HAS_SOURCE, StructuralNodeKind.SOURCE, candidate.source or candidate.source_claim_id)
    b.attach(StructuralEdgeKind.HAS_TARGET, StructuralNodeKind.TARGET, candidate.target or candidate.target_claim_id)
    b.attach(StructuralEdgeKind.HAS_CERTIFICATE, StructuralNodeKind.CERTIFICATE, candidate.originating_certificate_id)
    b.attach(StructuralEdgeKind.HAS_REASON, StructuralNodeKind.REASON, candidate.rule_kind.value)
    return b.graph


def structural_graph_from_discovery_value_score(score: Any) -> StructuralGraph:
    b = _Builder(score.score_id, StructuralObjectKind.DISCOVERY_VALUE_SCORE, StructuralNodeKind.METADATA)
    for signal in score.signals:
        node = b.node(StructuralNodeKind.METADATA, signal.kind.value)
        b.edge(StructuralEdgeKind.HAS_VALUE, b.root, node)
        if signal.reason:
            reason = b.node(StructuralNodeKind.REASON, signal.reason)
            b.edge(StructuralEdgeKind.HAS_REASON, node, reason)
    return b.graph


def structural_graph_from_curriculum(curriculum: ContinuationCurriculum) -> StructuralGraph:
    b = _Builder(curriculum.curriculum_id, StructuralObjectKind.CONTINUATION_CURRICULUM, StructuralNodeKind.ROOT)
    for stage in curriculum.stages:
        node = b.node(StructuralNodeKind.STAGE, stage.kind.value)
        b.edge(StructuralEdgeKind.HAS_STAGE, b.root, node)
        for dep in stage.depends_on:
            dep_node = b.node(StructuralNodeKind.STAGE, dep)
            b.edge(StructuralEdgeKind.DEPENDS_ON, node, dep_node)
    return b.graph


def structural_graph_from_curriculum_stage(stage: CurriculumStage) -> StructuralGraph:
    b = _Builder(stage.stage_id, StructuralObjectKind.CURRICULUM_STAGE, StructuralNodeKind.STAGE)
    b.attach(StructuralEdgeKind.HAS_SOURCE, StructuralNodeKind.SOURCE, stage.source)
    b.attach(StructuralEdgeKind.HAS_TARGET, StructuralNodeKind.TARGET, stage.target)
    for dep in stage.depends_on:
        b.attach(StructuralEdgeKind.DEPENDS_ON, StructuralNodeKind.STAGE, dep)
    return b.graph


def structural_graph_from_verifier_feedback(feedback: Any) -> StructuralGraph:
    b = _Builder(feedback.feedback_id, StructuralObjectKind.VERIFIER_FEEDBACK, StructuralNodeKind.FEEDBACK)
    b.attach(StructuralEdgeKind.HAS_ARTIFACT, StructuralNodeKind.ARTIFACT, feedback.artifact_id)
    b.attach(StructuralEdgeKind.HAS_REASON, StructuralNodeKind.REASON, feedback.flaw_severity.value)
    return b.graph


def structural_graph_from_repair_loop(trace: Any) -> StructuralGraph:
    b = _Builder(trace.trace_id, StructuralObjectKind.REPAIR_LOOP_TRACE, StructuralNodeKind.REPAIR)
    for feedback in trace.feedback_items:
        b.attach(StructuralEdgeKind.HAS_FEEDBACK, StructuralNodeKind.FEEDBACK, feedback.feedback_id)
    for plan in trace.repair_plans:
        b.attach(StructuralEdgeKind.HAS_REPAIR, StructuralNodeKind.REPAIR, plan.repair_plan_id)
    return b.graph


def structural_graph_from_alchemical_trace(trace: AlchemicalTrace) -> StructuralGraph:
    b = _Builder(trace.trace_id, StructuralObjectKind.ALCHEMICAL_TRACE, StructuralNodeKind.TRACE)
    prev = None
    for step in trace.steps:
        node = b.node(StructuralNodeKind.PHASE, step.phase.value)
        b.edge(StructuralEdgeKind.HAS_PHASE, b.root, node)
        if prev:
            b.edge(StructuralEdgeKind.DEPENDS_ON, node, prev)
        prev = node
    return b.graph


def structural_graph_from_agent_experience(exp: AgentExperience) -> StructuralGraph:
    b = _Builder(exp.experience_id, StructuralObjectKind.AGENT_EXPERIENCE, StructuralNodeKind.AGENT)
    b.attach(StructuralEdgeKind.HAS_ROUTE, StructuralNodeKind.ROUTE, exp.route)
    b.attach(StructuralEdgeKind.HAS_TERMINAL_FORM, StructuralNodeKind.TERMINAL_FORM, exp.terminal_form.value if exp.terminal_form else None)
    b.attach(StructuralEdgeKind.HAS_CERTIFICATE, StructuralNodeKind.CERTIFICATE, exp.certificate_id)
    return b.graph


def structural_graph_from_mapping(data: Mapping[str, Any], *, object_id: str | None = None, object_kind: StructuralObjectKind = StructuralObjectKind.RAW_OBJECT, max_depth: int = 4, max_items: int = 100) -> StructuralGraph:
    b = _Builder(object_id or content_id("raw-object", data), object_kind, StructuralNodeKind.ROOT)
    count = 0

    def visit(parent: str, value: Any, depth: int) -> None:
        nonlocal count
        if depth > max_depth or count >= max_items:
            return
        if isinstance(value, Mapping):
            for key, child in list(value.items())[:max_items]:
                if count >= max_items:
                    return
                node = b.node(StructuralNodeKind.METADATA, key)
                count += 1
                b.edge(StructuralEdgeKind.HAS_METADATA, parent, node)
                visit(node, child, depth + 1)
        elif isinstance(value, list):
            for child in value[:max_items]:
                if count >= max_items:
                    return
                node = b.node(StructuralNodeKind.METADATA, "item")
                count += 1
                b.edge(StructuralEdgeKind.LINKS_TO, parent, node)
                visit(node, child, depth + 1)
        else:
            node = b.node(StructuralNodeKind.METADATA, value)
            count += 1
            b.edge(StructuralEdgeKind.HAS_VALUE, parent, node)

    visit(b.root, data, 0)
    return b.graph


def structural_graph_from_object(obj: Any) -> StructuralGraph:
    from mathgraph.discovery_value import DiscoveryValueReport, DiscoveryValueScore
    from mathgraph.lawbook_query import LawbookQueryAnswer, LawbookQueryReport
    from mathgraph.projection import ProjectionCandidate
    from mathgraph.proof_digestion import LawbookAssimilationCandidate, ProofDigestionTrace
    from mathgraph.verifier_feedback import RepairLoopTrace, VerifierFeedback

    if isinstance(obj, LawbookEntry): return structural_graph_from_lawbook_entry(obj)
    if isinstance(obj, LawbookStore): return structural_graph_from_lawbook_store(obj)
    if isinstance(obj, LawbookQueryAnswer): return structural_graph_from_lawbook_query_answer(obj)
    if isinstance(obj, LawbookQueryReport): return structural_graph_from_mapping(obj.to_dict(), object_id=obj.report_id, object_kind=StructuralObjectKind.LAWBOOK_QUERY_REPORT)
    if isinstance(obj, ProofDigestionTrace): return structural_graph_from_proof_digestion_trace(obj)
    if isinstance(obj, LawbookAssimilationCandidate): return structural_graph_from_mapping(obj.to_dict(), object_id=obj.assimilation_id, object_kind=StructuralObjectKind.LAWBOOK_ASSIMILATION_CANDIDATE)
    if isinstance(obj, ProjectionCandidate): return structural_graph_from_projection_candidate(obj)
    if isinstance(obj, DiscoveryValueScore): return structural_graph_from_discovery_value_score(obj)
    if isinstance(obj, DiscoveryValueReport): return structural_graph_from_mapping(obj.to_dict(), object_id=obj.report_id, object_kind=StructuralObjectKind.DISCOVERY_VALUE_REPORT)
    if isinstance(obj, ContinuationCurriculum): return structural_graph_from_curriculum(obj)
    if isinstance(obj, CurriculumStage): return structural_graph_from_curriculum_stage(obj)
    if isinstance(obj, VerifierFeedback): return structural_graph_from_verifier_feedback(obj)
    if isinstance(obj, RepairLoopTrace): return structural_graph_from_repair_loop(obj)
    if isinstance(obj, AlchemicalTrace): return structural_graph_from_alchemical_trace(obj)
    if isinstance(obj, AgentExperience): return structural_graph_from_agent_experience(obj)
    if isinstance(obj, Mapping): return structural_graph_from_mapping(obj)
    return structural_graph_from_mapping({"repr": repr(obj)}, object_kind=StructuralObjectKind.RAW_OBJECT)


def compute_structural_signature(graph: StructuralGraph, *, wl_rounds: int = 2, include_value_digests: bool = False) -> StructuralSignature:
    colors = {node.node_id: content_id("structural-color", (node.kind.value, node.value_digest if include_value_digests else None)) for node in graph.nodes}
    incoming = {node.node_id: [] for node in graph.nodes}
    outgoing = {node.node_id: [] for node in graph.nodes}
    for edge in graph.edges:
        outgoing.setdefault(edge.source_node_id, []).append(edge)
        incoming.setdefault(edge.target_node_id, []).append(edge)
    for _ in range(wl_rounds):
        colors = {
            node.node_id: content_id(
                "structural-color",
                (
                    colors[node.node_id],
                    sorted((edge.kind.value, colors[edge.target_node_id]) for edge in outgoing.get(node.node_id, [])),
                    sorted((edge.kind.value, colors[edge.source_node_id]) for edge in incoming.get(node.node_id, [])),
                ),
            )
            for node in graph.nodes
        }
    histogram = tuple(sorted(Counter(colors.values()).items()))
    weak = content_id("structural-weak", (graph.node_count(), graph.edge_count(), graph.node_kind_counts(), graph.edge_kind_counts(), graph.degree_profile()))
    canonical = content_id("structural-canonical", (histogram, graph.edge_kind_counts(), graph.degree_profile()))
    return StructuralSignature(make_structural_signature_id(graph.graph_id, include_value_digests, wl_rounds), graph.object_id, graph.object_kind, graph.graph_id, graph.node_count(), graph.edge_count(), graph.node_kind_counts(), graph.edge_kind_counts(), graph.degree_profile(), wl_rounds, histogram, canonical, weak, dict(graph.metadata))


def compare_structural_signatures(left: StructuralSignature, right: StructuralSignature) -> StructuralMergeCandidate:
    left_id, right_id = left.object_id or left.signature_id, right.object_id or right.signature_id
    same_claim = left.metadata.get("claim_id") and left.metadata.get("claim_id") == right.metadata.get("claim_id")
    same_cert = left.metadata.get("certificate_id") and left.metadata.get("certificate_id") == right.metadata.get("certificate_id")
    conflicting_terminal = left.metadata.get("terminal_form") and right.metadata.get("terminal_form") and left.metadata.get("terminal_form") != right.metadata.get("terminal_form")
    if (same_claim or same_cert) and conflicting_terminal:
        return _candidate(left, right, StructuralMatchKind.CONFLICTING_DUPLICATE, StructuralMergeDecision.CONFLICT_REVIEW, 1.0, "shared claim/certificate has conflicting terminal forms", criticals=("conflicting terminal forms",))
    if left.canonical_digest and left.canonical_digest == right.canonical_digest:
        return _candidate(left, right, StructuralMatchKind.EXACT_DIGEST_MATCH, StructuralMergeDecision.MERGE_RECOMMENDED, 1.0, "same canonical digest", shared=left.canonical_digest)
    if left.weak_digest and left.weak_digest == right.weak_digest and left.node_count == right.node_count and left.edge_count == right.edge_count:
        return _candidate(left, right, StructuralMatchKind.SAME_SIGNATURE, StructuralMergeDecision.REVIEW_RECOMMENDED, 0.85, "same weak digest", shared=left.weak_digest)
    if left.node_count == right.node_count and left.edge_count == right.edge_count and left.node_kind_counts == right.node_kind_counts and left.edge_kind_counts == right.edge_kind_counts:
        return _candidate(left, right, StructuralMatchKind.POSSIBLE_ISOMORPHIC, StructuralMergeDecision.REVIEW_RECOMMENDED, 0.65, "same size and kind profile")
    overlap = _overlap(left.node_kind_counts, right.node_kind_counts)
    if overlap >= 0.5 and left.degree_profile == right.degree_profile:
        return _candidate(left, right, StructuralMatchKind.NEAR_DUPLICATE, StructuralMergeDecision.REVIEW_RECOMMENDED, 0.45, "overlapping kind profile and degree shape")
    return _candidate(left, right, StructuralMatchKind.DISTINCT, StructuralMergeDecision.KEEP_DISTINCT, 0.0, "distinct structural profile")


def find_structural_merge_candidates(signatures: Sequence[StructuralSignature], *, min_confidence: float = 0.45) -> list[StructuralMergeCandidate]:
    found = []
    for index, left in enumerate(signatures):
        for right in signatures[index + 1:]:
            candidate = compare_structural_signatures(left, right)
            if candidate.confidence >= min_confidence or candidate.match_kind == StructuralMatchKind.CONFLICTING_DUPLICATE:
                found.append(candidate)
    return found


def build_structural_identity_report(objects: Sequence[Any] = (), graphs: Sequence[StructuralGraph] = (), *, include_value_digests: bool = False, min_confidence: float = 0.45, max_objects: int | None = None) -> StructuralIdentityReport:
    built_graphs = list(graphs)
    for obj in list(objects)[:max_objects]:
        built_graphs.append(structural_graph_from_object(obj))
    signatures = [compute_structural_signature(graph, include_value_digests=include_value_digests) for graph in built_graphs]
    candidates = find_structural_merge_candidates(signatures, min_confidence=min_confidence)
    report = StructuralIdentityReport(make_structural_identity_report_id([g.graph_id for g in built_graphs], include_value_digests, min_confidence), built_graphs, signatures, candidates)
    report.summarize()
    if not built_graphs:
        report.status = StructuralIdentityReportStatus.EMPTY
    elif any(candidate.match_kind == StructuralMatchKind.CONFLICTING_DUPLICATE for candidate in candidates):
        report.status = StructuralIdentityReportStatus.HAS_CRITICALS
    elif candidates:
        report.status = StructuralIdentityReportStatus.MERGE_CANDIDATES_FOUND
    else:
        report.status = StructuralIdentityReportStatus.COMPARED
    return report


def structural_identity_report_to_lawbook_candidates(report: StructuralIdentityReport) -> list[LawbookEntry]:
    entries = []
    for candidate in report.merge_candidates:
        entries.append(LawbookEntry(entry_id=make_lawbook_entry_id("structural", candidate.candidate_id), kind=LawbookEntryKind.REUSABLE_SCHEMA_ENTRY if candidate.decision != StructuralMergeDecision.CONFLICT_REVIEW else LawbookEntryKind.ROUTE_RULE_ENTRY, status=LawbookEntryStatus.CANDIDATE, metadata={"structural_identity_not_equality": True, "merge_candidate_id": candidate.candidate_id, "match_kind": candidate.match_kind.value, "confidence": candidate.confidence}, advisory=True))
    return entries


def structural_identity_report_to_continuation_outputs(report: StructuralIdentityReport) -> list[ContinuationActionOutput]:
    outputs = []
    for candidate in report.merge_candidates:
        kind = "audit structural conflict" if candidate.decision == StructuralMergeDecision.CONFLICT_REVIEW else "review structural merge"
        outputs.append(ContinuationActionOutput(make_continuation_output_id({"source": "structural", "candidate_id": candidate.candidate_id}), "structural_identity", ContinuationOutputKind.TASK, ContinuationActionStatus.ADVISORY_ONLY, task_payload={"task": kind, "merge_candidate_id": candidate.candidate_id}, note=candidate.reason, metadata={"structural_identity_not_equality": True}, advisory=True))
    return outputs


def structural_identity_report_to_curriculum(report: StructuralIdentityReport) -> ContinuationCurriculum:
    stages = []
    for candidate in report.merge_candidates:
        kind = CurriculumStageKind.RESIDUAL_REVIEW if candidate.decision == StructuralMergeDecision.CONFLICT_REVIEW else CurriculumStageKind.HELD_IN_CHORA
        stages.append(CurriculumStage(make_curriculum_stage_id("structural", candidate.candidate_id), kind, CurriculumStageStatus.ADVISORY_ONLY, title="Review structural identity candidate", metadata={"merge_candidate_id": candidate.candidate_id, "structural_identity_not_equality": True}, advisory=True))
    return ContinuationCurriculum(make_curriculum_id("structural", report.report_id), strategy=CurriculumBuildStrategy.MIXED, stages=stages, status=CurriculumTraceStatus.TASKS_EMITTED if stages else CurriculumTraceStatus.EMPTY, metadata={"advisory_only": True}, advisory=True)


def structural_identity_report_to_alchemical_trace(report: StructuralIdentityReport) -> AlchemicalTrace:
    trace = AlchemicalTrace(make_alchemical_trace_id("structural_identity", report.report_id))
    for phase in (AlchemicalPhase.RAW_MATTER, AlchemicalPhase.CALCINATION, AlchemicalPhase.SUBLIMATION, AlchemicalPhase.DISTILLATION, AlchemicalPhase.COAGULATION):
        trace.add_step(phase=phase, status=AlchemicalStatus.ADVISORY_ONLY, metadata={"report_id": report.report_id})
    return trace


def structural_identity_report_to_agent_experiences(report: StructuralIdentityReport, agent_id: str | None = None) -> list[AgentExperience]:
    return [AgentExperience(content_id("structural-exp", (report.report_id, item.candidate_id)), agent_id or "structural-identity", None, None, "structural_identity", None, AgentExperienceOutcome.RESIDUAL if item.decision == StructuralMergeDecision.CONFLICT_REVIEW else AgentExperienceOutcome.ADVISORY_ONLY, metadata={"merge_candidate_id": item.candidate_id, "structural_identity_not_equality": True}) for item in report.merge_candidates]


def structural_identity_report_to_route_telemetry_events(report: StructuralIdentityReport) -> list[dict[str, Any]]:
    return [{"event_id": content_id("structural-telemetry", (report.report_id, item.candidate_id)), "route_kind": "structural_identity", "outcome": item.decision.value, "merge_candidate_id": item.candidate_id, "advisory": True} for item in report.merge_candidates]


def audit_structural_merge_candidate(candidate: StructuralMergeCandidate) -> list[dict[str, Any]]:
    findings = []
    if not candidate.advisory:
        findings.append(_finding("CRITICAL", "STRUCTURAL_MERGE_NON_ADVISORY", "merge candidate is non-advisory", candidate.candidate_id))
    if candidate.metadata.get("terminal_form"):
        findings.append(_finding("CRITICAL", "STRUCTURAL_MERGE_AS_TRUTH", "merge candidate claims terminal truth", candidate.candidate_id))
    if candidate.metadata.get("claims_equality_without_review"):
        findings.append(_finding("CRITICAL", "STRUCTURAL_EQUALITY_WITHOUT_REVIEW", "merge candidate claims equality without review", candidate.candidate_id))
    if candidate.match_kind == StructuralMatchKind.CONFLICTING_DUPLICATE and candidate.decision == StructuralMergeDecision.MERGE_RECOMMENDED:
        findings.append(_finding("CRITICAL", "STRUCTURAL_CONFLICT_MERGE", "conflict candidate recommends merge", candidate.candidate_id))
    if candidate.confidence > 0.8 and not candidate.reason:
        findings.append(_finding("WARNING", "STRUCTURAL_HIGH_CONFIDENCE_NO_REASON", "high-confidence candidate lacks reason", candidate.candidate_id))
    if candidate.match_kind == StructuralMatchKind.NEAR_DUPLICATE and candidate.decision != StructuralMergeDecision.REVIEW_RECOMMENDED:
        findings.append(_finding("WARNING", "STRUCTURAL_NEAR_DUPLICATE_NO_REVIEW", "near duplicate lacks review recommendation", candidate.candidate_id))
    if not 0 <= candidate.confidence <= 1:
        findings.append(_finding("WARNING", "STRUCTURAL_CONFIDENCE_RANGE", "candidate confidence outside 0..1", candidate.candidate_id))
    return findings


def audit_structural_identity_report(report: StructuralIdentityReport) -> list[dict[str, Any]]:
    findings = [item for candidate in report.merge_candidates for item in audit_structural_merge_candidate(candidate)]
    if report.metadata.get("verifier_boundary"):
        findings.append(_finding("CRITICAL", "STRUCTURAL_REPORT_AS_BOUNDARY", "report claims verifier boundary", report.report_id))
    if len(report.graphs) > 10 and not report.signatures:
        findings.append(_finding("WARNING", "STRUCTURAL_REPORT_NO_SIGNATURES", "large report has no signatures", report.report_id))
    if report.signatures and not report.merge_candidates:
        findings.append(_finding("WARNING", "STRUCTURAL_REPORT_NO_CANDIDATES", "report has signatures but no candidates", report.report_id))
    return findings


def _candidate(left: StructuralSignature, right: StructuralSignature, match: StructuralMatchKind, decision: StructuralMergeDecision, confidence: float, reason: str, *, shared: str | None = None, criticals: tuple[str, ...] = ()) -> StructuralMergeCandidate:
    return StructuralMergeCandidate(make_structural_merge_candidate_id(left.signature_id, right.signature_id, match.value), left.object_id or left.signature_id, right.object_id or right.signature_id, left.object_kind, right.object_kind, match, decision, confidence, shared, reason, criticals=criticals)


def _overlap(left: Mapping[str, int], right: Mapping[str, int]) -> float:
    keys = set(left) | set(right)
    total = sum(max(left.get(key, 0), right.get(key, 0)) for key in keys)
    return 0.0 if total == 0 else sum(min(left.get(key, 0), right.get(key, 0)) for key in keys) / total


def _value_digest(value: Any) -> str:
    return content_id("structural-value", value)


def _finding(severity: str, code: str, message: str, object_id: str) -> dict[str, Any]:
    return {"severity": severity, "code": code, "message": message, "object_id": object_id}


def _opt(value: Any) -> str | None:
    return None if value is None else str(value)


def _json(data: Mapping[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def _write(path: str | Path, text: str) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
