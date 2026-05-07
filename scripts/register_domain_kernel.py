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
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True)
    parser.add_argument("--preset", choices=["aot"])
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
    args = parser.parse_args(argv)

    metadata = json.loads(args.metadata_json) if args.metadata_json else {}
    if args.preset == "aot":
        kernel = make_aot_domain_kernel(args.source_commit)
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
        payload = {
            "status": "registered",
            "kernel_id": kernel.kernel_id,
            "name": kernel.name,
            "host_verifier": kernel.host_verifier.value,
            "embedding_kind": kernel.embedding_kind.value,
            "source_uri": kernel.source_uri,
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


if __name__ == "__main__":
    raise SystemExit(main())
