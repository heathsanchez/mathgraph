"""Advisory continuation action registry.

Continuation actions generate candidate next moves from claims and traces. They
are proposal mechanisms only; generated claims, tasks, proof artifacts,
projection candidates, and obstruction names are not terminal truth.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from mathgraph.agent_biography import AgentExperience, AgentExperienceOutcome
from mathgraph.alchemy import AlchemicalPhase, AlchemicalStatus, AlchemicalTrace, make_alchemical_trace_id
from mathgraph.certificates import TerminalForm
from mathgraph.domain_claims import (
    ClaimKind,
    DomainClaim,
    FormalWorldKind,
    domain_claim_to_verification_episode_input,
    parse_domain_claim,
)
from mathgraph.hashing import content_id
from mathgraph.proof_verification import ProofArtifact, make_lean_skeleton, make_theorem_schema
from mathgraph.projection import ProjectionCandidate, ProjectionRuleKind, make_projection_candidate_id
from mathgraph.root_constructors import ConstructorPlan
from mathgraph.verification_episode import VerificationEpisodeInput


class ContinuationActionKind(str, Enum):
    SPECIALIZE = "SPECIALIZE"
    GENERALIZE = "GENERALIZE"
    DUALIZE = "DUALIZE"
    IDENTIFY_VARIABLES = "IDENTIFY_VARIABLES"
    DROP_VARIABLE = "DROP_VARIABLE"
    PERMUTE_ROLES = "PERMUTE_ROLES"
    COMPOSE_CLAIMS = "COMPOSE_CLAIMS"
    FORM_IMPLICATION = "FORM_IMPLICATION"
    FORM_EQUIVALENCE = "FORM_EQUIVALENCE"
    NEGATE_TARGET = "NEGATE_TARGET"
    EMIT_PROOF_TASK = "EMIT_PROOF_TASK"
    EMIT_COUNTERMODEL_TASK = "EMIT_COUNTERMODEL_TASK"
    EMIT_PROJECTION_TASK = "EMIT_PROJECTION_TASK"
    EMIT_OBSTRUCTION_TASK = "EMIT_OBSTRUCTION_TASK"
    ABSTRACT_TRACE = "ABSTRACT_TRACE"
    PROJECT_LAWBOOK_ENTRY = "PROJECT_LAWBOOK_ENTRY"
    UNKNOWN = "UNKNOWN"


class ContinuationActionStatus(str, Enum):
    REGISTERED = "REGISTERED"
    APPLICABLE = "APPLICABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    APPLIED = "APPLIED"
    PRODUCED_CANDIDATE = "PRODUCED_CANDIDATE"
    PRODUCED_TASK = "PRODUCED_TASK"
    REJECTED = "REJECTED"
    RESIDUAL = "RESIDUAL"
    ADVISORY_ONLY = "ADVISORY_ONLY"


class ContinuationOutputKind(str, Enum):
    DOMAIN_CLAIM = "DOMAIN_CLAIM"
    EPISODE_INPUT = "EPISODE_INPUT"
    PROOF_ARTIFACT = "PROOF_ARTIFACT"
    PROJECTION_CANDIDATE = "PROJECTION_CANDIDATE"
    CONSTRUCTOR_PLAN = "CONSTRUCTOR_PLAN"
    OBSTRUCTION_CANDIDATE = "OBSTRUCTION_CANDIDATE"
    DEFINITION_CANDIDATE = "DEFINITION_CANDIDATE"
    THEOREM_SCHEMA_CANDIDATE = "THEOREM_SCHEMA_CANDIDATE"
    TASK = "TASK"
    NOTE = "NOTE"
    UNKNOWN = "UNKNOWN"


@dataclass
class ContinuationAction:
    action_id: str
    kind: ContinuationActionKind
    name: str
    description: str = ""
    input_kinds: tuple[str, ...] = ()
    output_kinds: tuple[ContinuationOutputKind, ...] = ()
    supported_worlds: tuple[str, ...] = ()
    deterministic: bool = True
    advisory: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "kind": self.kind.value,
            "name": self.name,
            "description": self.description,
            "input_kinds": list(self.input_kinds),
            "output_kinds": [kind.value for kind in self.output_kinds],
            "supported_worlds": list(self.supported_worlds),
            "deterministic": self.deterministic,
            "advisory": self.advisory,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ContinuationAction":
        return cls(
            action_id=str(data["action_id"]),
            kind=ContinuationActionKind(str(data.get("kind", ContinuationActionKind.UNKNOWN.value))),
            name=str(data["name"]),
            description=str(data.get("description", "")),
            input_kinds=tuple(str(x) for x in data.get("input_kinds", ())),
            output_kinds=tuple(ContinuationOutputKind(str(x)) for x in data.get("output_kinds", ())),
            supported_worlds=tuple(str(x) for x in data.get("supported_worlds", ())),
            deterministic=bool(data.get("deterministic", True)),
            advisory=bool(data.get("advisory", True)),
            metadata=dict(data.get("metadata", {})),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "ContinuationAction":
        return cls.from_dict(json.loads(text))


@dataclass
class ContinuationActionInput:
    input_id: str
    domain_claims: list[DomainClaim] = field(default_factory=list)
    episode_inputs: list[VerificationEpisodeInput] = field(default_factory=list)
    projection_candidates: list[ProjectionCandidate] = field(default_factory=list)
    constructor_plans: list[ConstructorPlan] = field(default_factory=list)
    proof_artifacts: list[ProofArtifact] = field(default_factory=list)
    raw_texts: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    advisory: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "input_id": self.input_id,
            "domain_claims": [claim.to_dict() for claim in self.domain_claims],
            "episode_inputs": [item.to_dict() for item in self.episode_inputs],
            "projection_candidates": [item.to_dict() for item in self.projection_candidates],
            "constructor_plans": [item.to_dict() for item in self.constructor_plans],
            "proof_artifacts": [item.to_dict() for item in self.proof_artifacts],
            "raw_texts": list(self.raw_texts),
            "metadata": dict(self.metadata),
            "advisory": self.advisory,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ContinuationActionInput":
        return cls(
            input_id=str(data["input_id"]),
            domain_claims=[DomainClaim.from_dict(item) for item in data.get("domain_claims", [])],
            episode_inputs=[VerificationEpisodeInput.from_dict(item) for item in data.get("episode_inputs", [])],
            projection_candidates=[ProjectionCandidate.from_dict(item) for item in data.get("projection_candidates", [])],
            constructor_plans=[ConstructorPlan.from_dict(item) for item in data.get("constructor_plans", [])],
            proof_artifacts=[ProofArtifact.from_dict(item) for item in data.get("proof_artifacts", [])],
            raw_texts=[str(x) for x in data.get("raw_texts", [])],
            metadata=dict(data.get("metadata", {})),
            advisory=bool(data.get("advisory", True)),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "ContinuationActionInput":
        return cls.from_dict(json.loads(text))


@dataclass
class ContinuationActionOutput:
    output_id: str
    action_id: str
    kind: ContinuationOutputKind
    status: ContinuationActionStatus
    domain_claim: DomainClaim | None = None
    episode_input: VerificationEpisodeInput | None = None
    proof_artifact: ProofArtifact | None = None
    projection_candidate: ProjectionCandidate | None = None
    constructor_plan: ConstructorPlan | None = None
    obstruction_name: str | None = None
    task_payload: dict[str, Any] = field(default_factory=dict)
    note: str | None = None
    score: float = 0.0
    terminal_form: TerminalForm | None = None
    certificate_id: str | None = None
    verifier_boundary_crossed: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    advisory: bool = True

    def is_terminal(self) -> bool:
        return self.terminal_form is not None and bool(self.certificate_id) and self.verifier_boundary_crossed

    def to_dict(self) -> dict[str, Any]:
        return {
            "output_id": self.output_id,
            "action_id": self.action_id,
            "kind": self.kind.value,
            "status": self.status.value,
            "domain_claim": self.domain_claim.to_dict() if self.domain_claim else None,
            "episode_input": self.episode_input.to_dict() if self.episode_input else None,
            "proof_artifact": self.proof_artifact.to_dict() if self.proof_artifact else None,
            "projection_candidate": self.projection_candidate.to_dict() if self.projection_candidate else None,
            "constructor_plan": self.constructor_plan.to_dict() if self.constructor_plan else None,
            "obstruction_name": self.obstruction_name,
            "task_payload": dict(self.task_payload),
            "note": self.note,
            "score": self.score,
            "terminal_form": self.terminal_form.value if self.terminal_form else None,
            "certificate_id": self.certificate_id,
            "verifier_boundary_crossed": self.verifier_boundary_crossed,
            "metadata": dict(self.metadata),
            "advisory": self.advisory,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ContinuationActionOutput":
        return cls(
            output_id=str(data["output_id"]),
            action_id=str(data["action_id"]),
            kind=ContinuationOutputKind(str(data.get("kind", ContinuationOutputKind.UNKNOWN.value))),
            status=ContinuationActionStatus(str(data.get("status", ContinuationActionStatus.ADVISORY_ONLY.value))),
            domain_claim=DomainClaim.from_dict(data["domain_claim"]) if data.get("domain_claim") else None,
            episode_input=VerificationEpisodeInput.from_dict(data["episode_input"]) if data.get("episode_input") else None,
            proof_artifact=ProofArtifact.from_dict(data["proof_artifact"]) if data.get("proof_artifact") else None,
            projection_candidate=ProjectionCandidate.from_dict(data["projection_candidate"]) if data.get("projection_candidate") else None,
            constructor_plan=ConstructorPlan.from_dict(data["constructor_plan"]) if data.get("constructor_plan") else None,
            obstruction_name=_optional_str(data.get("obstruction_name")),
            task_payload=dict(data.get("task_payload", {})),
            note=_optional_str(data.get("note")),
            score=float(data.get("score", 0.0) or 0.0),
            terminal_form=_terminal(data.get("terminal_form")),
            certificate_id=_optional_str(data.get("certificate_id")),
            verifier_boundary_crossed=bool(data.get("verifier_boundary_crossed", False)),
            metadata=dict(data.get("metadata", {})),
            advisory=bool(data.get("advisory", True)),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "ContinuationActionOutput":
        return cls.from_dict(json.loads(text))

    def to_jsonl_line(self) -> str:
        return self.to_json() + "\n"

    @classmethod
    def from_jsonl_line(cls, line: str) -> "ContinuationActionOutput":
        return cls.from_json(line.strip())


@dataclass
class ContinuationActionTrace:
    trace_id: str
    input: ContinuationActionInput
    actions: list[ContinuationAction]
    outputs: list[ContinuationActionOutput]
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    summary: dict[str, Any] = field(default_factory=dict)
    advisory: bool = True

    def output_count(self) -> int:
        return len(self.outputs)

    def task_count(self) -> int:
        return sum(1 for output in self.outputs if output.kind == ContinuationOutputKind.TASK)

    def candidate_count(self) -> int:
        return sum(1 for output in self.outputs if output.kind != ContinuationOutputKind.TASK)

    def terminal_count(self) -> int:
        return sum(1 for output in self.outputs if output.is_terminal())

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "input": self.input.to_dict(),
            "actions": [action.to_dict() for action in self.actions],
            "outputs": [output.to_dict() for output in self.outputs],
            "created_at": self.created_at,
            "summary": dict(self.summary),
            "advisory": self.advisory,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ContinuationActionTrace":
        return cls(
            trace_id=str(data["trace_id"]),
            input=ContinuationActionInput.from_dict(data["input"]),
            actions=[ContinuationAction.from_dict(item) for item in data.get("actions", [])],
            outputs=[ContinuationActionOutput.from_dict(item) for item in data.get("outputs", [])],
            created_at=str(data.get("created_at") or datetime.now(timezone.utc).isoformat()),
            summary=dict(data.get("summary", {})),
            advisory=bool(data.get("advisory", True)),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "ContinuationActionTrace":
        return cls.from_dict(json.loads(text))

    def write_json(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.to_dict(), sort_keys=True, indent=2) + "\n", encoding="utf-8")

    @classmethod
    def read_json(cls, path: str | Path) -> "ContinuationActionTrace":
        return cls.from_json(Path(path).read_text(encoding="utf-8"))

    def write_jsonl(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("".join(output.to_jsonl_line() for output in self.outputs), encoding="utf-8")

    @classmethod
    def read_jsonl(cls, path: str | Path) -> list[ContinuationActionOutput]:
        if not Path(path).exists():
            return []
        return [ContinuationActionOutput.from_jsonl_line(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


@dataclass
class ContinuationActionRegistry:
    registry_id: str
    actions: dict[str, ContinuationAction] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)
    advisory: bool = True

    def register(self, action: ContinuationAction) -> None:
        self.actions[action.action_id] = action
        self.registry_id = make_continuation_registry_id([item.to_dict() for item in self.actions.values()])

    def get(self, action_id: str) -> ContinuationAction | None:
        return self.actions.get(action_id)

    def by_kind(self, kind: ContinuationActionKind | str) -> list[ContinuationAction]:
        wanted = ContinuationActionKind(str(kind.value if hasattr(kind, "value") else kind))
        return [action for action in self.actions.values() if action.kind == wanted]

    def all(self) -> list[ContinuationAction]:
        return [self.actions[key] for key in sorted(self.actions)]

    def to_dict(self) -> dict[str, Any]:
        return {
            "registry_id": self.registry_id,
            "actions": {key: action.to_dict() for key, action in sorted(self.actions.items())},
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
            "advisory": self.advisory,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ContinuationActionRegistry":
        return cls(
            registry_id=str(data["registry_id"]),
            actions={str(key): ContinuationAction.from_dict(value) for key, value in dict(data.get("actions", {})).items()},
            created_at=str(data.get("created_at") or datetime.now(timezone.utc).isoformat()),
            metadata=dict(data.get("metadata", {})),
            advisory=bool(data.get("advisory", True)),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "ContinuationActionRegistry":
        return cls.from_dict(json.loads(text))


def default_continuation_action_registry() -> ContinuationActionRegistry:
    kinds = [
        ContinuationActionKind.SPECIALIZE,
        ContinuationActionKind.GENERALIZE,
        ContinuationActionKind.DUALIZE,
        ContinuationActionKind.IDENTIFY_VARIABLES,
        ContinuationActionKind.DROP_VARIABLE,
        ContinuationActionKind.PERMUTE_ROLES,
        ContinuationActionKind.FORM_IMPLICATION,
        ContinuationActionKind.FORM_EQUIVALENCE,
        ContinuationActionKind.EMIT_PROOF_TASK,
        ContinuationActionKind.EMIT_COUNTERMODEL_TASK,
        ContinuationActionKind.EMIT_PROJECTION_TASK,
        ContinuationActionKind.EMIT_OBSTRUCTION_TASK,
        ContinuationActionKind.ABSTRACT_TRACE,
        ContinuationActionKind.PROJECT_LAWBOOK_ENTRY,
    ]
    actions = [_make_action(kind) for kind in kinds]
    return ContinuationActionRegistry(
        registry_id=make_continuation_registry_id([action.to_dict() for action in actions]),
        actions={action.action_id: action for action in actions},
        metadata={"advisory_only": True, "actions_are_not_truth": True},
    )


def dualize_magma_expression(expr: str) -> str:
    text = str(expr)
    pattern = re.compile(r"\(([^()]+)\*([^()]+)\)")
    changed = True
    while changed:
        text, count = pattern.subn(lambda m: f"({m.group(2).strip()}*{m.group(1).strip()})", text)
        changed = count > 0
    return text


def identify_variables_in_expr(expr: str, mapping: Mapping[str, str]) -> str:
    result = str(expr)
    for source, target in sorted(mapping.items(), key=lambda item: (-len(item[0]), item[0])):
        result = re.sub(rf"\b{re.escape(str(source))}\b", str(target), result)
    return result


def drop_variable_from_expr(expr: str, variable: str) -> str:
    if not re.search(rf"\b{re.escape(variable)}\b", expr):
        return expr
    return expr


def form_implication_claim(source: str, target: str) -> DomainClaim:
    return parse_domain_claim(f"{source} => {target}").domain_claim


def form_equivalence_claim(a: str, b: str) -> list[DomainClaim]:
    return [form_implication_claim(a, b), form_implication_claim(b, a)]


def negate_target_task(source: str, target: str) -> dict[str, Any]:
    return {
        "task_kind": "countermodel_search",
        "source": source,
        "target": target,
        "advisory_only": True,
        "note": "Countermodel task payload, not logical truth.",
    }


def apply_continuation_action(action: ContinuationAction, action_input: ContinuationActionInput) -> list[ContinuationActionOutput]:
    outputs: list[ContinuationActionOutput] = []
    claims = list(action_input.domain_claims)
    claims.extend(parse_domain_claim(text).domain_claim for text in action_input.raw_texts)
    if action.kind == ContinuationActionKind.DUALIZE:
        for claim in _magma_claims(claims):
            source = dualize_magma_expression(claim.source or "")
            target = dualize_magma_expression(claim.target or "")
            outputs.append(_domain_output(action, form_implication_claim(source, target), {"dualized": True}))
    elif action.kind == ContinuationActionKind.IDENTIFY_VARIABLES:
        mapping = dict(action_input.metadata.get("variable_map", {"y": "x"}))
        for claim in _magma_claims(claims):
            source = identify_variables_in_expr(claim.source or "", mapping)
            target = identify_variables_in_expr(claim.target or "", mapping)
            if source != claim.source or target != claim.target:
                outputs.append(_domain_output(action, form_implication_claim(source, target), {"variable_map": mapping}))
    elif action.kind == ContinuationActionKind.FORM_IMPLICATION:
        texts = list(action_input.raw_texts)
        if len(texts) >= 2:
            outputs.append(_domain_output(action, form_implication_claim(texts[0], texts[1]), {}))
    elif action.kind == ContinuationActionKind.FORM_EQUIVALENCE:
        texts = list(action_input.raw_texts)
        if len(texts) >= 2:
            outputs.extend(_domain_output(action, claim, {"equivalence_candidate": True}) for claim in form_equivalence_claim(texts[0], texts[1]))
    elif action.kind == ContinuationActionKind.EMIT_PROOF_TASK:
        for claim in claims:
            if claim.world == FormalWorldKind.LEAN:
                artifact = make_lean_skeleton(claim_id=claim.claim_id, source=claim.raw, target=claim.conclusion, theorem_name=_theorem_name(claim.raw))
            else:
                artifact = make_theorem_schema(claim_id=claim.claim_id, source=claim.source or claim.raw, target=claim.target or claim.conclusion, metadata={"advisory_only": True})
            outputs.append(_proof_output(action, artifact))
    elif action.kind == ContinuationActionKind.EMIT_COUNTERMODEL_TASK:
        for claim in _magma_claims(claims):
            payload = negate_target_task(claim.source or "", claim.target or "")
            episode = domain_claim_to_verification_episode_input(claim)
            outputs.append(_episode_task_output(action, payload, episode))
    elif action.kind == ContinuationActionKind.EMIT_PROJECTION_TASK:
        for claim in _magma_claims(claims):
            candidate = ProjectionCandidate(
                candidate_id=make_projection_candidate_id({"claim": claim.to_dict(), "action": action.action_id}),
                source_claim_id=claim.claim_id,
                target_claim_id=None,
                source=claim.source,
                target=claim.target,
                rule_kind=ProjectionRuleKind.ADVISORY_SIMILARITY,
                confidence=0.1,
                advisory=True,
                reason="Continuation action emitted advisory projection task.",
                metadata={"advisory_only": True, "action_id": action.action_id},
            )
            outputs.append(_projection_output(action, candidate))
    elif action.kind == ContinuationActionKind.EMIT_OBSTRUCTION_TASK:
        for claim in claims:
            name = f"candidate_obstruction_{claim.claim_id}"
            outputs.append(_obstruction_output(action, name, f"Candidate obstruction for {claim.claim_id}; not named truth."))
    elif action.kind in {ContinuationActionKind.SPECIALIZE, ContinuationActionKind.GENERALIZE, ContinuationActionKind.DROP_VARIABLE, ContinuationActionKind.PERMUTE_ROLES, ContinuationActionKind.COMPOSE_CLAIMS, ContinuationActionKind.NEGATE_TARGET, ContinuationActionKind.ABSTRACT_TRACE, ContinuationActionKind.PROJECT_LAWBOOK_ENTRY}:
        outputs.append(_note_output(action, f"{action.kind.value} is registered; no safe deterministic output for this input."))
    if not outputs:
        outputs.append(_residual_output(action, "Action not applicable to current input."))
    return outputs


def run_continuation_actions(
    *,
    action_input: ContinuationActionInput,
    registry: ContinuationActionRegistry | None = None,
    action_kinds: Sequence[ContinuationActionKind | str] = (),
    max_outputs: int | None = None,
) -> ContinuationActionTrace:
    registry = registry or default_continuation_action_registry()
    selected = []
    if action_kinds:
        wanted = {ContinuationActionKind(str(kind.value if hasattr(kind, "value") else kind)) for kind in action_kinds}
        selected = [action for action in registry.all() if action.kind in wanted]
    else:
        selected = registry.all()
    outputs: list[ContinuationActionOutput] = []
    for action in selected:
        outputs.extend(apply_continuation_action(action, action_input))
        if max_outputs is not None and len(outputs) >= max_outputs:
            outputs = outputs[:max_outputs]
            break
    trace = ContinuationActionTrace(
        trace_id=make_continuation_trace_id(action_input.to_dict(), [action.to_dict() for action in selected], [output.to_dict() for output in outputs]),
        input=action_input,
        actions=selected,
        outputs=outputs,
    )
    trace.summary.update(_summary(trace))
    return trace


def continuation_trace_to_alchemical_trace(trace: ContinuationActionTrace) -> AlchemicalTrace:
    alchemical = AlchemicalTrace(trace_id=make_alchemical_trace_id("continuation_actions", trace.trace_id), claim_id=None, agent_id=None, episode_id=None)
    alchemical.add_step(phase=AlchemicalPhase.RAW_MATTER, status=AlchemicalStatus.SUCCEEDED)
    if trace.input.domain_claims or trace.input.raw_texts:
        alchemical.add_step(phase=AlchemicalPhase.CALCINATION, status=AlchemicalStatus.SUCCEEDED)
    if any(action.kind in {ContinuationActionKind.GENERALIZE, ContinuationActionKind.ABSTRACT_TRACE} for action in trace.actions):
        alchemical.add_step(phase=AlchemicalPhase.SUBLIMATION, status=AlchemicalStatus.ADVISORY_ONLY)
    if trace.task_count() or any(output.kind in {ContinuationOutputKind.PROOF_ARTIFACT, ContinuationOutputKind.PROJECTION_CANDIDATE, ContinuationOutputKind.EPISODE_INPUT} for output in trace.outputs):
        alchemical.add_step(phase=AlchemicalPhase.DESCENSION, status=AlchemicalStatus.ADVISORY_ONLY)
    if trace.outputs:
        alchemical.add_step(phase=AlchemicalPhase.COAGULATION, status=AlchemicalStatus.ADVISORY_ONLY)
    promoted = [output for output in trace.outputs if output.is_terminal()]
    if promoted:
        first = promoted[0]
        alchemical.terminal_form = first.terminal_form
        alchemical.promoted_certificate_id = first.certificate_id
        alchemical.add_step(phase=AlchemicalPhase.FIXATION, status=AlchemicalStatus.PROMOTED_BY_VERIFIER)
    return alchemical


def continuation_trace_to_agent_experiences(trace: ContinuationActionTrace, agent_id: str | None = None) -> list[AgentExperience]:
    actor = agent_id or "continuation-actions"
    return [
        AgentExperience(
            experience_id=content_id("continuation_action_exp", output.to_dict(), n=24),
            agent_id=actor,
            episode_id=None,
            claim_id=output.domain_claim.claim_id if output.domain_claim else output.output_id,
            route=f"continuation:{output.kind.value.lower()}",
            phase=AlchemicalPhase.COAGULATION.value,
            outcome=AgentExperienceOutcome.ADVISORY_ONLY if not output.is_terminal() else AgentExperienceOutcome.VERIFIED_PROOF,
            terminal_form=output.terminal_form if output.is_terminal() else None,
            certificate_id=output.certificate_id if output.is_terminal() else None,
            verifier_boundary_crossed=output.is_terminal(),
            metadata={"continuation_output": output.to_dict(), "boundary_preserved": not output.is_terminal()},
        )
        for output in trace.outputs
    ]


def continuation_outputs_to_episode_inputs(trace: ContinuationActionTrace) -> list[VerificationEpisodeInput]:
    rows = [output.episode_input for output in trace.outputs if output.episode_input is not None]
    rows.extend(domain_claim_to_verification_episode_input(output.domain_claim) for output in trace.outputs if output.domain_claim is not None)
    return rows


def continuation_outputs_to_projection_candidates(trace: ContinuationActionTrace) -> list[ProjectionCandidate]:
    return [output.projection_candidate for output in trace.outputs if output.projection_candidate is not None]


def continuation_outputs_to_proof_artifacts(trace: ContinuationActionTrace) -> list[ProofArtifact]:
    return [output.proof_artifact for output in trace.outputs if output.proof_artifact is not None]


def make_continuation_input_id(payload: Any) -> str:
    return content_id("continuation_action_input", payload, n=24)


def make_continuation_action_id(kind: ContinuationActionKind | str, name: str) -> str:
    return content_id("continuation_action", {"kind": str(kind.value if hasattr(kind, "value") else kind), "name": name}, n=24)


def make_continuation_output_id(payload: Any) -> str:
    return content_id("continuation_action_output", payload, n=24)


def make_continuation_registry_id(payload: Any) -> str:
    return content_id("continuation_action_registry", payload, n=24)


def make_continuation_trace_id(*parts: Any) -> str:
    return content_id("continuation_action_trace", parts, n=24)


def _make_action(kind: ContinuationActionKind) -> ContinuationAction:
    name = kind.value.lower()
    output_map = {
        ContinuationActionKind.EMIT_PROOF_TASK: (ContinuationOutputKind.PROOF_ARTIFACT, ContinuationOutputKind.TASK),
        ContinuationActionKind.EMIT_COUNTERMODEL_TASK: (ContinuationOutputKind.EPISODE_INPUT, ContinuationOutputKind.TASK),
        ContinuationActionKind.EMIT_PROJECTION_TASK: (ContinuationOutputKind.PROJECTION_CANDIDATE,),
        ContinuationActionKind.EMIT_OBSTRUCTION_TASK: (ContinuationOutputKind.OBSTRUCTION_CANDIDATE,),
    }
    return ContinuationAction(
        action_id=make_continuation_action_id(kind, name),
        kind=kind,
        name=name,
        description=f"Advisory continuation action {kind.value}.",
        input_kinds=("DomainClaim", "raw_text"),
        output_kinds=output_map.get(kind, (ContinuationOutputKind.DOMAIN_CLAIM, ContinuationOutputKind.NOTE)),
        supported_worlds=(FormalWorldKind.MAGMA_EQUATIONAL.value, FormalWorldKind.LEAN.value),
        metadata={"advisory_only": True, "action_is_not_truth": True},
    )


def _magma_claims(claims: Sequence[DomainClaim]) -> list[DomainClaim]:
    return [claim for claim in claims if claim.world == FormalWorldKind.MAGMA_EQUATIONAL and claim.source and claim.target]


def _domain_output(action: ContinuationAction, claim: DomainClaim, metadata: Mapping[str, Any]) -> ContinuationActionOutput:
    return ContinuationActionOutput(
        output_id=make_continuation_output_id({"action": action.action_id, "claim": claim.to_dict(), "metadata": dict(metadata)}),
        action_id=action.action_id,
        kind=ContinuationOutputKind.DOMAIN_CLAIM,
        status=ContinuationActionStatus.PRODUCED_CANDIDATE,
        domain_claim=claim,
        metadata={**dict(metadata), "advisory_only": True},
    )


def _proof_output(action: ContinuationAction, artifact: ProofArtifact) -> ContinuationActionOutput:
    return ContinuationActionOutput(
        output_id=make_continuation_output_id({"action": action.action_id, "artifact": artifact.to_dict()}),
        action_id=action.action_id,
        kind=ContinuationOutputKind.PROOF_ARTIFACT,
        status=ContinuationActionStatus.PRODUCED_TASK,
        proof_artifact=artifact,
        task_payload={"task_kind": "proof_task", "artifact_id": artifact.artifact_id, "advisory_only": True},
        metadata={"advisory_only": True, "generated_proof_task_not_truth": True},
    )


def _episode_task_output(action: ContinuationAction, payload: Mapping[str, Any], episode: VerificationEpisodeInput) -> ContinuationActionOutput:
    return ContinuationActionOutput(
        output_id=make_continuation_output_id({"action": action.action_id, "payload": dict(payload), "episode": episode.to_dict()}),
        action_id=action.action_id,
        kind=ContinuationOutputKind.EPISODE_INPUT,
        status=ContinuationActionStatus.PRODUCED_TASK,
        episode_input=episode,
        task_payload=dict(payload),
        metadata={"advisory_only": True, "countermodel_task_not_countermodel": True},
    )


def _projection_output(action: ContinuationAction, candidate: ProjectionCandidate) -> ContinuationActionOutput:
    return ContinuationActionOutput(
        output_id=make_continuation_output_id({"action": action.action_id, "projection": candidate.to_dict()}),
        action_id=action.action_id,
        kind=ContinuationOutputKind.PROJECTION_CANDIDATE,
        status=ContinuationActionStatus.PRODUCED_TASK,
        projection_candidate=candidate,
        metadata={"advisory_only": True, "projection_task_not_truth": True},
    )


def _obstruction_output(action: ContinuationAction, name: str, note: str) -> ContinuationActionOutput:
    return ContinuationActionOutput(
        output_id=make_continuation_output_id({"action": action.action_id, "obstruction": name}),
        action_id=action.action_id,
        kind=ContinuationOutputKind.OBSTRUCTION_CANDIDATE,
        status=ContinuationActionStatus.PRODUCED_CANDIDATE,
        obstruction_name=name,
        note=note,
        metadata={"advisory_only": True, "obstruction_candidate_not_named_obstruction": True},
    )


def _note_output(action: ContinuationAction, note: str) -> ContinuationActionOutput:
    return ContinuationActionOutput(
        output_id=make_continuation_output_id({"action": action.action_id, "note": note}),
        action_id=action.action_id,
        kind=ContinuationOutputKind.NOTE,
        status=ContinuationActionStatus.ADVISORY_ONLY,
        note=note,
        metadata={"advisory_only": True},
    )


def _residual_output(action: ContinuationAction, note: str) -> ContinuationActionOutput:
    return ContinuationActionOutput(
        output_id=make_continuation_output_id({"action": action.action_id, "residual": note}),
        action_id=action.action_id,
        kind=ContinuationOutputKind.NOTE,
        status=ContinuationActionStatus.RESIDUAL,
        note=note,
        metadata={"advisory_only": True, "residual": True},
    )


def _summary(trace: ContinuationActionTrace) -> dict[str, Any]:
    return {
        "actions_total": len(trace.actions),
        "outputs_total": len(trace.outputs),
        "domain_claim_outputs": sum(1 for output in trace.outputs if output.kind == ContinuationOutputKind.DOMAIN_CLAIM),
        "episode_input_outputs": sum(1 for output in trace.outputs if output.kind == ContinuationOutputKind.EPISODE_INPUT),
        "proof_artifact_outputs": sum(1 for output in trace.outputs if output.kind == ContinuationOutputKind.PROOF_ARTIFACT),
        "projection_candidate_outputs": sum(1 for output in trace.outputs if output.kind == ContinuationOutputKind.PROJECTION_CANDIDATE),
        "constructor_plan_outputs": sum(1 for output in trace.outputs if output.kind == ContinuationOutputKind.CONSTRUCTOR_PLAN),
        "obstruction_candidate_outputs": sum(1 for output in trace.outputs if output.kind == ContinuationOutputKind.OBSTRUCTION_CANDIDATE),
        "task_outputs": trace.task_count(),
        "terminal_outputs": trace.terminal_count(),
        "advisory_outputs": sum(1 for output in trace.outputs if not output.is_terminal()),
        "advisory_only": trace.terminal_count() == 0,
    }


def _theorem_name(raw: str) -> str | None:
    match = re.match(r"\s*(?:theorem|lemma|example)\s+([A-Za-z_][A-Za-z0-9_']*)", raw)
    return match.group(1) if match else None


def _optional_str(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value)


def _terminal(value: Any) -> TerminalForm | None:
    if value in (None, ""):
        return None
    return TerminalForm(str(value))
