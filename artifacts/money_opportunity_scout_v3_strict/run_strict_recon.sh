#!/usr/bin/env bash
set -u

ROOT="/Users/heath/Documents/mathgraph-lean-work"
BASE_OUT="$ROOT/artifacts/money_opportunity_scout_v3_strict/recon"
mkdir -p "$BASE_OUT"
cd "$ROOT" || exit 1

echo "MathGraph strict money recon"
echo

echo
echo "===================================================================================================="
echo "RECON SporkDAOOfficial/ETHDenver-2023 #161"
echo "===================================================================================================="

REPO_NAME="SporkDAOOfficial/ETHDenver-2023"
ISSUE_NUM="161"
SAFE="SporkDAOOfficial__ETHDenver-2023_161"
LOCAL_REPO="$ROOT/external/money_opportunity_scout_v3_strict/$SAFE"
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
  find . -maxdepth 4 -type f | sed 's#^./##' | sort | head -1000
  echo
  echo "build/test files"
  find . -maxdepth 6 -type f \( -name 'lakefile.toml' -o -name 'lakefile.lean' -o -name 'lean-toolchain' -o -name 'package.json' -o -name 'pnpm-lock.yaml' -o -name 'yarn.lock' -o -name 'package-lock.json' -o -name 'pyproject.toml' -o -name 'requirements.txt' -o -name 'Cargo.toml' -o -name 'go.mod' -o -name 'Makefile' -o -name 'README*' \) | sort
  echo
  echo "workflows"
  find .github/workflows -type f 2>/dev/null | sort
} > "$OUT/inventory.txt" 2>&1

echo
echo "04 grep focused"
{
  echo "===== issue terms ====="
  cat "$OUT/issue_body.md" 2>/dev/null || true

  echo
  echo "===== judge hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=.lake --exclude-dir=node_modules --exclude-dir=target --exclude-dir=dist --exclude-dir=build \
    "pytest|unittest|vitest|jest|npm test|pnpm test|yarn test|cargo test|go test|make test|lake build|benchmark|criterion|CI|workflow|acceptance|failing|regression|Cannot find module|static export|output: export|github pages|pages artifact" . 2>/dev/null | head -2500

  echo
  echo "===== patch surface hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=.lake --exclude-dir=node_modules --exclude-dir=target --exclude-dir=dist --exclude-dir=build \
    "TODO|FIXME|validate|validation|proof|theorem|invariant|correctness|performance|optimize|bug|error|failing|regression|static export|dynamic|api route|Cannot find module|Pages" . 2>/dev/null | head -2500
} > "$OUT/grep.txt" 2>&1

echo
echo "05 local cheap commands"
{
  echo "pwd=$(pwd)"
  echo
  if [ -f package.json ]; then
    echo "root package.json scripts:"
    node -e 'const p=require("./package.json"); console.log(JSON.stringify(p.scripts||{},null,2))' 2>/dev/null || cat package.json | head -120
  fi
  if [ -f aria-frontend/package.json ]; then
    echo
    echo "aria-frontend package.json scripts:"
    node -e 'const p=require("./aria-frontend/package.json"); console.log(JSON.stringify(p.scripts||{},null,2))' 2>/dev/null || cat aria-frontend/package.json | head -120
  fi
  if [ -f lean-toolchain ]; then
    echo
    echo "lean-toolchain:"
    cat lean-toolchain
  fi
  if [ -f lakefile.toml ] || [ -f lakefile.lean ]; then
    echo
    echo "lake build available"
  fi
} > "$OUT/cheap_commands.txt" 2>&1

echo
echo "06 classify manual"
python3 - "$OUT" <<'PY2'
from pathlib import Path
import json, sys, re

out = Path(sys.argv[1])
issue = {}
try:
  issue = json.loads((out / "issue_summary.json").read_text())
except Exception:
  pass

body = (out / "issue_body.md").read_text(errors="replace") if (out / "issue_body.md").exists() else ""
inv = (out / "inventory.txt").read_text(errors="replace") if (out / "inventory.txt").exists() else ""
grep = (out / "grep.txt").read_text(errors="replace") if (out / "grep.txt").exists() else ""
cheap = (out / "cheap_commands.txt").read_text(errors="replace") if (out / "cheap_commands.txt").exists() else ""
text = "\n".join([body, inv, grep, cheap]).lower()

has_explicit_acceptance = "acceptance criteria" in text or "acceptance" in text
has_local_command = any(x in text for x in ["npm test", "pnpm test", "yarn test", "pytest", "cargo test", "go test", "lake build", "benchmark"])
has_ci = ".github/workflows" in text or "github actions" in text or "workflow" in text
has_concrete_error = any(x in text for x in ["cannot find module", "static export", "failing", "build fails", "regression", "error"])
has_money = any(x in text for x in ["bounty", "reward", "paid", "usd", "$"])
risk = any(x in text for x in ["system prompt", "private key", "seed phrase", "jailbreak", "malware", "phishing", "token", "wallet", "mainnet"])

if risk:
  verdict = "PARK_RISK"
elif has_money and has_explicit_acceptance and (has_local_command or has_ci) and has_concrete_error:
  verdict = "PATCH_CANDIDATE"
elif has_money and (has_local_command or has_ci) and has_concrete_error:
  verdict = "RECON_CANDIDATE"
elif has_money:
  verdict = "ASK_FOR_VERIFIER_OR_PARK"
else:
  verdict = "PARK_NO_MONEY"

decision = {
  "verdict": verdict,
  "issue": issue,
  "has_explicit_acceptance": has_explicit_acceptance,
  "has_local_command": has_local_command,
  "has_ci": has_ci,
  "has_concrete_error": has_concrete_error,
  "has_money": has_money,
  "risk": risk,
}

(out / "decision.json").write_text(json.dumps(decision, indent=2))

lines = []
lines.append("# Strict Recon Report")
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
lines.append(cheap[:8000])
lines.append("")
lines.append("## Issue body")
lines.append("")
lines.append(body[:10000])
lines.append("")
lines.append("## Inventory excerpt")
lines.append("")
lines.append(inv[:10000])
lines.append("")
lines.append("## Grep excerpt")
lines.append("")
lines.append(grep[:20000])
lines.append("")
(out / "REPORT.md").write_text("\n".join(lines) + "\n")
print((out / "REPORT.md").read_text()[:16000])
PY2

cd "$ROOT" || exit 1

echo
echo "===================================================================================================="
echo "RECON SporkDAOOfficial/ETHDenver-2023 #162"
echo "===================================================================================================="

REPO_NAME="SporkDAOOfficial/ETHDenver-2023"
ISSUE_NUM="162"
SAFE="SporkDAOOfficial__ETHDenver-2023_162"
LOCAL_REPO="$ROOT/external/money_opportunity_scout_v3_strict/$SAFE"
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
  find . -maxdepth 4 -type f | sed 's#^./##' | sort | head -1000
  echo
  echo "build/test files"
  find . -maxdepth 6 -type f \( -name 'lakefile.toml' -o -name 'lakefile.lean' -o -name 'lean-toolchain' -o -name 'package.json' -o -name 'pnpm-lock.yaml' -o -name 'yarn.lock' -o -name 'package-lock.json' -o -name 'pyproject.toml' -o -name 'requirements.txt' -o -name 'Cargo.toml' -o -name 'go.mod' -o -name 'Makefile' -o -name 'README*' \) | sort
  echo
  echo "workflows"
  find .github/workflows -type f 2>/dev/null | sort
} > "$OUT/inventory.txt" 2>&1

echo
echo "04 grep focused"
{
  echo "===== issue terms ====="
  cat "$OUT/issue_body.md" 2>/dev/null || true

  echo
  echo "===== judge hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=.lake --exclude-dir=node_modules --exclude-dir=target --exclude-dir=dist --exclude-dir=build \
    "pytest|unittest|vitest|jest|npm test|pnpm test|yarn test|cargo test|go test|make test|lake build|benchmark|criterion|CI|workflow|acceptance|failing|regression|Cannot find module|static export|output: export|github pages|pages artifact" . 2>/dev/null | head -2500

  echo
  echo "===== patch surface hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=.lake --exclude-dir=node_modules --exclude-dir=target --exclude-dir=dist --exclude-dir=build \
    "TODO|FIXME|validate|validation|proof|theorem|invariant|correctness|performance|optimize|bug|error|failing|regression|static export|dynamic|api route|Cannot find module|Pages" . 2>/dev/null | head -2500
} > "$OUT/grep.txt" 2>&1

echo
echo "05 local cheap commands"
{
  echo "pwd=$(pwd)"
  echo
  if [ -f package.json ]; then
    echo "root package.json scripts:"
    node -e 'const p=require("./package.json"); console.log(JSON.stringify(p.scripts||{},null,2))' 2>/dev/null || cat package.json | head -120
  fi
  if [ -f aria-frontend/package.json ]; then
    echo
    echo "aria-frontend package.json scripts:"
    node -e 'const p=require("./aria-frontend/package.json"); console.log(JSON.stringify(p.scripts||{},null,2))' 2>/dev/null || cat aria-frontend/package.json | head -120
  fi
  if [ -f lean-toolchain ]; then
    echo
    echo "lean-toolchain:"
    cat lean-toolchain
  fi
  if [ -f lakefile.toml ] || [ -f lakefile.lean ]; then
    echo
    echo "lake build available"
  fi
} > "$OUT/cheap_commands.txt" 2>&1

echo
echo "06 classify manual"
python3 - "$OUT" <<'PY2'
from pathlib import Path
import json, sys, re

out = Path(sys.argv[1])
issue = {}
try:
  issue = json.loads((out / "issue_summary.json").read_text())
except Exception:
  pass

body = (out / "issue_body.md").read_text(errors="replace") if (out / "issue_body.md").exists() else ""
inv = (out / "inventory.txt").read_text(errors="replace") if (out / "inventory.txt").exists() else ""
grep = (out / "grep.txt").read_text(errors="replace") if (out / "grep.txt").exists() else ""
cheap = (out / "cheap_commands.txt").read_text(errors="replace") if (out / "cheap_commands.txt").exists() else ""
text = "\n".join([body, inv, grep, cheap]).lower()

has_explicit_acceptance = "acceptance criteria" in text or "acceptance" in text
has_local_command = any(x in text for x in ["npm test", "pnpm test", "yarn test", "pytest", "cargo test", "go test", "lake build", "benchmark"])
has_ci = ".github/workflows" in text or "github actions" in text or "workflow" in text
has_concrete_error = any(x in text for x in ["cannot find module", "static export", "failing", "build fails", "regression", "error"])
has_money = any(x in text for x in ["bounty", "reward", "paid", "usd", "$"])
risk = any(x in text for x in ["system prompt", "private key", "seed phrase", "jailbreak", "malware", "phishing", "token", "wallet", "mainnet"])

if risk:
  verdict = "PARK_RISK"
elif has_money and has_explicit_acceptance and (has_local_command or has_ci) and has_concrete_error:
  verdict = "PATCH_CANDIDATE"
elif has_money and (has_local_command or has_ci) and has_concrete_error:
  verdict = "RECON_CANDIDATE"
elif has_money:
  verdict = "ASK_FOR_VERIFIER_OR_PARK"
else:
  verdict = "PARK_NO_MONEY"

decision = {
  "verdict": verdict,
  "issue": issue,
  "has_explicit_acceptance": has_explicit_acceptance,
  "has_local_command": has_local_command,
  "has_ci": has_ci,
  "has_concrete_error": has_concrete_error,
  "has_money": has_money,
  "risk": risk,
}

(out / "decision.json").write_text(json.dumps(decision, indent=2))

lines = []
lines.append("# Strict Recon Report")
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
lines.append(cheap[:8000])
lines.append("")
lines.append("## Issue body")
lines.append("")
lines.append(body[:10000])
lines.append("")
lines.append("## Inventory excerpt")
lines.append("")
lines.append(inv[:10000])
lines.append("")
lines.append("## Grep excerpt")
lines.append("")
lines.append(grep[:20000])
lines.append("")
(out / "REPORT.md").write_text("\n".join(lines) + "\n")
print((out / "REPORT.md").read_text()[:16000])
PY2

cd "$ROOT" || exit 1

echo
echo "===================================================================================================="
echo "RECON SporkDAOOfficial/ETHDenver-2023 #159"
echo "===================================================================================================="

REPO_NAME="SporkDAOOfficial/ETHDenver-2023"
ISSUE_NUM="159"
SAFE="SporkDAOOfficial__ETHDenver-2023_159"
LOCAL_REPO="$ROOT/external/money_opportunity_scout_v3_strict/$SAFE"
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
  find . -maxdepth 4 -type f | sed 's#^./##' | sort | head -1000
  echo
  echo "build/test files"
  find . -maxdepth 6 -type f \( -name 'lakefile.toml' -o -name 'lakefile.lean' -o -name 'lean-toolchain' -o -name 'package.json' -o -name 'pnpm-lock.yaml' -o -name 'yarn.lock' -o -name 'package-lock.json' -o -name 'pyproject.toml' -o -name 'requirements.txt' -o -name 'Cargo.toml' -o -name 'go.mod' -o -name 'Makefile' -o -name 'README*' \) | sort
  echo
  echo "workflows"
  find .github/workflows -type f 2>/dev/null | sort
} > "$OUT/inventory.txt" 2>&1

echo
echo "04 grep focused"
{
  echo "===== issue terms ====="
  cat "$OUT/issue_body.md" 2>/dev/null || true

  echo
  echo "===== judge hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=.lake --exclude-dir=node_modules --exclude-dir=target --exclude-dir=dist --exclude-dir=build \
    "pytest|unittest|vitest|jest|npm test|pnpm test|yarn test|cargo test|go test|make test|lake build|benchmark|criterion|CI|workflow|acceptance|failing|regression|Cannot find module|static export|output: export|github pages|pages artifact" . 2>/dev/null | head -2500

  echo
  echo "===== patch surface hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=.lake --exclude-dir=node_modules --exclude-dir=target --exclude-dir=dist --exclude-dir=build \
    "TODO|FIXME|validate|validation|proof|theorem|invariant|correctness|performance|optimize|bug|error|failing|regression|static export|dynamic|api route|Cannot find module|Pages" . 2>/dev/null | head -2500
} > "$OUT/grep.txt" 2>&1

echo
echo "05 local cheap commands"
{
  echo "pwd=$(pwd)"
  echo
  if [ -f package.json ]; then
    echo "root package.json scripts:"
    node -e 'const p=require("./package.json"); console.log(JSON.stringify(p.scripts||{},null,2))' 2>/dev/null || cat package.json | head -120
  fi
  if [ -f aria-frontend/package.json ]; then
    echo
    echo "aria-frontend package.json scripts:"
    node -e 'const p=require("./aria-frontend/package.json"); console.log(JSON.stringify(p.scripts||{},null,2))' 2>/dev/null || cat aria-frontend/package.json | head -120
  fi
  if [ -f lean-toolchain ]; then
    echo
    echo "lean-toolchain:"
    cat lean-toolchain
  fi
  if [ -f lakefile.toml ] || [ -f lakefile.lean ]; then
    echo
    echo "lake build available"
  fi
} > "$OUT/cheap_commands.txt" 2>&1

echo
echo "06 classify manual"
python3 - "$OUT" <<'PY2'
from pathlib import Path
import json, sys, re

out = Path(sys.argv[1])
issue = {}
try:
  issue = json.loads((out / "issue_summary.json").read_text())
except Exception:
  pass

body = (out / "issue_body.md").read_text(errors="replace") if (out / "issue_body.md").exists() else ""
inv = (out / "inventory.txt").read_text(errors="replace") if (out / "inventory.txt").exists() else ""
grep = (out / "grep.txt").read_text(errors="replace") if (out / "grep.txt").exists() else ""
cheap = (out / "cheap_commands.txt").read_text(errors="replace") if (out / "cheap_commands.txt").exists() else ""
text = "\n".join([body, inv, grep, cheap]).lower()

has_explicit_acceptance = "acceptance criteria" in text or "acceptance" in text
has_local_command = any(x in text for x in ["npm test", "pnpm test", "yarn test", "pytest", "cargo test", "go test", "lake build", "benchmark"])
has_ci = ".github/workflows" in text or "github actions" in text or "workflow" in text
has_concrete_error = any(x in text for x in ["cannot find module", "static export", "failing", "build fails", "regression", "error"])
has_money = any(x in text for x in ["bounty", "reward", "paid", "usd", "$"])
risk = any(x in text for x in ["system prompt", "private key", "seed phrase", "jailbreak", "malware", "phishing", "token", "wallet", "mainnet"])

if risk:
  verdict = "PARK_RISK"
elif has_money and has_explicit_acceptance and (has_local_command or has_ci) and has_concrete_error:
  verdict = "PATCH_CANDIDATE"
elif has_money and (has_local_command or has_ci) and has_concrete_error:
  verdict = "RECON_CANDIDATE"
elif has_money:
  verdict = "ASK_FOR_VERIFIER_OR_PARK"
else:
  verdict = "PARK_NO_MONEY"

decision = {
  "verdict": verdict,
  "issue": issue,
  "has_explicit_acceptance": has_explicit_acceptance,
  "has_local_command": has_local_command,
  "has_ci": has_ci,
  "has_concrete_error": has_concrete_error,
  "has_money": has_money,
  "risk": risk,
}

(out / "decision.json").write_text(json.dumps(decision, indent=2))

lines = []
lines.append("# Strict Recon Report")
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
lines.append(cheap[:8000])
lines.append("")
lines.append("## Issue body")
lines.append("")
lines.append(body[:10000])
lines.append("")
lines.append("## Inventory excerpt")
lines.append("")
lines.append(inv[:10000])
lines.append("")
lines.append("## Grep excerpt")
lines.append("")
lines.append(grep[:20000])
lines.append("")
(out / "REPORT.md").write_text("\n".join(lines) + "\n")
print((out / "REPORT.md").read_text()[:16000])
PY2

cd "$ROOT" || exit 1

echo
echo "===================================================================================================="
echo "RECON SporkDAOOfficial/ETHDenver-2023 #160"
echo "===================================================================================================="

REPO_NAME="SporkDAOOfficial/ETHDenver-2023"
ISSUE_NUM="160"
SAFE="SporkDAOOfficial__ETHDenver-2023_160"
LOCAL_REPO="$ROOT/external/money_opportunity_scout_v3_strict/$SAFE"
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
  find . -maxdepth 4 -type f | sed 's#^./##' | sort | head -1000
  echo
  echo "build/test files"
  find . -maxdepth 6 -type f \( -name 'lakefile.toml' -o -name 'lakefile.lean' -o -name 'lean-toolchain' -o -name 'package.json' -o -name 'pnpm-lock.yaml' -o -name 'yarn.lock' -o -name 'package-lock.json' -o -name 'pyproject.toml' -o -name 'requirements.txt' -o -name 'Cargo.toml' -o -name 'go.mod' -o -name 'Makefile' -o -name 'README*' \) | sort
  echo
  echo "workflows"
  find .github/workflows -type f 2>/dev/null | sort
} > "$OUT/inventory.txt" 2>&1

echo
echo "04 grep focused"
{
  echo "===== issue terms ====="
  cat "$OUT/issue_body.md" 2>/dev/null || true

  echo
  echo "===== judge hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=.lake --exclude-dir=node_modules --exclude-dir=target --exclude-dir=dist --exclude-dir=build \
    "pytest|unittest|vitest|jest|npm test|pnpm test|yarn test|cargo test|go test|make test|lake build|benchmark|criterion|CI|workflow|acceptance|failing|regression|Cannot find module|static export|output: export|github pages|pages artifact" . 2>/dev/null | head -2500

  echo
  echo "===== patch surface hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=.lake --exclude-dir=node_modules --exclude-dir=target --exclude-dir=dist --exclude-dir=build \
    "TODO|FIXME|validate|validation|proof|theorem|invariant|correctness|performance|optimize|bug|error|failing|regression|static export|dynamic|api route|Cannot find module|Pages" . 2>/dev/null | head -2500
} > "$OUT/grep.txt" 2>&1

echo
echo "05 local cheap commands"
{
  echo "pwd=$(pwd)"
  echo
  if [ -f package.json ]; then
    echo "root package.json scripts:"
    node -e 'const p=require("./package.json"); console.log(JSON.stringify(p.scripts||{},null,2))' 2>/dev/null || cat package.json | head -120
  fi
  if [ -f aria-frontend/package.json ]; then
    echo
    echo "aria-frontend package.json scripts:"
    node -e 'const p=require("./aria-frontend/package.json"); console.log(JSON.stringify(p.scripts||{},null,2))' 2>/dev/null || cat aria-frontend/package.json | head -120
  fi
  if [ -f lean-toolchain ]; then
    echo
    echo "lean-toolchain:"
    cat lean-toolchain
  fi
  if [ -f lakefile.toml ] || [ -f lakefile.lean ]; then
    echo
    echo "lake build available"
  fi
} > "$OUT/cheap_commands.txt" 2>&1

echo
echo "06 classify manual"
python3 - "$OUT" <<'PY2'
from pathlib import Path
import json, sys, re

out = Path(sys.argv[1])
issue = {}
try:
  issue = json.loads((out / "issue_summary.json").read_text())
except Exception:
  pass

body = (out / "issue_body.md").read_text(errors="replace") if (out / "issue_body.md").exists() else ""
inv = (out / "inventory.txt").read_text(errors="replace") if (out / "inventory.txt").exists() else ""
grep = (out / "grep.txt").read_text(errors="replace") if (out / "grep.txt").exists() else ""
cheap = (out / "cheap_commands.txt").read_text(errors="replace") if (out / "cheap_commands.txt").exists() else ""
text = "\n".join([body, inv, grep, cheap]).lower()

has_explicit_acceptance = "acceptance criteria" in text or "acceptance" in text
has_local_command = any(x in text for x in ["npm test", "pnpm test", "yarn test", "pytest", "cargo test", "go test", "lake build", "benchmark"])
has_ci = ".github/workflows" in text or "github actions" in text or "workflow" in text
has_concrete_error = any(x in text for x in ["cannot find module", "static export", "failing", "build fails", "regression", "error"])
has_money = any(x in text for x in ["bounty", "reward", "paid", "usd", "$"])
risk = any(x in text for x in ["system prompt", "private key", "seed phrase", "jailbreak", "malware", "phishing", "token", "wallet", "mainnet"])

if risk:
  verdict = "PARK_RISK"
elif has_money and has_explicit_acceptance and (has_local_command or has_ci) and has_concrete_error:
  verdict = "PATCH_CANDIDATE"
elif has_money and (has_local_command or has_ci) and has_concrete_error:
  verdict = "RECON_CANDIDATE"
elif has_money:
  verdict = "ASK_FOR_VERIFIER_OR_PARK"
else:
  verdict = "PARK_NO_MONEY"

decision = {
  "verdict": verdict,
  "issue": issue,
  "has_explicit_acceptance": has_explicit_acceptance,
  "has_local_command": has_local_command,
  "has_ci": has_ci,
  "has_concrete_error": has_concrete_error,
  "has_money": has_money,
  "risk": risk,
}

(out / "decision.json").write_text(json.dumps(decision, indent=2))

lines = []
lines.append("# Strict Recon Report")
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
lines.append(cheap[:8000])
lines.append("")
lines.append("## Issue body")
lines.append("")
lines.append(body[:10000])
lines.append("")
lines.append("## Inventory excerpt")
lines.append("")
lines.append(inv[:10000])
lines.append("")
lines.append("## Grep excerpt")
lines.append("")
lines.append(grep[:20000])
lines.append("")
(out / "REPORT.md").write_text("\n".join(lines) + "\n")
print((out / "REPORT.md").read_text()[:16000])
PY2

cd "$ROOT" || exit 1

echo
echo "===================================================================================================="
echo "RECON ClankerNation/OpenAgents #43"
echo "===================================================================================================="

REPO_NAME="ClankerNation/OpenAgents"
ISSUE_NUM="43"
SAFE="ClankerNation__OpenAgents_43"
LOCAL_REPO="$ROOT/external/money_opportunity_scout_v3_strict/$SAFE"
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
  find . -maxdepth 4 -type f | sed 's#^./##' | sort | head -1000
  echo
  echo "build/test files"
  find . -maxdepth 6 -type f \( -name 'lakefile.toml' -o -name 'lakefile.lean' -o -name 'lean-toolchain' -o -name 'package.json' -o -name 'pnpm-lock.yaml' -o -name 'yarn.lock' -o -name 'package-lock.json' -o -name 'pyproject.toml' -o -name 'requirements.txt' -o -name 'Cargo.toml' -o -name 'go.mod' -o -name 'Makefile' -o -name 'README*' \) | sort
  echo
  echo "workflows"
  find .github/workflows -type f 2>/dev/null | sort
} > "$OUT/inventory.txt" 2>&1

echo
echo "04 grep focused"
{
  echo "===== issue terms ====="
  cat "$OUT/issue_body.md" 2>/dev/null || true

  echo
  echo "===== judge hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=.lake --exclude-dir=node_modules --exclude-dir=target --exclude-dir=dist --exclude-dir=build \
    "pytest|unittest|vitest|jest|npm test|pnpm test|yarn test|cargo test|go test|make test|lake build|benchmark|criterion|CI|workflow|acceptance|failing|regression|Cannot find module|static export|output: export|github pages|pages artifact" . 2>/dev/null | head -2500

  echo
  echo "===== patch surface hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=.lake --exclude-dir=node_modules --exclude-dir=target --exclude-dir=dist --exclude-dir=build \
    "TODO|FIXME|validate|validation|proof|theorem|invariant|correctness|performance|optimize|bug|error|failing|regression|static export|dynamic|api route|Cannot find module|Pages" . 2>/dev/null | head -2500
} > "$OUT/grep.txt" 2>&1

echo
echo "05 local cheap commands"
{
  echo "pwd=$(pwd)"
  echo
  if [ -f package.json ]; then
    echo "root package.json scripts:"
    node -e 'const p=require("./package.json"); console.log(JSON.stringify(p.scripts||{},null,2))' 2>/dev/null || cat package.json | head -120
  fi
  if [ -f aria-frontend/package.json ]; then
    echo
    echo "aria-frontend package.json scripts:"
    node -e 'const p=require("./aria-frontend/package.json"); console.log(JSON.stringify(p.scripts||{},null,2))' 2>/dev/null || cat aria-frontend/package.json | head -120
  fi
  if [ -f lean-toolchain ]; then
    echo
    echo "lean-toolchain:"
    cat lean-toolchain
  fi
  if [ -f lakefile.toml ] || [ -f lakefile.lean ]; then
    echo
    echo "lake build available"
  fi
} > "$OUT/cheap_commands.txt" 2>&1

echo
echo "06 classify manual"
python3 - "$OUT" <<'PY2'
from pathlib import Path
import json, sys, re

out = Path(sys.argv[1])
issue = {}
try:
  issue = json.loads((out / "issue_summary.json").read_text())
except Exception:
  pass

body = (out / "issue_body.md").read_text(errors="replace") if (out / "issue_body.md").exists() else ""
inv = (out / "inventory.txt").read_text(errors="replace") if (out / "inventory.txt").exists() else ""
grep = (out / "grep.txt").read_text(errors="replace") if (out / "grep.txt").exists() else ""
cheap = (out / "cheap_commands.txt").read_text(errors="replace") if (out / "cheap_commands.txt").exists() else ""
text = "\n".join([body, inv, grep, cheap]).lower()

has_explicit_acceptance = "acceptance criteria" in text or "acceptance" in text
has_local_command = any(x in text for x in ["npm test", "pnpm test", "yarn test", "pytest", "cargo test", "go test", "lake build", "benchmark"])
has_ci = ".github/workflows" in text or "github actions" in text or "workflow" in text
has_concrete_error = any(x in text for x in ["cannot find module", "static export", "failing", "build fails", "regression", "error"])
has_money = any(x in text for x in ["bounty", "reward", "paid", "usd", "$"])
risk = any(x in text for x in ["system prompt", "private key", "seed phrase", "jailbreak", "malware", "phishing", "token", "wallet", "mainnet"])

if risk:
  verdict = "PARK_RISK"
elif has_money and has_explicit_acceptance and (has_local_command or has_ci) and has_concrete_error:
  verdict = "PATCH_CANDIDATE"
elif has_money and (has_local_command or has_ci) and has_concrete_error:
  verdict = "RECON_CANDIDATE"
elif has_money:
  verdict = "ASK_FOR_VERIFIER_OR_PARK"
else:
  verdict = "PARK_NO_MONEY"

decision = {
  "verdict": verdict,
  "issue": issue,
  "has_explicit_acceptance": has_explicit_acceptance,
  "has_local_command": has_local_command,
  "has_ci": has_ci,
  "has_concrete_error": has_concrete_error,
  "has_money": has_money,
  "risk": risk,
}

(out / "decision.json").write_text(json.dumps(decision, indent=2))

lines = []
lines.append("# Strict Recon Report")
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
lines.append(cheap[:8000])
lines.append("")
lines.append("## Issue body")
lines.append("")
lines.append(body[:10000])
lines.append("")
lines.append("## Inventory excerpt")
lines.append("")
lines.append(inv[:10000])
lines.append("")
lines.append("## Grep excerpt")
lines.append("")
lines.append(grep[:20000])
lines.append("")
(out / "REPORT.md").write_text("\n".join(lines) + "\n")
print((out / "REPORT.md").read_text()[:16000])
PY2

cd "$ROOT" || exit 1

echo
echo "===================================================================================================="
echo "RECON ClankerNation/OpenAgents #59"
echo "===================================================================================================="

REPO_NAME="ClankerNation/OpenAgents"
ISSUE_NUM="59"
SAFE="ClankerNation__OpenAgents_59"
LOCAL_REPO="$ROOT/external/money_opportunity_scout_v3_strict/$SAFE"
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
  find . -maxdepth 4 -type f | sed 's#^./##' | sort | head -1000
  echo
  echo "build/test files"
  find . -maxdepth 6 -type f \( -name 'lakefile.toml' -o -name 'lakefile.lean' -o -name 'lean-toolchain' -o -name 'package.json' -o -name 'pnpm-lock.yaml' -o -name 'yarn.lock' -o -name 'package-lock.json' -o -name 'pyproject.toml' -o -name 'requirements.txt' -o -name 'Cargo.toml' -o -name 'go.mod' -o -name 'Makefile' -o -name 'README*' \) | sort
  echo
  echo "workflows"
  find .github/workflows -type f 2>/dev/null | sort
} > "$OUT/inventory.txt" 2>&1

echo
echo "04 grep focused"
{
  echo "===== issue terms ====="
  cat "$OUT/issue_body.md" 2>/dev/null || true

  echo
  echo "===== judge hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=.lake --exclude-dir=node_modules --exclude-dir=target --exclude-dir=dist --exclude-dir=build \
    "pytest|unittest|vitest|jest|npm test|pnpm test|yarn test|cargo test|go test|make test|lake build|benchmark|criterion|CI|workflow|acceptance|failing|regression|Cannot find module|static export|output: export|github pages|pages artifact" . 2>/dev/null | head -2500

  echo
  echo "===== patch surface hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=.lake --exclude-dir=node_modules --exclude-dir=target --exclude-dir=dist --exclude-dir=build \
    "TODO|FIXME|validate|validation|proof|theorem|invariant|correctness|performance|optimize|bug|error|failing|regression|static export|dynamic|api route|Cannot find module|Pages" . 2>/dev/null | head -2500
} > "$OUT/grep.txt" 2>&1

echo
echo "05 local cheap commands"
{
  echo "pwd=$(pwd)"
  echo
  if [ -f package.json ]; then
    echo "root package.json scripts:"
    node -e 'const p=require("./package.json"); console.log(JSON.stringify(p.scripts||{},null,2))' 2>/dev/null || cat package.json | head -120
  fi
  if [ -f aria-frontend/package.json ]; then
    echo
    echo "aria-frontend package.json scripts:"
    node -e 'const p=require("./aria-frontend/package.json"); console.log(JSON.stringify(p.scripts||{},null,2))' 2>/dev/null || cat aria-frontend/package.json | head -120
  fi
  if [ -f lean-toolchain ]; then
    echo
    echo "lean-toolchain:"
    cat lean-toolchain
  fi
  if [ -f lakefile.toml ] || [ -f lakefile.lean ]; then
    echo
    echo "lake build available"
  fi
} > "$OUT/cheap_commands.txt" 2>&1

echo
echo "06 classify manual"
python3 - "$OUT" <<'PY2'
from pathlib import Path
import json, sys, re

out = Path(sys.argv[1])
issue = {}
try:
  issue = json.loads((out / "issue_summary.json").read_text())
except Exception:
  pass

body = (out / "issue_body.md").read_text(errors="replace") if (out / "issue_body.md").exists() else ""
inv = (out / "inventory.txt").read_text(errors="replace") if (out / "inventory.txt").exists() else ""
grep = (out / "grep.txt").read_text(errors="replace") if (out / "grep.txt").exists() else ""
cheap = (out / "cheap_commands.txt").read_text(errors="replace") if (out / "cheap_commands.txt").exists() else ""
text = "\n".join([body, inv, grep, cheap]).lower()

has_explicit_acceptance = "acceptance criteria" in text or "acceptance" in text
has_local_command = any(x in text for x in ["npm test", "pnpm test", "yarn test", "pytest", "cargo test", "go test", "lake build", "benchmark"])
has_ci = ".github/workflows" in text or "github actions" in text or "workflow" in text
has_concrete_error = any(x in text for x in ["cannot find module", "static export", "failing", "build fails", "regression", "error"])
has_money = any(x in text for x in ["bounty", "reward", "paid", "usd", "$"])
risk = any(x in text for x in ["system prompt", "private key", "seed phrase", "jailbreak", "malware", "phishing", "token", "wallet", "mainnet"])

if risk:
  verdict = "PARK_RISK"
elif has_money and has_explicit_acceptance and (has_local_command or has_ci) and has_concrete_error:
  verdict = "PATCH_CANDIDATE"
elif has_money and (has_local_command or has_ci) and has_concrete_error:
  verdict = "RECON_CANDIDATE"
elif has_money:
  verdict = "ASK_FOR_VERIFIER_OR_PARK"
else:
  verdict = "PARK_NO_MONEY"

decision = {
  "verdict": verdict,
  "issue": issue,
  "has_explicit_acceptance": has_explicit_acceptance,
  "has_local_command": has_local_command,
  "has_ci": has_ci,
  "has_concrete_error": has_concrete_error,
  "has_money": has_money,
  "risk": risk,
}

(out / "decision.json").write_text(json.dumps(decision, indent=2))

lines = []
lines.append("# Strict Recon Report")
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
lines.append(cheap[:8000])
lines.append("")
lines.append("## Issue body")
lines.append("")
lines.append(body[:10000])
lines.append("")
lines.append("## Inventory excerpt")
lines.append("")
lines.append(inv[:10000])
lines.append("")
lines.append("## Grep excerpt")
lines.append("")
lines.append(grep[:20000])
lines.append("")
(out / "REPORT.md").write_text("\n".join(lines) + "\n")
print((out / "REPORT.md").read_text()[:16000])
PY2

cd "$ROOT" || exit 1

echo
echo "===================================================================================================="
echo "RECON tenstorrent/tt-blacksmith #529"
echo "===================================================================================================="

REPO_NAME="tenstorrent/tt-blacksmith"
ISSUE_NUM="529"
SAFE="tenstorrent__tt-blacksmith_529"
LOCAL_REPO="$ROOT/external/money_opportunity_scout_v3_strict/$SAFE"
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
  find . -maxdepth 4 -type f | sed 's#^./##' | sort | head -1000
  echo
  echo "build/test files"
  find . -maxdepth 6 -type f \( -name 'lakefile.toml' -o -name 'lakefile.lean' -o -name 'lean-toolchain' -o -name 'package.json' -o -name 'pnpm-lock.yaml' -o -name 'yarn.lock' -o -name 'package-lock.json' -o -name 'pyproject.toml' -o -name 'requirements.txt' -o -name 'Cargo.toml' -o -name 'go.mod' -o -name 'Makefile' -o -name 'README*' \) | sort
  echo
  echo "workflows"
  find .github/workflows -type f 2>/dev/null | sort
} > "$OUT/inventory.txt" 2>&1

echo
echo "04 grep focused"
{
  echo "===== issue terms ====="
  cat "$OUT/issue_body.md" 2>/dev/null || true

  echo
  echo "===== judge hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=.lake --exclude-dir=node_modules --exclude-dir=target --exclude-dir=dist --exclude-dir=build \
    "pytest|unittest|vitest|jest|npm test|pnpm test|yarn test|cargo test|go test|make test|lake build|benchmark|criterion|CI|workflow|acceptance|failing|regression|Cannot find module|static export|output: export|github pages|pages artifact" . 2>/dev/null | head -2500

  echo
  echo "===== patch surface hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=.lake --exclude-dir=node_modules --exclude-dir=target --exclude-dir=dist --exclude-dir=build \
    "TODO|FIXME|validate|validation|proof|theorem|invariant|correctness|performance|optimize|bug|error|failing|regression|static export|dynamic|api route|Cannot find module|Pages" . 2>/dev/null | head -2500
} > "$OUT/grep.txt" 2>&1

echo
echo "05 local cheap commands"
{
  echo "pwd=$(pwd)"
  echo
  if [ -f package.json ]; then
    echo "root package.json scripts:"
    node -e 'const p=require("./package.json"); console.log(JSON.stringify(p.scripts||{},null,2))' 2>/dev/null || cat package.json | head -120
  fi
  if [ -f aria-frontend/package.json ]; then
    echo
    echo "aria-frontend package.json scripts:"
    node -e 'const p=require("./aria-frontend/package.json"); console.log(JSON.stringify(p.scripts||{},null,2))' 2>/dev/null || cat aria-frontend/package.json | head -120
  fi
  if [ -f lean-toolchain ]; then
    echo
    echo "lean-toolchain:"
    cat lean-toolchain
  fi
  if [ -f lakefile.toml ] || [ -f lakefile.lean ]; then
    echo
    echo "lake build available"
  fi
} > "$OUT/cheap_commands.txt" 2>&1

echo
echo "06 classify manual"
python3 - "$OUT" <<'PY2'
from pathlib import Path
import json, sys, re

out = Path(sys.argv[1])
issue = {}
try:
  issue = json.loads((out / "issue_summary.json").read_text())
except Exception:
  pass

body = (out / "issue_body.md").read_text(errors="replace") if (out / "issue_body.md").exists() else ""
inv = (out / "inventory.txt").read_text(errors="replace") if (out / "inventory.txt").exists() else ""
grep = (out / "grep.txt").read_text(errors="replace") if (out / "grep.txt").exists() else ""
cheap = (out / "cheap_commands.txt").read_text(errors="replace") if (out / "cheap_commands.txt").exists() else ""
text = "\n".join([body, inv, grep, cheap]).lower()

has_explicit_acceptance = "acceptance criteria" in text or "acceptance" in text
has_local_command = any(x in text for x in ["npm test", "pnpm test", "yarn test", "pytest", "cargo test", "go test", "lake build", "benchmark"])
has_ci = ".github/workflows" in text or "github actions" in text or "workflow" in text
has_concrete_error = any(x in text for x in ["cannot find module", "static export", "failing", "build fails", "regression", "error"])
has_money = any(x in text for x in ["bounty", "reward", "paid", "usd", "$"])
risk = any(x in text for x in ["system prompt", "private key", "seed phrase", "jailbreak", "malware", "phishing", "token", "wallet", "mainnet"])

if risk:
  verdict = "PARK_RISK"
elif has_money and has_explicit_acceptance and (has_local_command or has_ci) and has_concrete_error:
  verdict = "PATCH_CANDIDATE"
elif has_money and (has_local_command or has_ci) and has_concrete_error:
  verdict = "RECON_CANDIDATE"
elif has_money:
  verdict = "ASK_FOR_VERIFIER_OR_PARK"
else:
  verdict = "PARK_NO_MONEY"

decision = {
  "verdict": verdict,
  "issue": issue,
  "has_explicit_acceptance": has_explicit_acceptance,
  "has_local_command": has_local_command,
  "has_ci": has_ci,
  "has_concrete_error": has_concrete_error,
  "has_money": has_money,
  "risk": risk,
}

(out / "decision.json").write_text(json.dumps(decision, indent=2))

lines = []
lines.append("# Strict Recon Report")
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
lines.append(cheap[:8000])
lines.append("")
lines.append("## Issue body")
lines.append("")
lines.append(body[:10000])
lines.append("")
lines.append("## Inventory excerpt")
lines.append("")
lines.append(inv[:10000])
lines.append("")
lines.append("## Grep excerpt")
lines.append("")
lines.append(grep[:20000])
lines.append("")
(out / "REPORT.md").write_text("\n".join(lines) + "\n")
print((out / "REPORT.md").read_text()[:16000])
PY2

cd "$ROOT" || exit 1

echo
echo "===================================================================================================="
echo "RECON ClankerNation/OpenAgents #21"
echo "===================================================================================================="

REPO_NAME="ClankerNation/OpenAgents"
ISSUE_NUM="21"
SAFE="ClankerNation__OpenAgents_21"
LOCAL_REPO="$ROOT/external/money_opportunity_scout_v3_strict/$SAFE"
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
  find . -maxdepth 4 -type f | sed 's#^./##' | sort | head -1000
  echo
  echo "build/test files"
  find . -maxdepth 6 -type f \( -name 'lakefile.toml' -o -name 'lakefile.lean' -o -name 'lean-toolchain' -o -name 'package.json' -o -name 'pnpm-lock.yaml' -o -name 'yarn.lock' -o -name 'package-lock.json' -o -name 'pyproject.toml' -o -name 'requirements.txt' -o -name 'Cargo.toml' -o -name 'go.mod' -o -name 'Makefile' -o -name 'README*' \) | sort
  echo
  echo "workflows"
  find .github/workflows -type f 2>/dev/null | sort
} > "$OUT/inventory.txt" 2>&1

echo
echo "04 grep focused"
{
  echo "===== issue terms ====="
  cat "$OUT/issue_body.md" 2>/dev/null || true

  echo
  echo "===== judge hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=.lake --exclude-dir=node_modules --exclude-dir=target --exclude-dir=dist --exclude-dir=build \
    "pytest|unittest|vitest|jest|npm test|pnpm test|yarn test|cargo test|go test|make test|lake build|benchmark|criterion|CI|workflow|acceptance|failing|regression|Cannot find module|static export|output: export|github pages|pages artifact" . 2>/dev/null | head -2500

  echo
  echo "===== patch surface hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=.lake --exclude-dir=node_modules --exclude-dir=target --exclude-dir=dist --exclude-dir=build \
    "TODO|FIXME|validate|validation|proof|theorem|invariant|correctness|performance|optimize|bug|error|failing|regression|static export|dynamic|api route|Cannot find module|Pages" . 2>/dev/null | head -2500
} > "$OUT/grep.txt" 2>&1

echo
echo "05 local cheap commands"
{
  echo "pwd=$(pwd)"
  echo
  if [ -f package.json ]; then
    echo "root package.json scripts:"
    node -e 'const p=require("./package.json"); console.log(JSON.stringify(p.scripts||{},null,2))' 2>/dev/null || cat package.json | head -120
  fi
  if [ -f aria-frontend/package.json ]; then
    echo
    echo "aria-frontend package.json scripts:"
    node -e 'const p=require("./aria-frontend/package.json"); console.log(JSON.stringify(p.scripts||{},null,2))' 2>/dev/null || cat aria-frontend/package.json | head -120
  fi
  if [ -f lean-toolchain ]; then
    echo
    echo "lean-toolchain:"
    cat lean-toolchain
  fi
  if [ -f lakefile.toml ] || [ -f lakefile.lean ]; then
    echo
    echo "lake build available"
  fi
} > "$OUT/cheap_commands.txt" 2>&1

echo
echo "06 classify manual"
python3 - "$OUT" <<'PY2'
from pathlib import Path
import json, sys, re

out = Path(sys.argv[1])
issue = {}
try:
  issue = json.loads((out / "issue_summary.json").read_text())
except Exception:
  pass

body = (out / "issue_body.md").read_text(errors="replace") if (out / "issue_body.md").exists() else ""
inv = (out / "inventory.txt").read_text(errors="replace") if (out / "inventory.txt").exists() else ""
grep = (out / "grep.txt").read_text(errors="replace") if (out / "grep.txt").exists() else ""
cheap = (out / "cheap_commands.txt").read_text(errors="replace") if (out / "cheap_commands.txt").exists() else ""
text = "\n".join([body, inv, grep, cheap]).lower()

has_explicit_acceptance = "acceptance criteria" in text or "acceptance" in text
has_local_command = any(x in text for x in ["npm test", "pnpm test", "yarn test", "pytest", "cargo test", "go test", "lake build", "benchmark"])
has_ci = ".github/workflows" in text or "github actions" in text or "workflow" in text
has_concrete_error = any(x in text for x in ["cannot find module", "static export", "failing", "build fails", "regression", "error"])
has_money = any(x in text for x in ["bounty", "reward", "paid", "usd", "$"])
risk = any(x in text for x in ["system prompt", "private key", "seed phrase", "jailbreak", "malware", "phishing", "token", "wallet", "mainnet"])

if risk:
  verdict = "PARK_RISK"
elif has_money and has_explicit_acceptance and (has_local_command or has_ci) and has_concrete_error:
  verdict = "PATCH_CANDIDATE"
elif has_money and (has_local_command or has_ci) and has_concrete_error:
  verdict = "RECON_CANDIDATE"
elif has_money:
  verdict = "ASK_FOR_VERIFIER_OR_PARK"
else:
  verdict = "PARK_NO_MONEY"

decision = {
  "verdict": verdict,
  "issue": issue,
  "has_explicit_acceptance": has_explicit_acceptance,
  "has_local_command": has_local_command,
  "has_ci": has_ci,
  "has_concrete_error": has_concrete_error,
  "has_money": has_money,
  "risk": risk,
}

(out / "decision.json").write_text(json.dumps(decision, indent=2))

lines = []
lines.append("# Strict Recon Report")
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
lines.append(cheap[:8000])
lines.append("")
lines.append("## Issue body")
lines.append("")
lines.append(body[:10000])
lines.append("")
lines.append("## Inventory excerpt")
lines.append("")
lines.append(inv[:10000])
lines.append("")
lines.append("## Grep excerpt")
lines.append("")
lines.append(grep[:20000])
lines.append("")
(out / "REPORT.md").write_text("\n".join(lines) + "\n")
print((out / "REPORT.md").read_text()[:16000])
PY2

cd "$ROOT" || exit 1
