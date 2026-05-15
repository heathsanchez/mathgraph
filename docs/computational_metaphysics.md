# Computational Metaphysics and MathGraph

Formal worlds can be embedded into host proof systems while preserving an
explicit trust boundary. MathGraph treats such worlds as registrable domains,
not as borrowed architecture.

The architectural lesson is direct:

- a target theory can be embedded into a host verifier;
- the host can be Isabelle, Lean, a Python finite checker, Z3, or another
  trusted execution environment;
- the target theory has native objects, relations, definitions, axioms,
  theorem statements, proof artifacts, and trust rules;
- MathGraph should register such worlds, import verified artifacts, and connect
  them to claims, certificates, roots, reasons, obstructions, and Lawbook
  memory.

This repo currently stores formal-world metadata only. It does not clone
external theories, run proof assistants on their behalf, extract theorem
dependencies, or verify their claims automatically.

Typed predication and objectification provide conservative substrate:
encoding/exemplification, denotation status, bounded fragments, formal worlds,
and artifact-risk metadata. Same extension is not same law, and a host theorem
is not a target-theory theorem until transport or native checking is explicit.

The formal workbench records layered workbench metadata, embedding strategy
profiles, faithfulness assessments, backend profiles, benchmark suites,
correspondence claims, and interpretation choice points. Those rows make bridge
risk visible; they do not turn metadata into target-theory theorems.

Local theory scanners index source declarations as advisory registry rows only.
They do not run a proof assistant and do not make external theorems verified
inside MathGraph.
