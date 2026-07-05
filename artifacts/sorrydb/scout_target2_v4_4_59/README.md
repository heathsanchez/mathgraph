# SorryDB v4.4.59 — Target #2 Scout, Search API GET

v4.4.57 failed because `gh search code` query qualifiers were malformed.
v4.4.58 failed because `gh api search/code -f ...` defaulted to POST, causing 404.

This run uses:

    gh api --method GET search/code -f q=... -F per_page=50

Goal: find a real public Lean 4 active sorry target for the next external repair.
