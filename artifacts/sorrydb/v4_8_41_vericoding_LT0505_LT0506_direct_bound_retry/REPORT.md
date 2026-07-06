# MathGraph SorryDB v4.8.41 - vericoding LT0505/LT0506 Direct Bound Retry

## Result

CERTIFIED_PARTIAL_OR_FULL

## Targets

LT0505:
- zero-index positivity hole
- flattened col_idx proof, using local arrow hypothesis or certified 2D calc

LT0506:
- zero-index positivity hole
- flattened col_idx proof, using local arrow hypothesis

## Accepted variants

LT0505:

    LT0505_v01_zero_only_mul_pos

LT0506:

    LT0506_v01_zero_only_mul_pos

## Main correction after v4.8.40

The  proof is already a local arrow hypothesis for both Legendre files, so the shortest proof is expected to be:

    by assumption

The zero-index holes require positivity of products of successors, not .

## Certification rule

Certified iff:

    lean target succeeds
    and total file sorry/admit count decreases
    and no new sorry/admit is introduced
