from normalizers.email_normalizer import normalize_obfuscated
from urllib.parse import urlparse

import requests
import re

URL_REGEX = r"https?://[^\s\"']+"


class JSParser:

    def __init__(self, connect_timeout: int = 8, read_timeout: int = 8):
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout

    def _is_external(self, script_url, base_domain):
        netloc = urlparse(script_url).netloc.lower().split(":")[0]
        base_domain = base_domain.lower().split(":")[0]

        return not (
            netloc == base_domain
            or netloc.endswith("." + base_domain)
        )

    def parse(self, script_url: str, base_domain: str) -> dict | None:

        try:
            if self._is_external(script_url, base_domain):
                return None

            r = requests.get(
                script_url,
                timeout=(self.connect_timeout, self.read_timeout),
                headers={"User-Agent": "EREBUS/1.0"}
            )

            if r.status_code != 200:
                return None

            content = r.text

            emails = normalize_obfuscated(content)
            urls = set(re.findall(URL_REGEX, content))  # endpoints / APIs

            return {
                "script_url": script_url,
                "emails": list(emails),
                "urls": list(urls),
                "raw": content
            }

        except Exception as e:
            print(f"[JS ERROR] {script_url} -> {e}")
            return None

