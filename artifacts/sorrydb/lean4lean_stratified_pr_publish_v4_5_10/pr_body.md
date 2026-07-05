## Summary

This removes one `sorry` in `Lean4Lean/Experimental/StratifiedUntyped.lean`, in the `constDF` case of `IsDefEq.inductionU1`.

The proof works by binding the recursive induction hypotheses explicitly in the `constDF` case pattern, then using the Γ-level induction hypothesis in reverse through `hdf`.

## Verification

Checked locally:

    lake build Lean4Lean.Experimental.StratifiedUntyped
    lake build

Both passed.

Note: the repository still contains unrelated existing `sorry`s in other files; this PR only removes the target `sorry` in `StratifiedUntyped.lean`.
