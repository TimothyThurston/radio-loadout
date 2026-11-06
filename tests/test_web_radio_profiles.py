"""Profile review/download parity, strict transport fields and generic compatibility."""

import json

import pytest
from fastapi.testclient import TestClient

from radio_loadout.compatibility import check_chirp_compatibility
from radio_loadout.radio_profiles import BF_F8HP_PRO_V053
from radio_loadout.web.app import app

client = TestClient(app)
PROFILE_ID = BF_F8HP_PRO_V053.profile_id
CHANNEL = {"name": "TEST", "receive_frequency_mhz": 146.52, "power_watts": 5.0}


def submitted(channels=None, profile=PROFILE_ID):
    data = {"channels_json": json.dumps([CHANNEL] if channels is None else channels)}
    if profile is not None:
        data["radio_profile_id"] = profile
    return data


def test_catalog_and_builder_label_documented_pilot_without_hardware_claims():
    response = client.get("/radio-profiles")
    assert response.status_code == 200
    profile = response.json()["profiles"][0]
    assert profile["profile_id"] == PROFILE_ID and not profile["hardware_verified"]
    assert profile["support"]["programming"] == "unsupported"
    page = client.get("/builder").text
    assert 'id="radio-profile" name="radio_profile_id"' in page
    assert "documented pilot" in page and "session-only" in page


def test_generic_review_and_csv_bytes_are_identical_when_profile_omitted_or_empty():
    a = client.post("/validation/chirp.csv", data=submitted(profile=None)).json()
    b = client.post("/validation/chirp.csv", data=submitted(profile="")).json()
    assert a == b and "radio_profile" not in a
    assert client.post("/downloads/chirp.csv", data=submitted(profile=None)).content == client.post("/downloads/chirp.csv", data=submitted(profile="")).content


def test_profile_pass_has_warnings_metadata_and_same_generic_csv_without_data_mutation():
    data = submitted()
    before = dict(data)
    report = client.post("/validation/chirp.csv", data=data).json()
    assert report["compatible"] and report["radio_profile"]["profile_id"] == PROFILE_ID
    assert any(i["severity"] == "warning" for i in report["issues"])
    download = client.post("/downloads/chirp.csv", data=data)
    assert download.status_code == 200
    assert download.content == client.post("/downloads/chirp.csv", data=submitted(profile=None)).content
    assert data == before


@pytest.mark.parametrize("channel", [
    {**CHANNEL, "transmit_frequency_mhz": 162.55},
    {**CHANNEL, "receive_frequency_mhz": 88.0, "receive_only": True},
    {**CHANNEL, "power_watts": 25.0},
    {**CHANNEL, "mode": "AM"},
])
def test_direct_download_cannot_bypass_profile_errors(channel):
    data = submitted([channel])
    response = client.post("/validation/chirp.csv", data=data)
    assert response.status_code == 200 and not response.json()["compatible"]
    assert client.post("/downloads/chirp.csv", data=data).status_code == 422
    # The same input remains format-valid when the user explicitly chooses generic.
    assert client.post("/downloads/chirp.csv", data=submitted([channel], profile=None)).status_code == 200


@pytest.mark.parametrize("route", ["/validation/chirp.csv", "/downloads/chirp.csv"])
@pytest.mark.parametrize("profile", ["uv-5r", "bf-f8hp", "baofeng-bf-f8hp-pro-v044-us", "x" * 81])
def test_unknown_or_oversized_profile_ids_never_fall_back(route, profile):
    assert client.post(route, data=submitted(profile=profile)).status_code == 422


@pytest.mark.parametrize("route", ["/validation/chirp.csv", "/downloads/chirp.csv"])
def test_duplicate_unexpected_and_file_fields_cannot_expand_transport(route):
    for body in [
        "channels_json=%5B%5D&radio_profile_id=&radio_profile_id=",
        "channels_json=%5B%5D&unexpected=value",
        "channels_json=%5B%5D&channels_json=%5B%5D",
    ]:
        assert client.post(route, content=body, headers={"content-type": "application/x-www-form-urlencoded"}).status_code in (400, 422)
    assert client.post(route, data=submitted(), files={"extra": ("extra.txt", b"not allowed")}).status_code == 400


def test_invalid_channel_report_retains_requested_profile_context():
    response = client.post("/validation/chirp.csv", data=submitted([{**CHANNEL, "receive_frequency_mhz": -1}]))
    assert response.status_code == 200 and not response.json()["compatible"]
    assert response.json()["radio_profile"]["profile_id"] == PROFILE_ID


def test_backup_format_remains_version_one_without_profile_metadata():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    source = (root / "src/radio_loadout/web/static/backup-format.js").read_text()
    assert "radio_profile_id" not in source
    assert check_chirp_compatibility([]).to_dict()["target"] == "chirp-generic-csv"
