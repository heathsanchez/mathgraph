# MathGraph SorryDB v4.8.10 — FormalBook Chapter 04 trivialInvo Fixed-Point Probe

## Target

FormalBook/Chapter_04.lean, theorem trivialInvo_fixedPoints.

## Goal

    (fixedPoints (trivialInvo k)).Nonempty

## Reason

This is the next better current-main target after Chapter04 sameCard failed simple cardinality probes. It is local to the existing involution proof chain.

## Verifier

    lake build FormalBook.Chapter_04

## Expected obstruction if variants fail

This likely needs the odd-cardinality fixed-point theorem for involutions, using card_T_odd and the fact that trivialInvo is an involution on T.
