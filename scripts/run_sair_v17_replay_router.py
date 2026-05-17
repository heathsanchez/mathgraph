#!/usr/bin/env python3
"""
Run the SAIR v17 replay router.

This CLI is intentionally safe by default:
- Running it with no arguments prints the next-route policy and exits 0.
- It does not require Drive artifacts to be present.
- It never promotes empirical constructor schemas to terminal truth.
- Terminal truth still requires VERIFIED_PROOF, FINITE_COUNTERMODEL, or NAMED_OBSTRUCTION policy.
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from _bootstrap import ensure_repo_root_on_path
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
else:
    ensure_repo_root_on_path(__file__)

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional


def _json_default(obj: Any) -> Any:
    if isinstance(obj, Path):
        return str(obj)
    return str(obj)


def _load_json(path: Optional[str]) -> Any:
    if not path:
        return None
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(p))
    return json.loads(p.read_text(encoding="utf-8"))


def _default_routes() -> Dict[str, Any]:
    try:
        from mathgraph.sair_v17_replay_router import next_routes
        routes = next_routes()
    except Exception:
        routes = [
            {
                "router_rank": 1,
                "next_route": "apply_packaged_constructors_to_small_residual_slice",
                "route_type": "stage2_certificate_growth",
                "constructor_family": "LAWBOOK_FIRST_RESIDUAL_ATTACK",
                "recommended_engine": "sair_v17_replay_router",
                "expected_terminal_form": "VERIFIED_PROOF_OR_FINITE_COUNTERMODEL_OR_NAMED_OBSTRUCTION",
                "policy": "Use packaged constructor memory first; do not return to broad BFS.",
                "router_score": 10.0,
            },
            {
                "router_rank": 2,
                "next_route": "wire_fixed_header_into_all_existing_lean_emitters",
                "route_type": "repo_integration",
                "constructor_family": "FIXED_HEADER_EXACT_REPLAY",
                "recommended_engine": "make_universe_u_header_mandatory",
                "expected_terminal_form": "LOWER_FALSE_FAILURE_RATE",
                "policy": "Every Lean emitter using type-universe declarations should emit `universe u` before the type universe is referenced.",
                "router_score": 9.5,
            },
            {
                "router_rank": 3,
                "next_route": "promote_fast_one_bridge_constructor_from_advisory_to_callable",
                "route_type": "constructor_integration",
                "constructor_family": "FAST_WITNESS_COMPLETED_ONE_BRIDGE",
                "recommended_engine": "no_bfs_one_bridge_before_closure",
                "expected_terminal_form": "VERIFIED_PROOF_OR_NAMED_OBSTRUCTION",
                "policy": "Use fast witness-completed one-bridge replay before bounded closure/BFS.",
                "router_score": 9.0,
            },
            {
                "router_rank": 4,
                "next_route": "promote_explicit_subposition_congrarg_repair_to_callable",
                "route_type": "constructor_integration",
                "constructor_family": "EXPLICIT_SUBPOSITION_CONGRARG_BRIDGE_REPAIR",
                "recommended_engine": "explicit_congrarg_two_step_symm_s2",
                "expected_terminal_form": "VERIFIED_PROOF_OR_NAMED_OBSTRUCTION",
                "policy": "Use explicit subposition congrArg/calc repair for bridge rw failures before broadening.",
                "router_score": 8.5,
            },
        ]

    return {
        "ok": True,
        "mode": "default_routes",
        "routes": routes,
        "authority_boundary": {
            "safety_rule": "Only actual Lean-verified generated proof files mapped to official TRUE pairs are terminal TRUE.",
            "terminal_form_contract": [
                "VERIFIED_PROOF",
                "FINITE_COUNTERMODEL",
                "NAMED_OBSTRUCTION",
            ],
            "non_promotion_rules": [
                "Finite-search failure never implies TRUE.",
                "Constructor schemas are empirical emitters; each claim still requires Lean verification.",
                "Named obstruction patterns guide routing; they do not settle implication truth without an attached terminal certificate policy.",
            ],
        },
    }


def _route_error(error_class: str) -> Dict[str, Any]:
    try:
        from mathgraph.sair_v17_replay_router import route_failed_attempt
        decision = route_failed_attempt(error_class=error_class)
        if hasattr(decision, "__dict__"):
            return dict(decision.__dict__)
        return decision
    except Exception:
        err = str(error_class or "").upper()
        if err in {"UNSOLVED_GOALS", "TYPE_MISMATCH"}:
            return {
                "constructor_family": "EXPLICIT_SUBPOSITION_CONGRARG_BRIDGE_REPAIR",
                "recommended_engine": "explicit_congrarg_two_step_symm_s2",
                "reason": "Bridge rewrite failure should try explicit subposition congrArg/calc repair before broadening.",
            }
        if err in {"EMIT_ERROR", "LEAN_ERROR"}:
            return {
                "constructor_family": "FIXED_HEADER_EXACT_REPLAY",
                "recommended_engine": "make_universe_u_header_mandatory",
                "reason": "Emitter/header failures should be repaired before semantic broadening.",
            }
        return {
            "constructor_family": "LAWBOOK_FIRST_RESIDUAL_ATTACK",
            "recommended_engine": "sair_v17_replay_router",
            "reason": "Use constructor memory before broad residual search.",
        }


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the SAIR v17 replay router safely.",
    )
    parser.add_argument(
        "--mode",
        choices=["routes", "route-error", "summary"],
        default="routes",
        help="Router mode. Default prints next routes and exits 0.",
    )
    parser.add_argument(
        "--error-class",
        default="UNSOLVED_GOALS",
        help="Error class for --mode route-error.",
    )
    parser.add_argument(
        "--summary-json",
        default="",
        help="Optional SAIR v17 import/package summary JSON to include in output.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON.",
    )
    args = parser.parse_args(argv)

    try:
        payload: Dict[str, Any]
        if args.mode == "routes":
            payload = _default_routes()
        elif args.mode == "route-error":
            payload = {
                "ok": True,
                "mode": "route_error",
                "error_class": args.error_class,
                "decision": _route_error(args.error_class),
            }
        elif args.mode == "summary":
            summary = _load_json(args.summary_json) if args.summary_json else None
            payload = {
                "ok": True,
                "mode": "summary",
                "summary": summary,
                "routes": _default_routes()["routes"],
            }
        else:
            payload = _default_routes()

        print(json.dumps(payload, indent=2 if args.pretty else None, ensure_ascii=False, default=_json_default))
        return 0

    except Exception as exc:
        payload = {
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
            "mode": args.mode,
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False, default=_json_default), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
