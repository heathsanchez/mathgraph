from mathgraph.closed_loop import ClosedVerificationLoop


def test_can_submit_and_schedule_pairs():
    loop = ClosedVerificationLoop()
    loop.submit_many([(f"s{i}", f"t{i}") for i in range(5)])
    tasks = loop.schedule(top_k=3)
    assert len(tasks) == 3
    assert len(loop.pending) == 5


def test_record_outcome_removes_pending_pair():
    loop = ClosedVerificationLoop()
    loop.submit_pending(("s", "t"))
    loop.record_outcome("s", "t", "VERIFIED_PROOF", "direct_substitution_instance")
    assert len(loop.pending) == 0
    assert len(loop.outcomes) == 1


def test_second_schedule_includes_prior_metadata():
    loop = ClosedVerificationLoop()
    loop.submit_many([("s1", "t1"), ("s2", "t2")])
    loop.record_outcome("s1", "t1", "VERIFIED_PROOF", "direct_substitution_instance")
    tasks = loop.schedule(top_k=1)
    assert tasks[0].metadata["prior_from_outcome_count"] == 1


def test_stats_terminal_form_distribution_updates():
    loop = ClosedVerificationLoop()
    loop.record_outcome("s", "t", "FINITE_COUNTERMODEL", "finite_countermodel", verification_status="REFUTED")
    stats = loop.stats()
    assert stats.terminal_form_distribution["FINITE_COUNTERMODEL"] == 1


def test_no_outcome_scheduler_still_works():
    loop = ClosedVerificationLoop()
    loop.submit_pending(("s", "t"))
    assert loop.schedule(top_k=10)


def test_warnings_include_advisory_nature():
    loop = ClosedVerificationLoop()
    assert "advisory" in " ".join(loop.stats().warnings).lower()
