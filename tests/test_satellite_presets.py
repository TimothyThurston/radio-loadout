"""Source-scoped RX-only definitions, generic/model review and exported TX disable."""

import csv
import json
from dataclasses import replace
from html.parser import HTMLParser
from io import StringIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from radio_loadout.exporters.chirp_csv import export_chirp_csv
from radio_loadout.importers.chirp_csv import import_chirp_csv
from radio_loadout.profile_compatibility import check_channel_compatibility
from radio_loadout.radio_profiles import BF_F8HP_PRO_V053
from radio_loadout.satellite_presets import ISS_VOICE_RX, SatelliteSource, satellite_catalog
from radio_loadout.web.app import app
from radio_loadout.web.production import create_app

client = TestClient(app)
ROOT = Path(__file__).resolve().parents[1]


def _read_catalog_fixture():
    return json.loads(
        (ROOT / "tests/fixtures/satellites/iss-voice-rx-v1.json").read_text(encoding="utf-8")
    )


def test_catalog_fixture_decoding_is_independent_of_windows_default_encoding(monkeypatch):
    original_read_text = Path.read_text

    def read_text_with_cp1252_default(path, encoding=None, errors=None):
        return original_read_text(path, encoding=encoding or "cp1252", errors=errors)

    monkeypatch.setattr(Path, "read_text", read_text_with_cp1252_default)
    assert _read_catalog_fixture() == satellite_catalog()


def test_source_checked_pack_is_nominal_voice_only_and_does_not_claim_live_or_hardware_support():
    catalog = satellite_catalog()
    assert catalog["schema_version"] == 1 and len(catalog["packs"]) == 1
    pack = catalog["packs"][0]
    assert pack["preset_id"] == "iss-voice-rx" and pack["revision"] == 1
    assert pack["frequency_sources_checked_on"] == "2026-11-06"
    assert pack["operational_status"] == "unknown-not-live-checked" and not pack["hardware_verified"]
    assert [channel["receive_frequency_hz"] for channel in pack["channels"]] == [437_800_000, 145_800_000]
    assert all(channel["mode"] == "FM" and channel["receive_only"] for channel in pack["channels"])
    assert all(channel["transmit_frequency_hz"] is None for channel in pack["channels"])
    assert all(channel["role"] == "earth-station-receive-downlink" for channel in pack["channels"])
    assert all(len(channel["draft"]["comment"]) <= 120 for channel in pack["channels"])
    assert {source["url"] for source in pack["sources"]} == {
        "https://www.ariss.org/contact-the-iss.html", "https://www.amsat.org/amateur-radio-on-the-iss/",
    }


@pytest.mark.parametrize("entry", ISS_VOICE_RX.channels, ids=lambda entry: entry.channel_id)
def test_each_entry_survives_csv_roundtrip_and_passes_documented_rx_review(entry):
    channel = entry.to_channel()
    assert channel.receive_only and channel.transmit_frequency_hz is None
    for profile in (None, BF_F8HP_PRO_V053):
        report = check_channel_compatibility([channel], profile)
        assert report.compatible
        if profile:
            assert any(issue.severity == "warning" for issue in report.issues)
    text = export_chirp_csv([channel])
    row = next(csv.DictReader(StringIO(text)))
    assert row["Duplex"] == "off" and row["Offset"] == "0.000000" and row["Tone"] == ""
    assert row["Mode"] == "FM" and "iss-voice-rx r1" in row["Comment"]
    restored = import_chirp_csv(text)[0]
    assert restored.receive_only and restored.receive_frequency_hz == entry.receive_frequency_hz
    assert export_chirp_csv([restored]) == text
    for profile in ("", BF_F8HP_PRO_V053.profile_id):
        draft = entry.to_dict()["draft"]
        # Backups/controls use blank strings; the web submission uses null for no TX.
        submitted = {"channels_json": json.dumps([{**draft, "transmit_frequency_mhz": None}]), "radio_profile_id": profile}
        assert client.post("/validation/chirp.csv", data=submitted).json()["compatible"]
        response = client.post("/downloads/chirp.csv", data=submitted)
        assert response.status_code == 200 and next(csv.DictReader(StringIO(response.text)))["Duplex"] == "off"


def test_catalog_api_is_read_only_and_returns_independent_values():
    data = client.get("/presets/satellites")
    assert data.status_code == 200 and data.json() == satellite_catalog()
    altered = data.json()
    altered["packs"][0]["channels"][0]["draft"]["receive_only"] = False
    assert client.get("/presets/satellites").json()["packs"][0]["channels"][0]["draft"]["receive_only"] is True
    assert client.post("/presets/satellites", json={}).status_code == 405


class CatalogParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.active = False
        self.text = ""

    def handle_starttag(self, tag, attrs):
        if tag == "script" and dict(attrs).get("id") == "satellite-catalog":
            self.active = True

    def handle_endtag(self, tag):
        if tag == "script":
            self.active = False

    def handle_data(self, data):
        if self.active:
            self.text += data


def test_rendered_catalog_and_committed_test_fixture_match_python_sources():
    parser = CatalogParser()
    response = client.get("/builder")
    assert response.status_code == 200
    parser.feed(response.text)
    assert json.loads(parser.text) == satellite_catalog()
    assert _read_catalog_fixture() == satellite_catalog()
    assert "not checked live" in response.text and "pass prediction" in response.text
    assert 'id="preview-satellite"' in response.text and 'id="add-satellite"' in response.text
    assert '<script src="/static/satellite-presets.js?v=1" defer>' in response.text


@pytest.mark.parametrize("changes", [
    {"channel_id": "invalid id"}, {"receive_frequency_hz": 0}, {"receive_frequency_hz": True},
    {"receive_frequency_hz": 145.8}, {"comment": "x" * 121}, {"name": ""}, {"purpose": ""},
    {"channel_id": None}, {"name": 123}, {"purpose": False}, {"comment": {}}, {"comment": "line\nbreak"},
])
def test_bad_channel_definitions_are_rejected(changes):
    with pytest.raises(ValueError):
        replace(ISS_VOICE_RX.channels[0], **changes)


@pytest.mark.parametrize("changes", [
    {"preset_id": "bad id"}, {"revision": True}, {"revision": 0}, {"frequency_sources_checked_on": "bad"},
    {"channels": ()}, {"channels": (ISS_VOICE_RX.channels[0], ISS_VOICE_RX.channels[0])}, {"sources": ()},
    {"frequency_sources_checked_on": None}, {"channels": list(ISS_VOICE_RX.channels)}, {"sources": ("not a source",)},
])
def test_bad_pack_definitions_are_rejected(changes):
    with pytest.raises(ValueError):
        replace(ISS_VOICE_RX, **changes)


def test_sources_require_https_and_locators():
    with pytest.raises(ValueError):
        SatelliteSource("Source", "http://unsafe.invalid", "Section")
    with pytest.raises(ValueError):
        SatelliteSource("Source", "https://example.invalid", "")


def test_production_controls_are_preserved_for_the_catalog_and_asset(monkeypatch):
    monkeypatch.setenv("RADIO_LOADOUT_ALLOWED_HOSTS", "testserver")
    production = TestClient(create_app())
    for path in ("/presets/satellites", "/static/satellite-presets.js"):
        response = production.get(path)
        assert response.status_code == 200 and response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
    assert production.get("/docs").status_code == 404
