"""Core data models used by every Radio Loadout exporter."""

from dataclasses import dataclass, field
from enum import StrEnum


class ChannelMode(StrEnum):
    """Supported radio channel modes."""

    FM = "FM"
    NFM = "NFM"
    AM = "AM"
    DMR = "DMR"


class ToneMode(StrEnum):
    """Supported analog tone modes."""

    NONE = "None"
    CTCSS = "CTCSS"
    DCS = "DCS"


class TonePolarity(StrEnum):
    """Supported DCS signal polarities."""

    NORMAL = "N"
    REVERSE = "R"


@dataclass(frozen=True, slots=True)
class Tone:
    """A CTCSS or DCS tone used for transmitting or receiving."""

    mode: ToneMode = ToneMode.NONE
    value: float | int | None = None
    polarity: TonePolarity = TonePolarity.NORMAL

    def __post_init__(self) -> None:
        if self.mode is ToneMode.NONE:
            if self.value is not None:
                raise ValueError(
                    "A disabled tone cannot have a value."
                )

            if self.polarity is not TonePolarity.NORMAL:
                raise ValueError(
                    "A disabled tone cannot use reverse polarity."
                )

            return

        if self.value is None:
            raise ValueError(
                "An enabled tone must have a value."
            )

        if self.mode is ToneMode.CTCSS:
            if self.polarity is not TonePolarity.NORMAL:
                raise ValueError(
                    "CTCSS tones cannot use DCS polarity."
                )

            if (
                isinstance(self.value, bool)
                or not isinstance(self.value, (int, float))
            ):
                raise ValueError(
                    "A CTCSS tone must be numeric."
                )

            if not 50.0 <= float(self.value) <= 300.0:
                raise ValueError(
                    "CTCSS tone must be between 50.0 and 300.0 Hz."
                )

        if self.mode is ToneMode.DCS:
            if isinstance(self.value, bool) or not isinstance(
                self.value,
                int,
            ):
                raise ValueError(
                    "A DCS code must be an integer."
                )

            digits = f"{self.value:03d}"

            if (
                len(digits) != 3
                or any(
                    digit not in "01234567"
                    for digit in digits
                )
            ):
                raise ValueError(
                    "A DCS code must contain three octal digits."
                )


@dataclass(frozen=True, slots=True)
class AnalogSettings:
    """Settings used by analog FM, NFM, and AM channels."""

    transmit_tone: Tone = field(default_factory=Tone)
    receive_tone: Tone = field(default_factory=Tone)
    power_watts: float | None = None

    def __post_init__(self) -> None:
        if self.power_watts is not None:
            if (
                isinstance(self.power_watts, bool)
                or not isinstance(
                    self.power_watts,
                    (int, float),
                )
            ):
                raise ValueError(
                    "Transmit power must be numeric."
                )

            if self.power_watts <= 0:
                raise ValueError(
                    "Transmit power must be greater than zero."
                )


@dataclass(frozen=True, slots=True)
class Channel:
    """A radio channel independent of any programming software."""

    name: str
    receive_frequency_hz: int
    transmit_frequency_hz: int | None
    mode: ChannelMode = ChannelMode.FM
    analog_settings: AnalogSettings | None = None
    comment: str = ""

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError(
                "Channel name cannot be empty."
            )

        if self.receive_frequency_hz <= 0:
            raise ValueError(
                "Receive frequency must be greater than zero."
            )

        if (
            self.transmit_frequency_hz is not None
            and self.transmit_frequency_hz <= 0
        ):
            raise ValueError(
                "Transmit frequency must be greater than zero."
            )

        if (
            self.mode is ChannelMode.DMR
            and self.analog_settings is not None
        ):
            raise ValueError(
                "A DMR channel cannot have analog settings."
            )

    @property
    def receive_only(self) -> bool:
        return self.transmit_frequency_hz is None