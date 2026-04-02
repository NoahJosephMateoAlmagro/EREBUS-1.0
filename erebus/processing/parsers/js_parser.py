from urllib.parse import urlparse
import re

import requests

from shared.logger import Logger

URL_REGEX = r"https?://[^\s\"']+"


class JSParser:
    """
    Parser responsible for retrieving JavaScript content and extracting
    emails and embedded URLs.
    """

    def __init__(
        self,
        email_analyzer,
        connect_timeout: int = 8,
        read_timeout: int = 8
    ):
        """
        Args:
            email_analyzer: Analyzer responsible for extracting emails
            connect_timeout (int): Connection timeout in seconds
            read_timeout (int): Read timeout in seconds
        """
        self.email_analyzer = email_analyzer
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout

    def _is_external(self, script_url: str, base_domain: str) -> bool:
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

    def parse(self, script_url: str, base_domain: str) -> dict | None:
        """
        Retrieves a JavaScript file and extracts emails and URLs.

        Args:
            script_url (str): Script URL
            base_domain (str): Target domain

        Returns:
            dict | None: Parsed result or None if skipped or failed
        """
        try:
            is_wayback = "web.archive.org" in script_url

            if not is_wayback and self._is_external(script_url, base_domain):
                return None

            response = requests.get(
                script_url,
                timeout=(self.connect_timeout, self.read_timeout),
                headers={"User-Agent": "EREBUS/1.0"}
            )

            if response.status_code != 200:
                return None

            content = response.text

            emails = self.email_analyzer.extract(content)
            urls = set(re.findall(URL_REGEX, content))

            return {
                "script_url": script_url,
                "emails": list(emails),
                "urls": list(urls),
                "raw": content
            }

        except Exception as e:
            Logger.error(
                f"JS parsing error script_url={script_url}: {e}",
                context=self.__class__.__name__
            )
            return None