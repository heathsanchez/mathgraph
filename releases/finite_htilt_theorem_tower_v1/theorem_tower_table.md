# Theorem Tower Table

| Layer | Artifact | Environment | Assumptions | Verified conclusion | Non-claims |
|---|---|---|---|---|---|
| 1 — Conditional killed-generator algebra | `finite_htilt_survivor_law_v1` | Lean 4.28.0; Mathlib `8f9d9cff…` | Finite real data; explicit left/right eigen-equations; nonzero denominators | Generator-style stationary weight, normalized stationary identity, and zero row sums | No PF existence or convergence |
| 2 — Conditional discrete Doob algebra | `finite_htilt_discrete_doob_stationary_v1` | Lean 4.28.0; Mathlib `8f9d9cff…` | Discrete left/right eigenmodes; explicit positivity and matrix nonnegativity for the stochastic package | Nonnegative row-stochastic Doob matrix and strictly positive normalized stationary distribution | Modes remain assumptions |
| 3 — Discrete PF portal | `finite_htilt_pf_discrete_survivor_law_v1` | HopfieldNet exact pins; Lean 4.27.0-rc1 | Finite nonempty index type; irreducible nonnegative real matrix | Positive Perron modes exist and produce the Layer 2 stochastic package | No killed-generator bridge, convergence, mixing, or Lean 4.28 compatibility claim |
