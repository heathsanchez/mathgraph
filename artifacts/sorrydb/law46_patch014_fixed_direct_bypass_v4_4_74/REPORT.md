# SorryDB v4.4.74 — Law46 Fixed Direct-Bypass Report

## Result

- Status: PATCH014_REJECTED_OR_DIAGNOSTIC_ONLY
- Accepted variant: None

## Variant Summary

- v01_trace_goal_after_unfold_diagnostic: rc=0, seconds=47.56, error=False, sorry_warning=False, diagnostic=True, accepted_leaf_bypass=False
- v02_direct_semantic_x_assignment: rc=1, seconds=4.71, error=True, sorry_warning=False, diagnostic=False, accepted_leaf_bypass=False
- v03_direct_semantic_two_var_assignment: rc=1, seconds=2.61, error=True, sorry_warning=False, diagnostic=False, accepted_leaf_bypass=False
- v04_after_intro_diagnostic: rc=0, seconds=2.99, error=False, sorry_warning=False, diagnostic=True, accepted_leaf_bypass=False
- v05_after_law46_models_diagnostic: rc=0, seconds=2.61, error=False, sorry_warning=False, diagnostic=True, accepted_leaf_bypass=False

## Named Obstruction If Rejected

Law46 leaf/leaf branch accepts local syntactic repairs, but the proof route bottlenecks at the semantic implication / MagmaLaw.toFin / Law2 canonicalization interface rather than simple term rewriting.

## Diagnostic Tails


### v01_trace_goal_after_unfold_diagnostic

STDOUT tail:
```
✔ [971/989] Built equational_theories.Magma (320ms)
✔ [972/989] Built equational_theories.Homomorphisms (6.7s)
✔ [973/989] Built equational_theories.ForMathlib.Definability (8.4s)
✔ [974/989] Built equational_theories.FreeMagma (5.1s)
✔ [975/989] Built equational_theories.MagmaLaw (2.9s)
✔ [976/989] Built equational_theories.EquationLawConversion (5.7s)
✔ [977/989] Built equational_theories.Preorder (5.7s)
✔ [978/989] Built equational_theories.Definability.Basic (4.9s)
✔ [979/989] Built equational_theories.ParseImplications (4.0s)
✔ [980/989] Built equational_theories.Equations.Command (5.1s)
✔ [981/989] Built equational_theories.Equations.Basic (8.1s)
✔ [982/989] Built equational_theories.EquationalResult (9.1s)
✔ [983/989] Built equational_theories.Equations.Eqns4000_4694 (12s)
✔ [984/989] Built equational_theories.Equations.Eqns1000_1999 (13s)
✔ [985/989] Built equational_theories.Equations.Eqns3000_3999 (13s)
✔ [986/989] Built equational_theories.Equations.Eqns1_999 (13s)
✔ [987/989] Built equational_theories.Equations.Eqns2000_2999 (13s)
✔ [988/989] Built equational_theories.Equations.All (4.3s)
⚠ [989/989] Built equational_theories.Definability.Law46 (2.4s)
info: equational_theories/Definability/Law46.lean:44:4: case h.h
L : NatMagmaLaw
x y : ℕ
hxy : x ≠ y
⊢ ∀ ⦃G : Type⦄ [inst : Magma G], G ⊧ Lf x ≃ Lf y → G ⊧ Law46
warning: equational_theories/Definability/Law46.lean:11:8: declaration uses `sorry`
Build completed successfully (989 jobs).
```
STDERR tail:
```

```

### v02_direct_semantic_x_assignment

STDOUT tail:
```
✖ [989/989] Building equational_theories.Definability.Law46 (3.0s)
trace: .> LEAN_PATH=/private/tmp/sorrydb_law46_patch014_v4_4_74/.lake/packages/Cli/.lake/build/lib/lean:/private/tmp/sorrydb_law46_patch014_v4_4_74/.lake/packages/batteries/.lake/build/lib/lean:/private/tmp/sorrydb_law46_patch014_v4_4_74/.lake/packages/Qq/.lake/build/lib/lean:/private/tmp/sorrydb_law46_patch014_v4_4_74/.lake/packages/aesop/.lake/build/lib/lean:/private/tmp/sorrydb_law46_patch014_v4_4_74/.lake/packages/proofwidgets/.lake/build/lib/lean:/private/tmp/sorrydb_law46_patch014_v4_4_74/.lake/packages/importGraph/.lake/build/lib/lean:/private/tmp/sorrydb_law46_patch014_v4_4_74/.lake/packages/LeanSearchClient/.lake/build/lib/lean:/private/tmp/sorrydb_law46_patch014_v4_4_74/.lake/packages/plausible/.lake/build/lib/lean:/private/tmp/sorrydb_law46_patch014_v4_4_74/.lake/packages/mathlib/.lake/build/lib/lean:/private/tmp/sorrydb_law46_patch014_v4_4_74/.lake/packages/checkdecls/.lake/build/lib/lean:/private/tmp/sorrydb_law46_patch014_v4_4_74/.lake/build/lib/lean /Users/heath/.elan/toolchains/leanprover--lean4---v4.29.1/bin/lean --tstack=262144 /private/tmp/sorrydb_law46_patch014_v4_4_74/equational_theories/Definability/Law46.lean -o /private/tmp/sorrydb_law46_patch014_v4_4_74/.lake/build/lib/lean/equational_theories/Definability/Law46.olean -i /private/tmp/sorrydb_law46_patch014_v4_4_74/.lake/build/lib/lean/equational_theories/Definability/Law46.ilean -c /private/tmp/sorrydb_law46_patch014_v4_4_74/.lake/build/ir/equational_theories/Definability/Law46.c --setup /private/tmp/sorrydb_law46_patch014_v4_4_74/.lake/build/ir/equational_theories/Definability/Law46.setup.json --json
error: equational_theories/Definability/Law46.lean:49:6: Type mismatch: After simplification, term
  hh
 has type
  satisfiesPhi (fun n ↦ if n = x then a else c) (Lf x ≃ Lf y)
but is expected to have type
  a = c
error: equational_theories/Definability/Law46.lean:52:6: Type mismatch: After simplification, term
  hh
 has type
  satisfiesPhi (fun n ↦ if n = x then b else d) (Lf x ≃ Lf y)
but is expected to have type
  b = d
error: Lean exited with code 1
Some required targets logged failures:
- equational_theories.Definability.Law46
```
STDERR tail:
```
error: build failed
```

### v03_direct_semantic_two_var_assignment

STDOUT tail:
```
✖ [989/989] Building equational_theories.Definability.Law46 (1.4s)
trace: .> LEAN_PATH=/private/tmp/sorrydb_law46_patch014_v4_4_74/.lake/packages/Cli/.lake/build/lib/lean:/private/tmp/sorrydb_law46_patch014_v4_4_74/.lake/packages/batteries/.lake/build/lib/lean:/private/tmp/sorrydb_law46_patch014_v4_4_74/.lake/packages/Qq/.lake/build/lib/lean:/private/tmp/sorrydb_law46_patch014_v4_4_74/.lake/packages/aesop/.lake/build/lib/lean:/private/tmp/sorrydb_law46_patch014_v4_4_74/.lake/packages/proofwidgets/.lake/build/lib/lean:/private/tmp/sorrydb_law46_patch014_v4_4_74/.lake/packages/importGraph/.lake/build/lib/lean:/private/tmp/sorrydb_law46_patch014_v4_4_74/.lake/packages/LeanSearchClient/.lake/build/lib/lean:/private/tmp/sorrydb_law46_patch014_v4_4_74/.lake/packages/plausible/.lake/build/lib/lean:/private/tmp/sorrydb_law46_patch014_v4_4_74/.lake/packages/mathlib/.lake/build/lib/lean:/private/tmp/sorrydb_law46_patch014_v4_4_74/.lake/packages/checkdecls/.lake/build/lib/lean:/private/tmp/sorrydb_law46_patch014_v4_4_74/.lake/build/lib/lean /Users/heath/.elan/toolchains/leanprover--lean4---v4.29.1/bin/lean --tstack=262144 /private/tmp/sorrydb_law46_patch014_v4_4_74/equational_theories/Definability/Law46.lean -o /private/tmp/sorrydb_law46_patch014_v4_4_74/.lake/build/lib/lean/equational_theories/Definability/Law46.olean -i /private/tmp/sorrydb_law46_patch014_v4_4_74/.lake/build/lib/lean/equational_theories/Definability/Law46.ilean -c /private/tmp/sorrydb_law46_patch014_v4_4_74/.lake/build/ir/equational_theories/Definability/Law46.c --setup /private/tmp/sorrydb_law46_patch014_v4_4_74/.lake/build/ir/equational_theories/Definability/Law46.setup.json --json
error: equational_theories/Definability/Law46.lean:50:6: Type mismatch: After simplification, term
  hh
 has type
  satisfiesPhi (fun n ↦ if n = x then a else if n = y then c else a) (Lf x ≃ Lf y)
but is expected to have type
  a = c
error: equational_theories/Definability/Law46.lean:53:6: Type mismatch: After simplification, term
  hh
 has type
  satisfiesPhi (fun n ↦ if n = x then b else if n = y then d else b) (Lf x ≃ Lf y)
but is expected to have type
  b = d
error: Lean exited with code 1
Some required targets logged failures:
- equational_theories.Definability.Law46
```
STDERR tail:
```
error: build failed
```

### v04_after_intro_diagnostic

STDOUT tail:
```
⚠ [989/989] Built equational_theories.Definability.Law46 (1.7s)
info: equational_theories/Definability/Law46.lean:45:4: case h.h
L : NatMagmaLaw
x y : ℕ
hxy : x ≠ y
G : Type
M : Magma G
hG : G ⊧ Lf x ≃ Lf y
⊢ G ⊧ Law46
warning: equational_theories/Definability/Law46.lean:11:8: declaration uses `sorry`
Build completed successfully (989 jobs).
```
STDERR tail:
```

```

### v05_after_law46_models_diagnostic

STDOUT tail:
```
⚠ [989/989] Built equational_theories.Definability.Law46 (1.5s)
info: equational_theories/Definability/Law46.lean:46:4: case h.h
L : NatMagmaLaw
x y : ℕ
hxy : x ≠ y
G : Type
M : Magma G
hG : G ⊧ Lf x ≃ Lf y
⊢ Equation46 G
warning: equational_theories/Definability/Law46.lean:11:8: declaration uses `sorry`
Build completed successfully (989 jobs).
```
STDERR tail:
```

```