import csv
import json
import subprocess
import sys
from pathlib import Path

from adapters.sair_stage2_adapter import row_to_trace
from mathgraph.artifact_audit import audit_trace_artifacts
from mathgraph.artifacts import (
    build_artifact_record,
    extract_countermodel_from_json,
    sha256_file,
)
from mathgraph import TerminalForm, VerificationStatus


ROOT = Path(__file__).resolve().parents[1]


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = sorted({field for row in rows for field in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_sha256_file_is_deterministic(tmp_path: Path) -> None:
    path = tmp_path / "artifact.json"
    path.write_text('{"a":1}\n', encoding="utf-8")

    assert sha256_file(path) == sha256_file(path)


def test_build_artifact_record_found_matching_hash(tmp_path: Path) -> None:
    path = tmp_path / "artifact.json"
    path.write_text('{"countermodel":{"table":[[0,1],[1,0]]}}\n', encoding="utf-8")
    digest = sha256_file(path)

    record = build_artifact_record(path, expected_sha256=digest, kind="json", load_json=True)

    assert record["exists"] is True
    assert record["sha256_matches"] is True
    assert record["load_ok"] is True
    assert record["json_preview_keys"] == ["countermodel"]


def test_build_artifact_record_found_mismatched_hash(tmp_path: Path) -> None:
    path = tmp_path / "artifact.json"
    path.write_text('{"a":1}\n', encoding="utf-8")

    record = build_artifact_record(path, expected_sha256="0" * 64, kind="json", load_json=True)

    assert record["exists"] is True
    assert record["sha256_matches"] is False


def test_build_artifact_record_missing_artifact(tmp_path: Path) -> None:
    record = build_artifact_record(
        tmp_path / "missing.json",
        expected_sha256="0" * 64,
        kind="json",
        load_json=True,
    )

    assert record["exists"] is False
    assert record["load_ok"] is False
    assert record["error"] == "file_not_found"


def test_extract_countermodel_from_json() -> None:
    obj = {"certificate": {"countermodel": {"table": [[0, 1], [1, 0]]}}}

    extracted = extract_countermodel_from_json(obj)

    assert extracted == {"table": [[0, 1], [1, 0]]}


def test_finite_countermodel_row_loads_json_artifact(tmp_path: Path) -> None:
    artifact = tmp_path / "countermodel.json"
    artifact.write_text(
        json.dumps({"countermodel": {"table": [[0, 1], [1, 0]], "assignment": {"x": 1}}}),
        encoding="utf-8",
    )
    digest = sha256_file(artifact)

    trace = row_to_trace(
        {
            "terminal_form": "FINITE_COUNTERMODEL",
            "lean_verified_v19_1": "true",
            "lean_verified_false_v19_1": "true",
            "promotion_status_v19_1": "lean_verified_false_promotable",
            "json_path": str(artifact),
            "json_sha256": digest,
            "source_idx": "1",
            "target_idx": "2",
            "source_equation": "x=x",
            "target_equation": "x*x=x",
            "claim_hash": "claim-false",
            "compiled_route": "finite_magma",
        },
        load_artifacts=True,
    )

    model = trace.certificate.payload["model"]
    assert trace.terminal_form == TerminalForm.FINITE_COUNTERMODEL
    assert trace.verification_status == VerificationStatus.REFUTED
    assert model["countermodel"] == {"table": [[0, 1], [1, 0]], "assignment": {"x": 1}}
    assert model["countermodel_extraction"] == "found"
    assert model["artifacts"]["json"][0]["sha256_matches"] is True


def test_verified_proof_row_loads_lean_artifact(tmp_path: Path) -> None:
    lean = tmp_path / "proof.lean"
    lean.write_text("theorem t : True := True.intro\n", encoding="utf-8")
    digest = sha256_file(lean)

    trace = row_to_trace(
        {
            "lean_path": str(lean),
            "lean_sha256": digest,
            "source_idx": "1",
            "target_idx": "2",
            "source_equation": "x=x",
            "target_equation": "x=x",
            "claim_hash": "claim-true",
            "compiled_route": "routelean_v19_1",
            "lean_verified_v19_1": "true",
            "lean_verified_true_v19_1": "true",
            "promotion_status_v19_1": "lean_verified_true_promotable",
        },
        load_artifacts=True,
    )

    assert trace.terminal_form == TerminalForm.VERIFIED_PROOF
    assert trace.certificate.payload["artifacts"]["lean"][0]["sha256_matches"] is True


def test_missing_artifact_does_not_block_verified_row_by_default(tmp_path: Path) -> None:
    trace = row_to_trace(
        {
            "json_path": str(tmp_path / "missing.json"),
            "json_sha256": "0" * 64,
            "source_equation": "x=x",
            "target_equation": "x*x=x",
            "lean_verified_false_v19_1": "true",
            "promotion_status_v19_1": "lean_verified_false_promotable",
        },
        load_artifacts=True,
    )

    model = trace.certificate.payload["model"]
    assert trace.terminal_form == TerminalForm.FINITE_COUNTERMODEL
    assert trace.verification_status == VerificationStatus.REFUTED
    assert model["countermodel"] is None
    assert model["artifacts"]["json"][0]["exists"] is False
    assert model["countermodel_extraction"] == "not_found"


def test_artifact_audit_detects_hash_mismatch(tmp_path: Path) -> None:
    artifact = tmp_path / "countermodel.json"
    artifact.write_text('{"countermodel":{"table":[[0]]}}\n', encoding="utf-8")
    trace = row_to_trace(
        {
            "json_path": str(artifact),
            "json_sha256": "0" * 64,
            "source_equation": "x=x",
            "target_equation": "x*x=x",
            "lean_verified_false_v19_1": "true",
            "promotion_status_v19_1": "lean_verified_false_promotable",
        },
        load_artifacts=True,
    )

    audit = audit_trace_artifacts([trace])

    assert audit["json_artifacts_hash_mismatch"] == 1
    assert audit["hash_mismatches"] == 1
    assert audit["countermodels_extracted"] == 1


def test_cli_load_artifacts_exports_artifact_summary(tmp_path: Path) -> None:
    artifact = tmp_path / "countermodel.json"
    artifact.write_text('{"countermodel":{"table":[[0,1],[1,0]]}}\n', encoding="utf-8")
    csv_path = tmp_path / "results.csv"
    out_dir = tmp_path / "out"
    _write_csv(
        csv_path,
        [
            {
                "source_idx": "1",
                "target_idx": "2",
                "source_equation": "x=x",
                "target_equation": "x*x=x",
                "claim_hash": "claim-false",
                "compiled_route": "finite_magma",
                "lean_verified_v19_1": "true",
                "lean_verified_false_v19_1": "true",
                "promotion_status_v19_1": "lean_verified_false_promotable",
                "json_path": str(artifact),
                "json_sha256": sha256_file(artifact),
            }
        ],
    )

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "import_sair_stage2_results.py"),
            "--input",
            str(csv_path),
            "--out",
            str(out_dir),
            "--load-artifacts",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    summary = json.loads((out_dir / "summary.json").read_text(encoding="utf-8"))
    traces = json.loads((out_dir / "traces.json").read_text(encoding="utf-8"))

    assert summary["artifact_summary"]["countermodels_extracted"] == 1
    assert summary["artifact_summary"]["json_artifacts_found"] == 1
    model = traces[0]["certificate"]["payload"]["model"]
    assert model["countermodel"] == {"table": [[0, 1], [1, 0]]}
