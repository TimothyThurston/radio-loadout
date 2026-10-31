"""Tests for CHIRP CSV importing."""

import pytest

from radio_loadout.exporters.chirp_csv import export_chirp_csv
from radio_loadout.importers.chirp_csv import import_chirp_csv
from radio_loadout.models import (
    AnalogSettings,
    Channel,
    ChannelMode,
    ScanBehavior,
    Tone,
    ToneMode,
    TonePolarity,
)


def test_chirp_csv_round_trip() -> None:
    original_channels = [
        Channel(
            name="TEST RPT",
            receive_frequency_hz=146_940_000,
            transmit_frequency_hz=146_340_000,
            mode=ChannelMode.FM,
            analog_settings=AnalogSettings(
                transmit_tone=Tone(
                    mode=ToneMode.CTCSS,
                    value=100.0,
                ),
                power_watts=5.0,
            ),
            tuning_step_khz=5.0,
            comment="Repeater test",
        ),
        Channel(
            name="NOAA 7",
            receive_frequency_hz=162_550_000,
            transmit_frequency_hz=None,
            mode=ChannelMode.NFM,
            analog_settings=AnalogSettings(
                power_watts=5.0,
            ),
            tuning_step_khz=25.0,
            scan_behavior=ScanBehavior.PRIORITY,
            comment="Receive-only weather",
        ),
        Channel(
            name="DCS TEST",
            receive_frequency_hz=444_500_000,
            transmit_frequency_hz=449_500_000,
            mode=ChannelMode.FM,
            analog_settings=AnalogSettings(
                transmit_tone=Tone(
                    mode=ToneMode.DCS,
                    value=23,
                    polarity=TonePolarity.NORMAL,
                ),
                receive_tone=Tone(
                    mode=ToneMode.DCS,
                    value=23,
                    polarity=TonePolarity.REVERSE,
                ),
                power_watts=2.5,
            ),
            tuning_step_khz=12.5,
            scan_behavior=ScanBehavior.SKIP,
            comment="DCS test",
        ),
        Channel(
            name="CROSS TEST",
            receive_frequency_hz=446_000_000,
            transmit_frequency_hz=446_000_000,
            mode=ChannelMode.FM,
            analog_settings=AnalogSettings(
                transmit_tone=Tone(
                    mode=ToneMode.CTCSS,
                    value=123.0,
                ),
                receive_tone=Tone(
                    mode=ToneMode.DCS,
                    value=25,
                    polarity=TonePolarity.REVERSE,
                ),
                power_watts=5.0,
            ),
            comment="Cross tone",
        ),
    ]

    csv_text = export_chirp_csv(original_channels)
    imported_channels = import_chirp_csv(csv_text)

    assert imported_channels == original_channels


def test_chirp_csv_requires_headers() -> None:
    with pytest.raises(
        ValueError,
        match="missing required columns",
    ):
        import_chirp_csv(
            "Location,Comment\n"
            "0,Missing data\n"
        )


def test_chirp_csv_rejects_empty_file() -> None:
    with pytest.raises(
        ValueError,
        match="does not contain any channels",
    ):
        import_chirp_csv("Name,Frequency\n")


def test_chirp_csv_reports_invalid_row() -> None:
    csv_text = (
        "Name,Frequency,Duplex,Mode\n"
        "BAD CHANNEL,not-a-frequency,,FM\n"
    )

    with pytest.raises(
        ValueError,
        match="Invalid CHIRP CSV row 2",
    ):
        import_chirp_csv(csv_text)