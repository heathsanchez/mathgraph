from mathgraph.continuation_traces import ContinuationTrace, ContinuationTraceStore, make_trace_id


def _trace(**overrides):
    payload = {
        "trace_id": "",
        "episode_id": "ep1",
        "claim_id": "claim1",
        "source": "(x*x)=x",
        "target": "(x*y)=x",
        "source_idx": 1,
        "target_idx": 2,
        "root_label": "new_variable_freedom_obstruction",
        "root_score": 0.9,
        "basin_label": "root_basin",
        "detector_evidence": {"new_target_vars": ["y"]},
        "route_type": "finite_countermodel_search",
        "constructor_family": "free_variable_separating_countermodel_family",
        "constructor_config": {"max_countermodel_order": 2},
        "status": "verified_false",
        "terminal_form": "REFUTATION_CERTIFICATE",
        "trust_level": "FINITE_VERIFIED",
        "provenance_type": "PRIMITIVE",
        "verifier_boundary": "IMPORTER_REVALIDATED",
        "certificate_id": "cert1",
        "obstruction_label": None,
        "attempted": True,
        "verified": True,
        "promoted": True,
        "known_skipped": False,
        "near_miss_score": 0.0,
        "residual_compression_delta": 1.0,
        "novelty_score": 1.0,
        "elapsed_sec": 0.1,
        "warnings": ["Continuation traces are memory, not truth."],
        "evidence": {"advisory_only": True},
        "created_at": "2026-01-01T00:00:00+00:00",
    }
    payload.update(overrides)
    payload["trace_id"] = payload["trace_id"] or make_trace_id(payload)
    return ContinuationTrace.from_dict(payload)


def test_continuation_trace_round_trips_to_dict():
    trace = _trace()

    loaded = ContinuationTrace.from_dict(trace.to_dict())

    assert loaded == trace
    assert loaded.verified is True
    assert loaded.promoted is True


def test_continuation_trace_store_append_load_filter_summary(tmp_path):
    path = tmp_path / "traces.jsonl"
    store = ContinuationTraceStore(path)
    verified = _trace()
    residual = _trace(
        trace_id="",
        claim_id="claim2",
        status="residual",
        terminal_form="NONE",
        trust_level="ADVISORY_ROUTE",
        provenance_type="SYSTEM",
        verifier_boundary="NOT_VERIFIED",
        certificate_id=None,
        verified=False,
        promoted=False,
        constructor_family="residual_search_family",
        near_miss_score=0.7,
        residual_compression_delta=0.0,
    )

    assert store.append_many([verified, residual]) == 2

    rows = store.load_all()
    assert len(rows) == 2
    assert store.filter_by_episode("ep1") == rows
    assert store.filter_by_root("new_variable_freedom_obstruction") == rows
    assert len(store.filter_by_constructor("residual_search_family")) == 1
    assert len(store.filter_by_status("verified_false")) == 1
    summary = store.summary()
    assert summary["trace_count"] == 2
    assert summary["verified_count"] == 1
    assert summary["promoted_count"] == 1
    assert summary["near_miss_count"] == 1
