from mathgraph.derived_certificates import DerivedCertificate


def test_target_strengthening_replay_metadata_is_not_auto_finite_verified():
    cert = DerivedCertificate.from_dict(
        {
            "derived_claim": "d1",
            "source": "A",
            "target": "C",
            "terminal_form": "FINITE_COUNTERMODEL",
            "verification_status": "DERIVED_REFUTED",
            "derivation_rule": "false_target_strengthening",
            "trust_level": "derived_from_verified_traces",
            "parent_claims": [],
            "parent_pairs": [],
            "route": "derived_false_target_strengthening",
            "explanation": "logical",
            "certificate_preservation_status": "seed_table_replay_possible",
            "requires_replay": True,
            "replay_status": "not_replayed",
        }
    )
    assert cert.terminal_form == "FINITE_COUNTERMODEL"
    assert cert.verification_status != "FINITE_VERIFIED"
    assert cert.requires_replay is True


def test_source_weakening_without_replay_is_not_finite_verified():
    cert = DerivedCertificate.from_dict(
        {
            "derived_claim": "d2",
            "source": "A",
            "target": "C",
            "terminal_form": "FINITE_COUNTERMODEL",
            "verification_status": "DERIVED_REFUTED",
            "derivation_rule": "false_source_weakening",
            "trust_level": "derived_from_verified_traces",
            "parent_claims": [],
            "parent_pairs": [],
            "route": "derived_false_source_weakening",
            "explanation": "logical",
            "certificate_preservation_status": "source_preservation_requires_replay",
            "failure_reason": "table_does_not_satisfy_derived_source",
        }
    )
    assert cert.failure_reason == "table_does_not_satisfy_derived_source"
    assert cert.verification_status == "DERIVED_REFUTED"
