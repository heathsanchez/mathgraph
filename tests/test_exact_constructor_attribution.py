import numpy as np
import pandas as pd

from mathgraph.exact_constructor_attribution import build_exact_constructor_attribution_frame, first_recovering_constructor_for_pair


def test_first_recovering_constructor_respects_route_order():
    pair_hits = np.array([True, True, False])
    assert first_recovering_constructor_for_pair(pair_hits, [1, 0]) == 1
    assert first_recovering_constructor_for_pair(pair_hits, [2]) is None


def test_build_exact_attribution_marks_lawbook_gain_constructor():
    matrix = np.array(
        [
            [True, False, False],
            [False, True, False],
        ],
        dtype=bool,
    )
    manifest = pd.DataFrame(
        [
            {"cid": "A", "family": "generic_family", "name": "a", "n": 2},
            {"cid": "B", "family": "lawbook_family", "name": "b", "n": 2},
            {"cid": "C", "family": "unused", "name": "c", "n": 2},
        ]
    )
    frame = build_exact_constructor_attribution_frame(
        [(0, 1), (0, 2)],
        matrix,
        manifest,
        {"generic": [0], "heldout_lawbook_guided": [0, 1]},
        seed=7,
    )

    assert frame.loc[0, "generic_first_constructor_id"] == "A"
    assert frame.loc[1, "heldout_lawbook_first_constructor_id"] == "B"
    assert frame.loc[1, "lawbook_gain_hit"] is True or bool(frame.loc[1, "lawbook_gain_hit"])
    assert frame.loc[1, "lawbook_gain_constructor_family"] == "lawbook_family"
    assert frame["exact_attribution_available"].all()
    assert not frame["can_promote_truth"].any()
