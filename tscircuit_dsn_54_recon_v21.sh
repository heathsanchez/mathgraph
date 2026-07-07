#!/usr/bin/env bash
set -euo pipefail

echo "MathGraph tscircuit/dsn-converter #54 Recon v21"
echo "Goal: verify whether #54 is a small local-testable cash win before claiming or patching."
echo

ROOT="/Users/heath/Documents/mathgraph-lean-work"
REPO="tscircuit/dsn-converter"
ISSUE="54"
DIR="$ROOT/external/cash_win_recon_v21/tscircuit__dsn-converter_54"
OUT="$ROOT/artifacts/tscircuit_dsn_54_recon_v21"

mkdir -p "$OUT"
cd "$ROOT"

echo "01 status"
date -u +"%Y-%m-%dT%H:%M:%SZ" | tee "$OUT/status_start.txt"
df -h / | tee "$OUT/df_start.txt"
git status --short | tee "$OUT/mathgraph_status_start.txt" || true
echo

echo "02 issue audit"
gh issue view "$ISSUE" -R "$REPO" --comments > "$OUT/issue_54_comments.txt"
grep -nEi "bounty|claim|claimed|assigned|available|smoothie|dsn|test|pr|pull request|heathsanchez" "$OUT/issue_54_comments.txt" | tee "$OUT/issue_signal_lines.txt" || true
echo

echo "03 clone/update"
mkdir -p "$(dirname "$DIR")"
if [ ! -d "$DIR/.git" ]; then
  gh repo clone "$REPO" "$DIR" -- --filter=blob:none
else
  git -C "$DIR" fetch origin
fi

cd "$DIR"
git checkout main 2>/dev/null || git checkout master 2>/dev/null || true
git pull --ff-only origin "$(git branch --show-current)" || true
git rev-parse HEAD | tee "$OUT/head.txt"
git status --short | tee "$OUT/repo_status_start.txt"
echo

echo "04 repo surface"
{
  echo "===== top files ====="
  find . -maxdepth 4 -type f | sed 's#^\./##' | sort | head -500
  echo
  echo "===== package files ====="
  find . -maxdepth 3 \( -name "package.json" -o -name "pnpm-lock.yaml" -o -name "package-lock.json" -o -name "yarn.lock" -o -name "bun.lockb" -o -name "tsconfig.json" -o -name "vitest.config.*" -o -name "jest.config.*" \) -type f | sort
  echo
  echo "===== package.json ====="
  [ -f package.json ] && cat package.json || true
  echo
  echo "===== DSN/Smoothie refs ====="
  grep -RIn --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=dist --exclude-dir=.turbo -- "smoothie\|freerouting\|dsn\|circuit json\|CircuitJson\|convert" . | head -500 || true
  echo
  echo "===== tests refs ====="
  grep -RIn --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=dist -- "describe(\|it(\|test(\|expect(\|vitest\|jest\|bun:test" . | head -300 || true
} | tee "$OUT/repo_surface.txt"
echo

echo "05 tool gate"
{
  echo "===== paths ====="
  command -v node || true
  command -v npm || true
  command -v pnpm || true
  command -v yarn || true
  command -v bun || true
  command -v npx || true
  command -v python3 || true
  command -v make || true
  echo
  echo "===== versions ====="
  node --version 2>/dev/null || true
  npm --version 2>/dev/null || true
  pnpm --version 2>/dev/null || true
  yarn --version 2>/dev/null || true
  bun --version 2>/dev/null || true
} | tee "$OUT/tool_gate.txt"
echo

echo "06 package script extraction"
python3 - "$OUT" <<'PY'
from pathlib import Path
import json, sys
out = Path(sys.argv[1])
pkg = Path("package.json")
data = json.loads(pkg.read_text()) if pkg.exists() else {}
scripts = data.get("scripts", {})
deps = sorted(list((data.get("dependencies") or {}).keys()))
devdeps = sorted(list((data.get("devDependencies") or {}).keys()))
report = {
    "name": data.get("name"),
    "version": data.get("version"),
    "scripts": scripts,
    "dependencies_count": len(deps),
    "devDependencies_count": len(devdeps),
    "dependencies_head": deps[:50],
    "devDependencies_head": devdeps[:50],
}
(out / "package_summary.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
PY
echo

echo "07 no-install static diagnosis"
python3 - "$OUT" <<'PY'
from pathlib import Path
import json, re, sys

out = Path(sys.argv[1])
issue = (out / "issue_54_comments.txt").read_text(errors="replace")
surface = (out / "repo_surface.txt").read_text(errors="replace")
tools = (out / "tool_gate.txt").read_text(errors="replace")
pkg = json.loads((out / "package_summary.json").read_text()) if (out / "package_summary.json").exists() else {}

claim_risk = bool(re.search(r"claimed|assigned|working on|pull request|PR", issue, re.I))
bounty_visible = bool(re.search(r"/bounty|\$70|bounty", issue, re.I))
smoothie_visible = bool(re.search(r"smoothie|Issue145|freerouting", issue, re.I))
has_node = bool(re.search(r"^/.*/node$|^node$", tools, re.M))
has_npm = bool(re.search(r"^/.*/npm$|^npm$", tools, re.M))
has_pnpm = bool(re.search(r"^/.*/pnpm$|^pnpm$", tools, re.M))
has_tests = bool(re.search(r"test|vitest|jest|bun:test", json.dumps(pkg.get("scripts", {}), indent=2), re.I) or re.search(r"describe\(|it\(|expect\(", surface))
has_src = bool(re.search(r"\.ts|src/|lib/", surface))

score = 0
reasons = []
if bounty_visible:
    score += 20; reasons.append("bounty visible")
if smoothie_visible:
    score += 20; reasons.append("concrete Smoothie Board DSN target visible")
if has_node and (has_npm or has_pnpm):
    score += 20; reasons.append("Node package toolchain visible")
if has_tests:
    score += 20; reasons.append("test surface visible")
if has_src:
    score += 10; reasons.append("source surface visible")
if claim_risk:
    score -= 20; reasons.append("claim/PR risk in comments")

verdict = "CLAIM_THEN_INSTALL_REPRO" if score >= 60 and not claim_risk else "RECON_MORE_OR_PARK"

decision = {
    "verdict": verdict,
    "score": score,
    "reasons": reasons,
    "issue": "https://github.com/tscircuit/dsn-converter/issues/54",
    "bounty_visible": bounty_visible,
    "claim_risk": claim_risk,
    "has_node": has_node,
    "has_npm": has_npm,
    "has_pnpm": has_pnpm,
    "has_tests": has_tests,
    "has_src": has_src,
    "next": "Post claim comment, then install minimally and reproduce conversion failure." if verdict == "CLAIM_THEN_INSTALL_REPRO" else "Do not claim yet; inspect comments and repo surface manually.",
}
(out / "decision.json").write_text(json.dumps(decision, indent=2) + "\n")

md = []
md.append("# tscircuit/dsn-converter #54 Recon v21")
md.append("")
md.append("## Verdict")
md.append("")
md.append(f"`{verdict}`")
md.append("")
md.append("## Score")
md.append("")
md.append(f"- Score: `{score}`")
md.append(f"- Reasons: {', '.join(reasons)}")
md.append("")
md.append("## Gates")
md.append("")
for k in ["bounty_visible", "claim_risk", "has_node", "has_npm", "has_pnpm", "has_tests", "has_src"]:
    md.append(f"- {k}: `{decision[k]}`")
md.append("")
md.append("## Next")
md.append("")
md.append(decision["next"])
md.append("")
(out / "RECON_REPORT.md").write_text("\n".join(md) + "\n")
print((out / "RECON_REPORT.md").read_text())
PY
echo

echo "08 claim draft"
cat > "$OUT/claim_draft.md" <<'MD'
Hi, I’d like to claim a narrow first slice of this bounty if it is still available.

I’ll start by reproducing the Smoothie Board DSN conversion failure locally, then submit a small PR with one of:

- a focused parser/converter fix plus regression test, or
- a minimal failing fixture/test that isolates the unsupported DSN construct if the correct conversion behavior needs maintainer guidance.

I’ll keep the first PR small and include exact local reproduction/test commands.
MD
cat "$OUT/claim_draft.md"
echo

echo "09 commit artifact"
cd "$ROOT"
git add "$OUT" tscircuit_dsn_54_recon_v21.sh
git commit -m "Recon tscircuit dsn converter bounty v21" || true
git push origin local-main || true
echo

echo "10 final"
git status --short
df -h /
echo
echo "Artifacts:"
echo "$OUT/RECON_REPORT.md"
echo "$OUT/decision.json"
echo "$OUT/issue_54_comments.txt"
echo "$OUT/repo_surface.txt"
echo "$OUT/tool_gate.txt"
echo "$OUT/package_summary.json"
echo "$OUT/claim_draft.md"
