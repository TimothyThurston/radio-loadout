"""Import-loss reports and authoritative resource bounds at adapter and web boundaries."""

import asyncio
import csv
import json
from dataclasses import replace
from importlib import import_module
from io import StringIO

import pytest
from fastapi.testclient import TestClient

from radio_loadout import input_limits
from radio_loadout.exporters.chirp_csv import export_chirp_csv
from radio_loadout.importers.chirp_csv import import_chirp_csv, import_chirp_csv_detailed
from radio_loadout.web.app import _read_csv_upload, app

client = TestClient(app)


def test_builder_embeds_central_limits_and_accessible_import_review() -> None:
    response = client.get("/builder")
    assert response.status_code == 200
    configuration = response.text.split('<script id="input-limits" type="application/json">', 1)[1].split("</script>", 1)[0]
    assert json.loads(configuration) == input_limits.public_limits()
    assert 'id="chirp-import-review" class="compatibility-panel" aria-live="polite"' in response.text
    for control in ("confirm-chirp-import", "cancel-chirp-import"):
        assert f'id="{control}"' in response.text


def source(**changes) -> str:
    row = {"Location": "0", "Name": "TEST", "Frequency": "146.520000", "Power": "5W",
           "Mode": "FM", "TStep": "5", "DtcsPolarity": "NN", **changes}
    output = StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=list(row))
    writer.writeheader()
    writer.writerow(row)
    return output.getvalue()


def test_legacy_import_api_and_detailed_channels_are_identical() -> None:
    text = source()
    result = import_chirp_csv_detailed(text)
    assert result.channels == import_chirp_csv(text)
    assert result.report()["requires_confirmation"] is False
    assert result.messages == []


def test_unsupported_nonempty_columns_report_channel_row_and_discarded_field() -> None:
    result = import_chirp_csv_detailed(source(Bank="Local", URCALL="CQCQCQ", EmptyVendor=""))
    report = result.report()
    assert report["requires_confirmation"] is True
    assert report["loss_count"] == 2
    assert {issue["field"] for issue in report["messages"]} == {"Bank", "URCALL"}
    assert all(issue["row_number"] == 2 and issue["channel_index"] == 0 and issue["channel_name"] == "TEST" for issue in report["messages"])
    assert all("discarded" in issue["message"] for issue in report["messages"])


def test_empty_unused_columns_do_not_create_warnings() -> None:
    result = import_chirp_csv_detailed(source(URCALL="", RPT1CALL=" ", Vendor=""))
    assert result.messages == []
    assert result.report()["requires_confirmation"] is False


@pytest.mark.parametrize(("location", "kind"), [("99", "loss"), ("000", "normalization"), ("", "normalization")])
def test_location_reassignment_is_explicit(location: str, kind: str) -> None:
    result = import_chirp_csv_detailed(source(Location=location))
    issue = next(issue for issue in result.messages if issue.field == "Location")
    assert issue.kind == kind
    assert "Location 0" in issue.message
    assert result.report()["requires_confirmation"] == (kind == "loss")
    assert next(csv.DictReader(StringIO(export_chirp_csv(result.channels))))["Location"] == "0"


def test_default_power_is_a_default_not_information_loss() -> None:
    result = import_chirp_csv_detailed(source(Power=""))
    issue = next(issue for issue in result.messages if issue.field == "Power")
    assert issue.kind == "default"
    assert "5 W" in issue.message
    assert result.channels[0].analog_settings.power_watts is None
    assert result.report()["requires_confirmation"] is False
    response = client.post("/imports/chirp.csv", files={"file": ("default.csv", source(Power=""))})
    assert response.status_code == 200
    assert response.json()["channels"][0]["power_watts"] == 5


@pytest.mark.parametrize(("changes", "field", "expected"), [
    ({"Frequency": "146.5200004"}, "Frequency", "146.520000"),
    ({"Duplex": "+", "Offset": "0.6000004"}, "Offset", "0.600000"),
    ({"Power": "2.5555W"}, "Power", "2.555"),
    ({"Power": "5.00000000000000001W"}, "Power", "5.000"),
    ({"Tone": "Tone", "rToneFreq": "100.04"}, "rToneFreq", "100.0"),
    ({"Tone": "TSQL", "cToneFreq": "100.00000000000000001"}, "cToneFreq", "100.0"),
    ({"Comment": " trim me "}, "Comment", "whitespace"),
])
def test_meaningful_precision_and_text_loss_requires_confirmation(changes: dict, field: str, expected: str) -> None:
    result = import_chirp_csv_detailed(source(**changes))
    issue = next(issue for issue in result.messages if issue.field == field)
    assert issue.kind == "loss"
    assert expected in issue.message
    assert result.report()["requires_confirmation"] is True


def test_expected_tone_and_split_normalization_is_not_information_loss() -> None:
    result = import_chirp_csv_detailed(source(Duplex="split", Offset="147.120000", Tone="DTCS", DtcsCode="023", RxDtcsCode="777"))
    assert result.report()["requires_confirmation"] is False
    assert {issue.kind for issue in result.messages} == {"normalization"}
    assert import_chirp_csv(export_chirp_csv(result.channels)) == result.channels


def test_tsql_precision_messages_identify_the_active_source_column() -> None:
    result = import_chirp_csv_detailed(source(Tone="TSQL", rToneFreq="88.54", cToneFreq="100.04"))
    losses = [issue for issue in result.messages if issue.kind == "loss"]
    assert len(losses) == 2
    assert {issue.field for issue in losses} == {"cToneFreq"}
    assert all("100.04 Hz to 100.0 Hz" in issue.message for issue in losses)


def test_unsupported_settings_and_unrepresentable_builder_comments_are_errors() -> None:
    for text, message in [
        (source(Mode="USB"), "Unsupported channel mode"),
        (source(Comment="line one\nline two"), "multiline Comment"),
        (source(Name="line one\nline two"), "multiline Name"),
    ]:
        response = client.post("/imports/chirp.csv", files={"file": ("bad.csv", text)})
        assert response.status_code == 422
        assert message in response.json()["detail"]


def test_reports_are_bounded_without_hiding_confirmation_requirement(monkeypatch) -> None:
    monkeypatch.setattr(input_limits, "LIMITS", replace(input_limits.LIMITS, import_messages=1, report_text_chars=80))
    result = import_chirp_csv_detailed(source(Bank="data", Vendor="data", Location="99"))
    assert len(result.messages) == 1
    assert result.omitted_messages == 2
    assert result.loss_count == 3
    assert result.report()["requires_confirmation"] is True


def test_row_and_channel_limits_include_exact_boundaries_and_blank_records(monkeypatch) -> None:
    monkeypatch.setattr(input_limits, "LIMITS", replace(input_limits.LIMITS, csv_rows=2, channels=2))
    two = "Name,Frequency\nFIRST,146.52\nSECOND,446\n"
    assert len(import_chirp_csv(two)) == 2
    assert len(import_chirp_csv("Name,Frequency\nFIRST,146.52\n\n")) == 1
    with pytest.raises(input_limits.InputLimitError, match="row limit"):
        import_chirp_csv(two + "\n")
    monkeypatch.setattr(input_limits, "LIMITS", replace(input_limits.LIMITS, csv_rows=10, channels=1))
    assert len(import_chirp_csv("Name,Frequency\nFIRST,146.52\n")) == 1
    with pytest.raises(input_limits.InputLimitError, match="channel limit"):
        import_chirp_csv(two)
    assert client.post("/imports/chirp.csv", files={"file": ("too-many.csv", two)}).status_code == 413
    one = import_chirp_csv("Name,Frequency\nFIRST,146.52\n")
    assert len(import_chirp_csv(export_chirp_csv(one))) == 1
    with pytest.raises(input_limits.InputLimitError, match="channel limit"):
        export_chirp_csv(channel for channel in one * 2)


@pytest.mark.parametrize("endpoint", ["/validation/chirp.csv", "/downloads/chirp.csv"])
def test_submitted_utf8_byte_limit_boundaries(endpoint: str, monkeypatch) -> None:
    payload = json.dumps([{"name": "Café", "receive_frequency_mhz": 146.52}], ensure_ascii=False)
    maximum = len(payload.encode("utf-8")) + 5
    monkeypatch.setattr(input_limits, "LIMITS", replace(input_limits.LIMITS, channels_json_bytes=maximum))
    assert client.post(endpoint, data={"channels_json": payload + " " * 5}).status_code == 200
    response = client.post(endpoint, data={"channels_json": payload + " " * 6})
    assert response.status_code == 413
    assert f"{maximum}-byte" in response.json()["detail"]


@pytest.mark.parametrize("endpoint", ["/validation/chirp.csv", "/downloads/chirp.csv"])
def test_multipart_json_field_uses_application_limit_instead_of_framework_default(endpoint: str) -> None:
    payload = json.dumps([{"name": "TEST", "receive_frequency_mhz": 146.52}])
    payload += " " * (input_limits.LIMITS.channels_json_bytes - len(payload))
    # This is deliberately above Starlette's usual 1 MiB non-file part default.
    assert client.post(endpoint, files={"channels_json": (None, payload)}).status_code == 200
    assert client.post(endpoint, files={"channels_json": (None, payload + " ")}).status_code == 413


@pytest.mark.parametrize("endpoint", ["/validation/chirp.csv", "/downloads/chirp.csv"])
def test_channel_count_checked_before_model_validation(endpoint: str, monkeypatch) -> None:
    monkeypatch.setattr(input_limits, "LIMITS", replace(input_limits.LIMITS, channels=1))
    web_app = import_module("radio_loadout.web.app")
    def should_not_validate(*args):
        raise AssertionError("Oversized document must not reach model construction")
    monkeypatch.setattr(web_app.CHANNEL_FORM_LIST, "validate_json", should_not_validate)
    assert client.post(endpoint, data={"channels_json": "[{},{}]"}).status_code == 413


def test_upload_reader_is_bounded_and_rejects_before_utf8_decode(monkeypatch) -> None:
    monkeypatch.setattr(input_limits, "LIMITS", replace(input_limits.LIMITS, csv_upload_bytes=32, read_chunk_bytes=7))
    class Upload:
        def __init__(self, data):
            self.data, self.position, self.reads = data, 0, []
        async def read(self, size):
            self.reads.append(size)
            chunk = self.data[self.position:self.position + size]
            self.position += len(chunk)
            return chunk
    exact = Upload(b"a" * 32)
    assert asyncio.run(_read_csv_upload(exact)) == b"a" * 32
    assert max(exact.reads) <= 7
    oversized = Upload(b"a" * 100)
    with pytest.raises(input_limits.InputLimitError):
        asyncio.run(_read_csv_upload(oversized))
    assert oversized.position == 33
    assert max(oversized.reads) <= 7
    response = client.post("/imports/chirp.csv", files={"file": ("large.csv", b"\xff" * 33)})
    assert response.status_code == 413


def test_csv_byte_boundaries_and_process_global_parser_settings(monkeypatch) -> None:
    text = "Name,Frequency,Comment\nTEST,146.52,"
    maximum = len(text.encode()) + 5
    monkeypatch.setattr(input_limits, "LIMITS", replace(input_limits.LIMITS, csv_upload_bytes=maximum))
    before = csv.field_size_limit()
    assert len(import_chirp_csv(text + " " * 5)) == 1
    assert client.post("/imports/chirp.csv", files={"file": ("exact.csv", text + " " * 5)}).status_code == 200
    with pytest.raises(input_limits.InputLimitError):
        import_chirp_csv(text + " " * 6)
    assert csv.field_size_limit() == before


def test_duplicate_headers_and_broken_quoting_do_not_silently_drop_data() -> None:
    for text in ["Name,Frequency,Comment,Comment\nTEST,146.52,first,second\n", 'Name,Frequency,Comment\nTEST,146.52,"unclosed']:
        with pytest.raises(ValueError, match="duplicate|Invalid CHIRP CSV"):
            import_chirp_csv(text)


def test_untrusted_column_and_channel_names_are_json_data_not_markup() -> None:
    attack = "<img src=x onerror=alert(1)>"
    response = client.post("/imports/chirp.csv", files={"file": ("untrusted.csv", source(Name=attack, **{"<script>bad()</script>": "value"}))})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    report = response.json()["import_report"]
    assert report["requires_confirmation"] is True
    assert report["messages"][0]["channel_name"] == attack
    assert report["messages"][0]["field"] == "<script>bad()</script>"


def test_form_endpoint_openapi_contract_is_preserved() -> None:
    schema = app.openapi()
    for endpoint in ("/validation/chirp.csv", "/downloads/chirp.csv"):
        content = schema["paths"][endpoint]["post"]["requestBody"]["content"]
        for content_type in ("application/x-www-form-urlencoded", "multipart/form-data"):
            assert content[content_type]["schema"]["properties"]["channels_json"]["type"] == "string"
