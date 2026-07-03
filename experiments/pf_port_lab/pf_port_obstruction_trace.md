# PF Port Obstruction Trace

## Outcome

The bounded port succeeded. No active obstruction prevents use of the PF
existence portal in the quarantined external-pin environment.

## Attempt trace

1. Cloned `mkaratarakis/HopfieldNet` at
   `0bbb8999d1703776516f37f412334e01e07a30a0`.
2. Confirmed toolchain `leanprover/lean4:v4.27.0-rc1` and Mathlib
   `ae0143cded18d09875e12c3056f428090484d9a4`.
3. Began a targeted source build of
   `MCMC.PF.LinearAlgebra.Matrix.PerronFrobenius.Irreducible`.
4. Stopped the inefficient source build after 670 successful targets because
   the broad `Mathlib.Tactic` import expanded the closure to 3,246 jobs.
5. Attempted Mathlib's exact-revision binary cache. The first attempt exhausted
   disk space during decompression.
6. Removed only disposable failed-cache data, generated `.lake` output, and
   cloned upstream `docbuild` trees. No project source or user artifact was
   removed.
7. Retried the exact cache with 7.6 GB free; all 7,868 cache files unpacked.
8. Built the irreducible PF target successfully: 3,239 jobs.
9. Built the dominance target successfully: 3,245 jobs.
10. Compiled the local existential PF survivor portal successfully.

## Minimal built external closure

The external PF subtree contains 16 Lean files. The built route to the portal
used 12 external support/PF files:

- `MCMC/PF/Topology/Compactness/ExtremeValueUSC.lean`
- `MCMC/PF/Data/List.lean`
- `MCMC/PF/LinearAlgebra/Matrix/Spectrum.lean`
- `MCMC/PF/aux.lean`
- `MCMC/PF/Combinatorics/Quiver/Path.lean`
- `MCMC/PF/LinearAlgebra/Matrix/PerronFrobenius/Lemmas.lean`
- `MCMC/PF/LinearAlgebra/Matrix/PerronFrobenius/CollatzWielandt.lean`
- `MCMC/PF/LinearAlgebra/Matrix/PerronFrobenius/Primitive.lean`
- `MCMC/PF/LinearAlgebra/Matrix/PerronFrobenius/Uniqueness.lean`
- `MCMC/PF/LinearAlgebra/Matrix/PerronFrobenius/Irreducible.lean`
- `MCMC/PF/Analysis/CstarAlgebra/Classes.lean`
- `MCMC/PF/LinearAlgebra/Matrix/PerronFrobenius/Dominance.lean`

This is below the 20-file kill threshold.

## Trust-boundary trace

A source scan found one `sorry` at
`MCMC/PF/Combinatorics/Quiver/Path.lean:1112`. That declaration is unrelated
to the compiled PF portal route. Lean's exact axiom audit reported:

```text
#print axioms HTiltPFDiscreteSurvivor.exists_positive_stationary_distribution_of_irreducible

'HTiltPFDiscreteSurvivor.exists_positive_stationary_distribution_of_irreducible'
depends on axioms: [propext, Classical.choice, Quot.sound]
```

There is no `sorryAx` dependency. The Lawbook entry records this precision and
does not claim the entire external subtree is placeholder-free.

## Normalization replay

For the stronger normalized portal, replaying the entire 7,868-file Mathlib
cache again exceeded the available disk headroom. The cache tool was instead
given the 30 direct Mathlib roots imported by the 12-file external closure. It
downloaded 3,218 cached files, after which the `Dominance` module and the
strongest normalized portal theorem compiled successfully. This is the
preferred bounded replay route.

## Remaining portability boundary

The portal is verified under the external repository's own Lean 4.27.0-rc1 and
Mathlib pin. It has not been ported into the main Lean 4.28.0 project. That is a
packaging/portability task, not an existence-theorem obstruction.
