import json
import subprocess
import sys

from mathgraph.domain_claims import (
    ClaimIRStatus,
    ClaimKind,
    ClaimParseResult,
    DomainClaim,
    FormalWorldKind,
    FormalWorldRegistry,
    LeanSkeletonAdapter,
    default_formal_world_registry,
    domain_claim_to_verification_episode_input,
    normalize_domain_claim,
    parse_domain_claim,
    run_domain_claim_pipeline,
)
from mathgraph.proof_verification import ProofArtifactKind
from mathgraph.roadmap_alignment import check_roadmap_alignment
from mathgraph.verification_episode import VerificationRouteKind


def test_domain_claim_serializes_roundtrip():
    claim = parse_domain_claim("x*x=x => x*y=x").domain_claim

    assert DomainClaim.from_json(claim.to_json()).to_dict() == claim.to_dict()
    assert DomainClaim.from_jsonl_line(claim.to_jsonl_line()).claim_id == claim.claim_id


def test_formal_world_registry_serializes_roundtrip():
    registry = default_formal_world_registry()

    loaded = FormalWorldRegistry.from_json(registry.to_json())

    assert loaded.to_dict() == registry.to_dict()


def test_default_registry_includes_magma_and_lean():
    registry = default_formal_world_registry()

    assert registry.by_kind(FormalWorldKind.MAGMA_EQUATIONAL)
    assert registry.by_kind(FormalWorldKind.LEAN)


def test_parse_domain_claim_infers_magma_implication():
    result = parse_domain_claim("x*x=x => x*y=x")

    assert result.status == ClaimIRStatus.NORMALIZED
    assert result.domain_claim.kind == ClaimKind.EQUATIONAL_IMPLICATION
    assert result.domain_claim.world == FormalWorldKind.MAGMA_EQUATIONAL
    assert result.domain_claim.source == "x*x=x"
    assert result.domain_claim.target == "x*y=x"


def test_normalize_domain_claim_normalizes_diamond_operator():
    result = parse_domain_claim("x◇x=x => x⋄y=x")
    normalized = normalize_domain_claim(result.domain_claim)

    assert "◇" not in normalized.normalized
    assert "⋄" not in normalized.normalized
    assert "*" in normalized.normalized


def test_lean_looking_theorem_is_advisory_theorem_statement():
    result = parse_domain_claim("theorem foo : True := by trivial")

    assert result.domain_claim.world == FormalWorldKind.LEAN
    assert result.domain_claim.kind == ClaimKind.THEOREM_STATEMENT
    assert result.domain_claim.advisory is True
    assert result.status == ClaimIRStatus.ROUTABLE


def test_natural_language_claim_is_advisory_and_not_terminal_supported():
    result = parse_domain_claim("Water is wet in ordinary conditions.")

    assert result.domain_claim.world == FormalWorldKind.NATURAL_LANGUAGE
    assert result.domain_claim.advisory is True
    assert result.status == ClaimIRStatus.ADVISORY_ONLY
    assert result.domain_claim.metadata["advisory_only"] is True


def test_domain_claim_to_verification_episode_input_maps_magma_source_target():
    claim = parse_domain_claim("x*x=x => x*y=x").domain_claim

    episode_input = domain_claim_to_verification_episode_input(claim)

    assert episode_input.source == "x*x=x"
    assert episode_input.target == "x*y=x"
    assert episode_input.route_hint == VerificationRouteKind.BOTH_SIDES


def test_lean_claim_maps_to_proof_artifact():
    claim = parse_domain_claim("theorem foo : True := by trivial").domain_claim
    artifact = LeanSkeletonAdapter().to_proof_artifact(claim)

    assert artifact is not None
    assert artifact.kind == ProofArtifactKind.LEAN_SKELETON
    assert artifact.theorem_name == "foo"
    assert artifact.advisory is True


def test_run_domain_claim_pipeline_works_on_empty_input():
    result = run_domain_claim_pipeline()

    assert result["claims"] == []
    assert result["parse_results"] == []
    assert result["summary"]["claims_total"] == 0


def test_run_domain_claim_pipeline_parses_multiple_raw_claims():
    result = run_domain_claim_pipeline(raw_claims=["x*x=x => x*y=x", "theorem foo : True := by trivial"])

    assert result["summary"]["claims_total"] == 2
    worlds = {claim["world"] for claim in result["claims"]}
    assert FormalWorldKind.MAGMA_EQUATIONAL.value in worlds
    assert FormalWorldKind.LEAN.value in worlds


def test_roadmap_alignment_catches_natural_language_as_terminal_truth():
    claim = parse_domain_claim("A broad scientific statement.").domain_claim
    claim.metadata["terminal_truth"] = True

    report = check_roadmap_alignment(domain_claims=[claim])

    assert report.critical_count() >= 1
    assert any(finding.code == "NATURAL_LANGUAGE_CLAIM_AS_TERMINAL_TRUTH" for finding in report.findings)


def test_roadmap_alignment_catches_parse_result_treated_as_terminal_truth():
    result = parse_domain_claim("x*x=x => x*y=x")
    unsafe = ClaimParseResult.from_dict({**result.to_dict(), "metadata": {"terminal_form": "VERIFIED_PROOF"}})

    report = check_roadmap_alignment(claim_parse_results=[unsafe])

    assert report.critical_count() >= 1
    assert any(finding.code == "CLAIM_PARSE_RESULT_AS_TERMINAL_TRUTH" for finding in report.findings)


def test_cli_runs_with_empty_input(tmp_path):
    out_path = tmp_path / "domain.json"
    report_path = tmp_path / "alignment.json"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_domain_claims.py",
            "--out-json",
            str(out_path),
            "--alignment-report-json",
            str(report_path),
            "--fail-on-critical",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(out_path.read_text(encoding="utf-8"))["claims"] == []


def test_cli_parses_magma_implication_and_writes_jsonl(tmp_path):
    out_path = tmp_path / "claims.jsonl"
    parse_path = tmp_path / "parse.jsonl"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_domain_claims.py",
            "--claim",
            "x*x=x => x*y=x",
            "--out-claims-jsonl",
            str(out_path),
            "--out-parse-results-jsonl",
            str(parse_path),
            "--fail-on-critical",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    rows = [json.loads(line) for line in out_path.read_text(encoding="utf-8").splitlines()]
    assert rows[0]["world"] == FormalWorldKind.MAGMA_EQUATIONAL.value
    assert parse_path.read_text(encoding="utf-8").strip()

