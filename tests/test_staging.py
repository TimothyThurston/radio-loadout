"""Production-only host/header/error controls and local staging smoke coverage."""

import logging
import os
import socket
import subprocess
import sys
import threading
import time
import traceback
from pathlib import Path

import pytest
import uvicorn
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from radio_loadout.web.app import app
from radio_loadout.web.production import ProductionBoundary, allowed_hosts, create_app
from radio_loadout.web.serve import server_options


@pytest.fixture
def staging(monkeypatch):
    monkeypatch.setenv("RADIO_LOADOUT_ALLOWED_HOSTS", "testserver,stage.example.invalid")
    return TestClient(create_app())


def test_health_is_minimal(staging, monkeypatch) -> None:
    monkeypatch.setenv("SECRET_TEST_VALUE", "DO-NOT-EXPOSE")
    response = staging.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert "DO-NOT-EXPOSE" not in response.text
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.parametrize("path", ["/", "/builder", "/static/builder.js", "/static/backup-format.js", "/downloads/chirp-sample.csv", "/missing"])
def test_security_headers_preserve_assets_and_downloads(staging, path) -> None:
    response = staging.get(path)
    assert response.status_code == (404 if path == "/missing" else 200)
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert "content-security-policy" not in response.headers  # Do not break existing Swagger CDN/JSON scripts.
    if path.endswith(".js"):
        assert "javascript" in response.headers["content-type"]
        assert response.content
    elif "sample.csv" in path:
        assert 'filename="radio_loadout_sample.csv"' in response.headers["content-disposition"]
        assert response.text.startswith("Location,Name,Frequency")
    if not path.startswith("/static/"):
        assert response.headers["cache-control"] == "no-store"


def test_hosts_are_enforced_even_with_spoofed_forwarded_headers(staging) -> None:
    assert staging.get("/healthz", headers={"Host": "stage.example.invalid:8000"}).status_code == 200
    response = staging.get("/healthz", headers={"Host": "attacker.invalid", "X-Forwarded-Host": "stage.example.invalid"})
    assert response.status_code == 400
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "attacker.invalid" not in response.text


@pytest.mark.parametrize("value", ["*", "", "stage.invalid,", "https://stage.invalid", "stage.invalid:8000", "*.stage.invalid"])
def test_invalid_allowed_hosts_fail_startup(value) -> None:
    with pytest.raises(ValueError, match="exact DNS names"):
        allowed_hosts(value)


def test_debug_mode_cannot_enter_staging(monkeypatch) -> None:
    monkeypatch.setattr(app, "debug", True)
    with pytest.raises(ValueError, match="debug mode"):
        create_app()


def test_unhandled_errors_do_not_disclose_or_log_payloads(caplog) -> None:
    backend = FastAPI()
    @backend.get("/failure")
    def failure():
        raise ValueError("PRIVATE-CHANNEL-AND-PRECISE-LOCATION")
    with caplog.at_level(logging.ERROR, logger="radio_loadout.production"):
        response = TestClient(ProductionBoundary(backend)).get("/failure")
    assert response.status_code == 500
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["cache-control"] == "no-store"
    assert "PRIVATE-CHANNEL" not in response.text + caplog.text
    assert "Traceback" not in response.text + caplog.text
    assert "ValueError" in caplog.text


def test_server_defaults_are_bounded_and_do_not_trust_forwarded_headers(monkeypatch) -> None:
    for key in list(os.environ):
        if key.startswith("RADIO_LOADOUT_") or key in {"HOST", "PORT"}:
            monkeypatch.delenv(key)
    options = server_options()
    assert options["host"] == "0.0.0.0" and options["port"] == 8000
    assert options["proxy_headers"] is False and options["forwarded_allow_ips"] == ""
    assert options["access_log"] is False and options["reload"] is False
    assert options["server_header"] is False and options["workers"] == 1
    assert options["limit_concurrency"] == 16
    assert options["timeout_keep_alive"] == 5 and options["timeout_graceful_shutdown"] == 30


@pytest.mark.parametrize(("name", "value"), [("PORT", "0"), ("PORT", "65536"), ("PORT", "bad"),
                                           ("HOST", "not-a-bind-address"),
                                           ("RADIO_LOADOUT_CONCURRENCY", "0"),
                                           ("RADIO_LOADOUT_FORWARDED_ALLOW_IPS", "*"),
                                           ("RADIO_LOADOUT_FORWARDED_ALLOW_IPS", "0.0.0.0/0"),
                                           ("RADIO_LOADOUT_FORWARDED_ALLOW_IPS", "::/0"),
                                           ("RADIO_LOADOUT_FORWARDED_ALLOW_IPS", "proxy.example.invalid")])
def test_invalid_server_configuration_fails(name, value, monkeypatch) -> None:
    monkeypatch.setenv(name, value)
    with pytest.raises(ValueError, match=name):
        server_options()


@pytest.mark.parametrize("name", ["PORT", "HOST", "RADIO_LOADOUT_FORWARDED_ALLOW_IPS"])
def test_startup_errors_do_not_echo_invalid_environment_values(name, monkeypatch) -> None:
    monkeypatch.setenv(name, "PRIVATE-CONFIGURATION-VALUE")
    with pytest.raises(ValueError) as error:
        server_options()
    assert "PRIVATE-CONFIGURATION-VALUE" not in "".join(traceback.format_exception(error.value))


def test_only_explicit_proxy_addresses_can_supply_client_and_scheme(monkeypatch) -> None:
    monkeypatch.setenv("RADIO_LOADOUT_FORWARDED_ALLOW_IPS", "127.0.0.1")
    options = server_options()
    backend = FastAPI()
    @backend.get("/request")
    def request_info(request: Request):
        return {"scheme": request.url.scheme, "client": request.client.host}
    wrapped = ProxyHeadersMiddleware(backend, trusted_hosts=options["forwarded_allow_ips"])
    headers = {"X-Forwarded-For": "192.0.2.10", "X-Forwarded-Proto": "https"}
    trusted = TestClient(wrapped, client=("127.0.0.1", 1234)).get("/request", headers=headers)
    assert trusted.json() == {"scheme": "https", "client": "192.0.2.10"}
    untrusted = TestClient(wrapped, client=("192.0.2.99", 1234)).get("/request", headers=headers)
    assert untrusted.json() == {"scheme": "http", "client": "192.0.2.99"}


def test_local_staging_smoke_checks_full_workflow_and_real_upload_limits() -> None:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
        server = uvicorn.Server(uvicorn.Config(create_app(), log_level="warning", access_log=False, lifespan="off"))
        thread = threading.Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
        thread.start()
        try:
            deadline = time.monotonic() + 10
            while not server.started:
                assert thread.is_alive() and time.monotonic() < deadline
                threading.Event().wait(0.05)
            script = Path(__file__).resolve().parents[1] / "scripts/staging_smoke.py"
            result = subprocess.run([sys.executable, str(script), "--base-url", f"http://127.0.0.1:{port}"],
                                    capture_output=True, text=True, timeout=45, check=True)
            assert "all three oversized-input rejections" in result.stdout
        finally:
            server.should_exit = True
            thread.join(timeout=10)
            assert not thread.is_alive()
