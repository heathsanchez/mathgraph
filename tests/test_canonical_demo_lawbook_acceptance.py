import json

from mathgraph.evidence_replay import replay_evidence_manifest
from scripts.run_canonical_finite_countermodel_demo import run_demo


def test_canonical_demo_writes_manifest_and_replay_passes(tmp_path):
    summary = run_demo(tmp_path)
    assert summary["lawbook_acceptance_ok"] is True
    assert summary["replay_ok"] is True
    manifest_path = summary["outputs"]["manifest"]
    assert replay_evidence_manifest(manifest_path).ok
    lawbook_entry = json.loads((tmp_path / "lawbook_entry.json").read_text(encoding="utf-8"))
    assert lawbook_entry["status"] == "ACCEPTED"
    assert lawbook_entry["terminal_form"] == "FINITE_COUNTERMODEL"
