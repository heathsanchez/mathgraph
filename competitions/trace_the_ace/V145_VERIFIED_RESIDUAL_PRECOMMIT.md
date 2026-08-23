# V145 Verified Residual Process Precommit

## Target / verifier
Primary target: beat the current ~0.5961 public log-loss leader by a clear margin while preserving competition legality and sample-independent inference.

Verifier hierarchy:
1. exact offline/runtime validity;
2. frozen full-data OOF/session-grouped evidence;
3. smoke-test score as a scarce external distribution probe;
4. public leaderboard score as final decision evidence.

Resource boundary: 2 smoke tests remain today; 3 full submissions remain before competition close. Full submissions are not to be spent on candidates supported only by tiny internal gains or smoke-only tuning.

## Current admitted state
- V97 is verified public incumbent (~0.6044).
- V135 is the strongest current lawful composition: V75 trajectory + RELATED ability + smoothed objective difficulty with exact V97 fallback for unsupported objectives.
- V135 full-data session OOF gain over V97: ~+0.001771 LL, positive in all four folds.
- V135 smoke score: 0.4674 vs V75/V97 smoke 0.4693.
- Runtime/research parity passed to numerical precision; sample-independence passed; official offline container passed.

## Current residual
The V135 capability is real and transfers to smoke, but the known gain is too small to reach #1. Applicability, simple routing, component gating, global calibration, generic semantics, timing, metadata, arithmetic verification and several relational-observable families are already closed or strongly downgraded.

The smoke shrinkage probes produced:
- shrink 0% (V135): 0.4674
- shrink 8%: 0.4675
- shrink 16%: 0.4676

Thus the first external local derivative disagrees with the full-OOF shrinkage optimum: smoke prefers stronger, not weaker, V135 composition over this interval.

## Primary diagnosis
Primary: validation/distribution geometry / composition-strength mismatch.
Secondary: possible representation insufficiency remains, but no new representation family is licensed until the current composition geometry has been decisively mapped with the remaining smoke budget.

Not currently diagnosed as:
- infrastructure failure;
- runtime failure;
- simple scalar applicability failure;
- global calibration failure.

## Live rivals
H1: The competition distribution genuinely prefers stronger movement in the V135 composition direction; modest extrapolation beyond V135 will improve smoke further.

H2: The apparent monotone smoke trend is only rounding/noise on a tiny smoke subset; +8%/+16% extrapolation will be flat or reverse.

H3: Smoke geometry differs from public geometry enough that even a positive smoke extrapolation should not by itself license a full submission.

H4: The remaining leaderboard gap is not a composition-strength problem at all; once the local curve is mapped, a larger representation/observable change is still required.

## Frozen separator
Use exactly two remaining smoke probes:
- PLUS08: 8% extrapolation beyond V135 along the same V135-minus-V97 logit direction.
- PLUS16: 16% extrapolation beyond V135 along the same direction.

No other runtime, feature, model, threshold, calibration or routing changes are allowed in these two probes.

These probes are diagnostic only. Their internal OOF values are mildly worse than V135, so neither is automatically admissible as a full submission even if smoke improves.

## Outcome -> next action table
A. Both PLUS08 and PLUS16 are >= 0.4674 (no improvement): close local composition-strength extrapolation. ZOOM OUT. Do not spend a full submission on V135 tuning.

B. PLUS08 improves but PLUS16 reverses/plateaus: fit the local smoke optimum only to locate the competition-favored composition strength. Then require a new protected internal/public-alignment test before any full submission.

C. Both improve monotonically, but total gain from 0% to +16% is <0.001: retain external-gradient law, but do not claim a #1-capable phase change. ZOOM to the next missing observable/representation while keeping the composition correction as a candidate component.

D. Both improve monotonically and the +16% gain is >=0.001: treat this as material external evidence of distribution mismatch. Freeze an interpolation/extrapolation candidate using only pre-specified curve fitting, then attack it with OOF stratification and official runtime. A full submission is allowed only if the expected public improvement plus existing V135 gain plausibly approaches the leader.

E. Surprise/non-monotone result not captured above: preserve as a new residual; do not post-hoc choose the best point and submit it.

## Attack / descaffold requirements after any apparent win
- Compare against V135, V97 and the OOF-safe region.
- Inspect per-fold and objective-frequency strata using existing saved OOF fields.
- No target labels, same-session labels or cross-test aggregation at inference.
- Keep runtime sample-independent.
- Re-run official offline container unchanged.

## Reconstruction baseline
Before claiming the retained residual process itself added value, compare the next major operator decision against a strong raw-history reconstruction: same experiment ledger and tools, but without the retained RCG/controller summary. Measure whether it reconstructs the same operator family within the same decision budget.

## Ratchet rule
Retain only causal/reproducible laws with scope and counterevidence. Current retained law from V144 shrink probes: on the smoke distribution, shrinking V135 toward V97 from 0% to 16% worsens log loss monotonically at observed precision.

## Recursion rule
The two remaining smoke results are the next verifier observations. They must update the residual field before any further candidate is designed.
