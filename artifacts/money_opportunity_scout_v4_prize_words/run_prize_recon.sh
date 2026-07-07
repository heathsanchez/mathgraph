#!/usr/bin/env bash
set -u

ROOT="/Users/heath/Documents/mathgraph-lean-work"
BASE_OUT="$ROOT/artifacts/money_opportunity_scout_v4_prize_words/recon"
mkdir -p "$BASE_OUT"
cd "$ROOT" || exit 1

echo "MathGraph prize-word opportunity recon"
echo

echo
echo "===================================================================================================="
echo "RECON karmonlong/ai-competition-voting-platform #3"
echo "===================================================================================================="

REPO_NAME="karmonlong/ai-competition-voting-platform"
ISSUE_NUM="3"
SAFE="karmonlong__ai-competition-voting-platform_3"
LOCAL_REPO="$ROOT/external/money_opportunity_scout_v4_prize_words/$SAFE"
OUT="$BASE_OUT/$SAFE"

mkdir -p "$OUT"
mkdir -p "$(dirname "$LOCAL_REPO")"

echo "01 issue"
gh issue view "$ISSUE_NUM" --repo "$REPO_NAME" --json number,title,state,url,labels,body,comments,updatedAt,createdAt \
  > "$OUT/issue.json" 2> "$OUT/issue.err" || true

python3 - "$OUT" <<'PY2'
from pathlib import Path
import json, sys
out = Path(sys.argv[1])
p = out / "issue.json"
if p.exists() and p.stat().st_size:
  j = json.loads(p.read_text())
  summary = {
    "url": j.get("url"),
    "title": j.get("title"),
    "state": j.get("state"),
    "labels": [x.get("name") for x in j.get("labels", [])],
    "comment_count": len(j.get("comments", [])),
    "updatedAt": j.get("updatedAt"),
  }
  (out / "issue_summary.json").write_text(json.dumps(summary, indent=2))
  (out / "issue_body.md").write_text(j.get("body") or "")
  (out / "issue_comments.md").write_text("\n---\n".join(
    "## " + str((c.get("author") or {}).get("login")) + " — " + str(c.get("createdAt")) + "\n\n" + str(c.get("body") or "")
    for c in j.get("comments", [])
  ))
  print(json.dumps(summary, indent=2))
else:
  print("issue view failed")
  print((out / "issue.err").read_text(errors="replace") if (out / "issue.err").exists() else "")
PY2

echo
echo "02 clone/update"
if [ ! -d "$LOCAL_REPO/.git" ]; then
  gh repo clone "$REPO_NAME" "$LOCAL_REPO" -- --filter=blob:none \
    > "$OUT/clone.log" 2>&1 || true
else
  echo "[exists] $LOCAL_REPO" | tee "$OUT/clone.log"
fi

if [ ! -d "$LOCAL_REPO/.git" ]; then
  echo "clone failed"
  cat "$OUT/clone.log"
  continue
fi

cd "$LOCAL_REPO" || continue
git fetch origin --prune > "$OUT/git_fetch.log" 2>&1 || true
DEFAULT_BRANCH="$(git remote show origin 2>/dev/null | awk '/HEAD branch/ {print $NF}' | head -1)"
if [ -z "$DEFAULT_BRANCH" ]; then DEFAULT_BRANCH="main"; fi
git checkout "$DEFAULT_BRANCH" > "$OUT/git_checkout.log" 2>&1 || true
git pull --ff-only origin "$DEFAULT_BRANCH" > "$OUT/git_pull.log" 2>&1 || true
git rev-parse HEAD | tee "$OUT/head.txt"

echo
echo "03 inventory"
{
  echo "top files"
  find . -maxdepth 4 -type f | sed 's#^./##' | sort | head -1200
  echo
  echo "build/test/competition files"
  find . -maxdepth 6 -type f \( -name 'README*' -o -name 'package.json' -o -name 'pyproject.toml' -o -name 'requirements.txt' -o -name 'Cargo.toml' -o -name 'go.mod' -o -name 'Makefile' -o -name 'Dockerfile' -o -name 'lakefile.toml' -o -name 'lakefile.lean' -o -name 'lean-toolchain' -o -name '*.ipynb' -o -name '*.md' \) | sort | head -1000
  echo
  echo "workflows"
  find .github/workflows -type f 2>/dev/null | sort
} > "$OUT/inventory.txt" 2>&1

echo
echo "04 focused grep"
{
  echo "===== issue body ====="
  cat "$OUT/issue_body.md" 2>/dev/null || true

  echo
  echo "===== money/competition/judge hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=.lake --exclude-dir=node_modules --exclude-dir=target --exclude-dir=dist --exclude-dir=build \
    "prize|payment|cash|bounty|reward|competition|challenge|hackathon|leaderboard|submission|score|scoring|benchmark|metric|eval|evaluation|winner|deadline|golf|test|pytest|ci|workflow|acceptance|verifier|checker" . 2>/dev/null | head -3000

  echo
  echo "===== patch/search surface hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=.lake --exclude-dir=node_modules --exclude-dir=target --exclude-dir=dist --exclude-dir=build \
    "TODO|FIXME|bug|error|failing|regression|optimize|performance|proof|theorem|solver|search|constraint|correctness|validation|static|compile|type|Cannot find module" . 2>/dev/null | head -3000
} > "$OUT/grep.txt" 2>&1

echo
echo "05 cheap commands"
{
  echo "pwd=$(pwd)"
  echo
  if [ -f README.md ]; then
    echo "README head:"
    sed -n '1,220p' README.md
  fi
  if [ -f package.json ]; then
    echo
    echo "package scripts:"
    node -e 'const p=require("./package.json"); console.log(JSON.stringify(p.scripts||{},null,2))' 2>/dev/null || cat package.json | head -160
  fi
  if [ -f pyproject.toml ]; then
    echo
    echo "pyproject head:"
    sed -n '1,220p' pyproject.toml
  fi
  if [ -f Makefile ]; then
    echo
    echo "Makefile targets:"
    grep -nE "^[A-Za-z0-9_.-]+:" Makefile | head -80
  fi
  if [ -f lean-toolchain ]; then
    echo
    echo "lean-toolchain:"
    cat lean-toolchain
  fi
} > "$OUT/cheap_commands.txt" 2>&1

echo
echo "06 classify"
python3 - "$OUT" <<'PY2'
from pathlib import Path
import json, sys

out = Path(sys.argv[1])
issue = {}
try:
  issue = json.loads((out / "issue_summary.json").read_text())
except Exception:
  pass

body = (out / "issue_body.md").read_text(errors="replace") if (out / "issue_body.md").exists() else ""
comments = (out / "issue_comments.md").read_text(errors="replace") if (out / "issue_comments.md").exists() else ""
inv = (out / "inventory.txt").read_text(errors="replace") if (out / "inventory.txt").exists() else ""
grep = (out / "grep.txt").read_text(errors="replace") if (out / "grep.txt").exists() else ""
cheap = (out / "cheap_commands.txt").read_text(errors="replace") if (out / "cheap_commands.txt").exists() else ""
text = "\n".join([body, comments, inv, grep, cheap]).lower()

money = any(x in text for x in ["prize", "payment", "cash", "bounty", "reward", "paid", "$", "usd"])
competition = any(x in text for x in ["competition", "challenge", "hackathon", "leaderboard", "submission", "winner", "deadline", "code golf", "golf"])
judge = any(x in text for x in ["leaderboard", "submission", "score", "scoring", "benchmark", "metric", "eval", "evaluation", "test", "pytest", "ci", "workflow", "verifier", "checker", "acceptance"])
local = any(x in text for x in ["pytest", "npm test", "pnpm test", "yarn test", "cargo test", "go test", "make", "lake build", "benchmark", "python", "node"])
mgfit = any(x in text for x in ["lean", "proof", "theorem", "formal verification", "solver", "search", "constraint", "benchmark", "leaderboard", "optimization", "performance", "code golf", "correctness", "validation"])
risk = any(x in text for x in ["system prompt", "platform prompt", "jailbreak", "private key", "seed phrase", "wallet", "mainnet", "malware", "phishing", "casino", "gambling", "airdrop", "token"])

if risk:
  verdict = "PARK_RISK"
elif money and competition and judge and mgfit:
  verdict = "PROMOTE_COMPETITION_MONEY"
elif money and judge and local and mgfit:
  verdict = "PROMOTE_PAID_REPAIR"
elif competition and judge and mgfit:
  verdict = "PROMOTE_COMPETITION_REPUTATION_OR_PRIZE_UNKNOWN"
elif money and not judge:
  verdict = "ASK_FOR_JUDGE"
else:
  verdict = "PARK_WEAK"

decision = {
  "verdict": verdict,
  "issue": issue,
  "money": money,
  "competition": competition,
  "judge": judge,
  "local": local,
  "mgfit": mgfit,
  "risk": risk,
}

(out / "decision.json").write_text(json.dumps(decision, indent=2))

lines = []
lines.append("# Prize Recon Report")
lines.append("")
lines.append("## Verdict")
lines.append("")
lines.append("`" + verdict + "`")
lines.append("")
lines.append("## Decision")
lines.append("")
lines.append("JSON:")
lines.append(json.dumps(decision, indent=2))
lines.append("")
lines.append("## Cheap commands")
lines.append("")
lines.append(cheap[:10000])
lines.append("")
lines.append("## Issue body")
lines.append("")
lines.append(body[:12000])
lines.append("")
lines.append("## Comments")
lines.append("")
lines.append(comments[:8000])
lines.append("")
lines.append("## Inventory excerpt")
lines.append("")
lines.append(inv[:12000])
lines.append("")
lines.append("## Grep excerpt")
lines.append("")
lines.append(grep[:24000])
lines.append("")
(out / "REPORT.md").write_text("\n".join(lines) + "\n")
print((out / "REPORT.md").read_text()[:18000])
PY2

cd "$ROOT" || exit 1

echo
echo "===================================================================================================="
echo "RECON cadallacricky1-maker/Shutterscore #5"
echo "===================================================================================================="

REPO_NAME="cadallacricky1-maker/Shutterscore"
ISSUE_NUM="5"
SAFE="cadallacricky1-maker__Shutterscore_5"
LOCAL_REPO="$ROOT/external/money_opportunity_scout_v4_prize_words/$SAFE"
OUT="$BASE_OUT/$SAFE"

mkdir -p "$OUT"
mkdir -p "$(dirname "$LOCAL_REPO")"

echo "01 issue"
gh issue view "$ISSUE_NUM" --repo "$REPO_NAME" --json number,title,state,url,labels,body,comments,updatedAt,createdAt \
  > "$OUT/issue.json" 2> "$OUT/issue.err" || true

python3 - "$OUT" <<'PY2'
from pathlib import Path
import json, sys
out = Path(sys.argv[1])
p = out / "issue.json"
if p.exists() and p.stat().st_size:
  j = json.loads(p.read_text())
  summary = {
    "url": j.get("url"),
    "title": j.get("title"),
    "state": j.get("state"),
    "labels": [x.get("name") for x in j.get("labels", [])],
    "comment_count": len(j.get("comments", [])),
    "updatedAt": j.get("updatedAt"),
  }
  (out / "issue_summary.json").write_text(json.dumps(summary, indent=2))
  (out / "issue_body.md").write_text(j.get("body") or "")
  (out / "issue_comments.md").write_text("\n---\n".join(
    "## " + str((c.get("author") or {}).get("login")) + " — " + str(c.get("createdAt")) + "\n\n" + str(c.get("body") or "")
    for c in j.get("comments", [])
  ))
  print(json.dumps(summary, indent=2))
else:
  print("issue view failed")
  print((out / "issue.err").read_text(errors="replace") if (out / "issue.err").exists() else "")
PY2

echo
echo "02 clone/update"
if [ ! -d "$LOCAL_REPO/.git" ]; then
  gh repo clone "$REPO_NAME" "$LOCAL_REPO" -- --filter=blob:none \
    > "$OUT/clone.log" 2>&1 || true
else
  echo "[exists] $LOCAL_REPO" | tee "$OUT/clone.log"
fi

if [ ! -d "$LOCAL_REPO/.git" ]; then
  echo "clone failed"
  cat "$OUT/clone.log"
  continue
fi

cd "$LOCAL_REPO" || continue
git fetch origin --prune > "$OUT/git_fetch.log" 2>&1 || true
DEFAULT_BRANCH="$(git remote show origin 2>/dev/null | awk '/HEAD branch/ {print $NF}' | head -1)"
if [ -z "$DEFAULT_BRANCH" ]; then DEFAULT_BRANCH="main"; fi
git checkout "$DEFAULT_BRANCH" > "$OUT/git_checkout.log" 2>&1 || true
git pull --ff-only origin "$DEFAULT_BRANCH" > "$OUT/git_pull.log" 2>&1 || true
git rev-parse HEAD | tee "$OUT/head.txt"

echo
echo "03 inventory"
{
  echo "top files"
  find . -maxdepth 4 -type f | sed 's#^./##' | sort | head -1200
  echo
  echo "build/test/competition files"
  find . -maxdepth 6 -type f \( -name 'README*' -o -name 'package.json' -o -name 'pyproject.toml' -o -name 'requirements.txt' -o -name 'Cargo.toml' -o -name 'go.mod' -o -name 'Makefile' -o -name 'Dockerfile' -o -name 'lakefile.toml' -o -name 'lakefile.lean' -o -name 'lean-toolchain' -o -name '*.ipynb' -o -name '*.md' \) | sort | head -1000
  echo
  echo "workflows"
  find .github/workflows -type f 2>/dev/null | sort
} > "$OUT/inventory.txt" 2>&1

echo
echo "04 focused grep"
{
  echo "===== issue body ====="
  cat "$OUT/issue_body.md" 2>/dev/null || true

  echo
  echo "===== money/competition/judge hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=.lake --exclude-dir=node_modules --exclude-dir=target --exclude-dir=dist --exclude-dir=build \
    "prize|payment|cash|bounty|reward|competition|challenge|hackathon|leaderboard|submission|score|scoring|benchmark|metric|eval|evaluation|winner|deadline|golf|test|pytest|ci|workflow|acceptance|verifier|checker" . 2>/dev/null | head -3000

  echo
  echo "===== patch/search surface hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=.lake --exclude-dir=node_modules --exclude-dir=target --exclude-dir=dist --exclude-dir=build \
    "TODO|FIXME|bug|error|failing|regression|optimize|performance|proof|theorem|solver|search|constraint|correctness|validation|static|compile|type|Cannot find module" . 2>/dev/null | head -3000
} > "$OUT/grep.txt" 2>&1

echo
echo "05 cheap commands"
{
  echo "pwd=$(pwd)"
  echo
  if [ -f README.md ]; then
    echo "README head:"
    sed -n '1,220p' README.md
  fi
  if [ -f package.json ]; then
    echo
    echo "package scripts:"
    node -e 'const p=require("./package.json"); console.log(JSON.stringify(p.scripts||{},null,2))' 2>/dev/null || cat package.json | head -160
  fi
  if [ -f pyproject.toml ]; then
    echo
    echo "pyproject head:"
    sed -n '1,220p' pyproject.toml
  fi
  if [ -f Makefile ]; then
    echo
    echo "Makefile targets:"
    grep -nE "^[A-Za-z0-9_.-]+:" Makefile | head -80
  fi
  if [ -f lean-toolchain ]; then
    echo
    echo "lean-toolchain:"
    cat lean-toolchain
  fi
} > "$OUT/cheap_commands.txt" 2>&1

echo
echo "06 classify"
python3 - "$OUT" <<'PY2'
from pathlib import Path
import json, sys

out = Path(sys.argv[1])
issue = {}
try:
  issue = json.loads((out / "issue_summary.json").read_text())
except Exception:
  pass

body = (out / "issue_body.md").read_text(errors="replace") if (out / "issue_body.md").exists() else ""
comments = (out / "issue_comments.md").read_text(errors="replace") if (out / "issue_comments.md").exists() else ""
inv = (out / "inventory.txt").read_text(errors="replace") if (out / "inventory.txt").exists() else ""
grep = (out / "grep.txt").read_text(errors="replace") if (out / "grep.txt").exists() else ""
cheap = (out / "cheap_commands.txt").read_text(errors="replace") if (out / "cheap_commands.txt").exists() else ""
text = "\n".join([body, comments, inv, grep, cheap]).lower()

money = any(x in text for x in ["prize", "payment", "cash", "bounty", "reward", "paid", "$", "usd"])
competition = any(x in text for x in ["competition", "challenge", "hackathon", "leaderboard", "submission", "winner", "deadline", "code golf", "golf"])
judge = any(x in text for x in ["leaderboard", "submission", "score", "scoring", "benchmark", "metric", "eval", "evaluation", "test", "pytest", "ci", "workflow", "verifier", "checker", "acceptance"])
local = any(x in text for x in ["pytest", "npm test", "pnpm test", "yarn test", "cargo test", "go test", "make", "lake build", "benchmark", "python", "node"])
mgfit = any(x in text for x in ["lean", "proof", "theorem", "formal verification", "solver", "search", "constraint", "benchmark", "leaderboard", "optimization", "performance", "code golf", "correctness", "validation"])
risk = any(x in text for x in ["system prompt", "platform prompt", "jailbreak", "private key", "seed phrase", "wallet", "mainnet", "malware", "phishing", "casino", "gambling", "airdrop", "token"])

if risk:
  verdict = "PARK_RISK"
elif money and competition and judge and mgfit:
  verdict = "PROMOTE_COMPETITION_MONEY"
elif money and judge and local and mgfit:
  verdict = "PROMOTE_PAID_REPAIR"
elif competition and judge and mgfit:
  verdict = "PROMOTE_COMPETITION_REPUTATION_OR_PRIZE_UNKNOWN"
elif money and not judge:
  verdict = "ASK_FOR_JUDGE"
else:
  verdict = "PARK_WEAK"

decision = {
  "verdict": verdict,
  "issue": issue,
  "money": money,
  "competition": competition,
  "judge": judge,
  "local": local,
  "mgfit": mgfit,
  "risk": risk,
}

(out / "decision.json").write_text(json.dumps(decision, indent=2))

lines = []
lines.append("# Prize Recon Report")
lines.append("")
lines.append("## Verdict")
lines.append("")
lines.append("`" + verdict + "`")
lines.append("")
lines.append("## Decision")
lines.append("")
lines.append("JSON:")
lines.append(json.dumps(decision, indent=2))
lines.append("")
lines.append("## Cheap commands")
lines.append("")
lines.append(cheap[:10000])
lines.append("")
lines.append("## Issue body")
lines.append("")
lines.append(body[:12000])
lines.append("")
lines.append("## Comments")
lines.append("")
lines.append(comments[:8000])
lines.append("")
lines.append("## Inventory excerpt")
lines.append("")
lines.append(inv[:12000])
lines.append("")
lines.append("## Grep excerpt")
lines.append("")
lines.append(grep[:24000])
lines.append("")
(out / "REPORT.md").write_text("\n".join(lines) + "\n")
print((out / "REPORT.md").read_text()[:18000])
PY2

cd "$ROOT" || exit 1

echo
echo "===================================================================================================="
echo "RECON treitforge/qsoripper #424"
echo "===================================================================================================="

REPO_NAME="treitforge/qsoripper"
ISSUE_NUM="424"
SAFE="treitforge__qsoripper_424"
LOCAL_REPO="$ROOT/external/money_opportunity_scout_v4_prize_words/$SAFE"
OUT="$BASE_OUT/$SAFE"

mkdir -p "$OUT"
mkdir -p "$(dirname "$LOCAL_REPO")"

echo "01 issue"
gh issue view "$ISSUE_NUM" --repo "$REPO_NAME" --json number,title,state,url,labels,body,comments,updatedAt,createdAt \
  > "$OUT/issue.json" 2> "$OUT/issue.err" || true

python3 - "$OUT" <<'PY2'
from pathlib import Path
import json, sys
out = Path(sys.argv[1])
p = out / "issue.json"
if p.exists() and p.stat().st_size:
  j = json.loads(p.read_text())
  summary = {
    "url": j.get("url"),
    "title": j.get("title"),
    "state": j.get("state"),
    "labels": [x.get("name") for x in j.get("labels", [])],
    "comment_count": len(j.get("comments", [])),
    "updatedAt": j.get("updatedAt"),
  }
  (out / "issue_summary.json").write_text(json.dumps(summary, indent=2))
  (out / "issue_body.md").write_text(j.get("body") or "")
  (out / "issue_comments.md").write_text("\n---\n".join(
    "## " + str((c.get("author") or {}).get("login")) + " — " + str(c.get("createdAt")) + "\n\n" + str(c.get("body") or "")
    for c in j.get("comments", [])
  ))
  print(json.dumps(summary, indent=2))
else:
  print("issue view failed")
  print((out / "issue.err").read_text(errors="replace") if (out / "issue.err").exists() else "")
PY2

echo
echo "02 clone/update"
if [ ! -d "$LOCAL_REPO/.git" ]; then
  gh repo clone "$REPO_NAME" "$LOCAL_REPO" -- --filter=blob:none \
    > "$OUT/clone.log" 2>&1 || true
else
  echo "[exists] $LOCAL_REPO" | tee "$OUT/clone.log"
fi

if [ ! -d "$LOCAL_REPO/.git" ]; then
  echo "clone failed"
  cat "$OUT/clone.log"
  continue
fi

cd "$LOCAL_REPO" || continue
git fetch origin --prune > "$OUT/git_fetch.log" 2>&1 || true
DEFAULT_BRANCH="$(git remote show origin 2>/dev/null | awk '/HEAD branch/ {print $NF}' | head -1)"
if [ -z "$DEFAULT_BRANCH" ]; then DEFAULT_BRANCH="main"; fi
git checkout "$DEFAULT_BRANCH" > "$OUT/git_checkout.log" 2>&1 || true
git pull --ff-only origin "$DEFAULT_BRANCH" > "$OUT/git_pull.log" 2>&1 || true
git rev-parse HEAD | tee "$OUT/head.txt"

echo
echo "03 inventory"
{
  echo "top files"
  find . -maxdepth 4 -type f | sed 's#^./##' | sort | head -1200
  echo
  echo "build/test/competition files"
  find . -maxdepth 6 -type f \( -name 'README*' -o -name 'package.json' -o -name 'pyproject.toml' -o -name 'requirements.txt' -o -name 'Cargo.toml' -o -name 'go.mod' -o -name 'Makefile' -o -name 'Dockerfile' -o -name 'lakefile.toml' -o -name 'lakefile.lean' -o -name 'lean-toolchain' -o -name '*.ipynb' -o -name '*.md' \) | sort | head -1000
  echo
  echo "workflows"
  find .github/workflows -type f 2>/dev/null | sort
} > "$OUT/inventory.txt" 2>&1

echo
echo "04 focused grep"
{
  echo "===== issue body ====="
  cat "$OUT/issue_body.md" 2>/dev/null || true

  echo
  echo "===== money/competition/judge hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=.lake --exclude-dir=node_modules --exclude-dir=target --exclude-dir=dist --exclude-dir=build \
    "prize|payment|cash|bounty|reward|competition|challenge|hackathon|leaderboard|submission|score|scoring|benchmark|metric|eval|evaluation|winner|deadline|golf|test|pytest|ci|workflow|acceptance|verifier|checker" . 2>/dev/null | head -3000

  echo
  echo "===== patch/search surface hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=.lake --exclude-dir=node_modules --exclude-dir=target --exclude-dir=dist --exclude-dir=build \
    "TODO|FIXME|bug|error|failing|regression|optimize|performance|proof|theorem|solver|search|constraint|correctness|validation|static|compile|type|Cannot find module" . 2>/dev/null | head -3000
} > "$OUT/grep.txt" 2>&1

echo
echo "05 cheap commands"
{
  echo "pwd=$(pwd)"
  echo
  if [ -f README.md ]; then
    echo "README head:"
    sed -n '1,220p' README.md
  fi
  if [ -f package.json ]; then
    echo
    echo "package scripts:"
    node -e 'const p=require("./package.json"); console.log(JSON.stringify(p.scripts||{},null,2))' 2>/dev/null || cat package.json | head -160
  fi
  if [ -f pyproject.toml ]; then
    echo
    echo "pyproject head:"
    sed -n '1,220p' pyproject.toml
  fi
  if [ -f Makefile ]; then
    echo
    echo "Makefile targets:"
    grep -nE "^[A-Za-z0-9_.-]+:" Makefile | head -80
  fi
  if [ -f lean-toolchain ]; then
    echo
    echo "lean-toolchain:"
    cat lean-toolchain
  fi
} > "$OUT/cheap_commands.txt" 2>&1

echo
echo "06 classify"
python3 - "$OUT" <<'PY2'
from pathlib import Path
import json, sys

out = Path(sys.argv[1])
issue = {}
try:
  issue = json.loads((out / "issue_summary.json").read_text())
except Exception:
  pass

body = (out / "issue_body.md").read_text(errors="replace") if (out / "issue_body.md").exists() else ""
comments = (out / "issue_comments.md").read_text(errors="replace") if (out / "issue_comments.md").exists() else ""
inv = (out / "inventory.txt").read_text(errors="replace") if (out / "inventory.txt").exists() else ""
grep = (out / "grep.txt").read_text(errors="replace") if (out / "grep.txt").exists() else ""
cheap = (out / "cheap_commands.txt").read_text(errors="replace") if (out / "cheap_commands.txt").exists() else ""
text = "\n".join([body, comments, inv, grep, cheap]).lower()

money = any(x in text for x in ["prize", "payment", "cash", "bounty", "reward", "paid", "$", "usd"])
competition = any(x in text for x in ["competition", "challenge", "hackathon", "leaderboard", "submission", "winner", "deadline", "code golf", "golf"])
judge = any(x in text for x in ["leaderboard", "submission", "score", "scoring", "benchmark", "metric", "eval", "evaluation", "test", "pytest", "ci", "workflow", "verifier", "checker", "acceptance"])
local = any(x in text for x in ["pytest", "npm test", "pnpm test", "yarn test", "cargo test", "go test", "make", "lake build", "benchmark", "python", "node"])
mgfit = any(x in text for x in ["lean", "proof", "theorem", "formal verification", "solver", "search", "constraint", "benchmark", "leaderboard", "optimization", "performance", "code golf", "correctness", "validation"])
risk = any(x in text for x in ["system prompt", "platform prompt", "jailbreak", "private key", "seed phrase", "wallet", "mainnet", "malware", "phishing", "casino", "gambling", "airdrop", "token"])

if risk:
  verdict = "PARK_RISK"
elif money and competition and judge and mgfit:
  verdict = "PROMOTE_COMPETITION_MONEY"
elif money and judge and local and mgfit:
  verdict = "PROMOTE_PAID_REPAIR"
elif competition and judge and mgfit:
  verdict = "PROMOTE_COMPETITION_REPUTATION_OR_PRIZE_UNKNOWN"
elif money and not judge:
  verdict = "ASK_FOR_JUDGE"
else:
  verdict = "PARK_WEAK"

decision = {
  "verdict": verdict,
  "issue": issue,
  "money": money,
  "competition": competition,
  "judge": judge,
  "local": local,
  "mgfit": mgfit,
  "risk": risk,
}

(out / "decision.json").write_text(json.dumps(decision, indent=2))

lines = []
lines.append("# Prize Recon Report")
lines.append("")
lines.append("## Verdict")
lines.append("")
lines.append("`" + verdict + "`")
lines.append("")
lines.append("## Decision")
lines.append("")
lines.append("JSON:")
lines.append(json.dumps(decision, indent=2))
lines.append("")
lines.append("## Cheap commands")
lines.append("")
lines.append(cheap[:10000])
lines.append("")
lines.append("## Issue body")
lines.append("")
lines.append(body[:12000])
lines.append("")
lines.append("## Comments")
lines.append("")
lines.append(comments[:8000])
lines.append("")
lines.append("## Inventory excerpt")
lines.append("")
lines.append(inv[:12000])
lines.append("")
lines.append("## Grep excerpt")
lines.append("")
lines.append(grep[:24000])
lines.append("")
(out / "REPORT.md").write_text("\n".join(lines) + "\n")
print((out / "REPORT.md").read_text()[:18000])
PY2

cd "$ROOT" || exit 1

echo
echo "===================================================================================================="
echo "RECON oslinin/chaingammon #5"
echo "===================================================================================================="

REPO_NAME="oslinin/chaingammon"
ISSUE_NUM="5"
SAFE="oslinin__chaingammon_5"
LOCAL_REPO="$ROOT/external/money_opportunity_scout_v4_prize_words/$SAFE"
OUT="$BASE_OUT/$SAFE"

mkdir -p "$OUT"
mkdir -p "$(dirname "$LOCAL_REPO")"

echo "01 issue"
gh issue view "$ISSUE_NUM" --repo "$REPO_NAME" --json number,title,state,url,labels,body,comments,updatedAt,createdAt \
  > "$OUT/issue.json" 2> "$OUT/issue.err" || true

python3 - "$OUT" <<'PY2'
from pathlib import Path
import json, sys
out = Path(sys.argv[1])
p = out / "issue.json"
if p.exists() and p.stat().st_size:
  j = json.loads(p.read_text())
  summary = {
    "url": j.get("url"),
    "title": j.get("title"),
    "state": j.get("state"),
    "labels": [x.get("name") for x in j.get("labels", [])],
    "comment_count": len(j.get("comments", [])),
    "updatedAt": j.get("updatedAt"),
  }
  (out / "issue_summary.json").write_text(json.dumps(summary, indent=2))
  (out / "issue_body.md").write_text(j.get("body") or "")
  (out / "issue_comments.md").write_text("\n---\n".join(
    "## " + str((c.get("author") or {}).get("login")) + " — " + str(c.get("createdAt")) + "\n\n" + str(c.get("body") or "")
    for c in j.get("comments", [])
  ))
  print(json.dumps(summary, indent=2))
else:
  print("issue view failed")
  print((out / "issue.err").read_text(errors="replace") if (out / "issue.err").exists() else "")
PY2

echo
echo "02 clone/update"
if [ ! -d "$LOCAL_REPO/.git" ]; then
  gh repo clone "$REPO_NAME" "$LOCAL_REPO" -- --filter=blob:none \
    > "$OUT/clone.log" 2>&1 || true
else
  echo "[exists] $LOCAL_REPO" | tee "$OUT/clone.log"
fi

if [ ! -d "$LOCAL_REPO/.git" ]; then
  echo "clone failed"
  cat "$OUT/clone.log"
  continue
fi

cd "$LOCAL_REPO" || continue
git fetch origin --prune > "$OUT/git_fetch.log" 2>&1 || true
DEFAULT_BRANCH="$(git remote show origin 2>/dev/null | awk '/HEAD branch/ {print $NF}' | head -1)"
if [ -z "$DEFAULT_BRANCH" ]; then DEFAULT_BRANCH="main"; fi
git checkout "$DEFAULT_BRANCH" > "$OUT/git_checkout.log" 2>&1 || true
git pull --ff-only origin "$DEFAULT_BRANCH" > "$OUT/git_pull.log" 2>&1 || true
git rev-parse HEAD | tee "$OUT/head.txt"

echo
echo "03 inventory"
{
  echo "top files"
  find . -maxdepth 4 -type f | sed 's#^./##' | sort | head -1200
  echo
  echo "build/test/competition files"
  find . -maxdepth 6 -type f \( -name 'README*' -o -name 'package.json' -o -name 'pyproject.toml' -o -name 'requirements.txt' -o -name 'Cargo.toml' -o -name 'go.mod' -o -name 'Makefile' -o -name 'Dockerfile' -o -name 'lakefile.toml' -o -name 'lakefile.lean' -o -name 'lean-toolchain' -o -name '*.ipynb' -o -name '*.md' \) | sort | head -1000
  echo
  echo "workflows"
  find .github/workflows -type f 2>/dev/null | sort
} > "$OUT/inventory.txt" 2>&1

echo
echo "04 focused grep"
{
  echo "===== issue body ====="
  cat "$OUT/issue_body.md" 2>/dev/null || true

  echo
  echo "===== money/competition/judge hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=.lake --exclude-dir=node_modules --exclude-dir=target --exclude-dir=dist --exclude-dir=build \
    "prize|payment|cash|bounty|reward|competition|challenge|hackathon|leaderboard|submission|score|scoring|benchmark|metric|eval|evaluation|winner|deadline|golf|test|pytest|ci|workflow|acceptance|verifier|checker" . 2>/dev/null | head -3000

  echo
  echo "===== patch/search surface hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=.lake --exclude-dir=node_modules --exclude-dir=target --exclude-dir=dist --exclude-dir=build \
    "TODO|FIXME|bug|error|failing|regression|optimize|performance|proof|theorem|solver|search|constraint|correctness|validation|static|compile|type|Cannot find module" . 2>/dev/null | head -3000
} > "$OUT/grep.txt" 2>&1

echo
echo "05 cheap commands"
{
  echo "pwd=$(pwd)"
  echo
  if [ -f README.md ]; then
    echo "README head:"
    sed -n '1,220p' README.md
  fi
  if [ -f package.json ]; then
    echo
    echo "package scripts:"
    node -e 'const p=require("./package.json"); console.log(JSON.stringify(p.scripts||{},null,2))' 2>/dev/null || cat package.json | head -160
  fi
  if [ -f pyproject.toml ]; then
    echo
    echo "pyproject head:"
    sed -n '1,220p' pyproject.toml
  fi
  if [ -f Makefile ]; then
    echo
    echo "Makefile targets:"
    grep -nE "^[A-Za-z0-9_.-]+:" Makefile | head -80
  fi
  if [ -f lean-toolchain ]; then
    echo
    echo "lean-toolchain:"
    cat lean-toolchain
  fi
} > "$OUT/cheap_commands.txt" 2>&1

echo
echo "06 classify"
python3 - "$OUT" <<'PY2'
from pathlib import Path
import json, sys

out = Path(sys.argv[1])
issue = {}
try:
  issue = json.loads((out / "issue_summary.json").read_text())
except Exception:
  pass

body = (out / "issue_body.md").read_text(errors="replace") if (out / "issue_body.md").exists() else ""
comments = (out / "issue_comments.md").read_text(errors="replace") if (out / "issue_comments.md").exists() else ""
inv = (out / "inventory.txt").read_text(errors="replace") if (out / "inventory.txt").exists() else ""
grep = (out / "grep.txt").read_text(errors="replace") if (out / "grep.txt").exists() else ""
cheap = (out / "cheap_commands.txt").read_text(errors="replace") if (out / "cheap_commands.txt").exists() else ""
text = "\n".join([body, comments, inv, grep, cheap]).lower()

money = any(x in text for x in ["prize", "payment", "cash", "bounty", "reward", "paid", "$", "usd"])
competition = any(x in text for x in ["competition", "challenge", "hackathon", "leaderboard", "submission", "winner", "deadline", "code golf", "golf"])
judge = any(x in text for x in ["leaderboard", "submission", "score", "scoring", "benchmark", "metric", "eval", "evaluation", "test", "pytest", "ci", "workflow", "verifier", "checker", "acceptance"])
local = any(x in text for x in ["pytest", "npm test", "pnpm test", "yarn test", "cargo test", "go test", "make", "lake build", "benchmark", "python", "node"])
mgfit = any(x in text for x in ["lean", "proof", "theorem", "formal verification", "solver", "search", "constraint", "benchmark", "leaderboard", "optimization", "performance", "code golf", "correctness", "validation"])
risk = any(x in text for x in ["system prompt", "platform prompt", "jailbreak", "private key", "seed phrase", "wallet", "mainnet", "malware", "phishing", "casino", "gambling", "airdrop", "token"])

if risk:
  verdict = "PARK_RISK"
elif money and competition and judge and mgfit:
  verdict = "PROMOTE_COMPETITION_MONEY"
elif money and judge and local and mgfit:
  verdict = "PROMOTE_PAID_REPAIR"
elif competition and judge and mgfit:
  verdict = "PROMOTE_COMPETITION_REPUTATION_OR_PRIZE_UNKNOWN"
elif money and not judge:
  verdict = "ASK_FOR_JUDGE"
else:
  verdict = "PARK_WEAK"

decision = {
  "verdict": verdict,
  "issue": issue,
  "money": money,
  "competition": competition,
  "judge": judge,
  "local": local,
  "mgfit": mgfit,
  "risk": risk,
}

(out / "decision.json").write_text(json.dumps(decision, indent=2))

lines = []
lines.append("# Prize Recon Report")
lines.append("")
lines.append("## Verdict")
lines.append("")
lines.append("`" + verdict + "`")
lines.append("")
lines.append("## Decision")
lines.append("")
lines.append("JSON:")
lines.append(json.dumps(decision, indent=2))
lines.append("")
lines.append("## Cheap commands")
lines.append("")
lines.append(cheap[:10000])
lines.append("")
lines.append("## Issue body")
lines.append("")
lines.append(body[:12000])
lines.append("")
lines.append("## Comments")
lines.append("")
lines.append(comments[:8000])
lines.append("")
lines.append("## Inventory excerpt")
lines.append("")
lines.append(inv[:12000])
lines.append("")
lines.append("## Grep excerpt")
lines.append("")
lines.append(grep[:24000])
lines.append("")
(out / "REPORT.md").write_text("\n".join(lines) + "\n")
print((out / "REPORT.md").read_text()[:18000])
PY2

cd "$ROOT" || exit 1

echo
echo "===================================================================================================="
echo "RECON moldovancsaba/matimato #66"
echo "===================================================================================================="

REPO_NAME="moldovancsaba/matimato"
ISSUE_NUM="66"
SAFE="moldovancsaba__matimato_66"
LOCAL_REPO="$ROOT/external/money_opportunity_scout_v4_prize_words/$SAFE"
OUT="$BASE_OUT/$SAFE"

mkdir -p "$OUT"
mkdir -p "$(dirname "$LOCAL_REPO")"

echo "01 issue"
gh issue view "$ISSUE_NUM" --repo "$REPO_NAME" --json number,title,state,url,labels,body,comments,updatedAt,createdAt \
  > "$OUT/issue.json" 2> "$OUT/issue.err" || true

python3 - "$OUT" <<'PY2'
from pathlib import Path
import json, sys
out = Path(sys.argv[1])
p = out / "issue.json"
if p.exists() and p.stat().st_size:
  j = json.loads(p.read_text())
  summary = {
    "url": j.get("url"),
    "title": j.get("title"),
    "state": j.get("state"),
    "labels": [x.get("name") for x in j.get("labels", [])],
    "comment_count": len(j.get("comments", [])),
    "updatedAt": j.get("updatedAt"),
  }
  (out / "issue_summary.json").write_text(json.dumps(summary, indent=2))
  (out / "issue_body.md").write_text(j.get("body") or "")
  (out / "issue_comments.md").write_text("\n---\n".join(
    "## " + str((c.get("author") or {}).get("login")) + " — " + str(c.get("createdAt")) + "\n\n" + str(c.get("body") or "")
    for c in j.get("comments", [])
  ))
  print(json.dumps(summary, indent=2))
else:
  print("issue view failed")
  print((out / "issue.err").read_text(errors="replace") if (out / "issue.err").exists() else "")
PY2

echo
echo "02 clone/update"
if [ ! -d "$LOCAL_REPO/.git" ]; then
  gh repo clone "$REPO_NAME" "$LOCAL_REPO" -- --filter=blob:none \
    > "$OUT/clone.log" 2>&1 || true
else
  echo "[exists] $LOCAL_REPO" | tee "$OUT/clone.log"
fi

if [ ! -d "$LOCAL_REPO/.git" ]; then
  echo "clone failed"
  cat "$OUT/clone.log"
  continue
fi

cd "$LOCAL_REPO" || continue
git fetch origin --prune > "$OUT/git_fetch.log" 2>&1 || true
DEFAULT_BRANCH="$(git remote show origin 2>/dev/null | awk '/HEAD branch/ {print $NF}' | head -1)"
if [ -z "$DEFAULT_BRANCH" ]; then DEFAULT_BRANCH="main"; fi
git checkout "$DEFAULT_BRANCH" > "$OUT/git_checkout.log" 2>&1 || true
git pull --ff-only origin "$DEFAULT_BRANCH" > "$OUT/git_pull.log" 2>&1 || true
git rev-parse HEAD | tee "$OUT/head.txt"

echo
echo "03 inventory"
{
  echo "top files"
  find . -maxdepth 4 -type f | sed 's#^./##' | sort | head -1200
  echo
  echo "build/test/competition files"
  find . -maxdepth 6 -type f \( -name 'README*' -o -name 'package.json' -o -name 'pyproject.toml' -o -name 'requirements.txt' -o -name 'Cargo.toml' -o -name 'go.mod' -o -name 'Makefile' -o -name 'Dockerfile' -o -name 'lakefile.toml' -o -name 'lakefile.lean' -o -name 'lean-toolchain' -o -name '*.ipynb' -o -name '*.md' \) | sort | head -1000
  echo
  echo "workflows"
  find .github/workflows -type f 2>/dev/null | sort
} > "$OUT/inventory.txt" 2>&1

echo
echo "04 focused grep"
{
  echo "===== issue body ====="
  cat "$OUT/issue_body.md" 2>/dev/null || true

  echo
  echo "===== money/competition/judge hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=.lake --exclude-dir=node_modules --exclude-dir=target --exclude-dir=dist --exclude-dir=build \
    "prize|payment|cash|bounty|reward|competition|challenge|hackathon|leaderboard|submission|score|scoring|benchmark|metric|eval|evaluation|winner|deadline|golf|test|pytest|ci|workflow|acceptance|verifier|checker" . 2>/dev/null | head -3000

  echo
  echo "===== patch/search surface hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=.lake --exclude-dir=node_modules --exclude-dir=target --exclude-dir=dist --exclude-dir=build \
    "TODO|FIXME|bug|error|failing|regression|optimize|performance|proof|theorem|solver|search|constraint|correctness|validation|static|compile|type|Cannot find module" . 2>/dev/null | head -3000
} > "$OUT/grep.txt" 2>&1

echo
echo "05 cheap commands"
{
  echo "pwd=$(pwd)"
  echo
  if [ -f README.md ]; then
    echo "README head:"
    sed -n '1,220p' README.md
  fi
  if [ -f package.json ]; then
    echo
    echo "package scripts:"
    node -e 'const p=require("./package.json"); console.log(JSON.stringify(p.scripts||{},null,2))' 2>/dev/null || cat package.json | head -160
  fi
  if [ -f pyproject.toml ]; then
    echo
    echo "pyproject head:"
    sed -n '1,220p' pyproject.toml
  fi
  if [ -f Makefile ]; then
    echo
    echo "Makefile targets:"
    grep -nE "^[A-Za-z0-9_.-]+:" Makefile | head -80
  fi
  if [ -f lean-toolchain ]; then
    echo
    echo "lean-toolchain:"
    cat lean-toolchain
  fi
} > "$OUT/cheap_commands.txt" 2>&1

echo
echo "06 classify"
python3 - "$OUT" <<'PY2'
from pathlib import Path
import json, sys

out = Path(sys.argv[1])
issue = {}
try:
  issue = json.loads((out / "issue_summary.json").read_text())
except Exception:
  pass

body = (out / "issue_body.md").read_text(errors="replace") if (out / "issue_body.md").exists() else ""
comments = (out / "issue_comments.md").read_text(errors="replace") if (out / "issue_comments.md").exists() else ""
inv = (out / "inventory.txt").read_text(errors="replace") if (out / "inventory.txt").exists() else ""
grep = (out / "grep.txt").read_text(errors="replace") if (out / "grep.txt").exists() else ""
cheap = (out / "cheap_commands.txt").read_text(errors="replace") if (out / "cheap_commands.txt").exists() else ""
text = "\n".join([body, comments, inv, grep, cheap]).lower()

money = any(x in text for x in ["prize", "payment", "cash", "bounty", "reward", "paid", "$", "usd"])
competition = any(x in text for x in ["competition", "challenge", "hackathon", "leaderboard", "submission", "winner", "deadline", "code golf", "golf"])
judge = any(x in text for x in ["leaderboard", "submission", "score", "scoring", "benchmark", "metric", "eval", "evaluation", "test", "pytest", "ci", "workflow", "verifier", "checker", "acceptance"])
local = any(x in text for x in ["pytest", "npm test", "pnpm test", "yarn test", "cargo test", "go test", "make", "lake build", "benchmark", "python", "node"])
mgfit = any(x in text for x in ["lean", "proof", "theorem", "formal verification", "solver", "search", "constraint", "benchmark", "leaderboard", "optimization", "performance", "code golf", "correctness", "validation"])
risk = any(x in text for x in ["system prompt", "platform prompt", "jailbreak", "private key", "seed phrase", "wallet", "mainnet", "malware", "phishing", "casino", "gambling", "airdrop", "token"])

if risk:
  verdict = "PARK_RISK"
elif money and competition and judge and mgfit:
  verdict = "PROMOTE_COMPETITION_MONEY"
elif money and judge and local and mgfit:
  verdict = "PROMOTE_PAID_REPAIR"
elif competition and judge and mgfit:
  verdict = "PROMOTE_COMPETITION_REPUTATION_OR_PRIZE_UNKNOWN"
elif money and not judge:
  verdict = "ASK_FOR_JUDGE"
else:
  verdict = "PARK_WEAK"

decision = {
  "verdict": verdict,
  "issue": issue,
  "money": money,
  "competition": competition,
  "judge": judge,
  "local": local,
  "mgfit": mgfit,
  "risk": risk,
}

(out / "decision.json").write_text(json.dumps(decision, indent=2))

lines = []
lines.append("# Prize Recon Report")
lines.append("")
lines.append("## Verdict")
lines.append("")
lines.append("`" + verdict + "`")
lines.append("")
lines.append("## Decision")
lines.append("")
lines.append("JSON:")
lines.append(json.dumps(decision, indent=2))
lines.append("")
lines.append("## Cheap commands")
lines.append("")
lines.append(cheap[:10000])
lines.append("")
lines.append("## Issue body")
lines.append("")
lines.append(body[:12000])
lines.append("")
lines.append("## Comments")
lines.append("")
lines.append(comments[:8000])
lines.append("")
lines.append("## Inventory excerpt")
lines.append("")
lines.append(inv[:12000])
lines.append("")
lines.append("## Grep excerpt")
lines.append("")
lines.append(grep[:24000])
lines.append("")
(out / "REPORT.md").write_text("\n".join(lines) + "\n")
print((out / "REPORT.md").read_text()[:18000])
PY2

cd "$ROOT" || exit 1

echo
echo "===================================================================================================="
echo "RECON anonhostpi/Agent-World #24"
echo "===================================================================================================="

REPO_NAME="anonhostpi/Agent-World"
ISSUE_NUM="24"
SAFE="anonhostpi__Agent-World_24"
LOCAL_REPO="$ROOT/external/money_opportunity_scout_v4_prize_words/$SAFE"
OUT="$BASE_OUT/$SAFE"

mkdir -p "$OUT"
mkdir -p "$(dirname "$LOCAL_REPO")"

echo "01 issue"
gh issue view "$ISSUE_NUM" --repo "$REPO_NAME" --json number,title,state,url,labels,body,comments,updatedAt,createdAt \
  > "$OUT/issue.json" 2> "$OUT/issue.err" || true

python3 - "$OUT" <<'PY2'
from pathlib import Path
import json, sys
out = Path(sys.argv[1])
p = out / "issue.json"
if p.exists() and p.stat().st_size:
  j = json.loads(p.read_text())
  summary = {
    "url": j.get("url"),
    "title": j.get("title"),
    "state": j.get("state"),
    "labels": [x.get("name") for x in j.get("labels", [])],
    "comment_count": len(j.get("comments", [])),
    "updatedAt": j.get("updatedAt"),
  }
  (out / "issue_summary.json").write_text(json.dumps(summary, indent=2))
  (out / "issue_body.md").write_text(j.get("body") or "")
  (out / "issue_comments.md").write_text("\n---\n".join(
    "## " + str((c.get("author") or {}).get("login")) + " — " + str(c.get("createdAt")) + "\n\n" + str(c.get("body") or "")
    for c in j.get("comments", [])
  ))
  print(json.dumps(summary, indent=2))
else:
  print("issue view failed")
  print((out / "issue.err").read_text(errors="replace") if (out / "issue.err").exists() else "")
PY2

echo
echo "02 clone/update"
if [ ! -d "$LOCAL_REPO/.git" ]; then
  gh repo clone "$REPO_NAME" "$LOCAL_REPO" -- --filter=blob:none \
    > "$OUT/clone.log" 2>&1 || true
else
  echo "[exists] $LOCAL_REPO" | tee "$OUT/clone.log"
fi

if [ ! -d "$LOCAL_REPO/.git" ]; then
  echo "clone failed"
  cat "$OUT/clone.log"
  continue
fi

cd "$LOCAL_REPO" || continue
git fetch origin --prune > "$OUT/git_fetch.log" 2>&1 || true
DEFAULT_BRANCH="$(git remote show origin 2>/dev/null | awk '/HEAD branch/ {print $NF}' | head -1)"
if [ -z "$DEFAULT_BRANCH" ]; then DEFAULT_BRANCH="main"; fi
git checkout "$DEFAULT_BRANCH" > "$OUT/git_checkout.log" 2>&1 || true
git pull --ff-only origin "$DEFAULT_BRANCH" > "$OUT/git_pull.log" 2>&1 || true
git rev-parse HEAD | tee "$OUT/head.txt"

echo
echo "03 inventory"
{
  echo "top files"
  find . -maxdepth 4 -type f | sed 's#^./##' | sort | head -1200
  echo
  echo "build/test/competition files"
  find . -maxdepth 6 -type f \( -name 'README*' -o -name 'package.json' -o -name 'pyproject.toml' -o -name 'requirements.txt' -o -name 'Cargo.toml' -o -name 'go.mod' -o -name 'Makefile' -o -name 'Dockerfile' -o -name 'lakefile.toml' -o -name 'lakefile.lean' -o -name 'lean-toolchain' -o -name '*.ipynb' -o -name '*.md' \) | sort | head -1000
  echo
  echo "workflows"
  find .github/workflows -type f 2>/dev/null | sort
} > "$OUT/inventory.txt" 2>&1

echo
echo "04 focused grep"
{
  echo "===== issue body ====="
  cat "$OUT/issue_body.md" 2>/dev/null || true

  echo
  echo "===== money/competition/judge hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=.lake --exclude-dir=node_modules --exclude-dir=target --exclude-dir=dist --exclude-dir=build \
    "prize|payment|cash|bounty|reward|competition|challenge|hackathon|leaderboard|submission|score|scoring|benchmark|metric|eval|evaluation|winner|deadline|golf|test|pytest|ci|workflow|acceptance|verifier|checker" . 2>/dev/null | head -3000

  echo
  echo "===== patch/search surface hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=.lake --exclude-dir=node_modules --exclude-dir=target --exclude-dir=dist --exclude-dir=build \
    "TODO|FIXME|bug|error|failing|regression|optimize|performance|proof|theorem|solver|search|constraint|correctness|validation|static|compile|type|Cannot find module" . 2>/dev/null | head -3000
} > "$OUT/grep.txt" 2>&1

echo
echo "05 cheap commands"
{
  echo "pwd=$(pwd)"
  echo
  if [ -f README.md ]; then
    echo "README head:"
    sed -n '1,220p' README.md
  fi
  if [ -f package.json ]; then
    echo
    echo "package scripts:"
    node -e 'const p=require("./package.json"); console.log(JSON.stringify(p.scripts||{},null,2))' 2>/dev/null || cat package.json | head -160
  fi
  if [ -f pyproject.toml ]; then
    echo
    echo "pyproject head:"
    sed -n '1,220p' pyproject.toml
  fi
  if [ -f Makefile ]; then
    echo
    echo "Makefile targets:"
    grep -nE "^[A-Za-z0-9_.-]+:" Makefile | head -80
  fi
  if [ -f lean-toolchain ]; then
    echo
    echo "lean-toolchain:"
    cat lean-toolchain
  fi
} > "$OUT/cheap_commands.txt" 2>&1

echo
echo "06 classify"
python3 - "$OUT" <<'PY2'
from pathlib import Path
import json, sys

out = Path(sys.argv[1])
issue = {}
try:
  issue = json.loads((out / "issue_summary.json").read_text())
except Exception:
  pass

body = (out / "issue_body.md").read_text(errors="replace") if (out / "issue_body.md").exists() else ""
comments = (out / "issue_comments.md").read_text(errors="replace") if (out / "issue_comments.md").exists() else ""
inv = (out / "inventory.txt").read_text(errors="replace") if (out / "inventory.txt").exists() else ""
grep = (out / "grep.txt").read_text(errors="replace") if (out / "grep.txt").exists() else ""
cheap = (out / "cheap_commands.txt").read_text(errors="replace") if (out / "cheap_commands.txt").exists() else ""
text = "\n".join([body, comments, inv, grep, cheap]).lower()

money = any(x in text for x in ["prize", "payment", "cash", "bounty", "reward", "paid", "$", "usd"])
competition = any(x in text for x in ["competition", "challenge", "hackathon", "leaderboard", "submission", "winner", "deadline", "code golf", "golf"])
judge = any(x in text for x in ["leaderboard", "submission", "score", "scoring", "benchmark", "metric", "eval", "evaluation", "test", "pytest", "ci", "workflow", "verifier", "checker", "acceptance"])
local = any(x in text for x in ["pytest", "npm test", "pnpm test", "yarn test", "cargo test", "go test", "make", "lake build", "benchmark", "python", "node"])
mgfit = any(x in text for x in ["lean", "proof", "theorem", "formal verification", "solver", "search", "constraint", "benchmark", "leaderboard", "optimization", "performance", "code golf", "correctness", "validation"])
risk = any(x in text for x in ["system prompt", "platform prompt", "jailbreak", "private key", "seed phrase", "wallet", "mainnet", "malware", "phishing", "casino", "gambling", "airdrop", "token"])

if risk:
  verdict = "PARK_RISK"
elif money and competition and judge and mgfit:
  verdict = "PROMOTE_COMPETITION_MONEY"
elif money and judge and local and mgfit:
  verdict = "PROMOTE_PAID_REPAIR"
elif competition and judge and mgfit:
  verdict = "PROMOTE_COMPETITION_REPUTATION_OR_PRIZE_UNKNOWN"
elif money and not judge:
  verdict = "ASK_FOR_JUDGE"
else:
  verdict = "PARK_WEAK"

decision = {
  "verdict": verdict,
  "issue": issue,
  "money": money,
  "competition": competition,
  "judge": judge,
  "local": local,
  "mgfit": mgfit,
  "risk": risk,
}

(out / "decision.json").write_text(json.dumps(decision, indent=2))

lines = []
lines.append("# Prize Recon Report")
lines.append("")
lines.append("## Verdict")
lines.append("")
lines.append("`" + verdict + "`")
lines.append("")
lines.append("## Decision")
lines.append("")
lines.append("JSON:")
lines.append(json.dumps(decision, indent=2))
lines.append("")
lines.append("## Cheap commands")
lines.append("")
lines.append(cheap[:10000])
lines.append("")
lines.append("## Issue body")
lines.append("")
lines.append(body[:12000])
lines.append("")
lines.append("## Comments")
lines.append("")
lines.append(comments[:8000])
lines.append("")
lines.append("## Inventory excerpt")
lines.append("")
lines.append(inv[:12000])
lines.append("")
lines.append("## Grep excerpt")
lines.append("")
lines.append(grep[:24000])
lines.append("")
(out / "REPORT.md").write_text("\n".join(lines) + "\n")
print((out / "REPORT.md").read_text()[:18000])
PY2

cd "$ROOT" || exit 1

echo
echo "===================================================================================================="
echo "RECON ropensci/ozunconf17 #22"
echo "===================================================================================================="

REPO_NAME="ropensci/ozunconf17"
ISSUE_NUM="22"
SAFE="ropensci__ozunconf17_22"
LOCAL_REPO="$ROOT/external/money_opportunity_scout_v4_prize_words/$SAFE"
OUT="$BASE_OUT/$SAFE"

mkdir -p "$OUT"
mkdir -p "$(dirname "$LOCAL_REPO")"

echo "01 issue"
gh issue view "$ISSUE_NUM" --repo "$REPO_NAME" --json number,title,state,url,labels,body,comments,updatedAt,createdAt \
  > "$OUT/issue.json" 2> "$OUT/issue.err" || true

python3 - "$OUT" <<'PY2'
from pathlib import Path
import json, sys
out = Path(sys.argv[1])
p = out / "issue.json"
if p.exists() and p.stat().st_size:
  j = json.loads(p.read_text())
  summary = {
    "url": j.get("url"),
    "title": j.get("title"),
    "state": j.get("state"),
    "labels": [x.get("name") for x in j.get("labels", [])],
    "comment_count": len(j.get("comments", [])),
    "updatedAt": j.get("updatedAt"),
  }
  (out / "issue_summary.json").write_text(json.dumps(summary, indent=2))
  (out / "issue_body.md").write_text(j.get("body") or "")
  (out / "issue_comments.md").write_text("\n---\n".join(
    "## " + str((c.get("author") or {}).get("login")) + " — " + str(c.get("createdAt")) + "\n\n" + str(c.get("body") or "")
    for c in j.get("comments", [])
  ))
  print(json.dumps(summary, indent=2))
else:
  print("issue view failed")
  print((out / "issue.err").read_text(errors="replace") if (out / "issue.err").exists() else "")
PY2

echo
echo "02 clone/update"
if [ ! -d "$LOCAL_REPO/.git" ]; then
  gh repo clone "$REPO_NAME" "$LOCAL_REPO" -- --filter=blob:none \
    > "$OUT/clone.log" 2>&1 || true
else
  echo "[exists] $LOCAL_REPO" | tee "$OUT/clone.log"
fi

if [ ! -d "$LOCAL_REPO/.git" ]; then
  echo "clone failed"
  cat "$OUT/clone.log"
  continue
fi

cd "$LOCAL_REPO" || continue
git fetch origin --prune > "$OUT/git_fetch.log" 2>&1 || true
DEFAULT_BRANCH="$(git remote show origin 2>/dev/null | awk '/HEAD branch/ {print $NF}' | head -1)"
if [ -z "$DEFAULT_BRANCH" ]; then DEFAULT_BRANCH="main"; fi
git checkout "$DEFAULT_BRANCH" > "$OUT/git_checkout.log" 2>&1 || true
git pull --ff-only origin "$DEFAULT_BRANCH" > "$OUT/git_pull.log" 2>&1 || true
git rev-parse HEAD | tee "$OUT/head.txt"

echo
echo "03 inventory"
{
  echo "top files"
  find . -maxdepth 4 -type f | sed 's#^./##' | sort | head -1200
  echo
  echo "build/test/competition files"
  find . -maxdepth 6 -type f \( -name 'README*' -o -name 'package.json' -o -name 'pyproject.toml' -o -name 'requirements.txt' -o -name 'Cargo.toml' -o -name 'go.mod' -o -name 'Makefile' -o -name 'Dockerfile' -o -name 'lakefile.toml' -o -name 'lakefile.lean' -o -name 'lean-toolchain' -o -name '*.ipynb' -o -name '*.md' \) | sort | head -1000
  echo
  echo "workflows"
  find .github/workflows -type f 2>/dev/null | sort
} > "$OUT/inventory.txt" 2>&1

echo
echo "04 focused grep"
{
  echo "===== issue body ====="
  cat "$OUT/issue_body.md" 2>/dev/null || true

  echo
  echo "===== money/competition/judge hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=.lake --exclude-dir=node_modules --exclude-dir=target --exclude-dir=dist --exclude-dir=build \
    "prize|payment|cash|bounty|reward|competition|challenge|hackathon|leaderboard|submission|score|scoring|benchmark|metric|eval|evaluation|winner|deadline|golf|test|pytest|ci|workflow|acceptance|verifier|checker" . 2>/dev/null | head -3000

  echo
  echo "===== patch/search surface hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=.lake --exclude-dir=node_modules --exclude-dir=target --exclude-dir=dist --exclude-dir=build \
    "TODO|FIXME|bug|error|failing|regression|optimize|performance|proof|theorem|solver|search|constraint|correctness|validation|static|compile|type|Cannot find module" . 2>/dev/null | head -3000
} > "$OUT/grep.txt" 2>&1

echo
echo "05 cheap commands"
{
  echo "pwd=$(pwd)"
  echo
  if [ -f README.md ]; then
    echo "README head:"
    sed -n '1,220p' README.md
  fi
  if [ -f package.json ]; then
    echo
    echo "package scripts:"
    node -e 'const p=require("./package.json"); console.log(JSON.stringify(p.scripts||{},null,2))' 2>/dev/null || cat package.json | head -160
  fi
  if [ -f pyproject.toml ]; then
    echo
    echo "pyproject head:"
    sed -n '1,220p' pyproject.toml
  fi
  if [ -f Makefile ]; then
    echo
    echo "Makefile targets:"
    grep -nE "^[A-Za-z0-9_.-]+:" Makefile | head -80
  fi
  if [ -f lean-toolchain ]; then
    echo
    echo "lean-toolchain:"
    cat lean-toolchain
  fi
} > "$OUT/cheap_commands.txt" 2>&1

echo
echo "06 classify"
python3 - "$OUT" <<'PY2'
from pathlib import Path
import json, sys

out = Path(sys.argv[1])
issue = {}
try:
  issue = json.loads((out / "issue_summary.json").read_text())
except Exception:
  pass

body = (out / "issue_body.md").read_text(errors="replace") if (out / "issue_body.md").exists() else ""
comments = (out / "issue_comments.md").read_text(errors="replace") if (out / "issue_comments.md").exists() else ""
inv = (out / "inventory.txt").read_text(errors="replace") if (out / "inventory.txt").exists() else ""
grep = (out / "grep.txt").read_text(errors="replace") if (out / "grep.txt").exists() else ""
cheap = (out / "cheap_commands.txt").read_text(errors="replace") if (out / "cheap_commands.txt").exists() else ""
text = "\n".join([body, comments, inv, grep, cheap]).lower()

money = any(x in text for x in ["prize", "payment", "cash", "bounty", "reward", "paid", "$", "usd"])
competition = any(x in text for x in ["competition", "challenge", "hackathon", "leaderboard", "submission", "winner", "deadline", "code golf", "golf"])
judge = any(x in text for x in ["leaderboard", "submission", "score", "scoring", "benchmark", "metric", "eval", "evaluation", "test", "pytest", "ci", "workflow", "verifier", "checker", "acceptance"])
local = any(x in text for x in ["pytest", "npm test", "pnpm test", "yarn test", "cargo test", "go test", "make", "lake build", "benchmark", "python", "node"])
mgfit = any(x in text for x in ["lean", "proof", "theorem", "formal verification", "solver", "search", "constraint", "benchmark", "leaderboard", "optimization", "performance", "code golf", "correctness", "validation"])
risk = any(x in text for x in ["system prompt", "platform prompt", "jailbreak", "private key", "seed phrase", "wallet", "mainnet", "malware", "phishing", "casino", "gambling", "airdrop", "token"])

if risk:
  verdict = "PARK_RISK"
elif money and competition and judge and mgfit:
  verdict = "PROMOTE_COMPETITION_MONEY"
elif money and judge and local and mgfit:
  verdict = "PROMOTE_PAID_REPAIR"
elif competition and judge and mgfit:
  verdict = "PROMOTE_COMPETITION_REPUTATION_OR_PRIZE_UNKNOWN"
elif money and not judge:
  verdict = "ASK_FOR_JUDGE"
else:
  verdict = "PARK_WEAK"

decision = {
  "verdict": verdict,
  "issue": issue,
  "money": money,
  "competition": competition,
  "judge": judge,
  "local": local,
  "mgfit": mgfit,
  "risk": risk,
}

(out / "decision.json").write_text(json.dumps(decision, indent=2))

lines = []
lines.append("# Prize Recon Report")
lines.append("")
lines.append("## Verdict")
lines.append("")
lines.append("`" + verdict + "`")
lines.append("")
lines.append("## Decision")
lines.append("")
lines.append("JSON:")
lines.append(json.dumps(decision, indent=2))
lines.append("")
lines.append("## Cheap commands")
lines.append("")
lines.append(cheap[:10000])
lines.append("")
lines.append("## Issue body")
lines.append("")
lines.append(body[:12000])
lines.append("")
lines.append("## Comments")
lines.append("")
lines.append(comments[:8000])
lines.append("")
lines.append("## Inventory excerpt")
lines.append("")
lines.append(inv[:12000])
lines.append("")
lines.append("## Grep excerpt")
lines.append("")
lines.append(grep[:24000])
lines.append("")
(out / "REPORT.md").write_text("\n".join(lines) + "\n")
print((out / "REPORT.md").read_text()[:18000])
PY2

cd "$ROOT" || exit 1

echo
echo "===================================================================================================="
echo "RECON agentclash/agentclash #1097"
echo "===================================================================================================="

REPO_NAME="agentclash/agentclash"
ISSUE_NUM="1097"
SAFE="agentclash__agentclash_1097"
LOCAL_REPO="$ROOT/external/money_opportunity_scout_v4_prize_words/$SAFE"
OUT="$BASE_OUT/$SAFE"

mkdir -p "$OUT"
mkdir -p "$(dirname "$LOCAL_REPO")"

echo "01 issue"
gh issue view "$ISSUE_NUM" --repo "$REPO_NAME" --json number,title,state,url,labels,body,comments,updatedAt,createdAt \
  > "$OUT/issue.json" 2> "$OUT/issue.err" || true

python3 - "$OUT" <<'PY2'
from pathlib import Path
import json, sys
out = Path(sys.argv[1])
p = out / "issue.json"
if p.exists() and p.stat().st_size:
  j = json.loads(p.read_text())
  summary = {
    "url": j.get("url"),
    "title": j.get("title"),
    "state": j.get("state"),
    "labels": [x.get("name") for x in j.get("labels", [])],
    "comment_count": len(j.get("comments", [])),
    "updatedAt": j.get("updatedAt"),
  }
  (out / "issue_summary.json").write_text(json.dumps(summary, indent=2))
  (out / "issue_body.md").write_text(j.get("body") or "")
  (out / "issue_comments.md").write_text("\n---\n".join(
    "## " + str((c.get("author") or {}).get("login")) + " — " + str(c.get("createdAt")) + "\n\n" + str(c.get("body") or "")
    for c in j.get("comments", [])
  ))
  print(json.dumps(summary, indent=2))
else:
  print("issue view failed")
  print((out / "issue.err").read_text(errors="replace") if (out / "issue.err").exists() else "")
PY2

echo
echo "02 clone/update"
if [ ! -d "$LOCAL_REPO/.git" ]; then
  gh repo clone "$REPO_NAME" "$LOCAL_REPO" -- --filter=blob:none \
    > "$OUT/clone.log" 2>&1 || true
else
  echo "[exists] $LOCAL_REPO" | tee "$OUT/clone.log"
fi

if [ ! -d "$LOCAL_REPO/.git" ]; then
  echo "clone failed"
  cat "$OUT/clone.log"
  continue
fi

cd "$LOCAL_REPO" || continue
git fetch origin --prune > "$OUT/git_fetch.log" 2>&1 || true
DEFAULT_BRANCH="$(git remote show origin 2>/dev/null | awk '/HEAD branch/ {print $NF}' | head -1)"
if [ -z "$DEFAULT_BRANCH" ]; then DEFAULT_BRANCH="main"; fi
git checkout "$DEFAULT_BRANCH" > "$OUT/git_checkout.log" 2>&1 || true
git pull --ff-only origin "$DEFAULT_BRANCH" > "$OUT/git_pull.log" 2>&1 || true
git rev-parse HEAD | tee "$OUT/head.txt"

echo
echo "03 inventory"
{
  echo "top files"
  find . -maxdepth 4 -type f | sed 's#^./##' | sort | head -1200
  echo
  echo "build/test/competition files"
  find . -maxdepth 6 -type f \( -name 'README*' -o -name 'package.json' -o -name 'pyproject.toml' -o -name 'requirements.txt' -o -name 'Cargo.toml' -o -name 'go.mod' -o -name 'Makefile' -o -name 'Dockerfile' -o -name 'lakefile.toml' -o -name 'lakefile.lean' -o -name 'lean-toolchain' -o -name '*.ipynb' -o -name '*.md' \) | sort | head -1000
  echo
  echo "workflows"
  find .github/workflows -type f 2>/dev/null | sort
} > "$OUT/inventory.txt" 2>&1

echo
echo "04 focused grep"
{
  echo "===== issue body ====="
  cat "$OUT/issue_body.md" 2>/dev/null || true

  echo
  echo "===== money/competition/judge hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=.lake --exclude-dir=node_modules --exclude-dir=target --exclude-dir=dist --exclude-dir=build \
    "prize|payment|cash|bounty|reward|competition|challenge|hackathon|leaderboard|submission|score|scoring|benchmark|metric|eval|evaluation|winner|deadline|golf|test|pytest|ci|workflow|acceptance|verifier|checker" . 2>/dev/null | head -3000

  echo
  echo "===== patch/search surface hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=.lake --exclude-dir=node_modules --exclude-dir=target --exclude-dir=dist --exclude-dir=build \
    "TODO|FIXME|bug|error|failing|regression|optimize|performance|proof|theorem|solver|search|constraint|correctness|validation|static|compile|type|Cannot find module" . 2>/dev/null | head -3000
} > "$OUT/grep.txt" 2>&1

echo
echo "05 cheap commands"
{
  echo "pwd=$(pwd)"
  echo
  if [ -f README.md ]; then
    echo "README head:"
    sed -n '1,220p' README.md
  fi
  if [ -f package.json ]; then
    echo
    echo "package scripts:"
    node -e 'const p=require("./package.json"); console.log(JSON.stringify(p.scripts||{},null,2))' 2>/dev/null || cat package.json | head -160
  fi
  if [ -f pyproject.toml ]; then
    echo
    echo "pyproject head:"
    sed -n '1,220p' pyproject.toml
  fi
  if [ -f Makefile ]; then
    echo
    echo "Makefile targets:"
    grep -nE "^[A-Za-z0-9_.-]+:" Makefile | head -80
  fi
  if [ -f lean-toolchain ]; then
    echo
    echo "lean-toolchain:"
    cat lean-toolchain
  fi
} > "$OUT/cheap_commands.txt" 2>&1

echo
echo "06 classify"
python3 - "$OUT" <<'PY2'
from pathlib import Path
import json, sys

out = Path(sys.argv[1])
issue = {}
try:
  issue = json.loads((out / "issue_summary.json").read_text())
except Exception:
  pass

body = (out / "issue_body.md").read_text(errors="replace") if (out / "issue_body.md").exists() else ""
comments = (out / "issue_comments.md").read_text(errors="replace") if (out / "issue_comments.md").exists() else ""
inv = (out / "inventory.txt").read_text(errors="replace") if (out / "inventory.txt").exists() else ""
grep = (out / "grep.txt").read_text(errors="replace") if (out / "grep.txt").exists() else ""
cheap = (out / "cheap_commands.txt").read_text(errors="replace") if (out / "cheap_commands.txt").exists() else ""
text = "\n".join([body, comments, inv, grep, cheap]).lower()

money = any(x in text for x in ["prize", "payment", "cash", "bounty", "reward", "paid", "$", "usd"])
competition = any(x in text for x in ["competition", "challenge", "hackathon", "leaderboard", "submission", "winner", "deadline", "code golf", "golf"])
judge = any(x in text for x in ["leaderboard", "submission", "score", "scoring", "benchmark", "metric", "eval", "evaluation", "test", "pytest", "ci", "workflow", "verifier", "checker", "acceptance"])
local = any(x in text for x in ["pytest", "npm test", "pnpm test", "yarn test", "cargo test", "go test", "make", "lake build", "benchmark", "python", "node"])
mgfit = any(x in text for x in ["lean", "proof", "theorem", "formal verification", "solver", "search", "constraint", "benchmark", "leaderboard", "optimization", "performance", "code golf", "correctness", "validation"])
risk = any(x in text for x in ["system prompt", "platform prompt", "jailbreak", "private key", "seed phrase", "wallet", "mainnet", "malware", "phishing", "casino", "gambling", "airdrop", "token"])

if risk:
  verdict = "PARK_RISK"
elif money and competition and judge and mgfit:
  verdict = "PROMOTE_COMPETITION_MONEY"
elif money and judge and local and mgfit:
  verdict = "PROMOTE_PAID_REPAIR"
elif competition and judge and mgfit:
  verdict = "PROMOTE_COMPETITION_REPUTATION_OR_PRIZE_UNKNOWN"
elif money and not judge:
  verdict = "ASK_FOR_JUDGE"
else:
  verdict = "PARK_WEAK"

decision = {
  "verdict": verdict,
  "issue": issue,
  "money": money,
  "competition": competition,
  "judge": judge,
  "local": local,
  "mgfit": mgfit,
  "risk": risk,
}

(out / "decision.json").write_text(json.dumps(decision, indent=2))

lines = []
lines.append("# Prize Recon Report")
lines.append("")
lines.append("## Verdict")
lines.append("")
lines.append("`" + verdict + "`")
lines.append("")
lines.append("## Decision")
lines.append("")
lines.append("JSON:")
lines.append(json.dumps(decision, indent=2))
lines.append("")
lines.append("## Cheap commands")
lines.append("")
lines.append(cheap[:10000])
lines.append("")
lines.append("## Issue body")
lines.append("")
lines.append(body[:12000])
lines.append("")
lines.append("## Comments")
lines.append("")
lines.append(comments[:8000])
lines.append("")
lines.append("## Inventory excerpt")
lines.append("")
lines.append(inv[:12000])
lines.append("")
lines.append("## Grep excerpt")
lines.append("")
lines.append(grep[:24000])
lines.append("")
(out / "REPORT.md").write_text("\n".join(lines) + "\n")
print((out / "REPORT.md").read_text()[:18000])
PY2

cd "$ROOT" || exit 1

echo
echo "===================================================================================================="
echo "RECON gittensor-vanguard/vanguarstew #662"
echo "===================================================================================================="

REPO_NAME="gittensor-vanguard/vanguarstew"
ISSUE_NUM="662"
SAFE="gittensor-vanguard__vanguarstew_662"
LOCAL_REPO="$ROOT/external/money_opportunity_scout_v4_prize_words/$SAFE"
OUT="$BASE_OUT/$SAFE"

mkdir -p "$OUT"
mkdir -p "$(dirname "$LOCAL_REPO")"

echo "01 issue"
gh issue view "$ISSUE_NUM" --repo "$REPO_NAME" --json number,title,state,url,labels,body,comments,updatedAt,createdAt \
  > "$OUT/issue.json" 2> "$OUT/issue.err" || true

python3 - "$OUT" <<'PY2'
from pathlib import Path
import json, sys
out = Path(sys.argv[1])
p = out / "issue.json"
if p.exists() and p.stat().st_size:
  j = json.loads(p.read_text())
  summary = {
    "url": j.get("url"),
    "title": j.get("title"),
    "state": j.get("state"),
    "labels": [x.get("name") for x in j.get("labels", [])],
    "comment_count": len(j.get("comments", [])),
    "updatedAt": j.get("updatedAt"),
  }
  (out / "issue_summary.json").write_text(json.dumps(summary, indent=2))
  (out / "issue_body.md").write_text(j.get("body") or "")
  (out / "issue_comments.md").write_text("\n---\n".join(
    "## " + str((c.get("author") or {}).get("login")) + " — " + str(c.get("createdAt")) + "\n\n" + str(c.get("body") or "")
    for c in j.get("comments", [])
  ))
  print(json.dumps(summary, indent=2))
else:
  print("issue view failed")
  print((out / "issue.err").read_text(errors="replace") if (out / "issue.err").exists() else "")
PY2

echo
echo "02 clone/update"
if [ ! -d "$LOCAL_REPO/.git" ]; then
  gh repo clone "$REPO_NAME" "$LOCAL_REPO" -- --filter=blob:none \
    > "$OUT/clone.log" 2>&1 || true
else
  echo "[exists] $LOCAL_REPO" | tee "$OUT/clone.log"
fi

if [ ! -d "$LOCAL_REPO/.git" ]; then
  echo "clone failed"
  cat "$OUT/clone.log"
  continue
fi

cd "$LOCAL_REPO" || continue
git fetch origin --prune > "$OUT/git_fetch.log" 2>&1 || true
DEFAULT_BRANCH="$(git remote show origin 2>/dev/null | awk '/HEAD branch/ {print $NF}' | head -1)"
if [ -z "$DEFAULT_BRANCH" ]; then DEFAULT_BRANCH="main"; fi
git checkout "$DEFAULT_BRANCH" > "$OUT/git_checkout.log" 2>&1 || true
git pull --ff-only origin "$DEFAULT_BRANCH" > "$OUT/git_pull.log" 2>&1 || true
git rev-parse HEAD | tee "$OUT/head.txt"

echo
echo "03 inventory"
{
  echo "top files"
  find . -maxdepth 4 -type f | sed 's#^./##' | sort | head -1200
  echo
  echo "build/test/competition files"
  find . -maxdepth 6 -type f \( -name 'README*' -o -name 'package.json' -o -name 'pyproject.toml' -o -name 'requirements.txt' -o -name 'Cargo.toml' -o -name 'go.mod' -o -name 'Makefile' -o -name 'Dockerfile' -o -name 'lakefile.toml' -o -name 'lakefile.lean' -o -name 'lean-toolchain' -o -name '*.ipynb' -o -name '*.md' \) | sort | head -1000
  echo
  echo "workflows"
  find .github/workflows -type f 2>/dev/null | sort
} > "$OUT/inventory.txt" 2>&1

echo
echo "04 focused grep"
{
  echo "===== issue body ====="
  cat "$OUT/issue_body.md" 2>/dev/null || true

  echo
  echo "===== money/competition/judge hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=.lake --exclude-dir=node_modules --exclude-dir=target --exclude-dir=dist --exclude-dir=build \
    "prize|payment|cash|bounty|reward|competition|challenge|hackathon|leaderboard|submission|score|scoring|benchmark|metric|eval|evaluation|winner|deadline|golf|test|pytest|ci|workflow|acceptance|verifier|checker" . 2>/dev/null | head -3000

  echo
  echo "===== patch/search surface hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=.lake --exclude-dir=node_modules --exclude-dir=target --exclude-dir=dist --exclude-dir=build \
    "TODO|FIXME|bug|error|failing|regression|optimize|performance|proof|theorem|solver|search|constraint|correctness|validation|static|compile|type|Cannot find module" . 2>/dev/null | head -3000
} > "$OUT/grep.txt" 2>&1

echo
echo "05 cheap commands"
{
  echo "pwd=$(pwd)"
  echo
  if [ -f README.md ]; then
    echo "README head:"
    sed -n '1,220p' README.md
  fi
  if [ -f package.json ]; then
    echo
    echo "package scripts:"
    node -e 'const p=require("./package.json"); console.log(JSON.stringify(p.scripts||{},null,2))' 2>/dev/null || cat package.json | head -160
  fi
  if [ -f pyproject.toml ]; then
    echo
    echo "pyproject head:"
    sed -n '1,220p' pyproject.toml
  fi
  if [ -f Makefile ]; then
    echo
    echo "Makefile targets:"
    grep -nE "^[A-Za-z0-9_.-]+:" Makefile | head -80
  fi
  if [ -f lean-toolchain ]; then
    echo
    echo "lean-toolchain:"
    cat lean-toolchain
  fi
} > "$OUT/cheap_commands.txt" 2>&1

echo
echo "06 classify"
python3 - "$OUT" <<'PY2'
from pathlib import Path
import json, sys

out = Path(sys.argv[1])
issue = {}
try:
  issue = json.loads((out / "issue_summary.json").read_text())
except Exception:
  pass

body = (out / "issue_body.md").read_text(errors="replace") if (out / "issue_body.md").exists() else ""
comments = (out / "issue_comments.md").read_text(errors="replace") if (out / "issue_comments.md").exists() else ""
inv = (out / "inventory.txt").read_text(errors="replace") if (out / "inventory.txt").exists() else ""
grep = (out / "grep.txt").read_text(errors="replace") if (out / "grep.txt").exists() else ""
cheap = (out / "cheap_commands.txt").read_text(errors="replace") if (out / "cheap_commands.txt").exists() else ""
text = "\n".join([body, comments, inv, grep, cheap]).lower()

money = any(x in text for x in ["prize", "payment", "cash", "bounty", "reward", "paid", "$", "usd"])
competition = any(x in text for x in ["competition", "challenge", "hackathon", "leaderboard", "submission", "winner", "deadline", "code golf", "golf"])
judge = any(x in text for x in ["leaderboard", "submission", "score", "scoring", "benchmark", "metric", "eval", "evaluation", "test", "pytest", "ci", "workflow", "verifier", "checker", "acceptance"])
local = any(x in text for x in ["pytest", "npm test", "pnpm test", "yarn test", "cargo test", "go test", "make", "lake build", "benchmark", "python", "node"])
mgfit = any(x in text for x in ["lean", "proof", "theorem", "formal verification", "solver", "search", "constraint", "benchmark", "leaderboard", "optimization", "performance", "code golf", "correctness", "validation"])
risk = any(x in text for x in ["system prompt", "platform prompt", "jailbreak", "private key", "seed phrase", "wallet", "mainnet", "malware", "phishing", "casino", "gambling", "airdrop", "token"])

if risk:
  verdict = "PARK_RISK"
elif money and competition and judge and mgfit:
  verdict = "PROMOTE_COMPETITION_MONEY"
elif money and judge and local and mgfit:
  verdict = "PROMOTE_PAID_REPAIR"
elif competition and judge and mgfit:
  verdict = "PROMOTE_COMPETITION_REPUTATION_OR_PRIZE_UNKNOWN"
elif money and not judge:
  verdict = "ASK_FOR_JUDGE"
else:
  verdict = "PARK_WEAK"

decision = {
  "verdict": verdict,
  "issue": issue,
  "money": money,
  "competition": competition,
  "judge": judge,
  "local": local,
  "mgfit": mgfit,
  "risk": risk,
}

(out / "decision.json").write_text(json.dumps(decision, indent=2))

lines = []
lines.append("# Prize Recon Report")
lines.append("")
lines.append("## Verdict")
lines.append("")
lines.append("`" + verdict + "`")
lines.append("")
lines.append("## Decision")
lines.append("")
lines.append("JSON:")
lines.append(json.dumps(decision, indent=2))
lines.append("")
lines.append("## Cheap commands")
lines.append("")
lines.append(cheap[:10000])
lines.append("")
lines.append("## Issue body")
lines.append("")
lines.append(body[:12000])
lines.append("")
lines.append("## Comments")
lines.append("")
lines.append(comments[:8000])
lines.append("")
lines.append("## Inventory excerpt")
lines.append("")
lines.append(inv[:12000])
lines.append("")
lines.append("## Grep excerpt")
lines.append("")
lines.append(grep[:24000])
lines.append("")
(out / "REPORT.md").write_text("\n".join(lines) + "\n")
print((out / "REPORT.md").read_text()[:18000])
PY2

cd "$ROOT" || exit 1

echo
echo "===================================================================================================="
echo "RECON python-discord/sir-lancebot #1021"
echo "===================================================================================================="

REPO_NAME="python-discord/sir-lancebot"
ISSUE_NUM="1021"
SAFE="python-discord__sir-lancebot_1021"
LOCAL_REPO="$ROOT/external/money_opportunity_scout_v4_prize_words/$SAFE"
OUT="$BASE_OUT/$SAFE"

mkdir -p "$OUT"
mkdir -p "$(dirname "$LOCAL_REPO")"

echo "01 issue"
gh issue view "$ISSUE_NUM" --repo "$REPO_NAME" --json number,title,state,url,labels,body,comments,updatedAt,createdAt \
  > "$OUT/issue.json" 2> "$OUT/issue.err" || true

python3 - "$OUT" <<'PY2'
from pathlib import Path
import json, sys
out = Path(sys.argv[1])
p = out / "issue.json"
if p.exists() and p.stat().st_size:
  j = json.loads(p.read_text())
  summary = {
    "url": j.get("url"),
    "title": j.get("title"),
    "state": j.get("state"),
    "labels": [x.get("name") for x in j.get("labels", [])],
    "comment_count": len(j.get("comments", [])),
    "updatedAt": j.get("updatedAt"),
  }
  (out / "issue_summary.json").write_text(json.dumps(summary, indent=2))
  (out / "issue_body.md").write_text(j.get("body") or "")
  (out / "issue_comments.md").write_text("\n---\n".join(
    "## " + str((c.get("author") or {}).get("login")) + " — " + str(c.get("createdAt")) + "\n\n" + str(c.get("body") or "")
    for c in j.get("comments", [])
  ))
  print(json.dumps(summary, indent=2))
else:
  print("issue view failed")
  print((out / "issue.err").read_text(errors="replace") if (out / "issue.err").exists() else "")
PY2

echo
echo "02 clone/update"
if [ ! -d "$LOCAL_REPO/.git" ]; then
  gh repo clone "$REPO_NAME" "$LOCAL_REPO" -- --filter=blob:none \
    > "$OUT/clone.log" 2>&1 || true
else
  echo "[exists] $LOCAL_REPO" | tee "$OUT/clone.log"
fi

if [ ! -d "$LOCAL_REPO/.git" ]; then
  echo "clone failed"
  cat "$OUT/clone.log"
  continue
fi

cd "$LOCAL_REPO" || continue
git fetch origin --prune > "$OUT/git_fetch.log" 2>&1 || true
DEFAULT_BRANCH="$(git remote show origin 2>/dev/null | awk '/HEAD branch/ {print $NF}' | head -1)"
if [ -z "$DEFAULT_BRANCH" ]; then DEFAULT_BRANCH="main"; fi
git checkout "$DEFAULT_BRANCH" > "$OUT/git_checkout.log" 2>&1 || true
git pull --ff-only origin "$DEFAULT_BRANCH" > "$OUT/git_pull.log" 2>&1 || true
git rev-parse HEAD | tee "$OUT/head.txt"

echo
echo "03 inventory"
{
  echo "top files"
  find . -maxdepth 4 -type f | sed 's#^./##' | sort | head -1200
  echo
  echo "build/test/competition files"
  find . -maxdepth 6 -type f \( -name 'README*' -o -name 'package.json' -o -name 'pyproject.toml' -o -name 'requirements.txt' -o -name 'Cargo.toml' -o -name 'go.mod' -o -name 'Makefile' -o -name 'Dockerfile' -o -name 'lakefile.toml' -o -name 'lakefile.lean' -o -name 'lean-toolchain' -o -name '*.ipynb' -o -name '*.md' \) | sort | head -1000
  echo
  echo "workflows"
  find .github/workflows -type f 2>/dev/null | sort
} > "$OUT/inventory.txt" 2>&1

echo
echo "04 focused grep"
{
  echo "===== issue body ====="
  cat "$OUT/issue_body.md" 2>/dev/null || true

  echo
  echo "===== money/competition/judge hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=.lake --exclude-dir=node_modules --exclude-dir=target --exclude-dir=dist --exclude-dir=build \
    "prize|payment|cash|bounty|reward|competition|challenge|hackathon|leaderboard|submission|score|scoring|benchmark|metric|eval|evaluation|winner|deadline|golf|test|pytest|ci|workflow|acceptance|verifier|checker" . 2>/dev/null | head -3000

  echo
  echo "===== patch/search surface hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=.lake --exclude-dir=node_modules --exclude-dir=target --exclude-dir=dist --exclude-dir=build \
    "TODO|FIXME|bug|error|failing|regression|optimize|performance|proof|theorem|solver|search|constraint|correctness|validation|static|compile|type|Cannot find module" . 2>/dev/null | head -3000
} > "$OUT/grep.txt" 2>&1

echo
echo "05 cheap commands"
{
  echo "pwd=$(pwd)"
  echo
  if [ -f README.md ]; then
    echo "README head:"
    sed -n '1,220p' README.md
  fi
  if [ -f package.json ]; then
    echo
    echo "package scripts:"
    node -e 'const p=require("./package.json"); console.log(JSON.stringify(p.scripts||{},null,2))' 2>/dev/null || cat package.json | head -160
  fi
  if [ -f pyproject.toml ]; then
    echo
    echo "pyproject head:"
    sed -n '1,220p' pyproject.toml
  fi
  if [ -f Makefile ]; then
    echo
    echo "Makefile targets:"
    grep -nE "^[A-Za-z0-9_.-]+:" Makefile | head -80
  fi
  if [ -f lean-toolchain ]; then
    echo
    echo "lean-toolchain:"
    cat lean-toolchain
  fi
} > "$OUT/cheap_commands.txt" 2>&1

echo
echo "06 classify"
python3 - "$OUT" <<'PY2'
from pathlib import Path
import json, sys

out = Path(sys.argv[1])
issue = {}
try:
  issue = json.loads((out / "issue_summary.json").read_text())
except Exception:
  pass

body = (out / "issue_body.md").read_text(errors="replace") if (out / "issue_body.md").exists() else ""
comments = (out / "issue_comments.md").read_text(errors="replace") if (out / "issue_comments.md").exists() else ""
inv = (out / "inventory.txt").read_text(errors="replace") if (out / "inventory.txt").exists() else ""
grep = (out / "grep.txt").read_text(errors="replace") if (out / "grep.txt").exists() else ""
cheap = (out / "cheap_commands.txt").read_text(errors="replace") if (out / "cheap_commands.txt").exists() else ""
text = "\n".join([body, comments, inv, grep, cheap]).lower()

money = any(x in text for x in ["prize", "payment", "cash", "bounty", "reward", "paid", "$", "usd"])
competition = any(x in text for x in ["competition", "challenge", "hackathon", "leaderboard", "submission", "winner", "deadline", "code golf", "golf"])
judge = any(x in text for x in ["leaderboard", "submission", "score", "scoring", "benchmark", "metric", "eval", "evaluation", "test", "pytest", "ci", "workflow", "verifier", "checker", "acceptance"])
local = any(x in text for x in ["pytest", "npm test", "pnpm test", "yarn test", "cargo test", "go test", "make", "lake build", "benchmark", "python", "node"])
mgfit = any(x in text for x in ["lean", "proof", "theorem", "formal verification", "solver", "search", "constraint", "benchmark", "leaderboard", "optimization", "performance", "code golf", "correctness", "validation"])
risk = any(x in text for x in ["system prompt", "platform prompt", "jailbreak", "private key", "seed phrase", "wallet", "mainnet", "malware", "phishing", "casino", "gambling", "airdrop", "token"])

if risk:
  verdict = "PARK_RISK"
elif money and competition and judge and mgfit:
  verdict = "PROMOTE_COMPETITION_MONEY"
elif money and judge and local and mgfit:
  verdict = "PROMOTE_PAID_REPAIR"
elif competition and judge and mgfit:
  verdict = "PROMOTE_COMPETITION_REPUTATION_OR_PRIZE_UNKNOWN"
elif money and not judge:
  verdict = "ASK_FOR_JUDGE"
else:
  verdict = "PARK_WEAK"

decision = {
  "verdict": verdict,
  "issue": issue,
  "money": money,
  "competition": competition,
  "judge": judge,
  "local": local,
  "mgfit": mgfit,
  "risk": risk,
}

(out / "decision.json").write_text(json.dumps(decision, indent=2))

lines = []
lines.append("# Prize Recon Report")
lines.append("")
lines.append("## Verdict")
lines.append("")
lines.append("`" + verdict + "`")
lines.append("")
lines.append("## Decision")
lines.append("")
lines.append("JSON:")
lines.append(json.dumps(decision, indent=2))
lines.append("")
lines.append("## Cheap commands")
lines.append("")
lines.append(cheap[:10000])
lines.append("")
lines.append("## Issue body")
lines.append("")
lines.append(body[:12000])
lines.append("")
lines.append("## Comments")
lines.append("")
lines.append(comments[:8000])
lines.append("")
lines.append("## Inventory excerpt")
lines.append("")
lines.append(inv[:12000])
lines.append("")
lines.append("## Grep excerpt")
lines.append("")
lines.append(grep[:24000])
lines.append("")
(out / "REPORT.md").write_text("\n".join(lines) + "\n")
print((out / "REPORT.md").read_text()[:18000])
PY2

cd "$ROOT" || exit 1
