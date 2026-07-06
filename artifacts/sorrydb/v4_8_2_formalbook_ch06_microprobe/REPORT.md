# MathGraph SorryDB v4.8.2 — FormalBook Chapter 06 Micro-Probe

## Target

Current-main live sorries in `FormalBook/Chapter_06.lean`.

## Reason

Chapter 05 top candidate appears mathematically false (`a^(p-1) = -1` instead of `1`), so it is promoted to a named obstruction rather than proof search.

Chapter 06 contains local calculation-chain sorries that are better PR candidates.

## Verifier

`lake build FormalBook.Chapter_06`
