from typing import Any
from urllib.parse import urlparse
import shared.constants as C

def list_to_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    return str(value)


def is_external(url: str, base_domain: str) -> bool:
    """
    Determines whether a URL is external to the target domain.

    Args:
        url (str): URL to inspect
        base_domain (str): Target domain

    Returns:
        bool: True if external, False otherwise
    """
    netloc = urlparse(url).netloc.lower().split(":")[0]
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


def build_base_urls(domain: str) -> list[str]:
    """
    Builds the default base URLs for a target domain.

    Args:
        domain (str): Target domain

    Returns:
        list[str]: Default base URLs
    """
    return [
        f"https://{domain}",
        f"https://www.{domain}",
        f"http://{domain}",
        f"http://www.{domain}",
    ]

def is_valid_html_url(url: str) -> bool:
    """
    Determines whether a URL is a valid HTTP(S) candidate and not a filtered asset type.

    Args:
        url (str): Original URL to validate

    Returns:
        bool: True if the URL is accepted, False otherwise
    """
    parsed = urlparse(url)

    if not parsed.scheme.startswith("http"):
        return False

    for ext in C.BAD_EXTENSIONS:
        if parsed.path.lower().endswith(ext):
            return False

    return True

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