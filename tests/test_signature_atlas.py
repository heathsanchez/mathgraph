from mathgraph.signature_atlas import SignatureAtlas, estimate_signature_features, parse_check_output


def test_parses_simple_theorem():
    record = parse_check_output("Nat.dvd_refl (a : ℕ) : a ∣ a", "Nat.dvd_refl", shape="nat_dvd")
    assert record.namespace == "Nat"
    assert record.returns_prop is True
    assert record.explicit_binder_count == 1
    assert record.can_be_exact_term_candidate is True


def test_parses_implicit_binders():
    record = parse_check_output(
        "Nat.dvd_trans {a b c : ℕ} (h₁ : a ∣ b) (h₂ : b ∣ c) : a ∣ c",
        "Nat.dvd_trans",
    )
    assert record.implicit_binder_count == 3
    assert record.explicit_binder_count == 2
    assert record.needs_hypotheses is True


def test_parses_typeclass_binder():
    record = parse_check_output(
        "le_trans.{u} {α : Type u} [Preorder α] {a b c : α} : a ≤ b → b ≤ c → a ≤ c",
        "le_trans",
    )
    assert record.typeclass_binder_count == 1
    assert record.has_typeclass_requirements is True
    assert record.has_universe_params is True


def test_detects_returns_prop():
    features = estimate_signature_features("foo (a : Nat) : a = a")
    assert features["returns_prop"] is True


def test_survives_malformed_input_without_crashing():
    record = parse_check_output("not really a lean signature", "Mystery.bad")
    assert record.decl_name == "Mystery.bad"
    assert record.arity_estimate >= 0


def test_signature_atlas_roundtrip_rows():
    record = parse_check_output("Nat.dvd_refl (a : ℕ) : a ∣ a", "Nat.dvd_refl")
    atlas = SignatureAtlas([record])
    rebuilt = SignatureAtlas.from_rows(atlas.to_rows())
    assert rebuilt.get("Nat.dvd_refl") is not None
