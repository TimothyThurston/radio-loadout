"""Tests for the Radio Loadout web application."""

import csv
import json
from io import StringIO

from fastapi.testclient import TestClient

from radio_loadout.web.app import app

client = TestClient(app)


def _read_csv_response(response_text: str) -> list[dict[str, str]]:
    return list(csv.DictReader(StringIO(response_text)))


def test_home() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Radio Loadout" in response.text


def test_builder_page() -> None:
    response = client.get("/builder")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Build your radio loadout" in response.text
    assert "Generate CHIRP CSV" in response.text
    assert "Tuning step (kHz)" in response.text
    assert "Scan behavior" in response.text
    assert "data-move-channel-up" in response.text
    assert "data-move-channel-down" in response.text
    assert "data-duplicate-channel" in response.text


def test_chirp_sample_download() -> None:
    response = client.get("/downloads/chirp-sample.csv")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.headers["content-disposition"] == (
        'attachment; filename="radio_loadout_sample.csv"'
    )

    rows = _read_csv_response(response.text)

    assert len(rows) == 4
    assert rows[0]["Name"] == "2M CALL"
    assert rows[0]["Frequency"] == "146.520000"
    assert rows[0]["TStep"] == "5.00"
    assert rows[0]["Skip"] == ""

    assert rows[3]["Name"] == "NOAA 7"
    assert rows[3]["Frequency"] == "162.550000"
    assert rows[3]["Duplex"] == "off"
    assert rows[3]["Mode"] == "NFM"
    assert rows[3]["Skip"] == "P"


def test_custom_chirp_download() -> None:
    channels = [
        {
            "name": "TEST RPT",
            "receive_frequency_mhz": 146.94,
            "transmit_frequency_mhz": 146.34,
            "mode": "FM",
            "power_watts": 5.0,
            "receive_only": False,
            "tone_mode": "tone",
            "tone_frequency_hz": 100.0,
            "comment": "Radio Loadout custom channel",
        },
        {
            "name": "NOAA 7",
            "receive_frequency_mhz": 162.55,
            "transmit_frequency_mhz": None,
            "mode": "NFM",
            "power_watts": 5.0,
            "receive_only": True,
            "tone_mode": "none",
            "tone_frequency_hz": None,
            "comment": "Receive-only weather radio",
        },
    ]

    response = client.post(
        "/downloads/chirp.csv",
        data={"channels_json": json.dumps(channels)},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.headers["content-disposition"] == (
        'attachment; filename="radio_loadout_custom.csv"'
    )

    rows = _read_csv_response(response.text)

    assert len(rows) == 2

    assert rows[0]["Name"] == "TEST RPT"
    assert rows[0]["Frequency"] == "146.940000"
    assert rows[0]["Duplex"] == "-"
    assert rows[0]["Offset"] == "0.600000"
    assert rows[0]["Mode"] == "FM"
    assert rows[0]["Tone"] == "Tone"
    assert rows[0]["rToneFreq"] == "100.0"
    assert rows[0]["TStep"] == "5.00"
    assert rows[0]["Skip"] == ""

    assert rows[1]["Name"] == "NOAA 7"
    assert rows[1]["Frequency"] == "162.550000"
    assert rows[1]["Duplex"] == "off"
    assert rows[1]["Mode"] == "NFM"


def test_custom_dcs_chirp_download() -> None:
    channels = [
        {
            "name": "DCS TEST",
            "receive_frequency_mhz": 444.5,
            "transmit_frequency_mhz": 449.5,
            "mode": "FM",
            "power_watts": 5.0,
            "receive_only": False,
            "tone_mode": "dtcs",
            "dcs_code": 23,
            "dcs_polarity": "NR",
            "comment": "Matched DCS test",
        }
    ]

    response = client.post(
        "/downloads/chirp.csv",
        data={"channels_json": json.dumps(channels)},
    )

    assert response.status_code == 200

    rows = _read_csv_response(response.text)

    assert len(rows) == 1
    assert rows[0]["Name"] == "DCS TEST"
    assert rows[0]["Tone"] == "DTCS"
    assert rows[0]["DtcsCode"] == "023"
    assert rows[0]["RxDtcsCode"] == "023"
    assert rows[0]["DtcsPolarity"] == "NR"


def test_custom_cross_tone_download() -> None:
    channels = [
        {
            "name": "CROSS TEST",
            "receive_frequency_mhz": 146.94,
            "transmit_frequency_mhz": 146.34,
            "mode": "FM",
            "power_watts": 5.0,
            "receive_only": False,
            "tone_mode": "cross",
            "transmit_tone_mode": "ctcss",
            "transmit_ctcss_frequency_hz": 100.0,
            "transmit_dcs_polarity": "N",
            "receive_tone_mode": "dcs",
            "receive_dcs_code": 23,
            "receive_dcs_polarity": "R",
            "comment": "Cross tone test",
        }
    ]

    response = client.post(
        "/downloads/chirp.csv",
        data={"channels_json": json.dumps(channels)},
    )

    assert response.status_code == 200

    rows = _read_csv_response(response.text)

    assert len(rows) == 1
    assert rows[0]["Name"] == "CROSS TEST"
    assert rows[0]["Tone"] == "Cross"
    assert rows[0]["rToneFreq"] == "100.0"
    assert rows[0]["RxDtcsCode"] == "023"
    assert rows[0]["DtcsPolarity"] == "NR"
    assert rows[0]["CrossMode"] == "Tone->DTCS"


def test_custom_tuning_step_and_scan_behavior() -> None:
    channels = [
        {
            "name": "SCAN TEST",
            "receive_frequency_mhz": 446.0,
            "transmit_frequency_mhz": 446.0,
            "mode": "FM",
            "power_watts": 5.0,
            "receive_only": False,
            "tone_mode": "none",
            "tuning_step_khz": 12.5,
            "scan_behavior": "S",
            "comment": "Skipped during scanning",
        }
    ]

    response = client.post(
        "/downloads/chirp.csv",
        data={"channels_json": json.dumps(channels)},
    )

    assert response.status_code == 200

    rows = _read_csv_response(response.text)

    assert len(rows) == 1
    assert rows[0]["Name"] == "SCAN TEST"
    assert rows[0]["TStep"] == "12.50"
    assert rows[0]["Skip"] == "S"