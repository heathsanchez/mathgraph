def test_task_planner_public_exports() -> None:
    from mathgraph import CertificateTask
    from mathgraph import plan_certificate_task
    from mathgraph import plan_many_certificate_tasks

    assert CertificateTask.__name__ == "CertificateTask"
    assert callable(plan_certificate_task)
    assert callable(plan_many_certificate_tasks)


def test_task_runner_public_exports() -> None:
    from mathgraph import TaskOutcome
    from mathgraph import TaskRunSummary
    from mathgraph import execute_certificate_task
    from mathgraph import execute_many_certificate_tasks
    from mathgraph import read_outcomes_json
    from mathgraph import read_outcomes_jsonl
    from mathgraph import residual_outcomes
    from mathgraph import summarize_task_outcomes
    from mathgraph import write_outcomes_json
    from mathgraph import write_outcomes_jsonl

    assert TaskOutcome.__name__ == "TaskOutcome"
    assert TaskRunSummary.__name__ == "TaskRunSummary"
    assert callable(execute_certificate_task)
    assert callable(execute_many_certificate_tasks)
    assert callable(summarize_task_outcomes)
    assert callable(residual_outcomes)
    assert callable(read_outcomes_json)
    assert callable(write_outcomes_json)
    assert callable(read_outcomes_jsonl)
    assert callable(write_outcomes_jsonl)


def test_asset_materialization_public_exports() -> None:
    from mathgraph import AssetMaterializationConfig
    from mathgraph import AssetMaterializationResult
    from mathgraph import materialize_mathgraph_assets

    assert AssetMaterializationConfig.__name__ == "AssetMaterializationConfig"
    assert AssetMaterializationResult.__name__ == "AssetMaterializationResult"
    assert callable(materialize_mathgraph_assets)


def test_verify_api_public_exports() -> None:
    from mathgraph import MathGraphVerifier
    from mathgraph import VerifyConfig
    from mathgraph import VerifyRequest
    from mathgraph import VerifyResult

    assert MathGraphVerifier.__name__ == "MathGraphVerifier"
    assert VerifyConfig.__name__ == "VerifyConfig"
    assert VerifyRequest.__name__ == "VerifyRequest"
    assert VerifyResult.__name__ == "VerifyResult"


def test_duplicate_frontier_public_export() -> None:
    from mathgraph import KnownPairFilter

    assert KnownPairFilter.__name__ == "KnownPairFilter"


def test_post_v167_public_exports() -> None:
    from mathgraph import GeneralClaim
    from mathgraph import ObstructionNode
    from mathgraph import ProvenanceType
    from mathgraph import ReasonNode
    from mathgraph import RefutationCertificate
    from mathgraph import RootNode
    from mathgraph import RootNodeOracle
    from mathgraph import TrustLevel
    from mathgraph import consolidate_root_nodes

    assert GeneralClaim.__name__ == "GeneralClaim"
    assert RootNode.__name__ == "RootNode"
    assert ReasonNode.__name__ == "ReasonNode"
    assert ObstructionNode.__name__ == "ObstructionNode"
    assert RootNodeOracle.__name__ == "RootNodeOracle"
    assert RefutationCertificate.__name__ == "RefutationCertificate"
    assert TrustLevel.FINITE_VERIFIED.value == "FINITE_VERIFIED"
    assert ProvenanceType.DERIVED.value == "DERIVED"
    assert callable(consolidate_root_nodes)
