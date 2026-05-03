import json
import subprocess
import sys
from pathlib import Path

from mathgraph import CertificateLawbook, JsonlLedger, Kernel, TerminalForm, VerificationStatus


ROOT = Path(__file__).resolve().parents[1]


def _traces():
    proof = Kernel().prove("x = x", "x = x")
    proof.metadata.update(
        {
            "source_idx": "1",
            "target_idx": "2",
            "source_equation": "x = x",
            "target_equation": "x = x",
            "compiled_route": "variable_identification",
            "claim_hash": "claim-proof",
            "lean_status": "lean_verified_true",
            "promotion_status": "lean_verified_true_promotable",
        }
    )
    proof.certificate.payload.update({"proof": {"route": "variable_identification"}})

    counter = Kernel().prove("x = x", "x * x = x")
    counter.metadata.update(
        {
            "source_idx": "1",
            "target_idx": "3",
            "source_equation": "x = x",
            "target_equation": "x * x = x",
            "compiled_route": "finite_countermodel",
            "claim_hash": "claim-counter",
        }
    )
    counter.certificate.payload["model"]["countermodel"] = {"table": [[0, 1], [1, 0]]}

    obstruction = Kernel(finite_magmas=[]).prove("x * y = x", "x * y = y")
    obstruction.metadata.update(
        {
            "source_idx": "4",
            "target_idx": "5",
            "compiled_route": "unknown_route",
            "claim_hash": "claim-obstruction",
        }
    )
    return [proof, counter, obstruction]


def test_lawbook_from_trace_list_summary_counts() -> None:
    lawbook = CertificateLawbook.from_traces(_traces())
    summary = lawbook.summary()

    assert summary["trace_count"] == 3
    assert summary["terminal_form_counts"]["VERIFIED_PROOF"] == 1
    assert summary["terminal_form_counts"]["FINITE_COUNTERMODEL"] == 1
    assert summary["terminal_form_counts"]["NAMED_OBSTRUCTION"] == 1
    assert summary["verification_status_counts"]["VERIFIED"] == 1
    assert summary["route_counts"]["finite_countermodel"] == 1
    assert summary["source_count"] == 2
    assert summary["target_count"] == 3
    assert summary["pair_count"] == 3
    assert summary["promotable_count"] == 2
    assert summary["obstruction_count"] == 1


def test_lawbook_route_and_endpoint_summaries() -> None:
    lawbook = CertificateLawbook.from_traces(_traces())
    routes = lawbook.route_summary()
    source = lawbook.source_summary("1")
    target = lawbook.target_summary("3")

    assert routes["variable_identification"]["count"] == 1
    assert routes["finite_countermodel"]["terminal_form_counts"]["FINITE_COUNTERMODEL"] == 1
    assert source["trace_count"] == 2
    assert source["target_indices"] == ["2", "3"]
    assert target["trace_count"] == 1
    assert target["source_indices"] == ["1"]


def test_lawbook_lookup_and_query() -> None:
    lawbook = CertificateLawbook.from_traces(_traces())

    assert lawbook.get_by_claim("claim-proof")[0].terminal_form == TerminalForm.VERIFIED_PROOF
    assert lawbook.get_by_pair(1, 3)[0].terminal_form == TerminalForm.FINITE_COUNTERMODEL
    assert lawbook.query(terminal_form="FINITE_COUNTERMODEL")[0].verification_status == VerificationStatus.REFUTED
    assert lawbook.query(route="variable_identification")[0].claim == "x = x => x = x"
    assert len(lawbook.query(limit=2)) == 2


def test_lawbook_extraction_helpers() -> None:
    lawbook = CertificateLawbook.from_traces(_traces())
    counter = lawbook.countermodels()[0]
    proof = lawbook.verified_proofs()[0]

    assert lawbook.extract_countermodel(counter) == {"table": [[0, 1], [1, 0]]}
    assert lawbook.extract_proof_payload(proof) == {"route": "variable_identification"}
    assert lawbook.obstructions()[0].terminal_form == TerminalForm.NAMED_OBSTRUCTION


def test_lawbook_missing_fields_do_not_crash() -> None:
    trace = Kernel().prove("x = x")
    lawbook = CertificateLawbook([trace.to_dict()])

    assert lawbook.summary()["trace_count"] == 1
    assert lawbook.source_summary("missing")["trace_count"] == 0
    assert lawbook.explain_trace(trace)["source_idx"] is None


def test_lawbook_explain_trace_and_claim_pair() -> None:
    lawbook = CertificateLawbook.from_traces(_traces())
    explanation = lawbook.explain_pair("1", "3")[0]

    assert explanation["terminal_form"] == "FINITE_COUNTERMODEL"
    assert explanation["compiled_route"] == "finite_countermodel"
    assert explanation["has_certificate"] is True
    assert explanation["has_countermodel"] is True
    assert lawbook.explain_claim("claim-counter")[0]["target_idx"] == "3"


def test_lawbook_save_summary(tmp_path: Path) -> None:
    path = tmp_path / "summary.json"
    route_path = tmp_path / "routes.json"
    lawbook = CertificateLawbook.from_traces(_traces())

    lawbook.save_summary(path)
    lawbook.save_route_summary(route_path)

    assert json.loads(path.read_text(encoding="utf-8"))["summary"]["trace_count"] == 3
    assert "finite_countermodel" in json.loads(route_path.read_text(encoding="utf-8"))


def test_lawbook_cli_traces_json(tmp_path: Path) -> None:
    traces_path = tmp_path / "traces.json"
    out_path = tmp_path / "lawbook_summary.json"
    traces_path.write_text(
        json.dumps([trace.to_dict() for trace in _traces()]),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_lawbook_summary.py"),
            "--traces-json",
            str(traces_path),
            "--out",
            str(out_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert '"trace_count": 3' in result.stdout
    assert out_path.exists()


def test_lawbook_cli_traces_jsonl(tmp_path: Path) -> None:
    ledger_path = tmp_path / "traces.jsonl"
    route_path = tmp_path / "route_summary.json"
    ledger = JsonlLedger(ledger_path)
    for trace in _traces():
        ledger.append_trace(trace)

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_lawbook_summary.py"),
            "--traces-jsonl",
            str(ledger_path),
            "--route-summary",
            str(route_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert route_path.exists()
    assert "variable_identification" in json.loads(route_path.read_text(encoding="utf-8"))
