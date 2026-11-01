"""Describe discarded input and export-time normalization without changing channels."""

from dataclasses import asdict, dataclass, field
from decimal import Decimal
from typing import Literal

from radio_loadout import input_limits
from radio_loadout.models import Channel, ToneMode

SUPPORTED_COLUMNS = {
    "Location", "Name", "Frequency", "Duplex", "Offset", "Tone", "rToneFreq", "cToneFreq",
    "DtcsCode", "DtcsPolarity", "RxDtcsCode", "CrossMode", "Mode", "TStep", "Skip", "Power", "Comment",
}


@dataclass(frozen=True)
class ImportMessage:
    kind: Literal["normalization", "default", "loss"]
    row_number: int
    channel_index: int
    channel_name: str
    field: str
    message: str


@dataclass
class ChirpImportResult:
    channels: list[Channel] = field(default_factory=list)
    source_rows: list[int] = field(default_factory=list)
    messages: list[ImportMessage] = field(default_factory=list)
    loss_count: int = 0
    omitted_messages: int = 0

    def add(self, kind, row_number, channel, field_name, message) -> None:
        if kind == "loss":
            self.loss_count += 1
        if len(self.messages) >= input_limits.LIMITS.import_messages:
            self.omitted_messages += 1
            return
        maximum = input_limits.LIMITS.report_text_chars
        def shorten(text):
            return text if len(text) <= maximum else text[:maximum] + "…"
        self.messages.append(ImportMessage(
            kind, row_number, len(self.channels) - 1, shorten(channel.name), shorten(field_name), shorten(message),
        ))

    def report(self) -> dict:
        return {
            "requires_confirmation": self.loss_count > 0,
            "loss_count": self.loss_count,
            "omitted_messages": self.omitted_messages,
            "messages": [asdict(message) for message in self.messages],
        }


def describe_row(result: ChirpImportResult, row: dict, channel: Channel, row_number: int) -> None:
    def add(kind, field, message):
        result.add(kind, row_number, channel, field, message)

    for name, value in row.items():
        if name not in SUPPORTED_COLUMNS and value and value.strip():
            add("loss", name, f"Unsupported column {name!r} contains data that will be discarded.")
    index = len(result.channels) - 1
    location = (row.get("Location") or "").strip()
    if location and location != str(index):
        kind = "normalization" if location.isascii() and location.isdigit() and int(location) == index else "loss"
        add(kind, "Location", f"Original Location {location!r} is not retained; export assigns Location {index} in file order.")
    elif not location:
        add("normalization", "Location", f"No Location supplied; export assigns Location {index} in file order.")
    settings = channel.analog_settings
    if settings.power_watts is None:
        add("default", "Power", "Power is unspecified; the builder and CSV export will use 5 W.")
    elif Decimal((row["Power"].strip().rstrip("wW")).strip()) != Decimal(f"{settings.power_watts:.3f}"):
        add("loss", "Power", f"CSV export rounds power from {row['Power']} to {settings.power_watts:.3f} W.")
    for name, expected in (("Mode", "FM"), ("TStep", "5.0")):
        if not (row.get(name) or "").strip():
            add("default", name, f"Blank or omitted {name} uses {expected}.")
    if any(tone.mode is ToneMode.DCS for tone in (settings.transmit_tone, settings.receive_tone)) and not (row.get("DtcsPolarity") or "").strip():
        add("default", "DtcsPolarity", "Blank or omitted DCS polarity uses NN.")
    for name in ("Name", "Comment"):
        value = row.get(name) or ""
        if value.strip() and value != value.strip():
            add("loss", name, f"Surrounding whitespace in {name} is removed on import.")
    for name in ("Frequency", "Offset"):
        value = (row.get(name) or "").strip()
        active = name == "Frequency" or (row.get("Duplex") or "").lower().strip() in {"+", "-", "split"}
        if value and active:
            original = Decimal(value) * 1_000_000
            rounded = channel.receive_frequency_hz if name == "Frequency" else round(float(value) * 1_000_000)
            if original != Decimal(rounded):
                add("loss", name, f"{name} is rounded from {value} MHz to {rounded / 1_000_000:.6f} MHz (whole Hz).")
    source_tone = (row.get("Tone") or "").casefold().strip()
    for direction, column in (("transmit", "rToneFreq"), ("receive", "cToneFreq")):
        tone = getattr(settings, f"{direction}_tone")
        if tone.mode is ToneMode.CTCSS:
            if source_tone == "tsql":
                column = "cToneFreq" if (row.get("cToneFreq") or "").strip() else "rToneFreq"
            source = row.get(column)
            if Decimal(source.strip()) != Decimal(f"{tone.value:.1f}"):
                add("loss", column, f"CSV export rounds {direction} CTCSS from {source} Hz to {tone.value:.1f} Hz; adjust it if this reaches a CHIRP boundary.")
    duplex = (row.get("Duplex") or "").strip().lower()
    if duplex == "split":
        add("normalization", "Duplex", "Absolute split frequency is retained; export writes an equivalent signed offset.")
    if source_tone in {"tsql", "dtcs"}:
        add("normalization", "Tone", "Matched tones use the active CHIRP value for both directions; inactive tone cells are not channel settings.")
    if source_tone == "cross":
        add("normalization", "Tone", "Tone settings are retained; export may use an equivalent Tone, TSQL, DTCS, or Cross spelling.")
