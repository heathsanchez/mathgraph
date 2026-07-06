# MathGraph SorryDB v4.8.20R - Recovered Chapter03 Line173 Certificate

## Incident

The v4.8.20 run accepted a proof variant, then the pasted shell script stopped because interactive zsh treated an inline `#` comment as a command.

Observed interruption:

    zsh: command not found: #

## Certified result before interruption

Target:

    FormalBook/Chapter_03.lean

Local hole:

    have h_2k'len : 2 * k' ≤ n := by
      sorry

Accepted replacement:

    have h_2k'len : 2 * k' ≤ n := by
      omega

Verifier:

    lake build FormalBook.Chapter_03

Result:

    v01_line173_only_omega    rc 0    sorry delta -1

## Certification rule

This is certified because:

1. build succeeded;
2. the replacement introduced no new `sorry` or `admit`;
3. total file sorry/admit count decreased.

## Relation to v4.8.19B

v4.8.19B separately certified the earlier local hole:

    have h_3lel : 3 ≤ l := by
      omega

Together these suggest a two-hole Chapter03 patch should be tested and then published as a PR if the combined build succeeds.
