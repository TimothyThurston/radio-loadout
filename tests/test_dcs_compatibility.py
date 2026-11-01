"""DCS codes are generic octal-digit codes, not a conventional-radio whitelist."""

import csv
import json
from io import StringIO

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from radio_loadout.compatibility import check_chirp_compatibility
from radio_loadout.dcs import format_dcs_code, parse_dcs_code
from radio_loadout.exporters.chirp_csv import export_chirp_csv
from radio_loadout.importers.chirp_csv import import_chirp_csv
from radio_loadout.models import AnalogSettings, Channel, Tone, ToneMode, TonePolarity
from radio_loadout.web.app import ChannelFormData, app

client = TestClient(app)


@pytest.mark.parametrize(("value", "text"), [(23, "023"), (777, "777"), (1, "001"), (0, "000"), (7, "007")])
def test_generic_dcs_model_and_formatter(value: int, text: str) -> None:
    tone = Tone(ToneMode.DCS, value, TonePolarity.REVERSE)
    assert tone.value == value
    assert format_dcs_code(tone.value) == text
    assert parse_dcs_code(text) == value
    assert parse_dcs_code(str(value)) == value


@pytest.mark.parametrize("value", [True, False, 23.5, 23.0, -1, 89, 8, 9, 778, 1000, [], {}, "023"])
def test_universal_dcs_model_rejects_invalid_values_and_types(value: object) -> None:
    with pytest.raises(ValueError):
        Tone(ToneMode.DCS, value)


@pytest.mark.parametrize("field", ["dcs_code", "transmit_dcs_code", "receive_dcs_code"])
@pytest.mark.parametrize("value", [True, False, 23.5, 23.0, -1, 89, 778, "23.5", "023.0", "089", "0001", "True", [], {}])
def test_all_builder_dcs_fields_reject_invalid_input_without_coercion(field: str, value: object) -> None:
    with pytest.raises(ValidationError):
        ChannelFormData(name="BAD", receive_frequency_mhz=146.52, **{field: value})
    channels = [{"name": "BAD", "receive_frequency_mhz": 146.52, field: value}]
    data = {"channels_json": json.dumps(channels)}
    review = client.post("/validation/chirp.csv", data=data).json()
    assert review["compatible"] is False
    assert any(issue["field"] == field and issue["severity"] == "error" for issue in review["issues"])
    assert client.post("/downloads/chirp.csv", data=data).status_code == 422


@pytest.mark.parametrize("field", ["dcs_code", "transmit_dcs_code", "receive_dcs_code"])
@pytest.mark.parametrize(("value", "expected"), [("023", 23), ("777", 777), ("001", 1), ("000", 0)])
def test_builder_accepts_leading_zero_integer_text(field: str, value: str, expected: int) -> None:
    form = ChannelFormData(name="TEST", receive_frequency_mhz=146.52, **{field: value})
    assert getattr(form, field) == expected


def _csv(mode: str, code: str, rx_code: str, polarity: str, cross: str = "DTCS->DTCS") -> str:
    row = {
        "Location": "7", "Name": "GENERIC DCS", "Frequency": "444.500000",
        "Duplex": "+", "Offset": "5.000000", "Tone": mode, "DtcsCode": code,
        "RxDtcsCode": rx_code, "DtcsPolarity": polarity, "CrossMode": cross,
        "rToneFreq": "100.0", "cToneFreq": "110.9", "Power": "2.5W",
        "TStep": "12.5", "Skip": "S", "Comment": "Generic format, radio support varies",
    }
    output = StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=list(row))
    writer.writeheader()
    writer.writerow(row)
    return output.getvalue()


@pytest.mark.parametrize("code", ["023", "777", "001", "000"])
@pytest.mark.parametrize("polarity", ["NN", "NR", "RN", "RR"])
def test_matched_dcs_import_builder_review_and_export(code: str, polarity: str) -> None:
    csv_text = _csv("DTCS", code, "025", polarity)
    original = import_chirp_csv(csv_text)
    imported = client.post("/imports/chirp.csv", files={"file": ("dcs.csv", csv_text, "text/csv")})
    assert imported.status_code == 200
    channels = imported.json()["channels"]
    assert channels[0]["transmit_dcs_code"] == int(code)
    assert channels[0]["receive_dcs_code"] == int(code)
    assert channels[0]["transmit_dcs_polarity"] == polarity[0]
    assert channels[0]["receive_dcs_polarity"] == polarity[1]
    # The quick matched-DCS control must support the same code as imported cross controls.
    matched = {"name": "MATCHED", "receive_frequency_mhz": 444.5, "tone_mode": "dtcs",
               "dcs_code": int(code), "dcs_polarity": polarity}
    for submitted in (channels, [matched]):
        data = {"channels_json": json.dumps(submitted)}
        assert client.post("/validation/chirp.csv", data=data).json()["compatible"] is True
        exported = client.post("/downloads/chirp.csv", data=data)
        assert exported.status_code == 200
        row = next(csv.DictReader(StringIO(exported.text)))
        assert row["DtcsCode"] == code
        assert row["RxDtcsCode"] == code
        assert row["DtcsPolarity"] == polarity
        assert row["Tone"] == "DTCS"
    exported = client.post("/downloads/chirp.csv", data={"channels_json": json.dumps(channels)})
    assert import_chirp_csv(exported.text) == original


@pytest.mark.parametrize("cross", ["DTCS->DTCS", "DTCS->Tone", "Tone->DTCS", "DTCS->", "->DTCS"])
@pytest.mark.parametrize("polarity", ["NR", "RN"])
def test_cross_dcs_codes_and_independent_polarities_survive(cross: str, polarity: str) -> None:
    csv_text = _csv("Cross", "777", "001", polarity, cross)
    original = import_chirp_csv(csv_text)
    response = client.post("/imports/chirp.csv", files={"file": ("cross.csv", csv_text, "text/csv")})
    assert response.status_code == 200
    channels = response.json()["channels"]
    data = {"channels_json": json.dumps(channels)}
    assert client.post("/validation/chirp.csv", data=data).json()["compatible"] is True
    exported = client.post("/downloads/chirp.csv", data=data)
    assert exported.status_code == 200
    assert import_chirp_csv(exported.text) == original


@pytest.mark.parametrize("code", ["True", "23.5", "023.0", "-1", "089", "778", "7777"])
def test_import_rejects_invalid_dcs_text(code: str) -> None:
    csv_text = _csv("DTCS", code, "023", "NN")
    with pytest.raises(ValueError, match="Invalid CHIRP CSV row 2: .*DCS code"):
        import_chirp_csv(csv_text)
    assert client.post("/imports/chirp.csv", files={"file": ("bad.csv", csv_text, "text/csv")}).status_code == 422


@pytest.mark.parametrize("value", [True, 23.5, -1, 89])
def test_direct_export_and_review_cannot_coerce_bad_dcs(value: object) -> None:
    tone = Tone(ToneMode.DCS, 23)
    object.__setattr__(tone, "value", value)
    channel = Channel("BAD", 146_520_000, 146_520_000, analog_settings=AnalogSettings(tone, power_watts=5))
    assert check_chirp_compatibility([channel]).compatible is False
    with pytest.raises((ValueError, TypeError)):
        export_chirp_csv([channel])
