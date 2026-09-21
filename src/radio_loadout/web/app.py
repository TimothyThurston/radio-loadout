"""Radio Loadout web application."""

from fastapi import FastAPI, Response

from radio_loadout.exporters.chirp_csv import export_chirp_csv
from radio_loadout.models import AnalogSettings, Channel, ChannelMode

app = FastAPI(title="Radio Loadout")


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
def home() -> dict[str, str]:
    return {
        "name": "Radio Loadout",
        "status": "online",
    }


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