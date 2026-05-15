# DomainKernels

A `DomainKernel` is MathGraph's lightweight registry object for a formal world.
It records the world's native language, host verifier, semantic embedding style,
ontology summary, source URI, and trust policy.

MathGraph generalizes a simple pattern:

- **DomainKernel**: the registered formal world.
- **HostVerifier**: Isabelle, Lean, Python finite checker, Z3, or another host.
- **SemanticEmbedding**: how the domain is represented in the host.
- **ImportedTheoryObject**: axioms, definitions, theorems, propositions, terms,
  proof artifacts, refutation artifacts, abstract objects, and similar nodes.
- **ImportedTheoryRelation**: typed dependencies between theory objects.
- **Certificate**: a verified terminal artifact, still distinct from metadata.
- **RootNode / ReasonNode**: compressive advisory structures over certificates.

Truth boundary:

DomainKernel registration is metadata, not proof. Imported theory objects are
trusted only according to explicit trust and provenance fields. Root, reason,
and obstruction advice remains advisory unless backed by certificate chains.
Proof authority stays with the host verifier and imported certificate/proof
artifacts.

## Typed metadata

DomainKernels may be accompanied by semantic embedding risk metadata, bounded
language fragments, formal worlds, paradox guards, typed objects, denotation
records, and theory-objectification maps. These rows make the formal-world
boundary explicit.

Registering a kernel, encoding a property, or importing an object-theory
metadata row does not verify a target theorem. Host-logic proof becomes
target-logic proof only when proof transport or native verification is explicit
and low risk.

Local theory scanners and registries can index declarations and proof-method
infrastructure, but those rows remain advisory until connected to verified
export artifacts and validated host/object theorem links.

## Workbench metadata

DomainKernels may point at workbench, lifecycle, embedding strategy,
faithfulness, benchmark, and default formal-world metadata. Faithfulness rows
reduce bridge risk only when they carry sound support. Benchmarks are regression
evidence, not proof. Logic combinations remain advisory until interaction
semantics and conflict policy are assessed.

Proof motif and lemma-candidate rows may attach to a DomainKernel as proof-side
search pressure. They do not change the DomainKernel truth policy: candidate
cuts require explicit verifier results before promotion.
