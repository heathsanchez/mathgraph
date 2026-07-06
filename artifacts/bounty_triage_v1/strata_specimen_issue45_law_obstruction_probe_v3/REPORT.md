# strata-org/specimen #45 Law Obstruction Probe v3

## Result

- Lean probe rc: `1`
- Lake build with probe rc: `0`

## Evaluated law probes

```text
DefaultScore: isBetter (combine a b) a = false
WorstLeafScore: isBetter (combine a b) a = false
DensityScore combine example = { density := Scoring.Density.Checking, varDeps := 0, forChecker := true }
DensityScore: isBetter (combine a b) a = true
```

## Interpretation

The class-only `LawfulScorable` interface compiles, but some obvious universal laws are likely too strong over the raw score types.

Key obstruction:

```text
Scorable.worst is a fixed finite sentinel, e.g. checks := 1000.
The raw score type allows larger values, e.g. checks := 1001.
Therefore `isBetter worst largerScore` can evaluate to true.
So the law `∀ a, ¬ isBetter worst a` is not valid over all inhabitants of the score type.
```

This suggests the issue needs one of these designs:

1. weaken the law to apply only to scheduler-produced/valid scores;
2. add bounded-score validity predicates;
3. redefine `worst` as an actual top element, e.g. an `Option`/`WithTop` style score;
4. keep `LawfulScorable` as an interface first, then negotiate exact law fields with maintainers.

## Best PR strategy

Open a small PR adding only the proof-carrying `LawfulScorable` interface, with a comment that instance proofs require clarifying the intended domain of `worst` and valid scores.

This is better than forcing false laws or adding weak placeholders.

## Maintainer question draft

```text
I started implementing `LawfulScorable`. A class-only interface compiles cleanly, but I found one design point before proving instances: `worst` is currently a finite sentinel such as `{ checks := 1000 }`, while the raw score type admits larger scores such as `{ checks := 1001 }`. So a universal law like `∀ a, ¬ isBetter worst a` is not true over all inhabitants of the score type.

Should the laws quantify only over scheduler-produced/valid scores, should we add a validity predicate/bounded-score invariant, or should `worst` be represented as a true top element?
```

## Probe diff

```diff

```

