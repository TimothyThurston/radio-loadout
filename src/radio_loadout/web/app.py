"""Radio Loadout web application."""

import csv
import json
import math
from pathlib import Path
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import (
    BaseModel,
    Field,
    TypeAdapter,
    ValidationError,
    field_validator,
    model_validator,
)
from starlette.exceptions import HTTPException as StarletteHTTPException

from radio_loadout import input_limits
from radio_loadout.compatibility import (
    CompatibilityIssue,
    CompatibilityReport,
    check_chirp_compatibility,
    validation_report,
)
from radio_loadout.dcs import parse_dcs_code
from radio_loadout.exporters.chirp_csv import export_chirp_csv
from radio_loadout.importers.chirp_csv import import_chirp_csv_detailed
from radio_loadout.models import (
    TUNING_STEPS_KHZ,
    AnalogSettings,
    Channel,
    ChannelMode,
    ScanBehavior,
    Tone,
    ToneMode,
    TonePolarity,
)

WEB_DIRECTORY = Path(__file__).resolve().parent

IndependentToneMode = Literal["none", "ctcss", "dcs"]
DcsPolarity = Literal["N", "R"]
CHANNELS_JSON_OPENAPI = {
    "requestBody": {"required": True, "content": {
        content_type: {"schema": {"type": "object", "required": ["channels_json"],
                                 "properties": {"channels_json": {"type": "string"}}}}
        for content_type in ("application/x-www-form-urlencoded", "multipart/form-data")
    }},
}

app = FastAPI(title="Radio Loadout")

app.mount(
    "/static",
    StaticFiles(directory=WEB_DIRECTORY / "static"),
    name="static",
)

templates = Jinja2Templates(directory=WEB_DIRECTORY / "templates")


def _validate_independent_tone(
    label: str,
    mode: IndependentToneMode,
    ctcss_frequency_hz: float | None,
    dcs_code: int | None,
) -> None:
    if mode == "ctcss" and ctcss_frequency_hz is None:
        raise ValueError(
            f"{label} CTCSS frequency is required."
        )

    if mode == "dcs" and dcs_code is None:
        raise ValueError(
            f"{label} DCS code is required."
        )


class ChannelFormData(BaseModel):
    """One channel submitted by the browser-based builder."""

    name: str = Field(min_length=1, max_length=32)
    receive_frequency_mhz: float = Field(gt=0, allow_inf_nan=False)
    transmit_frequency_mhz: float | None = Field(
        default=None,
        gt=0,
        allow_inf_nan=False,
    )
    mode: ChannelMode = ChannelMode.FM
    power_watts: float = Field(default=5.0, gt=0, allow_inf_nan=False)
    receive_only: bool = False

    tone_mode: Literal[
        "none",
        "tone",
        "tsql",
        "dtcs",
        "cross",
    ] = "none"

    tone_frequency_hz: float | None = Field(
        default=None,
        ge=50.0,
        le=300.0,
    )

    dcs_code: int | None = None
    dcs_polarity: Literal["NN", "NR", "RN", "RR"] = "NN"

    transmit_tone_mode: IndependentToneMode = "none"

    transmit_ctcss_frequency_hz: float | None = Field(
        default=None,
        ge=50.0,
        le=300.0,
    )

    transmit_dcs_code: int | None = None
    transmit_dcs_polarity: DcsPolarity = "N"

    receive_tone_mode: IndependentToneMode = "none"

    receive_ctcss_frequency_hz: float | None = Field(
        default=None,
        ge=50.0,
        le=300.0,
    )

    receive_dcs_code: int | None = None
    receive_dcs_polarity: DcsPolarity = "N"

    tuning_step_khz: float = 5.0
    scan_behavior: ScanBehavior = ScanBehavior.NORMAL
    comment: str = Field(default="", max_length=120)

    @field_validator("dcs_code", "transmit_dcs_code", "receive_dcs_code", mode="before")
    @classmethod
    def validate_generic_dcs_code(cls, value: object) -> int | None:
        return None if value is None else parse_dcs_code(value)

    @model_validator(mode="after")
    def validate_channel_settings(
        self,
    ) -> "ChannelFormData":
        if (
            self.tone_mode in {"tone", "tsql"}
            and self.tone_frequency_hz is None
        ):
            raise ValueError(
                "A CTCSS frequency is required when "
                "CTCSS is enabled."
            )

        if (
            self.tone_mode == "dtcs"
            and self.dcs_code is None
        ):
            raise ValueError(
                "A DCS code is required when "
                "DCS is enabled."
            )

        if self.tone_mode == "cross":
            _validate_independent_tone(
                "Transmit",
                self.transmit_tone_mode,
                self.transmit_ctcss_frequency_hz,
                self.transmit_dcs_code,
            )

            _validate_independent_tone(
                "Receive",
                self.receive_tone_mode,
                self.receive_ctcss_frequency_hz,
                self.receive_dcs_code,
            )

            if (
                self.transmit_tone_mode == "none"
                and self.receive_tone_mode == "none"
            ):
                raise ValueError(
                    "Advanced tone mode requires at least "
                    "one tone."
                )

        if self.tuning_step_khz not in TUNING_STEPS_KHZ:
            raise ValueError(
                "Tuning step must be a supported CHIRP value."
            )

        return self


CHANNEL_FORM_LIST = TypeAdapter(list[ChannelFormData])

VALIDATION_FIELD_LABELS = {
    "name": "channel name",
    "receive_frequency_mhz": "receive frequency",
    "transmit_frequency_mhz": "transmit frequency",
    "power_watts": "power",
    "tone_frequency_hz": "CTCSS frequency",
    "dcs_code": "DCS code",
    "tuning_step_khz": "tuning step",
    "scan_behavior": "scan behavior",
    "comment": "comment",
}


def _format_validation_error(
    error: ValidationError,
) -> str:
    messages = []

    for issue in error.errors(include_url=False):
        location = issue.get("loc", ())
        message = str(
            issue.get("msg", "Invalid value.")
        ).removeprefix("Value error, ")

        channel_number = None
        field_name = None

        if location and isinstance(location[0], int):
            channel_number = location[0] + 1

        if location and isinstance(location[-1], str):
            field_name = location[-1]

        if channel_number is None:
            messages.append(message)
        elif field_name is None:
            messages.append(
                f"Channel {channel_number}: {message}"
            )
        else:
            field_label = VALIDATION_FIELD_LABELS.get(
                field_name,
                field_name.replace("_", " "),
            )
            messages.append(
                f"Channel {channel_number}, "
                f"{field_label}: {message}"
            )

    if not messages:
        return "The submitted channel data is invalid."

    return " ".join(messages)


def _mhz_to_hz(frequency_mhz: float) -> int:
    frequency_hz = frequency_mhz * 1_000_000
    if not math.isfinite(frequency_hz):
        raise ValueError("Frequency must be finite and representable in Hz.")
    return round(frequency_hz)


def _build_independent_tone(
    mode: IndependentToneMode,
    ctcss_frequency_hz: float | None,
    dcs_code: int | None,
    dcs_polarity: DcsPolarity,
) -> Tone:
    if mode == "none":
        return Tone()

    if mode == "ctcss":
        return Tone(
            mode=ToneMode.CTCSS,
            value=ctcss_frequency_hz,
        )

    return Tone(
        mode=ToneMode.DCS,
        value=dcs_code,
        polarity=TonePolarity(dcs_polarity),
    )


def _build_channel(form_data: ChannelFormData) -> Channel:
    receive_frequency_hz = _mhz_to_hz(
        form_data.receive_frequency_mhz
    )

    if form_data.receive_only:
        transmit_frequency_hz = None
    elif form_data.transmit_frequency_mhz is None:
        transmit_frequency_hz = receive_frequency_hz
    else:
        transmit_frequency_hz = _mhz_to_hz(
            form_data.transmit_frequency_mhz
        )

    transmit_tone = Tone()
    receive_tone = Tone()

    if form_data.tone_mode in {"tone", "tsql"}:
        transmit_tone = Tone(
            mode=ToneMode.CTCSS,
            value=form_data.tone_frequency_hz,
        )

    if form_data.tone_mode == "tsql":
        receive_tone = Tone(
            mode=ToneMode.CTCSS,
            value=form_data.tone_frequency_hz,
        )

    if form_data.tone_mode == "dtcs":
        transmit_tone = Tone(
            mode=ToneMode.DCS,
            value=form_data.dcs_code,
            polarity=TonePolarity(
                form_data.dcs_polarity[0]
            ),
        )

        receive_tone = Tone(
            mode=ToneMode.DCS,
            value=form_data.dcs_code,
            polarity=TonePolarity(
                form_data.dcs_polarity[1]
            ),
        )

    if form_data.tone_mode == "cross":
        transmit_tone = _build_independent_tone(
            form_data.transmit_tone_mode,
            form_data.transmit_ctcss_frequency_hz,
            form_data.transmit_dcs_code,
            form_data.transmit_dcs_polarity,
        )

        receive_tone = _build_independent_tone(
            form_data.receive_tone_mode,
            form_data.receive_ctcss_frequency_hz,
            form_data.receive_dcs_code,
            form_data.receive_dcs_polarity,
        )

    return Channel(
        name=form_data.name.strip(),
        receive_frequency_hz=receive_frequency_hz,
        transmit_frequency_hz=transmit_frequency_hz,
        mode=form_data.mode,
        analog_settings=None if form_data.mode is ChannelMode.DMR else AnalogSettings(
            transmit_tone=transmit_tone,
            receive_tone=receive_tone,
            power_watts=form_data.power_watts,
        ),
        tuning_step_khz=form_data.tuning_step_khz,
        scan_behavior=form_data.scan_behavior,
        comment=form_data.comment.strip(),
    )


def _construct_channels(
    form_channels: list[ChannelFormData],
) -> tuple[list[Channel], list[CompatibilityIssue]]:
    channels = []
    issues = []
    for index, form_channel in enumerate(form_channels):
        try:
            channels.append(_build_channel(form_channel))
        except (TypeError, ValueError, OverflowError) as error:
            issues.append(CompatibilityIssue(
                "error", index, form_channel.name, "settings", str(error),
            ))
    return channels, issues


async def _submitted_channels_form(request: Request) -> str:
    # Set the per-request multipart field bound explicitly; Starlette's default
    # may be lower than our documented channels_json limit. No global changes.
    try:
        urlencoded = request.headers.get("content-type", "").split(";", 1)[0].strip().lower() == "application/x-www-form-urlencoded"
        # Percent encoding can occupy three bytes per decoded UTF-8 byte.
        part_limit = input_limits.LIMITS.channels_json_bytes * (3 if urlencoded else 1)
        async with request.form(
            max_files=0, max_fields=1, max_part_size=part_limit,
        ) as form:
            value = form.get("channels_json")
            if not isinstance(value, str):
                raise HTTPException(status_code=422, detail="channels_json must be a string form field.")
            _check_submitted_limits(value)
            return value
    except StarletteHTTPException as error:
        if error.status_code == 400 and "maximum size" in str(error.detail).lower():
            raise HTTPException(status_code=413, detail="channels_json exceeds the encoded form field size limit.") from error
        raise


@app.post("/validation/chirp.csv", openapi_extra=CHANNELS_JSON_OPENAPI)
def review_chirp_compatibility(channels_json: Annotated[str, Depends(_submitted_channels_form)]) -> dict:
    try:
        form_channels = CHANNEL_FORM_LIST.validate_json(channels_json)
    except ValidationError as error:
        try:
            submitted = json.loads(channels_json)
        except (ValueError, TypeError):
            submitted = None
        return validation_report(error.errors(include_url=False), submitted).to_dict()
    channels, issues = _construct_channels(form_channels)
    if issues:
        return CompatibilityReport(len(form_channels), tuple(issues)).to_dict()
    return check_chirp_compatibility(channels).to_dict()


def _channel_to_form_data(channel: Channel) -> ChannelFormData:
    """Represent imported tones using the builder's independent tone controls."""
    settings = channel.analog_settings or AnalogSettings()
    transmit = settings.transmit_tone
    receive = settings.receive_tone
    tone_fields = {}

    for direction, tone in (("transmit", transmit), ("receive", receive)):
        tone_fields[f"{direction}_tone_mode"] = tone.mode.value.lower()
        tone_fields[f"{direction}_ctcss_frequency_hz"] = (
            tone.value if tone.mode is ToneMode.CTCSS else None
        )
        tone_fields[f"{direction}_dcs_code"] = (
            tone.value if tone.mode is ToneMode.DCS else None
        )
        tone_fields[f"{direction}_dcs_polarity"] = tone.polarity.value

    return ChannelFormData(
        name=channel.name,
        receive_frequency_mhz=channel.receive_frequency_hz / 1_000_000,
        transmit_frequency_mhz=(
            channel.transmit_frequency_hz / 1_000_000
            if channel.transmit_frequency_hz is not None else None
        ),
        receive_only=channel.receive_only,
        mode=channel.mode,
        power_watts=settings.power_watts if settings.power_watts is not None else 5.0,
        tone_mode=(
            "none" if transmit.mode is ToneMode.NONE and receive.mode is ToneMode.NONE
            else "cross"
        ),
        tuning_step_khz=channel.tuning_step_khz,
        scan_behavior=channel.scan_behavior,
        comment=channel.comment,
        **tone_fields,
    )


def _check_submitted_limits(channels_json: str) -> None:
    try:
        input_limits.check_channels_json(channels_json)
    except input_limits.InputLimitError as error:
        raise HTTPException(status_code=413, detail=str(error)) from error


async def _read_csv_upload(file: UploadFile) -> bytes:
    data = bytearray()
    while True:
        chunk = await file.read(min(
            input_limits.LIMITS.read_chunk_bytes,
            input_limits.LIMITS.csv_upload_bytes - len(data) + 1,
        ))
        if not chunk:
            return bytes(data)
        input_limits.check_bytes(
            len(data) + len(chunk), input_limits.LIMITS.csv_upload_bytes, "CSV upload",
        )
        data.extend(chunk)


@app.post("/imports/chirp.csv")
async def upload_chirp_csv(
    file: Annotated[UploadFile, File()],
) -> dict:
    try:
        csv_text = (await _read_csv_upload(file)).decode("utf-8-sig")
    except input_limits.InputLimitError as error:
        raise HTTPException(status_code=413, detail=str(error)) from error
    except UnicodeDecodeError as error:
        raise HTTPException(
            status_code=422,
            detail="The CSV file must use UTF-8 encoding.",
        ) from error
    finally:
        await file.close()

    try:
        result = import_chirp_csv_detailed(csv_text)
        form_channels = []
        for index, channel in enumerate(result.channels):
            label = f"Invalid CHIRP CSV row {result.source_rows[index]} ({channel.name})"
            for field, value in (("Name", channel.name), ("Comment", channel.comment)):
                if "\n" in value or "\r" in value:
                    raise ValueError(f"{label}: multiline {field} is not supported by the builder's single-line control.")
            try:
                form_channels.append(_channel_to_form_data(channel))
            except ValidationError as error:
                raise ValueError(f"{label}: {_format_validation_error(error)}") from error
    except input_limits.InputLimitError as error:
        raise HTTPException(status_code=413, detail=str(error)) from error
    except ValidationError as error:
        raise HTTPException(
            status_code=422,
            detail=_format_validation_error(error),
        ) from error
    except (ValueError, csv.Error) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    return {"channels": form_channels, "import_report": result.report()}


def _sample_channels() -> list[Channel]:
    handheld_power = AnalogSettings(power_watts=5.0)

    return [
        Channel(
            name="2M CALL",
            receive_frequency_hz=146_520_000,
            transmit_frequency_hz=146_520_000,
            mode=ChannelMode.FM,
            analog_settings=handheld_power,
            comment="Two-meter national calling frequency",
        ),
        Channel(
            name="1.25 CALL",
            receive_frequency_hz=223_500_000,
            transmit_frequency_hz=223_500_000,
            mode=ChannelMode.FM,
            analog_settings=handheld_power,
            comment="1.25-meter national calling frequency",
        ),
        Channel(
            name="70CM CALL",
            receive_frequency_hz=446_000_000,
            transmit_frequency_hz=446_000_000,
            mode=ChannelMode.FM,
            analog_settings=handheld_power,
            comment="70-centimeter national calling frequency",
        ),
        Channel(
            name="NOAA 7",
            receive_frequency_hz=162_550_000,
            transmit_frequency_hz=None,
            mode=ChannelMode.NFM,
            scan_behavior=ScanBehavior.PRIORITY,
            comment="Receive-only weather radio",
        ),
    ]


@app.get("/")
def home(request: Request) -> Response:
    return templates.TemplateResponse(
        request=request,
        name="index.html",
    )


@app.get("/builder")
def builder(request: Request) -> Response:
    return templates.TemplateResponse(
        request=request,
        name="builder.html",
        context={"input_limits": input_limits.public_limits()},
    )


@app.post("/downloads/chirp.csv", openapi_extra=CHANNELS_JSON_OPENAPI)
def download_custom_chirp(
    channels_json: Annotated[str, Depends(_submitted_channels_form)],
) -> Response:
    try:
        form_channels = CHANNEL_FORM_LIST.validate_json(
            channels_json
        )
    except ValidationError as error:
        raise HTTPException(
            status_code=422,
            detail=_format_validation_error(error),
        ) from error

    if not form_channels:
        raise HTTPException(
            status_code=422,
            detail="At least one channel is required.",
        )

    channels, issues = _construct_channels(form_channels)
    report = CompatibilityReport(len(form_channels), tuple(issues)) if issues else (
        check_chirp_compatibility(channels)
    )
    if not report.compatible:
        detail = " ".join(
            f"Channel {issue.channel_index + 1} ({issue.channel_name}): {issue.message}"
            if issue.channel_index is not None else issue.message
            for issue in report.issues if issue.severity == "error"
        )
        raise HTTPException(status_code=422, detail=detail)

    csv_text = export_chirp_csv(channels)

    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={
            "Content-Disposition": (
                'attachment; filename="radio_loadout_custom.csv"'
            )
        },
    )


@app.get("/downloads/chirp-sample.csv")
def download_chirp_sample() -> Response:
    csv_text = export_chirp_csv(_sample_channels())

    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={
            "Content-Disposition": (
                'attachment; filename="radio_loadout_sample.csv"'
            )
        },
    )
