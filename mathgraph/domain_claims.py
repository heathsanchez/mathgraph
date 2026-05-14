"""Domain-general claim IR and lightweight formal-world registry.

Parsing, normalization, world selection, and adapter routing are advisory
structure. They help MathGraph decide what verifier-bound route to try, but
they do not verify claims and cannot create terminal truth.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from mathgraph.hashing import content_id
from mathgraph.proof_verification import ProofArtifact, make_lean_skeleton
from mathgraph.verification_episode import VerificationEpisodeInput, VerificationRouteKind, run_verification_episode


class ClaimKind(str, Enum):
    EQUATIONAL_IMPLICATION = "EQUATIONAL_IMPLICATION"
    THEOREM_STATEMENT = "THEOREM_STATEMENT"
    COUNTERMODEL_QUERY = "COUNTERMODEL_QUERY"
    PROGRAM_PROPERTY = "PROGRAM_PROPERTY"
    SCIENTIFIC_HYPOTHESIS = "SCIENTIFIC_HYPOTHESIS"
    SEMANTIC_ASSERTION = "SEMANTIC_ASSERTION"
    UNKNOWN = "UNKNOWN"


class FormalWorldKind(str, Enum):
    MAGMA_EQUATIONAL = "MAGMA_EQUATIONAL"
    LEAN = "LEAN"
    ISABELLE = "ISABELLE"
    COQ = "COQ"
    ROQC = "ROQC"
    PYTHON_PROPERTY = "PYTHON_PROPERTY"
    SMT = "SMT"
    NATURAL_LANGUAGE = "NATURAL_LANGUAGE"
    UNKNOWN = "UNKNOWN"


class ClaimIRStatus(str, Enum):
    RAW = "RAW"
    PARSED = "PARSED"
    NORMALIZED = "NORMALIZED"
    ROUTABLE = "ROUTABLE"
    ADAPTER_SUPPORTED = "ADAPTER_SUPPORTED"
    VERIFIER_SUPPORTED = "VERIFIER_SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    RESIDUAL = "RESIDUAL"
    ADVISORY_ONLY = "ADVISORY_ONLY"


@dataclass
class DomainClaim:
    claim_id: str
    kind: ClaimKind
    world: FormalWorldKind
    raw: str
    source: str | None = None
    target: str | None = None
    normalized: str | None = None
    variables: tuple[str, ...] = ()
    operators: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    conclusion: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    advisory: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "kind": self.kind.value,
            "world": self.world.value,
            "raw": self.raw,
            "source": self.source,
            "target": self.target,
            "normalized": self.normalized,
            "variables": list(self.variables),
            "operators": list(self.operators),
            "assumptions": list(self.assumptions),
            "conclusion": self.conclusion,
            "metadata": dict(self.metadata),
            "advisory": self.advisory,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DomainClaim":
        return cls(
            claim_id=str(data["claim_id"]),
            kind=_claim_kind(data.get("kind")),
            world=_world_kind(data.get("world")),
            raw=str(data.get("raw", "")),
            source=_optional_str(data.get("source")),
            target=_optional_str(data.get("target")),
            normalized=_optional_str(data.get("normalized")),
            variables=tuple(str(item) for item in data.get("variables", ())),
            operators=tuple(str(item) for item in data.get("operators", ())),
            assumptions=tuple(str(item) for item in data.get("assumptions", ())),
            conclusion=_optional_str(data.get("conclusion")),
            metadata=dict(data.get("metadata", {})),
            advisory=bool(data.get("advisory", True)),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "DomainClaim":
        return cls.from_dict(json.loads(text))

    def to_jsonl_line(self) -> str:
        return self.to_json() + "\n"

    @classmethod
    def from_jsonl_line(cls, line: str) -> "DomainClaim":
        return cls.from_json(line.strip())


@dataclass
class FormalWorld:
    world_id: str
    kind: FormalWorldKind
    name: str
    description: str = ""
    claim_kinds: tuple[ClaimKind, ...] = ()
    verifier_kinds: tuple[str, ...] = ()
    supports_countermodels: bool = False
    supports_proofs: bool = False
    supports_normalization: bool = False
    adapter_name: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    advisory: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "world_id": self.world_id,
            "kind": self.kind.value,
            "name": self.name,
            "description": self.description,
            "claim_kinds": [kind.value for kind in self.claim_kinds],
            "verifier_kinds": list(self.verifier_kinds),
            "supports_countermodels": self.supports_countermodels,
            "supports_proofs": self.supports_proofs,
            "supports_normalization": self.supports_normalization,
            "adapter_name": self.adapter_name,
            "metadata": dict(self.metadata),
            "advisory": self.advisory,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "FormalWorld":
        return cls(
            world_id=str(data["world_id"]),
            kind=_world_kind(data.get("kind")),
            name=str(data["name"]),
            description=str(data.get("description", "")),
            claim_kinds=tuple(_claim_kind(item) for item in data.get("claim_kinds", ())),
            verifier_kinds=tuple(str(item) for item in data.get("verifier_kinds", ())),
            supports_countermodels=bool(data.get("supports_countermodels", False)),
            supports_proofs=bool(data.get("supports_proofs", False)),
            supports_normalization=bool(data.get("supports_normalization", False)),
            adapter_name=_optional_str(data.get("adapter_name")),
            metadata=dict(data.get("metadata", {})),
            advisory=bool(data.get("advisory", True)),
        )


@dataclass
class ClaimParseResult:
    result_id: str
    claim_id: str
    status: ClaimIRStatus
    domain_claim: DomainClaim
    parser_name: str | None = None
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    advisory: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "result_id": self.result_id,
            "claim_id": self.claim_id,
            "status": self.status.value,
            "domain_claim": self.domain_claim.to_dict(),
            "parser_name": self.parser_name,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "metadata": dict(self.metadata),
            "advisory": self.advisory,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ClaimParseResult":
        return cls(
            result_id=str(data["result_id"]),
            claim_id=str(data["claim_id"]),
            status=ClaimIRStatus(str(data.get("status", ClaimIRStatus.RAW.value))),
            domain_claim=DomainClaim.from_dict(data["domain_claim"]),
            parser_name=_optional_str(data.get("parser_name")),
            errors=tuple(str(item) for item in data.get("errors", ())),
            warnings=tuple(str(item) for item in data.get("warnings", ())),
            metadata=dict(data.get("metadata", {})),
            advisory=bool(data.get("advisory", True)),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "ClaimParseResult":
        return cls.from_dict(json.loads(text))


@dataclass
class FormalWorldRegistry:
    registry_id: str
    worlds: dict[str, FormalWorld] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)
    advisory: bool = True

    def register(self, world: FormalWorld) -> None:
        self.worlds[world.world_id] = world
        self.registry_id = make_formal_world_registry_id([item.to_dict() for item in self.worlds.values()])

    def get(self, world_id: str) -> FormalWorld | None:
        return self.worlds.get(world_id)

    def by_kind(self, kind: FormalWorldKind | str) -> list[FormalWorld]:
        wanted = _world_kind(kind)
        return [world for world in self.worlds.values() if world.kind == wanted]

    def supports_claim_kind(self, kind: ClaimKind | str) -> bool:
        wanted = _claim_kind(kind)
        return any(wanted in world.claim_kinds for world in self.worlds.values())

    def to_dict(self) -> dict[str, Any]:
        return {
            "registry_id": self.registry_id,
            "worlds": {key: world.to_dict() for key, world in sorted(self.worlds.items())},
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
            "advisory": self.advisory,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "FormalWorldRegistry":
        return cls(
            registry_id=str(data["registry_id"]),
            worlds={str(key): FormalWorld.from_dict(value) for key, value in dict(data.get("worlds", {})).items()},
            created_at=str(data.get("created_at") or datetime.now(timezone.utc).isoformat()),
            metadata=dict(data.get("metadata", {})),
            advisory=bool(data.get("advisory", True)),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "FormalWorldRegistry":
        return cls.from_dict(json.loads(text))

    def write_json(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.to_dict(), sort_keys=True, indent=2) + "\n", encoding="utf-8")

    @classmethod
    def read_json(cls, path: str | Path) -> "FormalWorldRegistry":
        return cls.from_json(Path(path).read_text(encoding="utf-8"))


class DomainAdapter:
    name = "domain_adapter"
    world_kind = FormalWorldKind.UNKNOWN

    def parse(self, raw: str) -> ClaimParseResult:
        raise NotImplementedError

    def normalize(self, claim: DomainClaim) -> DomainClaim:
        return normalize_domain_claim(claim)

    def to_episode_input(self, claim: DomainClaim) -> VerificationEpisodeInput | None:
        return domain_claim_to_verification_episode_input(claim)

    def to_proof_artifact(self, claim: DomainClaim) -> ProofArtifact | None:
        return None


class MagmaEquationalAdapter(DomainAdapter):
    name = "magma_equational"
    world_kind = FormalWorldKind.MAGMA_EQUATIONAL

    def parse(self, raw: str) -> ClaimParseResult:
        return parse_domain_claim(raw, kind=ClaimKind.EQUATIONAL_IMPLICATION, world=FormalWorldKind.MAGMA_EQUATIONAL)


class LeanSkeletonAdapter(DomainAdapter):
    name = "lean_skeleton"
    world_kind = FormalWorldKind.LEAN

    def parse(self, raw: str) -> ClaimParseResult:
        return parse_domain_claim(raw, kind=ClaimKind.THEOREM_STATEMENT, world=FormalWorldKind.LEAN)

    def to_proof_artifact(self, claim: DomainClaim) -> ProofArtifact | None:
        if claim.world != FormalWorldKind.LEAN:
            return None
        return make_lean_skeleton(
            claim_id=claim.claim_id,
            source=claim.raw,
            target=claim.conclusion,
            theorem_name=_theorem_name(claim.raw),
            metadata={"domain_claim": claim.to_dict(), "advisory_only": True},
        )


class AdvisoryOnlyAdapter(DomainAdapter):
    name = "advisory_only"
    world_kind = FormalWorldKind.NATURAL_LANGUAGE

    def parse(self, raw: str) -> ClaimParseResult:
        return parse_domain_claim(raw, kind=ClaimKind.UNKNOWN, world=FormalWorldKind.NATURAL_LANGUAGE)

    def to_episode_input(self, claim: DomainClaim) -> VerificationEpisodeInput | None:
        return VerificationEpisodeInput(
            claim_id=claim.claim_id,
            source=claim.raw,
            route_hint=VerificationRouteKind.RESIDUAL_ONLY,
            metadata={"domain_claim": claim.to_dict(), "advisory_only": True, "unsupported_world": True},
        )


def default_formal_world_registry() -> FormalWorldRegistry:
    worlds = [
        FormalWorld(
            world_id="world_magma_equational",
            kind=FormalWorldKind.MAGMA_EQUATIONAL,
            name="Magma Equational Implication",
            description="SAIR/ETP-style equational implication over magmas.",
            claim_kinds=(ClaimKind.EQUATIONAL_IMPLICATION, ClaimKind.COUNTERMODEL_QUERY),
            verifier_kinds=("finite_countermodel_importer",),
            supports_countermodels=True,
            supports_proofs=False,
            supports_normalization=True,
            adapter_name="magma_equational",
            metadata={"advisory_only": True},
        ),
        FormalWorld(
            world_id="world_lean",
            kind=FormalWorldKind.LEAN,
            name="Lean theorem statement",
            description="Lean-looking theorem artifacts routed to proof skeleton lifecycle.",
            claim_kinds=(ClaimKind.THEOREM_STATEMENT,),
            verifier_kinds=("lean",),
            supports_proofs=True,
            supports_countermodels=False,
            adapter_name="lean_skeleton",
            metadata={"advisory_until_verifier_runs": True},
        ),
        FormalWorld(
            world_id="world_isabelle",
            kind=FormalWorldKind.ISABELLE,
            name="Isabelle theorem statement",
            claim_kinds=(ClaimKind.THEOREM_STATEMENT,),
            verifier_kinds=("isabelle_future",),
            supports_proofs=True,
            adapter_name="isabelle_future",
            metadata={"future_work": True},
        ),
        FormalWorld(
            world_id="world_python_property",
            kind=FormalWorldKind.PYTHON_PROPERTY,
            name="Python property",
            claim_kinds=(ClaimKind.PROGRAM_PROPERTY,),
            adapter_name="python_property_future",
            metadata={"future_work": True, "advisory_only": True},
        ),
        FormalWorld(
            world_id="world_natural_language",
            kind=FormalWorldKind.NATURAL_LANGUAGE,
            name="Natural language advisory claims",
            claim_kinds=(ClaimKind.SCIENTIFIC_HYPOTHESIS, ClaimKind.SEMANTIC_ASSERTION, ClaimKind.UNKNOWN),
            adapter_name="advisory_only",
            metadata={"advisory_only": True, "not_terminal_truth": True},
        ),
    ]
    registry = FormalWorldRegistry(
        registry_id=make_formal_world_registry_id([world.to_dict() for world in worlds]),
        worlds={world.world_id: world for world in worlds},
        metadata={"advisory_only": True, "parsing_is_not_truth": True},
    )
    return registry


def parse_domain_claim(
    raw: str,
    *,
    kind: ClaimKind | str | None = None,
    world: FormalWorldKind | str | None = None,
    claim_id: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> ClaimParseResult:
    raw_text = str(raw)
    inferred_kind, inferred_world = _infer_kind_world(raw_text, kind, world)
    claim_id = claim_id or make_domain_claim_id(raw_text, inferred_kind.value, inferred_world.value)
    parsed = _claim_for_kind_world(claim_id, raw_text, inferred_kind, inferred_world, metadata or {})
    normalized = normalize_domain_claim(parsed)
    status = _parse_status(normalized)
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    if inferred_world == FormalWorldKind.NATURAL_LANGUAGE:
        warnings = ("natural language claims are advisory/residual without a verifier/importer boundary",)
    if inferred_kind == ClaimKind.EQUATIONAL_IMPLICATION and not (normalized.source and normalized.target):
        status = ClaimIRStatus.RESIDUAL
        errors = ("equational implication missing source or target",)
    result_payload = {
        "claim_id": claim_id,
        "raw": raw_text,
        "kind": inferred_kind.value,
        "world": inferred_world.value,
        "normalized": normalized.to_dict(),
    }
    return ClaimParseResult(
        result_id=content_id("claim_parse_result", result_payload, n=24),
        claim_id=claim_id,
        status=status,
        domain_claim=normalized,
        parser_name=_parser_name(inferred_world),
        errors=errors,
        warnings=warnings,
        metadata={"advisory_only": True, "parsing_is_not_truth": True},
        advisory=True,
    )


def normalize_domain_claim(claim: DomainClaim) -> DomainClaim:
    metadata = dict(claim.metadata)
    metadata.setdefault("raw_original", claim.raw)
    if claim.world == FormalWorldKind.MAGMA_EQUATIONAL:
        source = _normalize_magma_text(claim.source or "")
        target = _normalize_magma_text(claim.target or "")
        normalized = f"{source} => {target}" if source or target else _normalize_magma_text(claim.raw).replace("->", "=>")
        source_target = _split_implication(normalized)
        if source_target:
            source, target = source_target
        return DomainClaim(
            claim_id=claim.claim_id,
            kind=claim.kind,
            world=claim.world,
            raw=claim.raw,
            source=source or None,
            target=target or None,
            normalized=normalized.strip(),
            variables=_extract_variables(normalized),
            operators=_extract_operators(normalized),
            assumptions=claim.assumptions,
            conclusion=target or claim.conclusion,
            metadata={**metadata, "normalized_advisory_only": True},
            advisory=True,
        )
    normalized = " ".join(claim.raw.strip().split())
    return DomainClaim(
        claim_id=claim.claim_id,
        kind=claim.kind,
        world=claim.world,
        raw=claim.raw,
        source=claim.source,
        target=claim.target,
        normalized=normalized,
        variables=claim.variables,
        operators=claim.operators,
        assumptions=claim.assumptions,
        conclusion=claim.conclusion,
        metadata={**metadata, "normalized_advisory_only": True},
        advisory=True,
    )


def route_domain_claim_to_existing_inputs(claim: DomainClaim) -> dict[str, Any]:
    if claim.kind == ClaimKind.EQUATIONAL_IMPLICATION and claim.world == FormalWorldKind.MAGMA_EQUATIONAL:
        return {
            "claim_id": claim.claim_id,
            "source": claim.source,
            "target": claim.target,
            "metadata": {"domain_claim": claim.to_dict(), "advisory_only": True},
        }
    if claim.world == FormalWorldKind.LEAN and claim.kind == ClaimKind.THEOREM_STATEMENT:
        return {
            "claim_id": claim.claim_id,
            "source": claim.raw,
            "target": claim.conclusion,
            "theorem_name": _theorem_name(claim.raw),
            "metadata": {"domain_claim": claim.to_dict(), "advisory_only": True},
        }
    return {
        "claim_id": claim.claim_id,
        "route_hint": VerificationRouteKind.RESIDUAL_ONLY.value,
        "metadata": {"domain_claim": claim.to_dict(), "unsupported_or_advisory": True},
    }


def get_default_domain_adapters() -> dict[str, DomainAdapter]:
    adapters: list[DomainAdapter] = [MagmaEquationalAdapter(), LeanSkeletonAdapter(), AdvisoryOnlyAdapter()]
    return {adapter.name: adapter for adapter in adapters}


def domain_claim_to_verification_episode_input(claim: DomainClaim) -> VerificationEpisodeInput:
    routed = route_domain_claim_to_existing_inputs(claim)
    if claim.kind == ClaimKind.EQUATIONAL_IMPLICATION and claim.world == FormalWorldKind.MAGMA_EQUATIONAL:
        route_hint = VerificationRouteKind.BOTH_SIDES
    elif claim.world == FormalWorldKind.LEAN:
        route_hint = VerificationRouteKind.PROOF_VERIFICATION
    else:
        route_hint = VerificationRouteKind.RESIDUAL_ONLY
    return VerificationEpisodeInput(
        claim_id=claim.claim_id,
        source=_optional_str(routed.get("source")) or claim.source or claim.raw,
        target=_optional_str(routed.get("target")) or claim.target or claim.conclusion,
        route_hint=route_hint,
        metadata={**dict(routed.get("metadata", {})), "domain_world": claim.world.value, "advisory_only": True},
    )


def run_domain_claim_pipeline(
    *,
    raw_claims: Sequence[str] = (),
    claims: Sequence[DomainClaim] = (),
    registry: FormalWorldRegistry | None = None,
    run_episodes: bool = False,
    episode_kwargs: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    registry = registry or default_formal_world_registry()
    parse_results = [parse_domain_claim(raw) for raw in raw_claims]
    normalized_claims = [result.domain_claim for result in parse_results]
    normalized_claims.extend(normalize_domain_claim(claim) for claim in claims)
    unsupported = [
        claim
        for claim in normalized_claims
        if not any(claim.kind in world.claim_kinds for world in registry.by_kind(claim.world))
        or claim.world in {FormalWorldKind.NATURAL_LANGUAGE, FormalWorldKind.UNKNOWN}
    ]
    episodes = []
    if run_episodes:
        kwargs = {
            "constructor_dry_run": True,
            "run_alignment": True,
            **dict(episode_kwargs or {}),
        }
        for claim in normalized_claims:
            episodes.append(run_verification_episode(episode_input=domain_claim_to_verification_episode_input(claim), **kwargs))
    return {
        "registry": registry.to_dict(),
        "claims": [claim.to_dict() for claim in normalized_claims],
        "parse_results": [result.to_dict() for result in parse_results],
        "episode_traces": [episode.to_dict() for episode in episodes],
        "unsupported_claims": [claim.to_dict() for claim in unsupported],
        "summary": {
            "claims_total": len(normalized_claims),
            "parse_results_total": len(parse_results),
            "unsupported_total": len(unsupported),
            "episodes_total": len(episodes),
            "advisory_only": True,
            "parsing_is_not_truth": True,
        },
    }


def make_domain_claim_id(raw: str, kind: str = "", world: str = "") -> str:
    return content_id("domain_claim", {"raw": raw, "kind": kind, "world": world}, n=24)


def make_formal_world_registry_id(payload: Any) -> str:
    return content_id("formal_world_registry", payload, n=24)


def _claim_for_kind_world(
    claim_id: str,
    raw: str,
    kind: ClaimKind,
    world: FormalWorldKind,
    metadata: Mapping[str, Any],
) -> DomainClaim:
    source = target = None
    assumptions: tuple[str, ...] = ()
    conclusion = None
    if kind == ClaimKind.EQUATIONAL_IMPLICATION:
        split = _split_implication(raw)
        if split:
            source, target = split
            conclusion = target
            assumptions = (source,)
    elif world == FormalWorldKind.LEAN:
        conclusion = _lean_conclusion(raw)
    return DomainClaim(
        claim_id=claim_id,
        kind=kind,
        world=world,
        raw=raw,
        source=source,
        target=target,
        normalized=None,
        variables=_extract_variables(raw) if world == FormalWorldKind.MAGMA_EQUATIONAL else (),
        operators=_extract_operators(raw),
        assumptions=assumptions,
        conclusion=conclusion,
        metadata={**dict(metadata), "advisory_only": True},
        advisory=True,
    )


def _infer_kind_world(
    raw: str,
    kind: ClaimKind | str | None,
    world: FormalWorldKind | str | None,
) -> tuple[ClaimKind, FormalWorldKind]:
    stripped = raw.strip()
    lowered = stripped.lower()
    inferred_kind = ClaimKind.UNKNOWN
    inferred_world = FormalWorldKind.NATURAL_LANGUAGE
    if ("=>" in stripped or "->" in stripped) and _looks_algebraic(stripped):
        inferred_kind = ClaimKind.EQUATIONAL_IMPLICATION
        inferred_world = FormalWorldKind.MAGMA_EQUATIONAL
    elif lowered.startswith(("theorem ", "lemma ", "example ", "import ")) or ":=" in stripped:
        inferred_kind = ClaimKind.THEOREM_STATEMENT
        inferred_world = FormalWorldKind.LEAN
    return (_claim_kind(kind) if kind is not None else inferred_kind, _world_kind(world) if world is not None else inferred_world)


def _split_implication(raw: str) -> tuple[str, str] | None:
    if "=>" in raw:
        left, right = raw.split("=>", 1)
        return " ".join(left.strip().split()), " ".join(right.strip().split())
    if "->" in raw:
        left, right = raw.split("->", 1)
        return " ".join(left.strip().split()), " ".join(right.strip().split())
    return None


def _normalize_magma_text(text: str) -> str:
    return " ".join(text.replace("◇", "*").replace("⋄", "*").replace("->", "=>").strip().split())


def _extract_variables(text: str) -> tuple[str, ...]:
    words = re.findall(r"\b[a-z][A-Za-z0-9_]*\b", text)
    return tuple(sorted(set(words)))


def _extract_operators(text: str) -> tuple[str, ...]:
    operators = []
    for token in ("*", "◇", "⋄", "+"):
        if token in text:
            operators.append("*" if token in {"◇", "⋄"} else token)
    return tuple(sorted(set(operators)))


def _looks_algebraic(text: str) -> bool:
    return bool(re.search(r"\b[a-z]\b", text)) and any(token in text for token in ("*", "◇", "⋄", "=", "+"))


def _lean_conclusion(raw: str) -> str | None:
    text = " ".join(raw.strip().split())
    if " : " in text:
        after = text.split(" : ", 1)[1]
        return after.split(" :=", 1)[0].strip()
    return None


def _theorem_name(raw: str) -> str | None:
    match = re.match(r"\s*(?:theorem|lemma|example)\s+([A-Za-z_][A-Za-z0-9_']*)", raw)
    return match.group(1) if match else None


def _parse_status(claim: DomainClaim) -> ClaimIRStatus:
    if claim.world == FormalWorldKind.NATURAL_LANGUAGE:
        return ClaimIRStatus.ADVISORY_ONLY
    if claim.normalized and claim.world == FormalWorldKind.MAGMA_EQUATIONAL:
        return ClaimIRStatus.NORMALIZED
    if claim.world == FormalWorldKind.LEAN:
        return ClaimIRStatus.ROUTABLE
    return ClaimIRStatus.PARSED


def _parser_name(world: FormalWorldKind) -> str:
    if world == FormalWorldKind.MAGMA_EQUATIONAL:
        return "magma_equational"
    if world == FormalWorldKind.LEAN:
        return "lean_skeleton"
    return "advisory_only"


def _claim_kind(value: ClaimKind | str | None) -> ClaimKind:
    if isinstance(value, ClaimKind):
        return value
    if value in (None, ""):
        return ClaimKind.UNKNOWN
    return ClaimKind(str(value))


def _world_kind(value: FormalWorldKind | str | None) -> FormalWorldKind:
    if isinstance(value, FormalWorldKind):
        return value
    if value in (None, ""):
        return FormalWorldKind.UNKNOWN
    return FormalWorldKind(str(value))


def _optional_str(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value)
