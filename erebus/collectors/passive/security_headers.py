import requests
import socket
from urllib.parse import urlparse

class SecurityHeadersCollector:

    def __init__(self, timeout=6):
        self.timeout = timeout

    def _is_resolvable(self, host: str) -> bool:
        try:
            socket.getaddrinfo(host, None)
            return True
        except socket.gaierror:
            return False

    def collect(self, url: str) -> dict:
        host = urlparse(url).hostname
        if not host:
            print(f"[SEC-HEADERS] URL inválida: {url}")
            return {}

        if not self._is_resolvable(host):
            print(f"[SEC-HEADERS] Host no resoluble: {host}")
            return {}

        try:
            r = requests.head(
                url,
                allow_redirects=True,
                timeout=self.timeout,
                headers={
                    "User-Agent": "EREBUS/1.0 (Security-Headers)"
                }
            )
        except requests.RequestException as e:
            print(f"[SEC-HEADERS] HEAD error en {url}: {type(e).__name__}")
            return {}

        print(f"[SEC-HEADERS] OK ({r.status_code}) {url}")

        headers = {k.lower(): v for k, v in r.headers.items()}

        return {
            "strict_transport_security": headers.get("strict-transport-security"),
            "content_security_policy": headers.get("content-security-policy"),
            "x_frame_options": headers.get("x-frame-options"),
            "x_content_type_options": headers.get("x-content-type-options"),
            "referrer_policy": headers.get("referrer-policy"),
            "permissions_policy": headers.get("permissions-policy"),
        }