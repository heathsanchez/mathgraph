# V139 precommit — Component-specific applicability

## Controller continuation
V138 closed the generic two-literal *whole-V135* gating language under its frozen admission rule, but all four meta-folds independently selected the same interaction family: `support_log <= q80 AND prior_disp > q20`, with ~64% coverage. The selector improved overall LL slightly versus full V135 and beat the equal-capacity shuffled selector, but only 2/4 folds beat V135.

## Residual
The joint geometry is stable, but applying it to the entire V135 operator may discard the independently useful V75+RELATED composition outside the region.

## Diagnosis
Primary: component applicability. Secondary: composition representation. This is not a new generic router search.

## Strongest rival
The V138 interaction is incidental selection structure; component-specific application will not improve full V135 and any gain will be matched by a random same-coverage prior mask.

## K(rho)
An admissible intervention must:
1. retain exact V97 fallback for unsupported objectives;
2. retain V75+RELATED composition on supported rows outside the prior region;
3. use the full V75+RELATED+objective-prior stack only inside the fixed V138-derived region;
4. use no target labels at inference;
5. beat full V135 on cross-fitted session-held-out predictions;
6. beat a matched-coverage random prior-activation control.

## Frozen operator
For each outer fold, define thresholds from outer-training runtime fields only:
- `support_log <= training q80`
- `prior_disp > training q20`

Supported outer rows satisfying both receive the full V135 stack. Other supported rows receive the composition-only V75+RELATED stack. Unsupported rows receive exact V97.

No threshold search, no alternative conjunction, no tree/router, no post-result tuning.

## Control
Within each untouched outer fold, randomly permute the binary prior-activation mask across supported rows, preserving the exact number of prior-enabled rows. Apply full V135 on the shuffled mask and composition-only elsewhere. Fixed seed 20260823.

## Action table
PROMOTE_COMPONENT_LAW if:
- incremental gain vs full V135 >= 0.0005;
- advantage vs matched random control >= 0.0005;
- >=3/4 folds beat V135;
- all folds non-regress vs V97.

RETAIN_COMPONENT_SIGNAL if incremental gain > 0, control advantage >= 0.0002, and >=3/4 folds beat V135.

Otherwise CLOSE_COMPONENT_APPLICABILITY_HYPOTHESIS.

## Epistemic status
V139 is a second-generation mechanism test induced by V138 on the same 35,072-row corpus. Even a pass is not final untouched admission; it must subsequently survive competition-shaped/runtime verification.

## Retention
The run saves OOF predictions for V97, composition-only, full V135, V139, and matched random control so future tests do not need to rebuild the full transcript matrices merely to analyze this component law.
