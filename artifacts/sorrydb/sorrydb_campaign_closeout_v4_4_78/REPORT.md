# SorryDB v4.4.78 — Campaign Closeout

## Verdict

Close the current SorryDB campaign on the pinned `teorth/equational_theories` commit.

## Target Commit

Repository: teorth/equational_theories  
Commit: b1cc1756202d7f44e07bd4069b5df16901a36938

## Outcome

The campaign produced:

1. One solved upstream-ready target.
2. One named obstruction with accepted local repairs.
3. Zero remaining active non-comment sorry targets after exclusions.

## Solved

### Law43

File:

    equational_theories/Definability/Law43.lean

Theorem:

    Equation43_termDefinableFrom_swapped_args

Status:

    SOLVED

Artifact:

    artifacts/sorrydb/patch022_final_clean_v4_4_56

Upstream PR:

    https://github.com/teorth/equational_theories/pull/1461

## Parked / Obstructed

### Law46

File:

    equational_theories/Definability/Law46.lean

Theorem:

    Equation46_termDefinableFrom_equalShape

Status:

    NAMED_OBSTRUCTION

Artifact:

    artifacts/sorrydb/law46_named_obstruction_v4_4_75

Accepted local repairs:

- Patch002: rhs-is-leaf
- Patch005: hxy : x != y
- Patch006: L = Lf x ≃ Lf y

Remaining obstruction:

    semantic implication / dependent canonicalization boundary

The hard boundary is not a small missing simp. It sits around:

- satisfiesPhi opacity for leaf laws;
- MagmaLaw.toFin dependent Fin index transport;
- Law2 canonicalization.

Return to Law46 only after building a reusable semantic or transport lemma.

## Active Sorry Exhaustion

Artifact:

    artifacts/sorrydb/active_sorry_scout_v4_4_77

Result:

    active candidate count: 0

One apparent sorry remained in FactsSyntax.lean, but v4.4.77 showed it is inside a comment block and is not an active Lean sorry.

## Campaign Status

    CAMPAIGN_CLOSED_ON_PINNED_COMMIT

## Next Best Move

Do not continue blind SorryDB patching on this pinned commit.

Choose one of:

1. Monitor current upstream for new sorries.
2. Start a new verifier campaign.
3. Build the reusable Law46 portal lemma:
   satisfies_leaf_law_iff or two_leaf_law_toFin_toNat_eq_Law2.
