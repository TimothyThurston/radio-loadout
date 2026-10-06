import csv
import io
import json

from fastapi.testclient import TestClient

from radio_loadout.web.app import app

client = TestClient(app)


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
    assert 'id="channel-form"' in response.text
    assert "DCS / DTCS" in response.text


def test_chirp_sample_download() -> None:
    response = client.get("/downloads/chirp-sample.csv")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.headers["content-disposition"] == (
        'attachment; filename="radio_loadout_sample.csv"'
    )
    assert "2M CALL" in response.text
    assert "NOAA 7" in response.text


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
            "dcs_code": None,
            "comment": "Test repeater",
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
            "dcs_code": None,
            "comment": "Weather radio",
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

    rows = list(
        csv.DictReader(
            io.StringIO(response.text)
        )
    )

    assert len(rows) == 2

    assert rows[0]["Name"] == "TEST RPT"
    assert rows[0]["Frequency"] == "146.940000"
    assert rows[0]["Duplex"] == "-"
    assert rows[0]["Offset"] == "0.600000"
    assert rows[0]["Mode"] == "FM"
    assert rows[0]["Tone"] == "Tone"
    assert rows[0]["rToneFreq"] == "100.0"

    assert rows[1]["Name"] == "NOAA 7"
    assert rows[1]["Frequency"] == "162.550000"
    assert rows[1]["Duplex"] == "off"
    assert rows[1]["Mode"] == "NFM"


def test_custom_dcs_chirp_download() -> None:
    channels = [
        {
            "name": "DCS TEST",
            "receive_frequency_mhz": 146.94,
            "transmit_frequency_mhz": 146.94,
            "mode": "FM",
            "power_watts": 5.0,
            "receive_only": False,
            "tone_mode": "dtcs",
            "tone_frequency_hz": None,
            "dcs_code": 23,
            "comment": "Radio Loadout DCS test",
        }
    ]

    response = client.post(
        "/downloads/chirp.csv",
        data={"channels_json": json.dumps(channels)},
    )

    assert response.status_code == 200

    rows = list(
        csv.DictReader(
            io.StringIO(response.text)
        )
    )

    assert len(rows) == 1
    assert rows[0]["Name"] == "DCS TEST"
    assert rows[0]["Frequency"] == "146.940000"
    assert rows[0]["Tone"] == "DTCS"
    assert int(rows[0]["DtcsCode"]) == 23
    assert int(rows[0]["RxDtcsCode"]) == 23
    assert rows[0]["DtcsPolarity"] == "NN"