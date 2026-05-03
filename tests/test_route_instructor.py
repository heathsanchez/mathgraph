import json
import subprocess
import sys
from pathlib import Path

from mathgraph import (
    CertificateLawbook,
    Kernel,
    RouteInstruction,
    TerminalForm,
    build_all_route_instructions,
    build_route_instruction,
    route_instruction_report,
)
from mathgraph.route_instructor import infer_route_kind


ROOT = Path(__file__).resolve().parents[1]


def _lawbook() -> CertificateLawbook:
    counter = Kernel().prove("x = x", "x * x = x")
    counter.metadata.update(
        {
            "source_idx": "1",
            "target_idx": "2",
            "source_equation": "x = x",
            "target_equation": "x * x = x",
            "compiled_route": "finite_countermodel",
        }
    )

    proof = Kernel().prove("x = x", "x = x")
    proof.metadata.update(
        {
            "source_idx": "3",
            "target_idx": "4",
            "source_equation": "x = x",
            "target_equation": "x = x",
            "compiled_route": "variable_identification",
        }
    )
    proof.certificate.payload["proof"] = {"route": "variable_identification"}

    long_proof = Kernel().prove("x = x", "x = x")
    long_text = "x " + ("* y " * 80) + "= x"
    long_proof.source = long_text
    long_proof.target = long_text
    long_proof.metadata.update(
        {
            "source_idx": "5",
            "target_idx": "6",
            "compiled_route": "skeleton_preserving_relabel",
        }
    )

    return CertificateLawbook.from_traces([counter, proof, long_proof])


def test_route_instruction_roundtrip() -> None:
    instruction = build_route_instruction(_lawbook(), "finite_countermodel")

    loaded = RouteInstruction.from_dict(instruction.to_dict())

    assert loaded == instruction
    assert loaded.route_kind == "countermodel_constructor"


def test_infer_route_kind() -> None:
    assert infer_route_kind("finite_countermodel", {}, {}) == "countermodel_constructor"
    assert infer_route_kind("variable_identification", {}, {}) == "proof_constructor"
    assert (
        infer_route_kind(
            "unknown",
            {"VERIFIED_PROOF": 1, "FINITE_COUNTERMODEL": 1},
            {},
        )
        == "mixed_or_unknown"
    )


def test_build_route_instruction_guidance() -> None:
    instruction = build_route_instruction(_lawbook(), "finite_countermodel")

    assert instruction.count == 1
    assert instruction.terminal_form_counts == {"FINITE_COUNTERMODEL": 1}
    assert "Finite search failure is not proof." in instruction.rejection_warnings
    assert any("finite magma" in item for item in instruction.positive_guidance)
    assert "verification status REFUTED" in instruction.evidence_requirements
    assert instruction.example_summaries[0]["source_idx"] == "1"


def test_proof_route_instruction_guidance() -> None:
    instruction = build_route_instruction(_lawbook(), "variable_identification")

    assert instruction.route_kind == "proof_constructor"
    assert "verification status VERIFIED" in instruction.evidence_requirements
    assert "Do not promote to VERIFIED_PROOF without explicit verification." in instruction.rejection_warnings


def test_sample_previews_are_capped() -> None:
    instruction = build_route_instruction(_lawbook(), "skeleton_preserving_relabel")

    example = instruction.example_summaries[0]

    assert len(example["source_preview"]) <= 120
    assert example["source_preview"].endswith("...")


def test_lawbook_convenience_methods() -> None:
    lawbook = _lawbook()

    instruction = lawbook.route_instruction("finite_countermodel")
    all_instructions = lawbook.all_route_instructions()

    assert instruction.route == "finite_countermodel"
    assert "variable_identification" in all_instructions


def test_instruction_report() -> None:
    report = route_instruction_report(_lawbook(), sample_limit=1)

    assert report["route_count"] == 3
    assert report["total_traces"] == 3
    assert report["instructions"]["finite_countermodel"]["example_summaries"][0]["target_idx"] == "2"


def test_build_all_route_instructions() -> None:
    instructions = build_all_route_instructions(_lawbook())

    assert set(instructions) == {
        "finite_countermodel",
        "skeleton_preserving_relabel",
        "variable_identification",
    }
    assert all(hasattr(instruction, "to_dict") for instruction in instructions.values())


def test_cli_build_route_instructions(tmp_path: Path) -> None:
    traces_path = tmp_path / "traces.json"
    out_path = tmp_path / "route_instructions.json"
    traces_path.write_text(
        json.dumps([trace.to_dict() for trace in _lawbook().traces]),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_route_instructions.py"),
            "--traces-json",
            str(traces_path),
            "--out",
            str(out_path),
            "--sample-limit",
            "2",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert out_path.exists()
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["instructions"]["finite_countermodel"]["route_kind"] == "countermodel_constructor"
    assert '"route_count": 3' in result.stdout
