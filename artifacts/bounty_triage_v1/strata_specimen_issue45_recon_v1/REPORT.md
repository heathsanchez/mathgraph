# strata-org/specimen #45 Recon

Issue: LawfulScorable: formally verify scorer invariants

Labels: 
Comments: 1

## Baseline

- Build completed successfully (47 jobs). rc: 

## Candidate files

- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 

## Issue body



## Initial MathGraph read

This is a good MathGraph-native target if the existing score types are simple Nat/Float/product scorers.

Likely route:

1. Define  with fields for monotonicity/transitivity/worst/empty/badness.
2. Add minimal instances for existing scorers.
3. Only add  constraint to  if this does not cascade through many callers.
4. Prefer a small PR that defines the class + one or two easy instances if full issue is too large.

Kill conditions:

- baseline Build completed successfully (47 jobs). fails unrelatedly and cannot be isolated
- scorer definitions use Float comparisons that make invariant proofs awkward
- issue is unpaid/unclear or maintainer intent requires large design changes

