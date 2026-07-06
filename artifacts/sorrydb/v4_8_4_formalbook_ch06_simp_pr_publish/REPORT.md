# MathGraph SorryDB v4.8.4 — FormalBook Chapter 06 Simp PR Publish

## Target

FormalBook/Chapter_06.lean, theorem h_lamb_gt_q_sub_one.

## Patch

Replace one local calculation-chain sorry with:

    by simp

## Verifier

    lake build FormalBook.Chapter_06

## Provenance

Discovered by v4.8.2/v4.8.3 current-main micro-probes.
