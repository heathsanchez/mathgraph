#!/usr/bin/env bash
set -u

ROOT="/Users/heath/Documents/mathgraph-lean-work"

X_OUT="$ROOT/artifacts/bounty_triage_v1/xevrion_agent_playground_2207_park_v2"
T_OWNER_REPO="tinygrad/tinygrad"
T_ISSUE="3039"
T_REPO="$ROOT/external/bounty_triage_v1/tinygrad__tinygrad"
T_OUT="$ROOT/artifacts/bounty_triage_v1/tinygrad_3039_parallel_scan_recon_v1"

mkdir -p "$X_OUT" "$T_OUT"
cd "$ROOT" || exit 1

echo "MathGraph bounty routing — park xevrion #2207, inspect tinygrad #3039"
echo

echo "01 park xevrion"
cat > "$X_OUT/REPORT.md" <<'MD'
# xevrion-v2/agent-playground #2207 Park Decision

## Verdict

`PARK_FALSE_POSITIVE_NO_PATCH_SURFACE`

## Reason

The issue title says `[Bounty] Validate user creation payloads`, but the checked repository does not currently contain the implementation surface needed for a normal validation patch.

Observed repo surface:

- `package.json`
- `README.md`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `leaderboard.json`

Missing expected patch targets:

- no backend package
- no user route/controller/service
- no validation schema files
- no tests for user creation payloads
- no real local acceptance test beyond root workspace scripts

The README describes intended architecture, including auth routes, CRUD routes, controller/service/route layers, and Zod schemas, but those files were not present in the checkout. Therefore a PR would likely require inventing substantial application structure rather than fixing a concrete validation bug.

## MathGraph classification

- external judge: weak / absent
- local test: weak / absent
- patch surface: absent
- bounty confidence: low
- action: park unless maintainer points to concrete files and acceptance tests

## Next route

Move to `tinygrad/tinygrad #3039` because it has stronger OSS reputation, real code, real tests, and a concrete performance/algorithm target.
MD

cat "$X_OUT/REPORT.md"

echo
echo "02 commit xevrion park artifact"
git add "$X_OUT"
git commit -m "Park xevrion issue2207 no patch surface" || true
git push origin local-main || true

echo
echo "03 clone/update tinygrad"
mkdir -p "$(dirname "$T_REPO")"
if [ ! -d "$T_REPO/.git" ]; then
  gh repo clone "$T_OWNER_REPO" "$T_REPO" -- --filter=blob:none 2>&1 | tee "$T_OUT/clone.log"
else
  echo "[exists] $T_REPO"
fi

cd "$T_REPO" || exit 1
git remote -v | tee "$T_OUT/remotes.txt"
git fetch origin --prune 2>&1 | tee "$T_OUT/git_fetch.log"
DEFAULT_BRANCH="$(git remote show origin 2>/dev/null | awk '/HEAD branch/ {print $NF}' | head -1)"
if [ -z "$DEFAULT_BRANCH" ]; then DEFAULT_BRANCH="master"; fi
git checkout "$DEFAULT_BRANCH" 2>&1 | tee "$T_OUT/git_checkout.log" || true
git pull --ff-only origin "$DEFAULT_BRANCH" 2>&1 | tee "$T_OUT/git_pull.log" || true
git rev-parse HEAD | tee "$T_OUT/head.txt"

echo
echo "04 issue view"
gh issue view "$T_ISSUE" --repo "$T_OWNER_REPO" \
  --json number,title,state,author,labels,body,comments,url,createdAt,updatedAt \
  > "$T_OUT/issue_view.json" 2> "$T_OUT/issue_view.err" || true

python3 - "$T_OUT" <<'PY'
import json, sys
from pathlib import Path
out = Path(sys.argv[1])
p = out / "issue_view.json"
if p.exists() and p.stat().st_size:
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
    (out / "issue_body.md").write_text(j.get("body") or "")
    (out / "issue_comments.md").write_text(
        "\n---\n".join(
            f"## {c.get('author',{}).get('login')} — {c.get('createdAt')}\n\n{c.get('body') or ''}"
            for c in j.get("comments", [])
        )
    )
else:
    print("[issue] no json")
PY

echo
echo "05 project inventory"
{
  echo "HEAD:"
  git rev-parse HEAD
  echo
  echo "top files:"
  find . -maxdepth 2 -type f | sed 's#^\./##' | sort | head -300
  echo
  echo "python/test files:"
  find . -maxdepth 4 -type f \( -name '*.py' -o -name 'pyproject.toml' -o -name 'setup.py' -o -name 'requirements*.txt' \) \
    | sed 's#^\./##' | sort | head -500
} | tee "$T_OUT/project_inventory.txt"

echo
echo "06 focused grep for scan/mamba/cumsum/prefix"
{
  echo "===== scan/cumsum/prefix/mamba hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=__pycache__ --exclude-dir=.venv --exclude-dir=venv \
    "parallel_scan|associative_scan|scan\\(|cumsum|cumprod|prefix|mamba|selective_scan|S6|ssm|recurrence" . 2>/dev/null | head -2000

  echo
  echo "===== test hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=__pycache__ --exclude-dir=.venv --exclude-dir=venv \
    "test_.*scan|scan.*test|cumsum|cumprod|mamba|selective_scan|prefix" test tests tinygrad examples extra 2>/dev/null | head -2000
} | tee "$T_OUT/focused_grep.txt"

echo
echo "07 static candidate map"
python3 - "$T_REPO" "$T_OUT" <<'PY'
import json, re, sys
from pathlib import Path

repo = Path(sys.argv[1])
out = Path(sys.argv[2])

terms = {
    "scan": 8,
    "parallel_scan": 20,
    "associative_scan": 20,
    "cumsum": 14,
    "cumprod": 12,
    "prefix": 8,
    "mamba": 18,
    "selective_scan": 22,
    "ssm": 10,
    "recurrence": 8,
    "kernel": 4,
    "schedule": 4,
    "uop": 4,
    "lower": 4,
    "tensor": 2,
    "test": 2,
}
skip_dirs = {".git", "__pycache__", ".venv", "venv", "build", "dist"}

cands = []
for p in repo.rglob("*"):
    if not p.is_file():
        continue
    rel = p.relative_to(repo)
    if any(x in skip_dirs for x in rel.parts):
        continue
    if p.suffix.lower() not in {".py", ".md", ".txt", ".toml", ".yaml", ".yml"}:
        continue
    try:
        txt = p.read_text(errors="replace")
    except Exception:
        continue
    low = txt.lower()
    score = 0
    hits = {}
    for t,w in terms.items():
        c = low.count(t)
        if c:
            score += c*w
            hits[t] = c
    if score:
        cands.append({
            "path": str(rel),
            "score": score,
            "hits": hits,
            "lines": txt.count("\n")+1,
            "bytes": len(txt.encode(errors="replace")),
        })

cands.sort(key=lambda x: (-x["score"], x["path"]))
(out / "candidate_files.json").write_text(json.dumps(cands[:300], indent=2))

snips = []
pat = re.compile(r"(parallel_scan|associative_scan|scan|cumsum|cumprod|prefix|mamba|selective_scan|ssm|recurrence)", re.I)
for item in cands[:50]:
    p = repo / item["path"]
    txt = p.read_text(errors="replace")
    lines = txt.splitlines()
    hit_lines = [i for i,l in enumerate(lines) if pat.search(l)]
    if not hit_lines:
        continue
    snips.append(f"\n\n===== {item['path']} score={item['score']} =====")
    used = []
    for h in hit_lines[:10]:
        start = max(0, h-14)
        end = min(len(lines), h+24)
        if any(abs(start-s) < 10 for s,e in used):
            continue
        used.append((start,end))
        snips.append(f"\n--- around line {h+1} ---")
        for i in range(start,end):
            snips.append(f"{i+1:04d}: {lines[i]}")
(out / "candidate_context.txt").write_text("\n".join(snips) + "\n")

summary = {
    "candidate_count": len(cands),
    "top_candidate_files": cands[:30],
}
(out / "analysis_summary.json").write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=2)[:20000])
PY

echo
echo "08 cheap environment/test surface"
{
  echo "python:"
  command -v python3 || true
  python3 --version || true
  echo
  echo "pytest:"
  python3 - <<'PY'
try:
    import pytest
    print("pytest", pytest.__version__)
except Exception as e:
    print("pytest_missing", repr(e))
try:
    import tinygrad
    print("tinygrad_import_from_env", tinygrad.__file__)
except Exception as e:
    print("tinygrad_import_missing_or_local_needed", repr(e))
PY
  echo
  echo "makefile/pyproject:"
  [ -f Makefile ] && sed -n '1,220p' Makefile || true
  [ -f pyproject.toml ] && sed -n '1,220p' pyproject.toml || true
} | tee "$T_OUT/env_and_test_surface.txt"

echo
echo "09 optional local tinygrad import smoke"
# Avoid installing. Just test local import path and targeted module discovery.
PYTHONPATH="$T_REPO" python3 - <<'PY' > "$T_OUT/local_import_smoke.out" 2> "$T_OUT/local_import_smoke.err" || true
import tinygrad, sys
print("tinygrad", tinygrad.__file__)
from tinygrad import Tensor
print("Tensor", Tensor)
print("has cumsum", hasattr(Tensor, "cumsum"))
print("has cummax", hasattr(Tensor, "cummax"))
print("has cumprod", hasattr(Tensor, "cumprod"))
PY

cat "$T_OUT/local_import_smoke.out" || true
cat "$T_OUT/local_import_smoke.err" || true

echo
echo "10 generate report"
python3 - "$T_OUT" "$T_OWNER_REPO" "$T_ISSUE" <<'PY'
import json, sys
from pathlib import Path

out = Path(sys.argv[1])
owner_repo = sys.argv[2]
issue = sys.argv[3]

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

body = issue_view.get("body") or ""
title = issue_view.get("title") or ""
low = (title + "\n" + body).lower()

has_scan_surface = any(
    any(k in item.get("hits", {}) for k in ["scan","parallel_scan","associative_scan","cumsum","mamba","selective_scan"])
    for item in top[:20]
)
has_local_import = "has cumsum True" in read("local_import_smoke.out")
issue_concrete = any(x in low for x in ["scan", "mamba", "parallel", "cumsum", "prefix"])

if has_scan_surface and has_local_import and issue_concrete:
    verdict = "PROMISING_PATCH_PROBE_NEXT"
elif has_scan_surface and issue_concrete:
    verdict = "PROMISING_NEEDS_TEST_COMMAND"
else:
    verdict = "ASK_OR_PARK"

lines = []
lines.append(f"# {owner_repo} #{issue} Parallel Scan Recon v1")
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
    "labels": [x.get("name") for x in issue_view.get("labels", [])] if issue_view else [],
    "comment_count": len(issue_view.get("comments", [])) if issue_view else None,
    "updatedAt": issue_view.get("updatedAt"),
}, indent=2))
lines.append("```")
lines.append("")
lines.append("## Static findings")
lines.append("")
lines.append(f"- issue concrete for scan/mamba: `{issue_concrete}`")
lines.append(f"- scan/cumsum candidate surface: `{has_scan_surface}`")
lines.append(f"- local tinygrad import smoke has Tensor.cumsum: `{has_local_import}`")
lines.append(f"- candidate files: `{summary.get('candidate_count')}`")
lines.append("")
lines.append("## Top candidate files")
lines.append("")
lines.append("```json")
lines.append(json.dumps(top[:40], indent=2))
lines.append("```")
lines.append("")
lines.append("## Local import smoke")
lines.append("")
lines.append("```text")
lines.append(read("local_import_smoke.out", 4000))
lines.append(read("local_import_smoke.err", 4000))
lines.append("```")
lines.append("")
lines.append("## Candidate context excerpt")
lines.append("")
lines.append("```text")
lines.append(read("candidate_context.txt", 30000))
lines.append("```")
lines.append("")
lines.append("## Issue body excerpt")
lines.append("")
lines.append("```text")
lines.append(body[:12000])
lines.append("```")
lines.append("")
lines.append("## Next action")
lines.append("")
if verdict == "PROMISING_PATCH_PROBE_NEXT":
    lines.append("Build a minimal benchmark/proof probe around Tensor.cumsum / scan lowering. Do not open PR until a before/after local metric exists.")
elif verdict == "PROMISING_NEEDS_TEST_COMMAND":
    lines.append("Ask/derive exact benchmark command before patching.")
else:
    lines.append("Park if issue is stale or lacks local metric.")
lines.append("")
(out / "REPORT.md").write_text("\n".join(lines) + "\n")
print((out / "REPORT.md").read_text())
PY

echo
echo "11 commit artifacts"
cd "$ROOT" || exit 1
git add "$X_OUT" "$T_OUT" park_xevrion_then_tinygrad_3039_recon_v1.sh
git commit -m "Park xevrion and inspect tinygrad issue3039" || true
git push origin local-main || true

echo
echo "12 final status"
git status --short
df -h /
du -sh "$T_REPO" 2>/dev/null || true
echo
echo "Artifacts:"
echo "$X_OUT/REPORT.md"
echo "$T_OUT/REPORT.md"
echo "$T_OUT/analysis_summary.json"
echo "$T_OUT/candidate_context.txt"
