"""Radio Loadout web application."""

from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Form, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from radio_loadout.exporters.chirp_csv import export_chirp_csv
from radio_loadout.models import AnalogSettings, Channel, ChannelMode

WEB_DIRECTORY = Path(__file__).resolve().parent

app = FastAPI(title="Radio Loadout")

app.mount(
    "/static",
    StaticFiles(directory=WEB_DIRECTORY / "static"),
    name="static",
)

templates = Jinja2Templates(directory=WEB_DIRECTORY / "templates")


def _mhz_to_hz(frequency_mhz: float) -> int:
    return round(frequency_mhz * 1_000_000)


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
    name: Annotated[str, Form(min_length=1, max_length=32)],
    receive_frequency_mhz: Annotated[float, Form(gt=0)],
    transmit_frequency_mhz: Annotated[float | None, Form(gt=0)] = None,
    mode: Annotated[ChannelMode, Form()] = ChannelMode.FM,
    power_watts: Annotated[float, Form(gt=0)] = 5.0,
    receive_only: Annotated[bool, Form()] = False,
    comment: Annotated[str, Form()] = "",
) -> Response:
    receive_frequency_hz = _mhz_to_hz(receive_frequency_mhz)

    if receive_only:
        transmit_frequency_hz = None
    elif transmit_frequency_mhz is None:
        transmit_frequency_hz = receive_frequency_hz
    else:
        transmit_frequency_hz = _mhz_to_hz(transmit_frequency_mhz)

    channel = Channel(
        name=name.strip(),
        receive_frequency_hz=receive_frequency_hz,
        transmit_frequency_hz=transmit_frequency_hz,
        mode=mode,
        analog_settings=AnalogSettings(power_watts=power_watts),
        comment=comment.strip(),
    )

    csv_text = export_chirp_csv([channel])

    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="radio_loadout_custom.csv"'
        },
    )


@app.get("/downloads/chirp-sample.csv")
def download_chirp_sample() -> Response:
    csv_text = export_chirp_csv(_sample_channels())

    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="radio_loadout_sample.csv"'
        },
    )