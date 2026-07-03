# Finite H-Tilt Survivor Law: Verified Theorem Tower v1

## Summary

This PR packages a three-layer Lean-verified theorem tower for finite H-Tilt
survivor laws.

## Verified layers

- Layer 1: conditional killed-generator algebra
- Layer 2: conditional discrete Doob algebra
- Layer 3: Perron–Frobenius discrete portal

## Trust boundary

- Main proof files compile under Lean 4.28.0.
- The PF portal compiles under the HopfieldNet exact pins.
- The promoted PF theorem has no `sorryAx` dependency.
- The external subtree has one unrelated `sorry`; this PR does not claim
  global cleanliness of that subtree.

## Tests

- Full pytest: 1774 passed
- Lean replay commands are recorded in the release bundle.

## Non-claims

No killed-generator bridge, Markov convergence, ergodicity, mixing, spectral
gap, empirical h-band, consciousness, or scheduler performance claim is made.

## Review focus

Please check:

- theorem-tower boundary wording;
- axiom-audit wording;
- absence of overclaim drift;
- replay commands;
- Lawbook entries.
