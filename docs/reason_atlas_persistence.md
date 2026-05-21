# Reason Atlas Persistence

The Reason Atlas is MathGraph's persistent advisory memory for reusable
reasoning structure. It is not the Lawbook.

The Lawbook owns terminal truth. The Reason Atlas remembers constructor hints,
contact laws, root operator schemas, repair obstructions, transfer statistics,
deletion tests, and scheduler priors that can make the next verifier attempt
sharper.

## Stored Entries

`mathgraph.reason_atlas_store` persists advisory entries such as:

- promoted route laws
- strict contact seeds
- visibility contacts
- repairable obstructions
- root operator schemas
- root operator instances
- constructor hints
- scheduler priors
- named advisory obstructions

All entries default to `advisory_only=True` and `verifier_promoted=False`.

## Feedback

`mathgraph.schema_feedback` updates scores from later evidence:

- transfer success/failure
- verifier success/failure feedback
- obstruction found
- residual compressed/expanded
- deletion hurt/safe
- duplicate or superseded entries

These events change support, transfer rates, obstruction penalties, residual
compression totals, priority scores, and decay. They do not create proof,
countermodel, or truth certificates.

## Feedback Loop

`mathgraph.reason_atlas_feedback_loop` orchestrates:

```text
ingest advisory entries
→ record feedback
→ rescore
→ export next advisory tasks
```

Next queue rows include `TRANSFER_TEST`, `REPAIR_TEST`, `SCHEMA_EXPANSION`,
`DELETION_TEST`, `OBSTRUCTION_SPLIT`, and `VERIFIER_ATTEMPT`-style advisory
tasks.

## Boundary

Reason Atlas entries are not certificates. Promotion is advisory. Transfer
success is not proof. A verifier-success feedback event can raise priority, but
the terminal truth artifact must live behind a proper verifier, trusted
importer, finite checker, or chain audit boundary.

This layer connects:

- Root Operator Induction
- Reason Atlas Contact Promotion
- Closed Verification Loop
- H-Tilt scheduling
- Root Node Atlas
- Abstraction Formation Law
- MathGraph as a generative verification kernel

## Smoke

```bash
python scripts/run_reason_atlas_persistence_smoke.py
```

Outputs:

```text
/tmp/mathgraph_reason_atlas_persistence_smoke/reason_atlas_store.sqlite
/tmp/mathgraph_reason_atlas_persistence_smoke/reason_atlas_entries.jsonl
/tmp/mathgraph_reason_atlas_persistence_smoke/next_queue_rows.jsonl
/tmp/mathgraph_reason_atlas_persistence_smoke/summary.json
```

## Future Work

- full ClosedVerificationLoop over real verifier jobs
- H-Tilt scheduling over persistent schema families
- finite countermodel root induction
- proof-constructor root induction
- second-order root operators
- schema composition algebra
- principled V discovery
- causal IR
- grounding IR
- multi-verifier ExternalCertificate envelope
- Lean/Coq/Isabelle trace anti-unification
