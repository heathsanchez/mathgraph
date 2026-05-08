# Continuation Traces

A continuation trace is the memory unit of lawful search:

```text
claim
→ detected root/basin
→ route/constructor attempted
→ verifier/importer outcome
→ certificate or obstruction/residual
→ residual compression / near-miss / route update signal
```

Continuation traces are memory, not truth. They record how MathGraph reached a
certificate, obstruction, near miss, or residual so that later runs can replay
and compare routes without confusing scheduling pressure for verification.

## Why Route Memory Matters

MathGraph should learn the routes by which truth and refutation become
reachable. A terminal certificate answers one claim; a trace records the path
that made the answer reachable. Repeated traces can show which roots, basins,
and constructors bear weight.

## Schema Overview

A trace records:

- claim identity, source, target, and optional equation indices;
- root label, basin label, detector score, and detector evidence;
- route type, constructor family, and constructor configuration;
- terminal contract fields from the verifier/importer outcome when available;
- certificate id or obstruction label;
- attempted, verified, promoted, and known-skipped flags;
- near-miss score, residual compression delta, novelty score, elapsed time;
- warnings and evidence.

The first store is append-only JSONL through `ContinuationTraceStore`.

## Replay Logic

The replay engine groups traces by:

```text
root_label + constructor_family + route_type
```

Successful verified/promoted traces strengthen routes. Structured repeated
failure becomes obstruction pressure. High near-miss routes are preserved for
replay. Low-value repeated residual routes are weakened.

## Route Plasticity

Route plasticity is advisory update of scheduling pressure. It may change which
constructor MathGraph tries next, but it never changes terminal form, trust
level, provenance, or verifier boundary.

## Advisory Boundary

Replay output is advisory unless backed by terminal certificates. A failed trace
is not proof. A near miss is not a certificate. Terminal truth still requires
verified proof, finite refutation/importer revalidation, or named obstruction
under the existing contract.
