# Cross-World Semantic Residual Invariant

Canonical evidence pack:
`examples/evidence_packs/cross_world_semantic_residual_invariant/`

The uploaded bundle search did not include a matching raw artifact file for
this result. The pack preserves the metrics supplied in Documents 9-11 with
provenance marked as conversation-provided context.

## What This Proves

This pack preserves a conversation-provenance empirical claim: the semantic
residual representation reportedly transferred across ETP magma implication,
Boolean CNF implication, finite graph property implication, and rewrite/string
rule implication with high false-AUC metrics.

## What This Does Not Prove

This is not a verified artifact-backed proof. Until raw cross-world run
artifacts are added, the evidence status is conversation-provenance only.
Residual scores, classifier confidence, and failed finite searches cannot
promote terminal truth.

## Metrics

- `semantic_root_all_world_auc_false`: `0.9933`
- `residual_rank_all_world_auc_false`: `0.9969`
- `leave_one_world_out_mean_auc_false`: `0.9838`
- `ETP semantic_root_auc_false`: `0.9791`
- ETP false explained: `2427 / 2500`
- ETP true explained: `2500 / 2500`
- ETP false underexplained: `73 / 2500`

Worlds:

- ETP magma implication
- Boolean CNF implication
- finite graph property implication
- rewrite/string-rule implication

## Invariant

```text
SOURCE -> semantic closure / quotient / model set
TARGET -> demand region
```

`TRUE` means target demand is absorbed by source closure. `FALSE` means
target-violating residue survives inside the source model set. `HARD` means
residue exists but requires richer representation or constructor.

The 73 underexplained ETP rows are a residual frontier, not ordinary failure.
They point to missing carriers, missing constructor families, or subtler source
closure geometry.

## Trust Boundary

This is empirical cross-world transfer evidence, not proof. Residual scores,
classifier confidence, and failed finite searches cannot promote truth.
