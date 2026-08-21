# Residual Constraint Graph (RCG) v1

## Thesis

Verified failures are not primarily records to retrieve. Each residual induces constraints on admissible future representations and operators. Multiple residual views can therefore be intersected to infer the smallest latent obstruction that explains them jointly.

The developmental inference loop is:

`world -> residual -> multi-typing -> constraint closure -> latent obstruction -> missing distinction -> operator family -> verified intervention -> new residual geometry`

## Objects

### Residual
A verifier-visible discrepancy or cost whose provenance is fixed.

Each residual carries typed views rather than one flat label:

- layer: representation / identity / routing / capacity / soundness / benchmark / infrastructure / semantics
- scope: local / family / workload / benchmark / cross-domain
- phenotype: high-frequency / tiny-state / shallow / repeated / cold / collision / unsupported / expensive-materialization
- invariant: soundness-required / reuse-required / source-independence / closure-preserving / no-capacity-assumption / no-leakage
- causal status: observational / intervention-supported / ablation-supported / transfer-supported / refuted
- eliminated families: operator or representation families contradicted by verified experiments
- required properties: positive constraints induced by evidence

### Operator
A representation or transformation with an explicit capability signature:

- properties it satisfies
- invariants it preserves
- residual types it is intended to cover
- cost assumptions
- provenance of supporting evidence

### Latent obstruction
A minimal conjunction of constraints shared by a residual cluster that is not currently satisfied by any operator in closure.

A latent obstruction is an inference object, not automatically a law. It becomes verified only after a predicted operator family closes the implicated residuals and survives controls.

## Constraint closure

For a residual set `R`, collect only verifier-supported constraints. Candidate common explanations are conjunctions of those constraints.

A useful obstruction should satisfy:

1. **Coverage** — explains multiple unresolved residuals.
2. **Consistency** — violates no verified invariant.
3. **Minimality** — dropping any conjunct admits an already-refuted family or loses explanatory coverage.
4. **Novelty** — no operator in current closure satisfies the conjunction.
5. **Testability** — predicts a discriminating intervention or operator family.

## Discovery objective

Given unresolved residuals `R`, existing operator closure `K`, and verified invariants `I`, search for a candidate operator `o` maximizing

`covered_residual_mass(o) - complexity(o)`

subject to

- `o` satisfies the inferred constraint conjunction,
- `o` violates no invariant in `I`,
- `o` is outside closure-equivalence of current `K`, and
- its claimed causal effect is externally testable.

The important novelty criterion is therefore closure-relative:

> An operator is developmentally novel when it satisfies a verified constraint intersection that no current closure-equivalent operator satisfies.

Syntactic novelty alone does not count.

## Example: kernel closure identity

The following verified negatives can be represented as constraints:

- cache capacity approximately flat -> `capacity-independent`
- source-pointer identity unsound -> `semantic-identity-required`
- structural key improves but duplicates semantic work -> `duplicate-key-computation-prohibited`
- cache bypass collapses useful reuse -> `reuse-essential`
- dominant states have 0/1/2 slots -> `tiny-state`

Their intersection generates a specification approximately of the form:

`tiny-state AND canonical-semantic-identity AND reuse-compatible AND no-duplicate-key-computation AND capacity-independent AND sound`

If no current operator satisfies that conjunction, the graph exposes a representation gap before the missing representation has been explicitly named.

## Verification discipline

RCG is not allowed to turn correlation into mechanism. A proposed latent obstruction remains provisional until an intervention chain establishes:

`residual cluster -> inferred constraint -> predicted operator family -> gap closure -> ablation reopens gap -> transfer`

Negative experiments are retained when they shrink admissible operator space, even when they add no capability.

## Developmental state

The compact state to remember is not every raw failed trace. It is:

- provenance-linked residuals,
- verifier-supported type assignments,
- induced positive/negative constraints,
- closure of eliminated operator families,
- unresolved constraint intersections,
- provisional latent obstructions,
- verified operator laws.

Raw evidence remains available for audit, but control/search operates over this constraint closure.
