"""Tests for the Radio Loadout web application."""

import csv
import json
from io import StringIO

import pytest
from fastapi.testclient import TestClient

from radio_loadout.web.app import app

client = TestClient(app)


@pytest.mark.parametrize("encoding", ["utf-8", "utf-8-sig"])
def test_chirp_import_returns_builder_channels(encoding: str) -> None:
    csv_text = (
        "Name,Frequency,Duplex,Offset,Mode,Tone,rToneFreq,cToneFreq,"
        "DtcsCode,RxDtcsCode,DtcsPolarity,CrossMode,Power,TStep,Skip,Comment\n"
        "Répéteur,146.94,-,0.6,FM,Tone,100,,,,NN,,2.5W,12.5,S,Local\n"
        "Weather,162.55,off,,NFM,,,,,,NN,,,25,P,Receive only\n"
        "DCS,444.5,+,5,FM,DTCS,,,023,023,NR,,5W,5,,\n"
        "Cross,446,,0,FM,Cross,123,,023,025,NR,Tone->DTCS,5W,5,,\n"
        "Squelch,145.5,,0,FM,TSQL,88.5,88.5,,,NN,,5W,5,,\n"
    )
    response = client.post(
        "/imports/chirp.csv",
        files={"file": ("channels.csv", csv_text.encode(encoding), "text/csv")},
    )

    assert response.status_code == 200, response.text
    channels = response.json()["channels"]
    assert len(channels) == 5
    assert channels[0]["name"] == "Répéteur"
    assert channels[0]["receive_frequency_mhz"] == 146.94
    assert channels[0]["transmit_frequency_mhz"] == 146.34
    assert channels[0]["power_watts"] == 2.5
    assert channels[0]["tuning_step_khz"] == 12.5
    assert channels[0]["scan_behavior"] == "S"
    assert channels[0]["comment"] == "Local"
    assert channels[0]["transmit_ctcss_frequency_hz"] == 100
    assert channels[1]["receive_only"] is True
    assert channels[1]["transmit_frequency_mhz"] is None
    assert channels[1]["mode"] == "NFM"
    assert channels[1]["power_watts"] == 5
    assert channels[1]["tone_mode"] == "none"
    assert channels[2]["transmit_dcs_code"] == 23
    assert channels[2]["receive_dcs_polarity"] == "R"
    assert channels[3]["tone_mode"] == "cross"
    assert channels[3]["transmit_tone_mode"] == "ctcss"
    assert channels[3]["receive_tone_mode"] == "dcs"
    assert channels[3]["receive_dcs_code"] == 25

    exported = client.post(
        "/downloads/chirp.csv", data={"channels_json": json.dumps(channels)},
    )
    assert exported.status_code == 200
    rows = _read_csv_response(exported.text)
    assert [row["Tone"] for row in rows] == ["Tone", "", "DTCS", "Cross", "TSQL"]
    assert rows[2]["DtcsPolarity"] == "NR"
    assert rows[3]["CrossMode"] == "Tone->DTCS"


@pytest.mark.parametrize(("content", "message"), [
    (b"\xff", "UTF-8"),
    (b"", "CSV header"),
    (b"Location,Comment\n0,Missing data\n", "missing required columns"),
    (b"Name,Frequency\n", "does not contain any channels"),
    (b"Name,Frequency\nBAD,nope\n", "Invalid CHIRP CSV row 2"),
    (b"Name,Frequency\nBAD,1e308\n", "Invalid CHIRP CSV row 2: Frequency is too large"),
    (b"Name,Frequency\nBAD,146.52,extra\n", "row 2: too many columns"),
    (b"Name,Frequency,Tone,DtcsCode\nBAD,146.52,DTCS,001\n", "standard DCS code"),
])
def test_chirp_import_rejects_invalid_file(content: bytes, message: str) -> None:
    response = client.post(
        "/imports/chirp.csv",
        files={"file": ("invalid.csv", content, "text/csv")},
    )
    assert response.status_code == 422
    assert message in response.json()["detail"]


def test_chirp_import_requires_upload() -> None:
    response = client.post("/imports/chirp.csv")
    assert response.status_code == 422


def _read_csv_response(
    response_text: str,
) -> list[dict[str, str]]:
    return list(csv.DictReader(StringIO(response_text)))


def test_home() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "text/html"
    )
    assert "Radio Loadout" in response.text


def test_builder_page() -> None:
    response = client.get("/builder")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "text/html"
    )
    assert "Build your radio loadout" in response.text
    assert "Generate CHIRP CSV" in response.text
    assert "Tuning step (kHz)" in response.text
    assert "Scan behavior" in response.text
    assert "data-move-channel-up" in response.text
    assert "data-move-channel-down" in response.text
    assert "data-duplicate-channel" in response.text


def test_chirp_sample_download() -> None:
    response = client.get("/downloads/chirp-sample.csv")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "text/csv"
    )
    assert response.headers["content-disposition"] == (
        'attachment; filename="radio_loadout_sample.csv"'
    )

    rows = _read_csv_response(response.text)

    assert len(rows) == 4
    assert rows[0]["Name"] == "2M CALL"
    assert rows[0]["Frequency"] == "146.520000"
    assert rows[0]["TStep"] == "5.00"
    assert rows[0]["Skip"] == ""

    assert rows[3]["Name"] == "NOAA 7"
    assert rows[3]["Frequency"] == "162.550000"
    assert rows[3]["Duplex"] == "off"
    assert rows[3]["Mode"] == "NFM"
    assert rows[3]["Skip"] == "P"


def test_custom_chirp_download() -> None:
    channels = [
        {
            "name": "TEST RPT",
            "receive_frequency_mhz": 146.94,
            "transmit_frequency_mhz": 146.34,
            "mode": "FM",
            "power_watts": 5.0,
            "receive_only": False,
            "tone_mode": "tone",
            "tone_frequency_hz": 100.0,
            "comment": "Radio Loadout custom channel",
        },
        {
            "name": "NOAA 7",
            "receive_frequency_mhz": 162.55,
            "transmit_frequency_mhz": None,
            "mode": "NFM",
            "power_watts": 5.0,
            "receive_only": True,
            "tone_mode": "none",
            "tone_frequency_hz": None,
            "comment": "Receive-only weather radio",
        },
    ]

    response = client.post(
        "/downloads/chirp.csv",
        data={"channels_json": json.dumps(channels)},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "text/csv"
    )
    assert response.headers["content-disposition"] == (
        'attachment; filename="radio_loadout_custom.csv"'
    )

    rows = _read_csv_response(response.text)

    assert len(rows) == 2

    assert rows[0]["Name"] == "TEST RPT"
    assert rows[0]["Frequency"] == "146.940000"
    assert rows[0]["Duplex"] == "-"
    assert rows[0]["Offset"] == "0.600000"
    assert rows[0]["Mode"] == "FM"
    assert rows[0]["Tone"] == "Tone"
    assert rows[0]["rToneFreq"] == "100.0"
    assert rows[0]["TStep"] == "5.00"
    assert rows[0]["Skip"] == ""

    assert rows[1]["Name"] == "NOAA 7"
    assert rows[1]["Frequency"] == "162.550000"
    assert rows[1]["Duplex"] == "off"
    assert rows[1]["Mode"] == "NFM"


def test_custom_dcs_chirp_download() -> None:
    channels = [
        {
            "name": "DCS TEST",
            "receive_frequency_mhz": 444.5,
            "transmit_frequency_mhz": 449.5,
            "mode": "FM",
            "power_watts": 5.0,
            "receive_only": False,
            "tone_mode": "dtcs",
            "dcs_code": 23,
            "dcs_polarity": "NR",
            "comment": "Matched DCS test",
        }
    ]

    response = client.post(
        "/downloads/chirp.csv",
        data={"channels_json": json.dumps(channels)},
    )

    assert response.status_code == 200

    rows = _read_csv_response(response.text)

    assert len(rows) == 1
    assert rows[0]["Name"] == "DCS TEST"
    assert rows[0]["Tone"] == "DTCS"
    assert rows[0]["DtcsCode"] == "023"
    assert rows[0]["RxDtcsCode"] == "023"
    assert rows[0]["DtcsPolarity"] == "NR"


def test_custom_cross_tone_download() -> None:
    channels = [
        {
            "name": "CROSS TEST",
            "receive_frequency_mhz": 146.94,
            "transmit_frequency_mhz": 146.34,
            "mode": "FM",
            "power_watts": 5.0,
            "receive_only": False,
            "tone_mode": "cross",
            "transmit_tone_mode": "ctcss",
            "transmit_ctcss_frequency_hz": 100.0,
            "transmit_dcs_polarity": "N",
            "receive_tone_mode": "dcs",
            "receive_dcs_code": 23,
            "receive_dcs_polarity": "R",
            "comment": "Cross tone test",
        }
    ]

    response = client.post(
        "/downloads/chirp.csv",
        data={"channels_json": json.dumps(channels)},
    )

    assert response.status_code == 200

    rows = _read_csv_response(response.text)

    assert len(rows) == 1
    assert rows[0]["Name"] == "CROSS TEST"
    assert rows[0]["Tone"] == "Cross"
    assert rows[0]["rToneFreq"] == "100.0"
    assert rows[0]["RxDtcsCode"] == "023"
    assert rows[0]["DtcsPolarity"] == "NR"
    assert rows[0]["CrossMode"] == "Tone->DTCS"


def test_custom_tuning_step_and_scan_behavior() -> None:
    channels = [
        {
            "name": "SCAN TEST",
            "receive_frequency_mhz": 446.0,
            "transmit_frequency_mhz": 446.0,
            "mode": "FM",
            "power_watts": 5.0,
            "receive_only": False,
            "tone_mode": "none",
            "tuning_step_khz": 12.5,
            "scan_behavior": "S",
            "comment": "Skipped during scanning",
        }
    ]

    response = client.post(
        "/downloads/chirp.csv",
        data={"channels_json": json.dumps(channels)},
    )

    assert response.status_code == 200

    rows = _read_csv_response(response.text)

    assert len(rows) == 1
    assert rows[0]["Name"] == "SCAN TEST"
    assert rows[0]["TStep"] == "12.50"
    assert rows[0]["Skip"] == "S"


def test_builder_autosave_assets() -> None:
    page_response = client.get("/builder")
    script_response = client.get("/static/builder.js")

    assert page_response.status_code == 200
    assert 'id="clear-draft"' in page_response.text
    assert 'id="draft-status"' in page_response.text

    assert script_response.status_code == 200
    assert (
        "radio-loadout-builder-draft-v1"
        in script_response.text
    )
    assert "window.localStorage" in script_response.text
    assert "restoreDraft" in script_response.text
    assert "clearDraft" in script_response.text


def test_builder_noaa_weather_preset_assets() -> None:
    page_response = client.get("/builder")
    script_response = client.get("/static/builder.js")

    assert page_response.status_code == 200
    assert 'id="add-noaa-weather"' in page_response.text
    assert 'id="preset-status"' in page_response.text
    assert "Add NOAA Weather" in page_response.text

    assert script_response.status_code == 200
    assert "NOAA_WEATHER_CHANNELS" in script_response.text
    assert "addNoaaWeatherPreset" in script_response.text
    assert "existingFrequencies" in script_response.text
    assert "tuning_step_khz: 25" in script_response.text

    for channel_number in range(1, 8):
        assert (
            f'name: "NOAA {channel_number}"'
            in script_response.text
        )

    for frequency in (
        "162.4",
        "162.425",
        "162.45",
        "162.475",
        "162.5",
        "162.525",
        "162.55",
    ):
        assert (
            f"receive_frequency_mhz: {frequency}"
            in script_response.text
        )


def test_builder_amateur_calling_preset_assets() -> None:
    page_response = client.get("/builder")
    script_response = client.get("/static/builder.js")

    assert page_response.status_code == 200
    assert (
        'id="add-amateur-calling"'
        in page_response.text
    )
    assert "Add Amateur Calling" in page_response.text

    assert script_response.status_code == 200
    assert (
        "AMATEUR_CALLING_CHANNELS"
        in script_response.text
    )
    assert (
        "addAmateurCallingPreset"
        in script_response.text
    )

    for channel_name in (
        "2M CALL",
        "1.25 CALL",
        "70CM CALL",
    ):
        assert (
            f'name: "{channel_name}"'
            in script_response.text
        )

    for frequency in (
        "146.52",
        "223.5",
        "446.0",
    ):
        assert (
            f"receive_frequency_mhz: {frequency}"
            in script_response.text
        )


def test_builder_validation_feedback_assets() -> None:
    page_response = client.get("/builder")
    script_response = client.get("/static/builder.js")

    assert page_response.status_code == 200
    assert 'id="form-message"' in page_response.text
    assert 'id="generate-csv"' in page_response.text

    assert script_response.status_code == 200
    assert "submitChannelForm" in script_response.text
    assert "window.fetch" in script_response.text
    assert "getResponseErrorMessage" in script_response.text
    assert "URL.createObjectURL" in script_response.text


def test_builder_chirp_import_assets() -> None:
    page_response = client.get("/builder")
    script_response = client.get("/static/builder.js")

    assert page_response.status_code == 200
    assert 'id="chirp-csv-file" type="file" accept=".csv"' in page_response.text
    assert 'id="import-chirp-csv"' in page_response.text
    assert "Import CHIRP CSV" in page_response.text
    assert "A successful import replaces the current channels." in page_response.text

    assert script_response.status_code == 200
    script = script_response.text
    assert 'bindBuilderEvent(importChirpCsvButton, "click", importChirpCsv)' in script
    import_handler = script.split("async function importChirpCsv() {", 1)[1].split(
        "async function submitChannelForm", 1,
    )[0]
    assert 'upload.append("file", file)' in import_handler
    assert 'window.fetch("/imports/chirp.csv"' in import_handler
    assert 'method: "POST"' in import_handler
    assert "getResponseErrorMessage(response, fallbackMessage)" in import_handler
    assert "Array.isArray(result.channels)" in import_handler
    assert import_handler.index("if (!response.ok)") < import_handler.index(
        "replaceChannelCards(result.channels)"
    ) < import_handler.index("saveDraft()")
    assert 'showFormMessage("Choose a CHIRP CSV file to import.", "error")' in import_handler
    assert '"success"' in import_handler
    assert 'chirpCsvFileInput.value = ""' in import_handler
    assert "finally" in import_handler
    assert "importChirpCsvButton.disabled = false" in import_handler
    assert "chirpCsvFileInput.disabled = false" in import_handler
    failure_handler = import_handler.split("} catch (error) {", 1)[1]
    assert "showFormMessage" in failure_handler
    assert "replaceChannelCards" not in failure_handler
    assert "saveDraft" not in failure_handler


def test_builder_import_reuses_draft_card_restoration() -> None:
    response = client.get("/static/builder.js")
    assert response.status_code == 200
    script = response.text
    replacement = script.split("function replaceChannelCards(channels) {", 1)[1].split(
        "function restoreDraft", 1,
    )[0]
    assert "document.createDocumentFragment()" in replacement
    assert "createChannelCard(replacement)" in replacement
    assert "applyDraftToCard(card, cardDraft)" in replacement
    assert replacement.index("initializeChannelCard(card)") < replacement.index(
        "channelList.replaceChildren(replacement)"
    ) < replacement.index("updateChannelNumbers()")
    assert "replaceChannelCards(savedDraft)" in script
    assert 'field.checked = Boolean(value)' in script
    assert 'field.matches("[data-ctcss-select]")' in script
    assert "Number(value).toFixed(1)" in script
    assert "field.value = toneValue" in script


def test_builder_backup_controls() -> None:
    response = client.get("/builder")
    assert response.status_code == 200
    assert 'id="export-backup" class="button button-secondary" type="button"' in response.text
    assert '<script src="/static/builder.js?v=3" defer></script>' in response.text
    assert 'id="import-backup"' in response.text
    assert 'id="backup-file" type="file" accept=".json"' in response.text
    assert "Export Backup" in response.text
    assert "Import Backup" in response.text
    assert "Radio Loadout JSON backup" in response.text


def test_builder_backup_serialization_assets() -> None:
    response = client.get("/static/builder.js")
    assert response.status_code == 200
    script = response.text
    assert 'document.querySelector("#export-backup")' in script
    assert 'bindBuilderEvent(exportBackupButton, "click", exportBackup)' in script
    assert 'bindBuilderEvent(importBackupButton, "click", importBackup)' in script
    export = script.split("function exportBackup() {", 1)[1].split(
        "async function importBackup", 1,
    )[0]
    assert 'format: "radio-loadout"' in export
    assert "version: 1" in export
    # Draft snapshots preserve hidden controls as well as the active tone preset.
    assert "channels: getChannelCards().map(getCardDraft)" in export
    assert "JSON.stringify(backup, null, 2)" in export
    assert 'type: "application/json;charset=utf-8"' in export
    assert 'downloadBlob(blob, "radio_loadout_backup.json")' in export
    assert export.index("downloadBlob(") < export.index('"success"')
    assert "Backup download requested" in export
    assert "channelDataFromCard" not in export


def test_builder_download_and_initialization_assets() -> None:
    response = client.get("/static/builder.js?v=3")
    assert response.status_code == 200
    script = response.text
    download = script.split("function downloadBlob(blob, filename) {", 1)[1].split(
        "function validateBackup", 1,
    )[0]
    assert "URL.createObjectURL(blob)" in download
    assert 'document.createElement("a")' in download
    assert "anchor.href = objectUrl" in download
    assert "anchor.download = filename" in download
    assert 'anchor.style.display = "none"' in download
    assert download.index("document.body.appendChild(anchor)") < download.index(
        "anchor.click()"
    ) < download.index("anchor?.remove()") < download.index("URL.revokeObjectURL")
    assert "finally" in download
    assert "}, 1000)" in download
    registration = script.split("function bindBuilderEvent(element, eventName, handler) {", 1)[1]
    assert registration.index("if (!element)") < registration.index("element.addEventListener")
    assert "console.warn" in registration
    assert 'console.error("Builder initialization failed:", error)' in registration
    assert 'console.error("Backup export failed:", error)' in script


def test_builder_backup_validation_and_restore_assets() -> None:
    response = client.get("/static/builder.js")
    assert response.status_code == 200
    script = response.text
    validation = script.split("function validateBackup(backup) {", 1)[1].split(
        "function exportBackup", 1,
    )[0]
    assert 'backup.format !== "radio-loadout"' in validation
    assert "backup.version !== 1" in validation
    assert "Array.isArray(backup.channels)" in validation
    assert "backup.channels.length === 0" in validation
    assert "Object.hasOwn(channel, name)" in validation
    assert 'typeof value !== "boolean"' in validation
    assert 'typeof value !== "string"' in validation
    assert "field.options" in validation
    assert "Number.isFinite" in validation
    assert "field.validity.rangeUnderflow" in validation
    assert "field.maxLength" in validation

    restore = script.split("async function importBackup() {", 1)[1].split(
        "async function importChirpCsv", 1,
    )[0]
    assert "await file.text()" in restore
    assert "JSON.parse" in restore
    assert restore.index("validateBackup(backup)") < restore.index(
        "replaceChannelCards(channels)"
    ) < restore.index("saveDraft()")
    assert "window.fetch" not in restore
    assert "import_chirp_csv" not in restore
    assert "getResponseErrorMessage" not in restore
    assert "not valid JSON" in restore
    assert '"success"' in restore
    failure = restore.split("} catch (error) {", 1)[1]
    assert "showFormMessage" in failure
    assert "replaceChannelCards" not in failure
    assert "saveDraft" not in failure
    assert "importBackupButton.disabled = false" in failure
    assert "backupFileInput.disabled = false" in failure


def test_invalid_channel_returns_specific_message() -> None:
    channels = [
        {
            "name": "INVALID CROSS",
            "receive_frequency_mhz": 146.94,
            "transmit_frequency_mhz": 146.34,
            "tone_mode": "cross",
            "transmit_tone_mode": "none",
            "receive_tone_mode": "none",
        }
    ]

    response = client.post(
        "/downloads/chirp.csv",
        data={"channels_json": json.dumps(channels)},
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": (
            "Channel 1: Advanced tone mode requires "
            "at least one tone."
        )
    }
