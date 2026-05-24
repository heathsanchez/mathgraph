"""Constructor family metadata for advisory PQ-IR routing."""

from __future__ import annotations

from dataclasses import dataclass


FAMILY_NAMES = (
    "constant",
    "left_projection",
    "right_projection",
    "projection_exception_left",
    "projection_exception_right",
    "quotient_spike",
    "quotient_fresh_gate",
    "random_fresh_sink",
    "random_fresh_collapse",
    "fresh_absorber",
    "fresh_gate_right",
    "fresh_gate_left",
    "linear_combo_mod",
    "add_mod",
    "sub_mod",
    "xor_mod",
    "diagonal_spike",
    "diag_perturb_right",
    "diag_perturb_left",
    "tail_coupled_projection",
    "head_coupled_projection",
    "diagonal_escape",
    "idempotent_random",
    "row_erasure_family",
    "col_erasure_family",
    "block_selector",
    "block_selector_dual",
    "prior",
)


@dataclass(frozen=True)
class ConstructorFamily:
    family: str
    description: str
    advisory_only: bool = True
    can_promote_truth: bool = False

    def to_dict(self) -> dict[str, object]:
        return dict(self.__dict__)


DESCRIPTIONS = {
    "constant": "collapse all products to a chosen element",
    "left_projection": "return the left input",
    "right_projection": "return the right input",
    "quotient_spike": "localized exception around quotient classes",
    "quotient_fresh_gate": "gate behavior for fresh variables escaping quotient pressure",
    "linear_combo_mod": "modular affine combination",
    "add_mod": "modular addition",
    "sub_mod": "modular subtraction",
    "xor_mod": "binary xor",
    "diagonal_spike": "diagonal perturbation",
    "tail_coupled_projection": "projection coupled to tail continuation",
    "head_coupled_projection": "projection coupled to head continuation",
    "prior": "existing baseline constructor family",
}

DEFAULT_PRIORITY_BY_BASIN: dict[str, tuple[str, ...]] = {
    "projection_pressure": ("left_projection", "right_projection", "projection_exception_left", "projection_exception_right"),
    "collapse_or_constant_pressure": ("constant", "random_fresh_collapse", "fresh_absorber"),
    "fresh_variable_escape": ("quotient_fresh_gate", "fresh_gate_right", "fresh_gate_left", "random_fresh_sink"),
    "commutativity_pressure": ("add_mod", "xor_mod", "linear_combo_mod"),
    "idempotent_band_pressure": ("diagonal_spike", "idempotent_random", "block_selector"),
    "associative_or_deep_term_pressure": ("tail_coupled_projection", "head_coupled_projection", "diagonal_escape"),
    "mixed_sair_false_pair": ("prior", "quotient_spike", "diag_perturb_right", "diag_perturb_left"),
}


def all_constructor_families() -> list[ConstructorFamily]:
    return [ConstructorFamily(name, DESCRIPTIONS.get(name, name.replace("_", " "))) for name in FAMILY_NAMES]


def normalize_family_name(value: str) -> str:
    text = str(value or "").strip().lower().replace("-", "_").replace(":", "_")
    aliases = {
        "projection": "left_projection",
        "affine": "linear_combo_mod",
        "band": "block_selector",
        "semilattice": "idempotent_random",
    }
    return aliases.get(text, text if text in FAMILY_NAMES else "prior")


def parse_constructor_id(constructor_id: str) -> dict[str, str]:
    parts = str(constructor_id or "").split(":")
    family = normalize_family_name(parts[0]) if parts else "prior"
    return {
        "family": family,
        "name": parts[1] if len(parts) > 1 else "",
        "carrier": parts[2] if len(parts) > 2 else "",
        "hash": parts[3] if len(parts) > 3 else "",
    }


def default_priority_for_basin(basin: str) -> list[str]:
    return list(DEFAULT_PRIORITY_BY_BASIN.get(str(basin or ""), DEFAULT_PRIORITY_BY_BASIN["mixed_sair_false_pair"]))
