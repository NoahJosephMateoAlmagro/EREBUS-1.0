def is_valid_domain(value: str) -> str | None:
    if not value:
        return None

    value = value.strip().lower()

    # permitir localhost para pruebas
    if value.startswith("localhost"):
        return value

    if ":" in value:
        value = value.split(":")[0]

    if value.endswith("."):
        value = value[:-1]

    if "." not in value:
        return None

    if any(x in value for x in ["/", "\\", "@", " "]):
        return None

    return value
