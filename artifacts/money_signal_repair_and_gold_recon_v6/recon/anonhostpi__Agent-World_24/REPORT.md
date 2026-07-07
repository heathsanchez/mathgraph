# Gold Recon Report

## Verdict

`PARK_NO_LOCAL_JUDGE_OR_NO_MONEY`

## Decision

```json
{
  "repo": "anonhostpi/Agent-World",
  "num": 24,
  "url": "https://github.com/anonhostpi/Agent-World/issues/24",
  "title": "Kaggle \u2014 Custom CLI Tool",
  "state": "OPEN",
  "updatedAt": "2026-03-30T05:49:09Z",
  "reason": "Kaggle discovery CLI; no cash but can improve future money search",
  "amount_estimate": 0.0,
  "money": true,
  "local_judge": true,
  "benchmark_or_metric": true,
  "has_surface": false,
  "prompt_risk": false,
  "hardware_risk": false,
  "web3_risk": false,
  "verdict": "PARK_NO_LOCAL_JUDGE_OR_NO_MONEY"
}
```

## Issue body excerpt

## Tool Type
Custom CLI tool (Node/Deno)

## Purpose
Give agents structured access to Kaggle — the data science competition platform and community. Kaggle provides active competitions (what problems the ML community is working on right now), trending notebooks (how people are solving them), and datasets.

## API
- **Kaggle API**: https://www.kaggle.com/docs/api — REST-based
- **Authentication**: API token required (free, from kaggle.com/settings)
- **Existing CLI**: \`kaggle\` Python CLI exists but is Python-only and focused on download/submission
- **Public data**: Competition listings, public notebooks, public datasets

## CLI Interface (proposed)

\`\`\`bash
# Competitions
kaggle competitions                  # Active competitions
kaggle competition <slug>            # Competition details + description
kaggle leaderboard <slug>            # Competition leaderboard
kaggle leaderboard <slug> --limit 20 # Top N entries

# Notebooks
kaggle notebooks --sort trending     # Trending notebooks
kaggle notebooks --competition <slug>  # Notebooks for a competition
kaggle notebook <slug>               # Notebook details + metadata

# Datasets
kaggle datasets --sort trending      # Trending datasets
kaggle datasets --search "query"     # Search datasets
kaggle dataset <slug>                # Dataset details + columns + preview

# Search
kaggle search "query"                # Search across competitions, notebooks, datasets
kaggle search "query" --type notebook

# Discovery
kaggle topics                        # Discussion topics/forums
kaggle discussion <id>               # Read discussion thread
kaggle user <username>               # User profile + tier + medals
\`\`\`

## Output Format
- **YAML** for all structured output
- Competition metadata: title, description, deadline, reward, team count, evaluation metric, tags
- Notebook metadata: title, author, votes, language (Python/R), competition link, last run date
- Dataset metadata: title, creator, size, download count, columns, usability score
- User metadata: username, tier (Grandmaster/Master/etc.), medals, competition ranking

## Key Design Decisions
1. **Competition-centric**: Competitions are Kaggle's unique signal — what ML problems have prizes and deadlines right now.
2. **Tier/medal system as signal**: Kaggle's ranking system (Grandmaster → Novice) indicates expertise. Surface it.
3. **No data download**: Discovery tool, not a data pipeline. Show metadata, schemas, and previews — not full datasets.
4. **API token required**: Setup instructions in CLAUDE.md.

## CLAUDE.md Content
- Kaggle as the ML competition platform — what problems are being solved and how
- Competition lifecycle: launch → join → submit → leaderboard → end
- Tier system and what each tier means for expertise signal
- Notebooks as shared solutions — the Kaggle community's knowledge base
- Datasets as structured data discovery
- Using Kaggle for "how do people solve X?" research

## Acceptance Criteria
- [ ] CLI is implemented in Node or Deno
- [ ] All output is YAML
- [ ] Competition listing and details work
- [ ] Notebook browsing works
- [ ] Dataset metadata and preview work
- [ ] \`tools/kaggle/CLAUDE.md\` covers discovery patterns
- [ ] Tests cover all subcommands

## Cheap commands

```text
pwd=/Users/heath/Documents/mathgraph-lean-work/external/money_gold_recon_v6/anonhostpi__Agent-World_24

workflows:

```

## Inventory excerpt

```text
.git/config
.git/description
.git/HEAD
.git/hooks/applypatch-msg.sample
.git/hooks/commit-msg.sample
.git/hooks/fsmonitor-watchman.sample
.git/hooks/post-update.sample
.git/hooks/pre-applypatch.sample
.git/hooks/pre-commit.sample
.git/hooks/pre-merge-commit.sample
.git/hooks/pre-push.sample
.git/hooks/pre-rebase.sample
.git/hooks/pre-receive.sample
.git/hooks/prepare-commit-msg.sample
.git/hooks/push-to-checkout.sample
.git/hooks/update.sample
.git/index
.git/info/exclude
.git/logs/HEAD
.git/objects/pack/pack-3ee4a3fc0123fa51306ead7ffb3de0861b622562.idx
.git/objects/pack/pack-3ee4a3fc0123fa51306ead7ffb3de0861b622562.pack
.git/objects/pack/pack-3ee4a3fc0123fa51306ead7ffb3de0861b622562.promisor
.git/objects/pack/pack-97a46fb96f583767427b82448f523a893e17ce74.idx
.git/objects/pack/pack-97a46fb96f583767427b82448f523a893e17ce74.pack
.git/objects/pack/pack-97a46fb96f583767427b82448f523a893e17ce74.promisor
.git/packed-refs
.git/refs/heads/main
.git/shallow
CLAUDE.md
README.md
tools/gh/CLAUDE.md

```

## Grep excerpt

```text
===== money / judge / benchmark / test hits =====
./tools/gh/CLAUDE.md:89:# Latest release
./CLAUDE.md:10:- **Test-Driven Development (TDD):** Tests are written *before* code. Red → Green → Refactor. No code exists without a failing test that demanded it.
./CLAUDE.md:21:| **The Architect** | Human Developer | Strategic vision, domain expertise, acceptance authority. Signs off on specs, arbitrates disputes between Builder and Adversary. |
./CLAUDE.md:22:| **The Builder** | Claude (or similar) | Spec authorship, test generation, code implementation, and refactoring. Operates under strict TDD constraints. |
./CLAUDE.md:23:| **The Tracker** | **GitHub Issues + gh CLI** | Hierarchical issue decomposition — Epics → Issues → Sub-issues. Every spec, test, and implementation maps to a tracked issue. |
./CLAUDE.md:24:| **The Adversary** | **Sarcasmotron** (see below) | Hyper-critical reviewer with zero patience. Reviews specs, tests, *and* implementation. Fresh context on every pass. |
./CLAUDE.md:111:| **Regression Check (2)** | Run test suite; verify 4-Result Rule (new fail + regression pass → new pass + regression pass). |
./CLAUDE.md:139:- **Provable Properties Catalog:** Which invariants, safety properties, and correctness guarantees must be formally verified — not just tested? Examples: "This state machine can never reach an invalid state." "This arithmetic can never overflow." "This parser always terminates." "This access control check is never bypassed." The Builder distinguishes between properties that *should* be proven (critical path, security boundaries, financial calculations) and properties where test coverage is sufficient (UI formatting, logging, non-critical defaults).
./CLAUDE.md:144:**Why this must happen in Phase 1:** If the system is designed with side effects woven through the core logic, no amount of Phase 5 heroics will make it verifiable. A function that reads from a database, performs a calculation, and writes to a log in one block cannot be formally verified without mocking infrastructure that the verifier may not support. But a function that takes data in, returns a result, and lets the caller handle persistence — that's a function a model checker can reason about. This boundary must be drawn at the spec level because it fundamentally shapes the module decomposition, the dependency graph, and the testing strategy that follows.
./CLAUDE.md:148:The complete spec — behavioral contracts *and* verification architecture — is reviewed by *both* the human and the Adversary before any tests are written. Sarcasmotron tears into the spec looking for:
./CLAUDE.md:154:- **Properties claimed as "testable only" that should be provable** (the Adversary pushes back on lazy verification boundaries)
./CLAUDE.md:160:**GitHub Integration:** Each spec maps to a GitHub Issue. Sub-issues are generated for each behavioral contract item, edge case, non-functional requirement, *and* each formally provable property. The provable properties get their own issue chain so their status is tracked independently from test coverage.
./CLAUDE.md:168:With an airtight spec in hand, the Builder now writes tests — and *only* tests. No implementation code yet.
./CLAUDE.md:172:The Builder translates the spec directly into executable tests:
./CLAUDE.md:174:- **Unit Tests:** One or more tests per behavioral contract item. Every postcondition becomes an assertion. Every precondition violation becomes a test that expects a specific error.
./CLAUDE.md:175:- **Edge Case Tests:** Every item in the Edge Case Catalog becomes a test. These are the tests that catch the bugs that "never happen in production" (until they do).
./CLAUDE.md:177:- **Property-Based Tests:** Where applicable, the Builder generates property-based tests (e.g., using Hypothesis, fast-check, or proptest) that assert invariants hold across randomized inputs.
./CLAUDE.md:179:**The Red Gate:** All tests must *fail* before any implementation begins. If a test passes without implementation, the test is suspect — it's either testing the wrong thing or the spec was wrong. The Builder flags this for human review.
./CLAUDE.md:181:**Regression Sets (The 4-Result Rule):** Regression tests follow the same Red → Green discipline. The spec must zoom out enough to identify its **blast radius** — related features, adjacent modules, shared interfaces — and include regression tests for them. Before implementation begins, the Builder must produce **4 test results across 2 runs**:
./CLAUDE.md:185:| **Pre-implementation (Red Gate)** | Fail (Red) — proves tests are real | Pass — proves existing behavior is intact |
./CLAUDE.md:188:Both Red Gate runs (new = fail, regression = pass) are **required before writing any implementation code**. Both Green Gate runs (new = pass, regression = pass) are **required to exit Phase 2**. If regression tests fail at any point, the implementation has introduced a regression and must be fixed before proceeding. This forces every spec to consider its neighbors, not just itself.
./CLAUDE.md:190:**Testing Before Committing:** The test suite is committed first — as many commits as needed. No non-test commit may be made on the branch until the Red Gate clears (new tests fail, regression tests pass). The branch is unlocked for implementation only after that.
./CLAUDE.md:194:The Builder writes the *minimum* code necessary to make each test pass, one at a time. This is classic TDD discipline:
./CLAUDE.md:196:1. Pick the next failing test.
./CLAUDE.md:203:After all tests are green, the Builder refactors for clarity, performance, and adherence to the non-functional requirements in the spec. The test suite acts as the safety net — if refactoring breaks something, the tests catch it immediately.
./CLAUDE.md:205:**Human Checkpoint:** The developer reviews the test suite and implementation for alignment with the "spirit" of the spec. AI can miss intent even when it nails the letter of the contract.
./CLAUDE.md:211:*The code survived testing. Now it faces the gauntlet.*
./CLAUDE.md:213:The verified, test-passing codebase — along with the spec and test suite — is presented to **Sarcasmotron** in a fresh context window.
./CLAUDE.md:217:1. **Spec Fidelity:** Does the implementation actually satisfy the spec, or did the tests inadvertently encode a misunderstanding?
./CLAUDE.md:218:2. **Test Quality:** Are the tests actually testing what they claim? Are there tests that would pass even if the implementation were subtly wrong? (Tautological tests, tests that mock too aggressively, tests that assert on implementation details rather than behavior.)
./CLAUDE.md:234:- **Test-level flaws** → Return to Phase 2a. Fix or add tests, verify they fail against the current implementation (or a deliberately broken version), then fix implementation if needed.
./CLAUDE.md:235:- **Implementation-level flaws** → Return to Phase 2c. Refactor, ensure all tests still pass.
./CLAUDE.md:236:- **New edge cases discovered** → Add to spec's Edge Case Catalog, write new failing tests, implement fixes.
./CLAUDE.md:244:The verification architecture designed in Phase 1b is now *executed* against the battle-tested implementation. Because the codebase was architected from the start with a pure core and clear purity boundaries, formal verification tools can operate on it without heroic refactoring.
./CLAUDE.md:247:- **Fuzz Testing:** Structured fuzzing (AFL++, libFuzzer, cargo-fuzz) is layered on top of property-based tests to find inputs that no human or AI anticipated. The deterministic core is an ideal fuzz target because it has no environmental dependencies to mock.
./CLAUDE.md:248:- **Security Hardening:** Suites like **Wycheproof** (cryptographic edge cases) and **Semgrep** (static analysis) are run as CI/CD gates.
./CLAUDE.md:249:- **Mutation Testing:** Tools like **mutmut** or **Stryker** mutate the code to verify the test suite actually catches real bugs. If a mutation survives, the test suite has a gap.
./CLAUDE.md:263:| **Tests** | The Adversa
```
