# Hyperintensional Identity

MathGraph does not identify objects merely because they share extension,
examples, truth values, coverage, or table behavior.

This matters for roots, reasons, obstructions, formal worlds, and theory
objects:

- same extension is not same law;
- same coverage is not same reason;
- same table behavior is not same root;
- same truth value is not same continuation.

`HyperintensionalIdentityMode` and `ExtensionalCollapsePolicy` make collapse
policy explicit. The default is `NEVER_BY_DEFAULT`. Merge only when equivalence
is verified, a DomainKernel declares a safe extensional identity rule, or a
canonical objectification map explicitly supplies the identity.
