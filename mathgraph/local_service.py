"""Local stdlib HTTP service for the MathGraph M0 middleware surface."""

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

from mathgraph.client import MathGraphAuditError, MathGraphClient, MathGraphClientConfig


SERVICE_NAME = "mathgraph-local"
SERVICE_VERSION = "0.1.0"
SERVICE_WARNINGS = [
    "Finite search failure is not proof.",
    "Advisory output is not truth.",
]
GET_ENDPOINTS = {"/health", "/stats", "/schema", "/openapi.json"}
POST_ENDPOINTS = {"/query", "/submit", "/audit"}


class MathGraphHTTPServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], config: MathGraphClientConfig) -> None:
        super().__init__(server_address, MathGraphRequestHandler)
        self.config = config
        self.client = MathGraphClient(config)


class MathGraphRequestHandler(BaseHTTPRequestHandler):
    server: MathGraphHTTPServer

    def log_message(self, format: str, *args: Any) -> None:
        return None

    def do_GET(self) -> None:
        path = _path(self.path)
        if path == "/health":
            self._send_json(
                {
                    "ok": True,
                    "service": SERVICE_NAME,
                    "version": SERVICE_VERSION,
                    "store_path": self.server.config.store_path,
                    "terminal_contract": True,
                }
            )
            return
        if path == "/stats":
            payload = self.server.client.stats()
            payload["ok"] = True
            self._send_json(payload)
            return
        if path in {"/schema", "/openapi.json"}:
            self._send_json(schema(self.server.config.store_path))
            return
        if path in POST_ENDPOINTS:
            self._send_error(HTTPStatus.METHOD_NOT_ALLOWED, "Method not allowed.", "method_not_allowed")
            return
        self._send_error(HTTPStatus.NOT_FOUND, "Unknown endpoint.", "not_found")

    def do_POST(self) -> None:
        path = _path(self.path)
        if path in GET_ENDPOINTS:
            self._send_error(HTTPStatus.METHOD_NOT_ALLOWED, "Method not allowed.", "method_not_allowed")
            return
        if path not in POST_ENDPOINTS:
            self._send_error(HTTPStatus.NOT_FOUND, "Unknown endpoint.", "not_found")
            return
        try:
            payload = self._read_json_body(required=path != "/audit")
        except ValueError as exc:
            self._send_error(HTTPStatus.BAD_REQUEST, str(exc), "bad_request")
            return
        try:
            if path == "/audit":
                result = self.server.client.audit()
                result["ok"] = True
                self._send_json(result)
                return
            source = payload.get("source")
            target = payload.get("target")
            if not source or not target:
                self._send_error(HTTPStatus.BAD_REQUEST, "Request requires source and target.", "bad_request")
                return
            if path == "/query":
                answer = self.server.client.query_claim(
                    str(source),
                    str(target),
                    source_idx=_optional_int(payload.get("source_idx")),
                    target_idx=_optional_int(payload.get("target_idx")),
                )
            else:
                answer = self.server.client.submit_claim(
                    str(source),
                    str(target),
                    source_idx=_optional_int(payload.get("source_idx")),
                    target_idx=_optional_int(payload.get("target_idx")),
                    allow_construction=bool(payload.get("allow_construction", True)),
                    max_countermodel_order=_optional_int(payload.get("max_countermodel_order")),
                )
            body = answer.to_dict()
            body["ok"] = True
            self._send_json(body)
        except MathGraphAuditError as exc:
            self._send_error(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                str(exc),
                "audit_failed",
                extra={"audit": exc.audit_report},
            )
        except Exception as exc:
            self._send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc), type(exc).__name__)

    def do_PUT(self) -> None:
        self._send_error(HTTPStatus.METHOD_NOT_ALLOWED, "Method not allowed.", "method_not_allowed")

    def do_DELETE(self) -> None:
        self._send_error(HTTPStatus.METHOD_NOT_ALLOWED, "Method not allowed.", "method_not_allowed")

    def _read_json_body(self, required: bool) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length == 0:
            if required:
                raise ValueError("Request body must be JSON.")
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("Malformed JSON request body.") from exc
        if not isinstance(data, dict):
            raise ValueError("JSON request body must be an object.")
        return data

    def _send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
        self.send_response(int(status))
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _send_error(
        self,
        status: HTTPStatus,
        message: str,
        error_type: str,
        extra: dict[str, Any] | None = None,
    ) -> None:
        payload = {
            "ok": False,
            "error": message,
            "error_type": error_type,
            "warnings": list(SERVICE_WARNINGS),
        }
        if extra:
            payload.update(extra)
        self._send_json(payload, status)


def make_server(
    store_path: str,
    host: str = "127.0.0.1",
    port: int = 8765,
    working_dir: str | None = None,
    audit_after_write: bool = True,
    fail_on_critical_audit: bool = True,
    max_countermodel_order: int = 3,
) -> MathGraphHTTPServer:
    config = MathGraphClientConfig(
        store_path=store_path,
        working_dir=working_dir,
        default_max_countermodel_order=max_countermodel_order,
        audit_after_write=audit_after_write,
        fail_on_critical_audit=fail_on_critical_audit,
    )
    return MathGraphHTTPServer((host, int(port)), config)


def schema(store_path: str | None = None) -> dict[str, Any]:
    return {
        "ok": True,
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "store_path": store_path,
        "terminal_contract": True,
        "endpoints": [
            {"method": "GET", "path": "/health", "description": "Service health and terminal contract flag."},
            {"method": "GET", "path": "/stats", "description": "Read-only LawbookStore statistics."},
            {"method": "POST", "path": "/query", "description": "Read-only exact claim query; never constructs."},
            {"method": "POST", "path": "/submit", "description": "May run M0 construction and promote verified certificates."},
            {"method": "POST", "path": "/audit", "description": "Run the M0 trust-boundary audit."},
            {"method": "GET", "path": "/schema", "description": "Machine-readable endpoint list."},
            {"method": "GET", "path": "/openapi.json", "description": "Alias for /schema."},
        ],
        "request_examples": {
            "query": {"source": "(x*x)=x", "target": "(x*y)=x", "source_idx": None, "target_idx": None},
            "submit": {
                "source": "(x*x)=x",
                "target": "(x*y)=x",
                "source_idx": None,
                "target_idx": None,
                "allow_construction": True,
                "max_countermodel_order": 3,
            },
        },
        "warnings": list(SERVICE_WARNINGS),
    }


def _path(raw_path: str) -> str:
    return urlparse(raw_path).path.rstrip("/") or "/"


def _optional_int(value: Any) -> int | None:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None
