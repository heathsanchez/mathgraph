"""Focused Mathlib digest runner for persistent Lawbook accumulation."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from mathgraph.lawbook_accumulator import (
    connect_lawbook,
    now_iso,
    stable_id,
    write_digest_payload,
)

TOKEN_RE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_']*(?:\.[A-Za-z_][A-Za-z0-9_']*)+\b")
KNOWN_AXIOMS = ("propext", "Classical.choice", "Quot.sound", "sorryAx")
RUN_NAME = "mathgraph_mathlib_digest_accumulator"
RUN_VERSION = "m12_2_constructor_statement_parity_fix"


@dataclass
class MathlibDigestConfig:
    pack_id: str
    modules: list[str] = field(default_factory=list)
    packs: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "MathlibDigestConfig":
        return cls(
            pack_id=str(data["pack_id"]),
            modules=[str(x) for x in data.get("modules", ())],
            packs=[dict(x) for x in data.get("packs", ())],
            metadata=dict(data.get("metadata", {})),
        )

    @classmethod
    def read_json(cls, path: str | Path) -> "MathlibDigestConfig":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    def target_names(self) -> list[str]:
        out: list[str] = []
        for pack in self.packs:
            out.extend(str(x) for x in pack.get("targets", ()))
        return out


def load_digest_config(path: str | Path) -> MathlibDigestConfig:
    return MathlibDigestConfig.read_json(path)


def write_json(path: str | Path, obj: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, sort_keys=True, default=str), encoding="utf-8")


def write_text(path: str | Path, text: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def detect_digest_environment(mathlib_root: str | Path | None) -> dict[str, Any]:
    root = Path(mathlib_root).resolve() if mathlib_root else None
    lean = shutil.which("lean")
    lake = shutil.which("lake")
    git = shutil.which("git")
    revision = None
    if root and git and (root / ".git").exists():
        try:
            revision = subprocess.run(
                [git, "-C", str(root), "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            ).stdout.strip() or None
        except Exception:
            revision = None
    toolchain = None
    if root and (root / "lean-toolchain").exists():
        toolchain = (root / "lean-toolchain").read_text(encoding="utf-8").strip()
    return {
        "mathlib_root": str(root) if root else None,
        "mathlib_root_exists": bool(root and root.exists()),
        "mathlib_revision": revision,
        "lean_toolchain": toolchain,
        "lean_path": lean,
        "lake_path": lake,
    }


def build_autopsy_text(modules: Sequence[str], target: str) -> str:
    imports = "\n".join(f"import {m}" for m in modules)
    return f"""{imports}

set_option pp.all false
set_option autoImplicit false

#check {target}
#print axioms {target}
#print {target}
"""


def _strip_lean_message_prefix(line: str, target: str) -> str:
    """Drop optional `/path/file.lean:line:col: info:` prefix before a #check result."""
    idx = line.find(target)
    return line[idx:].strip() if idx >= 0 else line.strip()


def parse_check_type(output: str, target: str) -> str:
    """Parse a #check type conservatively, preserving multiline pretty-printed types.

    Lean sometimes emits:

        Nat.foo : forall ...,
          more binders ...

    This parser starts at the target line, strips any Lean diagnostic prefix, and
    keeps indented continuation lines until the next obvious #print/diagnostic
    boundary. Later statement extraction strips any accidentally captured `:=`
    proof body from #print output so constructor files never embed declaration
    bodies inside type ascriptions.
    """
    escaped = re.escape(target)
    lines = output.splitlines()
    for i, line in enumerate(lines):
        stripped = _strip_lean_message_prefix(line, target)
        if re.search(escaped + r"(?:\.\{[^}]+\})?\s*:\s*", stripped):
            collected = [stripped]
            for nxt in lines[i + 1 :]:
                raw = nxt.rstrip()
                s = raw.strip()
                if not s:
                    break
                if s.startswith("[") and s.endswith("]"):
                    break
                if " does not depend on any axioms" in s:
                    break
                if s.startswith(("theorem ", "lemma ", "def ", "abbrev ", "axiom ")):
                    break
                if re.match(r"^.+\.lean:\d+:\d+:", s) and target not in s:
                    break
                # Continuation lines from pretty printing are normally indented.
                # Keep them; stop on a new unindented declaration-like line.
                if not raw[:1].isspace() and collected:
                    if not s.startswith(("∀", "fun", "Prop", "Sort", "Type")):
                        break
                collected.append(s)
            return " ".join(" ".join(collected).split())
    for line in lines:
        s = _strip_lean_message_prefix(line, target)
        if target in s and ":" in s:
            return " ".join(s.split())
    return ""


def _clean_formal_statement(statement: str) -> str:
    """Return only the theorem type, never a captured Lean declaration body.

    `#print` output can contain `theorem foo : TYPE := PROOF`. If the parser
    falls back to such a line, anything from `:=` onward is proof text, not a
    theorem statement. Keeping it produces malformed constructor files like
    `example : (... := ...) :=`. Strip it before parenthesizing the statement.
    """
    s = " ".join((statement or "").strip().split())
    if not s:
        return ""
    if ":=" in s:
        s = s.split(":=", 1)[0].strip()
    # A trailing comma means Lean pretty-printing was truncated before the
    # proposition body. Treat this as unusable rather than generating bad Lean.
    if s.endswith(","):
        return ""
    return s


def parse_formal_statement(parsed_type: str) -> str:
    if not parsed_type:
        return ""
    m = re.search(r"\b[A-Za-z_][A-Za-z0-9_'.]*(?:\.\{[^}]+\})?\s*:\s*(?P<statement>.*)$", parsed_type, re.S)
    if m:
        return _clean_formal_statement(m.group("statement"))
    if ":" not in parsed_type:
        return ""
    return _clean_formal_statement(parsed_type.split(":", 1)[1])


def parse_axioms(output: str) -> list[str]:
    if "does not depend on any axioms" in output:
        return []
    found = {x for x in KNOWN_AXIOMS if x in output}
    for line in output.splitlines():
        s = line.strip()
        if s.startswith("[") and s.endswith("]"):
            found.update(x.strip() for x in s.strip("[]").split(",") if x.strip())
    return sorted(found)


def classify_reference(ref: str, *, target: str = "") -> str:
    if ref in KNOWN_AXIOMS:
        return "axiom_or_assumption"
    if (target and ref.startswith(target + ".")) or ref.endswith("._f") or "._proof" in ref or "._match" in ref:
        return "local_proof_artifact"
    if ref.startswith("_private"):
        return "private_internal_artifact"
    if ref.startswith("Eq."):
        return "equality_transport_root"
    if ref in {"HAdd.hAdd", "HMul.hMul", "OfNat.ofNat", "Dvd.dvd"}:
        return "typeclass_or_notation_root"
    if "." in ref:
        return "shared_root_candidate"
    return "unknown_reference"


def extract_reference_hints(output: str, target: str, *, max_refs: int = 120) -> list[str]:
    seen = {target}
    out: list[str] = []
    for token in TOKEN_RE.findall(output):
        if token.startswith("Mathlib.") or token in seen:
            continue
        seen.add(token)
        out.append(token)
        if len(out) >= max_refs:
            break
    return out


def infer_reason_basin(target: str, pack: Mapping[str, Any] | None = None) -> tuple[str, str]:
    if pack and pack.get("basin_id"):
        return str(pack["basin_id"]), str(pack.get("pack_name") or pack["basin_id"])
    if "pow" in target:
        return "basin_nat_power_normalization", "Nat power normalization reason"
    if "dvd" in target or "div" in target:
        return "basin_nat_divisibility_division_normalization", "Nat divisibility / division normalization reason"
    if "set_induction" in target:
        return "basin_nat_set_induction", "Nat set induction reason"
    if "leRecOn" in target:
        return "basin_nat_lerec_order_recursion", "Nat leRecOn / order-recursion reason"
    return "basin_nat_injectivity_cancellation", "Nat injectivity / cancellation reason"


def constructor_strategy_for_basin(basin_id: str) -> str:
    if basin_id in {"basin_nat_set_induction", "basin_nat_lerec_order_recursion"}:
        return "exact_existing; simp; simpa; TODO real induction/leRecOn constructor synthesis"
    return "exact_existing; rfl; simp; simpa; simp_all_refs; simpa_all_refs"


def theorem_statement_from_check(parsed_type: str) -> str:
    return parse_formal_statement(parsed_type)


def valid_simp_roots(roots: Sequence[str], *, limit: int = 12) -> list[str]:
    out: list[str] = []
    for root in roots:
        if root.startswith(("Eq.", "HAdd.", "HMul.", "_private")):
            continue
        if "._proof" in root or "._match" in root or root.endswith("._f"):
            continue
        if root in {"Dvd.dvd", "OfNat.ofNat"}:
            continue
        if root not in out:
            out.append(root)
        if len(out) >= limit:
            break
    return out


def constructor_template_ids_for_basin(basin_id: str) -> list[str]:
    if basin_id in {"basin_nat_set_induction", "basin_nat_lerec_order_recursion"}:
        return ["exact_existing", "simp", "simpa"]
    return ["exact_existing", "rfl", "simp", "simpa", "simp_all_refs", "simpa_all_refs"]


def constructor_proof_body(template_id: str, target: str, roots: Sequence[str]) -> str:
    if template_id == "exact_existing":
        return f"by\n  exact {target}\n"
    if template_id == "rfl":
        return "by\n  rfl\n"
    if template_id == "simp":
        return "by\n  simp\n"
    if template_id == "simpa":
        return "by\n  simpa\n"
    simp_roots = valid_simp_roots(roots)
    bracket = "[" + ", ".join(simp_roots) + "]" if simp_roots else ""
    if template_id == "simp_all_refs":
        return f"by\n  simp {bracket}\n" if bracket else "by\n  simp\n"
    if template_id == "simpa_all_refs":
        return f"by\n  simpa {bracket}\n" if bracket else "by\n  simpa\n"
    return "by\n  simp\n"


def classify_constructor_error(stderr: str, stdout: str = "", returncode: int | None = None) -> str:
    text = f"{stderr}\n{stdout}".lower()
    if returncode == 0:
        return "verified"
    if "unexpected token ':='" in text:
        return "malformed_constructor_statement"
    if "typeclass instance problem is stuck" in text:
        return "typeclass_failure"
    if "unsolved goals" in text:
        return "unsolved_goals"
    if "unknown identifier" in text or "unknown constant" in text:
        return "unknown_reference"
    if "type mismatch" in text or "application type mismatch" in text:
        return "type_mismatch"
    if "failed to synthesize" in text:
        return "typeclass_failure"
    if "timeout" in text:
        return "timeout"
    return "lean_rejected"


def _run_lake_lean(mathlib_root: Path, lean_file: Path, timeout_sec: float) -> tuple[int | None, str, str, float, str]:
    lake = shutil.which("lake")
    lean = shutil.which("lean")
    if not lake or not lean:
        return None, "", "Lean or Lake missing.", 0.0, "SKIPPED_MISSING_LEAN_OR_LAKE"
    start = time.perf_counter()
    try:
        proc = subprocess.run(
            [lake, "env", "lean", str(lean_file)],
            cwd=str(mathlib_root),
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            check=False,
        )
        status = "LEAN_ACCEPTED_TARGET" if proc.returncode == 0 else "LEAN_REJECTED_OR_FAILED"
        return proc.returncode, proc.stdout or "", proc.stderr or "", time.perf_counter() - start, status
    except subprocess.TimeoutExpired as exc:
        return 124, str(exc.stdout or ""), str(exc.stderr or "") + "\nTIMEOUT", time.perf_counter() - start, "TIMEOUT"


def _parenthesize_statement(statement: str) -> str:
    s = _clean_formal_statement(statement)
    if not s:
        return s
    if s.startswith("(") and s.endswith(")"):
        return s
    return f"({s})"


def _write_constructor_file(
    path: Path,
    modules: Sequence[str],
    statement: str,
    proof_body: str,
    name_seed: str,
    *,
    target: str | None = None,
    template_id: str | None = None,
) -> None:
    imports = "\n".join(f"import {m}" for m in modules)
    theorem = re.sub(r"[^A-Za-z0-9_]", "_", f"mathgraph_test_{name_seed}")[:120]
    checked_statement = _parenthesize_statement(statement)
    body = f"""{imports}

set_option pp.all false
set_option autoImplicit false

example : {checked_statement} :=
{proof_body}

theorem {theorem} : {checked_statement} :=
{proof_body}
"""
    write_text(path, body)


def run_mathlib_digest_accumulator(
    *,
    lawbook: str | Path,
    pack_config: str | Path,
    out_base: str | Path,
    mathlib_root: str | Path | None = None,
    allow_live_lean: bool = False,
    verify_constructors: bool = False,
    timeout_sec: float = 90.0,
) -> dict[str, Any]:
    config = load_digest_config(pack_config)
    created = datetime.now(timezone.utc)
    run_id = stable_id("mathlib-digest-run", config.pack_id, created.isoformat())
    run_dir = Path(out_base) / f"{created.strftime('%Y%m%d_%H%M%S')}_{run_id[:16]}"
    run_dir.mkdir(parents=True, exist_ok=True)
    env = detect_digest_environment(mathlib_root)
    root = Path(mathlib_root).resolve() if mathlib_root else None
    conn = connect_lawbook(lawbook)

    target_payloads: list[dict[str, Any]] = []
    observation_payloads: list[dict[str, Any]] = []
    root_payloads: list[dict[str, Any]] = []
    reasons: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []
    attempts: list[dict[str, Any]] = []
    verified: list[dict[str, Any]] = []
    obstructions: list[dict[str, Any]] = []
    accepted_count = 0

    target_to_pack = {target: pack for pack in config.packs for target in pack.get("targets", ())}
    for target in config.target_names():
        pack = target_to_pack[target]
        basin_id, reason_name = infer_reason_basin(target, pack)
        target_id = stable_id("target", target)
        target_dir = run_dir / "targets" / re.sub(r"[^A-Za-z0-9_]", "_", target)
        lean_file = target_dir / "autopsy.lean"
        stdout_path = target_dir / "autopsy.stdout.txt"
        stderr_path = target_dir / "autopsy.stderr.txt"
        write_text(lean_file, build_autopsy_text(config.modules, target))
        if not allow_live_lean:
            rc, stdout, stderr, elapsed, status = None, "", "Live Lean not allowed.", 0.0, "SKIPPED_LIVE_LEAN_NOT_ALLOWED"
        elif not root or not root.exists() or not env.get("lean_path") or not env.get("lake_path"):
            rc, stdout, stderr, elapsed, status = None, "", "Missing Mathlib root, Lean, or Lake.", 0.0, "SKIPPED_MISSING_LEAN_OR_LAKE"
        else:
            rc, stdout, stderr, elapsed, status = _run_lake_lean(root, lean_file, timeout_sec)
        write_text(stdout_path, stdout)
        write_text(stderr_path, stderr)
        combined = stdout + "\n" + stderr
        parsed_type = parse_check_type(combined, target)
        statement = theorem_statement_from_check(parsed_type)
        axioms = parse_axioms(combined)
        refs = extract_reference_hints(combined, target) if status == "LEAN_ACCEPTED_TARGET" else []
        ref_classes = {ref: classify_reference(ref, target=target) for ref in refs}
        if status == "LEAN_ACCEPTED_TARGET":
            accepted_count += 1

        target_payloads.append(
            {
                "target_id": target_id,
                "declaration_name": target,
                "module": ",".join(config.modules),
                "formal_statement": statement,
                "theorem_shape": parsed_type,
                "status": status,
                "axiom_profile": Counter(axioms),
                "first_seen_run_id": run_id,
                "last_seen_run_id": run_id,
                "metadata": {"pack_id": pack["pack_id"], "basin_id": basin_id},
            }
        )
        observation_payloads.append(
            {
                "observation_id": stable_id("target-observation", run_id, target),
                "run_id": run_id,
                "target_id": target_id,
                "declaration_name": target,
                "status": status,
                "formal_statement": statement,
                "axiom_profile": Counter(axioms),
                "print_refs": refs,
                "reference_classes": ref_classes,
                "elapsed_sec": elapsed,
                "returncode": rc,
                "lean_file": str(lean_file),
                "stdout_path": str(stdout_path),
                "stderr_path": str(stderr_path),
                "metadata": {"#check_is_source_proof_replay": False},
            }
        )
        for ref in refs:
            root_payloads.append(
                {
                    "root_observation_id": stable_id("root-observation", run_id, target, ref),
                    "run_id": run_id,
                    "target_id": target_id,
                    "declaration_name": target,
                    "root_name": ref,
                    "root_class": ref_classes[ref],
                    "source": "#print reference hint",
                    "evidence_level": "ADVISORY_REFERENCE_HINT",
                }
            )
        reason = reasons.setdefault(
            basin_id,
            {
                "reason_id": basin_id,
                "reason_name": reason_name,
                "basin_class": pack["pack_id"],
                "explanation": f"{reason_name} from focused Mathlib digest pack.",
                "support_count": 0,
                "confidence": 0.55,
                "trust_level": "ADVISORY_REASON_FROM_FOCUSED_DIGEST",
                "root_nodes": [],
                "axiom_profile": {},
                "constructor_strategy": constructor_strategy_for_basin(basin_id),
                "metadata": {"pack_name": pack.get("pack_name")},
            },
        )
        if status == "LEAN_ACCEPTED_TARGET":
            reason["support_count"] += 1
            reason["root_nodes"] = sorted(set(reason["root_nodes"]) | set(refs[:20]))
            reason["axiom_profile"] = dict(Counter(reason["axiom_profile"]) + Counter(axioms))
        edges.append(
            {
                "edge_id": stable_id("target-reason-edge", target_id, basin_id),
                "target_id": target_id,
                "reason_id": basin_id,
                "confidence": 0.9 if pack.get("basin_id") else 0.5,
                "evidence": {"pack_id": pack["pack_id"], "status": status},
            }
        )
        if status == "LEAN_ACCEPTED_TARGET" and statement:
            for template_id in constructor_template_ids_for_basin(basin_id):
                proof_body = constructor_proof_body(template_id, target, refs)
                attempt_id = stable_id("constructor-attempt", run_id, target, template_id)
                cdir = run_dir / "constructors" / re.sub(r"[^A-Za-z0-9_]", "_", target)
                cfile = cdir / f"{template_id}.lean"
                cout = cdir / f"{template_id}.stdout.txt"
                cerr = cdir / f"{template_id}.stderr.txt"
                _write_constructor_file(
                    cfile,
                    config.modules,
                    statement,
                    proof_body,
                    attempt_id,
                    target=target,
                    template_id=template_id,
                )
                if not verify_constructors:
                    crc, cstdout, cstderr, celapsed, cstatus = None, "", "Constructor verification disabled.", 0.0, "SKIPPED_CONSTRUCTOR_VERIFICATION_DISABLED"
                elif not allow_live_lean:
                    crc, cstdout, cstderr, celapsed, cstatus = None, "", "Live Lean not allowed.", 0.0, "SKIPPED_LIVE_LEAN_NOT_ALLOWED"
                elif not root or not root.exists() or not env.get("lean_path") or not env.get("lake_path"):
                    crc, cstdout, cstderr, celapsed, cstatus = None, "", "Missing Mathlib root, Lean, or Lake.", 0.0, "SKIPPED_MISSING_LEAN_OR_LAKE"
                else:
                    crc, cstdout, cstderr, celapsed, raw_status = _run_lake_lean(root, cfile, timeout_sec)
                    cstatus = "LEAN_ACCEPTED_CONSTRUCTOR_TEST" if raw_status == "LEAN_ACCEPTED_TARGET" else "LEAN_REJECTED_CONSTRUCTOR_TEST"
                write_text(cout, cstdout)
                write_text(cerr, cstderr)
                error_class = classify_constructor_error(cstderr, cstdout, crc)
                attempt_metadata = {
                    "proof_rechecked_from_source": False,
                    "template_id": template_id,
                    "declaration_name": target,
                    "constructor_generation_mode": "statement_reconstruction_exact_existing" if template_id == "exact_existing" else "statement_reconstruction",
                }
                attempts.append(
                    {
                        "attempt_id": attempt_id,
                        "run_id": run_id,
                        "target_id": target_id,
                        "declaration_name": target,
                        "reason_id": basin_id,
                        "template_id": template_id,
                        "proof_body": proof_body,
                        "status": cstatus,
                        "returncode": crc,
                        "elapsed_sec": celapsed,
                        "lean_file": str(cfile),
                        "stdout_path": str(cout),
                        "stderr_path": str(cerr),
                        "error_excerpt": (cstderr + "\n" + cstdout).strip()[:1000],
                        "trust_level": "VERIFIED_CONSTRUCTOR_TEST" if cstatus == "LEAN_ACCEPTED_CONSTRUCTOR_TEST" else "OBSTRUCTION_TRACE",
                        "metadata": attempt_metadata,
                    }
                )
                if cstatus == "LEAN_ACCEPTED_CONSTRUCTOR_TEST":
                    verified.append(
                        {
                            "constructor_id": stable_id("verified-constructor", basin_id, template_id, proof_body),
                            "reason_id": basin_id,
                            "template_id": template_id,
                            "proof_body": proof_body,
                            "minimal_roots": valid_simp_roots(refs),
                            "target_examples": [target],
                            "first_seen_run_id": run_id,
                            "last_seen_run_id": run_id,
                            "metadata": {
                                "boundary_kind": "lean_constructor_test",
                                "declaration_name": target,
                                "constructor_generation_mode": attempt_metadata["constructor_generation_mode"],
                            },
                        }
                    )
                else:
                    obstructions.append(
                        {
                            "obstruction_id": stable_id("obstruction", attempt_id, error_class),
                            "run_id": run_id,
                            "target_id": target_id,
                            "reason_id": basin_id,
                            "template_id": template_id,
                            "obstruction_class": error_class,
                            "message": f"Constructor `{template_id}` did not verify.",
                            "error_excerpt": (cstderr + "\n" + cstdout).strip()[:1000],
                            "next_action": next_action_for_obstruction(error_class, basin_id),
                            "metadata": {"failed_constructor_is_not_disproof": True, "declaration_name": target},
                        }
                    )

    if verified:
        verified_reasons = {row["reason_id"] for row in verified}
        for reason_id in verified_reasons:
            reasons[reason_id]["trust_level"] = "VERIFIED_CONSTRUCTOR_REASON"

    summary = {
        "target_count": len(target_payloads),
        "accepted_target_count": accepted_count,
        "root_count": len(root_payloads),
        "reason_count": len(reasons),
        "constructor_attempt_count": len(attempts),
        "verified_constructor_count": len(verified),
        "obstruction_count": len(obstructions),
        "live_lean_allowed": allow_live_lean,
        "constructors_verified": verify_constructors,
    }
    payload = {
        "run": {
            "run_id": run_id,
            "created_at": now_iso(),
            "run_name": RUN_NAME,
            "run_version": RUN_VERSION,
            "mathlib_root": env.get("mathlib_root"),
            "mathlib_revision": env.get("mathlib_revision"),
            "lean_toolchain": env.get("lean_toolchain"),
            "modules": config.modules,
            "targets": config.target_names(),
            "pack_id": config.pack_id,
            "config_path": str(pack_config),
            "summary": summary,
        },
        "targets": target_payloads,
        "target_observations": observation_payloads,
        "root_observations": root_payloads,
        "reason_basins": list(reasons.values()),
        "target_reason_edges": edges,
        "constructor_attempts": attempts,
        "verified_constructors": verified,
        "obstructions": obstructions,
    }
    write_digest_payload(conn, payload)
    conn.close()
    write_json(run_dir / "digest_payload.json", payload)
    write_json(run_dir / "digest_summary.json", {"run_id": run_id, **summary, "environment": env})
    write_text(run_dir / "digest_report.md", render_digest_report(run_id, summary, env))
    return {"run_id": run_id, "run_dir": str(run_dir), "summary": summary, "environment": env}


def next_action_for_obstruction(kind: str, basin_id: str) -> str:
    if kind == "malformed_constructor_statement":
        return "Fix constructor theorem statement generation before treating as mathematical obstruction."
    if kind == "unsolved_goals":
        return "Mine goal state and split constructor strategy."
    if kind == "unknown_reference":
        return "Filter roots or add explicit imports."
    if kind == "type_mismatch":
        return "Try equality transport/orientation constructor."
    if kind == "typeclass_failure":
        return "Add instance/typeclass roots or avoid reconstructing inferred theorem types."
    if basin_id in {"basin_nat_set_induction", "basin_nat_lerec_order_recursion"}:
        return "TODO synthesize real induction/leRecOn constructor."
    return "Inspect stderr and refine basin."


def render_digest_report(run_id: str, summary: Mapping[str, Any], env: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# MathGraph Mathlib Digest Run",
            "",
            f"- Run ID: `{run_id}`",
            f"- Targets: {summary['target_count']}",
            f"- Lean accepted targets: {summary['accepted_target_count']}",
            f"- Roots: {summary['root_count']}",
            f"- Reasons: {summary['reason_count']}",
            f"- Constructor attempts: {summary['constructor_attempt_count']}",
            f"- Verified constructors: {summary['verified_constructor_count']}",
            f"- Obstructions: {summary['obstruction_count']}",
            f"- Mathlib root: {env.get('mathlib_root')}",
            f"- Lean: {env.get('lean_path')}",
            f"- Lake: {env.get('lake_path')}",
            "",
            "## Boundary",
            "Lean verifies. MathGraph records, routes, and compounds. #print references are hints, not complete proof dependencies.",
            "Constructor checks reconstruct theorem statements from #check output and verify generated Lean files; they do not reconstruct source proofs.",
        ]
    ) + "\n"
