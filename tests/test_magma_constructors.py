from mathgraph.magma_constructors import build_base_constructor_bank, build_random_constructor_bank, dedupe_constructors


def test_base_constructor_bank_is_deterministic_and_nonempty():
    first = build_base_constructor_bank(max_n=3, seed=7)
    second = build_base_constructor_bank(max_n=3, seed=7)

    assert first
    assert [m.cid for m in first] == [m.cid for m in second]
    assert {"constant", "left_projection", "right_projection", "add_mod", "sub_mod"} <= {m.family for m in first}


def test_random_constructor_bank_is_seeded():
    a = build_random_constructor_bank(max_n=3, count_per_n=2, seed=11)
    b = build_random_constructor_bank(max_n=3, count_per_n=2, seed=11)
    c = build_random_constructor_bank(max_n=3, count_per_n=2, seed=12)

    assert [m.table_hash for m in a] == [m.table_hash for m in b]
    assert [m.table_hash for m in a] != [m.table_hash for m in c]


def test_dedupe_constructors_removes_same_table_carrier():
    bank = build_base_constructor_bank(max_n=2, seed=1)
    doubled = bank + bank

    assert len(dedupe_constructors(doubled)) == len(bank)
