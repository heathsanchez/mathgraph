# Theory Registry

The theory registry stores advisory metadata for formal theories:

- axioms, definitions, theorems, lemmas, and world declarations;
- proof methods and method-like infrastructure;
- inference rules and rewrite/intro/elim metadata.

Registry rows are imported formal-world metadata. They are not MathGraph
terminal certificates unless later connected to verified proof artifacts or
finite refutation certificates.

The registry makes the host/object boundary explicit: a host theorem, method,
or declaration is not automatically a target-theory theorem.
