"""Strict settings definitions, evidence scope and channel/transport isolation."""

import json
from dataclasses import replace
from html.parser import HTMLParser

import pytest
from fastapi.testclient import TestClient

from radio_loadout.radio_profiles import BF_F8HP_PRO_V053
from radio_loadout.radio_settings import (
    PILOT_SETTINGS,
    SettingOption,
    settings_catalog,
    validate_setting_values,
)
from radio_loadout.web.app import app
from radio_loadout.web.production import create_app

PROFILE = BF_F8HP_PRO_V053.profile_id
client = TestClient(app)


def test_catalog_is_versioned_scoped_guidance_with_independent_support_states():
    catalog = settings_catalog(PROFILE)
    assert catalog["schema_version"] == catalog["catalog_revision"] == 1
    assert catalog["delivery"] == "manual-guidance-only"
    assert catalog["recommendation_author"] == "Radio Loadout"
    assert not catalog["hardware_verified"]
    assert catalog["radio_profile"]["support"]["programming"] == "unsupported"
    assert catalog["radio_profile"]["firmware_scope"].startswith("V0.53;")
    assert len(catalog["settings"]) == 7
    assert all(setting["manufacturer_default"] is None for setting in catalog["settings"])
    assert all(setting["default_evidence"] for setting in catalog["settings"])
    assert len({setting["setting_id"] for setting in catalog["settings"]}) == 7
    assert {"scan", "dual_watch", "power_watts"}.isdisjoint(s["setting_id"] for s in catalog["settings"])
    assert json.loads(json.dumps(catalog))["settings"][2]["recommendation"]["value"] is False


@pytest.mark.parametrize("setting", PILOT_SETTINGS, ids=lambda setting: setting.setting_id)
def test_each_recommendation_is_valid_qualified_and_does_not_set_a_default(setting):
    assert setting.validate(setting.recommendation.value) == setting.recommendation.value
    assert setting.manufacturer_default is None
    assert all((setting.explanation, setting.menu_locator, setting.source_locator,
                setting.recommendation.rationale, setting.recommendation.scenarios, setting.recommendation.tradeoffs))
    for option in setting.options:
        value = validate_setting_values(PROFILE, {setting.setting_id: option.value})
        assert type(value[setting.setting_id]) is type(option.value)


@pytest.mark.parametrize("values", [
    {"squelch": True}, {"squelch": "2"}, {"squelch": 2.0}, {"squelch": -1}, {"squelch": 9},
    {"vox": 0}, {"vox": "false"}, {"vox": None}, {"timeout_seconds": 61},
    {"timeout_seconds": False}, {"timeout_seconds": float("nan")},
    {"backlight_seconds": 10}, {"backlight_seconds": "20"}, {"backlight_seconds": []},
    {"unknown_setting": 1}, {"__proto__": "bad"}, [], None, "{}",
])
def test_invalid_types_ranges_and_unknowns_are_rejected_without_mutation(values):
    before = repr(values)
    with pytest.raises(ValueError):
        validate_setting_values(PROFILE, values)
    assert repr(values) == before


def test_partial_plan_and_no_value_coercion_or_default_injection():
    values = {"vox": False, "timeout_seconds": 0}
    assert validate_setting_values(PROFILE, values) == values
    assert validate_setting_values(PROFILE, {}) == {}
    assert not next(s for s in PILOT_SETTINGS if s.setting_id == "backlight_seconds").options_exhaustive
    catalog = settings_catalog(PROFILE)
    catalog["settings"][0]["recommendation"]["value"] = 8
    assert settings_catalog(PROFILE)["settings"][0]["recommendation"]["value"] == 2


@pytest.mark.parametrize("profile", ["", "uv-5r", "bf-f8hp", "baofeng-bf-f8hp-pro-v044-us", "x" * 81])
def test_other_model_or_firmware_never_inherits_settings(profile):
    with pytest.raises(ValueError):
        settings_catalog(profile)
    assert client.get(f"/radio-profiles/{profile or 'generic'}/settings").status_code == 404
    if profile:
        assert client.get("/radio-settings", params={"profile_id": profile}).status_code == 404


@pytest.mark.parametrize("changes", [
    {"setting_id": "bad-id"}, {"label": ""}, {"options": ()},
    {"options": (SettingOption(2, "Two"), SettingOption(2, "Duplicate"))},
    {"manufacturer_default": 99}, {"recommendation": replace(PILOT_SETTINGS[0].recommendation, value=True)},
    {"recommendation": replace(PILOT_SETTINGS[0].recommendation, revision=0)},
])
def test_bad_definitions_fail_at_construction(changes):
    with pytest.raises(ValueError):
        replace(PILOT_SETTINGS[0], **changes)


@pytest.mark.parametrize("value", [None, 2.5, {}, []])
def test_option_types_are_explicit(value):
    with pytest.raises(ValueError):
        SettingOption(value, "Invalid")


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.catalog = ""
        self.in_catalog = False
        self.selected = {}
        self.current_select = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "script" and attrs.get("id") == "settings-catalog":
            self.in_catalog = True
        if tag == "select":
            self.current_select = attrs.get("id")
        if tag == "option" and "selected" in attrs and (self.current_select or "").startswith("proposed-"):
            self.selected[self.current_select] = json.loads(attrs["value"])

    def handle_endtag(self, tag):
        if tag == "script":
            self.in_catalog = False
        if tag == "select":
            self.current_select = None

    def handle_data(self, data):
        if self.in_catalog:
            self.catalog += data


def test_page_and_api_share_exact_typed_catalog_and_render_recommendations():
    api = client.get(f"/radio-profiles/{PROFILE}/settings")
    assert api.status_code == 200 and api.json() == json.loads(json.dumps(settings_catalog(PROFILE)))
    response = client.get("/radio-settings", params={"profile_id": PROFILE})
    assert response.status_code == 200
    page = Page()
    page.feed(response.text)
    assert json.loads(page.catalog) == api.json()
    for setting in PILOT_SETTINGS:
        assert page.selected[f"proposed-{setting.setting_id}"] == setting.recommendation.value
        assert type(page.selected[f"proposed-{setting.setting_id}"]) is type(setting.recommendation.value)
    assert "No device connection" in response.text and "Session-only" in response.text
    assert 'data-current disabled' in response.text  # Fail closed without JS.
    assert '<p id="settings-js-required">JavaScript is required' in response.text
    assert '<noscript>' not in response.text  # Fallback does not depend on browser scripting/parser flags.
    assert client.post(f"/radio-profiles/{PROFILE}/settings", json={"vox": True}).status_code == 405


def test_generic_page_does_not_assume_radio_or_autoapply_suggestions():
    page = client.get("/radio-settings").text
    assert "No radio is selected" in page
    assert 'id="settings-catalog"' not in page
    assert 'src="/static/radio-settings.js' not in page
    assert 'href="/radio-settings"' in client.get("/builder").text


def test_settings_do_not_enter_channel_transport_csv_or_backup_schema():
    channel = {"name": "TEST", "receive_frequency_mhz": 146.52}
    data = {"channels_json": json.dumps([channel])}
    before = client.post("/downloads/chirp.csv", data=data).content
    client.get("/radio-settings", params={"profile_id": PROFILE})
    assert client.post("/downloads/chirp.csv", data=data).content == before
    assert client.post("/downloads/chirp.csv", data={**data, "settings_json": "{}"}).status_code == 422
    backup = client.get("/static/backup-format.js").text
    assert "timeout_seconds" not in backup and "radio_settings" not in backup


def test_production_boundaries_and_local_assets_remain_in_effect(monkeypatch):
    monkeypatch.setenv("RADIO_LOADOUT_ALLOWED_HOSTS", "testserver")
    production = TestClient(create_app())
    for path in (f"/radio-profiles/{PROFILE}/settings", f"/radio-settings?profile_id={PROFILE}",
                 "/static/settings-plan.js", "/static/radio-settings.js"):
        response = production.get(path)
        assert response.status_code == 200
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
    assert production.get("/docs").status_code == 404
