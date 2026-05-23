import pytest

from mathgraph.certificates import TerminalForm
from mathgraph.evidence_manifest import EvidenceManifest
from mathgraph.invariants import check_lawbook_entry_replayable, check_provenance_preserved


def test_manifest_hash_stable_ignoring_created_at():
    a = EvidenceManifest(
        claim_id="c",
        terminal_form=TerminalForm.FINITE_COUNTERMODEL,
        evidence_type="finite",
        verifier_boundary="finite_model_checker",
        artifact_hashes=("h",),
        witness={"x": 0},
        provenance=("p",),
        replay_instructions=("run",),
        created_at="t1",
    )
    b = EvidenceManifest.from_dict({**a.to_dict(), "created_at": "t2"})
    assert a.stable_hash() == b.stable_hash()


def test_missing_manifest_fields_rejected():
    with pytest.raises(ValueError):
        EvidenceManifest(
            claim_id="c",
            terminal_form=TerminalForm.FINITE_COUNTERMODEL,
            evidence_type="finite",
            verifier_boundary="finite_model_checker",
            artifact_hashes=(),
            witness={"x": 0},
            provenance=("p",),
            replay_instructions=("run",),
        )


def test_lawbook_entry_without_replay_manifest_fails():
    report = check_lawbook_entry_replayable({"terminal_form": "FINITE_COUNTERMODEL"})
    assert not report.ok
    assert report.violations[0].code == "missing_replay_manifest"


def test_derived_certificate_without_provenance_fails():
    report = check_provenance_preserved({"terminal_form": "FINITE_COUNTERMODEL", "derived": True, "provenance": ("p",)})
    assert not report.ok
    assert report.violations[0].code == "derived_missing_sources"
