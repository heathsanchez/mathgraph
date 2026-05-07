# Paradox Guards

Paradox guards are lightweight pre-verification safety checks. They exist because
semantic embeddings, comprehension principles, lambda abstraction, definite
descriptions, and complex terms can create artifact risk if treated naively.

Current guards are metadata and pattern checks only:

- Denotation/free-logic guardrails for complex terms.
- Host-artifact guards for semantic embedding transport risk.
- Set-collapse guards for extensional collapse hazards.

A guard can pass, warn, or block a candidate. A passing guard is not a theorem.
A blocked guard is not a refutation. Guards only shape safe construction and
import policy before a verifier decides.
