"""Runtime v2 editor contracts and fixture/source consistency; no device claims."""

import json
from html.parser import HTMLParser
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from radio_loadout.radio_settings import settings_catalog
from radio_loadout.web.app import app

ROOT = Path(__file__).resolve().parents[1]
client = TestClient(app)


def test_committed_catalog_fixture_matches_current_exact_python_catalog():
    fixture = json.loads((ROOT / "tests/fixtures/loadouts/catalog-v1.json").read_text())
    assert fixture == json.loads(json.dumps(settings_catalog("baofeng-bf-f8hp-pro-v053-us")))


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.scripts = []
        self.fieldsets = []
        self.settings_names = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if "id" in values:
            self.ids.append(values["id"])
        if tag == "script" and "src" in values:
            self.scripts.append(values["src"].split("?")[0])
        if tag == "fieldset":
            self.fieldsets.append(values)
        if tag in {"input", "select"} and any(key.startswith("data-current") for key in values):
            self.settings_names.append(values.get("name"))


def test_builder_has_one_editor_with_safe_script_order_and_no_submitted_settings_controls():
    response = client.get("/builder")
    assert response.status_code == 200
    parsed = Page()
    parsed.feed(response.text)
    assert len(parsed.ids) == len(set(parsed.ids))
    assert parsed.scripts == ["/static/backup-format.js", "/static/settings-plan.js", "/static/loadout-format.js",
                              "/static/radio-settings.js", "/static/builder.js"]
    fieldset = next(item for item in parsed.fieldsets if item.get("id") == "builder-settings")
    assert "hidden" in fieldset and "disabled" in fieldset
    assert len(parsed.settings_names) == 7 and set(parsed.settings_names) == {None}
    assert 'id="export-loadout"' in response.text
    assert "Settings are not autosaved" in response.text


def test_standalone_guide_and_builder_use_the_same_editor_and_catalog():
    guide = client.get("/radio-settings?profile_id=baofeng-bf-f8hp-pro-v053-us")
    builder = client.get("/builder")
    for response in (guide, builder):
        assert response.status_code == 200
        assert response.text.count('id="current-vox"') == 1
        assert response.text.count('id="settings-catalog"') == 1
    template = (ROOT / "src/radio_loadout/web/templates").resolve()
    assert '{% include "settings-editor.html" %}' in (template / "radio-settings.html").read_text()
    assert '{% include "settings-editor.html" %}' in (template / "builder.html").read_text()


@pytest.mark.parametrize("name", ["loadout-format.js", "settings-plan.js", "radio-settings.js"])
def test_runtime_scripts_are_local_and_available(name):
    response = client.get("/static/" + name)
    assert response.status_code == 200
    assert "javascript" in response.headers["content-type"]
    assert response.content


def test_v1_file_contract_is_not_extended_with_profile_or_settings_fields():
    source = client.get("/static/backup-format.js").text
    assert "radio_profile" not in source and "settings_plan" not in source
    assert "version: 1" in source


def test_v2_file_metadata_is_never_a_channel_export_form_field():
    for route in ("/validation/chirp.csv", "/downloads/chirp.csv"):
        response = client.post(route, data={"channels_json": json.dumps([
            {"name": "TEST", "receive_frequency_mhz": 146.52},
        ]), "settings_plan": "{}"})
        assert response.status_code == 422
