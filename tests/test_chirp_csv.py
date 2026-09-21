import csv
from io import StringIO

import pytest

from radio_loadout.exporters.chirp_csv import CHIRP_HEADERS, export_chirp_csv
from radio_loadout.models import (
    AnalogSettings,
    Channel,
    ChannelMode,
    Tone,
    ToneMode,
)


def _read_rows(csv_text: str) -> list[dict[str, str]]:
    reader = csv.DictReader(StringIO(csv_text))
    assert reader.fieldnames == CHIRP_HEADERS
    return list(reader)


def test_simplex_channel_export() -> None:
    channel = Channel(
        name="2M CALL",
        receive_frequency_hz=146_520_000,
        transmit_frequency_hz=146_520_000,
        mode=ChannelMode.FM,
        comment="National calling frequency",
    )

    rows = _read_rows(export_chirp_csv([channel]))
    row = rows[0]

    assert row["Location"] == "0"
    assert row["Name"] == "2M CALL"
    assert row["Frequency"] == "146.520000"
    assert row["Duplex"] == ""
    assert row["Offset"] == "0.000000"
    assert row["Mode"] == "FM"
    assert row["Comment"] == "National calling frequency"


def test_repeater_with_transmit_tone_export() -> None:
    channel = Channel(
        name="LOCAL RPT",
        receive_frequency_hz=145_400_000,
        transmit_frequency_hz=144_800_000,
        mode=ChannelMode.FM,
        analog_settings=AnalogSettings(
            transmit_tone=Tone(mode=ToneMode.CTCSS, value=100.0),
            power_watts=5.0,
        ),
    )

    row = _read_rows(export_chirp_csv([channel]))[0]

    assert row["Duplex"] == "-"
    assert row["Offset"] == "0.600000"
    assert row["Tone"] == "Tone"
    assert row["rToneFreq"] == "100.0"
    assert row["Power"] == "5.0W"


def test_receive_only_channel_export() -> None:
    channel = Channel(
        name="NOAA",
        receive_frequency_hz=162_550_000,
        transmit_frequency_hz=None,
        mode=ChannelMode.NFM,
    )

    row = _read_rows(export_chirp_csv([channel]))[0]

    assert row["Duplex"] == "off"
    assert row["Offset"] == "0.000000"
    assert row["Mode"] == "NFM"
    assert row["Power"] == "5.0W"


def test_matching_ctcss_tones_use_tsql() -> None:
    channel = Channel(
        name="TONE SQL",
        receive_frequency_hz=146_940_000,
        transmit_frequency_hz=146_340_000,
        analog_settings=AnalogSettings(
            transmit_tone=Tone(mode=ToneMode.CTCSS, value=110.9),
            receive_tone=Tone(mode=ToneMode.CTCSS, value=110.9),
        ),
    )

    row = _read_rows(export_chirp_csv([channel]))[0]

    assert row["Tone"] == "TSQL"
    assert row["rToneFreq"] == "110.9"
    assert row["cToneFreq"] == "110.9"


def test_cross_tone_export() -> None:
    channel = Channel(
        name="CROSS TONE",
        receive_frequency_hz=444_500_000,
        transmit_frequency_hz=449_500_000,
        analog_settings=AnalogSettings(
            transmit_tone=Tone(mode=ToneMode.CTCSS, value=100.0),
            receive_tone=Tone(mode=ToneMode.DCS, value=23),
        ),
    )

    row = _read_rows(export_chirp_csv([channel]))[0]

    assert row["Tone"] == "Cross"
    assert row["CrossMode"] == "Tone->DTCS"
    assert row["rToneFreq"] == "100.0"
    assert row["RxDtcsCode"] == "023"


def test_dmr_channel_is_rejected() -> None:
    channel = Channel(
        name="DMR TEST",
        receive_frequency_hz=444_000_000,
        transmit_frequency_hz=449_000_000,
        mode=ChannelMode.DMR,
    )

    with pytest.raises(ValueError, match="analog channels"):
        export_chirp_csv([channel])