# Trace the Ace — Unseen Log-Loss Plan

## Primary objective

The optimization target is **minimum log loss on genuinely unseen/private evaluation data**. Public leaderboard movement, AUC, model novelty, and write-up appeal are secondary. A change is retained only when it improves robust out-of-sample probability quality or provides a clearly orthogonal signal that improves a validated ensemble.

Formally, prefer models that minimize expected unseen log loss and avoid catastrophic regime failures:

`E[-y log p - (1-y) log(1-p)]`

Promotion requires evidence across multiple plausible test regimes, not merely a better mean on one split.

## Validation hierarchy

Every material experiment should report at least:

1. **Session-cold grouped OOF** — no session leakage.
2. **Objective-cold grouped OOF** — exact skills held out.
3. **Hard/rare-objective stress** — long-tail objectives receive explicit scrutiny.
4. **Fold dispersion / worst-fold loss** — a large mean gain that creates a catastrophic regime is not automatically promoted.
5. **Calibration diagnostics** — log loss is the target; overconfident mistakes matter more than ranking gains.

When historical public scores are available, use them only to audit whether a validation regime is predictive of transfer. Do not derive inference-time constants from leaderboard feedback.

## Measured anchor — V74 objective difficulty

Full 35,072-row training evaluation on 2026-08-15 established V74 as a mandatory independent prior:

- session-grouped global-prior log loss: **0.608771**
- session-grouped V74 hierarchical log loss: **0.552734**
- delta: **-0.056037**
- session-fold range: **0.548964 to 0.554711**
- objective-cold global-prior log loss: **0.611715**
- objective-cold semantic V74 log loss: **0.601736**
- objective-cold delta: **-0.009980**

V74 uses no transcripts. The session-cold gain shows objective difficulty is a very large component of the target; the objective-cold gain shows semantic transfer between objective descriptions is real but materially weaker and regime-dependent. V74 is therefore an **anchor/prior**, not a complete solution. Every transcript branch should now be measured primarily by residual log-loss improvement beyond leakage-safe V74 OOF predictions.

Aggregate result: `results/v74_full_training_oof_2026-08-15.json`.

## Priority order

### P0 — Preserve strong baselines and validation integrity

- Keep the best historical lexical/model predictions as an independent view.
- Keep V74 as a mandatory objective-difficulty prior.
- Reconstruct exact OOF predictions whenever possible.
- Do not accumulate features by version number.
- Reject interventions that improve one regime while materially degrading plausible unseen regimes unless they add independently validated ensemble value.

### P1 — High-signal transcript preprocessing / measurement

Before larger-model work, convert raw dialogue into cleaner evidence of student knowledge while preserving educationally meaningful variation.

1. **Conservative speaker-role repair**
   - retain original role, repaired role, and repair confidence;
   - never globally flip speakers from weak evidence.

2. **Interaction episode segmentation**
   - tutor question -> student answer -> feedback/correction/hint -> retry;
   - preserve chronological links between retries and feedback.

3. **Student-vs-tutor evidence separation**
   - tutor exposition is context;
   - student production is mastery evidence;
   - tutor-confirmed student correctness is weak supervision.

4. **Low-information turn down-weighting**
   - greetings, connection checks, scheduling, generic acknowledgements and boilerplate receive low mastery weight rather than blind deletion.

5. **Objective-conditioned relevance**
   - rank episodes by semantic relevance to each learning objective;
   - retain prerequisite/follow-up context when it helps objective transfer.

6. **Assistance / independence canonicalization**
   - distinguish independent correct, correct after prompt, correct after hint, copied/repeated answer, self-correction, unresolved error, repeated error, agreement-only, tutor exposition.

7. **Chronology and terminal-state emphasis**
   - represent transitions such as ERROR -> HINT -> INDEPENDENT_CORRECT;
   - terminal independent evidence should be available explicitly, not lost in bagged text.

8. **Math surface normalization with raw-text preservation**
   - normalize Unicode operators, spacing, simple fraction/decimal variants where safe;
   - keep original wording as an additional view.

9. **Multiple retained views**
   - raw transcript;
   - student-only transcript;
   - objective-local transcript;
   - canonical episode sequence;
   - terminal mastery window.

The rule is: **remove nuisance variation, not educational variation**.

### P2 — V71 mastery-event branch

Extract objective-conditioned micro-assessments and aggregate trajectory features. Evaluate whether these events improve unseen log loss **beyond V74 OOF**, not merely beyond a global prior.

### P3 — V72 hidden-supervision audit

Quantify:

- multi-objective session frequency;
- same-session mixed outcomes;
- opposite-label contrastive pairs;
- micro-assessment density;
- rare-objective structure.

Use this only to determine whether the richer training formulations have enough support.

### P4 — V73 same-session contrastive mastery

Exploit pairs from the same transcript with different objective outcomes. Same-session differencing suppresses generic session ability and forces the model toward objective-specific mastery evidence.

Primary question: does the contrastive residual improve held-out row log loss when added to V74 plus the strongest transcript evidence?

### P5 — V74 semantic/hierarchical objective difficulty — PROMOTED ANCHOR

Model objective difficulty explicitly and shrink rare objectives toward semantically related objectives. Exact objective identity should not be required for useful predictions.

Measured full-data results promote this branch as an independent probability prior. Future work should preserve its OOF predictions and train transcript models on its residuals or combine through leakage-safe stacking.

### P6 — V75 canonical student-state trajectory

Current transcript priority before larger pretrained models.

Canonical event alphabet should include at minimum:

- INDEPENDENT_CORRECT
- CORRECT_AFTER_PROMPT
- CORRECT_AFTER_HINT
- SELF_CORRECTION
- TUTOR_CORRECTION
- UNRESOLVED_ERROR
- REPEATED_ERROR
- AGREEMENT_ONLY
- TUTOR_EXPOSITION
- TRANSFER_SUCCESS when reliably detectable

For each `(session, objective)`, output both the ordered event sequence and compact numeric summaries: terminal state, number of hints, recurrence, recency, independence, correction distance, and objective relevance.

Compare raw/localized lexical views against canonical-state views under identical folds, always reporting incremental log loss beyond V74.

### P7 — Semantic objective-conditioned retrieval

Only after P1-P6 are measured. Use a compliant pretrained encoder to retrieve the most objective-relevant episodes from long transcripts. Larger models are justified only if they improve unseen log loss over cheaper lexical/event retrieval.

### P8 — Latent student-state model

Combine distinct factors rather than forcing one text classifier to infer all of them implicitly:

`logit P(correct) = objective_difficulty + session_state + objective_mastery + contrastive_residual + calibrated_residual_views`

Session state must be inferable from the individual test sample at inference time; no cross-test aggregation is allowed.

### P9 — Heterogeneous ensemble and calibration

Retain only genuinely different information channels, e.g.:

- robust lexical baseline;
- V74 hierarchical objective prior;
- mastery trajectory;
- contrastive residual;
- semantic retrieval/encoder signal.

Fit ensemble weights strictly OOF. Optimize log loss directly. Test temperature/logit scaling, isotonic or other calibration only when fitted without leakage and when improvement is stable across validation regimes.

### P10 — Submission discipline

Full submissions are scarce and should answer causal transfer questions, not tune small hyperparameters.

A candidate is submission-worthy only when:

- its unseen-oriented validation is materially better;
- no major plausible regime collapses;
- calibration improves or remains safe;
- runtime and code-execution constraints are satisfied;
- the inference path processes each test sample independently as required by the rules.

## Promotion rule

Default decision hierarchy:

1. Lower aggregate session-cold log loss **relative to V74 plus the strongest retained base**.
2. Lower or non-inferior hard/rare/objective-cold loss.
3. Lower worst-fold / tail risk.
4. Better calibration, especially fewer high-confidence errors.
5. Orthogonal residual value in a strictly OOF ensemble.
6. Only then consider runtime, elegance, interpretability, or write-up value.

A model that looks clever but worsens expected unseen log loss is rejected.

## Current working decomposition

The leading hypothesis is:

`P(next correct | transcript, objective)`

should be decomposed into:

- `D_o`: semantic objective difficulty — **measured and promoted via V74**;
- `A_s`: broad session/student competence state;
- `M_so`: objective-specific mastery evidence;
- `C_so`: same-session contrastive residual;
- `T_so`: trajectory / independence / recency.

The transcript is therefore treated as a measurement instrument for latent student state, not merely as a document to classify.

## Immediate next experiment

**V75/V71 residual-on-V74 is now the next decisive experiment.** Use the transcript archive plus the official feature/label CSVs to generate identical session folds and compare:

1. V74 OOF anchor;
2. V74 + V71 numeric mastery features;
3. V74 + raw/localized lexical transcript view;
4. V74 + V75 canonical trajectory;
5. V74 + lexical + V75;
6. add V73 contrastive residual.

Use identical frozen folds and save OOF predictions for stacking. Promote only on unseen-oriented log-loss evidence.
