"""Tiny LawbookStore warehouse demo."""

from __future__ import annotations

import tempfile
from pathlib import Path

from mathgraph import LawbookStore, RootNode


def main() -> None:
    db_path = Path(tempfile.mkdtemp(prefix="mathgraph_lawbook_demo_")) / "lawbook.sqlite"
    store = LawbookStore(db_path)
    try:
        store.import_refutations(
            [
                {
                    "certificate_id": "demo_refutation",
                    "source_idx": 0,
                    "target_idx": 1,
                    "source": "x = x",
                    "target": "x = y",
                    "table_hash": "demo_table",
                    "table": [[0, 1], [1, 0]],
                    "witness": {"x": 0, "y": 1},
                    "verification_status": "FINITE_VERIFIED",
                }
            ]
        )
        store.import_roots(
            [RootNode.from_dict({"root_node_id": "r_demo", "canonical_name": "ROOT_PROJECTION_LEFT"})]
        )
        print(store.query_refutation(0, 1))
        print(store.explain_root("r_demo"))
        print(store.summary()["warehouse"])
    finally:
        store.close()


if __name__ == "__main__":
    main()
