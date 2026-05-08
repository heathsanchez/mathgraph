import json
import subprocess
import sys

from mathgraph import MathGraphAnswer, MathGraphClient, MathGraphClientConfig
from mathgraph.terminal_contract import ProvenanceType, Status, TerminalForm, TrustLevel, VerifierBoundary


def test_client_query_empty_store_is_read_only_unknown(tmp_path):
    store = tmp_path / "sdk.sqlite"
    client = MathGraphClient(store)

    answer = client.query_claim("(x*x)=x", "(x*y)=x")

    assert answer.status == Status.UNKNOWN
    assert answer.terminal_form == TerminalForm.NAMED_OBSTRUCTION
    assert answer.trust_level == TrustLevel.ADVISORY_ROUTE
    assert answer.provenance_type == ProvenanceType.SYSTEM
    assert answer.verifier_boundary == VerifierBoundary.NOT_VERIFIED
    assert answer.certificate_id is None
    assert client.stats()["total_certificate_count"] == 0


def test_client_submit_known_false_pair_promotes_refutation(tmp_path):
    client = MathGraphClient(tmp_path / "sdk.sqlite")

    answer = client.submit_claim("(x*x)=x", "(x*y)=x", source_idx=1, target_idx=2)

    assert answer.status == Status.VERIFIED_FALSE
    assert answer.terminal_form == TerminalForm.REFUTATION_CERTIFICATE
    assert answer.trust_level == TrustLevel.FINITE_VERIFIED
    assert answer.provenance_type == ProvenanceType.PRIMITIVE
    assert answer.verifier_boundary == VerifierBoundary.IMPORTER_REVALIDATED
    assert answer.certificate_id
    assert answer.certificate_chain == [answer.certificate_id]


def test_client_submit_then_query_returns_known_without_new_construction(tmp_path):
    client = MathGraphClient(tmp_path / "sdk.sqlite")
    first = client.submit_claim("(x*x)=x", "(x*y)=x")

    second = client.query_claim("(x*x)=x", "(x*y)=x")

    assert first.certificate_id
    assert second.status == "REFUTED"
    assert second.terminal_form == TerminalForm.REFUTATION_CERTIFICATE
    assert second.certificate_id == first.certificate_id


def test_client_audit_after_write_is_visible_and_passes(tmp_path):
    client = MathGraphClient(MathGraphClientConfig(store_path=str(tmp_path / "sdk.sqlite")))

    answer = client.submit_claim("(x*x)=x", "(x*y)=x")

    assert answer.audit is not None
    assert answer.audit["passed"] is True
    assert answer.audit["critical_count"] == 0


def test_client_allow_construction_false_is_safe_unknown(tmp_path):
    client = MathGraphClient(tmp_path / "sdk.sqlite")

    answer = client.submit_claim("(x*x)=x", "(x*y)=x", allow_construction=False)

    assert answer.status == Status.UNKNOWN
    assert answer.trust_level == TrustLevel.ADVISORY_ROUTE
    assert answer.certificate_id is None
    assert client.stats()["total_certificate_count"] == 0


def test_client_stats_is_json_serializable(tmp_path):
    client = MathGraphClient(tmp_path / "sdk.sqlite")
    client.submit_claim("(x*x)=x", "(x*y)=x")

    payload = client.stats()

    json.dumps(payload, sort_keys=True)
    assert payload["total_certificate_count"] >= 1


def test_mathgraph_answer_to_json_round_trips():
    answer = MathGraphAnswer(
        status=Status.UNKNOWN,
        terminal_form=TerminalForm.NAMED_OBSTRUCTION,
        trust_level=TrustLevel.ADVISORY_ROUTE,
        provenance_type=ProvenanceType.SYSTEM,
        verifier_boundary=VerifierBoundary.NOT_VERIFIED,
        certificate_id=None,
        certificate_chain=[],
        source="x=x",
        target="x=y",
        source_idx=None,
        target_idx=None,
        claim="x=x => x=y",
        explanation="unknown",
        warnings=["Finite search failure is not proof."],
        evidence={"k": "v"},
    )

    payload = json.loads(answer.to_json())

    assert payload["status"] == Status.UNKNOWN
    assert payload["evidence"] == {"k": "v"}


def test_sdk_smoke_script_runs(tmp_path):
    proc = subprocess.run(
        [
            sys.executable,
            "scripts/sdk_smoke.py",
            "--store",
            str(tmp_path / "sdk.sqlite"),
            "--source",
            "(x*x)=x",
            "--target",
            "(x*y)=x",
            "--max-countermodel-order",
            "3",
        ],
        text=True,
        capture_output=True,
    )

    assert proc.returncode == 0, proc.stderr
    lines = [json.loads(line) for line in proc.stdout.splitlines()]
    assert lines[0]["terminal_form"] == TerminalForm.REFUTATION_CERTIFICATE
    assert lines[1]["certificate_id"]
