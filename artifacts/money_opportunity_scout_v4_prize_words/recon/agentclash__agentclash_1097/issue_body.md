Epic: #1088  
Roadmap order: **8 / 14**  
Depends on: #1092, #1093, #1095, #1096

## Goal

Ship runnable reference packs that prove the RAG eval stack works end to end and provide fixtures for CI, docs, demos, and regression tests.

## MVP packs

Ship these first:

| Slug | Tiers | Purpose |
|---|---|---|
| `rag-citation-required` | A | Evidence envelope, citation schema, retrieval hit |
| `rag-faithfulness-v2` | A+B | Grounded QA with citations and advisory judge metrics |
| `rag-abstention` | A+D | Unanswerable questions and refusal scoring |

## Full suite after MVP

| Slug | Tiers | Purpose |
|---|---|---|
| `rag-noisy-context` | D | MIRAGE-style mixed context |
| `rag-multi-hop` | A+B | Sequential retrieval and partial credit |
| `rag-claim-diagnostic` | C | Gold claims for RAGChecker-style attribution |

## Requirements per pack

- `eval_slice` on every case.
- Pinned corpus snapshot when using platform corpus; inline assets allowed for early fixture packs.
- Bad-agent fixtures that fail the expected dimension.
- Scorecard tier breakdown.
- Catalog metadata: category, difficulty, estimated cost.
- Builder/decompiler round-trip tests.

## Acceptance criteria

- [ ] MVP three packs pass catalog load and runnable tests.
- [ ] Each MVP pack fails a deliberately bad agent fixture on the expected dimension.
- [ ] At least one pack uses a real corpus snapshot once #1083/#1090 are available.
- [ ] Full six-pack suite is tracked but not required for the first CI gate.
- [ ] Docs explain which packs are fixture/demo vs benchmark-quality.
- [ ] Pack gallery does not imply public leaderboard validity before #1099.

## Blocks

#1102, #1101, #1099
