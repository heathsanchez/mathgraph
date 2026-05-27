import csv
import json

from mathgraph.lean_digest_lawbook_ingestion import run_lean_digest_lawbook_ingestion
from mathgraph.lean_lawbook_attention import (
    LeanAttentionCorpus,
    build_attention_trust_audit,
    run_attention_queries,
    run_lean_lawbook_attention,
)
from mathgraph.lean_project_digest import run_lean_project_digest


def test_fallback_demo_runs_and_emits_expected_files(tmp_path) -> None:
    result = run_lean_lawbook_attention(tmp_path / "attention", fallback_demo=True)
    assert result.query_count == 3
    assert result.declaration_count >= 6
    assert result.result_count > 0
    assert result.attention_boundary_ok is True
    assert result.can_promote_truth_count == 0
    expected = {
        "attention_manifest.json",
        "attention_results.csv",
        "attention_results.jsonl",
        "attention_trace.json",
        "route_suggestions.csv",
        "trust_boundary_audit.json",
        "lean_lawbook_attention_report.md",
    }
    assert expected <= {path.name for path in (tmp_path / "attention").iterdir()}
    report = (tmp_path / "attention" / "lean_lawbook_attention_report.md").read_text(encoding="utf-8")
    assert "Attention changes routing, not truth" in report
    assert "not H-tilt" in report


def test_token_scoring_ranks_relevant_declaration_above_irrelevant() -> None:
    corpus = LeanAttentionCorpus(
        input_dir=".",
        declarations=(
            {
                "declaration_id": "Nat.add_assoc",
                "declaration_kind": "theorem",
                "name": "Nat.add_assoc",
                "file": "A.lean",
                "line": 1,
                "statement_text": "Nat addition associativity theorem",
                "trust_status": "imported_verified_candidate",
                "provenance_type": "imported_lean_project",
                "boundary_type": "textual_digest",
            },
            {
                "declaration_id": "List.map_id",
                "declaration_kind": "lemma",
                "name": "List.map_id",
                "file": "B.lean",
                "line": 1,
                "statement_text": "List map identity",
                "trust_status": "imported_verified_candidate",
                "provenance_type": "imported_lean_project",
                "boundary_type": "textual_digest",
            },
        ),
    )
    rows = run_attention_queries(corpus, ["Nat addition associativity"], top_k=2)
    assert rows[0]["name"] == "Nat.add_assoc"
    assert rows[0]["attention_score"] > rows[1]["attention_score"]


def test_sorry_axiom_and_unsafe_routes_preserve_boundaries(tmp_path) -> None:
    result = run_lean_lawbook_attention(
        tmp_path / "attention",
        fallback_demo=True,
        queries=["sorry theorem", "Classical choice axiom", "unsafe declaration"],
        top_k=6,
    )
    rows = list(csv.DictReader(open(tmp_path / "attention" / "attention_results.csv", encoding="utf-8")))
    assert {row["can_promote_truth"] for row in rows} == {"False"}
    assert {row["advisory_only"] for row in rows} == {"True"}
    by_route = {row["route_suggestion"] for row in rows}
    assert "sorry_repair_candidate" in by_route
    assert "axiom_boundary_candidate" in by_route
    assert "unsafe_boundary_warning" in by_route
    audit = json.loads((tmp_path / "attention" / "trust_boundary_audit.json").read_text(encoding="utf-8"))
    assert audit["attention_boundary_ok"] is True
    assert audit["warning_count"] > 0


def test_trust_audit_fails_on_malformed_promotion_attempt() -> None:
    audit = build_attention_trust_audit(
        [
            {
                "declaration_id": "bad",
                "trust_status": "VERIFIED_PROOF",
                "boundary_type": "textual_digest",
                "advisory_only": False,
                "can_promote_truth": True,
            }
        ]
    )
    assert audit["attention_boundary_ok"] is False
    assert audit["can_promote_truth_count"] == 1
    assert audit["advisory_only_false_count"] == 1
    assert len(audit["violations"]) == 3


def test_digest_dir_mode_consumes_project_digest_and_ingestion_outputs(tmp_path) -> None:
    digest_dir = tmp_path / "digest"
    ingestion_dir = tmp_path / "ingestion"
    run_lean_project_digest(digest_dir, fallback_demo=True)
    run_lean_digest_lawbook_ingestion(ingestion_dir, digest_dir=digest_dir)

    from_digest = run_lean_lawbook_attention(
        tmp_path / "from_digest",
        digest_dir=digest_dir,
        queries=["Nat addition associativity"],
    )
    from_ingestion = run_lean_lawbook_attention(
        tmp_path / "from_ingestion",
        digest_dir=ingestion_dir,
        queries=["Nat addition associativity"],
    )
    assert from_digest.attention_boundary_ok is True
    assert from_ingestion.attention_boundary_ok is True
    assert from_digest.result_count > 0
    assert from_ingestion.result_count > 0
