# Typed Predication Kernel

MathGraph v16.10 adds a typed predication substrate inspired by AOT-style object theory.
It lets the repository represent formal objects, their types, and the difference between
two predication modes:

- **Exemplification**: an object instantiates a property, such as a verified finite
  certificate exemplifying `terminal_form = FINITE_COUNTERMODEL`.
- **Encoding**: an abstract graph object carries or characterizes a property, such
  as a root node encoding `table_motif = projection_left`.

Encoding is not truth. Exemplification is not automatically verification. A
predication fact becomes authoritative only when it is backed by safe trust,
safe provenance, and known denotation.

The typed layer supports relational type expressions such as `i`, `<>`, `<i>`,
`<i,i>`, `<<i>>`, and `<<i,i>>`. These are enough to register the ETP magma
nursery and AOT-style object-theory metadata without importing Isabelle or
claiming target-theory authority.

Hyperintensional identity is explicit. Same extension is not same law; same
coverage is not same reason; same table behavior is not same root; same truth
value is not same continuation.
