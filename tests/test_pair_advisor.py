import json
import subprocess
import sys
from pathlib import Path

from mathgraph import (
    CertificateLawbook,
    Kernel,
    PairAdvice,
    TerminalForm,
    advise_many,
    advise_pair,
    extract_pair_features,
)


ROOT = Path(__file__).resolve().parents[1]


def _lawbook() -> CertificateLawbook:
    counter = Kernel().prove("x = x", "x * x = x")
    counter.metadata.update(
        {
            "source_idx": "1",
            "target_idx": "2",
            "compiled_route": "finite_countermodel",
        }
    )
    proof = Kernel().prove("x * y = x", "x * x = x")
    proof.metadata.update(
        {
            "source_idx": "3",
            "target_idx": "4",
            "compiled_route": "variable_identification",
        }
    )
    relabel = Kernel().prove("x * y = y * x", "a * b = b * a")
    relabel.metadata.update(
        {
            "source_idx": "5",
            "target_idx": "6",
            "compiled_route": "skeleton_preserving_relabel",
        }
    )
    return CertificateLawbook.from_traces([counter, proof, relabel])


def test_pair_advice_roundtrip() -> None:
    advice = advise_pair(_lawbook(), "x = x", "z = z")

    loaded = PairAdvice.from_dict(advice.to_dict())

    assert loaded == advice


def test_exact_known_pair_returns_known_certificate() -> None:
    advice = advise_pair(_lawbook(), "x = x", "x * x = x")

    assert advice.status == "known_certificate"
    assert advice.exact_match is True
    assert advice.terminal_form == "FINITE_COUNTERMODEL"
    assert advice.verification_status == "REFUTED"
    assert advice.known_claim == "x = x => (x * x) = x"
    assert advice.candidate_routes[0]["route"] == "finite_countermodel"


def test_unknown_pair_is_advisory_obstruction() -> None:
    advice = advise_pair(_lawbook(), "x * y = x", "x * z = z")

    assert advice.status == "advisory_only"
    assert advice.terminal_form == "NAMED_OBSTRUCTION"
    assert advice.verification_status == "UNKNOWN"
    assert advice.known_claim is None
    assert "This is advisory only, not a proof or refutation." in advice.warnings


def test_variable_identification_candidate_for_variable_collapse() -> None:
    advice = advise_pair(_lawbook(), "x * y = x", "x * x = x")

    routes = [candidate["route"] for candidate in advice.candidate_routes]

    assert "variable_identification" in routes


def test_finite_countermodel_candidate_for_new_variables_or_complexity() -> None:
    advice = advise_pair(_lawbook(), "x = x", "(x * z) * y = z")

    routes = [candidate["route"] for candidate in advice.candidate_routes]

    assert "finite_countermodel" in routes
    finite = [candidate for candidate in advice.candidate_routes if candidate["route"] == "finite_countermodel"][0]
    assert "target_introduces_new_variables" in finite["reason_codes"]


def test_skeleton_preserving_candidate_for_rough_skeleton_match() -> None:
    advice = advise_pair(_lawbook(), "x * y = y * x", "a * b = b * a")

    routes = [candidate["route"] for candidate in advice.candidate_routes]

    assert "skeleton_preserving_relabel" in routes


def test_extract_pair_features() -> None:
    features = extract_pair_features("x * y = x", "x * x = x")

    assert features["target_vars_subset_source_vars"] is True
    assert features["target_has_repeated_vars"] is True
    assert features["source_op_count"] == 1


def test_advise_many_supports_tuple_and_dict_inputs() -> None:
    results = advise_many(
        _lawbook(),
        [
            ("x = x", "x * x = x"),
            {"source": "x * y = x", "target": "x * z = z"},
            ("malformed",),
        ],
    )

    assert results[0].status == "known_certificate"
    assert results[1].status == "advisory_only"
    assert results[2].status == "malformed_input"


def test_lawbook_convenience_method() -> None:
    advice = _lawbook().advise_pair("x * y = x", "x * z = z")

    assert advice.status == "advisory_only"
    assert advice.terminal_form == TerminalForm.NAMED_OBSTRUCTION.value


def test_malformed_input_is_handled() -> None:
    advice = advise_pair(_lawbook(), "", "x = x")

    assert advice.status == "malformed_input"
    assert advice.terminal_form == "NAMED_OBSTRUCTION"
    assert advice.candidate_routes == []


def test_cli_advise_pair(tmp_path: Path) -> None:
    traces_path = tmp_path / "traces.json"
    out_path = tmp_path / "advice.json"
    traces_path.write_text(
        json.dumps([trace.to_dict() for trace in _lawbook().traces]),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "advise_pair.py"),
            "--traces-json",
            str(traces_path),
            "--source",
            "x * y = x",
            "--target",
            "x * z = z",
            "--out",
            str(out_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["status"] == "advisory_only"
    assert '"candidate_routes"' in result.stdout
