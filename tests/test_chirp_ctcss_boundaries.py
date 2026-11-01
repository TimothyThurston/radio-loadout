"""CHIRP's strict CTCSS limits apply to source values and actual CSV cells."""

import csv
import json
from io import StringIO

import pytest
from fastapi.testclient import TestClient

from radio_loadout.compatibility import check_chirp_compatibility
from radio_loadout.exporters.chirp_csv import export_chirp_csv
from radio_loadout.importers.chirp_csv import import_chirp_csv
from radio_loadout.models import AnalogSettings, Channel, Tone, ToneMode
from radio_loadout.web.app import app

client = TestClient(app)
PATHS = ("tone", "tsql", "cross_tx", "cross_rx", "cross_rx_only", "cross_ctcss_tx", "cross_ctcss_rx")
BAD_EXPORT_VALUES = (50.0, 300.0, 50.001, 50.04, 50.049, 299.951, 299.96, 299.999)
# Include nonstandard dropdown values and safe rounding on either side.
VALID_EXPORT_VALUES = ((50.06, "50.1"), (50.1, "50.1"), (299.94, "299.9"),
                       (299.9, "299.9"), (100.0, "100.0"), (100.1, "100.1"), (123.4, "123.4"))


def _channel(path: str, value: float, name: str = "CTCSS TEST") -> Channel:
    ctcss = Tone(ToneMode.CTCSS, value)
    control = Tone(ToneMode.CTCSS, 110.9)
    dcs = Tone(ToneMode.DCS, 23)
    tx, rx = {
        "tone": (ctcss, Tone()),
        "tsql": (ctcss, ctcss),
        "cross_tx": (ctcss, dcs),
        "cross_rx": (dcs, ctcss),
        "cross_rx_only": (Tone(), ctcss),
        "cross_ctcss_tx": (ctcss, control),
        "cross_ctcss_rx": (control, ctcss),
    }[path]
    return Channel(name, 146_520_000, 146_520_000, analog_settings=AnalogSettings(tx, rx, 5))


def _affected_fields(path: str) -> set[str]:
    if path == "tsql":
        return {"transmit_tone", "receive_tone"}
    return {"receive_tone" if path in {"cross_rx", "cross_rx_only", "cross_ctcss_rx"} else "transmit_tone"}


def _form_channel(path: str, value: float) -> dict:
    channel = {"name": "CTCSS TEST", "receive_frequency_mhz": 146.52, "power_watts": 5}
    if path in {"tone", "tsql"}:
        return channel | {"tone_mode": path, "tone_frequency_hz": value}
    forms = {
        "cross_tx": {"transmit_tone_mode": "ctcss", "transmit_ctcss_frequency_hz": value,
                     "receive_tone_mode": "dcs", "receive_dcs_code": 23},
        "cross_rx": {"transmit_tone_mode": "dcs", "transmit_dcs_code": 23,
                     "receive_tone_mode": "ctcss", "receive_ctcss_frequency_hz": value},
        "cross_rx_only": {"receive_tone_mode": "ctcss", "receive_ctcss_frequency_hz": value},
        "cross_ctcss_tx": {"transmit_tone_mode": "ctcss", "transmit_ctcss_frequency_hz": value,
                           "receive_tone_mode": "ctcss", "receive_ctcss_frequency_hz": 110.9},
        "cross_ctcss_rx": {"transmit_tone_mode": "ctcss", "transmit_ctcss_frequency_hz": 110.9,
                           "receive_tone_mode": "ctcss", "receive_ctcss_frequency_hz": value},
    }
    return channel | {"tone_mode": "cross"} | forms[path]


def _source_csv(path: str, value: float) -> str:
    row = {
        "Name": "CTCSS TEST", "Frequency": "146.520000", "Power": "5W",
        "rToneFreq": "110.9", "cToneFreq": "110.9", "DtcsCode": "023",
        "RxDtcsCode": "023", "DtcsPolarity": "NN",
    }
    if path == "tone":
        row.update(Tone="Tone", rToneFreq=str(value))
    elif path == "tsql":
        row.update(Tone="TSQL", cToneFreq=str(value))
    else:
        row.update(Tone="Cross", CrossMode={
            "cross_tx": "Tone->DTCS", "cross_rx": "DTCS->Tone", "cross_rx_only": "->Tone",
            "cross_ctcss_tx": "Tone->Tone", "cross_ctcss_rx": "Tone->Tone",
        }[path])
        row["cToneFreq" if "receive_tone" in _affected_fields(path) else "rToneFreq"] = str(value)
    output = StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=list(row))
    writer.writeheader()
    writer.writerow(row)
    return output.getvalue()


@pytest.mark.parametrize("value", [50.0, 300.0])
def test_universal_tone_model_is_not_restricted_by_chirp(value: float) -> None:
    assert Tone(ToneMode.CTCSS, value).value == value


@pytest.mark.parametrize("path", PATHS)
@pytest.mark.parametrize("value", BAD_EXPORT_VALUES)
def test_review_and_direct_export_reject_ctcss_boundaries(path: str, value: float) -> None:
    channels = [_channel("tone", 100, "CONTROL"), _channel(path, value)]
    report = check_chirp_compatibility(channels)
    assert report.compatible is False
    errors = [issue for issue in report.issues if issue.severity == "error"]
    assert {issue.field for issue in errors} == _affected_fields(path)
    assert all(issue.channel_index == 1 and issue.channel_name == "CTCSS TEST" for issue in errors)
    assert all("50.0" in issue.message and "300.0" in issue.message for issue in errors)
    if 50 < value < 300:
        assert all("rounds to" in issue.message for issue in errors)
    with pytest.raises(ValueError, match="CTCSS.*strictly greater than 50.0.*strictly less than 300.0"):
        export_chirp_csv(channels)


@pytest.mark.parametrize("path", PATHS)
@pytest.mark.parametrize(("value", "expected_cell"), VALID_EXPORT_VALUES)
def test_nearby_and_intermediate_ctcss_remain_exportable(path: str, value: float, expected_cell: str) -> None:
    channel = _channel(path, value)
    assert check_chirp_compatibility([channel]).compatible is True
    row = next(csv.DictReader(StringIO(export_chirp_csv([channel]))))
    for field in _affected_fields(path):
        assert row["rToneFreq" if field == "transmit_tone" else "cToneFreq"] == expected_cell
    reimported = import_chirp_csv(export_chirp_csv([channel]))[0]
    for field in _affected_fields(path):
        assert getattr(reimported.analog_settings, field).value == float(expected_cell)


@pytest.mark.parametrize("path", PATHS)
@pytest.mark.parametrize("value", [50.0, 300.0, 50.04, 299.96])
def test_endpoints_report_affected_tone_and_refuse_csv(path: str, value: float) -> None:
    channels = [_form_channel("tone", 100), _form_channel(path, value)]
    data = {"channels_json": json.dumps(channels)}
    review = client.post("/validation/chirp.csv", data=data)
    assert review.status_code == 200
    assert review.json()["compatible"] is False
    errors = [issue for issue in review.json()["issues"] if issue["severity"] == "error"]
    assert {issue["field"] for issue in errors} == _affected_fields(path)
    assert all(issue["channel_index"] == 1 and issue["channel_name"] == "CTCSS TEST" for issue in errors)
    download = client.post("/downloads/chirp.csv", data=data)
    assert download.status_code == 422
    assert "Channel 2 (CTCSS TEST)" in download.json()["detail"]
    assert "50.0" in download.json()["detail"]
    assert "300.0" in download.json()["detail"]


@pytest.mark.parametrize("path", PATHS)
@pytest.mark.parametrize("value", [50.1, 299.9, 100.0, 100.1])
def test_endpoints_allow_supported_nonstandard_ctcss(path: str, value: float) -> None:
    data = {"channels_json": json.dumps([_form_channel(path, value)])}
    review = client.post("/validation/chirp.csv", data=data)
    assert review.status_code == 200
    assert review.json()["compatible"] is True
    download = client.post("/downloads/chirp.csv", data=data)
    assert download.status_code == 200
    assert download.headers["content-type"].startswith("text/csv")
    assert check_chirp_compatibility(import_chirp_csv(download.text)).compatible is True


@pytest.mark.parametrize("path", PATHS)
@pytest.mark.parametrize("value", [50.0, 300.0])
def test_import_rejects_chirp_source_boundaries(path: str, value: float) -> None:
    csv_text = _source_csv(path, value)
    with pytest.raises(ValueError, match="Invalid CHIRP CSV row 2: .*strictly greater than 50.0"):
        import_chirp_csv(csv_text)
    response = client.post("/imports/chirp.csv", files={"file": ("boundary.csv", csv_text, "text/csv")})
    assert response.status_code == 422
    assert "strictly less than 300.0" in response.json()["detail"]


@pytest.mark.parametrize(("path", "field"), [
    ("none", "rToneFreq"), ("none", "cToneFreq"),
    ("dtcs", "rToneFreq"), ("dtcs", "cToneFreq"),
    ("tone", "cToneFreq"), ("tsql", "rToneFreq"),
    ("cross_tx", "cToneFreq"), ("cross_rx", "rToneFreq"),
])
@pytest.mark.parametrize("value", [50.0, 300.0])
def test_import_also_validates_populated_inactive_ctcss_cells(path: str, field: str, value: float) -> None:
    row = next(csv.DictReader(StringIO(_source_csv(path if path in PATHS else "tone", 100))))
    if path in {"none", "dtcs"}:
        row["Tone"] = "DTCS" if path == "dtcs" else ""
    row[field] = str(value)
    output = StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=list(row))
    writer.writeheader()
    writer.writerow(row)
    with pytest.raises(ValueError, match=f"Invalid CHIRP CSV row 2: {field}: .*strictly greater"):
        import_chirp_csv(output.getvalue())


@pytest.mark.parametrize("path", PATHS)
@pytest.mark.parametrize("value", [50.1, 299.9, 100.0, 100.1])
def test_import_accepts_and_preserves_supported_nonstandard_ctcss(path: str, value: float) -> None:
    channels = import_chirp_csv(_source_csv(path, value))
    assert channels == [_channel(path, value)]
    assert import_chirp_csv(export_chirp_csv(channels)) == channels


@pytest.mark.parametrize("path", PATHS)
@pytest.mark.parametrize("value", [50.04, 299.96])
def test_import_retains_valid_source_precision_but_cannot_export_to_boundary(path: str, value: float) -> None:
    # CHIRP can read these interior values. Our one-decimal output cannot preserve
    # them safely, so import is allowed while review/export reject the rounding.
    channels = import_chirp_csv(_source_csv(path, value))
    assert channels == [_channel(path, value)]
    assert check_chirp_compatibility(channels).compatible is False
    with pytest.raises(ValueError, match="rounds to"):
        export_chirp_csv(channels)
