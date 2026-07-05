# SorryDB v4.4.58 — Target #2 Scout, Fixed Search

v4.4.57 produced no candidates because the GitHub search query was passed as one quoted argument and GitHub parsed qualifiers incorrectly.

This run fixes the search path by using `gh api search/code` with a raw `q` field.
