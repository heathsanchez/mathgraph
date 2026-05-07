from mathgraph import LawbookStore, make_aot_domain_kernel


def test_lawbook_store_domain_kernel_registration(tmp_path):
    store = LawbookStore(tmp_path / "lawbook.sqlite")
    try:
        kernel = make_aot_domain_kernel()
        store.upsert_domain_kernel(kernel)
        by_id = store.get_domain_kernel(kernel.kernel_id)
        by_name = store.get_domain_kernel("Abstract Object Theory")
        assert by_id["host_verifier"] == "ISABELLE_HOL"
        assert by_name["kernel_id"] == kernel.kernel_id
        assert len(store.list_domain_kernels()) == 1
        summary = store.domain_kernel_summary()
        assert summary["domain_kernels"] == 1
        assert store.summary()["domain_kernels"]["domain_kernels"] == 1
    finally:
        store.close()
