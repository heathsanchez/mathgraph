# MathGraph SorryDB v4.7.3 — FormalBook PR136 Closeout

## Public PR ledger

### 1. `teorth/equational_theories#1461`

- title: Prove Law43 term definability from swapped arguments
- state: OPEN
- url: https://github.com/teorth/equational_theories/pull/1461
- mergeStateStatus: CLEAN
- reviewDecision: 
- comments: 0
- reviews: 0

Outcome: live upstream PR; leave open for review.

### 2. `mo271/FormalBook#136`

- title: Prove edge cardinality step in Chapter 28 handshaking lemma
- state: CLOSED
- url: https://github.com/mo271/FormalBook/pull/136
- mergeStateStatus: DIRTY
- reviewDecision: 
- comments: 1
- reviews: 0

Outcome: closed by author.

Reason: the proof was valid against the SorryDB snapshot commit
`865934361ca7005e0a874efb39f5809117052e85`, but current `mo271/FormalBook:main`
already has no `sorry` in `FormalBook/Chapter_28.lean`, making the PR obsolete rather
than mergeable.

## Verified artifact retained

- artifact: `artifacts/sorrydb/official_formalbook_ch28_edgecard_patch011_v4_6_15`
- snapshot verifier: `lake build FormalBook.Chapter_28`
- status: verified replay certificate on SorryDB snapshot
- upstream status: obsolete on current main

## Campaign rule learned

A SorryDB repair can be a valid replay certificate even if upstream current main already fixed the
target. Public PRs should be opened only after checking whether the target still exists on current
main.

## Next policy

Before creating any future PR:

1. Verify the target sorry exists on current upstream main.
2. Patch from current upstream main, not the SorryDB snapshot.
3. Use the SorryDB snapshot only as the replay target when measuring benchmark validity.
4. Keep one clone, one cache, one focused probe batch, then cleanup.
