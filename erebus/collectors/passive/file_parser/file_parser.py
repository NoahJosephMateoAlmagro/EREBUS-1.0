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
            try:
                r = requests.get(url, timeout=self.timeout, stream=True)
                if r.status_code != 200:
                    return None

                content = r.content
                if self.max_size and len(content) > self.max_size:
                    return None

                return content
            except Exception:
                return None
