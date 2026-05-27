# CrossWorld v2 Semantic Residual Invariant

Canonical evidence pack:
`examples/evidence_packs/cross_world_semantic_residual_invariant/`

## What This Proves

This artifact-backed CrossWorld v2 run supports an empirical invariant
candidate across four formal worlds: ETP magma implication, Boolean CNF
implication, finite graph-property implication, and rewrite/string-rule
implication.

The supported measurement principle is
`semantic_residual_independence_after_source_closure`:

```text
TRUE  = target demand is absorbed by source closure.
FALSE = independent target-violating residue survives inside the source model set.
```

In finite-world form:

```text
A => B is TRUE  iff M(A) intersection not M(B) is empty.
A => B is FALSE iff M(A) intersection not M(B) is nonempty.
```

## What This Does Not Prove

This is not a formal theorem over all mathematics and not a truth oracle.
Residual scores, rank scores, root signatures, and route scores are advisory
only. A terminal FALSE certificate still requires a finite checked witness or a
verifier-backed refutation. A terminal TRUE certificate still requires a
verified proof, Lean artifact, or accepted verifier proof route.

Absorbed or rank-zero results are proof-route candidate only unless verified.
Failed finite search is not TRUE. The 73 ETP false-underexplained rows are a
named residual frontier, not errors and not TRUE claims.

## Why This Matters

The run reports:

- `semantic_root_all_world_auc_false`: `0.9933195438173603`
- `residual_rank_all_world_auc_false`: `0.9969114909460145`
- `leave_one_world_out_mean_auc_false`: `0.9837976420735745`
- `etp_semantic_root_auc_false`: `0.97914248`
- combined rows: `16,156`
- combined FALSE rows: `11,818`
- combined TRUE rows: `4,338`
- worlds: `BOOLEAN`, `ETP`, `GRAPH`, `REWRITE`
- top shared feature: `near_force_score`
- best abstract root signature:
  `residual_escape|gap_extreme|rank_very_high|source_large|absorption_low`

The raw run fields `root_level_candidate=false` and
`breakthrough_shaped=false` are preserved. They are not rewritten. They mean the
script did not find one discrete root signature that dominated across worlds
under its threshold. The broader supported object is the measurement principle:
absorption versus surviving independent residue after source closure.

The proof ledger summary preserves:

- explained FALSE: `11,745`
- explained TRUE: `4,338`
- FALSE underexplained: `73`

For ETP specifically:

- explained FALSE: `2,427 / 2,500`
- explained TRUE: `2,500 / 2,500`
- false-underexplained frontier: `73 / 2,500`

## Next Constructive Step

The next step is semantic residual to certificate extraction:

```text
claim
-> source closure
-> target residual extraction
-> residual rank
-> proof route / countermodel route / named obstruction
```

Rows with visible residue should drive finite witness extraction and
source-holds / target-violates checking. Absorbed rows should become proof-route
candidates and remain unverified until proof verification. The 73 ETP
false-underexplained rows should drive semantic-universe expansion and
minimum-carrier search because they are frontier rows where the current witness
universe did not expose the official FALSE residue.

## Artifact Policy

The pack follows Manifest Small. Small high-signal summary, report, proof
sketch, transfer, feature, world, root, proof-ledger, compression, and lawbook
CSV/MD/JSON artifacts are committed. Bulky raw claim-feature tables, world
feature tables, the SQLite ledger, magma table bank, and NPY satisfaction matrix
are recorded in the manifest but not committed.

## Producer Script Provenance

The uploaded artifacts were produced by the conversation-provided
`MATHGRAPH CROSSWORLD v2 -- SEMANTIC RESIDUAL INDEPENDENCE RANK TEST` script.
That script is recorded as provenance for the artifact bundle only. It is not
committed as a repo runner and this integration does not add a new algorithmic
system.
