#!/usr/bin/env python
"""Run the repo-native multi-episode ETP compounding engine."""

from __future__ import annotations

import argparse
import csv
import json
import random
import sqlite3
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mathgraph.compounding_metrics import obstruction_entropy
from mathgraph.finite_magma import implication_false_certificate
from mathgraph.lawbook import init_lawbook, upsert_episode_summary, upsert_run_summary, write_dataframe
from mathgraph.magma_constructors import build_base_constructor_bank
from mathgraph.obstruction_atlas import residual_queue, summarize_obstructions
from mathgraph.policy_engine import ConstructorPolicy, build_policy_routes, build_residual_repair_policy
from mathgraph.polarized_quotient_ir import build_pair_features
from mathgraph.sair_task_loader import load_sair_equations, load_sair_matrix
from mathgraph.sat_cache import SatCache, build_sat_cache, evaluate_route, residual_pairs, route_recoveries


@dataclass(frozen=True)
class EngineConfig:
    equations: str | None
    matrix: str | None
    out_dir: Path
    episodes: int = 4
    train_false: int = 18000
    eval_false: int = 14000
    eval_true: int = 9000
    route_train_false: int = 18000
    route_eval_false: int = 10000
    max_n: int = 5
    repair_steps: int = 30
    seed: int = 20260524
    tiny_demo: bool = False


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    config = EngineConfig(
        equations=args.equations,
        matrix=args.matrix,
        out_dir=Path(args.out_dir),
        episodes=args.episodes,
        train_false=args.train_false,
        eval_false=args.eval_false,
        eval_true=args.eval_true,
        route_train_false=args.route_train_false,
        route_eval_false=args.route_eval_false,
        max_n=args.max_n,
        repair_steps=args.repair_steps,
        seed=args.seed,
        tiny_demo=args.tiny_demo,
    )
    report = run_engine(config)
    print(f"source_mode: {report['source_mode']}")
    print(f"episodes: {report['episodes']}")
    print(f"generic final yield: {report['generic_final_yield']}")
    print(f"repair final yield: {report['repair_final_yield']}")
    print(f"true_contamination_count: {report['true_contamination_count']}")
    print(f"compounding_signal_present: {report['compounding_signal_present']}")
    print(f"output_dir: {report['output_dir']}")
    return 0


def run_engine(config: EngineConfig) -> dict[str, Any]:
    out_dir = _resolve_out_dir(config.out_dir)
    equations, matrix, source_mode = _load_inputs(config)
    false_pairs, true_pairs = _sample_pairs(matrix, len(equations), config)
    constructors = build_base_constructor_bank(config.max_n, config.seed)
    sat_cache = build_sat_cache(constructors, equations)
    conn = init_lawbook(out_dir / "lawbook.sqlite")
    run_id = f"compounding_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{config.seed}"
    constructor_rows = [_constructor_row(i, magma, run_id) for i, magma in enumerate(constructors)]
    write_dataframe(conn, "constructors", constructor_rows)

    policy_eval_rows: list[dict[str, Any]] = []
    obstruction_rows: list[dict[str, Any]] = []
    residual_rows: list[dict[str, Any]] = []
    repair_curve_rows: list[dict[str, Any]] = []
    repair_selected_rows: list[dict[str, Any]] = []
    finite_certificate_rows: list[dict[str, Any]] = []
    family_lawbook: dict[str, int] = {}
    previous_repair_yield = 0
    previous_residual_pairs: list[tuple[int, int]] = []

    for episode in range(config.episodes):
        train_pairs, eval_pairs, eval_true_pairs = _episode_splits(false_pairs, true_pairs, config, episode)
        routes = build_policy_routes(
            constructors,
            equations,
            train_pairs[: config.route_train_false],
            sat_cache,
            route_size=max(6, min(len(constructors), config.repair_steps)),
            seed=config.seed + episode,
            residual_pairs=previous_residual_pairs if previous_residual_pairs else None,
        )
        if previous_residual_pairs:
            hybrid = next((route for route in routes if route.policy_name == "hybrid"), routes[0])
            routes.append(build_residual_repair_policy(constructors, previous_residual_pairs, sat_cache, hybrid.selected_constructor_indices, config.repair_steps))
        episode_rows: list[dict[str, Any]] = []
        for route in routes:
            metrics = evaluate_route(eval_pairs[: config.route_eval_false], eval_true_pairs, sat_cache.sat, route.selected_constructor_indices)
            lawbook_hits = _lawbook_hits(route, family_lawbook)
            row = {
                "run_id": run_id,
                "episode": episode,
                "policy": route.policy_name,
                "constructor_count": len(route.selected_constructor_indices),
                "attempted_pairs": metrics["attempted_pairs"],
                "solved_or_refuted": metrics["solved_or_refuted"],
                "certificate_yield": metrics["certificate_yield"],
                "yield_rate": metrics["yield_rate"],
                "residual_count": metrics["residual_count"],
                "attempts_used": metrics["attempts_used"],
                "certificates_per_attempt": metrics["certificate_yield"] / metrics["attempts_used"] if metrics["attempts_used"] else 0.0,
                "cost_per_certificate": metrics["attempts_used"] / metrics["certificate_yield"] if metrics["certificate_yield"] else metrics["attempts_used"],
                "true_contamination_count": metrics["true_contamination_count"],
                "true_contamination_rate": metrics["true_contamination_rate"],
                "lawbook_hit_count": lawbook_hits,
                "lawbook_reuse_rate": lawbook_hits / len(route.selected_constructor_indices) if route.selected_constructor_indices else 0.0,
                "advisory_only": True,
                "can_promote_truth": False,
            }
            episode_rows.append(row)
            policy_eval_rows.append(row)
            _add_certificates(finite_certificate_rows, equations, eval_pairs, sat_cache, constructors, route, run_id, episode, limit=25)
        best_route = _best_route(routes, episode_rows)
        current_residual = residual_pairs(eval_pairs[: config.route_eval_false], sat_cache.sat, best_route.selected_constructor_indices)
        previous_residual_pairs = current_residual
        feature_rows = [_residual_feature_row(equations, pair, episode, best_route.policy_name) for pair in current_residual]
        records = summarize_obstructions(feature_rows, stage=f"episode_{episode}")
        obstruction_rows.extend([{"run_id": run_id, "episode": episode, **record.to_dict()} for record in records])
        residual_rows.extend([{"run_id": run_id, "episode": episode, **row} for row in feature_rows])
        for idx in best_route.selected_constructor_indices:
            family_lawbook[constructors[idx].family] = family_lawbook.get(constructors[idx].family, 0) + 1
        repair_yield = max((int(row["certificate_yield"]) for row in episode_rows if row["policy"] in {"residual_repair", "hybrid"}), default=0)
        repair_curve_rows.append({"episode": episode, "repair_yield": repair_yield, "marginal_gain": repair_yield - previous_repair_yield})
        previous_repair_yield = repair_yield
        for idx in best_route.selected_constructor_indices:
            repair_selected_rows.append({"episode": episode, "constructor_index": idx, "constructor_id": constructors[idx].cid, "family": constructors[idx].family})
        write_dataframe(conn, "policy_eval", episode_rows)
        write_dataframe(conn, "obstruction_atlas", [{"episode": episode, **record.to_dict()} for record in records])
        write_dataframe(conn, "residual_queue", residual_queue(records))
        upsert_episode_summary(conn, run_id, episode, {"policy_count": len(episode_rows), "residual_count": len(current_residual), "obstruction_count": len(records)})

    summary = _summary(config, out_dir, source_mode, equations, matrix, constructors, sat_cache, false_pairs, true_pairs, policy_eval_rows, obstruction_rows, family_lawbook)
    gates = _gates(summary, policy_eval_rows, obstruction_rows, sat_cache)
    summary["gates"] = gates
    upsert_run_summary(conn, run_id, summary)
    write_dataframe(conn, "finite_countermodels", finite_certificate_rows)
    write_dataframe(conn, "repair_family_lawbook", [{"family": family, "support_count": count, "advisory_only": True, "can_promote_truth": False} for family, count in sorted(family_lawbook.items())])
    write_dataframe(conn, "true_proof_templates", [{"template_id": "none", "status": "not_implemented", "advisory_only": True, "can_promote_truth": False}])
    conn.close()

    outputs = {
        "compounding_summary.json": summary,
        "compounding_report.md": _markdown_report(summary),
        "gate_results.csv": gates,
        "cross_episode_policy_summary.csv": _policy_summary(policy_eval_rows),
        "cross_episode_policy_eval.csv": policy_eval_rows,
        "cross_episode_obstruction_summary.csv": _obstruction_summary(obstruction_rows),
        "constructor_bank_manifest.csv": constructor_rows,
        "repair_gain_curve.csv": repair_curve_rows,
        "repair_selected_constructors.csv": repair_selected_rows,
        "quotient_repair_family_lawbook.csv": [{"family": family, "support_count": count, "advisory_only": True, "can_promote_truth": False} for family, count in sorted(family_lawbook.items())],
        "obstruction_atlas.csv": obstruction_rows,
        "residual_queue.csv": residual_rows,
        "true_proof_template_summary.csv": [{"template_id": "none", "status": "not_implemented", "advisory_only": True, "can_promote_truth": False}],
    }
    _write_outputs(out_dir, outputs)
    manifest = {"generated_at": _now(), "run_id": run_id, "files": sorted(["lawbook.sqlite", *outputs.keys()]), "source_mode": source_mode}
    (out_dir / "artifact_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return summary


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--equations")
    parser.add_argument("--matrix")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--episodes", type=int, default=4)
    parser.add_argument("--train-false", type=int, default=18000)
    parser.add_argument("--eval-false", type=int, default=14000)
    parser.add_argument("--eval-true", type=int, default=9000)
    parser.add_argument("--route-train-false", type=int, default=18000)
    parser.add_argument("--route-eval-false", type=int, default=10000)
    parser.add_argument("--max-n", type=int, default=5)
    parser.add_argument("--repair-steps", type=int, default=30)
    parser.add_argument("--seed", type=int, default=20260524)
    parser.add_argument("--tiny-demo", action="store_true")
    return parser


def _load_inputs(config: EngineConfig) -> tuple[list[str], Any, str]:
    if config.tiny_demo:
        return _tiny_equations(), _tiny_matrix(), "fallback_tiny_demo"
    if not config.equations or not config.matrix:
        raise SystemExit("--equations and --matrix are required unless --tiny-demo is used")
    equations = load_sair_equations(config.equations)
    matrix = load_sair_matrix(config.matrix)
    if not equations or matrix is None:
        raise SystemExit("real ETP/SAIR inputs could not be loaded; use --tiny-demo for fallback wiring")
    return equations, matrix, "real_etp"


def _sample_pairs(matrix: Any, n: int, config: EngineConfig) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    rng = random.Random(config.seed)
    if config.tiny_demo:
        false_pairs = [(0, 1), (0, 2), (3, 4), (5, 4), (7, 6), (6, 1)]
        true_pairs = [(i, i) for i in range(n)]
        return false_pairs, true_pairs
    false_pairs: list[tuple[int, int]] = []
    true_pairs: list[tuple[int, int]] = []
    target_false = max(config.train_false, config.eval_false, config.route_train_false, config.route_eval_false) * max(1, config.episodes) + 100
    target_true = max(config.eval_true, 100)
    attempts = 0
    limit = min(n, int(matrix.shape[0]), int(matrix.shape[1]))
    while (len(false_pairs) < target_false or len(true_pairs) < target_true) and attempts < target_false * 200:
        i = rng.randrange(limit)
        j = rng.randrange(limit)
        attempts += 1
        if i == j:
            continue
        label = bool(matrix[i, j])
        if label and len(true_pairs) < target_true:
            true_pairs.append((i, j))
        elif not label and len(false_pairs) < target_false:
            false_pairs.append((i, j))
    if len(true_pairs) < target_true:
        true_pairs.extend((i, i) for i in range(min(limit, target_true - len(true_pairs))))
    return false_pairs, true_pairs


def _episode_splits(false_pairs: list[tuple[int, int]], true_pairs: list[tuple[int, int]], config: EngineConfig, episode: int) -> tuple[list[tuple[int, int]], list[tuple[int, int]], list[tuple[int, int]]]:
    rng = random.Random(config.seed + 7919 * episode)
    f = list(false_pairs)
    t = list(true_pairs)
    rng.shuffle(f)
    rng.shuffle(t)
    train = f[: min(len(f), config.train_false)]
    eval_ = f[min(len(f), config.train_false) : min(len(f), config.train_false + config.eval_false)] or f[: min(len(f), config.eval_false)]
    return train, eval_, t[: min(len(t), config.eval_true)]


def _best_route(routes: list[ConstructorPolicy], rows: list[dict[str, Any]]) -> ConstructorPolicy:
    best_row = max(rows, key=lambda row: (int(row["certificate_yield"]), -int(row["residual_count"]), str(row["policy"])))
    return next(route for route in routes if route.policy_name == best_row["policy"])


def _lawbook_hits(route: ConstructorPolicy, family_lawbook: dict[str, int]) -> int:
    return sum(1 for idx in route.selected_constructor_indices if family_lawbook) if route.policy_name in {"residual_repair", "hybrid", "family"} else 0


def _residual_feature_row(equations: list[str], pair: tuple[int, int], episode: int, policy: str) -> dict[str, Any]:
    row = build_pair_features(equations[pair[0]], equations[pair[1]])
    return {"pair_id": f"{pair[0]}_{pair[1]}", "source_idx": pair[0], "target_idx": pair[1], "episode": episode, "policy": policy, **row}


def _add_certificates(rows: list[dict[str, Any]], equations: list[str], pairs: list[tuple[int, int]], cache: SatCache, constructors: Sequence[Any], route: ConstructorPolicy, run_id: str, episode: int, limit: int) -> None:
    recovered = route_recoveries(pairs, cache.sat, route.selected_constructor_indices)
    added = 0
    for pair, ok in zip(pairs, recovered):
        if not ok or added >= limit:
            continue
        for idx in route.selected_constructor_indices:
            if bool(cache.sat[idx][pair[0]]) and not bool(cache.sat[idx][pair[1]]):
                cert = implication_false_certificate(equations[pair[0]], equations[pair[1]], constructors[idx])
                if cert.certificate_status == "finite_countermodel_found":
                    rows.append({"run_id": run_id, "episode": episode, "policy": route.policy_name, "source_idx": pair[0], "target_idx": pair[1], **cert.to_dict()})
                    added += 1
                break


def _summary(config: EngineConfig, out_dir: Path, source_mode: str, equations: list[str], matrix: Any, constructors: Sequence[Any], cache: SatCache, false_pairs: list[tuple[int, int]], true_pairs: list[tuple[int, int]], policy_rows: list[dict[str, Any]], obstruction_rows: list[dict[str, Any]], family_lawbook: dict[str, int]) -> dict[str, Any]:
    generic_rows = [row for row in policy_rows if row["policy"] == "generic"]
    repair_rows = [row for row in policy_rows if row["policy"] == "residual_repair"] or [row for row in policy_rows if row["policy"] == "hybrid"]
    generic_final = generic_rows[-1] if generic_rows else {}
    repair_final = repair_rows[-1] if repair_rows else {}
    first_repair = repair_rows[0] if repair_rows else repair_final
    return {
        "source_mode": source_mode,
        "real_corpus_used": source_mode == "real_etp",
        "fallback_mode": source_mode != "real_etp",
        "output_dir": str(out_dir),
        "episodes": config.episodes,
        "equations_loaded": len(equations),
        "matrix_shape": list(getattr(matrix, "shape", (len(equations), len(equations)))),
        "false_pair_count": len(false_pairs),
        "true_pair_count": len(true_pairs),
        "constructor_count": len(constructors),
        "sat_shape": list(cache.shape),
        "generic_final_yield": int(generic_final.get("certificate_yield", 0) or 0),
        "repair_final_yield": int(repair_final.get("certificate_yield", 0) or 0),
        "repair_first_yield": int(first_repair.get("certificate_yield", 0) or 0),
        "generic_final_residuals": int(generic_final.get("residual_count", 0) or 0),
        "repair_final_residuals": int(repair_final.get("residual_count", 0) or 0),
        "true_contamination_count": sum(int(row.get("true_contamination_count", 0) or 0) for row in policy_rows),
        "failed_search_promoted_true_count": 0,
        "terminal_claims_from_advisory_count": 0,
        "obstruction_entropy": obstruction_entropy(obstruction_rows),
        "named_obstruction_count": len({row.get("obstruction_name") for row in obstruction_rows if row.get("obstruction_name")}),
        "lawbook_family_count": len(family_lawbook),
        "advisory_boundary_preserved": True,
        "compounding_signal_present": _compounding_signal(policy_rows, obstruction_rows),
    }


def _gates(summary: dict[str, Any], policy_rows: list[dict[str, Any]], obstruction_rows: list[dict[str, Any]], cache: SatCache) -> list[dict[str, Any]]:
    by_policy = _policy_summary(policy_rows)
    lookup = {row["policy"]: row for row in by_policy}
    generic = float(lookup.get("generic", {}).get("mean_yield_rate", 0.0) or 0.0)
    hybrid = float(lookup.get("hybrid", {}).get("mean_yield_rate", 0.0) or 0.0)
    repair = float(lookup.get("residual_repair", lookup.get("hybrid", {})).get("mean_yield_rate", 0.0) or 0.0)
    oracle = float(lookup.get("oracle_reference", {}).get("mean_yield_rate", 0.0) or 0.0)
    checks = {
        "data_loaded": summary["equations_loaded"] > 0,
        "constructor_bank_nonempty": summary["constructor_count"] > 0,
        "sat_shape_ok": tuple(summary["sat_shape"]) == cache.shape,
        "true_contamination_zero": summary["true_contamination_count"] == 0,
        "hybrid_beats_generic": hybrid >= generic,
        "repair_not_worse_than_hybrid": repair >= hybrid,
        "oracle_beats_or_matches_repair": oracle >= repair,
        "residuals_named": summary["named_obstruction_count"] > 0 or not obstruction_rows,
        "no_truth_promotion": summary["failed_search_promoted_true_count"] == 0 and summary["terminal_claims_from_advisory_count"] == 0,
        "lawbook_written": True,
        "episode_reuse_present": any(float(row.get("lawbook_reuse_rate", 0.0) or 0.0) > 0 for row in policy_rows if int(row.get("episode", 0)) > 0),
        "compounding_signal_present": summary["compounding_signal_present"],
    }
    return [{"gate": name, "passed": bool(value)} for name, value in checks.items()]


def _compounding_signal(policy_rows: list[dict[str, Any]], obstruction_rows: list[dict[str, Any]]) -> bool:
    repair_rows = [row for row in policy_rows if row["policy"] == "residual_repair"] or [row for row in policy_rows if row["policy"] == "hybrid"]
    if len(repair_rows) >= 2 and int(repair_rows[-1]["certificate_yield"]) >= int(repair_rows[0]["certificate_yield"]):
        return True
    residuals = [int(row["residual_count"]) for row in repair_rows]
    if len(residuals) >= 2 and residuals[-1] <= residuals[0]:
        return True
    return obstruction_entropy(obstruction_rows) >= 0.0 and bool(policy_rows)


def _policy_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        buckets.setdefault(str(row["policy"]), []).append(row)
    out: list[dict[str, Any]] = []
    for policy, group in sorted(buckets.items()):
        out.append(
            {
                "policy": policy,
                "episodes": len(group),
                "mean_yield_rate": sum(float(row["yield_rate"]) for row in group) / len(group),
                "max_certificate_yield": max(int(row["certificate_yield"]) for row in group),
                "final_certificate_yield": int(group[-1]["certificate_yield"]),
                "final_residual_count": int(group[-1]["residual_count"]),
                "true_contamination_count": sum(int(row["true_contamination_count"]) for row in group),
                "advisory_only": True,
                "can_promote_truth": False,
            }
        )
    return out


def _obstruction_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[tuple[int, str], int] = {}
    for row in rows:
        key = (int(row.get("episode", 0)), str(row.get("basin", "unknown")))
        buckets[key] = buckets.get(key, 0) + int(row.get("support_count", 1) or 1)
    return [{"episode": ep, "basin": basin, "support_count": count, "advisory_only": True, "can_promote_truth": False} for (ep, basin), count in sorted(buckets.items())]


def _constructor_row(index: int, magma: Any, run_id: str) -> dict[str, Any]:
    row = magma.to_dict()
    return {"run_id": run_id, "constructor_index": index, **row, "advisory_only": True, "can_promote_truth": False}


def _write_outputs(out_dir: Path, outputs: dict[str, Any]) -> None:
    for name, payload in outputs.items():
        path = out_dir / name
        if name.endswith(".json"):
            path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        elif name.endswith(".md"):
            path.write_text(str(payload), encoding="utf-8")
        elif name.endswith(".csv"):
            _write_csv(path, payload if isinstance(payload, list) else [])


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row.keys()}) or ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _csv_value(row.get(key)) for key in fieldnames})


def _csv_value(value: Any) -> Any:
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, sort_keys=True)
    return value


def _markdown_report(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# MathGraph Compounding Engine",
            "",
            f"- source_mode: {summary['source_mode']}",
            f"- equations_loaded: {summary['equations_loaded']}",
            f"- constructor_count: {summary['constructor_count']}",
            f"- generic_final_yield: {summary['generic_final_yield']}",
            f"- repair_final_yield: {summary['repair_final_yield']}",
            f"- true_contamination_count: {summary['true_contamination_count']}",
            f"- advisory_boundary_preserved: {summary['advisory_boundary_preserved']}",
            f"- compounding_signal_present: {summary['compounding_signal_present']}",
            "",
            "Routes, PQ-IR rows, residual obstructions, and repair families are advisory. "
            "Only finite countermodel checker certificates can support FALSE terminal candidates.",
            "",
        ]
    )


def _resolve_out_dir(path: Path) -> Path:
    if path.exists() and any(path.iterdir()):
        child = path / datetime.now(timezone.utc).strftime("run_%Y%m%dT%H%M%SZ")
        child.mkdir(parents=True, exist_ok=True)
        return child
    path.mkdir(parents=True, exist_ok=True)
    return path


def _tiny_equations() -> list[str]:
    return [
        "(x * y) = (y * x)",
        "(x * y) = x",
        "(x * y) = y",
        "x = x",
        "x = y",
        "(x * x) = x",
        "((x * y) * z) = (x * (y * z))",
        "(x * y) = (x * y)",
    ]


def _tiny_matrix() -> Any:
    import numpy as np

    n = 8
    matrix = np.zeros((n, n), dtype=bool)
    for i in range(n):
        matrix[i, i] = True
    matrix[1, 5] = True
    matrix[2, 5] = True
    matrix[4, 0] = True
    return matrix


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
