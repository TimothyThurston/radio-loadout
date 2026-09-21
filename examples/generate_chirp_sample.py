"""Generate a small CHIRP CSV file for manual testing."""

from pathlib import Path

from radio_loadout.exporters.chirp_csv import export_chirp_csv
from radio_loadout.models import AnalogSettings, Channel, ChannelMode

OUTPUT_PATH = Path("generated") / "radio_loadout_sample.csv"


def main() -> None:
    handheld_power = AnalogSettings(power_watts=5.0)

    channels = [
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

    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    OUTPUT_PATH.write_text(export_chirp_csv(channels), encoding="utf-8")

    print(f"Created: {OUTPUT_PATH.resolve()}")


if __name__ == "__main__":
    main()