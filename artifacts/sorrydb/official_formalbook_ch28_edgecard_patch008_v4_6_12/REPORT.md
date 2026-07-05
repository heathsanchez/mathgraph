# SorryDB v4.6.12 — FormalBook EdgeCard Patch008

- status: PATCH008_REJECTED_OR_DIAGNOSTIC
- accepted_variant: None

## Key repair

`Sym2.ind` leaves `he : s(a,b) ∈ G.edgeFinset`; run `simp at he` to obtain adjacency, then use looplessness plus explicit finset-pair cardinality.

## Variant summary
- v01_simp_he_manual_pair: rc=1, seconds=42.91, error=True, sorry=False
- v02_simp_he_manual_pair_ne_symm: rc=1, seconds=53.33, error=True, sorry=False
- v03_simp_he_insert_card: rc=1, seconds=51.24, error=True, sorry=False
- v04_trace_after_simp_he: rc=0, seconds=54.98, error=False, sorry=True