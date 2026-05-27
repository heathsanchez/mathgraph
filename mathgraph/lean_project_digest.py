"""Lightweight textual digest for Lean projects.

The digest is intentionally conservative: it scans Lean source text for
declarations, imports, and trust-boundary markers, then emits Lawbook and Reason
Atlas-ready metadata.  It does not run theorem proving or claim MathGraph has
proved imported declarations.
"""

from __future__ import annotations

import csv
import json
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


DECL_RE = re.compile(r"^\s*(?P<unsafe>unsafe\s+)?(?P<kind>theorem|lemma|def|example|axiom|opaque)\b(?:\s+(?P<name>[A-Za-z0-9_'.]+))?(?P<rest>.*)$")
IMPORT_RE = re.compile(r"^\s*import\s+(?P<module>[A-Za-z0-9_'.]+)")
MARKERS = ("sorry", "admit", "axiom", "unsafe")


@dataclass(frozen=True)
class LeanDeclarationRecord:
    declaration_id: str
    file: str
    line: int
    declaration_kind: str
    name: str
    statement_text: str
    imports: tuple[str, ...]
    has_sorry: bool
    has_admit: bool
    has_axiom: bool
    has_unsafe: bool
    trust_status: str
    provenance_type: str = "imported_lean_project"
    can_promote_truth: bool = False
    advisory_only: bool = True
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "declaration_id": self.declaration_id,
            "file": self.file,
            "line": self.line,
            "declaration_kind": self.declaration_kind,
            "name": self.name,
            "statement_text": self.statement_text,
            "imports": list(self.imports),
            "has_sorry": self.has_sorry,
            "has_admit": self.has_admit,
            "has_axiom": self.has_axiom,
            "has_unsafe": self.has_unsafe,
            "trust_status": self.trust_status,
            "provenance_type": self.provenance_type,
            "can_promote_truth": self.can_promote_truth,
            "advisory_only": self.advisory_only,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class LeanProjectDigestReport:
    mode: str
    project_root: str
    declaration_count: int
    import_count: int
    incomplete_proof_count: int
    axiom_count: int
    unsafe_count: int
    can_promote_truth_count: int
    advisory_boundary_ok: bool
    outputs: dict[str, str] = field(default_factory=dict)
    manifest: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "project_root": self.project_root,
            "declaration_count": self.declaration_count,
            "import_count": self.import_count,
            "incomplete_proof_count": self.incomplete_proof_count,
            "axiom_count": self.axiom_count,
            "unsafe_count": self.unsafe_count,
            "can_promote_truth_count": self.can_promote_truth_count,
            "advisory_boundary_ok": self.advisory_boundary_ok,
            "outputs": dict(self.outputs),
            "manifest": dict(self.manifest),
        }


def run_lean_project_digest(
    out_dir: str | Path,
    *,
    fallback_demo: bool = False,
    project_root: str | Path | None = None,
) -> LeanProjectDigestReport:
    """Run a textual Lean project digest and write report artifacts."""

    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    if fallback_demo or project_root is None:
        mode = "fallback-demo"
        root_label = "<fallback-demo>"
        files = _fallback_demo_files()
    else:
        mode = "project-root"
        root = Path(project_root)
        files = _scan_project_files(root)
        root_label = str(root)
    records, imports = digest_lean_files(files)
    lawbook_entries = build_lawbook_entries(records)
    reason_routes = build_reason_atlas_routes(records)
    audit = build_trust_boundary_audit(records)
    manifest = build_project_manifest(mode=mode, project_root=root_label, files=files, records=records, imports=imports)
    outputs = {
        "project_manifest": str(output / "project_manifest.json"),
        "declaration_inventory": str(output / "declaration_inventory.csv"),
        "import_graph": str(output / "import_graph.csv"),
        "trust_boundary_audit": str(output / "trust_boundary_audit.json"),
        "lawbook_entries": str(output / "lawbook_entries.jsonl"),
        "reason_atlas_routes": str(output / "reason_atlas_routes.csv"),
        "report_md": str(output / "lean_project_digest_report.md"),
    }
    report = LeanProjectDigestReport(
        mode=mode,
        project_root=root_label,
        declaration_count=len(records),
        import_count=len(imports),
        incomplete_proof_count=sum(1 for row in records if row.has_sorry or row.has_admit),
        axiom_count=sum(1 for row in records if row.has_axiom),
        unsafe_count=sum(1 for row in records if row.has_unsafe),
        can_promote_truth_count=sum(1 for row in records if row.can_promote_truth),
        advisory_boundary_ok=bool(audit["advisory_boundary_ok"]),
        outputs=outputs,
        manifest=manifest,
    )
    (output / "project_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    _write_csv(output / "declaration_inventory.csv", [row.to_dict() for row in records])
    _write_csv(output / "import_graph.csv", imports)
    (output / "trust_boundary_audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True), encoding="utf-8")
    _write_jsonl(output / "lawbook_entries.jsonl", lawbook_entries)
    _write_csv(output / "reason_atlas_routes.csv", reason_routes)
    (output / "lean_project_digest_report.md").write_text(_markdown(report, audit), encoding="utf-8")
    return report


def digest_lean_files(files: Sequence[Mapping[str, str]]) -> tuple[list[LeanDeclarationRecord], list[dict[str, Any]]]:
    records: list[LeanDeclarationRecord] = []
    import_edges: list[dict[str, Any]] = []
    for item in files:
        file_label = str(item["file"])
        text = str(item["text"])
        lines = text.splitlines()
        imports = tuple(_extract_imports(lines))
        for module in imports:
            import_edges.append({"file": file_label, "import": module, "advisory_only": True, "can_promote_truth": False})
        for line_no, line in enumerate(lines, start=1):
            match = DECL_RE.match(line)
            if not match:
                continue
            kind = match.group("kind")
            name = match.group("name") or f"anonymous_{line_no}"
            window = _declaration_window(lines, line_no - 1)
            markers = _marker_flags(window, kind)
            trust_status, notes = _trust_status(kind, markers)
            records.append(
                LeanDeclarationRecord(
                    declaration_id=f"{file_label}:{line_no}:{kind}:{name}",
                    file=file_label,
                    line=line_no,
                    declaration_kind=kind,
                    name=name,
                    statement_text=_statement_text(line),
                    imports=imports,
                    has_sorry=markers["has_sorry"],
                    has_admit=markers["has_admit"],
                    has_axiom=markers["has_axiom"],
                    has_unsafe=markers["has_unsafe"],
                    trust_status=trust_status,
                    notes=notes,
                )
            )
    return records, import_edges


def build_lawbook_entries(records: Sequence[LeanDeclarationRecord]) -> list[dict[str, Any]]:
    return [
        {
            "entry_id": record.declaration_id,
            "name": record.name,
            "declaration_kind": record.declaration_kind,
            "trust_status": record.trust_status,
            "provenance_type": "imported_lean_project",
            "boundary_type": "textual_digest",
            "can_promote_truth": False,
            "advisory_only": True,
            "statement_text": record.statement_text,
            "replay_hint": {"file": record.file, "line": record.line, "name": record.name},
            "notes": record.notes,
        }
        for record in records
    ]


def build_reason_atlas_routes(records: Sequence[LeanDeclarationRecord]) -> list[dict[str, Any]]:
    routes: list[dict[str, Any]] = []
    for record in records:
        if record.has_sorry or record.has_admit:
            route = "sorry_repair_candidate"
        elif record.has_axiom:
            route = "axiom_boundary_candidate"
        elif record.imports:
            route = "import_dependency_route"
        elif record.declaration_kind in {"theorem", "lemma"}:
            route = "theorem_cluster_route"
        else:
            route = "declaration_inventory_route"
        routes.append(
            {
                "declaration_id": record.declaration_id,
                "route_suggestion": route,
                "trust_status": record.trust_status,
                "advisory_only": True,
                "can_promote_truth": False,
                "notes": "Route suggestion only; no textual digest route is a verifier.",
            }
        )
    return routes


def build_trust_boundary_audit(records: Sequence[LeanDeclarationRecord]) -> dict[str, Any]:
    violations = []
    for record in records:
        if record.can_promote_truth:
            violations.append({"declaration_id": record.declaration_id, "reason": "textual_digest_can_promote_truth"})
        if (record.has_sorry or record.has_admit) and record.trust_status != "incomplete_proof":
            violations.append({"declaration_id": record.declaration_id, "reason": "sorry_admit_marked_verified"})
        if record.has_axiom and record.trust_status != "trusted_assumption_or_external_axiom":
            violations.append({"declaration_id": record.declaration_id, "reason": "axiom_marked_proof"})
    return {
        "declaration_count": len(records),
        "textual_parsing_is_advisory": True,
        "lean_execution_confirmed": False,
        "can_promote_truth_count": sum(1 for row in records if row.can_promote_truth),
        "incomplete_proof_count": sum(1 for row in records if row.has_sorry or row.has_admit),
        "axiom_count": sum(1 for row in records if row.has_axiom),
        "unsafe_count": sum(1 for row in records if row.has_unsafe),
        "violations": violations,
        "advisory_boundary_ok": not violations,
        "trust_boundary": "No textual digest declaration can become VERIFIED_PROOF without Lean/verifier execution.",
    }


def build_project_manifest(
    *,
    mode: str,
    project_root: str,
    files: Sequence[Mapping[str, str]],
    records: Sequence[LeanDeclarationRecord],
    imports: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    return {
        "mode": mode,
        "project_root": project_root,
        "lean_available": shutil.which("lean") is not None,
        "boundary_type": "textual_digest",
        "provenance_type": "imported_lean_project",
        "file_count": len(files),
        "declaration_count": len(records),
        "import_edge_count": len(imports),
        "can_promote_truth": False,
        "advisory_only": True,
        "files": [{"file": item["file"], "size_bytes": len(str(item["text"]).encode("utf-8"))} for item in files],
    }


def _scan_project_files(root: Path) -> list[dict[str, str]]:
    if not root.exists():
        raise FileNotFoundError(root)
    files = []
    for path in sorted(root.rglob("*.lean")):
        if ".lake" in path.parts or "build" in path.parts:
            continue
        files.append({"file": str(path.relative_to(root)), "text": path.read_text(encoding="utf-8")})
    return files


def _fallback_demo_files() -> list[dict[str, str]]:
    return [
        {
            "file": "Demo/Basic.lean",
            "text": "\n".join(
                [
                    "import Mathlib.Data.Nat.Basic",
                    "",
                    "theorem add_zero_demo (n : Nat) : n + 0 = n := by",
                    "  simpa",
                    "",
                    "lemma unfinished_demo (n : Nat) : n = n := by",
                    "  sorry",
                    "",
                    "axiom external_axiom_demo : Nat",
                    "",
                    "unsafe def risky_demo : Nat := 1",
                    "",
                    "def helper_demo : Nat := 0",
                    "",
                    "example : True := by",
                    "  trivial",
                ]
            ),
        }
    ]


def _extract_imports(lines: Iterable[str]) -> list[str]:
    imports = []
    for line in lines:
        match = IMPORT_RE.match(line)
        if match:
            imports.append(match.group("module"))
    return imports


def _marker_flags(window: str, kind: str) -> dict[str, bool]:
    lower = window.lower()
    return {
        "has_sorry": bool(re.search(r"\bsorry\b", lower)),
        "has_admit": bool(re.search(r"\badmit\b", lower)),
        "has_axiom": kind == "axiom" or bool(re.search(r"^\s*axiom\b", window, flags=re.MULTILINE)),
        "has_unsafe": bool(re.search(r"\bunsafe\b", lower)),
    }


def _declaration_window(lines: Sequence[str], start: int) -> str:
    selected = [lines[start]]
    for line in lines[start + 1 :]:
        if DECL_RE.match(line) or IMPORT_RE.match(line):
            break
        if line.strip() == "":
            selected.append(line)
            continue
        if line.startswith((" ", "\t")):
            selected.append(line)
            continue
        break
    return "\n".join(selected)


def _trust_status(kind: str, markers: Mapping[str, bool]) -> tuple[str, str]:
    if markers["has_sorry"] or markers["has_admit"]:
        return "incomplete_proof", "Contains sorry/admit; not verified."
    if markers["has_axiom"]:
        return "trusted_assumption_or_external_axiom", "Axiom/opaque boundary is an assumption, not a proof."
    if markers["has_unsafe"]:
        return "unsafe_requires_warning", "Unsafe declaration requires explicit warning."
    if kind in {"theorem", "lemma", "example"}:
        return "imported_verified_candidate", "Textually complete Lean declaration; imported candidate only until Lean check is run."
    return "imported_definition_metadata", "Definition metadata from textual digest."


def _statement_text(line: str) -> str:
    text = line.strip()
    if ":=" in text:
        text = text.split(":=", 1)[0].strip()
    return text


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    keys: list[str] = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _csv_value(row.get(key)) for key in keys})


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _csv_value(value: Any) -> Any:
    if isinstance(value, (dict, list, tuple, set)):
        return json.dumps(value, sort_keys=True)
    return value


def _markdown(report: LeanProjectDigestReport, audit: Mapping[str, Any]) -> str:
    return f"""# Lean Project Digest v0

- mode: `{report.mode}`
- declaration_count: `{report.declaration_count}`
- import_count: `{report.import_count}`
- incomplete_proof_count: `{report.incomplete_proof_count}`
- axiom_count: `{report.axiom_count}`
- unsafe_count: `{report.unsafe_count}`
- can_promote_truth_count: `{report.can_promote_truth_count}`
- advisory_boundary_ok: `{report.advisory_boundary_ok}`

This is a textual digest, not a Lean verification run. Imported theorem and
lemma declarations may be useful as Lawbook/Reason Atlas metadata, but they are
`imported_verified_candidate`, not MathGraph-proven results. Sorry/admit
declarations are incomplete, axioms are assumptions, unsafe declarations require
warnings, and no textual-only digest entry can become `VERIFIED_PROOF`.

Trust boundary: {audit.get("trust_boundary", "")}
"""
