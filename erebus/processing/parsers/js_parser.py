import re

import requests

from shared.logger import Logger
import shared.constants as C
import shared.utils as Utils
from exceptions.exceptions import ParserError


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
        self.email_analyzer = email_analyzer
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout

    def parse(self, script_url: str, base_domain: str) -> dict | None:
        """
        Retrieves a JavaScript file and extracts emails and URLs.
        """

        is_wayback = "web.archive.org" in script_url

        #Filter to use wayback but avoid external noise at the same time.
        if not is_wayback and Utils.is_external(script_url, base_domain):
            return None

        try:
            response = requests.get(
                script_url,
                timeout=(self.connect_timeout, self.read_timeout),
                headers={"User-Agent": C.USER_AGENT}
            )
        except Exception as e:
            Logger.error(
                f"JS download error script_url={script_url}: {e}",
                context=self.__class__.__name__
            )
            raise ParserError(f"Failed to fetch JS script: {script_url}") from e

        if response.status_code != 200:
            return None

        try:
            content = response.text
            emails = self.email_analyzer.extract(content)
            urls = set(re.findall(C.URL_REGEX, content))

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
            raise ParserError(f"Failed to parse JS script: {script_url}") from e