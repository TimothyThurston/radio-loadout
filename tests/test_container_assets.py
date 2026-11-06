"""Guard explicit runtime-asset declarations; not an emulator of Docker matching."""

import importlib
from pathlib import Path, PurePosixPath

import pytest

ROOT = Path(__file__).resolve().parents[1]


def check_explicit_asset_rules(rules, payload):
    # Keep the reviewed allowlist shape; don't replace it with broad static globs.
    assert rules[0] == "**"
    assert all(rule.startswith("!") for rule in rules[1:])
    for name in payload:
        if not name.startswith("radio_loadout/web/") or PurePosixPath(name).suffix == ".py":
            continue
        relative = PurePosixPath("src") / name
        assert f"!{relative}" in rules, f"Runtime asset lacks explicit container declaration: {relative}"
        for parent in relative.parents:
            if parent != PurePosixPath("."):
                assert f"!{parent}/" in rules, f"Missing explicit ancestor declaration: {parent}"


@pytest.fixture
def payload(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    return importlib.import_module("smoke_package").source_payload(ROOT)


def rules():
    return [line.strip() for line in (ROOT / ".dockerignore").read_text().splitlines()
            if line.strip() and not line.lstrip().startswith("#")]


def test_all_packaged_runtime_web_assets_have_explicit_container_entries(payload):
    check_explicit_asset_rules(rules(), payload)


@pytest.mark.parametrize("asset", ["web/static/settings-plan.js", "web/static/radio-settings.js",
                                  "web/templates/radio-settings.html"])
def test_omitting_a_settings_asset_is_detected(payload, asset):
    without_asset = [rule for rule in rules() if rule != "!src/radio_loadout/" + asset]
    with pytest.raises(AssertionError, match="lacks explicit container declaration"):
        check_explicit_asset_rules(without_asset, payload)


def test_new_packaged_asset_requires_an_explicit_rule(payload):
    with pytest.raises(AssertionError, match="future-feature.js"):
        check_explicit_asset_rules(rules(), {**payload, "radio_loadout/web/static/future-feature.js": b""})
