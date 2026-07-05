## Summary

This removes one `sorry` in `Lean4Lean/Experimental/StratifiedUntyped.lean`, in the `constDF` case of `IsDefEq.inductionU1`.

The missing proof is supplied by binding the recursive induction hypotheses explicitly in the `constDF` case pattern, then using the Γ-level induction hypothesis in the reverse direction through `hdf`.

## Verification

Locally checked:

    lake build Lean4Lean.Experimental.StratifiedUntyped
    lake build

Both passed.

Note: the repository still contains unrelated existing `sorry`s in other files; this patch only removes the target `sorry` in `StratifiedUntyped.lean`.
