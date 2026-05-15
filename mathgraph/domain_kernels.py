"""Formal-world registry objects inspired by AOT-style semantic embeddings."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, TypeVar

from mathgraph.hashing import content_id
from mathgraph.trust import ProvenanceType, TrustLevel, provenance_type, trust_level


class HostVerifier(str, Enum):
    PYTHON_FINITE_CHECKER = "PYTHON_FINITE_CHECKER"
    LEAN = "LEAN"
    ISABELLE_HOL = "ISABELLE_HOL"
    Z3 = "Z3"
    OTHER = "OTHER"


class SemanticEmbeddingKind(str, Enum):
    NONE = "NONE"
    SHALLOW_SEMANTIC_EMBEDDING = "SHALLOW_SEMANTIC_EMBEDDING"
    DEEP_EMBEDDING = "DEEP_EMBEDDING"
    DIRECT_NATIVE = "DIRECT_NATIVE"
    IMPORTED_CERTIFICATE_CORPUS = "IMPORTED_CERTIFICATE_CORPUS"
    OTHER = "OTHER"


class TheoryObjectKind(str, Enum):
    EQUATION = "EQUATION"
    CLAIM = "CLAIM"
    AXIOM = "AXIOM"
    DEFINITION = "DEFINITION"
    THEOREM = "THEOREM"
    LEMMA = "LEMMA"
    PROOF_ARTIFACT = "PROOF_ARTIFACT"
    REFUTATION_ARTIFACT = "REFUTATION_ARTIFACT"
    ABSTRACT_OBJECT = "ABSTRACT_OBJECT"
    PROPERTY = "PROPERTY"
    PROPOSITION = "PROPOSITION"
    POSSIBLE_WORLD = "POSSIBLE_WORLD"
    TYPE = "TYPE"
    TERM = "TERM"
    OTHER = "OTHER"


class TheoryRelationKind(str, Enum):
    DEFINES = "DEFINES"
    DEPENDS_ON = "DEPENDS_ON"
    PROVES = "PROVES"
    REFUTES = "REFUTES"
    EMBEDS_IN = "EMBEDS_IN"
    IMPORTED_FROM = "IMPORTED_FROM"
    HAS_HOST_VERIFIER = "HAS_HOST_VERIFIER"
    HAS_NATIVE_LANGUAGE = "HAS_NATIVE_LANGUAGE"
    HAS_ONTOLOGY_OBJECT = "HAS_ONTOLOGY_OBJECT"
    ENCODED_BY = "ENCODED_BY"
    EXEMPLIFIES = "EXEMPLIFIES"
    SATISFIES = "SATISFIES"
    VIOLATES = "VIOLATES"
    OTHER = "OTHER"


EnumT = TypeVar("EnumT", bound=Enum)


def _enum(value: str | Enum | None, enum_type: type[EnumT], default: EnumT) -> EnumT:
    if isinstance(value, enum_type):
        return value
    text = "" if value is None else str(value)
    for member in enum_type:
        if text == member.name or text == str(member.value):
            return member
    return default


def make_kernel_id(name: str, source_uri: str = "", source_commit: str = "") -> str:
    return content_id(
        "domain_kernel",
        {
            "name": " ".join(name.strip().split()),
            "source_uri": source_uri,
            "source_commit": source_commit,
        },
    )


@dataclass(frozen=True)
class DomainKernel:
    kernel_id: str
    name: str
    host_verifier: HostVerifier
    embedding_kind: SemanticEmbeddingKind
    description: str = ""
    native_language: str = ""
    source_uri: str = ""
    source_commit: str = ""
    trust_policy: str = ""
    ontology_summary: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    host_logic: str = ""
    object_logic: str = ""
    object_theory: str = ""
    artifact_risk: str = "UNKNOWN"
    proof_transport_status: str = "NOT_ATTEMPTED"
    default_denotation_policy: str = ""
    default_type_system: str = ""
    default_identity_policy: str = ""
    default_hyperintensional_identity_policy: str = ""
    extensional_collapse_policy: str = "NEVER_BY_DEFAULT"
    workbench_id: str = ""
    workbench_layer: str = ""
    lifecycle_status: str = ""
    embedding_strategy: str = ""
    faithfulness_status: str = ""
    benchmark_status: str = ""
    default_formal_world_id: str = ""
    notes: str = ""

    @classmethod
    def create(
        cls,
        *,
        name: str,
        host_verifier: str | HostVerifier,
        embedding_kind: str | SemanticEmbeddingKind,
        description: str = "",
        native_language: str = "",
        source_uri: str = "",
        source_commit: str = "",
        trust_policy: str = "",
        ontology_summary: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        host_logic: str = "",
        object_logic: str = "",
        object_theory: str = "",
        artifact_risk: str = "UNKNOWN",
        proof_transport_status: str = "NOT_ATTEMPTED",
        default_denotation_policy: str = "",
        default_type_system: str = "",
        default_identity_policy: str = "",
        default_hyperintensional_identity_policy: str = "",
        extensional_collapse_policy: str = "NEVER_BY_DEFAULT",
        workbench_id: str = "",
        workbench_layer: str = "",
        lifecycle_status: str = "",
        embedding_strategy: str = "",
        faithfulness_status: str = "",
        benchmark_status: str = "",
        default_formal_world_id: str = "",
        notes: str = "",
    ) -> "DomainKernel":
        return cls(
            kernel_id=make_kernel_id(name, source_uri, source_commit),
            name=name,
            description=description,
            native_language=native_language,
            host_verifier=_enum(host_verifier, HostVerifier, HostVerifier.OTHER),
            embedding_kind=_enum(
                embedding_kind, SemanticEmbeddingKind, SemanticEmbeddingKind.OTHER
            ),
            source_uri=source_uri,
            source_commit=source_commit,
            trust_policy=trust_policy,
            ontology_summary=list(ontology_summary or []),
            metadata=dict(metadata or {}),
            host_logic=host_logic,
            object_logic=object_logic,
            object_theory=object_theory,
            artifact_risk=artifact_risk,
            proof_transport_status=proof_transport_status,
            default_denotation_policy=default_denotation_policy,
            default_type_system=default_type_system,
            default_identity_policy=default_identity_policy,
            default_hyperintensional_identity_policy=default_hyperintensional_identity_policy,
            extensional_collapse_policy=extensional_collapse_policy,
            workbench_id=workbench_id,
            workbench_layer=workbench_layer,
            lifecycle_status=lifecycle_status,
            embedding_strategy=embedding_strategy,
            faithfulness_status=faithfulness_status,
            benchmark_status=benchmark_status,
            default_formal_world_id=default_formal_world_id,
            notes=notes,
        )

    def validate(self) -> "DomainKernel":
        if not self.kernel_id:
            raise ValueError("DomainKernel requires kernel_id")
        if not self.name:
            raise ValueError("DomainKernel requires name")
        return self

    @property
    def stable_id(self) -> str:
        return self.kernel_id

    def to_dict(self) -> dict[str, Any]:
        return {
            "kernel_id": self.kernel_id,
            "name": self.name,
            "description": self.description,
            "native_language": self.native_language,
            "host_verifier": self.host_verifier.value,
            "embedding_kind": self.embedding_kind.value,
            "source_uri": self.source_uri,
            "source_commit": self.source_commit,
            "trust_policy": self.trust_policy,
            "ontology_summary": list(self.ontology_summary),
            "metadata": dict(self.metadata),
            "host_logic": self.host_logic,
            "object_logic": self.object_logic,
            "object_theory": self.object_theory,
            "artifact_risk": self.artifact_risk,
            "proof_transport_status": self.proof_transport_status,
            "default_denotation_policy": self.default_denotation_policy,
            "default_type_system": self.default_type_system,
            "default_identity_policy": self.default_identity_policy,
            "default_hyperintensional_identity_policy": self.default_hyperintensional_identity_policy,
            "extensional_collapse_policy": self.extensional_collapse_policy,
            "workbench_id": self.workbench_id,
            "workbench_layer": self.workbench_layer,
            "lifecycle_status": self.lifecycle_status,
            "embedding_strategy": self.embedding_strategy,
            "faithfulness_status": self.faithfulness_status,
            "benchmark_status": self.benchmark_status,
            "default_formal_world_id": self.default_formal_world_id,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DomainKernel":
        kernel = cls(
            kernel_id=str(
                data.get("kernel_id")
                or make_kernel_id(
                    str(data.get("name", "")),
                    str(data.get("source_uri", "")),
                    str(data.get("source_commit", "")),
                )
            ),
            name=str(data.get("name", "")),
            description=str(data.get("description", "")),
            native_language=str(data.get("native_language", "")),
            host_verifier=_enum(data.get("host_verifier"), HostVerifier, HostVerifier.OTHER),
            embedding_kind=_enum(
                data.get("embedding_kind"),
                SemanticEmbeddingKind,
                SemanticEmbeddingKind.OTHER,
            ),
            source_uri=str(data.get("source_uri", "")),
            source_commit=str(data.get("source_commit", "")),
            trust_policy=str(data.get("trust_policy", "")),
            ontology_summary=[str(item) for item in data.get("ontology_summary", [])],
            metadata=dict(data.get("metadata", {})),
            host_logic=str(data.get("host_logic", "")),
            object_logic=str(data.get("object_logic", "")),
            object_theory=str(data.get("object_theory", "")),
            artifact_risk=str(data.get("artifact_risk", "UNKNOWN")),
            proof_transport_status=str(data.get("proof_transport_status", "NOT_ATTEMPTED")),
            default_denotation_policy=str(data.get("default_denotation_policy", "")),
            default_type_system=str(data.get("default_type_system", "")),
            default_identity_policy=str(data.get("default_identity_policy", "")),
            default_hyperintensional_identity_policy=str(
                data.get("default_hyperintensional_identity_policy", "")
            ),
            extensional_collapse_policy=str(data.get("extensional_collapse_policy", "NEVER_BY_DEFAULT")),
            workbench_id=str(data.get("workbench_id", "")),
            workbench_layer=str(data.get("workbench_layer", "")),
            lifecycle_status=str(data.get("lifecycle_status", "")),
            embedding_strategy=str(data.get("embedding_strategy", "")),
            faithfulness_status=str(data.get("faithfulness_status", "")),
            benchmark_status=str(data.get("benchmark_status", "")),
            default_formal_world_id=str(data.get("default_formal_world_id", "")),
            notes=str(data.get("notes", "")),
        )
        return kernel.validate()


@dataclass(frozen=True)
class SemanticEmbedding:
    embedding_id: str
    domain_kernel_id: str
    source_logic: str
    target_logic: str
    host_verifier: HostVerifier
    embedding_kind: SemanticEmbeddingKind
    description: str = ""
    soundness_status: str = "metadata_only"
    artifact_uri: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "embedding_id": self.embedding_id,
            "domain_kernel_id": self.domain_kernel_id,
            "source_logic": self.source_logic,
            "target_logic": self.target_logic,
            "host_verifier": self.host_verifier.value,
            "embedding_kind": self.embedding_kind.value,
            "description": self.description,
            "soundness_status": self.soundness_status,
            "artifact_uri": self.artifact_uri,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SemanticEmbedding":
        payload = dict(data)
        embedding_id = str(payload.get("embedding_id") or content_id("semantic_embedding", payload))
        return cls(
            embedding_id=embedding_id,
            domain_kernel_id=str(payload.get("domain_kernel_id", "")),
            source_logic=str(payload.get("source_logic", "")),
            target_logic=str(payload.get("target_logic", "")),
            host_verifier=_enum(payload.get("host_verifier"), HostVerifier, HostVerifier.OTHER),
            embedding_kind=_enum(
                payload.get("embedding_kind"),
                SemanticEmbeddingKind,
                SemanticEmbeddingKind.OTHER,
            ),
            description=str(payload.get("description", "")),
            soundness_status=str(payload.get("soundness_status", "metadata_only")),
            artifact_uri=str(payload.get("artifact_uri", "")),
            metadata=dict(payload.get("metadata", {})),
        )


@dataclass(frozen=True)
class ImportedTheoryObject:
    object_id: str
    domain_kernel_id: str
    kind: TheoryObjectKind
    name: str
    statement: str = ""
    source_file: str = ""
    source_line: int | None = None
    trust_level: TrustLevel = TrustLevel.CANDIDATE_CERTIFICATE
    provenance_type: ProvenanceType = ProvenanceType.IMPORTED
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "object_id": self.object_id,
            "domain_kernel_id": self.domain_kernel_id,
            "kind": self.kind.value,
            "name": self.name,
            "statement": self.statement,
            "source_file": self.source_file,
            "source_line": self.source_line,
            "trust_level": self.trust_level.value,
            "provenance_type": self.provenance_type.value,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ImportedTheoryObject":
        payload = dict(data)
        return cls(
            object_id=str(payload.get("object_id") or content_id("theory_object", payload)),
            domain_kernel_id=str(payload.get("domain_kernel_id", "")),
            kind=_enum(payload.get("kind"), TheoryObjectKind, TheoryObjectKind.OTHER),
            name=str(payload.get("name", "")),
            statement=str(payload.get("statement", "")),
            source_file=str(payload.get("source_file", "")),
            source_line=_optional_int(payload.get("source_line")),
            trust_level=trust_level(payload.get("trust_level"), TrustLevel.CANDIDATE_CERTIFICATE),
            provenance_type=provenance_type(payload.get("provenance_type")),
            metadata=dict(payload.get("metadata", {})),
        )


@dataclass(frozen=True)
class ImportedTheoryRelation:
    relation_id: str
    domain_kernel_id: str
    source_object_id: str
    target_object_id: str
    relation_kind: TheoryRelationKind
    trust_level: TrustLevel = TrustLevel.ADVISORY_ROUTE
    provenance_type: ProvenanceType = ProvenanceType.IMPORTED
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "relation_id": self.relation_id,
            "domain_kernel_id": self.domain_kernel_id,
            "source_object_id": self.source_object_id,
            "target_object_id": self.target_object_id,
            "relation_kind": self.relation_kind.value,
            "trust_level": self.trust_level.value,
            "provenance_type": self.provenance_type.value,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ImportedTheoryRelation":
        payload = dict(data)
        return cls(
            relation_id=str(payload.get("relation_id") or content_id("theory_relation", payload)),
            domain_kernel_id=str(payload.get("domain_kernel_id", "")),
            source_object_id=str(payload.get("source_object_id", "")),
            target_object_id=str(payload.get("target_object_id", "")),
            relation_kind=_enum(
                payload.get("relation_kind"),
                TheoryRelationKind,
                TheoryRelationKind.OTHER,
            ),
            trust_level=trust_level(payload.get("trust_level")),
            provenance_type=provenance_type(payload.get("provenance_type")),
            metadata=dict(payload.get("metadata", {})),
        )


def make_external_theory_domain_kernel(source_commit: str = "") -> DomainKernel:
    return DomainKernel(
        kernel_id="aot",
        name="External theory kernel",
        description=(
            "Metadata registration for an external Isabelle formalization. "
            "Registration is not "
            "itself proof import or verification."
        ),
        native_language="external Isabelle theories",
        host_verifier=HostVerifier.ISABELLE_HOL,
        embedding_kind=SemanticEmbeddingKind.SHALLOW_SEMANTIC_EMBEDDING,
        source_uri="",
        source_commit=source_commit,
        trust_policy=(
            "Proof authority remains with Isabelle/HOL and explicitly imported "
            "checked artifacts; this DomainKernel row is advisory metadata."
        ),
        ontology_summary=[
            "ordinary objects",
            "abstract objects",
            "properties",
            "propositions",
            "possible worlds",
            "encoding",
            "exemplification",
            "theorem objects",
            "definitions",
            "axioms",
        ],
        metadata={
            "formal_world": "computational_metaphysics",
            "truth_boundary": "metadata_only_until_proof_artifacts_are_imported",
        },
        host_logic="Isabelle/HOL",
        object_logic="external object logic",
        object_theory="external theory",
        artifact_risk="UNKNOWN",
        proof_transport_status="NOT_ATTEMPTED",
        default_type_system="relational_type_theory",
        default_denotation_policy="negative_free_logic_guarded",
        default_identity_policy="abstract_identity_by_encoded_properties",
        default_hyperintensional_identity_policy="ENCODED_PROPERTIES",
        extensional_collapse_policy="NEVER_BY_DEFAULT",
        workbench_id="workbench_logikey_style",
        workbench_layer="L1_LOGIC_AND_EMBEDDINGS",
        lifecycle_status="SEMANTICS_SELECTED",
        embedding_strategy="SHALLOW_SEMANTIC_EMBEDDING",
        faithfulness_status="UNKNOWN",
        benchmark_status="UNKNOWN",
        default_formal_world_id="formal_world_aot_precedent",
        notes=(
            "External-theory metadata preset: encoding/exemplification, abstract vs ordinary "
            "objects, canonical descriptions, shallow semantic embedding precedent, "
            "artifact theorem risk, denotation guardrails for complex terms, "
            "hyperintensional identity, no "
            "Isabelle import yet."
        ),
    )


def make_aot_domain_kernel(source_commit: str = "") -> DomainKernel:
    """Legacy internal alias; use ``make_external_theory_domain_kernel`` publicly."""

    return make_external_theory_domain_kernel(source_commit)


def make_etp_domain_kernel(source_commit: str = "") -> DomainKernel:
    return DomainKernel(
        kernel_id="etp_magma",
        name="Equational Theories Project Magma Fragment",
        description="Native MathGraph nursery for magma equational implication.",
        native_language="SAIR/ETP magma equations",
        host_verifier=HostVerifier.PYTHON_FINITE_CHECKER,
        embedding_kind=SemanticEmbeddingKind.DIRECT_NATIVE,
        source_uri="",
        source_commit=source_commit,
        trust_policy="Finite refutation authority comes from exact finite table checking.",
        ontology_summary=["equations", "magma operation", "implication claims", "finite tables", "witness assignments"],
        metadata={"truth_boundary": "finite_search_failure_is_not_proof"},
        host_logic="Python finite table checker / optional Lean",
        object_logic="universal equational logic over magmas",
        object_theory="ETP magma implication fragment",
        artifact_risk="LOW",
        proof_transport_status="NOT_APPLICABLE",
        default_type_system="single binary operation magma language",
        default_denotation_policy="all parsed core equations denote unless parser fails",
        default_identity_policy="equation_id_and_normalized_syntax",
        default_hyperintensional_identity_policy="NORMALIZED_SYNTAX",
        extensional_collapse_policy="ALLOW_IF_VERIFIED_EQUIVALENCE",
        workbench_id="workbench_mathgraph_default",
        workbench_layer="L3_APPLICATION_SCENARIOS",
        lifecycle_status="BENCHMARKED",
        embedding_strategy="NATIVE_KERNEL",
        faithfulness_status="NOT_APPLICABLE",
        benchmark_status="ETP_MATRIX_AVAILABLE",
        default_formal_world_id="formal_world_etp_magma",
        notes=(
            "Native finite-checker metadata for the SAIR/ETP algebraic nursery. "
            "The matrix is benchmark/evaluation data, not proof; Lean proof side remains future."
        ),
    )


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
