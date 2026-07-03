# Finite H-Tilt PF Portal Addendum

This directory contains the companion note:

> *A Lean-Verified Perron–Frobenius Portal for Finite H-Tilt Survivor Laws*

Build with a standard LaTeX installation:

```bash
cd papers/finite_htilt_pf_portal
pdflatex finite_htilt_pf_portal.tex
pdflatex finite_htilt_pf_portal.tex
```

The note presents the three-layer theorem tower and its trust boundary. The PF
layer is verified under HopfieldNet commit
`0bbb8999d1703776516f37f412334e01e07a30a0`, Lean 4.27.0-rc1, and Mathlib
`ae0143cded18d09875e12c3056f428090484d9a4`.

The source intentionally makes no claim about a killed-generator bridge,
Markov convergence, mixing, empirical h-band behavior, consciousness, or
scheduler performance.
