# SorryDB v4.4.70 — Law46 Patch010 corrected toFin micro Report

## Target

- Repository: teorth/equational_theories
- Commit: b1cc1756202d7f44e07bd4069b5df16901a36938
- File: equational_theories/Definability/Law46.lean
- Module: equational_theories.Definability.Law46

## Prior Accepted Partials

Patch002 accepted rhs-is-leaf.
Patch005 accepted hxy : x ≠ y.
Patch006 accepted L = Lf x ≃ Lf y.

## Baseline

- base_build_returncode: 0
- micro_returncode: 1

## Micro Tail

at (nat_lit 1)))))))))
            (instDecidableEqFin
              (@List.length.{0} Nat
                (@Subtype.val.{1} (List.{0} Nat)
                  (fun (l : List.{0} Nat) =>
                    And (@List.Nodup.{0} Nat l)
                      (∀ (a : Nat),
                        Iff (@Membership.mem.{0, 0} Nat (List.{0} Nat) (@List.instMembership.{0} Nat) l a)
                          (@Law.MagmaLaw.Mem.{0} Nat a
                            (@Law.MagmaLaw.mk.{0} Nat
                              (@FreeMagma.Leaf.{0} Nat (@OfNat.ofNat.{0} Nat (nat_lit 0) (instOfNatNat (nat_lit 0))))
                              (@FreeMagma.Leaf.{0} Nat
                                (@OfNat.ofNat.{0} Nat (nat_lit 1) (instOfNatNat (nat_lit 1))))))))
                  (@Law.MagmaLaw.elems.{0} Nat instDecidableEqNat
                    (@Law.MagmaLaw.mk.{0} Nat
                      (@FreeMagma.Leaf.{0} Nat (@OfNat.ofNat.{0} Nat (nat_lit 0) (instOfNatNat (nat_lit 0))))
                      (@FreeMagma.Leaf.{0} Nat (@OfNat.ofNat.{0} Nat (nat_lit 1) (instOfNatNat (nat_lit 1)))))))))
            (@Law.MagmaLaw.toFin.{0} Nat instDecidableEqNat
              (@Law.MagmaLaw.mk.{0} Nat
                (@FreeMagma.Leaf.{0} Nat (@OfNat.ofNat.{0} Nat (nat_lit 0) (instOfNatNat (nat_lit 0))))
                (@FreeMagma.Leaf.{0} Nat (@OfNat.ofNat.{0} Nat (nat_lit 1) (instOfNatNat (nat_lit 1))))))))))
Law46ToFinRecon.lean:30:52: error: Type mismatch
  @Law.MagmaLaw.toFin.{0} Nat instDecidableEqNat Law2
has type
  Law.MagmaLaw.{0}
    (Fin
      (@List.length.{0} Nat
        (@Subtype.val.{1} (List.{0} Nat)
          (fun (l : List.{0} Nat) =>
            And (@List.Nodup.{0} Nat l)
              (∀ (a : Nat),
                Iff (@Membership.mem.{0, 0} Nat (List.{0} Nat) (@List.instMembership.{0} Nat) l a)
                  (@Law.MagmaLaw.Mem.{0} Nat a Law2)))
          (@Law.MagmaLaw.elems.{0} Nat instDecidableEqNat Law2))))
but is expected to have type
  Law.MagmaLaw.{0}
    (Fin
      (@List.length.{0}
        (Fin
          (@List.length.{0} Nat
            (@Subtype.val.{1} (List.{0} Nat)
              (fun (l : List.{0} Nat) =>
                And (@List.Nodup.{0} Nat l)
                  (∀ (a : Nat),
                    Iff (@Membership.mem.{0, 0} Nat (List.{0} Nat) (@List.instMembership.{0} Nat) l a)
                      (@Law.MagmaLaw.Mem.{0} Nat a
                        (@Law.MagmaLaw.mk.{0} Nat
                          (@FreeMagma.Leaf.{0} Nat (@OfNat.ofNat.{0} Nat (nat_lit 1) (instOfNatNat (nat_lit 1))))
                          (@FreeMagma.Leaf.{0} Nat (@OfNat.ofNat.{0} Nat (nat_lit 0) (instOfNatNat (nat_lit 0))))))))
              (@Law.MagmaLaw.elems.{0} Nat instDecidableEqNat
                (@Law.MagmaLaw.mk.{0} Nat
                  (@FreeMagma.Leaf.{0} Nat (@OfNat.ofNat.{0} Nat (nat_lit 1) (instOfNatNat (nat_lit 1))))
                  (@FreeMagma.Leaf.{0} Nat (@OfNat.ofNat.{0} Nat (nat_lit 0) (instOfNatNat (nat_lit 0)))))))))
        (@Subtype.val.{1}
          (List.{0}
            (Fin
              (@List.length.{0} Nat
                (@Subtype.val.{1} (List.{0} Nat)
                  (fun (l : List.{0} Nat) =>
                    And (@List.Nodup.{0} Nat l)
                      (∀ (a : Nat),
                        Iff (@Membership.mem.{0, 0} Nat (List.{0} Nat) (@List.instMembership.{0} Nat) l a)
                          (@Law.MagmaLaw.Mem.{0} Nat a
                            (@Law.MagmaLaw.mk.{0} Nat
                              (@FreeMagma.Leaf.{0} Nat (@OfNat.ofNat.{0} Nat (nat_lit 1) (instOfNatNat (nat_lit 1))))
                              (@FreeMagma.Leaf.{0} Nat
                                (@OfNat.ofNat.{0} Nat (nat_lit 0) (instOfNatNat (nat_lit 0))))))))
                  (@Law.MagmaLaw.elems.{0} Nat instDecidableEqNat
                    (@Law.MagmaLaw.mk.{0} Nat
                      (@FreeMagma.Leaf.{0} Nat (@OfNat.ofNat.{0} Nat (nat_lit 1) (instOfNatNat (nat_lit 1))))
                      (@FreeMagma.Leaf.{0} Nat (@OfNat.ofNat.{0} Nat (nat_lit 0) (instOfNatNat (nat_lit 0))))))))))
          (fun
              (l :
                List.{0}
                  (Fin
                    (@List.length.{0} Nat
                      (@Subtype.val.{1} (List.{0} Nat)
                        (fun (l : List.{0} Nat) =>
                          And (@List.Nodup.{0} Nat l)
                            (∀ (a : Nat),
                              Iff (@Membership.mem.{0, 0} Nat (List.{0} Nat) (@List.instMembership.{0} Nat) l a)
                                (@Law.MagmaLaw.Mem.{0} Nat a
                                  (@Law.MagmaLaw.mk.{0} Nat
                                    (@FreeMagma.Leaf.{0} Nat
                                      (@OfNat.ofNat.{0} Nat (nat_lit 1) (instOfNatNat (nat_lit 1))))
                                    (@FreeMagma.Leaf.{0} Nat
                                      (@OfNat.ofNat.{0} Nat (nat_lit 0) (instOfNatNat (nat_lit 0))))))))
                        (@Law.MagmaLaw.elems.{0} Nat instDecidableEqNat
                          (@Law.MagmaLaw.mk.{0} Nat
                            (@FreeMagma.Leaf.{0} Nat (@OfNat.ofNat.{0} Nat (nat_lit 1) (instOfNatNat (nat_lit 1))))
                            (@FreeMagma.Leaf.{0} Nat
                              (@OfNat.ofNat.{0} Nat (nat_lit 0) (instOfNatNat (nat_lit 0)))))))))) =>
            And
              (@List.Nodup.{0}
                (Fin
                  (@List.length.{0} Nat
                    (@Subtype.val.{1} (List.{0} Nat)
                      (fun (l : List.{0} Nat) =>
                        And (@List.Nodup.{0} Nat l)
                          (∀ (a : Nat),
                            Iff (@Membership.mem.{0, 0} Nat (List.{0} Nat) (@List.instMembership.{0} Nat) l a)
                              (@Law.MagmaLaw.Mem.{0} Nat a
                                (@Law.MagmaLaw.mk.{0} Nat
                                  (@FreeMagma.Leaf.{0} Nat
                                    (@OfNat.ofNat.{0} Nat (nat_lit 1) (instOfNatNat (nat_lit 1))))
                                  (@FreeMagma.Leaf.{0} Nat
                                    (@OfNat.ofNat.{0} Nat (nat_lit 0) (instOfNatNat (nat_lit 0))))))))
                      (@Law.MagmaLaw.elems.{0} Nat instDecidableEqNat
                        (@Law.MagmaLaw.mk.{0} Nat
                          (@FreeMagma.Leaf.{0} Nat (@OfNat.ofNat.{0} Nat (nat_lit 1) (instOfNatNat (nat_lit 1))))
                          (@FreeMagma.Leaf.{0} Nat (@OfNat.ofNat.{0} Nat (nat_lit 0) (instOfNatNat (nat_lit 0)))))))))
                l)
              (∀
                (a :
                  Fin
                    (@List.length.{0} Nat
                      (@Subtype.val.{1} (List.{0} Nat)
                        (fun (l : List.{0} Nat) =>
                          And (@List.Nodup.{0} Nat l)
                            (∀ (a : Nat),
                              Iff (@Membership.mem.{0, 0} Nat (List.{0} Nat) (@List.instMembership.{0} Nat) l a)
                                (@Law.MagmaLaw.Mem.{0} Nat a
                                  (@Law.MagmaLaw.mk.{0} Nat
                                    (@FreeMagma.Leaf.{0} Nat
                                      (@OfNat.ofNat.{0} Nat (nat_lit 1) (instOfNatNat (nat_lit 1))))
                                    (@FreeMagma.Leaf.{0} Nat
                                      (@OfNat.ofNat.{0} Nat (nat_lit 0) (instOfNatNat (nat_lit 0))))))))
                        (@Law.MagmaLaw.elems.{0} Nat instDecidableEqNat
                          (@Law.MagmaLaw.mk.{0} Nat
                            (@FreeMagma.Leaf.{0} Nat (@OfNat.ofNat.{0} Nat (nat_lit 1) (instOfNatNat (nat_lit 1))))
                            (@FreeMagma.Leaf.{0} Nat
                              (@OfNat.ofNat.{0} Nat (nat_lit 0) (instOfNatNat (nat_lit 0))))))))),
                Iff
                  (@Membership.mem.{0, 0}
                    (Fin
                      (@List.length.{0} Nat
                        (@Subtype.val.{1} (List.{0} Nat)
                          (fun (l : List.{0} Nat) =>
                            And (@List.Nodup.{0} Nat l)
                              (∀ (a : Nat),
                                Iff (@Membership.mem.{0, 0} Nat (List.{0} Nat) (@List.instMembership.{0} Nat) l a)
                                  (@Law.MagmaLaw.Mem.{0} Nat a
                                    (@Law.MagmaLaw.mk.{0} Nat
                                      (@FreeMagma.Leaf.{0} Nat
                                        (@OfNat.ofNat.{0} Nat (nat_lit 1) (instOfNatNat (nat_lit 1))))
                                      (@FreeMagma.Leaf.{0} Nat
                                        (@OfNat.ofNat.{0} Nat (nat_lit 0) (instOfNatNat (nat_lit 0))))))))
                          (@Law.MagmaLaw.elems.{0} Nat instDecidableEqNat
                            (@Law.MagmaLaw.mk.{0} Nat
                              (@FreeMagma.Leaf.{0} Nat (@OfNat.ofNat.{0} Nat (nat_lit 1) (instOfNatNat (nat_lit 1))))
                              (@FreeMagma.Leaf.{0} Nat
                                (@OfNat.ofNat.{0} Nat (nat_lit 0) (instOfNatNat (nat_lit 0)))))))))
                    (List.{0}
                      (Fin
                        (@List.length.{0} Nat
                          (@Subtype.val.{1} (List.{0} Nat)
                            (fun (l : List.{0} Nat) =>
                              And (@List.Nodup.{0} Nat l)
                                (∀ (a : Nat),
                                  Iff (@Membership.mem.{0, 0} Nat (List.{0} Nat) (@List.instMembership.{0} Nat) l a)
                                    (@Law.MagmaLaw.Mem.{0} Nat a
                                      (@Law.MagmaLaw.mk.{0} Nat
                                        (@FreeMagma.Leaf.{0} Nat
                                          (@OfNat.ofNat.{0} Nat (nat_lit 1) (instOfNatNat (nat_lit 1))))
                                        (@FreeMagma.Leaf.{0} Nat
                                          (@OfNat.ofNat.{0} Nat (nat_lit 0) (instOfNatNat (nat_lit 0))))))))
                            (@Law.MagmaLaw.elems.{0} Nat instDecidableEqNat
                              (@Law.MagmaLaw.mk.{0} Nat
                                (@FreeMagma.Leaf.{0} Nat (@OfNat.ofNat.{0} Nat (nat_lit 1) (instOfNatNat (nat_lit 1))))
                                (@FreeMagma.Leaf.{0} Nat
                                  (@OfNat.ofNat.{0} Nat (nat_lit 0) (instOfNatNat (nat_lit 0))))))))))
                    (@List.instMembership.{0}
                      (Fin
                        (@List.length.{0} Nat
                          (@Subtype.val.{1} (List.{0} Nat)
                            (fun (l : List.{0} Nat) =>
                              And (@List.Nodup.{0} Nat l)
                                (∀ (a : Nat),
                                  Iff (@Membership.mem.{0, 0} Nat (List.{0} Nat) (@List.instMembership.{0} Nat) l a)
                                    (@Law.MagmaLaw.Mem.{0} Nat a
                                      (@Law.MagmaLaw.mk.{0} Nat
                                        (@FreeMagma.Leaf.{0} Nat
                                          (@OfNat.ofNat.{0} Nat (nat_lit 1) (instOfNatNat (nat_lit 1))))
                                        (@FreeMagma.Leaf.{0} Nat
                                          (@OfNat.ofNat.{0} Nat (nat_lit 0) (instOfNatNat (nat_lit 0))))))))
                            (@Law.MagmaLaw.elems.{0} Nat instDecidableEqNat
                              (@Law.MagmaLaw.mk.{0} Nat
                                (@FreeMagma.Leaf.{0} Nat (@OfNat.ofNat.{0} Nat (nat_lit 1) (instOfNatNat (nat_lit 1))))
                                (@FreeMagma.Leaf.{0} Nat
                                  (@OfNat.ofNat.{0} Nat (nat_lit 0) (instOfNatNat (nat_lit 0))))))))))
                    l a)
                  (@Law.MagmaLaw.Mem.{0}
                    (Fin
                      (@List.length.{0} Nat
                        (@Subtype.val.{1} (List.{0} Nat)
                          (fun (l : List.{0} Nat) =>
                            And (@List.Nodup.{0} Nat l)
                              (∀ (a : Nat),
                                Iff (@Membership.mem.{0, 0} Nat (List.{0} Nat) (@List.instMembership.{0} Nat) l a)
                                  (@Law.MagmaLaw.Mem.{0} Nat a
                                    (@Law.MagmaLaw.mk.{0} Nat
                                      (@FreeMagma.Leaf.{0} Nat
                                        (@OfNat.ofNat.{0} Nat (nat_lit 1) (instOfNatNat (nat_lit 1))))
                                      (@FreeMagma.Leaf.{0} Nat
                                        (@OfNat.ofNat.{0} Nat (nat_lit 0) (instOfNatNat (nat_lit 0))))))))
                          (@Law.MagmaLaw.elems.{0} Nat instDecidableEqNat
                            (@Law.MagmaLaw.mk.{0} Nat
                              (@FreeMagma.Leaf.{0} Nat (@OfNat.ofNat.{0} Nat (nat_lit 1) (instOfNatNat (nat_lit 1))))
                              (@FreeMagma.Leaf.{0} Nat
                                (@OfNat.ofNat.{0} Nat (nat_lit 0) (instOfNatNat (nat_lit 0)))))))))
                    a
                    (@Law.MagmaLaw.toFin.{0} Nat instDecidableEqNat
                      (@Law.MagmaLaw.mk.{0} Nat
                        (@FreeMagma.Leaf.{0} Nat (@OfNat.ofNat.{0} Nat (nat_lit 1) (instOfNatNat (nat_lit 1))))
                        (@FreeMagma.Leaf.{0} Nat (@OfNat.ofNat.{0} Nat (nat_lit 0) (instOfNatNat (nat_lit 0)))))))))
          (@Law.MagmaLaw.elems.{0}
            (Fin
              (@List.length.{0} Nat
                (@Subtype.val.{1} (List.{0} Nat)
                  (fun (l : List.{0} Nat) =>
                    And (@List.Nodup.{0} Nat l)
                      (∀ (a : Nat),
                        Iff (@Membership.mem.{0, 0} Nat (List.{0} Nat) (@List.instMembership.{0} Nat) l a)
                          (@Law.MagmaLaw.Mem.{0} Nat a
                            (@Law.MagmaLaw.mk.{0} Nat
                              (@FreeMagma.Leaf.{0} Nat (@OfNat.ofNat.{0} Nat (nat_lit 1) (instOfNatNat (nat_lit 1))))
                              (@FreeMagma.Leaf.{0} Nat
                                (@OfNat.ofNat.{0} Nat (nat_lit 0) (instOfNatNat (nat_lit 0))))))))
                  (@Law.MagmaLaw.elems.{0} Nat instDecidableEqNat
                    (@Law.MagmaLaw.mk.{0} Nat
                      (@FreeMagma.Leaf.{0} Nat (@OfNat.ofNat.{0} Nat (nat_lit 1) (instOfNatNat (nat_lit 1))))
                      (@FreeMagma.Leaf.{0} Nat (@OfNat.ofNat.{0} Nat (nat_lit 0) (instOfNatNat (nat_lit 0)))))))))
            (instDecidableEqFin
              (@List.length.{0} Nat
                (@Subtype.val.{1} (List.{0} Nat)
                  (fun (l : List.{0} Nat) =>
                    And (@List.Nodup.{0} Nat l)
                      (∀ (a : Nat),
                        Iff (@Membership.mem.{0, 0} Nat (List.{0} Nat) (@List.instMembership.{0} Nat) l a)
                          (@Law.MagmaLaw.Mem.{0} Nat a
                            (@Law.MagmaLaw.mk.{0} Nat
                              (@FreeMagma.Leaf.{0} Nat (@OfNat.ofNat.{0} Nat (nat_lit 1) (instOfNatNat (nat_lit 1))))
                              (@FreeMagma.Leaf.{0} Nat
                                (@OfNat.ofNat.{0} Nat (nat_lit 0) (instOfNatNat (nat_lit 0))))))))
                  (@Law.MagmaLaw.elems.{0} Nat instDecidableEqNat
                    (@Law.MagmaLaw.mk.{0} Nat
                      (@FreeMagma.Leaf.{0} Nat (@OfNat.ofNat.{0} Nat (nat_lit 1) (instOfNatNat (nat_lit 1))))
                      (@FreeMagma.Leaf.{0} Nat (@OfNat.ofNat.{0} Nat (nat_lit 0) (instOfNatNat (nat_lit 0)))))))))
            (@Law.MagmaLaw.toFin.{0} Nat instDecidableEqNat
              (@Law.MagmaLaw.mk.{0} Nat
                (@FreeMagma.Leaf.{0} Nat (@OfNat.ofNat.{0} Nat (nat_lit 1) (instOfNatNat (nat_lit 1))))
                (@FreeMagma.Leaf.{0} Nat (@OfNat.ofNat.{0} Nat (nat_lit 0) (instOfNatNat (nat_lit 0))))))))))



## Patch010 Goal

Replace:

    have : (Lf x ≃ Lf y).toFin.toNat = Law2 := by
      sorry

using corrected `Law2.toFin` / `.toFin.toFin` information.

## Variant Results

- v01_have_tofin_eq_Law2_tofin_native: rc=1, seconds=3.08, error=True, warning=False
- v02_have_tofin_eq_Law2_tofin_decide_kernel: rc=1, seconds=2.82, error=True, warning=False
- v03_suffices_tofin_eq_Law2_tofin: rc=1, seconds=2.81, error=True, warning=False
- v04_change_tofin_goal_then_native: rc=1, seconds=3.86, error=True, warning=False
- v05_zero_one_transport: rc=1, seconds=4.38, error=True, warning=False
- v06_cases_x_y_fin_native: rc=1, seconds=4.91, error=True, warning=False
- v07_unfold_all_then_exact_Law2_tofin: rc=1, seconds=4.27, error=True, warning=False
- v08_use_decide_revert_on_fin_only: rc=1, seconds=6.46, error=True, warning=False

## Status

PATCH010_REJECTED_OBSTRUCTION

## Accepted Variant

None

## Obstruction

## v01_have_tofin_eq_Law2_tofin_native
error: equational_theories/Definability/Law46.lean:44:60: Type mismatch
  toFin Law2
has type
  MagmaLaw (Fin (↑(elems Law2)).length)
but is expected to have type
  MagmaLaw (Fin (↑(Lf x ≃ Lf y).toFin.elems).length)
error: equational_theories/Definability/Law46.lean:47:13: Invalid argument: Variable `hfin` is not a proposition or let-declaration
error: equational_theories/Definability/Law46.lean:47:6: Tactic `assumption` failed

L : NatMagmaLaw
x y : ℕ
hxy : x ≠ y
hfin : sorry
⊢ map (fun x_1 ↦ ↑x_1) (Lf x ≃ Lf y).toFin.toFin = Law2
error: Lean exited with code 1
Some required targets logged failures:
- equational_theories.Definability.Law46

error: build failed
## v02_have_tofin_eq_Law2_tofin_decide_kernel
error: equational_theories/Definability/Law46.lean:44:60: Type mismatch
  toFin Law2
has type
  MagmaLaw (Fin (↑(elems Law2)).length)
but is expected to have type
  MagmaLaw (Fin (↑(Lf x ≃ Lf y).toFin.elems).length)
error: equational_theories/Definability/Law46.lean:47:13: Invalid argument: Variable `hfin` is not a proposition or let-declaration
error: equational_theories/Definability/Law46.lean:47:6: Tactic `assumption` failed

L : NatMagmaLaw
x y : ℕ
hxy : x ≠ y
hfin : sorry
⊢ map (fun x_1 ↦ ↑x_1) (Lf x ≃ Lf y).toFin.toFin = Law2
error: Lean exited with code 1
Some required targets logged failures:
- equational_theories.Definability.Law46

error: build failed
## v03_suffices_tofin_eq_Law2_tofin
error: equational_theories/Definability/Law46.lean:44:64: Type mismatch
  toFin Law2
has type
  MagmaLaw (Fin (↑(elems Law2)).length)
but is expected to have type
  MagmaLaw (Fin (↑(Lf x ≃ Lf y).toFin.elems).length)
error: equational_theories/Definability/Law46.lean:46:15: Invalid argument: Variable `hfin` is not a proposition or let-declaration
error: equational_theories/Definability/Law46.lean:46:8: Tactic `assumption` failed

L : NatMagmaLaw
x y : ℕ
hxy : x ≠ y
hfin : sorry
⊢ map (fun x_1 ↦ ↑x_1) (Lf x ≃ Lf y).toFin.toFin = Law2
error: Lean exited with code 1
Some required targets logged failures:
- equational_theories.Definability.Law46

error: build failed
## v04_change_tofin_goal_then_native
error: equational_theories/Definability/Law46.lean:46:60: Type mismatch
  toFin Law2
has type
  MagmaLaw (Fin (↑(elems Law2)).length)
but is expected to have type
  MagmaLaw (Fin (↑(Lf x ≃ Lf y).toFin.elems).length)
error: Lean exited with code 1
Some required targets logged failures:
- equational_theories.Definability.Law46

error: build failed
## v05_zero_one_transport
error: equational_theories/Definability/Law46.lean:46:6: Expected type must not contain free variables
  (Lf x ≃ Lf y).toFin.toNat = Law2

Hint: Use the `+revert` option to automatically clean up and revert free variables
error: Lean exited with code 1
Some required targets logged failures:
- equational_theories.Definability.Law46

error: build failed
## v06_cases_x_y_fin_native
error: equational_theories/Definability/Law46.lean:46:62: Type mismatch
  toFin Law2
has type
  MagmaLaw (Fin (↑(elems Law2)).length)
but is expected to have type
  MagmaLaw (Fin (↑(Lf x ≃ Lf y).toFin.elems).length)
error: equational_theories/Definability/Law46.lean:49:15: Invalid argument: Variable `hfin` is not a proposition or let-declaration
error: equational_theories/Definability/Law46.lean:49:8: Tactic `assumption` failed

case neg
L : NatMagmaLaw
x y : ℕ
hxy : x ≠ y
h : ¬x = y
hfin : sorry
⊢ map (fun x_1 ↦ ↑x_1) (Lf x ≃ Lf y).toFin.toFin = Law2
error: Lean exited with code 1
Some required targets logged failures:
- equational_theories.Definability.Law46

error: build failed
## v07_unfold_all_then_exact_Law2_tofin
error: equational_theories/Definability/Law46.lean:45:60: Type mismatch
  toFin Law2
has type
  MagmaLaw (Fin (↑(elems Law2)).length)
but is expected to have type
  MagmaLaw (Fin (↑(Lf x ≃ Lf y).toFin.elems).length)
error: equational_theories/Definability/Law46.lean:48:13: Invalid argument: Variable `hfin` is not a proposition or let-declaration
error: equational_theories/Definability/Law46.lean:48:6: Tactic `assumption` failed

L : NatMagmaLaw
x y : ℕ
hxy : x ≠ y
hfin : sorry
⊢ map (fun x_1 ↦ ↑x_1) (Lf x ≃ Lf y).toFin.toFin = Law2
error: Lean exited with code 1
Some required targets logged failures:
- equational_theories.Definability.Law46

error: build failed
## v08_use_decide_revert_on_fin_only
error: equational_theories/Definability/Law46.lean:44:60: Type mismatch
  toFin Law2
has type
  MagmaLaw (Fin (↑(elems Law2)).length)
but is expected to have type
  MagmaLaw (Fin (↑(Lf x ≃ Lf y).toFin.elems).length)
error: equational_theories/Definability/Law46.lean:47:13: Invalid argument: Variable `hfin` is not a proposition or let-declaration
error: equational_theories/Definability/Law46.lean:47:6: Tactic `assumption` failed

L : NatMagmaLaw
x y : ℕ
hxy : x ≠ y
hfin : sorry
⊢ map (fun x_1 ↦ ↑x_1) (Lf x ≃ Lf y).toFin.toFin = Law2
error: Lean exited with code 1
Some required targets logged failures:
- equational_theories.Definability.Law46

error: build failed

## Next Move

If accepted, carry Patch002 + Patch005 + Patch006 + Patch010 and verify whether the leaf/leaf branch is fully closed.

If rejected, the next move is to abandon the `toFin.toNat = Law2` proof route and use a direct implication/term-structural lemma if one exists, because `.toFin` canonicalization is the residual obstruction.
