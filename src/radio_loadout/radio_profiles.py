"""Versioned, immutable device capability descriptions, independent of channel data."""

import math
import re
from dataclasses import asdict, dataclass

from radio_loadout.models import ChannelMode, ToneMode


@dataclass(frozen=True, slots=True)
class RadioBand:
    lower_hz: int
    upper_hz: int
    modes: tuple[ChannelMode, ...]
    max_power_watts: float | None = None

    def __post_init__(self):
        if (type(self.lower_hz) is not int or type(self.upper_hz) is not int
                or self.lower_hz <= 0 or self.upper_hz < self.lower_hz or not self.modes
                or any(not isinstance(mode, ChannelMode) for mode in self.modes)):
            raise ValueError("Band limits must be positive ordered integer Hz with explicit modes.")
        if self.max_power_watts is not None and (
            isinstance(self.max_power_watts, bool) or not isinstance(self.max_power_watts, (int, float))
            or not math.isfinite(self.max_power_watts) or self.max_power_watts <= 0
        ):
            raise ValueError("Power ceiling must be finite and positive.")

    def contains(self, frequency_hz: int, mode: ChannelMode) -> bool:
        return self.lower_hz <= frequency_hz <= self.upper_hz and mode in self.modes


@dataclass(frozen=True, slots=True)
class ProfileSource:
    url: str
    title: str
    locator: str
    reviewed_on: str
    sha256: str | None = None

    def __post_init__(self):
        if not self.url.startswith("https://") or not self.title or not self.locator or not self.reviewed_on:
            raise ValueError("Profile sources require an HTTPS URL and review details.")
        if self.sha256 is not None and not re.fullmatch(r"[0-9a-f]{64}", self.sha256):
            raise ValueError("Invalid source checksum.")


@dataclass(frozen=True, slots=True)
class RadioCapabilityProfile:
    profile_id: str
    revision: int
    manufacturer: str
    model: str
    firmware_scope: str
    region_scope: str
    memory_capacity: int
    receive_bands: tuple[RadioBand, ...]
    transmit_bands: tuple[RadioBand, ...]
    sources: tuple[ProfileSource, ...]
    zone_count: int | None = None
    channels_per_zone: int | None = None
    name_max_length: int | None = None
    name_characters: str | None = None
    power_options_watts: tuple[float, ...] | None = None
    documented_tuning_steps_khz: tuple[float, ...] = ()
    tuning_steps_exhaustive: bool = False
    uncertain_receive_boundaries_hz: tuple[int, ...] = ()
    conditional_transmit_ranges_hz: tuple[tuple[int, int], ...] = ()
    airband_step_unverified: bool = False
    tone_modes: tuple[ToneMode, ...] = (ToneMode.NONE, ToneMode.CTCSS, ToneMode.DCS)
    ctcss_values_hz: tuple[float, ...] | None = None
    dcs_codes: tuple[int, ...] | None = None

    def __post_init__(self):
        if not re.fullmatch(r"[a-z0-9-]{1,80}", self.profile_id):
            raise ValueError("Invalid radio profile ID.")
        if type(self.revision) is not int or self.revision < 1:
            raise ValueError("Profile revision must be a positive integer.")
        if (not self.firmware_scope or not self.sources or type(self.memory_capacity) is not int
                or self.memory_capacity < 1):
            raise ValueError("Profile scope, source evidence and capacity are required.")
        if any(value is not None and (type(value) is not int or value < 1)
               for value in (self.name_max_length, self.zone_count, self.channels_per_zone)):
            raise ValueError("Optional name/zone limits must be positive integers or unknown.")
        if not self.receive_bands or not self.transmit_bands or any(
            band.lower_hz <= 0 or band.upper_hz < band.lower_hz or not band.modes
            for band in self.receive_bands + self.transmit_bands
        ):
            raise ValueError("Profile bands require positive ordered limits and modes.")

    def to_dict(self) -> dict:
        data = asdict(self)
        data.update(schema_version=1, evidence_status="manufacturer-documented-pilot",
                    hardware_verified=False, firmware_detected=False,
                    support={"configuration": "documented-review-only", "programming": "unsupported",
                             "live_control": "unsupported"},
                    unknowns=["hardware revision and installed firmware", "complete memory-programming behavior",
                              "frequency raster", "tone/cross-mode acceptance", "priority scan mapping",
                              "zone/free-slot mapping", "radio-wide settings"])
        return data


FM_MODES = (ChannelMode.FM, ChannelMode.NFM)
BF_F8HP_PRO_V053 = RadioCapabilityProfile(
    profile_id="baofeng-bf-f8hp-pro-v053-us", revision=1,
    manufacturer="BaoFeng / BTECH", model="BF-F8HP PRO",
    firmware_scope="V0.53; manual print version V3.1 (V53 Firmware)",
    region_scope="US manufacturer documentation; not a transmit-authorization check",
    memory_capacity=1000, zone_count=10, channels_per_zone=100,
    receive_bands=(RadioBand(108_000_000, 137_000_000, (ChannelMode.AM,)),
                   RadioBand(137_000_000, 174_000_000, FM_MODES),
                   RadioBand(219_000_000, 260_000_000, FM_MODES),
                   RadioBand(350_000_000, 390_000_000, FM_MODES),
                   RadioBand(400_000_000, 520_000_000, FM_MODES)),
    transmit_bands=(RadioBand(144_000_000, 148_000_000, FM_MODES, 10.0),
                    RadioBand(219_000_000, 225_000_000, FM_MODES, 5.0),
                    RadioBand(420_000_000, 450_000_000, FM_MODES, 10.0)),
    documented_tuning_steps_khz=(2.5, 5.0, 6.25, 10.0, 12.5, 20.0, 25.0, 50.0),
    uncertain_receive_boundaries_hz=(137_000_000,),
    conditional_transmit_ranges_hz=((219_000_000, 221_999_999),),
    airband_step_unverified=True,
    sources=(ProfileSource(
        "https://baofengtech.com/wp-content/uploads/2026/01/BTECHmanual_BF-F8HPPRO_2026.pdf",
        "BF-F8HP PRO instruction manual, print V3.1 (V53 Firmware)",
        "pp. 9, 45-46, 49, 64-66, 78; band endpoints and programming behavior remain qualified",
        "2026-11-06", "1114e1e55c6e6bc71dddcac1421333d199660377115ca2cc5ffb96e75d100b47"),
        ProfileSource("https://baofengtech.com/product/bf-f8hp-pro/", "BTECH product specifications",
                      "Technical specifications: power ceilings only, not exact selectable watt mappings", "2026-11-06")),
)

RADIO_PROFILES = (BF_F8HP_PRO_V053,)


def get_radio_profile(profile_id: str) -> RadioCapabilityProfile | None:
    if profile_id == "":
        return None
    for profile in RADIO_PROFILES:
        if profile_id == profile.profile_id:
            return profile
    raise ValueError("Unknown radio profile. Select Generic CHIRP CSV or a listed documented pilot.")
