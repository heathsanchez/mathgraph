# MathGraph SorryDB v4.8.32 - vericoding LTvander Index Bound Probes

## Result

NO_CERTIFIED_VARIANT

## Repository

Beneficial-AI-Foundation/vericoding-benchmark

## Targets

specs/LT0479_specs.lean:

    have h_idx : idx < (xdeg + 1) * (ydeg + 1) := by sorry

specs/LT0480_specs.lean:

    have h_idx : idx < (xdeg + 1) * (ydeg + 1) * (zdeg + 1) := by sorry

## Certification rule

Certified iff:

    lean target succeeds
    and total file sorry/admit count decreases
    and no new sorry/admit is introduced

## Accepted variants

LT0479:

    

LT0480:

    

## Probe table

See:

    probe_results.tsv
