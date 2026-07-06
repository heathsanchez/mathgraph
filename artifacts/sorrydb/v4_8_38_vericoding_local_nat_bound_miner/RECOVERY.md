# v4.8.38R Recovery

The original v4.8.38 miner found useful vericoding local Nat/index-bound candidates, but the raw ranked scan was too large to push.

Recovery action:

- removed `ranked_bound_holes.json`;
- kept compact `candidate_bound_holes.json`;
- kept compact `watch_bound_holes.json`;
- kept `REPORT.md`.

Key result preserved:

- all sorry rows scanned: 30844
- candidate bound holes: 25
- watch bound holes: 510

Best next candidates after excluding already-certified LT0032/LT0479/LT0480:

- `specs/LT0056_specs.lean`: inline `arr.get ⟨part_idx.val * (n / k) + elem_idx.val, by sorry⟩`
- `specs/LT0341_specs.lean`: `List.range (i.val + 1)` index bounds
- `specs/LT0401_specs.lean`: Chebyshev 2D flattened index bound, same shape as LT0479
- `specs/LT0505_specs.lean`: Legendre 2D flattened index bound
- `specs/LT0506_specs.lean`: Legendre 3D flattened index bound, same shape as LT0480
