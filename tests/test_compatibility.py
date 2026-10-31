"""Exporter capability reports without assumptions about a particular radio."""

from dataclasses import replace

import pytest

from radio_loadout import compatibility
from radio_loadout.compatibility import check_chirp_compatibility
from radio_loadout.models import (
    AnalogSettings,
    Channel,
    ChannelMode,
    ScanBehavior,
    Tone,
    ToneMode,
    TonePolarity,
)


def _channel(**changes) -> Channel:
    values = {
        "name": "CALL", "receive_frequency_hz": 146_520_000,
        "transmit_frequency_hz": 146_520_000,
        "analog_settings": AnalogSettings(power_watts=5),
    }
    return Channel(**(values | changes))


def test_valid_multi_channel_report() -> None:
    channels = [
        _channel(),
        _channel(name="NFM RX", transmit_frequency_hz=None, mode=ChannelMode.NFM,
                 tuning_step_khz=25, scan_behavior=ScanBehavior.PRIORITY),
        _channel(name="AM", mode=ChannelMode.AM),
        _channel(name="CROSS", analog_settings=AnalogSettings(
            Tone(ToneMode.CTCSS, 100), Tone(ToneMode.DCS, 23, TonePolarity.REVERSE), 2.5,
        )),
    ]
    report = check_chirp_compatibility(channels)
    assert report.compatible
    assert report.channel_count == 4
    assert not any(issue.severity == "error" for issue in report.issues)
    receive_only = next(issue for issue in report.issues if issue.field == "receive_only")
    assert receive_only.severity == "info"
    assert receive_only.channel_index == 1
    assert receive_only.channel_name == "NFM RX"
    assert report.to_dict()["compatible"] is True


def test_unsupported_dmr_is_channel_specific() -> None:
    report = check_chirp_compatibility([
        _channel(), _channel(name="DIGITAL", mode=ChannelMode.DMR, analog_settings=None),
    ])
    assert not report.compatible
    issue = next(issue for issue in report.issues if issue.severity == "error")
    assert (issue.channel_index, issue.channel_name, issue.field) == (1, "DIGITAL", "mode")
    assert "FM, NFM, and AM" in issue.message


@pytest.mark.parametrize(("changes", "field"), [
    ({"receive_frequency_hz": float("inf")}, "receive_frequency_hz"),
    ({"transmit_frequency_hz": float("nan")}, "transmit_frequency_hz"),
    ({"receive_frequency_hz": 146_520_000.5}, "receive_frequency_hz"),
    ({"analog_settings": AnalogSettings(power_watts=float("inf"))}, "power_watts"),
    ({"analog_settings": AnalogSettings(power_watts=0.0001)}, "power_watts"),
    ({"scan_behavior": "invalid"}, "scan_behavior"),
    ({"analog_settings": AnalogSettings(Tone(mode="unknown", value=100))}, "transmit_tone"),
    ({"analog_settings": AnalogSettings(Tone(ToneMode.DCS, 23, "X"))}, "transmit_tone"),
])
def test_invalid_model_settings_have_structured_errors(changes: dict, field: str) -> None:
    report = check_chirp_compatibility([_channel(**changes)])
    assert not report.compatible
    assert any(issue.severity == "error" and issue.field == field for issue in report.issues)


def test_warnings_do_not_block_export() -> None:
    report = check_chirp_compatibility([
        _channel(analog_settings=None),
        _channel(analog_settings=AnalogSettings(Tone(ToneMode.CTCSS, 100.04), power_watts=2.5555)),
    ])
    assert report.compatible
    assert {issue.field for issue in report.issues if issue.severity == "warning"} == {
        "power_watts", "transmit_tone",
    }


@pytest.mark.parametrize("transmit", [Tone(), Tone(ToneMode.CTCSS, 100), Tone(ToneMode.DCS, 23)])
@pytest.mark.parametrize("receive", [Tone(), Tone(ToneMode.CTCSS, 110.9), Tone(ToneMode.DCS, 25, TonePolarity.REVERSE)])
def test_all_analog_tone_combinations_are_representable(transmit: Tone, receive: Tone) -> None:
    assert check_chirp_compatibility([
        _channel(analog_settings=AnalogSettings(transmit, receive, 5)),
    ]).compatible


@pytest.mark.parametrize(("field", "value"), [
    ("tuning_step_khz", 8.33),
    ("receive_frequency_hz", 0),
    ("transmit_frequency_hz", -1),
])
def test_checker_rejects_invalid_model_instances(field: str, value) -> None:
    channel = _channel()
    # A reusable checker must still report corrupted/deserialized instances clearly.
    object.__setattr__(channel, field, value)
    report = check_chirp_compatibility([channel])
    assert not report.compatible
    assert any(issue.field == field and issue.severity == "error" for issue in report.issues)


def test_checker_validates_dcs_values_through_the_tone_model() -> None:
    tone = Tone(ToneMode.DCS, 23)
    object.__setattr__(tone, "value", 89)
    report = check_chirp_compatibility([_channel(analog_settings=AnalogSettings(tone, power_watts=5))])
    assert not report.compatible
    assert any(issue.field == "transmit_tone" and "octal" in issue.message for issue in report.issues)


def test_empty_loadout_is_incompatible() -> None:
    report = check_chirp_compatibility([])
    assert not report.compatible
    assert report.issues[0].channel_index is None
    assert report.issues[0].field == "channels"


def test_checker_exercises_complete_ordered_export(monkeypatch) -> None:
    channels = [_channel(), _channel(name="SECOND")]
    calls = []

    def fail_export(submitted):
        calls.append(submitted)
        raise ValueError("Cannot serialize this loadout")

    monkeypatch.setattr(compatibility, "export_chirp_csv", fail_export)
    report = check_chirp_compatibility(channels)
    assert calls == [channels]
    assert not report.compatible
    assert report.issues[0].field == "export"
    assert "Cannot serialize" in report.issues[0].message


def test_checker_does_not_impose_radio_specific_limits() -> None:
    # Unusual frequencies and long names are legal in Generic CSV, independent of radios.
    channels = [_channel(name="A" * 256, receive_frequency_hz=1, transmit_frequency_hz=50_000_000_000)]
    channels += [replace(channels[0], name=f"Channel {index}") for index in range(1200)]
    assert check_chirp_compatibility(channels).compatible
