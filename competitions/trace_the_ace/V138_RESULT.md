# V138 result — Joint effect field

## Frozen verdict

`CLOSE_TWO_LITERAL_APPLICABILITY_SPACE`

The precommitted two-literal applicability language is not admitted.

## Verified metrics

- V97 LL: `0.5392345448672131`
- Full V135 LL: `0.5374633492487556`
- Full V135 gain: `+0.0017711956184575106`
- V138 pair-gated LL: `0.5373080052672911`
- V138 pair gain vs V97: `+0.0019265395999220614`
- Incremental vs full V135: `+0.00015534398146455075`
- Equal-capacity shuffled-selector LL: `0.5382827410326881`
- Advantage vs shuffled selector: `+0.0009747357653970834`
- Pair coverage: `0.6436473540145985`
- Folds beating V135: `2 / 4`
- All folds non-regressive vs V97: `true`

## Residual structure

Despite failing admission, all four untouched meta-folds independently selected effectively the same rule family:

`support_log <= ~6.08 AND prior_disp > ~0.116`

with outer coverage about 64.3–64.5% in every fold.

This is stronger structural recurrence than V137's unstable one-scalar rules, and the real selector substantially outperformed equal-capacity shuffled selectors. However, the effect was not large or fold-consistent enough to satisfy the frozen admission rule.

## Retained law

`NOT_SUPPORTED_UNDER(two_literal_current_observable_applicability,V137_OOF,shuffle_control)`

with a secondary retained observation:

`STABLE_BUT_UNADMITTED_INTERACTION(support_log_low_or_mid, prior_displacement_nontrivial)`

The observation is hypothesis-generating only. It must not be promoted or threshold-tuned post hoc.

## Next controller state

- PUSH: full V135 remains the admitted candidate law.
- READ: V138 found stable joint geometry but insufficient causal/fold-level gain.
- DIAGNOSE: current observable applicability is structured but not sufficient for robust selective deployment.
- ZOOM: stop increasing router capacity over the same six fields.
- NEXT QUESTION: what mechanism makes objective-prior displacement useful specifically under non-saturated support, and can that mechanism be represented directly rather than routed indirectly?
