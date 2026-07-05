# Lawbook Obstruction Entry — Law46 leaf/leaf semantic-canonicalization boundary

Equation46_termDefinableFrom_equalShape partially repairs, but should be parked.

Accepted local repairs:

- rhs leaf extraction;
- distinctness of variables from disjointness;
- rewriting the law to Lf x ≃ Lf y.

Remaining obstruction:

    forall {G : Type} [Magma G], G models Lf x ≃ Lf y -> G models Law46

The direct route fails because hG remains an opaque satisfiesPhi proposition rather than reducing to equality.

The canonical route fails because MagmaLaw.toFin creates dependent Fin elems.length types that do not transport cheaply to Law2.

Classification:

    OBSTRUCTED: semantic implication / dependent canonicalization boundary

Reusable portal needed:

    lemma satisfies_leaf_law_iff ...

or:

    lemma two_leaf_law_toFin_toNat_eq_Law2 ...
