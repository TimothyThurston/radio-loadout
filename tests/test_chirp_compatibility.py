"""V1 CHIRP Generic CSV compatibility, using independent input fixtures."""

import csv
from dataclasses import replace
from io import StringIO
from pathlib import Path

import pytest

from radio_loadout.exporters.chirp_csv import CHIRP_HEADERS, export_chirp_csv
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

FIXTURES = Path(__file__).parent / "fixtures" / "chirp"


def _channel(
    name: str,
    rx: int,
    tx: int | None,
    *,
    mode: str = "FM",
    transmit_tone: Tone | None = None,
    receive_tone: Tone | None = None,
    power: float | None = 5.0,
    step: float = 5.0,
    scan: str = "",
    comment: str = "",
) -> Channel:
    return Channel(
        name=name,
        receive_frequency_hz=rx,
        transmit_frequency_hz=tx,
        mode=ChannelMode(mode),
        analog_settings=AnalogSettings(transmit_tone or Tone(), receive_tone or Tone(), power),
        tuning_step_khz=step,
        scan_behavior=ScanBehavior(scan),
        comment=comment,
    )


def _ctcss(value: float) -> Tone:
    return Tone(ToneMode.CTCSS, value)


def _dcs(value: int, polarity: str = "N") -> Tone:
    return Tone(ToneMode.DCS, value, TonePolarity(polarity))


ANALOG_CHANNELS = [
    _channel("2M CALL", 146_520_000, 146_520_000, comment="Simplex calling channel"),
    _channel("PLUS RPT", 444_500_000, 449_500_000, step=12.5, scan="S", power=25,
             comment="Positive repeater offset"),
    _channel("MINUS RPT", 146_940_000, 146_340_000, power=10,
             comment="Negative repeater offset"),
    _channel("NOAA 7", 162_550_000, None, mode="NFM", step=25, scan="P", power=0.5,
             comment="Receive-only weather"),
    _channel("AIR RX", 121_500_000, None, mode="AM", step=25,
             comment="AM receive-only channel"),
    _channel("SPLIT", 145_000_000, 435_000_000, step=10, power=2.5,
             comment="Absolute transmit frequency"),
]

TONE_CASES = [
    ("TX CTCSS", _ctcss(100), Tone(), 5, "", "Transmit tone only"),
    ("TSQL", _ctcss(110.9), _ctcss(110.9), 5, "", "Inactive rToneFreq differs"),
    ("DCS NN", _dcs(23), _dcs(23), 5, "", "Inactive RxDtcsCode differs"),
    ("DCS NR", _dcs(25), _dcs(25, "R"), 2.5, "S", "Normal TX reverse RX"),
    ("DCS RN", _dcs(26, "R"), _dcs(26), 1, "P", "Reverse TX normal RX"),
    ("DCS RR", _dcs(31, "R"), _dcs(31, "R"), 10, "", "Reverse both directions"),
    ("CROSS C D", _ctcss(123), _dcs(25, "R"), 5, "S", "CTCSS TX DCS RX"),
    ("CROSS D C", _dcs(47, "R"), _ctcss(136.5), 5, "", "DCS TX CTCSS RX"),
    ("CROSS C C", _ctcss(100), _ctcss(110.9), 5, "", "Different CTCSS frequencies"),
    ("CROSS D D", _dcs(23, "R"), _dcs(25, "R"), 5, "", "Different DCS codes"),
    ("RX DCS", Tone(), _dcs(43, "R"), 5, "", "DCS receive only"),
    ("TX DCS", _dcs(65, "R"), Tone(), 5, "", "DCS transmit only"),
    ("RX CTCSS", Tone(), _ctcss(151.4), 5, "", "CTCSS receive only"),
    ("CROSS TX TONE", _ctcss(127.3), Tone(), 5, "", "Transmit CTCSS cross spelling"),
]
TONE_CHANNELS = []
for index, (name, tx_tone, rx_tone, power, scan, comment) in enumerate(TONE_CASES):
    frequency = 146_520_000 + index * 10_000 if index < 6 else 446_000_000 + (index - 6) * 10_000
    TONE_CHANNELS.append(_channel(
        name, frequency, frequency, transmit_tone=tx_tone, receive_tone=rx_tone,
        power=power, scan=scan, step=5 if index < 6 else 12.5, comment=comment,
    ))

# Explicit fixture expectations, independent of the production tuning-step constant.
STEPS = (1, 2.5, 5, 6.25, 9, 10, 12.5, 15, 20, 25, 30, 50, 100, 125, 200)
POWERS = (0.5, 1, 2.5, 5, 10, 25, 50)
STEP_CHANNELS = [
    _channel(
        f"STEP {step}", 145_000_000 + index * 10_000, 145_000_000 + index * 10_000,
        mode={2: "NFM", 4: "AM", 6: "NFM"}.get(index, "FM"),
        step=step, scan=("", "S", "P")[index % 3], power=POWERS[index % len(POWERS)],
        comment=f"Step {step}",
    )
    for index, step in enumerate(STEPS)
]
EXPECTED_FIXTURES = {
    "analog_channels.csv": ANALOG_CHANNELS,
    "tones.csv": TONE_CHANNELS,
    "tuning_scan_power.csv": STEP_CHANNELS,
    "extra_columns.csv": [
        _channel("Répéteur", 146_520_001, 146_520_001, comment='Café, say "hello"'),
        _channel("SECOND", 446_006_250, 446_006_250, mode="NFM", step=6.25, power=2.5,
                 comment="Line one\nLine two"),
        _channel("THIRD", 121_500_000, None, mode="AM", step=25, power=10,
                 comment="Last file row"),
    ],
    "blank_optional.csv": [
        _channel("DEFAULTS", 146_520_000, 146_520_000, power=None),
        _channel("BLANK TONE DEFAULTS", 446_000_000, 446_000_000,
                 transmit_tone=_ctcss(100), power=None),
        _channel("BLANK RX CODE", 444_500_000, 444_500_000,
                 transmit_tone=_dcs(23), receive_tone=_dcs(23)),
    ],
    "utf8_bom_crlf.csv": [
        _channel("Café RX", 162_550_000, None, mode="NFM", step=25, scan="P", power=2.5,
                 comment='Weather, "quoted" comment'),
    ],
}


@pytest.mark.parametrize("filename", EXPECTED_FIXTURES)
def test_fixture_import_and_round_trip(filename: str) -> None:
    # decode utf-8 deliberately leaves the BOM for the importer to handle.
    imported = import_chirp_csv((FIXTURES / filename).read_bytes().decode("utf-8"))
    assert imported == EXPECTED_FIXTURES[filename]
    exported = export_chirp_csv(imported)
    rows = list(csv.DictReader(StringIO(exported)))
    assert list(rows[0]) == CHIRP_HEADERS
    assert [row["Name"] for row in rows] == [channel.name for channel in imported]
    # Locations are metadata, not sorting keys; export assigns sequential numbers.
    assert [row["Location"] for row in rows] == [str(i) for i in range(len(imported))]
    # Preserve the existing exporter policy: unspecified power becomes 5 W.
    expected = [
        replace(channel, analog_settings=replace(channel.analog_settings, power_watts=5.0))
        if channel.analog_settings.power_watts is None else channel
        for channel in imported
    ]
    assert import_chirp_csv(exported) == expected


def test_fixture_contains_real_utf8_bom_and_crlf_bytes() -> None:
    data = (FIXTURES / "utf8_bom_crlf.csv").read_bytes()
    assert data.startswith(b"\xef\xbb\xbf")
    assert b"\r\n" in data
    assert b"\n" not in data.replace(b"\r\n", b"")


@pytest.mark.parametrize(("filename", "message"), [
    ("missing_headers.csv", "missing required columns: Name, Frequency"),
    ("invalid_frequency.csv", "Frequency must be numeric"),
    ("unsupported_mode.csv", "Unsupported channel mode: USB"),
    ("invalid_offset.csv", "Offset must be greater than zero"),
    ("invalid_ctcss.csv", "CTCSS tone must be between"),
    ("invalid_dcs.csv", "three octal digits"),
    ("unsupported_tuning_step.csv", "Tuning step must be a supported CHIRP value"),
    ("empty.csv", "does not contain a CSV header"),
])
def test_invalid_fixtures_are_rejected(filename: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        import_chirp_csv((FIXTURES / filename).read_text(encoding="utf-8"))


def _csv_for_row(**values: str) -> str:
    row = {"Name": "BAD", "Frequency": "146.520000", **values}
    output = StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=list(row))
    writer.writeheader()
    writer.writerow(row)
    return output.getvalue()


@pytest.mark.parametrize(("values", "message"), [
    ({"Name": ""}, "Name cannot be empty"),
    *[({"Frequency": value}, "Frequency") for value in (
        "", "0", "-146.52", "NaN", "inf", "-inf", "1e309", "1e308",
    )],
    ({"Mode": "DMR"}, "analog channels only"),
    *[({"Duplex": "+", "Offset": value}, "Offset") for value in (
        "", "nope", "0", "-0.6", "NaN", "inf",
    )],
    ({"Duplex": "-", "Offset": "200"}, "Transmit frequency must be greater than zero"),
    ({"Duplex": "split", "Offset": "nope"}, "Transmit frequency must be numeric"),
    ({"Duplex": "invalid"}, "Unsupported duplex value"),
    *[({"Tone": "Tone", "rToneFreq": value}, "CTCSS|rToneFreq") for value in (
        "", "nope", "NaN", "inf", "49.9", "300.1",
    )],
    ({"Tone": "TSQL", "rToneFreq": "100", "cToneFreq": "bad"}, "CTCSS"),
    ({"Tone": "TSQL", "rToneFreq": "bad", "cToneFreq": "110.9"}, "CTCSS"),
    *[({"Tone": "DTCS", "DtcsCode": value}, "DCS|DtcsCode") for value in (
        "", "nope", "23.5", "089", "1234", "-23",
    )],
    ({"Tone": "DTCS", "DtcsCode": "023", "DtcsPolarity": "NX"}, "DTCS polarity"),
    ({"Tone": "DTCS", "DtcsCode": "023", "RxDtcsCode": "089"}, "three octal digits"),
    ({"Tone": "DTCS-R"}, "Unsupported tone mode"),
    ({"Tone": "Cross", "CrossMode": "nope"}, "CrossMode must contain"),
    ({"Tone": "Cross", "CrossMode": "Bogus->Tone"}, "Unsupported cross-tone mode"),
    ({"Tone": "Cross", "CrossMode": "Tone->DTCS", "rToneFreq": "100",
      "RxDtcsCode": "089"}, "three octal digits"),
    *[({"TStep": value}, "Tuning step") for value in ("nope", "0", "8.33", "NaN", "inf")],
    *[({"Power": value}, "Power") for value in ("High", "0W", "-5W", "NaN", "inf")],
    ({"Skip": "X"}, "Unsupported scan behavior"),
])
def test_invalid_values_report_row_and_field(values: dict[str, str], message: str) -> None:
    with pytest.raises(ValueError, match=f"Invalid CHIRP CSV row 2: .*({message})"):
        import_chirp_csv(_csv_for_row(**values))


@pytest.mark.parametrize("header", ["Name", "Frequency"])
def test_each_required_header_is_enforced(header: str) -> None:
    remaining = "Frequency" if header == "Name" else "Name"
    with pytest.raises(ValueError, match=f"missing required columns: {header}"):
        import_chirp_csv(f"{remaining}\nanything\n")


@pytest.mark.parametrize(("text", "message"), [
    ("", "CSV header"),
    ("\ufeff", "CSV header"),
    ("\n\n", "missing required columns"),
    ("Name,Frequency\n", "any channels"),
    ("Name,Frequency\n,\n", "any channels"),
])
def test_empty_and_header_only_csv_are_rejected(text: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        import_chirp_csv(text)


@pytest.mark.parametrize("inactive_frequency", ["88.5", ""])
def test_tsql_uses_receive_ctcss_for_both_directions(inactive_frequency: str) -> None:
    channel = import_chirp_csv(_csv_for_row(
        Tone="TSQL", rToneFreq=inactive_frequency, cToneFreq="110.9",
    ))[0]
    assert channel.analog_settings.transmit_tone == _ctcss(110.9)
    assert channel.analog_settings.receive_tone == _ctcss(110.9)
    assert import_chirp_csv(export_chirp_csv([channel])) == [
        replace(channel, analog_settings=replace(channel.analog_settings, power_watts=5.0)),
    ]


@pytest.mark.parametrize("inactive_code", ["025", ""])
def test_matched_dcs_ignores_cross_mode_receive_code(inactive_code: str) -> None:
    channel = import_chirp_csv(_csv_for_row(
        Tone="DTCS", DtcsCode="023", RxDtcsCode=inactive_code, DtcsPolarity="RN",
    ))[0]
    assert channel.analog_settings.transmit_tone == _dcs(23, "R")
    assert channel.analog_settings.receive_tone == _dcs(23)


@pytest.mark.parametrize("field", ["Mode", "TStep", "DtcsPolarity"])
def test_blank_optional_defaults_match_omitted_columns(field: str) -> None:
    assert import_chirp_csv(_csv_for_row(**{field: "  "})) == import_chirp_csv(_csv_for_row())


@pytest.mark.parametrize("tone_column", ["rToneFreq", "cToneFreq"])
def test_tsql_accepts_a_single_ctcss_column(tone_column: str) -> None:
    channel = import_chirp_csv(_csv_for_row(Tone="TSQL", **{tone_column: "110.9"}))[0]
    assert channel.analog_settings.transmit_tone == _ctcss(110.9)
    assert channel.analog_settings.receive_tone == _ctcss(110.9)


def test_blank_records_between_channels_are_ignored() -> None:
    channels = import_chirp_csv("Name,Frequency\nFIRST,146.52\n\n,\nSECOND,446.0\n")
    assert [channel.name for channel in channels] == ["FIRST", "SECOND"]


def test_unheaded_extra_values_remain_invalid() -> None:
    with pytest.raises(ValueError, match="Invalid CHIRP CSV row 2: too many columns"):
        import_chirp_csv("Name,Frequency\nBAD,146.520000,unheaded\n")


def test_100_channel_round_trip_preserves_every_supported_field() -> None:
    # Build input from independent fixture rows, not the exporter under test.
    fixture_rows = []
    for filename in ("analog_channels.csv", "tones.csv", "tuning_scan_power.csv"):
        fixture_rows.extend(csv.DictReader(StringIO((FIXTURES / filename).read_text("utf-8"))))
    fixture_models = ANALOG_CHANNELS + TONE_CHANNELS + STEP_CHANNELS
    output = StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=CHIRP_HEADERS, lineterminator="\r\n")
    writer.writeheader()
    expected = []
    for index in range(100):
        template_index = index % len(fixture_rows)
        row = dict(fixture_rows[template_index])
        template = fixture_models[template_index]
        delta_hz = index * 1_000
        row.update(
            Location=str((index * 37) % 100),
            Name=f"CH {index:03d}",
            Frequency=f"{(template.receive_frequency_hz + delta_hz) / 1_000_000:.6f}",
            TStep=str(STEPS[index % len(STEPS)]),
            Skip=("", "S", "P")[index % 3],
            Power=f"{POWERS[index % len(POWERS)]}W",
            Comment=f'Channel {index:03d}, "portable" café',
        )
        if row["Duplex"] == "split":
            row["Offset"] = f"{(template.transmit_frequency_hz + delta_hz) / 1_000_000:.6f}"
        writer.writerow(row)
        expected.append(replace(
            template, name=row["Name"],
            receive_frequency_hz=template.receive_frequency_hz + delta_hz,
            transmit_frequency_hz=(
                template.transmit_frequency_hz + delta_hz
                if template.transmit_frequency_hz is not None else None
            ),
            analog_settings=replace(
                template.analog_settings, power_watts=POWERS[index % len(POWERS)],
            ),
            tuning_step_khz=STEPS[index % len(STEPS)],
            scan_behavior=ScanBehavior(row["Skip"]), comment=row["Comment"],
        ))

    imported = import_chirp_csv(output.getvalue())
    assert len(imported) == 100
    assert imported == expected
    reimported = import_chirp_csv(export_chirp_csv(imported))
    assert len(reimported) == 100
    assert [channel.name for channel in reimported] == [f"CH {i:03d}" for i in range(100)]
    assert reimported == expected
