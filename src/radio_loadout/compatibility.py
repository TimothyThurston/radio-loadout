"""Reusable compatibility reports for CHIRP Generic CSV, independent of radios."""

import math
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass, replace
from typing import Literal

from radio_loadout.chirp_csv_validation import format_chirp_ctcss
from radio_loadout.exporters.chirp_csv import CHIRP_SUPPORTED_MODES, export_chirp_csv
from radio_loadout.models import (
    TUNING_STEPS_KHZ,
    Channel,
    ChannelMode,
    ScanBehavior,
    ToneMode,
    TonePolarity,
)

Severity = Literal["info", "warning", "error"]


@dataclass(frozen=True)
class CompatibilityIssue:
    """A capability issue; channel_index is zero-based, or None for the whole list."""

    severity: Severity
    channel_index: int | None
    channel_name: str | None
    field: str
    message: str


@dataclass(frozen=True)
class CompatibilityReport:
    channel_count: int
    issues: tuple[CompatibilityIssue, ...] = ()

    @property
    def compatible(self) -> bool:
        return not any(issue.severity == "error" for issue in self.issues)

    def to_dict(self) -> dict:
        return {
            "target": "chirp-generic-csv",
            "compatible": self.compatible,
            "channel_count": self.channel_count,
            "issues": [asdict(issue) for issue in self.issues],
        }


def _finite_positive(value: object) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(value) and value > 0
    except OverflowError:
        return False


def validation_report(errors: Iterable[dict], submitted: object) -> CompatibilityReport:
    """Translate existing form-validation errors, without adding validation rules."""
    channels = submitted if isinstance(submitted, list) else []
    issues = []
    for error in errors:
        location = error.get("loc", ())
        index = location[0] if location and isinstance(location[0], int) else None
        raw = channels[index] if index is not None and index < len(channels) else None
        name = raw.get("name") if isinstance(raw, dict) else None
        field = location[-1] if location and isinstance(location[-1], str) else "settings"
        issues.append(CompatibilityIssue(
            "error", index, name if isinstance(name, str) else None, field,
            str(error.get("msg", "Invalid channel data.")).removeprefix("Value error, "),
        ))
    return CompatibilityReport(len(channels), tuple(issues))


def check_chirp_compatibility(channels: Sequence[Channel]) -> CompatibilityReport:
    """Check model settings and exercise the exporter on the complete ordered list."""
    issues = []
    if not channels:
        issues.append(CompatibilityIssue(
            "error", None, None, "channels", "At least one channel is required.",
        ))

    for index, channel in enumerate(channels):
        def add(
            severity: Severity, field: str, message: str,
            channel_index: int = index, channel_name: str = channel.name,
        ) -> None:
            issues.append(CompatibilityIssue(severity, channel_index, channel_name, field, message))

        if not isinstance(channel.mode, ChannelMode) or (
            channel.mode not in CHIRP_SUPPORTED_MODES
        ):
            add("error", "mode", "The current CHIRP CSV exporter supports FM, NFM, and AM. "
                "Choose one of these modes instead of DMR or another unsupported mode.")
        for field in ("receive_frequency_hz", "transmit_frequency_hz"):
            value = getattr(channel, field)
            if field == "transmit_frequency_hz" and value is None:
                add("info", "receive_only", "Receive-only operation is supported by CHIRP Generic CSV.")
            elif not isinstance(value, int) or not _finite_positive(value):
                add("error", field, "Frequency must be a positive, finite whole number of Hz.")

        if isinstance(channel.tuning_step_khz, bool) or channel.tuning_step_khz not in TUNING_STEPS_KHZ:
            add("error", "tuning_step_khz", "Choose a supported CHIRP tuning step.")
        if not isinstance(channel.scan_behavior, ScanBehavior):
            add("error", "scan_behavior", "Choose normal, skip, or priority scan behavior.")

        settings = channel.analog_settings
        power = settings.power_watts if settings else None
        if power is None:
            add("warning", "power_watts", "No power is specified; CHIRP CSV export will use 5 W.")
        elif not _finite_positive(power):
            add("error", "power_watts", "Power must be a positive, finite value in watts.")
        elif round(power, 3) <= 0:
            add("error", "power_watts", "Power is too small for the exporter's three decimal places.")
        elif round(power, 3) != power:
            add("warning", "power_watts", "Power will be rounded to three decimal places on export.")

        if settings:
            for direction in ("transmit", "receive"):
                tone = getattr(settings, f"{direction}_tone")
                field = f"{direction}_tone"
                try:
                    # Reuse the Tone model's CTCSS, octal DCS, and polarity validation.
                    replace(tone)
                    if not isinstance(tone.mode, ToneMode):
                        raise TypeError("Choose no tone, CTCSS, or DCS.")
                    if not isinstance(tone.polarity, TonePolarity):
                        raise TypeError("DCS polarity must be normal (N) or reverse (R).")
                    if tone.mode is ToneMode.CTCSS:
                        formatted_ctcss = format_chirp_ctcss(tone.value)
                except (TypeError, ValueError) as error:
                    add("error", field, str(error))
                    continue
                if tone.mode is ToneMode.CTCSS and float(formatted_ctcss) != tone.value:
                    add("warning", field, "CTCSS will be rounded to one decimal place on export.")

    try:
        export_chirp_csv(channels)
    except (ValueError, TypeError, AttributeError, OverflowError) as error:
        if not any(issue.severity == "error" for issue in issues):
            issues.append(CompatibilityIssue(
                "error", None, None, "export", f"CHIRP CSV export could not complete: {error}",
            ))
    return CompatibilityReport(len(channels), tuple(issues))
