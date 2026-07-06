This removes nine local `sorry` placeholders from generated specification index-bound proofs.

Certified locally with:

    lean specs/LT0032_specs.lean
    lean specs/LT0401_specs.lean
    lean specs/LT0479_specs.lean
    lean specs/LT0480_specs.lean
    lean specs/LT0505_specs.lean
    lean specs/LT0506_specs.lean

Summary:

- `LT0032_specs.lean`: diagonal `Fin (min rows cols)` index bounds.
- `LT0479_specs.lean`: Laguerre 2D flattened index bound.
- `LT0480_specs.lean`: Laguerre 3D flattened index bound.
- `LT0401_specs.lean`: Chebyshev 2D flattened index bound.
- `LT0505_specs.lean`: Legendre 2D zero-index positivity and flattened index bound.
- `LT0506_specs.lean`: Legendre 3D zero-index positivity and flattened index bound.

Sorry/admit delta across changed files:

    -9
