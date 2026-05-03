# Architecture

The initial repository keeps the kernel small:

- `mathgraph/` contains the core term, equation, graph, certificate, and kernel
  objects.
- `adapters/` contains boundary code for finite magmas, Lean, and external
  theorem provers.
- `examples/` contains runnable demonstrations.
- `scripts/` is reserved for future Colab-friendly scripts.
- `tests/` contains pytest coverage for the current contract.

The first implemented route is finite magma countermodel checking. Lean and ETP
adapters are placeholders that return named obstructions until real integrations
exist.

## v0.1 Flow

```text
Kernel -> Routes -> Constructors -> Verification Adapters -> Terminal Forms -> Ledger/Graph Store
```

The integrity spine adds replayable audit records around that flow:

```text
Trace -> Certificate -> Hash -> Ledger -> Merkle Root -> Replay -> Audit
```

The v0.1 `Kernel.prove(source, target=None)` route set is intentionally narrow:

- exact equation match
- sides swapped
- skeleton-preserving variable renaming
- finite magma countermodel search over registered small tables

If none of those routes terminates, the kernel returns `NAMED_OBSTRUCTION`.
That obstruction records a failed route set; it is not a proof and not a truth
claim.

JSONL ledgers store content-addressed traces. Replaying a ledger recomputes
trace hashes and a Merkle root so later systems can verify what was actually
claimed without committing generated run files to GitHub.

## CertificateCorpus-Assisted Kernel Replay

`CertificateCorpus` is an optional in-memory replay/query layer for imported
terminal traces. A `Kernel` may receive a corpus and consult it before local
routes run. This is replay support, not a passive database mode.

Corpus lookup is conservative:

- source/target index matches are preferred when supplied
- exact equation-string matches are checked next
- claim-hash matches are checked last
- only `VERIFIED_PROOF` / `VERIFIED` and `FINITE_COUNTERMODEL` / `REFUTED`
  traces with certificates can terminate the claim
- `NAMED_OBSTRUCTION`, pending rows, failed searches, and ambiguous records are
  never promoted
- conflicting verified corpus hits return a named obstruction instead of
  silently choosing one

Returned corpus traces are copied and annotated with lookup metadata such as
`corpus_hit`, `corpus_lookup_mode`, and `corpus_trace_hash`. If the kernel has a
ledger, the replayed trace is appended like any other `Kernel.prove` result.
