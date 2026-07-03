# Verify killed-generator bridge from discrete PF portal

## Goal

Build the next theorem boundary after `finite_htilt_theorem_tower_v1`.

The current release verifies:

1. conditional killed-generator-style algebra;
2. conditional discrete Doob algebra;
3. Perron–Frobenius discrete portal for irreducible nonnegative finite
   matrices.

The remaining bridge is:

```text
killed_generator_bridge_from_discrete_pf
```

## Problem

The PF portal applies to finite irreducible nonnegative discrete matrices
$A$. A killed generator or generator-style operator may have negative
diagonal entries, so the discrete PF theorem does not directly apply.

## Candidate routes

### Route A — Shift bridge

Construct $A = cI + K$ with $c$ large enough to make $A$ entrywise
nonnegative.

Questions:

- What hypotheses on $K$ make such a finite $c$ easy to construct?
- Does irreducibility transfer from $K$'s off-diagonal graph to $A$?
- How do eigenvectors and eigenvalues transform?
- Does the Doob transform induced by $A$ correspond to the generator-style
  transform for $K$?

### Route B — Exponential bridge

Construct $A = \exp(tK)$.

Questions:

- Is finite matrix exponential available and usable in Mathlib?
- Does positivity/nonnegativity transfer under Metzler or generator
  assumptions?
- Does irreducibility transfer?
- Do eigenvectors transfer?

### Route C — Resolvent bridge

Construct $A = (\alpha I-K)^{-1}$.

Questions:

- What invertibility and positivity hypotheses are needed?
- Is inverse positivity formalized?
- Do eigenvectors transfer?

## Preferred first route

Start with Route A, the shift bridge, because it is algebraically finite and
likely cheapest.

## Definition of done

A Lean theorem, separate from the v1 release, proving one explicit bridge from
a generator-style operator to the discrete PF portal.

Minimum acceptable target:

Under explicit finite hypotheses on $K$ and $c$, $A=cI+K$ is nonnegative and
irreducible, the PF portal applies to $A$, and the resulting survivor modes
correspond to eigenmodes of $K$ with shifted eigenvalue.

## Non-claims

This issue does not ask for:

- Markov convergence;
- ergodicity;
- mixing;
- spectral gap;
- empirical h-band;
- consciousness;
- scheduler performance.

## Kill condition

Park if:

- the bridge requires broad analytic machinery;
- Mathlib lacks required finite matrix support;
- positivity/irreducibility transfer becomes larger than the theorem tower
  itself.

This is issue draft text only. No GitHub issue has been created.
