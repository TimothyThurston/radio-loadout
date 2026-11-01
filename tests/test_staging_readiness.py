"""Deterministic startup retries must never turn permanent failures into success."""

import importlib
import json
import sys
from http.client import IncompleteRead, RemoteDisconnected
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
from urllib.error import HTTPError, URLError

import pytest


class Clock:
    def __init__(self):
        self.now = 0.0
        self.pauses = []

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.pauses.append(seconds)
        self.now += seconds


class HealthResponse(BytesIO):
    def __init__(self, status=200, body=b'{"status":"ok"}'):
        super().__init__(body)
        self.status = status


@pytest.fixture
def readiness(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    module = importlib.import_module("staging_smoke")
    clock, open_request, verify = Clock(), Mock(), Mock()
    monkeypatch.setattr(module, "time", clock)
    monkeypatch.setattr(module, "build_opener", lambda *args: SimpleNamespace(open=open_request))
    monkeypatch.setattr(module, "verify_staging", verify)
    monkeypatch.setattr(sys, "argv", ["staging_smoke.py", "--wait-seconds", "0.25"])
    return module, clock, open_request, verify


@pytest.mark.parametrize("failure", [
    ConnectionResetError(104, "startup reset"), RemoteDisconnected("early EOF"),
    IncompleteRead(b"partial", 10), ConnectionAbortedError("aborted"),
    ConnectionRefusedError("refused"), BrokenPipeError("closed during write"),
    TimeoutError("startup timeout"), URLError(ConnectionRefusedError("wrapped refusal")),
    URLError(ConnectionResetError(104, "wrapped reset")),
])
def test_transient_disconnect_then_healthy_response_runs_smoke(readiness, failure) -> None:
    module, clock, open_request, verify = readiness
    open_request.side_effect = [failure, HealthResponse()]
    module.main()
    assert open_request.call_count == 2
    assert clock.now == pytest.approx(0.1)
    verify.assert_called_once()


@pytest.mark.parametrize("failure_class", [ConnectionResetError, RemoteDisconnected])
def test_repeated_disconnects_stop_at_deadline_and_report_final_error(readiness, failure_class) -> None:
    module, clock, open_request, verify = readiness
    failures = [failure_class(f"startup failure {number}") for number in (1, 2, 3)]
    open_request.side_effect = [*failures, HealthResponse()]
    with pytest.raises(RuntimeError, match=f"Final connection error: {failure_class.__name__}: startup failure 3") as error:
        module.main()
    assert error.value.__cause__ is failures[-1]
    assert clock.now == pytest.approx(0.25)
    assert clock.pauses == pytest.approx([0.1, 0.1, 0.05])
    assert [call.kwargs["timeout"] for call in open_request.call_args_list] == pytest.approx([0.25, 0.15, 0.05])
    assert open_request.call_count == 3
    verify.assert_not_called()


@pytest.mark.parametrize("status", [400, 401, 404, 500, 503])
def test_http_errors_fail_immediately_without_running_smoke(readiness, status) -> None:
    module, clock, open_request, verify = readiness
    failure = HTTPError("http://127.0.0.1:8000/healthz", status, "permanent HTTP failure", {}, None)
    open_request.side_effect = failure
    with pytest.raises(HTTPError) as error:
        module.main()
    assert error.value is failure
    assert open_request.call_count == 1
    assert clock.pauses == []
    verify.assert_not_called()


@pytest.mark.parametrize("failure", [URLError(PermissionError("denied")), URLError("invalid configuration"),
                                     ValueError("invalid port"), OSError("unexpected OS failure")])
def test_permanent_configuration_errors_are_not_retried_or_hidden(readiness, failure) -> None:
    module, clock, open_request, verify = readiness
    open_request.side_effect = failure
    with pytest.raises(type(failure)) as error:
        module.main()
    assert error.value is failure
    assert open_request.call_count == 1
    assert clock.pauses == []
    verify.assert_not_called()


@pytest.mark.parametrize(("response", "error_class"), [
    (HealthResponse(status=503), AssertionError),
    (HealthResponse(body=b'{"status":"down"}'), AssertionError),
    (HealthResponse(body=b"invalid JSON"), json.JSONDecodeError),
])
def test_invalid_health_responses_do_not_pass_or_retry(readiness, response, error_class) -> None:
    module, clock, open_request, verify = readiness
    open_request.return_value = response
    with pytest.raises(error_class):
        module.main()
    assert open_request.call_count == 1
    assert clock.pauses == []
    verify.assert_not_called()


def test_healthy_response_after_deadline_cannot_pass(readiness) -> None:
    module, clock, open_request, verify = readiness
    def late_response(*args, **kwargs):
        clock.now += kwargs["timeout"] + 0.01
        return HealthResponse()
    open_request.side_effect = late_response
    with pytest.raises(RuntimeError, match="Health response arrived after the readiness deadline"):
        module.main()
    assert open_request.call_count == 1
    assert clock.pauses == []
    verify.assert_not_called()


@pytest.mark.parametrize("seconds", [0, -1, float("nan"), float("inf")])
def test_readiness_budget_must_be_finite_and_positive(readiness, seconds) -> None:
    module, _, open_request, verify = readiness
    with pytest.raises(ValueError, match="finite, positive"):
        module.wait_for_health("http://127.0.0.1:8000", seconds)
    open_request.assert_not_called()
    verify.assert_not_called()


def test_workflow_failure_after_readiness_is_not_suppressed(readiness) -> None:
    module, clock, open_request, verify = readiness
    open_request.return_value = HealthResponse()
    verify.side_effect = AssertionError("CSV export is incorrect")
    with pytest.raises(AssertionError, match="CSV export is incorrect"):
        module.main()
    assert clock.pauses == []
    assert open_request.call_count == 1
    verify.assert_called_once()
