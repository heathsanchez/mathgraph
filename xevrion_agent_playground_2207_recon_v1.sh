#!/usr/bin/env bash
set -u

ROOT="/Users/heath/Documents/mathgraph-lean-work"
OWNER_REPO="xevrion-v2/agent-playground"
ISSUE_NUM="2207"
REPO="$ROOT/external/bounty_triage_v1/xevrion-v2__agent-playground"
OUT="$ROOT/artifacts/bounty_triage_v1/xevrion_agent_playground_2207_recon_v1"

mkdir -p "$OUT"
cd "$ROOT" || exit 1

echo "MathGraph Bounty Recon v1 — $OWNER_REPO #$ISSUE_NUM"
echo

echo "01 status"
date -u +"%Y-%m-%dT%H:%M:%SZ" | tee "$OUT/start_utc.txt"
df -h / | tee "$OUT/df_start.txt"
git status --short | tee "$OUT/root_git_status_start.txt"

echo
echo "02 clone/update repo"
mkdir -p "$(dirname "$REPO")"

if [ ! -d "$REPO/.git" ]; then
  echo "[clone] $OWNER_REPO -> $REPO"
  gh repo clone "$OWNER_REPO" "$REPO" -- --filter=blob:none 2>&1 | tee "$OUT/clone.log"
else
  echo "[exists] $REPO"
fi

cd "$REPO" || exit 1

git remote -v | tee "$OUT/remotes.txt"
git status --short | tee "$OUT/repo_status_before.txt"

# Keep repo clean and current, but don't destroy unknown local work without recording.
git fetch origin --prune 2>&1 | tee "$OUT/git_fetch.log"
DEFAULT_BRANCH="$(git remote show origin 2>/dev/null | awk '/HEAD branch/ {print $NF}' | head -1)"
if [ -z "$DEFAULT_BRANCH" ]; then DEFAULT_BRANCH="main"; fi
git checkout "$DEFAULT_BRANCH" 2>&1 | tee "$OUT/git_checkout_default.log" || true
git pull --ff-only origin "$DEFAULT_BRANCH" 2>&1 | tee "$OUT/git_pull.log" || true

HEAD="$(git rev-parse HEAD 2>/dev/null || echo unknown)"
echo "$HEAD" | tee "$OUT/head.txt"

echo
echo "03 issue view"
gh issue view "$ISSUE_NUM" --repo "$OWNER_REPO" \
  --json number,title,state,author,labels,body,comments,url,createdAt,updatedAt \
  > "$OUT/issue_view.json" 2> "$OUT/issue_view.err" || true

python3 - "$OUT" <<'PY'
import json, sys
from pathlib import Path

out = Path(sys.argv[1])
p = out / "issue_view.json"
if not p.exists() or p.stat().st_size == 0:
    print("[issue] no json")
    raise SystemExit(0)

j = json.loads(p.read_text())
print(json.dumps({
    "number": j.get("number"),
    "title": j.get("title"),
    "state": j.get("state"),
    "url": j.get("url"),
    "labels": [x.get("name") for x in j.get("labels", [])],
    "comment_count": len(j.get("comments", [])),
    "updatedAt": j.get("updatedAt"),
}, indent=2))

body = j.get("body") or ""
(out / "issue_body.md").write_text(body)
comments = []
for c in j.get("comments", []):
    comments.append(f"## {c.get('author',{}).get('login')} — {c.get('createdAt')}\n\n{c.get('body') or ''}\n")
(out / "issue_comments.md").write_text("\n---\n".join/comments if False else "\n---\n".join(comments))
PY

echo
echo "04 project inventory"
find . -maxdepth 3 -type f \
  \( -name 'package.json' -o -name 'pnpm-lock.yaml' -o -name 'yarn.lock' -o -name 'package-lock.json' -o -name 'bun.lockb' -o -name 'tsconfig.json' -o -name 'vite.config.*' -o -name 'next.config.*' -o -name 'jest.config.*' -o -name 'vitest.config.*' -o -name 'playwright.config.*' -o -name '.env.example' -o -name 'README*' \) \
  | sort | tee "$OUT/project_files.txt"

echo
echo "05 static grep"
{
  echo "===== validation/user/rpc/api hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=dist --exclude-dir=build --exclude-dir=.next \
    "createUser|create user|user creation|signup|sign up|register|registration|validate|validation|payload|zod|joi|yup|express|fastify|hono|trpc|rpc|router|route|api/users|/users|User" . 2>/dev/null | head -1000

  echo
  echo "===== test hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=dist --exclude-dir=build --exclude-dir=.next \
    "describe\\(|it\\(|test\\(|expect\\(|supertest|vitest|jest|playwright|cypress|mocha|ava" . 2>/dev/null | head -1000

  echo
  echo "===== TODO/FIXME/security hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=dist --exclude-dir=build --exclude-dir=.next \
    "TODO|FIXME|HACK|SECURITY|sanitize|schema|required|email|password|username" . 2>/dev/null | head -1000
} | tee "$OUT/static_grep.txt"

echo
echo "06 package analysis"
python3 - "$REPO" "$OUT" <<'PY'
import json, os, re, sys
from pathlib import Path
from collections import Counter

repo = Path(sys.argv[1])
out = Path(sys.argv[2])

def read(p):
    try:
        return p.read_text(errors="replace")
    except Exception:
        return ""

package_files = list(repo.rglob("package.json"))
packages = []
for p in package_files:
    if "node_modules" in p.parts:
        continue
    try:
        j = json.loads(p.read_text())
    except Exception as e:
        packages.append({"path": str(p.relative_to(repo)), "error": str(e)})
        continue
    packages.append({
        "path": str(p.relative_to(repo)),
        "name": j.get("name"),
        "type": j.get("type"),
        "scripts": j.get("scripts", {}),
        "deps": sorted(list((j.get("dependencies") or {}).keys())),
        "devDeps": sorted(list((j.get("devDependencies") or {}).keys())),
    })

(out / "package_summary.json").write_text(json.dumps(packages, indent=2))

all_files = []
for p in repo.rglob("*"):
    if not p.is_file():
        continue
    rel = p.relative_to(repo)
    if any(part in {".git","node_modules","dist","build",".next","coverage"} for part in rel.parts):
        continue
    if p.suffix.lower() not in {".ts",".tsx",".js",".jsx",".mjs",".cjs",".json",".md",".yml",".yaml"}:
        continue
    try:
        size = p.stat().st_size
    except Exception:
        continue
    if size > 500_000:
        continue
    txt = read(p)
    low = txt.lower()
    score = 0
    terms = {
        "user": 3, "users": 3, "createuser": 8, "create user": 8,
        "register": 5, "signup": 5, "payload": 5, "validate": 6,
        "validation": 6, "zod": 7, "joi": 7, "yup": 7,
        "router": 2, "route": 2, "api": 2, "rpc": 4,
        "email": 4, "password": 3, "username": 3,
        "test(": 3, "describe(": 3, "expect(": 3, "supertest": 6,
    }
    hits = {}
    for t, w in terms.items():
        c = low.count(t)
        if c:
            score += c*w
            hits[t] = c
    if score:
        all_files.append({
            "path": str(rel),
            "score": score,
            "hits": hits,
            "lines": txt.count("\n")+1,
            "bytes": len(txt.encode(errors="replace")),
        })

all_files.sort(key=lambda x: (-x["score"], x["path"]))
(out / "candidate_files.json").write_text(json.dumps(all_files[:200], indent=2))

# Focused context snippets.
snippets = []
for item in all_files[:40]:
    p = repo / item["path"]
    txt = read(p)
    lines = txt.splitlines()
    pats = re.compile(r"(createUser|create user|register|signup|payload|validate|validation|zod|joi|yup|api/users|/users|rpc|email|password|username)", re.I)
    hit_lines = [i for i,l in enumerate(lines) if pats.search(l)]
    if not hit_lines:
        hit_lines = [0]
    snippets.append(f"\n\n===== {item['path']} score={item['score']} =====")
    used = set()
    for h in hit_lines[:8]:
        start = max(0, h-12)
        end = min(len(lines), h+18)
        key = (start,end)
        if key in used:
            continue
        used.add(key)
        snippets.append(f"\n--- around line {h+1} ---")
        for idx in range(start,end):
            snippets.append(f"{idx+1:04d}: {lines[idx]}")
(out / "candidate_context.txt").write_text("\n".join(snippets) + "\n")

# Detect test commands.
test_surface = []
for pkg in packages:
    scripts = pkg.get("scripts") or {}
    for k,v in scripts.items():
        lk = k.lower()
        lv = str(v).lower()
        if any(t in lk for t in ["test","lint","type","check","build"]) or any(t in lv for t in ["vitest","jest","mocha","playwright","tsc","eslint"]):
            test_surface.append({"package": pkg["path"], "script": k, "command": v})

locks = {
    "pnpm": (repo / "pnpm-lock.yaml").exists(),
    "npm": (repo / "package-lock.json").exists(),
    "yarn": (repo / "yarn.lock").exists(),
    "bun": (repo / "bun.lockb").exists(),
}
manager = "pnpm" if locks["pnpm"] else "npm" if locks["npm"] else "yarn" if locks["yarn"] else "bun" if locks["bun"] else "npm"

summary = {
    "package_count": len(packages),
    "package_manager_guess": manager,
    "lockfiles": locks,
    "test_surface": test_surface,
    "top_candidate_files": all_files[:20],
}
(out / "analysis_summary.json").write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=2)[:12000])
PY

echo
echo "07 try cheap no-install commands"
cd "$REPO" || exit 1
{
  echo "node:"
  command -v node || true
  node --version 2>/dev/null || true
  echo
  echo "npm:"
  command -v npm || true
  npm --version 2>/dev/null || true
  echo
  echo "pnpm:"
  command -v pnpm || true
  pnpm --version 2>/dev/null || true
  echo
  echo "yarn:"
  command -v yarn || true
  yarn --version 2>/dev/null || true
  echo
  echo "bun:"
  command -v bun || true
  bun --version 2>/dev/null || true
} | tee "$OUT/tool_versions.txt"

if [ -f package.json ]; then
  node -e 'const p=require("./package.json"); console.log(JSON.stringify({name:p.name, scripts:p.scripts, dependencies:Object.keys(p.dependencies||{}), devDependencies:Object.keys(p.devDependencies||{})}, null, 2))' \
    > "$OUT/root_package_node_parse.json" 2> "$OUT/root_package_node_parse.err" || true
fi

# Do NOT npm install yet. Only run tests if deps already exist.
if [ -d node_modules ]; then
  echo "[node_modules exists] attempting cheap test/lint/typecheck"
  timeout 120 npm test > "$OUT/npm_test.out" 2> "$OUT/npm_test.err" || true
  timeout 120 npm run lint > "$OUT/npm_lint.out" 2> "$OUT/npm_lint.err" || true
  timeout 120 npm run typecheck > "$OUT/npm_typecheck.out" 2> "$OUT/npm_typecheck.err" || true
  timeout 120 npm run build > "$OUT/npm_build.out" 2> "$OUT/npm_build.err" || true
else
  echo "[skip] no node_modules; avoiding install on low disk" | tee "$OUT/no_install_decision.txt"
fi

echo
echo "08 generate report"
python3 - "$OUT" "$REPO" "$OWNER_REPO" "$ISSUE_NUM" <<'PY'
import json, sys
from pathlib import Path

out = Path(sys.argv[1])
repo = Path(sys.argv[2])
owner_repo = sys.argv[3]
issue = sys.argv[4]

def load_json(name, default):
    p = out / name
    try:
        return json.loads(p.read_text())
    except Exception:
        return default

def read(name, limit=None):
    p = out / name
    if not p.exists():
        return ""
    s = p.read_text(errors="replace")
    return s if limit is None else s[:limit]

issue_view = load_json("issue_view.json", {})
summary = load_json("analysis_summary.json", {})
top = summary.get("top_candidate_files", [])
test_surface = summary.get("test_surface", [])

labels = [x.get("name") for x in issue_view.get("labels", [])] if issue_view else []

has_local_tests = bool(test_surface)
has_candidate_files = bool(top)
issue_body = issue_view.get("body") or ""
issue_mentions_validation = any(x in issue_body.lower() for x in ["validate", "validation", "payload", "user", "creation", "create"])
moneyish = any("bounty" in str(x).lower() for x in labels) or "bounty" in (issue_view.get("title","") + issue_body).lower()

if has_candidate_files and has_local_tests and issue_mentions_validation:
    verdict = "PATCH_NEXT"
elif has_candidate_files and issue_mentions_validation:
    verdict = "PATCH_PROBE_AFTER_INSTALL_DECISION"
else:
    verdict = "ASK_OR_PARK"

lines = []
lines.append(f"# {owner_repo} #{issue} Recon v1")
lines.append("")
lines.append("## Verdict")
lines.append("")
lines.append(f"`{verdict}`")
lines.append("")
lines.append("## Issue")
lines.append("")
lines.append("```json")
lines.append(json.dumps({
    "title": issue_view.get("title"),
    "state": issue_view.get("state"),
    "url": issue_view.get("url"),
    "labels": labels,
    "comment_count": len(issue_view.get("comments", [])) if issue_view else None,
}, indent=2))
lines.append("```")
lines.append("")
lines.append("## Static findings")
lines.append("")
lines.append(f"- bounty-ish: `{moneyish}`")
lines.append(f"- issue mentions validation/user payload: `{issue_mentions_validation}`")
lines.append(f"- package manager guess: `{summary.get('package_manager_guess')}`")
lines.append(f"- package count: `{summary.get('package_count')}`")
lines.append(f"- local test/build/lint script surface: `{len(test_surface)}`")
lines.append(f"- candidate implementation/test files: `{len(top)}`")
lines.append("")
lines.append("## Test surface")
lines.append("")
lines.append("```json")
lines.append(json.dumps(test_surface[:30], indent=2))
lines.append("```")
lines.append("")
lines.append("## Top candidate files")
lines.append("")
lines.append("```json")
lines.append(json.dumps(top[:30], indent=2))
lines.append("```")
lines.append("")
lines.append("## Next action")
lines.append("")
if verdict == "PATCH_NEXT":
    lines.append("Proceed to a surgical patch probe: inspect the top candidate route/controller/service file, add/repair payload validation, add targeted regression tests, run the smallest local test command.")
elif verdict == "PATCH_PROBE_AFTER_INSTALL_DECISION":
    lines.append("Likely patchable, but first inspect candidate context and decide whether dependency install is safe. Avoid broad install while disk is low.")
else:
    lines.append("Do not patch yet. Ask maintainer for exact acceptance/test command or park if issue text is stale/ambiguous.")
lines.append("")
lines.append("## Candidate context excerpt")
lines.append("")
lines.append("```text")
lines.append(read("candidate_context.txt", 20000))
lines.append("```")
lines.append("")
lines.append("## Static grep excerpt")
lines.append("")
lines.append("```text")
lines.append(read("static_grep.txt", 12000))
lines.append("```")
lines.append("")
(out / "REPORT.md").write_text("\n".join(lines) + "\n")
print((out / "REPORT.md").read_text())
PY

echo
echo "09 commit artifact"
cd "$ROOT" || exit 1
git add "$OUT" xevrion_agent_playground_2207_recon_v1.sh
git commit -m "Add xevrion agent-playground issue2207 recon v1" || true
git push origin local-main || true

echo
echo "10 final status"
git status --short
df -h /
du -sh "$REPO" 2>/dev/null || true
echo
echo "Artifacts:"
echo "$OUT/REPORT.md"
echo "$OUT/analysis_summary.json"
echo "$OUT/candidate_context.txt"
echo "$OUT/issue_view.json"
