#!/usr/bin/env bash
set -u

ROOT="/Users/heath/Documents/mathgraph-lean-work"
BASE_OUT="$ROOT/artifacts/money_opportunity_scout_v2/recon"
mkdir -p "$BASE_OUT"
cd "$ROOT" || exit 1

echo "MathGraph top-5 opportunity recon"
echo


echo
echo "===================================================================================================="
echo "RECON omegahat/XML #4"
echo "===================================================================================================="

REPO_NAME="omegahat/XML"
ISSUE_NUM="4"
SAFE="omegahat__XML_4"
LOCAL_REPO="$ROOT/external/money_opportunity_scout_v2/$SAFE"
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
  print(json.dumps(summary, indent=2))
else:
  print("issue view failed")
  print((out / "issue.err").read_text(errors="replace") if (out / "issue.err").exists() else "")
PY2

echo
echo "02 clone/update shallow"
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
  find . -maxdepth 3 -type f | sed 's#^./##' | sort | head -600
  echo
  echo "build/test files"
  find . -maxdepth 5 -type f \( -name 'lakefile.toml' -o -name 'lakefile.lean' -o -name 'lean-toolchain' -o -name 'package.json' -o -name 'pyproject.toml' -o -name 'Cargo.toml' -o -name 'go.mod' -o -name 'Makefile' -o -name '.github' -o -name 'README*' \) | sort
} > "$OUT/inventory.txt" 2>&1

echo
echo "04 grep judge and surface"
{
  echo "===== judge hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=.lake --exclude-dir=node_modules --exclude-dir=target --exclude-dir=dist --exclude-dir=build \
    "lake build|lean-toolchain|sorry|admit|pytest|unittest|vitest|jest|cargo test|go test|make test|benchmark|criterion|CI|workflow|failing|regression" . 2>/dev/null | head -2500

  echo
  echo "===== issue/surface hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=.lake --exclude-dir=node_modules --exclude-dir=target --exclude-dir=dist --exclude-dir=build \
    "bounty|reward|TODO|FIXME|validate|validation|proof|theorem|invariant|correctness|performance|optimize|bug|error|failing|regression" . 2>/dev/null | head -2500
} > "$OUT/grep.txt" 2>&1

echo
echo "05 classify"
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
text = "\n".join([body, inv, grep]).lower()

has_lean = any(x in text for x in ["lean-toolchain", "lakefile", "lake build", ".lean", "sorry", "admit"])
has_tests = any(x in text for x in ["pytest", "unittest", "vitest", "jest", "cargo test", "go test", "make test", "lake build"])
has_benchmark = "benchmark" in text or "criterion" in text
has_money = "bounty" in text or "$" in text or "reward" in text or "paid" in text
has_surface = len(grep.strip()) > 800
risk = any(x in text for x in ["system prompt", "private key", "seed phrase", "jailbreak", "malware", "phishing"])
no_surface = not has_surface

if risk:
  verdict = "PARK_RISK"
elif has_lean and has_tests and has_surface:
  verdict = "PROMOTE_LEAN_RECON"
elif has_money and has_tests and has_surface:
  verdict = "PROMOTE_MONEY_RECON"
elif has_tests and has_surface:
  verdict = "MAYBE_RECON"
elif no_surface:
  verdict = "PARK_NO_SURFACE"
else:
  verdict = "MAYBE_NEEDS_MANUAL_READ"

decision = {
  "verdict": verdict,
  "issue": issue,
  "has_lean": has_lean,
  "has_tests": has_tests,
  "has_benchmark": has_benchmark,
  "has_money": has_money,
  "has_surface": has_surface,
  "risk": risk,
}

(out / "decision.json").write_text(json.dumps(decision, indent=2))

lines = []
lines.append("# Recon Report")
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
lines.append("## Issue body excerpt")
lines.append("")
lines.append(body[:7000])
lines.append("")
lines.append("## Inventory excerpt")
lines.append("")
lines.append(inv[:9000])
lines.append("")
lines.append("## Grep excerpt")
lines.append("")
lines.append(grep[:18000])
lines.append("")
(out / "REPORT.md").write_text("\n".join(lines) + "\n")
print((out / "REPORT.md").read_text()[:12000])
PY2

cd "$ROOT" || exit 1

echo
echo "===================================================================================================="
echo "RECON geraintluff/json-model #4"
echo "===================================================================================================="

REPO_NAME="geraintluff/json-model"
ISSUE_NUM="4"
SAFE="geraintluff__json-model_4"
LOCAL_REPO="$ROOT/external/money_opportunity_scout_v2/$SAFE"
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
  print(json.dumps(summary, indent=2))
else:
  print("issue view failed")
  print((out / "issue.err").read_text(errors="replace") if (out / "issue.err").exists() else "")
PY2

echo
echo "02 clone/update shallow"
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
  find . -maxdepth 3 -type f | sed 's#^./##' | sort | head -600
  echo
  echo "build/test files"
  find . -maxdepth 5 -type f \( -name 'lakefile.toml' -o -name 'lakefile.lean' -o -name 'lean-toolchain' -o -name 'package.json' -o -name 'pyproject.toml' -o -name 'Cargo.toml' -o -name 'go.mod' -o -name 'Makefile' -o -name '.github' -o -name 'README*' \) | sort
} > "$OUT/inventory.txt" 2>&1

echo
echo "04 grep judge and surface"
{
  echo "===== judge hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=.lake --exclude-dir=node_modules --exclude-dir=target --exclude-dir=dist --exclude-dir=build \
    "lake build|lean-toolchain|sorry|admit|pytest|unittest|vitest|jest|cargo test|go test|make test|benchmark|criterion|CI|workflow|failing|regression" . 2>/dev/null | head -2500

  echo
  echo "===== issue/surface hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=.lake --exclude-dir=node_modules --exclude-dir=target --exclude-dir=dist --exclude-dir=build \
    "bounty|reward|TODO|FIXME|validate|validation|proof|theorem|invariant|correctness|performance|optimize|bug|error|failing|regression" . 2>/dev/null | head -2500
} > "$OUT/grep.txt" 2>&1

echo
echo "05 classify"
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
text = "\n".join([body, inv, grep]).lower()

has_lean = any(x in text for x in ["lean-toolchain", "lakefile", "lake build", ".lean", "sorry", "admit"])
has_tests = any(x in text for x in ["pytest", "unittest", "vitest", "jest", "cargo test", "go test", "make test", "lake build"])
has_benchmark = "benchmark" in text or "criterion" in text
has_money = "bounty" in text or "$" in text or "reward" in text or "paid" in text
has_surface = len(grep.strip()) > 800
risk = any(x in text for x in ["system prompt", "private key", "seed phrase", "jailbreak", "malware", "phishing"])
no_surface = not has_surface

if risk:
  verdict = "PARK_RISK"
elif has_lean and has_tests and has_surface:
  verdict = "PROMOTE_LEAN_RECON"
elif has_money and has_tests and has_surface:
  verdict = "PROMOTE_MONEY_RECON"
elif has_tests and has_surface:
  verdict = "MAYBE_RECON"
elif no_surface:
  verdict = "PARK_NO_SURFACE"
else:
  verdict = "MAYBE_NEEDS_MANUAL_READ"

decision = {
  "verdict": verdict,
  "issue": issue,
  "has_lean": has_lean,
  "has_tests": has_tests,
  "has_benchmark": has_benchmark,
  "has_money": has_money,
  "has_surface": has_surface,
  "risk": risk,
}

(out / "decision.json").write_text(json.dumps(decision, indent=2))

lines = []
lines.append("# Recon Report")
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
lines.append("## Issue body excerpt")
lines.append("")
lines.append(body[:7000])
lines.append("")
lines.append("## Inventory excerpt")
lines.append("")
lines.append(inv[:9000])
lines.append("")
lines.append("## Grep excerpt")
lines.append("")
lines.append(grep[:18000])
lines.append("")
(out / "REPORT.md").write_text("\n".join(lines) + "\n")
print((out / "REPORT.md").read_text()[:12000])
PY2

cd "$ROOT" || exit 1

echo
echo "===================================================================================================="
echo "RECON qurbaneliii/AI-Social-Media-Manager #4"
echo "===================================================================================================="

REPO_NAME="qurbaneliii/AI-Social-Media-Manager"
ISSUE_NUM="4"
SAFE="qurbaneliii__AI-Social-Media-Manager_4"
LOCAL_REPO="$ROOT/external/money_opportunity_scout_v2/$SAFE"
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
  print(json.dumps(summary, indent=2))
else:
  print("issue view failed")
  print((out / "issue.err").read_text(errors="replace") if (out / "issue.err").exists() else "")
PY2

echo
echo "02 clone/update shallow"
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
  find . -maxdepth 3 -type f | sed 's#^./##' | sort | head -600
  echo
  echo "build/test files"
  find . -maxdepth 5 -type f \( -name 'lakefile.toml' -o -name 'lakefile.lean' -o -name 'lean-toolchain' -o -name 'package.json' -o -name 'pyproject.toml' -o -name 'Cargo.toml' -o -name 'go.mod' -o -name 'Makefile' -o -name '.github' -o -name 'README*' \) | sort
} > "$OUT/inventory.txt" 2>&1

echo
echo "04 grep judge and surface"
{
  echo "===== judge hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=.lake --exclude-dir=node_modules --exclude-dir=target --exclude-dir=dist --exclude-dir=build \
    "lake build|lean-toolchain|sorry|admit|pytest|unittest|vitest|jest|cargo test|go test|make test|benchmark|criterion|CI|workflow|failing|regression" . 2>/dev/null | head -2500

  echo
  echo "===== issue/surface hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=.lake --exclude-dir=node_modules --exclude-dir=target --exclude-dir=dist --exclude-dir=build \
    "bounty|reward|TODO|FIXME|validate|validation|proof|theorem|invariant|correctness|performance|optimize|bug|error|failing|regression" . 2>/dev/null | head -2500
} > "$OUT/grep.txt" 2>&1

echo
echo "05 classify"
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
text = "\n".join([body, inv, grep]).lower()

has_lean = any(x in text for x in ["lean-toolchain", "lakefile", "lake build", ".lean", "sorry", "admit"])
has_tests = any(x in text for x in ["pytest", "unittest", "vitest", "jest", "cargo test", "go test", "make test", "lake build"])
has_benchmark = "benchmark" in text or "criterion" in text
has_money = "bounty" in text or "$" in text or "reward" in text or "paid" in text
has_surface = len(grep.strip()) > 800
risk = any(x in text for x in ["system prompt", "private key", "seed phrase", "jailbreak", "malware", "phishing"])
no_surface = not has_surface

if risk:
  verdict = "PARK_RISK"
elif has_lean and has_tests and has_surface:
  verdict = "PROMOTE_LEAN_RECON"
elif has_money and has_tests and has_surface:
  verdict = "PROMOTE_MONEY_RECON"
elif has_tests and has_surface:
  verdict = "MAYBE_RECON"
elif no_surface:
  verdict = "PARK_NO_SURFACE"
else:
  verdict = "MAYBE_NEEDS_MANUAL_READ"

decision = {
  "verdict": verdict,
  "issue": issue,
  "has_lean": has_lean,
  "has_tests": has_tests,
  "has_benchmark": has_benchmark,
  "has_money": has_money,
  "has_surface": has_surface,
  "risk": risk,
}

(out / "decision.json").write_text(json.dumps(decision, indent=2))

lines = []
lines.append("# Recon Report")
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
lines.append("## Issue body excerpt")
lines.append("")
lines.append(body[:7000])
lines.append("")
lines.append("## Inventory excerpt")
lines.append("")
lines.append(inv[:9000])
lines.append("")
lines.append("## Grep excerpt")
lines.append("")
lines.append(grep[:18000])
lines.append("")
(out / "REPORT.md").write_text("\n".join(lines) + "\n")
print((out / "REPORT.md").read_text()[:12000])
PY2

cd "$ROOT" || exit 1

echo
echo "===================================================================================================="
echo "RECON lovecn/lovecn.github.io #4"
echo "===================================================================================================="

REPO_NAME="lovecn/lovecn.github.io"
ISSUE_NUM="4"
SAFE="lovecn__lovecn.github.io_4"
LOCAL_REPO="$ROOT/external/money_opportunity_scout_v2/$SAFE"
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
  print(json.dumps(summary, indent=2))
else:
  print("issue view failed")
  print((out / "issue.err").read_text(errors="replace") if (out / "issue.err").exists() else "")
PY2

echo
echo "02 clone/update shallow"
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
  find . -maxdepth 3 -type f | sed 's#^./##' | sort | head -600
  echo
  echo "build/test files"
  find . -maxdepth 5 -type f \( -name 'lakefile.toml' -o -name 'lakefile.lean' -o -name 'lean-toolchain' -o -name 'package.json' -o -name 'pyproject.toml' -o -name 'Cargo.toml' -o -name 'go.mod' -o -name 'Makefile' -o -name '.github' -o -name 'README*' \) | sort
} > "$OUT/inventory.txt" 2>&1

echo
echo "04 grep judge and surface"
{
  echo "===== judge hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=.lake --exclude-dir=node_modules --exclude-dir=target --exclude-dir=dist --exclude-dir=build \
    "lake build|lean-toolchain|sorry|admit|pytest|unittest|vitest|jest|cargo test|go test|make test|benchmark|criterion|CI|workflow|failing|regression" . 2>/dev/null | head -2500

  echo
  echo "===== issue/surface hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=.lake --exclude-dir=node_modules --exclude-dir=target --exclude-dir=dist --exclude-dir=build \
    "bounty|reward|TODO|FIXME|validate|validation|proof|theorem|invariant|correctness|performance|optimize|bug|error|failing|regression" . 2>/dev/null | head -2500
} > "$OUT/grep.txt" 2>&1

echo
echo "05 classify"
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
text = "\n".join([body, inv, grep]).lower()

has_lean = any(x in text for x in ["lean-toolchain", "lakefile", "lake build", ".lean", "sorry", "admit"])
has_tests = any(x in text for x in ["pytest", "unittest", "vitest", "jest", "cargo test", "go test", "make test", "lake build"])
has_benchmark = "benchmark" in text or "criterion" in text
has_money = "bounty" in text or "$" in text or "reward" in text or "paid" in text
has_surface = len(grep.strip()) > 800
risk = any(x in text for x in ["system prompt", "private key", "seed phrase", "jailbreak", "malware", "phishing"])
no_surface = not has_surface

if risk:
  verdict = "PARK_RISK"
elif has_lean and has_tests and has_surface:
  verdict = "PROMOTE_LEAN_RECON"
elif has_money and has_tests and has_surface:
  verdict = "PROMOTE_MONEY_RECON"
elif has_tests and has_surface:
  verdict = "MAYBE_RECON"
elif no_surface:
  verdict = "PARK_NO_SURFACE"
else:
  verdict = "MAYBE_NEEDS_MANUAL_READ"

decision = {
  "verdict": verdict,
  "issue": issue,
  "has_lean": has_lean,
  "has_tests": has_tests,
  "has_benchmark": has_benchmark,
  "has_money": has_money,
  "has_surface": has_surface,
  "risk": risk,
}

(out / "decision.json").write_text(json.dumps(decision, indent=2))

lines = []
lines.append("# Recon Report")
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
lines.append("## Issue body excerpt")
lines.append("")
lines.append(body[:7000])
lines.append("")
lines.append("## Inventory excerpt")
lines.append("")
lines.append(inv[:9000])
lines.append("")
lines.append("## Grep excerpt")
lines.append("")
lines.append(grep[:18000])
lines.append("")
(out / "REPORT.md").write_text("\n".join(lines) + "\n")
print((out / "REPORT.md").read_text()[:12000])
PY2

cd "$ROOT" || exit 1
