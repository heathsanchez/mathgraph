"""Deterministic Lean Lawbook Attention over textual digest memory.

This is sparse advisory retrieval.  It changes route suggestions, not truth.
No result from this module is a Lean proof, MathGraph proof, or truth oracle.
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from mathgraph.lean_digest_lawbook_ingestion import run_lean_digest_lawbook_ingestion


STOP_TOKENS = {"a", "an", "and", "by", "for", "in", "is", "of", "on", "or", "the", "to", "with"}
OUTPUT_FILES = (
    "attention_manifest.json",
    "attention_results.csv",
    "attention_results.jsonl",
    "attention_trace.json",
    "route_suggestions.csv",
    "trust_boundary_audit.json",
    "lean_lawbook_attention_report.md",
)


@dataclass(frozen=True)
class LeanAttentionCorpus:
    input_dir: Path
    declarations: tuple[dict[str, Any], ...]
    reason_routes: tuple[dict[str, Any], ...] = ()
    import_edges: tuple[dict[str, Any], ...] = ()
    manifest: dict[str, Any] = field(default_factory=dict)
    trust_audit: dict[str, Any] = field(default_factory=dict)
    detected_files: tuple[str, ...] = ()
    missing_files: tuple[str, ...] = ()
    sqlite_detected: bool = False


@dataclass(frozen=True)
class LeanLawbookAttentionResult:
    out_dir: str
    query_count: int
    declaration_count: int
    result_count: int
    attention_boundary_ok: bool
    can_promote_truth_count: int
    advisory_only_false_count: int
    outputs: dict[str, str] = field(default_factory=dict)
    manifest: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "out_dir": self.out_dir,
            "query_count": self.query_count,
            "declaration_count": self.declaration_count,
            "result_count": self.result_count,
            "attention_boundary_ok": self.attention_boundary_ok,
            "can_promote_truth_count": self.can_promote_truth_count,
            "advisory_only_false_count": self.advisory_only_false_count,
            "outputs": dict(self.outputs),
            "manifest": dict(self.manifest),
        }


def tokenize(text: str) -> tuple[str, ...]:
    camel = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", str(text))
    raw = re.split(r"[^A-Za-z0-9]+", camel.lower())
    return tuple(tok for tok in raw if len(tok) > 1 and tok not in STOP_TOKENS)


def load_lawbook_entries_from_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_declaration_inventory(path: Path) -> list[dict[str, Any]]:
    return _read_csv(path)


def load_reason_routes(path: Path) -> list[dict[str, Any]]:
    return _read_csv(path)


def load_import_graph(path: Path) -> list[dict[str, Any]]:
    return _read_csv(path)


def load_attention_corpus(input_dir: str | Path) -> LeanAttentionCorpus:
    input_path = Path(input_dir)
    if not input_path.exists():
        raise FileNotFoundError(input_path)
    candidates = {
        "declarations": ("imported_declarations.csv", "declaration_inventory.csv", "lawbook_entries.csv"),
        "reason_routes": ("imported_reason_routes.csv", "reason_atlas_routes.csv"),
        "import_edges": ("imported_import_edges.csv", "import_graph.csv"),
        "manifest": ("ingestion_manifest.json", "project_manifest.json", "attention_manifest.json"),
        "trust_audit": ("trust_boundary_audit.json",),
        "lawbook_jsonl": ("lawbook_entries.jsonl",),
    }
    detected: list[str] = []
    missing: list[str] = []

    declarations_path = _first_existing(input_path, candidates["declarations"])
    if declarations_path is None:
        jsonl = _first_existing(input_path, candidates["lawbook_jsonl"])
        declarations = _lawbook_jsonl_to_declarations(load_lawbook_entries_from_jsonl(jsonl)) if jsonl else []
        if jsonl:
            detected.append(jsonl.name)
        else:
            missing.extend(candidates["declarations"])
    else:
        declarations = load_declaration_inventory(declarations_path)
        detected.append(declarations_path.name)

    routes_path = _first_existing(input_path, candidates["reason_routes"])
    reason_routes = load_reason_routes(routes_path) if routes_path else []
    detected.extend([routes_path.name] if routes_path else [])
    if routes_path is None:
        missing.extend(candidates["reason_routes"])

    imports_path = _first_existing(input_path, candidates["import_edges"])
    import_edges = load_import_graph(imports_path) if imports_path else []
    detected.extend([imports_path.name] if imports_path else [])
    if imports_path is None:
        missing.extend(candidates["import_edges"])

    manifest_path = _first_existing(input_path, candidates["manifest"])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path else {}
    detected.extend([manifest_path.name] if manifest_path else [])
    if manifest_path is None:
        missing.extend(candidates["manifest"])

    audit_path = _first_existing(input_path, candidates["trust_audit"])
    trust_audit = json.loads(audit_path.read_text(encoding="utf-8")) if audit_path else {}
    detected.extend([audit_path.name] if audit_path else [])
    if audit_path is None:
        missing.extend(candidates["trust_audit"])

    sqlite_detected = any((input_path / name).exists() for name in ("lean_digest_lawbook.sqlite", "lawbook.sqlite"))
    if sqlite_detected:
        detected.append("lean_digest_lawbook.sqlite")
    return LeanAttentionCorpus(
        input_dir=input_path,
        declarations=tuple(_normalize_declaration(row) for row in declarations),
        reason_routes=tuple(reason_routes),
        import_edges=tuple(import_edges),
        manifest=manifest,
        trust_audit=trust_audit,
        detected_files=tuple(sorted(set(detected))),
        missing_files=tuple(sorted(set(missing))),
        sqlite_detected=sqlite_detected,
    )


def run_lean_lawbook_attention(
    out_dir: str | Path,
    *,
    digest_dir: str | Path | None = None,
    queries: Sequence[str] | None = None,
    fallback_demo: bool = False,
    top_k: int = 5,
) -> LeanLawbookAttentionResult:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    if fallback_demo or digest_dir is None:
        fixture_dir = out / "fallback_ingestion"
        run_lean_digest_lawbook_ingestion(fixture_dir, fallback_demo=True)
        corpus = load_attention_corpus(fixture_dir)
        input_source = str(fixture_dir)
        query_list = list(queries or ("Nat addition associativity", "commutativity of addition", "unsafe declaration"))
    else:
        corpus = load_attention_corpus(digest_dir)
        input_source = str(digest_dir)
        query_list = list(queries or ("Nat addition associativity",))
    results = run_attention_queries(corpus, query_list, top_k=top_k)
    route_rows = [_route_row(row) for row in results]
    audit = build_attention_trust_audit(results, corpus)
    manifest = {
        "input_source": input_source,
        "query_count": len(query_list),
        "declaration_count": len(corpus.declarations),
        "result_count": len(results),
        "detected_files": list(corpus.detected_files),
        "missing_files": list(corpus.missing_files),
        "sqlite_detected": corpus.sqlite_detected,
        "boundary_type": "textual_digest",
        "advisory_only": True,
        "can_promote_truth": False,
    }
    outputs = {name: str(out / name) for name in OUTPUT_FILES}
    (out / "attention_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    _write_csv(out / "attention_results.csv", results)
    _write_jsonl(out / "attention_results.jsonl", results)
    (out / "attention_trace.json").write_text(json.dumps({"queries": query_list, "results": results}, indent=2, sort_keys=True), encoding="utf-8")
    _write_csv(out / "route_suggestions.csv", route_rows)
    (out / "trust_boundary_audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True), encoding="utf-8")
    (out / "lean_lawbook_attention_report.md").write_text(_markdown(manifest, audit, results), encoding="utf-8")
    return LeanLawbookAttentionResult(
        out_dir=str(out),
        query_count=len(query_list),
        declaration_count=len(corpus.declarations),
        result_count=len(results),
        attention_boundary_ok=bool(audit["attention_boundary_ok"]),
        can_promote_truth_count=int(audit["can_promote_truth_count"]),
        advisory_only_false_count=int(audit["advisory_only_false_count"]),
        outputs=outputs,
        manifest=manifest,
    )


def run_attention_queries(corpus: LeanAttentionCorpus, queries: Sequence[str], *, top_k: int = 5) -> list[dict[str, Any]]:
    route_by_decl = _route_by_declaration(corpus.reason_routes)
    import_degree = _import_degree(corpus.import_edges)
    rows: list[dict[str, Any]] = []
    for q_index, query in enumerate(queries):
        scored = []
        for decl in corpus.declarations:
            row = score_declaration(query, decl, route_by_decl.get(str(decl.get("declaration_id", ""))), import_degree)
            row["query_id"] = f"q{q_index:03d}"
            row["query_text"] = query
            scored.append(row)
        scored.sort(key=lambda row: (-float(row["attention_score"]), str(row.get("name", "")), str(row.get("declaration_id", ""))))
        for rank, row in enumerate(scored[: max(1, top_k)], start=1):
            row["rank"] = rank
            rows.append(row)
    return rows


def score_declaration(
    query: str,
    declaration: Mapping[str, Any],
    route: Mapping[str, Any] | None = None,
    import_degree: Mapping[str, int] | None = None,
) -> dict[str, Any]:
    q_tokens = set(tokenize(query))
    name = str(declaration.get("name", ""))
    statement = str(declaration.get("statement_text", ""))
    name_tokens = set(tokenize(name))
    statement_tokens = set(tokenize(statement))
    exact_name_match = 1.0 if query.strip().lower() == name.lower() or name.lower() in query.lower() else 0.0
    name_j = _jaccard(q_tokens, name_tokens)
    statement_j = _jaccard(q_tokens, statement_tokens)
    namespace_overlap = _namespace_overlap(q_tokens, name)
    route_type = _route_type_for(declaration, route)
    reason_route_boost = 1.0 if route else 0.0
    import_route_boost = min((import_degree or {}).get(str(declaration.get("file", "")), 0), 3) / 3.0
    trust_adjustment = _trust_adjustment(str(declaration.get("trust_status", "")))
    safety_penalty = _safety_penalty(declaration)
    kind_boost = _kind_boost(q_tokens, str(declaration.get("declaration_kind", "")))
    score = (
        3.0 * exact_name_match
        + 2.0 * name_j
        + 1.5 * statement_j
        + 1.0 * namespace_overlap
        + 0.5 * import_route_boost
        + 0.5 * reason_route_boost
        + kind_boost
        + trust_adjustment
        - safety_penalty
    )
    components = {
        "exact_name_match": exact_name_match,
        "name_token_jaccard": name_j,
        "statement_token_jaccard": statement_j,
        "namespace_overlap": namespace_overlap,
        "import_route_boost": import_route_boost,
        "reason_route_boost": reason_route_boost,
        "kind_boost": kind_boost,
        "trust_adjustment": trust_adjustment,
        "safety_penalty": safety_penalty,
    }
    notes = _notes_for(declaration)
    return {
        "query_id": "",
        "query_text": query,
        "rank": 0,
        "declaration_id": declaration.get("declaration_id", ""),
        "declaration_kind": declaration.get("declaration_kind", ""),
        "name": name,
        "file": declaration.get("file", ""),
        "line": _int(declaration.get("line")),
        "statement_text": statement,
        "trust_status": declaration.get("trust_status", ""),
        "provenance_type": declaration.get("provenance_type", "imported_lean_project"),
        "boundary_type": declaration.get("boundary_type", "textual_digest"),
        "attention_score": round(score, 6),
        "score_components_json": json.dumps(components, sort_keys=True),
        "route_suggestion": route_type,
        "why_retrieved": _why(q_tokens, name_tokens, statement_tokens, route_type, notes),
        "action_suggestion": _action_suggestion(route_type),
        "advisory_only": True,
        "can_promote_truth": False,
        "notes": notes,
    }


def build_attention_trust_audit(results: Sequence[Mapping[str, Any]], corpus: LeanAttentionCorpus | None = None) -> dict[str, Any]:
    violations = []
    can_promote = 0
    advisory_false = 0
    verified_textual = 0
    for row in results:
        if _truthy(row.get("can_promote_truth")):
            can_promote += 1
            violations.append({"declaration_id": row.get("declaration_id", ""), "reason": "attention_can_promote_truth"})
        if not _truthy(row.get("advisory_only")):
            advisory_false += 1
            violations.append({"declaration_id": row.get("declaration_id", ""), "reason": "attention_not_advisory"})
        if row.get("trust_status") == "VERIFIED_PROOF" and str(row.get("boundary_type", "")).startswith("textual"):
            verified_textual += 1
            violations.append({"declaration_id": row.get("declaration_id", ""), "reason": "textual_result_marked_verified_proof"})
    unsafe_count = sum(1 for row in results if "unsafe" in str(row.get("trust_status", "")).lower() or "unsafe" in str(row.get("route_suggestion", "")).lower())
    axiom_count = sum(1 for row in results if "axiom" in str(row.get("trust_status", "")).lower() or "axiom" in str(row.get("route_suggestion", "")).lower())
    incomplete_count = sum(1 for row in results if row.get("trust_status") == "incomplete_proof")
    textual_count = sum(1 for row in results if str(row.get("boundary_type", "textual_digest")).startswith("textual"))
    return {
        "attention_boundary_ok": not violations,
        "can_promote_truth_count": can_promote,
        "advisory_only_false_count": advisory_false,
        "unsafe_count": unsafe_count,
        "axiom_count": axiom_count,
        "incomplete_proof_count": incomplete_count,
        "textual_only_count": textual_count,
        "lean_execution_confirmed": bool((corpus.trust_audit if corpus else {}).get("lean_execution_confirmed", False)),
        "violations": violations,
        "warning_count": unsafe_count + axiom_count + incomplete_count,
        "trust_boundary_statement": "Lean Lawbook Attention changes routing, not truth; textual digest results cannot become VERIFIED_PROOF.",
    }


def fallback_demo_corpus_dir(out_dir: Path) -> Path:
    fixture = out_dir / "fallback_ingestion"
    run_lean_digest_lawbook_ingestion(fixture, fallback_demo=True)
    return fixture


def _normalize_declaration(row: Mapping[str, Any]) -> dict[str, Any]:
    replay = _parse_json(row.get("replay_hint_json", "{}"))
    name = row.get("name") or replay.get("name", "")
    return {
        "declaration_id": row.get("declaration_id") or row.get("entry_id") or "",
        "declaration_kind": row.get("declaration_kind", ""),
        "name": name,
        "file": row.get("file") or replay.get("file", ""),
        "line": _int(row.get("line") or replay.get("line", 0)),
        "statement_text": row.get("statement_text", ""),
        "trust_status": row.get("trust_status", ""),
        "provenance_type": row.get("provenance_type", "imported_lean_project"),
        "boundary_type": row.get("boundary_type", "textual_digest"),
        "has_sorry": _truthy(row.get("has_sorry")),
        "has_admit": _truthy(row.get("has_admit")),
        "has_axiom": _truthy(row.get("has_axiom")) or row.get("declaration_kind") == "axiom",
        "has_unsafe": _truthy(row.get("has_unsafe")),
        "advisory_only": True,
        "can_promote_truth": False,
    }


def _lawbook_jsonl_to_declarations(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        replay = row.get("replay_hint") if isinstance(row.get("replay_hint"), dict) else {}
        out.append(
            {
                "declaration_id": row.get("entry_id", ""),
                "declaration_kind": row.get("declaration_kind", ""),
                "name": row.get("name", ""),
                "file": replay.get("file", ""),
                "line": replay.get("line", 0),
                "statement_text": row.get("statement_text", ""),
                "trust_status": row.get("trust_status", ""),
                "provenance_type": row.get("provenance_type", "imported_lean_project"),
                "boundary_type": row.get("boundary_type", "textual_digest"),
            }
        )
    return out


def _route_by_declaration(routes: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    out = {}
    for row in routes:
        decl = str(row.get("declaration_id", ""))
        if decl and decl not in out:
            out[decl] = row
    return out


def _import_degree(imports: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    degree: dict[str, int] = {}
    for row in imports:
        file = str(row.get("source_file") or row.get("file") or "")
        if file:
            degree[file] = degree.get(file, 0) + 1
    return degree


def _route_type_for(declaration: Mapping[str, Any], route: Mapping[str, Any] | None) -> str:
    if _truthy(declaration.get("has_unsafe")) or "unsafe" in str(declaration.get("trust_status", "")).lower():
        return "unsafe_boundary_warning"
    if _truthy(declaration.get("has_axiom")) or "axiom" in str(declaration.get("trust_status", "")).lower():
        return "axiom_boundary_candidate"
    if declaration.get("trust_status") == "incomplete_proof":
        return "sorry_repair_candidate"
    if route:
        return str(route.get("route_type") or route.get("route_suggestion") or "textual_digest_review_route")
    if declaration.get("declaration_kind") in {"theorem", "lemma", "example"}:
        return "theorem_cluster_route"
    if declaration.get("declaration_kind") == "def":
        return "definition_lookup_route"
    return "textual_digest_review_route"


def _action_suggestion(route_type: str) -> str:
    if route_type in {"theorem_cluster_route", "definition_lookup_route", "import_dependency_route"}:
        return "review_imported_textual_digest_then_optionally_contact_lean_verifier"
    if route_type == "sorry_repair_candidate":
        return "queue_sorry_repair_candidate_without_truth_promotion"
    if route_type == "axiom_boundary_candidate":
        return "record_axiom_boundary_before_any_verifier_route"
    if route_type == "unsafe_boundary_warning":
        return "inspect_unsafe_boundary_before_reuse"
    return "textual_digest_review_route"


def _trust_adjustment(trust_status: str) -> float:
    return {
        "imported_verified_candidate": 0.25,
        "imported_definition_metadata": 0.05,
        "incomplete_proof": -0.75,
        "trusted_assumption_or_external_axiom": -1.0,
        "unsafe_requires_warning": -1.25,
    }.get(trust_status, 0.0)


def _safety_penalty(declaration: Mapping[str, Any]) -> float:
    penalty = 0.0
    if _truthy(declaration.get("has_sorry")) or _truthy(declaration.get("has_admit")) or declaration.get("trust_status") == "incomplete_proof":
        penalty += 1.0
    if _truthy(declaration.get("has_axiom")) or "axiom" in str(declaration.get("trust_status", "")).lower():
        penalty += 1.25
    if _truthy(declaration.get("has_unsafe")) or "unsafe" in str(declaration.get("trust_status", "")).lower():
        penalty += 1.5
    return penalty


def _kind_boost(query_tokens: set[str], kind: str) -> float:
    if kind in {"theorem", "lemma", "example"} and query_tokens & {"theorem", "lemma", "proof", "assoc", "comm"}:
        return 0.2
    if kind == "def" and query_tokens & {"def", "definition", "lookup"}:
        return 0.2
    return 0.0


def _jaccard(a: set[str], b: set[str]) -> float:
    return len(a & b) / len(a | b) if a and b else 0.0


def _namespace_overlap(query_tokens: set[str], name: str) -> float:
    parts = set(tokenize(name.replace(".", " ")))
    return len(query_tokens & parts) / max(len(parts), 1) if parts else 0.0


def _why(query: set[str], name: set[str], statement: set[str], route: str, notes: str) -> str:
    bits = []
    if query & name:
        bits.append("name token overlap: " + ",".join(sorted(query & name)))
    if query & statement:
        bits.append("statement token overlap: " + ",".join(sorted(query & statement)[:6]))
    bits.append(f"route={route}")
    if notes:
        bits.append(notes)
    return " | ".join(bits)


def _notes_for(declaration: Mapping[str, Any]) -> str:
    status = str(declaration.get("trust_status", ""))
    if status == "incomplete_proof":
        return "Incomplete proof; advisory repair candidate only."
    if "axiom" in status:
        return "Axiom/assumption boundary; not a proof."
    if "unsafe" in status:
        return "Unsafe declaration warning."
    if status == "imported_verified_candidate":
        return "Imported textual candidate, not MathGraph-proven."
    return "Textual digest memory only."


def _route_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "query_id": row.get("query_id", ""),
        "declaration_id": row.get("declaration_id", ""),
        "name": row.get("name", ""),
        "route_suggestion": row.get("route_suggestion", ""),
        "action_suggestion": row.get("action_suggestion", ""),
        "advisory_only": True,
        "can_promote_truth": False,
        "attention_score": row.get("attention_score", 0.0),
    }


def _first_existing(root: Path, names: Sequence[str]) -> Path | None:
    for name in names:
        path = root / name
        if path.exists():
            return path
    return None


def _read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


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
    path.write_text("".join(json.dumps(row, sort_keys=True, default=str) + "\n" for row in rows), encoding="utf-8")


def _csv_value(value: Any) -> Any:
    if isinstance(value, (dict, list, tuple, set)):
        return json.dumps(value, sort_keys=True, default=str)
    return value


def _parse_json(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    try:
        return json.loads(str(value))
    except Exception:
        return {}


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _int(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def _markdown(manifest: Mapping[str, Any], audit: Mapping[str, Any], results: Sequence[Mapping[str, Any]]) -> str:
    lines = [
        "# Lean Lawbook Attention v1",
        "",
        f"- input source: `{manifest.get('input_source')}`",
        f"- query count: `{manifest.get('query_count')}`",
        f"- declaration count: `{manifest.get('declaration_count')}`",
        f"- result count: `{manifest.get('result_count')}`",
        f"- attention_boundary_ok: `{audit.get('attention_boundary_ok')}`",
        f"- can_promote_truth_count: `{audit.get('can_promote_truth_count')}`",
        f"- warning_count: `{audit.get('warning_count')}`",
        "",
        "## Top Results",
    ]
    for row in results:
        if int(row.get("rank", 0)) <= 3:
            lines.append(
                f"- `{row.get('query_id')}` rank {row.get('rank')}: `{row.get('name')}` "
                f"score `{row.get('attention_score')}` route `{row.get('route_suggestion')}`"
            )
    lines.extend(
        [
            "",
            "## What Attention Can Do",
            "",
            "Lean Lawbook Attention can retrieve imported textual declarations and suggest advisory routes such as import dependency review, theorem clustering, sorry repair, axiom boundary review, unsafe boundary warning, or Lean verifier contact candidates.",
            "",
            "## What Attention Cannot Do",
            "",
            "This is not H-tilt, theorem proving, proof synthesis, or a truth oracle. Attention changes routing, not truth. Imported declarations are not MathGraph-proven, textual digest entries cannot become `VERIFIED_PROOF`, and advisory route suggestions cannot promote truth.",
            "",
            "## Next Step",
            "",
            "Run verifier-contact evaluation for any declaration that should move beyond textual digest memory.",
        ]
    )
    return "\n".join(lines) + "\n"
