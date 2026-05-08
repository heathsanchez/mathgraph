import json
import threading
import urllib.error
import urllib.request

import pytest

from mathgraph.local_service import make_server
from mathgraph.terminal_contract import Status, TerminalForm, TrustLevel, VerifierBoundary


@pytest.fixture
def service(tmp_path):
    try:
        server = make_server(str(tmp_path / "api.sqlite"), host="127.0.0.1", port=0)
    except PermissionError as exc:
        pytest.skip(f"local socket bind is blocked in this sandbox: {exc}")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        yield base_url
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def _get(base_url, path):
    with urllib.request.urlopen(base_url + path, timeout=10) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def _post(base_url, path, payload=None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        base_url + path,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def _post_raw(base_url, path, text):
    request = urllib.request.Request(
        base_url + path,
        data=text.encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        urllib.request.urlopen(request, timeout=10)
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))
    raise AssertionError("expected HTTP error")


def _post_error(base_url, path, payload):
    request = urllib.request.Request(
        base_url + path,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        urllib.request.urlopen(request, timeout=10)
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))
    raise AssertionError("expected HTTP error")


def test_health_returns_ok(service):
    status, payload = _get(service, "/health")

    assert status == 200
    assert payload["ok"] is True
    assert payload["service"] == "mathgraph-local"
    assert payload["terminal_contract"] is True


def test_stats_returns_json(service):
    status, payload = _get(service, "/stats")

    assert status == 200
    assert payload["ok"] is True
    assert "total_certificate_count" in payload


def test_query_empty_store_is_read_only_unknown(service):
    status, payload = _post(service, "/query", {"source": "(x*x)=x", "target": "(x*y)=x"})

    assert status == 200
    assert payload["ok"] is True
    assert payload["status"] == Status.UNKNOWN
    assert payload["trust_level"] == TrustLevel.ADVISORY_ROUTE
    assert payload["verifier_boundary"] == VerifierBoundary.NOT_VERIFIED
    assert payload["certificate_id"] is None
    _, stats = _get(service, "/stats")
    assert stats["total_certificate_count"] == 0


def test_submit_known_false_pair_returns_verified_refutation(service):
    status, payload = _post(
        service,
        "/submit",
        {
            "source": "(x*x)=x",
            "target": "(x*y)=x",
            "allow_construction": True,
            "max_countermodel_order": 3,
        },
    )

    assert status == 200
    assert payload["ok"] is True
    assert payload["terminal_form"] == TerminalForm.REFUTATION_CERTIFICATE
    assert payload["trust_level"] == TrustLevel.FINITE_VERIFIED
    assert payload["verifier_boundary"] == VerifierBoundary.IMPORTER_REVALIDATED
    assert payload["certificate_id"]
    assert payload["audit"]["passed"] is True


def test_query_after_submit_returns_known_without_construction(service):
    _, first = _post(service, "/submit", {"source": "(x*x)=x", "target": "(x*y)=x"})

    _, second = _post(service, "/query", {"source": "(x*x)=x", "target": "(x*y)=x"})

    assert second["status"] == "REFUTED"
    assert second["terminal_form"] == TerminalForm.REFUTATION_CERTIFICATE
    assert second["certificate_id"] == first["certificate_id"]


def test_audit_returns_passed_true(service):
    _post(service, "/submit", {"source": "(x*x)=x", "target": "(x*y)=x"})

    status, payload = _post(service, "/audit")

    assert status == 200
    assert payload["ok"] is True
    assert payload["passed"] is True


def test_malformed_json_returns_400(service):
    status, payload = _post_raw(service, "/query", "{bad json")

    assert status == 400
    assert payload["ok"] is False
    assert payload["error_type"] == "bad_request"
    assert "Finite search failure is not proof." in payload["warnings"]


def test_missing_source_target_returns_400(service):
    status, payload = _post_error(service, "/query", {"source": "(x*x)=x"})

    assert status == 400
    assert payload["ok"] is False
    assert payload["error_type"] == "bad_request"


def test_unknown_endpoint_returns_404(service):
    try:
        urllib.request.urlopen(service + "/missing", timeout=10)
    except urllib.error.HTTPError as exc:
        payload = json.loads(exc.read().decode("utf-8"))
        assert exc.code == 404
        assert payload["ok"] is False
        assert payload["error_type"] == "not_found"
    else:
        raise AssertionError("expected HTTPError")


def test_wrong_method_returns_405(service):
    try:
        urllib.request.urlopen(service + "/query", timeout=10)
    except urllib.error.HTTPError as exc:
        payload = json.loads(exc.read().decode("utf-8"))
        assert exc.code == 405
        assert payload["ok"] is False
        assert payload["error_type"] == "method_not_allowed"
    else:
        raise AssertionError("expected HTTPError")


def test_schema_endpoint_returns_endpoint_list(service):
    status, payload = _get(service, "/schema")

    assert status == 200
    assert payload["ok"] is True
    paths = {endpoint["path"] for endpoint in payload["endpoints"]}
    assert {"/health", "/stats", "/query", "/submit", "/audit", "/schema"} <= paths
