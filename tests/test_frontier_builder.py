import json
import subprocess
import sys
from pathlib import Path

import pytest

from mathgraph import (
    Certificate,
    CertificateLawbook,
    FrontierBuilderConfig,
    FrontierBuilderResult,
    FrontierCandidate,
    LawbookStore,
    TerminalForm,
    Trace,
    VerificationStatus,
    build_candidate_frontier,
)
from mathgraph.frontier_builder import score_frontier_pair
from mathgraph.htilt_scheduler import SchedulerInputPair


ROOT = Path(__file__).resolve().parents[1]


def _write_equations(path: Path) -> None:
    path.write_text("x = x\nx * y = x\nx * x = x\nx * y = z\n", encoding="utf-8")


def _known_store(path: Path, source: str = "x = x", target: str = "x = x") -> LawbookStore:
    trace = Trace(
        claim=f"{source}=>{target}",
        source=source,
        target=target,
        routes_tried=["exact"],
        terminal_form=TerminalForm.VERIFIED_PROOF,
        verification_status=VerificationStatus.VERIFIED,
        certificate=Certificate(TerminalForm.VERIFIED_PROOF, f"{source}=>{target}", payload={}),
    )
    store = LawbookStore(path)
    store.import_lawbook(CertificateLawbook.from_traces([trace]), replace=True)
    return store


def test_dataclass_roundtrip() -> None:
    candidate = FrontierCandidate(
        source="A",
        target="B",
        source_idx=1,
        target_idx=2,
        label="structural_unknown",
        candidate_origin="structural_frontier",
        frontier_score=0.5,
        frontier_reason_codes=["reason"],
        features={"same_text": False},
        metadata={"m": 1},
    )
    assert FrontierCandidate.from_dict(candidate.to_dict()) == candidate
    config = FrontierBuilderConfig("eq.txt", "out.jsonl")
    assert FrontierBuilderConfig.from_dict(config.to_dict()) == config
    result = FrontierBuilderResult([candidate.to_dict()], {"candidate_count": 1}, {"jsonl": "out"})
    assert FrontierBuilderResult.from_dict(result.to_dict()) == result


def test_structural_feature_scoring_and_same_text_low_score() -> None:
    score, reasons, features = score_frontier_pair("x = x", "x * y = z")
    assert score > 0
    assert "target_introduces_new_variables" in reasons
    assert features["target_op_count"] > features["source_op_count"]
    same_score, same_reasons, _ = score_frontier_pair("x = x", "x = x")
    assert same_score == 0
    assert "same_text_low_priority" in same_reasons


def test_no_matrix_frontier_generation(tmp_path: Path) -> None:
    equations = tmp_path / "equations.txt"
    out = tmp_path / "frontier.jsonl"
    _write_equations(equations)
    result = build_candidate_frontier(
        FrontierBuilderConfig(str(equations), str(out), max_candidates=5)
    )
    assert result.summary["candidate_count"] == 5
    assert result.summary["by_label"]["structural_unknown"] == 5
    rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert SchedulerInputPair.from_dict(rows[0]).source
    assert "terminal_form" not in rows[0]
    assert "verification_status" not in rows[0]


def test_matrix_false_generation(tmp_path: Path) -> None:
    np = pytest.importorskip("numpy")
    equations = tmp_path / "equations.txt"
    matrix = tmp_path / "matrix.npy"
    out = tmp_path / "frontier.jsonl"
    _write_equations(equations)
    np.save(matrix, np.array([[True, False], [True, True]], dtype=bool))
    result = build_candidate_frontier(
        FrontierBuilderConfig(
            str(equations),
            str(out),
            matrix_path=str(matrix),
            source_limit=2,
            target_limit=2,
            max_candidates=10,
            include_unknown_matrix_missing=False,
        )
    )
    assert result.summary["matrix_loaded"]
    assert result.summary["by_label"]["matrix_false_unverified"] == 1
    assert result.candidates[0]["label"] == "matrix_false_unverified"


def test_skip_known_behavior(tmp_path: Path) -> None:
    equations = tmp_path / "equations.txt"
    out = tmp_path / "frontier.jsonl"
    _write_equations(equations)
    store = _known_store(tmp_path / "lawbook.sqlite")
    store.close()
    result = build_candidate_frontier(
        FrontierBuilderConfig(
            str(equations),
            str(out),
            store_path=str(tmp_path / "lawbook.sqlite"),
            source_limit=1,
            target_limit=1,
            max_candidates=10,
            skip_known=True,
        )
    )
    assert result.summary["skipped_known_count"] == 1
    assert result.summary["candidate_count"] == 0


def test_jsonl_and_summary_exist_and_scheduler_compatible(tmp_path: Path) -> None:
    equations = tmp_path / "equations.txt"
    out = tmp_path / "frontier.jsonl"
    _write_equations(equations)
    build_candidate_frontier(FrontierBuilderConfig(str(equations), str(out), max_candidates=3))
    summary = out.with_name("frontier_summary.json")
    assert out.exists()
    assert summary.exists()
    row = json.loads(out.read_text(encoding="utf-8").splitlines()[0])
    assert SchedulerInputPair.from_dict(row).target


def test_cli_smoke(tmp_path: Path) -> None:
    equations = tmp_path / "equations.txt"
    out = tmp_path / "frontier.jsonl"
    _write_equations(equations)
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_candidate_frontier.py"),
            "--equations-path",
            str(equations),
            "--out",
            str(out),
            "--max-candidates",
            "4",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["candidate_count"] == 4
    assert out.exists()
    assert out.with_name("frontier_summary.json").exists()
