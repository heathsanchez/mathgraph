# Derived False Elevation

Derived false rows are logical consequences of already verified certificates,
but they are not automatically concrete finite certificates.

For target strengthening, if `A ⇏ B` and `C => B`, then `A ⇏ C`: a witness that
violates `B` also violates the stronger target `C`. In v16.6.2 this was
certificate-preserving by seed-table replay for the sampled artifacts.

For source weakening, if `B => A` and `B ⇏ C`, then `A ⇏ C` is logically sound,
but the original table must be replayed or reconstructed. A table satisfying
`B` satisfies `A`; however, external elevation artifacts showed that source
weakening often needs source-preserving countermodel construction before it can
be called `FINITE_VERIFIED`.

The rule is strict:

- logical derived false row: derived-chain evidence only
- replay-elevated row: finite table/witness revalidated
- failed elevation: obstruction pressure, not truth
- finite search miss: residual evidence, not proof

The v16.6.1 audit found zero elevated rows when primitive table payloads were
not available. The v16.6.2 table-aware audit elevated 401,742 of 500,000
attempted derived false rows with zero sampled matrix contradictions.
