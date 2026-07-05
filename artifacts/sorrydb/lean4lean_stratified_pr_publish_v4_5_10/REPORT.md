# SorryDB v4.5.10 — lean4lean PR Publish

## Result

- module build return code: 0
- full build return code: 0
- push return code: 128
- PR create return code: 127
- status: BUILD_VERIFIED_PR_MANUAL_OR_PUSH_FAILED
- PR URL/output: 

## Patch

Branch:

    sorrydb-fix-stratified-constdf

Commit:

    fddde29e12f8974b9c464a16819525dd4db3df7b

## Note

v4.5.9 falsely marked the build as failed because it used Bash PIPESTATUS handling from zsh. v4.5.10 uses direct bash commands and captures return codes safely.

## Manual PR fallback

If PR did not open automatically, push branch manually and use pr_body.md.
