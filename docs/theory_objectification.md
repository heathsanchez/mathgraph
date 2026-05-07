# Theory Objectification

Theory objectification records how a domain theory maps symbols, propositions,
finite structures, witnesses, definitions, and theorems into MathGraph objects.

Examples:

- In ETP, the magma operation objectifies as a binary operation object of type
  `<i,i>`.
- An equation objectifies as a proposition-like object of type `<>`.
- A finite countermodel witness objectifies as a theory-relative assignment.
- In AOT, a theorem or definition can be registered as imported formal-world
  metadata before any proof artifact is imported.

Objectification records are not terminal certificates. Analytic readings are
authoritative only when their denotations are known to denote and when a verifier
or imported proof artifact supplies the appropriate trust.

Non-denoting and unknown-denoting terms are stored as advisory metadata only.
