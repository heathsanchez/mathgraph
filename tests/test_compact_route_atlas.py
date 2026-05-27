from mathgraph.compact_route_atlas import (
    CompactAtlasEntry,
    compare_random_controls,
    compare_shuffled_controls,
    make_same_size_random_control,
    make_shuffled_atlas_control,
    select_compact_atlas,
)


def test_select_compact_atlas_keeps_load_bearing_advisory_memory_only() -> None:
    entries = [
        CompactAtlasEntry("base", generation=0, load_bearing_score=100, unique_new_hits_vs_generic=10),
        CompactAtlasEntry("bad", generation=2, load_bearing_score=200, unique_new_hits_vs_generic=20, can_promote_truth=True),
        CompactAtlasEntry("weak", generation=2, load_bearing_score=50, unique_new_hits_vs_generic=0),
        CompactAtlasEntry("a", generation=1, load_bearing_score=8, unique_new_hits_vs_generic=4, first_hit_count=5),
        CompactAtlasEntry("b", generation=1, load_bearing_score=9, unique_new_hits_vs_generic=2, first_hit_count=10),
    ]

    selected = select_compact_atlas(entries, top_k=2)

    assert [entry.constructor_id for entry in selected] == ["b", "a"]
    assert all(entry.advisory_only and not entry.can_promote_truth for entry in selected)


def test_random_and_shuffled_controls_compare_mean_recoveries() -> None:
    compact = [10, 12, 11]

    assert compare_random_controls(compact, [7, 9, 8])["compact_gain_vs_random_same_size"] == 3
    assert compare_shuffled_controls(compact, [10, 9, 8])["compact_gain_vs_shuffled_atlas_same_size"] == 2


def test_same_size_control_builders_are_seeded_and_sized() -> None:
    ids = [f"c{i}" for i in range(10)]

    a = make_same_size_random_control(ids, compact_size=4, seed=1729, excluded_constructor_ids=("c0",))
    b = make_same_size_random_control(ids, compact_size=4, seed=1729, excluded_constructor_ids=("c0",))
    shuffled = make_shuffled_atlas_control(ids, compact_size=3, seed=42)

    assert a == b
    assert len(a) == 4
    assert "c0" not in a
    assert len(shuffled) == 3
