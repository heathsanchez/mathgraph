This removes four local `sorry` placeholders from generated specification index-bound proofs.

Certified locally with:

    lean specs/LT0032_specs.lean
    lean specs/LT0479_specs.lean
    lean specs/LT0480_specs.lean

Summary:

- `LT0032_specs.lean`: proves diagonal index bounds from `i : Fin (min rows cols)` using `omega`.
- `LT0479_specs.lean`: proves the flattened 2D index bound with an explicit `Nat` multiplication calculation.
- `LT0480_specs.lean`: proves the flattened 3D index bound by reducing to a row bound and extending by the z dimension.

Sorry/admit delta across changed files:

    -4
