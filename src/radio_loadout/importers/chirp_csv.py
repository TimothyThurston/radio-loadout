"""Import channels from CHIRP's generic CSV format."""

import csv
import math
from io import StringIO

from radio_loadout.models import (
    AnalogSettings,
    Channel,
    ChannelMode,
    ScanBehavior,
    Tone,
    ToneMode,
    TonePolarity,
)

REQUIRED_HEADERS = ["Name", "Frequency"]


def import_chirp_csv(csv_text: str) -> list[Channel]:
    """Convert CHIRP generic CSV text into Radio Loadout channels."""

    reader = csv.DictReader(
        StringIO(csv_text.lstrip("\ufeff"))
    )

    if reader.fieldnames is None:
        raise ValueError(
            "The uploaded file does not contain a CSV header."
        )

    missing_headers = [
        header
        for header in REQUIRED_HEADERS
        if header not in reader.fieldnames
    ]

    if missing_headers:
        missing_text = ", ".join(missing_headers)

        raise ValueError(
            f"CHIRP CSV is missing required columns: "
            f"{missing_text}."
        )

    channels = []

    for row_number, row in enumerate(reader, start=2):
        if None in row:
            raise ValueError(
                f"Invalid CHIRP CSV row {row_number}: too many columns."
            )
        if _is_blank_row(row):
            continue

        try:
            channels.append(_row_to_channel(row))
        except (TypeError, ValueError) as error:
            raise ValueError(
                f"Invalid CHIRP CSV row {row_number}: {error}"
            ) from error

    if not channels:
        raise ValueError(
            "The CHIRP CSV does not contain any channels."
        )

    return channels


def _is_blank_row(row: dict[str, str | None]) -> bool:
    return not any(
        value is not None and value.strip()
        for value in row.values()
    )


def _row_value(
    row: dict[str, str | None],
    field_name: str,
    default: str = "",
) -> str:
    value = row.get(field_name)

    if value is None:
        return default

    return value.strip()


def _required_row_value(
    row: dict[str, str | None],
    field_name: str,
) -> str:
    value = _row_value(row, field_name)

    if not value:
        raise ValueError(
            f"{field_name} cannot be empty."
        )

    return value


def _row_to_channel(
    row: dict[str, str | None],
) -> Channel:
    name = _required_row_value(row, "Name")

    receive_frequency_hz = _parse_frequency_mhz(
        _required_row_value(row, "Frequency"),
        "Frequency",
    )

    transmit_frequency_hz = _parse_transmit_frequency(
        row,
        receive_frequency_hz,
    )

    mode = _parse_channel_mode(
        _row_value(row, "Mode") or "FM"
    )

    transmit_tone, receive_tone = _parse_tones(row)

    power_watts = _parse_power(
        _row_value(row, "Power")
    )

    tuning_step_khz = _parse_tuning_step(
        _row_value(row, "TStep") or "5.0"
    )

    scan_behavior = _parse_scan_behavior(
        _row_value(row, "Skip")
    )

    return Channel(
        name=name,
        receive_frequency_hz=receive_frequency_hz,
        transmit_frequency_hz=transmit_frequency_hz,
        mode=mode,
        analog_settings=AnalogSettings(
            transmit_tone=transmit_tone,
            receive_tone=receive_tone,
            power_watts=power_watts,
        ),
        tuning_step_khz=tuning_step_khz,
        scan_behavior=scan_behavior,
        comment=_row_value(row, "Comment"),
    )


def _parse_frequency_mhz(
    value: str,
    field_name: str,
) -> int:
    try:
        frequency_mhz = float(value)
    except ValueError as error:
        raise ValueError(
            f"{field_name} must be numeric."
        ) from error

    if (
        not math.isfinite(frequency_mhz)
        or frequency_mhz <= 0
    ):
        raise ValueError(
            f"{field_name} must be greater than zero."
        )

    frequency_hz = frequency_mhz * 1_000_000
    if not math.isfinite(frequency_hz):
        raise ValueError(f"{field_name} is too large.")

    return round(frequency_hz)


def _parse_transmit_frequency(
    row: dict[str, str | None],
    receive_frequency_hz: int,
) -> int | None:
    duplex = _row_value(row, "Duplex").lower()
    offset = _row_value(row, "Offset", "0")

    if duplex == "off":
        return None

    if duplex == "":
        return receive_frequency_hz

    if duplex == "split":
        return _parse_frequency_mhz(
            offset,
            "Transmit frequency",
        )

    if duplex not in {"+", "-"}:
        raise ValueError(
            f"Unsupported duplex value: {duplex}."
        )

    offset_hz = _parse_frequency_mhz(
        offset,
        "Offset",
    )

    if duplex == "+":
        return receive_frequency_hz + offset_hz

    return receive_frequency_hz - offset_hz


def _parse_channel_mode(value: str) -> ChannelMode:
    normalized_value = value.upper()

    try:
        mode = ChannelMode(normalized_value)
    except ValueError as error:
        raise ValueError(
            f"Unsupported channel mode: {value}."
        ) from error

    if mode is ChannelMode.DMR:
        raise ValueError(
            "CHIRP CSV import currently supports "
            "analog channels only."
        )

    return mode


def _parse_tones(
    row: dict[str, str | None],
) -> tuple[Tone, Tone]:
    tone_mode = _row_value(row, "Tone").casefold()
    transmit_polarity, receive_polarity = (
        _parse_dcs_polarities(
            _row_value(row, "DtcsPolarity") or "NN"
        )
    )

    if tone_mode == "":
        return Tone(), Tone()

    if tone_mode == "tone":
        return (
            _parse_ctcss_tone(
                _required_row_value(row, "rToneFreq")
            ),
            Tone(),
        )

    if tone_mode == "tsql":
        # CHIRP TSQL uses ctone in both directions; rtone is inactive.
        # Keep validating populated inactive fields instead of accepting bad CSV.
        if _row_value(row, "rToneFreq"):
            _parse_ctcss_tone(_row_value(row, "rToneFreq"))
        frequency = (
            _row_value(row, "cToneFreq")
            or _required_row_value(row, "rToneFreq")
        )

        return (
            _parse_ctcss_tone(frequency),
            _parse_ctcss_tone(frequency),
        )

    if tone_mode == "dtcs":
        transmit_code = _required_row_value(
            row,
            "DtcsCode",
        )
        if _row_value(row, "RxDtcsCode"):
            _parse_dcs_tone(_row_value(row, "RxDtcsCode"), receive_polarity)

        return (
            _parse_dcs_tone(
                transmit_code,
                transmit_polarity,
            ),
            _parse_dcs_tone(
                transmit_code,
                receive_polarity,
            ),
        )

    if tone_mode == "cross":
        return _parse_cross_tones(
            row,
            transmit_polarity,
            receive_polarity,
        )

    raise ValueError(
        f"Unsupported tone mode: "
        f"{_row_value(row, 'Tone')}."
    )


def _parse_cross_tones(
    row: dict[str, str | None],
    transmit_polarity: TonePolarity,
    receive_polarity: TonePolarity,
) -> tuple[Tone, Tone]:
    cross_mode = _required_row_value(
        row,
        "CrossMode",
    )

    if "->" not in cross_mode:
        raise ValueError(
            "CrossMode must contain '->'."
        )

    transmit_mode, receive_mode = cross_mode.split(
        "->",
        maxsplit=1,
    )

    transmit_tone = _parse_cross_tone(
        row=row,
        mode=transmit_mode,
        ctcss_field="rToneFreq",
        dcs_field="DtcsCode",
        polarity=transmit_polarity,
    )

    receive_tone = _parse_cross_tone(
        row=row,
        mode=receive_mode,
        ctcss_field="cToneFreq",
        dcs_field="RxDtcsCode",
        polarity=receive_polarity,
    )

    return transmit_tone, receive_tone


def _parse_cross_tone(
    row: dict[str, str | None],
    mode: str,
    ctcss_field: str,
    dcs_field: str,
    polarity: TonePolarity,
) -> Tone:
    normalized_mode = mode.strip().casefold()

    if normalized_mode in {"", "none"}:
        return Tone()

    if normalized_mode == "tone":
        return _parse_ctcss_tone(
            _required_row_value(row, ctcss_field)
        )

    if normalized_mode == "dtcs":
        return _parse_dcs_tone(
            _required_row_value(row, dcs_field),
            polarity,
        )

    raise ValueError(
        f"Unsupported cross-tone mode: {mode}."
    )


def _parse_ctcss_tone(value: str) -> Tone:
    try:
        frequency_hz = float(value)
    except ValueError as error:
        raise ValueError(
            "CTCSS frequency must be numeric."
        ) from error

    return Tone(
        mode=ToneMode.CTCSS,
        value=frequency_hz,
    )


def _parse_dcs_tone(
    value: str,
    polarity: TonePolarity,
) -> Tone:
    try:
        code = int(value)
    except ValueError as error:
        raise ValueError(
            "DCS code must be an integer."
        ) from error

    return Tone(
        mode=ToneMode.DCS,
        value=code,
        polarity=polarity,
    )


def _parse_dcs_polarities(
    value: str,
) -> tuple[TonePolarity, TonePolarity]:
    normalized_value = value.upper()

    if (
        len(normalized_value) != 2
        or any(
            polarity not in {"N", "R"}
            for polarity in normalized_value
        )
    ):
        raise ValueError(
            "DTCS polarity must contain two "
            "characters using N or R."
        )

    return (
        TonePolarity(normalized_value[0]),
        TonePolarity(normalized_value[1]),
    )


def _parse_power(value: str) -> float | None:
    if not value:
        return None

    normalized_value = value.strip()

    if normalized_value.casefold().endswith("w"):
        normalized_value = normalized_value[:-1].strip()

    try:
        power_watts = float(normalized_value)
    except ValueError as error:
        raise ValueError(
            "Power must be a numeric watt value."
        ) from error

    if (
        not math.isfinite(power_watts)
        or power_watts <= 0
    ):
        raise ValueError(
            "Power must be greater than zero."
        )

    return power_watts


def _parse_tuning_step(value: str) -> float:
    try:
        return float(value)
    except ValueError as error:
        raise ValueError(
            "Tuning step must be numeric."
        ) from error


def _parse_scan_behavior(value: str) -> ScanBehavior:
    normalized_value = value.upper()

    try:
        return ScanBehavior(normalized_value)
    except ValueError as error:
        raise ValueError(
            f"Unsupported scan behavior: {value}."
        ) from error
