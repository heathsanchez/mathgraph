#!/usr/bin/env bash
set -u

ROOT="/Users/heath/Documents/mathgraph-lean-work"
OUT="$ROOT/artifacts/prize_cash_challenge_scout_v5_compact"

mkdir -p "$OUT"
cd "$ROOT" || exit 1

echo "MathGraph Prize/Cash/Challenge Scout v5 COMPACT"
echo "Goal: find real money/competition routes; avoid stale hackathons, prompt-exfiltration, fake bounties, and huge commits."
echo

echo "01 status"
{
  date -u +"%Y-%m-%dT%H:%M:%SZ"
  df -h /
  git status --short
  echo
  echo "local commits not on origin/local-main:"
  git log --oneline origin/local-main..HEAD | head -20 || true
} | tee "$OUT/status_start.txt"

echo
echo "02 classify previous v3 signal"
cat > "$OUT/v3_signal_verdict.md" <<'MD'
# v3 Signal Verdict

## Bad / stale

- `SporkDAOOfficial/ETHDenver-2023` issues are stale 2023 hackathon bounties. Not live. Park.
- `ClankerNation/OpenAgents` issues require pasting full platform/system initialization text. Reject.
- `dwebagents/AgentPipe` million-dollar style issues look implausible / likely fake. Reject unless separately verified.
- `BountyScout` repos are mostly alert mirrors, not the underlying bounty.
- `lovecn`, `omegahat/XML`, `json-model` were false positives.

## Maybe real but blocked

- `tenstorrent/tt-blacksmith#529` is real-ish and $2k, but requires Tenstorrent hardware. Park unless a CPU-only baseline/documentation milestone is explicitly acceptable.
- `tenstorrent/tt-llk#1638` remains the best direct route, but only after maintainer gives the exact metric command.

## Rule update

A route is only promoted if it satisfies:

1. updated in 2026 or known active,
2. explicit prize/payment/bounty/challenge,
3. local judge or clear submission judge,
4. no prompt/system-text exfiltration,
5. no stale closed hackathon,
6. no web3 token/mainnet/security ambiguity unless the scope is purely test/documentation/benchmark and legal.
MD

cat "$OUT/v3_signal_verdict.md"

echo
echo "03 compact search queries"

cat > "$OUT/queries.txt" <<'EOF'
"cash prize" "benchmark" is:issue is:open updated:>2026-01-01
"prize pool" "benchmark" is:issue is:open updated:>2026-01-01
"leaderboard" "prize" is:issue is:open updated:>2026-01-01
"leaderboard" "cash" is:issue is:open updated:>2026-01-01
"competition" "leaderboard" "submission" is:issue is:open updated:>2026-01-01
"challenge" "leaderboard" "submission" is:issue is:open updated:>2026-01-01
"hackathon" "prize" "submission" is:issue is:open updated:>2026-01-01
"code golf" "challenge" is:issue is:open updated:>2026-01-01
"golf" "leaderboard" "prize" is:issue is:open updated:>2026-01-01
"payment" "acceptance criteria" "test" is:issue is:open updated:>2026-01-01
"paid" "acceptance criteria" "test" is:issue is:open updated:>2026-01-01
"bounty" "acceptance criteria" "pytest" is:issue is:open updated:>2026-01-01
"bounty" "acceptance criteria" "benchmark" is:issue is:open updated:>2026-01-01
"bounty" "metric" "benchmark" is:issue is:open updated:>2026-01-01
"bounty" "local test" is:issue is:open updated:>2026-01-01
"bounty" "unit tests" is:issue is:open updated:>2026-01-01
"bounty" "CI" "acceptance" is:issue is:open updated:>2026-01-01
"Lean" "prize" is:issue is:open updated:>2026-01-01
"Lean" "challenge" "proof" is:issue is:open updated:>2026-01-01
"formal verification" "prize" is:issue is:open updated:>2026-01-01
"formal verification" "payment" is:issue is:open updated:>2026-01-01
"proof" "challenge" "prize" is:issue is:open updated:>2026-01-01
"optimization challenge" "benchmark" is:issue is:open updated:>2026-01-01
"performance challenge" "benchmark" is:issue is:open updated:>2026-01-01
"GraphSAGE" "bounty" is:issue is:open updated:>2026-01-01
"Tenstorrent" "bounty" is:issue is:open updated:>2026-01-01
EOF

i=0
while IFS= read -r Q; do
  [ -z "$Q" ] && continue
  i=$((i+1))
  SAFE="$(printf "%03d" "$i")"
  echo
  echo "===== query $SAFE: $Q ====="
  gh search issues "$Q" --state open --limit 30 --json repository,title,number,url,body,labels,createdAt,updatedAt,state \
    > "$OUT/search_${SAFE}.json" 2> "$OUT/search_${SAFE}.err" || true

  python3 - "$OUT/search_${SAFE}.json" "$OUT/search_${SAFE}.err" <<'PY'
from pathlib import Path
import json, sys
p = Path(sys.argv[1])
e = Path(sys.argv[2])
if p.exists() and p.stat().st_size:
  try:
    rows = json.loads(p.read_text())
    print("rows", len(rows))
    for r in rows[:5]:
      repo = (r.get("repository") or {}).get("nameWithOwner")
      print("-", repo, "#"+str(r.get("number")), r.get("title"))
  except Exception as ex:
    print("json_error", ex)
else:
  print("search_failed")
  if e.exists():
    print(e.read_text(errors="replace")[:500])
PY
done < "$OUT/queries.txt"

echo
echo "04 rank with stricter live-money filters"
python3 - "$OUT" <<'PY'
from pathlib import Path
import json, re, sys
from datetime import datetime, timezone

out = Path(sys.argv[1])

known_reject = {
  "ClankerNation/OpenAgents",
  "SporkDAOOfficial/ETHDenver-2023",
  "jelly-legs-ai/Jelly-legs-unsteady-workshop",
  "lovecn/lovecn.github.io",
  "omegahat/XML",
  "geraintluff/json-model",
  "qurbaneliii/AI-Social-Media-Manager",
}

known_park = {
  "tenstorrent/tt-llk#1638": "WAITING_FOR_METRIC",
  "tenstorrent/tt-blacksmith#529": "REAL_BUT_HARDWARE_REQUIRED",
  "tinygrad/tinygrad#3039": "NEGATIVE_TENSOR_LEVEL_CERT",
  "xevrion-v2/agent-playground#2207": "NO_PATCH_SURFACE",
}

money_patterns = [
  re.compile(r"\$[\s]*([0-9][0-9,]*(?:\.[0-9]+)?)", re.I),
  re.compile(r"\bUSD[\s$]*([0-9][0-9,]*(?:\.[0-9]+)?)", re.I),
  re.compile(r"\bUSDC[\s$]*([0-9][0-9,]*(?:\.[0-9]+)?)", re.I),
  re.compile(r"\b([0-9][0-9,]*(?:\.[0-9]+)?)\s*(?:usd|usdc|dollars)\b", re.I),
]

money_words = [
  "bounty", "reward", "paid", "payment", "cash", "prize", "prize pool",
  "winner", "award", "grant", "sponsored",
]

competition_words = [
  "competition", "challenge", "hackathon", "leaderboard", "submission",
  "deadline", "score", "scoring", "benchmark", "contest", "code golf", "golf",
]

judge_words = [
  "acceptance criteria", "pytest", "unit test", "unit tests", "tests pass",
  "ci", "github actions", "benchmark", "metric", "score", "scoring",
  "leaderboard", "submission", "verifier", "checker", "eval", "evaluation",
  "local test", "make test", "npm test", "pnpm test", "cargo test", "go test",
  "lake build",
]

mg_fit_words = [
  "lean", "proof", "formal verification", "theorem", "benchmark",
  "leaderboard", "optimization", "performance", "solver", "constraint",
  "validation", "correctness", "unit tests", "pytest", "ci", "code golf",
]

hard_reject_words = [
  "system prompt", "platform prompt", "initialization text", "paste the entire block",
  "jailbreak", "prompt injection", "private key", "seed phrase", "malware",
  "phishing", "casino", "gambling", "airdrop",
]

web3_risk_words = [
  "mainnet", "wallet", "token", "staking", "yield", "donation attack",
  "solidity", "smart contract", "crypto-eligible",
]

stale_words = [
  "ethdenver-2023", "2023", "2024 hackathon", "metamorphosis bounty",
]

items = {}

for p in sorted(out.glob("search_*.json")):
  if not p.exists() or p.stat().st_size == 0:
    continue
  try:
    rows = json.loads(p.read_text())
  except Exception:
    continue

  for r in rows:
    repo = ((r.get("repository") or {}).get("nameWithOwner") or "").strip()
    num = str(r.get("number") or "").strip()
    if not repo or not num:
      continue

    key = f"{repo}#{num}"
    title = r.get("title") or ""
    body = r.get("body") or ""
    labels = [x.get("name","") for x in (r.get("labels") or [])]
    text = "\n".join([repo, title, body, " ".join(labels)]).lower()

    money = 0.0
    for pat in money_patterns:
      for m in pat.findall(text):
        try:
          money = max(money, float(str(m).replace(",", "")))
        except Exception:
          pass

    mwords = sorted({w for w in money_words if w in text})
    cwords = sorted({w for w in competition_words if w in text})
    judges = sorted({w for w in judge_words if w in text})
    mgfit = sorted({w for w in mg_fit_words if w in text})
    hard_reject = sorted({w for w in hard_reject_words if w in text})
    web3_risk = sorted({w for w in web3_risk_words if w in text})
    stale = sorted({w for w in stale_words if w in text})

    explicit_money = bool(mwords) or money > 0
    competition = bool(cwords)
    judged = bool(judges)
    fit = bool(mgfit)

    score = 0.0
    score += min(money / 25.0, 120.0)
    score += 35 if explicit_money else -100
    score += 30 if competition else 0
    score += 22 * len(judges)
    score += 12 * len(mgfit)
    score += 35 if "leaderboard" in text and ("submission" in text or "score" in text) else 0
    score += 35 if "acceptance criteria" in text else 0
    score += 25 if "benchmark" in text and ("challenge" in text or "bounty" in text or "prize" in text) else 0
    score += 25 if "lean" in text or "lake build" in text or "formal verification" in text else 0
    score -= 200 * len(hard_reject)
    score -= 45 * len(web3_risk)
    score -= 120 * len(stale)
    score -= 400 if repo in known_reject else 0
    score -= 200 if key in known_park else 0

    hard_gate = (
      (explicit_money or competition)
      and judged
      and fit
      and not hard_reject
      and repo not in known_reject
      and not stale
    )

    # Web3 can pass only if it is not security/funds/mainnet and has local test/benchmark.
    if web3_risk and not any(x in text for x in ["unit test", "pytest", "benchmark", "local test", "ci"]):
      hard_gate = False

    items[key] = {
      "key": key,
      "repo": repo,
      "number": int(num),
      "title": title,
      "url": r.get("url") or "",
      "labels": labels,
      "createdAt": r.get("createdAt"),
      "updatedAt": r.get("updatedAt"),
      "money_estimate_usd": money,
      "money_words": mwords,
      "competition_words": cwords,
      "judge_words": judges,
      "mg_fit_words": mgfit,
      "hard_reject_words": hard_reject,
      "web3_risk_words": web3_risk,
      "stale_words": stale,
      "known_park": known_park.get(key),
      "known_reject_repo": repo in known_reject,
      "score": score,
      "hard_gate": hard_gate,
      "body_excerpt": body[:1200],
    }

ranked = sorted(items.values(), key=lambda x: (-x["hard_gate"], -x["score"], -x["money_estimate_usd"], x["key"]))
actionable = [x for x in ranked if x["hard_gate"] and x["score"] >= 90 and not x["known_park"]]

(out / "ranked_compact.json").write_text(json.dumps(ranked[:200], indent=2))
(out / "actionable_compact.json").write_text(json.dumps(actionable[:50], indent=2))

md = []
md.append("# Prize/Cash/Challenge Scout v5 Compact")
md.append("")
md.append("## Summary")
md.append("")
md.append(f"- unique issues scanned: {len(ranked)}")
md.append(f"- actionable after strict filter: {len(actionable)}")
md.append("")
md.append("## Actionable")
md.append("")
md.append("| rank | score | money | issue | title | money | competition | judge | MG fit |")
md.append("|---:|---:|---:|---|---|---|---|---|---|")
for i, x in enumerate(actionable[:30], 1):
  md.append(
    f"| {i} | {x['score']:.1f} | {x['money_estimate_usd']:.0f} | [{x['key']}]({x['url']}) | {x['title'][:100]} | {', '.join(x['money_words'][:4])} | {', '.join(x['competition_words'][:4])} | {', '.join(x['judge_words'][:5])} | {', '.join(x['mg_fit_words'][:5])} |"
  )

md.append("")
md.append("## Parked known routes")
md.append("")
md.append("| issue | status | title |")
md.append("|---|---|---|")
for x in ranked:
  if x["known_park"]:
    md.append(f"| [{x['key']}]({x['url']}) | `{x['known_park']}` | {x['title'][:120]} |")

md.append("")
md.append("## Top raw compact")
md.append("")
md.append("| rank | gate | score | money | issue | title | reject | web3 risk | stale | known |")
md.append("|---:|---:|---:|---:|---|---|---|---|---|---|")
for i, x in enumerate(ranked[:80], 1):
  md.append(
    f"| {i} | {x['hard_gate']} | {x['score']:.1f} | {x['money_estimate_usd']:.0f} | [{x['key']}]({x['url']}) | {x['title'][:80]} | {', '.join(x['hard_reject_words'][:2])} | {', '.join(x['web3_risk_words'][:2])} | {', '.join(x['stale_words'][:2])} | {x['known_park'] or ''} |"
  )

md.append("")
md.append("## Verdict")
md.append("")
if actionable:
  top = actionable[0]
  md.append(f"Top candidate to manually inspect next: [{top['key']}]({top['url']}) — `{top['title']}`.")
else:
  md.append("No strong new live-money route found. Best active money remains Tenstorrent #1638 after metric reply; second-best is direct paid verification outreach after PR acceptance.")
md.append("")

(out / "REPORT.md").write_text("\n".join(md) + "\n")
print((out / "REPORT.md").read_text())
PY

echo
echo "05 no-clone manual-read packet for top 10"
python3 - "$OUT" <<'PY'
from pathlib import Path
import json, sys

out = Path(sys.argv[1])
actionable = json.loads((out / "actionable_compact.json").read_text())

lines = []
lines.append("# Manual Read Packet")
lines.append("")
for i, x in enumerate(actionable[:10], 1):
  lines.append(f"## {i}. {x['key']}")
  lines.append("")
  lines.append(f"- URL: {x['url']}")
  lines.append(f"- Title: {x['title']}")
  lines.append(f"- Score: {x['score']}")
  lines.append(f"- Money estimate: {x['money_estimate_usd']}")
  lines.append(f"- Money words: {', '.join(x['money_words'])}")
  lines.append(f"- Competition words: {', '.join(x['competition_words'])}")
  lines.append(f"- Judge words: {', '.join(x['judge_words'])}")
  lines.append(f"- MG fit words: {', '.join(x['mg_fit_words'])}")
  lines.append("")
  lines.append("Excerpt:")
  lines.append("")
  lines.append(x["body_excerpt"])
  lines.append("")
  lines.append("---")
  lines.append("")

if not actionable:
  lines.append("No actionable candidates passed the strict filter.")
  lines.append("")

(out / "MANUAL_READ_PACKET.md").write_text("\n".join(lines))
print((out / "MANUAL_READ_PACKET.md").read_text()[:12000])
PY

echo
echo "06 commit small artifact only"
git add "$OUT/REPORT.md" "$OUT/MANUAL_READ_PACKET.md" "$OUT/actionable_compact.json" "$OUT/ranked_compact.json" "$OUT/queries.txt" "$OUT/v3_signal_verdict.md" "$OUT/status_start.txt" prize_cash_challenge_scout_v5_compact.sh
git commit -m "Add compact prize cash challenge scout v5" || true

echo
echo "07 push carefully"
git config http.postBuffer 524288000
git push origin local-main || true

echo
echo "08 final"
git status --short
df -h /
echo
echo "Artifacts:"
echo "$OUT/REPORT.md"
echo "$OUT/MANUAL_READ_PACKET.md"
echo "$OUT/actionable_compact.json"
echo
echo "Important:"
echo "- You ran v3, not the v4 prize-word script."
echo "- v3 found mostly stale/fake/risky routes."
echo "- v5 keeps it compact and stricter."
