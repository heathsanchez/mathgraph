# Perron–Frobenius External Source Audit

## Paper

- **Title:** *Formalized Hopfield Networks and Boltzmann Machines*
- **Authors:** Matteo Cipollina, Michail Karatarakis, Freek Wiedijk
- **Date:** 8 December 2025
- **Record:** [arXiv:2512.07766](https://arxiv.org/abs/2512.07766)

The abstract reports a Lean 4 formalization of Perron–Frobenius theory used to
prove ergodicity and uniqueness of a stationary distribution for Boltzmann
machines. This confirms relevance, but the paper is not itself an importable
dependency.

## Code Repository

- **Repository:** [mkaratarakis/HopfieldNet](https://github.com/mkaratarakis/HopfieldNet)
- **Audited commit:** `0bbb8999d1703776516f37f412334e01e07a30a0`
- **License:** MIT
- **Current `lean-toolchain`:** `leanprover/lean4:v4.27.0-rc1`
- **Current Mathlib revision:** `ae0143cded18d09875e12c3056f428090484d9a4`

The repository README still says Lean 4.18.0, while the checked-out toolchain is
4.27.0-rc1. Reservoir reports that commit `0bbb899` fails to build on that
toolchain. The project under audit uses Lean 4.28.0 and Mathlib
`8f9d9cff6bd728b17a24e163c9402775d9e6a365`. Therefore the public repository is
evidence that the formalization source exists, but it is not presently a
verified compatible dependency.

## Mathlib Pull Requests

The formalization is split across an open PR stack. The central portals are:

- [#39920: PF for primitive matrices](https://github.com/leanprover-community/mathlib4/pull/39920)
- [#39922: PF for irreducible matrices](https://github.com/leanprover-community/mathlib4/pull/39922)
- [#39918: core nonnegative-matrix lemmas](https://github.com/leanprover-community/mathlib4/pull/39918)
- [#39919: Collatz–Wielandt and Perron-root bounds](https://github.com/leanprover-community/mathlib4/pull/39919)
- [#39921: uniqueness of the Perron eigenvector](https://github.com/leanprover-community/mathlib4/pull/39921)
- [#39923: spectral dominance for irreducible matrices](https://github.com/leanprover-community/mathlib4/pull/39923)

As audited on 3 July 2026, #39920 and #39922 are open, have no recorded review
decision, and their build checks are failing. #39922 explicitly depends on
#39918 and #39921; #39920 depends on #39919.

The precursor irreducibility/primitivity definitions were merged in
[#28728](https://github.com/leanprover-community/mathlib4/pull/28728), which
explains why those definitions are present in the pinned Mathlib while the PF
existence results are absent.

## Theorem Locations

The external repository contains these candidate declarations:

| File | Declaration | Relevant output |
|---|---|---|
| `.../PerronFrobenius/Primitive.lean` | `Matrix.exists_positive_eigenvector_of_primitive` | Positive eigenvalue and strictly positive right eigenvector |
| `.../PerronFrobenius/Irreducible.lean` | `Matrix.exists_positive_eigenvector_of_irreducible` | Positive eigenvalue and strictly positive right eigenvector |
| `.../PerronFrobenius/Irreducible.lean` | `Matrix.pft_irreducible` | Unique normalized eigenvector in `stdSimplex` |
| `.../PerronFrobenius/Dominance.lean` | `Matrix.perronRoot_transpose_eq` | Same Perron root for `A` and `Aᵀ` |
| `.../PerronFrobenius/Dominance.lean` | `Matrix.perron_root_eq_positive_eigenvalue` | Identifies a positive eigenvalue with the Perron root |

The core irreducible existence statement has the interface:

```lean
theorem Matrix.exists_positive_eigenvector_of_irreducible [Nonempty n]
    (hA_irred : A.IsIrreducible) :
    ∃ (r : ℝ) (v : n → ℝ),
      0 < r ∧ (∀ i, 0 < v i) ∧ A *ᵥ v = r • v
```

Here `Matrix.IsIrreducible` already includes entrywise nonnegativity.

## Dependency Status

- **Pinned Mathlib:** irreducibility and primitivity definitions are present;
  PF existence, positivity, uniqueness, and Perron-root transpose equality are
  not present.
- **Mathlib master integration:** under review in an open PR stack.
- **External repository:** source found, but not verified compatible with the
  project pins and reported failing by Reservoir.
- **Import probe:** deliberately skipped because the theorem dependency is not
  locally available.

## Relevance

The external interface is close to the H-Tilt obstruction. Apply the
irreducible theorem to `A` for the positive right mode and to `Aᵀ` for a
positive left mode. Use Perron-root transpose equality, or a separate finite
pairing argument, to align the eigenvalues. Then a Matrix wrapper can feed the
result to the existing survivor-law cancellation.

This applies naturally to a discrete-time nonnegative matrix. It does not
directly apply to a killed generator with potentially negative diagonal
entries.
