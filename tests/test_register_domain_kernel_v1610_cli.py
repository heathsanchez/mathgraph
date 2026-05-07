import json
import subprocess
import sys

from mathgraph.lawbook_store import LawbookStore


def test_register_domain_kernel_presets_create_v1610_metadata(tmp_path):
    db = tmp_path / "lawbook.sqlite"
    for preset in ("aot", "etp"):
        result = subprocess.run(
            [sys.executable, "scripts/register_domain_kernel.py", "--db", str(db), "--preset", preset],
            check=True,
            text=True,
            capture_output=True,
        )
        payload = json.loads(result.stdout)
        assert payload["status"] == "registered"
        assert payload["extras"]["fragments"] == 1
        assert payload["extras"]["embeddings"] == 1
        assert payload["extras"]["formal_worlds"] == 1

    store = LawbookStore(db)
    try:
        assert len(store.list_domain_kernels()) == 2
        assert len(store.list_semantic_embeddings()) == 2
        assert len(store.list_language_fragments()) == 2
        assert len(store.list_formal_worlds()) == 2
        assert len(store.list_paradox_guards()) >= 3
    finally:
        store.close()

    for flag in ("--domain-kernels", "--semantic-embeddings", "--language-fragments", "--formal-worlds", "--paradox-guards"):
        result = subprocess.run(
            [sys.executable, "scripts/query_lawbook.py", "--db", str(db), flag],
            check=True,
            text=True,
            capture_output=True,
        )
        assert json.loads(result.stdout) is not None
