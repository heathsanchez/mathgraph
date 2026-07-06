# MathGraph SorryDB v4.8.28R - ArkLib Timeout Disk Rescue

## Reason

v4.8.28 attempted a baseline build for:

    Verified-zkEVM/ArkLib
    ArkLib.ProofSystem.Binius.BinaryBasefold.QueryPhase

The baseline build timed out after 1200 seconds before reaching the target module.

## Classification

    BASELINE_TIMEOUT_OBSTRUCTION

No proof probe was certified.

## Rescue

Removed ArkLib build artifacts from the persistent clone to recover disk.

## Disk law

Do not build ArkLib again on this machine unless there is substantially more free disk/time or a narrower prebuilt cache path.
