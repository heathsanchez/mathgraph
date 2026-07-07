#!/usr/bin/env bash
set -euo pipefail

echo "MathGraph qojulia/QuantumOptics.jl #407 Fork Push PR v12"
echo "Goal: fix gh fork syntax, create fork if needed, push patch branch, open draft PR."
echo

ROOT="/Users/heath/Documents/mathgraph-lean-work"
REPO="qojulia/QuantumOptics.jl"
UPSTREAM_OWNER="qojulia"
UPSTREAM_NAME="QuantumOptics.jl"
REPO_DIR="$ROOT/external/money_gold_recon_v6/qojulia__QuantumOptics.jl_407"
OUT="$ROOT/artifacts/qojulia_407_fork_push_pr_v12"
BRANCH="heath/benchmark-smoke-407"
JULIA_BIN="${JULIA_BIN:-$HOME/.juliaup/bin/julia}"

mkdir -p "$OUT"
cd "$ROOT"

echo "01 status"
date -u +"%Y-%m-%dT%H:%M:%SZ" | tee "$OUT/status_start.txt"
df -h / | tee "$OUT/df_start.txt"
git status --short | tee "$OUT/mathgraph_status_start.txt" || true
echo

echo "02 identify GitHub user"
GH_USER="$(gh api user --jq .login)"
echo "$GH_USER" | tee "$OUT/gh_user.txt"
FORK_REPO="$GH_USER/$UPSTREAM_NAME"
FORK_URL="https://github.com/$GH_USER/$UPSTREAM_NAME.git"
echo "FORK_REPO=$FORK_REPO" | tee "$OUT/fork_repo.txt"
echo "FORK_URL=$FORK_URL" | tee "$OUT/fork_url.txt"
echo

echo "03 inspect external patch branch"
cd "$REPO_DIR"
git checkout "$BRANCH"
git status --short | tee "$OUT/external_status_start.txt"
git log --oneline -5 | tee "$OUT/external_log_start.txt"
git show --stat --oneline HEAD | tee "$OUT/external_head_stat.txt"
test -f benchmark/run_smoke.jl
test -f .github/workflows/benchmark-smoke.yml
grep -n "BENCHMARK_SMOKE_OK" benchmark/run_smoke.jl | tee "$OUT/runner_grep.txt"
grep -n "benchmark/run_smoke.jl" README.md | tee "$OUT/readme_grep.txt"
echo

echo "04 rerun local smoke"
if [ ! -x "$JULIA_BIN" ]; then
  JULIA_BIN="$(command -v julia || true)"
fi
if [ -z "${JULIA_BIN:-}" ] || [ ! -x "$JULIA_BIN" ]; then
  echo "Julia not found." | tee "$OUT/julia_error.txt"
  exit 1
fi
set +e
"$JULIA_BIN" --project=benchmark benchmark/run_smoke.jl > "$OUT/local_smoke.out" 2> "$OUT/local_smoke.err"
SMOKE_RC=$?
set -e
echo "$SMOKE_RC" | tee "$OUT/local_smoke.rc"
tail -80 "$OUT/local_smoke.out" || true
tail -80 "$OUT/local_smoke.err" || true
if [ "$SMOKE_RC" -ne 0 ]; then
  echo "Local smoke failed; stop."
  exit 1
fi
echo

echo "05 create or confirm fork"
set +e
gh repo view "$FORK_REPO" --json nameWithOwner,url > "$OUT/fork_view_before.json" 2> "$OUT/fork_view_before.err"
FORK_VIEW_RC=$?
set -e
echo "$FORK_VIEW_RC" | tee "$OUT/fork_view_before.rc"
cat "$OUT/fork_view_before.json" || true
cat "$OUT/fork_view_before.err" || true

if [ "$FORK_VIEW_RC" -ne 0 ]; then
  echo "Fork not found or inaccessible; creating fork without --remote."
  set +e
  gh repo fork "$REPO" --clone=false > "$OUT/gh_fork.out" 2> "$OUT/gh_fork.err"
  FORK_RC=$?
  set -e
  echo "$FORK_RC" | tee "$OUT/gh_fork.rc"
  cat "$OUT/gh_fork.out" || true
  cat "$OUT/gh_fork.err" || true
else
  echo "Fork already exists."
  echo "0" > "$OUT/gh_fork.rc"
fi

echo "Waiting briefly for fork availability..."
sleep 5

set +e
gh repo view "$FORK_REPO" --json nameWithOwner,url > "$OUT/fork_view_after.json" 2> "$OUT/fork_view_after.err"
FORK_AFTER_RC=$?
set -e
echo "$FORK_AFTER_RC" | tee "$OUT/fork_view_after.rc"
cat "$OUT/fork_view_after.json" || true
cat "$OUT/fork_view_after.err" || true

if [ "$FORK_AFTER_RC" -ne 0 ]; then
  echo "Fork still not confirmed. Stop before push."
  exit 1
fi
echo

echo "06 set heath remote to actual fork"
if git remote get-url heath >/dev/null 2>&1; then
  git remote set-url heath "$FORK_URL"
else
  git remote add heath "$FORK_URL"
fi
git remote -v | tee "$OUT/remotes_after.txt"
echo

echo "07 push branch"
set +e
git push -u heath "$BRANCH" > "$OUT/external_push.out" 2> "$OUT/external_push.err"
PUSH_RC=$?
set -e
echo "$PUSH_RC" | tee "$OUT/external_push.rc"
cat "$OUT/external_push.out" || true
cat "$OUT/external_push.err" || true
if [ "$PUSH_RC" -ne 0 ]; then
  echo "Push failed; stop before PR."
  exit 1
fi
echo

echo "08 create or locate draft PR"
cat > "$OUT/PR_BODY.md" <<'MD'
## Summary

Adds a lightweight benchmark smoke gate for the existing `benchmark/` suite.

This is intentionally narrow for the first step of #407:

- instantiate the benchmark project
- load `benchmark/benchmarks.jl`
- run one tiny benchmark path
- fail CI if the benchmark suite no longer loads or cannot run a minimal benchmark

## Local verification

    julia --project=benchmark benchmark/run_smoke.jl

The smoke runner prints `BENCHMARK_SMOKE_OK` on success.

## Scope

This PR does not attempt the full comparative benchmark report against QuTiP / QuantumToolbox.jl yet. It is meant to establish the small PR-safe CI gate first, so the benchmark suite stops silently bitrotting.
MD

set +e
gh pr view \
  -R "$REPO" \
  --head "$GH_USER:$BRANCH" \
  --json url,state,isDraft,title \
  > "$OUT/pr_existing.json" 2> "$OUT/pr_existing.err"
PR_VIEW_RC=$?
set -e
echo "$PR_VIEW_RC" | tee "$OUT/pr_existing.rc"
cat "$OUT/pr_existing.json" || true
cat "$OUT/pr_existing.err" || true

if [ "$PR_VIEW_RC" -eq 0 ] && [ -s "$OUT/pr_existing.json" ]; then
  echo "Existing PR found; not creating duplicate."
else
  set +e
  gh pr create \
    -R "$REPO" \
    --head "$GH_USER:$BRANCH" \
    --base master \
    --draft \
    --title "Add benchmark smoke gate" \
    --body-file "$OUT/PR_BODY.md" \
    > "$OUT/pr_create.out" 2> "$OUT/pr_create.err"
  PR_CREATE_RC=$?
  set -e
  echo "$PR_CREATE_RC" | tee "$OUT/pr_create.rc"
  cat "$OUT/pr_create.out" || true
  cat "$OUT/pr_create.err" || true
fi
echo

echo "09 summarize"
python3 - "$OUT" "$GH_USER" <<'PY'
import json
import pathlib
import sys

out = pathlib.Path(sys.argv[1])
gh_user = sys.argv[2]

def read(name):
    p = out / name
    return p.read_text(errors="replace").strip() if p.exists() else ""

pr_url = ""
if read("pr_create.out"):
    pr_url = read("pr_create.out").splitlines()[-1].strip()
elif read("pr_existing.json"):
    try:
        pr_url = json.loads(read("pr_existing.json")).get("url", "")
    except Exception:
        pass

decision = {
    "verdict": "DRAFT_PR_OPENED_OR_EXISTS" if pr_url else "PR_NOT_CONFIRMED",
    "repo": "qojulia/QuantumOptics.jl",
    "fork_repo": f"{gh_user}/QuantumOptics.jl",
    "branch": "heath/benchmark-smoke-407",
    "local_smoke_rc": read("local_smoke.rc"),
    "fork_confirmed_rc": read("fork_view_after.rc"),
    "push_rc": read("external_push.rc"),
    "pr_url": pr_url,
}
(out / "decision.json").write_text(json.dumps(decision, indent=2) + "\n")

md = []
md.append("# qojulia #407 Fork Push PR v12")
md.append("")
md.append("## Verdict")
md.append("")
md.append(f"`{decision['verdict']}`")
md.append("")
md.append("## Result")
md.append("")
md.append(f"- Local smoke rc: `{decision['local_smoke_rc']}`")
md.append(f"- Fork confirmed rc: `{decision['fork_confirmed_rc']}`")
md.append(f"- Push rc: `{decision['push_rc']}`")
md.append(f"- PR: {pr_url or '(not confirmed)'}")
md.append("")
md.append("## Patch")
md.append("")
md.append("- `benchmark/run_smoke.jl`")
md.append("- `.github/workflows/benchmark-smoke.yml`")
md.append("- `README.md` benchmark smoke docs")
md.append("")
(out / "PR_OPEN_REPORT.md").write_text("\n".join(md) + "\n")
print((out / "PR_OPEN_REPORT.md").read_text())
PY
echo

echo "10 commit MathGraph artifact"
cd "$ROOT"
git add "$OUT" qojulia_407_fork_push_pr_v12.sh
git commit -m "Open qojulia benchmark smoke draft PR v12" || true
git push origin local-main || true
echo

echo "11 final"
git status --short
df -h /
echo
echo "Artifacts:"
echo "$OUT/PR_OPEN_REPORT.md"
echo "$OUT/decision.json"
echo "$OUT/local_smoke.out"
echo "$OUT/external_push.out"
echo "$OUT/external_push.err"
echo "$OUT/pr_create.out"
echo "$OUT/pr_create.err"
