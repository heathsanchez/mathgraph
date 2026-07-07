#!/usr/bin/env bash
set -u

ROOT="/Users/heath/Documents/mathgraph-lean-work"
OUT="$ROOT/artifacts/paid_verification_offer_v1"

mkdir -p "$OUT"
cd "$ROOT" || exit 1

echo "MathGraph Paid Verification Offer v1"
echo

echo "01 status"
{
  date -u +"%Y-%m-%dT%H:%M:%SZ"
  df -h /
  git status --short
} | tee "$OUT/status_start.txt"

echo
echo "02 write offer package"

cat > "$OUT/ONE_PAGER.md" <<'MD'
# MathGraph Proof-Repair / Verification Sprints

## Offer

MathGraph turns stuck formal/code claims into externally judged artifacts:

- verified Lean proofs
- removed `sorry` / `admit`
- repaired generated specs
- CI-green pull requests
- finite counterexamples
- benchmark-backed negative results
- named obstruction reports

The output is not advice. The output is proof, patch, counterexample, or obstruction, judged by your verifier.

## Best fit

Good:

- Lean 4 proof gaps
- failing proof obligations
- generated specs that almost compile
- small theorem repairs
- correctness invariants
- formal-methods repos with local CI
- benchmark tasks with clear acceptance criteria

Bad:

- vague “improve the agent” work
- no local verifier
- no reproducible failure
- prompt extraction / jailbreak tasks
- optimization work without a canonical metric

## Sprint format

You provide:

- repo
- issue
- failing file or theorem
- verifier command
- acceptance criterion

I return:

- patch or PR if repairable
- local verifier log
- short route trace
- obstruction report if not repairable

## Recent public traces

- `strata-org/specimen#46`: added `LawfulScorable` proof-carrying scorer-law interface; local `lake build` passes.
- `mo271/FormalBook#137`: Lean proof repair; CI green 2/2.
- `mo271/FormalBook#138`: Lean proof repair; CI green 2/2.
- `teorth/equational_theories#1461`: Law43 definability proof; CI green.
- `Beneficial-AI-Foundation/vericoding-benchmark#12`: generated-spec index-bound proof repairs.
- `tinygrad/tinygrad#3039`: certified negative result; correct Tensor-level scan was slower, so no bad PR was opened.
- `tenstorrent/tt-llk#1638`: metric requested before patching, to avoid blind optimization.

## Pricing

### Diagnostic sprint — USD $500

One repo, one issue, one verifier.

Output:

- setup/repro attempt
- obstruction map
- likely patch route
- go/no-go judgment

No guaranteed fix.

### Proof-repair sprint — USD $1,500

One small proof/code repair.

Output:

- patch or PR
- local verifier evidence
- short report

### Verification retainer — USD $3,000–$5,000/month

Ongoing queue of small proof/code repair tasks.

Output:

- weekly patches / PRs / obstruction reports
- Lawbook of verified fixes and failed routes

## One-line pitch

MathGraph turns stuck formal claims into verifier-judged artifacts: proof, counterexample, or named obstruction.
MD

cat > "$OUT/SHORT_DM.md" <<'MD'
Hey — I’m doing fixed-scope proof-repair / verification sprints for Lean and formal-methods repos.

Recent public traces include CI-green FormalBook/equational-theories proof PRs, generated-spec proof repairs, and a draft Strata PR adding a proof-carrying `LawfulScorable` interface with local `lake build` passing.

The workflow is simple: give me one repo, one issue, and one verifier command. I return a patch/PR if repairable, or a short obstruction report if not.

Best fit is Lean 4 proof gaps, `sorry` removal, generated spec obligations, or small correctness invariants.

Diagnostic sprint: $500. Proof-repair sprint: $1.5k.
MD

cat > "$OUT/EMAIL_TEMPLATE.md" <<'MD'
Subject: Fixed-scope Lean / formal verification repair sprint

Hi {{name}},

I’m Heath, founder of MathGraph. I’m offering fixed-scope proof-repair and verification sprints for Lean/formal-methods repos.

The model is simple:

- you provide one repo, one issue, and one verifier command
- I reproduce the proof gap or failing obligation
- I return either a patch/PR with verifier evidence, or a short obstruction report explaining why the route failed

Recent public traces:

- Strata/specimen: draft PR adding a `LawfulScorable` proof-carrying scorer-law interface; local `lake build` passes
- FormalBook: two Lean proof-repair PRs with CI green
- equational-theories: Law43 definability proof PR with CI green
- vericoding-benchmark: generated-spec index-bound proof repairs
- tinygrad: negative benchmark certificate where a correct scan route was slower than builtin, so I did not open a bad PR

Current packages:

- Diagnostic sprint: USD $500
- Proof-repair sprint: USD $1,500
- Retainer: USD $3k–$5k/month for an ongoing repair queue

Good fits are Lean 4 proof gaps, `sorry` removal, generated spec obligations, small theorem repairs, or correctness invariants with a local checker.

Do you have one stuck proof or verification issue that would be worth testing this on?

Heath
Metalogic Labs / MathGraph
MD

cat > "$OUT/TARGET_LIST.md" <<'MD'
# First Paid Verification Targets

## 1. Maintainers already seeing public PRs

Best after merge/review:

- FormalBook maintainers
- equational_theories ecosystem
- vericoding-benchmark / Beneficial AI Foundation
- Strata/specimen
- Lean4Lean

Ask:

“Do you have a paid queue of similar small proof repairs?”

## 2. Lean-heavy AI/formal-method teams

Offer:

“Give me one stuck Lean proof obligation and one verifier command.”

## 3. Tenstorrent

Status:

Waiting for scoring metric on #1638.

Only act when exact metric/command is provided.

## 4. Avoid

- prompt extraction bounties
- vague AI-agent issues
- optimization without canonical metric
- no local verifier
MD

cat > "$OUT/POST_ACCEPTANCE_FOLLOWUP.md" <<'MD'
Thanks — glad this was useful.

I’m doing fixed-scope proof-repair / verification sprints now. If you have a queue of similar small Lean/proof obligations, I can take one repo + one issue + one verifier command and return either a PR or a short obstruction report.

Typical scope:

- diagnostic sprint: $500
- proof-repair sprint: $1.5k
- ongoing repair queue: $3k–$5k/month

Happy to start with one small stuck obligation.
MD

cat > "$OUT/GITHUB_BIO_BLURB.md" <<'MD'
I build MathGraph: a proof-repair and verification system that turns AI-generated or stuck formal claims into externally judged artifacts — verified proof, counterexample, or named obstruction.

Available for fixed-scope Lean / formal verification repair sprints.
MD

cat > "$OUT/README.md" <<'MD'
# Paid Verification Offer v1

Files:

- `ONE_PAGER.md`
- `SHORT_DM.md`
- `EMAIL_TEMPLATE.md`
- `TARGET_LIST.md`
- `POST_ACCEPTANCE_FOLLOWUP.md`
- `GITHUB_BIO_BLURB.md`

Next move:

Do not spam. Use this only after a PR is accepted/reviewed, or for a warm contact with a concrete Lean/formal-verification pain.
MD

cat "$OUT/ONE_PAGER.md"

echo
echo "03 commit"
git add "$OUT" paid_verification_offer_v1.sh
git commit -m "Add paid verification offer package v1" || true
git push origin local-main || true

echo
echo "04 final status"
git status --short
df -h /
echo
echo "Artifacts:"
echo "$OUT/ONE_PAGER.md"
echo "$OUT/SHORT_DM.md"
echo "$OUT/EMAIL_TEMPLATE.md"
echo "$OUT/TARGET_LIST.md"
echo "$OUT/POST_ACCEPTANCE_FOLLOWUP.md"
echo "$OUT/GITHUB_BIO_BLURB.md"
