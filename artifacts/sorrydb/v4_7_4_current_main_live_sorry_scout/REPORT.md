# MathGraph SorryDB v4.7.4 — Current-Main Live-Sorry Scout

## Purpose

Find next upstream PR-clean target only among sorries that still exist on current upstream main.

## Selection criteria

Prefer targets with:

- one local `sorry`;
- small theorem body;
- clear module-level build;
- no stale snapshot drift;
- likely proof reducible to one typed residual;
- small, reviewable PR.

## Exclusions

- stale SorryDB snapshot targets already fixed on current main;
- comment-only `sorry`;
- intentional examples/tests;
- huge theorem projects requiring broad architectural work;
- targets requiring repeated fresh `lake exe cache get`.
