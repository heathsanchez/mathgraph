#!/usr/bin/env python
"""Register a formal-world DomainKernel in a MathGraph LawbookStore."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mathgraph import LawbookStore  # noqa: E402
from mathgraph.artifact_warehouse import register_domain_kernel_in_store  # noqa: E402
from mathgraph.domain_kernels import (  # noqa: E402
    DomainKernel,
    HostVerifier,
    SemanticEmbeddingKind,
    make_aot_domain_kernel,
    make_etp_domain_kernel,
)
from mathgraph.formal_worlds import aot_formal_world_precedent, etp_magma_formal_world  # noqa: E402
from mathgraph.language_fragments import aot_l23_precedent_fragment, etp_magma_equations_fragment  # noqa: E402
from mathgraph.paradox_guards import (  # noqa: E402
    aot_complex_term_guard,
    semantic_embedding_artifact_guard,
    set_collapse_guard,
)
from mathgraph.predication import PredicateKind, encodes  # noqa: E402
from mathgraph.semantic_embeddings import (  # noqa: E402
    ArtifactRisk,
    EmbeddingKind,
    ProofTransportStatus,
    SemanticEmbedding,
)
from mathgraph.types import TypedObject  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True)
    parser.add_argument("--preset", choices=["aot", "etp"])
    parser.add_argument("--name")
    parser.add_argument("--description", default="")
    parser.add_argument("--native-language", default="")
    parser.add_argument("--host-verifier", default=HostVerifier.OTHER.value)
    parser.add_argument("--embedding-kind", default=SemanticEmbeddingKind.OTHER.value)
    parser.add_argument("--source-uri", default="")
    parser.add_argument("--source-commit", default="")
    parser.add_argument("--trust-policy", default="")
    parser.add_argument("--ontology", action="append", default=[])
    parser.add_argument("--metadata-json", default=None)
    parser.add_argument("--with-fragment", action="store_true")
    parser.add_argument("--with-embedding", action="store_true")
    parser.add_argument("--with-formal-world", action="store_true")
    parser.add_argument("--with-paradox-guards", action="store_true")
    args = parser.parse_args(argv)

    metadata = json.loads(args.metadata_json) if args.metadata_json else {}
    if args.preset == "aot":
        kernel = make_aot_domain_kernel(args.source_commit)
    elif args.preset == "etp":
        kernel = make_etp_domain_kernel(args.source_commit)
    else:
        if not args.name:
            parser.error("--name is required without --preset")
        ontology = _ontology_items(args.ontology)
        kernel = DomainKernel.create(
            name=args.name,
            description=args.description,
            native_language=args.native_language,
            host_verifier=args.host_verifier,
            embedding_kind=args.embedding_kind,
            source_uri=args.source_uri,
            source_commit=args.source_commit,
            trust_policy=args.trust_policy,
            ontology_summary=ontology,
            metadata=metadata,
        )

    store = LawbookStore(args.db)
    try:
        result = register_domain_kernel_in_store(store, kernel)
        extras = _register_preset_extras(store, args.preset, args) if args.preset else {}
        payload = {
            "status": "registered",
            "kernel_id": kernel.kernel_id,
            "name": kernel.name,
            "host_verifier": kernel.host_verifier.value,
            "embedding_kind": kernel.embedding_kind.value,
            "source_uri": kernel.source_uri,
            "extras": extras,
            "truth_boundary": result["truth_boundary"],
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    finally:
        store.close()
    return 0


def _ontology_items(items: list[str]) -> list[str]:
    values: list[str] = []
    for item in items:
        values.extend(part.strip() for part in item.split(",") if part.strip())
    return values


def _register_preset_extras(store: LawbookStore, preset: str | None, args: argparse.Namespace) -> dict[str, int]:
    if not preset:
        return {}
    requested = {
        "fragment": args.with_fragment,
        "embedding": args.with_embedding,
        "formal_world": args.with_formal_world,
        "paradox_guards": args.with_paradox_guards,
    }
    register_all = not any(requested.values())
    extras = {"fragments": 0, "embeddings": 0, "formal_worlds": 0, "paradox_guards": 0}
    if preset == "aot":
        if register_all or requested["embedding"]:
            store.add_semantic_embedding(
                SemanticEmbedding(
                    embedding_id="embedding_aot_isabelle_shallow",
                    domain_kernel_id="aot",
                    formal_world_id="formal_world_aot_precedent",
                    embedding_kind=EmbeddingKind.SHALLOW_SEMANTIC_EMBEDDING,
                    host_logic="Isabelle/HOL",
                    object_logic="AOT / second-order modal object theory",
                    host_verifier="Isabelle/HOL",
                    object_theory="Abstract Object Theory",
                    artifact_risk=ArtifactRisk.UNKNOWN,
                    object_theory_verified=False,
                    host_embedding_verified=False,
                    proof_transport_status=ProofTransportStatus.NOT_ATTEMPTED,
                    notes="Metadata-only AOT shallow semantic embedding precedent; no Isabelle import yet.",
                )
            )
            extras["embeddings"] += 1
        if register_all or requested["fragment"]:
            store.add_language_fragment(aot_l23_precedent_fragment())
            extras["fragments"] += 1
        if register_all or requested["formal_world"]:
            world = aot_formal_world_precedent()
            store.add_formal_world(world)
            _register_world_objectification(store, world)
            extras["formal_worlds"] += 1
        if register_all or requested["paradox_guards"]:
            for guard in (aot_complex_term_guard(), semantic_embedding_artifact_guard(), set_collapse_guard()):
                store.add_paradox_guard(guard)
                extras["paradox_guards"] += 1
    elif preset == "etp":
        if register_all or requested["embedding"]:
            store.add_semantic_embedding(
                SemanticEmbedding(
                    embedding_id="embedding_etp_native_finite_checker",
                    domain_kernel_id="etp_magma",
                    formal_world_id="formal_world_etp_magma",
                    embedding_kind=EmbeddingKind.NATIVE_KERNEL,
                    host_logic="Python finite table checker / optional Lean",
                    object_logic="universal equational logic over magmas",
                    host_verifier="python finite checker",
                    object_theory="ETP magma implication fragment",
                    artifact_risk=ArtifactRisk.LOW,
                    object_theory_verified=True,
                    host_embedding_verified=True,
                    proof_transport_status=ProofTransportStatus.NOT_APPLICABLE,
                    notes="Native finite-checker metadata; finite search failure remains non-proof.",
                )
            )
            extras["embeddings"] += 1
        if register_all or requested["fragment"]:
            store.add_language_fragment(etp_magma_equations_fragment())
            extras["fragments"] += 1
        if register_all or requested["formal_world"]:
            world = etp_magma_formal_world()
            store.add_formal_world(world)
            _register_world_objectification(store, world)
            extras["formal_worlds"] += 1
    return extras


def _register_world_objectification(store: LawbookStore, world: object) -> None:
    data = world.to_dict() if hasattr(world, "to_dict") else dict(world)
    world_id = data["formal_world_id"]
    encoded = {
        "object_logic": data.get("object_logic", ""),
        "identity_policy": data.get("identity_policy", ""),
        "denotation_policy": data.get("denotation_policy", ""),
        "verifier_policy": data.get("verifier_policy", ""),
        "language_fragment_ids": data.get("language_fragment_ids", []),
        "semantic_embedding_ids": data.get("semantic_embedding_ids", []),
    }
    store.add_typed_object(
        TypedObject(
            object_id=world_id,
            type_expr="i",
            object_kind="FormalWorld",
            domain_kernel_id=data.get("domain_kernel_id"),
            formal_world_id=world_id,
            ordinary_or_abstract="ABSTRACT",
            identity_mode="THEORY_RELATIVE_DENOTATION",
            uniqueness_status="FAMILY_NAME_ONLY",
            label=data.get("name"),
            encoded_properties=encoded,
            payload={
                "truth_boundary": "FormalWorld metadata encodes context; it is not a proof object.",
            },
        )
    )
    for field, value in encoded.items():
        if value in (None, "", []):
            continue
        store.add_predication_fact(
            encodes(
                world_id,
                f"formal_world:{field}",
                predicate_kind=PredicateKind.OBJECTIFICATION_FEATURE,
                domain_kernel_id=data.get("domain_kernel_id"),
                formal_world_id=world_id,
                payload={"field": field, "value": value, "advisory_only": True},
            )
        )


if __name__ == "__main__":
    raise SystemExit(main())
