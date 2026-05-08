# Root Node Discovery Note: Obstruction-Surface Completion Distillation

## Key finding

A root node is discovered when a constrained residual surface produces reusable
certificates with high contrast against nearby failures.

Compact form:

```text
Root nodes are SAT-clusters carved out by UNSAT boundaries.
```

Operational form:

```text
Do not search for models.
Search for the smallest obstruction surface where models suddenly become reusable.
```

This note records the technique learned from the v16.34 closure-separation run:
finite countermodels became productive only after the search was narrowed to a
specific residual obstruction surface, encoded as a symbolic finite-operation
completion problem, and then distilled by source bursts, table reuse, witness
patterns, and SAT/UNSAT contrast.

This is not merely a solver trick. It is a MathGraph discovery law.

## Why this matters

MathGraph already separates truth authority from search pressure:

- verifiers decide truth;
- constructors produce candidate continuations;
- importers promote only revalidated certificates;
- obstructions record failed continuations;
- roots compress certificate-generating structure.

The missing methodological bridge is how roots are discovered from hard
residuals. The v16.34 lesson is that roots do not usually appear by broad table
generation. They appear when a failed residual field is narrowed until one
constraint surface becomes sharply productive.

A root is therefore not simply a frequent motif, a high-support table, or a good
route. A root is a persistent, load-bearing continuation point discovered at the
boundary between:

```text
nearby attempts that remain UNSAT / UNKNOWN
and a narrow basin that becomes SAT and certificate-reusable.
```

The contrast matters as much as the hits.

## The method

The reusable method is:

```text
1. Start from the current best residual mask.
2. Select one named obstruction surface, not the whole universe.
3. Build only pairs matching that obstruction.
4. Encode the source law universally over a finite carrier.
5. Encode target failure existentially through a separating witness.
6. Treat the finite operation itself as a symbolic unknown.
7. Run a narrow symbolic completer such as Z3.
8. Record SAT / UNSAT / UNKNOWN, not just successful certificates.
9. Group SAT rows by source, target demand, table hash, order, witness schema,
   source shape, target shape, and route.
10. Group UNSAT and UNKNOWN rows by the same features.
11. Score contrast: where does this route sharply work versus fail?
12. Promote high-contrast SAT clusters into root-node candidates.
13. Promote coherent UNSAT clusters into named obstructions or negative route
    evidence.
14. Replay candidate families against nearby residuals.
15. Only then turn a repeated pattern into a constructor family, route card,
    lawbook entry, or scheduler pressure update.
```

The important inversion is:

```text
Do not generate first and explain later.
Constrain first, complete narrowly, then distill what survived.
```

## Correct role of Z3 and other solvers

The solver is not the discovery engine. It is a narrow completer.

Correct use:

```text
source law     = universal finite constraint
operation      = symbolic unknown Op : Int x Int -> Int
target failure = existential separator / witness
solver         = completer of a named obstruction hypothesis
```

Incorrect use:

```text
throw broad pairs at Z3 and hope models appear
```

When a solver returns UNSAT on a narrow obstruction surface, that is not wasted.
It is obstruction data. It says that this route is blocked for a particular
source shape, target demand, carrier bound, or completion geometry. Those
negative boundaries help define the root just as much as the SAT hits.

## What counts as root evidence

A candidate root becomes interesting when several of these hold:

- one source produces a burst of certificates;
- one target-demand pattern appears repeatedly;
- a small set of table hashes explains many rows;
- witnesses share a common assignment or role pattern;
- the carrier order is stable or sharply bounded;
- nearby sources or targets are UNSAT / UNKNOWN under the same route;
- replay against neighboring residuals recovers additional certificates;
- derived closure amplifies the primitive certificates;
- the residual becomes smaller, sharper, more nameable, or more compressible.

The central score is not raw hit count. The central score is load-bearing
contrast:

```text
root_score = certificate_yield
           + table_reuse
           + source_burst
           + witness_schema_reuse
           + SAT/UNSAT contrast
           + replay gain
           + derived amplification
           + residual compression gain
           - broadness penalty
```

A high-support pattern with no boundary is only a cluster. A high-contrast
cluster that produces reusable certificates is a root candidate.

## What should be stored

For each obstruction-surface completion run, MathGraph should preserve both hits
and misses. A future root-discovery artifact should include at least:

```text
run_id
obstruction_surface_id
source_idx
target_idx
source_equation
target_equation
carrier_order
solver_status = SAT | UNSAT | UNKNOWN | ERROR
certificate_id
table_hash
table_json
witness_assignment
source_signature
target_signature
target_demand_signature
route
elapsed_sec
failure_reason
```

For promoted root candidates, store:

```text
root_node_id
canonical_name
root_type = symbolic_closure_separator_root | source_burst_root |
            table_reuse_root | witness_schema_root | obstruction_boundary_root
root_key
source_signature
target_demand_signature
table_hashes
orders
witness_schema
sat_count
unsat_count
unknown_count
attempt_count
hit_rate
table_reuse_score
source_burst_score
witness_reuse_score
sat_unsat_contrast
replay_gain
derived_amplification_factor
residual_compression_gain
load_bearing_score
status
```

Existing `RootNode`, `ReasonNode`, `ObstructionNode`, `tables`, `refutations`,
`certificates`, and route-policy surfaces can already carry most of this. The
missing layer is a distiller that turns completion-run telemetry into those
objects.

## Proposed module

A natural next module is:

```text
mathgraph/obstruction_surface_distiller.py
```

or:

```text
mathgraph/root_discovery.py
```

Its job:

```text
Input:
  completion result rows
  finite countermodel rows
  failed completion rows
  current residual mask / frontier metadata
  optional table registry

Output:
  RootNode candidates
  ReasonNode candidates
  ObstructionNode candidates
  route-policy updates
  replay queues
  constructor-family cards
```

The distiller should not promote truth. It should only create discovery objects
and scheduling pressure. Promotion still belongs to the verifier/importer
boundary.

## Design consequence for MathGraph

The main design consequence is that the root atlas should be generated from
contrastive episode telemetry, not only from successful certificates.

Current lawbook memory answers:

```text
What has already been verified?
```

Root discovery must answer:

```text
Where did a failed residual surface become certificate-productive?
Why there?
What boundary separates productive continuations from blocked ones?
Can that boundary be replayed as a constructor family?
```

This changes the meaning of residuals. Residuals are not leftovers. They are
pressure fields. A residual becomes valuable when it is split into named
subsurfaces whose SAT/UNSAT behavior is stable enough to generate roots,
obstructions, or route-negative evidence.

## Immediate study targets

From the v16.34 run, study first:

1. The strongest source burst.
   A source that yields many certificates under one obstruction surface should
   be treated as a root candidate before it is treated as a solved batch.

2. Repeated table hashes.
   A repeated table hash is a constructor fingerprint. If one table explains
   many pairs with coherent witnesses, it may be a reusable finite-magma
   constructor family.

3. Repeated witness schemas.
   A witness pattern explains the separator geometry. This is often closer to
   the reason than the table itself.

4. Zero-hit high-priority sources.
   They should become negative route basins or named obstructions, not ignored
   failures.

5. Carrier-order boundaries.
   If order 4 works for some sources and order 5 is needed for others, the
   order jump itself may identify a structural obstruction.

## Memory rule

When a MathGraph search stalls, do not broaden first.

Instead:

```text
1. Identify the surviving residual surface.
2. Name the obstruction hypothesis.
3. Build a narrow symbolic completion problem.
4. Preserve SAT, UNSAT, and UNKNOWN telemetry.
5. Distill high-contrast clusters into roots and obstructions.
6. Replay only the distilled family.
```

This is the practical root-node path.

## One-sentence doctrine

A MathGraph root node is a persistent, load-bearing continuation point revealed
when obstruction-constrained search produces reusable certificates across a
sharp SAT/UNSAT boundary.
