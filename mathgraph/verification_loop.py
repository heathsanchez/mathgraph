"""Stable façade for MathGraph verification-loop entry points."""

from __future__ import annotations

from typing import Any


def run_compounding_episode(**kwargs: Any) -> Any:
    from mathgraph.compounding_engine import CompoundingEngineConfig, run_compounding_loop

    return run_compounding_loop(CompoundingEngineConfig(**kwargs))


def run_closed_verification_episode(*args: Any, **kwargs: Any) -> Any:
    from mathgraph.closed_verification_loop import ClosedVerificationLoop, ClosedVerificationLoopConfig

    config = kwargs.pop("config", None) or ClosedVerificationLoopConfig(**kwargs)
    return ClosedVerificationLoop(config).run(*args)


def run_advisory_scheduled_episode(**kwargs: Any) -> Any:
    return run_compounding_episode(**kwargs)


def run_finite_countermodel_episode(source_equation: str, target_equation: str, table: list[list[int]]) -> Any:
    from mathgraph.finite_magma_world import check_finite_countermodel

    return check_finite_countermodel(source_equation, target_equation, table)
