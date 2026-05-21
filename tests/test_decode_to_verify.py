import json

from mathgraph.decode_to_verify import DecodeStatus, decode_reason_to_verify, decode_reasons_to_verify
from mathgraph.lawbook_store import LawbookStore


def test_supported_reason_decodes_to_action(tmp_path):
    store = LawbookStore(tmp_path / "lawbook.sqlite")
    store.insert_artifact({"domain": "sair", "basin": "b", "terminal_form": "FINITE_COUNTERMODEL", "trust_level": 100, "boundary_type": "finite_model_checker"})
    reason = {"reason_id": "r", "support_count": 2}
    result = decode_reason_to_verify(store, reason, [{"domain": "sair", "basin": "b"}])
    assert result.status in {DecodeStatus.DECODE_VERIFIED, DecodeStatus.DECODE_PARTIAL}
    assert result.action_suggestions
    store.close()


def test_unsupported_and_overfit_reasons():
    store = LawbookStore(":memory:")
    assert decode_reason_to_verify(store, {"reason_id": "r", "support_count": 0}, [{"domain": "sair"}]).status == DecodeStatus.DECODE_UNSUPPORTED
    assert decode_reason_to_verify(store, {"reason_id": "r", "support_count": 1}, [{"domain": "sair"}]).status in {DecodeStatus.DECODE_FAILED, DecodeStatus.DECODE_OVERFIT}
    store.close()


def test_decode_report_json_serializable(tmp_path):
    store = LawbookStore(tmp_path / "lawbook.sqlite")
    report = decode_reasons_to_verify(store, [{"reason_id": "r", "support_count": 0}], [{"domain": "sair"}])
    json.dumps(report)
    store.close()
