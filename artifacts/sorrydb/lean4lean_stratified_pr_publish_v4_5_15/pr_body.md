## Summary

This removes one `sorry` in `Lean4Lean/Experimental/Stratified.lean`, in the `constDF` case of `IsDefEq.induction1`.

This is the typed/stratified analogue of #14. The proof binds the recursive induction hypotheses explicitly in the `constDF` case pattern and uses the Γ-level induction hypothesis in reverse through `hdf`.

A first attempt with an explicit universe argument failed because it over-constrained the type index. Letting Lean infer the `.defeq` universe argument resolves the index.

## Verification

Checked locally:

    lake build Lean4Lean.Experimental.Stratified
    lake build

Both passed.

Note: the repository still contains unrelated existing `sorry`s in other files; this PR only removes the target `sorry` in `Stratified.lean`.
