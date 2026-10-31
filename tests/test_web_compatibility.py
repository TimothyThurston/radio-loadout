"""The review endpoint shares builder validation and also protects direct downloads."""

import json

import pytest
from fastapi.testclient import TestClient

from radio_loadout.web.app import app

client = TestClient(app)


def _channel(**changes) -> dict:
    return {"name": "CALL", "receive_frequency_mhz": 146.52, "power_watts": 5, **changes}


def _review(channels):
    response = client.post("/validation/chirp.csv", data={"channels_json": json.dumps(channels)})
    assert response.status_code == 200
    return response.json()


def test_review_valid_multi_channel_loadout() -> None:
    report = _review([
        _channel(), _channel(name="WEATHER", mode="NFM", receive_only=True, scan_behavior="P"),
        _channel(name="AIR", mode="AM"),
    ])
    assert report["target"] == "chirp-generic-csv"
    assert report["compatible"] is True
    assert report["channel_count"] == 3
    assert report["issues"][0]["severity"] == "info"
    assert report["issues"][0]["channel_name"] == "WEATHER"


@pytest.mark.parametrize(("changes", "field"), [
    ({"mode": "DMR"}, "mode"),
    ({"mode": "USB"}, "mode"),
    ({"receive_frequency_mhz": -1}, "receive_frequency_mhz"),
    ({"transmit_frequency_mhz": -1}, "transmit_frequency_mhz"),
    ({"receive_frequency_mhz": float("inf")}, "receive_frequency_mhz"),
    ({"receive_frequency_mhz": 1e308}, "settings"),
    ({"name": "  "}, "settings"),
    ({"tuning_step_khz": 8.33}, "settings"),
    ({"scan_behavior": "X"}, "scan_behavior"),
    ({"power_watts": -1}, "power_watts"),
    ({"power_watts": float("inf")}, "power_watts"),
    ({"tone_mode": "tone", "tone_frequency_hz": 400}, "tone_frequency_hz"),
    ({"tone_mode": "dtcs", "dcs_code": 89}, "settings"),
    ({"dcs_polarity": "XX"}, "dcs_polarity"),
    ({"tone_mode": "cross", "transmit_tone_mode": "ctcss"}, "settings"),
])
def test_review_reports_channel_specific_errors_and_blocks_download(changes: dict, field: str) -> None:
    channels = [_channel(), _channel(**({"name": "BAD"} | changes))]
    report = _review(channels)
    assert report["compatible"] is False
    error = next(issue for issue in report["issues"] if issue["severity"] == "error")
    assert error["channel_index"] == 1
    assert error["channel_name"] == channels[1]["name"]
    assert error["field"] == field
    assert error["message"]
    response = client.post("/downloads/chirp.csv", data={"channels_json": json.dumps(channels)})
    assert response.status_code == 422


@pytest.mark.parametrize("payload", ["not-json", "{}", "null", "[]", "[null]"])
def test_invalid_document_returns_structured_report(payload: str) -> None:
    response = client.post("/validation/chirp.csv", data={"channels_json": payload})
    assert response.status_code == 200
    report = response.json()
    assert report["compatible"] is False
    assert report["issues"][0]["severity"] == "error"


def test_review_warnings_allow_download() -> None:
    channels = [_channel(power_watts=2.5555)]
    report = _review(channels)
    assert report["compatible"] is True
    assert any(issue["severity"] == "warning" for issue in report["issues"])
    assert client.post("/downloads/chirp.csv", data={"channels_json": json.dumps(channels)}).status_code == 200


def test_compatibility_panel_assets() -> None:
    page = client.get("/builder").text
    assert 'id="review-compatibility"' in page
    assert 'id="compatibility-results"' in page
    assert 'aria-live="polite"' in page
    assert 'aria-labelledby="compatibility-heading"' in page
    assert "Compatible with CHIRP Generic CSV does not guarantee support by every radio." in page
