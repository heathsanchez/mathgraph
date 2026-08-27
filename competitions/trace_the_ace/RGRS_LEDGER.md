# Trace the Ace — Residual-Guided Representation Search Ledger

This ledger applies Residual-Guided Representation Search (RGRS) to the Trace the Ace programme. The purpose is to prevent blind search inside a representation after repeated evidence says the missing information is representational.

## Frozen current baseline

- Public champion retained architecture: V75 canonical trajectory, public log loss 0.6047.
- Primary unseen proxy: exact objective-cold validation.
- V75 objective-cold aggregate: ~0.59235.
- V81 best blend objective-cold: ~0.59097.
- Promotion target: several-thousandths objective-cold improvement with no regression in the official runtime/independence gates before spending a full public submission.

## Residual records

### TTA-ρ-001 — Generic semantics does not recover mastery

`rho = (R6 Representation, semantic prediction layer, V78 MiniLM standalone ~0.7145 and only ~0.0004 gain when blended with V75, objective-cold, high)`

Material interventions inside the old text-prediction representation:
- frozen MiniLM semantic view;
- retrieval/learning-gain semantic view (V79).

Both are weak standalone and only add a small orthogonal residual correction.

**Decision:** do not classify the main gap as R1 search. More generic embedding capacity is not justified by the residual.

### TTA-ρ-002 — Hard target scoping loses useful information

`rho = (R5 Applicability, lesson-segment scoping, target-only V81 ~0.5991 worse than whole-session ~0.5924 while blended whole+target+phase reaches ~0.5910, objective-cold, high)`

Observed separator:
- 91.6% of examples are multi-segment;
- target region averages ~32.1% of session;
- deleting non-target context hurts;
- exposing target context alongside whole context helps.

**Decision:** target scoping is conditionally useful. Search for the predicate/weight governing when evidence belongs to the assessed objective; do not globally discard the rest of the session.

### TTA-ρ-003 — Tutor feedback is not equivalent to mastery evidence

`rho = (R6 Representation, evidence object, transcript audit contains label-0 sessions ending in strong tutor praise and label-1 sessions with later unrelated failures, audited examples, high)`

The current text representation conflates:
- student-generated competence evidence;
- tutor evaluation language;
- assistance supplied before an answer;
- later unrelated lesson performance.

The language cannot cleanly state the distinction needed to explain the residual.

**Representation candidate:** replace transcript-as-example with an objective-conditioned evidence graph/state sequence.

### TTA-ρ-004 — Large supervised encoder on CPU is an infrastructure failure

`rho = (R10 Infrastructure, V82 ModernBERT-large execution, hours-long CPU runner without deciding result, GitHub Actions CPU environment, high)`

**Decision:** draw no semantic conclusion about supervised transformers from V82 runtime. Use a feasible domain encoder (V83) or GPU for the large-model hypothesis.

## Current primary residual

The strongest current diagnosis is:

`R6 Representation + R5 Applicability`

The missing object is not "better transcript semantics". It is approximately:

`EvidenceEvent = (objective_match, phase, question, student_answer, assistance_before_answer, correction_state, independence, transfer, position)`

with an objective-conditioned state trajectory:

`K_pre -> K_guided -> K_independent -> K_application`

and an applicability predicate deciding which events should influence the assessed objective.

## Smallest deciding representation test

### Hypothesis H85

An explicit objective-conditioned student-evidence representation will outperform an otherwise matched representation that includes tutor-evaluation wording as first-class predictive text.

### One intervention

Create an `EvidenceEvent` view from the existing transcript while holding vectorizer/model/folds/hyperparameters fixed.

### Frozen arms

- **A0 — V75/V81-style text evidence:** existing whole + target + canonical views.
- **A1 — Student-evidence IR:** objective-matched question -> student-answer episodes, phase tags, assistance tags, canonical state, whole-context summary; tutor praise removed from raw predictive text.
- **A2 — Causal ablation:** same as A1 but remove assistance/independence tags while preserving all event text and ordering.

### Opposing discriminators

1. Cases where tutor praise is high but independent student evidence is weak: A1 should improve over A0.
2. Cases where independent evidence is strong but later unrelated struggle exists: A1 should preserve/promote probability relative to target-only deletion.
3. Cases with no meaningful target evidence: A1 should not manufacture confidence; A0 behavior/prior should be preserved.

### Primary metric

Exact objective-cold log loss, frozen folds.

### Precommitted interpretation

- A1 beats A0 by >= 0.003 and A2 materially weakens the gain -> **clean mechanism win; escalate representation**.
- A1 beats A0 by < 0.001 -> **insufficient; preserve negative law**.
- A1 helps only a subset -> **R5 Applicability; learn/certify event activation predicate**.
- A1 wins but A2 is equal -> **causal attribution fails; do not admit assistance/independence tags**.

## Current live experiments

### V83 — TalkMove-BERT supervised

Purpose: test whether domain-matched tutoring-language supervision supplies a useful semantic layer once V81 structure is exposed.

RGRS classification before result: **R1/R6 separator test**, not an admitted representation change.

If V83 is weak, generic/model-capacity search is further demoted and the programme should prioritize explicit evidence-state IR.

### V84 — Student evidence ablation

Purpose: preliminary test of the TTA-ρ-003 hypothesis by suppressing raw tutor-praise language and retaining student/objective evidence.

RGRS classification: **R6 candidate separator**.

## Admission gate for a new Trace-the-Ace representation

A proposed representation is retained only when all hold:

1. **Semantic/data-contract gate** — legal competition features only; no test adaptation/leakage; official runtime contract passes.
2. **Causal gate** — removing the proposed representational feature materially weakens the gain.
3. **Predictive resource gate** — frozen primary metric improves; no post-hoc metric switching.
4. **Reproducibility gate** — same commit/folds/config reproduces and official inference remains sample-independent.

State machine:

`PROPOSED -> SEPARATED -> VERIFIED -> ADMITTED`

otherwise:

`REJECTED` or `OBSTRUCTED`.

## Governing law for this competition

> Never add model capacity merely because the score is imperfect when repeated residuals show that the model is being asked to predict mastery from the wrong object.

The current highest-value search direction is therefore:

`raw transcript -> objective-conditioned evidence events -> assistance/independence-aware knowledge state -> calibrated predictor`

not:

`raw transcript -> larger generic embedding -> classifier`.
