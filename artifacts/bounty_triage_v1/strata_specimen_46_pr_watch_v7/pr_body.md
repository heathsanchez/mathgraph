Draft progress for #45.

This PR adds a proof-carrying `LawfulScorable` interface next to the existing executable `Scorable` typeclass.

What is included:

- `combine` should not strictly improve the left score
- `isBetter` should be transitive
- `empty` should be a left and right identity for `combine`
- `worst` should not beat a real candidate
- `badness` should be monotone with `isBetter`

Local verification:

- `lake env lean Specimen/Scoring.lean` passes
- `lake build` passes

I kept this as a separate law class rather than modifying `Scorable`, so existing scoring strategies remain executable/lightweight and proof-carrying code can request the stronger interface explicitly.

Important design note: the issue text says `worst` must be worse than any real schedule. The current instances use finite sentinels such as `1000`, so a strong global law like “every score beats worst” may not hold for unbounded scores. This draft therefore uses the safer law “worst does not beat a candidate” while leaving open whether the final fix should use bounded laws or a true top sentinel.

Next step after feedback: add `LawfulScorable` instances or refine the `worst` law to match the intended branch-and-bound invariant.

Refs #45.
