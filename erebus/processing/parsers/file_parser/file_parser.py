import requests


class FileParser:

    def __init__(self, parsers, timeout, max_size):
        self.parsers = parsers
        self.timeout = timeout
        self.max_size = max_size

    def parse(self, url: str):

        parser = self._select_parser(url)
        if not parser:
            return None

        content = self._download(url)
        if not content:
            return None

        text = parser.parse(url, content)

        if not text:
            return None

        return {
            "text": text,
            "technique": parser.technique
        }

    def _select_parser(self, url: str):

        for parser in self.parsers:
            if parser.can_parse(url):
                return parser

        return None

    def _download(self, url: str) -> bytes | None:

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        try:

            r = requests.get(
                url,
                timeout=self.timeout,
                headers=headers,
                stream=True,
                allow_redirects=True
            )

            if r.status_code != 200:
                print(f"[DOWNLOAD] HTTP {r.status_code} -> {url}")
                return None

            content = bytearray()
            size = 0

            for chunk in r.iter_content(chunk_size=8192):

                if not chunk:
                    continue

                size += len(chunk)

                if self.max_size and size > self.max_size:
                    print(f"[DOWNLOAD] File too large -> {url}")
                    return None

                content.extend(chunk)

            return bytes(content)

        except Exception as e:

            print(f"[DOWNLOAD] Exception -> {url} -> {e}")
            return None