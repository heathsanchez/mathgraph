#!/usr/bin/env bash
set -u

ROOT="/Users/heath/Documents/mathgraph-lean-work"
RUN="money_signal_repair_and_gold_recon_v6"
OUT="$ROOT/artifacts/$RUN"
BACK="/tmp/${RUN}_backup_$(date -u +%Y%m%dT%H%M%SZ)"

mkdir -p "$BACK"
cd "$ROOT" || exit 1

echo "MathGraph Money Signal Repair + Gold Recon v6"
echo "Purpose: preserve compact signal, remove failed huge unpushed scout commits, then recon real judged money routes."
echo

echo "01 starting status"
date -u +"%Y-%m-%dT%H:%M:%SZ"
df -h /
git status --short
echo
echo "Local commits ahead of origin/local-main:"
git fetch origin local-main || true
git log --oneline origin/local-main..HEAD || true

echo
echo "02 backup compact summaries before history repair"
mkdir -p "$BACK/previous_signal"

for p in \
  "artifacts/money_opportunity_scout_v3_strict/REPORT.md" \
  "artifacts/money_opportunity_scout_v3_strict/STRICT_RECON_SUMMARY.md" \
  "artifacts/money_opportunity_scout_v4_prize_words/REPORT.md" \
  "artifacts/money_opportunity_scout_v4_prize_words/PRIZE_RECON_SUMMARY.md" \
  "artifacts/money_opportunity_scout_v4_prize_words/recon/cadallacricky1-maker__Shutterscore_5/REPORT.md" \
  "artifacts/money_opportunity_scout_v4_prize_words/recon/treitforge__qsoripper_424/REPORT.md" \
  "artifacts/money_opportunity_scout_v4_prize_words/recon/anonhostpi__Agent-World_24/REPORT.md" \
  "artifacts/money_opportunity_scout_v3_strict/recon/tenstorrent__tt-blacksmith_529/REPORT.md" \
  "artifacts/money_opportunity_scout_v3_strict/recon/ClankerNation__OpenAgents_21/REPORT.md" \
  "artifacts/money_opportunity_scout_v3_strict/recon/ClankerNation__OpenAgents_43/REPORT.md" \
  "artifacts/money_opportunity_scout_v3_strict/recon/ClankerNation__OpenAgents_59/REPORT.md"
do
  if [ -f "$p" ]; then
    safe="$(echo "$p" | tr '/ ' '__')"
    cp "$p" "$BACK/previous_signal/$safe"
    echo "backed up $p"
  fi
done

cat > "$BACK/previous_signal/README.md" <<'MD'
# Backed-up unpushed money scout signal

This folder was created before resetting failed large unpushed scout commits.

Reason:
- v3/v4 scout commits contained huge raw GitHub search JSON/recon artifacts.
- `git push` failed with HTTP 400.
- The useful signal is compact and should be recommitted without giant raw artifacts.

Interpretation:
- Clanker/OpenAgents: reject because issues request platform/system initialization text.
- SporkDAO/ETHDenver-2023: stale hackathon bounties, not live.
- Shutterscore: likely no real repo patch surface despite high "estimated value" text.
- Treitforge/QsoRipper #424: no cash, but real external Kaggle leaderboard benchmark route.
- Tenstorrent tt-blacksmith #529: real $2k but hardware gated.
MD

echo
echo "03 repair local branch by dropping failed huge unpushed commits"
echo "This resets only local unpushed commits back to origin/local-main; compact signal was backed up to:"
echo "$BACK"
git reset --hard origin/local-main

echo
echo "04 recreate compact artifact"
mkdir -p "$OUT/previous_signal"
cp -R "$BACK/previous_signal/." "$OUT/previous_signal/" 2>/dev/null || true

cat > "$OUT/SIGNAL_VERDICT.md" <<'MD'
# Money Signal Verdict v6

## What v4 taught us

The words `prize`, `payment`, `cash`, `competition`, `challenge`, `golf`, and `hackathon` produce many false positives.

### Reject / park

- `ClankerNation/OpenAgents`: reject. Multiple issues require pasting full platform/system initialization text. Do not engage.
- `SporkDAOOfficial/ETHDenver-2023`: stale 2023 hackathon bounty archive. Not a live route.
- `cadallacricky1-maker/Shutterscore#5`: likely a mirage. Issue text claims "$15,000+ estimated value", but recon showed almost no repo surface.
- `karmonlong/ai-competition-voting-platform#3`: plausible app task, but not a real external paid/prize route.
- `tenstorrent/tt-blacksmith#529`: real-ish $2k, but hardware gated. Park unless CPU-baseline-only milestone is accepted.
- `treitforge/qsoripper#424`: no cash, but a strong external-leaderboard benchmark route.
- `anonhostpi/Agent-World#24`: no cash, but strategically useful: a Kaggle discovery CLI could improve the money finder.

## Current best money hypothesis

Look below the noisy top ranks for small, explicit, testable bounties:

- Julia benchmark bounties: `qojulia/QuantumOptics.jl#407` and `QuantumSavory/QuantumSavory.jl#131`
- Small Python/pytest bounties: `jackjin1997/zeroeye#1`, `jackjin1997/TentOfTrials#3`
- Tooling benchmark/script bounties: `tailcallhq/tailcall#3551`
- Existing Tenstorrent route: `tenstorrent/tt-llk#1638`, parked until metric reply

Rule: no new PR unless local judge is real and risk is low.
MD

cat "$OUT/SIGNAL_VERDICT.md"

echo
echo "05 build targeted gold recon list"
cat > "$OUT/targets.json" <<'JSON'
[
  {
    "repo": "qojulia/QuantumOptics.jl",
    "num": 407,
    "reason": "$400 benchmark suite + CI runner, likely real judged route"
  },
  {
    "repo": "QuantumSavory/QuantumSavory.jl",
    "num": 131,
    "reason": "$200 benchmark route, likely real judged route"
  },
  {
    "repo": "jackjin1997/zeroeye",
    "num": 1,
    "reason": "$30 Python pytest edge-case tests, small but judgeable"
  },
  {
    "repo": "jackjin1997/TentOfTrials",
    "num": 3,
    "reason": "$30 Python diagnostic metadata tests, small but judgeable"
  },
  {
    "repo": "tailcallhq/tailcall",
    "num": 3551,
    "reason": "$50 analyze.sh JS rewrite / benchmark tooling, maybe judgeable"
  },
  {
    "repo": "treitforge/qsoripper",
    "num": 424,
    "reason": "Kaggle external benchmark route; no cash but high MathGraph fit"
  },
  {
    "repo": "anonhostpi/Agent-World",
    "num": 24,
    "reason": "Kaggle discovery CLI; no cash but can improve future money search"
  },
  {
    "repo": "tenstorrent/tt-blacksmith",
    "num": 529,
    "reason": "$2000 GraphSAGE workload; hardware gated, maybe ask milestone split"
  }
]
JSON

cat "$OUT/targets.json"

echo
echo "06 targeted recon"
python3 - "$ROOT" "$OUT" <<'PY'
from pathlib import Path
import json, os, re, subprocess, textwrap, shutil

root = Path(__import__("sys").argv[1])
out = Path(__import__("sys").argv[2])
targets = json.loads((out / "targets.json").read_text())

recon_root = out / "recon"
recon_root.mkdir(parents=True, exist_ok=True)

external_root = root / "external" / "money_gold_recon_v6"
external_root.mkdir(parents=True, exist_ok=True)

def run(cmd, cwd=None, timeout=90):
    try:
        p = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
        return {"rc": p.returncode, "out": p.stdout, "err": p.stderr}
    except subprocess.TimeoutExpired as e:
        return {"rc": 124, "out": e.stdout or "", "err": e.stderr or "TIMEOUT"}
    except Exception as e:
        return {"rc": 999, "out": "", "err": repr(e)}

def write(path, s):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(s if isinstance(s, str) else json.dumps(s, indent=2), errors="replace")

def safe_name(repo, num):
    return repo.replace("/", "__") + f"_{num}"

summaries = []

for t in targets:
    repo = t["repo"]
    num = int(t["num"])
    name = safe_name(repo, num)
    rd = recon_root / name
    rd.mkdir(parents=True, exist_ok=True)
    clone = external_root / name

    print("\n" + "=" * 100)
    print(f"RECON {repo} #{num}")
    print("=" * 100)

    issue_cmd = ["gh", "issue", "view", str(num), "-R", repo, "--json", "url,title,body,state,labels,comments,updatedAt,createdAt"]
    issue_res = run(issue_cmd, cwd=root)
    write(rd / "issue_raw.json", issue_res["out"] or "{}")
    write(rd / "issue.err", issue_res["err"])

    try:
        issue = json.loads(issue_res["out"])
    except Exception:
        issue = {"url": f"https://github.com/{repo}/issues/{num}", "title": "", "body": "", "state": "UNKNOWN", "labels": [], "comments": []}

    print(json.dumps({
        "url": issue.get("url"),
        "title": issue.get("title"),
        "state": issue.get("state"),
        "updatedAt": issue.get("updatedAt"),
        "labels": [x.get("name","") for x in issue.get("labels", [])],
        "comment_count": len(issue.get("comments") or []),
    }, indent=2))

    if clone.exists():
        res = run(["git", "fetch", "--depth", "1", "origin"], cwd=clone)
        write(rd / "git_fetch.log", res["out"] + res["err"])
        res = run(["git", "checkout", "FETCH_HEAD"], cwd=clone)
        write(rd / "git_checkout.log", res["out"] + res["err"])
    else:
        res = run(["git", "clone", "--depth", "1", "--filter=blob:none", f"https://github.com/{repo}.git", str(clone)], cwd=root, timeout=180)
        write(rd / "clone.log", res["out"] + res["err"])

    inv = run(["bash", "-lc", "find . -maxdepth 4 -type f | sed 's#^./##' | sort | head -300"], cwd=clone)
    write(rd / "inventory.txt", inv["out"] + inv["err"])

    grep = run(["bash", "-lc", r"""
{
  echo "===== money / judge / benchmark / test hits ====="
  grep -RInE "bounty|reward|\$[0-9]|USD|benchmark|pytest|julia|Pkg\.test|runtests|CI|github actions|acceptance|leaderboard|score|metric|test" \
    --exclude-dir=.git --exclude='*.min.js' --exclude='*.lock' . 2>/dev/null | head -250
  echo
  echo "===== package/test files ====="
  find . -maxdepth 5 \( -name 'Project.toml' -o -name 'Manifest.toml' -o -name 'runtests.jl' -o -name 'package.json' -o -name 'pyproject.toml' -o -name 'requirements.txt' -o -name 'pytest.ini' -o -name 'Cargo.toml' -o -name 'Makefile' -o -path './.github/workflows/*' \) -type f | sort | head -200
}
"""], cwd=clone)
    write(rd / "grep.txt", grep["out"] + grep["err"])

    cheap_lines = []
    cheap_lines.append(f"pwd={clone}")

    if (clone / "package.json").exists():
        p = run(["bash", "-lc", "python3 - <<'PY'\nimport json\np=json.load(open('package.json'))\nprint(json.dumps(p.get('scripts',{}), indent=2))\nPY"], cwd=clone)
        cheap_lines.append("\npackage scripts:\n" + p["out"] + p["err"])

    if (clone / "Project.toml").exists():
        cheap_lines.append("\nJulia Project.toml found.")
        if shutil.which("julia"):
            p = run(["julia", "--project=.", "-e", "using Pkg; Pkg.status()"], cwd=clone, timeout=120)
            cheap_lines.append("\njulia project status:\n" + p["out"] + p["err"])
        else:
            cheap_lines.append("\njulia not installed locally; cannot run Pkg.test without setup.")

    if (clone / "pyproject.toml").exists() or (clone / "requirements.txt").exists():
        cheap_lines.append("\nPython project files found.")
        p = run(["bash", "-lc", "find . -maxdepth 4 -type f \\( -name 'test_*.py' -o -name '*_test.py' -o -path './tests/*' \\) | head -80"], cwd=clone)
        cheap_lines.append("\npython tests:\n" + p["out"] + p["err"])

    p = run(["bash", "-lc", "find .github/workflows -type f -maxdepth 2 2>/dev/null | sort | xargs -r -n1 echo"], cwd=clone)
    cheap_lines.append("\nworkflows:\n" + p["out"] + p["err"])

    write(rd / "cheap_commands.txt", "\n".join(cheap_lines))

    text = "\n".join([
        repo,
        issue.get("title") or "",
        issue.get("body") or "",
        " ".join([x.get("name","") for x in issue.get("labels", [])]),
        inv["out"],
        grep["out"],
        "\n".join(cheap_lines),
    ]).lower()

    money = bool(re.search(r"\$[0-9]|usd|usdc|\bbounty\b|\breward\b|\[\$[0-9]", text))
    amount = 0.0
    for m in re.findall(r"\$[\s]*([0-9][0-9,]*(?:\.[0-9]+)?)", text):
        try:
            amount = max(amount, float(m.replace(",", "")))
        except Exception:
            pass

    local = any(s in text for s in [
        "runtests.jl", "pkg.test", "pytest", "npm test", "pnpm test", "cargo test",
        "make test", "github/workflows", ".github/workflows", "benchmark", "ci"
    ])
    benchmark = "benchmark" in text or "leaderboard" in text or "metric" in text
    prompt_risk = any(s in text for s in [
        "system prompt", "platform initialization", "paste the entire block", "seed phrase",
        "private key", "jailbreak"
    ])
    hardware_risk = any(s in text for s in ["wormhole", "n300", "tenstorrent hardware", "tt execution on hardware"])
    web3_risk = any(s in text for s in ["mainnet", "wallet", "staking", "yield", "solidity", "smart contract"]) and not repo.startswith("tenstorrent/")
    stale = any(s in text for s in ["ethdenver-2023", "2017", "2018"]) and "updatedat" not in text

    has_surface = any(s in text for s in [
        "project.toml", "package.json", "pyproject.toml", "requirements.txt", "cargo.toml",
        "src/", "tests/", "test/", "runtests.jl"
    ])

    if prompt_risk:
        verdict = "REJECT_PROMPT_EXFILTRATION"
    elif hardware_risk:
        verdict = "PARK_HARDWARE_REQUIRED"
    elif web3_risk:
        verdict = "PARK_WEB3_SECURITY_RISK"
    elif money and local and has_surface and amount >= 100:
        verdict = "PROMOTE_PAID_RECON"
    elif money and local and has_surface:
        verdict = "PROMOTE_SMALL_PAID_RECON"
    elif benchmark and local and has_surface:
        verdict = "PROMOTE_EXTERNAL_BENCHMARK_RECON"
    else:
        verdict = "PARK_NO_LOCAL_JUDGE_OR_NO_MONEY"

    decision = {
        "repo": repo,
        "num": num,
        "url": issue.get("url"),
        "title": issue.get("title"),
        "state": issue.get("state"),
        "updatedAt": issue.get("updatedAt"),
        "reason": t.get("reason"),
        "amount_estimate": amount,
        "money": money,
        "local_judge": local,
        "benchmark_or_metric": benchmark,
        "has_surface": has_surface,
        "prompt_risk": prompt_risk,
        "hardware_risk": hardware_risk,
        "web3_risk": web3_risk,
        "verdict": verdict,
    }
    write(rd / "decision.json", decision)

    report = []
    report.append("# Gold Recon Report")
    report.append("")
    report.append("## Verdict")
    report.append("")
    report.append(f"`{verdict}`")
    report.append("")
    report.append("## Decision")
    report.append("")
    report.append("```json")
    report.append(json.dumps(decision, indent=2))
    report.append("```")
    report.append("")
    report.append("## Issue body excerpt")
    report.append("")
    report.append((issue.get("body") or "")[:5000])
    report.append("")
    report.append("## Cheap commands")
    report.append("")
    report.append("```text")
    report.append("\n".join(cheap_lines)[:5000])
    report.append("```")
    report.append("")
    report.append("## Inventory excerpt")
    report.append("")
    report.append("```text")
    report.append((inv["out"] + inv["err"])[:5000])
    report.append("```")
    report.append("")
    report.append("## Grep excerpt")
    report.append("")
    report.append("```text")
    report.append((grep["out"] + grep["err"])[:8000])
    report.append("```")
    write(rd / "REPORT.md", "\n".join(report) + "\n")

    summaries.append({**decision, "artifact": str(rd / "REPORT.md")})

(out / "gold_recon_summary.json").write_text(json.dumps(summaries, indent=2))

rank = {
    "PROMOTE_PAID_RECON": 1,
    "PROMOTE_SMALL_PAID_RECON": 2,
    "PROMOTE_EXTERNAL_BENCHMARK_RECON": 3,
    "PARK_HARDWARE_REQUIRED": 4,
    "PARK_WEB3_SECURITY_RISK": 5,
    "PARK_NO_LOCAL_JUDGE_OR_NO_MONEY": 6,
    "REJECT_PROMPT_EXFILTRATION": 9,
}
summaries.sort(key=lambda x: (rank.get(x["verdict"], 99), -x["amount_estimate"], x["repo"]))

md = []
md.append("# Gold Recon Summary v6")
md.append("")
md.append("| rank | verdict | amount | issue | title | local | benchmark | risk | artifact |")
md.append("|---:|---|---:|---|---|---:|---:|---|---|")
for i, x in enumerate(summaries, 1):
    risks = []
    if x["prompt_risk"]: risks.append("prompt")
    if x["hardware_risk"]: risks.append("hardware")
    if x["web3_risk"]: risks.append("web3")
    md.append(
        f"| {i} | `{x['verdict']}` | {x['amount_estimate']:.0f} | [{x['repo']}#{x['num']}]({x['url']}) | {str(x['title'])[:80]} | {x['local_judge']} | {x['benchmark_or_metric']} | {','.join(risks)} | `{x['artifact']}` |"
    )

md.append("")
md.append("## Next action")
md.append("")
promoted = [x for x in summaries if x["verdict"] in {"PROMOTE_PAID_RECON", "PROMOTE_SMALL_PAID_RECON", "PROMOTE_EXTERNAL_BENCHMARK_RECON"}]
if promoted:
    x = promoted[0]
    md.append(f"Work next: [{x['repo']}#{x['num']}]({x['url']}) — `{x['verdict']}`.")
    md.append("")
    md.append(f"Read: `{x['artifact']}`")
else:
    md.append("No safe paid/local-judge target promoted. Return to Tenstorrent metric watch and current PR queue.")

(out / "GOLD_RECON_SUMMARY.md").write_text("\n".join(md) + "\n")
print((out / "GOLD_RECON_SUMMARY.md").read_text())
PY

echo
echo "07 write final route table"
cat > "$OUT/ROUTE_TABLE.md" <<'MD'
# Route Table v6

## Strong rules

- Do not chase issues just because they mention prize/cash/challenge.
- Do not touch prompt-exfiltration issues.
- Do not chase stale hackathons.
- Do not commit giant raw search JSON.
- Do not open another PR unless there is a local judge or explicit external judge.

## Current likely money stack

1. Tenstorrent `tt-llk#1638`: best upside, waiting for metric.
2. Julia benchmark bounties: best small paid route if local Julia judge is available.
3. Small pytest bounties: low money but fast acceptance practice.
4. External benchmark routes: no cash but useful for MathGraph proof-of-work.
5. Paid verification sprint offer: monetize accepted PRs once review/merge signal lands.
MD

echo
echo "08 commit compact repair + gold recon only"
git add "$OUT" money_signal_repair_and_gold_recon_v6.sh
git commit -m "Repair money scout signal and run gold recon v6" || true

echo
echo "09 push"
git push origin local-main || true

echo
echo "10 final"
git status --short
df -h /
echo
echo "Artifacts:"
echo "$OUT/SIGNAL_VERDICT.md"
echo "$OUT/GOLD_RECON_SUMMARY.md"
echo "$OUT/ROUTE_TABLE.md"
echo "$OUT/recon"
