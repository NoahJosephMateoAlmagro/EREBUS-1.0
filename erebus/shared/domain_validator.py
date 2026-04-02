def is_valid_domain(value: str) -> str | None:

    """
    Validates and normalizes a domain string.
    Args:
        value (str): Input domain candidate

    Returns:
        str | None: Normalized domain if valid, otherwise None
    """

    if not value:
        return None

    value = value.strip().lower()

    # allow localhost for testing
    if value.startswith("localhost"):
        return value

    # remove port if present
    if ":" in value:
        value = value.split(":")[0]

    # remove trailing dot
    if value.endswith("."):
        value = value[:-1]

    # must contain at least one dot
    if "." not in value:
        return None

    # reject clearly invalid characters
    if any(x in value for x in ["/", "\\", "@", " "]):
        return None

    return value
