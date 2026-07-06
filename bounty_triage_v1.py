#!/usr/bin/env python3
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path.cwd()
OUT = ROOT / "artifacts" / "bounty_triage_v1"
EXT = ROOT / "external" / "bounty_triage_v1"
TARGETS = OUT / "targets.tsv"
REFINED = ROOT / "artifacts" / "paid_fix_scout" / "paid_fix_scout_refined.json"
REPORT = OUT / "BOUNTY_TRIAGE_REPORT.md"
RAW = OUT / "bounty_triage_raw.json"

OUT.mkdir(parents=True, exist_ok=True)
EXT.mkdir(parents=True, exist_ok=True)

def run(cmd, cwd=None, timeout=90):
    try:
        p = subprocess.run(
            cmd,
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired as e:
        out = e.stdout or ""
        err = e.stderr or ""
        if isinstance(out, bytes):
            out = out.decode(errors="replace")
        if isinstance(err, bytes):
            err = err.decode(errors="replace")
        return 124, out, err + "\nTIMEOUT\n"

def parse_issue_url(url):
    m = re.match(r"https://github\.com/([^/]+)/([^/]+)/issues/(\d+)", url.strip())
    if not m:
        raise ValueError(f"bad issue url: {url}")
    owner, repo, num = m.group(1), m.group(2), int(m.group(3))
    return owner, repo, num, f"{owner}/{repo}"

def load_targets():
    rows = []
    for line in TARGETS.read_text().splitlines()[1:]:
        if not line.strip():
            continue
        rank, url, why = line.split("\t", 2)
        owner, repo, num, full = parse_issue_url(url)
        rows.append({
            "rank": int(rank),
            "url": url,
            "why_seeded": why,
            "owner": owner,
            "repo": repo,
            "issue": num,
            "full": full,
        })
    return rows

def load_refined_index():
    idx = {}
    if REFINED.exists():
        try:
            for r in json.loads(REFINED.read_text()):
                if r.get("url"):
                    idx[r["url"]] = r
        except Exception:
            pass
    return idx

def gh_issue_view(url):
    cmd = [
        "gh", "issue", "view", url,
        "--json",
        "title,body,author,createdAt,updatedAt,state,comments,labels,url",
    ]
    rc, out, err = run(cmd, timeout=45)
    if rc != 0:
        return None, f"gh issue view failed rc={rc}: {err.strip()[:500]}"
    try:
        return json.loads(out), None
    except Exception as e:
        return None, f"issue json parse failed: {e}"

def gh_repo_view(full):
    cmd = [
        "gh", "repo", "view", full,
        "--json",
        "nameWithOwner,description,homepageUrl,isArchived,isFork,stargazerCount,forkCount,defaultBranchRef,primaryLanguage,languages,repositoryTopics,url",
    ]
    rc, out, err = run(cmd, timeout=45)
    if rc != 0:
        return None, f"gh repo view failed rc={rc}: {err.strip()[:500]}"
    try:
        return json.loads(out), None
    except Exception as e:
        return None, f"repo json parse failed: {e}"

def safe_name(full):
    return full.replace("/", "__")

def sparse_clone_root(full, default_branch=None):
    dest = EXT / safe_name(full)
    log = {"dest": str(dest), "steps": []}

    if dest.exists() and (dest / ".git").exists():
        rc, out, err = run(["git", "fetch", "--depth", "1", "origin"], cwd=dest, timeout=120)
        log["steps"].append({"cmd": "git fetch --depth 1 origin", "rc": rc, "err": err[-500:]})
        rc2, out2, err2 = run(["git", "reset", "--hard", "origin/HEAD"], cwd=dest, timeout=60)
        log["steps"].append({"cmd": "git reset --hard origin/HEAD", "rc": rc2, "err": err2[-500:]})
        return dest, log

    url = f"https://github.com/{full}.git"
    cmd = ["git", "clone", "--depth", "1", "--filter=blob:none", "--sparse", url, str(dest)]
    rc, out, err = run(cmd, timeout=240)
    log["steps"].append({"cmd": " ".join(cmd), "rc": rc, "err": err[-1000:]})
    if rc != 0:
        if dest.exists():
            shutil.rmtree(dest, ignore_errors=True)
        return None, log

    sparse_paths = [
        "README.md", "readme.md", "Readme.md",
        "package.json", "pnpm-lock.yaml", "yarn.lock", "package-lock.json",
        "pyproject.toml", "requirements.txt", "setup.py", "tox.ini",
        "lakefile.lean", "lakefile.toml", "lean-toolchain",
        "Cargo.toml", "Cargo.lock",
        "go.mod", "go.sum",
        "Makefile", "CMakeLists.txt",
        ".github/workflows",
        "tests", "test", "spec", "specs", "benchmarks", "benchmark",
        "src", "sdk",
    ]
    rc2, out2, err2 = run(["git", "sparse-checkout", "set", *sparse_paths], cwd=dest, timeout=180)
    log["steps"].append({"cmd": "git sparse-checkout set <common paths>", "rc": rc2, "err": err2[-1000:]})

    return dest, log

def list_files(dest, max_files=500):
    if not dest or not dest.exists():
        return []
    rc, out, err = run(["git", "ls-files"], cwd=dest, timeout=30)
    if rc != 0:
        return []
    return out.splitlines()[:max_files]

def read_small(dest, rel, max_bytes=6000):
    p = dest / rel
    if not p.exists() or not p.is_file():
        return ""
    try:
        data = p.read_bytes()[:max_bytes]
        return data.decode(errors="replace")
    except Exception:
        return ""

def detect_project(dest, files):
    fset = set(files)
    signals = []
    commands = []
    judge = []

    if "lakefile.lean" in fset or "lakefile.toml" in fset or "lean-toolchain" in fset:
        signals.append("Lean project")
        commands.append("lake build")
        commands.append("lake env lean <target>.lean")
        judge.append("Lean/Lake checker")

    if "package.json" in fset:
        signals.append("Node/TypeScript project")
        pkg = read_small(dest, "package.json")
        try:
            pj = json.loads(pkg)
            scripts = pj.get("scripts", {}) if isinstance(pj, dict) else {}
            for key in ["test", "check", "typecheck", "lint", "build", "bench"]:
                if key in scripts:
                    commands.append(f"npm run {key}")
                    judge.append(f"package.json script: {key}")
        except Exception:
            commands.append("npm test")
            judge.append("package.json present")

    if "pyproject.toml" in fset or "requirements.txt" in fset or "setup.py" in fset:
        signals.append("Python project")
        if any(x.startswith("test") or x.startswith("tests/") for x in files):
            commands.append("python -m pytest")
            judge.append("pytest/tests present")
        if any("benchmark" in x.lower() or "benchmarks" in x.lower() for x in files):
            commands.append("python -m pytest benchmarks || custom benchmark command")
            judge.append("benchmark files present")

    if "Cargo.toml" in fset:
        signals.append("Rust project")
        commands.append("cargo test")
        commands.append("cargo build")
        judge.append("Cargo test/build")

    if "go.mod" in fset:
        signals.append("Go project")
        commands.append("go test ./...")
        judge.append("Go tests")

    if "Makefile" in fset:
        signals.append("Makefile present")
        commands.append("make test || make")
        judge.append("Makefile target likely available")

    if any(x.startswith(".github/workflows/") for x in files):
        signals.append("GitHub Actions workflows present")
        judge.append("CI workflows available")

    if any("test" in x.lower() for x in files):
        signals.append("test files present")
    if any("bench" in x.lower() for x in files):
        signals.append("benchmark files present")
    if any("spec" in x.lower() for x in files):
        signals.append("spec files present")

    return {
        "signals": sorted(set(signals)),
        "suggested_commands": list(dict.fromkeys(commands))[:10],
        "judge_signals": sorted(set(judge)),
    }

def money_from_text(s):
    vals = []
    for m in re.finditer(r"(?i)(?:\$|USD\s*|US\$|€|£)\s?([0-9][0-9,]*(?:\.\d+)?)|([0-9][0-9,]*)\s?(?:USD|dollars|eur|euro|gbp)", s):
        raw = m.group(1) or m.group(2)
        if raw:
            try:
                vals.append(float(raw.replace(",", "")))
            except Exception:
                pass
    return max(vals) if vals else None

def assess(row, issue, repo, project):
    title = (issue or {}).get("title") or row.get("title") or ""
    body = (issue or {}).get("body") or row.get("body_snippet") or ""
    labels = []
    if issue and issue.get("labels"):
        labels = [x.get("name", "") for x in issue["labels"]]
    elif row.get("labels"):
        labels = row.get("labels") or []

    text = "\n".join([title, body, " ".join(labels), row["url"]])
    low = text.lower()

    score = 0
    reasons = []
    risks = []

    if "bounty" in low or "paid" in low or "reward" in low or "payment" in low:
        score += 25
        reasons.append("explicit bounty/paid/reward language")

    money = money_from_text(text) or row.get("money")
    if money:
        if money >= 1000:
            score += 20
        elif money >= 250:
            score += 12
        else:
            score += 5
        reasons.append(f"detected payout/budget ≈ {money:g}")

    if any(x in low for x in ["acceptance criteria", "acceptance", "must pass", "tests", "test suite", "benchmark", "ci", "reproduce"]):
        score += 25
        reasons.append("acceptance/test/benchmark language")

    if project.get("judge_signals"):
        score += 20
        reasons.append("repo has detectable local judge signals")

    if any(x in low for x in ["lean", "formal verification", "theorem", "proof", "invariant", "spec", "solver", "optimizer", "optimization", "compiler", "type checker"]):
        score += 20
        reasons.append("MathGraph-shaped technical terms")

    if (issue or {}).get("comments") is not None:
        comments = issue.get("comments") or []
        ncomments = len(comments)
        if ncomments <= 5:
            score += 6
            reasons.append("low comment competition")
        elif ncomments >= 40:
            score -= 12
            risks.append("crowded issue")

    if any(x in low for x in ["paste the entire block", "platform initialization", "system prompt", "first user message", "secret", "private key"]):
        score -= 100
        risks.append("asks for system prompt/secrets/platform initialization; avoid")

    if any(x in low for x in ["security audit", "vulnerability", "exploit", "rce", "xss", "cve", "bug bounty program"]):
        score -= 15
        risks.append("security/audit lane; higher reputation/legal risk")

    if any(x in low for x in ["proposal", "rfp", "daily brief", "hackathon prep", "marketing", "article"]):
        score -= 25
        risks.append("may be proposal/content/noise rather than concrete fix")

    if score >= 75:
        verdict = "WORK_FIRST"
    elif score >= 55:
        verdict = "INSPECT_NEXT"
    elif score >= 35:
        verdict = "MAYBE_LATER"
    else:
        verdict = "PARK"

    return {
        "score": score,
        "verdict": verdict,
        "money": money,
        "reasons": reasons,
        "risks": risks,
        "title": title,
        "body": body,
        "labels": labels,
    }

def main():
    rows = load_targets()
    refined = load_refined_index()
    results = []

    gh_ok = shutil.which("gh") is not None
    if gh_ok:
        rc, out, err = run(["gh", "auth", "status"], timeout=20)
        gh_ok = (rc == 0)

    for row in rows:
        print(f"\n=== {row['rank']} {row['full']} #{row['issue']} ===")
        old = refined.get(row["url"], {})
        row.update(old)

        issue, issue_err = (None, "gh unavailable")
        repo, repo_err = (None, "gh unavailable")

        if gh_ok:
            issue, issue_err = gh_issue_view(row["url"])
            repo, repo_err = gh_repo_view(row["full"])

        if issue:
            print(f"issue: {issue.get('title')}")
        else:
            print(f"issue fetch fallback: {issue_err}")

        if repo:
            default_branch = ((repo.get("defaultBranchRef") or {}).get("name")) or None
        else:
            default_branch = None
            print(f"repo fetch fallback: {repo_err}")

        print("sparse clone / update")
        dest, clone_log = sparse_clone_root(row["full"], default_branch=default_branch)
        files = list_files(dest) if dest else []
        project = detect_project(dest, files) if dest else {"signals": [], "suggested_commands": [], "judge_signals": []}
        assessment = assess(row, issue, repo, project)

        print(f"verdict={assessment['verdict']} score={assessment['score']}")
        print(f"signals={project['signals']}")
        print(f"commands={project['suggested_commands']}")

        result = {
            **row,
            "issue_fetch_error": issue_err,
            "repo_fetch_error": repo_err,
            "issue_live": issue,
            "repo_live": repo,
            "clone_log": clone_log,
            "clone_dest": str(dest) if dest else None,
            "files_sample": files[:200],
            "project": project,
            "assessment": assessment,
        }
        results.append(result)

        per = OUT / f"target_{row['rank']}_{safe_name(row['full'])}_issue_{row['issue']}.json"
        per.write_text(json.dumps(result, indent=2), encoding="utf-8")

    results.sort(key=lambda r: (r["assessment"]["score"], -r["rank"]), reverse=True)
    RAW.write_text(json.dumps(results, indent=2), encoding="utf-8")

    lines = []
    lines.append("# MathGraph Bounty Triage v1")
    lines.append("")
    lines.append(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append("")
    lines.append("## Executive ranking")
    lines.append("")

    for r in results:
        a = r["assessment"]
        lines.append(f"### {a['verdict']} · score {a['score']} · rank {r['rank']} · {a['title']}")
        lines.append("")
        lines.append(f"- Repo: `{r['full']}`")
        lines.append(f"- Issue: {r['url']}")
        lines.append(f"- Seed reason: {r['why_seeded']}")
        if a.get("money"):
            lines.append(f"- Detected money/budget: `{a['money']:g}`")
        lines.append(f"- Clone path: `{r.get('clone_dest')}`")
        lines.append(f"- Labels: `{', '.join([x for x in a.get('labels', []) if x])}`")
        lines.append("")
        lines.append("Reasons:")
        if a["reasons"]:
            for reason in a["reasons"]:
                lines.append(f"- {reason}")
        else:
            lines.append("- No strong positive reasons detected")
        lines.append("")
        lines.append("Risks:")
        if a["risks"]:
            for risk in a["risks"]:
                lines.append(f"- {risk}")
        else:
            lines.append("- No major automatic red flags detected")
        lines.append("")
        lines.append("Detected local judge signals:")
        if r["project"]["judge_signals"]:
            for sig in r["project"]["judge_signals"]:
                lines.append(f"- {sig}")
        else:
            lines.append("- None detected from sparse checkout")
        lines.append("")
        lines.append("Suggested first commands:")
        if r["project"]["suggested_commands"]:
            for cmd in r["project"]["suggested_commands"]:
                lines.append(f"- `{cmd}`")
        else:
            lines.append("- Manual inspection needed")
        lines.append("")
        snippet = (a.get("body") or "").strip()
        if snippet:
            lines.append("Issue snippet:")
            lines.append("")
            lines.append("```text")
            lines.append("\n".join(snippet.splitlines()[:18])[:2200])
            lines.append("```")
            lines.append("")

    lines.append("## Recommended next move")
    lines.append("")
    lines.append("Work only the first target with all four properties:")
    lines.append("")
    lines.append("1. explicit real payout")
    lines.append("2. local judge/test/benchmark")
    lines.append("3. small enough first patch attempt")
    lines.append("4. no prompt/secret/security weirdness")
    lines.append("")
    lines.append("Do not chase highest nominal payout if the issue is proposal-shaped, security-shaped, or reputation-risky.")
    lines.append("")
    lines.append("## Red-flag exclusions")
    lines.append("")
    lines.append("ClankerNation/OpenAgents bounties were excluded despite high payout because their issue text asks for the full platform initialization/system prompt. Do not submit that.")
    lines.append("")

    REPORT.write_text("\n".join(lines), encoding="utf-8")

    print("\n=== FINAL RANKING ===")
    for r in results:
        a = r["assessment"]
        money = f" money≈{a['money']:g}" if a.get("money") else ""
        print(f"- {a['verdict']} score={a['score']}{money} {r['full']} #{r['issue']} :: {a['title']}")
        print(f"  {r['url']}")

    print(f"\nWrote: {REPORT}")
    print(f"Wrote: {RAW}")

if __name__ == "__main__":
    main()
