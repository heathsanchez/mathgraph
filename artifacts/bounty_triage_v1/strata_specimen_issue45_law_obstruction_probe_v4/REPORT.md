# strata-org/specimen #45 LawfulScorable Obstruction Probe v4

## Result

- `lake env lean Specimen/LawfulScorableObstructionProbe.lean` rc: `0`
- `lake build` with probe file rc: `0`

Verdict: `CERTIFIED_COUNTEREXAMPLES`

## Eval output

```text
DefaultScore worst beats beyond-worst score:
true
WorstLeafScore worst beats beyond-worst score:
true
UniformDensityScore worst beats beyond-worst score:
true
DefaultScore combine improves left:
false
WorstLeafScore combine improves left:
false
DensityScore combined value:
{ density := Scoring.Density.Checking, varDeps := 0, forChecker := true }
DensityScore combine improves left:
true
```

## What this proves

The currently obvious global `LawfulScorable` laws are too strong for the raw score types.

Counterexamples certified by Lean:

1. `worst` is a finite sentinel, not a true top element.
   For `DefaultScore`, `WorstLeafScore`, and `UniformDensityScore`, a raw score with `1001` can be worse than the `{ ... := 1000 }` sentinel, so `Scorable.isBetter worst largerScore = true`.

2. `DensityScore.combine` can strictly improve the left score.
   `combine` uses `forChecker := a.forChecker || b.forChecker`, while `Ord DensityScore` reverses density ordering when `forChecker = true`. This permits `isBetter (combine a b) a = true`.

Therefore a class with laws like:

```lean
∀ a b, ¬ Scorable.isBetter (Scorable.combine a b) a
∀ a, ¬ Scorable.isBetter Scorable.worst a
```

cannot be instantiated for the current raw score types without changing semantics, adding validity predicates, or weakening the laws.

## Recommended action

Do not open a PR claiming full `LawfulScorable` instances yet.

Best move is a maintainer comment asking for the intended law domain:

```text
I started implementing `LawfulScorable` for #45 and found two design constraints before opening a PR.

First, `worst` is currently a finite sentinel such as `{ checks := 1000 }`, while the raw score types admit larger scores, so `isBetter worst { checks := 1001 }` can evaluate to true. That means a global law like `∀ a, ¬ isBetter worst a` is not valid over all inhabitants.

Second, for `DensityScore`, `combine` can flip `forChecker` to true, and the ordering reverses density interpretation in checker mode. I found a small example where `isBetter (combine a b) a = true`, so the monotonicity law is also not globally valid for the raw type.

Should `LawfulScorable` quantify over a validity predicate / scheduler-produced scores, should `worst` become a true top element, or should the intended laws be weaker?
```

## Probe source

```lean
import Specimen.Scoring

namespace Scoring

/-
This file is not intended as a repo patch.
It certifies that some plausible global LawfulScorable laws are false
for the current raw score types.
-/

def defaultBeyondWorst : DefaultScore :=
  { checks := 1001, length := 0, unconstrained := 0 }

def worstDefault : DefaultScore :=
  (Scorable.worst : DefaultScore)

def defaultWorstBeatsBeyond : Bool :=
  Scorable.isBetter worstDefault defaultBeyondWorst

def worstLeafBeyondWorst : WorstLeafScore :=
  { checks := 1001, length := 0, unconstrained := 0 }

def worstLeafWorst : WorstLeafScore :=
  (Scorable.worst : WorstLeafScore)

def worstLeafWorstBeatsBeyond : Bool :=
  Scorable.isBetter worstLeafWorst worstLeafBeyondWorst

def uniformBeyondWorst : UniformDensityScore :=
  { density := .Checking, varDeps := 1001 }

def uniformWorst : UniformDensityScore :=
  (Scorable.worst : UniformDensityScore)

def uniformWorstBeatsBeyond : Bool :=
  Scorable.isBetter uniformWorst uniformBeyondWorst

def defaultA : DefaultScore :=
  { checks := 1, length := 1, unconstrained := 0 }

def defaultB : DefaultScore :=
  { checks := 1, length := 0, unconstrained := 0 }

def defaultCombineImprovesLeft : Bool :=
  Scorable.isBetter (Scorable.combine defaultA defaultB) defaultA

def worstLeafA : WorstLeafScore :=
  { checks := 1, length := 1, unconstrained := 0 }

def worstLeafB : WorstLeafScore :=
  { checks := 0, length := 2, unconstrained := 0 }

def worstLeafCombineImprovesLeft : Bool :=
  Scorable.isBetter (Scorable.combine worstLeafA worstLeafB) worstLeafA

/-
DensityScore has an especially direct obstruction.

For generator mode (`forChecker = false`), larger density.toNat is worse.
For checker mode (`forChecker = true`), the comparison reverses density level.
Combining uses OR for `forChecker`, so combine can flip the interpretation
and make the combined score strictly better than the original left score.
-/
def densityA : DensityScore :=
  { density := .Checking, varDeps := 0, forChecker := false }

def densityB : DensityScore :=
  { density := .Total, varDeps := 0, forChecker := true }

def densityCombined : DensityScore :=
  Scorable.combine densityA densityB

def densityCombineImprovesLeft : Bool :=
  Scorable.isBetter densityCombined densityA

-- Boolean certificates.
example : defaultWorstBeatsBeyond = true := by native_decide
example : worstLeafWorstBeatsBeyond = true := by native_decide
example : uniformWorstBeatsBeyond = true := by native_decide
example : defaultCombineImprovesLeft = false := by native_decide
example : worstLeafCombineImprovesLeft = false := by native_decide
example : densityCombineImprovesLeft = true := by native_decide

#eval IO.println "DefaultScore worst beats beyond-worst score:"
#eval IO.println defaultWorstBeatsBeyond

#eval IO.println "WorstLeafScore worst beats beyond-worst score:"
#eval IO.println worstLeafWorstBeatsBeyond

#eval IO.println "UniformDensityScore worst beats beyond-worst score:"
#eval IO.println uniformWorstBeatsBeyond

#eval IO.println "DefaultScore combine improves left:"
#eval IO.println defaultCombineImprovesLeft

#eval IO.println "WorstLeafScore combine improves left:"
#eval IO.println worstLeafCombineImprovesLeft

#eval IO.println "DensityScore combined value:"
#eval IO.println (repr densityCombined)

#eval IO.println "DensityScore combine improves left:"
#eval IO.println densityCombineImprovesLeft

end Scoring

```

