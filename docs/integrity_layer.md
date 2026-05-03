# Integrity Layer

MathGraph includes a lightweight integrity layer for mathematical traces. It
uses content-addressed traces, Merkle audit summaries, and replayable
verification records. This is not cryptocurrency. There is no token, consensus
network, mining, or economic protocol.

The goal is reproducibility: every accepted claim should be traceable from
stable hashes, ledgers, certificates, and verification records. A trace hash
commits to the serialized route record. A certificate hash commits to the
terminal certificate payload. A JSONL ledger can be summarized by a Merkle root
so a run can be checked without rereading every line.

The replay path is:

```text
Trace -> Certificate -> Hash -> Ledger -> Merkle Root -> Replay -> Audit
```

Candidate status and verified status remain distinct. Hashing a candidate does
not make it true. A Merkle root proves integrity of recorded bytes, not
mathematical validity. MathGraph still requires accepted claims to terminate as
exactly one of:

- `VERIFIED_PROOF`
- `FINITE_COUNTERMODEL`
- `NAMED_OBSTRUCTION`

Generated ledgers and run outputs should live outside GitHub. The repository
stores source code, tests, docs, and small manifests.
