# MathGraph SorryDB v4.7.0 — PR Watch + Next Target Scout

## Current public proof-repair ledger

1. `teorth/equational_theories#1461`
   - Law43 term definability from swapped arguments.
   - Local and GitHub verified.
   - Status: awaiting upstream review/merge.

2. `mo271/FormalBook#136`
   - Chapter 28 handshaking lemma edge-cardinality sorry repair.
   - Local verifier: `lake build FormalBook.Chapter_28`.
   - Status: opened upstream.

## Next target policy

Do not start another heavy build until a target satisfies:

- one local `sorry`;
- small theorem body;
- module-level build target identifiable;
- no giant import-boundary uncertainty;
- proof likely reducible to one typed residual;
- PR would be small and reviewable.

## Disk rule

Do not run repeated `lake exe cache get` in fresh clones.
Use one clone, one cache, one focused probe batch, then cleanup.

