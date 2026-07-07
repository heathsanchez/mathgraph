# v8 Patch Plan if Review Requests More Substance

Current PR #46 only adds the proof-carrying `LawfulScorable` interface.

If maintainers ask for concrete instances, do not blindly prove all current laws. First split the laws by what is actually true.

Likely safe next steps:

1. Add weaker executable helper lemmas, not global instances, for the current score shapes.
2. Replace the too-strong global `worst` wording with a bounded version if maintainers care about `worst := 1000`.
3. Consider removing `badness_mono`: `badness : S → Float` is visual/UI-facing and proving Float monotonicity may be noisy and not central to branch-and-bound correctness.

Candidate bounded law shape:

    class BoundedWorstScorable (S : Type) [Scorable S] : Prop where
      withinBound : S -> Prop
      worst_loses_to_bounded :
        forall a : S, withinBound a -> Scorable.isBetter (S := S) a (Scorable.worst (S := S))

Most likely maintainer-good v8:

- keep `LawfulScorable` as interface
- remove or postpone `badness_mono`
- add comment explaining finite sentinels
- ask whether to model `worst` with `WithTop` or bounded law
