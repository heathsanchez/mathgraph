# SorryDB v4.4.77 — Active Sorry Scout

## Purpose

Rerun target scout with Lean comment stripping so commented-out `sorry` tokens are not counted.

## Exclusions

- equational_theories/Definability/Law43.lean
- equational_theories/Definability/Law46.lean

## Result

- active candidate count: 0
- comment-only false positives: 1
- status: NO_ACTIVE_TARGET_FOUND

## Recommended Next Target

None. After excluding solved Law43 and parked Law46, no active non-comment `sorry` target was found in `equational_theories/**/*.lean`.

## Comment-only False Positives

- equational_theories/FactsSyntax.lean raw=1 active=0