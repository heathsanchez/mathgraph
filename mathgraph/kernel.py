"""Core MathGraph kernel."""

from __future__ import annotations

from collections.abc import Iterable

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
    ) -> None:
        self.store = store or InMemoryGraphStore()
        self.certificates: list[Certificate] = []
        self.finite_magmas = list(finite_magmas) if finite_magmas is not None else _default_magmas()

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

    def prove(self, source: Equation | str, target: Equation | str | None = None) -> Trace:
        """Try the deliberately small v0.1 route set for a claim.

        This method checks only exact/symmetric/renaming structural routes and
        finite magma countermodels over registered small tables. Failure to find
        either is recorded as an obstruction, not as proof.
        """

        source_eq = parse_equation(source) if isinstance(source, str) else source
        target_eq = parse_equation(target) if isinstance(target, str) else target
        routes_tried: list[str] = []

        if target_eq is None:
            claim = str(source_eq)
            routes_tried.append("structural_reflexive")
            if source_eq.lhs == source_eq.rhs:
                cert = self.accept_certificate(verified_proof(claim, "structural_reflexive"))
                return self._trace(claim, routes_tried, cert)

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
                    return self._trace(claim, routes_tried, cert)

            obstruction = self.accept_certificate(
                named_obstruction(
                    claim,
                    "NO_ROUTE_TERMINATED",
                    "No structural proof or finite countermodel was found. This is not a truth claim.",
                )
            )
            return self._trace(claim, routes_tried, obstruction)

        claim = f"{source_eq} => {target_eq}"

        structural_route = self._structural_route(source_eq, target_eq, routes_tried)
        if structural_route is not None:
            cert = self.accept_certificate(verified_proof(claim, structural_route))
            return self._trace(claim, routes_tried, cert)

        routes_tried.append("finite_magma_countermodel")
        for magma in self.finite_magmas:
            payload = magma.countermodel_certificate_payload(source_eq, target_eq)
            if payload is not None:
                cert = self.accept_certificate(finite_countermodel(claim, payload))
                return self._trace(claim, routes_tried, cert)

        obstruction = self.accept_certificate(
            named_obstruction(
                claim,
                "NO_ROUTE_TERMINATED",
                "No structural proof or finite countermodel was found. This is not a truth claim.",
            )
        )
        return self._trace(claim, routes_tried, obstruction)

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

    def _trace(
        self,
        claim: str,
        routes_tried: list[str],
        certificate: Certificate,
    ) -> Trace:
        if certificate.terminal_form == TerminalForm.VERIFIED_PROOF:
            return Trace(
                claim=claim,
                routes_tried=routes_tried,
                terminal_form=certificate.terminal_form,
                verification_status=VerificationStatus.VERIFIED,
                certificate=certificate,
            )
        if certificate.terminal_form == TerminalForm.FINITE_COUNTERMODEL:
            return Trace(
                claim=claim,
                routes_tried=routes_tried,
                terminal_form=certificate.terminal_form,
                verification_status=VerificationStatus.REFUTED,
                certificate=certificate,
            )
        return Trace(
            claim=claim,
            routes_tried=routes_tried,
            terminal_form=certificate.terminal_form,
            verification_status=VerificationStatus.OBSTRUCTED,
            obstruction=certificate,
        )

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
