# Replay and Route Plasticity

MathGraph treats continuation traces as learning pressure. A replay does not
make a claim true; it tests whether a previously useful construction route still
produces verifier-acceptable certificates near the same residual membrane.

## Concepts

**Continuation trace**: a record of the source node, target node, constructor,
features, outcome, and certificate or obstruction status for an attempted route.

**Route plasticity**: the scheduler's ability to strengthen, weaken, split, or
hold routes based on replay outcomes.

**Replay as law distillation**: successful replay can expose a reusable law-like
construction pattern, but the pattern remains advisory until terminal
certificates are produced.

**Failures as prediction errors**: repeated structured failure is evidence that
the route's current representation is wrong or incomplete.

**Near misses as constructor pressure**: a near miss at the residual membrane
should be preserved for future replay, simplification, or bounded escalation.

## Edge Fields

Route-plasticity edges should preserve:

- source node
- target node
- route type
- constructor attempted
- features used
- success/failure
- certificate status
- obstruction status
- residual compression
- novelty
- reuse count
- near-miss score

## Update Logic

Verified certificate found:
: strengthen route.

Structured repeated failure:
: weaken route and create an obstruction candidate.

Near miss at residual membrane:
: preserve and promote for replay.

Large residual compression:
: strongly promote.

Trivial success:
: weakly promote.

## Advisory Boundary

Route weights are scheduling pressure, not truth. They may affect what
MathGraph tries next, but they must not change terminal form, trust level, or
provenance.
