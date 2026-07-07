#!/usr/bin/env bash
set -euo pipefail

echo "MathGraph Cash Win Deep Recon v24"
echo "Goal: deep-check tinygrad#3039 and QuantumSavory#132 for claim risk, local verifier, and smallest viable PR path."
echo

ROOT="/Users/heath/Documents/mathgraph-lean-work"
OUT="$ROOT/artifacts/cash_win_deep_recon_v24"
mkdir -p "$OUT"
cd "$ROOT"

echo "01 status"
date -u +"%Y-%m-%dT%H:%M:%SZ" | tee "$OUT/status_start.txt"
df -h / | tee "$OUT/df_start.txt"
git status --short | tee "$OUT/mathgraph_status_start.txt" || true
echo

echo "02 tool gate"
{
  echo "===== paths ====="
  command -v python3 || true
  command -v pip || true
  command -v pytest || true
  command -v node || true
  command -v npm || true
  command -v julia || true
  command -v git || true
  command -v make || true
  echo
  echo "===== versions ====="
  python3 --version 2>/dev/null || true
  pip --version 2>/dev/null || true
  pytest --version 2>/dev/null || true
  node --version 2>/dev/null || true
  npm --version 2>/dev/null || true
  julia --version 2>/dev/null || true
  git --version 2>/dev/null || true
} | tee "$OUT/tool_gate.txt"
echo

echo "03 issue and PR audit"
python3 - "$OUT" <<'PY'
from pathlib import Path
import subprocess, json, time, re, sys

out = Path(sys.argv[1])
cands = [
    {
        "name": "tinygrad_3039",
        "repo": "tinygrad/tinygrad",
        "issue": "3039",
        "search": "3039 OR parallel scan OR associative_scan OR scan associative OR Mamba",
    },
    {
        "name": "quantumsavory_132",
        "repo": "QuantumSavory/QuantumSavory.jl",
        "issue": "132",
        "search": "132 OR Makie OR visualization OR visualisation",
    },
]

def run(cmd):
    return subprocess.run(cmd, text=True, capture_output=True)

summary = []
for c in cands:
    name = c["name"]
    repo = c["repo"]
    issue = c["issue"]
    print(f"audit {repo}#{issue}")

    issue_txt = run(["gh", "issue", "view", issue, "-R", repo, "--comments"])
    (out / f"{name}_issue.txt").write_text(issue_txt.stdout + issue_txt.stderr)

    issue_json = run(["gh", "issue", "view", issue, "-R", repo, "--json", "title,url,body,state,labels,assignees,comments,author,createdAt,updatedAt"])
    try:
        issue_data = json.loads(issue_json.stdout or "{}")
    except Exception:
        issue_data = {}

    pr_json = run(["gh", "pr", "list", "-R", repo, "--state", "all", "--limit", "100", "--search", c["search"], "--json", "number,title,state,isDraft,author,createdAt,updatedAt,mergedAt,url,headRefName,baseRefName"])
    try:
        prs = json.loads(pr_json.stdout or "[]")
    except Exception:
        prs = []

    repo_json = run(["gh", "repo", "view", repo, "--json", "nameWithOwner,description,stargazerCount,forkCount,isArchived,isPrivate,pushedAt,primaryLanguage,url"])
    try:
        repo_data = json.loads(repo_json.stdout or "{}")
    except Exception:
        repo_data = {}

    (out / f"{name}_issue.json").write_text(json.dumps(issue_data, indent=2) + "\n")
    (out / f"{name}_prs.json").write_text(json.dumps(prs, indent=2) + "\n")
    (out / f"{name}_repo.json").write_text(json.dumps(repo_data, indent=2) + "\n")

    text = "\n".join([
        issue_data.get("title") or "",
        issue_data.get("body") or "",
        "\n".join((cm.get("body") or "") for cm in issue_data.get("comments", []) if isinstance(cm, dict)),
    ])
    claim_words = re.findall(r"claim|claimed|assigned|working on|PR|pull request|submitted|merged|bounty is yours|reserved|until", text, re.I)
    no_one = bool(re.search(r"claimed by\s+`?no one`?|claimed by no one|unclaimed|available", text, re.I))
    open_prs = [p for p in prs if p.get("state") == "OPEN"]
    merged_prs = [p for p in prs if p.get("mergedAt")]
    assignees = [a.get("login") for a in issue_data.get("assignees", []) if isinstance(a, dict)]

    summary.append({
        "name": name,
        "repo": repo,
        "issue": issue,
        "url": issue_data.get("url"),
        "title": issue_data.get("title"),
        "stars": repo_data.get("stargazerCount"),
        "language": (repo_data.get("primaryLanguage") or {}).get("name"),
        "assignees": assignees,
        "claim_words_count": len(claim_words),
        "explicit_no_one_or_available": no_one,
        "open_related_prs": open_prs,
        "merged_related_prs": merged_prs,
    })
    time.sleep(0.25)

(out / "audit_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=2))
PY
echo

echo "04 clone/update and static source surfaces"
python3 - "$ROOT" "$OUT" <<'PY'
from pathlib import Path
import subprocess, json, sys

root = Path(sys.argv[1])
out = Path(sys.argv[2])
cands = [
    ("tinygrad_3039", "tinygrad/tinygrad", "3039"),
    ("quantumsavory_132", "QuantumSavory/QuantumSavory.jl", "132"),
]

def run(cmd, cwd=None):
    return subprocess.run(cmd, text=True, capture_output=True, cwd=cwd)

for name, repo, issue in cands:
    safe = repo.replace("/", "__")
    d = root / "external" / "cash_win_deep_recon_v24" / f"{safe}_{issue}"
    d.parent.mkdir(parents=True, exist_ok=True)
    if not (d / ".git").exists():
        p = run(["gh", "repo", "clone", repo, str(d), "--", "--filter=blob:none"])
        (out / f"{name}_clone.out").write_text(p.stdout)
        (out / f"{name}_clone.err").write_text(p.stderr)
    else:
        p = run(["git", "fetch", "origin"], cwd=d)
        (out / f"{name}_fetch.out").write_text(p.stdout)
        (out / f"{name}_fetch.err").write_text(p.stderr)

    run(["git", "checkout", "master"], cwd=d)
    run(["git", "checkout", "main"], cwd=d)
    branch = run(["git", "branch", "--show-current"], cwd=d).stdout.strip()
    if branch:
        run(["git", "pull", "--ff-only", "origin", branch], cwd=d)

    head = run(["git", "rev-parse", "HEAD"], cwd=d).stdout.strip()
    status = run(["git", "status", "--short"], cwd=d).stdout
    files = run(["bash", "-lc", "find . -maxdepth 4 -type f | sed 's#^./##' | sort | head -700"], cwd=d).stdout

    (out / f"{name}_head.txt").write_text(head + "\n")
    (out / f"{name}_status.txt").write_text(status)
    (out / f"{name}_files.txt").write_text(files)

    if name == "tinygrad_3039":
        cmd = r'''
echo "===== package/test files ====="
find . -maxdepth 3 \( -name "setup.py" -o -name "pyproject.toml" -o -name "requirements*.txt" -o -name "Makefile" \) -type f | sort
echo
echo "===== scan refs ====="
grep -RIn --exclude-dir=.git --exclude-dir=.venv --exclude-dir=__pycache__ --exclude-dir=.mypy_cache -- "associative_scan\|parallel scan\|cumsum\|cumprod\|prefix sum\|scan\|Mamba\|mamba" tinygrad test extra examples 2>/dev/null | head -600 || true
echo
echo "===== tensor/op refs ====="
grep -RIn --exclude-dir=.git --exclude-dir=.venv --exclude-dir=__pycache__ -- "cumsum\|cumprod\|Tensor.*scan\|ReduceOps\|Ops." tinygrad test 2>/dev/null | head -600 || true
'''
    else:
        cmd = r'''
echo "===== julia project files ====="
find . -maxdepth 3 \( -name "Project.toml" -o -name "Manifest.toml" -o -name "runtests.jl" -o -name "*.jl" \) -type f | sort | head -500
echo
echo "===== Makie/visual refs ====="
grep -RIn --exclude-dir=.git -- "Makie\|visual\|plot\|GraphMakie\|CairoMakie\|WGLMakie\|draw\|render" src test docs examples benchmark 2>/dev/null | head -600 || true
echo
echo "===== test refs ====="
grep -RIn --exclude-dir=.git -- "@test\|runtests\|@testset" test src docs examples 2>/dev/null | head -400 || true
'''
    surf = run(["bash", "-lc", cmd], cwd=d)
    (out / f"{name}_surface.txt").write_text(surf.stdout + surf.stderr)
PY
echo

echo "05 classify"
python3 - "$OUT" <<'PY'
from pathlib import Path
import json, re, sys

out = Path(sys.argv[1])
summary = json.loads((out / "audit_summary.json").read_text())
tool = (out / "tool_gate.txt").read_text(errors="replace")

has_python = bool(re.search(r"/python3$|^python3$", tool, re.M))
has_julia = bool(re.search(r"/julia$|^julia$", tool, re.M))

decisions = []
for s in summary:
    name = s["name"]
    surface = (out / f"{name}_surface.txt").read_text(errors="replace") if (out / f"{name}_surface.txt").exists() else ""
    files = (out / f"{name}_files.txt").read_text(errors="replace") if (out / f"{name}_files.txt").exists() else ""
    open_prs = s.get("open_related_prs") or []
    assignees = s.get("assignees") or []
    claim_count = int(s.get("claim_words_count") or 0)
    explicit_available = bool(s.get("explicit_no_one_or_available"))

    if name == "tinygrad_3039":
        complexity = "HIGH_ALGO"
        local_tool = has_python
        local_surface = bool(re.search(r"test|pyproject|setup.py|cumsum|scan|Ops", surface + files, re.I))
        base_score = 50
        if local_tool: base_score += 15
        if local_surface: base_score += 15
        if open_prs: base_score -= 25
        if claim_count > 10: base_score -= 15
        verdict = "RECON_ONLY_HIGH_COMPLEXITY"
        next_action = "Do not claim yet. First inspect tinygrad op/reduce architecture and see whether a minimal associative_scan primitive can be tested locally."
    else:
        complexity = "MEDIUM_VISUAL"
        local_tool = has_julia
        local_surface = bool(re.search(r"Makie|visual|plot|@test|Project.toml", surface + files, re.I))
        base_score = 50
        if local_tool: base_score += 20
        if local_surface: base_score += 15
        if explicit_available: base_score += 15
        if open_prs: base_score -= 25
        if assignees: base_score -= 25
        if claim_count > 20 and not explicit_available: base_score -= 10
        verdict = "CLAIM_WINDOW_CANDIDATE" if base_score >= 75 and not open_prs and not assignees else "ASK_OR_RECON"
        next_action = "If issue text confirms claimed by no one, post a narrow claim for a small Makie visualization/test slice; otherwise ask availability."

    decisions.append({
        **s,
        "score": base_score,
        "complexity": complexity,
        "local_tool_available": local_tool,
        "local_surface": local_surface,
        "verdict": verdict,
        "next_action": next_action,
    })

decisions.sort(key=lambda d: (-d["score"], d["complexity"]))
(out / "decision.json").write_text(json.dumps(decisions, indent=2) + "\n")

md = []
md.append("# Cash Win Deep Recon v24")
md.append("")
md.append("## Verdicts")
md.append("")
for d in decisions:
    md.append(f"### {d['repo']}#{d['issue']} - {d['title']}")
    md.append("")
    md.append(f"- Verdict: `{d['verdict']}`")
    md.append(f"- Score: `{d['score']}`")
    md.append(f"- Complexity: `{d['complexity']}`")
    md.append(f"- Local tool available: `{d['local_tool_available']}`")
    md.append(f"- Local surface: `{d['local_surface']}`")
    md.append(f"- Claim words count: `{d['claim_words_count']}`")
    md.append(f"- Explicit available/no-one wording: `{d['explicit_no_one_or_available']}`")
    md.append(f"- Open related PRs: `{len(d['open_related_prs'])}`")
    md.append(f"- Assignees: `{', '.join(d['assignees']) if d['assignees'] else ''}`")
    md.append(f"- URL: {d['url']}")
    md.append(f"- Next: {d['next_action']}")
    md.append("")
md.append("## Recommendation")
md.append("")
md.append("Prefer QuantumSavory#132 only if the bounty text really says no one has claimed it and Julia is runnable. Keep tinygrad#3039 as a high-value but larger algorithmic route, not a quick cash patch.")
md.append("")
(out / "DEEP_RECON_REPORT.md").write_text("\n".join(md) + "\n")
print((out / "DEEP_RECON_REPORT.md").read_text())
PY
echo

echo "06 write comment drafts"
cat > "$OUT/quantumsavory_132_claim_draft.md" <<'MD'
Hi, I’d like to claim a narrow first slice of this bounty if it is still available.

To avoid overlapping with larger visualization work, I’d start with a small, testable Makie-focused improvement: inspect the current visualization entry points, add one focused capability or example that is currently missing, and include local verification notes. I’ll keep the PR small and avoid broad refactors.
MD

cat > "$OUT/tinygrad_3039_availability_draft.md" <<'MD'
Hi, is this bounty still open for a new implementation attempt?

Before claiming, I want to inspect the current reduce/op architecture and see whether I can make a small locally tested associative scan primitive rather than a speculative large change.
MD

echo "QuantumSavory #132 draft:"
cat "$OUT/quantumsavory_132_claim_draft.md"
echo
echo "tinygrad #3039 draft:"
cat "$OUT/tinygrad_3039_availability_draft.md"
echo

echo "07 commit artifact"
cd "$ROOT"
git add "$OUT" cash_win_deep_recon_v24.sh
git commit -m "Deep recon cash candidates v24" || true
git push origin local-main || true
echo

echo "08 final"
git status --short
df -h /
echo
echo "Artifacts:"
echo "$OUT/DEEP_RECON_REPORT.md"
echo "$OUT/decision.json"
echo "$OUT/tinygrad_3039_issue.txt"
echo "$OUT/tinygrad_3039_surface.txt"
echo "$OUT/quantumsavory_132_issue.txt"
echo "$OUT/quantumsavory_132_surface.txt"
echo "$OUT/quantumsavory_132_claim_draft.md"
echo "$OUT/tinygrad_3039_availability_draft.md"
