from typing import Any
from urllib.parse import urlparse


def list_to_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    return str(value)


def is_external(script_url: str, base_domain: str) -> bool:
    """
    Determines whether a script URL is external to the target domain.

    Args:
        script_url (str): Script URL
        base_domain (str): Target domain

    Returns:
        bool: True if external, False otherwise
    """
    netloc = urlparse(script_url).netloc.lower().split(":")[0]
    base_domain = base_domain.lower().split(":")[0]

    return not (
        netloc == base_domain
        or netloc.endswith("." + base_domain)
    )


def first_or_value(value: Any) -> Any:
    """
    Returns the first element if value is a list, otherwise returns value.
    """
    if isinstance(value, list):
        return value[0] if value else None
    return value


def ensure_list(value: Any) -> list[Any]:
    """
    Ensures the value is always returned as a list.
    """
    if not value:
        return []
    return value if isinstance(value, list) else [value]

def normalize_URL(url: str) -> str:
    """
    Normalizes URLs by removing fragments and trailing slashes.
    """
    return url.split("#")[0].rstrip("/")
