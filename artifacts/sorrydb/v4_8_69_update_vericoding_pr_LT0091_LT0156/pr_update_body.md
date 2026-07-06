This removes twenty-two local `sorry` placeholders from generated specification index-bound proofs.

Certified locally with:

    lean specs/LT0009_specs.lean
    lean specs/LT0032_specs.lean
    lean specs/LT0049_specs.lean
    lean specs/LT0091_specs.lean
    lean specs/LT0156_specs.lean
    lean specs/LT0380_specs.lean
    lean specs/LT0400_specs.lean
    lean specs/LT0401_specs.lean
    lean specs/LT0402_specs.lean
    lean specs/LT0428_specs.lean
    lean specs/LT0445_specs.lean
    lean specs/LT0479_specs.lean
    lean specs/LT0480_specs.lean
    lean specs/LT0505_specs.lean
    lean specs/LT0506_specs.lean
    lean specs/LT0513_specs.lean

Summary:

- `LT0009_specs.lean`: diagflat flattened matrix diagonal/offdiagonal bounds.
- `LT0032_specs.lean`: diagonal `Fin (min rows cols)` index bounds.
- `LT0049_specs.lean`: delete left/right successor index bounds.
- `LT0091_specs.lean`: unpackbits fixed-width flattened index bound.
- `LT0156_specs.lean`: ifftshift modulo index bound.
- `LT0380_specs.lean`: Chebyshev derivative coefficient source-index bound.
- `LT0400_specs.lean`: Chebyshev 1D zero-index bound.
- `LT0401_specs.lean`: Chebyshev 2D flattened index bound.
- `LT0402_specs.lean`: Chebyshev 3D flattened index bound.
- `LT0428_specs.lean`: HermiteE 2D coefficient flattening bound.
- `LT0445_specs.lean`: Hermite multiplication-by-x if-branch bounds.
- `LT0479_specs.lean`: Laguerre 2D flattened index bound.
- `LT0480_specs.lean`: Laguerre 3D flattened index bound.
- `LT0505_specs.lean`: Legendre 2D zero-index positivity and flattened index bound.
- `LT0506_specs.lean`: Legendre 3D zero-index positivity and flattened index bound.
- `LT0513_specs.lean`: polynomial derivative coefficient source-index bound.

Sorry/admit delta across changed files:

    -22
