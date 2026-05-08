# Root Discovery Architecture

Root discovery is not table search.

MathGraph treats root nodes as persistent, load-bearing continuation points
revealed when obstruction-constrained search produces reusable certificates
across a sharp SAT/UNSAT boundary. A frequent table, a successful route, or a
large motif is not enough by itself.

Compact doctrine:

```text
Root nodes are SAT-clusters carved out by UNSAT boundaries.
```

Operational doctrine:

```text
Do not search for models.
Search for the smallest obstruction surface where models suddenly become reusable.
```

## Telemetry Is The Substrate

The distiller consumes completion telemetry, not terminal truth:

- SAT rows show where continuation exists.
- UNSAT rows show where continuation is blocked.
- UNKNOWN and TIMEOUT rows show where the frontier needs pressure.
- ERROR rows preserve failed route evidence instead of hiding it.
- Table reuse, witness reuse, source bursts, target-demand patterns, carrier
  order boundaries, replay gain, derived amplification, and residual
  compression all contribute to candidate scoring.

Residuals are pressure fields, not leftovers.

## Narrow Completion

The intended completion loop is:

1. Select one named obstruction surface.
2. Build only pairs matching that obstruction.
3. Encode the source law universally over a finite carrier.
4. Encode target failure through an existential separating witness.
5. Treat the operation as symbolic.
6. Use a solver or completer only inside that narrow hypothesis.
7. Preserve SAT, UNSAT, UNKNOWN, TIMEOUT, and ERROR telemetry.
8. Distill candidates from the contrast.

Solvers are narrow completers, not truth authorities. A solver result can create
candidate pressure, but only verifier/importer boundaries can promote terminal
claims.

## Discovery Outputs

`mathgraph.root_discovery` emits advisory artifacts:

- `RootCandidate`
- `ObstructionCandidate`
- `ConstructorFamilyCard`
- replay queue rows
- summary telemetry

These objects are lawbook-adjacent discovery artifacts. They are not
`VERIFIED_PROOF`, `REFUTATION_CERTIFICATE`, or `NAMED_OBSTRUCTION` terminal
claims.

The module includes adapters to existing `RootNode` and `ObstructionNode`
schemas, but the resulting records remain candidates until backed by verified
certificate families.

The next consolidation layer is:

```text
completion telemetry
-> persistent filtration
-> shadow collapse
-> effective filtration count
-> advisory root promotion
-> root compiler
-> constructor family plan
-> replay/elevation
```

See [Root Node Discovery Doctrine](root_node_discovery_doctrine.md),
[Persistent Filtration](persistent_filtration.md),
[Shadow Collapse](shadow_collapse.md), and [Root Compiler](root_compiler.md).

## Verifier Boundary

Root discovery does not change the terminal contract.

Only importer-revalidated finite countermodels, chain-audited derived
certificates, or formal verification can cross the truth boundary. Failed
completion telemetry is valuable, but it remains scheduling and discovery
pressure.
