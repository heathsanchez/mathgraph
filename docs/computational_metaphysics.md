# Computational Metaphysics and MathGraph

Daniel Kirchner's Isabelle/HOL embedding of Edward Zalta's Abstract Object
Theory is a close cousin of MathGraph's long-term architecture. AOT implements
major parts of a formal metaphysical theory inside a host verifier with custom
syntax and mechanically checked internal theorems.

AOT is one formal world. MathGraph is a metakernel for many formal worlds.

The architectural lesson is direct:

- a target theory can be embedded into a host verifier;
- the host can be Isabelle/HOL, Lean, Python finite checker, Z3, or another
  trusted execution environment;
- the target theory has native objects, relations, definitions, axioms,
  theorem statements, proof artifacts, and trust rules;
- MathGraph should register such worlds, import verified artifacts, and connect
  them to claims, certificates, roots, reasons, obstructions, and lawbook
  memory.

Compactly:

> AOT proves that a metaphysical world can be formalized. MathGraph should prove
> that formalized worlds can compound.

This repo currently registers AOT as metadata only. It does not clone AOT, run
Isabelle, extract theorem dependencies, or verify AOT claims.

v16.10 adds the typed predication and objectification substrate suggested by
that precedent: encoding/exemplification, denotation status, bounded fragments,
formal worlds, and artifact-risk metadata. The substrate is deliberately
conservative: same extension is not same law, and a host theorem is not a
target-theory theorem until transport or native checking is explicit.

The AOT scanner indexes `.thy` and `.ML` declarations as advisory theory
registry rows only. It does not run Isabelle and does not make AOT theorems
verified inside MathGraph.
