"""Non-mutating, source-qualified device review layered over generic CSV validation."""

from dataclasses import dataclass

from radio_loadout.compatibility import (
    CompatibilityIssue,
    CompatibilityReport,
    check_chirp_compatibility,
)
from radio_loadout.models import Channel, ChannelMode, ToneMode
from radio_loadout.radio_profiles import RadioCapabilityProfile


@dataclass(frozen=True)
class RadioCompatibilityReport(CompatibilityReport):
    profile: RadioCapabilityProfile | None = None

    def to_dict(self) -> dict:
        data = super().to_dict()
        if self.profile is not None:
            data["radio_profile"] = self.profile.to_dict()
        return data


def profile_context(report: CompatibilityReport, profile: RadioCapabilityProfile | None):
    if profile is None:
        return report
    return RadioCompatibilityReport(report.channel_count, report.issues, profile)


def check_channel_compatibility(channels: list[Channel], profile: RadioCapabilityProfile | None = None):
    generic = check_chirp_compatibility(channels)
    if profile is None:
        return generic
    if not generic.compatible:
        return profile_context(generic, profile)
    issues = list(generic.issues)
    issues.extend((
        CompatibilityIssue("warning", None, None, "radio_profile",
                           "Documented pilot only: installed hardware/firmware and programming behavior are unverified. "
                           "No device read/write or live control. Frequency coverage is not transmit authorization."),
        CompatibilityIssue("warning", None, None, "unverified_fields",
                           "Name limits/characters, exact power-level mappings, tone/cross-mode acceptance and "
                           "priority-scan mapping remain unverified; no automatic substitutions are made."),
        CompatibilityIssue("info", None, None, "zones",
                           "Only total memory capacity is checked. Generic CSV does not assign zones, reserve "
                           "slots or preserve a radio image. Verify the destination in CHIRP/CPS."),
    ))
    if len(channels) > profile.memory_capacity:
        issues.append(CompatibilityIssue("error", None, None, "channels",
                                        f"The documented profile capacity is {profile.memory_capacity} memories."))
    for index, channel in enumerate(channels):
        def add(severity, field, message, channel_index=index, channel_name=channel.name):
            issues.append(CompatibilityIssue(severity, channel_index, channel_name, field, message))

        if not any(band.contains(channel.receive_frequency_hz, channel.mode) for band in profile.receive_bands):
            add("error", "receive_frequency_hz", "Receive frequency/mode is outside this profile's reviewed memory scope. "
                "Separate broadcast-FM reception is not treated as programmable channel support.")
        if profile.name_max_length is not None and len(channel.name) > profile.name_max_length:
            add("error", "name", f"The profile name limit is {profile.name_max_length} characters; no truncation was applied.")
        if profile.name_characters is not None and any(c not in profile.name_characters for c in channel.name):
            add("error", "name", "Channel name contains characters outside the profile's documented set.")
        if channel.mode is ChannelMode.AM and profile.airband_step_unverified:
            add("warning", "tuning_step_khz", "Airband stepping/bandwidth behavior is not fully modeled by the current "
                "generic channel fields; confirm it in the destination. No 8.33 kHz value is synthesized.")
        elif channel.tuning_step_khz not in profile.documented_tuning_steps_khz:
            add("error" if profile.tuning_steps_exhaustive else "warning", "tuning_step_khz",
                "Requested tuning step is not in the reviewed quick feature list. The manual's VFO table differs; "
                "memory-step applicability is not verified.")
        if channel.receive_frequency_hz in profile.uncertain_receive_boundaries_hz:
            add("warning", "receive_frequency_hz", "The exact 137 MHz band boundary is not hardware verified.")
        settings = channel.analog_settings
        if settings:
            for direction in ("transmit", "receive"):
                tone = getattr(settings, direction + "_tone")
                if tone.mode not in profile.tone_modes:
                    add("error", direction + "_tone", "Tone mode is outside the profile's documented set.")
                values = profile.ctcss_values_hz if tone.mode is ToneMode.CTCSS else profile.dcs_codes
                if tone.mode is not ToneMode.NONE and values is not None and tone.value not in values:
                    add("error", direction + "_tone", "Tone value is outside the profile's documented set.")
        if channel.transmit_frequency_hz is None:
            continue
        bands = [b for b in profile.transmit_bands if b.contains(channel.transmit_frequency_hz, channel.mode)]
        if not bands:
            add("error", "transmit_frequency_hz", "Transmit frequency/mode is outside this profile's documented scope. "
                "Use receive-only when appropriate; the review never disables transmit automatically.")
        power = settings.power_watts if settings and settings.power_watts is not None else 5.0
        if bands and all(b.max_power_watts is not None and power > b.max_power_watts for b in bands):
            add("error", "power_watts", "Requested/export-default power exceeds the documented band ceiling. "
                "Exact selectable watt-to-H/M/L mapping is not verified.")
        if profile.power_options_watts is not None and power not in profile.power_options_watts:
            add("error", "power_watts", "Power is outside the profile's documented options; no nearest value was substituted.")
        if any(low <= channel.transmit_frequency_hz <= high for low, high in profile.conditional_transmit_ranges_hz):
            add("warning", "transmit_frequency_hz", "Manufacturer-listed coverage here is not an operating permission. "
                "Special operating conditions may apply; independently verify authorization.")
    return RadioCompatibilityReport(generic.channel_count, tuple(issues), profile)
