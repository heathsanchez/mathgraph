"""Core MathGraph kernel."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from mathgraph.certificates import (
    Certificate,
    TerminalForm,
    VerificationStatus,
    finite_countermodel,
    named_obstruction,
    verified_proof,
)
from mathgraph.equations import (
    Equation,
    equations_alpha_equivalent,
    equations_swapped,
    equations_swapped_alpha_equivalent,
    parse_equation,
)
from mathgraph.graph_store import InMemoryGraphStore
from mathgraph.trace import Trace
from mathgraph.verification import verify_certificate


class Kernel:
    """Minimal kernel enforcing terminal-form certificates."""

    def __init__(
        self,
        store: InMemoryGraphStore | None = None,
        finite_magmas: Iterable[object] | None = None,
        ledger: object | None = None,
        corpus: object | None = None,
    ) -> None:
        self.store = store or InMemoryGraphStore()
        self.certificates: list[Certificate] = []
        self.finite_magmas = list(finite_magmas) if finite_magmas is not None else _default_magmas()
        self.ledger = ledger
        self.corpus = corpus

    def add_equation(self, name: str, equation: Equation | str) -> Equation:
        parsed = parse_equation(equation) if isinstance(equation, str) else equation
        self.store.add_node(name, "equation", equation=str(parsed), variables=sorted(parsed.variables()))
        return parsed

    def accept_certificate(self, certificate: Certificate) -> Certificate:
        verified = verify_certificate(certificate)
        self.certificates.append(verified)
        node_id = f"certificate:{len(self.certificates)}"
        self.store.add_node(
            node_id,
            "certificate",
            terminal_form=verified.terminal_form.value,
            claim=verified.claim,
            payload=verified.payload,
        )
        return verified

    def record_verified_proof(self, claim: str, proof_id: str) -> Certificate:
        return self.accept_certificate(verified_proof(claim, proof_id))

    def record_named_obstruction(self, claim: str, name: str, detail: str = "") -> Certificate:
        return self.accept_certificate(named_obstruction(claim, name, detail))

    def prove(
        self,
        source: Equation | str,
        target: Equation | str | None = None,
        *,
        lean_code: str | None = None,
        lean_file: str | None = None,
        source_idx: str | int | None = None,
        target_idx: str | int | None = None,
        claim_hash: str | None = None,
    ) -> Trace:
        """Try the deliberately small v0.1 route set for a claim.

        This method checks only exact/symmetric/renaming structural routes and
        finite magma countermodels over registered small tables. Failure to find
        either is recorded as an obstruction, not as proof.
        """

        if lean_code is not None and lean_file is not None:
            raise ValueError("provide at most one of lean_code or lean_file")

        source_eq = parse_equation(source) if isinstance(source, str) else source
        target_eq = parse_equation(target) if isinstance(target, str) else target
        routes_tried: list[str] = []

        corpus_trace = self.lookup_corpus(
            source=str(source_eq),
            target=str(target_eq) if target_eq is not None else None,
            source_idx=source_idx,
            target_idx=target_idx,
            claim_hash=claim_hash,
        )
        if corpus_trace is not None:
            return self._attach_external_verification(corpus_trace, lean_code, lean_file)

        if target_eq is None:
            claim = str(source_eq)
            routes_tried.append("structural_reflexive")
            if source_eq.lhs == source_eq.rhs:
                cert = self.accept_certificate(verified_proof(claim, "structural_reflexive"))
                trace = self._trace(claim, routes_tried, cert, source=str(source_eq), target=None)
                return self._attach_external_verification(trace, lean_code, lean_file)

            routes_tried.append("finite_magma_countermodel")
            for magma in self.finite_magmas:
                witness = magma.counterexample_to_equation(source_eq)
                if witness is not None:
                    payload = {
                        "name": magma.name,
                        "table": [list(row) for row in magma.table],
                        "carrier_order": magma.size,
                        "target_equation": str(source_eq),
                        "target_violated": True,
                        "assignment": witness["assignment"],
                        "target_lhs": witness["lhs"],
                        "target_rhs": witness["rhs"],
                        "table_invariants": magma.invariants(),
                    }
                    cert = self.accept_certificate(finite_countermodel(claim, payload))
                    trace = self._trace(claim, routes_tried, cert, source=str(source_eq), target=None)
                    return self._attach_external_verification(trace, lean_code, lean_file)

            obstruction = self.accept_certificate(
                named_obstruction(
                    claim,
                    "NO_ROUTE_TERMINATED",
                    "No structural proof or finite countermodel was found. This is not a truth claim.",
                )
            )
            trace = self._trace(claim, routes_tried, obstruction, source=str(source_eq), target=None)
            return self._attach_external_verification(trace, lean_code, lean_file)

        claim = f"{source_eq} => {target_eq}"

        structural_route = self._structural_route(source_eq, target_eq, routes_tried)
        if structural_route is not None:
            cert = self.accept_certificate(verified_proof(claim, structural_route))
            trace = self._trace(claim, routes_tried, cert, source=str(source_eq), target=str(target_eq))
            return self._attach_external_verification(trace, lean_code, lean_file)

        routes_tried.append("finite_magma_countermodel")
        for magma in self.finite_magmas:
            payload = magma.countermodel_certificate_payload(source_eq, target_eq)
            if payload is not None:
                cert = self.accept_certificate(finite_countermodel(claim, payload))
                trace = self._trace(claim, routes_tried, cert, source=str(source_eq), target=str(target_eq))
                return self._attach_external_verification(trace, lean_code, lean_file)

        obstruction = self.accept_certificate(
            named_obstruction(
                claim,
                "NO_ROUTE_TERMINATED",
                "No structural proof or finite countermodel was found. This is not a truth claim.",
            )
        )
        trace = self._trace(claim, routes_tried, obstruction, source=str(source_eq), target=str(target_eq))
        return self._attach_external_verification(trace, lean_code, lean_file)

    def _structural_route(
        self,
        source: Equation,
        target: Equation,
        routes_tried: list[str],
    ) -> str | None:
        routes_tried.append("structural_exact")
        if source == target:
            return "structural_exact"

        routes_tried.append("structural_sides_swapped")
        if equations_swapped(source, target):
            return "structural_sides_swapped"

        routes_tried.append("structural_variable_renaming")
        if equations_alpha_equivalent(source, target) or equations_swapped_alpha_equivalent(
            source, target
        ):
            return "structural_variable_renaming"

        return None

    def lookup_corpus(
        self,
        *,
        source: str,
        target: str | None,
        source_idx: str | int | None = None,
        target_idx: str | int | None = None,
        claim_hash: str | None = None,
    ) -> Trace | None:
        if self.corpus is None:
            return None

        lookups: list[tuple[str, list[Trace]]] = []
        if source_idx is not None and target_idx is not None:
            lookups.append(("pair_indices", list(self.corpus.get_by_pair(source_idx, target_idx))))
        if target is not None:
            lookups.append(("equation_strings", self._lookup_corpus_by_equations(source, target)))
        if claim_hash is not None:
            lookups.append(("claim_hash", list(self.corpus.get_by_claim_hash(claim_hash))))

        for mode, matches in lookups:
            promotable = [trace for trace in matches if self._is_promotable_corpus_trace(trace)]
            if not promotable:
                continue
            if self._has_conflicting_corpus_hits(promotable):
                return self._corpus_conflict_trace(source, target, mode, promotable)
            return self._corpus_replay_trace(promotable[0], mode)

        return None

    def _lookup_corpus_by_equations(self, source: str, target: str) -> list[Trace]:
        matches: list[Trace] = []
        for trace in getattr(self.corpus, "traces", []):
            trace_source = _trace_lookup_value(trace, "source_equation") or trace.source
            trace_target = _trace_lookup_value(trace, "target_equation") or trace.target
            if _equation_text_matches(trace_source, source) and _equation_text_matches(
                trace_target,
                target,
            ):
                matches.append(trace)
        return matches

    def _is_promotable_corpus_trace(self, trace: Trace) -> bool:
        return (
            (
                trace.terminal_form == TerminalForm.VERIFIED_PROOF
                and trace.verification_status == VerificationStatus.VERIFIED
            )
            or (
                trace.terminal_form == TerminalForm.FINITE_COUNTERMODEL
                and trace.verification_status == VerificationStatus.REFUTED
            )
        ) and trace.certificate is not None

    def _has_conflicting_corpus_hits(self, traces: list[Trace]) -> bool:
        signatures = {
            (
                trace.terminal_form.value,
                trace.verification_status.value,
                trace.claim,
                _trace_lookup_value(trace, "claim_hash"),
            )
            for trace in traces
        }
        return len(signatures) > 1

    def _corpus_replay_trace(self, trace: Trace, mode: str) -> Trace:
        replay = Trace.from_dict(trace.to_dict())
        replay.routes_tried = ["certificate_corpus_lookup", *replay.routes_tried]
        replay.metadata = dict(replay.metadata)
        replay.metadata.update(
            {
                "corpus_hit": True,
                "corpus_lookup_mode": mode,
                "corpus_trace_hash": trace.content_hash(),
            }
        )
        return replay

    def _corpus_conflict_trace(
        self,
        source: str,
        target: str | None,
        mode: str,
        matches: list[Trace],
    ) -> Trace:
        claim = f"{source} => {target}" if target is not None else source
        obstruction = named_obstruction(
            claim,
            "CONFLICTING_CORPUS_TRACES",
            "Multiple verified corpus traces matched the requested claim with conflicting payloads.",
        )
        trace = self._trace(
            claim,
            ["certificate_corpus_lookup"],
            obstruction,
            source=source,
            target=target,
        )
        trace.metadata.update(
            {
                "corpus_hit": False,
                "corpus_lookup_mode": mode,
                "corpus_conflict": True,
                "corpus_conflict_count": len(matches),
                "corpus_conflict_hashes": [match.content_hash() for match in matches],
            }
        )
        return trace

    def _trace(
        self,
        claim: str,
        routes_tried: list[str],
        certificate: Certificate,
        source: str | None,
        target: str | None,
    ) -> Trace:
        if certificate.terminal_form == TerminalForm.VERIFIED_PROOF:
            return Trace(
                claim=claim,
                source=source,
                target=target,
                routes_tried=routes_tried,
                terminal_form=certificate.terminal_form,
                verification_status=VerificationStatus.VERIFIED,
                certificate=certificate,
            )
        if certificate.terminal_form == TerminalForm.FINITE_COUNTERMODEL:
            return Trace(
                claim=claim,
                source=source,
                target=target,
                routes_tried=routes_tried,
                terminal_form=certificate.terminal_form,
                verification_status=VerificationStatus.REFUTED,
                certificate=certificate,
            )
        return Trace(
            claim=claim,
            source=source,
            target=target,
            routes_tried=routes_tried,
            terminal_form=certificate.terminal_form,
            verification_status=VerificationStatus.OBSTRUCTED,
            obstruction=certificate,
        )

    def _attach_external_verification(
        self,
        trace: Trace,
        lean_code: str | None,
        lean_file: str | None,
    ) -> Trace:
        if lean_code is None and lean_file is None:
            return self._append_trace(trace)

        from mathgraph.verification import verify_external_artifact

        if lean_code is not None:
            result = verify_external_artifact("lean_code", {"code": lean_code})
        else:
            result = verify_external_artifact("lean_file", {"path": lean_file})
        trace.add_external_verification(result)
        self._append_trace(trace)
        return trace

    def _append_trace(self, trace: Trace) -> Trace:
        if self.ledger is not None:
            self.ledger.append_trace(trace)
        return trace

    def check_finite_magma_implication(
        self,
        premises: Iterable[Equation | str],
        conclusion: Equation | str,
        magma: object,
    ) -> Certificate:
        """Accept a finite countermodel when the adapter finds one."""

        from adapters.finite_magma_adapter import FiniteMagma

        if not isinstance(magma, FiniteMagma):
            raise TypeError("magma must be a FiniteMagma")
        parsed_premises = [parse_equation(p) if isinstance(p, str) else p for p in premises]
        parsed_conclusion = parse_equation(conclusion) if isinstance(conclusion, str) else conclusion
        claim = f"{', '.join(map(str, parsed_premises))} => {parsed_conclusion}"

        witness = magma.counterexample_to_implication(parsed_premises, parsed_conclusion)
        if witness is not None:
            return self.accept_certificate(finite_countermodel(claim, witness))

        return self.accept_certificate(
            named_obstruction(
                claim,
                "NO_COUNTERMODEL_IN_GIVEN_FINITE_MAGMA",
                "The supplied finite magma does not refute this implication.",
            )
        )


def _default_magmas() -> list[object]:
    from adapters.finite_magma_adapter import FiniteMagma

    return [
        FiniteMagma.from_table([[0, 1], [1, 0]], name="xor_magma"),
    ]


def _trace_lookup_value(trace: Trace, key: str) -> str | None:
    value = _nested_lookup(getattr(trace, "metadata", {}) or {}, key)
    if value is not None:
        return str(value)

    certificate = getattr(trace, "certificate", None)
    payload = getattr(certificate, "payload", {}) if certificate is not None else {}
    value = _nested_lookup(payload, key)
    if value is not None:
        return str(value)

    obstruction = getattr(trace, "obstruction", None)
    payload = getattr(obstruction, "payload", {}) if obstruction is not None else {}
    value = _nested_lookup(payload, key)
    return str(value) if value is not None else None


def _nested_lookup(payload: dict[str, Any], key: str) -> Any:
    if key in payload and payload[key] not in (None, ""):
        return payload[key]
    for nested_key in ("model", "record"):
        nested = payload.get(nested_key)
        if isinstance(nested, dict) and key in nested and nested[key] not in (None, ""):
            return nested[key]
    return None


def _equation_text_matches(left: str | None, right: str | None) -> bool:
    if left == right:
        return True
    if left is None or right is None:
        return False
    try:
        return str(parse_equation(left)) == str(parse_equation(right))
    except ValueError:
        return False
