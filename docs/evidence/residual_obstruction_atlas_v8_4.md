# Residual Obstruction Atlas v8.4

Canonical evidence pack:
`examples/evidence_packs/residual_obstruction_atlas_v8_4/`

## Metrics

- Official FALSE pairs: `13,855,357`
- Finite-covered FALSE: `13,794,206`
- Coverage: `99.558647%`
- Remaining frontier: `61,151`
- Source obstruction rows: `813`
- Target obstruction rows: `4,693`
- Motif classes: `28`
- Basin classes: `71`
- Top root node: `residue_zero|mixed_residual_geometry|source_ultra_specific|target_mid|near_equal`
- Top constructor pressure: `needs_new_semantic_universe_or_higher_carrier`
- Recommended next engine: `expand_semantic_bank_then_min_carrier_search`

## Principle

`RESIDUAL_ZERO_MEANS_INCOMPLETE_WITNESS_UNIVERSE`

Residual-zero frontier does not falsify semantic residual rank. It means the
current finite witness universe cannot see the residue. The correct next action
is semantic-universe expansion around source closure and minimum-carrier
source-model search.

Do not keep mutating stale winner tables blindly.

## Trust Boundary

The obstruction atlas is advisory constructor pressure. It names a residual
surface and recommends continuation, but it does not produce TRUE claims or
terminal FALSE certificates by itself.
