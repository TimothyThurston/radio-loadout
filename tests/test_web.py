from fastapi.testclient import TestClient

from radio_loadout.web.app import app

client = TestClient(app)


def test_home() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Radio Loadout" in response.text
    assert "Download CHIRP sample" in response.text


def test_chirp_sample_download() -> None:
    response = client.get("/downloads/chirp-sample.csv")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.headers["content-disposition"] == (
        'attachment; filename="radio_loadout_sample.csv"'
    )
    assert "2M CALL" in response.text
    assert "NOAA 7" in response.text