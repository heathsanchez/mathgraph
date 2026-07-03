# Remaining Boundaries

## `killed_generator_bridge_from_discrete_pf`

**Why open:** The PF portal applies to nonnegative discrete matrices. A killed
generator may have a negative diagonal.

**What would close it:** One separately verified route:

- shift bridge: `A = cI + K`;
- exponential bridge: `A = exp(tK)`;
- resolvent bridge: `A = (alpha I - K)^{-1}`.

This release does not choose a route.

## `markov_convergence_not_proved`

**Why open:** A stationary distribution does not imply convergence from an
arbitrary initial state.

**What would close it:** A verified finite-chain convergence theorem with
explicit hypotheses connected to the Doob matrix.

## `ergodicity_not_proved`

**Why open:** No irreducibility/aperiodicity-to-ergodicity theorem is invoked
for the constructed Doob matrix.

**What would close it:** A verified ergodicity theorem and proofs that its
hypotheses hold for this construction.

## `mixing_not_proved`

**Why open:** The tower has no quantitative convergence rate.

**What would close it:** A verified mixing bound under explicit spectral or
minorization hypotheses.

## `spectral_gap_not_proved`

**Why open:** Positive Perron modes do not by themselves provide a quantitative
spectral gap.

**What would close it:** A verified spectral-separation theorem for the
relevant operator class.

## `empirical_h_band_not_proved`

**Why open:** The tower contains no held-out calibration data.

**What would close it:** A separate preregistered empirical audit with frozen
metrics and held-out evaluation.

## `consciousness_not_proved`

**Why open:** No mathematical or empirical consciousness boundary is present.

**What would close it:** Nothing in this theorem tower; any such claim needs an
independent operational definition and evidence boundary.

## `scheduler_performance_not_proved`

**Why open:** Scheduler experiments are separate and H-Tilt was not promoted.

**What would close it:** A separate held-out scheduler benchmark satisfying its
promotion gates.
