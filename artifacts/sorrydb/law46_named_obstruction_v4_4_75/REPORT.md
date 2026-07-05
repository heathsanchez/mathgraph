# SorryDB v4.4.75 — Law46 Named Obstruction

## Verdict

Park Law46.

This is not an unproductive failure. The leaf/leaf branch produced three accepted local repairs, then hit a reusable boundary.

## Target

- Repository: teorth/equational_theories
- Commit: b1cc1756202d7f44e07bd4069b5df16901a36938
- File: equational_theories/Definability/Law46.lean
- Theorem: Equation46_termDefinableFrom_equalShape

## Accepted Local Repairs

1. Patch002 closed the first local sorry: L.rhs is a leaf when L.lhs is a leaf and hShape holds.

2. Patch005 closed hxy : x != y using disjointness of variables.

3. Patch006 closed L = Lf x ≃ Lf y by cases on L plus simplification/Aesop.

These are real reusable progress.

## Residual Goal

After the accepted local repairs and unfold implies, Patch014 showed the actual residual:

    forall {G : Type} [Magma G], G models Lf x ≃ Lf y -> G models Law46

After introducing the semantic hypothesis:

    G : Type
    M : Magma G
    hG : G models Lf x ≃ Lf y
    goal: G models Law46

After rewriting Law46.models_iff:

    hG : G models Lf x ≃ Lf y
    goal: Equation46 G

## Named Obstruction

Law46 leaf/leaf semantic-canonicalization boundary.

The proof route bottlenecks at two coupled interfaces:

1. MagmaLaw.toFin canonicalization introduces dependent Fin index types based on elems.length, so Law2.toFin and candidate.toFin.toFin do not transport by simple rewriting.

2. Direct semantic assignment does not immediately simplify hG from satisfiesPhi ... (Lf x ≃ Lf y) into the expected equality, such as a = c.

So the remaining work is not a small missing simp. It requires a reusable semantic lemma for satisfaction of leaf laws or a more principled transport lemma across MagmaLaw.toFin.

## Kill Condition

Met.

Stop spending blind variants on Law46. Return only after one of these exists:

- a reusable theorem simplifying G models Lf x ≃ Lf y;
- a reusable transport theorem for MagmaLaw.toFin across equivalent two-leaf laws;
- a direct theorem that Lf x ≃ Lf y implies Law46 under x != y.

## Next Best Move

Pick a new SorryDB target where the residual is syntactic or constructor-local, not semantic/canonicalization-heavy.
