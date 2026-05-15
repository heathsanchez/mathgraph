import json
import subprocess
import sys

from mathgraph import LawbookStore


def test_register_domain_kernel_cli_aot_and_query(tmp_path):
    db = tmp_path / "lawbook.sqlite"
    result = subprocess.run(
        [sys.executable, "scripts/register_domain_kernel.py", "--db", str(db), "--preset", "aot"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["name"] == "External theory kernel"
    assert payload["host_verifier"] == "ISABELLE_HOL"
    store = LawbookStore(db)
    try:
        assert store.get_domain_kernel("External theory kernel") is not None
    finally:
        store.close()
    query = subprocess.run(
        [sys.executable, "scripts/query_lawbook.py", "--db", str(db), "--domain-kernels"],
        check=True,
        capture_output=True,
        text=True,
    )
    rows = json.loads(query.stdout)
    assert rows[0]["embedding_kind"] == "SHALLOW_SEMANTIC_EMBEDDING"
