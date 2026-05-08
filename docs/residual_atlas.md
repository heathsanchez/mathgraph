# Residual Atlas v1

Residuals are membranes, not backlog.

The Residual Atlas records the structured boundary left after current
constructors, routes, certificates, replay pressure, and route policy have acted.
It is advisory: residual classification never verifies or refutes a claim.

## Purpose

The atlas answers:

- which pairs remain unresolved;
- which obstruction or root basin they appear to belong to;
- which routes failed or nearly worked;
- which cases are high-pressure next tasks;
- which regions are saturated and should become named obstruction pressure;
- which clusters are candidates for representation change.

## Case Schema

Each `ResidualCase` records source/target identity, status, root and obstruction
labels, constructor family, route key, attempt/failure/near-miss counts,
H-tilt priority from Route Policy v2, membrane pressure, saturation score,
representation-shift score, and next action.

## Cluster Schema

`ResidualCluster` groups cases deterministically by:

```text
(root_label, obstruction_label, constructor_family)
```

Fallback labels keep unclassified residuals visible instead of dropping them.

## Scoring

`membrane_pressure` combines attempt pressure, failure pressure, near-miss
pressure, and route-policy priority.

`saturation_score` rises when many attempts fail and near-miss signal is low.

`representation_shift_score` rises when membrane pressure and saturation are
both high or repeated obstruction pressure appears.

## Next Actions

- `schedule_next_attempt`
- `name_obstruction`
- `seek_representation_shift`
- `suppress_saturated_region`
- `hold`

## Trust Boundary

Residual atlas output is scheduling and discovery pressure only. Failed search
is not proof. A near miss is not a certificate. Terminal truth still requires
verified proof, finite refutation/importer revalidation, or named obstruction
under the existing terminal contract.

## Frontier v2

Frontier Builder v2 consumes Residual Atlas cases and clusters to produce the
next prioritized task frontier. This keeps the next episode aligned with the
membrane instead of restarting from a flat backlog.
