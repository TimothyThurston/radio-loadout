"""Central application resource policy, also provided to the browser by the server."""

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class InputLimits:
    csv_upload_bytes: int
    backup_bytes: int
    channels_json_bytes: int
    csv_rows: int
    channels: int
    read_chunk_bytes: int
    import_messages: int
    report_text_chars: int


LIMITS = InputLimits(**json.loads(
    (Path(__file__).parent / "web/static/input-limits.json").read_text(encoding="utf-8")
))


class InputLimitError(ValueError):
    """The request exceeds an application resource limit (HTTP 413)."""


def public_limits() -> dict[str, int]:
    return asdict(LIMITS)


def check_bytes(size: int, maximum: int, label: str) -> None:
    if size > maximum:
        raise InputLimitError(f"{label} exceeds the {maximum}-byte limit.")


def check_channel_count(count: int) -> None:
    if count > LIMITS.channels:
        raise InputLimitError(f"Channel count exceeds the {LIMITS.channels}-channel limit.")


def check_channels_json(text: str) -> None:
    check_bytes(len(text.encode("utf-8")), LIMITS.channels_json_bytes, "channels_json")
    try:
        value = json.loads(text)
    except (ValueError, TypeError):
        return  # Existing form validation supplies the malformed-JSON report.
    except RecursionError as error:
        raise InputLimitError("channels_json is nested too deeply.") from error
    if isinstance(value, list):
        check_channel_count(len(value))
