# Reason Atlas Contact Promotion

Reason Atlas contact promotion turns raw Lean/mathlib probe rows into a
disciplined, advisory learning pipeline:

```text
STRICT_CONTACT_SEED
→ SIGNATURE_ATLAS_RECORD
→ REPAIRABLE_OBSTRUCTION
→ TRANSFER_TEST
→ PROMOTED_ROUTE_LAW
→ NEXT_EXPANSION_QUEUE
```

## Contact Seeds Are Not Route Laws

A single clean Lean contact is useful, but it is only a seed. It says that one
generated declaration interval was structurally valid, markers were present, no
mapped Lean errors appeared inside the interval, and the run did not hit an
operational timeout.

That is not enough evidence for a reusable route law.

By default, MathGraph promotes a route law only after repeated clean transfer:

- at least one strict contact seed
- at least two transfer successes
- at least three total clean successes
- no dirty intervals among promoted examples
- failure rate at or below `0.20`
- at least two distinct declarations or target instantiations
- not visibility-only

## Signature Atlas

`mathgraph.signature_atlas` records rough declaration signatures from `#check`
style text. The parser is deliberately heuristic. It captures useful shape
features such as namespace, theorem-like return type, binder counts, typeclass
requirements, and whether a declaration might be an exact-term candidate.

These records are structure for routing and scheduling, not proof evidence.

## Repairable Obstructions

Dirty contacts and failed probe attempts become `REPAIRABLE_OBSTRUCTION`
records. Common failure classes include:

- `unknown_constant_or_identifier`
- `type_mismatch`
- `function_expected`
- `parse_or_command_boundary_error`
- `synthesis_failure`
- `resource_limit`
- `marker_missing`
- `timeout`

Failed constructor or contact attempts are obstruction traces, not mathematical
disproofs.

## Transfer Tests And Route Laws

`TRANSFER_TEST` rows ask MathGraph to try a clean contact strategy on nearby
compatible declarations. A `PROMOTED_ROUTE_LAW` appears only after repeated
clean transfer. Route laws guide scheduling and constructor attempts; they are
advisory and are not terminal-form certificates.

## Verifier Boundary

Advisory objects cannot promote truth. Contact seeds, visibility contacts,
signature records, route priors, and promoted route laws do not become accepted
claims without explicit verifier, importer, finite-validator, or chain-audit
boundary evidence.

## Running The Smoke Scripts

```bash
python scripts/run_contact_promotion_smoke.py
python scripts/run_reason_atlas_import_smoke.py
```

The first script writes synthetic artifacts to
`/tmp/mathgraph_contact_promotion_smoke/`. The second script can also import
CSV rows:

```bash
python scripts/run_reason_atlas_import_smoke.py \
  --probe-results path/to/probe_results.csv \
  --declarations path/to/declarations.csv \
  --out-dir /tmp/mathgraph_reason_atlas_import_smoke
```

## Connection To Closed Loop And Route Priors

Promoted route laws and next-queue rows feed the control plane: the
`ClosedVerificationLoop` can schedule transfer and repair work, while
`RoutePriors` can treat repeated clean contact as advisory scheduling pressure.
Neither component promotes truth on its own.
