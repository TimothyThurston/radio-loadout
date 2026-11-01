"""Generic DCS code validation; physical radios may support only a subset."""


def validate_dcs_code(value: object) -> int:
    """Validate an integer whose zero-padded decimal spelling is three octal digits."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("A DCS code must be an integer.")
    digits = f"{value:03d}"
    if len(digits) != 3 or any(digit not in "01234567" for digit in digits):
        raise ValueError("A DCS code must contain three octal digits.")
    return value


def parse_dcs_code(value: object) -> int:
    """Read CSV/builder text without coercing booleans, floats, or invalid digits."""
    if isinstance(value, str):
        digits = value.strip()
        if not 1 <= len(digits) <= 3 or any(digit not in "01234567" for digit in digits):
            raise ValueError("A DCS code must contain three octal digits.")
        value = int(digits)
    try:
        return validate_dcs_code(value)
    except TypeError as error:
        # Pydantic field validators treat ValueError as a user validation error.
        raise ValueError(str(error)) from error


def format_dcs_code(value: object) -> str:
    """Preserve leading-zero DCS notation on export without coercing invalid data."""
    return f"{validate_dcs_code(value):03d}"
