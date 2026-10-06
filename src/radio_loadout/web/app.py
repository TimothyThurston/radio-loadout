"""Radio Loadout web application."""

from pathlib import Path
from typing import Annotated, Literal

from fastapi import FastAPI, Form, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import (
    BaseModel,
    Field,
    TypeAdapter,
    ValidationError,
    model_validator,
)

from radio_loadout.exporters.chirp_csv import export_chirp_csv
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

STANDARD_DCS_CODES = (
    23,
    25,
    26,
    31,
    32,
    36,
    43,
    47,
    51,
    53,
    54,
    65,
    71,
    72,
    73,
    74,
    114,
    115,
    116,
    122,
    125,
    131,
    132,
    134,
    143,
    145,
    152,
    155,
    156,
    162,
    165,
    172,
    174,
    205,
    212,
    223,
    225,
    226,
    243,
    244,
    245,
    246,
    251,
    252,
    255,
    261,
    263,
    265,
    266,
    271,
    274,
    306,
    311,
    315,
    325,
    331,
    332,
    343,
    346,
    351,
    356,
    364,
    365,
    371,
    411,
    412,
    413,
    423,
    431,
    432,
    445,
    446,
    452,
    454,
    455,
    462,
    464,
    465,
    466,
    503,
    506,
    516,
    523,
    526,
    532,
    546,
    565,
    606,
    612,
    624,
    627,
    631,
    632,
    654,
    662,
    664,
    703,
    712,
    723,
    731,
    732,
    734,
    743,
    754,
)

IndependentToneMode = Literal["none", "ctcss", "dcs"]
DcsPolarity = Literal["N", "R"]

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

    if mode == "dcs" and dcs_code not in STANDARD_DCS_CODES:
        raise ValueError(
            f"{label} DCS code must be a standard DCS code."
        )


class ChannelFormData(BaseModel):
    """One channel submitted by the browser-based builder."""

    name: str = Field(min_length=1, max_length=32)
    receive_frequency_mhz: float = Field(gt=0)
    transmit_frequency_mhz: float | None = Field(default=None, gt=0)
    mode: ChannelMode = ChannelMode.FM
    power_watts: float = Field(default=5.0, gt=0)
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

    @model_validator(mode="after")
    def validate_channel_settings(self) -> "ChannelFormData":
        if (
            self.tone_mode in {"tone", "tsql"}
            and self.tone_frequency_hz is None
        ):
            raise ValueError(
                "A CTCSS frequency is required when CTCSS is enabled."
            )

        if (
            self.tone_mode == "dtcs"
            and self.dcs_code not in STANDARD_DCS_CODES
        ):
            raise ValueError(
                "A standard DCS code is required when DCS is enabled."
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
                    "Advanced tone mode requires at least one tone."
                )

        if self.tuning_step_khz not in TUNING_STEPS_KHZ:
            raise ValueError(
                "Tuning step must be a supported CHIRP value."
            )

        return self


CHANNEL_FORM_LIST = TypeAdapter(list[ChannelFormData])


def _mhz_to_hz(frequency_mhz: float) -> int:
    return round(frequency_mhz * 1_000_000)


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
        analog_settings=AnalogSettings(
            transmit_tone=transmit_tone,
            receive_tone=receive_tone,
            power_watts=form_data.power_watts,
        ),
        tuning_step_khz=form_data.tuning_step_khz,
        scan_behavior=form_data.scan_behavior,
        comment=form_data.comment.strip(),
    )


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
    )


@app.post("/downloads/chirp.csv")
def download_custom_chirp(
    channels_json: Annotated[str, Form()],
) -> Response:
    try:
        form_channels = CHANNEL_FORM_LIST.validate_json(
            channels_json
        )
    except ValidationError as error:
        raise HTTPException(
            status_code=422,
            detail="The submitted channel data is invalid.",
        ) from error

    if not form_channels:
        raise HTTPException(
            status_code=422,
            detail="At least one channel is required.",
        )

    channels = [
        _build_channel(form_channel)
        for form_channel in form_channels
    ]

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