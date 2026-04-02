import requests

from shared.logger import Logger


class FileParser:
    """
    Service responsible for downloading files and delegating parsing
    to the appropriate file parser.
    """

    def __init__(self, parsers, timeout, max_size):
        """
        Args:
            parsers: List of available file parsers
            timeout: Request timeout
            max_size: Maximum allowed file size in bytes
        """
        self.parsers = parsers
        self.timeout = timeout
        self.max_size = max_size

    def parse(self, url: str):
        """
        Downloads and parses a file if supported.

        Args:
            url (str): File URL

        Returns:
            dict | None: Parsed result or None if not supported/failed
        """
        parser = self._select_parser(url)
        if not parser:
            return None

        content = self._download(url)
        if content is None:
            return None

        text = parser.extract_text(content)

        if not text:
            return None

        return {
            "text": text,
            "technique": parser.technique
        }

    def _select_parser(self, url: str):
        """
        Selects an appropriate parser based on file extension.

        Args:
            url (str): File URL

        Returns:
            BaseFileParser | None
        """
        for parser in self.parsers:
            if parser.can_parse(url):
                return parser

        return None

    def _download(self, url: str) -> bytes | None:
        """
        Downloads file content with size limit enforcement.

        Args:
            url (str): File URL

        Returns:
            bytes | None: File content or None if failed
        """
        headers = {
            "User-Agent": "EREBUS/1.0"
        }

        try:
            response = requests.get(
                url,
                timeout=self.timeout,
                headers=headers,
                stream=True,
                allow_redirects=True
            )

            if response.status_code != 200:
                Logger.error(
                    f"File download HTTP error status={response.status_code} url={url}",
                    context=self.__class__.__name__
                )
                return None

            content = bytearray()
            size = 0

            for chunk in response.iter_content(chunk_size=8192):
                if not chunk:
                    continue

                size += len(chunk)

                if self.max_size and size > self.max_size:
                    Logger.error(
                        f"File download exceeded max size url={url}",
                        context=self.__class__.__name__
                    )
                    return None

                content.extend(chunk)

            return bytes(content)

        except Exception as e:
            Logger.error(
                f"File download error url={url}: {e}",
                context=self.__class__.__name__
            )
            return None