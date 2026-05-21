from mathgraph.contact_promotion import ContactKind, ContactPromotionEngine, PromotionPolicy


def clean_row(idx: int, *, shape: str = "shape_a", strategy: str = "exact_existing") -> dict[str, str]:
    return {
        "probe_id": f"p{idx}",
        "level": "L2_STRICT_CONTACT",
        "shape": shape,
        "theorem_decl": f"Nat.thm{idx}",
        "repair_strategy": strategy,
        "strict_success": "true",
        "marker_start": "true",
        "marker_ok": "true",
        "marker_end": "true",
    }


def test_one_clean_strict_contact_becomes_seed_not_law():
    engine = ContactPromotionEngine()
    engine.ingest_probe_rows([clean_row(1)])
    assert engine.seeds[0].kind == ContactKind.STRICT_CONTACT_SEED
    assert engine.to_route_law_rows() == []


def test_three_compatible_clean_contacts_promote():
    engine = ContactPromotionEngine()
    engine.ingest_probe_rows([clean_row(1), clean_row(2), clean_row(3)])
    laws = engine.to_route_law_rows()
    assert len(laws) == 1
    assert laws[0]["law_kind"] == "PROMOTED_ROUTE_LAW"


def test_dirty_interval_becomes_repairable_obstruction():
    engine = ContactPromotionEngine()
    engine.ingest_probe_rows(
        [
            {
                "probe_id": "dirty",
                "level": "L2_STRICT_CONTACT",
                "shape": "shape_a",
                "theorem_decl": "Nat.bad",
                "repair_strategy": "simp",
                "strict_success": "false",
                "dirty_interval": "true",
            }
        ]
    )
    assert engine.obstructions[0].failure_class == "parse_or_command_boundary_error"


def test_visibility_contact_does_not_promote_by_default():
    rows = [clean_row(1), clean_row(2), clean_row(3)]
    for row in rows:
        row["level"] = "L1_VISIBILITY_CONTACT"
        row["repair_strategy"] = "visibility_check"
    engine = ContactPromotionEngine()
    engine.ingest_probe_rows(rows)
    assert engine.to_route_law_rows() == []


def test_promotion_policy_can_be_overridden():
    engine = ContactPromotionEngine(PromotionPolicy(min_clean_successes=1, min_transfer_successes=0, require_distinct_declarations=1))
    engine.ingest_probe_rows([clean_row(1)])
    assert len(engine.to_route_law_rows()) == 1


def test_failure_rate_blocks_promotion():
    rows = [clean_row(1), clean_row(2), clean_row(3)]
    rows.append(
        {
            "probe_id": "dirty",
            "level": "L2_STRICT_CONTACT",
            "shape": "shape_a",
            "theorem_decl": "Nat.bad",
            "repair_strategy": "exact_existing",
            "strict_success": "false",
            "dirty_interval": "true",
        }
    )
    engine = ContactPromotionEngine()
    engine.ingest_probe_rows(rows)
    assert engine.to_route_law_rows() == []


def test_transfer_and_repair_queues_generated():
    engine = ContactPromotionEngine()
    engine.ingest_probe_rows([clean_row(1), {"probe_id": "bad", "strict_success": "false"}])
    assert engine.build_transfer_queue()
    assert engine.build_repair_queue()
