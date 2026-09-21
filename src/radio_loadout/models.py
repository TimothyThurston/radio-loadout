"""Core data models used by every Radio Loadout exporter."""

from dataclasses import dataclass
from enum import StrEnum


class ChannelMode(StrEnum):
    """Supported radio channel modes."""

    FM = "FM"
    NFM = "NFM"
    AM = "AM"
    DMR = "DMR"


@dataclass(frozen=True, slots=True)
class Channel:
    """A radio channel independent of any specific programming software."""

    name: str
    receive_frequency_hz: int
    transmit_frequency_hz: int | None
    mode: ChannelMode = ChannelMode.FM
    comment: str = ""

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Channel name cannot be empty.")

        if self.receive_frequency_hz <= 0:
            raise ValueError("Receive frequency must be greater than zero.")

        if self.transmit_frequency_hz is not None and self.transmit_frequency_hz <= 0:
            raise ValueError("Transmit frequency must be greater than zero.")

    @property
    def receive_only(self) -> bool:
        return self.transmit_frequency_hz is None