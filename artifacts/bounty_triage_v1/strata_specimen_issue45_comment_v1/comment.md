I started implementing `LawfulScorable` for this and found two design constraints before opening a PR.

A class-only interface compiles cleanly, but some natural global laws appear false over the current raw score types.

First, `worst` is currently a finite sentinel such as `{ checks := 1000 }`, while the raw score types admit larger scores. For example, Lean confirms that for `DefaultScore`, `WorstLeafScore`, and `UniformDensityScore`, a score with `1001` can be worse than the current sentinel, so:

    Scorable.isBetter Scorable.worst largerScore = true

That means a global law like:

    ∀ a, ¬ Scorable.isBetter Scorable.worst a

does not hold over all inhabitants of the score type.

Second, `DensityScore.combine` can strictly improve the left score. `combine` uses:

    forChecker := a.forChecker || b.forChecker

but the ordering reverses density interpretation when `forChecker = true`. I found a small Lean-checked example where:

    Scorable.isBetter (Scorable.combine a b) a = true

So a global monotonicity law like:

    ∀ a b, ¬ Scorable.isBetter (Scorable.combine a b) a

also does not hold for the raw type as currently defined.

The probe compiles with:

    lake env lean Specimen/LawfulScorableObstructionProbe.lean

Question before I continue: should `LawfulScorable` quantify over a validity predicate / scheduler-produced scores, should `worst` become a true top element, or should the intended laws be weaker than the invariants listed above?
