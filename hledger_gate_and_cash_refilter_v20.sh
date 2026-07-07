#!/usr/bin/env bash
set -euo pipefail

echo "MathGraph hledger Gate + Cash Refilter v20"
echo "Goal: decide if hledger is locally runnable; if not, park until verifier exists and refilter cash list for real projects only."
echo

ROOT="/Users/heath/Documents/mathgraph-lean-work"
H_OUT="$ROOT/artifacts/hledger_1825_watch_autopsy_v19"
OUT="$ROOT/artifacts/hledger_gate_and_cash_refilter_v20"
RANKED="$ROOT/artifacts/cash_win_scout_v16_rest/ranked_candidates.json"

mkdir -p "$OUT"
cd "$ROOT"

echo "01 status"
date -u +"%Y-%m-%dT%H:%M:%SZ" | tee "$OUT/status_start.txt"
df -h / | tee "$OUT/df_start.txt"
git status --short | tee "$OUT/mathgraph_status_start.txt" || true
echo

echo "02 hledger executable/toolchain gate"
{
  echo "===== executable paths ====="
  command -v hledger-ui || true
  command -v hledger || true
  command -v stack || true
  command -v cabal || true
  command -v ghc || true
  command -v ghcup || true
  command -v brew || true
  command -v nix || true
  command -v docker || true
  echo
  echo "===== versions if present ====="
  hledger-ui --version 2>/dev/null || true
  hledger --version 2>/dev/null || true
  stack --version 2>/dev/null || true
  cabal --version 2>/dev/null || true
  ghc --version 2>/dev/null || true
  ghcup --version 2>/dev/null || true
  brew --version 2>/dev/null | head -5 || true
  nix --version 2>/dev/null || true
  docker --version 2>/dev/null || true
} | tee "$OUT/hledger_gate.txt"
echo

echo "03 post conservative hledger update"
if [ -f "$H_OUT/issue_update_draft.md" ]; then
  gh issue comment 1825 -R simonmichael/hledger --body-file "$H_OUT/issue_update_draft.md" > "$OUT/hledger_update_comment.out" 2> "$OUT/hledger_update_comment.err" || true
  cat "$OUT/hledger_update_comment.out" || true
  cat "$OUT/hledger_update_comment.err" || true
else
  echo "missing $H_OUT/issue_update_draft.md" | tee "$OUT/hledger_update_comment.err"
fi
echo

echo "04 refilter cash scout to real candidates"
python3 - "$RANKED" "$OUT" <<'PY'
from pathlib import Path
import json, re, sys

ranked_path = Path(sys.argv[1])
out = Path(sys.argv[2])
rows = json.loads(ranked_path.read_text()) if ranked_path.exists() else []

deny_repo = re.compile(
    r"(agent-playground|BountyScout|bountyscout|Bounty-Hunters|bug-bounty|claude-builders-bounty|"
    r"ai-research|ai-growth-engine|zeroeye|TentOfTrials|Rustchain|rustchain-bounties|"
    r"bitcoin$|mysql$|cobra$|UnsafeLabs|SecureBananaLabs|LennyMalcolm0|Markp1598M|"
    r"xevrion|dev-kp-eloper|vansh-09|greyw0rks|zhangjiayang|Nexussyn|relayhop)",
    re.I,
)

deny_title = re.compile(
    r"(calculate the exact value of pi|bounty alert|test bounty|seed good first issues|"
    r"add is-.*-present api utility|opportunityies|star this repository)",
    re.I,
)

prefer_repo = re.compile(
    r"(hledger|QuantumSavory|QuantumSymbolics|JuliaGraphs|JuliaDynamics|tinygrad|tscircuit|Dasharo|cline)",
    re.I,
)

real = []
park = []

for r in rows:
    repo = r.get("repo", "")
    title = r.get("title", "")
    reasons = list(r.get("reasons", []))
    score = int(r.get("score", 0))
    amount = r.get("amount")
    assignees = r.get("assignees") or []
    verdict = r.get("verdict", "")

    real_score = score
    real_reasons = []

    if prefer_repo.search(repo):
        real_score += 25
        real_reasons.append("known-real-project")
    if deny_repo.search(repo) or deny_title.search(title):
        real_score -= 100
        real_reasons.append("synthetic/spam/proxy-risk")
    if assignees:
        real_score -= 20
        real_reasons.append("assigned-risk")
    if amount and amount >= 100:
        real_score += 10
        real_reasons.append("meaningful-payout")
    if re.search(r"(benchmark|performance|ci|workflow|test|julia|haskell|python|compiler|docs)", title, re.I):
        real_score += 10
        real_reasons.append("patchable-surface-title")

    new = dict(r)
    new["real_score"] = real_score
    new["real_reasons"] = real_reasons + reasons

    if real_score >= 65 and not deny_repo.search(repo) and not deny_title.search(title):
        real.append(new)
    else:
        park.append(new)

real.sort(key=lambda x: (-x["real_score"], -(x.get("amount") or 0), x.get("repo","")))
park.sort(key=lambda x: (-x["real_score"], -(x.get("amount") or 0), x.get("repo","")))

(out / "real_candidates.json").write_text(json.dumps(real, indent=2) + "\n")
(out / "parked_candidates.json").write_text(json.dumps(park, indent=2) + "\n")

md = []
md.append("# Cash Refilter v20")
md.append("")
md.append("## Real candidates")
md.append("")
for i, r in enumerate(real[:20], 1):
    amount = f"${r.get('amount')}" if r.get("amount") else "amount unclear"
    md.append(f"### {i}. {r.get('repo')}#{r.get('number')} - {r.get('title')}")
    md.append("")
    md.append(f"- Real score: `{r.get('real_score')}`")
    md.append(f"- Original score: `{r.get('score')}`")
    md.append(f"- Money: `{amount}`")
    md.append(f"- URL: {r.get('url')}")
    md.append(f"- Reasons: {', '.join(r.get('real_reasons', [])[:8])}")
    if r.get("assignees"):
        md.append(f"- Assignees: {', '.join(r.get('assignees'))}")
    md.append(f"- Snippet: {(r.get('snippet') or '')[:500]}")
    md.append("")
md.append("## Immediate recommendation")
md.append("")
md.append("1. hledger remains best if a verifier can be obtained.")
md.append("2. If hledger has no local executable/toolchain, use the next real Julia/benchmark candidate instead.")
md.append("3. Avoid synthetic bounty farms and mirror/proxy bounty repos.")
md.append("")
(out / "REAL_GOLD_LIST.md").write_text("\n".join(md) + "\n")
print((out / "REAL_GOLD_LIST.md").read_text())
PY
echo

echo "05 classify hledger gate"
python3 - "$OUT" <<'PY'
from pathlib import Path
import json, re, sys

out = Path(sys.argv[1])
gate = (out / "hledger_gate.txt").read_text(errors="replace")
real = json.loads((out / "real_candidates.json").read_text()) if (out / "real_candidates.json").exists() else []

can_run = bool(re.search(r"/hledger-ui$|^hledger-ui$", gate, re.M))
can_build = bool(re.search(r"/(stack|cabal|ghc)$|^(stack|cabal|ghc)$", gate, re.M))

decision = {
    "hledger": {
        "verdict": "RUN_REPRO_NEXT" if can_run else "BUILD_TOOLCHAIN_NEEDED" if can_build else "PARK_UNTIL_VERIFIER",
        "can_run_hledger_ui": can_run,
        "can_build_haskell": can_build,
        "claim_comment": "https://github.com/simonmichael/hledger/issues/1825#issuecomment-4901262602",
    },
    "next_real_candidates": [
        {
            "repo": r.get("repo"),
            "number": r.get("number"),
            "title": r.get("title"),
            "url": r.get("url"),
            "amount": r.get("amount"),
            "real_score": r.get("real_score"),
        }
        for r in real[:10]
    ],
}
(out / "decision.json").write_text(json.dumps(decision, indent=2) + "\n")

md = []
md.append("# hledger Gate + Cash Refilter v20")
md.append("")
md.append("## hledger")
md.append("")
md.append(f"- Verdict: `{decision['hledger']['verdict']}`")
md.append(f"- Can run hledger-ui now: `{can_run}`")
md.append(f"- Can build Haskell now: `{can_build}`")
md.append("")
md.append("## Next real candidates")
md.append("")
for i, r in enumerate(decision["next_real_candidates"], 1):
    md.append(f"{i}. `{r['real_score']}` ${r['amount']} - {r['repo']}#{r['number']} - {r['title']} - {r['url']}")
md.append("")
(out / "REPORT.md").write_text("\n".join(md) + "\n")
print((out / "REPORT.md").read_text())
PY
echo

echo "06 commit artifact"
cd "$ROOT"
git add "$OUT" hledger_gate_and_cash_refilter_v20.sh
git commit -m "Gate hledger and refilter cash candidates v20" || true
git push origin local-main || true
echo

echo "07 final"
git status --short
df -h /
echo
echo "Artifacts:"
echo "$OUT/REPORT.md"
echo "$OUT/decision.json"
echo "$OUT/hledger_gate.txt"
echo "$OUT/REAL_GOLD_LIST.md"
echo "$OUT/real_candidates.json"
