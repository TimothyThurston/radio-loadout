"""Documented-profile limits, explicit uncertainty and non-mutating generic layering."""

import copy
from dataclasses import FrozenInstanceError, replace

import pytest

from radio_loadout.compatibility import check_chirp_compatibility
from radio_loadout.models import AnalogSettings, Channel, ChannelMode, Tone, ToneMode
from radio_loadout.profile_compatibility import check_channel_compatibility
from radio_loadout.radio_profiles import (
    BF_F8HP_PRO_V053,
    ProfileSource,
    RadioBand,
    get_radio_profile,
)

PROFILE = BF_F8HP_PRO_V053


def channel(rx=146_520_000, tx=146_520_000, **kwargs):
    return Channel("TEST", rx, tx, **kwargs)


def errors(report):
    return {(issue.field, issue.channel_index) for issue in report.issues if issue.severity == "error"}


def test_generic_report_is_exactly_unchanged_without_selection():
    channels = [channel()]
    assert check_channel_compatibility(channels).to_dict() == check_chirp_compatibility(channels).to_dict()
    assert "radio_profile" not in check_channel_compatibility(channels).to_dict()
    assert get_radio_profile("") is None


def test_profile_metadata_versions_sources_and_independent_support_states():
    data = PROFILE.to_dict()
    assert data["schema_version"] == 1 and data["revision"] == 1
    assert "V0.53" in data["firmware_scope"] and "V3.1" in data["firmware_scope"]
    assert not data["hardware_verified"] and not data["firmware_detected"]
    assert data["support"] == {"configuration": "documented-review-only", "programming": "unsupported", "live_control": "unsupported"}
    assert data["name_max_length"] is None and data["name_characters"] is None
    assert data["power_options_watts"] is None and data["dcs_codes"] is None
    assert data["ctcss_values_hz"] is None and data["tuning_steps_exhaustive"] is False
    assert data["sources"][0]["sha256"] == "1114e1e55c6e6bc71dddcac1421333d199660377115ca2cc5ffb96e75d100b47"
    with pytest.raises(FrozenInstanceError):
        PROFILE.memory_capacity = 1
    data["memory_capacity"] = 1
    assert PROFILE.memory_capacity == 1000


@pytest.mark.parametrize("profile_id", ["BF-F8HP", "uv-5r", "baofeng-bf-f8hp-pro-v044-us", " ", "x" * 81])
def test_unknown_models_firmware_or_ids_never_silently_fall_back(profile_id):
    with pytest.raises(ValueError, match="Unknown radio profile"):
        get_radio_profile(profile_id)


@pytest.mark.parametrize("rx,mode", [
    (108_000_000, "AM"), (136_999_999, "AM"), (137_000_000, "AM"), (137_000_000, "FM"),
    (174_000_000, "NFM"), (219_000_000, "FM"), (260_000_000, "NFM"),
    (350_000_000, "FM"), (390_000_000, "FM"), (400_000_000, "NFM"), (520_000_000, "FM"),
])
def test_reviewed_receive_edges_and_modes_do_not_become_hardware_claims(rx, mode):
    report = check_channel_compatibility([channel(rx, None, mode=ChannelMode(mode))], PROFILE)
    assert report.compatible
    assert any(i.field == "radio_profile" and i.severity == "warning" for i in report.issues)
    if rx == 137_000_000:
        assert any("137 MHz" in i.message for i in report.issues)


@pytest.mark.parametrize("rx,mode", [(107_999_999, "AM"), (121_500_000, "FM"), (145_000_000, "AM"),
                                   (174_000_001, "FM"), (218_999_999, "FM"), (260_000_001, "NFM"),
                                   (349_999_999, "FM"), (390_000_001, "FM"), (399_999_999, "FM"),
                                   (520_000_001, "FM"), (88_000_000, "FM")])
def test_outside_reviewed_memory_scope_is_blocked_not_reinterpreted(rx, mode):
    assert ("receive_frequency_hz", 0) in errors(check_channel_compatibility([channel(rx, None, mode=ChannelMode(mode))], PROFILE))


@pytest.mark.parametrize("tx", [144_000_000, 148_000_000, 219_000_000, 225_000_000, 420_000_000, 450_000_000])
def test_documented_tx_edges_are_configuration_checks_not_operating_permission(tx):
    report = check_channel_compatibility([channel(tx, tx)], PROFILE)
    assert report.compatible
    assert any("transmit authorization" in issue.message for issue in report.issues)


@pytest.mark.parametrize("tx", [143_999_999, 148_000_001, 218_999_999, 225_000_001, 419_999_999, 450_000_001, 162_550_000])
def test_out_of_scope_tx_blocked_and_receive_only_not_silently_applied(tx):
    item = channel(146_520_000, tx)
    report = check_channel_compatibility([item], PROFILE)
    assert ("transmit_frequency_hz", 0) in errors(report)
    assert item.transmit_frequency_hz == tx


def test_airband_must_be_receive_only_and_step_limitations_are_explicit():
    assert ("transmit_frequency_hz", 0) in errors(check_channel_compatibility([channel(121_500_000, 121_500_000, mode=ChannelMode.AM)], PROFILE))
    report = check_channel_compatibility([channel(121_500_000, None, mode=ChannelMode.AM)], PROFILE)
    assert report.compatible and any("8.33" in i.message for i in report.issues)


@pytest.mark.parametrize("frequency,ceiling", [(146_520_000, 10.0), (223_500_000, 5.0), (446_000_000, 10.0)])
def test_band_power_ceiling_is_not_a_guessed_selectable_power_mapping(frequency, ceiling):
    good = channel(frequency, frequency, analog_settings=AnalogSettings(power_watts=ceiling))
    bad = replace(good, analog_settings=AnalogSettings(power_watts=ceiling + 0.1))
    assert check_channel_compatibility([good], PROFILE).compatible
    assert ("power_watts", 0) in errors(check_channel_compatibility([bad], PROFILE))


def test_total_memory_capacity_boundary_only_not_zone_or_free_slot_mapping():
    assert check_channel_compatibility([channel()] * 1000, PROFILE).compatible
    report = check_channel_compatibility([channel()] * 1001, PROFILE)
    assert ("channels", None) in errors(report)
    assert any("reserve slots" in i.message for i in report.issues)


def test_unknown_name_tones_and_steps_are_preserved_with_explicit_uncertainty():
    item = channel(analog_settings=AnalogSettings(Tone(ToneMode.DCS, 777), Tone(ToneMode.CTCSS, 101.1), 3.0), tuning_step_khz=100.0)
    item = replace(item, name="Unverified Unicode name 🙂")
    before = copy.deepcopy(item)
    report = check_channel_compatibility([item], PROFILE)
    assert report.compatible and item == before
    assert any(i.field == "unverified_fields" for i in report.issues)
    assert any(i.field == "tuning_step_khz" and i.severity == "warning" for i in report.issues)


def test_profile_foundation_can_enforce_known_limits_without_altering_channels():
    profile = replace(PROFILE, name_max_length=3, name_characters="ABC", power_options_watts=(1.0, 5.0),
                      dcs_codes=(23,), ctcss_values_hz=(100.0,), tuning_steps_exhaustive=True)
    item = channel(analog_settings=AnalogSettings(Tone(ToneMode.DCS, 777), Tone(ToneMode.CTCSS, 101.1), 3.0), tuning_step_khz=100.0)
    before = copy.deepcopy(item)
    report = check_channel_compatibility([item], profile)
    assert {field for field, _ in errors(report)} >= {"name", "power_watts", "transmit_tone", "receive_tone", "tuning_step_khz"}
    assert item == before


def test_generic_invalid_modes_fail_before_profile_specific_checks():
    assert not check_channel_compatibility([channel(mode=ChannelMode.DMR)], PROFILE).compatible


@pytest.mark.parametrize("changes", [{"profile_id": "UPPER"}, {"revision": 0}, {"revision": True},
                                    {"firmware_scope": ""}, {"sources": ()}, {"memory_capacity": True},
                                    {"name_max_length": 0}, {"receive_bands": ()}])
def test_invalid_profile_definitions_fail_visibly(changes):
    with pytest.raises(ValueError):
        replace(PROFILE, **changes)


@pytest.mark.parametrize("low,high,modes,power", [(0, 1, (ChannelMode.FM,), None), (10, 1, (ChannelMode.FM,), None),
                                              (1, 10, (), None), (1, 10, ("FM",), None),
                                              (1, 10, (ChannelMode.FM,), float("nan"))])
def test_bad_band_definitions_fail(low, high, modes, power):
    with pytest.raises(ValueError):
        RadioBand(low, high, modes, power)


def test_sources_need_reviewable_origins_and_valid_optional_hashes():
    with pytest.raises(ValueError):
        ProfileSource("javascript:bad", "title", "locator", "2026-11-06")
    with pytest.raises(ValueError):
        ProfileSource("https://example.com", "title", "locator", "2026-11-06", "bad")
