"""Prospective tone contract: literal inputs/expectations, public converters only."""

import csv
from io import StringIO

import pytest

from radio_loadout.exporters.chirp_csv import export_chirp_csv
from radio_loadout.importers.chirp_csv import import_chirp_csv
from radio_loadout.models import AnalogSettings, Channel, Tone, ToneMode, TonePolarity

TONE_COLUMNS = (
    "Tone", "rToneFreq", "cToneFreq", "DtcsCode", "DtcsPolarity", "RxDtcsCode", "CrossMode",
)


def _channel(tx: Tone, rx: Tone, *, receive_only: bool = False) -> Channel:
    return Channel(
        "SYNTH", 146_520_000, None if receive_only else 146_520_000,
        analog_settings=AnalogSettings(tx, rx, 5.0),
    )


@pytest.mark.parametrize(("tx", "rx", "expected"), [
    pytest.param(Tone(), Tone(),
                 ("", "88.5", "88.5", "023", "NN", "023", "Tone->Tone"), id="no-tones"),
    pytest.param(Tone(ToneMode.CTCSS, 100.0), Tone(),
                 ("Tone", "100.0", "88.5", "023", "NN", "023", "Tone->Tone"), id="tx-ctcss"),
    pytest.param(Tone(), Tone(ToneMode.CTCSS, 110.9),
                 ("Cross", "88.5", "110.9", "023", "NN", "023", "->Tone"), id="rx-ctcss"),
    pytest.param(Tone(ToneMode.DCS, 1, TonePolarity.REVERSE), Tone(),
                 ("Cross", "88.5", "88.5", "001", "RN", "023", "DTCS->"), id="tx-dcs"),
    pytest.param(Tone(), Tone(ToneMode.DCS, 777, TonePolarity.REVERSE),
                 ("Cross", "88.5", "88.5", "023", "NR", "777", "->DTCS"), id="rx-dcs"),
    pytest.param(Tone(ToneMode.CTCSS, 100.0), Tone(ToneMode.CTCSS, 100.0),
                 ("TSQL", "100.0", "100.0", "023", "NN", "023", "Tone->Tone"), id="equal-ctcss"),
    pytest.param(Tone(ToneMode.CTCSS, 100.0), Tone(ToneMode.CTCSS, 110.9),
                 ("Cross", "100.0", "110.9", "023", "NN", "023", "Tone->Tone"), id="unequal-ctcss"),
    pytest.param(Tone(ToneMode.DCS, 23), Tone(ToneMode.DCS, 23, TonePolarity.REVERSE),
                 ("DTCS", "88.5", "88.5", "023", "NR", "023", "Tone->Tone"), id="equal-dcs"),
    pytest.param(Tone(ToneMode.DCS, 1, TonePolarity.REVERSE), Tone(ToneMode.DCS, 777),
                 ("Cross", "88.5", "88.5", "001", "RN", "777", "DTCS->DTCS"), id="unequal-dcs"),
    pytest.param(Tone(ToneMode.CTCSS, 100.0), Tone(ToneMode.DCS, 777, TonePolarity.REVERSE),
                 ("Cross", "100.0", "88.5", "023", "NR", "777", "Tone->DTCS"), id="ctcss-to-dcs"),
    pytest.param(Tone(ToneMode.DCS, 1, TonePolarity.REVERSE), Tone(ToneMode.CTCSS, 110.9),
                 ("Cross", "88.5", "110.9", "001", "RN", "023", "DTCS->Tone"), id="dcs-to-ctcss"),
])
def test_export_tone_cells_from_models(tx: Tone, rx: Tone, expected: tuple[str, ...]) -> None:
    rows = list(csv.DictReader(StringIO(export_chirp_csv([_channel(tx, rx)]))))
    assert len(rows) == 1
    assert tuple(rows[0][field] for field in TONE_COLUMNS) == expected


@pytest.mark.parametrize(("source", "tx", "rx", "expected"), [
    pytest.param(
        "Name,Frequency,Tone,CrossMode,rToneFreq,cToneFreq,Power\n"
        "SYNTH,146.520000,Cross,Tone->Tone,100.0,100.0,5W\n",
        Tone(ToneMode.CTCSS, 100.0), Tone(ToneMode.CTCSS, 100.0),
        ("TSQL", "100.0", "100.0", "023", "NN", "023", "Tone->Tone"), id="equal-ctcss",
    ),
    pytest.param(
        "Name,Frequency,Tone,CrossMode,DtcsCode,RxDtcsCode,DtcsPolarity,Power\n"
        "SYNTH,146.520000,Cross,DTCS->DTCS,001,001,RN,5W\n",
        Tone(ToneMode.DCS, 1, TonePolarity.REVERSE), Tone(ToneMode.DCS, 1),
        ("DTCS", "88.5", "88.5", "001", "RN", "001", "Tone->Tone"), id="equal-dcs",
    ),
])
def test_equivalent_cross_spelling_has_literal_import_and_export_expectations(
    source: str, tx: Tone, rx: Tone, expected: tuple[str, ...],
) -> None:
    expected_channel = _channel(tx, rx)
    assert import_chirp_csv(source) == [expected_channel]
    # The export input is constructed independently, not taken from the importer.
    exported = export_chirp_csv([expected_channel])
    row = next(csv.DictReader(StringIO(exported)))
    assert tuple(row[field] for field in TONE_COLUMNS) == expected
    assert import_chirp_csv(exported) == [expected_channel]
    reexported = export_chirp_csv(import_chirp_csv(source))
    assert tuple(next(csv.DictReader(StringIO(reexported)))[field] for field in TONE_COLUMNS) == expected


def test_minimal_csv_import_defaults_are_explicit() -> None:
    expected = Channel(
        "SYNTH", 146_520_000, 146_520_000,
        analog_settings=AnalogSettings(Tone(), Tone(), None),
    )
    assert import_chirp_csv("Name,Frequency\nSYNTH,146.520000\n") == [expected]
    assert expected.tuning_step_khz == 5.0
    assert expected.scan_behavior.value == ""
    row = next(csv.DictReader(StringIO(export_chirp_csv([expected]))))
    assert row["Power"] == "5.0W"
    assert row["Mode"] == "FM"
    assert row["TStep"] == "5.00"
    assert row["Skip"] == ""
    assert tuple(row[field] for field in TONE_COLUMNS) == (
        "", "88.5", "88.5", "023", "NN", "023", "Tone->Tone",
    )


@pytest.mark.parametrize(("source", "field"), [
    ("Name,Frequency,Tone\nSYNTH,146.520000,TSQL\n", "rToneFreq"),
    ("Name,Frequency,Tone,CrossMode\nSYNTH,146.520000,Cross,->Tone\n", "cToneFreq"),
    ("Name,Frequency,Tone,CrossMode\nSYNTH,146.520000,Cross,DTCS->\n", "DtcsCode"),
    ("Name,Frequency,Tone,CrossMode\nSYNTH,146.520000,Cross,->DTCS\n", "RxDtcsCode"),
])
def test_missing_active_values_are_rejected(source: str, field: str) -> None:
    with pytest.raises(ValueError, match=f"row 2: {field} cannot be empty"):
        import_chirp_csv(source)


@pytest.mark.parametrize("source", [
    pytest.param("Name,Frequency,Tone,DtcsCode\nSYNTH,146.520000,,089\n", id="no-tones-invalid-tx-dcs"),
    pytest.param(
        "Name,Frequency,Tone,rToneFreq,RxDtcsCode\nSYNTH,146.520000,Tone,100.0,089\n",
        id="ctcss-invalid-inactive-rx-dcs",
    ),
])
def test_import_rejects_invalid_inactive_dcs_fields(source: str) -> None:
    # Prospective reference-validation target; do not bless acceptance as a default.
    with pytest.raises(ValueError, match="DCS|octal"):
        import_chirp_csv(source)


def test_receive_only_receive_filter_survives_both_directions() -> None:
    source = (
        "Name,Frequency,Duplex,Tone,CrossMode,RxDtcsCode,DtcsPolarity,Power\n"
        "SYNTH,146.520000,off,Cross,->DTCS,777,NR,5W\n"
    )
    expected = _channel(Tone(), Tone(ToneMode.DCS, 777, TonePolarity.REVERSE), receive_only=True)
    assert import_chirp_csv(source) == [expected]
    row = next(csv.DictReader(StringIO(export_chirp_csv([expected]))))
    assert row["Duplex"] == "off"
    assert row["Offset"] == "0.000000"
    assert tuple(row[field] for field in TONE_COLUMNS) == (
        "Cross", "88.5", "88.5", "023", "NR", "777", "->DTCS",
    )
    assert import_chirp_csv(export_chirp_csv([expected])) == [expected]


@pytest.mark.parametrize(("tone", "cross"), [
    ("", "Tone->Tone"), ("Tone", "Tone->Tone"), ("TSQL", "Tone->Tone"),
    ("DTCS", "Tone->Tone"), ("Cross", "Tone->Tone"),
    ("Cross", "DTCS->"), ("Cross", "->DTCS"),
])
@pytest.mark.parametrize("field", ["DtcsCode", "RxDtcsCode"])
def test_invalid_dcs_cells_keep_field_and_row_context(tone: str, cross: str, field: str) -> None:
    control = {
        "Name": "CONTROL", "Frequency": "146.520000", "Tone": tone, "CrossMode": cross,
        "rToneFreq": "100.0", "cToneFreq": "110.9", "DtcsCode": "001",
        "RxDtcsCode": "777", "DtcsPolarity": "RN",
    }
    output = StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=list(control))
    writer.writeheader()
    writer.writerow(control)
    writer.writerow({**control, "Name": "INVALID", field: "089"})
    with pytest.raises(ValueError, match=f"Invalid CHIRP CSV row 3: {field}: .*octal"):
        import_chirp_csv(output.getvalue())


@pytest.mark.parametrize("code", ["", "  ", "000", "001", "023", "777"])
def test_optional_inactive_dcs_cells_preserve_valid_codes_and_empty_values(code: str) -> None:
    source = (
        "Name,Frequency,DtcsCode,RxDtcsCode,Power\n"
        f"SYNTH,146.520000,{code},{code},5W\n"
    )
    assert import_chirp_csv(source) == [_channel(Tone(), Tone())]
