from csv import DictReader
from io import StringIO

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
    assert "Create your first custom channel" in response.text
    assert "Generate CHIRP CSV" in response.text


def test_custom_chirp_download() -> None:
    response = client.post(
        "/downloads/chirp.csv",
        data={
            "name": "TEST RPT",
            "receive_frequency_mhz": "146.940000",
            "transmit_frequency_mhz": "146.340000",
            "mode": "FM",
            "power_watts": "5.0",
            "comment": "Radio Loadout custom export test",
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.headers["content-disposition"] == (
        'attachment; filename="radio_loadout_custom.csv"'
    )

    row = next(DictReader(StringIO(response.text)))

    assert row["Name"] == "TEST RPT"
    assert row["Frequency"] == "146.940000"
    assert row["Duplex"] == "-"
    assert row["Offset"] == "0.600000"
    assert row["Mode"] == "FM"
    assert row["Power"] == "5.0W"


def test_chirp_sample_download() -> None:
    response = client.get("/downloads/chirp-sample.csv")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.headers["content-disposition"] == (
        'attachment; filename="radio_loadout_sample.csv"'
    )
    assert "2M CALL" in response.text
    assert "NOAA 7" in response.text