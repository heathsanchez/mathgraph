#!/usr/bin/env bash
set -u

ROOT="/Users/heath/Documents/mathgraph-lean-work"
RUN="qojulia_407_claim_scope_v8"
OUT="$ROOT/artifacts/$RUN"
REPO_DIR="$ROOT/external/money_gold_recon_v6/qojulia__QuantumOptics.jl_407"
REPO="qojulia/QuantumOptics.jl"
ISSUE="407"

mkdir -p "$OUT"
cd "$ROOT" || exit 1

echo "MathGraph qojulia/QuantumOptics.jl #407 Claim + Scope v8"
echo "Goal: avoid blind patching; claim/scope the real \$400 benchmark bounty."
echo

echo "01 status"
date -u +"%Y-%m-%dT%H:%M:%SZ"
df -h /
git status --short

echo
echo "02 refresh repo"
if [ ! -d "$REPO_DIR/.git" ]; then
  mkdir -p "$(dirname "$REPO_DIR")"
  git clone --depth 1 --filter=blob:none "https://github.com/$REPO.git" "$REPO_DIR" > "$OUT/clone.log" 2>&1 || true
else
  git -C "$REPO_DIR" fetch --depth 1 origin > "$OUT/git_fetch.log" 2>&1 || true
  git -C "$REPO_DIR" checkout origin/master > "$OUT/git_checkout.log" 2>&1 || git -C "$REPO_DIR" checkout FETCH_HEAD >> "$OUT/git_checkout.log" 2>&1 || true
fi
git -C "$REPO_DIR" rev-parse HEAD | tee "$OUT/head.txt"

echo
echo "03 inspect existing benchmark infra"
{
  echo "===== .github/workflows/benchmark.yml ====="
  sed -n '1,260p' "$REPO_DIR/.github/workflows/benchmark.yml" 2>/dev/null || true

  echo
  echo "===== benchmark/benchmarks.jl ====="
  sed -n '1,260p' "$REPO_DIR/benchmark/benchmarks.jl" 2>/dev/null || true

  echo
  echo "===== benchmark/Project.toml ====="
  sed -n '1,220p' "$REPO_DIR/benchmark/Project.toml" 2>/dev/null || true

  echo
  echo "===== README benchmark mention ====="
  grep -RIn "Benchmark" "$REPO_DIR/README.md" "$REPO_DIR/CLAUDE.md" "$REPO_DIR/docs" 2>/dev/null | head -80 || true

  echo
  echo "===== comparative benchmark references ====="
  grep -RInE "qutip|QuTiP|QuantumToolbox|comparative|comparison|webpage|benchmark.*web|makefile|Makefile" "$REPO_DIR" \
    --exclude-dir=.git --exclude='*.ipynb' 2>/dev/null | head -200 || true
} | tee "$OUT/existing_benchmark_infra.txt"

echo
echo "04 issue latest"
gh issue view "$ISSUE" -R "$REPO" \
  --json url,title,body,state,labels,comments,assignees,updatedAt \
  > "$OUT/issue.json" 2> "$OUT/issue.err" || true

python3 - "$OUT" <<'PY'
import json, pathlib, sys, textwrap, re
out = pathlib.Path(sys.argv[1])
issue = json.loads((out/"issue.json").read_text())

comments = issue.get("comments") or []
claimed_text = "\n\n".join(c.get("body") or "" for c in comments).lower()
assignees = [a.get("login") for a in issue.get("assignees", [])]

already_claimed = bool(assignees) or any(x in claimed_text for x in [
    "i claim", "i'll claim", "i would like to claim", "i’m claiming", "i am claiming",
    "assigned", "working on this", "opened a pr", "pull request"
])

summary = {
    "url": issue.get("url"),
    "title": issue.get("title"),
    "state": issue.get("state"),
    "labels": [x.get("name") for x in issue.get("labels", [])],
    "assignees": assignees,
    "comment_count": len(comments),
    "updatedAt": issue.get("updatedAt"),
    "already_claimed_or_active": already_claimed,
}
(out/"issue_latest_summary.json").write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=2))

claim = """Hi, I’d like to claim this bounty if it is still available.

Name: Heath Sanchez
GitHub: @heathsanchez

Proposed scope/sequence:

1. First PR: repair the existing `benchmark/` suite enough that it has a reproducible local command and a lightweight GitHub Actions smoke gate suitable for pull requests.
2. Preserve/reuse the current `benchmark/benchmarks.jl` and `benchmark/Project.toml` where possible rather than replacing them.
3. Second step, if the first PR direction is accepted: repair/extend comparative benchmark support for QuTiP and QuantumToolbox.jl, then add a Makefile/documented command for regenerating the public comparative benchmark page.

Before I patch, I want to confirm the intended CI shape: should PR CI run a small benchmark smoke subset only, with full benchmarks reserved for manual/scheduled runs? That seems safest to avoid expensive/noisy PR jobs while still preventing benchmark-suite bitrot.

I’ll keep the first patch narrow and reviewable: benchmark project repair, smoke runner, CI wiring, and documentation for the local command.
"""

(out/"CLAIM_COMMENT.md").write_text(claim)

plan = []
plan.append("# qojulia #407 Claim + Scope v8")
plan.append("")
plan.append("## Verdict")
plan.append("")
if already_claimed:
    plan.append("`DO_NOT_CLAIM_YET__READ_ACTIVE_THREAD`")
else:
    plan.append("`CLAIM_BEFORE_PATCH`")
plan.append("")
plan.append("## Why")
plan.append("")
plan.append("- Bounty is explicit and unclaimed in the issue packet.")
plan.append("- Existing benchmark infra already exists, so this is a repair/modernization bounty.")
plan.append("- No local Julia runtime is installed, so a patch without scope confirmation is risky.")
plan.append("- Issue logistics explicitly encourage a claim comment.")
plan.append("")
plan.append("## Proposed route")
plan.append("")
plan.append("1. Claim/scope the bounty.")
plan.append("2. v9: install or locate Julia only if scope is confirmed.")
plan.append("3. v10: patch a small benchmark smoke command + CI job.")
plan.append("4. v11: comparative QuTiP/QuantumToolbox + Makefile/page command.")
plan.append("")
plan.append("## Claim comment")
plan.append("")
plan.append(claim)
(out/"CLAIM_SCOPE_PLAN.md").write_text("\n".join(plan) + "\n")
print((out/"CLAIM_SCOPE_PLAN.md").read_text())
PY

echo
echo "05 optional post claim"
if [ "${POST_CLAIM:-0}" = "1" ]; then
  echo "POST_CLAIM=1 set; posting claim comment"
  gh issue comment "$ISSUE" -R "$REPO" --body-file "$OUT/CLAIM_COMMENT.md" \
    > "$OUT/post_claim.out" 2> "$OUT/post_claim.err" || true
  cat "$OUT/post_claim.out" || true
  cat "$OUT/post_claim.err" || true
else
  echo "Dry run only. To post claim:"
  echo "POST_CLAIM=1 bash qojulia_407_claim_scope_v8.sh"
fi

echo
echo "06 commit artifact"
git add "$OUT" qojulia_407_claim_scope_v8.sh
git commit -m "Scope qojulia benchmark bounty claim v8" || true
git push origin local-main || true

echo
echo "07 final"
git status --short
df -h /
echo
echo "Artifacts:"
echo "$OUT/CLAIM_SCOPE_PLAN.md"
echo "$OUT/CLAIM_COMMENT.md"
echo "$OUT/existing_benchmark_infra.txt"
echo "$OUT/issue_latest_summary.json"
echo "$OUT/post_claim.out"
