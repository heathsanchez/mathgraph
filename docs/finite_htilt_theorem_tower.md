# Finite H-Tilt Theorem Tower

The tower separates three verified claims by operator class, hypotheses, and
Lean environment. A higher layer may discharge assumptions of a lower layer,
but it does not retroactively enlarge that layer's claim.

## Layer 1: Conditional killed-generator algebra

**Artifact:** `finite_htilt_survivor_law_v1`

**What it proves:** Given finite real-valued data `K`, `lambda`, `q`, and `h`
satisfying explicit left and right eigen-equations, the generator-style Doob
transform has zero row sums and the biorthogonal weight
`piStar ∝ q ⊙ h` is stationary.

**Boundary:** The modes `q,h` are assumed. There is no Perron–Frobenius
existence theorem at this layer and no Markov convergence conclusion.

## Layer 2: Conditional discrete Doob algebra

**Artifact:** `finite_htilt_discrete_doob_stationary_v1`

**What it proves:** Given `rho,q,h` satisfying discrete left and right
eigen-equations,

```text
D_ij = A_ij h_j / (rho h_i)
```

has row sums one and `piStar` is stationary. Under explicit positivity of
`rho,q,h` and entrywise nonnegativity of `A`, the kernel entries are
nonnegative, `piStar` is strictly positive, and `piStar` sums to one.

**Boundary:** The scalar and modes are assumed. Perron–Frobenius existence is
not proved unless Layer 3 is invoked.

## Layer 3: Discrete PF portal

**Artifact:** `finite_htilt_pf_discrete_survivor_law_v1`

**What it proves:** For an irreducible nonnegative real matrix on a finite
nonempty index type, Perron–Frobenius theory supplies a shared `rho > 0`, a
strictly positive right mode `h`, and a strictly positive transpose-right mode
`q`. Consequently, the discrete Doob transform is a nonnegative row-stochastic
matrix and

```text
piStar_i = q_i h_i / sum_k q_k h_k
```

is a strictly positive normalized stationary distribution.

**Boundary:** This theorem is verified in the quarantined external exact-pin
environment: HopfieldNet commit
`0bbb8999d1703776516f37f412334e01e07a30a0`, Lean 4.27.0-rc1, Mathlib
`ae0143cded18d09875e12c3056f428090484d9a4`. It does not supply a
killed-generator bridge or a convergence theorem.

The external PF subtree contains one unrelated `sorry`; Lean's exact axiom
audit for the promoted theorem contains no `sorryAx`. The artifact claims a
clean dependency graph for the promoted theorem, not global
placeholder-freedom of the external repository.

## Remaining Named Obstructions

- `killed_generator_bridge_from_discrete_pf`: a killed generator may have
  negative diagonal entries and needs a verified shift, exponential, or
  resolvent bridge.
- `markov_convergence_not_proved`: stationarity alone gives no convergence,
  mixing time, limiting-law uniqueness, or spectral gap.
- `spectral_gap_not_proved`: no quantitative spectral separation is in the
  theorem tower.
- `empirical_h_band_not_proved`: empirical calibration is separate from the
  formal theorem boundary.
- `consciousness_not_proved`: no consciousness interpretation is licensed.
- `scheduler_performance_not_proved`: scheduler experiments and promotion
  remain separate.
