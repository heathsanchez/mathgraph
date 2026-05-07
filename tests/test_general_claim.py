from mathgraph import GeneralClaim


def test_general_claim_stable_hashing_and_normalization():
    left = GeneralClaim.create(" x  = x ", " y = y ", source_idx=1, target_idx=2)
    right = GeneralClaim.create("x = x", "y = y", source_idx=1, target_idx=2)
    assert left.claim_id == right.claim_id
    assert left.normalized_source == "x = x"
    assert GeneralClaim.from_dict(left.to_dict()).claim_id == left.claim_id
