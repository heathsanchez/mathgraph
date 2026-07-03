# Perron–Frobenius Feasibility Audit for Finite H-Tilt

## Executive Result

**Classification: `WAIT_FOR_MATHLIB_PR`.**

The relevant Lean source exists and exposes nearly the right mathematical
interface. It is not in pinned Mathlib
`8f9d9cff6bd728b17a24e163c9402775d9e6a365`. Its Mathlib integration is an open,
multi-PR stack, and the central primitive and irreducible PRs currently have
failing build checks. The public package also uses different Lean/Mathlib pins
and is reported by Reservoir as failing to build.

Accordingly, this audit neither imports the external code nor claims
Perron–Frobenius existence. The shortest low-risk route is to wait for the PR
stack to merge, then implement a separate discrete-time Matrix theorem.

## Existing Verified Kernel

`finite_htilt_survivor_law_v1` remains a `VERIFIED_PROOF`. It proves finite
algebraic cancellation identities after receiving `q`, `h`, and their left and
right eigen-equations as hypotheses. It does not construct those modes and does
not prove their positivity, uniqueness, dominance, or convergence of a Markov
process.

This audit does not modify the Lean file or Lawbook entry.

## External Source

The paper [*Formalized Hopfield Networks and Boltzmann
Machines*](https://arxiv.org/abs/2512.07766), by Matteo Cipollina, Michail
Karatarakis, and Freek Wiedijk, reports a Lean 4 Perron–Frobenius formalization.
The source is public in
[mkaratarakis/HopfieldNet](https://github.com/mkaratarakis/HopfieldNet).

The audited repository commit is
`0bbb8999d1703776516f37f412334e01e07a30a0`. It contains:

- `Matrix.exists_positive_eigenvector_of_irreducible`
- `Matrix.pft_irreducible`
- `Matrix.perronRoot_transpose_eq`
- `Matrix.perron_root_eq_positive_eigenvalue`

The current repository toolchain is Lean 4.27.0-rc1 and its Mathlib pin is
`ae0143cded18d09875e12c3056f428090484d9a4`. Its README says Lean 4.18.0, so the
README is stale relative to the manifest. Reservoir reports that the audited
commit fails to build.

The principal Mathlib PRs are
[#39920](https://github.com/leanprover-community/mathlib4/pull/39920) for the
primitive case and
[#39922](https://github.com/leanprover-community/mathlib4/pull/39922) for the
irreducible case. Both are open and currently have failing build checks.

## Local Mathlib Status

The installed Mathlib checkout was verified at the required revision:

```text
8f9d9cff6bd728b17a24e163c9402775d9e6a365
```

A source search found no Perron–Frobenius existence declaration. The only
`Perron-Frobenius` occurrence in the relevant matrix module is a documentation
tag. The pinned revision does contain:

- `Matrix.IsIrreducible`
- `Matrix.IsPrimitive`
- `Matrix.isIrreducible_iff_exists_pow_pos`
- `Matrix.IsPrimitive.isIrreducible`
- `Matrix.IsIrreducible.transpose`
- `Matrix.isIrreducible_transpose_iff`

Thus the combinatorial input language is ready, but the eigenpair theorem is
not.

No import probe was created. A local `#check` file could only confirm the
irreducibility definitions already found by source inspection; it could not
check the absent PF declarations. Adding the external project as a dependency
would be a dependency mutation and porting exercise, not a probe.

## Interface to Existing Survivor Law

1. **Right versus left mode.** The external irreducible theorem directly
   produces a strictly positive right eigenvector. Apply it to `Aᵀ` to obtain a
   vector `q` whose right-eigenvector equation is the left-eigenvector equation
   for `A`.
2. **Matrix shape.** The interface uses `Matrix n n ℝ` with finite, nonempty
   index type `n`, matching the intended finite-state target.
3. **Nonnegativity.** `Matrix.IsIrreducible` includes entrywise nonnegativity.
4. **Connectivity.** The existence theorem requires irreducibility. A primitive
   theorem is also available but is stronger than necessary.
5. **Strict positivity.** The existence theorem produces `∀ i, 0 < v i`.
6. **Uniqueness.** `Matrix.pft_irreducible` gives uniqueness after normalization
   to the standard simplex.
7. **Left mode.** The pinned Mathlib already proves irreducibility is preserved
   by transpose, so applying PF to `Aᵀ` is structurally available.
8. **Eigenvalue agreement.** The external dominance module contains
   `perronRoot_transpose_eq`. Alternatively, equality can be derived from the
   positive left/right pairing, but that would require a small new algebraic
   proof.
9. **API wrapper.** The existing survivor theorem uses functions
   `ι → ι → ℝ`; `Matrix ι ι ℝ` is definitionally the same function shape, but a
   wrapper theorem is still desirable to express `mulVec`, transpose, and the
   discrete Doob transform cleanly.
10. **Operator class.** The PF theorem targets a nonnegative matrix `A`. It
    does not directly target the existing killed-generator expression
    `K - λI`, whose diagonal may be negative.

## Recommended First Formal Target

The first implementation should be a new discrete-time theorem, separate from
the existing generator theorem:

```lean
theorem exists_positive_survivor_weight_of_irreducible
    {ι : Type*} [Fintype ι] [Nonempty ι] [DecidableEq ι]
    (A : Matrix ι ι ℝ)
    (hA : A.IsIrreducible) :
    ∃ ρ h q,
      0 < ρ ∧
      (∀ i, 0 < h i) ∧
      (∀ i, 0 < q i) ∧
      A *ᵥ h = ρ • h ∧
      Aᵀ *ᵥ q = ρ • q ∧
      stationaryForDiscreteDoob A ρ h q
```

The discrete Doob matrix should be

```text
doob(A,ρ,h)ᵢⱼ = Aᵢⱼ hⱼ / (ρ hᵢ).
```

Strict positivity supplies nonzero denominators and positive normalization.
The existing algebraic cancellation can then be reused or mirrored through a
small Matrix-facing adapter.

The killed-generator case should remain a later theorem. It needs an explicit,
verified bridge such as a nonnegative shift, semigroup exponential, or
resolvent. None of those bridges is licensed by this audit.

## Risks

- A killed generator may not be entrywise nonnegative.
- The external package is not verified against Lean 4.28.0 or the pinned
  Mathlib revision.
- The Mathlib PF work is split across dependent PRs, so theorem names and
  interfaces may change during review.
- Applying PF separately to `A` and `Aᵀ` requires a proof that the returned
  positive eigenvalues agree.
- A Matrix API theorem is needed to keep transpose and `mulVec` reasoning
  explicit.
- Stationarity does not imply Markov convergence, mixing rates, or ergodicity.

## Decision

`WAIT_FOR_MATHLIB_PR`

This is not `READY_TO_IMPORT_FROM_MATHLIB`: the theorem is absent from the
pinned checkout.

This is not `READY_TO_VENDOR_EXTERNAL_REPO`: the external pins differ, the
public package is reported failing, and no Lean 4.28.0 import probe has passed.

This is not `REQUIRES_CUSTOM_PF_FORMALIZATION`: relevant source and an active
Mathlib integration route exist.

## Next Prompt

Re-audit Mathlib PRs #39920 and #39922. If they have merged, select and pin a
Mathlib revision containing the irreducible existence, normalized uniqueness,
and transpose-root results. Then create a separate Matrix-based Lean proof that
obtains `h` from `A`, obtains `q` from `Aᵀ`, aligns their Perron eigenvalues, and
proves discrete Doob stationarity. Do not modify
`finite_htilt_survivor_law_v1`; add a new Lawbook entry only after the new Lean
file compiles without placeholders.
