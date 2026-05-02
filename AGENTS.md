# AGENTS.md

Canonical instructions for coding agents working on MathGraph.

## Core Identity

MathGraph is a lightweight generative verification kernel for verifiable
mathematics and trustworthy AI. It is not a passive database and not a static
encyclopedia.

MathGraph represents axioms, definitions, theorems, proofs, transformations,
finite countermodels, obstructions, and verification traces as typed semantic
graph objects.

## Terminal Forms

Every accepted claim must end in exactly one terminal form:

- `VERIFIED_PROOF`
- `FINITE_COUNTERMODEL`
- `NAMED_OBSTRUCTION`

Candidate status and verified status must never be confused. A candidate,
search hit, heuristic result, partial derivation, failed route, or unverified
external output is not an accepted claim.

Finite-search failure is not proof. Exhausting a bounded search only records what
that search did or did not find; it does not establish a theorem unless a
verified proof route certifies the claim.

## Product Scope

SAIR Stage 2, equational implication over magmas, is the first practical
testbed. It is not the whole product. Keep the repository shaped as a general
MathGraph kernel.

## Repository Discipline

Keep source code, tests, docs, and small manifests in GitHub. Keep generated
artifacts in Google Drive or external artifact storage.

Do not add large generated files to the repository. This includes ledgers, run
directories, archives, Lean build outputs, `.parquet`, `.sqlite`, `.npy`, and
other bulky experiment outputs.

Prefer small typed modules, focused tests, explicit manifests, and reproducible
verification traces. Avoid hidden assumptions: encode assumptions in types,
metadata, manifests, docs, or tests.

Any new feature must add or update tests.

## Architecture

The intended flow is:

```text
Kernel -> Routes -> Constructors -> Verification Adapters -> Terminal Forms -> Ledger/Graph Store
```

- `Kernel`: owns accepted claims and enforces the terminal-form contract.
- `Routes`: describe the verification path being attempted.
- `Constructors`: build candidate proofs, countermodels, obstructions, or traces.
- `Verification Adapters`: check candidates with finite models, proof assistants,
  or external theorem provers.
- `Terminal Forms`: collapse accepted claims into exactly one accepted outcome.
- `Ledger/Graph Store`: records accepted certificates and typed graph structure.

## Setup

```bash
pip install -e ".[dev]"
pytest
```
