# DomainKernels

A `DomainKernel` is MathGraph's lightweight registry object for a formal
world. It records the world's native language, host verifier, semantic
embedding style, ontology summary, source URI, and trust policy.

This layer is motivated by Abstract Object Theory (AOT): a target
philosophical/formal world embedded into Isabelle/HOL by a shallow semantic
embedding. AOT shows that a domain can have native objects, relations,
definitions, axioms, theorems, proof artifacts, and verifier-specific trust
rules.

MathGraph generalizes that pattern:

- **DomainKernel**: the registered formal world.
- **HostVerifier**: Isabelle/HOL, Lean, Python finite checker, Z3, or other host.
- **SemanticEmbedding**: how the domain is represented in the host.
- **ImportedTheoryObject**: axioms, definitions, theorems, propositions, terms,
  proof artifacts, refutation artifacts, abstract objects, and similar nodes.
- **ImportedTheoryRelation**: typed dependencies between theory objects.
- **Certificate**: a verified terminal artifact, still distinct from metadata.
- **RootNode / ReasonNode**: compressive/advisory structures over certificates.

Truth boundary:

DomainKernel registration is metadata, not proof. Imported theory objects are
trusted only according to explicit trust and provenance fields. Root, reason,
and obstruction advice remains advisory unless backed by certificate chains.
Proof authority stays with the host verifier and imported certificate/proof
artifacts.

## v16.10 typed metadata

DomainKernels may now be accompanied by semantic embedding risk metadata,
bounded language fragments, formal worlds, paradox guards, typed objects,
denotation records, and theory-objectification maps. These rows make the
formal-world boundary explicit.

The key distinction is still the truth boundary: registering a kernel, encoding
a property, or importing an object-theory metadata row does not verify a target
theorem. Host-logic proof becomes target-logic proof only when proof transport
or native verification is explicit and low risk.
