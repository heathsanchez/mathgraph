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
