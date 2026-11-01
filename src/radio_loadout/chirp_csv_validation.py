"""Shared CHIRP Generic CSV restrictions, separate from universal channel models."""


def validate_chirp_ctcss(value: float) -> None:
    """Validate the source value against CHIRP's open CTCSS interval."""
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise TypeError("CHIRP Generic CSV CTCSS must be numeric.")
    if not 50.0 < value < 300.0:
        raise ValueError(
            "CHIRP Generic CSV CTCSS must be strictly greater than 50.0 "
            "and strictly less than 300.0 Hz."
        )


def format_chirp_ctcss(value: float) -> str:
    """Return the actual CSV cell only if both source and rounded values are valid."""
    validate_chirp_ctcss(value)
    formatted = f"{float(value):.1f}"
    try:
        validate_chirp_ctcss(float(formatted))
    except ValueError as error:
        raise ValueError(
            f"CTCSS {value} Hz rounds to {formatted} Hz on export. {error}"
        ) from error
    return formatted
