"""Export Radio Loadout channels to CHIRP's generic CSV format."""

import csv
from collections.abc import Iterable
from io import StringIO

from radio_loadout.models import (
    AnalogSettings,
    Channel,
    ChannelMode,
    Tone,
    ToneMode,
)

CHIRP_HEADERS = [
    "Location",
    "Name",
    "Frequency",
    "Duplex",
    "Offset",
    "Tone",
    "rToneFreq",
    "cToneFreq",
    "DtcsCode",
    "DtcsPolarity",
    "RxDtcsCode",
    "CrossMode",
    "Mode",
    "TStep",
    "Skip",
    "Power",
    "Comment",
    "URCALL",
    "RPT1CALL",
    "RPT2CALL",
    "DVCODE",
]


def export_chirp_csv(channels: Iterable[Channel]) -> str:
    """Convert channels into text using CHIRP's generic CSV format."""

    output = StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(CHIRP_HEADERS)

    for location, channel in enumerate(channels):
        writer.writerow(_channel_to_row(location, channel))

    return output.getvalue()


def _channel_to_row(location: int, channel: Channel) -> list[str]:
    if channel.mode is ChannelMode.DMR:
        raise ValueError(
            "CHIRP CSV export currently supports analog channels only."
        )

    settings = channel.analog_settings or AnalogSettings()
    duplex, offset = _duplex_fields(channel)

    (
        tone_mode,
        transmit_ctcss,
        receive_ctcss,
        transmit_dcs,
        receive_dcs,
        cross_mode,
    ) = _tone_fields(settings)

    power_watts = settings.power_watts

    if power_watts is None:
        power_watts = 5.0

    return [
        str(location),
        channel.name,
        _format_frequency(channel.receive_frequency_hz),
        duplex,
        offset,
        tone_mode,
        transmit_ctcss,
        receive_ctcss,
        transmit_dcs,
        _dcs_polarity(settings),
        receive_dcs,
        cross_mode,
        channel.mode.value,
        _format_tuning_step(channel.tuning_step_khz),
        channel.scan_behavior.value,
        _format_power(power_watts),
        channel.comment,
        "",
        "",
        "",
        "",
    ]


def _duplex_fields(channel: Channel) -> tuple[str, str]:
    transmit_frequency = channel.transmit_frequency_hz

    if transmit_frequency is None:
        return "off", "0.000000"

    difference = transmit_frequency - channel.receive_frequency_hz

    if difference == 0:
        return "", "0.000000"

    duplex = "+" if difference > 0 else "-"
    return duplex, _format_frequency(abs(difference))


def _tone_fields(
    settings: AnalogSettings,
) -> tuple[str, str, str, str, str, str]:
    transmit_tone = settings.transmit_tone
    receive_tone = settings.receive_tone

    transmit_ctcss = "88.5"
    receive_ctcss = "88.5"
    transmit_dcs = "023"
    receive_dcs = "023"
    cross_mode = "Tone->Tone"

    if transmit_tone.mode is ToneMode.CTCSS:
        transmit_ctcss = f"{float(transmit_tone.value):.1f}"
    elif transmit_tone.mode is ToneMode.DCS:
        transmit_dcs = f"{int(transmit_tone.value):03d}"

    if receive_tone.mode is ToneMode.CTCSS:
        receive_ctcss = f"{float(receive_tone.value):.1f}"
    elif receive_tone.mode is ToneMode.DCS:
        receive_dcs = f"{int(receive_tone.value):03d}"

    if (
        transmit_tone.mode is ToneMode.NONE
        and receive_tone.mode is ToneMode.NONE
    ):
        tone_mode = ""
    elif (
        transmit_tone.mode is ToneMode.CTCSS
        and receive_tone.mode is ToneMode.NONE
    ):
        tone_mode = "Tone"
    elif _matching_tones(
        transmit_tone,
        receive_tone,
        ToneMode.CTCSS,
    ):
        tone_mode = "TSQL"
    elif _matching_tones(
        transmit_tone,
        receive_tone,
        ToneMode.DCS,
    ):
        tone_mode = "DTCS"
    else:
        tone_mode = "Cross"
        cross_mode = (
            f"{_chirp_tone_name(transmit_tone)}"
            f"->{_chirp_tone_name(receive_tone)}"
        )

    return (
        tone_mode,
        transmit_ctcss,
        receive_ctcss,
        transmit_dcs,
        receive_dcs,
        cross_mode,
    )


def _matching_tones(
    transmit_tone: Tone,
    receive_tone: Tone,
    mode: ToneMode,
) -> bool:
    return (
        transmit_tone.mode is mode
        and receive_tone.mode is mode
        and transmit_tone.value == receive_tone.value
    )


def _chirp_tone_name(tone: Tone) -> str:
    if tone.mode is ToneMode.CTCSS:
        return "Tone"

    if tone.mode is ToneMode.DCS:
        return "DTCS"

    return ""


def _dcs_polarity(settings: AnalogSettings) -> str:
    transmit_polarity = "N"
    receive_polarity = "N"

    if settings.transmit_tone.mode is ToneMode.DCS:
        transmit_polarity = settings.transmit_tone.polarity.value

    if settings.receive_tone.mode is ToneMode.DCS:
        receive_polarity = settings.receive_tone.polarity.value

    return f"{transmit_polarity}{receive_polarity}"


def _format_frequency(frequency_hz: int) -> str:
    return f"{frequency_hz / 1_000_000:.6f}"


def _format_tuning_step(tuning_step_khz: float) -> str:
    return f"{float(tuning_step_khz):.2f}"


def _format_power(power_watts: float) -> str:
    value = f"{float(power_watts):.3f}".rstrip("0").rstrip(".")

    if "." not in value:
        value += ".0"

    return f"{value}W"