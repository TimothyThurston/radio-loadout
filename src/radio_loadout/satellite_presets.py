"""Small independently structured, source-qualified receive-only monitoring presets."""

import re
from dataclasses import asdict, dataclass
from datetime import date

from radio_loadout.models import AnalogSettings, Channel, ChannelMode


@dataclass(frozen=True, slots=True)
class SatelliteSource:
    title: str
    url: str
    locator: str

    def __post_init__(self):
        if (any(type(value) is not str or not value for value in (self.title, self.url, self.locator))
                or not self.url.startswith("https://")):
            raise ValueError("Satellite references require an HTTPS URL and a locator.")


@dataclass(frozen=True, slots=True)
class MonitoringChannel:
    channel_id: str
    name: str
    receive_frequency_hz: int
    purpose: str
    comment: str

    def __post_init__(self):
        if type(self.channel_id) is not str or not re.fullmatch(r"[a-z0-9-]{1,64}", self.channel_id):
            raise ValueError("Invalid monitoring channel ID.")
        if (any(type(value) is not str for value in (self.name, self.purpose, self.comment))
                or not self.name.strip() or len(self.name) > 32 or type(self.receive_frequency_hz) is not int
                or self.receive_frequency_hz <= 0 or not self.purpose or len(self.comment) > 120
                or any(char in self.name + self.comment for char in "\r\n")):
            raise ValueError("Invalid monitoring channel definition.")

    def to_channel(self) -> Channel:
        return Channel(name=self.name, receive_frequency_hz=self.receive_frequency_hz,
                       transmit_frequency_hz=None, mode=ChannelMode.FM,
                       analog_settings=AnalogSettings(power_watts=5.0), comment=self.comment)

    def to_dict(self) -> dict:
        return {**asdict(self), "role": "earth-station-receive-downlink", "mode": "FM",
                "receive_only": True, "transmit_frequency_hz": None,
                "draft": {"name": self.name, "receive_frequency_mhz": f"{self.receive_frequency_hz / 1_000_000:.6f}",
                          "transmit_frequency_mhz": "", "receive_only": True, "mode": "FM", "tone_mode": "none",
                          "power_watts": "5.0", "tuning_step_khz": "5", "scan_behavior": "", "comment": self.comment}}


@dataclass(frozen=True, slots=True)
class MonitoringPack:
    preset_id: str
    revision: int
    title: str
    frequency_sources_checked_on: str
    channels: tuple[MonitoringChannel, ...]
    sources: tuple[SatelliteSource, ...]

    def __post_init__(self):
        if (type(self.preset_id) is not str or not re.fullmatch(r"[a-z0-9-]{1,64}", self.preset_id)
                or type(self.revision) is not int or self.revision < 1 or type(self.title) is not str or not self.title
                or type(self.channels) is not tuple or not self.channels or type(self.sources) is not tuple or not self.sources
                or any(not isinstance(channel, MonitoringChannel) for channel in self.channels)
                or any(not isinstance(source, SatelliteSource) for source in self.sources)
                or type(self.frequency_sources_checked_on) is not str):
            raise ValueError("Invalid monitoring pack.")
        date.fromisoformat(self.frequency_sources_checked_on)
        if len({channel.channel_id for channel in self.channels}) != len(self.channels):
            raise ValueError("Monitoring channel IDs must be unique.")

    def to_dict(self) -> dict:
        return {"preset_id": self.preset_id, "revision": self.revision, "title": self.title,
                "frequency_sources_checked_on": self.frequency_sources_checked_on,
                "operational_status": "unknown-not-live-checked", "hardware_verified": False,
                "sources": [asdict(source) for source in self.sources],
                "channels": [channel.to_dict() for channel in self.channels]}


ISS_VOICE_RX = MonitoringPack(
    "iss-voice-rx", 1, "ISS voice monitoring — receive-only", "2026-11-06",
    (MonitoringChannel("iss-repeater-rx", "ISS RPT RX", 437_800_000,
                       "Nominal FM repeater downlink; listening does not imply a crew conversation.",
                       "RX only; ISS rpt nominal. Ref iss-voice-rx r1; ariss.org/contact-the-iss.html checked 2026-11-06; no live status"),
     MonitoringChannel("iss-crew-rx", "ISS CREW RX", 145_800_000,
                       "Nominal FM crew/school-contact downlink; contacts are intermittent, not a continuous beacon.",
                       "RX only; ISS crew nominal. Ref iss-voice-rx r1; ariss.org/contact-the-iss.html checked 2026-11-06; no live status")),
    (SatelliteSource("ARISS — Contact the ISS", "https://www.ariss.org/contact-the-iss.html",
                     "Selected voice and repeater receive-frequency entries"),
     SatelliteSource("AMSAT — Amateur Radio on the ISS", "https://www.amsat.org/amateur-radio-on-the-iss/",
                     "Selected crew-contact and FM repeater receive-frequency entries")),
)


def satellite_catalog() -> dict:
    return {"schema_version": 1, "packs": [ISS_VOICE_RX.to_dict()],
            "status_url": "https://www.ariss.org/current-status-of-iss-stations.html",
            "limitations": [
                "Source-check dates describe frequency-reference review, not verified RF activity or current station status.",
                "Nominal frequencies only: Doppler shift may require manual receive tuning. No correction or pass prediction is provided.",
                "Reception depends on a suitable pass, equipment, antenna, terrain and interference; silence does not prove a fault.",
                "No uplinks, transmit plans, packet/SSTV decoding, orbit tracking or radio writes are included.",
                "Mode FM is source-backed. Power 5 W (unused on RX-only channels), 5 kHz tuning step and normal scan are application defaults, not satellite-specific requirements.",
                "Adding a preset does not verify physical-radio behavior. Confirm transmit is disabled in the destination software/radio before use.",
                "Channels remain editable after addition; changing receive-only manually may enable transmitting. Preserve receive-only for this monitoring pack.",
            ]}
