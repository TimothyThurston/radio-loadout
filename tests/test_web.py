from csv import DictReader
from io import StringIO
from json import dumps

from fastapi.testclient import TestClient

from radio_loadout.web.app import app

client = TestClient(app)


def test_home() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Radio Loadout" in response.text
    assert "Open channel builder" in response.text


def test_builder_page() -> None:
    response = client.get("/builder")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Build your radio loadout" in response.text
    assert "Add another channel" in response.text
    assert "Generate CHIRP CSV" in response.text


def test_custom_chirp_download() -> None:
    channels = [
        {
            "name": "TEST RPT",
            "receive_frequency_mhz": 146.940000,
            "transmit_frequency_mhz": 146.340000,
            "mode": "FM",
            "power_watts": 5.0,
            "receive_only": False,
            "comment": "Test repeater",
        },
        {
            "name": "NOAA 7",
            "receive_frequency_mhz": 162.550000,
            "transmit_frequency_mhz": None,
            "mode": "NFM",
            "power_watts": 5.0,
            "receive_only": True,
            "comment": "Receive-only weather radio",
        },
    ]

    response = client.post(
        "/downloads/chirp.csv",
        data={"channels_json": dumps(channels)},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.headers["content-disposition"] == (
        'attachment; filename="radio_loadout_custom.csv"'
    )

    rows = list(DictReader(StringIO(response.text)))

    assert len(rows) == 2

    assert rows[0]["Name"] == "TEST RPT"
    assert rows[0]["Frequency"] == "146.940000"
    assert rows[0]["Duplex"] == "-"
    assert rows[0]["Offset"] == "0.600000"
    assert rows[0]["Mode"] == "FM"

    assert rows[1]["Name"] == "NOAA 7"
    assert rows[1]["Frequency"] == "162.550000"
    assert rows[1]["Duplex"] == "off"
    assert rows[1]["Mode"] == "NFM"


def test_chirp_sample_download() -> None:
    response = client.get("/downloads/chirp-sample.csv")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.headers["content-disposition"] == (
        'attachment; filename="radio_loadout_sample.csv"'
    )
    assert "2M CALL" in response.text
    assert "NOAA 7" in response.text