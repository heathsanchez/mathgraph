import csv
import json
import sqlite3

from mathgraph.lean_digest_lawbook_ingestion import load_digest_dir, run_lean_digest_lawbook_ingestion
from mathgraph.lean_project_digest import run_lean_project_digest


EXPECTED_FILES = {
    "lean_digest_lawbook.sqlite",
    "ingestion_manifest.json",
    "imported_declarations.csv",
    "imported_import_edges.csv",
    "imported_trust_boundaries.csv",
    "imported_reason_routes.csv",
    "lawbook_ingestion_report.md",
}


def test_fallback_demo_ingests_digest_and_writes_sqlite_tables(tmp_path) -> None:
    result = run_lean_digest_lawbook_ingestion(tmp_path / "ingest", fallback_demo=True)
    assert result.declaration_count == 6
    assert result.import_edge_count == 1
    assert result.trust_boundary_count == 6
    assert result.reason_route_count == 6
    assert result.can_promote_truth_count == 0
    assert result.advisory_boundary_ok is True
    assert EXPECTED_FILES <= {path.name for path in (tmp_path / "ingest").iterdir()}

    conn = sqlite3.connect(result.sqlite_path)
    try:
        tables = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        }
        assert {
            "imported_declarations",
            "import_edges",
            "trust_boundaries",
            "reason_routes",
            "ingestion_runs",
        } <= tables
        assert conn.execute("SELECT COUNT(*) FROM imported_declarations").fetchone()[0] == 6
        assert conn.execute("SELECT COUNT(*) FROM reason_routes WHERE advisory_only=1 AND can_promote_truth=0").fetchone()[0] == 6
    finally:
        conn.close()


def test_imported_records_preserve_trust_status_and_no_truth_promotion(tmp_path) -> None:
    digest_dir = tmp_path / "digest"
    run_lean_project_digest(digest_dir, fallback_demo=True)
    result = run_lean_digest_lawbook_ingestion(tmp_path / "ingest", digest_dir=digest_dir)
    declarations = list(csv.DictReader(open(result.imported_declarations_path, encoding="utf-8")))
    by_name = {row["name"]: row for row in declarations}
    assert {row["can_promote_truth"] for row in declarations} == {"False"}
    assert {row["advisory_only"] for row in declarations} == {"True"}
    assert by_name["unfinished_demo"]["trust_status"] == "incomplete_proof"
    assert by_name["external_axiom_demo"]["trust_status"] == "trusted_assumption_or_external_axiom"
    assert by_name["risky_demo"]["trust_status"] == "unsafe_requires_warning"

    boundaries = list(csv.DictReader(open(result.imported_trust_boundaries_path, encoding="utf-8")))
    risky = next(row for row in boundaries if row["name"] == "risky_demo")
    assert json.loads(risky["warning_flags_json"])["has_unsafe"] is True
    assert {row["can_promote_truth"] for row in boundaries} == {"False"}


def test_missing_optional_files_are_manifested_without_crashing(tmp_path) -> None:
    digest_dir = tmp_path / "digest"
    run_lean_project_digest(digest_dir, fallback_demo=True)
    for name in ("import_graph.csv", "trust_boundary_audit.json", "lawbook_entries.jsonl", "reason_atlas_routes.csv"):
        (digest_dir / name).unlink()
    bundle = load_digest_dir(digest_dir)
    assert set(bundle.missing_files) >= {"import_graph.csv", "reason_atlas_routes.csv"}
    result = run_lean_digest_lawbook_ingestion(tmp_path / "ingest", digest_dir=digest_dir)
    manifest = json.loads(open(result.ingestion_manifest_path, encoding="utf-8").read())
    assert set(manifest["missing_files"]) >= {"import_graph.csv", "trust_boundary_audit.json", "lawbook_entries.jsonl", "reason_atlas_routes.csv"}
    assert result.declaration_count == 6
    assert result.advisory_boundary_ok is True


def test_can_promote_truth_textual_entry_flags_boundary(tmp_path) -> None:
    digest_dir = tmp_path / "digest"
    run_lean_project_digest(digest_dir, fallback_demo=True)
    rows = list(csv.DictReader(open(digest_dir / "declaration_inventory.csv", encoding="utf-8")))
    rows[0]["can_promote_truth"] = "true"
    with open(digest_dir / "declaration_inventory.csv", "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    result = run_lean_digest_lawbook_ingestion(tmp_path / "ingest", digest_dir=digest_dir)
    assert result.can_promote_truth_count == 1
    assert result.advisory_boundary_ok is False
    declarations = list(csv.DictReader(open(result.imported_declarations_path, encoding="utf-8")))
    assert {row["can_promote_truth"] for row in declarations} == {"False"}


def test_report_states_ingestion_is_not_verification(tmp_path) -> None:
    result = run_lean_digest_lawbook_ingestion(tmp_path / "ingest", fallback_demo=True)
    report = open(result.report_path, encoding="utf-8").read()
    assert "persistent imported Lean-project memory" in report
    assert "not Lean verification" in report
    assert "cannot become `VERIFIED_PROOF`" in report
    assert "Lean execution" in report
