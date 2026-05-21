#!/usr/bin/env python
"""Exercise the next implementable MathGraph layer end to end."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path(__file__)

from mathgraph.causal_ir import CausalClaim, CausalClaimKind, CausalEdge, CausalVariable, Intervention  # noqa: E402
from mathgraph.closed_loop import ClosedVerificationLoop  # noqa: E402
from mathgraph.external_certificates import ExternalCertificate, ExternalCertificateStatus, ExternalVerifierKind  # noqa: E402
from mathgraph.grounding import GroundingFunctionSpec, GroundingRecord, SensorSignature  # noqa: E402
from mathgraph.route_priors import recommend_route_with_prior  # noqa: E402
from mathgraph.terminal_schema import terminal_form_from_legacy  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default="/tmp/mathgraph_next_layer_smoke")
    args = parser.parse_args()

    cert = ExternalCertificate(
        cert_id="cert_smoke",
        verifier=ExternalVerifierKind.LEAN4,
        status=ExternalCertificateStatus.ACCEPTED,
        claim="theorem smoke : True",
        claim_hash="hash_smoke",
    )
    loop = ClosedVerificationLoop()
    loop.submit_many([("x = x", "y = y"), ("x * y = y * x", "a * b = b * a")])
    loop.schedule(top_k=2)
    outcome = loop.record_outcome(
        "x = x",
        "y = y",
        "VERIFIED_PROOF",
        "direct_substitution_instance",
    )
    prior = recommend_route_with_prior("x = x", "z = z", loop.outcomes)
    causal = CausalClaim(
        claim_id="causal_smoke",
        kind=CausalClaimKind.INTERVENTIONAL,
        variables=[CausalVariable("x"), CausalVariable("y")],
        edges=[CausalEdge("x", "y", is_confounded=True)],
        query="effect(x, y)",
        interventions=[Intervention("x", 1)],
    )
    identifiable, reason = causal.simple_identifiability_check()
    grounding = GroundingRecord(
        grounding_id="ground_smoke",
        symbol="HIGH_SIGNAL",
        sensor=SensorSignature("s1", "scalar", 1, 1.0, (0.0, 1.0)),
        grounding_function=GroundingFunctionSpec("mean_threshold", "Mean threshold", threshold=0.5),
    ).attempt_grounding([0.8, 0.9])
    payload = {
        "terminal_mapping": terminal_form_from_legacy("FINITE_COUNTERMODEL").value,
        "external_certificate": cert.to_candidate_payload(),
        "closed_loop": loop.stats().to_dict(),
        "recorded_outcome": outcome.to_dict(),
        "route_prior": prior,
        "causal_identifiable": identifiable,
        "causal_reason": reason,
        "causal_obstruction": causal.to_named_obstruction(reason),
        "grounding": grounding.to_denotation_payload(),
        "advisory": True,
    }
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    output = out_dir / "next_layer_smoke.json"
    output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"output": str(output), "advisory": True}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
