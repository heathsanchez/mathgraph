"""Benchmark suite metadata and run/result records."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class BenchmarkExpectedStatus(str, Enum):
    EXPECT_PROOF = "EXPECT_PROOF"
    EXPECT_COUNTERMODEL = "EXPECT_COUNTERMODEL"
    EXPECT_UNKNOWN = "EXPECT_UNKNOWN"
    EXPECT_OBSTRUCTION = "EXPECT_OBSTRUCTION"
    EXPECT_TIMEOUT_OK = "EXPECT_TIMEOUT_OK"
    UNKNOWN = "UNKNOWN"


class BenchmarkObservedStatus(str, Enum):
    PROOF_FOUND = "PROOF_FOUND"
    COUNTERMODEL_FOUND = "COUNTERMODEL_FOUND"
    OBSTRUCTION_NAMED = "OBSTRUCTION_NAMED"
    UNKNOWN = "UNKNOWN"
    TIMEOUT = "TIMEOUT"
    ERROR = "ERROR"


def _enum(enum_type: Any, value: Any, default: Any) -> Any:
    if isinstance(value, enum_type):
        return value
    for member in enum_type:
        if str(value) == member.value:
            return member
    return default


@dataclass(frozen=True)
class BenchmarkSuite:
    suite_id: str
    name: str
    domain_kernel_id: str | None = None
    formal_world_id: str | None = None
    description: str = ""
    case_count: int = 0
    source: str = ""
    notes: str = ""
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {**self.__dict__, "payload": dict(self.payload)}


@dataclass(frozen=True)
class BenchmarkCase:
    case_id: str
    suite_id: str
    claim_id: str | None = None
    source_statement: str | None = None
    target_statement: str | None = None
    expected_status: BenchmarkExpectedStatus = BenchmarkExpectedStatus.UNKNOWN
    expected_terminal_form: str | None = None
    notes: str = ""
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.__dict__,
            "expected_status": self.expected_status.value,
            "payload": dict(self.payload),
        }


@dataclass(frozen=True)
class BenchmarkRun:
    run_id: str
    suite_id: str
    backend_id: str | None = None
    domain_kernel_id: str | None = None
    formal_world_id: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    total_cases: int = 0
    passed_cases: int = 0
    failed_cases: int = 0
    unknown_cases: int = 0
    notes: str = ""
    payload: dict[str, Any] = field(default_factory=dict)

    def pass_rate(self) -> float:
        return 0.0 if self.total_cases <= 0 else self.passed_cases / self.total_cases

    def to_dict(self) -> dict[str, Any]:
        return {**self.__dict__, "payload": dict(self.payload)}


@dataclass(frozen=True)
class BenchmarkResult:
    result_id: str
    run_id: str
    case_id: str
    observed_status: BenchmarkObservedStatus = BenchmarkObservedStatus.UNKNOWN
    expected_status: BenchmarkExpectedStatus = BenchmarkExpectedStatus.UNKNOWN
    verifier_backend_id: str | None = None
    runtime_sec: float | None = None
    proof_result_id: str | None = None
    model_result_id: str | None = None
    artifact_risk: str = "UNKNOWN"
    regression_status: str = "UNKNOWN"
    notes: str = ""
    payload: dict[str, Any] = field(default_factory=dict)

    def matches_expectation(self) -> bool:
        return (
            (self.expected_status is BenchmarkExpectedStatus.EXPECT_PROOF and self.observed_status is BenchmarkObservedStatus.PROOF_FOUND)
            or (
                self.expected_status is BenchmarkExpectedStatus.EXPECT_COUNTERMODEL
                and self.observed_status is BenchmarkObservedStatus.COUNTERMODEL_FOUND
            )
            or (
                self.expected_status is BenchmarkExpectedStatus.EXPECT_OBSTRUCTION
                and self.observed_status is BenchmarkObservedStatus.OBSTRUCTION_NAMED
            )
            or (self.expected_status is BenchmarkExpectedStatus.EXPECT_UNKNOWN and self.observed_status is BenchmarkObservedStatus.UNKNOWN)
            or (self.expected_status is BenchmarkExpectedStatus.EXPECT_TIMEOUT_OK and self.observed_status is BenchmarkObservedStatus.TIMEOUT)
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.__dict__,
            "observed_status": self.observed_status.value,
            "expected_status": self.expected_status.value,
            "payload": dict(self.payload),
        }


def etp_matrix_benchmark_suite_metadata() -> BenchmarkSuite:
    return BenchmarkSuite(
        suite_id="benchmark_etp_matrix_metadata",
        name="ETP implication matrix benchmark metadata",
        domain_kernel_id="etp_magma",
        formal_world_id="formal_world_etp_magma",
        description="The ETP implication matrix is a benchmark universe, not proof.",
        source="external_artifact",
        notes="Matrix truth is evaluation data; terminal certificates still require verifier replay.",
        payload={"truth_boundary": "matrix_rows_are_not_certificates"},
    )


def reference_methodology_benchmark_suite_metadata() -> BenchmarkSuite:
    return BenchmarkSuite(
        suite_id="benchmark_logikey_methodology",
        name="Reference methodology benchmark metadata",
        description="Object logics and domain theories should be tested by prover/model-finder runs.",
        source="methodology_metadata",
        notes="Benchmarks are regression/evidence, not proof.",
        payload={"advisory_only": True},
    )


def logikey_methodology_benchmark_suite_metadata() -> BenchmarkSuite:
    """Legacy internal alias; use ``reference_methodology_benchmark_suite_metadata`` publicly."""

    return reference_methodology_benchmark_suite_metadata()
