# MathGraph SorryDB v4.8.28 - ArkLib QueryPhase Length Probe

## Result

Baseline build did not complete successfully, so no proof replacement was certified.

No source changes were kept.

## Candidate

Repository:

    Verified-zkEVM/ArkLib

File:

    ArkLib/ProofSystem/Binius/BinaryBasefold/QueryPhase.lean

Target:

    have h_f_i_on_fiber_length: f_i_on_fiber.length = 2 ^ ϑ := by
      sorry

## Certification rule

A replacement is certified only if:

    lake build ArkLib.ProofSystem.Binius.BinaryBasefold.QueryPhase succeeds
    and sorry/admit count decreases
    and no new sorry/admit is introduced
