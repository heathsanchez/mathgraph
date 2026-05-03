"""MathGraph: a lightweight kernel for verifiable mathematical claims."""

from mathgraph.certificates import Certificate, TerminalForm, VerificationStatus
from mathgraph.corpus import CertificateCorpus
from mathgraph.equations import Equation, parse_equation
from mathgraph.derived_certificates import (
    DerivedCertificate,
    DerivedCertificateGenerator,
    DerivedCertificateStats,
)
from mathgraph.hashing import (
    canonical_json,
    content_id,
    hash_certificate,
    hash_file,
    hash_trace,
    sha256_hex,
    sha256_json,
    sha256_text,
)
from mathgraph.flywheel import (
    FlywheelConfig,
    FlywheelResult,
    FlywheelStageResult,
    run_mathgraph_flywheel,
)
from mathgraph.frontier_builder import (
    FrontierBuilderConfig,
    FrontierBuilderResult,
    FrontierCandidate,
    build_candidate_frontier,
)
from mathgraph.finite_countermodel_executor import (
    FiniteCountermodelConfig,
    FiniteCountermodelResult,
    FiniteCountermodelRunResult,
    run_finite_countermodel_tasks,
)
from mathgraph.htilt_scheduler import (
    HTiltScheduler,
    HTiltSchedulerStats,
    HTiltScoreBreakdown,
    ScheduledTask,
    SchedulerInputPair,
)
from mathgraph.kernel import Kernel
from mathgraph.kernel_oracle import KernelOracle, OracleAnswer
from mathgraph.lawbook import CertificateLawbook
from mathgraph.lawbook_store import LawbookStore, LawbookStoreStats
from mathgraph.ledger import JsonlLedger
from mathgraph.outcome_dataset import (
    CompoundingDiagnostics,
    OutcomeDatasetBuilder,
    OutcomeDatasetStats,
    PairOutcome,
    extract_pair_features as extract_outcome_pair_features,
)
from mathgraph.pair_advisor import PairAdvice, advise_many, advise_pair, extract_pair_features
from mathgraph.route_instructor import (
    RouteInstruction,
    build_all_route_instructions,
    build_route_instruction,
    route_instruction_report,
)
from mathgraph.route_learner import (
    RouteBasinKey,
    RouteLearner,
    RouteLearnerStats,
    RoutePolicyCard,
    RouteRecommendation,
    make_basin_key,
)
from mathgraph.task_planner import (
    CertificateTask,
    plan_certificate_task,
    plan_many_certificate_tasks,
)
from mathgraph.task_queue import (
    TaskQueueConfig,
    TaskQueueItem,
    TaskQueueResult,
    build_task_queue,
)
from mathgraph.task_runner import (
    TaskOutcome,
    TaskRunSummary,
    execute_certificate_task,
    execute_many_certificate_tasks,
    read_outcomes_json,
    read_outcomes_jsonl,
    residual_outcomes,
    summarize_task_outcomes,
    write_outcomes_json,
    write_outcomes_jsonl,
)
from mathgraph.terms import Term, parse_term
from mathgraph.trace import Trace

__all__ = [
    "Certificate",
    "CertificateCorpus",
    "CertificateLawbook",
    "CertificateTask",
    "CompoundingDiagnostics",
    "DerivedCertificate",
    "DerivedCertificateGenerator",
    "DerivedCertificateStats",
    "Equation",
    "FiniteCountermodelConfig",
    "FiniteCountermodelResult",
    "FiniteCountermodelRunResult",
    "FlywheelConfig",
    "FlywheelResult",
    "FlywheelStageResult",
    "FrontierBuilderConfig",
    "FrontierBuilderResult",
    "FrontierCandidate",
    "HTiltScheduler",
    "HTiltSchedulerStats",
    "HTiltScoreBreakdown",
    "Kernel",
    "KernelOracle",
    "JsonlLedger",
    "LawbookStore",
    "LawbookStoreStats",
    "OracleAnswer",
    "OutcomeDatasetBuilder",
    "OutcomeDatasetStats",
    "PairAdvice",
    "PairOutcome",
    "RouteBasinKey",
    "RouteLearner",
    "RouteLearnerStats",
    "TaskOutcome",
    "TaskQueueConfig",
    "TaskQueueItem",
    "TaskQueueResult",
    "TaskRunSummary",
    "canonical_json",
    "RouteInstruction",
    "RoutePolicyCard",
    "RouteRecommendation",
    "ScheduledTask",
    "SchedulerInputPair",
    "build_all_route_instructions",
    "build_route_instruction",
    "build_candidate_frontier",
    "build_task_queue",
    "advise_many",
    "advise_pair",
    "content_id",
    "extract_pair_features",
    "extract_outcome_pair_features",
    "execute_certificate_task",
    "execute_many_certificate_tasks",
    "hash_certificate",
    "hash_file",
    "hash_trace",
    "make_basin_key",
    "sha256_hex",
    "sha256_json",
    "sha256_text",
    "Term",
    "TerminalForm",
    "parse_equation",
    "parse_term",
    "plan_certificate_task",
    "plan_many_certificate_tasks",
    "read_outcomes_json",
    "read_outcomes_jsonl",
    "residual_outcomes",
    "route_instruction_report",
    "run_mathgraph_flywheel",
    "run_finite_countermodel_tasks",
    "summarize_task_outcomes",
    "Trace",
    "VerificationStatus",
    "write_outcomes_json",
    "write_outcomes_jsonl",
]
